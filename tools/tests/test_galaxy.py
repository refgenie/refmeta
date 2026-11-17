"""Tests for the Galaxy adapters (refmeta/formats/galaxy.py) against sources/galaxy/."""
import json

import pytest

from refmeta.formats import all_formats

SOURCE = "galaxy"


@pytest.fixture
def inventory(sources_dir):
    return json.loads((sources_dir / SOURCE / "fields.json").read_text())


@pytest.fixture
def formats():
    return {fid: f for fid, f in all_formats().items() if f.source == SOURCE}


def _adapter_formats(inventory):
    return [f for f in inventory["formats"] if f.get("adapter")]


def _paths(inventory, fid):
    return {fld["path"] for fld in inventory["fields"] if fld["format"] == fid}


def _read(sources_dir, rel):
    return (sources_dir / SOURCE / rel).read_text()


def test_inventory_and_registry_agree(sources_dir, inventory, formats):
    assert inventory["source"] == SOURCE
    listed = {f["id"] for f in _adapter_formats(inventory)}
    assert listed == set(formats)
    ids = {f["id"] for f in inventory["formats"]}
    for fld in inventory["fields"]:
        assert fld["format"] in ids
        assert fld["level"] in {"assembly", "collection", "sequence", "copy", "deployment", "other"}
        assert fld["unique"] in {"global", "namespace", "none", "unknown"}
        assert fld["cardinality"] in {"one", "many"}
        assert fld["type"] in {"string", "integer", "number", "boolean", "array", "object", "date", "uri"}
    for spec in inventory["formats"]:
        for rel in spec["spec_files"] + spec["example_files"]:
            assert (sources_dir / SOURCE / rel).is_file(), rel


def test_read_every_example(sources_dir, inventory, formats):
    for spec in _adapter_formats(inventory):
        fmt = formats[spec["id"]]
        allowed = _paths(inventory, spec["id"])
        assert spec["example_files"], spec["id"]
        for rel in spec["example_files"]:
            records = fmt.read(_read(sources_dir, rel))
            assert records, f"{spec['id']} read nothing from {rel}"
            for rec in records:
                json.dumps(rec)  # values must be JSON-serializable
                extra = set(rec) - allowed
                assert not extra, f"{rel}: keys not in fields.json for {spec['id']}: {sorted(extra)}"


def test_examples_in_fields_json_are_real(sources_dir, inventory, formats):
    """Each non-null example value occurs in some example (or spec) file of its format."""
    by_id = {f["id"]: f for f in inventory["formats"]}
    for fld in inventory["fields"]:
        spec = by_id[fld["format"]]
        if not spec["adapter"] or fld["example"] is None:
            continue
        fmt = formats[fld["format"]]
        seen = []
        for rel in spec["example_files"] + spec["spec_files"]:
            text = _read(sources_dir, rel)
            if fmt.detect(text, rel) < 0.5:
                continue
            seen += [r.get(fld["path"]) for r in fmt.read(text)]
        assert fld["example"] in seen, (fld["format"], fld["path"])


def test_write_then_read_round_trips(sources_dir, inventory, formats):
    for spec in _adapter_formats(inventory):
        fmt = formats[spec["id"]]
        if fmt.write is None:
            continue
        for rel in spec["example_files"]:
            records = fmt.read(_read(sources_dir, rel))
            assert fmt.read(fmt.write(records)) == records, f"{spec['id']} round trip failed for {rel}"


def test_detect_prefers_own_format(sources_dir, inventory, formats):
    owners: dict[str, set] = {}
    for spec in _adapter_formats(inventory):
        for rel in spec["example_files"]:
            owners.setdefault(rel, set()).add(spec["id"])
    for rel, own in owners.items():
        text = _read(sources_dir, rel)
        name = rel.rsplit("/", 1)[-1]
        scores = {fid: f.detect(text, name) for fid, f in formats.items()}
        best_own = max(scores[fid] for fid in own)
        assert best_own >= 0.5, (rel, scores)
        assert all(s < best_own for fid, s in scores.items() if fid not in own), (rel, scores)


def test_loc_parsing_follows_galaxy_rules(formats):
    fmt = formats["galaxy_loc_all_fasta"]
    text = (
        "#<value>\t<dbkey>\t<name>\t<path>\n"
        "  # indented comment\n"
        "\n"
        "hg38canon\thg38\tHuman (Homo sapiens) (b38): hg38 Canonical\t/x/hg38canon.fa\textra\n"
        "short\trow\n"
    )
    recs = fmt.read(text)
    # comments skipped, extra fields ignored, rows with too few fields dropped
    assert recs == [{"value": "hg38canon", "dbkey": "hg38",
                     "name": "Human (Homo sapiens) (b38): hg38 Canonical", "path": "/x/hg38canon.fa"}]


def test_loc_detect_uses_file_name(formats):
    row = "hg38canon\thg38\tHuman\t/x/hg38canon.fa\n"
    assert formats["galaxy_loc_all_fasta"].detect(row, "all_fasta_dbkeys.loc") > formats["galaxy_loc_dbkeys"].detect(row, "all_fasta_dbkeys.loc")
    assert formats["galaxy_loc_bwa_mem_indexes"].detect(row, "bwa_mem_index.loc") >= 0.9
    assert formats["galaxy_loc_all_fasta"].detect(row, "bwa_mem_index.loc") < 0.5


def test_one_dbkey_many_builds(sources_dir, formats):
    """The key quirk: dbkey hg38 covers several unique_build_ids (value)."""
    recs = formats["galaxy_loc_all_fasta"].read(_read(sources_dir, "examples/cvmfs_all_fasta.loc"))
    hg38 = [r["value"] for r in recs if r["dbkey"] == "hg38"]
    assert sorted(hg38) == ["hg38", "hg38canon", "hg38female"]


def test_refget_json_and_yaml_agree(sources_dir, formats):
    j = formats["galaxy_idc_refget_json"].read(_read(sources_dir, "examples/constructed/idc_pr88_json_hg38canon.json"))[0]
    y = {r["unique_build_id"]: r for r in formats["galaxy_idc_refget_yaml"].read(
        _read(sources_dir, "examples/constructed/idc_pr88_yaml_all_fasta.yml"))}["hg38canon"]
    assert j["level_0"] == y["level_0"]
    assert y["level_2_peek.sequence_count"] == len(j["level_2.names"]) == 25
    assert j["aliases.galaxy_dbkey"] == "hg38"


def test_request_flattening(sources_dir, formats):
    fmt = formats["galaxy_idc_request"]
    rec = fmt.read(_read(sources_dir, "examples/idc_request_all_fasta_hg38canon.yaml"))[0]
    assert rec["params.dbkey_source.dbkey"] == "hg38"
    assert rec["params.sequence_id"] == "hg38canon"
    assert rec["sha256"] == {"hg38canon.fa": "87b0ea46eefe6158fcdb7343980c5c9ea31f681c99a9c96bf2f6cbc64b86b335"}
    assert len(rec["params.sorting.sequence_identifiers"]) == 25
