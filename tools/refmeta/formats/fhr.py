"""FHR (FAIR Header Reference genome) adapters.

Spec: https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification (release
v0.6.0, FHR schemaVersion "2.1"), plus the RefgetStore sidecar variant written by
gtars (gtars-refget/src/store/fhr_metadata.rs). See sources/fhr/README.md.

One FHR record describes one genome file. Every format here holds exactly one
record, so read() returns a one-item list and write() takes a one-item list.

Native records are flat. FHR's nested values are flattened like this (the same
path notation the FHR mapping tables use):

- fixed nested objects become dotted keys: ``taxon.name``, ``accessionID.url``,
  ``vitalStats.N50``;
- lists of objects become one list per sub-key, aligned by position, with None
  where an item lacks that key: ``metadataAuthor[].name``,
  ``assemblySoftware[].commandLineOption`` (a list of lists);
- everything else keeps its top-level key, including lists of strings
  (``genomeSynonym``), the legacy string form of ``assemblySoftware``, and
  extension fields (``x-...`` keys, or the sidecar's non-standard keys such as
  ``assemblySource``), whose values are kept exactly as written.

Standard library plus pyyaml only, text in and text out (runs under Pyodide).
"""
from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from typing import Any, Optional

import yaml

from . import Format

SOURCE = "fhr"

# fhr.json (v0.6.0, FHR 2.1) top-level properties, in schema order.
STANDARD_FIELDS = (
    "schema", "schemaVersion", "genome", "genomeSynonym", "taxon", "version",
    "metadataAuthor", "assemblyAuthor", "dateCreated", "voucherSpecimen",
    "accessionID", "instrument", "scholarlyArticle", "documentation",
    "identifier", "relatedLink", "funding", "reuseConditions", "masking",
    "vitalStats", "checksum", "assemblySoftware", "assemblyProtocol", "seqcol_id",
)
NESTED_OBJECTS = ("taxon", "accessionID", "vitalStats")
OBJECT_LISTS = ("metadataAuthor", "assemblyAuthor", "assemblySoftware")

# gtars FhrMetadata field order (serde camelCase), used when writing sidecars.
SIDECAR_FIELDS = (
    "schema", "schemaVersion", "genome", "taxon", "version", "metadataAuthor",
    "assemblyAuthor", "dateCreated", "voucherSpecimen", "masking", "checksum",
    "genomeSynonym", "accessionID", "instrument", "scholarlyArticle",
    "documentation", "identifier", "license", "relatedLink", "funding",
    "vitalStats",
)
SIDECAR_NESTED_ORDER = {
    "taxon": ("name", "uri"),
    "accessionID": ("name", "url"),
    "vitalStats": ("L50", "N50", "L90", "totalBasePairs", "numberContigs",
                   "numberScaffolds", "readTechnology"),
    "metadataAuthor": ("name", "uri"),
    "assemblyAuthor": ("name", "uri"),
}
# Not a key in the JSON body: gtars keeps it in a #[serde(skip)] field and names
# the file after it (<seqcolDigest>.fhr.json). read() never emits it.
SIDECAR_DIGEST_KEY = "seqcolDigest"

FHR_MICRODATA_ITEMTYPE = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json"
)
_ITEMTYPE_RE = re.compile(
    r"^https://raw\.githubusercontent\.com/FAIR-bioHeaders/"
    r"(FHR-Specification|FAIR-bioHeaders-Specification)/main/fhr\.json$"
)
_SIDECAR_NAME_RE = re.compile(r"([A-Za-z0-9_-]{32})\.fhr\.json$")
_FHR_SCHEMA_HINT = re.compile(r"fair-bioheaders|fhr-specification|ffrgs", re.I)
_LINK_RE = re.compile(r"^(?:https?|ftp)://[^\s/?#]+", re.I)
_CTRL_OR_SPACE = re.compile(r"[\s\x00-\x1f\x7f‎‏‪-‮⁦-⁩]")

