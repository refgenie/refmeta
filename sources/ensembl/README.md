# Ensembl

Ensembl is a genome database run by EMBL-EBI (Hinxton, UK). It loads an
INSDC assembly, annotates genes on it, and serves the result through a
website, a REST API, MySQL databases and an FTP site.

In 2026 Ensembl runs two systems side by side, and both matter for mapping:

- **Legacy release system** (numbered releases; this folder uses release 116,
  dated 2026-04-04). Metadata lives in each species' *core* MySQL database
  (the `meta` key/value table plus `seq_region` tables), in a release-wide
  `ensembl_metadata` database, and on `ftp.ensembl.org/pub/release-116/`.
  REST at `rest.ensembl.org` serves it. The old website docs now redirect to
  `jun2026.archive.ensembl.org`.
- **New Ensembl** (`www.ensembl.org`; `beta.ensembl.org` now redirects there).
  Each genome (one assembly + one gene annotation) has a **genome UUID**. The
  metadata lives in a new `ensembl_genome_metadata` database, defined by the
  SQLAlchemy models in
  [Ensembl/ensembl-metadata-api](https://github.com/Ensembl/ensembl-metadata-api)
  and served by `www.ensembl.org/api/metadata/...`
  ([Ensembl/ensembl-web-metadata-api](https://github.com/Ensembl/ensembl-web-metadata-api)).
  Files sit on `ftp.ebi.ac.uk/pub/ensemblorganisms/`, organised by assembly
  accession, then provider, then genebuild date.

All files here were retrieved on **2026-11-17**.

## Formats

| Format id | What | Adapter | Record key |
|---|---|---|---|
| `ensembl_rest_info_assembly` | REST `/info/assembly/:species`, assembly-level keys | yes | `assembly_accession` (species is only in the URL) |
| `ensembl_rest_toplevel_region` | the `top_level_region` rows of that same response, one per sequence, with `synonyms` | yes | `name` within the response |
| `ensembl_rest_info_assembly_region` | REST `/info/assembly/:species/:region_name`, one sequence | yes | none in the body (the URL holds species + region) |
| `ensembl_rest_info_genomes` | REST `/info/genomes/:name` (same object from `/info/genomes/assembly/:accession`) | yes | `name` (production name) or `assembly_accession` |
| `ensembl_core_meta` | core DB `meta` table dump (`meta.txt`) | yes | `species.production_name` + database name |
| `ensembl_species_list` | `species_EnsemblVertebrates.txt` | yes | `species`; `core_db` |
| `ensembl_fasta_header` | genomic FASTA header lines, both FTP styles | yes | `id` within one file |
| `ensembl_chromosomes_tsv` | new FTP `genome/chromosomes.tsv.gz` | yes | `name` within one file |
| `ensembl_web_genome` | new API `/genome/{id}/details`, `/explain`, `/api/search/genomes`, `/genomeid` | yes | `genome_id` (UUID); `genome_tag` |
| `ensembl_web_karyotype` | new API `/genome/{id}/karyotype` (and `/top-regions`) | yes | `name` within the genome |
| `ensembl_web_genome_stats` | new API `/genome/{id}/stats` | yes | genome_id in the URL |
| `ensembl_web_ftplinks` | new API `/genome/{id}/ftplinks` | yes | `url` |
| `ensembl_ftp_species_json` | new FTP `species.json` catalog | yes | species key + assembly accession |
| `ensembl_web_region_checksum` | new API `/genome/{id}/checksum/{region}` (text/plain MD5) | no | URL only |
| `ensembl_core_seq_region` | core DB sequence tables (needs a join) | no | `seq_region.name` + coord system |
| `ensembl_genome_metadata_db` | new metadata DB model (genome / assembly / assembly_sequence / sequence_alias / organism) | no | `genome_uuid`, `assembly_uuid`, `organism_uuid` |

Adapter: `tools/refmeta/formats/ensembl.py`. Nested JSON from the new API is
flattened with `.` (`assembly.accession_id`). In `species.json` the map keys
are data, so paths use `{species}` and `{accession}` placeholders; a field
whose path ends in a placeholder holds that key.

## Levels covered

- **assembly**: accession (GCA only), name, date, level, provider, taxon IDs,
  scientific/common name, strain, BioSample, UCSC name (`assembly_ucsc`,
  `assembly.ucsc_alias`).
- **collection**: karyotype name list, total lengths (`golden_path`,
  `base_count`, `total_genome_length`). There is no seqcol digest and no named
  "sequence set" concept; the FASTA files (`toplevel`, `primary_assembly`,
  `alt`, ensemblorganisms `unmasked`) are the de facto collections.
- **sequence**: Ensembl name, length, coord system, circular flag,
  reference/non-reference, synonyms (INSDC, UCSC, RefSeq_genomic), MD5 and
  refget `sha512t24u` digests (core `seq_region_attrib`; MD5 also from the
  new API `/checksum`).
- **copy**: FASTA header type (`dna`, `unmasked`), new FTP paths and dataset
  URLs. No file checksums are in the records (the FTP has `CHECKSUMS` and
  `md5sum.txt` files; not inventoried).
- **deployment**: production name, URL name, division, display name, species
  aliases, release ids, website sample links, genome UUID and tag.
- **other**: gene annotation (genebuild) keys, schema bookkeeping, statistics.

## Files

### spec/

| File | From |
|---|---|
| `rest_info_assembly.md` | https://rest.ensembl.org/documentation/info/assembly_info (HTML to text; client code samples removed) |
| `rest_info_assembly_region.md` | https://rest.ensembl.org/documentation/info/assembly_stats (same treatment) |
| `rest_info_genomes.md` | https://rest.ensembl.org/documentation/info/info_genome |
| `rest_info_genomes_assembly.md` | https://rest.ensembl.org/documentation/info/info_genomes_assembly |
| `core_schema_doc_excerpt.md` | https://www.ensembl.org/info/docs/api/core/core_schema.html, which redirects to https://jun2026.archive.ensembl.org/info/docs/api/core/core_schema.html. HTML to text; kept only tables meta, coord_system, seq_region, seq_region_synonym, seq_region_attrib, attrib_type, assembly_exception, karyotype, external_db, dna; removed the per-table species lists. |
| `core_schema_116_excerpt.sql` | `CREATE TABLE` statements for the same tables, from https://ftp.ensembl.org/pub/release-116/mysql/homo_sapiens_core_116_38/homo_sapiens_core_116_38.sql.gz |
| `ensembl_production_116_meta_key.tsv` | Controlled vocabulary of meta keys (name, is_optional, db_type, description, ...): https://ftp.ensembl.org/pub/release-116/mysql/ensembl_production_116/meta_key.txt.gz, header row added from `ensembl_production_116.sql.gz` |
| `ensembl_production_116_meta_key_mvp.tsv` | Same for the new site ("mvp") keys: `.../ensembl_production_116/meta_key_mvp.txt.gz` |
| `ftp_release116_README.txt` | https://ftp.ensembl.org/pub/release-116/README |
| `ftp_release116_fasta_dna_README.txt` | https://ftp.ensembl.org/pub/release-116/fasta/homo_sapiens/dna/README (file naming, toplevel vs primary_assembly) |
| `ftp_ensemblorganisms_README.md` | https://ftp.ebi.ac.uk/pub/ensemblorganisms/README.md (new FTP layout) |
| `ensembl_metadata_api/*.py.txt`, `README.md` | SQLAlchemy models `assembly.py`, `genome.py`, `organism.py`, `dataset.py`, `release.py` and README from https://raw.githubusercontent.com/Ensembl/ensembl-metadata-api/main/ (path `src/ensembl/production/metadata/api/models/`). Saved as `.py.txt`: kept as data, never run. |
| `ensembl_web_metadata_api/APISpecification.yaml` | OpenAPI spec of the new metadata API: https://raw.githubusercontent.com/Ensembl/ensembl-web-metadata-api/main/docs/APISpecification.yaml |

### examples/

All are unmodified responses or files unless noted.

| File(s) | From |
|---|---|
| `rest_info_assembly_{homo_sapiens,saccharomyces_cerevisiae}.json` | `https://rest.ensembl.org/info/assembly/<species>?content-type=application/json;synonyms=1` |
| `rest_info_assembly_region_<species>_<region>.json` | `https://rest.ensembl.org/info/assembly/<species>/<region>?content-type=application/json;synonyms=1` for human 1, MT, KI270728.1 (unplaced), HG76_PATCH (fix patch), HSCHR6_MHC_SSTO_CTG1 (alt haplotype); yeast I, Mito |
| `rest_info_genomes_<species>.json` | `https://rest.ensembl.org/info/genomes/<species>?content-type=application/json` |
| `core_meta_homo_sapiens_core_116_38.txt`, `core_meta_saccharomyces_cerevisiae_core_63_116_4.txt` | `https://ftp.ensembl.org/pub/release-116/mysql/<db>/meta.txt.gz`, decompressed, complete |
| `species_EnsemblVertebrates_release116_excerpt.txt` | https://ftp.ensembl.org/pub/release-116/species_EnsemblVertebrates.txt (359 genomes). **Excerpt**: header, first 3 rows, and the human, mouse and yeast rows, unchanged. |
| `fasta_headers_Homo_sapiens.GRCh38.dna.toplevel.txt` | All 706 `>` lines of https://ftp.ensembl.org/pub/release-116/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.toplevel.fa.gz (streamed through `zcat \| grep '>'`; trailing spaces kept) |
| `fasta_headers_Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.txt` | All 17 `>` lines of `.../fasta/saccharomyces_cerevisiae/dna/Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.fa.gz` |
| `fasta_headers_ftp_GCA_000146045.2_unmasked.txt` | All 17 `>` lines of https://ftp.ebi.ac.uk/pub/ensemblorganisms/GCA/000/146/045/2/community/2018_10/genome/unmasked.fa.bgz |
| `fasta_headers_ftp_GCA_000001405.29_unmasked_sample.txt` | **Sample** of 12 of the 706 `>` lines of https://ftp.ebi.ac.uk/pub/ensemblorganisms/GCA/000/001/405/29/ensembl/2026_04/genome/unmasked.fa.bgz, fetched with HTTP range requests using the published `.fai` and `.gzi` indexes (the EBI FTP timed out on a full pass). Lines are copied exactly, in `.fai` order. |
| `ftp_chromosomes_GCA_000001405.29.tsv`, `ftp_chromosomes_GCA_000146045.2.tsv` | `genome/chromosomes.tsv.gz` in the same two ensemblorganisms directories, decompressed |
| `ftp_species_json_excerpt.json` | https://ftp.ebi.ac.uk/pub/ensemblorganisms/species.json (59 MB, 17,048 species keys). **Excerpt**: `last_updated`, plus `species.Homo_sapiens` reduced to its `GCA_000001405.29` assembly entry, plus `species.Saccharomyces_cerevisiae_S288C` whole. Nothing else changed. |
| `web_genomeid_<acc>.json` | `https://www.ensembl.org/api/metadata/genomeid?assembly_accession_id=<acc>` |
| `web_explain_<acc>.json`, `web_details_<acc>.json`, `web_stats_<acc>.json`, `web_karyotype_<acc>.json`, `web_ftplinks_<acc>.json` | `https://www.ensembl.org/api/metadata/genome/<uuid>/{explain,details,stats,karyotype,ftplinks}`; human uuid 59871324-7803-4234-856e-2a2bd96d7b3c, yeast a733574a-93e7-11ec-a39d-005056b38ce3 |
| `web_search_<acc>.json` | `https://www.ensembl.org/api/search/genomes?query=GRCh38` and `?query=R64-1-1` |
| `web_checksum_responses_<acc>.json` | **Assembled by us**: the text/plain bodies of `https://www.ensembl.org/api/metadata/genome/<uuid>/checksum/<region>` for every karyotype region, gathered into one JSON object (`responses`: region -> body). The bodies are unchanged; the wrapper is ours. |
| `derived/core_toplevel_seq_regions_<db>.tsv` | **Derived by us** (not an Ensembl format): one row per toplevel `seq_region` (LRG coord system excluded), joining the release-116 dumps `seq_region`, `coord_system`, `seq_region_attrib` + `attrib_type` (codes toplevel, md5_toplevel, sha512t24u_toplevel, karyotype_rank, non_ref, circular_seq, sequence_location) and `seq_region_synonym` + `external_db` from `https://ftp.ensembl.org/pub/release-116/mysql/<db>/`. Synonyms written as `db_name:synonym`, `;`-separated. |

No hand-written (constructed) records were needed.

Raw downloads (full dumps, FASTA headers, species.json, docs HTML) are in
a local download folder (not in this repository).

## Not covered

- `species_metadata_EnsemblVertebrates.json` on the release FTP is 2.5 GB
  (the legacy metadata DB with every sequence name); not downloaded. REST
  `/info/genomes/:name?expand=1` returns the same per-genome object, mostly
  annotation/compara/variation counts; not inventoried.
- REST `bands=1` (cytogenetic bands), `/info/genomes/division|taxonomy` lists.
- The legacy `ensembl_metadata_116` database dump (tables `genome`,
  `assembly`, `assembly_sequence`, `organism`, `organism_alias`), which feeds
  REST `/info/genomes`.
- New API `/dataset/{type}/attributes` (works for `genebuild`, returned HTTP 500
  for `assembly`), `/example_objects`, `/vep/file_paths`.
- cDNA / peptide FASTA headers (they carry gene and transcript fields, not
  genome metadata).
- The FTP `CHECKSUMS` / `md5sum.txt` file checksums.

## Quirks that matter for mapping

1. **Ensembl names sequences its own way.** Human `1`, `X`, `MT`; yeast
   `I`..`XVI`, `Mito`; unplaced scaffolds by INSDC accession (`KI270728.1`);
   alt haplotypes and patches by GRC scaffold names (`HSCHR6_MHC_SSTO_CTG1`,
   `HG76_PATCH`). UCSC (`chr1`, `chr6_GL000256v2_alt`), INSDC (`CM000663.2`)
   and RefSeq (`NC_000001.11`) names come only as `synonyms`. When the
   Ensembl name already is the INSDC accession, there is no INSDC synonym.
   Yeast has only INSDC synonyms: no UCSC (sacCer3) or RefSeq names.
2. **Accession version.** Ensembl human is `GCA_000001405.29` (GRCh38.p14),
   not `GCA_000001405.15`. REST `/info/genomes/assembly/GCA_000001405.15` and
   the new API both say "not found". No GCF (RefSeq) accessions anywhere.
   Sequence digests let you match sequences across sources regardless
   (chr1 MD5 2648ae1bacce4ec4b6cf337dcae37816, sha512t24u
   2YnepKM7OkBoOrKmvHbGqguVfF9amCST).
3. **Three different "assembly names".** `assembly_name` / `assembly.name` =
   `GRCh38.p14`; `assembly.default` / `default_coord_system_version` = `GRCh38`
   (used in FASTA headers, file names, and confusingly in the
   `assembly_name` key of `/info/assembly/:species/:region`);
   `assembly.long_name` = "Genome Reference Consortium Human Build 38".
4. **Three different sequence sets for one assembly.** REST `top_level_region`
   lists 194 human sequences (primary assembly: 25 chromosomes + 169
   unplaced/unlocalised); the toplevel FASTA has 706 (adds 512 alt/patch
   scaffolds); the core DB has 2030 toplevel regions (adds 1324 LRGs). Totals:
   `golden_path` 3,099,750,718 (the 194), FASTA 3,291,585,349 (the 706),
   `base_count` 3,398,673,745 (all 2030, LRGs included). The new API
   `total_genome_length` 3,298,912,062 and `toplevel_sequences` 709 match none
   of these; unexplained. New-site `karyotype` and `chromosomes.tsv` list only
   the 25 / 17 karyotype sequences.
5. **FASTA header styles differ.** Release FTP: `>1 dna:chromosome chromosome:GRCh38:1:1:248956422:1 REF`.
   ensemblorganisms FTP: `>1 unmasked:chromosome GRCh38:1:1:248956422:1`
   (no coord system inside the location, no `REF`). Alt/patch scaffolds end
   with an empty fourth token (a trailing space) in both styles. That empty
   token lines up exactly with the core `non_ref` seq_region attribute (512
   human scaffolds); in release 116 alt/patch sequences are scaffolds, not
   N-padded chromosomes (the FASTA README still describes padding). ensemblorganisms
   files sort sequences by length (yeast IV first); release files use karyotype order.
6. **Same key, different spelling or type across endpoints.**
   `coord_system` (top_level_region) vs `coordinate_system` (region endpoint);
   taxonomy IDs are integers in REST, strings in the new API;
   `annotation_provider` is an object in `/details` but a string in search
   results; `is_circular` is 0/1 in REST but boolean in the new API.
7. **Circularity is inconsistent.** Human MT: not circular everywhere (no
   `circular_seq` attribute). Yeast Mito: circular in legacy REST and core,
   not circular in the new API karyotype.
8. **Assembly level and division disagree.** Yeast is `chromosome` in REST
   but `complete genome` in the new API. Yeast is `EnsemblVertebrates` in
   REST and the species list, but `species.division = EnsemblFungi` in its
   core meta table. Its database is listed as
   `saccharomyces_cerevisiae_core_116_4` but dumped on FTP as
   `saccharomyces_cerevisiae_core_63_116_4`.
9. **Taxonomy at two ranks.** `taxonomy_id` can be strain level (yeast
   559292) while `species_taxonomy_id` is species level (4932).
10. **Genome UUID identifies assembly + annotation**, not the assembly alone.
    The new-site search returns one genome for GRCh38; per the `genome`
    model (assembly + organism + genebuild fields), a new gene build would be
    a new genome row with a new UUID (not observed directly). The
    yeast UUID is time-based (v1), human is random (v4). The model declares
    `genome_uuid` as String(32) though the values have 36 characters.
    `genome_tag` (= the GCA accession here) is a readable alias.
11. **species.json species-level fields describe one genome only.**
    `species.Homo_sapiens` has strain HG03540 and BioSample SAMN17861670 (a
    pangenome sample), yet it holds 563 assemblies including GRCh38. Read
    taxonomy from it, not strain or BioSample.
12. **Release numbers.** Legacy: release 116 (`schema_version` 116,
    `data_release_id` 80 is an internal row id). New site: date labels
    (`release.name` 2026-07); FTP directory dates are genebuild dates
    (`2026_04`), and `species.json` lists four genebuilds for GRCh38 but only
    the latest genome directory.
13. **Meta table encoding.** One row per value; repeated keys
    (`species.alias`, `species.classification`, `assembly.mapping`, `patch`)
    hold lists. Values are text with MySQL escaping (`\N` = NULL, `\\n` = a
    literal backslash-n). Rows with species_id NULL are database-wide.
14. **Digests.** The core DB stores MD5 and GA4GH `sha512t24u` per toplevel
    sequence (`md5_toplevel`, `sha512t24u_toplevel` attributes, no `SQ.`
    prefix). These are standard refget digests of the uppercase sequence: for
    human MT we hashed the release-116 FASTA and got the same two values. The
    new API `/checksum/{region}` returns the same MD5 (checked for all 25 human
    and 17 yeast karyotype regions). The new metadata model has `md5` and
    `sha512t24u` columns on `assembly_sequence` and a `sequence_alias` table;
    the public API exposes only the MD5, one region per call.

## Reuse terms

Ensembl disclaimer (https://jun2026.archive.ensembl.org/info/about/legal/disclaimer.html):
"Ensembl imposes no restrictions on access to, or use of, the data provided
and the software used to analyse and present it." Ensembl code is Apache 2.0;
ensembl-metadata-api and ensembl-web-metadata-api are Apache-2.0 on GitHub.
