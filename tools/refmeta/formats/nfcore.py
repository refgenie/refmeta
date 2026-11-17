"""nf-core and AWS iGenomes reference formats.

Formats (ids match sources/nfcore/fields.json):

- nfcore_igenomes_config: the Groovy `params.genomes` map in an nf-core
  pipeline's conf/igenomes.config. One record per genome key.
- nfcore_references_datasheet: nf-core/references asset datasheet YAML
  (a list of genome entries). One record per entry.
- nfcore_igenomes_manifest: AWS iGenomes file manifest (one s3:// URI per
  line). One record per file, with the URI split along the iGenomes layout.
- nfcore_igenomes_genomesize: Illumina iGenomes GenomeSize.xml. One record
  per <chromosome> element.
- nfcore_igenomes_dict: sequence dictionary (genome.dict, SAM header) as
  served in iGenomes. One record per @SQ line.
- nfcore_igenomes_fai: FASTA index (genome.fa.fai) as served in iGenomes.
  One record per line.

Standard library plus pyyaml only; text in, text out.
"""
from __future__ import annotations

import datetime as _dt
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

import yaml

from . import Format

SOURCE = "nfcore"

# ---------------------------------------------------------------------------
# Groovy map parser (only the literal syntax used by igenomes.config files)
# ---------------------------------------------------------------------------

_PUNCT = set("[]{}:=,")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
_IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$.]*")


class GroovyParseError(ValueError):
    pass


def _tokenize(text: str) -> list[tuple[str, object]]:
    """Split Groovy config text into (kind, value) tokens.

    Kinds: 'str', 'num', 'ident', 'punct'. Comments and whitespace are dropped.
    Strings keep their raw content, including any ${...} placeholders.
    """
    toks: list[tuple[str, object]] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "'\"":
            if text.startswith(c * 3, i):
                j = text.find(c * 3, i + 3)
                if j < 0:
                    raise GroovyParseError("unterminated triple-quoted string")
                toks.append(("str", text[i + 3 : j]))
                i = j + 3
                continue
            j = i + 1
            buf = []
            while j < n and text[j] != c:
                if text[j] == "\\" and j + 1 < n:
                    nxt = text[j + 1]
                    buf.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                    j += 2
                    continue
                if text[j] == "\n":
                    raise GroovyParseError("newline inside string")
                buf.append(text[j])
                j += 1
            if j >= n:
                raise GroovyParseError("unterminated string")
            toks.append(("str", "".join(buf)))
            i = j + 1
        elif c in _PUNCT:
            toks.append(("punct", c))
            i += 1
        else:
            m = _NUM_RE.match(text, i)
            if m and (m.end() == n or not (text[m.end()].isalnum() or text[m.end()] == "_")):
                s = m.group(0)
                toks.append(("num", float(s) if any(ch in s for ch in ".eE") else int(s)))
                i = m.end()
                continue
            m = _IDENT_RE.match(text, i)
            if m:
                toks.append(("ident", m.group(0)))
                i = m.end()
                continue
            # anything else (operators, parentheses, ...) is kept as a lone
            # punct token; the genomes block never contains these.
            toks.append(("punct", c))
            i += 1
    return toks


_CONSTS = {"true": True, "false": False, "null": None}


