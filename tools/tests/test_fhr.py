"""Tests for the FHR adapters (refmeta/formats/fhr.py) against sources/fhr/."""
import json

import pytest

from refmeta.formats import all_formats, fhr

FORMATS = {f.id: f for f in fhr.FORMATS}


def _inventory(sources_dir):
    return json.loads((sources_dir / "fhr" / "fields.json").read_text())


def _adapter_cases(sources_dir):
    inv = _inventory(sources_dir)
    for fmt in inv["formats"]:
        if fmt["adapter"]:
            for path in fmt["example_files"]:
                yield fmt["id"], path


def test_every_adapter_format_is_registered(sources_dir):
    inv = _inventory(sources_dir)
    declared = {f["id"] for f in inv["formats"] if f["adapter"]}
    assert declared == set(FORMATS)
    registry = all_formats()
    for fid in declared:
        assert registry[fid].source == "fhr"


def test_examples_read_and_keys_are_inventoried(sources_dir):
    inv = _inventory(sources_dir)
    paths = {}
    for f in inv["fields"]:
        paths.setdefault(f["format"], set()).add(f["path"])
    cases = list(_adapter_cases(sources_dir))
    assert cases
    for fid, rel in cases:
        text = (sources_dir / "fhr" / rel).read_text(encoding="utf-8")
        records = FORMATS[fid].read(text)
        assert len(records) == 1, rel
        json.dumps(records)  # JSON-serializable
        unknown = set(records[0]) - paths[fid]
        assert not unknown, f"{rel}: keys missing from fields.json: {sorted(unknown)}"


def test_write_then_read_round_trips(sources_dir):
    for fid, rel in _adapter_cases(sources_dir):
        fmt = FORMATS[fid]
        if fmt.write is None:
            continue
        records = fmt.read((sources_dir / "fhr" / rel).read_text(encoding="utf-8"))
        assert fmt.read(fmt.write(records)) == records, rel


def test_detect_picks_the_right_format(sources_dir):
    # Compared with the other FHR formats only, so other sources' adapters can't break it.
    for fid, rel in _adapter_cases(sources_dir):
        path = sources_dir / "fhr" / rel
        text = path.read_text(encoding="utf-8")
        mine = FORMATS[fid].detect(text, path.name)
        assert mine >= 0.9, (rel, mine)
        for other in FORMATS.values():
            if other.id != fid:
                assert other.detect(text, path.name) < mine, (rel, other.id)


@pytest.mark.parametrize("name", [
    "upstream_example.fhr.json", "upstream_minimal.fhr.json", "upstream_example.fhr.yaml",
    "upstream_example.fhr.jsonld", "upstream_minimal.fhr.jsonld",
    "upstream_example.microdata.fhr.html",
])
def test_writers_reproduce_official_examples_byte_for_byte(sources_dir, name):
    fid = {"json": "fhr_json", "yaml": "fhr_yaml", "jsonld": "fhr_jsonld",
           "html": "fhr_microdata"}[name.rsplit(".", 1)[1]]
    text = (sources_dir / "fhr" / "examples" / name).read_text(encoding="utf-8")
    assert FORMATS[fid].write(FORMATS[fid].read(text)) == text


def test_sidecar_writer_matches_gtars_output(sources_dir):
    fmt = FORMATS["fhr_refgetstore_sidecar"]
    files = sorted((sources_dir / "fhr" / "examples").glob("sidecar_*.fhr.json"))
    assert len(files) >= 2
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert fmt.write(fmt.read(text)) == text, path.name
        assert fhr.sidecar_digest(path.name) and len(fhr.sidecar_digest(path.name)) == 32


def test_all_upstream_serializations_hold_the_same_record(sources_dir):
    ex = sources_dir / "fhr" / "examples"
    base = FORMATS["fhr_json"].read((ex / "upstream_example.fhr.json").read_text())[0]
    for fid, name in [("fhr_yaml", "upstream_example.fhr.yaml"),
                      ("fhr_jsonld", "upstream_example.fhr.jsonld"),
                      ("fhr_microdata", "upstream_example.microdata.fhr.html"),
                      ("fhr_fasta_header", "upstream_example.fhr.fasta"),
                      ("fhr_gfa_header", "upstream_example.fhr.gfa")]:
        rec = FORMATS[fid].read((ex / name).read_text())[0]
        rec.pop("checksum"), dict(base).pop("checksum")
        assert {k: v for k, v in rec.items()} == {k: v for k, v in base.items() if k != "checksum"}, fid


