# ga4gh: GA4GH standards that carry reference genome metadata

This folder covers the standards that describe a reference genome by its
**sequences**: what each sequence is (digest, length, aliases) and which
sequences, in which order and with which names, make up a set. None of them
describes the assembly as a publication (no assembler, date, or assembly level).

| Standard | Maintainer | What it carries |
|---|---|---|
| Refget **sequence collections** (seqcol) v1.0.0 | GA4GH Large Scale Genomics work stream, refget team (github.com/ga4gh/refget) | A set of named sequences as collated arrays, plus digests that identify the set |
| Refget **sequences** v2.0.0 | same | One sequence: md5 and ga4gh digests, length, aliases with a naming authority |
| **VRS** 2.1.1 `SequenceReference` | GA4GH Genomic Knowledge Standards (github.com/ga4gh/vrs) | A pointer to one sequence by refget accession, used inside every VRS variant |
| **SeqRepo** alias namespaces | biocommons (github.com/biocommons/seqrepo, seqrepo-rest-service) | Every `namespace:alias` known for one sequence; the reference implementation behind VRS tools |
| **SAM** `@SQ` header | samtools / hts-specs team (GA4GH Large Scale Genomics) | Per-sequence name, length, md5, assembly, species, alt names, file URI |
| **VCF** `##contig`, `##reference`, `##assembly` | same | Per-contig name, length, md5, URL; one file-level reference name |

## Formats

| Format id | Records | Level(s) | What identifies a record |
|---|---|---|---|
| `ga4gh_seqcol_level2` | one per collection (JSON object of arrays) | sequence (collated arrays), collection (sorted attributes) | level 0 seqcol digest, computed from `names` + `sequences`; not stored in the object |
| `ga4gh_seqcol_level1` | one per collection (JSON object of digests) | collection | the same level 0 digest, computed from the level 1 `names` and `sequences` digests |
| `ga4gh_refget_metadata` | one per sequence | sequence | `metadata.md5` or `metadata.ga4gh` |
| `ga4gh_seqrepo_metadata` | one per sequence | sequence (+ `added`, deployment) | the `sha512t24u:` / `ga4gh:` entry inside `aliases` |
| `ga4gh_vrs_sequence_reference` | one per SequenceReference object | sequence | `refgetAccession` |
| `ga4gh_sam_header_sq` | one per `@SQ` line | sequence; `AS`, `SP` are assembly; `UR` is copy | `SN` within one header; `M5` globally |
| `ga4gh_vcf_header_contig` | one per `##contig` line | sequence; `assembly`, `species` are assembly; `URL` is copy | `ID` within one header; `md5` or EVA `accession` globally |
| `ga4gh_vcf_header_reference` | one per VCF file | copy or assembly (depends on value); `##assembly` is other | nothing reliable; EVA's `reference.accession` when present |

All eight have adapters in `tools/refmeta/formats/ga4gh.py`. The module also
has `level0_digest()` and `level1_digests()`, which recompute seqcol digests;
they reproduce every served level 1 digest and both anchor top-level digests.

