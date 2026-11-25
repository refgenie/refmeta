"""refmeta command line.

    refmeta formats [--source S]              list the formats refmeta reads and writes
    refmeta detect FILE                       guess a file's format
    refmeta core FILE [--from F] [--json]     print the core record (YAML by default)
    refmeta convert FILE --to F [--from F]    convert a file to another format
    refmeta sssom [FORMAT ...] [-o DIR]       export crosswalks as SSSOM mapping sets

FILE may be '-' for standard input. --to and --from also accept 'core'.
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from . import convert as C
from .validate import check_namespaces


def _read(path: str) -> tuple[str, str]:
    if path == "-":
        return sys.stdin.read(), ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read(), path


def _write(text: str, out: Optional[str]) -> None:
    if out and out != "-":
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def _report(warnings: list, verbose: bool) -> None:
    if not warnings:
        return
    if verbose:
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
    else:
        print(f"refmeta: {len(warnings)} value(s) could not be mapped and were kept as extras "
              f"or skipped (-v to list them)", file=sys.stderr)


def cmd_formats(args) -> int:
    rows = [r for r in C.list_formats() if not args.source or r["source"] == args.source]
    width = max((len(r["id"]) for r in rows), default=10)
    for r in rows:
        rw = ("r" if r["read"] else "-") + ("w" if r["write"] else "-")
        desc = r["description"].split(". ")[0].split(": ")[0][:70]
        print(f"{r['id']:<{width}}  {r['source']:<12} {rw}  {desc}")
    return 0


def cmd_detect(args) -> int:
    text, name = _read(args.file)
    found = C.detect(text, name)
    if not found:
        print("unknown format", file=sys.stderr)
        return 1
    print(found[0][0])
    if args.all or args.verbose:
        for fid, score in found[:10]:
            print(f"  {score:.2f}  {fid}", file=sys.stderr)
    return 0


def cmd_core(args) -> int:
    text, name = _read(args.file)
    res = C.convert_detailed(text, "core.json" if args.json else C.CORE, args.from_format, name,
                             names=args.names)
    _report(res.warnings, args.verbose)
    if args.verbose:
        print(f"refmeta: read as {' + '.join([res.from_format] + res.also_read)}", file=sys.stderr)
        for core in res.core:
            for note in check_namespaces(core):
                print(f"namespace: {note}", file=sys.stderr)
    _write(res.text, args.output)
    return 0


def cmd_convert(args) -> int:
    text, name = _read(args.file)
    res = C.convert_detailed(text, args.to_format, args.from_format, name, names=args.names)
    _report(res.warnings, args.verbose)
    if args.verbose:
        print(f"refmeta: read as {' + '.join([res.from_format] + res.also_read)}", file=sys.stderr)
    _write(res.text, args.output)
    return 0


def cmd_sssom(args) -> int:
    import os

    from . import sssom
    ids = args.formats or sssom.all_ids()
    unknown = [f for f in ids if f not in sssom.all_ids()]
    if unknown:
        raise C.ConversionError(f"no crosswalk for {', '.join(unknown)}")
    if not args.output:
        for f in ids:
            sys.stdout.write(sssom.to_tsv(f))
        return 0
    os.makedirs(args.output, exist_ok=True)
    for f in ids:
        _write(sssom.to_tsv(f), os.path.join(args.output, f"{f}.sssom.tsv"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="refmeta", description="Convert reference genome metadata "
                                 "between formats through one shared core record.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("formats", help="list formats")
    p.add_argument("--source", help="only formats from this source (ncbi, ucsc, ...)")
    p.set_defaults(func=cmd_formats)

    p = sub.add_parser("detect", help="guess a file's format")
    p.add_argument("file")
    p.add_argument("-a", "--all", action="store_true", help="also list other candidate formats")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_detect)

    p = sub.add_parser("core", help="print a file as a refmeta core record")
    p.add_argument("file")
    p.add_argument("--from", dest="from_format", help="input format id (default: detect)")
    p.add_argument("--json", action="store_true", help="print JSON instead of YAML")
    p.add_argument("--names", help="rename sequences to this naming style first (ucsc, ensembl, insdc, ...)")
    p.add_argument("-o", "--output", help="write here instead of standard output")
    p.add_argument("-v", "--verbose", action="store_true", help="list warnings and namespace notes")
    p.set_defaults(func=cmd_core)

    p = sub.add_parser("convert", help="convert a file to another format")
    p.add_argument("file")
    p.add_argument("--to", dest="to_format", required=True, help="output format id, or 'core'")
    p.add_argument("--names", help="rename sequences to this naming style first (ucsc, ensembl, insdc, ...)")
    p.add_argument("--from", dest="from_format", help="input format id (default: detect)")
    p.add_argument("-o", "--output", help="write here instead of standard output")
    p.add_argument("-v", "--verbose", action="store_true", help="list warnings")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("sssom", help="export crosswalks as SSSOM mapping sets")
    p.add_argument("formats", nargs="*", help="format ids (default: all)")
    p.add_argument("-o", "--output", help="write one <format>.sssom.tsv per format into this folder")
    p.set_defaults(func=cmd_sssom)
    return ap


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (C.ConversionError, OSError) as e:
        print(f"refmeta: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