def test_fasta_and_gfa_checksums_verify(sources_dir):
    ex = sources_dir / "fhr" / "examples"
    for name, prefix, fid in [("upstream_example.fhr.fasta", ";~", "fhr_fasta_header"),
                              ("upstream_example.fhr.gfa", "#~", "fhr_gfa_header"),
                              ("constructed/hg38.fhr.fasta", ";~", "fhr_fasta_header"),
                              ("constructed/R64-1-1.fhr.gfa", "#~", "fhr_gfa_header")]:
        text = (ex / name).read_text(encoding="utf-8")
        assert FORMATS[fid].read(text)[0]["checksum"] == fhr.file_checksum(text, prefix), name


def test_flatten_unflatten_inverse():
    obj = {
        "schema": "https://w3id.org/fair-bioheaders/fhr/v0.6.0",
        "taxon": {"name": "Homo sapiens"},
        "metadataAuthor": [{"name": "A", "uri": "https://orcid.org/0000-0000-0000-0001"}, {"name": "B"}],
        "assemblySoftware": "legacy-assembler",
        "x-a.b": {"nested": [1, 2]},
    }
    flat = fhr.flatten(obj)
    assert flat["metadataAuthor[].uri"] == ["https://orcid.org/0000-0000-0000-0001", None]
    assert flat["x-a.b"] == {"nested": [1, 2]}
    assert fhr.unflatten(flat) == obj


def test_fasta_reader_edge_cases():
    text = (";~schema: 'https://w3id.org/fair-bioheaders/fhr/v0.6.0'\r\n"
            "; ordinary comment\r\n"
            ";~genome: \"a\\x3Eb\"\r\n"
            ";~dateCreated: 2024-01-02\r\n"
            ";~checksum: 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='\r\n"
            ">chr1\r\nACGT\r\n;~genome: ignored after the first record\n")
    rec = fhr.read_fasta(text)[0]
    assert rec["genome"] == "a>b"
    assert rec["dateCreated"] == "2024-01-02"  # dates stay strings (R12)
    assert rec["checksum"].endswith("=")
    out = fhr.write_fasta([rec])
    assert ">" not in out and out.splitlines()[-1].startswith(";~checksum: ")
    assert fhr.read_fasta(out) == [rec]


def test_yaml_writer_quotes_ambiguous_strings():
    rec = {"schemaVersion": "2.1", "version": "1e3", "genome": "yes", "dateCreated": "2022-03-21"}
    out = fhr.write_yaml([rec])
    assert "'1e3'" in out and "'yes'" in out and "'2.1'" in out and "'2022-03-21'" in out
    assert fhr.read_yaml(out) == [rec]


def test_jsonld_and_microdata_leave_out_extension_fields():
    rec = {"genome": "g", "x-refget-assemblySource": "ncbi", "assemblySource": "ncbi",
           "documentation": "https://example.org/doc"}
    ld = json.loads(fhr.write_jsonld([rec]))
    assert "x-refget-assemblySource" not in ld and "assemblySource" not in ld
    assert ld["subjectOf"] == "https://example.org/doc"
    assert fhr.read_jsonld(json.dumps(ld)) == [{"genome": "g", "documentation": "https://example.org/doc"}]
    html_text = fhr.write_microdata([rec])
    assert fhr.read_microdata(html_text) == [{"genome": "g", "documentation": "https://example.org/doc"}]


def test_schemaorg_export_is_detected_but_not_read_as_jsonld(sources_dir):
    text = (sources_dir / "fhr" / "examples" / "upstream_example.fhr.export.jsonld").read_text()
    assert fhr.detect_schemaorg_export(text, "x.jsonld") > 0.5
    assert fhr.detect_jsonld(text, "x.jsonld") < 0.5
    with pytest.raises(ValueError):
        fhr.read_jsonld(text)


def test_single_record_formats_reject_many():
    with pytest.raises(ValueError):
        fhr.write_json([{"genome": "a"}, {"genome": "b"}])
