"""Bioconductor genome metadata formats.

Covers the files Bioconductor packages ship or serve that describe reference
genomes (see sources/bioconductor/README.md):

- Seqinfo tables (Seqinfo package; as.data.frame(Seqinfo) columns)
- GenomeInfoDb cached chrom info tables (chrominfo_db/UCSC/*.tab, NCBI/*.tab)
- GenomeInfoDb seqlevelsStyle naming tables (extdata/dataFiles/<Organism>.txt)
- GenomeInfoDb genomeMappingTbl.csv (UCSC <-> Ensembl build table)
- GenomeInfoDb registration files (registered/NCBI_assemblies/*.R and
  registered/UCSC_genomes/*.R), parsed for their simple assignment pattern
- BSgenomeForge seed files and BSgenome package DESCRIPTION files (DCF)
- AnnotationHub records (JSON from annotationhub.bioconductor.org/ahid/<id>)
  and AnnotationHub contributor metadata.csv files

Standard library only. Text in, text out. The R parser below evaluates only
literals and a handful of vector builders (c, list, paste0, paste, character,
as.character, as.roman, a:b). It never runs R code; function definitions are
kept as raw source text or skipped.
"""
from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Callable

from . import Format

SOURCE = "bioconductor"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line
    return ""


def _na(v: str | None) -> bool:
    return v is None or v in ("NA", "")


def _to_int(v: str | None):
    if _na(v):
        return None
    try:
        return int(v)
    except ValueError:
        return v


def _to_rbool(v: str | None):
    """R logical as written by write.table (TRUE/FALSE) or abbreviated (T/F)."""
    if _na(v):
        return None
    u = v.strip().upper()
    if u in ("TRUE", "T"):
        return True
    if u in ("FALSE", "F"):
        return False
    return v


def _to_str(v: str | None):
    return None if _na(v) else v


def _from_bool(v, short: bool = False) -> str:
    if v is None:
        return "NA"
    if isinstance(v, bool):
        if short:
            return "T" if v else "F"
        return "TRUE" if v else "FALSE"
    return str(v)


def _from_val(v) -> str:
    if v is None:
        return "NA"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return str(v)


# ---------------------------------------------------------------------------
# delimited tables (TSV/CSV), one record per row
# ---------------------------------------------------------------------------

def _sniff_delim(text: str) -> str:
    head = _first_line(text)
    return "\t" if head.count("\t") >= head.count(",") else ","


