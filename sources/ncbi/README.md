# NCBI assembly metadata

**What it is.** NCBI (National Center for Biotechnology Information, U.S.
National Library of Medicine) runs the GenBank and RefSeq assembly
databases. It describes each genome assembly in two places:

- **NCBI Datasets v2**: a REST API (`https://api.ncbi.nlm.nih.gov/datasets/v2`)
  and CLI. It serves JSON "data reports" for an assembly and for each of its
  sequences. Downloaded data packages hold the same reports as JSON Lines.
- **The genomes FTP site** (`https://ftp.ncbi.nlm.nih.gov/genomes/`): plain
  text files in each assembly's directory (`*_assembly_report.txt`,
  `md5checksums.txt`, ...) and the big `assembly_summary_*.txt` tables.

Both are maintained by NCBI. All files here were retrieved on **2026-11-17**.

**Levels covered:** assembly (strong), sequence (strong; this is the best name
map across naming styles), collection (implicitly, through assembly units and
GenBank/RefSeq differences; no seqcol digests), copy (FTP paths and file
checksums), deployment (only the UCSC synonym and BLAST URL). Per-sequence
MD5 digests exist only in the GRCh38 analysis-set FASTA headers.

## Formats

| Format id | One record is | Identified by | Examples |
|---|---|---|---|
| `ncbi_datasets_assembly_report` | one assembly version (JSON, nested objects flattened to dotted paths) | `accession` | 7 |
| `ncbi_datasets_sequence_report` | one top-level sequence (JSON) | `assembly_accession` + `sequence_name` | 4 |
| `ncbi_assembly_report_header` | header block of `*_assembly_report.txt` | the accession in the file name | 5 |
| `ncbi_assembly_report_sequences` | one row of the `*_assembly_report.txt` table | `Sequence-Name` within the assembly | 5 |
| `ncbi_assembly_summary` | one row of `assembly_summary_{refseq,genbank}[_historical].txt` | `assembly_accession` | 4 |
| `ncbi_md5checksums` | one file in an assembly FTP directory | `file` within the directory | 5 |
| `ncbi_uncompressed_checksums` | one file, after decompression | `file` within the directory | 4 |
| `ncbi_analysis_set_defline` | one sequence of a GRCh38 analysis-set FASTA | `name`, or `AC` / `M5` | 1 |

All eight have adapters in `tools/refmeta/formats/ncbi.py` (read, write,
detect). `fields.json` lists 281 fields. For the Datasets assembly report it
lists every leaf of the OpenAPI schema (175 paths). 64 of those never appear
in the example records; they have `example: null` and say so in `notes`.
Every other field has a real example value.

**Native record keys.**
- Datasets: snake_case paths as the REST API serves them (`assembly_info.assembly_name`).
  Data packages use camelCase JSON Lines (`assemblyInfo.assemblyName`). The adapter
  converts them, so both read to the same record. Arrays stay whole at their path
  (for example `assembly_info.bioproject_lineage`).
- FTP tables: the column names exactly as in the file (`Sequence-Name`, `UCSC-style-name`, `asm_name`).
- `md5checksums.txt` has no header line. The keys `file` and `md5sum` are borrowed
  from `uncompressed_checksums.txt`.
- In the analysis-set deflines, the key `name` (the text after `>`) was chosen by refmeta.
  The other keys are NCBI's tags (`AC`, `LN`, `M5`, ...).

**`required`** in `fields.json` means "always present in records NCBI serves".
The OpenAPI schema marks nothing as required, so this was judged from the spec
text and the examples.

## Where every file came from (all retrieved 2026-11-17)

### spec/

| File | Source | How excerpted |
|---|---|---|
| `datasets_v2_openapi_genome_reports.excerpt.yaml` | https://www.ncbi.nlm.nih.gov/datasets/docs/v2/openapi3/openapi3.docs.yaml (570 KB) | Only the two GET endpoints `/genome/accession/{accessions}/dataset_report` and `/genome/accession/{accession}/sequence_reports`, plus every component schema they reference (60 schemas). Full file in `a local download folder (not in this repository)spec/`. |
| `datasets_docs_genome_assembly_report.md` | https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/ | HTML converted to text (tags stripped). Field tables include the `dataformat` mnemonics. |
| `datasets_docs_genome_sequence_report.md` | https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-sequence/ | Same as above. |
| `datasets_docs_dataformat_tsv_genome.md` | https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/dataformat/tsv/dataformat_tsv_genome/ | Same as above. Lists every TSV column of `dataformat tsv genome`. |
| `datasets_docs_dataformat_tsv_genome-seq.md` | https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/dataformat/tsv/dataformat_tsv_genome-seq/ | Same as above. |
| `ftp_genomes_all_README.txt` | https://ftp.ncbi.nlm.nih.gov/genomes/all/README.txt | Verbatim. Describes the per-assembly files (`*_assembly_report.txt`, `md5checksums.txt`, `assembly_status.txt`, ...). |
| `ftp_README_assembly_summary.txt` | https://ftp.ncbi.nlm.nih.gov/genomes/README_assembly_summary.txt | Verbatim. Defines the assembly_summary columns. |
| `ftp_GRCh38_README_analysis_sets.txt` | https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/README_analysis_sets.txt | Verbatim. |

