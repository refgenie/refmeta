# nf-core and AWS iGenomes

**What it is.** How nf-core Nextflow pipelines name and find reference genomes.
There are three layers:

1. **AWS iGenomes**: an S3 mirror (`s3://ngi-igenomes/igenomes/`, ~5 TB, public)
   of Illumina's iGenomes bundles, unpacked in April 2016, with extra STAR,
   Bismark and BED12 files and GATK bundles added later. It was set up by Phil
   Ewels (SciLifeLab NGI) and is now kept by nf-core. The folder layout is the
   schema: `igenomes/<species>/<source>/<build>/<Sequence|Annotation>/<asset>/...`.
2. **`conf/igenomes.config`**: a Groovy `params.genomes` map shipped in every
   nf-core pipeline (from the nf-core/tools template). Each key (`GRCh38`,
   `hg38`, `R64-1-1`, ...) is a `--genome` value and maps to paths under
   `${params.igenomes_base}`. Each pipeline adds its own keys.
3. **nf-core/references** (in progress): a pipeline that builds reference assets
   from YAML "datasheets", plus the `nf-core/references-datasheets` repo of
   published datasheets (one per genome). These describe both iGenomes builds and
   newer `s3://nf-core-references` builds. Maintainer: Maxime U. Garcia
   (`@maxulysse`). The schema lives in `subworkflows/local/utils_references/`, which
   its README calls a proof of concept that "can be deleted at any moment".

Maintainers: the nf-core community (MIT-licensed repos). The data itself comes
from Illumina iGenomes, GATK resource bundles and the Mouse Genome Project.

## Formats

| Format id | What | One record is | Record key | Adapter |
|---|---|---|---|---|
| `nfcore_igenomes_config` | Groovy `params.genomes` map | one genome key | `genome` (map key), unique per pipeline | read, write, detect |
| `nfcore_references_datasheet` | nf-core/references datasheet YAML | one list entry | `species` + `reference_source` + `genome` | read, write, detect |
| `nfcore_igenomes_manifest` | AWS iGenomes file list | one S3 file | `uri` | read, write, detect |
| `nfcore_igenomes_genomesize` | Illumina `GenomeSize.xml` | one `<chromosome>` | `contigName` within a file | read, write, detect |
| `nfcore_igenomes_dict` | `genome.dict` (SAM `@HD`/`@SQ` header) | one `@SQ` line | `SN` within a file | read, write, detect |
| `nfcore_igenomes_fai` | `genome.fa.fai` (htslib faidx) | one sequence | `NAME` within a file | read, write, detect |
| `nfcore_igenomes_readme` | `Annotation/README.txt` | one file (prose) | its path | none (prose) |

Adapter notes:

- **Config parser.** The adapter has its own small parser for the plain map
  syntax only. It handles both forms seen in real pipelines: the map literal
  `params.genomes = [ 'KEY' : [ k : "v", ... ] ]` (template, rnaseq, sarek) and
  the block form `params { genomes { 'KEY' { k = "v" } } }` (methylseq, atacseq,
  chipseq, AWS-iGenomes example). The map key is stored as `genome`.
  `${params.igenomes_base}` and `${projectDir}` are kept as written, not
  expanded. Nested maps (atacseq `macs_gsize` per read length) become dotted
  keys (`macs_gsize.50`). `write` always uses the map literal form with double
  quotes, so it does not keep comments or the block syntax.
- **Datasheet.** Read with `yaml.safe_load`. YAML comments (e.g.
  `# macs_gsize: 1.2e7`) are lost on write.
- **Manifest.** The native line is only `uri`. The adapter also splits it into
  `species`, `source`, `build`, `section` and `subpath` along the iGenomes layout.
- **GenomeSize / dict.** Values from the file header (`genomeName`, `@HD/VN`,
  `@HD/SO`) are copied onto every per-sequence record.
- **dict and fai are generic formats** (SAM spec, htslib), documented here as
  files that iGenomes serves for every build. Other sources may document the
  same formats.

