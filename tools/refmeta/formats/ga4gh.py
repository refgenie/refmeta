"""GA4GH adapters: refget seqcol, refget sequences, SeqRepo, VRS, SAM and VCF headers.

See sources/ga4gh/README.md for where each format comes from. Formats:

- ga4gh_seqcol_level2: a canonical (level 2) sequence collection, the JSON
  object served by ``/collection/<digest>?level=2``. One record per
  collection; collated attributes stay as arrays (element i belongs to
  sequence i).
- ga4gh_seqcol_level1: the level 1 collection (one digest per attribute).
- ga4gh_refget_metadata: refget sequences ``/sequence/<id>/metadata``
  response. Keys are dotted (``metadata.md5``). The ``aliases`` list of
  objects is split into aligned lists ``metadata.aliases[].alias`` and
  ``metadata.aliases[].naming_authority`` (same convention as fhr.py).
- ga4gh_seqrepo_metadata: SeqRepo REST ``/seqrepo/1/metadata/<alias>``
  response; ``aliases`` stays a list of ``namespace:alias`` strings.
- ga4gh_vrs_sequence_reference: VRS 2.x SequenceReference objects. read()
  collects every object with ``type: SequenceReference`` anywhere in the
  JSON/YAML document, so a whole VRS Allele or service response works.
- ga4gh_sam_header_sq: SAM header ``@SQ`` lines (also .dict files); one
  record per line, keyed by the two-letter tag.
- ga4gh_vcf_header_contig: VCF ``##contig=<...>`` lines; one record per line.
- ga4gh_vcf_header_reference: the file-level VCF lines ``##fileformat``,
  ``##reference`` and ``##assembly``; one record per file. A structured
  ``##reference=<ID=..,accession=..>`` (as EVA writes it) becomes
  ``reference.ID``, ``reference.accession`` ...

Also exported: level0_digest() and level1_digests(), which compute seqcol
digests from a level 2 or level 1 record (the digest is not stored in the
served object).

Standard library plus pyyaml only, text in and text out (runs under Pyodide).
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any, Iterator

import yaml

from . import Format

SOURCE = "ga4gh"

# ---------------------------------------------------------------- helpers


def _load(text: str, allow_yaml: bool = True) -> Any:
    """Parse JSON, falling back to YAML. Raises ValueError if neither works."""
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    if allow_yaml:
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"not JSON or YAML: {exc}") from exc
    raise ValueError("not JSON")


def _try_json(text: str, filename: str = "") -> Any:
    """Cheap parse for detect(): JSON, or YAML only for .yaml/.yml files."""
    s = text.lstrip()
    if s[:1] in ("{", "["):
        try:
            return json.loads(text)
        except ValueError:
            return None
    if filename.lower().endswith((".yaml", ".yml")):
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            return None
    return None


def _as_list(obj: Any) -> list:
    if isinstance(obj, list):
        return obj
    if obj is None:
        return []
    return [obj]


def _dump_json(records: list[dict]) -> str:
    obj: Any = records[0] if len(records) == 1 else records
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


SEQCOL_REQUIRED = ("names", "lengths", "sequences")  # seqcol_minimal_v1.0.0.json "required"


def _write_seqcol(level: int):
    """A seqcol writer that refuses records missing a required attribute, so it never
    writes an object the seqcol schema rejects (for example names and lengths only)."""
    def write(records: list[dict]) -> str:
        for rec in records:
            missing = [k for k in SEQCOL_REQUIRED if rec.get(k) in (None, [], "")]
            if level == 2 and not missing:
                missing = [k for k in SEQCOL_REQUIRED
                           if not isinstance(rec[k], list) or any(v is None for v in rec[k])]
            if missing:
                raise ValueError(f"a level {level} sequence collection needs "
                                 f"{', '.join(SEQCOL_REQUIRED)}; this record has no complete "
                                 f"{', '.join(missing)}")
        return _dump_json(records)
    return write


def _ext_bonus(filename: str, exts: tuple[str, ...]) -> float:
    return 0.05 if filename and filename.lower().endswith(exts) else 0.0


# ---------------------------------------------------------------- seqcol

SEQCOL_ATTRS = (
    "names", "lengths", "sequences", "name_length_pairs",
    "sorted_name_length_pairs", "sorted_sequences", "accessions",
)
SEQCOL_INHERENT = ("names", "sequences")


def _canonical(obj: Any) -> bytes:
    """RFC-8785-style canonical JSON for the value types seqcol uses."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")