# The published FHR JSON-LD context (jsonld/fhr.context.jsonld, release v0.6.0),
# embedded because rule J7 says writers embed it.
_JSONLD_CONTEXT_TEXT = r"""{"@version":1.1,"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","xsd":"http://www.w3.org/2001/XMLSchema#","dct":"http://purl.org/dc/terms/","Dataset":"sdo:Dataset","Taxon":"sdo:Taxon","Person":"sdo:Person","Organization":"sdo:Organization","Agent":"fhr:Agent","PropertyValue":"sdo:PropertyValue","VitalStats":"fhr:VitalStats","SoftwareApplication":"sdo:SoftwareApplication","schema":{"@id":"sdo:schemaVersion","@type":"@id"},"schemaVersion":{"@id":"fhr:schemaVersion"},"genome":{"@id":"sdo:name"},"genomeSynonym":{"@id":"sdo:alternateName","@container":"@set"},"taxon":{"@id":"sdo:about","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","Taxon":"sdo:Taxon","name":{"@id":"sdo:name"},"uri":"@id"}]},"version":{"@id":"sdo:version"},"metadataAuthor":{"@id":"fhr:metadataAuthor","@container":"@set","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","Person":"sdo:Person","Organization":"sdo:Organization","Agent":"fhr:Agent","name":{"@id":"sdo:name"},"uri":"@id","nameType":{"@id":"fhr:nameType"}}]},"assemblyAuthor":{"@id":"sdo:creator","@container":"@set","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","Person":"sdo:Person","Organization":"sdo:Organization","Agent":"fhr:Agent","name":{"@id":"sdo:name"},"uri":"@id","nameType":{"@id":"fhr:nameType"}}]},"dateCreated":{"@id":"sdo:dateCreated","@type":"xsd:date"},"voucherSpecimen":{"@id":"fhr:voucherSpecimen"},"accessionID":{"@id":"fhr:accessionID","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","PropertyValue":"sdo:PropertyValue","name":{"@id":"sdo:name"},"url":{"@id":"sdo:url","@type":"@id"}}]},"instrument":{"@id":"fhr:instrument","@container":"@set"},"scholarlyArticle":{"@id":"sdo:citation"},"documentation":{"@id":"sdo:description"},"identifier":{"@id":"sdo:identifier","@container":"@set"},"relatedLink":{"@id":"fhr:relatedLink","@type":"@id","@container":"@set"},"funding":{"@id":"sdo:funding"},"reuseConditions":{"@id":"sdo:license"},"masking":{"@id":"fhr:masking"},"vitalStats":{"@id":"fhr:vitalStats","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","VitalStats":"fhr:VitalStats","L50":{"@id":"fhr:L50"},"N50":{"@id":"fhr:N50"},"L90":{"@id":"fhr:L90"},"totalBasePairs":{"@id":"fhr:totalBasePairs"},"numberContigs":{"@id":"fhr:numberContigs"},"numberScaffolds":{"@id":"fhr:numberScaffolds"},"readTechnology":{"@id":"fhr:readTechnology"},"N90":{"@id":"fhr:N90"},"scaffoldN50":{"@id":"fhr:scaffoldN50"},"scaffoldN90":{"@id":"fhr:scaffoldN90"},"scaffoldL50":{"@id":"fhr:scaffoldL50"},"scaffoldL90":{"@id":"fhr:scaffoldL90"},"gcContent":{"@id":"fhr:gcContent"}}]},"checksum":{"@id":"fhr:checksum"},"assemblySoftware":{"@id":"fhr:assemblySoftware","@container":"@set","@context":[null,{"@protected":true,"sdo":"http://schema.org/","fhr":"https://w3id.org/fair-bioheaders/terms#","SoftwareApplication":"sdo:SoftwareApplication","name":{"@id":"sdo:name"},"uri":{"@id":"sdo:url","@type":"@id"},"version":{"@id":"sdo:softwareVersion"},"commandLineOption":{"@id":"fhr:commandLineOption","@container":"@list"}}]},"assemblyProtocol":{"@id":"fhr:assemblyProtocol","@type":"@id"},"seqcol_id":{"@id":"fhr:seqcol_id"},"subjectOf":{"@id":"sdo:subjectOf","@type":"@id"},"keywords":{"@id":"sdo:keywords","@container":"@set"},"url":{"@id":"sdo:url","@type":"@id"},"conformsTo":{"@id":"dct:conformsTo","@type":"@id"}}"""
JSONLD_CONTEXT = json.loads(_JSONLD_CONTEXT_TEXT)
JSONLD_CONTEXT_URLS = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/main/jsonld/fhr.context.jsonld",
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/jsonld/fhr.context.jsonld",
)

# Numeric and list fields, for microdata written without data-fhr-type (rule M3).
_INT_FIELDS = {"L50", "N50", "L90", "N90", "totalBasePairs", "numberContigs",
               "numberScaffolds", "scaffoldN50", "scaffoldN90", "scaffoldL50",
               "scaffoldL90"}
_NUMBER_FIELDS = {"gcContent"}
_LIST_FIELDS = {"genomeSynonym", "metadataAuthor", "assemblyAuthor", "instrument",
                "identifier", "relatedLink", "commandLineOption"}


