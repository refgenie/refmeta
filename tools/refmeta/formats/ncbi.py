"""NCBI assembly metadata formats.

Covers the NCBI Datasets v2 genome reports (JSON from the REST API, or JSON
Lines from a downloaded data package) and the plain-text files on the NCBI
genomes FTP site. See sources/ncbi/README.md for where each format comes from
and sources/ncbi/fields.json for every field.

Native records are flat dicts:
- Datasets JSON: nested objects are flattened to dotted paths
  ("assembly_info.assembly_name"); arrays stay as JSON values at their path.
  camelCase keys (data-package JSONL) are converted to the snake_case keys
  the REST API uses, so both spellings read to the same record.
- FTP tables: keys are the column names exactly as written in the file.
"""
from __future__ import annotations

import json
import re
from typing import Any

from . import Format

SOURCE = "ncbi"

# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

_CAMEL = re.compile(r"(?<=[a-z0-9])([A-Z])")


def _snake(key: str) -> str:
    """camelCase -> snake_case; snake_case keys pass through unchanged."""
    return _CAMEL.sub(r"_\1", key).lower() if any(c.isupper() for c in key) else key


def _snake_keys(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {_snake(k): _snake_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_snake_keys(v) for v in obj]
    return obj


def _flatten(obj: dict, prefix: str = "") -> dict:
    out: dict = {}
    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
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


def _json_items(text: str) -> list:
    """Return the report objects in a Datasets API page, a single report,
    a JSON array of reports, or JSON Lines (one report per line)."""
    text = text.lstrip("﻿").strip()
    if not text:
        return []
    try:
        doc = json.loads(text)
    except ValueError:
        items = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))
        return items
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        if "reports" in doc:
            return list(doc.get("reports") or [])
        if not doc:  # the API answers {} when nothing matches
            return []
        return [doc]
    return []


def _head(text: str, n: int = 20000) -> str:
    return text[:n].lstrip("﻿")


def _lines(text: str) -> list[str]:
    # splitlines() also drops the CR of the CRLF endings the FTP files use
    return text.lstrip("﻿").splitlines()


# --------------------------------------------------------------------------
# Datasets v2 genome dataset_report (assembly level)
# --------------------------------------------------------------------------


def read_datasets_assembly_report(text: str) -> list[dict]:
    return [_flatten(_snake_keys(item)) for item in _json_items(text) if isinstance(item, dict)]


def write_datasets_assembly_report(records: list[dict]) -> str:
    reports = [_unflatten(r) for r in records]
    return json.dumps({"reports": reports, "total_count": len(reports)}, indent=2) + "\n"


def detect_datasets_assembly_report(text: str, filename: str = "") -> float:
    head = _head(text)
    if not head.lstrip().startswith(("{", "[")):
        return 0.0
    if '"assembly_info"' in head or '"assemblyInfo"' in head:
        return 0.95
    if filename.endswith("assembly_data_report.jsonl") or filename.endswith("dataset_report.json"):
        return 0.6
    return 0.0


# --------------------------------------------------------------------------
# Datasets v2 genome sequence_reports (one record per sequence)
# --------------------------------------------------------------------------


def read_datasets_sequence_report(text: str) -> list[dict]:
    return [_flatten(_snake_keys(item)) for item in _json_items(text) if isinstance(item, dict)]


def write_datasets_sequence_report(records: list[dict]) -> str:
    rows = [_unflatten(r) for r in records]
    return json.dumps({"reports": rows, "total_count": len(rows)}, indent=2) + "\n"


def detect_datasets_sequence_report(text: str, filename: str = "") -> float:
    head = _head(text)
    if not head.lstrip().startswith(("{", "[")):
        return 0.0
    if '"assembly_info"' in head or '"assemblyInfo"' in head:
        return 0.0
    markers = ('"ucsc_style_name"', '"ucscStyleName"', '"assembly_unit"', '"assemblyUnit"',
               '"assigned_molecule_location_type"', '"assignedMoleculeLocationType"')
    if sum(m in head for m in markers) >= 2:
        return 0.95
    if filename.endswith("sequence_report.jsonl") or filename.endswith("sequence_reports.json"):
        return 0.6
    return 0.0