def _sha512t24u(data: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha512(data).digest()[:24]).decode("ascii")


def level1_digests(record: dict) -> dict:
    """Digest each array attribute of a level 2 record (level 1 view).

    The recommended ancillary attributes (seqcol spec section 5:
    name_length_pairs, sorted_name_length_pairs, sorted_sequences) are
    derived from names, lengths and sequences when absent. Attributes
    already digested (strings) are passed through.
    """
    out = {}
    for key, value in record.items():
        if isinstance(value, list):
            out[key] = _sha512t24u(_canonical(value))
        elif isinstance(value, str):
            out[key] = value
    names, lengths, seqs = record.get("names"), record.get("lengths"), record.get("sequences")
    if isinstance(names, list) and isinstance(lengths, list):
        pairs = [{"length": length, "name": name} for name, length in zip(names, lengths)]
        out.setdefault("name_length_pairs", _sha512t24u(_canonical(pairs)))
        if "sorted_name_length_pairs" not in out:
            sorted_pairs = sorted(_sha512t24u(_canonical(p)) for p in pairs)
            out["sorted_name_length_pairs"] = _sha512t24u(_canonical(sorted_pairs))
    if isinstance(seqs, list):
        out.setdefault("sorted_sequences", _sha512t24u(_canonical(sorted(seqs))))
    return out


def level0_digest(record: dict, inherent: tuple[str, ...] = SEQCOL_INHERENT) -> str:
    """Top-level seqcol digest from a level 1 or level 2 record."""
    l1 = level1_digests(record)
    return _sha512t24u(_canonical({k: l1[k] for k in inherent}))


def _seqcol_objects(text: str) -> list[dict]:
    data = _load(text)
    objs = _as_list(data)
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("a sequence collection must be a JSON object")
    return objs


def _read_seqcol_l2(text: str) -> list[dict]:
    out = []
    for obj in _seqcol_objects(text):
        if any(isinstance(v, str) for k, v in obj.items() if k in ("names", "sequences", "lengths")):
            raise ValueError("this looks like a level 1 collection (digests, not arrays)")
        out.append(dict(obj))
    return out


def _read_seqcol_l1(text: str) -> list[dict]:
    out = []
    for obj in _seqcol_objects(text):
        if any(isinstance(v, list) for v in obj.values()):
            raise ValueError("this looks like a level 2 collection (arrays, not digests)")
        out.append(dict(obj))
    return out


def _detect_seqcol(level: int):
    def detect(text: str, filename: str = "") -> float:
        data = _try_json(text, filename)
        objs = _as_list(data)
        if not objs or not all(isinstance(o, dict) for o in objs):
            return 0.0
        o = objs[0]
        if "names" not in o or ("sequences" not in o and "lengths" not in o):
            return 0.0
        want = list if level == 2 else str
        if all(isinstance(o.get(k), want) for k in ("names", "sequences", "lengths") if k in o):
            score = 0.9
            if level == 2 and isinstance(o.get("sequences"), list) and o["sequences"] \
                    and str(o["sequences"][0]).startswith("SQ."):
                score = 0.95
            if level == 1 and re.fullmatch(r"[A-Za-z0-9_-]{32}", str(o.get("names", ""))):
                score = 0.95
            return min(1.0, score + _ext_bonus(filename, (".json",)))
        return 0.0
    return detect


# ---------------------------------------------------------------- refget sequences metadata

_REFGET_SCALARS = ("id", "md5", "trunc512", "ga4gh", "length")


