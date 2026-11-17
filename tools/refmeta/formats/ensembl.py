"""Ensembl genome metadata formats.

Covers the legacy Ensembl release (REST /info endpoints, core database meta
table dumps, the per-release species list, FASTA DNA header lines) and the new
Ensembl site (metadata API at www.ensembl.org/api/metadata, the
ftp.ebi.ac.uk/pub/ensemblorganisms species.json and chromosomes.tsv files).

Field paths match sources/ensembl/fields.json. Nested JSON objects from the new
metadata API are flattened with "." (e.g. "assembly.accession_id"). In
species.json, map keys that are data (species name, assembly accession) are
written as "{species}" and "{accession}" placeholders in the path.
"""
from __future__ import annotations

import json
import re

from . import Format

SOURCE = "ensembl"


# ----------------------------------------------------------------- helpers


def _load_json(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _flatten(obj: dict, prefix: str = "") -> dict:
    """Flatten nested dicts with '.'; lists, scalars and empty dicts stay as values."""
    out: dict = {}
    for k, v in obj.items():
        path = f"{prefix}{k}"
        if isinstance(v, dict) and v:
            out.update(_flatten(v, path + "."))
        else:
            out[path] = v
    return out


def _unflatten(rec: dict) -> dict:
    out: dict = {}
    for path, v in rec.items():
        parts = path.split(".")
        cur = out
        for p in parts[:-1]:
            nxt = cur.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[p] = nxt
            cur = nxt
        cur[parts[-1]] = v
    return out


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line
    return ""


def _is_list_of_dicts_with(obj, keys: set) -> bool:
    return (
        isinstance(obj, list)
        and len(obj) > 0
        and all(isinstance(r, dict) and keys <= set(r) for r in obj)
    )


# --------------------------------------- REST /info/assembly/:species


def read_rest_info_assembly(text: str) -> list[dict]:
    d = _load_json(text)
    items = d if isinstance(d, list) else [d]
    return [{k: v for k, v in o.items() if k != "top_level_region"} for o in items if isinstance(o, dict)]


def write_rest_info_assembly(records: list[dict]) -> str:
    return _dump(records[0] if len(records) == 1 else records)


def detect_rest_info_assembly(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and "default_coord_system_version" in d and (
        "golden_path" in d or "karyotype" in d or "top_level_region" in d
    ):
        return 0.95
    return 0.0


# ------------------------ REST /info/assembly/:species top_level_region rows


def read_rest_toplevel_region(text: str) -> list[dict]:
    d = _load_json(text)
    rows = d.get("top_level_region", []) if isinstance(d, dict) else d
    return [dict(r) for r in rows or [] if isinstance(r, dict)]


def write_rest_toplevel_region(records: list[dict]) -> str:
    return _dump({"top_level_region": records})


def detect_rest_toplevel_region(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and isinstance(d.get("top_level_region"), list):
        # A full /info/assembly response is better described by the assembly format.
        return 0.6 if "default_coord_system_version" in d else 0.9
    if _is_list_of_dicts_with(d, {"name", "length", "coord_system"}):
        return 0.85
    return 0.0


# ------------------------------- REST /info/assembly/:species/:region_name


def read_rest_info_assembly_region(text: str) -> list[dict]:
    d = _load_json(text)
    items = d if isinstance(d, list) else [d]
    return [dict(o) for o in items if isinstance(o, dict)]


def write_rest_info_assembly_region(records: list[dict]) -> str:
    return _dump(records[0] if len(records) == 1 else records)


def detect_rest_info_assembly_region(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and "coordinate_system" in d and "is_chromosome" in d:
        return 0.95
    return 0.0


# ------------------------------------------------ REST /info/genomes/:name


def read_rest_info_genomes(text: str) -> list[dict]:
    d = _load_json(text)
    items = d if isinstance(d, list) else [d]
    return [dict(o) for o in items if isinstance(o, dict)]


def write_rest_info_genomes(records: list[dict]) -> str:
    return _dump(records[0] if len(records) == 1 else records)


def detect_rest_info_genomes(text: str, filename: str = "") -> float:
    d = _load_json(text)
    o = d[0] if isinstance(d, list) and d else d
    if isinstance(o, dict) and "assembly_accession" in o and "url_name" in o and (
        "data_release_id" in o or "division" in o
    ):
        return 0.95
    return 0.0


# --------------------------------------------- core database meta table dump

# Keys stored with species_id NULL (database-wide, not per species).
_META_DB_LEVEL = {"schema_type", "schema_version", "patch"}
# Keys that may repeat; always read as lists so the type is stable.
_META_MULTI = {
    "patch",
    "assembly.mapping",
    "liftover.mapping",
    "repeat.analysis",
    "species.alias",
    "species.classification",
}
_MYSQL_UNESCAPE = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r", "0": "\0", "Z": "\x1a", "b": "\b"}


def _mysql_unescape(s: str):
    if s == "\\N":
        return None
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(_MYSQL_UNESCAPE.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _mysql_escape(v) -> str:
    if v is None:
        return "\\N"
    s = str(v)
    return (
        s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r").replace("\0", "\\0")
    )


def read_core_meta(text: str) -> list[dict]:
    db_rows: list[tuple] = []
    by_species: dict[int, list[tuple]] = {}
    order: list[int] = []
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        species_id = _mysql_unescape(cols[1])
        key = _mysql_unescape(cols[2])
        value = _mysql_unescape(cols[3])
        if species_id is None:
            db_rows.append((key, value))
        else:
            sid = int(species_id)
            if sid not in by_species:
                by_species[sid] = []
                order.append(sid)
            by_species[sid].append((key, value))
    if not order:
        order = [1]
        by_species[1] = []
    records = []
    for sid in order:
        pairs = db_rows + by_species[sid]
        counts: dict[str, int] = {}
        for k, _ in pairs:
            counts[k] = counts.get(k, 0) + 1
        rec: dict = {"species_id": sid}
        for k, v in pairs:
            if k in _META_MULTI or counts[k] > 1:
                rec.setdefault(k, []).append(v)
            else:
                rec[k] = v
        records.append(rec)
    return records


def write_core_meta(records: list[dict]) -> str:
    lines = []
    meta_id = 0
    written_db_level = set()
    for rec in records:
        sid = rec.get("species_id", 1)
        for k, v in rec.items():
            if k == "species_id":
                continue
            values = v if isinstance(v, list) else [v]
            if k in _META_DB_LEVEL:
                if k in written_db_level:
                    continue
                written_db_level.add(k)
                row_sid = None
            else:
                row_sid = sid
            for val in values:
                meta_id += 1
                lines.append("\t".join([str(meta_id), _mysql_escape(row_sid), _mysql_escape(k), _mysql_escape(val)]))
    return "\n".join(lines) + "\n"


_META_KEY_RE = re.compile(r"^(schema_type|schema_version|patch|[a-z_]+\.[a-z_.]+|[a-z_]+)$")


def detect_core_meta(text: str, filename: str = "") -> float:
    lines = [l for l in text.split("\n")[:500] if l.strip()]
    if not lines:
        return 0.0
    good = 0
    keys = set()
    patch_rows = 0
    for l in lines:
        c = l.split("\t")
        if len(c) == 4 and c[0].isdigit() and (c[1].isdigit() or c[1] == "\\N") and _META_KEY_RE.match(c[2]):
            good += 1
            keys.add(c[2])
            if c[2] == "patch" and c[3].startswith("patch_"):
                patch_rows += 1
    if good < len(lines) * 0.9:
        return 0.0
    score = 0.6
    if patch_rows or keys & {"schema_type", "schema_version", "species.production_name", "assembly.default", "assembly.name"}:
        score = 0.9
    if filename.endswith(("meta.txt", "meta.txt.gz")):
        score = max(score, 0.95)
    return score


# ------------------------------------------ species_<Division>.txt list file

_SPECIES_LIST_INT = {"taxonomy_id", "species_id"}


def read_species_list(text: str) -> list[dict]:
    header = None
    records = []
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        cols = line.split("\t")
        if header is None:
            header = cols
            while header and header[-1] == "":
                header.pop()
            continue
        rec = {}
        for i, h in enumerate(header):
            v = cols[i] if i < len(cols) else ""
            if h in _SPECIES_LIST_INT and v.isdigit():
                rec[h] = int(v)
            else:
                rec[h] = v
        records.append(rec)
    return records


_SPECIES_LIST_COLUMNS = [
    "#name", "species", "division", "taxonomy_id", "assembly", "assembly_accession", "genebuild",
    "variation", "microarray", "pan_compara", "peptide_compara", "genome_alignments",
    "other_alignments", "core_db", "species_id",
]


def write_species_list(records: list[dict]) -> str:
    cols = list(_SPECIES_LIST_COLUMNS)
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    out = ["\t".join(cols)]
    for r in records:
        # Ensembl's file ends every data row with a tab (an empty last column).
        out.append("\t".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + "\t")
    return "\n".join(out) + "\n"


def detect_species_list(text: str, filename: str = "") -> float:
    first = _first_line(text)
    if first.startswith("#name\tspecies\tdivision\ttaxonomy_id"):
        return 0.99
    if re.search(r"species_Ensembl\w*\.txt$", filename or ""):
        return 0.7
    return 0.0


# ------------------------------------------------ FASTA DNA header lines

_FASTA_TYPE_RE = re.compile(r"^([A-Za-z_]+):([A-Za-z_]+)$")


def _parse_header(line: str) -> dict:
    body = line[1:] if line.startswith(">") else line
    tokens = body.split(" ")
    rec: dict = {"id": tokens[0]}
    if len(tokens) < 3:
        return rec
    m = _FASTA_TYPE_RE.match(tokens[1])
    if not m:
        return rec
    seq_type, cs_name = m.group(1), m.group(2)
    parts = tokens[2].split(":")
    if len(parts) >= 6 and parts[0] == cs_name:
        slice_cs, version, name_parts = parts[0], parts[1], parts[2:-3]
    elif len(parts) >= 5:
        slice_cs, version, name_parts = None, parts[0], parts[1:-3]
    else:
        return rec
    try:
        start, end, strand = int(parts[-3]), int(parts[-2]), int(parts[-1])
    except ValueError:
        return rec
    rec["sequence_type"] = seq_type
    rec["coord_system_name"] = cs_name
    if slice_cs is not None:
        rec["slice.coord_system_name"] = slice_cs
    rec["slice.version"] = version
    rec["slice.seq_region_name"] = ":".join(name_parts)
    rec["slice.start"] = start
    rec["slice.end"] = end
    rec["slice.strand"] = strand
    if len(tokens) >= 4:
        rec["assembly_exception_type"] = " ".join(tokens[3:])
    return rec


def read_fasta_header(text: str) -> list[dict]:
    out = []
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith(">"):
            out.append(_parse_header(line))
    return out


def _format_header(rec: dict) -> str:
    if "sequence_type" not in rec:
        return ">" + str(rec["id"])
    slice_parts = []
    if "slice.coord_system_name" in rec:
        slice_parts.append(str(rec["slice.coord_system_name"]))
    slice_parts += [
        str(rec.get("slice.version", "")),
        str(rec.get("slice.seq_region_name", rec["id"])),
        str(rec.get("slice.start", "")),
        str(rec.get("slice.end", "")),
        str(rec.get("slice.strand", 1)),
    ]
    tokens = [str(rec["id"]), f"{rec['sequence_type']}:{rec['coord_system_name']}", ":".join(slice_parts)]
    if "assembly_exception_type" in rec:
        tokens.append("" if rec["assembly_exception_type"] is None else str(rec["assembly_exception_type"]))
    return ">" + " ".join(tokens)


def write_fasta_header(records: list[dict]) -> str:
    return "\n".join(_format_header(r) for r in records) + "\n"


def detect_fasta_header(text: str, filename: str = "") -> float:
    first = _first_line(text)
    if not first.startswith(">"):
        return 0.0
    rec = _parse_header(first)
    if "slice.start" in rec:
        return 0.95 if "slice.coord_system_name" in rec else 0.9
    return 0.0


# ------------------------------- ensemblorganisms genome/chromosomes.tsv


def read_chromosomes_tsv(text: str) -> list[dict]:
    out = []
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        cols = line.split("\t")
        rec = {"name": cols[0]}
        if len(cols) > 1:
            rec["length"] = int(cols[1]) if cols[1].strip().isdigit() else cols[1]
        out.append(rec)
    return out


def write_chromosomes_tsv(records: list[dict]) -> str:
    return "".join(f"{r['name']}\t{r.get('length', '')}\n" for r in records)


def detect_chromosomes_tsv(text: str, filename: str = "") -> float:
    lines = [l for l in text.split("\n")[:200] if l.strip()]
    if not lines:
        return 0.0
    ok = all(len(l.split("\t")) == 2 and l.split("\t")[1].strip().isdigit() for l in lines)
    if not ok:
        return 0.0
    if re.search(r"chromosomes[^/]*\.tsv(\.gz)?$", filename or ""):
        return 0.9
    return 0.2  # Same shape as a UCSC chrom.sizes file.


# ----------------------------- new site: genome explain/details/search/genomeid


def read_web_genome(text: str) -> list[dict]:
    d = _load_json(text)
    if isinstance(d, dict) and isinstance(d.get("matches"), list):
        items = d["matches"]
    elif isinstance(d, list):
        items = d
    else:
        items = [d]
    return [_flatten(o) for o in items if isinstance(o, dict)]


def write_web_genome(records: list[dict]) -> str:
    objs = [_unflatten(r) for r in records]
    if len(objs) == 1:
        return _dump(objs[0])
    return _dump({"matches": objs})


def detect_web_genome(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and isinstance(d.get("matches"), list) and d["matches"]:
        d = d["matches"][0]
    if isinstance(d, dict) and "genome_tag" in d and ("genome_id" in d or "genome_uuid" in d):
        return 0.95
    return 0.0


# ------------------------------------- new site: karyotype / top-regions


def read_web_karyotype(text: str) -> list[dict]:
    d = _load_json(text)
    return [dict(r) for r in d or [] if isinstance(r, dict)] if isinstance(d, list) else []


def write_web_karyotype(records: list[dict]) -> str:
    return _dump(records)


def detect_web_karyotype(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if _is_list_of_dicts_with(d, {"name", "type", "length", "is_circular"}):
        return 0.95
    return 0.0


# --------------------------------------------------- new site: genome stats


def read_web_genome_stats(text: str) -> list[dict]:
    d = _load_json(text)
    if not isinstance(d, dict):
        return []
    return [_flatten(d)]


def write_web_genome_stats(records: list[dict]) -> str:
    return _dump(_unflatten(records[0]) if records else {})


def detect_web_genome_stats(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and isinstance(d.get("genome_stats"), dict):
        return 0.95
    return 0.0


# ------------------------------------------------- new site: ftplinks


def read_web_ftplinks(text: str) -> list[dict]:
    d = _load_json(text)
    return [dict(r) for r in d if isinstance(r, dict)] if isinstance(d, list) else []


def write_web_ftplinks(records: list[dict]) -> str:
    return _dump(records)


def detect_web_ftplinks(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if _is_list_of_dicts_with(d, {"dataset", "url"}) and all(len(r) == 2 for r in d):
        return 0.9
    return 0.0


# ------------------------------------ ensemblorganisms FTP species.json

_SP = "species.{species}"
_AS = "species.{species}.assemblies.{accession}"


def read_species_json(text: str) -> list[dict]:
    d = _load_json(text)
    if not isinstance(d, dict) or not isinstance(d.get("species"), dict):
        return []
    top = {k: v for k, v in d.items() if k != "species"}
    out = []
    for sp_key, sp in d["species"].items():
        sp_fields = {f"{_SP}.{k}": v for k, v in sp.items() if k != "assemblies"}
        assemblies = sp.get("assemblies") or {}
        if not assemblies:
            out.append({**top, _SP: sp_key, **sp_fields})
            continue
        for acc, asm in assemblies.items():
            rec = {**top, _SP: sp_key, **sp_fields, _AS: acc}
            for k, v in asm.items():
                rec[f"{_AS}.{k}"] = v
            out.append(rec)
    return out


def write_species_json(records: list[dict]) -> str:
    top: dict = {}
    species: dict = {}
    for r in records:
        sp_key = r[_SP]
        sp = species.setdefault(sp_key, {})
        acc = r.get(_AS)
        for k, v in r.items():
            if k in (_SP, _AS):
                continue
            if k.startswith(_AS + "."):
                if acc is not None:
                    sp.setdefault("assemblies", {}).setdefault(acc, {})[k[len(_AS) + 1:]] = v
            elif k.startswith(_SP + "."):
                sp[k[len(_SP) + 1:]] = v
            else:
                top[k] = v
        if acc is not None:
            sp.setdefault("assemblies", {}).setdefault(acc, {})
    # Keep "assemblies" last within each species, as in the Ensembl file.
    for sp in species.values():
        if "assemblies" in sp:
            sp["assemblies"] = sp.pop("assemblies")
    return _dump({**top, "species": species})


def detect_species_json(text: str, filename: str = "") -> float:
    d = _load_json(text)
    if isinstance(d, dict) and isinstance(d.get("species"), dict):
        first = next(iter(d["species"].values()), None)
        if isinstance(first, dict) and "assemblies" in first:
            return 0.95
    return 0.0


# ----------------------------------------------------------------- registry

FORMATS = [
    Format(
        id="ensembl_rest_info_assembly",
        source=SOURCE,
        description="Ensembl REST GET /info/assembly/:species (assembly-level fields; top_level_region rows are the ensembl_rest_toplevel_region format)",
        read=read_rest_info_assembly,
        write=write_rest_info_assembly,
        detect=detect_rest_info_assembly,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_rest_toplevel_region",
        source=SOURCE,
        description="Ensembl REST GET /info/assembly/:species top_level_region rows, one record per toplevel sequence (with synonyms when synonyms=1)",
        read=read_rest_toplevel_region,
        write=write_rest_toplevel_region,
        detect=detect_rest_toplevel_region,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_rest_info_assembly_region",
        source=SOURCE,
        description="Ensembl REST GET /info/assembly/:species/:region_name (one toplevel sequence; the region name is only in the URL)",
        read=read_rest_info_assembly_region,
        write=write_rest_info_assembly_region,
        detect=detect_rest_info_assembly_region,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_rest_info_genomes",
        source=SOURCE,
        description="Ensembl REST GET /info/genomes/:genome_name (also /info/genomes/assembly/:accession), legacy metadata database record",
        read=read_rest_info_genomes,
        write=write_rest_info_genomes,
        detect=detect_rest_info_genomes,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_core_meta",
        source=SOURCE,
        description="Ensembl core database meta table, MySQL dump meta.txt (meta_id, species_id, meta_key, meta_value); one record per species_id",
        read=read_core_meta,
        write=write_core_meta,
        detect=detect_core_meta,
        extensions=(".txt",),
    ),
    Format(
        id="ensembl_species_list",
        source=SOURCE,
        description="Ensembl release species list species_<Division>.txt (one row per genome)",
        read=read_species_list,
        write=write_species_list,
        detect=detect_species_list,
        extensions=(".txt",),
    ),
    Format(
        id="ensembl_fasta_header",
        source=SOURCE,
        description="Ensembl genomic FASTA header lines (release FTP '>1 dna:chromosome chromosome:GRCh38:1:1:248956422:1 REF' and ensemblorganisms '>1 unmasked:chromosome GRCh38:1:1:248956422:1'); one record per sequence",
        read=read_fasta_header,
        write=write_fasta_header,
        detect=detect_fasta_header,
        extensions=(".fa", ".fasta", ".txt"),
    ),
    Format(
        id="ensembl_chromosomes_tsv",
        source=SOURCE,
        description="ensemblorganisms FTP genome/chromosomes.tsv(.gz): name<TAB>length, no header",
        read=read_chromosomes_tsv,
        write=write_chromosomes_tsv,
        detect=detect_chromosomes_tsv,
        extensions=(".tsv",),
    ),
    Format(
        id="ensembl_web_genome",
        source=SOURCE,
        description="New Ensembl metadata API genome record (/api/metadata/genome/{id}/details or /explain, /api/search/genomes matches, /api/metadata/genomeid); nested objects flattened with '.'",
        read=read_web_genome,
        write=write_web_genome,
        detect=detect_web_genome,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_web_karyotype",
        source=SOURCE,
        description="New Ensembl metadata API /api/metadata/genome/{id}/karyotype (or /top-regions), one record per region",
        read=read_web_karyotype,
        write=write_web_karyotype,
        detect=detect_web_karyotype,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_web_genome_stats",
        source=SOURCE,
        description="New Ensembl metadata API /api/metadata/genome/{id}/stats; nested objects flattened with '.'",
        read=read_web_genome_stats,
        write=write_web_genome_stats,
        detect=detect_web_genome_stats,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_web_ftplinks",
        source=SOURCE,
        description="New Ensembl metadata API /api/metadata/genome/{id}/ftplinks, one record per dataset link",
        read=read_web_ftplinks,
        write=write_web_ftplinks,
        detect=detect_web_ftplinks,
        extensions=(".json",),
    ),
    Format(
        id="ensembl_ftp_species_json",
        source=SOURCE,
        description="ensemblorganisms FTP species.json (new Ensembl file catalog); one record per species x assembly accession",
        read=read_species_json,
        write=write_species_json,
        detect=detect_species_json,
        extensions=(".json",),
    ),
]
