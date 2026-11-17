"""Tests for the conversion engine (refmeta/convert.py), the CLI and the validator.

Facts the sources disagree on are not failures: they are reported as
SourceDisagreement warnings, which pytest prints in its warnings summary.
Round-trip changes that a crosswalk causes by design are reported the same way
(RoundTripNote), listed in KNOWN_ROUND_TRIP_CHANGES with the reason.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import warnings
from collections import defaultdict
from contextlib import redirect_stderr, redirect_stdout
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from refmeta import cli
from refmeta import convert as C
from refmeta.validate import validate, validate_core

TOOLS = Path(__file__).resolve().parents[1]
TASK = TOOLS.parent
SOURCES = TASK / "sources"


class SourceDisagreement(UserWarning):
    """Two sources state different values for the same fact."""


class RoundTripNote(UserWarning):
    """native -> core -> native changed or added a value, for a known reason."""


# (format, native field) -> why a lossless-marked field still changes on a round trip
KNOWN_ROUND_TRIP_CHANGES = {
    ("ncbi_assembly_summary", "isolate"): (
        "isolate and infraspecific_name both map to assembly.taxon.strain; on write the strain "
        "from 'strain=S288C' also fills isolate, which was 'na'"),
    ("refgenie_registry_genome", "fasta.sources[].provider"): (
        "copies[kind=fasta].provider uses keyed set semantics (section 4.1), so two equal "
        "providers for two sources ([NCBI, NCBI]) become one"),
}


# ---------------------------------------------------------------- example files

def _owned() -> list[tuple[str, str, str]]:
    """(format id, source, example path relative to the source) for every crosswalk format."""
    info = C.format_info()
    return [(fid, info[fid]["source"], rel) for fid in C.crosswalk_ids()
            for rel in info[fid]["example_files"]]


OWNED = [x for x in _owned() if (SOURCES / x[1] / x[2]).is_file()]
OWNED_PATHS = {SOURCES / src / rel for _, src, rel in OWNED}
UNOWNED = sorted(p for p in SOURCES.glob("*/examples/**/*") if p.is_file() and p not in OWNED_PATHS)


def _id(x) -> str:
    return f"{x[0]}:{Path(x[2]).name}"


@lru_cache(maxsize=None)
def _text(src: str, rel: str) -> str:
    return (SOURCES / src / rel).read_text(encoding="utf-8", errors="replace")


@lru_cache(maxsize=None)
def _converted(fid: str, src: str, rel: str):
    """(native records, core records, warnings) for one example file."""
    native = C.read_native(_text(src, rel), fid)
    w: list = []
    cores = C.to_core(fid, native, filename=rel, warnings=w)
    return native, cores, w


# ---------------------------------------------------------------- data and crosswalks

def test_package_data_matches_mapping():
    spec = importlib.util.spec_from_file_location("sync_data", TOOLS / "sync_data.py")
    sync = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync)
    write, delete = sync.stale(sync.planned())
    assert not write and not delete, (
        f"refmeta/data is out of date ({len(write)} changed, {len(delete)} extra): run python sync_data.py")


def test_every_adapter_format_has_a_crosswalk():
    adapters = set(C.formats())
    assert adapters == set(C.crosswalk_ids())


def test_crosswalks_compile_and_cover_fields():
    problems = []
    for fid in C.crosswalk_ids():
        cw = C.load_crosswalk(fid)  # parses every core path against core.schema.json
        assert cw.format == fid
        named = set(cw.rules_by_native) | set(cw.unmapped)
        missing = [f for f in cw.fields if f not in named]
        extra = [f for f in named if f not in cw.fields]
        if missing or extra:
            problems.append(f"{fid}: not covered {missing[:5]}, not in fields.json {extra[:5]}")
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- transforms (section 7 tables)

SPEC_ROWS = [
    # (transform, forward input, forward output) from CROSSWALK_FORMAT.md section 7
    ({"cast": {"to": "integer", "from": "string"}}, "3099441038", 3099441038),
    ({"cast": {"to": "integer", "from": "string"}}, " 9606 ", 9606),
    ({"map": {"values": {"Complete Genome": "complete genome", "Chromosome": "chromosome"}}},
     "Complete Genome", "complete genome"),
    ({"map": {"values": {"1": True, "0": False}}}, "1", True),
    ({"map": {"values": {"unlocalised-scaffold": "unlocalized-scaffold"}}},
     "unlocalised-scaffold", "unlocalized-scaffold"),
    ({"regex": {"pattern": r"taxonomy:(\d+)$", "as": "integer", "template": "https://identifiers.org/taxonomy:{}"}},
     "https://identifiers.org/taxonomy:9606", 9606),
    ({"regex": {"pattern": r"^(.*?)(?: \(.*\))?$"}}, "Homo sapiens (human)", "Homo sapiens"),
    ({"regex": {"pattern": "=(.*)$"}}, "strain=S288C", "S288C"),
    ({"prefix": {"add": "SQ."}}, "Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO", "SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"),
    ({"prefix": {"strip": "./"}}, "./GCA_000146045.2_R64_genomic.fna.gz", "GCA_000146045.2_R64_genomic.fna.gz"),
    ({"replace": {"old": "_", "new": " "}}, "Homo_sapiens", "Homo sapiens"),
    ({"split": {"sep": ";"}}, "7219534;10508508;10830953", ["7219534", "10508508", "10830953"]),
    ({"split": {"sep": ","}}, "chrMT,M,chrM", ["chrMT", "M", "chrM"]),
    ({"date": {"format": "%Y/%m/%d"}}, "2022/02/03", "2022-02-03"),
    ({"date": {"format": "%Y/%m/%dT%H:%M:%S"}}, "2014/01/15T21:14:12", "2014-01-15T21:14:12"),
    ({"curie": {"namespaces": {"NCBI": "refseq"}}}, "refseq:NC_000001.11",
     {"namespace": "refseq", "value": "NC_000001.11"}),
    ({"curie": {}}, ["GRCh38:chr1", "MD5:6aef897c3d6ff0c78aff06ac189178dd"],
     [{"namespace": "grch38", "value": "chr1"}, {"namespace": "md5", "value": "6aef897c3d6ff0c78aff06ac189178dd"}]),
    ({"rekey": {"keys": {"dbname": "namespace", "name": "value"}, "values": {"namespace": {"UCSC": "ucsc"}}}},
     [{"dbname": "UCSC", "name": "chr1"}], [{"namespace": "ucsc", "value": "chr1"}]),
    ({"rekey": {"keys": {"chrom": "name", "len": "length"}}}, [{"chrom": "chrI", "len": 230218}],
     [{"name": "chrI", "length": 230218}]),
    ({"entries": {"key": "location", "value": "checksums.sha256"}}, {"hg38canon.fa": "87b0"},
     [{"location": "hg38canon.fa", "checksums": {"sha256": "87b0"}}]),
    ({"entries": {"key": "kind", "value": "location"}}, {"fasta": "hg38.fa", "fai": "hg38.fa.fai"},
     [{"kind": "fasta", "location": "hg38.fa"}, {"kind": "fai", "location": "hg38.fa.fai"}]),
    ({"accession": {}}, "GCF_000001405.40", {"namespace": "insdc.gcf", "value": "GCF_000001405.40"}),
    ({"accession": {}}, "GCA_000001405", {"namespace": "insdc.gca", "value": "GCA_000001405"}),
    ({"accession": {"other": "unspecified"}}, "PBARC", {"namespace": "unspecified", "value": "PBARC"}),
]

SPEC_INVERSE_ROWS = [
    ({"cast": {"to": "integer", "from": "string"}}, 3099441038, "3099441038", None),
    ({"map": {"values": {"1": True, "0": False}}}, True, "1", "string"),
    ({"map": {"values": {"1": True, "0": False}}}, True, 1, "integer"),  # Ensembl is_circular
    ({"regex": {"pattern": r"taxonomy:(\d+)$", "as": "integer", "template": "https://identifiers.org/taxonomy:{}"}},
     9606, "https://identifiers.org/taxonomy:9606", None),
    ({"prefix": {"add": "SQ."}}, "SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO", "Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO", None),
    ({"replace": {"old": "_", "new": " "}}, "Saccharomyces cerevisiae", "Saccharomyces_cerevisiae", None),
    ({"split": {"sep": ";"}}, ["a", "b"], "a;b", None),
    ({"date": {"format": "%Y/%m/%d"}}, "2022-02-03", "2022/02/03", None),
    ({"curie": {"namespaces": {"NCBI": "refseq"}}}, {"namespace": "refseq", "value": "NC_000001.11"},
     "NCBI:NC_000001.11", None),
    ({"rekey": {"keys": {"dbname": "namespace", "name": "value"}, "values": {"namespace": {"UCSC": "ucsc"}}}},
     [{"namespace": "ucsc", "value": "chr1"}], [{"dbname": "UCSC", "name": "chr1"}], None),
    ({"entries": {"key": "kind", "value": "location"}}, [{"kind": "fasta", "location": "hg38.fa"}],
     {"fasta": "hg38.fa"}, None),
    ({"accession": {}}, [{"namespace": "insdc.gcf", "value": "GCF_000001405.40"},
                         {"namespace": "insdc.gca", "value": "GCA_000001405.29"}], "GCF_000001405.40", None),
    ({"accession": {"namespaces": ["insdc.gca", "insdc.gcf"], "index": 1}},
     [{"namespace": "insdc.gcf", "value": "GCF_000001405.40"},
      {"namespace": "insdc.gca", "value": "GCA_000001405.29"}], "GCA_000001405.29", None),
    ({"accession": {"namespaces": ["insdc.gca"]}},
     [{"namespace": "unspecified", "value": "PBARC"}, {"namespace": "insdc.gca", "value": "GCA_000001405.15"}],
     "GCA_000001405.15", None),
]


@pytest.mark.parametrize("transform,value,expected", SPEC_ROWS, ids=lambda x: str(x)[:30])
def test_transform_forward_spec_rows(transform, value, expected):
    assert C.forward(transform, value) == expected


@pytest.mark.parametrize("transform,value,expected,native_type", SPEC_INVERSE_ROWS, ids=lambda x: str(x)[:30])
def test_transform_inverse_spec_rows(transform, value, expected, native_type):
    assert C.inverse(transform, value, native_type) == expected


def test_transform_no_value_cases():
    with pytest.raises(C.NoValue):
        C.forward({"regex": {"pattern": "^x(.)"}}, "abc")
    with pytest.raises(C.NoValue):
        C.inverse({"regex": {"pattern": "(.)"}}, "a")  # no template, no inverse
    with pytest.raises(C.NoValue):
        C.forward({"map": {"values": {"a": "b"}, "other": "drop"}}, "z")
    with pytest.raises(C.NoValue):
        C.forward({"cast": {"to": "integer", "from": "string"}}, "12a")
    with pytest.raises(C.NoValue):
        C.forward({"date": {"format": "%Y/%m/%d"}}, "April 2011")
    with pytest.raises(C.NoValue):
        C.forward({"accession": {}}, "hg38")  # matches no accession pattern and no `other`
    with pytest.raises(C.NoValue):
        C.inverse({"accession": {"index": 1}}, [{"namespace": "insdc.gca", "value": "GCA_000146045.2"}])
    # element-wise on a list: items that give no value become null (kept in place)
    assert C.forward({"regex": {"pattern": "^MD5:(.*)$"}}, ["GRCh38:1", "MD5:abc"]) == [None, "abc"]


def test_rule_examples_match_transforms():
    """Section 10 checks 3 and 4: every rule example converts as written, and
    both-way rules without a lossy note give the native value back."""
    bad, checked = [], 0
    for fid in C.crosswalk_ids():
        cw = C.load_crosswalk(fid)
        for rule in cw.rules:
            ex = rule.raw.get("example")
            if not ex or ex.get("truncated") or rule.direction == "from_core" or rule.compute:
                continue
            checked += 1
            try:
                got = C.forward(rule.transforms, ex["native"])
            except C.NoValue:
                got = "<no value>"
            if isinstance(got, list) and not isinstance(ex["core"], list):
                got = [x for x in got if x is not None]
                got = got[0] if len(got) == 1 else got
            if got != ex["core"]:
                bad.append(f"{fid} {rule.native}: {ex['native']!r} -> {got!r}, example says {ex['core']!r}")
                continue
            if rule.direction == "both" and rule.lossy is None:
                core_value = ex["core"]
                # an `accession` transform with index n reads item n of the accessions list
                n = next((p.get("index", 0) for name, p in rule.transforms if name == "accession"), 0)
                if n:
                    core_value = [ex["core"]] * (n + 1)
                try:
                    back = C.inverse(rule.transforms, core_value, rule.native_type)
                except C.NoValue:
                    back = "<no value>"
                if back != ex["native"]:
                    bad.append(f"{fid} {rule.native}: inverse of {ex['core']!r} is {back!r}, not {ex['native']!r}")
    assert checked > 900
    assert not bad, "\n".join(bad[:20])


# ---------------------------------------------------------------- every example to core

@pytest.mark.parametrize("case", OWNED, ids=_id)
def test_example_converts_to_valid_core(case):
    fid, src, rel = case
    native, cores, _ = _converted(fid, src, rel)
    assert native, f"adapter read nothing from {rel}"
    assert cores, f"{fid} made no core record from {rel}"
    cw = C.load_crosswalk(fid)
    for core in cores:
        errors = validate_core(core)
        assert not errors, f"{rel}: " + "; ".join(errors[:5])
        assert core["subject"] == cw.subject
        assert core["provenance"][0]["format"] == fid


@pytest.mark.parametrize("path", UNOWNED, ids=lambda p: f"{p.parent.parent.name}:{p.name}")
def test_unlisted_example_converts_or_has_no_adapter(path):
    """Example files no crosswalk format lists: convert if some adapter detects them."""
    text = path.read_text(encoding="utf-8", errors="replace")
    found = [(f, s) for f, s in C.detect(text, path.name) if f != C.CORE and s >= 0.5]
    if not found:
        owners = [fid for fid, i in C.format_info().items()
                  if any((SOURCES / i["source"] / e) == path for e in i["example_files"])]
        pytest.skip(f"no adapter reads this file (listed for formats without an adapter: {owners or 'none'})")
    fid = found[0][0]
    cores = C.to_core(fid, C.read_native(text, fid), filename=path.name)
    assert cores
    for core in cores:
        assert not validate_core(core)


def test_seqcol_digests_are_derived_correctly():
    """The derived seqcol digest equals the digest in the example file names."""
    checked = 0
    for fid, src, rel in OWNED:
        m = re.search(r"_([A-Za-z0-9_-]{32})\.json$", rel)
        if fid != "ga4gh_seqcol_level2" or not m:
            continue
        _, cores, _ = _converted(fid, src, rel)
        assert cores[0]["collection"]["digest"] == m.group(1), rel
        assert len(cores[0]["collection"]["level1"]) == 6
        checked += 1
    assert checked >= 2


def test_no_example_contradicts_its_own_digest():
    """Where a source states a seqcol digest or counts and the engine can also compute
    them, they must agree (a conflict here means wrong data or a wrong derivation)."""
    bad = []
    for fid, src, rel in OWNED:
        for core in _converted(fid, src, rel)[1]:
            for c in core.get("conflicts") or []:
                if c["path"].startswith(("collection.digest", "collection.level1", "collection.nSequences",
                                         "collection.totalLength")):
                    bad.append(f"{fid} {rel}: {c['path']} {[v['value'] for v in c['values']]}")
    assert not bad, "\n".join(bad)


# ---------------------------------------------------------------- round trip

def _round_trip(fid, src, rel):
    native, cores, _ = _converted(fid, src, rel)
    back = C.from_core(fid, cores)
    return native, back


@pytest.mark.parametrize("case", OWNED, ids=_id)
def test_round_trip_keeps_lossless_fields(case):
    """native -> core -> native keeps every field whose rules all have lossy: null
    (and every unmapped field, through extras)."""
    fid, src, rel = case
    native, back = _round_trip(fid, src, rel)
    assert len(back) == len(native), f"{len(native)} records became {len(back)}"
    cw = C.load_crosswalk(fid)
    lossless = cw.lossless_fields()
    changed = defaultdict(list)
    for i, (a, b) in enumerate(zip(native, back)):
        for k in lossless:
            if a.get(k) is not None and a.get(k) != b.get(k):
                changed[k].append((i, a.get(k), b.get(k)))
    known = {k: v for k, v in changed.items() if (fid, k) in KNOWN_ROUND_TRIP_CHANGES}
    for k, v in known.items():
        warnings.warn(RoundTripNote(f"{fid} {Path(rel).name}: {k} {v[0][1]!r} -> {v[0][2]!r} "
                                    f"({KNOWN_ROUND_TRIP_CHANGES[(fid, k)]})"))
    unknown = {k: v for k, v in changed.items() if k not in known}
    assert not unknown, "\n".join(f"{k}: row {v[0][0]}: {v[0][1]!r} -> {v[0][2]!r} ({len(v)} rows)"
                                  for k, v in unknown.items())
    C.write_native(back, fid)  # the adapter can write what came back


def test_round_trip_added_fields_report():
    """Fields that come back filled although the source left them empty: two native
    fields share one core path (e.g. taxon.strain), so writing fills both. Reported."""
    added = defaultdict(int)
    for fid, src, rel in OWNED:
        native, back = _round_trip(fid, src, rel)
        for a, b in zip(native, back):
            for k, v in b.items():
                if v is not None and a.get(k) is None:
                    added[(fid, k)] += 1
    if added:
        lines = [f"  {fid}: {k} ({n} rows)" for (fid, k), n in sorted(added.items())]
        warnings.warn(RoundTripNote(f"{len(added)} native fields are filled on write although the "
                                    f"example left them empty:\n" + "\n".join(lines)))


def test_lossy_and_one_way_fields_report():
    """How much each format loses on a round trip, by the crosswalk's own notes."""
    one_way = []
    for fid in C.crosswalk_ids():
        cw = C.load_crosswalk(fid)
        for f in cw.fields:
            rules = cw.rules_by_native.get(f, [])
            if rules and not any(r.writes for r in rules):
                one_way.append(f"{fid}: {f}")
    if one_way:
        warnings.warn(RoundTripNote(f"{len(one_way)} native fields are read but never written back "
                                    "(to_core rules only):\n  " + "\n  ".join(one_way)))