def _read_table(text: str, converters: dict[str, Callable], delim: str | None = None,
                default: Callable = _to_str) -> list[dict]:
    delim = delim or _sniff_delim(text)
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim) if r and any(c.strip() for c in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    out = []
    for row in rows[1:]:
        # R write.table() with row.names=TRUE writes one fewer header cell.
        if len(row) == len(header) + 1:
            row = row[1:]
        rec = {}
        for k, v in zip(header, row):
            conv = converters.get(k, default)
            rec[k] = conv(v)
        out.append(rec)
    return out


def _write_table(records: list[dict], columns: list[str], delim: str,
                 formatter: Callable[[str, Any], str]) -> str:
    cols = list(columns)
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    cols = [c for c in cols if any(c in r for r in records)] or list(columns)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delim, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(cols)
    for r in records:
        w.writerow([formatter(c, r.get(c)) for c in cols])
    return buf.getvalue()


# --- Seqinfo -----------------------------------------------------------------

SEQINFO_COLS = ["seqnames", "seqlengths", "isCircular", "genome"]
_SEQINFO_CONV = {"seqnames": _to_str, "seqlengths": _to_int, "isCircular": _to_rbool, "genome": _to_str}


def _read_seqinfo(text: str) -> list[dict]:
    lines = text.splitlines()
    if any(l.lstrip().startswith("Seqinfo object with") for l in lines[:3]):
        return _read_seqinfo_show(lines)
    recs = _read_table(text, _SEQINFO_CONV)
    # also accept the 'seqlevels' or 'is_circular' spellings that as(df, "Seqinfo") accepts
    fixed = []
    for r in recs:
        if "seqlevels" in r and "seqnames" not in r:
            r["seqnames"] = r.pop("seqlevels")
        if "is_circular" in r and "isCircular" not in r:
            r["isCircular"] = _to_rbool(r.pop("is_circular"))
        fixed.append(r)
    return fixed


def _read_seqinfo_show(lines: list[str]) -> list[dict]:
    """Parse the text that show(<Seqinfo>) prints in an R console."""
    out = []
    header = None
    for line in lines:
        s = line.strip()
        if not s or s.startswith("Seqinfo object with"):
            continue
        parts = s.split()
        if header is None:
            if parts[:1] == ["seqnames"]:
                header = parts
            continue
        if parts and parts[0] in ("...", "\u2026"):
            continue  # truncated display
        rec = {}
        for k, v in zip(header, parts):
            rec[k] = _SEQINFO_CONV.get(k, _to_str)(v)
        out.append(rec)
    return out


def _write_seqinfo(records: list[dict]) -> str:
    return _write_table(records, SEQINFO_COLS, "\t", lambda c, v: _from_val(v))


def _detect_seqinfo(text: str, filename: str) -> float:
    head = _first_line(text)
    if head.lstrip().startswith("Seqinfo object with"):
        return 0.95
    cols = re.split(r"[\t,]", head.replace('"', ""))
    cols = [c.strip() for c in cols]
    if "seqlengths" in cols and ("seqnames" in cols or "isCircular" in cols):
        return 0.9
    return 0.0


# --- GenomeInfoDb chrominfo_db/UCSC/<genome>.tab ------------------------------

CHROMINFO_UCSC_COLS = ["chrom", "size", "assembled", "circular"]
_CHROMINFO_UCSC_CONV = {"chrom": _to_str, "size": _to_int, "assembled": _to_rbool, "circular": _to_rbool}


def _read_chrominfo_ucsc(text: str) -> list[dict]:
    return _read_table(text, _CHROMINFO_UCSC_CONV, delim="\t")


def _write_chrominfo_ucsc(records: list[dict]) -> str:
    return _write_table(records, CHROMINFO_UCSC_COLS, "\t", lambda c, v: _from_val(v))


def _detect_chrominfo_ucsc(text: str, filename: str) -> float:
    head = [c.strip() for c in _first_line(text).split("\t")]
    if head[:2] == ["chrom", "size"] and "assembled" in head:
        return 0.95
    return 0.0


# --- GenomeInfoDb chrominfo_db/NCBI/<accession>.tab ---------------------------

CHROMINFO_NCBI_COLS = ["SequenceName", "SequenceRole", "AssignedMolecule", "GenBankAccn",
                       "Relationship", "RefSeqAccn", "AssemblyUnit", "SequenceLength",
                       "UCSCStyleName", "circular"]
_CHROMINFO_NCBI_CONV = {"SequenceLength": _to_int, "circular": _to_rbool}


def _read_chrominfo_ncbi(text: str) -> list[dict]:
    return _read_table(text, _CHROMINFO_NCBI_CONV, delim="\t")


def _write_chrominfo_ncbi(records: list[dict]) -> str:
    return _write_table(records, CHROMINFO_NCBI_COLS, "\t", lambda c, v: _from_val(v))


def _detect_chrominfo_ncbi(text: str, filename: str) -> float:
    head = [c.strip() for c in _first_line(text).split("\t")]
    if head[:2] == ["SequenceName", "SequenceRole"]:
        # NCBI's own assembly_report.txt uses '# Sequence-Name' with dashes; this
        # is GenomeInfoDb's reformatted table.
        return 0.9 if "UCSCStyleName" in head or "circular" in head else 0.6
    return 0.0


# --- GenomeInfoDb extdata/dataFiles/<Organism>.txt (seqlevelsStyle) ------------

_STYLE_BOOL = ("circular", "auto", "sex")


def _read_seqlevels_style(text: str) -> list[dict]:
    conv = {k: _to_rbool for k in _STYLE_BOOL}
    return _read_table(text, conv, delim="\t")


def _write_seqlevels_style(records: list[dict]) -> str:
    def fmt(c, v):
        if c in _STYLE_BOOL:
            return _from_bool(v, short=True)
        return _from_val(v)
    cols = ["circular", "auto", "sex", "NCBI", "UCSC", "dbSNP", "Ensembl"]
    # keep the column order of the first record (files differ, e.g. Drosophila)
    if records:
        cols = list(records[0].keys())
    return _write_table(records, cols, "\t", fmt)


def _detect_seqlevels_style(text: str, filename: str) -> float:
    head = [c.strip() for c in _first_line(text).split("\t")]
    if set(head[:3]) == {"circular", "auto", "sex"}:
        return 0.95
    return 0.0


# --- GenomeInfoDb extdata/dataFiles/genomeMappingTbl.csv -----------------------

GENOME_MAPPING_COLS = ["commonName", "organism", "ensemblID", "origEnsemblVersion",
                       "origEnsemblDate", "ensemblVersion", "ensemblDate", "ucscID",
                       "ucscDate", "releaseName"]
_GENOME_MAPPING_CONV = {"origEnsemblVersion": _to_int, "ensemblVersion": _to_int}


def _read_genome_mapping(text: str) -> list[dict]:
    return _read_table(text, _GENOME_MAPPING_CONV, delim=",")


def _write_genome_mapping(records: list[dict]) -> str:
    return _write_table(records, GENOME_MAPPING_COLS, ",", lambda c, v: _from_val(v))


def _detect_genome_mapping(text: str, filename: str) -> float:
    head = [c.strip().strip('"') for c in _first_line(text).split(",")]
    if "ensemblID" in head and "ucscID" in head:
        return 0.95
    return 0.0


# ---------------------------------------------------------------------------
# A tiny reader for the R registration files in GenomeInfoDb/inst/registered
# ---------------------------------------------------------------------------

class RParseError(ValueError):
    pass


_TOKEN_RE = re.compile(r"""
    (?P<ws>[ \t\r\f]+)
  | (?P<nl>\n)
  | (?P<comment>\#[^\n]*)
  | (?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
  | (?P<bt>`[^`]*`)
  | (?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?L?)
  | (?P<name>[A-Za-z.][A-Za-z0-9._]*)
  | (?P<op><<-|<-|->|:::|::|==|!=|<=|>=|&&|\|\||%[^%\n]*%|[-+*/^!&|<>=~?@$:,;(){}\[\]])
""", re.VERBOSE)


def _tokenize(src: str) -> list[tuple[str, str, int, int]]:
    toks = []
    pos = 0
    n = len(src)
    while pos < n:
        m = _TOKEN_RE.match(src, pos)
        if not m:
            raise RParseError(f"cannot tokenize R source at offset {pos}: {src[pos:pos + 20]!r}")
        kind = m.lastgroup
        if kind not in ("ws", "comment"):
            toks.append((kind, m.group(), m.start(), m.end()))
        pos = m.end()
    return toks


def _unquote(s: str) -> str:
    body = s[1:-1]
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body)


