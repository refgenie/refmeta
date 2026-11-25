"""Write the SSSOM mapping sets (one per crosswalk) into mapping/sssom/.

    python build_sssom.py           # write ../mapping/sssom/<format>.sssom.tsv
    python build_sssom.py --check   # exit 1 if mapping/sssom/ is out of date

The crosswalks are the source of truth; these files are generated from the package copy
(run sync_data.py first). See refmeta/sssom.py for how rules become SSSOM rows.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from refmeta import sssom

OUT = Path(__file__).resolve().parent.parent / "mapping" / "sssom"


def planned() -> dict[Path, str]:
    return {OUT / f"{f}.sssom.tsv": sssom.to_tsv(f) for f in sssom.all_ids()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="only report whether mapping/sssom/ is current")
    args = ap.parse_args(argv)
    files = planned()
    write = [p for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    delete = sorted(set(OUT.glob("*.sssom.tsv")) - set(files)) if OUT.exists() else []
    if args.check:
        for p in write + delete:
            print(f"out of date: {p.name}")
        return 1 if (write or delete) else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p in write:
        p.write_text(files[p], encoding="utf-8")
    for p in delete:
        p.unlink()
    print(f"mapping/sssom: {len(write)} written, {len(delete)} removed, {len(files)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
