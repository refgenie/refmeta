# refgenie

refgenie is our own reference genome manager. It is maintained by the Sheffield
lab at the University of Virginia (GitHub org `refgenie`). All of its code is
BSD-2-Clause. This folder covers the four places where refgenie writes down
genome metadata:

1. **Registry genome YAML.** One file per genome in `refgenie-registry/genomes/`.
   This is the curated source of truth.
2. **Store build table.** `refgenie-registry/stores/<store>/sources.csv` lists the
   FASTA files that each RefgetStore loads.
3. **refgenie 1.x server API.** The JSON records that api.refgenie.org serves,
   which are built from the refgenie database (`refgenie/db/tables.py`).
4. **Legacy refgenie 0.x `genome_config.yaml`.** The old config format, read by
   refgenconf. Galaxy still reads it through its `refgenie` tool data table type.

The FHR sidecars (`<seqcol digest>.fhr.json`) belong to the **fhr** source. See
the pointers at the end of this file.

## Formats

| Format id | What one record is | Media type |
|---|---|---|
| `refgenie_registry_genome` | One registry genome YAML (one named sequence collection) | application/yaml |
| `refgenie_store_sources` | One row of a store's `sources.csv` (one FASTA, which becomes one collection) | text/csv |
| `refgenie_api_genome` | `GET /v4/genomes/{digest}`: DB columns, species, and the FHR block | application/json |
| `refgenie_api_genome_list` | One item of `GET /v4/genomes?...` `results`, which includes every alias of the genome | application/json |
| `refgenie_api_alias` | `GET /v4/aliases/{name}`: digest, seqcol level-2 arrays, and FHR | application/json |
| `refgenie_api_sequences` | One sequence row of `GET /v4/genomes/{digest}/sequences`, with the collection fields repeated on each row | application/json |
| `refgenie_genome_config` | One genome/asset/tag of a legacy `genome_config.yaml`, or of refgenieserver 0.x `/_private_api/genomes/dict` | application/yaml |

All seven formats have an adapter in `tools/refmeta/formats/refgenie.py`, with
read, write and detect. `fields.json` lists all 205 fields. Every non-null
`example` in it is a real value taken from the files in `examples/`. A null
example means that no collected record sets the field, and its `notes` say so.

### How records are flattened

These rules apply to every format, so they matter when mapping.

- Nested objects become dotted keys, such as `organism.taxon_id` and `fhr.taxon.uri`.
- An array of objects becomes parallel lists, one list per member. For example,
  `fasta.sources` becomes `fasta.sources[].provider` and `fasta.sources[].url`.
  A missing member is `None` at that position.
- Null values are dropped. A missing key means "not given".
- `refgenie_api_sequences`: each record is one element of `sequences[]`. The row
  fields keep their own names (`name`, `length`, `sha512t24u`, `md5`,
  `alphabet`, `description`, `aliases[].*`). The collection fields (`digest`,
  `n_sequences`, `total_length`, `level1.*`, `collection_aliases[].*`) are
  copied onto every row.
- `refgenie_genome_config`: the file is keyed by data (genome digest, then
  asset name, then tag name), so those levels appear as placeholders in the
  path: `genomes.{genome}.assets.{asset}.tags.{tag}.seek_keys`. The key that is
  exactly the placeholder path holds the map key itself. For example,
  `genomes.{genome}` is `"2230c535…"`. The top-level keys (`config_version`,
  `genome_folder`, …) are repeated on every record. `seek_keys` and `remotes`
  are kept as whole objects because their keys vary.
- YAML dates come back as ISO strings.

## Where every file came from (all retrieved 2026-11-17)

Local repos are clones under the maintainers' local clones. None of the
copied paths had uncommitted changes.

| Repo | Commit | GitHub |
|---|---|---|
| refgenie-registry | `1647661d1a953d55ff0ead7e37824c0b932e6698` | https://github.com/refgenie/refgenie-registry |
| refgenie (1.x) | `7d0ee7fa69f9ddfd739b4f8875dda8b4b78e125d` | https://github.com/refgenie/refgenie |
| refgenconf | `1cc4257943bbc8107a44635875892622f468addf` | https://github.com/refgenie/refgenconf |
| refgenomes.databio.org | `904d2a5a82c2ee44190af6615a18e450c577a96e` (2021-05-17) | https://github.com/refgenie/refgenomes.databio.org |

### spec/