# ---------------------------------------------------------------- cross-source checks

def _versions(prefix: str, lo: int, hi: int) -> set:
    return {f"{prefix}.{v}" for v in range(lo, hi + 1)}


ANCHORS = {
    # GRCh38 and its patches; GCA .1-.14 and GCF .1-.25 are GRCh37 and older
    "GRCh38": {"accessions": _versions("GCA_000001405", 15, 29) | _versions("GCF_000001405", 26, 40),
               "labels": {"GRCh38", "GRCh38.p14", "hg38"}, "taxa": {9606}},
    "R64": {"accessions": {"GCA_000146045.2", "GCF_000146045.2"},
            "labels": {"R64", "R64-1-1", "sacCer3"}, "taxa": {4932, 559292}},
}
MAIN_SOURCES = ("ncbi", "ena", "ensembl", "ucsc")


@lru_cache(maxsize=None)
def _anchor_facts() -> dict[str, list[dict]]:
    """One row of facts per core record that is about an anchor genome."""
    out = defaultdict(list)
    seen = set()
    for fid, src, rel in OWNED:
        path = SOURCES / src / rel
        if path in seen:
            continue
        seen.add(path)
        fmt, _, cores, also = C.read_core(_text(src, rel), fid, rel, companions=True)
        full_table = any(C.load_crosswalk(f).mode == "group" and C.load_crosswalk(f).target == "sequences"
                         for f in [fmt] + also)
        for core in cores:
            a, col = core.get("assembly") or {}, core.get("collection") or {}
            acc_list = [x["value"] for x in a.get("accessions") or []]
            accs = set(acc_list)
            names = {x["value"] for x in (a.get("labels") or []) + (col.get("labels") or []) + (col.get("aliases") or [])}
            seqs = core.get("sequences") or []
            n = col.get("nSequences") or (len(seqs) if full_table and seqs else None)
            for anchor, spec in ANCHORS.items():
                if accs & spec["accessions"] or names & spec["labels"]:
                    out[anchor].append({
                        "where": f"{src}/{'+'.join([fmt] + also)}/{Path(rel).name}",
                        "source": src, "accession": acc_list[0] if acc_list else None, "accessions": accs,
                        "taxon": (a.get("taxon") or {}).get("id"), "species": (a.get("taxon") or {}).get("name"),
                        "n": n, "total": col.get("totalLength") or (a.get("vitalStats") or {}).get("totalBasePairs"),
                        "names": names & spec["labels"],
                    })
    return out


