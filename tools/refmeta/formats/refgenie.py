"""refgenie formats: registry genome YAML, store build table, refgenie 1.x
server API records, and the legacy refgenie 0.x genome_config.yaml.

Field paths are documented in sources/refgenie/fields.json. Conventions:

- Nested objects become dotted keys ("organism.taxon_id").
- An array of objects becomes parallel lists, one per member, keyed
  "<array>[].<member>" ("fasta.sources[].url"). Missing members are None.
- Arrays of scalars stay lists.
- Null values are dropped: a missing key means "not given".
- The legacy genome_config is keyed by data (genome digest, asset name, tag
  name). Those levels appear as placeholders in the path
  ("genomes.{genome}.assets.{asset}.tags.{tag}.asset_digest"), and the key
  that is exactly the placeholder path holds the map key itself.
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import re
from itertools import zip_longest
from typing import Any

import yaml

from . import Format

SOURCE = "refgenie"


# ---------------------------------------------------------------- helpers


def _norm(v: Any) -> Any:
    """Make YAML values JSON-serializable (dates become ISO strings)."""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def _flatten(obj: dict, obj_arrays: dict[str, list[str]] | None = None, prefix: str = "") -> dict:
    """Flatten nested dicts to dotted keys; arrays of objects to parallel lists."""
    obj_arrays = obj_arrays or {}
    out: dict[str, Any] = {}
    for key, val in obj.items():
        path = f"{prefix}{key}"
        if val is None:
            continue
        if isinstance(val, dict):
            out.update(_flatten(val, obj_arrays, prefix=f"{path}."))
        elif isinstance(val, list) and (
            path in obj_arrays or (val and all(isinstance(x, dict) for x in val))
        ):
            members: list[str] = list(obj_arrays.get(path, []))
            for item in val:
                for m in item:
                    if m not in members:
                        members.append(m)
            for m in members:
                out[f"{path}[].{m}"] = [item.get(m) for item in val]
        else:
            out[path] = val
    return out


def _set_path(d: dict, parts: list[str], val: Any) -> None:
    for p in parts[:-1]:
        nxt = d.get(p)
        if not isinstance(nxt, dict):
            nxt = d[p] = {}
        d = nxt
    d[parts[-1]] = val


def _unflatten(rec: dict) -> dict:
    """Inverse of _flatten."""
    out: dict[str, Any] = {}
    arrays: dict[str, dict[str, list]] = {}
    order: list[tuple[str, str]] = []  # ("key", k) or ("array", path)
    for k, v in rec.items():
        if "[]." in k:
            path, member = k.split("[].", 1)
            if path not in arrays:
                arrays[path] = {}
                order.append(("array", path))
            arrays[path][member] = list(v) if v is not None else []
        else:
            order.append(("key", k))
    for kind, k in order:
        if kind == "key":
            _set_path(out, k.split("."), rec[k])
        else:
            members = arrays[k]
            names = list(members)
            items = []
            for row in zip_longest(*[members[m] for m in names]):
                items.append({m: x for m, x in zip(names, row) if x is not None})
            _set_path(out, k.split("."), items)
    return out


def _load_json(text: str) -> Any:
    return json.loads(text)


def _try_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _try_yaml_first(text: str) -> Any:
    try:
        for doc in yaml.safe_load_all(text):
            if doc is not None:
                return doc
    except Exception:
        return None
    return None


def _objects(data: Any) -> list[dict]:
    """A JSON body that is one object or a list of objects."""
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        return data
    raise ValueError("expected a JSON object or a list of objects")


def _dump_json(objs: list[dict]) -> str:
    body: Any = objs[0] if len(objs) == 1 else objs
    return json.dumps(body, indent=2, ensure_ascii=False) + "\n"


class _Dumper(yaml.SafeDumper):
    pass


def _str_rep(dumper: yaml.SafeDumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_rep)


def _dump_yaml(obj: Any) -> str:
    return yaml.dump(obj, Dumper=_Dumper, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _ext(filename: str | None) -> str:
    return (filename or "").lower()


# ------------------------------------------------- 1. registry genome YAML

REGISTRY_OBJ_ARRAYS = {
    "fasta.sources": ["provider", "url"],
    "fhr.metadata_author": ["name", "uri"],
    "fhr.assembly_author": ["name", "uri"],
}


def read_registry_genome(text: str) -> list[dict]:
    recs = []
    for doc in yaml.safe_load_all(text):
        if doc is None:
            continue
        if not isinstance(doc, dict):
            raise ValueError("registry genome YAML must be a mapping")
        recs.append(_flatten(_norm(doc), REGISTRY_OBJ_ARRAYS))
    return recs


def write_registry_genome(records: list[dict]) -> str:
    return "---\n".join(_dump_yaml(_unflatten(r)) for r in records)


def detect_registry_genome(text: str, filename: str = "") -> float:
    doc = _try_yaml_first(text)
    if not isinstance(doc, dict) or "name" not in doc or "organism" not in doc:
        return 0.0
    score = 0.6
    if "seqcol" in doc or "fasta" in doc:
        score = 0.8
    if "build" in doc and "seqcol" in doc:
        score = 0.95
    if isinstance(doc.get("organism"), dict) and "taxon_id" in doc["organism"]:
        score = max(score, 0.85)
    return score


# --------------------------------------------- 2. store build table (CSV)

_SOURCES_COLS = {"name", "organism", "source", "genome_assembly", "accession", "synonyms", "group", "version"}


def read_store_sources(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "fasta" not in reader.fieldnames:
        raise ValueError("sources.csv needs a 'fasta' column")
    recs = []
    for row in reader:
        recs.append({k: v for k, v in row.items() if k is not None and v not in (None, "")})
    return recs


def write_store_sources(records: list[dict]) -> str:
    cols: list[str] = ["fasta"]
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in records:
        w.writerow({k: r.get(k, "") for k in cols})
    return buf.getvalue()


def detect_store_sources(text: str, filename: str = "") -> float:
    first = text.lstrip("﻿").split("\n", 1)[0].strip()
    if "," not in first:
        return 0.0
    cols = {c.strip() for c in next(csv.reader([first]))}
    if "fasta" not in cols:
        return 0.0
    hits = len(cols & _SOURCES_COLS)
    if hits == 0:
        return 0.2
    score = 0.8 if hits >= 2 else 0.6
    if _ext(filename).endswith("sources.csv"):
        score = 0.95
    return score


# ------------------------------------------ 3. refgenie 1.x API: genome

API_FHR_OBJ_ARRAYS = {"fhr.metadataAuthor": ["name", "uri"], "fhr.assemblyAuthor": ["name", "uri"]}

GENOME_DETAIL_KEYS = [
    "digest", "description", "species_name", "synonyms", "taxon_id", "assembly_source",
    "assembly_accession", "assembly_level", "remote_url", "common_name", "taxon_uri",
    "fhr", "species", "refget_store_url",
]


def read_api_genome(text: str) -> list[dict]:
    return [_flatten(o, API_FHR_OBJ_ARRAYS) for o in _objects(_load_json(text))]


def _with_nulls(obj: dict, keys: list[str]) -> dict:
    out = {k: obj.get(k) for k in keys}
    for k, v in obj.items():
        if k not in out:
            out[k] = v
    return out


def write_api_genome(records: list[dict]) -> str:
    return _dump_json([_with_nulls(_unflatten(r), GENOME_DETAIL_KEYS) for r in records])


def detect_api_genome(text: str, filename: str = "") -> float:
    data = _try_json(text)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if not isinstance(data, dict) or "digest" not in data or "results" in data:
        return 0.0
    if "alias" in data or "n_sequences" in data:
        return 0.0
    if "species_name" in data or "assembly_accession" in data:
        if {"fhr", "refget_store_url", "taxon_uri"} & set(data):
            return 0.9
        return 0.6
    return 0.0


# ------------------------------------- 4. refgenie 1.x API: genome listing

GENOME_LIST_KEYS = [
    "digest", "aliases", "description", "asset_count", "species_name", "common_name",
    "synonyms", "taxon_id", "assembly_source", "assembly_accession", "assembly_level", "species",
]


def read_api_genome_list(text: str) -> list[dict]:
    data = _load_json(text)
    if isinstance(data, dict) and "results" in data:
        items = data["results"]
    else:
        items = data
    return [_flatten(o) for o in _objects(items)] if items else []


def write_api_genome_list(records: list[dict]) -> str:
    results = [_with_nulls(_unflatten(r), GENOME_LIST_KEYS) for r in records]
    body = {
        "results": results,
        "pagination": {"page": 0, "page_size": max(100, len(results)), "total": len(results)},
    }
    return json.dumps(body, indent=2, ensure_ascii=False) + "\n"


def detect_api_genome_list(text: str, filename: str = "") -> float:
    data = _try_json(text)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return 0.0
    if "pagination" not in data:
        return 0.0
    res = data["results"]
    if not res:
        return 0.3
    first = res[0]
    if isinstance(first, dict) and "digest" in first and ("asset_count" in first or "aliases" in first):
        return 0.9
    return 0.0


# ------------------------------------------ 5. refgenie 1.x API: alias

ALIAS_KEYS = ["alias", "digest", "source", "collection", "fhr"]


def read_api_alias(text: str) -> list[dict]:
    return [_flatten(o, API_FHR_OBJ_ARRAYS) for o in _objects(_load_json(text))]


def write_api_alias(records: list[dict]) -> str:
    objs = []
    for r in records:
        o = _with_nulls(_unflatten(r), ALIAS_KEYS)
        if o.get("collection") is None:
            o["collection"] = {}
        objs.append(o)
    return _dump_json(objs)


def detect_api_alias(text: str, filename: str = "") -> float:
    data = _try_json(text)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if isinstance(data, dict) and {"alias", "digest", "collection"} <= set(data):
        return 0.95
    return 0.0


# ------------------------- 6. refgenie 1.x API: genome sequences (per row)

SEQ_HEADER_ARRAYS = {"collection_aliases": ["namespace", "alias"]}
SEQ_ROW_ARRAYS = {"aliases": ["namespace", "alias"]}
SEQ_HEADER_TOP = ["digest", "n_sequences", "total_length", "level1", "collection_aliases"]
SEQ_ROW_KEYS = ["name", "length", "sha512t24u", "md5", "alphabet", "description", "aliases"]


def _is_header_key(k: str) -> bool:
    top = k.split("[]", 1)[0].split(".", 1)[0]
    return top in SEQ_HEADER_TOP


def read_api_sequences(text: str) -> list[dict]:
    recs = []
    for body in _objects(_load_json(text)):
        header = _flatten({k: v for k, v in body.items() if k != "sequences"}, SEQ_HEADER_ARRAYS)
        for row in body.get("sequences") or []:
            rec = dict(header)
            rec.update(_flatten(row, SEQ_ROW_ARRAYS))
            recs.append(rec)
    return recs


def write_api_sequences(records: list[dict]) -> str:
    bodies: dict[Any, dict] = {}
    for r in records:
        hdr = {k: v for k, v in r.items() if _is_header_key(k)}
        row = {k: v for k, v in r.items() if not _is_header_key(k)}
        key = r.get("digest")
        if key not in bodies:
            body = _unflatten(hdr)
            body["sequences"] = []
            bodies[key] = body
        bodies[key]["sequences"].append(_with_nulls(_unflatten(row), SEQ_ROW_KEYS))
    return _dump_json(list(bodies.values()))


def detect_api_sequences(text: str, filename: str = "") -> float:
    data = _try_json(text)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if isinstance(data, dict) and {"n_sequences", "level1", "sequences"} <= set(data):
        return 0.95
    return 0.0


# ------------------------------- 7. legacy refgenie 0.x genome_config.yaml

G = "genomes.{genome}"
A = G + ".assets.{asset}"
T = A + ".tags.{tag}"
_HEX48 = re.compile(r"^[0-9a-f]{48}$")


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def read_genome_config(text: str) -> list[dict]:
    data = _norm(yaml.safe_load(text))
    if not isinstance(data, dict):
        raise ValueError("genome config must be a mapping")
    if "genomes" in data:
        top = _drop_none({k: v for k, v in data.items() if k != "genomes"})
        genomes = data.get("genomes") or {}
    else:  # a bare genomes block, e.g. refgenieserver's /genomes/dict
        top, genomes = {}, data
    recs = []
    for gname, g in genomes.items():
        g = g or {}
        base = dict(top)
        base[G] = gname
        for k, v in g.items():
            if k != "assets" and v is not None:
                base[f"{G}.{k}"] = v
        assets = g.get("assets") or {}
        if not assets:
            recs.append(base)
            continue
        for aname, a in assets.items():
            a = a or {}
            abase = dict(base)
            abase[A] = aname
            for k, v in a.items():
                if k != "tags" and v is not None:
                    abase[f"{A}.{k}"] = v
            tags = a.get("tags") or {}
            if not tags:
                recs.append(abase)
                continue
            for tname, t in tags.items():
                rec = dict(abase)
                rec[T] = tname
                for k, v in (t or {}).items():
                    if v is not None:
                        rec[f"{T}.{k}"] = v
                recs.append(rec)
    return recs


def write_genome_config(records: list[dict]) -> str:
    top: dict[str, Any] = {}
    genomes: dict[str, dict] = {}
    for r in records:
        for k, v in r.items():
            if not k.startswith("genomes.") and k not in top:
                top[k] = v
        gname = r.get(G)
        if gname is None:
            if any(k.startswith("genomes.") and v is not None for k, v in r.items()):
                raise KeyError(G)  # genome-level values with no genome key: refuse, do not drop them
            continue
        gd = genomes.setdefault(gname, {})
        aname, tname = r.get(A), r.get(T)
        ad = td = None
        if aname is not None:
            ad = gd.setdefault("assets", {}).setdefault(aname, {})
            if tname is not None:
                td = ad.setdefault("tags", {}).setdefault(tname, {})
        for k, v in r.items():
            if k in (G, A, T):
                continue
            if k.startswith(T + "."):
                if td is not None:
                    td[k[len(T) + 1:]] = v
            elif k.startswith(A + "."):
                if ad is not None:
                    ad[k[len(A) + 1:]] = v
            elif k.startswith(G + "."):
                gd[k[len(G) + 1:]] = v
    for gd in genomes.values():
        gd.setdefault("assets", {})
    out = dict(top)
    out["genomes"] = genomes
    return _dump_yaml(out)


def detect_genome_config(text: str, filename: str = "") -> float:
    data = _try_yaml_first(text)
    if not isinstance(data, dict):
        return 0.0
    if isinstance(data.get("genomes"), dict):
        if {"genome_folder", "config_version", "genome_servers"} & set(data):
            return 0.95
        return 0.5
    vals = list(data.values())[:5]
    keys = list(data)[:5]
    if vals and all(isinstance(v, dict) and ("assets" in v or "genome_description" in v) for v in vals):
        return 0.85 if all(_HEX48.match(str(k)) for k in keys) else 0.6
    return 0.0


# ----------------------------------------------------------------- FORMATS

FORMATS = [
    Format(
        id="refgenie_registry_genome",
        source=SOURCE,
        description="refgenie-registry genome entry (genomes/<organism>/<name>.yaml): one named sequence collection with organism, assembly, FASTA sources and seqcol digest",
        read=read_registry_genome,
        write=write_registry_genome,
        detect=detect_registry_genome,
        extensions=(".yaml", ".yml"),
    ),
    Format(
        id="refgenie_store_sources",
        source=SOURCE,
        description="refgenie-registry RefgetStore build table (stores/<store>/sources.csv): one FASTA to load per row",
        read=read_store_sources,
        write=write_store_sources,
        detect=detect_store_sources,
        extensions=(".csv",),
    ),
    Format(
        id="refgenie_api_genome",
        source=SOURCE,
        description="refgenie 1.x server genome record (GET /v4/genomes/{digest}, GenomeDetailResponse)",
        read=read_api_genome,
        write=write_api_genome,
        detect=detect_api_genome,
        extensions=(".json",),
    ),
    Format(
        id="refgenie_api_genome_list",
        source=SOURCE,
        description="refgenie 1.x server genome listing (GET /v4/genomes, PageResponse[GenomeResponse]); one record per genome, with all its aliases",
        read=read_api_genome_list,
        write=write_api_genome_list,
        detect=detect_api_genome_list,
        extensions=(".json",),
    ),
    Format(
        id="refgenie_api_alias",
        source=SOURCE,
        description="refgenie 1.x server alias resolution (GET /v4/aliases/{name}, AliasResponse): digest, seqcol level-2 arrays and FHR",
        read=read_api_alias,
        write=write_api_alias,
        detect=detect_api_alias,
        extensions=(".json",),
    ),
    Format(
        id="refgenie_api_sequences",
        source=SOURCE,
        description="refgenie 1.x server sequence table (GET /v4/genomes/{digest}/sequences); one record per sequence, collection fields repeated",
        read=read_api_sequences,
        write=write_api_sequences,
        detect=detect_api_sequences,
        extensions=(".json",),
    ),
    Format(
        id="refgenie_genome_config",
        source=SOURCE,
        description="legacy refgenie 0.x genome configuration (genome_config.yaml, config_version 0.4; also refgenieserver's /genomes/dict); one record per genome/asset/tag",
        read=read_genome_config,
        write=write_genome_config,
        detect=detect_genome_config,
        extensions=(".yaml", ".yml", ".json"),
    ),
]
