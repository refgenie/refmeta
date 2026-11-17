"""Python side of the refmeta converter page (web/convert.html).

The page runs this module in Pyodide next to the refmeta package; build_web.py
bundles both. Every conversion goes through refmeta.convert. This module only
keeps the dropped file, reuses the core record read from it, and turns results
and errors into JSON text, so the page never handles Python objects.

    catalog()                  every format, for the dropdowns
    set_input(text, filename)  the file to work on
    analyze(from_format)       detect, read and describe the core record
    convert(to_format, names)  write the record in another format
    scan(ids_json, names)      which target formats can hold the record
"""
from __future__ import annotations

import copy
import json
import re
import traceback
from contextlib import contextmanager
from typing import Any, Optional

from refmeta import convert as C
from refmeta.validate import validate_core

SOURCE_NAMES = {
    "bioconductor": "Bioconductor", "ena": "ENA", "ensembl": "Ensembl", "fhr": "FHR",
    "ga4gh": "GA4GH", "galaxy": "Galaxy", "ncbi": "NCBI", "nfcore": "nf-core",
    "refgenie": "refgenie", "ucsc": "UCSC",
}
AMBIGUOUS_GAP = 0.15  # a second guess this close to the best one is shown to the user
CORE_TARGETS = (C.CORE, "core.json")

_state: dict = {"text": "", "filename": "", "read": None}


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _short(desc: str) -> str:
    """The first phrase of a format description, as a menu label."""
    cut = len(desc)
    for sep in (": ", "; ", ", one ", ". ", " ("):
        i = desc.find(sep)
        if 6 < i < cut:
            cut = i
    s = desc[:cut].strip()
    return s if len(s) <= 64 else s[:61].rstrip() + "..."


def label(fid: str) -> str:
    """'UCSC chrom.sizes (ucsc_chrom_sizes)'."""
    if fid in CORE_TARGETS:
        return "the refmeta core record"
    f = C.formats().get(fid)
    desc = (f.description if f else "") or C.format_info().get(fid, {}).get("description", "")
    return f"{_short(desc)} ({fid})" if desc else fid


def catalog() -> str:
    info = C.format_info()
    rows = []
    for r in C.list_formats():
        rows.append({
            "id": r["id"], "source": r["source"],
            "sourceName": SOURCE_NAMES.get(r["source"], r["source"]),
            "label": _short(r["description"]), "description": r["description"],
            "read": r["read"], "write": r["write"], "extensions": r["extensions"],
            "companions": info.get(r["id"], {}).get("companions", []),
        })
    return _dump({"formats": rows, "coreVersion": C.CORE_VERSION})


def set_input(text: str, filename: str = "") -> None:
    _state.update(text=text, filename=filename or "", read=None)


def _fail(kind: str, message: str, **more) -> str:
    return _dump({"ok": False, "kind": kind, "error": message, **more})


def _namespaces(cores: list) -> list:
    """Naming styles the sequences have aliases in, most complete first."""
    counts: dict = {}
    total = 0
    for c in cores:
        for s in c.get("sequences") or []:
            total += 1
            seen = set()
            for al in s.get("aliases") or []:
                ns = al.get("namespace") if isinstance(al, dict) else None
                if ns and ns not in seen:
                    seen.add(ns)
                    counts[ns] = counts.get(ns, 0) + 1
    return [{"namespace": ns, "count": n, "total": total}
            for ns, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]