def _report(anchor: str, fact: str, rows: list[dict]) -> None:
    by_value = defaultdict(list)
    for r in rows:
        if r[fact] is not None:
            by_value[r[fact]].append(r["where"])
    if len(by_value) > 1:
        lines = [f"  {v!r}: {len(w)} record(s), e.g. {', '.join(sorted(set(w))[:3])}"
                 for v, w in sorted(by_value.items(), key=lambda kv: -len(kv[1]))]
        warnings.warn(SourceDisagreement(f"{anchor}: sources give {len(by_value)} different values for "
                                         f"{fact}:\n" + "\n".join(lines)))


@pytest.mark.parametrize("anchor", list(ANCHORS))
def test_anchor_found_in_main_sources(anchor):
    rows = _anchor_facts()[anchor]
    have = {r["source"] for r in rows}
    assert set(MAIN_SOURCES) <= have, f"{anchor}: no records from {set(MAIN_SOURCES) - have}"


@pytest.mark.parametrize("anchor", list(ANCHORS))
def test_anchor_taxon_and_accession_family_agree(anchor):
    """Hard facts: every taxon id given for the anchor is the species (or its strain),
    and a record found by an anchor name (hg38, sacCer3, ...) never carries another
    assembly's accession. Species names are free text in some formats (SAM SP:
    'Human'), so they are only reported."""
    spec, bad = ANCHORS[anchor], []
    for r in _anchor_facts()[anchor]:
        if r["taxon"] is not None and r["taxon"] not in spec["taxa"]:
            bad.append(f"{r['where']}: taxon {r['taxon']}")
        if r["accession"] and re.match(r"^GC[AF]_", r["accession"]) and r["accession"] not in spec["accessions"]:
            bad.append(f"{r['where']}: accession {r['accession']}")
    assert not bad, "\n".join(bad)


