"""Tests for the NCBI adapters (refmeta/formats/ncbi.py) against sources/ncbi/."""
import json
import re

import pytest

from refmeta.formats import all_formats

SOURCE = "ncbi"


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


def test_inventory_and_registry_agree(inventory, formats):
    listed = {f["id"] for f in _adapter_formats(inventory)}
    assert listed == set(formats)
    for fld in inventory["fields"]:
        assert fld["format"] in {f["id"] for f in inventory["formats"]}
        assert fld["level"] in {"assembly", "collection", "sequence", "copy", "deployment", "other"}
        assert fld["unique"] in {"global", "namespace", "none", "unknown"}
        assert fld["cardinality"] in {"one", "many"}


def test_read_every_example(sources_dir, inventory, formats):
    for spec in _adapter_formats(inventory):
        fmt = formats[spec["id"]]
        allowed = _paths(inventory, spec["id"])
        assert spec["example_files"], spec["id"]
        for rel in spec["example_files"]:
            text = (sources_dir / SOURCE / rel).read_text()
            records = fmt.read(text)
            assert records, f"{spec['id']} read nothing from {rel}"
            for rec in records:
                json.dumps(rec)  # values must be JSON-serializable
                missing = set(rec) - allowed
                assert not missing, f"{rel}: keys not in fields.json for {spec['id']}: {sorted(missing)}"


def test_write_then_read_round_trips(sources_dir, inventory, formats):
    for spec in _adapter_formats(inventory):
        fmt = formats[spec["id"]]
        if fmt.write is None:
            continue
        for rel in spec["example_files"]:
            records = fmt.read((sources_dir / SOURCE / rel).read_text())
            assert fmt.read(fmt.write(records)) == records, f"{spec['id']} round trip failed for {rel}"


def test_detect_prefers_own_format(sources_dir, inventory, formats):
    owners: dict[str, set] = {}
    for spec in _adapter_formats(inventory):
        for rel in spec["example_files"]:
            owners.setdefault(rel, set()).add(spec["id"])
    for rel, own in owners.items():
        text = (sources_dir / SOURCE / rel).read_text()
        name = rel.rsplit("/", 1)[-1]
        scores = {fid: f.detect(text, name) for fid, f in formats.items()}
        best_own = max(scores[fid] for fid in own)
        assert best_own >= 0.5, (rel, scores)
        assert all(s <= best_own for fid, s in scores.items() if fid not in own), (rel, scores)


def _camel(key):
    return re.sub(r"_([a-z0-9])", lambda m: m.group(1).upper(), key)


def _camel_keys(obj):
    if isinstance(obj, dict):
        return {_camel(k): _camel_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_camel_keys(v) for v in obj]
    return obj


@pytest.mark.parametrize(
    "fid,rel",
    [
        ("ncbi_datasets_assembly_report", "examples/datasets_dataset_report_GCF_009914755.1.json"),
        ("ncbi_datasets_sequence_report", "examples/datasets_sequence_report_GCF_000146045.2.json"),
    ],
)
def test_package_jsonl_camelcase_reads_like_api_json(sources_dir, formats, fid, rel):
    """Data packages hold camelCase JSON Lines; the REST API serves snake_case JSON."""
    text = (sources_dir / SOURCE / rel).read_text()
    reports = json.loads(text)["reports"]
    jsonl = "\n".join(json.dumps(_camel_keys(r)) for r in reports) + "\n"
    assert formats[fid].read(jsonl) == formats[fid].read(text)


def test_anchor_facts(sources_dir, formats):
    ex = sources_dir / SOURCE / "examples"
    seq = formats["ncbi_assembly_report_sequences"]
    rows40 = seq.read((ex / "ftp_GCF_000001405.40_GRCh38.p14_assembly_report.txt").read_text())
    api40 = formats["ncbi_datasets_sequence_report"].read(
        (ex / "datasets_sequence_report_GCF_000001405.40.json").read_text()
    )
    # The FTP report keeps the 4 GenBank-only scaffolds (RefSeq-Accn "na"); Datasets drops them.
    assert len(rows40) == 709 and len(api40) == 705
    assert sum(r["RefSeq-Accn"] == "na" for r in rows40) == 4
    chr1 = rows40[0]
    assert chr1["UCSC-style-name"] == "chr1" and chr1["RefSeq-Accn"] == "NC_000001.11"
    assert chr1["Sequence-Length"] == 248956422

    head = formats["ncbi_assembly_report_header"].read(
        (ex / "ftp_GCA_000001405.15_GRCh38_assembly_report.txt").read_text()
    )[0]
    assert head["RefSeq assembly accession"] == "GCF_000001405.26"  # not .40

    rep = formats["ncbi_datasets_assembly_report"].read(
        (ex / "datasets_dataset_report_GCF_000001405.40.json").read_text()
    )[0]
    assert rep["paired_accession"] == "GCA_000001405.29"
    assert rep["assembly_info.synonym"] == "hg38"

    deflines = formats["ncbi_analysis_set_defline"].read(
        (ex / "ftp_GCA_000001405.15_GRCh38_full_analysis_set.deflines.txt").read_text()
    )
    chrm = next(r for r in deflines if r["name"] == "chrM")
    assert chrm["AC"] == "J01415.2" and chrm["LN"] == 16569 and chrm["tp"] == "circular"

    summary = formats["ncbi_assembly_summary"].read((ex / "ftp_assembly_summary_refseq.anchors.txt").read_text())
    yeast = next(r for r in summary if r["assembly_accession"] == "GCF_000146045.2")
    assert yeast["taxid"] == 559292 and yeast["species_taxid"] == 4932 and yeast["gc_percent"] == 38.5


def test_empty_api_answer_reads_as_no_records(formats):
    # The API returns {} for an accession filtered out by default (e.g. GCA_000001405.15)
    assert formats["ncbi_datasets_assembly_report"].read("{}") == []