# --------------------------------------------------------------------------
# flatten / unflatten
# --------------------------------------------------------------------------

def flatten(obj: dict) -> dict:
    """Nested FHR metadata -> flat native record (see module docstring)."""
    if not isinstance(obj, dict):
        raise ValueError("FHR metadata must be a mapping at the top level")
    out: dict = {}
    for key, value in obj.items():
        key = str(key)
        if key in NESTED_OBJECTS and isinstance(value, dict) and value:
            for sub, sub_value in value.items():
                out[f"{key}.{sub}"] = sub_value
        elif (key in OBJECT_LISTS and isinstance(value, list) and value
              and all(isinstance(item, dict) for item in value)):
            subkeys: list = []
            for item in value:
                for sub in item:
                    if sub not in subkeys:
                        subkeys.append(sub)
            if not subkeys:  # e.g. [{}]: nothing to align, keep as written
                out[key] = value
                continue
            for sub in subkeys:
                out[f"{key}[].{sub}"] = [item.get(sub) for item in value]
        else:
            out[key] = value
    return out


def unflatten(record: dict) -> dict:
    """Flat native record -> nested FHR metadata (inverse of flatten)."""
    out: dict = {}
    for key, value in record.items():
        head, sep, sub = key.partition("[].")
        if sep and head in OBJECT_LISTS:
            items = out.setdefault(head, [])
            if not isinstance(items, list):
                raise ValueError(f"{head} given both as a value and as {key}")
            values = value if isinstance(value, list) else [value]
            while len(items) < len(values):
                items.append({})
            for i, v in enumerate(values):
                if v is not None:
                    items[i][sub] = v
            continue
        head, sep, sub = key.partition(".")
        if sep and head in NESTED_OBJECTS:
            obj = out.setdefault(head, {})
            if not isinstance(obj, dict):
                raise ValueError(f"{head} given both as a value and as {key}")
            obj[sub] = value
            continue
        out[key] = value
    return out


def _one(records: list) -> dict:
    if len(records) != 1:
        raise ValueError(f"an FHR file holds exactly one record, got {len(records)}")
    return unflatten(records[0])


def _strip_bom(text: str) -> str:
    return text[1:] if text.startswith("﻿") else text


# --------------------------------------------------------------------------
# YAML (rule R12: no implicit timestamps; quote anything YAML 1.1 or 1.2 retypes)
# --------------------------------------------------------------------------

class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class _Dumper(yaml.SafeDumper):
    pass


_YAML12_NON_STR = re.compile(
    r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+"
    r"|[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
    r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)"
    r"|null|Null|NULL|~|true|True|TRUE|false|False|FALSE"
    r"|[yY]|[nN]|yes|Yes|YES|no|No|NO|on|On|ON|off|Off|OFF)$"
)


def _represent_str(dumper, data):
    if data == "" or _YAML12_NON_STR.match(data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    if "\n" in data:  # literal block keeps multi-line text readable
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _represent_str)


def _yaml_load(text: str) -> Any:
    return yaml.load(text, Loader=_Loader)


def _dq_escape(s: str) -> str:
    """A YAML double-quoted scalar with > and @ escaped (rule R11)."""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == ">":
            out.append("\\x3E")
        elif ch == "@":
            out.append("\\x40")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20 or ord(ch) == 0x7f or ch in "\x85  ":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _yaml_dump(obj: dict, fasta_safe: bool = False) -> str:
    placeholders: dict = {}
    if fasta_safe:
        def swap(v):
            if isinstance(v, str) and (">" in v or "@" in v):
                token = f"FHRQUOTED{len(placeholders):06d}X"
                placeholders[token] = _dq_escape(v)
                return token
            if isinstance(v, list):
                return [swap(x) for x in v]
            if isinstance(v, dict):
                return {k: swap(x) for k, x in v.items()}
            return v
        obj = swap(obj)
    text = yaml.dump(obj, Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False)
    for token, quoted in placeholders.items():
        text = text.replace(token, quoted)
    return text


# --------------------------------------------------------------------------
# helpers for detection
# --------------------------------------------------------------------------

def _looks_fhr(obj: Any) -> float:
    """How much a parsed mapping looks like FHR metadata (0..1)."""
    if not isinstance(obj, dict):
        return 0.0
    schema = obj.get("schema")
    if isinstance(schema, str) and _FHR_SCHEMA_HINT.search(schema) and \
            "fhp.json" not in schema and "fhgff3" not in schema and "/fhp/" not in schema:
        return 0.9
    hits = sum(1 for k in ("genome", "taxon", "schemaVersion", "assemblyAuthor",
                           "metadataAuthor", "genomeSynonym", "accessionID", "masking")
               if k in obj)
    return 0.5 if hits >= 3 else 0.0


