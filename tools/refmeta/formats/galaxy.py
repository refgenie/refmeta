"""Galaxy reference-data formats.

Covers how Galaxy names and finds reference genomes: the builds.txt dbkey list,
.len chromosome-size files, the /api/genomes and /api/tool_data endpoints,
tool_data_table_conf.xml, the tab-separated .loc files for all_fasta,
fasta_indexes, bwa_mem_indexes, bowtie2_indexes, rnastar_index2x_versioned and
__dbkeys__, the data manager output JSON, and the IDC (Intergalactic Data
Commission) files: genomes.yml, data_managers.yml, per-build request YAML,
and the PR #88 summaries (all_tables YAML, refget json/<id>.json and
yaml/all_fasta.yml). See sources/galaxy/README.md and fields.json.

Native records are flat dicts:
- Tab-separated files: keys are the column names Galaxy declares for the
  table (tool_data_table_conf.xml), or the names used in the maintainer's
  sample-file headers when the file has none (builds.txt, .len).
- JSON/YAML: nested objects are flattened to dotted paths ("level_1.names",
  "params.dbkey_source.dbkey"); arrays stay as values at their path.
- When a record's identity is a mapping key or an enclosing key rather than a
  field, it gets a named key: "data_table", "table", "data_manager",
  "unique_build_id". JSON arrays without keys use "[0]" and "[1]".
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any

import yaml

from . import Format

SOURCE = "galaxy"

# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

try:  # libyaml is faster but absent under Pyodide
    _Loader = yaml.CSafeLoader
except AttributeError:  # pragma: no cover
    _Loader = yaml.SafeLoader


def _jsonable(obj: Any) -> Any:
    """YAML can produce dates; native records must be JSON-serializable."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    return obj


@lru_cache(maxsize=4)
def _yaml(text: str) -> Any:
    """Parse YAML once per text (detectors share the result). None if not YAML."""
    try:
        return yaml.load(text, Loader=_Loader)
    except yaml.YAMLError:
        return None


@lru_cache(maxsize=4)
def _json(text: str) -> Any:
    try:
        return json.loads(text.lstrip("﻿"))
    except ValueError:
        return None


def _flatten(obj: dict, prefix: str = "") -> dict:
    out: dict = {}
    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict) and v:
            out.update(_flatten(v, path))
        else:
            out[path] = v
    return out


def _unflatten(rec: dict) -> dict:
    out: dict = {}
    for path, v in rec.items():
        parts = path.split(".")
        node = out
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return out


def _basename(filename: str) -> str:
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].lower()
    for suffix in (".sample", ".test", ".txt"):
        if name.endswith(suffix) and name != suffix:
            name = name[: -len(suffix)]
    return name


def _data_lines(text: str, comment_char: str = "#") -> list[list[str]]:
    """Split a Galaxy tab-separated file the way TabularToolDataTable does:
    skip lines whose first non-blank character is the comment character,
    drop the line ending, skip empty lines, split on TAB."""
    rows = []
    for line in text.lstrip("﻿").splitlines():
        if line.lstrip().startswith(comment_char):
            continue
        if not line:
            continue
        rows.append(line.split("\t"))
    return rows


def _looks_structured(text: str) -> bool:
    head = text.lstrip("﻿").lstrip()[:1]
    return head in ("{", "[", "<")


# --------------------------------------------------------------------------
# Tab-separated tables: .loc files, builds.txt, .len
# --------------------------------------------------------------------------


def _tsv_reader(cols: list[str], ints: tuple[str, ...] = ()):
    def read(text: str) -> list[dict]:
        out = []
        for fields in _data_lines(text):
            # Galaxy rejects rows with fewer fields than declared columns
            # and ignores fields past the last declared column.
            if len(fields) < len(cols):
                continue
            rec = dict(zip(cols, fields))
            for c in ints:
                if rec.get(c, "").strip().lstrip("-").isdigit():
                    rec[c] = int(rec[c])
            out.append(rec)
        return out

    return read


def _tsv_writer(cols: list[str], header: bool = True):
    def write(records: list[dict]) -> str:
        lines = []
        if header:
            lines.append("#" + "\t".join(f"<{c}>" for c in cols))
        for r in records:
            vals = ["" if r.get(c) is None else str(r.get(c)) for c in cols]
            lines.append("\t".join(v.replace("\t", " ") for v in vals))
        return "\n".join(lines) + "\n"

    return write