## Levels covered

- **assembly**: only weakly. There is a species name (`species`, `vep_species`,
  `SP`) but no assembly accession, except the free-text `annotation_version` /
  `reference_version` (GCF accessions) in a few datasheets and the `site` URL.
- **collection**: build names (`genome`, manifest `build`), providers
  (`reference_source`, manifest `source`), GenomeSize `genomeName`, dict `AS`.
  There are no collection digests.
- **sequence**: names, lengths, MD5s (GenomeSize `md5`, dict `M5`), non-N
  counts (`knownBases`), roles (GenomeSize `type`, `mito_name`).
- **copy**: almost everything else, such as paths to the FASTA, `.fai`, `.dict`,
  index folders, line width (`LINEBASES`) and where a dict was built (`UR`).
- **deployment**: the `--genome` key, tool settings (`snpeff_db`,
  `vep_cache_version`, `vep_genome`, `ascat_genome`, `macs_gsize`,
  `star_legacy`, `*_vqsr`, STAR build parameters).
- **other**: gene annotation and variant resource files (GTF, BED12, VCFs,
  blacklists, model files) that sit next to a genome.

## Quirks that matter for mapping

- **One key, different builds.** `GRCh38` means the iGenomes **NCBI/GRCh38**
  build in rnaseq, methylseq, atacseq and the template. sarek has no plain
  `GRCh38`; it uses `NCBI.GRCh38` and `GATK.GRCh38` (the Broad
  `Homo_sapiens_assembly38.fasta`, 3,366 sequences, including alts and HLA).
  `hg38` is iGenomes UCSC/hg38 everywhere. A `--genome` value only identifies a
  build inside one pipeline version.
- **iGenomes NCBI/GRCh38 uses UCSC-style names.** It has `chr1`...`chrM`,
  `chrEBV`, and 195 sequences, with exactly the same names as iGenomes UCSC/hg38.
  So `mito_name` is `chrM` for both `GRCh38` and `hg38`, while Ensembl builds
  use `MT`. The provider name in the path does not tell you the naming style.
- **Same names, different MD5s.** iGenomes NCBI/GRCh38 and UCSC/hg38 have the
  same 195 names and lengths, and the same `knownBases`, but 14 sequences have
  a different MD5 (chr1, chr2, chr3, chr6, chr7, chr9, chr10, chr12, chr13,
  chr16, chr17, chr21, chr22, chrX). The cause is not known. NCBI/GRCh38 MD5s
  match the GATK dict for all 195 shared names. Yeast Ensembl R64-1-1 and UCSC
  sacCer3 have identical MD5s (only names differ: `I` vs `chrI`, `MT` vs `chrM`).
  Check MD5s before treating these builds as the same collection.
