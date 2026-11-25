"""Export crosswalks as SSSOM mapping sets (https://w3id.org/sssom).

A crosswalk says how to convert a format; an SSSOM mapping set only says which native
field matches which core field, and how closely. This module writes that summary so
other tools can find and compare refmeta's mappings. The crosswalk stays the source of
truth: nothing here is read back.

One mapping set per format. Each rule becomes one row:

- subject: the native field (`<format_id>:<native path>`, percent-encoded)
- object: the core field (`refmeta:<core path>`). SSSOM ids cannot hold brackets, so
  selectors are dropped from the id (`collection.labels.value`) and the full path, with
  conditions such as `[namespace=galaxy.dbkey]`, goes in object_label
- predicate: a rule's `match` if it has one, else skos:exactMatch for a both-way rule
  with no `lossy` note, else skos:closeMatch
- unmapped fields: object sssom:NoTermFound, with the reason as the comment
"""
from __future__ import annotations

import yaml

import re
from urllib.parse import quote

from .convert import _data, crosswalk_ids, format_info

SITE = "https://refgenie.github.io/refmeta/"
SET_BASE = f"{SITE}sssom/"  # the site serves mapping/sssom/ here
CORE_URL = f"{SITE}core/0.1/core.schema.json"  # and mapping/core.schema.json here
FIELD_BASE = f"{SITE}#field/"  # opens that core field on the terms page
FORMAT_BASE = f"{SITE}format/"
LICENSE = "https://opensource.org/licenses/BSD-2-Clause"
MATCH = {
    "exact": "skos:exactMatch",
    "close": "skos:closeMatch",
    "broad": "skos:broadMatch",
    "narrow": "skos:narrowMatch",
    "related": "skos:relatedMatch",
}
COLUMNS = [
    "subject_id", "subject_label", "predicate_id", "object_id", "object_label",
    "mapping_justification", "subject_type", "object_type", "comment",
]


def _raw(format_id: str) -> dict:
    return yaml.safe_load(_data("crosswalk", f"{format_id}.yaml").read_text(encoding="utf-8"))


def _predicate(rule: dict) -> str:
    if rule.get("match"):
        return MATCH[rule["match"]]
    if rule.get("direction") == "both" and not rule.get("lossy"):
        return MATCH["exact"]
    return MATCH["close"]


def _element(path: str) -> str:
    """A path as an SSSOM-safe local id: selectors removed, other unsafe characters
    (the braces of `{genome}`, spaces) percent-encoded."""
    return quote(re.sub(r"\[[^\]]*\]", "", path), safe="._-~")


def _native(path: str) -> str:
    """A native path as an SSSOM-safe local id. Native keys are opaque (the crosswalk
    format never splits them), so nothing is removed; unsafe characters are encoded."""
    return quote(path, safe="._-~")


def _cell(v) -> str:
    return " ".join(str(v).split()) if v is not None else ""


def _comment(rule: dict) -> str:
    parts = []
    if rule.get("direction") != "both":
        parts.append(f"Used only {rule['direction'].replace('_', ' ')}.")
    if rule.get("transform"):
        names = [next(iter(t)) for t in (rule["transform"] if isinstance(rule["transform"], list)
                                          else [rule["transform"]])]
        parts.append(f"Value transformed ({', '.join(names)}).")
    if rule.get("compute"):
        parts.append(f"Computed on write ({_cell(rule['compute'])}).")
    if rule.get("lossy"):
        parts.append(f"Lossy: {rule['lossy']}")
    if rule.get("note"):
        parts.append(rule["note"])
    return _cell(" ".join(parts))


def mapping_set(format_id: str) -> tuple[dict, list[dict]]:
    """The mapping-set metadata and rows for one format."""
    cw = _raw(format_id)
    info = format_info().get(format_id, {})
    meta = {
        "curie_map": {
            format_id: f"{SET_BASE}{format_id}/field/",
            "refmeta": FIELD_BASE,
            "refmetaformat": FORMAT_BASE,
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "semapv": "https://w3id.org/semapv/vocab/",
        },
        "mapping_set_id": f"{SET_BASE}{format_id}.sssom.tsv",
        "mapping_set_version": f"core-{cw['core']}",
        "mapping_set_title": f"{format_id} to refmeta core",
        "mapping_set_description": _cell(cw.get("description")),
        "license": LICENSE,
        "subject_source": f"refmetaformat:{format_id}",
        "object_source": "refmetaformat:core",
        "object_source_version": cw["core"],
        "mapping_tool": "refmeta crosswalk (mapping/CROSSWALK_FORMAT.md)",
        "see_also": [u for u in (info.get("docs_url"), CORE_URL) if u],
    }
    rows = []
    for r in cw["rules"]:
        rows.append({
            "subject_id": f"{format_id}:{_native(r['native'])}",
            "subject_label": r["native"],
            "predicate_id": _predicate(r),
            "object_id": f"refmeta:{_element(r['core'])}" if r.get("core") else "sssom:NoTermFound",
            "object_label": r.get("core") or "",
            "mapping_justification": "semapv:ManualMappingCuration",
            "subject_type": "rdf property",
            "object_type": "rdf property" if r.get("core") else "",
            "comment": _comment(r),
        })
    for u in cw.get("unmapped", []):
        rows.append({
            "subject_id": f"{format_id}:{_native(u['native'])}",
            "subject_label": u["native"],
            "predicate_id": MATCH["exact"],
            "object_id": "sssom:NoTermFound",
            "mapping_justification": "semapv:ManualMappingCuration",
            "subject_type": "rdf property",
            "comment": _cell(u.get("reason")),
        })
    return meta, rows


def to_tsv(format_id: str) -> str:
    meta, rows = mapping_set(format_id)
    if any(r["object_id"] == "sssom:NoTermFound" for r in rows):
        meta["curie_map"]["sssom"] = "https://w3id.org/sssom/"
    header = "".join(f"#{line}\n" for line in
                     yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).splitlines())
    lines = ["\t".join(COLUMNS)]
    for r in rows:
        lines.append("\t".join(_cell(r.get(c)) for c in COLUMNS))
    return header + "\n".join(lines) + "\n"


def all_ids() -> tuple[str, ...]:
    return crosswalk_ids()
