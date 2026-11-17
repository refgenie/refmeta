"""refmeta conversion engine.

Applies the crosswalks (refmeta/data/crosswalk/<format_id>.yaml) exactly as
mapping/CROSSWALK_FORMAT.md (crosswalk version 1) defines them:

    to_core(format_id, records)    native records -> core records
    from_core(format_id, core)     core record(s)  -> native records
    convert(text, to_format, from_format=None, filename="")
                                   file text -> file text, through the core

The crosswalks, core.schema.json and a compact copy of the fields.json field
types are package data (tools/sync_data.py copies them from mapping/ and
sources/), loaded with importlib.resources, so the same code runs in a normal
install and in the browser (Pyodide). Standard library plus pyyaml only.

Section numbers in comments refer to CROSSWALK_FORMAT.md.

Two readings of the spec that it leaves open:
- Element-wise transforms on a list (7) keep the list's positions: an item that
  gives no value becomes null instead of being removed, so a `[]` spread still
  puts item i in element i (null items are skipped by the spread, 4.1). Where
  the value is not spread, the nulls are dropped, which is the spec's "drop".
- On from_core, a native value kept in extras (9) fills a field that no rule
  wrote, and it beats the `missing` token a rule would otherwise write (3), so a
  token such as 'na' versus '' comes back exactly as read.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import re
from functools import lru_cache
from importlib import resources
from typing import Any, Iterable, NamedTuple, Optional

import yaml

from .formats import Format, all_formats
from .formats import ga4gh as _ga4gh

__all__ = [
    "CORE", "CORE_VERSION", "ConversionError", "CrosswalkError", "NoValue",
    "load_schema", "load_crosswalk", "crosswalk_ids", "format_info", "formats",
    "list_formats", "detect", "read_native", "write_native", "to_core", "from_core",
    "convert", "convert_detailed", "read_core", "merge", "rename", "shared_identifiers", "dump_core", "load_core",
    "forward", "inverse", "load_namespaces", "accession_namespaces",
]

CORE_VERSION = "0.1"
CORE = "core"  # pseudo format id: the core record itself (YAML or JSON)

log = logging.getLogger("refmeta")

TRANSFORMS = ("cast", "map", "regex", "prefix", "replace", "split", "date", "curie", "rekey", "entries",
              "accession")
ELEMENTWISE = frozenset({"cast", "map", "regex", "prefix", "replace", "date"})
DERIVATIONS = ("seqcol_digests", "counts", "accession_version")
COMPUTES = ("seqcol_name_length_pairs", "seqcol_sorted_sequences", "seqcol_sorted_name_length_pairs")


class ConversionError(ValueError):
    """A file or record could not be converted."""


class CrosswalkError(ValueError):
    """A crosswalk file breaks CROSSWALK_FORMAT.md."""


class NoValue(Exception):
    """A transform gave no value (section 7)."""


class _Missing:
    def __repr__(self) -> str:
        return "MISSING"


MISSING: Any = _Missing()

# ---------------------------------------------------------------- package data

_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _data(*parts: str):
    node = resources.files("refmeta").joinpath("data")
    for p in parts:
        node = node.joinpath(p)
    return node


@lru_cache(maxsize=None)
def load_schema() -> dict:
    """core.schema.json as a dict."""
    return json.loads(_data("core.schema.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_namespaces() -> dict[str, dict]:
    """The official namespaces (mapping/namespaces.yaml), by id, in file order."""
    raw = yaml.load(_data("namespaces.yaml").read_text(encoding="utf-8"), Loader=_Loader)
    return {n["id"]: n for n in raw["namespaces"]}


@lru_cache(maxsize=None)
def accession_namespaces() -> tuple[str, ...]:
    """Official accession namespaces that have a pattern, in registry order: the ones the
    `accession` transform tries (unspecified, which has no pattern, is only a fallback)."""
    return tuple(i for i, n in load_namespaces().items()
                 if "assembly.accessions" in n.get("lists", []) and n.get("pattern"))


@lru_cache(maxsize=None)
def format_info() -> dict:
    """Per-format info from fields.json: source, description, fields [[path, type, cardinality]]."""
    return json.loads(_data("formats.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def crosswalk_ids() -> tuple[str, ...]:
    d = _data("crosswalk")
    return tuple(sorted(p.name[:-5] for p in d.iterdir() if p.name.endswith(".yaml")))


@lru_cache(maxsize=None)
def formats() -> dict[str, Format]:
    """All format adapters, by id."""
    return all_formats()


@lru_cache(maxsize=None)
def load_crosswalk(format_id: str) -> "Crosswalk":
    """The compiled crosswalk for a format id."""
    if format_id not in crosswalk_ids():
        raise ConversionError(f"no crosswalk for format {format_id!r}")
    raw = yaml.load(_data("crosswalk", f"{format_id}.yaml").read_text(encoding="utf-8"), Loader=_Loader)
    return Crosswalk(raw)


def list_formats() -> list[dict]:
    """One row per format that has an adapter or a crosswalk."""
    fmts, info, cws = formats(), format_info(), set(crosswalk_ids())
    out = []
    for fid in sorted(set(fmts) | cws):
        f = fmts.get(fid)
        i = info.get(fid, {})
        out.append({
            "id": fid,
            "source": f.source if f else i.get("source", ""),
            "description": (f.description if f else "") or i.get("description", ""),
            "read": bool(f and fid in cws),
            "write": bool(f and f.write and fid in cws),
            "extensions": list(f.extensions) if f else i.get("extensions", []),
        })
    return out

# ---------------------------------------------------------------- values


def text_form(v: Any) -> str:
    """A value's text form (4.1, 7.2): strings as is, numbers and booleans as JSON text."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return v
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def _same(a: Any, b: Any) -> bool:
    """Equality that keeps booleans apart from numbers (true is not 1)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def _is_empty(v: Any) -> bool:
    return v is None or v is MISSING or (isinstance(v, list) and all(x is None for x in v))

# ---------------------------------------------------------------- core paths (4.1)


class Seg(NamedTuple):
    name: str
    kind: Optional[str] = None  # None | spread | plus | index | keyed
    index: int = 0
    conds: tuple = ()  # ((member, text value), ...)

    def __str__(self) -> str:
        if self.kind is None:
            return self.name
        if self.kind == "spread":
            return self.name + "[]"
        if self.kind == "plus":
            return self.name + "[+]"
        if self.kind == "index":
            return f"{self.name}[{self.index}]"
        return self.name + "[" + ",".join(f"{k}={v}" for k, v in self.conds) + "]"


_SEG_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]*)\])?")
_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@lru_cache(maxsize=None)
def parse_path(path: str) -> tuple[Seg, ...]:
    """Split a core path into segments (on '.' outside brackets only)."""
    parts, depth, cur = [], 0, ""
    for ch in path:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "." and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    segs = []
    for p in parts:
        m = _SEG_RE.fullmatch(p)
        if not m:
            raise CrosswalkError(f"bad segment {p!r} in core path {path!r}")
        name, sel = m.group(1), m.group(2)
        if sel is None:
            segs.append(Seg(name))
        elif sel == "":
            segs.append(Seg(name, "spread"))
        elif sel == "+":
            segs.append(Seg(name, "plus"))
        elif sel.isdigit():
            segs.append(Seg(name, "index", int(sel)))
        else:
            conds = []
            for c in sel.split(","):
                if "=" not in c:
                    raise CrosswalkError(f"bad selector [{sel}] in core path {path!r}")
                k, v = c.split("=", 1)
                if not _NAME_RE.fullmatch(k):
                    raise CrosswalkError(f"bad selector member {k!r} in core path {path!r}")
                conds.append((k, v))
            segs.append(Seg(name, "keyed", 0, tuple(conds)))
    return tuple(segs)


class SegInfo(NamedTuple):
    is_array: bool  # the member's schema type is array
    leaf_type: Any  # the member's schema type (after the selector, the item's)
    cond_types: dict  # keyed selector: member -> schema type


def _deref(s: Any) -> Any:
    root = load_schema()
    n = 0
    while isinstance(s, dict) and "$ref" in s:
        s = root["$defs"][s["$ref"].rsplit("/", 1)[-1]]
        n += 1
        if n > 50:
            raise CrosswalkError("$ref loop in core.schema.json")
    return s


def _member_schema(s: dict, name: str, path: str) -> dict:
    props = s.get("properties", {})
    if name in props:
        return _deref(props[name])
    for pat, sub in s.get("patternProperties", {}).items():
        if re.search(pat, name):
            return _deref(sub)
    ap = s.get("additionalProperties")
    if isinstance(ap, dict):
        return _deref(ap)
    raise CrosswalkError(f"core path {path!r}: {name!r} is not a core field")


@lru_cache(maxsize=None)
def resolve_path(path: str) -> tuple[SegInfo, ...]:
    """Check a core path against core.schema.json (4.1) and return schema facts per segment."""
    segs = parse_path(path)
    s = _deref(load_schema())
    infos = []
    for i, seg in enumerate(segs):
        sub = _member_schema(s, seg.name, path)
        is_array = sub.get("type") == "array"
        cond_types = {}
        if seg.kind is not None:
            if not is_array:
                raise CrosswalkError(f"core path {path!r}: selector on {seg.name!r}, which is not an array")
            item = _deref(sub.get("items", {}))
            for k, _ in seg.conds:
                if k not in item.get("properties", {}):
                    raise CrosswalkError(f"core path {path!r}: selector member {k!r} is not in {seg.name!r} items")
                cond_types[k] = _deref(item["properties"][k]).get("type")
            s = item
            leaf_type = item.get("type")
        else:
            if is_array and i < len(segs) - 1:
                raise CrosswalkError(f"core path {path!r}: array {seg.name!r} needs a selector")
            s = sub
            leaf_type = sub.get("type")
        infos.append(SegInfo(is_array, leaf_type, cond_types))
    return tuple(infos)


def _matches(el: Any, conds: tuple) -> bool:
    return isinstance(el, dict) and all(k in el and text_form(el[k]) == v for k, v in conds)


def _cond_value(v: str, t: Any) -> Any:
    try:
        if t == "integer":
            return int(v)
        if t == "number":
            return float(v) if not re.fullmatch(r"[+-]?\d+", v) else int(v)
        if t == "boolean":
            return {"true": True, "false": False}[v]
    except (ValueError, KeyError):
        pass
    return v

# ---------------------------------------------------------------- transforms (7)


def _cast(v: Any, t: str) -> Any:
    if t == "integer":
        if isinstance(v, bool):
            raise NoValue
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise NoValue
        s = str(v).strip()
        if re.fullmatch(r"[+-]?\d+", s):
            return int(s)
        raise NoValue
    if t == "number":
        if isinstance(v, bool):
            raise NoValue
        if isinstance(v, (int, float)):
            return v
        s = str(v).strip()
        if re.fullmatch(r"[+-]?\d+", s):
            return int(s)
        try:
            return float(s)
        except ValueError:
            raise NoValue from None
    if t == "string":
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return v
        raise NoValue
    if t == "boolean":
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)) and v in (0, 1):
            return bool(v)
        s = str(v).strip().lower()
        if s in ("true", "1"):
            return True
        if s in ("false", "0"):
            return False
        raise NoValue
    raise CrosswalkError(f"cast: unknown type {t!r}")


_DATE_TOKENS = {"%Y": r"(?P<Y>\d{4})", "%m": r"(?P<m>\d{2})", "%d": r"(?P<d>\d{2})",
                "%H": r"(?P<H>\d{2})", "%M": r"(?P<M>\d{2})", "%S": r"(?P<S>\d{2})"}


@lru_cache(maxsize=None)
def _date_regex(fmt: str) -> re.Pattern:
    out = ""
    for tok in re.split(r"(%[YmdHMS])", fmt):
        out += _DATE_TOKENS.get(tok, re.escape(tok))
    return re.compile(out)


_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):(\d{2}))?")


def _set_dotted(d: dict, dotted: str, val: Any) -> None:
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = val


def _get_dotted(d: Any, dotted: str) -> Any:
    for k in dotted.split("."):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _fwd_one(name: str, p: dict, v: Any) -> Any:
    """Forward transform of one value (not a list, for element-wise transforms)."""
    if name == "cast":
        return _cast(v, p["to"])
    if name == "map":
        key = text_form(v)
        values = p["values"]
        if key in values:
            out = values[key]
            if out is None:
                raise NoValue
            return copy.deepcopy(out)
        if p.get("other", "keep") == "drop":
            raise NoValue
        return v
    if name == "regex":
        m = re.search(p["pattern"], text_form(v))
        if not m:
            raise NoValue
        g = m.group(p.get("group", 1))
        if g is None:
            raise NoValue
        return _cast(g, p.get("as", "string"))
    if name == "prefix":
        s = text_form(v)
        if "add" in p:
            return s if s.startswith(p["add"]) else p["add"] + s
        return s[len(p["strip"]):] if s.startswith(p["strip"]) else s
    if name == "replace":
        return text_form(v).replace(p["old"], p["new"])
    if name == "date":
        m = _date_regex(p["format"]).fullmatch(text_form(v))
        if not m:
            raise NoValue
        g = m.groupdict()
        out = f"{g['Y']}-{g.get('m') or '01'}-{g.get('d') or '01'}"
        if "H" in g:
            out += f"T{g['H']}:{g.get('M') or '00'}:{g.get('S') or '00'}"
        return out
    raise CrosswalkError(f"unknown transform {name!r}")


def _inv_one(name: str, p: dict, v: Any, native_type: Optional[str]) -> Any:
    if name == "cast":
        return _cast(v, p["from"])
    if name == "map":
        for k, mapped in p["values"].items():
            if _same(mapped, v):
                if native_type in ("integer", "number", "boolean"):
                    try:
                        return _cast(k, native_type)
                    except NoValue:
                        return k
                return k
        if p.get("other", "keep") == "drop":
            raise NoValue
        return v
    if name == "regex":
        if "template" not in p:
            raise NoValue
        return p["template"].replace("{}", text_form(v))
    if name == "prefix":
        s = text_form(v)
        if "add" in p:
            return s[len(p["add"]):] if s.startswith(p["add"]) else s
        return s if s.startswith(p["strip"]) else p["strip"] + s
    if name == "replace":
        return text_form(v).replace(p["new"], p["old"])
    if name == "date":
        m = _ISO_RE.fullmatch(text_form(v))
        if not m:
            raise NoValue
        y, mo, d, hh, mi, ss = m.groups()
        return (p["format"].replace("%Y", y).replace("%m", mo).replace("%d", d)
                .replace("%H", hh or "00").replace("%M", mi or "00").replace("%S", ss or "00"))
    raise CrosswalkError(f"unknown transform {name!r}")


def _curie_fwd(p: dict, v: Any) -> dict:
    sep = p.get("sep", ":")
    if not isinstance(v, str) or sep not in v:
        raise NoValue
    prefix, rest = v.split(sep, 1)
    return {"namespace": p.get("namespaces", {}).get(prefix, prefix.lower()), "value": rest}


def _curie_inv(p: dict, v: Any) -> str:
    if not isinstance(v, dict) or v.get("namespace") is None or v.get("value") is None:
        raise NoValue
    sep = p.get("sep", ":")
    for native, core in p.get("namespaces", {}).items():
        if core == v["namespace"]:
            return f"{native}{sep}{v['value']}"
    return f"{v['namespace']}{sep}{v['value']}"


def _rekey_fwd(p: dict, o: Any) -> dict:
    if not isinstance(o, dict):
        raise NoValue
    out = {}
    for k, val in o.items():
        if k in p["keys"]:
            ck = p["keys"][k]
            vm = (p.get("values") or {}).get(ck)
            if vm is not None and text_form(val) in vm:
                val = vm[text_form(val)]
            out[ck] = copy.deepcopy(val)
    return out


def _rekey_inv(p: dict, o: Any) -> dict:
    if not isinstance(o, dict):
        raise NoValue
    back = {c: n for n, c in reversed(list(p["keys"].items()))}
    out = {}
    for ck, val in o.items():
        if ck not in back:
            continue
        vm = (p.get("values") or {}).get(ck)
        if vm is not None:
            for nv, cv in vm.items():
                if _same(cv, val):
                    val = nv
                    break
        out[back[ck]] = copy.deepcopy(val)
    return out


def _accession_fwd(p: dict, v: Any) -> dict:
    """A plain accession string -> {namespace, value}, by the registry patterns (7.11)."""
    if not isinstance(v, str) or not v.strip():
        raise NoValue
    v = v.strip()
    reg = load_namespaces()
    for ns in p["namespaces"]:
        pat = reg.get(ns, {}).get("pattern")
        if pat and re.fullmatch(pat, v):
            return {"namespace": ns, "value": v}
    if p.get("other"):
        return {"namespace": p["other"], "value": v}
    raise NoValue


def _accession_inv(p: dict, v: Any, native_type: Optional[str]) -> Any:
    """{namespace, value} items -> the value of item `index` (all items from `index` on
    for an array native field). Only items in `namespaces` (and `other`) count when the
    crosswalk lists `namespaces`; otherwise every item counts (7.11)."""
    items = v if isinstance(v, list) else [v]
    allowed = set(p["namespaces"]) | ({p["other"]} if p.get("other") else set())
    vals = [x["value"] for x in items if isinstance(x, dict) and x.get("value") is not None
            and (not p["filter"] or x.get("namespace") in allowed)]
    vals = vals[p.get("index", 0):]
    if not vals:
        raise NoValue
    return vals if native_type == "array" else vals[0]


def _apply(name: str, p: dict, v: Any, inverse_: bool, native_type: Optional[str], fails: list) -> Any:
    """Apply one transform to a value, handling lists as section 7 says."""
    if name in ELEMENTWISE:
        if isinstance(v, list):
            out = []
            for x in v:
                if x is None:
                    out.append(None)
                    continue
                try:
                    out.append(_inv_one(name, p, x, native_type) if inverse_ else _fwd_one(name, p, x))
                except NoValue:
                    fails.append(x)
                    out.append(None)
            if all(x is None for x in out):
                raise NoValue
            return out
        return _inv_one(name, p, v, native_type) if inverse_ else _fwd_one(name, p, v)
    if name == "split":
        if not inverse_:
            if isinstance(v, list):
                return v
            parts = [x.strip() for x in text_form(v).split(p["sep"])]
            parts = [x for x in parts if x]
            if not parts:
                raise NoValue
            return parts
        if isinstance(v, list):
            items = [text_form(x) for x in v if x is not None]
            if not items:
                raise NoValue
            return p["sep"].join(items)
        return v
    if name == "curie":
        f = _curie_inv if inverse_ else _curie_fwd
        if isinstance(v, list):
            out = []
            for x in v:
                try:
                    out.append(f(p, x))
                except NoValue:
                    fails.append(x)
            if not out:
                raise NoValue
            return out
        return f(p, v)
    if name == "rekey":
        f = _rekey_inv if inverse_ else _rekey_fwd
        if isinstance(v, list):
            out = []
            for x in v:
                try:
                    out.append(f(p, x))
                except NoValue:
                    fails.append(x)
            return out
        return f(p, v)
    if name == "accession":
        if inverse_:
            return _accession_inv(p, v, native_type)
        if isinstance(v, list):
            out = []
            for x in v:
                try:
                    out.append(_accession_fwd(p, x))
                except NoValue:
                    fails.append(x)
            if not out:
                raise NoValue
            return out
        return _accession_fwd(p, v)
    if name == "entries":
        if not inverse_:
            if not isinstance(v, dict):
                raise NoValue
            out = []
            for k, val in v.items():
                e = {p["key"]: k}
                _set_dotted(e, p["value"], copy.deepcopy(val))
                out.append(e)
            return out
        items = v if isinstance(v, list) else [v]
        out = {}
        for e in items:
            if not isinstance(e, dict):
                continue
            k, val = e.get(p["key"]), _get_dotted(e, p["value"])
            if k is None or val is None:
                continue
            out[k] = copy.deepcopy(val)
        if not out:
            raise NoValue
        return out
    raise CrosswalkError(f"unknown transform {name!r}")


def _compile_transforms(t: Any) -> tuple:
    if t is None:
        return ()
    items = [t] if isinstance(t, dict) else list(t)
    out = []
    for item in items:
        if not isinstance(item, dict) or len(item) != 1:
            raise CrosswalkError(f"a transform is one {{name: params}} pair, got {item!r}")
        (name, params), = item.items()
        if name not in TRANSFORMS:
            raise CrosswalkError(f"unknown transform {name!r}")
        params = dict(params or {})
        if name == "map":
            params["values"] = {text_form(k): v for k, v in (params.get("values") or {}).items()}
        if name == "rekey":
            params["values"] = {ck: {text_form(k): v for k, v in (vm or {}).items()}
                                for ck, vm in (params.get("values") or {}).items()}
        if name == "prefix" and ("add" in params) == ("strip" in params):
            raise CrosswalkError("prefix takes exactly one of add or strip")
        if name == "accession":
            ns = params.get("namespaces")
            params["filter"] = bool(ns)
            params["namespaces"] = tuple(ns) if ns else accession_namespaces()
            unknown = [n for n in params["namespaces"] if not load_namespaces().get(n, {}).get("pattern")]
            if unknown:
                raise CrosswalkError(f"accession: {unknown} are not official namespaces with a pattern")
            if not isinstance(params.get("index", 0), int) or params.get("index", 0) < 0:
                raise CrosswalkError("accession: index is a number, 0 or more")
        out.append((name, params))
    return tuple(out)


def forward(transforms: Any, value: Any, fails: Optional[list] = None) -> Any:
    """Apply a crosswalk `transform` (one or a list) forward. Raises NoValue."""
    fails = [] if fails is None else fails
    for name, p in _compile_transforms(transforms) if not isinstance(transforms, tuple) else transforms:
        value = _apply(name, p, value, False, None, fails)
    return value


def inverse(transforms: Any, value: Any, native_type: Optional[str] = None,
            fails: Optional[list] = None) -> Any:
    """Apply the inverse of a crosswalk `transform`, last step first. Raises NoValue."""
    fails = [] if fails is None else fails
    steps = _compile_transforms(transforms) if not isinstance(transforms, tuple) else transforms
    for name, p in reversed(steps):
        value = _apply(name, p, value, True, native_type, fails)
    return value

# ---------------------------------------------------------------- crosswalk objects


class Rule:
    def __init__(self, raw: dict, cw: "Crosswalk", pos: int):
        self.raw = raw
        self.pos = pos
        self.native: str = raw["native"]
        self.direction: str = raw.get("direction", "both")
        if self.direction not in ("both", "to_core", "from_core"):
            raise CrosswalkError(f"{cw.format}: rule {self.native!r}: bad direction {self.direction!r}")
        self.compute: Optional[str] = raw.get("compute")
        self.core: Optional[str] = raw.get("core")
        if self.compute is not None:
            if self.compute not in COMPUTES:
                raise CrosswalkError(f"{cw.format}: unknown compute {self.compute!r}")
            if self.direction != "from_core":
                raise CrosswalkError(f"{cw.format}: compute rule {self.native!r} must be from_core")
        elif self.core is None:
            raise CrosswalkError(f"{cw.format}: rule {self.native!r} has neither core nor compute")
        self.segs = parse_path(self.core) if self.core else ()
        self.infos = resolve_path(self.core) if self.core else ()
        self.fallback = [p for p in (raw.get("fallback") or [])]
        for p in self.fallback:
            resolve_path(p)
        self.transforms = _compile_transforms(raw.get("transform"))
        m = raw.get("missing")
        self.missing: list = [] if m is None else (list(m) if isinstance(m, list) else [m])
        self.lossy = raw.get("lossy")
        self.native_type, self.native_card = cw.field_types.get(self.native, (None, "one"))
        # group mode: a per-row rule writes into the row's element of rows.target (5.2)
        self.per_row = bool(cw.mode == "group" and cw.target and self.segs
                            and self.segs[0].name == cw.target and self.segs[0].kind == "spread")
        self.uses_plus = any(s.kind == "plus" for s in self.segs[1:]) if self.per_row else False
        self.plus_inner: tuple = ()  # path (inside the row's element) of the [+] array
        if self.uses_plus:
            i = next(i for i, s in enumerate(self.segs) if s.kind == "plus" and i > 0)
            self.plus_inner = tuple(self.segs[1:i]) + (Seg(self.segs[i].name),)
        # does the value get spread (so list positions matter)?
        write_segs = self.segs[1:] if self.per_row else self.segs
        self.spreads = any(s.kind == "spread" for s in write_segs)

    @property
    def reads(self) -> bool:  # used on to_core
        return self.direction in ("both", "to_core") and self.core is not None

    @property
    def writes(self) -> bool:  # used on from_core
        return self.direction in ("both", "from_core")

    def is_missing(self, v: Any) -> bool:
        return any(_same(v, t) or (isinstance(v, str) and v == text_form(t)) for t in self.missing)

    def __repr__(self) -> str:
        return f"Rule({self.native!r} -> {self.core or self.compute!r}, {self.direction})"


class Crosswalk:
    """A loaded crosswalk (one format <-> core)."""

    def __init__(self, raw: dict):
        if raw.get("crosswalk") != 1:
            raise CrosswalkError(f"unsupported crosswalk version {raw.get('crosswalk')!r}")
        self.raw = raw
        self.format: str = raw["format"]
        self.source: str = raw["source"]
        self.subject: str = raw.get("subject", "collection")
        rec = raw.get("records") or {"mode": "each"}
        self.mode: str = rec.get("mode", "each")
        if self.mode not in ("each", "group"):
            raise CrosswalkError(f"{self.format}: bad records.mode {self.mode!r}")
        self.group_by: list = list(rec.get("group_by") or [])
        rows = rec.get("rows") or {}
        self.target: Optional[str] = rows.get("target")
        self.key: Optional[str] = rows.get("key")
        self.explode: Optional[dict] = rows.get("explode")
        info = format_info().get(self.format, {})
        self.fields: list = [f[0] for f in info.get("fields", [])]
        self.field_types: dict = {f[0]: (f[1], f[2]) for f in info.get("fields", [])}
        self.constants: dict = dict(raw.get("constants") or {})
        for p in self.constants:
            resolve_path(p)
        self.derive: list = list(raw.get("derive") or [])
        for d in self.derive:
            if d not in DERIVATIONS:
                raise CrosswalkError(f"{self.format}: unknown derivation {d!r}")
        self.rules = [Rule(r, self, i) for i, r in enumerate(raw.get("rules") or [])]
        self.unmapped: dict = {u["native"]: u for u in (raw.get("unmapped") or [])}
        self.rules_by_native: dict[str, list[Rule]] = {}
        for r in self.rules:
            self.rules_by_native.setdefault(r.native, []).append(r)
        self.computed = {r.native for r in self.rules if r.compute}

    def per_of(self, native: str) -> str:
        """Where an extras value goes in group mode: 'row' or 'record' (section 9)."""
        if self.mode != "group" or not self.target:
            return "record"
        if native in self.unmapped:
            return self.unmapped[native].get("per") or "row"
        rules = self.rules_by_native.get(native)
        if rules:
            return "row" if any(r.per_row for r in rules) else "record"
        return "row"

    def missing_default(self, native: str) -> Any:
        """The token from_core writes when the core has no value (section 3), else MISSING."""
        rules = self.rules_by_native.get(native, [])
        if len(rules) == 1 and rules[0].missing and rules[0].writes:
            return rules[0].missing[0]
        return MISSING

    def lossless_fields(self) -> list[str]:
        """Native fields that should survive native -> core -> native: unmapped fields
        (kept in extras), and fields whose rules all have lossy: null and that some
        rule can write back."""
        out = []
        for f in self.fields:
            rules = self.rules_by_native.get(f)
            if not rules:
                out.append(f)
            elif all(r.lossy is None for r in rules) and any(r.writes for r in rules):
                out.append(f)
        return out

# ---------------------------------------------------------------- writing the core (to_core)


class _Ctx:
    def __init__(self, fmt: str, filename: str, warnings: Optional[list]):
        self.fmt = fmt
        self.filename = filename
        self.warnings = warnings
        self.conflicts: list[dict] = []

    def warn(self, msg: str) -> None:
        msg = f"{self.fmt}{(' ' + self.filename) if self.filename else ''}: {msg}"
        log.debug(msg)
        if self.warnings is not None:
            self.warnings.append(msg)

    def conflict(self, path: str, kept: Any, other: Any) -> None:
        for c in self.conflicts:
            if c["path"] == path:
                if not any(_same(x["value"], other) for x in c["values"]):
                    c["values"].append({"value": copy.deepcopy(other)})
                return
        self.conflicts.append({"path": path, "values": [{"value": copy.deepcopy(kept)},
                                                         {"value": copy.deepcopy(other)}]})


def _join(prefix: str, name: str) -> str:
    return f"{prefix}.{name}" if prefix else name


def _set_member(ctx: _Ctx, obj: dict, name: str, value: Any, path: str) -> None:
    """Write a value to a non-array member (4.2): lists collapse, first value wins."""
    if isinstance(value, list):
        vals = [x for x in value if x is not None]
        if not vals:
            return
        value = vals[0]
        for extra in vals[1:]:
            if not _same(extra, value):
                ctx.conflict(path, value, extra)
    if name in obj and obj[name] is not None:
        old = obj[name]
        if isinstance(old, dict) and isinstance(value, dict):
            for k, v in value.items():
                if v is not None:
                    _set_member(ctx, old, k, v, _join(path, k))
        elif not _same(old, value):
            ctx.conflict(path, old, value)
        return
    obj[name] = copy.deepcopy(value)


def _set_element(ctx: _Ctx, arr: list, i: int, item: Any, path: str) -> None:
    cur = arr[i]
    if isinstance(item, dict) and isinstance(cur, dict):
        for k, v in item.items():
            if v is not None:
                _set_member(ctx, cur, k, v, _join(path, k))
    elif cur == {}:
        arr[i] = copy.deepcopy(item)
    elif not _same(cur, item):
        ctx.conflict(path, cur, item)


def _append_items(arr: list, value: Any) -> None:
    for item in value if isinstance(value, list) else [value]:
        if item is not None and not any(_same(item, x) for x in arr):
            arr.append(copy.deepcopy(item))


def _new_keyed(seg: Seg, info: SegInfo) -> dict:
    return {k: _cond_value(v, info.cond_types.get(k)) for k, v in seg.conds}


def put(ctx: _Ctx, obj: dict, segs: tuple, infos: tuple, value: Any, path: str = "",
        plus: Optional[dict] = None) -> None:
    """Write a value at a core path (4.1, 4.2)."""
    plus = {} if plus is None else plus
    seg, info = segs[0], infos[0]
    last = len(segs) == 1
    here = _join(path, seg.name)
    if seg.kind is None:
        if last:
            if info.is_array:
                arr = obj.get(seg.name)
                if not isinstance(arr, list):
                    arr = obj[seg.name] = []
                _append_items(arr, value)
            else:
                _set_member(ctx, obj, seg.name, value, here)
            return
        child = obj.get(seg.name)
        if child is None:
            child = obj[seg.name] = {}
        if not isinstance(child, dict):
            ctx.warn(f"cannot write {here}: it holds {child!r:.60}, not an object")
            return
        put(ctx, child, segs[1:], infos[1:], value, here, plus)
        return

    arr = obj.get(seg.name)
    if not isinstance(arr, list):
        arr = obj[seg.name] = []

    if seg.kind == "spread":
        items = value if isinstance(value, list) else [value]
        for i, item in enumerate(items):
            if item is None:
                continue
            while len(arr) <= i:
                arr.append({})
            if last:
                _set_element(ctx, arr, i, item, f"{here}[{i}]")
            elif isinstance(arr[i], dict):
                put(ctx, arr[i], segs[1:], infos[1:], item, f"{here}[{i}]", plus)
        return

    if seg.kind == "plus":
        key = id(arr)
        if key not in plus:
            arr.append({})
            plus[key] = (arr, len(arr) - 1)
        i = plus[key][1]
        if last:
            _set_element(ctx, arr, i, value, f"{here}[{i}]")
        else:
            put(ctx, arr[i], segs[1:], infos[1:], value, f"{here}[{i}]", plus)
        return

    if seg.kind == "index":
        i = seg.index
        while len(arr) <= i:
            arr.append({})
        if last:
            _set_element(ctx, arr, i, value, f"{here}[{i}]")
        else:
            put(ctx, arr[i], segs[1:], infos[1:], value, f"{here}[{i}]", plus)
        return

    # keyed element [k=v,...]
    rest = segs[1:]
    if len(rest) == 1 and rest[0].kind is None:
        member, member_array = rest[0].name, infos[1].is_array
        items = [value] if member_array or not isinstance(value, list) else value
        for item in items:
            if item is None:
                continue
            found = None
            for el in arr:
                if _matches(el, seg.conds) and (member not in el or _same(el[member], item)
                                                 or member_array):
                    found = el
                    break
            if found is None:
                found = _new_keyed(seg, info)
                arr.append(found)
            if member_array:
                _append_items(found.setdefault(member, []), item)
            else:
                found[member] = copy.deepcopy(item)
        return
    i = next((n for n, el in enumerate(arr) if _matches(el, seg.conds)), None)
    if i is None:
        arr.append(_new_keyed(seg, info))
        i = len(arr) - 1
    found = arr[i]
    if last:
        if isinstance(value, dict):
            _set_element(ctx, arr, i, value, f"{here}[{i}]")
        return
    put(ctx, found, rest, infos[1:], value, f"{here}[{i}]", plus)

# ---------------------------------------------------------------- reading the core (from_core)


class Multi(list):
    """Values gathered through a selector, in element order."""

    def __init__(self, items: Iterable = (), keyed: bool = False):
        super().__init__(items)
        self.keyed = keyed


def read(obj: Any, segs: tuple, plus_index: Optional[int] = None) -> Any:
    """Read a core path (4.1, 'On read'). Returns MISSING, a value, or a Multi."""
    if not segs:
        return obj
    seg = segs[0]
    if not isinstance(obj, dict) or seg.name not in obj or obj[seg.name] is None:
        return MISSING
    v = obj[seg.name]
    if seg.kind is None:
        return read(v, segs[1:], plus_index)
    if not isinstance(v, list):
        return MISSING
    if seg.kind == "plus" and plus_index is not None:
        return read(v[plus_index], segs[1:], plus_index) if plus_index < len(v) else MISSING
    if seg.kind in ("spread", "plus"):
        out = Multi()
        for el in v:
            r = read(el, segs[1:], plus_index)
            if isinstance(r, Multi):
                r = next((x for x in r if x is not None), None) if r.keyed else list(r)
            out.append(None if r is MISSING else r)
        return out
    if seg.kind == "index":
        return read(v[seg.index], segs[1:], plus_index) if seg.index < len(v) else MISSING
    out = Multi(keyed=True)
    for el in v:
        if _matches(el, seg.conds):
            r = read(el, segs[1:], plus_index)
            if isinstance(r, Multi):
                out.extend(x for x in r if x is not None)
            elif r is not MISSING and r is not None:
                out.append(r)
    return out


def _has_value(v: Any) -> bool:
    if v is MISSING or v is None:
        return False
    if isinstance(v, Multi):
        return any(x is not None for x in v)
    return True


def _plain(v: Any) -> Any:
    return list(v) if isinstance(v, Multi) else v

# ---------------------------------------------------------------- derivations (8)


def _sha512t24u_json(obj: Any) -> str:
    return _ga4gh._sha512t24u(_ga4gh._canonical(obj))


def _derive(rec: dict, names: list, ctx: _Ctx) -> None:
    for name in names:
        if name == "seqcol_digests":
            seqs = rec.get("sequences") or []
            col = rec.get("collection") or {}
            l1 = col.get("level1") or {}
            if seqs and all(isinstance(s, dict) and s.get("name") is not None and s.get("length") is not None
                            and s.get("digest") is not None for s in seqs):
                l2 = {"names": [s["name"] for s in seqs], "lengths": [s["length"] for s in seqs],
                      "sequences": [s["digest"] for s in seqs]}
                new_l1 = _ga4gh.level1_digests(l2)
                digest = _ga4gh.level0_digest(l2)
            elif l1.get("names") and l1.get("sequences"):
                new_l1 = {}
                digest = _ga4gh.level0_digest({"names": l1["names"], "sequences": l1["sequences"]})
            else:
                continue
            col = rec.setdefault("collection", {})
            if new_l1:
                have = col.setdefault("level1", {})
                for k, v in new_l1.items():
                    if k not in have:
                        have[k] = v
                    elif have[k] != v:
                        ctx.conflict(f"collection.level1.{k}", have[k], v)
            if "digest" not in col:
                col["digest"] = digest
            elif col["digest"] != digest:
                ctx.conflict("collection.digest", col["digest"], digest)
        elif name == "counts":
            seqs = rec.get("sequences") or []
            if not seqs:
                continue
            col = rec.setdefault("collection", {})
            n = len(seqs)
            if "nSequences" not in col:
                col["nSequences"] = n
            elif col["nSequences"] != n:
                ctx.conflict("collection.nSequences", col["nSequences"], n)
            lengths = [s.get("length") if isinstance(s, dict) else None for s in seqs]
            if all(isinstance(x, int) and not isinstance(x, bool) for x in lengths):
                total = sum(lengths)
                if "totalLength" not in col:
                    col["totalLength"] = total
                elif col["totalLength"] != total:
                    ctx.conflict("collection.totalLength", col["totalLength"], total)
        elif name == "accession_version":
            a = rec.get("assembly") or {}
            ver = a.get("version")
            if ver is None or not re.fullmatch(r"\d+", str(ver)):
                continue
            for item in a.get("accessions") or []:
                if (isinstance(item, dict) and item.get("namespace") in ("insdc.gca", "insdc.gcf")
                        and re.fullmatch(r"GC[AF]_\d{9}", str(item.get("value")))):
                    item["value"] = f"{item['value']}.{ver}"
        else:
            raise CrosswalkError(f"unknown derivation {name!r}")


def _compute(name: str, core: dict) -> Any:
    seqs = core.get("sequences") or []
    if not seqs or not all(isinstance(s, dict) for s in seqs):
        return MISSING
    if name == "seqcol_sorted_sequences":
        digests = [s.get("digest") for s in seqs]
        return MISSING if None in digests else sorted(digests)
    names = [s.get("name") for s in seqs]
    lengths = [s.get("length") for s in seqs]
    if None in names or None in lengths:
        return MISSING
    pairs = [{"length": ln, "name": nm} for nm, ln in zip(names, lengths)]
    if name == "seqcol_name_length_pairs":
        return pairs
    if name == "seqcol_sorted_name_length_pairs":
        return sorted(_sha512t24u_json(p) for p in pairs)
    raise CrosswalkError(f"unknown compute {name!r}")

# ---------------------------------------------------------------- to_core


_KEY_ORDER = ("refmeta", "subject", "assembly", "collection", "sequences", "copies", "deployments",
              "provenance", "fieldSources", "conflicts", "extras")


def _ordered(rec: dict) -> dict:
    out = {k: rec[k] for k in _KEY_ORDER if k in rec and rec[k] not in (None, {}, [])}
    out.update({k: v for k, v in rec.items() if k not in out and v not in (None, {}, [])})
    return out


def _explode(cw: Crosswalk, records: list[dict]) -> list[dict]:
    field, sep = cw.explode["field"], cw.explode.get("sep", ",")
    out = []
    for r in records:
        v = r.get(field)
        if isinstance(v, str):
            parts = [x.strip() for x in v.split(sep) if x.strip()]
            if parts:
                for part in parts:
                    c = dict(r)
                    c[field] = part
                    out.append(c)
                continue
        out.append(r)
    return out


def _groups(cw: Crosswalk, records: list[dict]) -> list[list[dict]]:
    if cw.mode == "each":
        return [[r] for r in records]
    order: list = []
    groups: dict = {}
    for r in records:
        k = tuple(json.dumps(r.get(g), sort_keys=True) for g in cw.group_by)
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)
    return [groups[k] for k in order]


def _native_input(rule: Rule, v: Any) -> Any:
    """The native value a rule reads, after `missing` tokens are removed; MISSING if none."""
    if v is None or (isinstance(v, list) and all(x is None for x in v)):
        return MISSING  # null, [] and [null, ...] count as absent
    if rule.missing:
        if rule.is_missing(v):
            return MISSING
        if isinstance(v, list):
            v = [x for x in v if not rule.is_missing(x)]
            if not v:
                return MISSING
    return v


def _rule_to_core(rule: Rule, row: dict, ctx: _Ctx) -> Any:
    """Forward value of a rule for a native row, or MISSING."""
    v = _native_input(rule, row.get(rule.native))
    if v is MISSING:
        return MISSING
    fails: list = []
    try:
        out = v
        for name, p in rule.transforms:
            out = _apply(name, p, out, False, None, fails)
    except NoValue:
        ctx.warn(f"{rule.native}={text_form(v)[:80]!s}: no value for {rule.core}")
        return MISSING
    if fails:  # some list items gave no value: dropped (section 7), not a warning
        log.debug("%s: %s: %d item(s) gave no value for %s", ctx.fmt, rule.native, len(fails), rule.core)
    if _is_empty(out) or out == []:
        return MISSING
    if isinstance(out, list) and not rule.spreads:
        out = [x for x in out if x is not None]
    return out


def to_core(format_id: str, records: list[dict], *, filename: str = "",
            provenance: Optional[dict] = None, warnings: Optional[list] = None) -> list[dict]:
    """Native records (an adapter's read() output) to core records (section 5).

    `provenance` adds members to provenance[0] (url, retrieved, authority, ...).
    `warnings`, if given, collects messages about values that no rule could use.
    """
    cw = load_crosswalk(format_id)
    out = []
    rows = _explode(cw, list(records)) if cw.explode else list(records)
    for group in _groups(cw, rows):
        ctx = _Ctx(format_id, os.path.basename(filename) if filename else "", warnings)
        rec: dict = {"refmeta": CORE_VERSION, "subject": cw.subject}
        first_record_value: dict[int, Any] = {}
        record_extras: dict = {}
        keyed: dict = {}
        for row in group:
            plus: dict = {}
            elem, elem_path = None, ""
            if cw.mode == "group" and cw.target:
                arr = rec.setdefault(cw.target, [])
                kv = row.get(cw.key) if cw.key else None
                kk = json.dumps(kv, sort_keys=True) if kv is not None else None
                if kk is not None and kk in keyed:
                    elem, idx = keyed[kk]
                else:
                    elem, idx = {}, len(arr)
                    arr.append(elem)
                    if kk is not None:
                        keyed[kk] = (elem, idx)
                elem_path = f"{cw.target}[{idx}]"
            used: set = set()
            for rule in cw.rules:
                if not rule.reads:
                    continue
                cv = _rule_to_core(rule, row, ctx)
                if cv is MISSING:
                    continue
                used.add(rule.native)
                if rule.per_row and elem is not None:
                    if len(rule.segs) == 1:
                        if isinstance(cv, dict):
                            for k, v in cv.items():
                                if v is not None:
                                    _set_member(ctx, elem, k, v, _join(elem_path, k))
                        continue
                    put(ctx, elem, rule.segs[1:], rule.infos[1:], cv, elem_path, plus)
                elif cw.mode == "group":
                    # record rule: the first row with a value gives it (5.2 step 3)
                    if rule.pos in first_record_value:
                        if first_record_value[rule.pos] != cv:
                            ctx.conflict(rule.core, first_record_value[rule.pos], cv)
                        continue
                    first_record_value[rule.pos] = copy.deepcopy(cv)
                    put(ctx, rec, rule.segs, rule.infos, cv, "", plus)
                else:
                    put(ctx, rec, rule.segs, rule.infos, cv, "", plus)
            # extras (section 9)
            for k, v in row.items():
                if v is None or k in used or k in cw.computed:
                    continue
                if k in cw.rules_by_native and _same(v, cw.missing_default(k)):
                    continue  # from_core writes this token back by itself
                if cw.per_of(k) == "row" and elem is not None:
                    elem.setdefault("extras", {}).setdefault(format_id, {})[k] = copy.deepcopy(v)
                elif k in record_extras:
                    if record_extras[k] != v:
                        ctx.conflict(f"extras.{format_id}.{k}", record_extras[k], v)
                else:
                    record_extras[k] = copy.deepcopy(v)
        if record_extras:
            rec.setdefault("extras", {})[format_id] = record_extras
        # constants (6), derivations (8.1), provenance
        for path, value in cw.constants.items():
            if not _has_value(read(rec, parse_path(path))):
                put(ctx, rec, parse_path(path), resolve_path(path), value)
        _derive(rec, cw.derive, ctx)
        p0 = {"id": "p1", "source": cw.source, "format": format_id}
        if filename:
            p0["file"] = os.path.basename(filename)
        prov = rec.get("provenance") or [{}]
        p0.update({k: v for k, v in prov[0].items() if k not in p0})
        if provenance:
            p0.update(provenance)
        prov[0] = p0
        rec["provenance"] = prov
        if ctx.conflicts:
            rec["conflicts"] = ctx.conflicts
        out.append(_ordered(rec))
    return out

# ---------------------------------------------------------------- from_core


def _shape(cw: Crosswalk, native: str, value: Any) -> Any:
    """Shape a value for a native field by its fields.json type (4.3); MISSING if none."""
    t, card = cw.field_types.get(native, (None, "one"))
    value = _plain(value)
    if t == "array" or card == "many":
        if value is None:
            return MISSING
        return value if isinstance(value, list) else [value]
    if isinstance(value, list):
        return next((x for x in value if x is not None), MISSING)
    return MISSING if value is None else value


def _rule_from_core(cw: Crosswalk, rule: Rule, obj: dict, segs: tuple, core: dict,
                    plus_index: Optional[int], ctx: _Ctx) -> Any:
    """Native value one rule gives, or MISSING."""
    if rule.compute:
        return _compute(rule.compute, core)
    raw = MISSING
    for path_segs in [segs] + [parse_path(p) for p in rule.fallback]:
        r = read(obj if path_segs is segs else core, path_segs, plus_index)
        if _has_value(r):
            raw = _plain(r)
            break
    if raw is MISSING:
        return MISSING
    fails: list = []
    try:
        val = raw
        if rule.direction == "both":
            for name, p in reversed(rule.transforms):
                val = _apply(name, p, val, True, rule.native_type, fails)
        else:
            for name, p in rule.transforms:
                val = _apply(name, p, val, False, None, fails)
    except NoValue:
        ctx.warn(f"{rule.native}: core value {text_form(raw)[:60]} has no native form")
        return MISSING
    if _is_empty(val):
        return MISSING
    return copy.deepcopy(val)


def _native_record(cw: Crosswalk, values: dict, extras: dict) -> dict:
    """Fill defaults and extras, order keys like fields.json."""
    out = dict(values)
    for k, v in extras.items():
        if k not in out or out[k] is MISSING:
            out[k] = copy.deepcopy(v)
    for k in list(out):
        if out[k] is MISSING:
            d = cw.missing_default(k)
            if d is MISSING:
                del out[k]
            else:
                out[k] = d
    for k in cw.rules_by_native:
        if k not in out and cw.missing_default(k) is not MISSING:
            out[k] = cw.missing_default(k)
    order = {f: i for i, f in enumerate(cw.fields)}
    return dict(sorted(out.items(), key=lambda kv: order.get(kv[0], len(order))))


def _values_for(cw: Crosswalk, rules: list[Rule], obj: dict, core: dict, ctx: _Ctx,
                plus_index: Optional[int] = None, row_mode: bool = False) -> dict:
    values: dict = {}
    for rule in rules:
        if not rule.writes:
            continue
        if values.get(rule.native, MISSING) is not MISSING:
            continue  # the first rule (file order) that yields a value wins
        segs = rule.segs[1:] if row_mode else rule.segs
        v = _rule_from_core(cw, rule, obj, segs, core, plus_index, ctx)
        if v is not MISSING:
            v = _shape(cw, rule.native, v)
        values[rule.native] = v
    return values


def from_core(format_id: str, core: dict | list[dict], *, warnings: Optional[list] = None) -> list[dict]:
    """Core record(s) to native records (sections 3, 5.3, 5.4, 9)."""
    cw = load_crosswalk(format_id)
    cores = core if isinstance(core, list) else [core]
    out: list[dict] = []
    for c in cores:
        if not isinstance(c, dict):
            raise ConversionError("a core record must be an object")
        ctx = _Ctx(format_id, "", warnings)
        c = copy.deepcopy(c)
        _derive(c, cw.derive, ctx)  # 8.1: so a writer can use them
        rec_extras = ((c.get("extras") or {}).get(format_id)) or {}
        if cw.mode == "each":
            values = _values_for(cw, cw.rules, c, c, ctx)
            out.append(_native_record(cw, values, rec_extras))
            continue
        row_rules = [r for r in cw.rules if r.per_row]
        rec_rules = [r for r in cw.rules if not r.per_row]
        rec_values = _values_for(cw, rec_rules, c, c, ctx)
        plus_rules = [r for r in row_rules if r.uses_plus]
        rows = []
        for el in c.get(cw.target) or []:
            if not isinstance(el, dict):
                continue
            el_extras = ((el.get("extras") or {}).get(format_id)) or {}
            if plus_rules:
                inner = read(el, plus_rules[0].plus_inner)
                indexes: list = list(range(len(inner))) if isinstance(inner, list) else []
            else:
                indexes = [None]
            for j in indexes:
                values = {}
                for rule in cw.rules:
                    if not rule.writes or values.get(rule.native, MISSING) is not MISSING:
                        continue
                    if rule.per_row:
                        v = _values_for(cw, [rule], el, c, ctx, plus_index=j, row_mode=True)[rule.native]
                    else:
                        v = rec_values.get(rule.native, MISSING)
                    values[rule.native] = v
                extras = dict(rec_extras)
                extras.update(el_extras)
                rows.append(_native_record(cw, values, extras))
        if cw.explode:
            rows = _merge_exploded(rows, cw.explode["field"], cw.explode.get("sep", ","))
        out.extend(rows)
    return out


def _merge_exploded(rows: list[dict], field: str, sep: str) -> list[dict]:
    """5.3 step 4: merge rows equal except for the explode field."""
    order: list = []
    merged: dict = {}
    for r in rows:
        key = json.dumps({k: v for k, v in r.items() if k != field}, sort_keys=True, default=str)
        if key not in merged:
            merged[key] = (r, [])
            order.append(key)
        v = r.get(field)
        if v is not None and text_form(v) not in merged[key][1]:
            merged[key][1].append(text_form(v))
    out = []
    for key in order:
        r, vals = merged[key]
        r = dict(r)
        if vals:
            r[field] = sep.join(vals)
        out.append(r)
    return out

# ---------------------------------------------------------------- merging (5.5)


def _is_name_list(v: Any) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) and "namespace" in x and "value" in x
                                                   for x in v)


def shared_identifiers(a: dict, b: dict) -> list[str]:
    """Identifiers two core records share (5.5 step 1)."""
    out = []
    def _accs(r: dict) -> set:
        return {(x.get("namespace"), x.get("value")) for x in (r.get("assembly") or {}).get("accessions") or []
                if isinstance(x, dict)}
    for ns, val in sorted(_accs(a) & _accs(b)):
        out.append(f"assembly.accessions={ns}:{val}")
    dg = (a.get("collection") or {}).get("digest")
    if dg and dg == (b.get("collection") or {}).get("digest"):
        out.append(f"collection.digest={dg}")
    for key in ("digest", "md5"):
        sa = {s.get(key) for s in a.get("sequences") or [] if isinstance(s, dict)} - {None}
        sb = {s.get(key) for s in b.get("sequences") or [] if isinstance(s, dict)} - {None}
        if sa & sb:
            out.append(f"sequences[].{key} ({len(sa & sb)} shared)")
    ca = {(c.get("location"), k, v) for c in a.get("copies") or [] for k, v in (c.get("checksums") or {}).items()}
    cb = {(c.get("location"), k, v) for c in b.get("copies") or [] for k, v in (c.get("checksums") or {}).items()}
    if ca & cb:
        out.append("copies[].location+checksum")
    return out


def _leaf_paths(obj: Any, path: str = "") -> set:
    """Crosswalk-style paths of the values in a core record (for fieldSources)."""
    out: set = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if path == "" and k in ("refmeta", "subject", "provenance", "fieldSources", "conflicts"):
                continue
            if k == "extras":
                continue
            out |= _leaf_paths(v, _join(path, k))
    elif isinstance(obj, list):
        if _is_name_list(obj):
            out |= {f"{path}[namespace={x['namespace']}].value" for x in obj}
        else:
            for x in obj:
                out |= _leaf_paths(x, path + "[]")
    elif obj is not None:
        out.add(path)
    return out


def _seq_key(s: dict) -> list:
    keys = []
    if s.get("digest"):
        keys.append(("digest", s["digest"]))
    if s.get("md5"):
        keys.append(("md5", s["md5"]))
    for al in s.get("aliases") or []:
        if isinstance(al, dict) and al.get("namespace") in ("insdc", "refseq"):
            keys.append((al["namespace"], al.get("value")))
    return keys


def _merge_value(ctx: _Ctx, a: Any, b: Any, path: str, pa: str, pb: str) -> Any:
    if a is None:
        return copy.deepcopy(b)
    if b is None:
        return a
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            a[k] = _merge_value(ctx, a.get(k), v, _join(path, k), pa, pb)
        return a
    if isinstance(a, list) and isinstance(b, list):
        if path == "assembly.accessions":  # one item per (namespace, value); url etc. merge
            return _merge_list_by(ctx, a, b, lambda x: [(x.get("namespace"), x.get("value"))], path, pa, pb)
        _append_items(a, b)  # Names and plain lists merge as sets
        return a
    if not _same(a, b):
        for c in ctx.conflicts:
            if c["path"] == path:
                if not any(_same(x["value"], b) for x in c["values"]):
                    c["values"].append({"value": copy.deepcopy(b), "provenance": pb})
                return a
        ctx.conflicts.append({"path": path, "values": [{"value": copy.deepcopy(a), "provenance": pa},
                                                       {"value": copy.deepcopy(b), "provenance": pb}]})
    return a


def _merge_list_by(ctx: _Ctx, a: list, b: list, keyf, path: str, pa: str, pb: str) -> list:
    index = {}
    for i, el in enumerate(a):
        for k in keyf(el):
            index.setdefault(k, i)
    for el in b:
        hit = next((index[k] for k in keyf(el) if k in index), None)
        if hit is None:
            a.append(copy.deepcopy(el))
            for k in keyf(el):
                index.setdefault(k, len(a) - 1)
        else:
            _merge_value(ctx, a[hit], el, f"{path}[{hit}]", pa, pb)
    return a


def merge(records: list[dict], *, require_shared_id: bool = True) -> dict:
    """Merge core records about the same thing into one (CROSSWALK_FORMAT.md 5.5).

    Records merge only if they share an identifier, unless require_shared_id is
    False (for records read from the same file). Scalars that differ go to
    conflicts (first kept); Name lists merge as sets; copies merge by location,
    deployments by system+scope+table+key, sequences by index when the collection
    digests match and otherwise by digest, md5, then an insdc or refseq alias.
    """
    if not records:
        raise ConversionError("nothing to merge")
    out = copy.deepcopy(records[0])
    out.setdefault("provenance", [{"id": "p1"}])
    sources = {p: {pr["id"] for pr in out["provenance"]}
               for p in _leaf_paths(out)} if "fieldSources" not in out else dict(out["fieldSources"])
    for rec in records[1:]:
        if require_shared_id and not shared_identifiers(out, rec):
            raise ConversionError("these records share no identifier (accession, seqcol digest, "
                                  "sequence digest or md5, or file location plus checksum)")
        rec = copy.deepcopy(rec)
        n = len(out["provenance"])
        renum = {}
        for i, pr in enumerate(rec.get("provenance") or [{"id": "p1"}]):
            renum[pr.get("id")] = f"p{n + i + 1}"
            pr = dict(pr, id=renum[pr.get("id")])
            out["provenance"].append(pr)
        pa = out["provenance"][0]["id"]
        pb = renum.get((rec.get("provenance") or [{"id": "p1"}])[0].get("id"), f"p{n + 1}")
        ctx = _Ctx("merge", "", None)
        ctx.conflicts = out.setdefault("conflicts", [])
        for c in rec.get("conflicts") or []:
            c = copy.deepcopy(c)
            for v in c["values"]:
                if "provenance" in v:
                    v["provenance"] = renum.get(v["provenance"], v["provenance"])
            ctx.conflicts.append(c)
        rec_sources = rec.get("fieldSources") or {p: {pr.get("id") for pr in rec.get("provenance") or [{"id": "p1"}]}
                                                  for p in _leaf_paths(rec)}
        for p, ids in rec_sources.items():
            sources.setdefault(p, set()).update(renum.get(i, i) for i in ids)
        for block in ("assembly", "collection"):
            if block in rec:
                out[block] = _merge_value(ctx, out.get(block), rec[block], block, pa, pb)
        a_seqs, b_seqs = out.get("sequences") or [], rec.get("sequences") or []
        if b_seqs:
            same_col = ((out.get("collection") or {}).get("digest")
                        and (out.get("collection") or {}).get("digest") == (rec.get("collection") or {}).get("digest"))
            if not a_seqs:
                out["sequences"] = copy.deepcopy(b_seqs)
            elif same_col and len(a_seqs) == len(b_seqs):
                for i, (x, y) in enumerate(zip(a_seqs, b_seqs)):
                    _merge_value(ctx, x, y, f"sequences[{i}]", pa, pb)
            else:
                _merge_list_by(ctx, a_seqs, b_seqs, _seq_key, "sequences", pa, pb)
        if rec.get("copies"):
            out["copies"] = _merge_list_by(ctx, out.get("copies") or [], rec["copies"],
                                           lambda c: [c["location"]] if c.get("location") else [],
                                           "copies", pa, pb)
        if rec.get("deployments"):
            out["deployments"] = _merge_list_by(
                ctx, out.get("deployments") or [], rec["deployments"],
                lambda d: [(d.get("system"), d.get("scope"), d.get("table"), d.get("key"))], "deployments", pa, pb)
        for fid, ex in (rec.get("extras") or {}).items():
            have = out.setdefault("extras", {}).setdefault(fid, {})
            for k, v in ex.items():
                have.setdefault(k, v)
    if len(out["provenance"]) > 1:
        out["fieldSources"] = {p: sorted(ids, key=lambda x: (len(x), x)) for p, ids in sorted(sources.items())}
    if not out.get("conflicts"):
        out.pop("conflicts", None)
    return _ordered(out)

# ---------------------------------------------------------------- renaming


def rename(records: list[dict], namespace: str, warnings: Optional[list] = None) -> list[dict]:
    """Name each sequence by its alias in `namespace` (PROPOSAL.md: 'pick a
    namespace, copy those aliases into name').

    Sequences with no alias in that namespace are left out, so every name in the
    result follows one style. If no sequence has such an alias, the record is
    returned unchanged (with a warning). If any name changes or a sequence is left
    out, the result is a different collection: the old collection's digest, level 1
    digests, counts, aliases, copies and deployments are dropped, and a relation
    points to the old digest.
    """
    warnings = [] if warnings is None else warnings
    out = []
    for rec in records:
        rec = copy.deepcopy(rec)
        seqs = rec.get("sequences") or []
        col = rec.get("collection") or {}
        old_ns = col.get("namingAuthority")
        hits = [next((al.get("value") for al in s.get("aliases") or []
                      if isinstance(al, dict) and al.get("namespace") == namespace), None) for s in seqs]
        if not any(h is not None for h in hits):
            if seqs:
                warnings.append(f"rename: no sequence has a {namespace} name; names left as they are")
            out.append(rec)
            continue
        changed = dropped = 0
        kept = []
        for s, hit in zip(seqs, hits):
            if hit is None:
                dropped += 1
                continue
            old = s.get("name")
            if old is not None and old != hit:
                changed += 1  # keep the old name as an alias ('unspecified' when its style is unknown)
                _append_items(s.setdefault("aliases", []), {"namespace": old_ns or "unspecified", "value": old})
            s["name"] = hit
            kept.append(s)
        if dropped:
            warnings.append(f"rename: {dropped} sequence(s) have no {namespace} name and were left out")
        rec["sequences"] = kept
        if changed or dropped:
            old_digest = col.get("digest")
            for k in ("digest", "level1", "nSequences", "totalLength", "aliases"):
                col.pop(k, None)
            if old_digest:
                _append_items(col.setdefault("relations", []),
                              {"type": "renamed" if not dropped else "derived_from", "digest": old_digest,
                               "method": "computed"})
            rec.pop("copies", None)
            rec.pop("deployments", None)
        col["namingAuthority"] = namespace
        rec["collection"] = col
        rec["subject"] = "collection"
        out.append(_ordered(rec))
    return out

# ---------------------------------------------------------------- files


_CORE_HINT = re.compile(r"^\s*(?:---\s*)?(?:-\s+)?[\"']?refmeta[\"']?\s*:\s*[\"']?0\.\d", re.M)


def _looks_like_core(text: str) -> bool:
    head = text.lstrip()[:2000]
    if head.startswith(("{", "[")):
        try:
            data = json.loads(text)
        except ValueError:
            return False
        items = data if isinstance(data, list) else [data]
        return bool(items) and all(isinstance(x, dict) and "refmeta" in x for x in items)
    return bool(_CORE_HINT.match(head))


def detect(text: str, filename: str = "") -> list[tuple[str, float]]:
    """Formats that could have written this text, best first: [(format_id, score)].
    Only formats with a crosswalk are listed; 'core' means a refmeta core record."""
    scores = []
    if _looks_like_core(text):
        scores.append((CORE, 1.0))
    cws = set(crosswalk_ids())
    for fid, fmt in formats().items():
        if fmt.detect is None or fid not in cws:
            continue
        try:
            s = float(fmt.detect(text, filename))
        except Exception:  # a detector must never break detection
            s = 0.0
        if s > 0:
            scores.append((fid, s))
    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores


def best_format(text: str, filename: str = "") -> str:
    found = detect(text, filename)
    if not found:
        raise ConversionError("could not tell which format this file is; pass the format explicitly")
    return found[0][0]


def read_native(text: str, format_id: str) -> list[dict]:
    try:
        fmt = formats()[format_id]
    except KeyError:
        raise ConversionError(f"unknown format {format_id!r}") from None
    try:
        return fmt.read(text)
    except ConversionError:
        raise
    except Exception as e:  # an adapter that cannot parse this text (bad JSON, XML, ...)
        raise ConversionError(f"cannot read this text as {format_id}: {type(e).__name__}: {e}") from e


def write_native(records: list[dict], format_id: str) -> str:
    try:
        fmt = formats()[format_id]
    except KeyError:
        raise ConversionError(f"unknown format {format_id!r}") from None
    if fmt.write is None:
        raise ConversionError(f"format {format_id!r} has no writer")
    return fmt.write(records)


def load_core(text: str) -> list[dict]:
    """Parse core record(s) from JSON or YAML text."""
    try:
        data = json.loads(text)
    except ValueError:
        docs = [d for d in yaml.load_all(text, Loader=_Loader) if d is not None]
        data = docs[0] if len(docs) == 1 else docs
    items = data if isinstance(data, list) else [data]
    if not items or not all(isinstance(x, dict) and "refmeta" in x for x in items):
        raise ConversionError("not a refmeta core record (no 'refmeta' member)")
    return items


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _str_presenter)


def dump_core(records: list[dict] | dict, fmt: str = "yaml") -> str:
    """Core record(s) as YAML or JSON text (one record as an object, several as a list)."""
    data = records[0] if isinstance(records, list) and len(records) == 1 else records
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


class Conversion(NamedTuple):
    text: str
    from_format: str
    to_format: str
    native_in: list
    core: list
    native_out: list
    warnings: list
    also_read: list  # companion formats read from the same file and merged in


def read_core(text: str, from_format: Optional[str] = None, filename: str = "",
              provenance: Optional[dict] = None, warnings: Optional[list] = None,
              companions: Optional[bool] = None) -> tuple[str, list, list, list]:
    """File text to core records: (format, native records, core records, companions read).

    Some files hold two formats at once (an NCBI assembly report has a header
    and a sequence table; a VCF header has contig and reference lines). When
    `companions` is true (the default when the format is detected), those
    formats are read too and merged into the record (5.5, same file).
    """
    warnings = [] if warnings is None else warnings
    src = from_format or best_format(text, filename)
    if src == CORE:
        return src, [], load_core(text), []
    native_in = read_native(text, src)
    cores = to_core(src, native_in, filename=filename, provenance=provenance, warnings=warnings)
    also = []
    if companions if companions is not None else from_format is None:
        for comp in format_info().get(src, {}).get("companions", []):
            if comp not in crosswalk_ids():
                continue
            try:
                recs = read_native(text, comp)
            except Exception:
                continue
            if not recs:
                continue
            extra = to_core(comp, recs, filename=filename, provenance=provenance, warnings=warnings)
            if len(cores) == 1 and len(extra) == 1:
                cores = [merge([cores[0], extra[0]], require_shared_id=False)]
                also.append(comp)
            else:
                warnings.append(f"{comp}: also in this file, but not merged "
                                f"({len(cores)} and {len(extra)} records)")
    return src, native_in, cores, also


def convert_detailed(text: str, to_format: str, from_format: Optional[str] = None, filename: str = "",
                     provenance: Optional[dict] = None, companions: Optional[bool] = None,
                     names: Optional[str] = None) -> Conversion:
    """Like convert(), but also returns the detected format, the core records and warnings.
    to_format may be 'core' (YAML) or 'core.json'. names: rename sequences to this
    namespace first (see rename())."""
    warnings: list = []
    src, native_in, cores, also = read_core(text, from_format, filename, provenance, warnings, companions)
    if names:
        cores = rename(cores, names, warnings)
    what = " + ".join([src] + also)
    if to_format in (CORE, "core.yaml", "core.json"):
        out = dump_core(cores, "json" if to_format == "core.json" else "yaml")
        return Conversion(out, src, to_format, native_in, cores, [], warnings, also)
    cw = load_crosswalk(to_format)
    native_out = from_core(to_format, cores, warnings=warnings)
    # drop records with nothing in them but `missing` tokens
    native_out = [r for r in native_out
                  if any(v is not None and not _same(v, cw.missing_default(k)) for k, v in r.items())]
    if not native_out:
        raise ConversionError(f"nothing to write: the {what} record has no fields that {to_format} can hold")
    try:
        out = write_native(native_out, to_format)
    except ConversionError:
        raise
    except KeyError as e:
        hint = " (try --names ucsc, or another naming style)" if any(
            not s.get("name") for c in cores for s in c.get("sequences") or []) else ""
        raise ConversionError(f"cannot write {to_format}: it needs field {e.args[0]!r}, "
                              f"which the {what} record does not give{hint}") from None
    except (ValueError, TypeError) as e:
        raise ConversionError(f"cannot write {to_format}: {e}") from None
    try:
        read_native(out, to_format)
    except Exception as e:  # the adapter wrote text it cannot read back
        warnings.append(f"{to_format}: the written text does not read back ({e})")
    return Conversion(out, src, to_format, native_in, cores, native_out, warnings, also)


def convert(text: str, to_format: str, from_format: Optional[str] = None, filename: str = "",
            names: Optional[str] = None) -> str:
    """Convert file text to another format through the core record.

    from_format=None detects the input format with the adapters' detect().
    names: give sequences their names in this namespace first (ucsc, ensembl, ...).
    """
    return convert_detailed(text, to_format, from_format, filename, names=names).text