class _Parser:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else (None, None)

    def take(self, kind=None, value=None):
        tok = self.peek()
        if tok[0] is None or (kind and tok[0] != kind) or (value is not None and tok[1] != value):
            raise GroovyParseError(f"expected {kind} {value!r}, got {tok!r} at token {self.i}")
        self.i += 1
        return tok

    def key(self):
        kind, val = self.peek()
        if kind in ("str", "ident"):
            self.i += 1
            return str(val)
        if kind == "num":
            self.i += 1
            return str(val)
        raise GroovyParseError(f"expected key, got {(kind, val)!r}")

    def value(self):
        kind, val = self.peek()
        if kind == "str" or kind == "num":
            self.i += 1
            return val
        if kind == "ident":
            self.i += 1
            if val in _CONSTS:
                return _CONSTS[val]
            raise GroovyParseError(f"unsupported expression {val!r}")
        if (kind, val) == ("punct", "["):
            return self.bracket()
        raise GroovyParseError(f"unexpected token {(kind, val)!r}")

    def bracket(self):
        """Parse [ ... ]: a map literal ([k: v, ...] or [:]) or a list."""
        self.take("punct", "[")
        if self.peek() == ("punct", ":") and self.peek(1) == ("punct", "]"):
            self.i += 2
            return {}
        if self.peek() == ("punct", "]"):
            self.i += 1
            return []
        is_map = self.peek(1) == ("punct", ":")
        out_map: dict = {}
        out_list: list = []
        while True:
            if self.peek() == ("punct", "]"):
                self.i += 1
                return out_map if is_map else out_list
            if is_map:
                k = self.key()
                self.take("punct", ":")
                out_map[k] = self.value()
            else:
                out_list.append(self.value())
            if self.peek() == ("punct", ","):
                self.i += 1

    def block(self):
        """Parse { key = value  key { ... } ... } config block syntax."""
        self.take("punct", "{")
        out: dict = {}
        while True:
            tok = self.peek()
            if tok == ("punct", "}"):
                self.i += 1
                return out
            if tok[0] is None:
                raise GroovyParseError("unterminated block")
            k = self.key()
            nxt = self.peek()
            if nxt == ("punct", "{"):
                out[k] = self.block()
            elif nxt == ("punct", "="):
                self.i += 1
                out[k] = self.value()
            else:
                raise GroovyParseError(f"expected '=' or '{{' after {k!r}, got {nxt!r}")


def parse_genomes_map(text: str) -> dict:
    """Return the params.genomes map from igenomes.config-style Groovy text.

    Supports `params.genomes = [ 'KEY' : [ k : v, ... ], ... ]` (current
    nf-core template) and `params { genomes { 'KEY' { k = v } } }` (older
    pipelines and the AWS-iGenomes example config).
    """
    toks = _tokenize(text)
    for idx, (kind, val) in enumerate(toks):
        if kind != "ident" or val not in ("params.genomes", "genomes"):
            continue
        nxt = toks[idx + 1] if idx + 1 < len(toks) else (None, None)
        nxt2 = toks[idx + 2] if idx + 2 < len(toks) else (None, None)
        p = _Parser(toks)
        if nxt == ("punct", "=") and nxt2 == ("punct", "["):
            p.i = idx + 2
            m = p.bracket()
        elif nxt == ("punct", "{"):
            p.i = idx + 1
            m = p.block()
        else:
            continue
        if m == []:
            m = {}
        if not isinstance(m, dict):
            raise GroovyParseError("params.genomes is not a map")
        return m
    raise GroovyParseError("no params.genomes map found")


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key + "."))
        else:
            out[key] = v
    return out


def igenomes_config_read(text: str) -> list[dict]:
    genomes = parse_genomes_map(text)
    records = []
    for key, attrs in genomes.items():
        rec = {"genome": key}
        rec.update(_flatten(attrs) if isinstance(attrs, dict) else {"value": attrs})
        records.append(rec)
    return records


_BARE_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _groovy_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _unflatten(items) -> dict:
    """Rebuild nested maps from dotted attribute keys (inverse of _flatten)."""
    out: dict = {}
    for k, v in items:
        parts = k.split(".")
        cur = out
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                raise ValueError(f"key {k!r} clashes with a scalar value")
        cur[parts[-1]] = v
    return out


def _groovy_value(v) -> str:
    if isinstance(v, dict):
        inner = ", ".join(
            f"{k if _BARE_KEY_RE.match(k) else _groovy_str(k)} : {_groovy_value(x)}" for k, x in v.items()
        )
        return "[" + inner + "]" if inner else "[:]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_groovy_value(x) for x in v) + "]"
    return _groovy_str(str(v))