def _read_refget_metadata(text: str) -> list[dict]:
    out = []
    for obj in _as_list(_load(text)):
        if not isinstance(obj, dict) or not isinstance(obj.get("metadata"), dict):
            raise ValueError("refget metadata must be an object with a 'metadata' object")
        md = obj["metadata"]
        rec: dict = {}
        for key, value in md.items():
            if key == "aliases" and isinstance(value, list):
                rec["metadata.aliases[].alias"] = [a.get("alias") if isinstance(a, dict) else a for a in value]
                rec["metadata.aliases[].naming_authority"] = [
                    a.get("naming_authority") if isinstance(a, dict) else None for a in value
                ]
            else:
                rec[f"metadata.{key}"] = value
        out.append(rec)
    return out


def _write_refget_metadata(records: list[dict]) -> str:
    objs = []
    for rec in records:
        md: dict = {}
        for key, value in rec.items():
            if key.startswith("metadata.aliases[]."):
                continue
            md[key[len("metadata."):] if key.startswith("metadata.") else key] = value
        if "metadata.aliases[].alias" in rec or "metadata.aliases[].naming_authority" in rec:
            names = rec.get("metadata.aliases[].alias") or []
            auths = rec.get("metadata.aliases[].naming_authority") or []
            n = max(len(names), len(auths))
            md["aliases"] = [
                {"alias": names[i] if i < len(names) else None,
                 "naming_authority": auths[i] if i < len(auths) else None}
                for i in range(n)
            ]
        objs.append({"metadata": md})
    return _dump_json(objs)


def _detect_refget_metadata(text: str, filename: str = "") -> float:
    data = _try_json(text, filename)
    objs = _as_list(data)
    if not objs or not isinstance(objs[0], dict):
        return 0.0
    md = objs[0].get("metadata")
    if isinstance(md, dict) and "length" in md and ("md5" in md or "aliases" in md or "ga4gh" in md):
        return 0.95
    return 0.0


# ---------------------------------------------------------------- SeqRepo REST metadata


def _read_seqrepo_metadata(text: str) -> list[dict]:
    out = []
    for obj in _as_list(_load(text)):
        if not isinstance(obj, dict) or "aliases" not in obj:
            raise ValueError("SeqRepo metadata must be an object with 'aliases'")
        out.append(dict(obj))
    return out


def _detect_seqrepo_metadata(text: str, filename: str = "") -> float:
    data = _try_json(text, filename)
    objs = _as_list(data)
    if not objs or not isinstance(objs[0], dict):
        return 0.0
    o = objs[0]
    aliases = o.get("aliases")
    if isinstance(aliases, list) and "length" in o and ("alphabet" in o or "added" in o):
        if all(isinstance(a, str) and ":" in a for a in aliases[:20]):
            return 0.9
        return 0.6
    return 0.0


# ---------------------------------------------------------------- VRS SequenceReference


