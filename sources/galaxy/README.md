# Galaxy reference data

**What it is.** How the Galaxy platform names, lists and finds reference
genomes: the dbkey list (`builds.txt`, `__dbkeys__`), the "data tables" that
tools read (`tool_data_table_conf.xml` plus one tab-separated `.loc` file per
table), the data managers that fill those tables, the public API that exposes
them, and the Intergalactic Data Commission (IDC) files that decide what goes
on the shared CVMFS reference repository (`/cvmfs/data.galaxyproject.org`).

**Who maintains it.**

| Part | Repository | Maintainer |
|---|---|---|
| builds.txt, data tables, .loc parsing, API, RefgenieToolDataTable | [galaxyproject/galaxy](https://github.com/galaxyproject/galaxy) | Galaxy Project |
| Data managers (fetch genome, samtools faidx, BWA-MEM, Bowtie2, STAR) | [galaxyproject/tools-iuc](https://github.com/galaxyproject/tools-iuc) `data_managers/` | Intergalactic Utilities Commission (IUC) |
| genomes.yml, data_managers.yml, request files, CVMFS builds | [galaxyproject/idc](https://github.com/galaxyproject/idc) | Intergalactic Data Commission (IDC) |
| `sync/` summaries (all_tables YAML, seqcol JSON/YAML) | [galaxyproject/idc#88](https://github.com/galaxyproject/idc/pull/88), head `lldelisle/idc@245c1a9` | Lucille Delisle and IDC contributors (open WIP PR) |

**Reuse terms.** Galaxy: MIT since 2026-02-25 (docs CC BY 3.0, per
`LICENSE.txt`). tools-iuc, idc and lldelisle/idc: MIT. The served API data
(usegalaxy.org, usegalaxy.eu) has no stated terms.

## How Galaxy models a genome (read this first)

```
dbkey  hg38                          <- builds.txt / __dbkeys__ (value=hg38, name, len_path -> hg38.len)
 |- all_fasta value=hg38       path=.../hg38/seq/hg38.fa
 |- all_fasta value=hg38canon  path=.../hg38/seq/hg38canon.fa      (chr1-22,X,Y,M)
 |- all_fasta value=hg38female path=.../hg38/seq/hg38female.fa
 |- bwa_mem_indexes value=hg38      path=.../hg38/hg38full/bwa_index_v0.7.10-r789/hg38full.fa
 |- bwa_mem_indexes value=hg38canon path=.../hg38/hg38canon/bwa_index_v0.7.10-r789/hg38canon.fa
 '- ...
```

- **dbkey** is a label on datasets that says "these coordinates belong to this
  build". It is shared: one dbkey covers several FASTA files (full,
  canonical, female). It is not a unique key.
- **value** (called `<unique_build_id>` in every `.loc` sample) is the row key
  of each data table and what tools and workflows store. It is the closest
  thing Galaxy has to a sequence-collection id, but it is a free string,
  only meant to be unique within one table on one server.
- **path** is one copy of the file (or index) on one server.
- The **.len** file named by `__dbkeys__` `len_path` gives the dbkey's
  sequence names and lengths. It is per dbkey, not per FASTA.
- Galaxy stores **no assembly accession, taxon, seqcol digest or checksum**
  in any of its own tables. Assembly facts appear only as free text inside
  display names (`Human Dec. 2013 (GRCh38/hg38) (hg38)`), or because newer
  repositories (BRC, VGP) use the accession itself as dbkey and value
  (`GCF_000001405.40`). PR #88 adds seqcol digests next to the Galaxy names.

Levels covered: mostly **deployment** and **copy**; **sequence** (.len,
seqcol level 2); **collection** only through PR #88 digests, the API
`chrom_info`, and the IDC request `sorting` parameters (which decide which
sequences a FASTA keeps); **assembly** only weakly (UCSC dbkey or NCBI
accession in IDC request parameters, free text in names).

## Formats

All 20 formats are in `fields.json`; 19 have adapters in
`tools/refmeta/formats/galaxy.py` (format ids are `galaxy_*`).

| Format id | What | One native record = | Record key |
|---|---|---|---|
| `galaxy_builds_txt` | `tool-data/shared/ucsc/builds.txt`: `dbkey<TAB>display name` | one line | dbkey (can repeat) |
| `galaxy_len` | `.len`: `chrom<TAB>length` | one sequence | chrom (within file) |
| `galaxy_api_genomes` | `GET /api/genomes`: `[[name, dbkey], ...]` | one pair | `[1]` dbkey (can repeat) |
| `galaxy_api_genome` | `GET /api/genomes/{dbkey}` | one dbkey | `id` |
| `galaxy_api_tool_data` | `GET /api/tool_data/{table}`: `{name, model_class, columns, fields:[[...]]}` | one table row | `name` + `fields[].value` |
| `galaxy_tool_data_table_conf` | `tool_data_table_conf.xml` | one `<table>` | `name` |
| `galaxy_loc_all_fasta` | `all_fasta.loc`: value, dbkey, name, path | one row | `value` |
| `galaxy_loc_fasta_indexes` | `fasta_indexes.loc`: value, dbkey, name, path | one row | `value` |
| `galaxy_loc_bwa_mem_indexes` | `bwa_mem_index.loc`: value, dbkey, name, path | one row | `value` |
| `galaxy_loc_bowtie2_indexes` | `bowtie2_indices.loc`: value, dbkey, name, path | one row | `value` |
| `galaxy_loc_rnastar_index2x_versioned` | `rnastar_index2x_versioned.loc`: + with_gene_model, version | one row | `value` |
| `galaxy_loc_dbkeys` | `dbkeys.loc` (table `__dbkeys__`): value, name, len_path | one row | `value` (= dbkey) |
| `galaxy_data_manager_json` | data manager output `{"data_tables": {table: [entries]}}` | one entry | `data_table` + `value` |
| `galaxy_refgenie_table` | template variables of `RefgenieToolDataTable` (prose/code only, **no adapter**) | - | `__REFGENIE_UUID__` |
| `galaxy_idc_genomes` | IDC `genomes.yml` and `cvmfs_current_managed/cvmfs_managed_genomes.yml` | one genome entry | `id` |
| `galaxy_idc_data_managers` | IDC `data_managers.yml` | one data manager | `data_manager` (mapping key) |
| `galaxy_idc_request` | IDC `data-managers/<table>/<version>.yaml` | one file | its path |
| `galaxy_idc_all_tables` | PR #88 `sync/cvmfs_20260715.yml` (all data tables of a server) | one table row | `table` + `value` + `loc_file` |
| `galaxy_idc_refget_json` | PR #88 `json/<unique_build_id>.json` (seqcol digests + Galaxy aliases) | one file | `level_0` |
| `galaxy_idc_refget_yaml` | PR #88 `yaml/all_fasta.yml` | one entry | `unique_build_id` (mapping key) |

Native-record conventions: TSV keys are the column names Galaxy declares
(`.loc`) or the names in the maintainers' sample headers (`builds.txt`:
`dbkey`, `display_name`; `.len`: `chrom`, `len` as in the API). Nested
JSON/YAML is flattened to dotted paths (`level_1.names`,
`params.dbkey_source.dbkey`; in IDC requests only `params` and `depends_on`
are flattened, `sha256` stays an object keyed by file name). A mapping key or
enclosing key becomes a named key: `data_table`, `table`, `data_manager`,
`unique_build_id`. Arrays without keys use `[0]`, `[1]`. Table rows in the
API use `fields[].<column>` so the table's `name` and the row's `name` do not
collide. `.loc` reading follows `TabularToolDataTable.parse_file_fields`:
lines whose first non-blank character is `#` are skipped, split on TAB, rows
with fewer fields than columns are dropped, extra fields are ignored.

## Quirks that matter for mapping

1. **One dbkey, many builds; `value` is the key.** `dbkey=hg38` covers
   `hg38`, `hg38canon` and `hg38female` in `all_fasta`
   (`examples/cvmfs_all_fasta.loc`). Map dbkey to "a build family / naming
   context", never to one collection.
2. **`value` is not enforced unique.** usegalaxy.org serves `all_fasta`
   `hg38canon` twice (same in the public view, which hides the directory); usegalaxy.eu serves
   `hg38canon` twice with two different display names; PR #88 found `ornAna1`
   listed twice in one `.loc`, and `GCF_014108235.1` in both the BRC and VGP
   `.loc` files. `allow_duplicate_entries="False"` only removes rows that are
   identical in every column.
3. **The same `value` in two tables need not be the same FASTA.** `all_fasta`
   `hg38` -> `hg38/seq/hg38.fa`, but `bwa_mem_indexes` and `bowtie2_indexes`
   `hg38` -> `hg38full`. `fasta_indexes` `hg38` is `sam_index/hg38.fa`.
   `rnastar_index2x_versioned` `hg38` does not say which FASTA it used.
   Index tables have no column pointing to the source FASTA; the link is by
   matching value/dbkey only, and data managers let admins change the value
   (`sam_fasta_index_builder 1.21+galaxy0` defaults it to the **dbkey**).
4. **Two naming systems for the same assembly live side by side, unlinked.**
   usegalaxy.org has dbkey `hg38` (UCSC) and dbkey `GCF_000001405.40` (BRC);
   `sacCer3` and `GCF_000146045.2`. Nothing in Galaxy says they are the same
   assembly. Their `.len` files: `sacCer3` uses `chrI...chrM`,
   `GCF_000146045.2` uses `NC_001133.9...` (same 17 lengths);
   `GCF_000001405.40` uses UCSC names (`chr1`, `chr1_KI270706v1_random`) and
   its 455 entries are an exact subset of the 711 in `hg38.len`.
5. **Display names are free text and server-specific.** Same value, different
   names on org and EU. They embed assembly names (`GRCh38/hg38`, `b38`,
   `GCF_000146045.2_R64`) that a parser could mine, but nothing guarantees the
   pattern. Lookalike: usegalaxy.eu dbkey **`GRCh38`** is "Homo Sapiens
   (GRCh38) Transcriptome + ERCC", not the genome.
6. **`.len` describes the dbkey, not a FASTA.** `hg38.len` lists 711 sequences
   (p14 patches incl.), `hg38canon.fa` has 25. Do not treat `len_path` or
   `/api/genomes/{id}` as the coordinate system of any one `all_fasta` row.
7. **API hides paths and reorders sequences.** `/api/tool_data/{table}` shows
   only the basename of the column named `path` to non-admins (`len_path` is
   shown in full). `/api/genomes/{id}` `chrom_info` is natural-sorted by name
   (`split_by_number`), not in `.len` or FASTA order.
8. **`__dbkeys__` has no `dbkey` column**: its `value` is the dbkey. The fetch
   data manager still writes a `dbkey` key in `__dbkeys__` JSON entries (used
   only to build the target path).
9. **Paths** are absolute server paths; `.loc` lines may contain
   `${__HERE__}` (the `.loc` file's directory). Data managers write relative
   names in their JSON; `data_manager_conf.xml` moves them to
   `genomes/<dbkey>/seq/`, `genomes/<dbkey>/<index>/<version>/<value>/` etc.
10. **PR #88 aliases replace `/` with `!`** in every alias value (so they fit
    in seqcol API URLs), including display names
    (`A. mellifera 04 Nov 2010 (Amel_4.5!apiMel4)`).
11. **PR #88 `level_0` is computed from `names` and `sequences` only** (gtars;
    `lengths` is not an inherent attribute in the current seqcol schema). I
    checked this by recomputing phiX174: only {names, sequences} reproduces
    the published `mVofqJ-PNURHT67R9WKgfNPjYXkVDKCF`.
12. **IDC `sha256` is a file checksum** (depends on line width, header text,
    blank lines), not a sequence digest. Data manager versions before 0.0.6
    wrote an extra empty line between chromosome files, which changes it.
13. **builds.txt**: an all-digit dbkey is a "manual" microbial build (sorted
    separately); `?` is "unspecified". `/api/genomes` merges builds.txt,
    `__dbkeys__`, user custom builds and history `.len` datasets, so the same
    dbkey can appear several times.
14. **Refgenie bridge.** A `type="refgenie"` table maps refgenie genome name ->
    `dbkey` (and `__dbkeys__` value), `refgenie:<genome>/<asset>:<tag>@<digest>`
    -> `value`, asset path -> `path`, seek key `chrom_sizes` -> `len_path`
    (`spec/galaxy/tool_data_table_conf.xml.sample`, lines 118-164). The
    digest is a refgenie asset digest, not a seqcol digest.
15. **IDC request directory/file name is the identity**
    (`data-managers/<data_table>/<version>.yaml`); the stem is the expected
    output `value`. `depends_on` wires the input but does not set the output
    value.

## Where every file came from (all fetched 2026-11-17)

Raw downloads are in a local download folder (not in this repository) (59 MB: full API responses,
the 24 MB `cvmfs_20260715.yml`, the 21 MB `cvmfs_20260715_perdbkey.yml`,
`usegalaxy_eu_20261009_perdbkey.yml`, UCSC `sacCer3.fa.gz`). Code files are
saved as `*.py.txt` so nothing imports or runs them. `make/` holds the
scripts that built `spec/`, `examples/` and `fields.json` from the raw folder
(`build_folder.py`, then `build_constructed.py`, then `make_fields.py`).

### spec/

| Path | Source URL |
|---|---|
| `spec/galaxy/builds.txt.sample` | https://raw.githubusercontent.com/galaxyproject/galaxy/dev/tool-data/shared/ucsc/builds.txt.sample |
| `spec/galaxy/manual_builds.txt.sample`, `ucsc_build_sites.txt.sample` | same folder, `tool-data/shared/ucsc/` |
| `spec/galaxy/all_fasta.loc.sample`, `twobit.loc.sample` | `.../galaxy/dev/tool-data/<file>` |
| `spec/galaxy/tool_data_table_conf.xml.sample` | `.../galaxy/dev/lib/galaxy/config/sample/tool_data_table_conf.xml.sample` (`config/tool_data_table_conf.xml.sample` is a symlink to it) |
| `spec/galaxy/dbkeys.loc.test` | `.../galaxy/dev/lib/galaxy/datatypes/converters/dbkeys.loc.test` |
| `spec/galaxy/lib_galaxy_tools_data__init__.py.txt` | `.../galaxy/dev/lib/galaxy/tools/data/__init__.py` (RefgenieToolDataTable) |
| `spec/galaxy/lib_galaxy_tool_util_data__init__.excerpt.py.txt` | lines 243-720 of `.../galaxy/dev/lib/galaxy/tool_util/data/__init__.py` (ToolDataTable, TabularToolDataTable, .loc parsing) |
| `spec/galaxy/lib_galaxy_managers_dbkeys.py.txt` | `.../galaxy/dev/lib/galaxy/managers/dbkeys.py` (read_dbnames, GenomeBuilds) |
| `spec/galaxy/lib_galaxy_visualization_genomes.py.txt` | `.../galaxy/dev/lib/galaxy/visualization/genomes.py` (/api/genomes/{id} body) |
| `spec/galaxy/lib_galaxy_webapps_galaxy_api_genomes.py.txt`, `..._api_tool_data.py.txt`, `lib_galaxy_managers_tool_data.py.txt` | `.../galaxy/dev/lib/galaxy/webapps/galaxy/api/{genomes,tool_data}.py`, `lib/galaxy/managers/tool_data.py` |
| `spec/galaxy/test_unit_app_tools_test_refgenie_data_table.py.txt`, `test_integration_refgenie.yml` | `.../galaxy/dev/test/unit/app/tools/test_refgenie_data_table.py`, `test/integration/refgenie.yml` |
| `spec/tools-iuc/<data_manager>/...` | `https://raw.githubusercontent.com/galaxyproject/tools-iuc/main/data_managers/<data_manager>/<same path>` for `data_manager_fetch_genome_dbkeys_all_fasta`, `data_manager_sam_fasta_index_builder`, `data_manager_bwa_mem_index_builder`, `data_manager_bowtie2_index_builder`, `data_manager_star_index_builder` (tool XML, `data_manager_conf.xml`, `tool_data_table_conf.xml.sample`, `tool-data/*.loc.sample`, `test-data/*`) |
| `spec/idc/...` | `https://raw.githubusercontent.com/galaxyproject/idc/3c1bddcfa2c2059dc478c6929f167c2e80aadb91/<same path>` (README, genomes.yml, data_managers.yml, config/tool_data_table_conf.xml, cvmfs_current_managed/*.yml, docs/*.md, schemas/data_managers.yml, data-managers/*/hg38canon.yaml) |
| `spec/idc/schemas/request.schema.excerpt.json` | **excerpt** of `schemas/request.schema.json` (630 KB, 98 `$defs`): top level kept whole; `$defs` and `allOf` cut to the 5 genome data managers (see `$comment` in the file) |
| `spec/idc_pr88/sync/...` | `https://raw.githubusercontent.com/lldelisle/idc/245c1a9de5e054c7dcede5f6435ef5dfb63b6414/sync/<file>` (README.md, ADMINS.md, four scripts as .txt) |

Commits: galaxy `dev` head was `d3e1f13ab44c` when fetched; tools-iuc `main`
head `a700fd5c27e0` (2026-11-16); idc `main` pinned at `3c1bddcfa2c2`
(2026-11-05); PR #88 head `245c1a9de5e0` (PR still open).

### examples/ (real records)

| Path | Source and how it was cut |
|---|---|
| `builds.txt` | the `#Harvested...` header, `hg38` and `sacCer3` lines of `builds.txt.sample` |
| `usegalaxy_org_api_genomes.excerpt.json` | https://usegalaxy.org/api/genomes (7473 pairs), kept `?`, hg38, sacCer3, GCF_000001405.40, GCF_000146045.2 in served order |
| `usegalaxy_org_api_genomes_{hg38,sacCer3,GCF_000001405.40,GCF_000146045.2}.json` | https://usegalaxy.org/api/genomes/{id}, whole response |
| `usegalaxy_org_api_tool_data_<table>.excerpt.json` | https://usegalaxy.org/api/tool_data/<table> for all_fasta, fasta_indexes, bwa_mem_indexes, bowtie2_indexes, rnastar_index2x_versioned, `__dbkeys__`; `fields` cut to rows whose value is hg38, hg38canon, hg38female, sacCer3, GCF_000001405.40 or GCF_000146045.2 |
| `usegalaxy_eu_api_tool_data_{all_fasta,__dbkeys__}.excerpt.json` | https://usegalaxy.eu/api/tool_data/<table>, same cut plus the `GRCh38` lookalike row |
| `cvmfs_{all_fasta,fasta_indexes,bwa_mem_index,bowtie2_indices,rnastar_index2x_versioned,dbkeys}.loc` | rows of PR #88 `sync/cvmfs_20260715.yml` whose value or dbkey is an anchor id, written back as TAB-joined `.loc` lines in the table's column order, with a `# from <loc_file>` comment before each source file's rows. Field text is exactly as in the YAML (the script had stripped line ends) |
| `idc_pr88_cvmfs_20260715_all_tables.excerpt.yml` | same anchor rows of `sync/cvmfs_20260715.yml` for those 6 tables plus twobit, sam_fa_indexes, picard_indexes, re-dumped with `yaml.dump` (as the PR script does) |
| `idc_pr88_test_dig_json_phiX174.json`, `idc_pr88_test_dig_yaml_all_fasta.yml` | PR #88 `sync/test_dig/json/phiX174.json`, `sync/test_dig/yaml/all_fasta.yml`, whole files |
| `dm_*` | tools-iuc `test-data` outputs of the five data managers (phiX174), whole files |
| `galaxy_tool_data_table_conf.xml.sample`, `idc_tool_data_table_conf.xml` | Galaxy sample (has refgenie tables) and IDC `config/tool_data_table_conf.xml` (a real deployment config), whole files |
| `idc_genomes_sacCer3.excerpt.yml` | the sacCer3 entry of IDC `genomes.yml`, text kept byte for byte (hg38 is not in genomes.yml) |
| `idc_cvmfs_managed_genomes_hg38_sacCer3.excerpt.yml` | the sacCer3, hg38female, hg38canon, hg38 entries of `cvmfs_current_managed/cvmfs_managed_genomes.yml`, text kept |
| `idc_request_{all_fasta,fasta_indexes,rnastar_index2x_versioned}_hg38canon.yaml` | IDC `data-managers/<table>/hg38canon.yaml`, whole files |
| `idc_data_managers.yml` | IDC `data_managers.yml`, whole file (not genome-specific) |

### examples/constructed/ (not served as files; say so when using them)

| Path | How it was made |
|---|---|
| `idc_pr88_json_hg38canon.json` | Computed by me, in the PR #88 json layout. Digests from UCSC `hg38.chromFa.tar.gz` (Last-Modified 2014-01-24), chr1-22, X, Y, M concatenated in that order. The concatenation's sha256 is `87b0ea46...b335`, **identical** to the `sha256` in IDC's `hg38canon` request, which says the served CVMFS `hg38canon.fa` has that checksum, so these digests should be the ones the PR script would produce for it. Aliases copied from the real `all_fasta` row in `cvmfs_20260715.yml`. The 980 MB tarball was deleted after use. |
| `idc_pr88_json_sacCer3.json` | Same method from UCSC `sacCer3.fa.gz` in UCSC's file order (chrI..chrXVI, chrM). **Not verified** against the CVMFS `sacCer3.fa`: if that file orders or names sequences differently, `level_0`, `names`, `sequences` and `name_length_pairs` would differ (the sorted digests would not). |
| `idc_pr88_yaml_all_fasta.yml` | The two records above in the PR #88 `yaml/all_fasta.yml` layout. |
| `{hg38,sacCer3,GCF_000001405.40,GCF_000146045.2}.len` | Lines `chrom<TAB>len` written from the real `/api/genomes/{id}` responses. Content is real, but **order is the API's natural sort**, not the served `.len` order. |
| `dm_fetch_genome_all_fasta_{hg38canon,sacCer3}.data_manager_json` | Hand-written in the shape the fetch data manager writes (`all_fasta` entry with relative path), values from the real `.loc` rows. |
| `idc_request_all_fasta_sacCer3.yaml` | Hand-written request modelled on `hg38canon.yaml`; no such file in the IDC repo; no sha256. |
| `idc_request_all_fasta_GCF_000001405.40.from_docs.yaml` | Copied verbatim from IDC `docs/genome-indexing.md`; the maintainers' illustrative example, not a filed request. |

The digest code (`make/seqcol.py`, `make/hg38canon.py`) reproduces the
published phiX174 level 0 and level 1 digests exactly.

## Gaps

- No real data manager JSON, request file, or seqcol summary exists for the
  anchors except the IDC `hg38canon` requests; the rest are in
  `constructed/`.
- The CVMFS `.loc` and `.len` files themselves were not read (CVMFS is not
  mounted here); `.loc` rows come from PR #88's parsed YAML and `.len`
  content from the API.
- `/api/tool_data/{table}/fields/{value}` (file list with full paths) needs
  an admin key (403 for anonymous).
- `galaxy_refgenie_table` has no real records; its fields have no example.
- PR #88's `*_perdbkey.yml` (fasta-centric regrouping) and the RGSI tables are
  described in `spec/idc_pr88/sync/README.md` but not inventoried; RGSI is a
  refget/gtars format.
- Other data tables (hisat2, picard, twobit, kraken, ...) follow the same
  `.loc` pattern but are not inventoried. The `galaxy_api_tool_data` and
  `galaxy_idc_all_tables` adapters pass their columns through unchanged,
  so those keys are not in `fields.json`.