# --------------------------------------------------------------------------
# FTP *_assembly_report.txt: header (assembly level) and table (sequence level)
# --------------------------------------------------------------------------

AR_COLUMNS = [
    "Sequence-Name", "Sequence-Role", "Assigned-Molecule", "Assigned-Molecule-Location/Type",
    "GenBank-Accn", "Relationship", "RefSeq-Accn", "Assembly-Unit", "Sequence-Length",
    "UCSC-style-name",
]
_AR_INT_COLUMNS = {"Sequence-Length"}
_AR_HEADER_KEY = re.compile(r"^# ([A-Za-z][A-Za-z0-9 ()-]*):[ \t]*(.*)$")
_AR_UNIT_COLS = ["GenBank Unit Accession", "RefSeq Unit Accession", "Assembly-Unit name"]
_AR_BOILERPLATE = [
    "#",
    "# Ordered by chromosome/plasmid; the chromosomes/plasmids are followed by",
    "# unlocalized scaffolds.",
    "# Unplaced scaffolds are listed at the end.",
    "# RefSeq is equal or derived from GenBank object.",
    "#",
]


def _ar_value(key: str, raw: str):
    raw = raw.rstrip("\r")
    if key == "Taxid" and raw.strip().isdigit():
        return int(raw.strip())
    if key == "Synonyms":
        # Written as "hg38<TAB>"; tab-separated list (separator inferred, see fields.json)
        return [s for s in raw.split("\t") if s.strip()]
    return raw.strip()


def _ar_split(text: str):
    """Return (header_record, column_names, row_lines)."""
    header: dict = {}
    columns: list[str] | None = None
    rows: list[str] = []
    unit_mode = None  # "names" | "table"
    unit_cols: list[str] | None = None
    for line in _lines(text):
        if not line.strip():
            continue
        if line.startswith("## "):
            body = line[3:]
            if body.rstrip() == "Assembly-Unit names:":
                unit_mode = "names"
                header["Assembly-Unit names"] = []
            elif body.rstrip() == "Assembly-Units:":
                unit_mode = "table"
                header["Assembly-Units"] = []
            elif unit_mode == "names":
                header["Assembly-Unit names"].append(body.strip())
            elif unit_mode == "table":
                cells = body.split("\t")
                if unit_cols is None:
                    unit_cols = [c.strip() for c in cells]
                else:
                    header["Assembly-Units"].append(
                        {c: (cells[i].strip() if i < len(cells) else "") for i, c in enumerate(unit_cols)}
                    )
            continue
        if line.startswith("#"):
            unit_mode = None
            if line.startswith("# Sequence-Name"):
                columns = [c.strip() for c in line[2:].split("\t")]
                continue
            m = _AR_HEADER_KEY.match(line)
            if m and columns is None:
                header[m.group(1)] = _ar_value(m.group(1), m.group(2))
            continue
        rows.append(line)
    return header, columns, rows


def read_assembly_report_header(text: str) -> list[dict]:
    header, _cols, _rows = _ar_split(text)
    return [header] if header else []


def write_assembly_report_header(records: list[dict]) -> str:
    chunks = []
    for rec in records:
        out = []
        for k, v in rec.items():
            if k in ("Assembly-Unit names", "Assembly-Units"):
                continue
            if k == "Synonyms":
                v = "".join(f"{s}\t" for s in (v or []))
            label = f"{k}:"
            out.append(f"# {label.ljust(max(16, len(label) + 1))}{v}")
        if "Assembly-Units" in rec:
            out.append("#")
            out.append("## Assembly-Units:")
            out.append("## " + "\t".join(_AR_UNIT_COLS))
            for u in rec["Assembly-Units"]:
                out.append("## " + "\t".join(str(u.get(c, "")) for c in _AR_UNIT_COLS))
        if "Assembly-Unit names" in rec:
            out.append("#")
            out.append("## Assembly-Unit names:")
            out.extend(f"## {n}" for n in rec["Assembly-Unit names"])
        out.extend(_AR_BOILERPLATE)
        chunks.append("\n".join(out) + "\n")
    return "".join(chunks)