| File | Source |
|---|---|
| `registry/genome.schema.yaml` | refgenie-registry `schema/genome.schema.yaml` (verbatim) |
| `registry/schema_README.md` | refgenie-registry `schema/README.md` (verbatim; includes the YAML-to-FHR table and the registry/FHR boundary) |
| `registry/CONTRIBUTING_adding_a_genome.md` | refgenie-registry `CONTRIBUTING.md`, lines 1-162 ("Adding a Genome") |
| `registry/genome_to_fhr.py.txt` | refgenie-registry `tools/genome_to_fhr.py` (verbatim; saved as .txt; the executable YAML-to-FHR mapping) |
| `stores/sources_schema.json` | refgenie-registry `stores/sources_schema.json` (verbatim) |
| `stores/stores_README.md` | refgenie-registry `stores/README.md` (verbatim; aliases, FHR build, species.json) |
| `api/openapi.json` | https://api.refgenie.org/openapi.json (refgenieserver API 1.0.0a3; full, verbatim) |
| `api/tables_genome_excerpt.py.txt` | refgenie `refgenie/db/tables.py` lines 134-243 (Genome, Alias, Species tables) |
| `api/genome_manager_apply_fhr_excerpt.py.txt` | refgenie `refgenie/managers/genome.py` lines 206-300 (how FHR keys land in DB columns) |
| `legacy/genome_config.md` | refgenie `docs/site/legacy/genome_config.md` (verbatim; the 0.x config docs and changelog) |
| `legacy/refgenconf_const_excerpt.py.txt` | refgenconf `refgenconf/const.py` lines 107-330 (config key names, `CONF_STRUCTURE` template) |
| `legacy/refgenieserver_0.8.0_openapi.json` | http://refgenomes.databio.org/openapi.json (legacy refgenieserver 0.8.0; verbatim) |
| `legacy/galaxy_RefgenieToolDataTable_excerpt.py.txt` | https://raw.githubusercontent.com/galaxyproject/galaxy/dev/lib/galaxy/tools/data/__init__.py at `d3e1f13ab44c4714a6a6e063dbdddd503cce75f5`, lines 1-26 and 43-182 (third-party consumer; Galaxy is MIT-licensed since 2026-02-25) |

The legacy genome config has no machine-readable schema. refgenconf validates
it in code, and the docs page plus `const.py` are the spec.

### examples/

Anchor genomes: hg38 (GRCh38, `EiFob05aCWgVU_B_Ae0cypnQut3cxUP1`), R64-1-1
(Ensembl naming, `ia9g4Myony-xxLsSc7eQOC_NdClGgPGu`), and sacCer3 (UCSC naming
via iGenomes, `8zSJ7M2oerPcCKc8x310hjyfB5u8SJNJ`). R64-1-1 and sacCer3 are the
same 17 yeast sequences in the same order with different names, so they have
different collection digests. A few non-anchor real records were added only to
give real values for rare fields. Those rows are marked "non-anchor".