def _parse_json_object(text: str) -> Optional[dict]:
    text = _strip_bom(text).lstrip()
    if not text.startswith("{"):
        return None
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def sidecar_digest(filename: str) -> Optional[str]:
    """The seqcol digest a RefgetStore sidecar is named after, or None."""
    m = _SIDECAR_NAME_RE.search(filename or "")
    return m.group(1) if m else None


# --------------------------------------------------------------------------
# fhr_json
# --------------------------------------------------------------------------

def read_json(text: str) -> list:
    obj = json.loads(_strip_bom(text))
    return [flatten(obj)]


def write_json(records: list) -> str:
    return json.dumps(_one(records), indent=2, ensure_ascii=False) + "\n"


def _nonstandard_keys(obj: dict) -> list:
    return [k for k in obj if k not in STANDARD_FIELDS and not str(k).startswith("x-")]


def detect_json(text: str, filename: str = "") -> float:
    obj = _parse_json_object(text)
    if obj is None or "@context" in obj or "@graph" in obj:
        return 0.0
    score = _looks_fhr(obj)
    if not score:
        return 0.0
    if sidecar_digest(filename) or _nonstandard_keys(obj):
        return 0.6  # the RefgetStore sidecar adapter claims these
    if filename.lower().endswith((".fhr.json",)):
        return 0.95
    return score


# --------------------------------------------------------------------------
# fhr_yaml
# --------------------------------------------------------------------------

def read_yaml(text: str) -> list:
    obj = _yaml_load(_strip_bom(text))
    return [flatten(obj)]


def write_yaml(records: list) -> str:
    return _yaml_dump(_one(records))


def detect_yaml(text: str, filename: str = "") -> float:
    head = _strip_bom(text).lstrip()
    if not head or head[0] in "{[<>;" or head.startswith("#~") or len(text) > 5_000_000:
        return 0.0
    try:
        obj = _yaml_load(_strip_bom(text))
    except yaml.YAMLError:
        return 0.0
    score = _looks_fhr(obj)
    if score and filename.lower().endswith((".fhr.yaml", ".fhr.yml")):
        return 0.95
    return score


# --------------------------------------------------------------------------
# fhr_fasta_header and fhr_gfa_header (YAML in ;~ or #~ comment lines)
# --------------------------------------------------------------------------

def _header_lines(text: str, prefix: str) -> list:
    text = _strip_bom(text)
    found = []
    for line in text.splitlines():
        if line.startswith(prefix):
            found.append(line[len(prefix):])
        elif prefix == ";~":
            if line.startswith(">"):
                break  # rule R10: the header block ends at the first record
        else:
            if line.startswith("#") or not line.strip():
                continue
            break
    return found


def _read_header(text: str, prefix: str) -> list:
    lines = _header_lines(text, prefix)
    if not lines:
        raise ValueError(f"no FHR header lines (starting with {prefix}) found")
    obj = _yaml_load("\n".join(lines))
    return [flatten(obj)]


def _write_header(records: list, prefix: str, fasta_safe: bool) -> str:
    obj = _one(records)
    checksum = obj.pop("checksum", None)
    lines = [prefix + line for line in _yaml_dump(obj, fasta_safe=fasta_safe).splitlines()]
    if checksum is not None:
        # Rule R5: exactly "<prefix>checksum: <value>"; rule R3: writers put it last.
        lines.append(f"{prefix}checksum: {checksum}")
    return "\n".join(lines) + "\n"


def file_checksum(text: str, prefix: str = ";~") -> str:
    """FHR file checksum (rules R1 to R4) of a FASTA (;~) or GFA (#~) file.

    Base64 SHA-512/256 of every line except the root checksum line. The rules
    hash the file's bytes; this takes text and encodes it as UTF-8, so it is
    exact only for UTF-8 files read without newline translation. Needs a Python
    whose hashlib offers sha512_256 (some builds, possibly Pyodide, lack it).
    """
    import base64
    import hashlib

    line_re = re.compile(r"[^\r\n]*(?:\r\n|\r|\n|$)")
    lines = [ln for ln in line_re.findall(_strip_bom(text)) if ln]
    header = [ln[len(prefix):] for ln in lines if ln.startswith(prefix)]
    roots = [h for h in header if h.strip() and not h.lstrip().startswith(("#", "-"))]
    indent = len(roots[0]) - len(roots[0].lstrip(" ")) if roots else 0
    # Only the root-level checksum line is left out (R2); nested ones are hashed.
    checksum_re = re.compile(re.escape(prefix) + " " * indent + r"checksum *:")
    kept = [ln for ln in lines if not checksum_re.match(ln)]
    data = "".join(kept).encode("utf-8", errors="surrogateescape")
    return base64.b64encode(hashlib.new("sha512_256", data).digest()).decode("ascii")