@pytest.mark.parametrize("anchor", list(ANCHORS))
def test_anchor_cross_source_report(anchor):
    """Accession version, taxon id, species, sequence count and total length, compared
    across all sources. Differences are reported as SourceDisagreement warnings."""
    rows = _anchor_facts()[anchor]
    for fact in ("accession", "taxon", "species", "n", "total"):
        _report(anchor, fact, rows)
    # same exact accession, different sequence counts: the sharpest kind of disagreement
    by_acc = defaultdict(list)
    for r in rows:
        if r["n"] is not None:
            for acc in r["accessions"]:
                by_acc[acc].append(r)
    for acc, rs in sorted(by_acc.items()):
        _report(f"{anchor} {acc}", "n", rs)
    assert rows


def test_merge_records_that_share_an_accession():
    a = C.to_core("ncbi_datasets_assembly_report",
                  C.read_native(_text("ncbi", "examples/datasets_dataset_report_GCA_000146045.2.json"),
                                "ncbi_datasets_assembly_report"))[0]
    b = C.to_core("ena_assembly_xml", C.read_native(_text("ena", "examples/assembly_xml_GCA_000146045.2.xml"),
                                                    "ena_assembly_xml"))[0]
    assert C.shared_identifiers(a, b)
    m = C.merge([a, b])
    assert [p["id"] for p in m["provenance"]] == ["p1", "p2"]
    assert m["assembly"]["accessions"][0] == {"namespace": "insdc.gca", "value": "GCA_000146045.2"}
    assert len({(x["namespace"], x["value"]) for x in m["assembly"]["accessions"]}) == len(m["assembly"]["accessions"])
    assert "fieldSources" in m and "assembly.accessions[namespace=insdc.gca].value" in m["fieldSources"]
    assert not validate_core(m), validate_core(m)[:3]
    c = C.to_core("ucsc_chrom_sizes", C.read_native("chrA\t10\n", "ucsc_chrom_sizes"))[0]
    with pytest.raises(C.ConversionError):
        C.merge([a, c])