# .loc tables -------------------------------------------------------------

_LOC_TABLES = [
    # (format id, data table, columns, file name tokens, description)
    ("galaxy_loc_all_fasta", "all_fasta", ["value", "dbkey", "name", "path"], ("all_fasta",),
     "Galaxy all_fasta.loc: one FASTA file per row (data table all_fasta)."),
    ("galaxy_loc_fasta_indexes", "fasta_indexes", ["value", "dbkey", "name", "path"], ("fasta_indexes",),
     "Galaxy fasta_indexes.loc: samtools faidx-indexed FASTA per row (data table fasta_indexes)."),
    ("galaxy_loc_bwa_mem_indexes", "bwa_mem_indexes", ["value", "dbkey", "name", "path"], ("bwa_mem_index",),
     "Galaxy bwa_mem_index.loc: BWA (0.6+/MEM) index prefix per row (data table bwa_mem_indexes)."),
    ("galaxy_loc_bowtie2_indexes", "bowtie2_indexes", ["value", "dbkey", "name", "path"],
     ("bowtie2_indices", "bowtie2_index"),
     "Galaxy bowtie2_indices.loc: Bowtie2 index basename per row (data table bowtie2_indexes)."),
    ("galaxy_loc_rnastar_index2x_versioned", "rnastar_index2x_versioned",
     ["value", "dbkey", "name", "path", "with_gene_model", "version"], ("rnastar_index2x_versioned",),
     "Galaxy rnastar_index2x_versioned.loc: STAR index directory per row."),
    ("galaxy_loc_dbkeys", "__dbkeys__", ["value", "name", "len_path"], ("dbkeys",),
     "Galaxy dbkeys.loc (data table __dbkeys__): one dbkey per row with its .len file."),
]


def _loc_name_match(filename: str, tokens: tuple[str, ...], table: str) -> bool:
    name = _basename(filename)
    if not name.endswith(".loc"):
        return False
    stem = name[:-4]
    if table == "__dbkeys__" and "all_fasta" in stem:  # all_fasta_dbkeys.loc is an all_fasta file
        return False
    return any(stem == t or stem.endswith("_" + t) or stem.endswith(t) for t in tokens)


def _loc_detector(table: str, cols: list[str], tokens: tuple[str, ...]):
    def detect(text: str, filename: str = "") -> float:
        if _looks_structured(text):
            return 0.0
        rows = _data_lines(text[:200000])
        name_hit = _loc_name_match(filename, tokens, table)
        if name_hit:
            if not rows or all(len(r) >= len(cols) for r in rows):
                return 0.95
            return 0.6
        if not rows:
            return 0.0
        widths = {len(r) for r in rows}
        if widths != {len(cols)}:
            return 0.0
        if table == "__dbkeys__":
            return 0.45 if all(r[2].endswith(".len") for r in rows) else 0.1
        if table == "rnastar_index2x_versioned":
            return 0.5 if all(r[4] in ("0", "1") for r in rows) else 0.1
        paths = [r[3] for r in rows]
        fa = sum(p.endswith((".fa", ".fasta", ".fna")) for p in paths)
        if table == "all_fasta":
            return 0.4 if fa == len(paths) else 0.15
        if table == "bowtie2_indexes":
            return 0.3 if fa == 0 else 0.1
        return 0.2

    return detect


# builds.txt ----------------------------------------------------------------

_BUILDS_COLS = ["dbkey", "display_name"]


def _read_builds(text: str) -> list[dict]:
    # read_dbnames(): '#' lines skipped, then fields[0], fields[1]
    out = []
    for line in text.lstrip("﻿").splitlines():
        if line[:1] == "#":
            continue
        fields = line.replace("\r", "").split("\t")
        if len(fields) < 2:
            continue
        out.append({"dbkey": fields[0], "display_name": fields[1]})
    return out


def _detect_builds(text: str, filename: str = "") -> float:
    if _looks_structured(text):
        return 0.0
    name = _basename(filename)
    rows = _data_lines(text[:100000])
    if name in ("builds", "builds.txt", "manual_builds", "manual_builds.txt") or name.endswith("builds.txt"):
        return 0.9
    if not rows or any(len(r) < 2 for r in rows):
        return 0.0
    if all(not r[1].strip().isdigit() for r in rows) and sum("(" in r[1] for r in rows) >= len(rows) / 2:
        return 0.35 if all(len(r) == 2 for r in rows) else 0.15
    return 0.0