- **Placeholder values in GenomeSize.xml.** `isCircular` is `false` and
  `ploidy` is `2` for every sequence, including chrM and haploid yeast. Only
  NCBI/GRCh38 has `build`, `species` and `type` attributes. `genomeName` is
  free text with uneven capitals ("Homo Sapiens (NCBI GRCh38)" vs "Homo sapiens
  (UCSC hg38)").
- **`UR` in dicts is the build machine's path**, e.g.
  `file:C:\Genomes\Homo_sapiens\NCBI\GRCh38\...`,
  `file:/illumina/scratch/iGenomes/...`, or
  `/seq/references/Homo_sapiens_assembly38/v0/...` (Broad). It is not where
  the file lives now.
- **Line width varies by copy.** It is 70 for NCBI/GRCh38, 50 for UCSC/hg38,
  100 for GATK GRCh38, 60 for R64-1-1 and 50 for sacCer3, so the `.fai` offsets
  differ between copies.
- **Same file, different names.** The FASTA index is `fasta_fai` (sarek,
  datasheets) or `fasta_index` (methylseq). The dict is `dict` (sarek) or
  `fasta_dict` (datasheets). The BWA index is `bwa` (configs) or
  `bwamem1_index` (datasheets). Genes BED12 is `bed12` (configs, schema) or
  `genes_bed` (igenomes/ datasheets). The MSIsensor-pro list is
  `msisensorpro_scan` (sarek) or `msisensorpro_list` (schema). Index fields
  end in `_index` in datasheets but are bare tool names in configs.
- **Datasheet keys outside the schema.** The igenomes/ datasheets use many
  keys that `schema_references.json` does not define (`genes_bed`,
  `genome_size_xml`, `chromosomes_fasta`, `bismark_index`, `hairpin_fasta`,
  ...). The pipeline ignores these with a warning. They are marked in
  `fields.json` notes.
- **Schema renames.** The older main-branch `schema_input.json` used `source`,
  `source_version`, `source_vcf` and `vcf`. The dev schema uses
  `reference_source`, `annotation_version` and per-kind `vcf_<kind>_vcf[_tbi|_vqsr|_source]`.
  One legacy example is kept.
- **Values that look like errors in published sheets.** These should be checked,
  not trusted:
  - The NCBI GRCh38.p14 and Gencode GRCh38.p14 source sheets say `mito_name: MT`,
    but their FASTAs (NCBI analysis set, Gencode primary assembly) are believed
    to use `chrM`.
  - The Gencode sheet has `annotation_version: GCF_000001405.40` and an NCBI
    `site` URL.
  - `genomes/Homo_sapiens/GATK/GRCh38_chr22.yml` (human) has
    `snpeff_db: WBcel235.105` and `vep_species: caenorhabditis_elegans`.
- **`annotation_version` holds assembly accessions** (GCF_...) in real sheets,
  not annotation release numbers.
- **Brace globs and lists.** sarek `known_indels` packs two files into one
  string with a brace glob (`{a,b}.vcf.gz`). Datasheets use a YAML list for
  the same thing.
- **`macs_gsize` has two shapes.** It is a quoted string (`"2.7e9"`) in
  rnaseq, methylseq and the template, and a map keyed by read length with
  integer values in atacseq and chipseq. It is a tool setting, not an identifier.
- **Annotations are old.** Per the nf-core docs, human iGenomes annotation is
  from Ensembl release 75. The AWS-iGenomes example config points `fasta` at
  the WholeGenomeFasta folder, not the file.
- **Path placeholders.** Configs use `${params.igenomes_base}` (default
  `s3://ngi-igenomes/igenomes`). Datasheets use `${params.references_base_path}`
  (same default), and `genomes_source/` sheets use absolute upstream URLs.
  `blacklist` uses `${projectDir}` (inside the pipeline).

## Files and where they came from

Everything was retrieved on **2026-11-17**. Raw downloads, including full
files that were cut down here, are in a local download folder (not in this repository).

### spec/

| File | Source URL (commit) |
|---|---|
| `igenomes_config/nf-core_tools_pipeline-template_igenomes.config` | https://raw.githubusercontent.com/nf-core/tools/main/nf_core/pipeline-template/conf/igenomes.config (eb2f709) |
| `igenomes_config/nf-core_tools_pipeline-template_igenomes_ignored.config` | https://raw.githubusercontent.com/nf-core/tools/main/nf_core/pipeline-template/conf/igenomes_ignored.config (9765f18) |
| `igenomes_config/rnaseq_nextflow_schema_reference_genome_options.json` | excerpt (only `$defs.reference_genome_options`) of https://raw.githubusercontent.com/nf-core/rnaseq/master/nextflow_schema.json (a6a0de0) |
| `references/schema_references.json` | https://raw.githubusercontent.com/nf-core/references/dev/subworkflows/local/utils_references/schema_references.json (dev 4a244d7) |
| `references/utils_references_README.md` | same folder, README.md (dev 4a244d7) |
| `references/schema_input_main_legacy.json` | https://raw.githubusercontent.com/nf-core/references/main/assets/schema_input.json (main 19f92a9; older field names) |
| `references/nf-core_references_README_dev.md`, `references/nf-core_references_usage_dev.md` | nf-core/references dev `README.md`, `docs/usage.md` (4a244d7) |
| `references/references-datasheets_README.md`, `..._path_placeholders_AGENTS.md`, `..._VCFs.md`, `..._LICENSE` | https://github.com/nf-core/references-datasheets branch `latest` (e82856f): `README.md`, `AGENTS.md` (the placeholder rules), `docs/VCFs.md`, `LICENSE` |
| `aws_igenomes/AWS-iGenomes_README.md`, `AWS-iGenomes_LICENSE` | https://github.com/ewels/AWS-iGenomes master (1066c8c) |
| `nfcore_docs/reference-genomes.md` | https://raw.githubusercontent.com/nf-core/website/main/sites/docs/src/content/docs/running/reference-genomes.md (b6970a7) |
| `nfcore_docs/ReferencesExtension.md` | nf-core/website `sites/docs/src/content/docs/nf-core-tools/nf-core-utils/ReferencesExtension.md` (49da83a; copied from nf-core-utils 0.6.0) |
| `hts_formats/htslib_faidx.5` | https://raw.githubusercontent.com/samtools/htslib/develop/faidx.5 (9cd85ab) |
| `hts_formats/SAMv1_header_SQ_excerpt.tex` | lines 270-320 and 379-400 (the `@SQ` tag table and the MD5 rules) of https://raw.githubusercontent.com/samtools/hts-specs/master/SAMv1.tex (b5341fb) |

### examples/

All records are real files, served as shown. None are made up, and there is no
`examples/constructed/`.

| File | Source | How it was cut down |
|---|---|---|
| `igenomes_config_rnaseq_anchors.config` | nf-core/rnaseq master `conf/igenomes.config` (bbf987b) | Header plus the entries `GRCh38`, `CHM13`, `hg38`, `R64-1-1`, `sacCer3`, copied word for word. CHM13 is kept because it is the only entry with `gff` and `bwamem2`. |
| `igenomes_config_sarek_anchors.config` | nf-core/sarek master `conf/igenomes.config` (8419980) | Entries `GATK.GRCh38`, `NCBI.GRCh38`, `hg38`, `R64-1-1`, `sacCer3`. |
| `igenomes_config_methylseq_anchors.config` | nf-core/methylseq master (e03bc46) | Entries `GRCh38`, `hg38`, `R64-1-1`, `sacCer3` (block syntax). |
| `igenomes_config_atacseq_anchors.config` | nf-core/atacseq master (b743e10; chipseq is the same file) | Entries `GRCh38`, `hg38`, `R64-1-1`, `sacCer3` (block syntax, `macs_gsize` per read length). |
| `igenomes_config_aws-igenomes_example_R64-1-1.config` | ewels/AWS-iGenomes master `nextflow.config` (1066c8c) | Entry `R64-1-1` only. This file has no GRCh38 or hg38 entry. |
| `datasheet_igenomes_{NCBI_GRCh38,UCSC_hg38,GATK_GRCh38,GATK_hg38,Ensembl_R64-1-1,UCSC_sacCer3}.yml` | nf-core/references-datasheets `latest` (e82856f) `igenomes/<source>/<build>.yml` | Whole files. |
| `datasheet_genomes_source_{NCBI,Gencode}_GRCh38.p14.yml` | same repo, `genomes_source/Homo_sapiens/{NCBI,Gencode}/GRCh38.p14.yml` | Whole files. |
| `datasheet_genomes_nf-core_GRCh38_chr21.yml`, `datasheet_genomes_GATK_GRCh38_chr22.yml` | same repo, `genomes/Homo_sapiens/...` (built assets in `s3://nf-core-references`) | Whole files. These are GRCh38 subsets (test data). |
| `datasheet_genomes_source_nf-core_GRCh38_chr22.yml`, `..._GRCh38_chr21_star_params.yml` | same repo, `genomes_source/Homo_sapiens/nf-core/` | Whole files. |
| `datasheet_igenomes_GATK_GRCh37decoy.yml` | same repo, `igenomes/GATK/GRCh37decoy.yml` | Whole file. Not an anchor build; kept because it is the only real record with `vcf_hapmap_vcf_source`. |
| `datasheet_nonanchor_genomes_NCBI_WBcel235.yml` | same repo, `genomes/Caenorhabditis_elegans/NCBI/WBcel235.yml` | Whole file. Not an anchor (worm); it is the only real record with `hisat2_index`, `kallisto_index`, `rsem_index`, `salmon_index` and `msisensorpro_list`. |
| `datasheet_nonanchor_genomes_source_NCBI_mm39.yml` | same repo, `genomes_source/Mus_musculus/NCBI/mm39.yml` | Whole file. Not an anchor (mouse); it is the only real record with `reference_version`. |
| `datasheet_legacy_nf-core_references_main_test_default_extended.yml` | nf-core/references main `assets/test/default_extended.yml` (19f92a9) | Whole file. GRCh38 chr21 test sheet using the old field names. |
| `igenomes_manifest_anchors_excerpt.txt` | https://raw.githubusercontent.com/ewels/AWS-iGenomes/master/ngi-igenomes_file_manifest.txt (1066c8c; 21,588 lines, 2.2 MB) | Only lines under `Homo_sapiens/{NCBI/GRCh38,UCSC/hg38,GATK/GRCh38,GATK/hg38}` and `Saccharomyces_cerevisiae/{Ensembl/R64-1-1,UCSC/sacCer3}`. Of the 2,829 `GATK/GRCh38/Annotation/MSIsensor2/models_hg38/*` lines, only the first 3 are kept. 924 lines in all. |
| `igenomes_GenomeSize_<species>_<source>_<build>.xml` | `https://ngi-igenomes.s3.amazonaws.com/igenomes/<species>/<source>/<build>/Sequence/WholeGenomeFasta/GenomeSize.xml` (S3 Last-Modified April 2017) | Whole files. |
| `igenomes_dict_<...>.dict`, `igenomes_fai_<...>.fa.fai` | the same folder's `genome.dict` and `genome.fa.fai`. For GATK GRCh38: `Homo_sapiens/GATK/GRCh38/Sequence/WholeGenomeFasta/Homo_sapiens_assembly38.{dict,fasta.fai}` (Last-Modified 2018-11-16) | Whole files. |
| `igenomes_README_Saccharomyces_cerevisiae_UCSC_sacCer3_Annotation.txt` | `https://ngi-igenomes.s3.amazonaws.com/igenomes/Saccharomyces_cerevisiae/UCSC/sacCer3/Annotation/README.txt` | Whole file. There is no `Annotation/README.txt` for NCBI/GRCh38, UCSC/hg38 or Ensembl/R64-1-1 (S3 returns 404). |
| `local/aws_igenomes_manifest_20260721_excerpt.txt` | `aws_igenomes_manifest_20260721.txt`, a lab-local capture of a refgenie-built copy of AWS iGenomes, not an nf-core file | Header, plus only the human and yeast alias lines and alias-to-asset lines. The digest sections are left out. It shows how the lab mapped iGenomes paths to refgenie aliases (`<species>-<source>-<build>`, all lowercase, e.g. `homo_sapiens-ncbi-grch38`). It belongs to no format. |

## Reuse terms

- nf-core/tools, rnaseq, sarek, methylseq, atacseq, references, website and
  references-datasheets are MIT licensed (GitHub license metadata, 2026-11-17).
- ewels/AWS-iGenomes is MIT (Copyright 2017 Phil Ewels).
- htslib `faidx.5` has an MIT-style permission notice (Genome Research Ltd).
- No license statement was found for hts-specs (SAMv1.tex) or for the iGenomes
  data files themselves. The AWS-iGenomes README credits Illumina for the
  original data.
