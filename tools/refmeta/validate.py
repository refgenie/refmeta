"""A small JSON Schema validator, standard library only.

It covers the keywords core.schema.json uses: $ref (local #/$defs/...), type,
enum, const, required, properties, patternProperties, additionalProperties,
propertyNames, items, minimum, maximum, minLength and pattern. It is not a full
draft 2020-12 validator; use the `jsonschema` package for that when it is
installed (see validate_core).
"""
from __future__ import annotations

import re
from typing import Any, Iterator

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _where(path: tuple) -> str:
    out = ""
    for p in path:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out or "(root)"


def _resolve(root: dict, schema: dict) -> dict:
    seen = 0
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"only local $ref is supported: {ref}")
        node: Any = root
        for part in ref[2:].split("/"):
            node = node[part]
        schema = node
        seen += 1
        if seen > 50:
            raise ValueError("$ref loop")
    return schema


def iter_errors(instance: Any, schema: dict, root: dict | None = None,
                path: tuple = ()) -> Iterator[str]:
    root = schema if root is None else root
    schema = _resolve(root, schema)
    if schema is True or schema == {}:
        return
    if schema is False:
        yield f"{_where(path)}: no value allowed here"
        return

    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_TYPES[x](instance) for x in types):
            yield f"{_where(path)}: {instance!r:.80} is not of type {'/'.join(types)}"
            return
    if "const" in schema and instance != schema["const"]:
        yield f"{_where(path)}: {instance!r:.80} is not {schema['const']!r}"
    if "enum" in schema and instance not in schema["enum"]:
        yield f"{_where(path)}: {instance!r:.80} is not one of {schema['enum']}"

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            yield f"{_where(path)}: string shorter than {schema['minLength']}"
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            yield f"{_where(path)}: {instance!r:.80} does not match {schema['pattern']}"
    if _TYPES["number"](instance):
        if "minimum" in schema and instance < schema["minimum"]:
            yield f"{_where(path)}: {instance} is less than {schema['minimum']}"
        if "maximum" in schema and instance > schema["maximum"]:
            yield f"{_where(path)}: {instance} is more than {schema['maximum']}"

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            yield from iter_errors(item, schema["items"], root, path + (i,))

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                yield f"{_where(path)}: missing required member {req!r}"
        props = schema.get("properties", {})
        pattern_props = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties", True)
        names = schema.get("propertyNames")
        for key, value in instance.items():
            if names is not None:
                for err in iter_errors(key, names, root, path + (key,)):
                    yield f"{_where(path + (key,))}: member name invalid ({err.split(': ', 1)[-1]})"
            matched = False
            if key in props:
                matched = True
                yield from iter_errors(value, props[key], root, path + (key,))
            for pat, sub in pattern_props.items():
                if re.search(pat, key):
                    matched = True
                    yield from iter_errors(value, sub, root, path + (key,))
            if not matched:
                if additional is False:
                    yield f"{_where(path)}: unexpected member {key!r}"
                elif isinstance(additional, dict):
                    yield from iter_errors(value, additional, root, path + (key,))


def validate(instance: Any, schema: dict) -> list[str]:
    """All error messages (empty when the instance is valid)."""
    return list(iter_errors(instance, schema))


def validate_core(record: dict) -> list[str]:
    """Validate a core record against core.schema.json.

    Uses the `jsonschema` package when it can be imported (full draft
    2020-12), and this module's subset validator otherwise.
    """
    from .convert import load_schema

    schema = load_schema()
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return validate(record, schema)
    v = jsonschema.Draft202012Validator(schema)
    return [f"{_where(tuple(e.absolute_path))}: {e.message}" for e in v.iter_errors(record)]


NAME_LISTS = ("assembly.accessions", "assembly.labels", "collection.aliases", "collection.labels",
              "sequences.aliases")


def _name_lists(record: dict):
    """(list path, item) for every {namespace, value} item in a core record."""
    for block, key in (("assembly", "accessions"), ("assembly", "labels"),
                       ("collection", "aliases"), ("collection", "labels")):
        for x in (record.get(block) or {}).get(key) or []:
            yield f"{block}.{key}", x
    for s in record.get("sequences") or []:
        for x in (s.get("aliases") or []) if isinstance(s, dict) else []:
            yield "sequences.aliases", x


def check_namespaces(record: dict) -> list[str]:
    """Notes on the namespaces a core record uses, checked against
    mapping/namespaces.yaml. Not schema errors: custom namespaces are allowed.

    Reports (one line per namespace and list):
    - custom: a namespace that is not official;
    - misplaced: an official namespace in a list it is not meant for;
    - pattern: values that do not match an official namespace's pattern.
    """
    from .convert import load_namespaces

    reg = load_namespaces()
    custom: dict = {}
    misplaced: dict = {}
    bad: dict = {}
    for where, x in _name_lists(record):
        if not isinstance(x, dict):
            continue
        ns, val = x.get("namespace"), x.get("value")
        entry = reg.get(ns)
        if entry is None:
            custom.setdefault((where, ns), []).append(val)
            continue
        if where not in entry.get("lists", []):
            misplaced.setdefault((where, ns), []).append(val)
        pat = entry.get("pattern")
        if pat and isinstance(val, str) and not re.fullmatch(pat, val):
            bad.setdefault((where, ns), []).append(val)
    out = []
    for (where, ns), vals in custom.items():
        out.append(f"{where}: custom namespace {ns!r} ({len(vals)} value(s), e.g. {vals[0]!r})")
    for (where, ns), vals in misplaced.items():
        out.append(f"{where}: namespace {ns!r} is not meant for this list "
                   f"({len(vals)} value(s), e.g. {vals[0]!r})")
    for (where, ns), vals in bad.items():
        out.append(f"{where}: {len(vals)} value(s) do not match the {ns!r} pattern, e.g. {vals[0]!r}")
    return out