def analyze(from_format: Optional[str] = None) -> str:
    """Read the current file into core records. from_format None or '' means detect."""
    text, name = _state["text"], _state["filename"]
    _state["read"] = None
    if not text.strip():
        return _fail("empty", "This file is empty.")
    detected = [[f, round(s, 3)] for f, s in C.detect(text, name)]
    auto = not from_format
    if auto and not detected:
        return _fail("unknown", "refmeta could not tell which format this file is. If it is one of "
                     "the formats under 'Read as', pick it there and refmeta will read it that way.",
                     detected=[])
    fmt = from_format or detected[0][0]
    if not auto and detected and fmt == detected[0][0]:
        auto = True  # picking the detected format by hand is the same as detecting it
    notes = []
    if not auto and fmt != C.CORE and all(f != fmt for f, _ in detected):
        notes.append(f"This file does not look like {label(fmt)}: its detector gives it no "
                     f"score. The record below may be empty or wrong.")
    others = [f for f, _ in detected if f != fmt][:4]
    warnings: list = []
    try:
        # companions=True when detected: the same rule the CLI follows
        src, native_in, cores, also = C.read_core(text, fmt, name, warnings=warnings,
                                                  companions=True if auto else None)
    except C.ConversionError as e:
        msg = str(e)
        return _fail("read", msg[:1].upper() + msg[1:], format=fmt, auto=auto,
                     detected=detected[:8], others=others)
    except Exception as e:  # a reader that chokes on the text
        return _fail("read", f"The {fmt} reader stopped with {type(e).__name__}: {e}", format=fmt,
                     auto=auto, detected=detected[:8], others=others)
    if not cores:
        return _fail("norecords", f"refmeta read this file as {label(src)} but found no records in it.",
                     format=src, auto=auto, detected=detected[:8], others=others)
    ambiguous = []
    if auto and detected:
        best, best_score = detected[0]
        skip = {best, *also, *C.format_info().get(best, {}).get("companions", [])}
        ambiguous = [[f, s] for f, s in detected[1:] if f not in skip and s >= best_score - AMBIGUOUS_GAP]
    _state["read"] = (src, native_in, copy.deepcopy(cores), also, list(warnings))
    try:
        core_json = C.dump_core(cores, "json")
    except (TypeError, ValueError):
        core_json = json.dumps(cores[0] if len(cores) == 1 else cores, indent=2, ensure_ascii=False,
                               default=str) + "\n"
    return _dump({
        "ok": True, "format": src, "auto": auto, "detected": detected[:8], "alsoRead": also,
        "ambiguous": ambiguous, "notes": notes, "records": cores, "nativeRecords": len(native_in),
        "yaml": C.dump_core(cores), "json": core_json, "warnings": warnings,
        "invalid": [validate_core(c) for c in cores], "namespaces": _namespaces(cores),
    })


@contextmanager
def _reusing(read: tuple):
    """Let convert_detailed() reuse the records analyze() read, instead of reading
    and detecting the file again for every target format."""
    original = C.read_core
    src, native_in, cores, also, warns = read

    def cached(text, from_format=None, filename="", provenance=None, warnings=None, companions=None):
        if warnings is not None:
            warnings.extend(warns)
        return src, native_in, copy.deepcopy(cores), also

    C.read_core = cached
    try:
        yield
    finally:
        C.read_core = original


_NAMES_HINT = re.compile(r"\s*\(try --names [^)]*\)")


def _convert(to_format: str, names: Optional[str]) -> dict:
    read = _state["read"]
    if read is None:
        return {"ok": False, "kind": "state", "error": "Read a file first."}
    try:
        with _reusing(read):
            res = C.convert_detailed(_state["text"], to_format, read[0], _state["filename"],
                                     names=names or None)
    except C.ConversionError as e:
        msg = str(e)
        if _NAMES_HINT.search(msg):
            msg = _NAMES_HINT.sub("", msg) + ". Its sequences have no names of their own: choose a " \
                  "naming style under 'Sequence names'."
        return {"ok": False, "kind": "conversion", "error": msg[:1].upper() + msg[1:]}
    except Exception as e:
        return {"ok": False, "kind": "bug",
                "error": f"refmeta hit an unexpected error while writing {label(to_format)}: "
                         f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-3000:]}
    return {"ok": True, "text": res.text, "format": to_format, "warnings": res.warnings,
            "records": len(res.native_out) if res.native_out else len(res.core)}


def convert(to_format: str, names: Optional[str] = None) -> str:
    return _dump(_convert(to_format, names))


def scan(ids_json: str, names: Optional[str] = None) -> str:
    """{format id: null when it can hold the record, else the reason it cannot}."""
    out = {}
    for fid in json.loads(ids_json):
        r = _convert(fid, names)
        out[fid] = None if r["ok"] else r["error"]
    return _dump(out)