# .len ------------------------------------------------------------------------

_LEN_COLS = ["chrom", "len"]


def _detect_len(text: str, filename: str = "") -> float:
    if _looks_structured(text):
        return 0.0
    rows = _data_lines(text[:100000])
    ok = bool(rows) and all(len(r) == 2 and r[1].strip().isdigit() for r in rows)
    if _basename(filename).endswith(".len"):
        return 0.95 if ok or not rows else 0.5
    return 0.45 if ok else 0.0


# --------------------------------------------------------------------------
# Galaxy API JSON
# --------------------------------------------------------------------------


def _read_api_genomes(text: str) -> list[dict]:
    doc = _json(text)
    if not isinstance(doc, list):
        return []
    return [{"[0]": x[0], "[1]": x[1]} for x in doc if isinstance(x, list) and len(x) >= 2]


def _write_api_genomes(records: list[dict]) -> str:
    return json.dumps([[r.get("[0]"), r.get("[1]")] for r in records]) + "\n"


def _detect_api_genomes(text: str, filename: str = "") -> float:
    if not text.lstrip().startswith("["):
        return 0.0
    doc = _json(text)
    if not isinstance(doc, list) or not doc:
        return 0.0
    if all(isinstance(x, list) and len(x) == 2 and all(isinstance(v, str) for v in x) for x in doc[:200]):
        return 0.9
    return 0.0


_API_GENOME_KEYS = ["id", "reference", "chrom_info", "prev_chroms", "next_chroms", "start_index"]


def _read_api_genome(text: str) -> list[dict]:
    doc = _json(text)
    docs = doc if isinstance(doc, list) else [doc]
    return [dict(d) for d in docs if isinstance(d, dict) and "chrom_info" in d]


def _write_api_genome(records: list[dict]) -> str:
    if len(records) == 1:
        return json.dumps(records[0]) + "\n"
    return json.dumps(records) + "\n"


def _detect_api_genome(text: str, filename: str = "") -> float:
    if '"chrom_info"' not in text[:5000]:
        return 0.0
    return 0.9 if _read_api_genome(text) else 0.0


def _read_api_tool_data(text: str) -> list[dict]:
    doc = _json(text)
    docs = doc if isinstance(doc, list) else [doc]
    out = []
    for d in docs:
        if not (isinstance(d, dict) and isinstance(d.get("columns"), list) and "fields" in d):
            continue
        cols = d["columns"]
        for row in d.get("fields") or []:
            rec = {"name": d.get("name"), "model_class": d.get("model_class"), "columns": list(cols)}
            for c, v in zip(cols, row):
                rec[f"fields[].{c}"] = v
            out.append(rec)
    return out


def _write_api_tool_data(records: list[dict]) -> str:
    tables: dict = {}
    for r in records:
        key = (r.get("name"), r.get("model_class"), tuple(r.get("columns") or []))
        t = tables.setdefault(key, {"name": key[0], "model_class": key[1], "columns": list(key[2]), "fields": []})
        t["fields"].append([r.get(f"fields[].{c}") for c in t["columns"]])
    docs = list(tables.values())
    return json.dumps(docs[0] if len(docs) == 1 else docs) + "\n"


def _detect_api_tool_data(text: str, filename: str = "") -> float:
    head = text[:3000]
    if '"columns"' not in head or '"fields"' not in head:
        return 0.0
    return 0.9 if _read_api_tool_data(text) else 0.0


# --------------------------------------------------------------------------
# tool_data_table_conf.xml
# --------------------------------------------------------------------------

_TABLE_ATTRS = ["name", "comment_char", "allow_duplicate_entries", "type", "asset", "separator",
                "empty_field_value", "user_accessible"]


def _read_tdtc(text: str) -> list[dict]:
    try:
        root = ET.fromstring(text.lstrip("﻿").strip())
    except ET.ParseError:
        return []
    tables = [root] if root.tag == "table" else root.findall("table")
    out = []
    for t in tables:
        rec: dict = {}
        for a in _TABLE_ATTRS:
            if a in t.attrib:
                rec[a] = t.attrib[a]
        cols = t.find("columns")
        if cols is not None and cols.text is not None:
            rec["columns"] = [c.strip() for c in cols.text.split(",")]
        col_elems = t.findall("column")
        if col_elems:
            rec["column"] = [dict(c.attrib) for c in col_elems]
        files = t.findall("file")
        if files:
            rec["file"] = [dict(f.attrib) for f in files]
        fields = t.findall("field")
        if fields:
            rec["field"] = [dict(f.attrib, text=(f.text or "")) for f in fields]
        out.append(rec)
    return out