# ---------------------------------------------------------------- API and CLI

def test_convert_api_examples():
    text = _text("ucsc", "examples/bigZips_sacCer3.chrom.sizes")
    out = C.convert(text, "galaxy_len")
    assert out.split() == text.split()
    # an NCBI assembly report holds two formats; both are read when the format is detected
    rep = _text("ncbi", "examples/ftp_GCA_000146045.2_R64_assembly_report.txt")
    res = C.convert_detailed(rep, "ucsc_chrom_sizes", names="ucsc")
    assert res.also_read == ["ncbi_assembly_report_sequences"]
    assert res.text.splitlines()[0] == "chrI\t230218"
    with pytest.raises(C.ConversionError):
        C.convert(rep, "ucsc_chrom_sizes")  # no names chosen: the report keeps names only as aliases
    # core text converts onward, and a core record round-trips through text
    core_yaml = C.convert(text, C.CORE)
    assert C.detect(core_yaml)[0][0] == C.CORE
    assert C.convert(core_yaml, "ucsc_chrom_sizes") == C.convert(text, "ucsc_chrom_sizes")
    with pytest.raises(C.ConversionError):
        C.convert(text, "ncbi_assembly_report_header")  # nothing to write


def _cli(*args) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


def test_cli_commands():
    code, out, _ = _cli("formats")
    assert code == 0 and len(out.splitlines()) == len(C.crosswalk_ids())
    seqcol = str(SOURCES / "ga4gh/examples/seqcol_level2_R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.json")
    code, out, _ = _cli("detect", seqcol)
    assert code == 0 and out.strip() == "ga4gh_seqcol_level2"
    code, out, _ = _cli("core", seqcol)
    core = yaml.safe_load(out)
    assert code == 0 and core["collection"]["digest"] == "ia9g4Myony-xxLsSc7eQOC_NdClGgPGu"
    code, out, _ = _cli("core", seqcol, "--json")
    assert json.loads(out)["collection"]["nSequences"] == 17
    code, out, _ = _cli("convert", seqcol, "--to", "ucsc_chrom_sizes")
    assert code == 0 and out.splitlines()[0] == "I\t230218"
    code, _, err = _cli("convert", seqcol, "--to", "ncbi_assembly_report_header")
    assert code == 2 and "nothing to write" in err


