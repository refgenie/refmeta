import json

import pytest

from refmeta.formats import ena

FORMATS = {f.id: f for f in ena.FORMATS}


@pytest.fixture
def inventory(sources_dir):
    return json.loads((sources_dir / "ena" / "fields.json").read_text())


def _example_cases(inventory):
    for fmt in inventory["formats"]:
        if fmt["adapter"]:
            for path in fmt["example_files"]:
                yield fmt["id"], path


def test_formats_match_inventory(inventory):
    documented = {f["id"] for f in inventory["formats"] if f["adapter"]}
    assert documented == set(FORMATS)
    for f in ena.FORMATS:
        assert f.source == "ena"


def test_every_format_has_examples(inventory):
    for fmt in inventory["formats"]:
        if fmt["adapter"]:
            assert fmt["example_files"], fmt["id"]


def test_examples_read_and_keys_documented(inventory, sources_dir):
    paths_by_format = {}
    for fld in inventory["fields"]:
        paths_by_format.setdefault(fld["format"], set()).add(fld["path"])
    n = 0
    for fid, rel in _example_cases(inventory):
        text = (sources_dir / "ena" / rel).read_text()
        records = FORMATS[fid].read(text)
        assert records, f"{rel}: no records"
        for rec in records:
            json.dumps(rec)  # JSON-serializable
            unknown = set(rec) - paths_by_format[fid]
            assert not unknown, f"{rel}: keys not in fields.json: {sorted(unknown)}"
        n += 1
    assert n >= 15


def test_write_then_read_roundtrip(inventory, sources_dir):
    for fid, rel in _example_cases(inventory):
        fmt = FORMATS[fid]
        if fmt.write is None:
            continue
        records = fmt.read((sources_dir / "ena" / rel).read_text())
        assert fmt.read(fmt.write(records)) == records, rel


def test_detect_prefers_own_format(inventory, sources_dir):
    for fid, rel in _example_cases(inventory):
        text = (sources_dir / "ena" / rel).read_text()
        name = rel.rsplit("/", 1)[-1]
        scores = {f.id: f.detect(text, name) for f in ena.FORMATS}
        assert 0 <= min(scores.values()) and max(scores.values()) <= 1
        best = max(scores, key=scores.get)
        assert best == fid and scores[fid] >= 0.5, (rel, scores)


def test_anchor_facts(sources_dir):
    ex = sources_dir / "ena" / "examples"
    human = ena.read_assembly_xml((ex / "assembly_xml_GCA_000001405.15.xml").read_text())[0]
    assert human["@accession"] == "GCA_000001405.15"
    assert human["NAME"] == "GRCh38"
    assert human["TAXON/TAXON_ID"] == 9606
    assert human["ASSEMBLY_ATTRIBUTES/total-length"] == 3209286105

    yeast_rows = ena.read_sequence_report((ex / "sequence_report_GCA_000146045.2.txt").read_text())
    assert len(yeast_rows) == 16  # the GCA has no mitochondrion
    assert yeast_rows[0]["accession"] == "BK006935.2"

    human_rows = ena.read_sequence_report((ex / "sequence_report_GCA_000001405.15.txt").read_text())
    assert len(human_rows) == 455
    unplaced = [r for r in human_rows if r["sequence-role"] == "unplaced-scaffold"]
    assert unplaced and all("replicon-name" not in r for r in unplaced)

    md5 = {r["sequence_accession"]: r.get("sequence_md5")
           for r in ena.read_portal_sequence((ex / "portal_sequence_GCA_000001405.15.tsv").read_text())}
    refget = ena.read_refget_metadata((ex / "refget_metadata_GCA_000001405.15.jsonl").read_text())
    for r in refget:
        acc = r["metadata.id"].removeprefix("insdc:")
        assert md5[acc] == r["metadata.md5"]
    assert md5["CM000663.2"] == "6aef897c3d6ff0c78aff06ac189178dd"

    portal = ena.read_portal_assembly((ex / "portal_assembly_GCA_000001405.15.tsv").read_text())[0]
    assert portal["assembly_accession"] == "GCA_000001405"  # unversioned chain
    assert portal["assembly_set_accession"] == "GCA_000001405.15"
    # Only chromosome-assigned sequences (25 assembled + 42 unlocalised), not all 455.
    assert len(portal["sequence_accession"]) == 67


def test_chromosome_list_topology_split():
    recs = ena.read_chromosome_list("chr01\t1\tLinear-Chromosome\nchrMi\tMIT\tcircular-chromosome\tMitochondrion\n")
    assert recs[0] == {"OBJECT_NAME": "chr01", "CHROMOSOME_NAME": "1", "TOPOLOGY": "Linear", "CHROMOSOME_TYPE": "Chromosome"}
    assert recs[1]["CHROMOSOME_LOCATION"] == "Mitochondrion"
    assert ena.read_chromosome_list(ena.write_chromosome_list(recs)) == recs