def _write_tdtc(records: list[dict]) -> str:
    root = ET.Element("tables")
    for r in records:
        t = ET.SubElement(root, "table", {a: str(r[a]) for a in _TABLE_ATTRS if r.get(a) is not None})
        if r.get("columns") is not None:
            ET.SubElement(t, "columns").text = ", ".join(r["columns"])
        for c in r.get("column") or []:
            ET.SubElement(t, "column", {k: str(v) for k, v in c.items()})
        for f in r.get("file") or []:
            ET.SubElement(t, "file", {k: str(v) for k, v in f.items()})
        for f in r.get("field") or []:
            el = ET.SubElement(t, "field", {k: str(v) for k, v in f.items() if k != "text"})
            el.text = f.get("text", "")
    try:
        ET.indent(root, space="    ")
    except AttributeError:  # pragma: no cover (Python < 3.9)
        pass
    return ET.tostring(root, encoding="unicode") + "\n"


def _detect_tdtc(text: str, filename: str = "") -> float:
    head = text.lstrip("﻿").lstrip()[:4000]
    if not head.startswith("<"):
        return 0.0
    if "<tables" in head and "<table " in head:
        return 0.95
    if "<table " in head and ("<columns>" in head or "<file " in head):
        return 0.7
    return 0.0


# --------------------------------------------------------------------------
# Data manager output JSON  {"data_tables": {table: [ {col: val} ]}}
# --------------------------------------------------------------------------


def _read_dm_json(text: str) -> list[dict]:
    doc = _json(text)
    if not isinstance(doc, dict) or not isinstance(doc.get("data_tables"), dict):
        return []
    out = []
    for table, entries in doc["data_tables"].items():
        if isinstance(entries, dict):  # a single entry is allowed instead of a list
            entries = [entries]
        for e in entries or []:
            if isinstance(e, dict):
                out.append({"data_table": table, **e})
    return out


def _write_dm_json(records: list[dict]) -> str:
    tables: dict = {}
    for r in records:
        e = {k: v for k, v in r.items() if k != "data_table"}
        tables.setdefault(r.get("data_table"), []).append(e)
    return json.dumps({"data_tables": tables}, indent=2) + "\n"


def _detect_dm_json(text: str, filename: str = "") -> float:
    if '"data_tables"' not in text[:2000]:
        return 0.0
    return 0.9 if _read_dm_json(text) else 0.1


# --------------------------------------------------------------------------
# IDC genomes.yml (and cvmfs_current_managed/cvmfs_managed_genomes.yml)
# --------------------------------------------------------------------------


def _genome_lists(doc: Any) -> list[list]:
    if isinstance(doc, dict) and isinstance(doc.get("genomes"), list):
        return [doc["genomes"]]
    if isinstance(doc, list):
        return [d["genomes"] for d in doc if isinstance(d, dict) and isinstance(d.get("genomes"), list)]
    return []


def _read_idc_genomes(text: str) -> list[dict]:
    out = []
    for genomes in _genome_lists(_yaml(text)):
        out.extend(_jsonable(dict(g)) for g in genomes if isinstance(g, dict))
    return out


def _write_idc_genomes(records: list[dict]) -> str:
    return yaml.safe_dump({"genomes": records}, sort_keys=False, default_flow_style=False)


def _detect_idc_genomes(text: str, filename: str = "") -> float:
    if "genomes" not in text[:2000] or "dbkey" not in text[:5000]:
        return 0.0
    lists = _genome_lists(_yaml(text))
    if lists and any(isinstance(g, dict) and "dbkey" in g for gl in lists for g in gl):
        return 0.9
    return 0.0


# --------------------------------------------------------------------------
# IDC data_managers.yml  {name: {tool_id, tags, parameters}}
# --------------------------------------------------------------------------


def _read_idc_dms(text: str) -> list[dict]:
    doc = _yaml(text)
    if not isinstance(doc, dict):
        return []
    out = []
    for k, v in doc.items():
        if isinstance(v, dict) and "tool_id" in v:
            out.append(_jsonable({"data_manager": k, **v}))
    return out