def test_validator_catches_bad_records():
    schema = C.load_schema()
    assert validate({"refmeta": "0.1"}, schema) == []
    errors = validate({"subject": "planet", "collection": {"digest": "short"}, "junk": 1}, schema)
    text = "\n".join(errors)
    assert "refmeta" in text and "planet" in text and "short" in text and "junk" in text
    assert validate({"refmeta": "0.1", "sequences": [{"length": True}]}, schema)


def test_unreadable_input_is_a_conversion_error():
    # review fix: a reader that cannot parse the text gives a clean error (CLI exit 2), not a traceback
    export = str(SOURCES / "fhr/examples/upstream_example.fhr.export.jsonld")
    code, _, err = _cli("convert", export, "--to", "ucsc_chrom_sizes")
    assert code == 2 and "cannot read this text as" in err
    for fid in ("fhr_json", "ena_assembly_xml", "ucsc_chrom_sizes", "refgenie_genome_config"):
        with pytest.raises(C.ConversionError):
            C.convert("hello\n{[", C.CORE, from_format=fid)


def test_seqcol_writers_need_required_attributes():
    # review fix: names and lengths alone are not a sequence collection (seqcol requires sequences)
    sizes = _text("ucsc", "examples/bigZips_sacCer3.chrom.sizes")
    with pytest.raises(C.ConversionError, match="needs names, lengths, sequences"):
        C.convert(sizes, "ga4gh_seqcol_level2")
    with pytest.raises(C.ConversionError):
        C.convert(sizes, "ga4gh_seqcol_level1")
    seqcol = _text("ga4gh", "examples/seqcol_level2_R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.json")
    assert json.loads(C.convert(seqcol, "ga4gh_seqcol_level2"))["sequences"]