def read_fasta(text: str) -> list:
    return _read_header(text, ";~")


def write_fasta(records: list) -> str:
    return _write_header(records, ";~", fasta_safe=True)


def detect_fasta(text: str, filename: str = "") -> float:
    head = _strip_bom(text)[:200_000]
    if not head.lstrip().startswith((";", ">")):
        return 0.0
    lines = _header_lines(head, ";~")
    if not lines:
        return 0.0
    keys = {ln.split(":", 1)[0].strip() for ln in lines if ":" in ln and not ln.startswith((" ", "-"))}
    if "schema" in keys or "genome" in keys:
        return 0.97
    return 0.6


def read_gfa(text: str) -> list:
    return _read_header(text, "#~")


def write_gfa(records: list) -> str:
    return _write_header(records, "#~", fasta_safe=False)


def detect_gfa(text: str, filename: str = "") -> float:
    head = _strip_bom(text)[:200_000]
    if "##gff-version" in head[:2000] or not head.lstrip().startswith("#"):
        return 0.0  # FHGFF3 headers in GFF3 files also use #~; not this format
    lines = _header_lines(head, "#~")
    if not lines:
        return 0.0
    if any("fhgff3" in ln or "/fhp" in ln for ln in lines[:5]):
        return 0.0
    keys = {ln.split(":", 1)[0].strip() for ln in lines if ":" in ln and not ln.startswith((" ", "-"))}
    if not ("schema" in keys or "genome" in keys):
        return 0.4
    gfa_lines = re.search(r"^(H|S|L|P|W)\t", head, re.M)
    if gfa_lines or filename.lower().endswith((".gfa", ".gfa.gz")):
        return 0.97
    return 0.7


# --------------------------------------------------------------------------
# fhr_jsonld (the FHR record plus @context and @type; rules J1 to J9)
# --------------------------------------------------------------------------

def _strip_ld(value: Any) -> Any:
    if isinstance(value, list):
        return [_strip_ld(v) for v in value]
    if isinstance(value, dict):
        if "@list" in value:
            return _strip_ld(value["@list"])
        if "@value" in value:
            return value["@value"]
        keys = [k for k in value if k != "@type"]
        if keys == ["@id"]:
            return value["@id"]
        return {k: _strip_ld(v) for k, v in value.items() if k not in ("@type",)}
    return value


def read_jsonld(text: str) -> list:
    doc = json.loads(_strip_bom(text))
    if isinstance(doc, list):
        if len(doc) != 1:
            raise ValueError("FHR JSON-LD holds one record (J4)")
        doc = doc[0]
    if not isinstance(doc, dict):
        raise ValueError("FHR JSON-LD must be an object")
    if "@graph" in doc:
        graph = doc["@graph"]
        if not isinstance(graph, list) or len(graph) != 1:
            raise ValueError(
                "JSON-LD with several nodes is not an FHR record (J4); the one-way "
                "schema.org export (fhr_schemaorg_export) cannot be read back")
        doc = graph[0]
    node = {k: v for k, v in doc.items()
            if k not in ("@context", "@type", "@id", "keywords", "url", "conformsTo")}
    if any(k.startswith(("http://", "https://")) for k in node):
        raise ValueError("expanded JSON-LD is not supported here; use `bioheaders convert`")
    if "subjectOf" in node:
        if "documentation" in node:
            raise ValueError("a document with both documentation and subjectOf is invalid (J1)")
        node = {("documentation" if k == "subjectOf" else k): v for k, v in node.items()}
    return [flatten(_strip_ld(node))]


def _author_type(author: dict) -> str:
    name_type = author.get("nameType")
    if name_type == "Personal":
        return "Person"
    if name_type == "Organizational":
        return "Organization"
    uri = author.get("uri") or ""
    if isinstance(uri, str) and uri.startswith("https://orcid.org/"):
        return "Person"
    if isinstance(uri, str) and uri.startswith("https://ror.org/"):
        return "Organization"
    return "Agent"