def read_assembly_report_sequences(text: str) -> list[dict]:
    _header, columns, rows = _ar_split(text)
    columns = columns or AR_COLUMNS
    out = []
    for line in rows:
        cells = line.split("\t")
        rec = {}
        for i, col in enumerate(columns):
            v = cells[i].strip() if i < len(cells) else ""
            if col in _AR_INT_COLUMNS and v.isdigit():
                rec[col] = int(v)
            else:
                rec[col] = v
        out.append(rec)
    return out


def write_assembly_report_sequences(records: list[dict]) -> str:
    cols = list(AR_COLUMNS)
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    lines = ["# " + "\t".join(cols)]
    for r in records:
        lines.append("\t".join("na" if r.get(c) is None else str(r.get(c)) for c in cols))
    return "\n".join(lines) + "\n"


def _is_assembly_report(head: str) -> bool:
    return "# Sequence-Name\tSequence-Role" in head or (
        head.startswith("# Assembly name:") and "RefSeq assembly accession" in head
    )


def detect_assembly_report_header(text: str, filename: str = "") -> float:
    head = _head(text)
    if head.startswith("# Assembly name:"):
        return 0.9
    if _is_assembly_report(head):
        return 0.7
    return 0.0


def detect_assembly_report_sequences(text: str, filename: str = "") -> float:
    head = _head(text)
    if "# Sequence-Name\tSequence-Role" in head:
        # Same file as the header format; prefer the header format when both are present.
        return 0.85 if head.startswith("# Assembly name:") else 0.95
    return 0.0


# --------------------------------------------------------------------------
# FTP assembly_summary_{refseq,genbank}[_historical].txt
# --------------------------------------------------------------------------

AS_COLUMNS = [
    "assembly_accession", "bioproject", "biosample", "wgs_master", "refseq_category", "taxid",
    "species_taxid", "organism_name", "infraspecific_name", "isolate", "version_status",
    "assembly_level", "release_type", "genome_rep", "seq_rel_date", "asm_name", "asm_submitter",
    "gbrs_paired_asm", "paired_asm_comp", "ftp_path", "excluded_from_refseq",
    "relation_to_type_material", "asm_not_live_date", "assembly_type", "group", "genome_size",
    "genome_size_ungapped", "gc_percent", "replicon_count", "scaffold_count", "contig_count",
    "annotation_provider", "annotation_name", "annotation_date", "total_gene_count",
    "protein_coding_gene_count", "non_coding_gene_count", "pubmed_id",
]
_AS_INT = {
    "taxid", "species_taxid", "genome_size", "genome_size_ungapped", "replicon_count",
    "scaffold_count", "contig_count", "total_gene_count", "protein_coding_gene_count",
    "non_coding_gene_count",
}
_AS_FLOAT = {"gc_percent"}
_AS_COMMENT = ("##  See ftp://ftp.ncbi.nlm.nih.gov/genomes/README_assembly_summary.txt for a "
               "description of the columns in this file.")


def _as_value(col: str, v: str):
    if col in _AS_INT and v.isdigit():
        return int(v)
    if col in _AS_FLOAT:
        try:
            return float(v)
        except ValueError:
            return v
    return v


def read_assembly_summary(text: str) -> list[dict]:
    columns = None
    out = []
    for line in _lines(text):
        if not line.strip():
            continue
        if line.startswith("##"):
            continue
        if line.startswith("#"):
            columns = [c.strip() for c in line[1:].split("\t")]
            continue
        cols = columns or AS_COLUMNS
        cells = line.split("\t")
        out.append({c: _as_value(c, cells[i] if i < len(cells) else "") for i, c in enumerate(cols)})
    return out


