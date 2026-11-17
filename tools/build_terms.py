"""Build the data file for the terms explorer page (web/index.html).

    python build_terms.py           # write ../web/terms_data.js
    python build_terms.py --check   # exit 1 if web/terms_data.js is out of date

The page lists every native term (field) of every format, with its definition,
example, and the shared core field it maps to, and links out to the format's
upstream docs and to the spec copy in this repository. It reads the sources of
truth directly:

  sources/*/fields.json     terms, definitions, examples, docs_url, spec_files
  mapping/crosswalk/*.yaml  which core field each term maps to, lossy notes,
                            and why unmapped terms have no core field
  mapping/core.schema.json  definitions of the core fields
  mapping/namespaces.yaml   the official namespaces

The output is a script that sets window.REFMETA_TERMS, so the page also works
when opened from file:// (browsers block fetch() there). Standard library plus
pyyaml only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent
TASK = TOOLS.parent
SOURCES = TASK / "sources"
MAPPING = TASK / "mapping"
OUT = TASK / "web" / "terms_data.js"

REPO = "https://github.com/refgenie/refmeta"
BRANCH = "master"

NAME_LISTS = {"aliases", "labels", "accessions"}
LEVEL_OF = {"assembly": "assembly", "collection": "collection", "sequences": "sequence",
            "copies": "copy", "deployments": "deployment", "provenance": "provenance"}
LEVEL_ORDER = ["assembly", "collection", "sequence", "copy", "deployment", "provenance", "other"]

_SEL = re.compile(r"\[([^\]]*)\]")


def normalize(core: str) -> tuple[str, str]:
    """A crosswalk core path -> (concept path without selectors, qualifier text).

    'collection.labels[namespace=galaxy.dbkey].value' -> ('collection.labels', 'galaxy.dbkey')
    'copies[kind=fasta].checksums.md5'                -> ('copies.checksums.md5', 'kind=fasta')
    """
    quals = []
    for sel in _SEL.findall(core):
        if sel in ("", "+") or sel.isdigit():
            continue
        for cond in sel.split(","):
            k, _, v = cond.partition("=")
            quals.append(v if k == "namespace" else cond)
    path = _SEL.sub("", core)
    segs = path.split(".")
    if len(segs) >= 2 and segs[-1] == "value" and segs[-2] in NAME_LISTS:
        segs = segs[:-1]
    return ".".join(segs), ", ".join(quals)


def level_of(path: str) -> str:
    return LEVEL_OF.get(path.split(".")[0], "other")


class Schema:
    def __init__(self, schema: dict):
        self.root = schema

    def _deref(self, s):
        n = 0
        while isinstance(s, dict) and "$ref" in s and n < 50:
            node = self.root
            for part in s["$ref"][2:].split("/"):
                node = node[part]
            s, n = node, n + 1
        return s

    def describe(self, path: str) -> tuple[str, str]:
        """(description, type) of a concept path. A field without its own description
        borrows its parent field's (assemblyAuthor.name -> assemblyAuthor), never a
        whole block's (assembly)."""
        node, descs, typ = self.root, [], ""
        for seg in path.split("."):
            node = self._deref(node)
            if node.get("type") == "array":
                node = self._deref(node.get("items", {}))
            props = node.get("properties", {})
            if seg in props:
                node = props[seg]
            elif isinstance(node.get("additionalProperties"), dict):
                node = node["additionalProperties"]
            else:
                break
            own = node.get("description", "")
            node_d = self._deref(node)
            descs.append(own or node_d.get("description", ""))
            t = node_d.get("type", "")
            typ = t if isinstance(t, str) else "/".join(t)
            if typ == "array":
                items = self._deref(node_d.get("items", {}))
                it = items.get("type", "")
                typ = f"array of {it}" if it else typ
        desc = descs[-1] if descs else ""
        if not desc and len(descs) >= 3:
            desc = descs[-2]
        return desc, typ


def load_crosswalks() -> dict[str, dict]:
    out = {}
    for f in sorted((MAPPING / "crosswalk").glob("*.yaml")):
        out[f.stem] = yaml.safe_load(f.read_text(encoding="utf-8"))
    return out


def _example(v):
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 160 else s[:157] + "..."


