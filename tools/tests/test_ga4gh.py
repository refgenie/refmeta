"""Tests for the GA4GH adapters (refmeta/formats/ga4gh.py) against sources/ga4gh/."""
import json
from pathlib import Path

import pytest

from refmeta.formats import all_formats, ga4gh

FORMATS = {f.id: f for f in ga4gh.FORMATS}


def _inventory(sources_dir: Path) -> dict:
    return json.loads((sources_dir / "ga4gh" / "fields.json").read_text(encoding="utf-8"))


def _paths(inv: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for f in inv["fields"]:
        out.setdefault(f["format"], set()).add(f["path"])
    return out


def _cases(sources_dir: Path):
    for fmt in _inventory(sources_dir)["formats"]:
        if fmt["adapter"]:
            for rel in fmt["example_files"]:
                yield fmt["id"], rel


def _text(sources_dir: Path, rel: str) -> str:
    return (sources_dir / "ga4gh" / rel).read_text(encoding="utf-8")


def test_inventory_shape(sources_dir):
    inv = _inventory(sources_dir)
    assert inv["source"] == "ga4gh"
    fmt_ids = {f["id"] for f in inv["formats"]}
    for f in inv["fields"]:
        assert f["format"] in fmt_ids
        assert f["level"] in {"assembly", "collection", "sequence", "copy", "deployment", "other"}
        assert f["cardinality"] in {"one", "many"}
        assert f["unique"] in {"global", "namespace", "none", "unknown"}
    for fmt in inv["formats"]:
        for rel in fmt["spec_files"] + fmt["example_files"]:
            assert (sources_dir / "ga4gh" / rel).is_file(), rel


def test_every_adapter_format_is_registered(sources_dir):
    declared = {f["id"] for f in _inventory(sources_dir)["formats"] if f["adapter"]}
    assert declared == set(FORMATS)
    registry = all_formats()
    for fid in declared:
        assert registry[fid].source == "ga4gh"


def test_examples_read_and_keys_are_inventoried(sources_dir):
    paths = _paths(_inventory(sources_dir))
    cases = list(_cases(sources_dir))
    assert cases
    for fid, rel in cases:
        records = FORMATS[fid].read(_text(sources_dir, rel))
        assert records, rel
        json.dumps(records)  # JSON-serializable
        for rec in records:
            unknown = set(rec) - paths[fid]
            assert not unknown, f"{rel}: keys missing from fields.json: {sorted(unknown)}"


def test_write_then_read_round_trips(sources_dir):
    for fid, rel in _cases(sources_dir):
        fmt = FORMATS[fid]
        if fmt.write is None:
            continue
        records = fmt.read(_text(sources_dir, rel))
        assert fmt.read(fmt.write(records)) == records, rel


def test_detect_prefers_own_examples(sources_dir):
    owners: dict[str, set[str]] = {}
    for fid, rel in _cases(sources_dir):
        owners.setdefault(rel, set()).add(fid)
    for rel, fids in owners.items():
        text = _text(sources_dir, rel)
        name = Path(rel).name
        scores = {fid: fmt.detect(text, name) for fid, fmt in FORMATS.items()}
        for fid in fids:
            assert scores[fid] > 0, (fid, rel)
        best = max(scores, key=scores.get)
        assert best in fids and scores[best] >= 0.5, (rel, scores)


def test_detect_rejects_other_text():
    for fmt in FORMATS.values():
        assert fmt.detect("", "x.txt") == 0.0
        assert fmt.detect(">chr1\nACGT\n", "x.fa") == 0.0
        assert fmt.detect('{"foo": 1}', "x.json") == 0.0


@pytest.mark.parametrize(
    "stem, digest",
    [
        ("hg38_EiFob05aCWgVU_B_Ae0cypnQut3cxUP1", "EiFob05aCWgVU_B_Ae0cypnQut3cxUP1"),
        ("R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu", "ia9g4Myony-xxLsSc7eQOC_NdClGgPGu"),
    ],
)
def test_seqcol_digests_match_server(sources_dir, stem, digest):
    l2 = FORMATS["ga4gh_seqcol_level2"].read(_text(sources_dir, f"examples/seqcol_level2_{stem}.json"))[0]
    l1 = FORMATS["ga4gh_seqcol_level1"].read(_text(sources_dir, f"examples/seqcol_level1_{stem}.json"))[0]
    assert ga4gh.level0_digest(l2) == digest
    assert ga4gh.level0_digest(l1) == digest
    computed = ga4gh.level1_digests(l2)
    for key, value in l1.items():
        assert computed[key] == value, key


def test_specific_values(sources_dir):
    sq = FORMATS["ga4gh_sam_header_sq"].read(_text(sources_dir, "examples/sam_dict_igenomes_R64-1-1_genome.dict"))
    assert [r["SN"] for r in sq][:3] == ["I", "II", "III"] and sq[0]["LN"] == 230218
    eva = "examples/vcf_header_eva_release9_R64_GCA_000146045.2.vcf"
    ref = FORMATS["ga4gh_vcf_header_reference"].read(_text(sources_dir, eva))[0]
    assert ref["reference.accession"] == "GCA_000146045.2"
    contigs = FORMATS["ga4gh_vcf_header_contig"].read(_text(sources_dir, eva))
    assert {"ID": "I", "accession": "BK006935.2"} in contigs
    spec = FORMATS["ga4gh_vcf_header_contig"].read(_text(sources_dir, "examples/vcf_header_spec_example_VCFv4.5.vcf"))
    assert spec[0]["species"] == "Homo sapiens" and spec[0]["length"] == 62435964
    vrs = FORMATS["ga4gh_vrs_sequence_reference"].read(
        _text(sources_dir, "examples/vrs_normalizer_response_NC_000001.11_g.11796321G_A.json"))
    assert vrs == [{"type": "SequenceReference", "refgetAccession": "SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"}]
    md = FORMATS["ga4gh_refget_metadata"].read(_text(sources_dir, "examples/refget_metadata_spec_example_chr1.json"))[0]
    assert md["metadata.aliases[].naming_authority"] == ["insdc", "ucsc"]
