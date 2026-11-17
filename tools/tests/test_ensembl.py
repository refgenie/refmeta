import json

import pytest

from refmeta.formats import ensembl

FORMATS = {f.id: f for f in ensembl.FORMATS}


@pytest.fixture
def inventory(sources_dir):
    return json.loads((sources_dir / "ensembl" / "fields.json").read_text())


def _adapter_formats(inventory):
    return [f for f in inventory["formats"] if f["adapter"]]


def test_every_adapter_format_is_registered(inventory):
    documented = {f["id"] for f in _adapter_formats(inventory)}
    assert documented == set(FORMATS)
    for fmt in FORMATS.values():
        assert fmt.source == "ensembl"


def test_examples_read_and_keys_documented(inventory, sources_dir):
    src = sources_dir / "ensembl"
    paths_by_format = {}
    for fld in inventory["fields"]:
        paths_by_format.setdefault(fld["format"], set()).add(fld["path"])
    for f in _adapter_formats(inventory):
        fmt = FORMATS[f["id"]]
        assert f["example_files"], f["id"]
        for ef in f["example_files"]:
            text = (src / ef).read_text()
            records = fmt.read(text)
            assert records, f"{f['id']} read nothing from {ef}"
            for rec in records:
                json.dumps(rec)  # JSON-serializable
                extra = set(rec) - paths_by_format[f["id"]]
                assert not extra, f"{f['id']} {ef}: undocumented keys {sorted(extra)}"


def test_detect_prefers_own_format(inventory, sources_dir):
    src = sources_dir / "ensembl"
    for f in _adapter_formats(inventory):
        for ef in f["example_files"]:
            text = (src / ef).read_text()
            name = ef.rsplit("/", 1)[-1]
            own = FORMATS[f["id"]].detect(text, name)
            assert own > 0, f"{f['id']} does not detect {ef}"
            if f["id"] == "ensembl_rest_toplevel_region":
                continue  # shares its file with ensembl_rest_info_assembly, which wins
            best = max(fmt.detect(text, name) for fmt in FORMATS.values())
            assert own == best, f"{ef}: another format scores higher than {f['id']}"


def test_write_then_read_roundtrip(inventory, sources_dir):
    src = sources_dir / "ensembl"
    for f in _adapter_formats(inventory):
        fmt = FORMATS[f["id"]]
        if fmt.write is None:
            continue
        for ef in f["example_files"]:
            records = fmt.read((src / ef).read_text())
            again = fmt.read(fmt.write(records))
            assert again == records, f"{f['id']} roundtrip changed records from {ef}"


def test_fasta_header_parsing():
    fmt = FORMATS["ensembl_fasta_header"]
    legacy, alt, new = fmt.read(
        ">1 dna:chromosome chromosome:GRCh38:1:1:248956422:1 REF\nACGT\n"
        ">HG76_PATCH dna:scaffold scaffold:GRCh38:HG76_PATCH:1:6367528:1 \n"
        ">IV unmasked:chromosome R64-1-1:IV:1:1531933:1\n"
    )
    assert legacy["slice.coord_system_name"] == "chromosome"
    assert legacy["slice.end"] == 248956422 and legacy["assembly_exception_type"] == "REF"
    assert alt["assembly_exception_type"] == ""
    assert "slice.coord_system_name" not in new and "assembly_exception_type" not in new
    assert new["slice.version"] == "R64-1-1" and new["sequence_type"] == "unmasked"


def test_core_meta_multi_values_and_db_level_rows():
    fmt = FORMATS["ensembl_core_meta"]
    text = (
        "1\t\\N\tschema_type\tcore\n"
        "2\t\\N\tpatch\tpatch_1.sql|x\n"
        "3\t1\tspecies.alias\thuman\n"
        "4\t1\tassembly.default\tGRCh38\n"
        "5\t1\tsample.vep_id\ta\\\\nb\n"
    )
    [rec] = fmt.read(text)
    assert rec["schema_type"] == "core" and rec["patch"] == ["patch_1.sql|x"]
    assert rec["species.alias"] == ["human"] and rec["assembly.default"] == "GRCh38"
    assert rec["sample.vep_id"] == "a\\nb"
    out = fmt.write([rec])
    assert "\t\\N\tschema_type\tcore" in out and "\t1\tassembly.default\tGRCh38" in out