def build() -> str:
    schema = Schema(json.loads((MAPPING / "core.schema.json").read_text(encoding="utf-8")))
    crosswalks = load_crosswalks()
    namespaces = yaml.safe_load((MAPPING / "namespaces.yaml").read_text(encoding="utf-8"))["namespaces"]

    sources, formats, terms = {}, {}, []
    concepts: dict[str, dict] = {}
    for fj in sorted(SOURCES.glob("*/fields.json")):
        inv = json.loads(fj.read_text(encoding="utf-8"))
        src = fj.parent.name
        sources[src] = {"title": inv.get("title", src), "maintainer": inv.get("maintainer", ""),
                        "retrieved": inv.get("retrieved", ""),
                        "readme": f"{REPO}/blob/{BRANCH}/sources/{src}/README.md"}
        for fm in inv["formats"]:
            cw = crosswalks.get(fm["id"])
            formats[fm["id"]] = {
                "source": src,
                "description": fm.get("description", ""),
                "docs": fm.get("docs_url") or "",
                "specs": [f"{REPO}/blob/{BRANCH}/sources/{src}/{p}" for p in fm.get("spec_files", [])],
                "crosswalk": f"{REPO}/blob/{BRANCH}/mapping/crosswalk/{fm['id']}.yaml" if cw else "",
            }
        for fld in inv["fields"]:
            fid = fld["format"]
            cw = crosswalks.get(fid)
            maps, why = [], None
            if cw is None:
                why = "This format has no crosswalk yet, so its terms are not mapped."
            else:
                seen = {}
                for r in cw.get("rules") or []:
                    if r.get("native") != fld["path"]:
                        continue
                    if r.get("compute"):
                        key = ("sequences", f"computed: {r['compute']}")
                    else:
                        key = normalize(r["core"])
                    m = seen.get(key)
                    if m is None:
                        m = seen[key] = {"core": key[0], "q": key[1], "dir": [], "lossy": ""}
                        maps.append(m)
                    m["dir"].append(r.get("direction", "both"))
                    if r.get("lossy") and not m["lossy"]:
                        m["lossy"] = r["lossy"]
                for m in maps:
                    d = set(m["dir"])
                    m["dir"] = "both" if "both" in d or d == {"to_core", "from_core"} else d.pop()
                    if not m["lossy"]:
                        del m["lossy"]
                    if not m["q"]:
                        del m["q"]
                if not maps:
                    why = next((u.get("reason", "") for u in cw.get("unmapped") or []
                                if u.get("native") == fld["path"]), "") or "No rule maps this term."
            t = {"f": fid, "p": fld["path"], "d": fld.get("description", ""), "l": fld.get("level", ""),
                 "t": fld.get("type", ""), "c": fld.get("cardinality", "")}
            ex = _example(fld.get("example"))
            if ex is not None:
                t["x"] = ex
            if fld.get("notes"):
                t["n"] = fld["notes"]
            if maps:
                t["m"] = maps
                for m in maps:
                    if m["core"] not in concepts:
                        desc, typ = schema.describe(m["core"])
                        concepts[m["core"]] = {"path": m["core"], "level": level_of(m["core"]),
                                               "d": desc, "t": typ}
            else:
                t["u"] = why
            terms.append(t)

    # within a level, the fields that the most sources share come first
    n_src: dict[str, set] = {}
    for t in terms:
        for m in t.get("m", []):
            n_src.setdefault(m["core"], set()).add(formats[t["f"]]["source"])
    concept_list = sorted(concepts.values(), key=lambda c: (LEVEL_ORDER.index(c["level"]),
                                                           -len(n_src.get(c["path"], ())), c["path"]))
    data = {
        "repo": REPO,
        "branch": BRANCH,
        "levels": LEVEL_ORDER,
        "sources": sources,
        "formats": formats,
        "concepts": concept_list,
        "terms": terms,
        "namespaces": namespaces,
    }
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    return ("/* refmeta terms explorer data. Generated by tools/build_terms.py; do not edit. */\n"
            f"window.REFMETA_TERMS = {body};\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="only report whether the data file is current")
    args = ap.parse_args(argv)
    text = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("build_terms: web/terms_data.js is out of date; run `python build_terms.py`", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    d = json.loads(text.split("=", 1)[1].rstrip().rstrip(";"))
    n_mapped = sum(1 for t in d["terms"] if "m" in t)
    print(f"build_terms: wrote web/terms_data.js ({len(text) // 1024} KB): {len(d['terms'])} terms "
          f"({n_mapped} mapped) from {len(d['formats'])} formats, {len(d['concepts'])} shared fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