| File | Source and excerpt method |
|---|---|
| `registry_genome_hg38.yaml` | refgenie-registry `genomes/human/hg38.yaml` (verbatim) |
| `registry_genome_R64-1-1.yaml` | `genomes/yeast/R64-1-1.yaml` (verbatim) |
| `registry_genome_sacCer3.yaml` | `genomes/yeast/sacCer3.yaml` (verbatim) |
| `registry_genome_t2t-chm13.yaml` | `genomes/human/t2t-chm13.yaml` (verbatim; non-anchor; has `metadata.last_verified`) |
| `registry_genome_rAllMis1.yaml` | `genomes/vertebrates/rAllMis1.yaml` (verbatim; non-anchor; has an `fhr:` block and `seqcol.compute`) |
| `store_sources_legacy_hg38.csv` | `stores/legacy/sources.csv`: header + the `hg38.fa.gz` row |
| `store_sources_plantcore_R64-1-1.csv` | `stores/plantcore/sources.csv`: header + the `R64-1-1` row |
| `store_sources_igenomes_anchors.csv` | `stores/igenomes/sources.csv`: header + the rows for Homo_sapiens NCBI/GRCh38 and UCSC/hg38, and S. cerevisiae Ensembl/R64-1-1, NCBI/build3.1 and UCSC/sacCer3 |
| `store_sources_jungle_hg38.csv` | `stores/jungle/sources.csv`: header + 7 GRCh38 rows (ENA, Broad, Ensembl primary, hs38, hg38-refgenie) |
| `store_sources_vrs_GRCh38.csv` | `stores/vrs/sources.csv`: header + the GCF_000001405.26 and .40 rows (has the extra column `assembly_report`) |
| `store_sources_salmon_txomes_GRCh38.csv` | `stores/salmon_txomes/sources.csv`: header + the GENCODE 49 human row (has `version`, `gtf`, `sha256`) |
| `store_sources_pangenome_HG002.csv` | `stores/pangenome/sources.csv`: header + the first HG002 row (non-anchor; has `population`) |
| `api_genome_hg38_EiFob….json`, `api_genome_R64-1-1_ia9g….json`, `api_genome_sacCer3_8zSJ….json` | `https://api.refgenie.org/v4/genomes/{digest}` (verbatim response bodies) |
| `api_genome_rAllMis1_hb4Y….json` | same endpoint, non-anchor (FHR `dateCreated`, `identifier`) |
| `api_genomes_list_alias_hg38.json`, `api_genomes_list_alias_R64-1-1.json` | `https://api.refgenie.org/v4/genomes?alias={hg38,R64-1-1}` (verbatim) |
| `api_alias_hg38.json`, `api_alias_R64-1-1.json`, `api_alias_sacCer3.json` | `https://api.refgenie.org/v4/aliases/{name}` (verbatim) |
| `api_alias_rAllMis1.json` | same endpoint, non-anchor |
| `api_sequences_hg38_….json`, `api_sequences_R64-1-1_….json`, `api_sequences_sacCer3_….json` | `https://api.refgenie.org/v4/genomes/{digest}/sequences` (verbatim) |
| `legacy_genome_config_refgenomes.databio.org_hg38.yaml` | refgenomes.databio.org `config/refgenie_config_archive.yaml` (the 2021 public server's archive config). Lines 1-12 (top-level keys and `remotes`), 126-458 (the hg38 genome, all 18 assets), and 3108-3109 (the trailing top-level keys), verbatim. |
| `legacy_server_genomes_dict_hg38.json` | `http://refgenomes.databio.org/_private_api/genomes/dict` (live legacy server). This is the hg38 entry only, re-serialized as compact JSON with the values unchanged. |

Raw downloads, including the full legacy genomes dict, the alias listings, the
legacy asset attrs, and the Galaxy source, are in
a local download folder (not in this repository).

**Not available:** the legacy 0.x server never hosted a yeast genome, so there
is no real `genome_config` record for R64-1-1 or sacCer3. I did not write a
constructed one, because its 48-hex legacy digest cannot be made up honestly.
There is no `examples/constructed/` folder.

## What identifies a record

- **Registry YAML**: `name`. It is unique in the registry and equals the file
  stem. `seqcol.digest` is the global content identifier.
- **sources.csv**: `fasta`, which is unique within one store. `name` should equal
  the genome YAML `name` when the row has a YAML.
- **API genome, genome list, and sequences**: `digest`, which is the GA4GH seqcol
  top-level digest. Sequence rows are identified by `digest` + `name`.
- **API alias**: `alias`. Each alias resolves to exactly one digest on the server.
- **Legacy config**: genome map key + asset + tag. In config 0.4 the genome key
  is the legacy 48-hex refgenie digest.

## Levels covered

| Level | Where |
|---|---|
| assembly | `organism.*`, `assembly.accession`/`level` (YAML); `organism`, `genome_assembly`, `accession` (CSV); `species_name`, `taxon_id`, `assembly_accession`, `assembly_level`, `species.*`, `fhr.taxon.*`, `fhr.accessionID.*` (API) |
| collection | `name`, `aliases`, `seqcol.*` (YAML); `name`, `source`, `synonyms` (CSV); `digest`, `synonyms`, `aliases`, `level1.*`, `collection_aliases` (API); `genomes.{genome}` and its aliases (legacy) |
| sequence | `collection.names`/`lengths`/`sequences` (alias API); sequence rows with name, length, sha512t24u, md5, and refseq/insdc aliases (sequences API) |
| copy | `fasta.sources[].url`, `fasta.checksum.*` (YAML); `fasta` (CSV); `remote_url` (API); `asset_path`, `seek_keys`, `asset_digest`, `archive_digest`, sizes (legacy) |
| deployment | `build.*` (YAML); `refget_store_url`, `asset_count` (API); `genome_folder`, `genome_servers`, `remotes`, asset/tag names (legacy) |

## Quirks that matter for mapping

1. **A refgenie "genome" is a sequence collection, not an assembly.** `hg38`
   here is the NCBI no-alt analysis set with UCSC names. Its alias `GRCh38` points
   at that one collection, not at the GRCh38 assembly. Several registry genomes
   share one accession (hg38, hg38_full_analysis and
   hg38_full_analysis_plus_decoy all cite GCA_000001405.15). Many other GRCh38
   flavors (Ensembl, GENCODE, Broad) set no accession at all.
   `assembly.accession` and `assembly_accession` therefore do not identify a
   record.
2. **Two different "genome digests".** refgenie 1.x uses the GA4GH seqcol digest
   (32 base64url characters, for example `EiFob05aCWgVU_B_Ae0cypnQut3cxUP1`).
   Legacy 0.x uses a 48-hex truncated-SHA-512 digest (`2230c535…` for hg38).
   The legacy digest is computed over (whole FASTA header line, length, sequence
   digest) without uppercasing, so the same sequences under a different FASTA
   description get a different legacy digest. The two digests are not
   convertible without the FASTA.
3. **`assembly.source` / `assembly_source` / `assemblySource` / CSV `source`
   name the provider of this sequence set, not the assembler.** sacCer3 says
   UCSC and R64-1-1 says Ensembl for the same S288C assembly. Case is not
   normalized (`ncbi` from a store override vs `NCBI` in the YAML).
4. **Names differ across the same sequences.** The yeast rows are named `I`/`Mito`
   in R64-1-1 and `chrI`/`chrM` in sacCer3. `level1.lengths`, `level1.sequences`
   and `level1.sorted_sequences` match between them, while `level1.names` and
   the top-level digest do not.
5. **Sequence digest prefix.** The alias API's `collection.sequences` has the
   `SQ.` prefix. The sequences API's `sha512t24u` does not.
6. **Aliases vs synonyms.** `synonyms` (API) and `genomeSynonym` (FHR) are only
   the names the FHR record lists. The full alias set is in the genome listing's
   `aliases` (hg38 has 7). `collection_aliases` in the sequences response lists
   only the serving store's aliases, with namespaces `name` and
   `genome_assembly`. `species.synonyms` are names of the species, not of the
   genome.
7. **sources.csv columns are uneven.** `genome_assembly` mixes assembly names
   (GRCh38, R64-1-1), UCSC builds (hg38, sacCer3), and iGenomes folder labels.
   The igenomes NCBI `build3.1` row is labeled `R64-1-1`. `accession` is a claim
   that the alias builder checks against NCBI. `sha256` in salmon_txomes is a
   "legacy Salmon index hash", not a FASTA checksum. `synonyms` is one
   `;`-separated string. `fasta` can be several space-separated URLs that are
   concatenated.
8. **Checksums.** `fasta.checksum.sha256` is of the uncompressed FASTA, and
   `fasta.checksum.md5` is of the compressed file. Every registry YAML uses the
   sentinel `compute_on_registration`, so no real SHA-256 is recorded yet.
   `fasta.sources[]` URLs are upstream URLs. The store ingests a different
   string (staged path) for the same content.
9. **Served records can lag or differ from the registry.** hg38's API
   description and `relatedLink` come from a store-level override
   (`stores/jungle/genomes/hs38.yaml`), not from `genomes/human/hg38.yaml`. The
   API's sacCer3 description is shorter than the current YAML. hg38's YAML says
   `build.store: legacy`, but the API serves it from the `jungle` store.
10. **Galaxy reading the legacy config**: dbkey = the genome's first alias,
    value = `refgenie:{alias}/{asset}:{tag}@{asset_digest}`, and path = the
    asset folder (via `rgc.seek`). The fasta asset's `seek_keys.fasta` is the
    FASTA file, relative to `asset_path`.
11. **Sequence `description`** (sequences API) is the raw FASTA defline text. In
    the NCBI analysis set it carries tags such as `AC:` (INSDC accession), `rl:`
    (role: Chromosome, unlocalized, unplaced, decoy), `rg:` (parent chromosome),
    and `M5:` (md5). refgenie does not parse them.

## Pointers (owned by other sources)

- FHR sidecars per collection:
  `https://refgenie.s3.us-east-1.amazonaws.com/refget-store/<store>/fhr/<digest>.fhr.json`,
  for example `jungle/fhr/EiFob05aCWgVU_B_Ae0cypnQut3cxUP1.fhr.json` and
  `plantcore/fhr/ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.fhr.json` (both return HTTP 200).
  They are generated by `tools/genome_to_fhr.py` and `stores/build_fhr.py`.
  Per-store FHR override YAMLs are in `stores/<store>/genomes/<row>.yaml`
  (flat camelCase FHR keys). The same FHR record appears as the `fhr` block in
  the API formats here. See `sources/fhr`.
- `species.json` (store root) and `tools/taxon_ids.json`: the species name list
  behind `species.*` and `common_name`.

## Reuse terms

The refgenie-registry, refgenie, refgenconf and refgenomes.databio.org repos are
BSD-2-Clause (Sheffield lab / Nathan Sheffield). The vendored FHR schema in
refgenie-registry comes from FAIR-bioHeaders. The Galaxy excerpt is under
Galaxy's MIT license (Galaxy's LICENSE.txt on the dev branch). The API responses are public data from
api.refgenie.org and refgenomes.databio.org.