def _walk_seqrefs(obj: Any) -> Iterator[dict]:
    if isinstance(obj, dict):
        if obj.get("type") == "SequenceReference":
            yield obj
            return
        for value in obj.values():
            yield from _walk_seqrefs(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_seqrefs(value)


def _read_vrs_seqref(text: str) -> list[dict]:
    refs = [dict(r) for r in _walk_seqrefs(_load(text))]
    if not refs:
        raise ValueError("no VRS SequenceReference object found")
    return refs


def _detect_vrs_seqref(text: str, filename: str = "") -> float:
    if "SequenceReference" not in text:
        return 0.0
    data = _try_json(text, filename)
    if data is None:
        return 0.0
    if isinstance(data, dict) and data.get("type") == "SequenceReference":
        return 0.95
    if isinstance(data, list) and data and all(
            isinstance(d, dict) and d.get("type") == "SequenceReference" for d in data):
        return 0.95
    return 0.6 if any(True for _ in _walk_seqrefs(data)) else 0.0


# ---------------------------------------------------------------- SAM @SQ

SAM_INT_TAGS = ("LN",)
SAM_TAG_ORDER = ("SN", "LN", "AH", "AN", "AS", "DS", "M5", "SP", "TP", "UR")


def _read_sam_sq(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if not line.startswith("@SQ\t"):
            continue
        rec: dict = {}
        for field in line.rstrip("\r").split("\t")[1:]:
            if len(field) < 3 or field[2] != ":":
                raise ValueError(f"bad @SQ field {field!r}")
            tag, value = field[:2], field[3:]
            if tag in SAM_INT_TAGS:
                try:
                    value = int(value)
                except ValueError:
                    pass
            rec[tag] = value
        out.append(rec)
    if not out:
        raise ValueError("no @SQ lines found")
    return out


def _write_sam_sq(records: list[dict]) -> str:
    lines = []
    for rec in records:
        tags = [t for t in SAM_TAG_ORDER if t in rec] + [t for t in rec if t not in SAM_TAG_ORDER]
        fields = [f"{t}:{rec[t]}" for t in tags if rec[t] is not None]
        lines.append("@SQ\t" + "\t".join(fields))
    return "\n".join(lines) + "\n"


def _detect_sam_sq(text: str, filename: str = "") -> float:
    head = text[:20000]
    if "\n@SQ\t" in "\n" + head:
        return min(1.0, 0.9 + _ext_bonus(filename, (".sam", ".dict")))
    if head.startswith("@HD\t"):
        return 0.4
    return 0.0


# ---------------------------------------------------------------- VCF header

VCF_INT_KEYS = ("length",)
_NEEDS_QUOTE = re.compile(r'[\s,"<>=]')


def _split_structured(body: str) -> list[tuple[str, str]]:
    """Split 'k=v,k="v, with comma"' into pairs, unquoting quoted values."""
    pairs = []
    i, n = 0, len(body)
    while i < n:
        eq = body.find("=", i)
        if eq < 0:
            raise ValueError(f"bad structured field near {body[i:]!r}")
        key = body[i:eq]
        j = eq + 1
        if j < n and body[j] == '"':
            j += 1
            buf = []
            while j < n and body[j] != '"':
                if body[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(body[j])
                j += 1
            value = "".join(buf)
            j += 1  # closing quote
            if j < n and body[j] != ",":
                raise ValueError(f"junk after quoted value in {body!r}")
        else:
            k = body.find(",", j)
            k = n if k < 0 else k
            value = body[j:k]
            j = k
        pairs.append((key, value))
        i = j + 1
    return pairs


def _parse_meta(line: str) -> tuple[str, Any]:
    """'##key=value' -> (key, str) or (key, list of pairs) when structured."""
    key, _, value = line[2:].partition("=")
    if value.startswith("<") and value.endswith(">"):
        return key, _split_structured(value[1:-1])
    return key, value


def _fmt_value(value: Any) -> str:
    s = str(value)
    if _NEEDS_QUOTE.search(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _header_lines(text: str) -> Iterator[str]:
    for line in text.splitlines():
        line = line.rstrip("\r")
        if not line.startswith("#"):
            break
        yield line


def _read_vcf_contig(text: str) -> list[dict]:
    out = []
    for line in _header_lines(text):
        if not line.startswith("##contig="):
            continue
        _, pairs = _parse_meta(line)
        if isinstance(pairs, str):
            raise ValueError(f"##contig line is not structured: {line!r}")
        rec: dict = {}
        for key, value in pairs:
            if key in VCF_INT_KEYS:
                try:
                    value = int(value)
                except ValueError:
                    pass
            rec[key] = value
        out.append(rec)
    if not out:
        raise ValueError("no ##contig lines found")
    return out


def _write_vcf_contig(records: list[dict]) -> str:
    lines = ["##fileformat=VCFv4.5"]
    for rec in records:
        keys = (["ID"] if "ID" in rec else []) + [k for k in rec if k != "ID"]
        body = ",".join(f"{k}={_fmt_value(rec[k])}" for k in keys if rec[k] is not None)
        lines.append(f"##contig=<{body}>")
    lines.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    return "\n".join(lines) + "\n"


VCF_FILE_KEYS = ("fileformat", "reference", "assembly")


def _read_vcf_reference(text: str) -> list[dict]:
    if not text.lstrip().startswith("##fileformat=VCF"):
        raise ValueError("not a VCF header (no ##fileformat=VCF line)")
    rec: dict = {}
    for line in _header_lines(text):
        if not line.startswith("##"):
            continue
        key, value = _parse_meta(line)
        if key not in VCF_FILE_KEYS:
            continue
        if isinstance(value, list):
            for sub, subval in value:
                rec[f"{key}.{sub}"] = subval
        else:
            rec[key] = value
    return [rec]


def _write_vcf_reference(records: list[dict]) -> str:
    if len(records) != 1:
        raise ValueError("a VCF header holds exactly one file-level record")
    rec = records[0]
    lines = [f"##fileformat={rec.get('fileformat') or 'VCFv4.5'}"]
    for key in ("reference", "assembly"):
        if rec.get(key) is not None:
            lines.append(f"##{key}={rec[key]}")
        subs = [(k.split(".", 1)[1], v) for k, v in rec.items() if k.startswith(key + ".")]
        if subs:
            body = ",".join(f"{k}={_fmt_value(v)}" for k, v in subs if v is not None)
            lines.append(f"##{key}=<{body}>")
    lines.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    return "\n".join(lines) + "\n"


def _is_vcf(text: str) -> bool:
    return text.lstrip()[:16].startswith("##fileformat=VCF")


def _detect_vcf_contig(text: str, filename: str = "") -> float:
    if not _is_vcf(text):
        return 0.0
    head = text[:200000]
    return 0.9 if "\n##contig=<" in head else 0.3


def _detect_vcf_reference(text: str, filename: str = "") -> float:
    if not _is_vcf(text):
        return 0.0
    head = text[:200000]
    has_ref = "\n##reference=" in head or "\n##assembly=" in head
    has_contig = "\n##contig=<" in head
    if has_ref:
        return 0.85
    return 0.5 if not has_contig else 0.4


# ---------------------------------------------------------------- registry

FORMATS = [
    Format(
        id="ga4gh_seqcol_level2",
        source=SOURCE,
        description="GA4GH refget sequence collection, canonical level 2 JSON (collated arrays)",
        read=_read_seqcol_l2,
        write=_write_seqcol(2),
        detect=_detect_seqcol(2),
        extensions=(".json",),
    ),
    Format(
        id="ga4gh_seqcol_level1",
        source=SOURCE,
        description="GA4GH refget sequence collection, level 1 JSON (one digest per attribute)",
        read=_read_seqcol_l1,
        write=_write_seqcol(1),
        detect=_detect_seqcol(1),
        extensions=(".json",),
    ),
    Format(
        id="ga4gh_refget_metadata",
        source=SOURCE,
        description="GA4GH refget sequences /sequence/<id>/metadata response",
        read=_read_refget_metadata,
        write=_write_refget_metadata,
        detect=_detect_refget_metadata,
        extensions=(".json",),
    ),
    Format(
        id="ga4gh_seqrepo_metadata",
        source=SOURCE,
        description="biocommons SeqRepo REST /seqrepo/1/metadata/<alias> response (namespaced aliases)",
        read=_read_seqrepo_metadata,
        write=_dump_json,
        detect=_detect_seqrepo_metadata,
        extensions=(".json",),
    ),
    Format(
        id="ga4gh_vrs_sequence_reference",
        source=SOURCE,
        description="GA4GH VRS 2.x SequenceReference objects (found anywhere in a JSON/YAML document)",
        read=_read_vrs_seqref,
        write=_dump_json,
        detect=_detect_vrs_seqref,
        extensions=(".json", ".yaml", ".yml"),
    ),
    Format(
        id="ga4gh_sam_header_sq",
        source=SOURCE,
        description="SAM header @SQ lines (SAM/CRAM headers, Picard .dict files), one record per sequence",
        read=_read_sam_sq,
        write=_write_sam_sq,
        detect=_detect_sam_sq,
        extensions=(".dict", ".sam"),
    ),
    Format(
        id="ga4gh_vcf_header_contig",
        source=SOURCE,
        description="VCF header ##contig lines, one record per contig",
        read=_read_vcf_contig,
        write=_write_vcf_contig,
        detect=_detect_vcf_contig,
        extensions=(".vcf",),
    ),
    Format(
        id="ga4gh_vcf_header_reference",
        source=SOURCE,
        description="VCF header file-level ##fileformat, ##reference and ##assembly lines, one record per file",
        read=_read_vcf_reference,
        write=_write_vcf_reference,
        detect=_detect_vcf_reference,
        extensions=(".vcf",),
    ),
]