def _write_idc_dms(records: list[dict]) -> str:
    doc = {r["data_manager"]: {k: v for k, v in r.items() if k != "data_manager"} for r in records}
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def _detect_idc_dms(text: str, filename: str = "") -> float:
    if "tool_id" not in text[:3000]:
        return 0.0
    doc = _yaml(text)
    if isinstance(doc, dict) and doc and all(isinstance(v, dict) and "tool_id" in v for v in doc.values()):
        return 0.9
    return 0.0


# --------------------------------------------------------------------------
# IDC request: data-managers/<data_table>/<version>.yaml
# --------------------------------------------------------------------------

_REQ_FLATTEN = ("params", "depends_on")


def _read_idc_request(text: str) -> list[dict]:
    doc = _yaml(text)
    if not (isinstance(doc, dict) and "tool_id" in doc and "data_tables" in doc):
        return []
    rec: dict = {}
    for k, v in doc.items():
        if k in _REQ_FLATTEN and isinstance(v, dict) and v:
            rec.update(_flatten(v, k))
        else:
            rec[k] = v
    return [_jsonable(rec)]


def _write_idc_request(records: list[dict]) -> str:
    docs = [_unflatten(r) for r in records]
    return "---\n".join(yaml.safe_dump(d, sort_keys=False, default_flow_style=False) for d in docs)


def _detect_idc_request(text: str, filename: str = "") -> float:
    if "tool_id" not in text[:5000] or "data_tables" not in text[:5000]:
        return 0.0
    return 0.9 if _read_idc_request(text) else 0.0


# --------------------------------------------------------------------------
# PR #88 all_tables YAML (tool_data_table_conf_to_yaml.py)
# {table: [ {<columns>..., loc_file, xml_file} ]}
# --------------------------------------------------------------------------


def _read_all_tables(text: str) -> list[dict]:
    doc = _yaml(text)
    if not isinstance(doc, dict):
        return []
    out = []
    for table, rows in doc.items():
        if not isinstance(rows, list):
            continue
        for r in rows:
            if isinstance(r, dict):
                out.append(_jsonable({"table": table, **r}))
    return out


def _write_all_tables(records: list[dict]) -> str:
    doc: dict = {}
    for r in records:
        doc.setdefault(r.get("table"), []).append({k: v for k, v in r.items() if k != "table"})
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def _detect_all_tables(text: str, filename: str = "") -> float:
    if "loc_file" not in text[:20000]:
        return 0.0
    doc = _yaml(text)
    if not isinstance(doc, dict) or not doc:
        return 0.0
    lists = [v for v in doc.values() if isinstance(v, list)]
    if lists and all(isinstance(r, dict) and "loc_file" in r for v in lists for r in v[:5]):
        return 0.9
    return 0.0


# --------------------------------------------------------------------------
# PR #88 refget summaries: json/<unique_build_id>.json and yaml/all_fasta.yml
# --------------------------------------------------------------------------


def _read_refget_json(text: str) -> list[dict]:
    doc = _json(text)
    docs = doc if isinstance(doc, list) else [doc]
    return [_flatten(d) for d in docs if isinstance(d, dict) and "level_0" in d and "level_2" in d]


def _write_refget_json(records: list[dict]) -> str:
    docs = [_unflatten(r) for r in records]
    return json.dumps(docs[0] if len(docs) == 1 else docs, indent=2) + "\n"


def _detect_refget_json(text: str, filename: str = "") -> float:
    head = text[:3000]
    if '"level_0"' not in head:
        return 0.0
    return 0.9 if _read_refget_json(text) else 0.0


def _read_refget_yaml(text: str) -> list[dict]:
    doc = _yaml(text)
    if not isinstance(doc, dict):
        return []
    out = []
    for k, v in doc.items():
        if isinstance(v, dict) and "level_0" in v:
            out.append(_jsonable({"unique_build_id": k, **_flatten(v)}))
    return out


def _write_refget_yaml(records: list[dict]) -> str:
    doc = {}
    for r in records:
        doc[r["unique_build_id"]] = _unflatten({k: v for k, v in r.items() if k != "unique_build_id"})
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def _detect_refget_yaml(text: str, filename: str = "") -> float:
    if "level_0:" not in text[:3000]:
        return 0.0
    return 0.9 if _read_refget_yaml(text) else 0.0


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