def _is_link(value: Any) -> bool:
    return isinstance(value, str) and bool(_LINK_RE.match(value)) and \
        not _CTRL_OR_SPACE.search(value)


def _typed(type_name: str, obj: dict) -> dict:
    return {"@type": type_name, **obj}


def write_jsonld(records: list) -> str:
    obj = _one(records)
    out: dict = {"@context": JSONLD_CONTEXT, "@type": "Dataset"}
    for key, value in obj.items():
        if key not in STANDARD_FIELDS:
            continue  # J9: no extension fields; other keys have no term
        if key == "taxon" and isinstance(value, dict):
            value = _typed("Taxon", value)
        elif key in ("metadataAuthor", "assemblyAuthor") and isinstance(value, list):
            value = [_typed(_author_type(a), a) if isinstance(a, dict) else a for a in value]
        elif key == "accessionID" and isinstance(value, dict):
            value = _typed("PropertyValue", value)
        elif key == "assemblySoftware" and isinstance(value, list):
            value = [_typed("SoftwareApplication", s) if isinstance(s, dict) else s for s in value]
        elif key == "vitalStats" and isinstance(value, dict):
            value = _typed("VitalStats", value)
        elif key == "documentation" and _is_link(value):
            key = "subjectOf"
        out[key] = value
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def detect_jsonld(text: str, filename: str = "") -> float:
    obj = _parse_json_object(text)
    if obj is None or "@context" not in obj:
        return 0.0
    ctx = obj["@context"]
    if isinstance(ctx, list) and len(ctx) == 1:
        ctx = ctx[0]
    is_fhr_ctx = ctx == JSONLD_CONTEXT or ctx in JSONLD_CONTEXT_URLS
    if "@graph" in obj:
        graph = obj["@graph"]
        if isinstance(graph, list) and len(graph) > 1:
            return 0.1  # schema.org export, not readable
    if is_fhr_ctx:
        return 0.97
    if "fair-bioheaders" in json.dumps(ctx)[:5000].lower():
        return 0.6
    return 0.0


def detect_schemaorg_export(text: str, filename: str = "") -> float:
    obj = _parse_json_object(text)
    if obj is None or "@graph" not in obj:
        return 0.0
    ids = {n.get("@id") for n in obj["@graph"] if isinstance(n, dict)}
    return 0.9 if "_:assembly" in ids and "_:metadata-record" in ids else 0.0


# --------------------------------------------------------------------------
# fhr_microdata (HTML; rules M1 to M5)
# --------------------------------------------------------------------------

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
         "param", "source", "track", "wbr"}
_P_CLOSERS = {"address", "article", "aside", "blockquote", "details", "div", "dl",
               "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
               "h4", "h5", "h6", "header", "hgroup", "hr", "main", "menu", "nav", "ol",
               "p", "pre", "section", "table", "ul"}
_IMPLIED = {  # start tag -> (open elements it closes, elements that stop the search)
    "li": ({"li"}, {"ul", "ol", "menu"}),
    "dt": ({"dt", "dd"}, {"dl"}),
    "dd": ({"dt", "dd"}, {"dl"}),
    "td": ({"td", "th"}, {"tr", "table"}),
    "th": ({"td", "th"}, {"tr", "table"}),
    "tr": ({"tr", "td", "th"}, {"table", "tbody", "thead", "tfoot"}),
    "tbody": ({"tbody", "thead", "tfoot", "tr", "td", "th"}, {"table"}),
    "thead": ({"tbody", "thead", "tfoot", "tr", "td", "th"}, {"table"}),
    "tfoot": ({"tbody", "thead", "tfoot", "tr", "td", "th"}, {"table"}),
    "option": ({"option"}, {"select", "datalist", "optgroup"}),
    "optgroup": ({"option", "optgroup"}, {"select"}),
}
_VALUE_ATTR = {"meta": "content", "a": "href", "area": "href", "link": "href",
               "audio": "src", "embed": "src", "iframe": "src", "img": "src",
               "source": "src", "track": "src", "video": "src", "object": "data",
               "data": "value", "meter": "value", "time": "datetime"}


