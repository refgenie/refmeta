"""Format adapters, one module per source (e.g. ncbi.py).

Each module defines FORMATS, a list of Format objects. A Format turns file
text into "native records" and back. A native record is a flat dict whose keys
are exactly the field paths listed for that format in
sources/<source>/fields.json, with JSON-serializable values.

Adapters use only the standard library and pyyaml, so they also run in the
browser (Pyodide). They take and return text, never paths.
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Format:
    id: str  # e.g. "ncbi_datasets_report"
    source: str  # folder name under sources/, e.g. "ncbi"
    description: str
    read: Callable[[str], list[dict]]  # file text -> native records
    write: Optional[Callable[[list[dict]], str]] = None  # native records -> file text
    detect: Optional[Callable[[str, str], float]] = None  # (text, filename) -> 0..1
    extensions: tuple[str, ...] = field(default_factory=tuple)


def all_formats() -> dict[str, Format]:
    out: dict[str, Format] = {}
    for mod_info in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{mod_info.name}")
        for fmt in getattr(mod, "FORMATS", []):
            if fmt.id in out:
                raise ValueError(f"duplicate format id {fmt.id}")
            out[fmt.id] = fmt
    return out
