import json

import pytest

from refmeta.formats import all_formats

SOURCE = "bioconductor"


def _inventory(sources_dir):
    return json.loads((sources_dir / SOURCE / "fields.json").read_text())


def _adapter_formats(sources_dir):
    inv = _inventory(sources_dir)
    return [f for f in inv["formats"] if f.get("adapter")]


def _cases(sources_dir):
    for f in _adapter_formats(sources_dir):
        for ex in f["example_files"]:
            yield f["id"], ex


def test_formats_registered(sources_dir):
    registered = all_formats()
    for f in _adapter_formats(sources_dir):
        assert f["id"] in registered, f"{f['id']} listed in fields.json but has no adapter"
        assert registered[f["id"]].source == SOURCE
    ours = {k for k, v in registered.items() if v.source == SOURCE}
    listed = {f["id"] for f in _adapter_formats(sources_dir)}
    assert ours == listed


def test_every_format_has_examples_and_fields(sources_dir):
    inv = _inventory(sources_dir)
    paths_by_format = {}
    for fld in inv["fields"]:
        paths_by_format.setdefault(fld["format"], set()).add(fld["path"])
    for f in inv["formats"]:
        assert f["example_files"], f["id"]
        assert paths_by_format.get(f["id"]), f"no fields for {f['id']}"
        for p in f["example_files"] + f["spec_files"]:
            assert (sources_dir / SOURCE / p).exists(), p


def test_read_examples_keys_in_inventory(sources_dir):
    inv = _inventory(sources_dir)
    fmts = all_formats()
    paths_by_format = {}
    for fld in inv["fields"]:
        paths_by_format.setdefault(fld["format"], set()).add(fld["path"])
    for fid, ex in _cases(sources_dir):
        text = (sources_dir / SOURCE / ex).read_text()
        records = fmts[fid].read(text)
        assert records, f"{ex}: no records"
        for rec in records:
            json.dumps(rec)  # JSON-serializable
            extra = set(rec) - paths_by_format[fid]
            assert not extra, f"{ex}: keys not in fields.json for {fid}: {sorted(extra)}"


def test_detect_picks_own_format(sources_dir):
    fmts = all_formats()
    ours = {k: v for k, v in fmts.items() if v.source == SOURCE}
    for fid, ex in _cases(sources_dir):
        text = (sources_dir / SOURCE / ex).read_text()
        name = ex.rsplit("/", 1)[-1]
        scores = {k: v.detect(text, name) for k, v in ours.items() if v.detect}
        best = max(scores, key=scores.get)
        assert best == fid, f"{ex}: detected {best} ({scores[best]}) not {fid} ({scores[fid]})"
        assert 0.0 <= scores[fid] <= 1.0


def test_write_read_roundtrip(sources_dir):
    fmts = all_formats()
    for fid, ex in _cases(sources_dir):
        fmt = fmts[fid]
        if fmt.write is None:
            continue
        records = fmt.read((sources_dir / SOURCE / ex).read_text())
        again = fmt.read(fmt.write(records))
        assert again == records, f"{ex}: write/read changed records"


def test_anchor_values(sources_dir):
    fmts = all_formats()
    ex = sources_dir / SOURCE / "examples"
    ncbi = fmts["bioconductor_registered_ncbi"].read((ex / "registered_ncbi_Homo_sapiens.R").read_text())
    p14 = [r for r in ncbi if r["assembly"] == "GRCh38.p14"][0]
    assert p14["assembly_accession"] == "GCF_000001405.40"
    assert p14["circ_seqs"] == ["MT"]
    yeast = fmts["bioconductor_registered_ncbi"].read(
        (ex / "registered_ncbi_Saccharomyces_cerevisiae.R").read_text())
    r64 = [r for r in yeast if r["assembly"] == "R64"][0]
    assert r64["extra_info"] == {"strain": "S288C"}
    assert r64["NCBI2Ensembl_special_mappings"] == {"MT": "Mito"}
    ucsc = fmts["bioconductor_registered_ucsc"].read((ex / "registered_ucsc_sacCer3.R").read_text())[0]
    assert ucsc["ASSEMBLED_MOLECULES"][0] == "chrI" and ucsc["ASSEMBLED_MOLECULES"][-1] == "chrM"
    assert len(ucsc["ASSEMBLED_MOLECULES"]) == 17
    assert ucsc["NCBI_LINKER.special_mappings"] == {"chrM": "MT"}
    hg38 = fmts["bioconductor_registered_ucsc"].read((ex / "registered_ucsc_hg38.R").read_text())[0]
    assert hg38["ASSEMBLED_MOLECULES"][-1] == "chrM" and len(hg38["ASSEMBLED_MOLECULES"]) == 25
    assert hg38["FETCH_ORDERED_CHROM_SIZES"].startswith("function(")
    ah = fmts["bioconductor_annotationhub_record"].read((ex / "annotationhub_AH49186.json").read_text())[0]
    assert len(ah["rdatapaths[].rdatapath"]) == 2
    seed = fmts["bioconductor_bsgenome_description"].read(
        (ex / "bsgenome_DESCRIPTION_BSgenome.Hsapiens.UCSC.hg38_1.4.5").read_text())[0]
    assert seed["source_url"] == "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/p14/"


def test_seqinfo_show_text():
    fmt = all_formats()["bioconductor_seqinfo"]
    text = (
        "Seqinfo object with 2 sequences (1 circular) from sacCer3 genome:\n"
        "  seqnames seqlengths isCircular  genome\n"
        "  chrI         230218      FALSE sacCer3\n"
        "  chrM          85779       TRUE sacCer3\n"
    )
    assert fmt.detect(text, "x.txt") > 0.9
    assert fmt.read(text) == [
        {"seqnames": "chrI", "seqlengths": 230218, "isCircular": False, "genome": "sacCer3"},
        {"seqnames": "chrM", "seqlengths": 85779, "isCircular": True, "genome": "sacCer3"},
    ]


def test_r_reader_does_not_execute_code():
    fmt = all_formats()["bioconductor_registered_ucsc"]
    text = (
        'GENOME <- "x1"\nORGANISM <- "X y"\n'
        'ASSEMBLED_MOLECULES <- paste0("chr", c(1:2, "M"))\nCIRC_SEQS <- system("echo hi")\n'
    )
    rec = fmt.read(text)[0]
    assert rec["ASSEMBLED_MOLECULES"] == ["chr1", "chr2", "chrM"]
    # unsupported calls are kept as raw text, never evaluated
    assert rec["CIRC_SEQS"] == ['system("echo hi")']


@pytest.mark.parametrize("fid", ["bioconductor_bsgenome_seed", "bioconductor_bsgenome_description"])
def test_dcf_continuation(fid):
    fmt = all_formats()[fid]
    text = "Package: BSgenome.X.Y.z1\nTitle: a\n        b\nsource_url:\n        https://e/x/\n"
    rec = fmt.read(text)[0]
    assert rec == {"Package": "BSgenome.X.Y.z1", "Title": "a\nb", "source_url": "https://e/x/"}
    assert fmt.read(fmt.write([rec])) == [rec]