class _Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: dict):
        self.tag = tag
        self.attrs = attrs
        self.children: list = []

    def text(self) -> str:
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {})
        self.stack = [self.root]

    def _close_implied(self, tag):
        """HTML implied end tags (rule M2), for the elements that commonly need it."""
        if tag in _P_CLOSERS:
            self._pop_open({"p"}, {"button", "table", "td", "th", "li", "dd", "dt"})
        if tag in _IMPLIED:
            closes, boundaries = _IMPLIED[tag]
            self._pop_open(closes, boundaries)

    def _pop_open(self, closes, boundaries):
        for i in range(len(self.stack) - 1, 0, -1):
            tag = self.stack[i].tag
            if tag in closes:
                del self.stack[i:]
                return
            if tag in boundaries:
                return

    def handle_starttag(self, tag, attrs):
        self._close_implied(tag)
        first: dict = {}
        for k, v in attrs:  # rule R9: the first of repeated attributes applies
            first.setdefault(k, "" if v is None else v)
        node = _Node(tag, first)
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _props(scope: _Node) -> list:
    """(name, node) pairs that belong to this item scope or array container."""
    found = []

    def walk(node):
        for child in node.children:
            if isinstance(child, str):
                continue
            prop = child.attrs.get("itemprop")
            if prop is not None:
                for name in prop.split():
                    found.append((name, child))
                if "itemscope" in child.attrs or child.attrs.get("data-fhr-type") == "array":
                    continue
            elif "itemscope" in child.attrs:
                continue  # rule M1: a separate item, not part of FHR metadata
            walk(child)

    walk(scope)
    return found


def _micro_value(node: _Node, name: str) -> Any:
    kind = node.attrs.get("data-fhr-type")
    if kind == "object" or (kind is None and "itemscope" in node.attrs):
        return _micro_object(node)
    if kind == "array":
        return [_micro_value(n, "item") for nm, n in _props(node) if nm == "item"]
    attr = _VALUE_ATTR.get(node.tag)
    raw = node.attrs[attr] if attr and attr in node.attrs else node.text()
    if kind == "string":
        return raw
    if kind in ("integer", "number", "boolean", "null"):
        value = json.loads(raw.strip())
        ok = {"integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
              "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
              "boolean": lambda v: isinstance(v, bool),
              "null": lambda v: v is None}[kind](value)
        if not ok:
            raise ValueError(f"microdata value {raw!r} is not of data-fhr-type {kind} (M3)")
        return value
    if name in _INT_FIELDS:
        return int(raw.strip())
    if name in _NUMBER_FIELDS:
        return float(raw.strip())
    if name == "schemaVersion" and re.fullmatch(r"\s*1(\.0+)?\s*", raw):
        return json.loads(raw.strip())  # FHR 1: untyped text that reads as the number 1 (V6)
    return raw


def _micro_object(scope: _Node) -> dict:
    out: dict = {}
    seen: set = set()
    for name, node in _props(scope):
        value = _micro_value(node, name)
        if name in out:
            if name not in seen:
                out[name] = [out[name]]
                seen.add(name)
            out[name].append(value)  # rule M4: a repeated property becomes a list
        else:
            out[name] = value
    for name in _LIST_FIELDS:
        if name in out and not isinstance(out[name], list):
            out[name] = [out[name]]
    return out


def _find_fhr_scopes(node: _Node, found: list) -> None:
    for child in node.children:
        if isinstance(child, str):
            continue
        if "itemscope" in child.attrs and any(
                _ITEMTYPE_RE.match(t) for t in child.attrs.get("itemtype", "").split()):
            found.append(child)
        _find_fhr_scopes(child, found)


def read_microdata(text: str) -> list:
    builder = _TreeBuilder()
    builder.feed(_strip_bom(text))
    builder.close()
    scopes: list = []
    _find_fhr_scopes(builder.root, scopes)
    if len(scopes) != 1:
        raise ValueError(f"expected exactly one FHR item scope (M1), found {len(scopes)}")
    obj = _micro_object(scopes[0])
    if any(k.startswith("x-") for k in obj):
        raise ValueError("microdata carries no extension fields (M5)")
    return [flatten(obj)]


def _micro_element(name: str, value: Any) -> str:
    attr = f'itemprop="{html.escape(name, quote=True)}"'
    if isinstance(value, dict):
        inner = "".join(_micro_element(k, v) for k, v in value.items())
        return f'<span {attr} itemscope data-fhr-type="object">{inner}</span>'
    if isinstance(value, list):
        inner = "".join(_micro_element("item", v) for v in value)
        return f'<span {attr} data-fhr-type="array">{inner}</span>'
    if isinstance(value, bool):
        kind, text = "boolean", "true" if value else "false"
    elif isinstance(value, int):
        kind, text = "integer", str(value)
    elif isinstance(value, float):
        kind, text = "number", json.dumps(value)
    elif value is None:
        kind, text = "null", "null"
    else:
        kind, text = "string", str(value)
    return f'<span {attr} data-fhr-type="{kind}">{html.escape(text, quote=False)}</span>'


