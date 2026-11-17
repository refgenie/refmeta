"""Tests for the refgenie adapters (refmeta/formats/refgenie.py)."""
import json

import pytest

from refmeta.formats import all_formats
from refmeta.formats import refgenie as rg

FORMATS = {f.id: f for f in rg.FORMATS}


@pytest.fixture
def inventory(sources_dir):
    return json.loads((sources_dir / "refgenie" / "fields.json").read_text())


def _example_cases(inventory):
    for fmt in inventory["formats"]:
        if fmt["adapter"]:
            for rel in fmt["example_files"]:
                yield fmt["id"], rel


def test_formats_registered(inventory):
    registered = all_formats()
    for fmt in inventory["formats"]:
        if fmt["adapter"]:
            assert fmt["id"] in registered
            assert registered[fmt["id"]].source == "refgenie"
    assert set(FORMATS) == {f["id"] for f in inventory["formats"] if f["adapter"]}


def test_every_format_has_examples(inventory, sources_dir):
    for fmt in inventory["formats"]:
        assert fmt["example_files"], fmt["id"]
        for rel in fmt["example_files"] + fmt["spec_files"]:
            assert (sources_dir / "refgenie" / rel).is_file(), rel


def test_read_examples_keys_in_inventory(inventory, sources_dir):
    paths = {}
    for f in inventory["fields"]:
        paths.setdefault(f["format"], set()).add(f["path"])
    for fid, rel in _example_cases(inventory):
        text = (sources_dir / "refgenie" / rel).read_text()
        records = FORMATS[fid].read(text)
        assert records, rel
        for rec in records:
            json.dumps(rec)  # JSON-serializable
            unknown = set(rec) - paths[fid]
            assert not unknown, (rel, unknown)


def test_write_then_read_roundtrip(inventory, sources_dir):
    for fid, rel in _example_cases(inventory):
        fmt = FORMATS[fid]
        if fmt.write is None:
            continue
        records = fmt.read((sources_dir / "refgenie" / rel).read_text())
        assert fmt.read(fmt.write(records)) == records, rel


def test_detect_picks_own_format(inventory, sources_dir):
    for fid, rel in _example_cases(inventory):
        text = (sources_dir / "refgenie" / rel).read_text()
        name = rel.rsplit("/", 1)[-1]
        scores = {k: f.detect(text, name) for k, f in FORMATS.items()}
        assert max(scores, key=scores.get) == fid, (rel, scores)
        assert scores[fid] >= 0.5, (rel, scores)


def test_inventory_examples_match_records(inventory, sources_dir):
    """Every non-null example in fields.json is a value some example record has."""
    seen = {}
    for fid, rel in _example_cases(inventory):
        for rec in FORMATS[fid].read((sources_dir / "refgenie" / rel).read_text()):
            for k, v in rec.items():
                seen.setdefault((fid, k), []).append(v)
    for f in inventory["fields"]:
        if f["example"] is None:
            continue
        assert f["example"] in seen.get((f["format"], f["path"]), []), (f["format"], f["path"])


def test_anchor_values():
    """Spot checks on the anchor genomes."""
    hg38 = rg.read_registry_genome(
        "name: hg38\naliases: [GRCh38]\ndescription: x\norganism: {scientific_name: Homo sapiens, taxon_id: 9606}\n"
        "fasta:\n  sources:\n    - url: https://example.org/a.fa.gz\n    - provider: NCBI\n      url: https://example.org/b.fa.gz\n"
        "seqcol: {digest: EiFob05aCWgVU_B_Ae0cypnQut3cxUP1}\nbuild: {store: legacy, tier: full}\nmetadata: {added: 2026-05-20}\n"
    )[0]
    assert hg38["fasta.sources[].provider"] == [None, "NCBI"]
    assert hg38["metadata.added"] == "2026-05-20"
    out = rg.write_registry_genome([hg38])
    assert rg.read_registry_genome(out) == [hg38]
    assert "provider" not in out.split("- url: https://example.org/a.fa.gz")[1].split("\n")[0]


def test_sequences_rows_carry_collection(sources_dir):
    text = (sources_dir / "refgenie" / "examples" / "api_sequences_R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.json").read_text()
    rows = rg.read_api_sequences(text)
    assert len(rows) == 17
    assert {r["digest"] for r in rows} == {"ia9g4Myony-xxLsSc7eQOC_NdClGgPGu"}
    assert rows[5]["name"] == "Mito" and rows[5]["length"] == 85779
    assert rows[0]["aliases[].alias"] == []


def test_genome_config_rows(sources_dir):
    text = (sources_dir / "refgenie" / "examples" / "legacy_genome_config_refgenomes.databio.org_hg38.yaml").read_text()
    rows = rg.read_genome_config(text)
    fasta = [r for r in rows if r["genomes.{genome}.assets.{asset}"] == "fasta"]
    assert len(fasta) == 1
    r = fasta[0]
    assert r["genomes.{genome}"] == "2230c535660fb4774114bfa966a62f823fdb6d21acf138d4"
    assert r["genomes.{genome}.aliases"] == ["hg38"]
    assert r["genomes.{genome}.assets.{asset}.tags.{tag}.seek_keys"]["fasta"].endswith(".fa")
    assert r["config_version"] == 0.4