_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _roman(n: int) -> str:
    out = ""
    for v, s in _ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


class _Named:
    """A named R vector/list, kept as ordered (name, value) pairs while building."""

    def __init__(self, items, kind):
        self.items = items  # list of (name|None, value)
        self.kind = kind  # "c" or "list"


def _as_vector(v) -> list:
    if isinstance(v, list):
        return v
    if v is None:
        return []
    return [v]


def _r_str(x) -> str:
    if isinstance(x, bool):
        return "TRUE" if x else "FALSE"
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


class _RParser:
    def __init__(self, src: str):
        self.src = src
        self.toks = _tokenize(src)
        self.i = 0

    # token helpers
    def peek(self, skip_nl=False):
        j = self.i
        while skip_nl and j < len(self.toks) and self.toks[j][0] == "nl":
            j += 1
        return self.toks[j] if j < len(self.toks) else None

    def next(self, skip_nl=False):
        if skip_nl:
            self.skip_nl()
        t = self.toks[self.i]
        self.i += 1
        return t

    def skip_nl(self):
        while self.i < len(self.toks) and self.toks[self.i][0] == "nl":
            self.i += 1

    def expect(self, text, skip_nl=True):
        t = self.next(skip_nl=skip_nl)
        if t[1] != text:
            raise RParseError(f"expected {text!r}, got {t[1]!r}")
        return t

    # statements
    def statements(self):
        """Yield (name, value, raw_source) for each top-level assignment."""
        while True:
            self.skip_nl()
            t = self.peek()
            if t is None:
                return
            if t[0] in ("name", "bt") and self.i + 1 < len(self.toks) and self.toks[self.i + 1][1] in ("<-", "="):
                name = t[1].strip("`")
                self.i += 2
                self.skip_nl()
                start = self.peek()[2]
                if self.peek()[1] == "function":
                    self._skip_function()
                    raw = self.src[start:self.toks[self.i - 1][3]]
                    yield name, None, raw
                    continue
                j0 = self.i
                try:
                    val = self.expr()
                    raw = self.src[start:self.toks[self.i - 1][3]]
                    yield name, val, raw
                except RParseError:
                    self.i = j0
                    self._skip_expr()
                    raw = self.src[start:self.toks[self.i - 1][3]]
                    yield name, _Unparsed(raw), raw
            else:
                self._skip_expr()

    def _skip_balanced(self, open_, close):
        depth = 0
        while self.i < len(self.toks):
            t = self.toks[self.i]
            self.i += 1
            if t[1] == open_:
                depth += 1
            elif t[1] == close:
                depth -= 1
                if depth == 0:
                    return
        raise RParseError("unbalanced brackets")

    def _skip_function(self):
        self.next()  # 'function'
        self.skip_nl()
        self._skip_balanced("(", ")")
        self.skip_nl()
        if self.peek() and self.peek()[1] == "{":
            self._skip_balanced("{", "}")
        else:
            self._skip_expr()

    def _skip_expr(self):
        """Skip to the end of the current top-level expression."""
        depth = 0
        while self.i < len(self.toks):
            t = self.toks[self.i]
            if t[1] in ("(", "{", "["):
                depth += 1
            elif t[1] in (")", "}", "]"):
                depth -= 1
            elif t[0] == "nl" and depth <= 0:
                prev = self.toks[self.i - 1][1] if self.i > 0 else ""
                if prev not in ("<-", "=", "+", "-", "*", "/", ",", "(", "|", "&", "&&", "||", "function"):
                    return
            self.i += 1

    # expressions
    def expr(self):
        left = self.unary()
        t = self.peek()
        if t is not None and t[1] == ":":
            self.next()
            right = self.unary()
            a, b = _scalar_num(left), _scalar_num(right)
            step = 1 if b >= a else -1
            return list(range(a, b + step, step))
        return left

    def unary(self):
        t = self.peek(skip_nl=True)
        if t is not None and t[1] == "-":
            self.next(skip_nl=True)
            v = self.primary()
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return -v
            raise RParseError("unsupported unary minus")
        return self.primary()

    def primary(self):
        t = self.next(skip_nl=True)
        kind, text = t[0], t[1]
        if kind == "str":
            return _unquote(text)
        if kind == "num":
            s = text.rstrip("L")
            return int(s) if re.fullmatch(r"\d+", s) else float(s)
        if text == "(":
            v = self.expr()
            self.expect(")")
            return v
        if kind == "name":
            nxt = self.peek()
            if nxt is not None and nxt[1] == "(":
                return self.call(text)
            if nxt is not None and nxt[1] in ("::", ":::"):
                raise RParseError("namespaced call not supported")
            consts = {"TRUE": True, "T": True, "FALSE": False, "F": False, "NULL": None,
                      "NA": None, "NA_character_": None, "NA_integer_": None}
            if text in consts:
                return consts[text]
            raise RParseError(f"unsupported symbol {text!r}")
        raise RParseError(f"unexpected token {text!r}")

    def args(self):
        self.expect("(", skip_nl=False)
        items = []
        self.skip_nl()
        if self.peek()[1] == ")":
            self.next()
            return items
        while True:
            self.skip_nl()
            name = None
            t = self.peek()
            if t[0] in ("name", "bt", "str") and self.i + 1 < len(self.toks) and self.toks[self.i + 1][1] == "=":
                name = t[1].strip("`") if t[0] != "str" else _unquote(t[1])
                self.i += 2
            items.append((name, self.expr()))
            t = self.next(skip_nl=True)
            if t[1] == ")":
                return items
            if t[1] != ",":
                raise RParseError(f"expected ',' or ')', got {t[1]!r}")

    def call(self, fname):
        items = self.args()
        if fname == "c":
            if any(n is not None for n, _ in items):
                return _Named(items, "c")
            out = []
            for _, v in items:
                if isinstance(v, _Named):
                    raise RParseError("nested named vector")
                out.extend(_as_vector(v))
            if any(isinstance(x, str) for x in out):
                out = [_r_str(x) if x is not None else None for x in out]
            return out
        if fname == "list":
            if any(n is not None for n, _ in items):
                return _Named(items, "list")
            return [_finish(v) for _, v in items]
        if fname in ("paste0", "paste"):
            sep = "" if fname == "paste0" else " "
            vecs = []
            for n, v in items:
                if n == "sep":
                    sep = v
                elif n == "collapse":
                    raise RParseError("collapse not supported")
                else:
                    vecs.append([_r_str(x) for x in _as_vector(v)])
            if not vecs:
                return []
            if any(len(v) == 0 for v in vecs):
                return []
            n = max(len(v) for v in vecs)
            return [sep.join(v[k % len(v)] for v in vecs) for k in range(n)]
        if fname == "character" and len(items) == 1 and items[0][1] == 0:
            return []
        if fname == "as.character" and len(items) == 1:
            return [_r_str(x) for x in _as_vector(items[0][1])]
        if fname == "as.roman" and len(items) == 1:
            return [_roman(int(x)) for x in _as_vector(items[0][1])]
        raise RParseError(f"unsupported function {fname!r}")