**Levels covered:** sequence (all formats), collection (seqcol; and the ordered
list of `@SQ` or `##contig` lines is itself a collection), copy (SAM `UR`, VCF
`URL` and usually `##reference`), assembly (only free text: SAM `AS`/`SP`, VCF
`assembly`/`species`, EVA's structured `##reference`). Nothing here covers
deployment except SeqRepo's `added` timestamp.

## Anchor genomes

| | Human GRCh38 | Yeast R64 |
|---|---|---|
| seqcol level 2 + level 1 | `EiFob05aCWgVU_B_Ae0cypnQut3cxUP1` (alias `hg38` on api.refgenie.org = GRCh38 no-alt analysis set, 195 sequences, UCSC names) | `ia9g4Myony-xxLsSc7eQOC_NdClGgPGu` (alias `R64-1-1`, Ensembl names I..XVI, Mito; 17 sequences) |
| refget metadata (ENA) | chr1 by `insdc:CM000663.2` and by md5 | chrI by `insdc:BK006935.2` and by md5 |
| SeqRepo metadata | chr1 (`refseq:NC_000001.11`), chrM (`refseq:NC_012920.1`) | not available: the public SeqRepo has no yeast sequences (404 for NC_001133.9, its md5, and its ga4gh id) |
| VRS SequenceReference | chr1, from a real variation-normalizer response; chr7 from the VRS spec examples | hand-written record in `examples/constructed/` (no public VRS service covers yeast) |
| SAM `@SQ` | Broad hg38 `.dict` (full), 1000 Genomes GRCh38 `.dict` (excerpt) | iGenomes Ensembl R64-1-1 `genome.dict` |
| VCF headers | GIAB, 1000 Genomes (2), gnomAD, Broad, dbSNP, ClinVar, Ensembl | EVA release 9, Ensembl Fungi |

## Where every file came from (all retrieved 2026-11-17)

### spec/

| File | Source |
|---|---|
| `refget/seqcol_spec_v1.0.0.md` | `docs/seqcols/README.md` from https://github.com/ga4gh/refget (master @ f90bbdf0b5a6). Byte-identical to the raw.githubusercontent.com copy and to the local clone `repos/refget-ga4gh`. |
| `refget/seqcol_minimal_v1.0.0.json`, `seqcol_extended_v1.0.0.json`, `seqcol_refs_v1.0.0.json`, `schemas_README.md` | `docs/schemas/` in the same repo and commit (also served at https://ga4gh.github.io/refget/schemas/) |
| `refget/sequences_spec_v2.0.0.md` | `docs/sequences/README.md`, same repo and commit |
| `refget/refget-sequences-openapi.yaml` | `docs/sequences/pub/refget-openapi.yaml`, same repo and commit |
| `refget/api.refgenie.org_seqcol_service-info.json` | https://api.refgenie.org/seqcol/service-info (pretty-printed; the schema this deployment actually uses) |
| `seqrepo/README.md`, `seqrepo/design.rst` | https://github.com/biocommons/seqrepo (main), `README.md` and `docs/design.rst` |
| `seqrepo/seqaliasdb_migration_0001-initial.py.txt` | same repo, `src/biocommons/seqrepo/seqaliasdb/_data/migrations/0001-initial.py` (the alias table schema; renamed `.txt` so it is never run) |
| `seqrepo/translate.py.txt` | same repo, `src/biocommons/seqrepo/_internal/translate.py` (DB namespace to API namespace mapping; renamed `.txt`) |
| `seqrepo/seqrepo-rest-service_openapi.json` | https://services.genomicmedlab.org/seqrepo/1/openapi.json (pretty-printed) |
| `vrs/SequenceReference.json`, `vrs/SequenceLocation.json` | https://github.com/ga4gh/vrs tag 2.1.1, `schema/vrs/json/` |
| `vrs/SequenceReference.rst` | same tag, `schema/vrs/def/SequenceReference.rst` |
| `hts-specs/SAMv1_header_SQ_excerpt.tex` | excerpt of `SAMv1.tex`, https://github.com/samtools/hts-specs (master @ 510c107ba89a): the example header, character-set rules, the header tag table (incl. `@SQ`), and the reference MD5 section. Line ranges are in the file's first lines. |
| `hts-specs/VCFv4.5_reference_contig_excerpt.tex` | excerpt of `VCFv4.5.tex`, same commit: example file, meta-information lines, `##assembly`, `##contig`, BCF contig dictionary |
| `hts-specs/VCFv4.3_sv_example_excerpt.tex` | excerpt of `VCFv4.3.tex`, same commit: start of the SV example (`##reference` as a bare name, `##assembly` URL) |

### examples/

| File | Source | Notes |
|---|---|---|
| `seqcol_level2_hg38_EiFob05aCWgVU_B_Ae0cypnQut3cxUP1.json` | https://api.refgenie.org/seqcol/collection/EiFob05aCWgVU_B_Ae0cypnQut3cxUP1?level=2 | as served; digest found via https://api.refgenie.org/v4/aliases/hg38 |
| `seqcol_level1_hg38_EiFob05aCWgVU_B_Ae0cypnQut3cxUP1.json` | same URL with `?level=1` | as served |
| `seqcol_level2_R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.json` | the `collection` object of https://api.refgenie.org/v4/aliases/R64-1-1 | extracted unchanged from the wrapper (the wrapper also holds `alias`, `digest`, `fhr`). The seqcol API (api.refgenie.org/seqcol, seqcolapi.databio.org) does not hold this collection (404), so refgenie's own API was the only live source. |
| `seqcol_level1_R64-1-1_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.json` | the `level1` object of https://api.refgenie.org/v4/genomes/ia9g4Myony-xxLsSc7eQOC_NdClGgPGu/sequences | extracted unchanged |
| `refget_metadata_ENA_insdc_CM000663.2.json`, `refget_metadata_ENA_md5_6aef897c3d6ff0c78aff06ac189178dd.json` | https://www.ebi.ac.uk/ena/cram/sequence/insdc:CM000663.2/metadata and `.../6aef897c3d6ff0c78aff06ac189178dd/metadata` | human chr1. ENA answers 406 to `Accept: application/json` and to the spec's `application/vnd.ga4gh.refget.v2.0.0+json`; `Accept: */*` works. |
| `refget_metadata_ENA_insdc_BK006935.2.json`, `refget_metadata_ENA_md5_6681ac2f62509cfc220d78751b8dc524.json` | same server, yeast chrI | |
| `refget_metadata_spec_example_chr1.json` | **spec example**, JSON body of the example in `spec/refget/sequences_spec_v2.0.0.md` | the only example with a non-null `ga4gh` value and a UCSC alias |
| `seqrepo_metadata_refseq_NC_000001.11.json`, `seqrepo_metadata_refseq_NC_012920.1.json` | https://services.genomicmedlab.org/seqrepo/1/metadata/refseq:NC_000001.11 and `.../refseq:NC_012920.1` | human chr1 and chrM, as served |
| `vrs_normalizer_response_NC_000001.11_g.11796321G_A.json` | https://normalize.cancervariants.org/variation/normalize?q=NC_000001.11:g.11796321G>A | full response of the GA4GH-VRS variation normalizer (v0.17.1); the adapter pulls the SequenceReference out of `variation.location` |
| `vrs_SequenceReference_spec_example_GRCh38_chr7.yaml` | **spec example**, `examples/coverage/sequence_reference.yaml` in ga4gh/vrs tag 2.1.1 | refgetAccession is GRCh38 chr7 |
| `constructed/vrs_SequenceReference_R64-1-1_chrI_constructed.json` | **hand-written** from the VRS schema | refgetAccession from the real yeast seqcol record, `BK006935.2` from ENA/EVA, `chrI` from UCSC sacCer3 naming. Exists to exercise the optional fields; no public VRS service covers yeast. |
| `sam_dict_broad_hg38_Homo_sapiens_assembly38.dict` | https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/Homo_sapiens_assembly38.dict | full file (3366 `@SQ` lines) |
| `sam_dict_1kg_GRCh38_full_analysis_set_plus_decoy_hla.excerpt.dict` | https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.dict | **excerpt**: first 26 lines (`@HD` + first 25 `@SQ`); full file (757 KB) in `a local download folder (not in this repository)4gh/sam/` |
| `sam_dict_igenomes_R64-1-1_genome.dict` | https://ngi-igenomes.s3.amazonaws.com/igenomes/Saccharomyces_cerevisiae/Ensembl/R64-1-1/Sequence/WholeGenomeFasta/genome.dict | full file |
| `sam_header_spec_example_SAMv1_section1.sam` | **spec example**, SAMv1 section 1.1 | spaces in the PDF/tex rendering replaced by the TABs SAM requires |
| `sam_header_spec_example_SAMv1_AN_footnote.sam` | **spec example**, the footnote under `@SQ AN` | same TAB replacement |
| `constructed/sam_header_AH_DS_constructed.sam` | **hand-written** | `SN`, `LN`, `M5` copied from the Broad dict line for `chr1_KI270762v1_alt`; `AH:*` and `DS` written by hand because no real header with these tags was found |
| `vcf_header_giab_HG002_GRCh38_v4.2.1.vcf` | https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/NISTv4.2.1/GRCh38/HG002_GRCh38_1_22_v4.2.1_benchmark.vcf.gz | header excerpt (see below); its 195 contigs are the same no-alt set as the hg38 seqcol |
| `vcf_header_1kGP_high_coverage_chr22.vcf` | https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV/1kGP_high_coverage_Illumina.chr22.filtered.SNV_INDEL_SV_phased_panel.vcf.gz | header excerpt |
| `vcf_header_1kg_phase3_GRCh38_chr22.vcf` | https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz | header excerpt |
| `vcf_header_gnomad_v4.1_genomes_chr21.vcf` | https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites.chr21.vcf.bgz | header excerpt |
| `vcf_header_broad_hg38_1000G_omni2.5.vcf` | https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/1000G_omni2.5.hg38.vcf.gz | header excerpt (all 3366 contigs kept) |
| `vcf_header_dbsnp_GCF_000001405.40.vcf` | https://ftp.ncbi.nih.gov/snp/latest_release/VCF/GCF_000001405.40.gz (dbSNP build 157) | header excerpt |
| `vcf_header_clinvar_GRCh38.vcf` | https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz (fileDate 2026-11-15) | header excerpt |
| `vcf_header_ensembl116_homo_sapiens_chr21.vcf` | https://ftp.ensembl.org/pub/current_variation/vcf/homo_sapiens/homo_sapiens-chr21.vcf.gz | header excerpt |
| `vcf_header_eva_release9_R64_GCA_000146045.2.vcf` | https://ftp.ebi.ac.uk/pub/databases/eva/rs_releases/release_9/by_species/saccharomyces_cerevisiae/GCA_000146045.2/4932_GCA_000146045.2_current_ids.vcf.gz | header excerpt (the whole header is reference lines) |
| `vcf_header_ensemblfungi_saccharomyces_cerevisiae.vcf` | https://ftp.ebi.ac.uk/ensemblgenomes/pub/fungi/current/variation/vcf/saccharomyces_cerevisiae/saccharomyces_cerevisiae.vcf.gz | header excerpt (main ftp.ensembl.org has no yeast variation VCF) |
| `vcf_header_spec_example_VCFv4.5.vcf` | **spec example**, VCFv4.5 section 1.1 | first 5 meta lines; `#CHROM` line rebuilt with TABs |
| `vcf_header_spec_example_VCFv4.3_sv.vcf` | **spec example**, VCFv4.3 SV example | first 4 meta lines; `#CHROM` line added (8 fixed columns) |

**How VCF headers were excerpted.** Only the first 1-2 MB of each `.vcf.gz`
was downloaded (HTTP range request) and decompressed member by member; raw
partial files and full headers are in `a local download folder (not in this repository)4gh/vcf/`. From
each header I kept, in original order, only the lines starting with
`##fileformat=`, `##fileDate=`, `##source=`, `##reference=`, `##assembly=`,
`##contig=`, and the `#CHROM` line cut to its first 9 columns (sample names
dropped). `##INFO`, `##FORMAT`, `##FILTER`, `##ALT`, tool command lines and
annotation-version lines were dropped. Nothing was edited.

## Quirks that matter for mapping

**Identity and digests**

- The seqcol top-level digest is not in the served object. It is computed from
  the level 1 digests of the inherent attributes only (`names`, `sequences`).
  So renaming sequences changes it; changing `lengths` alone cannot happen.
- Same sequences, different names, different collections: refgenie's R64-1-1
  calls the mitochondrion `Mito`, iGenomes' R64-1-1 `.dict` calls it `MT`, EVA
  calls it `KP263414.1`, UCSC sacCer3 `chrM`. The `sequences` and
  `sorted_sequences` digests match across these; `names` and the top-level
  digest do not.
- R64-1-1 names are sorted as text (`I, II, III, IV, IX, Mito, V, ...`), not
  in chromosome order; the iGenomes Ensembl `.dict` has the same order. Order is part of the collection; EVA
  lists contigs in yet another order (`VIII` first).
- The api.refgenie.org alias `hg38` points to the GRCh38 **no-alt analysis
  set** (195 sequences incl. chrEBV), not UCSC's full hg38.fa. Its other
  aliases (`/seqcol/aliases/collection/<digest>`) are `hs38`,
  `GRCh38-fasta-no-alt-analysis`, `hg38-noALT-noHLA-noDecoy-broad`,
  `GRCh38-igenomes-ncbi`, `hg38-refgenie`. Collection aliases are a refget
  package extension, not part of the GA4GH seqcol spec, and are not modeled here.
- Three spellings of one sequence digest: seqcol `sequences` and VRS
  `refgetAccession` use `SQ.Ya6R...`; SeqRepo uses `ga4gh:SQ.Ya6R...`,
  `sha512t24u:Ya6R...` and `VMC:GS_Ya6R...`; the refget OpenAPI example uses
  `ga4gh:SQ....` while the README example uses `SQ....`. The refgenie seqcol
  API's `/aliases/sequence/<digest>` wants the bare digest (with `SQ.` it
  returns no aliases).
- md5 is the shared key between the hts world and refget: SAM `M5`, VCF
  `md5`, refget `md5`, SeqRepo `MD5:`. The normalization rules differ slightly
  (refget keeps only A-Z; SAM keeps all printable characters 33-126), which
  matters only for sequences with `*` or other non-letters.

**Names and namespaces**

- Refget `naming_authority` values are recommended lowercase (`insdc`,
  `ucsc`, `ensembl`, `refseq`, `md5`, `ga4gh`); ENA sends `INSDC`. ENA lists
  an alias only when you ask by that alias; asking by md5 returns `aliases: []`.
- SeqRepo namespaces mix three kinds of thing: assembly names used as a
  namespace for sequence names (`GRCh38:1`, `GRCh38:chr1`, `GRCh38.p12:chr1`,
  so the same sequence has a name in every patch release and both naming
  styles), accession namespaces (`NCBI`/`refseq`, `Ensembl`/`ensembl`), and
  digest namespaces (`MD5`, `SHA1`, `SEGUID`, `VMC`, `sha512t24u`, `ga4gh`).
  The REST API returns both the DB spelling and an API spelling
  (`NCBI:NC_000001.11` and `refseq:NC_000001.11`). A `(namespace, alias)` pair
  is unique among current aliases (unique index in the alias DB schema).
- SAM `AN` and VCF have no naming authority at all. VRS `aliases` are plain
  strings.

**Assembly-level fields are free text**

- SAM `AS`: `GRCh38` (1000 Genomes), `38` (Broad), absent (iGenomes). SAM
  `SP`: `Homo sapiens` (Broad), `Human` (1000 Genomes). Both repeat on every
  `@SQ` line.
- VCF `##contig` `assembly=`: a FASTA file name (GIAB
  `human_GRCh38_no_alt_analysis_set.fasta`), a project label (gnomAD
  `gnomAD_GRCh38`), or junk (Broad hg38 resource VCFs `20`). `taxonomy=` appears
  only in the spec example, with the placeholder value `x`.
- VCF `##reference` holds whatever the producer chose: a FASTA URL (1000
  Genomes), an Ensembl FASTA directory URL, `GRCh38` (ClinVar), `GRCh38.p14`
  (dbSNP), or EVA's structured `<ID=R64,accession=GCA_000146045.2,URL=...>`.
  The adapter keeps unstructured values in `reference` and splits structured
  ones into `reference.ID`, `reference.accession`, `reference.URL`.
- VCF `##assembly` is **not** the genome assembly: it is a FASTA of SV
  breakpoint assemblies.
- dbSNP uses RefSeq accessions as CHROM and declares no `##contig` lines.
  1000 Genomes phase 3 GRCh38 declares `##contig=<ID=22>` with no length.

**Schema inconsistencies in the seqcol spec**

- `seqcol_extended_v1.0.0.json` is not valid JSON (trailing comma after the
  last property).
- `sorted_name_length_pairs`: the spec text says items are digests, not
  collated, transient; the extended JSON schema says items are `{name, length}`
  objects and `collated: true`. The api.refgenie.org schema says objects,
  `collated: false`, transient. A transient attribute never appears at level 2.
- `seqcol_refs_v1.0.0.json` requires only `names` and `sequences`; the
  minimal schema also requires `lengths`.
- The refget sequences OpenAPI requires `id` and has `trunc512`; the v2 README
  response table has neither but adds `ga4gh`.

**Attribute qualifiers (seqcol section 4).** `collated`: element i belongs to
sequence i (`names`, `lengths`, `sequences`, `name_length_pairs`). `inherent`:
feeds the digest (`names`, `sequences`). `transient`: only the level 1 digest
is kept (`sorted_name_length_pairs`). `passthru`: same value at levels 1 and 2
(none in the base schema). The deployed api.refgenie.org schema adds a custom
collated `accessions` attribute that no stored collection uses.

## Gaps

- No yeast SeqRepo record (public SeqRepo is human-only) and no real yeast VRS
  record (constructed one instead).
- No real SAM header with `AH`, `AN`, `DS` or `TP`; those values come from the
  SAM spec or the constructed file.
- No real VCF `##contig` with `md5` or `URL`; values come from the spec.
- No public refget sequences server returned a non-null `ga4gh` digest or a
  non-INSDC alias; only the spec example shows them.
- The SeqRepo alias **table** (`seqalias`: seqalias_id, seq_id, namespace,
  alias, added, is_current) is documented in `spec/seqrepo/` but not modeled as
  a format, because no real rows are published outside a 13.5 GB snapshot.

## Reuse terms

- ga4gh/refget (seqcol, refget sequences, schemas): no license file in the
  repository; `mkdocs.yml` states "copyright: GA4GH Large Scale Genomics
  Workstream, refget team".
- ga4gh/vrs: Apache-2.0.
- biocommons/seqrepo and seqrepo-rest-service: Apache-2.0.
- samtools/hts-specs (SAM, VCF): no license file or statement found in the
  repository.
- Example records are public data from ENA, NCBI, EBI/EVA, Ensembl, GIAB,
  1000 Genomes, gnomAD, Broad (GCP public datasets), Illumina iGenomes (AWS
  open data), api.refgenie.org, and the variation-normalizer service (code MIT).