def test_genome_config_writer_does_not_drop_rows():
    # review fix: rows with asset paths but no genome digest used to give 'genomes: {}' silently
    loc = _text("galaxy", "examples/cvmfs_all_fasta.loc")
    with pytest.raises(C.ConversionError, match=r"genomes\.\{genome\}"):
        C.convert(loc, "refgenie_genome_config")


# ---------------------------------------------------------------- namespaces (mapping/namespaces.yaml)

def test_namespace_registry_is_consistent():
    reg = C.load_namespaces()
    lists = {"assembly.accessions", "assembly.labels", "collection.aliases", "collection.labels",
             "sequences.aliases"}
    for ns, n in reg.items():
        assert re.fullmatch(r"^[a-z][a-z0-9_.-]*$", ns), ns
        assert set(n["lists"]) <= lists, ns
        if n.get("pattern") and n.get("example") is not None:
            assert re.fullmatch(n["pattern"], str(n["example"])), ns
    assert C.accession_namespaces()[:2] == ("insdc.gca", "insdc.gcf")


def test_crosswalk_namespaces_are_official():
    """Every namespace a crosswalk names in a keyed path is in the registry, and used
    in a list the registry allows. (Namespaces that come from the data, such as
    SeqRepo's assembly prefixes, are custom and are not checked here.)"""
    reg, bad = C.load_namespaces(), []
    for fid in C.crosswalk_ids():
        text = (C._data("crosswalk", f"{fid}.yaml")).read_text(encoding="utf-8")
        for path, ns in re.findall(r"((?:assembly|collection|sequences\[\])\.\w+)\[namespace=([^\],]+)", text):
            where = path.replace("[]", "")
            if ns not in reg:
                bad.append(f"{fid}: {ns} not official")
            elif where not in reg[ns]["lists"]:
                bad.append(f"{fid}: {ns} used in {where}")
    assert not bad, "\n".join(bad)


def test_check_namespaces_reports_custom_misplaced_and_pattern():
    from refmeta.validate import check_namespaces
    rec = {"refmeta": "0.1", "subject": "assembly",
           "assembly": {"accessions": [{"namespace": "insdc.gca", "value": "GCA_1"},
                                       {"namespace": "gwh", "value": "GWHAAAA00000000"}],
                        "labels": [{"namespace": "refseq", "value": "NC_000001.11"}]},
           "sequences": [{"name": "chr1", "aliases": [{"namespace": "ucsc", "value": "chr1"}]}]}
    notes = check_namespaces(rec)
    assert any("custom namespace 'gwh'" in n for n in notes)
    assert any("'refseq' is not meant for this list" in n for n in notes)
    assert any("do not match the 'insdc.gca' pattern" in n for n in notes)
    assert len(notes) == 3