`uncompressed_checksums.txt` has no spec. The README does not mention it, so its
columns come from the file's own header line (`#file md5sum crc32 size`).

### examples/

Base URLs: `API=https://api.ncbi.nlm.nih.gov/datasets/v2`,
`FTP=https://ftp.ncbi.nlm.nih.gov/genomes`.

| File(s) | URL | Notes |
|---|---|---|
| `datasets_dataset_report_GCF_000001405.40.json`, `..._GCF_000146045.2.json`, `..._GCA_000146045.2.json` | `API/genome/accession/<acc>/dataset_report` | As served. |
| `datasets_dataset_report_GCA_000001405.15.json`, `..._GCA_000001405.29.json`, `..._GCF_000001405.26.json` | `API/genome/accession/<acc>/dataset_report?filters.assembly_version=all_assemblies` | Without the filter, the API answers `{}` for GCA_000001405.15 because it is no longer the current version. `.29` and `.26` are the GenBank/RefSeq partners of `.40` and `.15`. |
| `datasets_dataset_report_GCF_009914755.1.json` | `API/genome/accession/GCF_009914755.1/dataset_report` | Not an anchor. T2T-CHM13v2.0, added for field coverage (BioSample, sequencing_tech, assembly_method, genome_coverage, isolate, sex). |
| `datasets_sequence_report_<acc>.json` for GCF_000001405.40, GCA_000001405.15, GCF_000146045.2, GCA_000146045.2 | `API/genome/accession/<acc>/sequence_reports?page_size=1000` | As served. All rows fit on one page. |
| `ftp_<acc>_<name>_assembly_report.txt` (4 anchors + CHM13) | `FTP/all/GCx/NNN/NNN/NNN/<acc>_<name>/<acc>_<name>_assembly_report.txt` | Verbatim (CRLF line endings). |
| `ftp_assembly_summary_refseq.anchors.txt` | `FTP/ASSEMBLY_REPORTS/assembly_summary_refseq.txt` (255 MB) | First 2 header lines + rows GCF_000001405.40, GCF_000146045.2. |
| `ftp_assembly_summary_genbank.anchors.txt` | `FTP/ASSEMBLY_REPORTS/assembly_summary_genbank.txt` (1.8 GB) | Header + GCA_000001405.29, GCA_000146045.2. |
| `ftp_assembly_summary_genbank_historical.anchors.txt` | `FTP/ASSEMBLY_REPORTS/assembly_summary_genbank_historical.txt` | Header + GCA_000001405.15 (replaced, so not in the current file). |
| `ftp_assembly_summary_refseq_historical.anchors.txt` | `FTP/ASSEMBLY_REPORTS/assembly_summary_refseq_historical.txt` | Header + GCF_000001405.26. |
| `ftp_GCF_000146045.2_R64_md5checksums.txt`, `ftp_GCA_000146045.2_R64_md5checksums.txt` | `<assembly dir>/md5checksums.txt` | Verbatim. |
| `ftp_GCF_000001405.40_GRCh38.p14_md5checksums.toplevel.txt`, `ftp_GCA_000001405.15_GRCh38_md5checksums.toplevel.txt` | same | Kept only lines for files at the top of the directory. Dropped the ~1,350 `assembly_structure/`, RNA-seq and annotation-comparison lines. |
| `ftp_GCA_000001405.15_GRCh38_analysis_set_md5checksums.txt` | `FTP/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/md5checksums.txt` | Verbatim. |
| `ftp_*_uncompressed_checksums.txt` (yeast), `ftp_*_uncompressed_checksums.toplevel.txt` (human) | `<assembly dir>/uncompressed_checksums.txt` | Yeast verbatim. Human: header + top-level files only. |
| `ftp_GCA_000001405.15_GRCh38_full_analysis_set.deflines.txt` | `.../seqs_for_alignment_pipelines.ucsc_ids/GCA_000001405.15_GRCh38_full_analysis_set.fna.gz` (861 MB) | Streamed and decompressed; kept only the 456 `>` lines. No sequence. |