def write_microdata(records: list) -> str:
    obj = _one(records)
    body = "".join(_micro_element(k, v) for k, v in obj.items() if k in STANDARD_FIELDS)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        "<title>FHR example</title></head><body>\n"
        f'<div itemscope itemtype="{FHR_MICRODATA_ITEMTYPE}">{body}</div>\n'
        "</body></html>\n"
    )


def detect_microdata(text: str, filename: str = "") -> float:
    head = _strip_bom(text)[:2_000_000]
    if "itemscope" not in head:
        return 0.0
    if re.search(r"FAIR-bioHeaders[-A-Za-z]*/main/fhr\.json", head) or \
            re.search(r"FHR-Specification/main/fhr\.json", head):
        return 0.97
    return 0.0


# --------------------------------------------------------------------------
# fhr_refgetstore_sidecar (gtars FhrMetadata JSON, file <seqcolDigest>.fhr.json)
# --------------------------------------------------------------------------

def read_sidecar(text: str) -> list:
    obj = json.loads(_strip_bom(text))
    return [flatten(obj)]


def _ordered(obj: dict, order: tuple) -> dict:
    out = {k: obj[k] for k in order if k in obj}
    out.update((k, v) for k, v in obj.items() if k not in out)
    return out


def write_sidecar(records: list) -> str:
    """serde_json::to_string_pretty layout: gtars field order, extras last, no final newline."""
    obj = _one(records)
    obj.pop(SIDECAR_DIGEST_KEY, None)
    out = _ordered(obj, SIDECAR_FIELDS)
    for key, order in SIDECAR_NESTED_ORDER.items():
        value = out.get(key)
        if isinstance(value, dict):
            out[key] = _ordered(value, order)
        elif isinstance(value, list):
            out[key] = [_ordered(v, order) if isinstance(v, dict) else v for v in value]
    return json.dumps(out, indent=2, ensure_ascii=False)


def detect_sidecar(text: str, filename: str = "") -> float:
    obj = _parse_json_object(text)
    if obj is None or "@context" in obj or "@graph" in obj or not _looks_fhr(obj):
        return 0.0
    if sidecar_digest(filename):
        return 0.97
    if _nonstandard_keys(obj):
        return 0.85
    return 0.3


FORMATS = [
    Format(id="fhr_json", source=SOURCE,
           description="FHR metadata as a JSON file (FAIR-bioHeaders FHR 2.1; also FHR 1 and 2.0 records)",
           read=read_json, write=write_json, detect=detect_json,
           extensions=(".fhr.json", ".json")),
    Format(id="fhr_yaml", source=SOURCE,
           description="FHR metadata as a YAML file",
           read=read_yaml, write=write_yaml, detect=detect_yaml,
           extensions=(".fhr.yaml", ".fhr.yml", ".yaml", ".yml")),
    Format(id="fhr_fasta_header", source=SOURCE,
           description="FHR YAML header in ;~ comment lines at the top of a FASTA file "
                       "(write() emits the header block only)",
           read=read_fasta, write=write_fasta, detect=detect_fasta,
           extensions=(".fhr.fasta", ".fhr.fa", ".fasta", ".fa", ".fna")),
    Format(id="fhr_gfa_header", source=SOURCE,
           description="FHR YAML header in #~ comment lines at the top of a GFA file "
                       "(write() emits the header block only)",
           read=read_gfa, write=write_gfa, detect=detect_gfa,
           extensions=(".fhr.gfa", ".gfa")),
    Format(id="fhr_jsonld", source=SOURCE,
           description="FHR JSON-LD: the FHR record plus the FHR @context and @type (no extension fields)",
           read=read_jsonld, write=write_jsonld, detect=detect_jsonld,
           extensions=(".fhr.jsonld", ".jsonld")),
    Format(id="fhr_microdata", source=SOURCE,
           description="FHR metadata as HTML microdata with data-fhr-type annotations (no extension fields)",
           read=read_microdata, write=write_microdata, detect=detect_microdata,
           extensions=(".fhr.html", ".html")),
    Format(id="fhr_refgetstore_sidecar", source=SOURCE,
           description="RefgetStore FHR sidecar written by gtars (fhr/<seqcol digest>.fhr.json), "
                       "e.g. refgenie's public stores",
           read=read_sidecar, write=write_sidecar, detect=detect_sidecar,
           extensions=(".fhr.json",)),
]
