"""Tests for the UCSC adapter (refmeta/formats/ucsc.py) against sources/ucsc.

Field paths in fields.json may contain '*' (e.g. 'liftOver.*' for hub genome
settings whose key carries the target genome); those match record keys by
glob.
"""
import fnmatch
import json

import pytest

from refmeta.formats import ucsc

FORMATS = {f.id: f for f in ucsc.FORMATS}


@pytest.fixture
def ucsc_dir(sources_dir):
    return sources_dir / "ucsc"


@pytest.fixture
def inventory(ucsc_dir):
    return json.loads((ucsc_dir / "fields.json").read_text())


def _paths(inventory, fmt_id):
    return [f["path"] for f in inventory["fields"] if f["format"] == fmt_id]


def _known(key, paths):
    return any(fnmatch.fnmatchcase(key, p) if "*" in p else key == p for p in paths)


def _adapter_formats(inventory):
    return [f for f in inventory["formats"] if f["adapter"]]


def test_inventory_matches_adapter(inventory):
    assert inventory["source"] == "ucsc"
    declared = {f["id"] for f in _adapter_formats(inventory)}
    assert declared == set(FORMATS)
    for fmt in FORMATS.values():
        assert fmt.source == "ucsc" and fmt.detect is not None


def test_spec_and_example_files_exist(inventory, ucsc_dir):
    for f in inventory["formats"]:
        assert f["example_files"], f["id"]
        for rel in f["spec_files"] + f["example_files"]:
            assert (ucsc_dir / rel).is_file(), rel


def test_read_examples_keys_in_inventory(inventory, ucsc_dir):
    for f in _adapter_formats(inventory):
        fmt, paths = FORMATS[f["id"]], _paths(inventory, f["id"])
        for rel in f["example_files"]:
            records = fmt.read((ucsc_dir / rel).read_text())
            assert records, f"{f['id']}: no records from {rel}"
            for rec in records:
                json.dumps(rec)
                unknown = [k for k in rec if not _known(k, paths)]
                assert not unknown, f"{f['id']} {rel}: keys not in fields.json: {unknown}"


def test_write_then_read_roundtrip(inventory, ucsc_dir):
    for f in _adapter_formats(inventory):
        fmt = FORMATS[f["id"]]
        if fmt.write is None:
            continue
        for rel in f["example_files"]:
            records = fmt.read((ucsc_dir / rel).read_text())
            again = fmt.read(fmt.write(records))
            assert again == records, f"{f['id']} {rel}: round trip changed records"


def test_examples_in_inventory_are_real(inventory, ucsc_dir):
    """Every fields.json example value occurs in that format's example records."""
    seen = {}
    for f in _adapter_formats(inventory):
        recs = []
        for rel in f["example_files"]:
            recs += FORMATS[f["id"]].read((ucsc_dir / rel).read_text())
        seen[f["id"]] = recs
    for fd in inventory["fields"]:
        recs = seen[fd["format"]]
        hit = any(
            v == fd["example"]
            for r in recs
            for k, v in r.items()
            if _known(k, [fd["path"]])
        )
        assert hit, f"{fd['format']} {fd['path']}: example {fd['example']!r} not found"


def test_detect_picks_the_right_format(inventory, ucsc_dir):
    for f in _adapter_formats(inventory):
        for rel in f["example_files"]:
            text = (ucsc_dir / rel).read_text()
            name = rel.rsplit("/", 1)[-1]
            scores = {fid: fmt.detect(text, name) for fid, fmt in FORMATS.items()}
            best = max(scores, key=scores.get)
            if f["id"] == "ucsc_hub_txt" and best == "ucsc_genomes_txt":
                # a useOneFile hub.txt holds both stanzas; the genome reader wins
                assert scores["ucsc_hub_txt"] >= 0.5, rel
                continue
            assert best == f["id"], f"{rel}: detected {best} {scores[best]} over {f['id']} {scores[f['id']]}"
            assert scores[best] >= 0.5


def test_anchor_values(ucsc_dir):
    ex = ucsc_dir / "examples"
    dbdb = {r["name"]: r for r in FORMATS["ucsc_dbdb"].read((ex / "api_list_ucscGenomes_hg38_sacCer3.json").read_text())}
    assert dbdb["hg38"]["taxId"] == 9606 and "GCA_000001405.15" in dbdb["hg38"]["sourceName"]
    assert dbdb["sacCer3"]["taxId"] == 559292

    alias = FORMATS["ucsc_chromalias_txt"].read((ex / "bigZips_sacCer3.chromAlias.txt").read_text())
    chr_m = next(r for r in alias if r["ucsc"] == "chrM")
    assert chr_m == {"ucsc": "chrM", "ensembl": "Mito", "genbank": "AJ011856.1", "refseq": "NC_001224.1"}

    genark = FORMATS["ucsc_chromalias_txt"].read((ex / "genark_GCF_000146045.2.chromAlias.txt").read_text())
    mt = next(r for r in genark if r["ucsc"] == "chrM")
    assert mt["refseq"] == "NC_001224.1" and mt["genbank"] is None
    assert list(genark[0])[0] == "refseq"  # GenArk's own names come first

    legacy = FORMATS["ucsc_chromalias_txt"].read((ex / "bigZips_hg38.chromAlias.txt").read_text())
    assert legacy[0] == {"sequenceName": "chr1", "alias names": ["1", "CM000663.2", "NC_000001.11"]}

    sizes = FORMATS["ucsc_chrom_sizes"].read((ex / "bigZips_latest_hg38.chrom.sizes").read_text())
    api = FORMATS["ucsc_api_chromosomes"].read((ex / "api_list_chromosomes_hg38.json").read_text())
    assert {(r["chrom"], r["size"]) for r in sizes} == {(r["chrom"], r["size"]) for r in api}

    genomes = FORMATS["ucsc_genomes_txt"].read((ex / "genark_GCF_000146045.2_hub.txt").read_text())
    assert len(genomes) == 1 and genomes[0]["genome"] == "GCF_000146045.2"
    assert genomes[0]["taxId"] == 559292 and genomes[0]["chromAuthority"] == "ucsc"
    hub = FORMATS["ucsc_hub_txt"].read((ex / "genark_GCF_000146045.2_hub.txt").read_text())
    assert [h["hub"] for h in hub] == ["GCF_000146045.2 genome assembly"]


def test_stanza_parser_edge_cases():
    text = "# comment\nhub  myHub \nshortLabel a \\\n  b\nlongLabel L\nemail e@x\ngenomesFile genomes.txt\n\n\ngenome x\norderKey 7\n"
    hubs = FORMATS["ucsc_hub_txt"].read(text)
    assert hubs == [{"hub": "myHub", "shortLabel": "a b", "longLabel": "L", "email": "e@x", "genomesFile": "genomes.txt"}]
    genomes = FORMATS["ucsc_genomes_txt"].read(text)
    assert genomes == [{"genome": "x", "orderKey": 7}]