def igenomes_config_write(records: list[dict]) -> str:
    lines = [
        "/*",
        " * params.genomes map written by refmeta (nf-core igenomes.config syntax).",
        " */",
        "",
        "params.genomes = [",
    ]
    for rec in records:
        key = rec.get("genome")
        if key is None:
            raise ValueError("nfcore_igenomes_config record needs a 'genome' key")
        attrs = [(k, v) for k, v in rec.items() if k != "genome"]
        top = list(_unflatten(attrs))
        width = max([len(k) if _BARE_KEY_RE.match(k) else len(k) + 2 for k in top] or [0])
        quoted_key = "'" + str(key).replace("\\", "\\\\").replace("'", "\\'") + "'"
        lines.append(f"    {quoted_key} : [")
        for k, v in _unflatten(attrs).items():
            kk = k if _BARE_KEY_RE.match(k) else _groovy_str(k)
            lines.append(f"        {kk.ljust(width)} : {_groovy_value(v)},")
        lines.append("    ],")
    if not records:
        lines[-1] = "params.genomes = [:]"
    else:
        lines.append("]")
    return "\n".join(lines) + "\n"


def igenomes_config_detect(text: str, filename: str = "") -> float:
    fn = (filename or "").lower()
    score = 0.0
    if re.search(r"params\.genomes\s*=\s*\[", text):
        score = 0.95
    elif re.search(r"\bgenomes\s*\{", text) and ("igenomes" in text or "WholeGenomeFasta" in text):
        score = 0.85
    elif "params.genomes" in text:
        score = 0.5
    if fn.endswith(".config") and score:
        score = min(1.0, score + 0.04)
    return score


# ---------------------------------------------------------------------------
# nf-core/references datasheet (YAML list)
# ---------------------------------------------------------------------------


def _jsonable(v):
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    return v


def datasheet_read(text: str) -> list[dict]:
    data = yaml.safe_load(text)
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("datasheet must be a YAML list of genome entries")
    out = []
    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("datasheet entries must be mappings")
        out.append({str(k): _jsonable(v) for k, v in entry.items()})
    return out


def datasheet_write(records: list[dict]) -> str:
    return yaml.safe_dump(
        [dict(r) for r in records],
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=4096,
    )


_DATASHEET_KEYS = {
    "fasta", "reference_source", "species", "source", "fasta_fai", "fasta_dict",
    "gtf", "gff", "annotation_version", "site", "bwamem1_index", "star_index",
}


def datasheet_detect(text: str, filename: str = "") -> float:
    fn = (filename or "").lower()
    if not re.search(r"(?m)^-\s+genome:", text):
        return 0.0
    try:
        recs = datasheet_read(text)
    except Exception:
        return 0.2
    if not recs or not all("genome" in r for r in recs):
        return 0.2
    hits = sum(1 for r in recs if _DATASHEET_KEYS & set(r))
    score = 0.6 + 0.3 * hits / len(recs)
    if fn.endswith((".yml", ".yaml")):
        score += 0.05
    return min(score, 0.95)


# ---------------------------------------------------------------------------
# AWS iGenomes file manifest
# ---------------------------------------------------------------------------

MANIFEST_PREFIX = "s3://ngi-igenomes/igenomes/"
_MANIFEST_FIELDS = ("species", "source", "build", "section", "subpath")


def _split_igenomes_uri(uri: str) -> dict:
    parts = {k: None for k in _MANIFEST_FIELDS}
    if not uri.startswith(MANIFEST_PREFIX):
        return parts
    segs = uri[len(MANIFEST_PREFIX) :].split("/")
    if len(segs) < 4:
        return parts
    parts["species"], parts["source"], parts["build"] = segs[0], segs[1], segs[2]
    rest = segs[3:]
    if len(rest) >= 2:
        parts["section"] = rest[0]
        parts["subpath"] = "/".join(rest[1:])
    else:
        parts["subpath"] = rest[0]
    return parts