FORMATS = [
    Format(id="galaxy_builds_txt", source=SOURCE,
           description="Galaxy builds.txt: dbkey and display name, one genome build per line.",
           read=_read_builds, write=_tsv_writer(_BUILDS_COLS, header=False), detect=_detect_builds,
           extensions=(".txt", ".sample")),
    Format(id="galaxy_len", source=SOURCE,
           description="Galaxy .len chromosome-length file: chrom and length per line (path from __dbkeys__ len_path).",
           read=_tsv_reader(_LEN_COLS, ints=("len",)), write=_tsv_writer(_LEN_COLS, header=False),
           detect=_detect_len, extensions=(".len",)),
    Format(id="galaxy_api_genomes", source=SOURCE,
           description="Galaxy GET /api/genomes: JSON list of [display name, dbkey] pairs.",
           read=_read_api_genomes, write=_write_api_genomes, detect=_detect_api_genomes,
           extensions=(".json",)),
    Format(id="galaxy_api_genome", source=SOURCE,
           description="Galaxy GET /api/genomes/{id}: one dbkey with its chromosome names and lengths.",
           read=_read_api_genome, write=_write_api_genome, detect=_detect_api_genome,
           extensions=(".json",)),
    Format(id="galaxy_api_tool_data", source=SOURCE,
           description="Galaxy GET /api/tool_data/{table}: one data table's columns and rows.",
           read=_read_api_tool_data, write=_write_api_tool_data, detect=_detect_api_tool_data,
           extensions=(".json",)),
    Format(id="galaxy_tool_data_table_conf", source=SOURCE,
           description="Galaxy tool_data_table_conf.xml: declares each data table, its columns and .loc files.",
           read=_read_tdtc, write=_write_tdtc, detect=_detect_tdtc, extensions=(".xml", ".sample")),
]

for _fid, _table, _cols, _tokens, _desc in _LOC_TABLES:
    FORMATS.append(Format(id=_fid, source=SOURCE, description=_desc,
                          read=_tsv_reader(_cols), write=_tsv_writer(_cols),
                          detect=_loc_detector(_table, _cols, _tokens), extensions=(".loc", ".sample")))

FORMATS += [
    Format(id="galaxy_data_manager_json", source=SOURCE,
           description="Galaxy data manager output JSON: {\"data_tables\": {table: [entries]}}.",
           read=_read_dm_json, write=_write_dm_json, detect=_detect_dm_json,
           extensions=(".json", ".data_manager_json")),
    Format(id="galaxy_idc_genomes", source=SOURCE,
           description="IDC genomes.yml (and cvmfs_managed_genomes.yml): genomes to fetch and index.",
           read=_read_idc_genomes, write=_write_idc_genomes, detect=_detect_idc_genomes,
           extensions=(".yml", ".yaml")),
    Format(id="galaxy_idc_data_managers", source=SOURCE,
           description="IDC data_managers.yml: data manager name to tool id, tags and fixed parameters.",
           read=_read_idc_dms, write=_write_idc_dms, detect=_detect_idc_dms, extensions=(".yml", ".yaml")),
    Format(id="galaxy_idc_request", source=SOURCE,
           description="IDC request file data-managers/<table>/<version>.yaml: one data manager run.",
           read=_read_idc_request, write=_write_idc_request, detect=_detect_idc_request,
           extensions=(".yml", ".yaml")),
    Format(id="galaxy_idc_all_tables", source=SOURCE,
           description="IDC PR #88 all_tables YAML: every data table row with its .loc and conf file.",
           read=_read_all_tables, write=_write_all_tables, detect=_detect_all_tables,
           extensions=(".yml", ".yaml")),
    Format(id="galaxy_idc_refget_json", source=SOURCE,
           description="IDC PR #88 json/<unique_build_id>.json: seqcol digests plus Galaxy aliases for one FASTA.",
           read=_read_refget_json, write=_write_refget_json, detect=_detect_refget_json,
           extensions=(".json",)),
    Format(id="galaxy_idc_refget_yaml", source=SOURCE,
           description="IDC PR #88 yaml/all_fasta.yml: seqcol digest summary per unique_build_id.",
           read=_read_refget_yaml, write=_write_refget_yaml, detect=_detect_refget_yaml,
           extensions=(".yml", ".yaml")),
]
