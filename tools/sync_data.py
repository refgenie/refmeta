"""Copy the mapping files into the refmeta package, so the engine can load them
as package data (the same way in a normal install and in the browser).

    python sync_data.py          # write refmeta/data/
    python sync_data.py --check  # exit 1 if refmeta/data/ is out of date

Sources of truth (never edit the copies):
  mapping/crosswalk/*.yaml  -> refmeta/data/crosswalk/*.yaml   (copied as is)
  mapping/core.schema.json  -> refmeta/data/core.schema.json   (copied as is)
  mapping/namespaces.yaml   -> refmeta/data/namespaces.yaml    (copied as is)
  sources/*/fields.json     -> refmeta/data/formats.json       (compact field
                               types, which the engine needs to shape values
                               when it writes native records)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TASK = TOOLS.parent
MAPPING = TASK / "mapping"
SOURCES = TASK / "sources"
DATA = TOOLS / "refmeta" / "data"


def build_formats() -> str:
    """Compact per-format info from every sources/*/fields.json."""
    out: dict[str, dict] = {}
    shared: dict[str, set] = {}  # example file -> adapter formats that read it
    for fj in sorted(SOURCES.glob("*/fields.json")):
        inv = json.loads(fj.read_text(encoding="utf-8"))
        for fm in inv["formats"]:
            if fm.get("adapter"):
                for ex in fm.get("example_files", []):
                    shared.setdefault(f"{fj.parent.name}/{ex}", set()).add(fm["id"])
    for fj in sorted(SOURCES.glob("*/fields.json")):
        inv = json.loads(fj.read_text(encoding="utf-8"))
        src = fj.parent.name
        by_fmt: dict[str, list] = {}
        for f in inv["fields"]:
            by_fmt.setdefault(f["format"], []).append([f["path"], f["type"], f["cardinality"]])
        for fm in inv["formats"]:
            # companions: other formats that read the same files (an NCBI assembly
            # report holds a header format and a sequence-table format)
            companions = sorted({c for ex in fm.get("example_files", [])
                                 for c in shared.get(f"{src}/{ex}", ())} - {fm["id"]})
            out[fm["id"]] = {
                "source": src,
                "companions": companions if fm.get("adapter") else [],
                "description": fm.get("description", ""),
                "maintainer": inv.get("maintainer", ""),
                "retrieved": inv.get("retrieved", ""),
                "adapter": bool(fm.get("adapter")),
                "extensions": fm.get("extensions", []),
                "example_files": fm.get("example_files", []),
                "fields": by_fmt.get(fm["id"], []),
            }
    return json.dumps(dict(sorted(out.items())), indent=1, ensure_ascii=False) + "\n"


def planned() -> dict[Path, str]:
    """Every file refmeta/data/ should hold, with its content."""
    files: dict[Path, str] = {}
    for src in sorted((MAPPING / "crosswalk").glob("*.yaml")):
        files[DATA / "crosswalk" / src.name] = src.read_text(encoding="utf-8")
    files[DATA / "core.schema.json"] = (MAPPING / "core.schema.json").read_text(encoding="utf-8")
    files[DATA / "namespaces.yaml"] = (MAPPING / "namespaces.yaml").read_text(encoding="utf-8")
    files[DATA / "formats.json"] = build_formats()
    return files


def stale(files: dict[Path, str]) -> tuple[list[Path], list[Path]]:
    """(files to write, files to delete)."""
    write = [p for p, text in files.items()
             if not p.exists() or p.read_text(encoding="utf-8") != text]
    existing = set((DATA / "crosswalk").glob("*.yaml")) if (DATA / "crosswalk").exists() else set()
    delete = sorted(existing - set(files))
    return write, delete


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="only report whether refmeta/data/ is current")
    args = ap.parse_args(argv)
    files = planned()
    write, delete = stale(files)
    if args.check:
        for p in write:
            print(f"out of date: {p.relative_to(TOOLS)}")
        for p in delete:
            print(f"not in mapping/: {p.relative_to(TOOLS)}")
        return 1 if (write or delete) else 0
    for p in write:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(files[p], encoding="utf-8")
    for p in delete:
        p.unlink()
    print(f"refmeta/data: {len(write)} written, {len(delete)} removed, {len(files)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
