import json

import pytest

from refmeta.formats import nfcore
from refmeta.formats.nfcore import FORMATS, parse_genomes_map

FMT = {f.id: f for f in FORMATS}


@pytest.fixture
def inventory(sources_dir):
    return json.loads((sources_dir / "nfcore" / "fields.json").read_text())


def _adapter_formats(inventory):
    return [f for f in inventory["formats"] if f["adapter"]]


def test_every_adapter_format_is_registered(inventory):
    ids = {f["id"] for f in _adapter_formats(inventory)}
    assert ids == set(FMT)


def test_examples_read_and_keys_in_inventory(inventory, sources_dir):
    root = sources_dir / "nfcore"
    for f in _adapter_formats(inventory):
        allowed = {x["path"] for x in inventory["fields"] if x["format"] == f["id"]}
        assert f["example_files"], f["id"]
        for ef in f["example_files"]:
            text = (root / ef).read_text()
            recs = FMT[f["id"]].read(text)
            assert recs, ef
            for r in recs:
                json.dumps(r)
                extra = set(r) - allowed
                assert not extra, (ef, extra)


def test_write_then_read_roundtrip(inventory, sources_dir):
    root = sources_dir / "nfcore"
    for f in _adapter_formats(inventory):
        fmt = FMT[f["id"]]
        if fmt.write is None:
            continue
        for ef in f["example_files"]:
            recs = fmt.read((root / ef).read_text())
            assert fmt.read(fmt.write(recs)) == recs, ef


def test_detect_picks_own_format(inventory, sources_dir):
    root = sources_dir / "nfcore"
    for f in _adapter_formats(inventory):
        for ef in f["example_files"]:
            text = (root / ef).read_text()
            name = ef.rsplit("/", 1)[-1]
            scores = {fid: fmt.detect(text, name) for fid, fmt in FMT.items()}
            assert max(scores, key=scores.get) == f["id"], (ef, scores)
            assert scores[f["id"]] >= 0.5, (ef, scores)


def test_inventory_examples_are_real_values(inventory, sources_dir):
    """Every non-null example value in fields.json occurs in some example record."""
    root = sources_dir / "nfcore"
    for f in _adapter_formats(inventory):
        values: dict = {}
        for ef in f["example_files"]:
            for r in FMT[f["id"]].read((root / ef).read_text()):
                for k, v in r.items():
                    values.setdefault(k, []).append(v)
        for fld in inventory["fields"]:
            if fld["format"] != f["id"] or fld["example"] is None:
                continue
            assert fld["example"] in values.get(fld["path"], []), (f["id"], fld["path"])


def test_spec_template_config_parses(sources_dir):
    text = (sources_dir / "nfcore/spec/igenomes_config/nf-core_tools_pipeline-template_igenomes.config").read_text()
    recs = FMT["nfcore_igenomes_config"].read(text)
    keys = {r["genome"] for r in recs}
    assert {"GRCh38", "hg38", "R64-1-1", "sacCer3"} <= keys
    empty = (sources_dir / "nfcore/spec/igenomes_config/nf-core_tools_pipeline-template_igenomes_ignored.config").read_text()
    assert FMT["nfcore_igenomes_config"].read(empty) == []


def test_groovy_parser_details():
    text = """
    // comment with 'quotes' and genomes
    params.genomes = [
        'A.B' : [
            fasta : "${params.igenomes_base}/x//y.fa", // trailing comment
            flag  : true,
            size  : '1.2e7',
            nested : [ "50" : 123, "75" : 456 ],
        ],
    ]
    """
    m = parse_genomes_map(text)
    assert m == {"A.B": {"fasta": "${params.igenomes_base}/x//y.fa", "flag": True, "size": "1.2e7",
                         "nested": {"50": 123, "75": 456}}}
    block = "params { genome = false\n genomes { 'X' { fasta = 's3://b/x.fa' } } }"
    assert parse_genomes_map(block) == {"X": {"fasta": "s3://b/x.fa"}}


def test_manifest_layout_split():
    rec = nfcore.manifest_read(
        "s3://ngi-igenomes/igenomes/Homo_sapiens/NCBI/GRCh38/Sequence/WholeGenomeFasta/genome.fa\n"
    )[0]
    assert (rec["species"], rec["source"], rec["build"], rec["section"], rec["subpath"]) == (
        "Homo_sapiens", "NCBI", "GRCh38", "Sequence", "WholeGenomeFasta/genome.fa")
    flat = nfcore.manifest_read("s3://ngi-igenomes/igenomes/Homo_sapiens/GATK/hg38/dbsnp_146.hg38.vcf.gz\n")[0]
    assert flat["section"] is None and flat["subpath"] == "dbsnp_146.hg38.vcf.gz"