def manifest_read(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rec = {"uri": line}
        rec.update(_split_igenomes_uri(line))
        out.append(rec)
    return out


def manifest_write(records: list[dict]) -> str:
    lines = []
    for r in records:
        uri = r.get("uri")
        if not uri:
            segs = [r.get(k) for k in _MANIFEST_FIELDS]
            if not all(segs[:3]) or not segs[4]:
                raise ValueError("manifest record needs uri, or species/source/build/subpath")
            uri = MANIFEST_PREFIX + "/".join(s for s in segs if s)
        lines.append(uri)
    return "\n".join(lines) + "\n"


def manifest_detect(text: str, filename: str = "") -> float:
    lines = [ln.strip() for ln in text.splitlines()[:200] if ln.strip()]
    if not lines:
        return 0.0
    ig = sum(ln.startswith(MANIFEST_PREFIX) for ln in lines)
    if ig == len(lines):
        return 0.95
    if ig / len(lines) > 0.5:
        return 0.7
    if all(ln.startswith("s3://") for ln in lines):
        return 0.3
    return 0.0


# ---------------------------------------------------------------------------
# Illumina iGenomes GenomeSize.xml
# ---------------------------------------------------------------------------

_GS_INT = ("totalBases", "knownBases", "ploidy")
_GS_BOOL = ("isCircular",)


def genomesize_read(text: str) -> list[dict]:
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("DTDs are not allowed in GenomeSize.xml")
    root = ET.fromstring(text.strip())
    if root.tag != "sequenceSizes":
        raise ValueError(f"expected <sequenceSizes> root, got <{root.tag}>")
    root_attrs = dict(root.attrib)
    out = []
    for el in root:
        if el.tag != "chromosome":
            continue
        rec = dict(root_attrs)
        for k, v in el.attrib.items():
            if k in _GS_INT and re.fullmatch(r"-?\d+", v):
                rec[k] = int(v)
            elif k in _GS_BOOL and v in ("true", "false"):
                rec[k] = v == "true"
            else:
                rec[k] = v
        out.append(rec)
    return out


def genomesize_write(records: list[dict]) -> str:
    root_keys = ("genomeName",)
    gname = next((r.get("genomeName") for r in records if r.get("genomeName") is not None), None)
    head = "<sequenceSizes"
    if gname is not None:
        head += f" genomeName={quoteattr(str(gname))}"
    lines = [head + ">"]
    for r in records:
        attrs = []
        for k, v in r.items():
            if k in root_keys or v is None:
                continue
            if isinstance(v, bool):
                v = "true" if v else "false"
            attrs.append(f"{k}={quoteattr(str(v))}")
        lines.append("\t<chromosome " + " ".join(attrs) + " />")
    lines.append("</sequenceSizes>")
    return "\n".join(lines) + "\n"


def genomesize_detect(text: str, filename: str = "") -> float:
    head = text[:2000]
    if "<sequenceSizes" in head and "<chromosome" in head:
        return 0.97
    if (filename or "").endswith("GenomeSize.xml"):
        return 0.6
    return 0.0


# ---------------------------------------------------------------------------
# Sequence dictionary (genome.dict, SAM header lines)
# ---------------------------------------------------------------------------


def dict_read(text: str) -> list[dict]:
    hd: dict = {}
    out = []
    for line in text.splitlines():
        if line.startswith("@HD"):
            for f in line.split("\t")[1:]:
                if ":" in f:
                    t, v = f.split(":", 1)
                    hd[f"@HD/{t}"] = v
        elif line.startswith("@SQ"):
            rec = dict(hd)
            for f in line.split("\t")[1:]:
                if ":" not in f:
                    continue
                t, v = f.split(":", 1)
                rec[t] = int(v) if t == "LN" and v.isdigit() else v
            out.append(rec)
    return out


def dict_write(records: list[dict]) -> str:
    lines = []
    hd = {}
    for r in records:
        for k, v in r.items():
            if k.startswith("@HD/") and v is not None:
                hd.setdefault(k[4:], v)
    if hd:
        lines.append("@HD\t" + "\t".join(f"{k}:{v}" for k, v in hd.items()))
    for r in records:
        if r.get("SN") is None or r.get("LN") is None:
            raise ValueError("@SQ record needs SN and LN")
        tags = [("SN", r["SN"]), ("LN", r["LN"])]
        tags += [(k, v) for k, v in r.items() if k not in ("SN", "LN") and not k.startswith("@HD/") and v is not None]
        lines.append("@SQ\t" + "\t".join(f"{k}:{v}" for k, v in tags))
    return "\n".join(lines) + "\n"


def dict_detect(text: str, filename: str = "") -> float:
    lines = [ln for ln in text.splitlines()[:50] if ln.strip()]
    if not lines:
        return 0.0
    sq = sum(ln.startswith("@SQ\t") for ln in lines)
    if sq and all(ln.startswith("@") for ln in lines):
        return 0.9 if (filename or "").endswith(".dict") else 0.8
    return 0.0


# ---------------------------------------------------------------------------
# FASTA index (.fai)
# ---------------------------------------------------------------------------

FAI_COLUMNS = ("NAME", "LENGTH", "OFFSET", "LINEBASES", "LINEWIDTH", "QUALOFFSET")


def fai_read(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) not in (5, 6):
            raise ValueError(f"fai line must have 5 or 6 columns: {line!r}")
        rec = {"NAME": cols[0]}
        for name, val in zip(FAI_COLUMNS[1:], cols[1:]):
            rec[name] = int(val)
        out.append(rec)
    return out


def fai_write(records: list[dict]) -> str:
    lines = []
    for r in records:
        cols = [r.get(c) for c in FAI_COLUMNS]
        if cols[5] is None:
            cols = cols[:5]
        if any(c is None for c in cols):
            raise ValueError("fai record needs NAME, LENGTH, OFFSET, LINEBASES, LINEWIDTH")
        lines.append("\t".join(str(c) for c in cols))
    return "\n".join(lines) + "\n"


def fai_detect(text: str, filename: str = "") -> float:
    lines = [ln for ln in text.splitlines()[:50] if ln.strip()]
    if not lines:
        return 0.0
    for ln in lines:
        cols = ln.split("\t")
        if len(cols) not in (5, 6) or not all(c.isdigit() for c in cols[1:]):
            return 0.0
    return 0.9 if (filename or "").endswith(".fai") else 0.6


FORMATS = [
    Format(
        id="nfcore_igenomes_config",
        source=SOURCE,
        description="nf-core igenomes.config: Groovy params.genomes map, one record per genome key (--genome value)",
        read=igenomes_config_read,
        write=igenomes_config_write,
        detect=igenomes_config_detect,
        extensions=(".config",),
    ),
    Format(
        id="nfcore_references_datasheet",
        source=SOURCE,
        description="nf-core/references asset datasheet YAML, one record per genome entry",
        read=datasheet_read,
        write=datasheet_write,
        detect=datasheet_detect,
        extensions=(".yml", ".yaml"),
    ),
    Format(
        id="nfcore_igenomes_manifest",
        source=SOURCE,
        description="AWS iGenomes file manifest (s3://ngi-igenomes/igenomes/... one URI per line), one record per file",
        read=manifest_read,
        write=manifest_write,
        detect=manifest_detect,
        extensions=(".txt",),
    ),
    Format(
        id="nfcore_igenomes_genomesize",
        source=SOURCE,
        description="Illumina iGenomes GenomeSize.xml, one record per <chromosome>",
        read=genomesize_read,
        write=genomesize_write,
        detect=genomesize_detect,
        extensions=(".xml",),
    ),
    Format(
        id="nfcore_igenomes_dict",
        source=SOURCE,
        description="Sequence dictionary (genome.dict, SAM @HD/@SQ header) as served in iGenomes, one record per @SQ",
        read=dict_read,
        write=dict_write,
        detect=dict_detect,
        extensions=(".dict",),
    ),
    Format(
        id="nfcore_igenomes_fai",
        source=SOURCE,
        description="FASTA index (genome.fa.fai) as served in iGenomes, one record per sequence",
        read=fai_read,
        write=fai_write,
        detect=fai_detect,
        extensions=(".fai",),
    ),
]