def _as_fmt(col: str, v) -> str:
    if v is None:
        return "na"
    if col in _AS_FLOAT and isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def write_assembly_summary(records: list[dict]) -> str:
    cols = [c for c in AS_COLUMNS if any(c in r for r in records)] or list(AS_COLUMNS)
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    lines = [_AS_COMMENT, "#" + "\t".join(cols)]
    for r in records:
        lines.append("\t".join(_as_fmt(c, r.get(c)) for c in cols))
    return "\n".join(lines) + "\n"


def detect_assembly_summary(text: str, filename: str = "") -> float:
    head = _head(text, 4000)
    if "#assembly_accession\tbioproject" in head:
        return 0.95
    return 0.0


# --------------------------------------------------------------------------
# FTP md5checksums.txt (one record per file)
# --------------------------------------------------------------------------

_MD5_LINE = re.compile(r"^([0-9a-fA-F]{32})\s+(\S.*)$")


def read_md5checksums(text: str) -> list[dict]:
    out = []
    for line in _lines(text):
        m = _MD5_LINE.match(line.strip())
        if m:
            out.append({"file": m.group(2), "md5sum": m.group(1)})
    return out


def write_md5checksums(records: list[dict]) -> str:
    return "".join(f"{r['md5sum']}  {r['file']}\n" for r in records)


def detect_md5checksums(text: str, filename: str = "") -> float:
    lines = [ln for ln in _lines(_head(text, 4000)) if ln.strip()][:20]
    if not lines or not all(_MD5_LINE.match(ln.strip()) for ln in lines):
        return 0.0
    if "md5checksums" in filename:
        return 0.95
    # Plain md5sum output looks the same; NCBI writes every path as "./<name>".
    return 0.9 if all(ln.split(None, 1)[1].startswith("./") for ln in lines) else 0.4


# --------------------------------------------------------------------------
# FTP uncompressed_checksums.txt (one record per file)
# --------------------------------------------------------------------------

UC_COLUMNS = ["file", "md5sum", "crc32", "size"]


def read_uncompressed_checksums(text: str) -> list[dict]:
    columns = UC_COLUMNS
    out = []
    for line in _lines(text):
        if not line.strip():
            continue
        if line.startswith("#"):
            columns = [c.strip() for c in line[1:].split("\t")]
            continue
        cells = line.split("\t")
        rec = {}
        for i, c in enumerate(columns):
            v = cells[i].strip() if i < len(cells) else ""
            rec[c] = int(v) if c == "size" and v.isdigit() else v
        out.append(rec)
    return out


def write_uncompressed_checksums(records: list[dict]) -> str:
    lines = ["#" + "\t".join(UC_COLUMNS)]
    for r in records:
        lines.append("\t".join("" if r.get(c) is None else str(r.get(c)) for c in UC_COLUMNS))
    return "\n".join(lines) + "\n"


def detect_uncompressed_checksums(text: str, filename: str = "") -> float:
    return 0.95 if _head(text, 200).startswith("#file\tmd5sum\tcrc32\tsize") else 0.0


# --------------------------------------------------------------------------
# GRCh38 analysis-set FASTA definition lines (seqs_for_alignment_pipelines)
# --------------------------------------------------------------------------

_TAG = re.compile(r"^([A-Za-z][A-Za-z0-9]):(.*)$")
_DEFLINE_INT = {"LN"}


def read_analysis_set_defline(text: str) -> list[dict]:
    """Read '>' lines from an analysis-set FASTA (sequence lines are skipped)."""
    out = []
    for line in _lines(text):
        if not line.startswith(">"):
            continue
        tokens = line[1:].split()
        if not tokens:
            continue
        rec: dict = {"name": tokens[0]}
        last = None
        for tok in tokens[1:]:
            m = _TAG.match(tok)
            if m:
                last = m.group(1)
                val = m.group(2)
                rec[last] = int(val) if last in _DEFLINE_INT and val.isdigit() else val
            elif last is not None:  # untagged word: continuation of the previous value
                rec[last] = f"{rec[last]} {tok}"
        out.append(rec)
    return out