class _Unparsed(str):
    """Raw R source for a value the reader does not evaluate."""


def _scalar_num(v) -> int:
    if isinstance(v, list) and len(v) == 1:
        v = v[0]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise RParseError("':' needs numbers")
    return int(v)


def _finish(v):
    """Turn parser output into plain JSON-able Python values."""
    if isinstance(v, _Named):
        return {n if n is not None else "": _finish(x) for n, x in v.items}
    if isinstance(v, _Unparsed):
        return str(v)
    if isinstance(v, list):
        return [_finish(x) for x in v]
    return v


def _rq(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


_R_SYNTACTIC = re.compile(r"^(?:[A-Za-z]|\.(?![0-9]))[A-Za-z0-9._]*$")


def _rname(n: str) -> str:
    return n if _R_SYNTACTIC.match(n) else f"`{n}`"


def _rval(v, indent: str = "") -> str:
    """Format a JSON-able value as R source."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return _r_str(v)
    if isinstance(v, str):
        return _rq(v)
    if isinstance(v, list):
        if not v:
            return "character(0)"
        if len(v) == 1 and isinstance(v[0], str):
            return _rq(v[0])
        return "c(" + ", ".join(_rval(x) for x in v) + ")"
    if isinstance(v, dict):
        if all(isinstance(x, str) for x in v.values()):
            return "c(" + ", ".join(f"{_rname(k)}={_rq(x)}" for k, x in v.items()) + ")"
        inner = indent + "    "
        parts = [f"{inner}{_rname(k)}={_rval(x, inner)}" for k, x in v.items()]
        return "list(\n" + ",\n".join(parts) + "\n" + indent + ")"
    raise TypeError(f"cannot write {type(v).__name__} as R")


# --- registered NCBI assemblies (NCBI_assemblies/<Organism>.R) -----------------

_NCBI_VECTOR_FIELDS = {"circ_seqs"}
_NCBI_FIELD_ORDER = ["assembly", "assembly_level", "date", "extra_info",
                     "assembly_accession", "circ_seqs", "NCBI2Ensembl_special_mappings"]


def _read_registered_ncbi(text: str) -> list[dict]:
    p = _RParser(text)
    organism = None
    out = []
    for name, val, raw in p.statements():
        if name == "ORGANISM":
            organism = _finish(val)
            if isinstance(organism, list) and len(organism) == 1:
                organism = organism[0]
        elif name == "ASSEMBLIES":
            entries = val if isinstance(val, list) else []
            for e in entries:
                if not isinstance(e, dict):
                    continue
                rec = {"ORGANISM": organism}
                for k, v in e.items():
                    if k in _NCBI_VECTOR_FIELDS:
                        v = _as_vector(v)
                    rec[k] = v
                out.append(rec)
    return out


def _write_registered_ncbi(records: list[dict]) -> str:
    blocks = []
    groups: list[tuple[Any, list[dict]]] = []
    for r in records:
        org = r.get("ORGANISM")
        if groups and groups[-1][0] == org:
            groups[-1][1].append(r)
        else:
            groups.append((org, [r]))
    for org, recs in groups:
        lines = [f"ORGANISM <- {_rval(org)}", "", "ASSEMBLIES <- list("]
        entries = []
        for r in recs:
            keys = [k for k in _NCBI_FIELD_ORDER if k in r] + \
                   [k for k in r if k not in _NCBI_FIELD_ORDER and k != "ORGANISM"]
            fields = [f"{_rname(k)}={_rval(r[k], '         ')}" for k in keys]
            entries.append("    list(" + ",\n         ".join(fields) + ")")
        lines.append(",\n\n".join(entries))
        lines.append(")")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)


def _detect_registered_ncbi(text: str, filename: str) -> float:
    if re.search(r"^ASSEMBLIES\s*<-\s*list\(", text, re.M) and re.search(r"^ORGANISM\s*<-", text, re.M):
        return 0.95
    return 0.0


# --- registered UCSC genomes (UCSC_genomes/<genome>.R) ---------------------------

_UCSC_TOP = ["GENOME", "ORGANISM", "ASSEMBLED_MOLECULES", "CIRC_SEQS",
             "FETCH_ORDERED_CHROM_SIZES", "NCBI_LINKER", "ENSEMBL_LINKER"]
_UCSC_VECTOR_FIELDS = {"ASSEMBLED_MOLECULES", "CIRC_SEQS", "NCBI_LINKER.AssemblyUnits"}
_UCSC_SCALAR_FIELDS = {"GENOME", "ORGANISM", "ENSEMBL_LINKER", "NCBI_LINKER.assembly_accession",
                       "NCBI_LINKER.drop_unmapped"}


def _read_registered_ucsc(text: str) -> list[dict]:
    p = _RParser(text)
    out: list[dict] = []
    cur: dict = {}
    for name, val, raw in p.statements():
        if not name.isupper() and not re.fullmatch(r"[A-Z0-9_]+", name):
            continue  # helper functions/variables (lower case, dot-prefixed)
        if name == "GENOME" and "GENOME" in cur:
            out.append(cur)
            cur = {}
        if name == "FETCH_ORDERED_CHROM_SIZES":
            cur[name] = raw  # R function source, kept verbatim, never evaluated
            continue
        v = _finish(val)
        if name == "NCBI_LINKER":
            if isinstance(v, dict):
                for k, x in v.items():
                    key = f"NCBI_LINKER.{k}"
                    cur[key] = _norm_ucsc(key, x)
            else:
                # uses helper variables or functions we do not evaluate
                cur["NCBI_LINKER"] = raw
            continue
        cur[name] = _norm_ucsc(name, v)
    if cur:
        out.append(cur)
    return out


def _norm_ucsc(key, v):
    if key in _UCSC_VECTOR_FIELDS:
        return _as_vector(v)
    if key == "NCBI_LINKER.unmapped_seqs" and isinstance(v, dict):
        return {k: _as_vector(x) for k, x in v.items()}
    if key in _UCSC_SCALAR_FIELDS and isinstance(v, list) and len(v) == 1:
        return v[0]
    return v


def _write_registered_ucsc(records: list[dict]) -> str:
    blocks = []
    for r in records:
        lines = []
        for k in ["GENOME", "ORGANISM", "ASSEMBLED_MOLECULES", "CIRC_SEQS"]:
            if k in r:
                lines.append(f"{k} <- {_rval(r[k])}")
        if "FETCH_ORDERED_CHROM_SIZES" in r:
            lines.append("")
            lines.append(f"FETCH_ORDERED_CHROM_SIZES <- {r['FETCH_ORDERED_CHROM_SIZES']}")
        linker = {k.split(".", 1)[1]: v for k, v in r.items() if k.startswith("NCBI_LINKER.")}
        if isinstance(r.get("NCBI_LINKER"), str):
            lines.append("")
            lines.append(f"NCBI_LINKER <- {r['NCBI_LINKER']}")
        elif linker:
            parts = [f"    {_rname(k)}={_rval(v, '    ')}" for k, v in linker.items()]
            lines.append("")
            lines.append("NCBI_LINKER <- list(\n" + ",\n".join(parts) + "\n)")
        if "ENSEMBL_LINKER" in r:
            lines.append("")
            lines.append(f"ENSEMBL_LINKER <- {_rval(r['ENSEMBL_LINKER'])}")
        for k, v in r.items():
            if k not in _UCSC_TOP and not k.startswith("NCBI_LINKER."):
                lines.append(f"{k} <- {_rval(v)}")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)


def _detect_registered_ucsc(text: str, filename: str) -> float:
    if re.search(r"^GENOME\s*<-", text, re.M) and re.search(r"^ASSEMBLED_MOLECULES\s*<-", text, re.M):
        return 0.95
    return 0.0


# ---------------------------------------------------------------------------
# DCF (BSgenome seed files and package DESCRIPTION files)
# ---------------------------------------------------------------------------

_DCF_KEY = re.compile(r"^([A-Za-z0-9_.@/-]+):(.*)$")


def _read_dcf(text: str) -> list[dict]:
    """Like R's read.dcf(): continuation lines start with whitespace; their
    leading whitespace is dropped and lines are joined with newlines; values
    are stripped. Records are separated by blank lines."""
    records: list[dict] = []
    cur: dict = {}
    key = None
    for line in text.splitlines():
        if not line.strip():
            if cur:
                records.append(cur)
                cur, key = {}, None
            continue
        if line[0] in " \t":
            if key is None:
                continue
            cur[key].append(line.strip())
            continue
        m = _DCF_KEY.match(line)
        if not m:
            continue
        key = m.group(1)
        cur[key] = [m.group(2).strip()]
    if cur:
        records.append(cur)
    return [{k: "\n".join(v).strip() for k, v in r.items()} for r in records]


def _write_dcf(records: list[dict]) -> str:
    out = []
    for r in records:
        lines = []
        for k, v in r.items():
            if v is None:
                continue
            parts = str(v).split("\n")
            lines.append(f"{k}: {parts[0]}".rstrip())
            for p in parts[1:]:
                lines.append("\t" + (p if p else "."))
        out.append("\n".join(lines) + "\n")
    return "\n".join(out)


_SEED_ONLY = ("BSgenomeObjname", "seqs_srcdir", "seqfile_name", "masks_srcdir", "RefPkgname",
              "PkgExamples", "SrcDataFiles", "nmask_per_seq", "ondisk_seq_format",
              "seqfiles_prefix", "seqfiles_suffix", "AGAPSfiles_name", "RMfiles_name")


def _dcf_keys(text: str) -> set[str]:
    return {m.group(1) for m in (_DCF_KEY.match(l) for l in text.splitlines() if l[:1] not in (" ", "\t"))
            if m}


def _detect_seed(text: str, filename: str) -> float:
    keys = _dcf_keys(text)
    if "Package" not in keys:
        return 0.0
    score = 0.0
    if keys & set(_SEED_ONLY):
        score = 0.9
    if filename.endswith("-seed"):
        score = max(score, 0.95)
    return score


def _detect_description(text: str, filename: str) -> float:
    keys = _dcf_keys(text)
    if "Package" not in keys:
        return 0.0
    if keys & {"BSgenomeObjname", "seqs_srcdir", "masks_srcdir"}:
        return 0.2
    pkg = re.search(r"^Package:\s*(\S+)", text, re.M)
    is_bsgenome = bool(pkg and pkg.group(1).startswith("BSgenome."))
    has_genome = bool(keys & {"organism", "provider", "provider_version", "genome", "release_date"})
    if is_bsgenome and has_genome:
        return 0.9
    if has_genome:
        return 0.6
    if filename.endswith("DESCRIPTION") or "DESCRIPTION" in filename:
        return 0.3
    return 0.1


# ---------------------------------------------------------------------------
# AnnotationHub
# ---------------------------------------------------------------------------

_AH_ARRAYS = ("rdatapaths", "input_sources")


def _flatten_ah(obj: dict) -> dict:
    rec: dict = {}
    for k, v in obj.items():
        if k in _AH_ARRAYS and isinstance(v, list):
            subkeys: list[str] = []
            for item in v:
                for sk in item:
                    if sk not in subkeys:
                        subkeys.append(sk)
            for sk in subkeys:
                rec[f"{k}[].{sk}"] = [item.get(sk) for item in v]
        else:
            rec[k] = v
    return rec


def _unflatten_ah(rec: dict) -> dict:
    obj: dict = {}
    arrays: dict[str, dict[str, list]] = {}
    for k, v in rec.items():
        if "[]." in k:
            arr, sk = k.split("[].", 1)
            if arr not in obj:
                obj[arr] = None  # keep key position
            arrays.setdefault(arr, {})[sk] = v
        else:
            obj[k] = v
    for arr, cols in arrays.items():
        n = max((len(c) for c in cols.values()), default=0)
        obj[arr] = [{sk: (vals[i] if i < len(vals) else None) for sk, vals in cols.items()} for i in range(n)]
    return obj


def _read_ah_record(text: str) -> list[dict]:
    data = json.loads(text)
    items = data if isinstance(data, list) else [data]
    return [_flatten_ah(o) for o in items if isinstance(o, dict)]


def _write_ah_record(records: list[dict]) -> str:
    objs = [_unflatten_ah(r) for r in records]
    return json.dumps(objs[0] if len(objs) == 1 else objs, indent=2) + "\n"


def _detect_ah_record(text: str, filename: str) -> float:
    s = text.lstrip()
    if not s.startswith(("{", "[")):
        return 0.0
    try:
        data = json.loads(text)
    except ValueError:
        return 0.0
    item = data[0] if isinstance(data, list) and data else data
    if isinstance(item, dict) and "ah_id" in item:
        return 0.95 if "rdatapaths" in item else 0.8
    return 0.0


AH_CSV_COLS = ["Title", "Description", "BiocVersion", "Genome", "SourceType", "SourceUrl",
               "SourceVersion", "Species", "TaxonomyId", "Coordinate_1_based", "DataProvider",
               "Maintainer", "RDataClass", "DispatchClass", "Location_Prefix", "RDataPath", "Tags"]
_AH_CSV_CONV = {"TaxonomyId": _to_int, "Coordinate_1_based": _to_rbool}


def _read_ah_csv(text: str) -> list[dict]:
    return _read_table(text, _AH_CSV_CONV, delim=",")


def _write_ah_csv(records: list[dict]) -> str:
    return _write_table(records, AH_CSV_COLS, ",", lambda c, v: _from_val(v))


def _detect_ah_csv(text: str, filename: str) -> float:
    head = {c.strip().strip('"') for c in _first_line(text).split(",")}
    if {"RDataPath", "RDataClass"} <= head and ("DispatchClass" in head or "SourceType" in head):
        return 0.95
    if "RDataPath" in head:
        return 0.6
    return 0.0


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

FORMATS = [
    Format(
        id="bioconductor_seqinfo",
        source=SOURCE,
        description="Seqinfo object as a table (as.data.frame(<Seqinfo>): seqnames, seqlengths, "
                    "isCircular, genome), one record per sequence; also reads show(<Seqinfo>) text",
        read=_read_seqinfo, write=_write_seqinfo, detect=_detect_seqinfo,
        extensions=(".tsv", ".txt", ".csv"),
    ),
    Format(
        id="bioconductor_chrominfo_ucsc",
        source=SOURCE,
        description="GenomeInfoDb getChromInfoFromUCSC() table (chrominfo_db/UCSC/<genome>.tab), "
                    "one record per sequence",
        read=_read_chrominfo_ucsc, write=_write_chrominfo_ucsc, detect=_detect_chrominfo_ucsc,
        extensions=(".tab",),
    ),
    Format(
        id="bioconductor_chrominfo_ncbi",
        source=SOURCE,
        description="GenomeInfoDb getChromInfoFromNCBI() table (chrominfo_db/NCBI/<accession>.tab), "
                    "one record per sequence",
        read=_read_chrominfo_ncbi, write=_write_chrominfo_ncbi, detect=_detect_chrominfo_ncbi,
        extensions=(".tab",),
    ),
    Format(
        id="bioconductor_seqlevels_style",
        source=SOURCE,
        description="GenomeInfoDb seqlevelsStyle() naming table (extdata/dataFiles/<Organism>.txt), "
                    "one record per chromosome with its name in each style",
        read=_read_seqlevels_style, write=_write_seqlevels_style, detect=_detect_seqlevels_style,
        extensions=(".txt",),
    ),
    Format(
        id="bioconductor_genome_mapping_tbl",
        source=SOURCE,
        description="GenomeInfoDb genomeMappingTbl.csv used by mapGenomeBuilds(): Ensembl assembly "
                    "to UCSC genome build, one record per Ensembl assembly",
        read=_read_genome_mapping, write=_write_genome_mapping, detect=_detect_genome_mapping,
        extensions=(".csv",),
    ),
    Format(
        id="bioconductor_registered_ncbi",
        source=SOURCE,
        description="GenomeInfoDb registered NCBI assembly file (registered/NCBI_assemblies/"
                    "<Organism>.R), one record per assembly",
        read=_read_registered_ncbi, write=_write_registered_ncbi, detect=_detect_registered_ncbi,
        extensions=(".R",),
    ),
    Format(
        id="bioconductor_registered_ucsc",
        source=SOURCE,
        description="GenomeInfoDb registered UCSC genome file (registered/UCSC_genomes/<genome>.R), "
                    "one record per UCSC genome",
        read=_read_registered_ucsc, write=_write_registered_ucsc, detect=_detect_registered_ucsc,
        extensions=(".R",),
    ),
    Format(
        id="bioconductor_bsgenome_seed",
        source=SOURCE,
        description="BSgenomeForge seed file (DCF) used to forge a BSgenome data package",
        read=_read_dcf, write=_write_dcf, detect=_detect_seed,
        extensions=("-seed", ".dcf"),
    ),
    Format(
        id="bioconductor_bsgenome_description",
        source=SOURCE,
        description="DESCRIPTION file (DCF) of a built BSgenome data package",
        read=_read_dcf, write=_write_dcf, detect=_detect_description,
        extensions=("DESCRIPTION", ".dcf"),
    ),
    Format(
        id="bioconductor_annotationhub_record",
        source=SOURCE,
        description="AnnotationHub resource record as served by annotationhub.bioconductor.org/ahid/<AH id> "
                    "(JSON); array members flattened to 'array[].field' lists",
        read=_read_ah_record, write=_write_ah_record, detect=_detect_ah_record,
        extensions=(".json",),
    ),
    Format(
        id="bioconductor_annotationhub_metadata_csv",
        source=SOURCE,
        description="AnnotationHub contributor metadata.csv (inst/extdata/*.csv of a hub package), "
                    "one record per hub resource",
        read=_read_ah_csv, write=_write_ah_csv, detect=_detect_ah_csv,
        extensions=(".csv",),
    ),
]
