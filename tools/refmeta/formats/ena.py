"""ENA (European Nucleotide Archive, EMBL-EBI) assembly and sequence formats.

See sources/ena/README.md and sources/ena/fields.json. Field paths:

- XML (ena_assembly_xml): XPath relative to <ASSEMBLY>, "/" between elements,
  "@name" for attributes. ASSEMBLY_ATTRIBUTE tag/value pairs become
  "ASSEMBLY_ATTRIBUTES/<TAG>". Repeated groups (CHROMOSOMES/CHROMOSOME,
  WGS_SET, ASSEMBLY_LINKS/ASSEMBLY_LINK) are lists of dicts whose keys are
  paths relative to the repeated element.
- JSON (ena_browser_summary, ena_refget_metadata): "." between keys. Summary
  "attributes" tag/value pairs become "attributes.<tag>".
- TSV (portal results, FTP reports, Webin lists): the column name.

Empty values are dropped on read and restored on write.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

from . import Format

SOURCE = "ena"


# ---------------------------------------------------------------- helpers


def _num(text):
    """'83' -> 83, '52.5' -> 52.5, anything else unchanged."""
    if isinstance(text, str):
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        if re.fullmatch(r"-?\d+\.\d+", text):
            return float(text)
    return text


def _int(text):
    if isinstance(text, str) and re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _json_or_none(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.rstrip("\r\n")
    return ""


def _read_tsv(text: str) -> tuple[list[str], list[dict]]:
    # Plain tab split: ENA TSVs are not quoted, and values may contain '"'.
    lines = [ln.rstrip("\r") for ln in text.lstrip("\ufeff").split("\n")]
    rows = [ln.split("\t") for ln in lines if ln.strip()]
    if not rows:
        return [], []
    header = rows[0]
    out = []
    for r in rows[1:]:
        out.append({h: (r[i] if i < len(r) else "") for i, h in enumerate(header)})
    return header, out


def _cell(value) -> str:
    return re.sub(r"[\t\r\n]+", " ", _str(value))


def _write_tsv(header: list[str], rows: list[dict]) -> str:
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join(_cell(r.get(h)) for h in header))
    return "\n".join(lines) + "\n"


def _ordered_columns(canonical: list[str], records: list[dict]) -> list[str]:
    present = []
    for r in records:
        for k in r:
            if k not in present:
                present.append(k)
    cols = [c for c in canonical if c in present]
    cols += [c for c in present if c not in cols]
    return cols


# ---------------------------------------------------------------- assembly XML

# Top-level element order used when writing (from ENA.assembly.xsd, plus the
# elements ENA serves but the XSD does not declare: ASSEMBLY_TYPE, PLATFORM,
# PROGRAM, COVERAGE; their position follows the served XML).
_XML_ORDER = [
    "IDENTIFIERS", "TITLE", "DESCRIPTION", "NAME", "ASSEMBLY_LEVEL",
    "ASSEMBLY_TYPE", "PLATFORM", "PROGRAM", "COVERAGE", "GENOME_REPRESENTATION",
    "TAXON", "SAMPLE_REF", "STUDY_REF", "WGS_SET", "CHROMOSOMES",
    "ASSEMBLY_LINKS", "ASSEMBLY_ATTRIBUTES",
]
_XML_ATTR_ORDER = ["@accession", "@alias", "@center_name", "@broker_name"]
# Repeated groups kept as lists of dicts.
_XML_GROUPS = {
    "CHROMOSOMES/CHROMOSOME": "CHROMOSOMES",
    "ASSEMBLY_LINKS/ASSEMBLY_LINK": "ASSEMBLY_LINKS",
    "WGS_SET": None,
    "IDENTIFIERS/EXTERNAL_ID": "IDENTIFIERS",  # items: {"@namespace": ..., "#text": ...}
}
# Repeatable leaf elements kept as lists of strings.
_XML_LISTS = {"IDENTIFIERS/SECONDARY_ID", "IDENTIFIERS/UUID"}
_XML_INT = {"TAXON/TAXON_ID"}
_XML_NUM = {"COVERAGE"}


def _flatten_elem(elem, prefix: str, out: dict) -> None:
    for k, v in elem.attrib.items():
        out[f"{prefix}/@{k}" if prefix else f"@{k}"] = v
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        if text:
            out[prefix or "#text"] = text
        return
    for child in children:
        path = f"{prefix}/{child.tag}" if prefix else child.tag
        if path in _XML_GROUPS:
            sub: dict = {}
            _flatten_elem(child, "", sub)
            out.setdefault(path, []).append(sub)
        elif path == "ASSEMBLY_ATTRIBUTES/ASSEMBLY_ATTRIBUTE":
            tag = (child.findtext("TAG") or "").strip()
            val = (child.findtext("VALUE") or "").strip()
            if tag:
                out[f"ASSEMBLY_ATTRIBUTES/{tag}"] = _int(val) if val else val
        elif path in _XML_LISTS:
            text = (child.text or "").strip()
            if text:
                out.setdefault(path, []).append(text)
        else:
            _flatten_elem(child, path, out)


def read_assembly_xml(text: str) -> list[dict]:
    root = ET.fromstring(text.lstrip("\ufeff").encode("utf-8"))
    assemblies = [root] if root.tag == "ASSEMBLY" else root.findall("ASSEMBLY")
    records = []
    for asm in assemblies:
        rec: dict = {}
        _flatten_elem(asm, "", rec)
        for k in _XML_INT:
            if k in rec:
                rec[k] = _int(rec[k])
        for k in _XML_NUM:
            if k in rec:
                rec[k] = _num(rec[k])
        records.append(rec)
    return records


def _xml_set(parent, rel_path: str, value) -> None:
    """Create elements along rel_path under parent and set text or attribute."""
    parts = rel_path.split("/")
    node = parent
    for part in parts[:-1]:
        child = node.find(part)
        if child is None:
            child = ET.SubElement(node, part)
        node = child
    last = parts[-1]
    if last.startswith("@"):
        node.set(last[1:], _str(value))
    else:
        child = node.find(last)
        if child is None:
            child = ET.SubElement(node, last)
        child.text = _str(value)


def _xml_top(key: str) -> str:
    return key.split("/")[0]


def write_assembly_xml(records: list[dict]) -> str:
    root = ET.Element("ASSEMBLY_SET")
    for rec in records:
        asm = ET.SubElement(root, "ASSEMBLY")
        for a in _XML_ATTR_ORDER + [k for k in rec if k.startswith("@") and k not in _XML_ATTR_ORDER]:
            if a in rec:
                asm.set(a[1:], _str(rec[a]))
        elem_keys = [k for k in rec if not k.startswith("@")]
        order = {name: i for i, name in enumerate(_XML_ORDER)}
        elem_keys.sort(key=lambda k: order.get(_xml_top(k), len(order)))
        for key in elem_keys:
            value = rec[key]
            if key in _XML_GROUPS:
                container_name = _XML_GROUPS[key]
                if container_name:
                    container = asm.find(container_name)
                    if container is None:
                        container = ET.SubElement(asm, container_name)
                    item_tag = key.split("/")[-1]
                else:
                    container, item_tag = asm, key
                for item in value:
                    el = ET.SubElement(container, item_tag)
                    for sub_key, sub_val in item.items():
                        if sub_key.startswith("@"):
                            el.set(sub_key[1:], _str(sub_val))
                    for sub_key, sub_val in item.items():
                        if sub_key == "#text":
                            el.text = _str(sub_val)
                        elif not sub_key.startswith("@"):
                            _xml_set(el, sub_key, sub_val)
            elif key.startswith("ASSEMBLY_ATTRIBUTES/"):
                container = asm.find("ASSEMBLY_ATTRIBUTES")
                if container is None:
                    container = ET.SubElement(asm, "ASSEMBLY_ATTRIBUTES")
                att = ET.SubElement(container, "ASSEMBLY_ATTRIBUTE")
                ET.SubElement(att, "TAG").text = key[len("ASSEMBLY_ATTRIBUTES/"):]
                ET.SubElement(att, "VALUE").text = _str(value)
            elif key in _XML_LISTS:
                parent_path, leaf = key.rsplit("/", 1)
                parent = asm.find(parent_path)
                if parent is None:
                    parent = ET.SubElement(asm, parent_path)
                for v in value:
                    ET.SubElement(parent, leaf).text = _str(v)
            else:
                _xml_set(asm, key, value)
    # Same layout as ENA serves: <ASSEMBLY> elements are not indented.
    parts = []
    for asm in root:
        asm.tail = None
        if hasattr(ET, "indent"):
            ET.indent(asm, space="  ")
        parts.append(ET.tostring(asm, encoding="unicode"))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<ASSEMBLY_SET>\n'
            + "\n".join(parts) + "\n</ASSEMBLY_SET>\n")


def detect_assembly_xml(text: str, filename: str = "") -> float:
    head = text[:2000]
    if "<ASSEMBLY_SET" in head:
        return 0.95
    if re.search(r"<ASSEMBLY[\s>]", head) and "<ASSEMBLY_LEVEL>" in text[:20000]:
        return 0.85
    return 0.0


# ---------------------------------------------------------------- browser API summary JSON

_SUMMARY_LISTS = {"chromosomes", "links", "publications", "secondaryAccession",
                  "parentAccession", "merged"}


def read_browser_summary(text: str) -> list[dict]:
    data = json.loads(text)
    items = data.get("summaries", []) if isinstance(data, dict) else data
    if isinstance(items, dict):
        items = [items]
    records = []
    for s in items:
        rec: dict = {}
        for k, v in s.items():
            if v is None or v == "" or v == []:
                continue
            if k == "attributes" and isinstance(v, list):
                for a in v:
                    tag = a.get("tag")
                    if tag:
                        val = a.get("value")
                        rec[f"attributes.{tag}"] = _int(val) if isinstance(val, str) and val else val
            elif k == "searchFields" and isinstance(v, dict):
                for sk, sv in v.items():
                    if sv not in (None, ""):
                        rec[f"searchFields.{sk}"] = sv
            else:
                rec[k] = v
        records.append(rec)
    return records


def write_browser_summary(records: list[dict]) -> str:
    out = []
    for rec in records:
        s: dict = {}
        attrs = []
        search = {}
        for k, v in rec.items():
            if k.startswith("attributes."):
                attrs.append({"tag": k[len("attributes."):], "value": _str(v)})
            elif k.startswith("searchFields."):
                search[k[len("searchFields."):]] = v
            else:
                s[k] = v
        if attrs:
            s["attributes"] = attrs
        if search:
            s["searchFields"] = search
        out.append(s)
    return json.dumps({"summaries": out, "total": str(len(out))}, indent=2) + "\n"


def detect_browser_summary(text: str, filename: str = "") -> float:
    if '"summaries"' not in text[:200]:
        return 0.0
    data = _json_or_none(text)
    if isinstance(data, dict) and isinstance(data.get("summaries"), list):
        if any(isinstance(s, dict) and s.get("dataType") == "ASSEMBLY" for s in data["summaries"]):
            return 0.95
        return 0.5
    return 0.0


# ---------------------------------------------------------------- portal API (assembly and sequence results)

# Column order of a fields=all search, as served on 2026-11-17.
_PORTAL_ASSEMBLY_COLS = (
    "accession assembly_title experimental_factor sequence_accession sample_accession "
    "environment_biome program dev_stage binning_software location_start marine_region "
    "assembly_software common_name serotype environment_feature last_updated germline "
    "sample_collection assembly_set_accession culture_collection version "
    "broad_scale_environmental_context submission_tool genome_representation status "
    "completeness_score lon collected_by isolate tax_lineage host_sex variety temperature ecotype "
    "sample_alias sampling_campaign mating_type tissue_lib collection_date_start "
    "environmental_sample sub_species sex checklist contamination_score specimen_voucher depth "
    "assembly_accession tax_division assembly_type taxonomic_identity_marker "
    "host_growth_conditions study_name collection_date country ncbi_reporting_standard "
    "description_comment host_gravidity wgs_set run_accession center_name identified_by cell_line "
    "sampling_site assembly_level host tag first_created lat strain study_title bio_material "
    "host_body_site local_environmental_context scientific_name assembly_quality "
    "collection_date_end sample_capture_status sample_title host_status tax_id host_genotype "
    "host_phenotype study_accession environmental_medium cultivar target_gene submitted_host_sex "
    "surveillance_target altitude host_scientific_name description assembly_name "
    "secondary_sample_accession platform environment_material host_tax_id sampling_platform "
    "sample_material taxonomic_classification location_end protocol_label cell_type coverage "
    "elevation salinity sequencing_method disease study_description sub_strain base_count ph "
    "serovar investigation_type location category tissue_type age isolation_source"
).split()

_PORTAL_SEQUENCE_COLS = (
    "accession description collection_date country keywords sequence_accession dataclass "
    "sample_accession dev_stage run_accession pubmed_id identified_by cell_line host tag "
    "serotype strain bio_material last_updated germline organelle topology agricola_id "
    "sequence_md5 scientific_name collection_date_end culture_collection tax_id "
    "study_accession cultivar doi mol_type status altitude metagenome_source plasmid "
    "collected_by secondary_sample_accession host_tax_id isolate tax_lineage variety "
    "cell_type ecotype haplotype mating_type tissue_lib collection_date_start "
    "environmental_sample first_public sub_species sex sub_strain base_count "
    "specimen_voucher assembly_accession patent_number tax_division serovar location "
    "lab_host tissue_type indexed_date isolation_source sequence_version"
).split()

_PORTAL_INT = {"version", "tax_id", "base_count", "host_tax_id", "sequence_version"}
_PORTAL_NUM = {"coverage", "completeness_score", "contamination_score"}
_PORTAL_BOOL = {"germline", "environmental_sample"}
_PORTAL_SPLIT = {"assembly": {"sequence_accession"}, "sequence": set()}


def _portal_typed(row: dict, kind: str) -> dict:
    rec = {}
    for k, v in row.items():
        if v is None:
            continue
        if not isinstance(v, str):
            v = _str(v)
        if v == "":
            continue
        if k in _PORTAL_SPLIT[kind]:
            rec[k] = [x for x in v.split(";") if x]
        elif k in _PORTAL_INT:
            rec[k] = _int(v)
        elif k in _PORTAL_NUM:
            rec[k] = _num(v)
        elif k in _PORTAL_BOOL and v in ("true", "false"):
            rec[k] = v == "true"
        else:
            rec[k] = v
    return rec


def _portal_rows(text: str) -> list[dict]:
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("["):
        data = json.loads(stripped)
        return [d for d in data if isinstance(d, dict)]
    _, rows = _read_tsv(text)
    return rows


def _portal_untyped(rec: dict, kind: str) -> dict:
    out = {}
    for k, v in rec.items():
        if k in _PORTAL_SPLIT[kind] and isinstance(v, list):
            out[k] = ";".join(_str(x) for x in v)
        else:
            out[k] = v
    return out


def read_portal_assembly(text: str) -> list[dict]:
    return [_portal_typed(r, "assembly") for r in _portal_rows(text)]


def write_portal_assembly(records: list[dict]) -> str:
    rows = [_portal_untyped(r, "assembly") for r in records]
    return _write_tsv(_ordered_columns(_PORTAL_ASSEMBLY_COLS, rows), rows)


def read_portal_sequence(text: str) -> list[dict]:
    return [_portal_typed(r, "sequence") for r in _portal_rows(text)]


def write_portal_sequence(records: list[dict]) -> str:
    rows = [_portal_untyped(r, "sequence") for r in records]
    return _write_tsv(_ordered_columns(_PORTAL_SEQUENCE_COLS, rows), rows)


def _portal_columns(text: str) -> set[str]:
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("["):
        data = _json_or_none(stripped)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return set(data[0])
        return set()
    return set(_first_line(stripped).split("\t"))


_ASSEMBLY_MARKERS = {"assembly_set_accession", "assembly_name", "assembly_level", "assembly_title"}
_SEQUENCE_MARKERS = {"sequence_md5", "dataclass", "sequence_version", "mol_type", "topology"}


def detect_portal_assembly(text: str, filename: str = "") -> float:
    cols = _portal_columns(text)
    if cols & _ASSEMBLY_MARKERS and not cols & _SEQUENCE_MARKERS:
        return 0.9 if len(cols & _ASSEMBLY_MARKERS) >= 2 else 0.6
    return 0.0


def detect_portal_sequence(text: str, filename: str = "") -> float:
    cols = _portal_columns(text)
    if cols & _SEQUENCE_MARKERS and not cols & _ASSEMBLY_MARKERS:
        if "sequence_md5" in cols or len(cols & _SEQUENCE_MARKERS) >= 2:
            return 0.85
        return 0.5
    return 0.0


# ---------------------------------------------------------------- FTP assembly reports

_SEQREPORT_COLS = ["accession", "sequence-name", "sequence-length", "sequence-role",
                   "replicon-name", "replicon-type", "assembly-unit"]
_SEQREPORT_NA = {"replicon-name", "replicon-type"}


def read_sequence_report(text: str) -> list[dict]:
    _, rows = _read_tsv(text)
    out = []
    for r in rows:
        rec = {}
        for k, v in r.items():
            if v == "" or (k in _SEQREPORT_NA and v == "NA"):
                continue
            rec[k] = _int(v) if k == "sequence-length" else v
        out.append(rec)
    return out


def write_sequence_report(records: list[dict]) -> str:
    cols = _ordered_columns(_SEQREPORT_COLS, records)
    for c in _SEQREPORT_COLS:
        if c not in cols:
            cols.insert(_SEQREPORT_COLS.index(c), c)
    rows = [{**{c: "NA" for c in _SEQREPORT_NA}, **r} for r in records]
    return _write_tsv(cols, rows)


def detect_sequence_report(text: str, filename: str = "") -> float:
    if _first_line(text).split("\t") == _SEQREPORT_COLS:
        return 1.0 if filename.endswith("_sequence_report.txt") else 0.95
    return 0.0


_REGIONS_COLS = ["region", "accession", "sequence-length", "sequence-range",
                 "replicon", "replicon-range"]


def read_regions(text: str) -> list[dict]:
    _, rows = _read_tsv(text)
    return [{k: (_int(v) if k == "sequence-length" else v) for k, v in r.items() if v != ""}
            for r in rows]


def write_regions(records: list[dict]) -> str:
    return _write_tsv(_ordered_columns(_REGIONS_COLS, records), records)


def detect_regions(text: str, filename: str = "") -> float:
    if _first_line(text).split("\t") == _REGIONS_COLS:
        return 1.0 if filename.endswith("_regions.txt") else 0.95
    return 0.0


# ---------------------------------------------------------------- CRAM reference registry (refget) metadata

_REFGET_KEYS = ["id", "md5", "trunc512", "ga4gh", "length", "aliases"]


def read_refget_metadata(text: str) -> list[dict]:
    text = text.lstrip("\ufeff").strip()
    docs = []
    whole = _json_or_none(text)
    if isinstance(whole, list):
        docs = whole
    elif isinstance(whole, dict):
        docs = [whole]
    else:
        docs = [json.loads(line) for line in text.splitlines() if line.strip()]
    out = []
    for d in docs:
        meta = d.get("metadata", d) if isinstance(d, dict) else {}
        rec = {}
        for k, v in meta.items():
            if v is None or v == []:
                continue
            rec[f"metadata.{k}"] = v
        out.append(rec)
    return out


def write_refget_metadata(records: list[dict]) -> str:
    lines = []
    for rec in records:
        meta = {k: None for k in _REFGET_KEYS}
        meta["aliases"] = []
        for k, v in rec.items():
            meta[k[len("metadata."):] if k.startswith("metadata.") else k] = v
        lines.append(json.dumps({"metadata": meta}, separators=(",", ":")))
    return "\n".join(lines) + "\n"


def detect_refget_metadata(text: str, filename: str = "") -> float:
    line = _first_line(text.lstrip("\ufeff"))
    if '"metadata"' not in line:
        return 0.0
    d = _json_or_none(line) or _json_or_none(text)
    if isinstance(d, list) and d:
        d = d[0]
    meta = d.get("metadata") if isinstance(d, dict) else None
    if not isinstance(meta, dict) or "md5" not in meta or "length" not in meta:
        return 0.0
    # ENA's registry returns trunc512 alongside ga4gh, and INSDC aliases.
    if '"naming_authority":"INSDC"' in text.replace(" ", "") or str(meta.get("id", "")).startswith("insdc:"):
        return 0.8
    if "trunc512" in meta:
        return 0.6
    return 0.4


# ---------------------------------------------------------------- Webin-CLI submission lists

_CHR_TYPES = {"chromosome", "plasmid", "linkage_group", "monopartite", "segmented", "multipartite"}


def _ws_rows(text: str) -> list[list[str]]:
    return [line.split() for line in text.lstrip("\ufeff").splitlines() if line.strip()]


def read_chromosome_list(text: str) -> list[dict]:
    out = []
    for cols in _ws_rows(text):
        rec = {"OBJECT_NAME": cols[0]}
        if len(cols) > 1:
            rec["CHROMOSOME_NAME"] = cols[1]
        if len(cols) > 2:
            parts = cols[2].split("-")
            if len(parts) == 2:
                rec["TOPOLOGY"] = parts[0]
                rec["CHROMOSOME_TYPE"] = parts[1]
            else:
                rec["CHROMOSOME_TYPE"] = cols[2]
        if len(cols) > 3:
            rec["CHROMOSOME_LOCATION"] = cols[3]
        out.append(rec)
    return out


def write_chromosome_list(records: list[dict]) -> str:
    lines = []
    for r in records:
        ctype = _str(r.get("CHROMOSOME_TYPE", "chromosome"))
        if r.get("TOPOLOGY"):
            ctype = f"{r['TOPOLOGY']}-{ctype}"
        cols = [_str(r.get("OBJECT_NAME")), _str(r.get("CHROMOSOME_NAME")), ctype]
        if r.get("CHROMOSOME_LOCATION"):
            cols.append(_str(r["CHROMOSOME_LOCATION"]))
        lines.append("\t".join(cols))
    return "\n".join(lines) + "\n"


def detect_chromosome_list(text: str, filename: str = "") -> float:
    rows = _ws_rows(text[:20000])
    if not rows or any(len(r) not in (3, 4) for r in rows):
        return 0.0
    for r in rows:
        t = r[2].lower().split("-")[-1]
        if t not in _CHR_TYPES:
            return 0.0
    return 0.85


def read_unlocalised_list(text: str) -> list[dict]:
    out = []
    for cols in _ws_rows(text):
        rec = {"OBJECT_NAME": cols[0]}
        if len(cols) > 1:
            rec["CHROMOSOME_NAME"] = cols[1]
        out.append(rec)
    return out


def write_unlocalised_list(records: list[dict]) -> str:
    return "".join(f"{_str(r.get('OBJECT_NAME'))}\t{_str(r.get('CHROMOSOME_NAME'))}\n" for r in records)


def detect_unlocalised_list(text: str, filename: str = "") -> float:
    rows = _ws_rows(text[:20000])
    if not rows or any(len(r) != 2 for r in rows):
        return 0.0
    if all(r[1].isdigit() for r in rows):
        return 0.02  # looks like chrom.sizes (name, length)
    if "unlocali" in filename.lower():
        return 0.8
    return 0.25


# ---------------------------------------------------------------- registry

FORMATS = [
    Format(
        id="ena_assembly_xml",
        source=SOURCE,
        description="ENA Browser API assembly XML (ASSEMBLY_SET/ASSEMBLY), one record per assembly",
        read=read_assembly_xml,
        write=write_assembly_xml,
        detect=detect_assembly_xml,
        extensions=(".xml",),
    ),
    Format(
        id="ena_browser_summary",
        source=SOURCE,
        description="ENA Browser API /summary JSON for an assembly, one record per summary",
        read=read_browser_summary,
        write=write_browser_summary,
        detect=detect_browser_summary,
        extensions=(".json",),
    ),
    Format(
        id="ena_portal_assembly",
        source=SOURCE,
        description="ENA Portal API search result=assembly (TSV or JSON), one record per assembly version",
        read=read_portal_assembly,
        write=write_portal_assembly,
        detect=detect_portal_assembly,
        extensions=(".tsv", ".json"),
    ),
    Format(
        id="ena_portal_sequence",
        source=SOURCE,
        description="ENA Portal API search result=sequence (TSV or JSON), one record per INSDC sequence",
        read=read_portal_sequence,
        write=write_portal_sequence,
        detect=detect_portal_sequence,
        extensions=(".tsv", ".json"),
    ),
    Format(
        id="ena_sequence_report",
        source=SOURCE,
        description="ENA FTP <GCA>_sequence_report.txt, one record per sequence in the assembly",
        read=read_sequence_report,
        write=write_sequence_report,
        detect=detect_sequence_report,
        extensions=(".txt", ".tsv"),
    ),
    Format(
        id="ena_regions",
        source=SOURCE,
        description="ENA FTP <GCA>_regions.txt, one record per alt-locus scaffold placement",
        read=read_regions,
        write=write_regions,
        detect=detect_regions,
        extensions=(".txt", ".tsv"),
    ),
    Format(
        id="ena_refget_metadata",
        source=SOURCE,
        description="ENA CRAM reference registry (refget 2.0) sequence metadata JSON, one record per sequence",
        read=read_refget_metadata,
        write=write_refget_metadata,
        detect=detect_refget_metadata,
        extensions=(".json", ".jsonl"),
    ),
    Format(
        id="ena_webin_chromosome_list",
        source=SOURCE,
        description="ENA Webin-CLI genome submission chromosome list file, one record per chromosome",
        read=read_chromosome_list,
        write=write_chromosome_list,
        detect=detect_chromosome_list,
        extensions=(".txt", ".tsv"),
    ),
    Format(
        id="ena_webin_unlocalised_list",
        source=SOURCE,
        description="ENA Webin-CLI genome submission unlocalised list file, one record per unlocalised sequence",
        read=read_unlocalised_list,
        write=write_unlocalised_list,
        detect=detect_unlocalised_list,
        extensions=(".txt", ".tsv"),
    ),
]
