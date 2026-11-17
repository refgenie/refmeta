"""The terms explorer data (tools/build_terms.py -> web/terms_data.js)."""
import importlib.util
import json
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]


def _build():
    spec = importlib.util.spec_from_file_location("build_terms", TOOLS / "build_terms.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = mod.build()
    return mod, json.loads(text.split("=", 1)[1].rstrip().rstrip(";"))


def test_terms_data_is_complete():
    mod, d = _build()
    concepts = {c["path"] for c in d["concepts"]}
    assert len(d["terms"]) > 2000 and len(d["formats"]) >= 100
    for c in d["concepts"]:
        assert c["d"], f"shared field {c['path']} has no definition in core.schema.json"
    for t in d["terms"]:
        assert t["f"] in d["formats"]
        assert ("m" in t) != ("u" in t), t  # mapped, or a reason why not
        for m in t.get("m", []):
            assert m["core"] in concepts
    for f in d["formats"].values():
        assert f["docs"] == "" or f["docs"].startswith("https://") or f["docs"].startswith("http://")


def test_terms_data_file_is_current():
    mod, _ = _build()
    assert mod.OUT.read_text(encoding="utf-8") == mod.build(), "run `python build_terms.py`"


def test_normalize_core_paths():
    mod, _ = _build()
    assert mod.normalize("collection.labels[namespace=galaxy.dbkey].value") == ("collection.labels", "galaxy.dbkey")
    assert mod.normalize("copies[kind=fasta].checksums.md5") == ("copies.checksums.md5", "kind=fasta")
    assert mod.normalize("sequences[].aliases[+].value") == ("sequences.aliases", "")
    assert mod.normalize("assembly.accessions[0].url") == ("assembly.accessions.url", "")