def write_analysis_set_defline(records: list[dict]) -> str:
    """Write definition lines only (no sequence), two spaces between fields as NCBI does."""
    lines = []
    for r in records:
        parts = [str(r.get("name", ""))]
        parts += [f"{k}:{v}" for k, v in r.items() if k != "name" and v is not None]
        lines.append(">" + "  ".join(parts))
    return "\n".join(lines) + "\n"


def detect_analysis_set_defline(text: str, filename: str = "") -> float:
    first = next((ln for ln in _lines(_head(text, 2000)) if ln.strip()), "")
    if first.startswith(">") and " AC:" in first and " LN:" in first:
        return 0.9 if " M5:" in first else 0.7
    return 0.0


# --------------------------------------------------------------------------

FORMATS = [
    Format(
        id="ncbi_datasets_assembly_report",
        source=SOURCE,
        description="NCBI Datasets v2 genome assembly data report (REST dataset_report JSON or "
        "package assembly_data_report.jsonl); one record per assembly",
        read=read_datasets_assembly_report,
        write=write_datasets_assembly_report,
        detect=detect_datasets_assembly_report,
        extensions=(".json", ".jsonl"),
    ),
    Format(
        id="ncbi_datasets_sequence_report",
        source=SOURCE,
        description="NCBI Datasets v2 genome sequence report (REST sequence_reports JSON or "
        "package sequence_report.jsonl); one record per sequence",
        read=read_datasets_sequence_report,
        write=write_datasets_sequence_report,
        detect=detect_datasets_sequence_report,
        extensions=(".json", ".jsonl"),
    ),
    Format(
        id="ncbi_assembly_report_header",
        source=SOURCE,
        description="NCBI FTP *_assembly_report.txt header comment lines; one record per file "
        "(assembly level)",
        read=read_assembly_report_header,
        write=write_assembly_report_header,
        detect=detect_assembly_report_header,
        extensions=(".txt",),
    ),
    Format(
        id="ncbi_assembly_report_sequences",
        source=SOURCE,
        description="NCBI FTP *_assembly_report.txt sequence table; one record per sequence "
        "(the name map across GenBank, RefSeq, submitter and UCSC-style names)",
        read=read_assembly_report_sequences,
        write=write_assembly_report_sequences,
        detect=detect_assembly_report_sequences,
        extensions=(".txt",),
    ),
    Format(
        id="ncbi_assembly_summary",
        source=SOURCE,
        description="NCBI FTP assembly_summary_refseq.txt / assembly_summary_genbank.txt "
        "(and _historical); one record per assembly",
        read=read_assembly_summary,
        write=write_assembly_summary,
        detect=detect_assembly_summary,
        extensions=(".txt",),
    ),
    Format(
        id="ncbi_md5checksums",
        source=SOURCE,
        description="NCBI FTP md5checksums.txt; one record per file in an assembly directory",
        read=read_md5checksums,
        write=write_md5checksums,
        detect=detect_md5checksums,
        extensions=(".txt",),
    ),
    Format(
        id="ncbi_uncompressed_checksums",
        source=SOURCE,
        description="NCBI FTP uncompressed_checksums.txt; md5, crc32 and size of each file "
        "after decompression",
        read=read_uncompressed_checksums,
        write=write_uncompressed_checksums,
        detect=detect_uncompressed_checksums,
        extensions=(".txt",),
    ),
    Format(
        id="ncbi_analysis_set_defline",
        source=SOURCE,
        description="FASTA definition lines of NCBI's GRCh38 analysis sets "
        "(seqs_for_alignment_pipelines.ucsc_ids); one record per sequence",
        read=read_analysis_set_defline,
        write=write_analysis_set_defline,
        detect=detect_analysis_set_defline,
        extensions=(".fna", ".fa", ".fasta", ".txt"),
    ),
]