Nothing under `examples/` was written by hand (there is no `constructed/` folder).

Raw downloads (2.1 GB, mostly the summary tables) are in
a local download folder (not in this repository). That folder also holds the FTP directory listings,
`assembly_stats.txt`, `assembly_status.txt` and the analysis-set `.fai` files,
which are not used here.

## RefSeq vs GenBank pairing

Every NCBI assembly has a GenBank accession (`GCA_`, the submitter's INSDC
record). Many also have a RefSeq accession (`GCF_`, NCBI's curated copy). The
number is shared, but **pairing is between specific versions, and the version
numbers need not match**:

| GenBank | RefSeq | Name | Same sequences? |
|---|---|---|---|
| GCA_000001405.15 | GCF_000001405.26 | GRCh38 (2013, no patches) | identical |
| GCA_000001405.29 | GCF_000001405.40 | GRCh38.p14 (2022) | different: RefSeq dropped 4 scaffolds (KI270752.1, KI270825.1, KI270721.1, KI270734.1) |
| GCA_000146045.2 | GCF_000146045.2 | R64 (sacCer3) | different: RefSeq adds chromosome MT (NC_001224.1) |

So "GRCh38" is at least four accessions. The anchor pair
GCA_000001405.15 / GCF_000001405.40 from the project README is **not** a
NCBI pair; each has a different partner. The pairing appears in
`paired_accession` (Datasets), `gbrs_paired_asm` (assembly_summary) and the two
accession lines of the FTP report header.

## GRCh38 analysis sets

NCBI publishes "analysis set" FASTAs for alignment pipelines under
`GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/`. They are
built from **GCA_000001405.15** (GRCh38 without patches) and are **not the same
sequence collection as the assembly**:

- They use UCSC-style names (chr1, chrUn_KI270302v1, chr1_KI270762v1_alt).
- They add chrEBV (Epstein-Barr virus, AJ507799.2), which is not part of the assembly.
- They hard-mask the chrY PARs and duplicate centromeric arrays on chr5, 14,
  19, 21 and 22 with N. Those sequences keep their coordinates but differ from
  the INSDC records.
- Four variants: `no_alt` (195 sequences: chromosomes, chrM, unlocalized,
  unplaced, chrEBV), `full` (adds the 261 alt scaffolds: 456 in total), and
  `no_alt_plus_hs38d1` / `full_plus_hs38d1` (add the hs38d1 decoys from GCA_000786075.2).
- Each FASTA header carries `AC:` (GenBank accession), `LN:` (length), `M5:`
  (MD5 of the uppercase sequence, the same MD5 refget and SAM @SQ M5 use),
  `rl:` (role), `rg:` (placement), `hm:` (masked spans) and `tp:circular`.

The M5 of a masked sequence is the MD5 of the masked analysis-set sequence. It
is not the MD5 of the GenBank record named in `AC`. Treat each analysis set as
its own collection derived from the assembly. This is the "copy vs collection"
split the refmeta levels are meant to capture.

## Quirks that matter for mapping

**Identity and versions**
- **One accession = one exact sequence set, but names are not unique.**
  `assembly_name` / `asm_name` are not unique (NCBI says so). `synonym` (hg38,
  sacCer3) is UCSC's name, and NCBI puts it on all four GRCh38 accessions. It
  is a cross-reference to UCSC, not an identifier. T2T-CHM13 has no synonym,
  although UCSC calls it hs1.
- **Status vocabularies differ.** Datasets `assembly_status` uses current /
  previous / suppressed. assembly_summary `version_status` uses latest /
  replaced / suppressed. `assembly_status.txt` uses `status=latest|replaced`.
  Replaced versions appear only in the `_historical` summary files. The
  Datasets API returns them only with `filters.assembly_version=all_assemblies`.
- **BioProject differs by source for the same assembly.** For human:
  PRJNA31257 (GenBank / Datasets) vs PRJNA168 (RefSeq rows, and the FTP header
  of GCA_000001405.15). For yeast: PRJNA43747 vs PRJNA128.
- **The GCA_ and GCF_ copies of the FTP assembly report are nearly identical.**
  Both list both accessions. For yeast R64 the only difference is the `Date`
  line. Which record a file describes is known only from its file name or
  directory.
- **Dates are per accession version.** GCA_000146045.2 is 2011-04-18 and
  GCF_000146045.2 is 2014-12-17, for the same R64 sequences.

**Sequence names and rows**
- **Sequence name styles in one row.** `sequence_name` / `Sequence-Name` is
  the submitter's name ('1', 'MT', 'HSCHR1_CTG1_UNLOCALIZED'). `ucsc_style_name`
  / `UCSC-style-name` is UCSC's name. It exists only when UCSC has the
  assembly: for fission yeast GCF_000002945.2, Datasets leaves the field out
  and the FTP table writes `na` on every row. `genbank_accession` and `refseq_accession` are the INSDC and
  RefSeq names. Ensembl-style names equal `sequence_name` for chromosomes, but
  Ensembl uses accessions for scaffolds (KI270706.1), not the submitter's name.
- **Unplaced scaffolds look different in the two sources.** Datasets says
  `chr_name: "Un"`, `assigned_molecule_location_type: "Chromosome"`,
  `sort_order: 9999`. The FTP table says `na` / `na`.
- **Row counts differ.** For GCF_000001405.40, the FTP report has 709 rows (it
  keeps the 4 GenBank-only scaffolds with `RefSeq-Accn` = `na` and
  `Relationship` = `<>`). The Datasets sequence report has 705 rows.
  `total_count` in a sequence-report page (191, 194) does not equal the number
  of rows returned (705, 455). Count the rows.
- **Yeast MT** is only in the RefSeq assembly. The FTP report shows
  `GenBank-Accn` = `na`, but Datasets gives `genbank_accession` KP263414.1
  (also in `additional_submitters`).
- **Patch scaffolds.** In `UCSC-style-name`, fix patches end in `_fix`
  (chr1_KN196472v1_fix) and novel patches end in `_alt` (chr1_KQ458382v1_alt),
  the same suffix as true alt loci. The analysis-set README describes a
  `_patch` suffix instead.

**Values and spellings**
- **Role vocabularies differ.** The assembly report uses `assembled-molecule`,
  `unlocalized-scaffold`, ... Analysis-set deflines use `Chromosome`,
  `unlocalized`, `alt-scaffold`, `decoy`.
- **Case and spelling.** `refseq_category` is 'reference genome' (Datasets,
  summary) but 'Reference Genome' (FTP header). `organism_name` is
  'Homo sapiens' in Datasets and the summary, but 'Homo sapiens (human)' in the
  FTP header. `assembly_level` is served as 'Complete Genome' / 'Chromosome',
  although the OpenAPI enum lists `complete_genome` / `chromosome`. Strain is
  'S288C' in Datasets and 'strain=S288C' in the FTP files.
- **Taxon level.** Yeast S288C `taxid` is 559292 (strain) and `species_taxid`
  is 4932. Only the summary has `species_taxid`.
- **Totals depend on which sequences count.** `genome_size` and
  `total_sequence_length` count primary-assembly top-level sequences only, so
  they differ between GRCh38.p14 RefSeq (3099441038) and GenBank (3099734149).
  `replicon_count` (24) excludes MT.
- **64-bit numbers as strings.** Datasets serializes `total_sequence_length`,
  `gc_count` and similar fields as JSON strings ("3099441038").

**File details**
- **Line endings.** FTP assembly reports use CRLF. `Synonyms` has a trailing
  tab (`hg38<TAB>`).
- **Header layouts differ.** Older reports (GCA_000001405.15) have an
  `## Assembly-Units:` table with GenBank/RefSeq unit accessions (for example
  Primary Assembly = GCA_000001305.2 / GCF_000001305.14). Newer ones only list
  `## Assembly-Unit names:`. Optional header lines (Isolate, Sex, BioSample,
  Assembly method, Genome coverage, Sequencing technology, Expected final
  version) appear only for some assemblies, and their value alignment is not
  fixed.
- **assembly_summary** says "37 columns" but defines 38. `pubmed_id` is
  separated by `;`, not by commas as the README says. `gc_percent` has 6
  decimals. Missing values are the string `na`; the adapter keeps them as
  strings.
- **Checksums.** `md5checksums.txt` hashes the files as served (gzipped).
  `uncompressed_checksums.txt` hashes the decompressed files and gives byte
  size and CRC-32. Neither is a sequence digest.

## Reuse terms

NCBI's policy page (https://www.ncbi.nlm.nih.gov/home/about/policies/,
retrieved 2026-11-17) says: "Information that is created by or for the US
government on this site is within the public domain" and, for molecular
databases, "NCBI itself places no restrictions on the use or distribution of
the data contained therein". It adds that original submitters may claim
rights in some data. The documentation and schema files in `spec/` are NCBI
works, so they are public domain under that policy.
