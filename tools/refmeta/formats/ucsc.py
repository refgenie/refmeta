"""UCSC Genome Browser formats.

Covers the REST API (api.genome.ucsc.edu) JSON responses for genome lists,
chromosome lists, GenArk lists, genome search and file lists; the download
server text files (chrom.sizes, chromAlias.txt, the chromAlias database table,
md5sum.txt); and the hub.txt / genomes.txt stanza files of track and assembly
hubs. Field inventory: sources/ucsc/fields.json.

API envelope keys (downloadTime, dataTime, itemCount, ...) describe the HTTP
response, not a genome, so read() drops them and write() does not produce them.
"""
from __future__ import annotations

import json
import re

from . import Format

SOURCE = "ucsc"


def _load_json(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return None


def _dump(obj) -> str:
    return json.dumps(obj, indent=1) + "\n"


def _name(filename: str) -> str:
    return (filename or "").rsplit("/", 1)[-1].lower()


def _lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def _group(records: list[dict], keys: tuple[str, ...]) -> list[tuple[tuple, list[dict]]]:
    """Group records by the values of envelope keys, keeping first-seen order."""
    groups: dict[tuple, list[dict]] = {}
    for r in records:
        groups.setdefault(tuple(r.get(k) for k in keys), []).append(r)
    return list(groups.items())


def _responses(text: str) -> list[dict]:
    """A response object, or a list of them (what write() emits for several genomes)."""
    d = _load_json(text)
    if isinstance(d, dict):
        return [d]
    if isinstance(d, list):
        return [x for x in d if isinstance(x, dict)]
    return []


def _one_or_list(objs: list[dict]) -> str:
    return _dump(objs[0] if len(objs) == 1 else objs)


# --------------------------------------------------------------------------
# /list/ucscGenomes  (hgcentral.dbDb rows)

def read_dbdb(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        for name, row in (d.get("ucscGenomes") or {}).items():
            out.append({"name": name, **row})
    return out


def write_dbdb(records: list[dict]) -> str:
    genomes = {}
    for r in records:
        row = dict(r)
        genomes[row.pop("name")] = row
    return _dump({"ucscGenomes": genomes})


def detect_dbdb(text: str, filename: str) -> float:
    head = text[:4000]
    if '"ucscGenomes"' in head and text.lstrip().startswith("{"):
        return 0.95
    return 0.0


# --------------------------------------------------------------------------
# /list/chromosomes  (chromInfo names and sizes, or a hub genome's chrom sizes)

_CHROM_ENV = ("genome", "hubUrl", "track")


def read_api_chromosomes(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        env = {k: d[k] for k in _CHROM_ENV if k in d}
        for chrom, size in (d.get("chromosomes") or {}).items():
            out.append({**env, "chrom": chrom, "size": size})
    return out


def write_api_chromosomes(records: list[dict]) -> str:
    objs = []
    for key, rows in _group(records, _CHROM_ENV):
        obj = {k: v for k, v in zip(_CHROM_ENV, key) if k in rows[0]}
        obj["chromCount"] = len(rows)
        obj["chromosomes"] = {r["chrom"]: r["size"] for r in rows}
        objs.append(obj)
    return _one_or_list(objs)


def detect_api_chromosomes(text: str, filename: str) -> float:
    head = text[:4000]
    if '"chromosomes"' in head and '"chromCount"' in head and text.lstrip()[:1] in "{[":
        return 0.95
    return 0.0


# --------------------------------------------------------------------------
# chrom.sizes  (two-column TSV: name, length)

_SIZES_RE = re.compile(r"^\S+\t\d+\s*$")


def read_chrom_sizes(text: str) -> list[dict]:
    out = []
    for ln in text.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split("\t") if "\t" in ln else ln.split()
        out.append({"chrom": parts[0].strip(), "size": int(parts[1])})
    return out


def write_chrom_sizes(records: list[dict]) -> str:
    return "".join(f"{r['chrom']}\t{r['size']}\n" for r in records)


def detect_chrom_sizes(text: str, filename: str) -> float:
    lines = [ln for ln in _lines(text)[:200] if not ln.startswith("#")]
    if not lines or not all(_SIZES_RE.match(ln) for ln in lines):
        return 0.0
    n = _name(filename)
    if n.endswith((".chrom.sizes", ".chrom.sizes.txt", ".chromsizes", "chrom.sizes")):
        return 0.9
    return 0.5


# --------------------------------------------------------------------------
# chromAlias.txt  (one row per sequence; header names the naming authority of
# each column). The old hg38 bigZips file has an unlabeled header
# "# sequenceName<TAB>alias names<TAB>UCSC database: hg38", where the alias
# columns are an unordered list.

_LEGACY_NAME = "sequenceName"
_LEGACY_ALIASES = "alias names"


def _alias_header(text: str):
    for ln in text.splitlines():
        if not ln.strip():
            continue
        if ln.startswith("#"):
            body = ln[1:].strip()
            cols = [c.strip() for c in (body.split("\t") if "\t" in body else body.split())]
            return cols, True
        return None, False
    return None, False


def read_chromalias_txt(text: str) -> list[dict]:
    header, has_header = _alias_header(text)
    legacy = (not has_header) or (header and header[0] == _LEGACY_NAME)
    out = []
    for ln in text.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        cells = ln.rstrip("\r\n").split("\t")
        if legacy:
            out.append({_LEGACY_NAME: cells[0], _LEGACY_ALIASES: [c for c in cells[1:] if c]})
        else:
            cells += [""] * (len(header) - len(cells))
            out.append({h: (c if c != "" else None) for h, c in zip(header, cells)})
    return out


def write_chromalias_txt(records: list[dict]) -> str:
    if not records:
        return ""
    if _LEGACY_ALIASES in records[0]:
        lines = [f"# {_LEGACY_NAME}\t{_LEGACY_ALIASES}"]
        for r in records:
            lines.append("\t".join([r[_LEGACY_NAME], *r.get(_LEGACY_ALIASES, [])]))
        return "\n".join(lines) + "\n"
    cols: list[str] = []
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    lines = ["# " + "\t".join(cols)]
    for r in records:
        lines.append("\t".join("" if r.get(c) is None else str(r[c]) for c in cols))
    return "\n".join(lines) + "\n"


_AUTHORITIES = {"ucsc", "ensembl", "genbank", "refseq", "assembly", "ncbi"}


def detect_chromalias_txt(text: str, filename: str) -> float:
    header, has_header = _alias_header(text)
    n = _name(filename)
    if "chromalias" in n and "database" not in n and has_header:
        return 0.95
    if not has_header or not header:
        return 0.0
    if header[0] == _LEGACY_NAME and len(header) > 1 and header[1] == _LEGACY_ALIASES:
        return 0.85
    if len(_AUTHORITIES & set(header)) >= 2:
        return 0.8
    return 0.0


# --------------------------------------------------------------------------
# chromAlias database table  (goldenPath/<db>/database/chromAlias.txt.gz;
# one row per alias: alias, chrom, source)

_SOURCE_RE = re.compile(r"^[A-Za-z]+(,[A-Za-z]+)*$")


def read_chromalias_table(text: str) -> list[dict]:
    out = []
    for ln in text.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        alias, chrom, source = ln.rstrip("\r\n").split("\t")[:3]
        out.append({"alias": alias, "chrom": chrom, "source": source})
    return out


def write_chromalias_table(records: list[dict]) -> str:
    return "".join(f"{r['alias']}\t{r['chrom']}\t{r['source']}\n" for r in records)


def detect_chromalias_table(text: str, filename: str) -> float:
    lines = _lines(text)[:200]
    if not lines or lines[0].startswith("#"):
        return 0.0
    ok = 0
    for ln in lines:
        cells = ln.split("\t")
        if len(cells) != 3 or not _SOURCE_RE.match(cells[2].strip()):
            return 0.0
        if set(cells[2].strip().split(",")) & _AUTHORITIES:
            ok += 1
    return 0.9 if ok == len(lines) else 0.0


# --------------------------------------------------------------------------
# hub.txt / genomes.txt  (stanza files of "key value" lines, blank-line
# separated; "#" comments; trailing "\" continues a line)

_INT_SETTINGS = {"taxId", "orderKey"}


def _stanzas(text: str) -> list[dict]:
    stanzas: list[dict] = []
    cur: dict | None = None
    carry = ""
    for raw in text.splitlines():
        line = raw.strip()
        if carry:
            line = carry + line
            carry = ""
        if line.endswith("\\"):
            carry = line[:-1]
            continue
        if not line:
            if cur:
                stanzas.append(cur)
            cur = None
            continue
        if line.startswith("#"):
            continue
        parts = line.split(None, 1)
        key, value = parts[0], (parts[1].strip() if len(parts) > 1 else "")
        if key in _INT_SETTINGS and re.fullmatch(r"-?\d+", value):
            value = int(value)
        if cur is None:
            cur = {}
        cur[key] = value
    if carry and cur is not None:
        parts = carry.strip().split(None, 1)
        cur[parts[0]] = parts[1] if len(parts) > 1 else ""
    if cur:
        stanzas.append(cur)
    return stanzas


def _write_stanzas(records: list[dict]) -> str:
    blocks = []
    for r in records:
        blocks.append("\n".join(f"{k} {v}".rstrip() for k, v in r.items()))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _first_key(stanza: dict) -> str:
    return next(iter(stanza), "")


def read_hub_txt(text: str) -> list[dict]:
    return [s for s in _stanzas(text) if _first_key(s) == "hub"]


def read_genomes_txt(text: str) -> list[dict]:
    return [s for s in _stanzas(text) if _first_key(s) == "genome"]


_HUB_LINE = re.compile(r"(?m)^[ \t]*hub[ \t]+\S")
_GENOME_LINE = re.compile(r"(?m)^[ \t]*genome[ \t]+\S")
_HUB_KEYS = re.compile(r"(?m)^[ \t]*(shortLabel|longLabel|email|genomesFile|useOneFile)[ \t]")
_GENOME_KEYS = re.compile(r"(?m)^[ \t]*(trackDb|twoBitPath|groups|organism|scientificName|chromAlias|chromAliasBb|chromSizes|defaultPos)[ \t]")


def _looks_json(text: str) -> bool:
    return text.lstrip()[:1] in ("{", "[")


def detect_hub_txt(text: str, filename: str) -> float:
    if _looks_json(text) or not _HUB_LINE.search(text) or not _HUB_KEYS.search(text):
        return 0.0
    # a useOneFile hub.txt also holds a genome stanza; prefer the genome reader then
    return 0.7 if _GENOME_LINE.search(text) else 0.9


def detect_genomes_txt(text: str, filename: str) -> float:
    if _looks_json(text) or not _GENOME_LINE.search(text):
        return 0.0
    if _HUB_LINE.search(text):
        return 0.8
    if _GENOME_KEYS.search(text):
        return 0.9
    return 0.6 if "genomes" in _name(filename) else 0.3


# --------------------------------------------------------------------------
# /list/genarkGenomes  (hgcentral.genark rows)

def read_api_genark(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        for acc, row in (d.get("genarkGenomes") or {}).items():
            out.append({"gcAccession": acc, **row})
    return out


def write_api_genark(records: list[dict]) -> str:
    rows = {}
    for r in records:
        row = dict(r)
        rows[row.pop("gcAccession")] = row
    return _dump({"genarkGenomes": rows})


def detect_api_genark(text: str, filename: str) -> float:
    return 0.95 if '"genarkGenomes"' in text[:4000] and _looks_json(text) else 0.0


# --------------------------------------------------------------------------
# /findGenome  (hgcentral.assemblyList rows; each match is an object keyed by
# its name, beside scalar envelope keys)

def read_api_findgenome(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        for name, row in d.items():
            if isinstance(row, dict):
                out.append({"name": name, **row})
    return out


def write_api_findgenome(records: list[dict]) -> str:
    rows = {}
    for r in records:
        row = dict(r)
        rows[row.pop("name")] = row
    return _dump(rows)


def detect_api_findgenome(text: str, filename: str) -> float:
    if _looks_json(text) and '"browserExists"' in text and '"assemblyLevel"' in text:
        return 0.9
    return 0.0


# --------------------------------------------------------------------------
# /list/hubGenomes  (genome stanzas of a hub, as the API reports them)

def read_api_hubgenomes(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        env = {"hubUrl": d["hubUrl"]} if "hubUrl" in d else {}
        for genome, row in (d.get("genomes") or {}).items():
            out.append({**env, "genome": genome, **row})
    return out


def write_api_hubgenomes(records: list[dict]) -> str:
    objs = []
    for (hub_url,), rows in _group(records, ("hubUrl",)):
        genomes = {}
        for r in rows:
            row = {k: v for k, v in r.items() if k not in ("hubUrl", "genome")}
            genomes[r["genome"]] = row
        obj = {"hubUrl": hub_url} if "hubUrl" in rows[0] else {}
        obj["genomes"] = genomes
        objs.append(obj)
    return _one_or_list(objs)


def detect_api_hubgenomes(text: str, filename: str) -> float:
    head = text[:4000]
    if _looks_json(text) and '"genomes"' in head and '"trackDbFile"' in text:
        return 0.95
    return 0.0


# --------------------------------------------------------------------------
# /list/files  (download files for one genome)

_FILES_ENV = ("genome", "rsyncHost")


def read_api_files(text: str) -> list[dict]:
    out = []
    for d in _responses(text):
        env = {k: d[k] for k in _FILES_ENV if k in d}
        for row in d.get("urlList") or []:
            out.append({**env, **row})
    return out


def write_api_files(records: list[dict]) -> str:
    objs = []
    for key, rows in _group(records, _FILES_ENV):
        obj = {k: v for k, v in zip(_FILES_ENV, key) if k in rows[0]}
        obj["urlList"] = [{k: v for k, v in r.items() if k not in _FILES_ENV} for r in rows]
        objs.append(obj)
    return _one_or_list(objs)


def detect_api_files(text: str, filename: str) -> float:
    head = text[:4000]
    if _looks_json(text) and '"urlList"' in head and '"sizeBytes"' in head:
        return 0.95
    return 0.0


# --------------------------------------------------------------------------
# md5sum.txt  (GNU md5sum output: "<md5>  <file>")

_MD5_RE = re.compile(r"^([0-9a-fA-F]{32}) [ *](.+)$")


def read_md5sum(text: str) -> list[dict]:
    out = []
    for ln in text.splitlines():
        if not ln.strip():
            continue
        m = _MD5_RE.match(ln.rstrip("\r\n"))
        if m:
            out.append({"md5": m.group(1), "file": m.group(2)})
    return out


def write_md5sum(records: list[dict]) -> str:
    return "".join(f"{r['md5']}  {r['file']}\n" for r in records)


def detect_md5sum(text: str, filename: str) -> float:
    lines = _lines(text)[:200]
    if not lines or not all(_MD5_RE.match(ln) for ln in lines):
        return 0.0
    n = _name(filename)
    if "md5checksums" in n or all(_MD5_RE.match(ln).group(2).startswith("./") for ln in lines):
        return 0.3  # NCBI md5checksums.txt; ncbi.py claims those
    return 0.85 if "md5" in n else 0.6


# --------------------------------------------------------------------------

FORMATS = [
    Format("ucsc_dbdb", SOURCE,
           "UCSC REST API /list/ucscGenomes: one record per UCSC database genome (hgcentral.dbDb row)",
           read_dbdb, write_dbdb, detect_dbdb, (".json",)),
    Format("ucsc_api_chromosomes", SOURCE,
           "UCSC REST API /list/chromosomes: one record per sequence name and size of a UCSC or hub genome",
           read_api_chromosomes, write_api_chromosomes, detect_api_chromosomes, (".json",)),
    Format("ucsc_chrom_sizes", SOURCE,
           "UCSC chrom.sizes: two-column tab-separated sequence name and length, one record per sequence",
           read_chrom_sizes, write_chrom_sizes, detect_chrom_sizes, (".chrom.sizes", ".sizes", ".txt")),
    Format("ucsc_chromalias_txt", SOURCE,
           "UCSC chromAlias.txt: one record per sequence; columns are names of that sequence under each naming authority",
           read_chromalias_txt, write_chromalias_txt, detect_chromalias_txt, (".txt",)),
    Format("ucsc_chromalias_table", SOURCE,
           "UCSC chromAlias database table: one record per alias (alias, UCSC chrom, naming source)",
           read_chromalias_table, write_chromalias_table, detect_chromalias_table, (".txt", ".tsv")),
    Format("ucsc_hub_txt", SOURCE,
           "UCSC track/assembly hub hub.txt: the hub stanza (hub id, labels, contact, genomes file)",
           read_hub_txt, _write_stanzas, detect_hub_txt, (".txt",)),
    Format("ucsc_genomes_txt", SOURCE,
           "UCSC hub genome stanzas (genomes.txt, or inside a useOneFile hub.txt): one record per hub genome",
           read_genomes_txt, _write_stanzas, detect_genomes_txt, (".txt",)),
    Format("ucsc_api_genark", SOURCE,
           "UCSC REST API /list/genarkGenomes: one record per GenArk assembly hub (hgcentral.genark row)",
           read_api_genark, write_api_genark, detect_api_genark, (".json",)),
    Format("ucsc_api_findgenome", SOURCE,
           "UCSC REST API /findGenome: one record per matching genome (hgcentral.assemblyList row)",
           read_api_findgenome, write_api_findgenome, detect_api_findgenome, (".json",)),
    Format("ucsc_api_hubgenomes", SOURCE,
           "UCSC REST API /list/hubGenomes: one record per genome stanza of a hub, as parsed by the browser",
           read_api_hubgenomes, write_api_hubgenomes, detect_api_hubgenomes, (".json",)),
    Format("ucsc_api_files", SOURCE,
           "UCSC REST API /list/files: one record per downloadable file of a genome (path, size, date)",
           read_api_files, write_api_files, detect_api_files, (".json",)),
    Format("ucsc_md5sum", SOURCE,
           "UCSC download md5sum.txt: one record per file checksum (md5, file name)",
           read_md5sum, write_md5sum, detect_md5sum, (".txt", ".md5")),
]
