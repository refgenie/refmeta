# Bioconductor genome metadata

Bioconductor is the R project for genomics. It has no single genome schema.
Genome metadata is spread over a few core packages, each with its own record
format:

| Package | What it holds about genomes | Maintainer |
|---|---|---|
| **Seqinfo** (new in Bioc 3.22) | `Seqinfo` class: names, lengths, circular flags and genome label of a set of sequences; `GenomeDescription` class | Hervé Pagès |
| **GenomeInfoDb** | Registration files for NCBI assemblies and UCSC genomes; cached chrom-info tables; chromosome naming-style tables (`seqlevelsStyle`); Ensembl/UCSC build map | Hervé Pagès |
| **BSgenomeForge** / **BSgenome** | Seed files (DCF) that define each `BSgenome.*` sequence package; the packages' DESCRIPTION files | Hervé Pagès |
| **AnnotationHub** / **AnnotationHubData** | Hub database of downloadable resources (including genome 2bit/FASTA copies); contributor `metadata.csv` | Bioconductor Package Maintainer <maintainer@bioconductor.org> |

All these packages are licensed Artistic-2.0, as their DESCRIPTION files say.
That covers the spec text and registration files copied here. The hub
metadata (annotationhub.bioconductor.org) has no separate license on it. The
data files the hub points to keep their providers' terms (UCSC, Ensembl).

All files were retrieved on **2026-11-17**. GitHub files come from the
`devel` branch of the `github.com/Bioconductor/<pkg>` mirror. Packages and
commits:

- GenomeInfoDb 1.49.3 (`0eaf67c`)
- Seqinfo 1.3.2 (`93f9978`)
- BSgenome 1.81.1 (`da2ce6b`)
- BSgenomeForge 1.13.0 (`34fd2f4`)
- AnnotationHub 4.3.3 (`9d207d2`)
- AnnotationHubData 1.43.0 (`47cd0ee`)

The Bioconductor release is 3.23 and devel is 3.24.

## The Seqinfo move

`Seqinfo` and `GenomeDescription` moved from GenomeInfoDb into the new
**Seqinfo** package in Bioconductor 3.22 (GenomeInfoDb 1.46.0 NEWS; Seqinfo
1.0.0 NEWS). Their accessors moved with them: `seqnames()`, `seqlengths()`,
`isCircular()`, `genome()`, `commonName()`, `provider()`, `providerVersion()`,
`releaseDate()` and `bsgenomeName()`.

Seqinfo objects saved before 3.22 need `updateObject()`. Objects saved with
3.22 or later cannot be read by older versions.

GenomeInfoDb keeps the parts that link genomes to outside sources: the
registration files, `getChromInfoFromNCBI/UCSC/Ensembl()`, `seqlevelsStyle()`
and `mapGenomeBuilds()`.

## Formats

| Format id | Records | Level(s) | Adapter |
|---|---|---|---|
| `bioconductor_seqinfo` | one per sequence | sequence (+ genome label) | read/write TSV; also reads `show()` text |
| `bioconductor_chrominfo_ucsc` | one per sequence | sequence | read/write |
| `bioconductor_chrominfo_ncbi` | one per sequence | sequence | read/write |
| `bioconductor_seqlevels_style` | one per chromosome | sequence (name aliases) | read/write |
| `bioconductor_genome_mapping_tbl` | one per Ensembl assembly name | assembly ↔ collection | read/write |
| `bioconductor_registered_ncbi` | one per assembly | assembly | read/write (R) |
| `bioconductor_registered_ucsc` | one per UCSC genome | collection, assembly link | read/write (R) |
| `bioconductor_bsgenome_seed` | one per package | assembly, collection, copy, deployment | read/write (DCF) |
| `bioconductor_bsgenome_description` | one per package | same as seed | read/write (DCF) |
| `bioconductor_annotationhub_record` | one per hub resource | copy, deployment | read/write (JSON) |
| `bioconductor_annotationhub_metadata_csv` | one per hub resource | copy, deployment | read/write (CSV) |

Format details:

- **Seqinfo.** This is an in-memory R object with no official file format.
  The adapter uses the columns of `as.data.frame(<Seqinfo>)`: `seqnames`,
  `seqlengths`, `isCircular`, `genome`. That is what `write.table()` gives,
  and what `as(<data.frame>, "Seqinfo")` reads back.
- **chrominfo tables.** `getChromInfoFromUCSC()` and `getChromInfoFromNCBI()`
  return these as data frames. GenomeInfoDb ships cached copies as `.tab`
  files in `inst/chrominfo_db/`. There are 7 UCSC genomes (dm6, hg19, hg38,
  hs1, mm39, sacCer2, sacCer3) and 7 NCBI accessions, both anchors included.
  When called with `map.NCBI=TRUE` or `add.ensembl.col=TRUE`, the functions
  add `NCBI.*` or `ensembl` columns in memory. Those columns are not in any
  file and are not covered here.
- **Registration files.** These are R scripts. Bioconductor itself runs them
  with `source()`. The adapter never runs them. It reads only the simple
  pattern they use: `NAME <- value`, where the value is built from string
  literals and `c()`, `list()`, `paste0()`, `paste()`, `character(0)`,
  `as.character()`, `as.roman()` and `a:b`. Function definitions are skipped.
  The one exception is `FETCH_ORDERED_CHROM_SIZES`, whose source text is kept
  verbatim as a string.
- **Not covered as formats.** `GenomeDescription` (the slots
  `organism, common_name, provider, provider_version, release_date,
  release_name, seqinfo`) is only an R object. A BSgenome object fills it
  from the seed fields of the same names (`provider_version` comes from
  `genome` in newer seeds). `mcols(<AnnotationHub>)` is the R view of the hub
  record. Its columns are `title, dataprovider, species, taxonomyid, genome,
  description, coordinate_1_based, maintainer, rdatadateadded,
  preparerclass, tags, rdataclass, rdatapath, sourceurl, sourcetype`, and
  each one is noted on the matching field of
  `bioconductor_annotationhub_record`.

## Where each file came from

Base URLs used below:

- GH = `https://raw.githubusercontent.com/Bioconductor`
- BIOC = `https://bioconductor.org/packages/release/data/annotation/src/contrib`
- AH = `https://annotationhub.bioconductor.org`

### spec/

| File | Source |
|---|---|
| `Seqinfo/Seqinfo-class.Rd`, `seqinfo.Rd`, `GenomeDescription-class.Rd`, `DESCRIPTION` | GH`/Seqinfo/devel/man/...`, GH`/Seqinfo/devel/DESCRIPTION` |
| `Seqinfo/NEWS_excerpt.txt` | GH`/Seqinfo/devel/NEWS`, lines 1–40 |
| `Seqinfo/Seqinfo-class_R_excerpt.txt` | GH`/Seqinfo/devel/R/Seqinfo-class.R`, lines 1–30 (class) and 455–540 (as.data.frame and coercion) |
| `Seqinfo/GenomeDescription-class_R_excerpt.txt` | GH`/Seqinfo/devel/R/GenomeDescription-class.R`, lines 1–32 |
| `GenomeInfoDb/UCSC_genomes_README.TXT` | GH`/GenomeInfoDb/devel/inst/registered/UCSC_genomes/README.TXT` (the spec for UCSC registration files) |
| `GenomeInfoDb/getChromInfoFromNCBI.Rd`, `getChromInfoFromUCSC.Rd`, `seqlevelsStyle.Rd`, `mapGenomeBuilds.Rd`, `DESCRIPTION` | GH`/GenomeInfoDb/devel/man/...` |
| `GenomeInfoDb/getChromInfoFromNCBI_R_excerpt.txt` | GH`/GenomeInfoDb/devel/R/getChromInfoFromNCBI.R`, lines 1–215. This is the validator for NCBI registration files. It is the only written statement of their required fields (`assembly`, `date`, `assembly_accession`, `circ_seqs`) and optional fields (`extra_info`, `NCBI2Ensembl_special_mappings`; `assembly_level` is not checked). |
| `GenomeInfoDb/chrominfo_db_NCBI_README.TXT`, `chrominfo_db_UCSC_README.TXT` | GH`/GenomeInfoDb/devel/inst/chrominfo_db/{NCBI,UCSC}/README.TXT` |
| `GenomeInfoDb/dataFiles_README.txt` | GH`/GenomeInfoDb/devel/inst/extdata/dataFiles/README` |
| `GenomeInfoDb/NEWS_excerpt.txt` | GH`/GenomeInfoDb/devel/NEWS`, lines 1–90 (includes the Seqinfo move) |
| `BSgenomeForge/AdvancedBSgenomeForge_seed_fields_excerpt.Rnw.txt` | GH`/BSgenomeForge/devel/vignettes/AdvancedBSgenomeForge.Rnw`, lines 233–446 (seed file fields) |
| `BSgenomeForge/AdvancedBSgenomeForge_masked_seed_fields_excerpt.Rnw.txt` | same vignette, lines 581–690 (masked seed fields) |
| `BSgenomeForge/BSgenomeDataPkgSeed_class_R_excerpt.txt` | GH`/BSgenomeForge/devel/R/AdvancedBSgenomeForge.R`, lines 700–800 (seed classes, with deprecation comments) |
| `BSgenomeForge/DESCRIPTION` | GH`/BSgenomeForge/devel/DESCRIPTION` |
| `BSgenomeForge/BSgenome-class.Rd` | GH`/BSgenome/devel/man/BSgenome-class.Rd` (accessors that expose seed fields) |
| `AnnotationHub/makeAnnotationHubMetadata.Rd`, `AnnotationHubMetadata-class.Rd` | GH`/AnnotationHubData/devel/man/...` (the spec for `metadata.csv`) |
| `AnnotationHub/AnnotationHubServer3.0_schema_sequel.rb.txt` | GH`/AnnotationHubServer3.0/master/schema_sequel.rb` |
| `AnnotationHub/AnnotationHubServer3.0_app_formatId_excerpt.rb.txt` | GH`/AnnotationHubServer3.0/master/app.rb`, lines 60–135 and 270–300 (`formatId()` builds the `/ahid/` JSON) |
| `AnnotationHub/AnnotationHub_mcols_sql-utils_R_excerpt.txt` | GH`/AnnotationHub/devel/R/sql-utils.R`, lines 100–125 (which columns `mcols()` shows) |
| `AnnotationHub/annotationhub_sqlite3_schema.sql` | `CREATE` statements and the `statuses` table, dumped with Python's sqlite3 from AH`/metadata/annotationhub.sqlite3`. The database file is 137 MB, with `database_timestamp` 2026-11-13 18:57:25. It is kept at `a local download folder (not in this repository)annotationhub.sqlite3`. |

Code excerpts are saved as `.txt` and are reference text only. Nothing
downloaded was run.

### examples/ (real records)

| File | Source |
|---|---|
| `registered_ncbi_Homo_sapiens.R`, `registered_ncbi_Saccharomyces_cerevisiae.R` | GH`/GenomeInfoDb/devel/inst/registered/NCBI_assemblies/{Homo_sapiens,Saccharomyces_cerevisiae}.R`, whole files. The anchors are GRCh38.p14 = GCF_000001405.40 and R64 = GCA_000146045.2. |
| `registered_ucsc_hg38.R`, `registered_ucsc_sacCer3.R` | GH`/GenomeInfoDb/devel/inst/registered/UCSC_genomes/{hg38,sacCer3}.R` |
| `chrominfo_ucsc_hg38.tab`, `chrominfo_ucsc_sacCer3.tab` | GH`/GenomeInfoDb/devel/inst/chrominfo_db/UCSC/{hg38,sacCer3}.tab` (711 and 17 rows) |
| `chrominfo_ncbi_GCF_000001405.40.tab`, `chrominfo_ncbi_GCA_000146045.2.tab` | GH`/GenomeInfoDb/devel/inst/chrominfo_db/NCBI/...` (709 and 17 rows) |
| `seqlevels_style_Homo_sapiens.txt`, `seqlevels_style_Saccharomyces_cerevisiae.txt` | GH`/GenomeInfoDb/devel/inst/extdata/dataFiles/{Homo_sapiens,Saccharomyces_cerevisiae}.txt` |
| `genome_mapping_tbl_human_yeast.csv` | **Excerpt** of GH`/GenomeInfoDb/devel/inst/extdata/dataFiles/genomeMappingTbl.csv`: the header plus every row starting `human,` or `yeast,` (27 of 493 rows) |
| `bsgenome_seed_BSgenome.Hsapiens.UCSC.hg38-seed`, `...Scerevisiae.UCSC.sacCer3-seed`, `...Hsapiens.NCBI.GRCh38-seed`, `...Hsapiens.UCSC.hg38.masked-seed` | GH`/BSgenomeForge/devel/inst/extdata/seeds/<name>-seed` |
| `bsgenome_DESCRIPTION_BSgenome.Hsapiens.UCSC.hg38_1.4.5` | `DESCRIPTION` from BIOC`/BSgenome.Hsapiens.UCSC.hg38_1.4.5.tar.gz`. Only that one file was streamed out of the tarball (`tar --occurrence=1`); the rest of the tarball was not downloaded. |
| `bsgenome_DESCRIPTION_BSgenome.Scerevisiae.UCSC.sacCer3_1.4.0` | `DESCRIPTION` from BIOC`/BSgenome.Scerevisiae.UCSC.sacCer3_1.4.0.tar.gz` (tarball kept in `a local download folder (not in this repository)bsgenome_pkgs/`) |
| `annotationhub_AH13963.json` (hg38.2bit, UCSC) | AH`/ahid/AH13963` |
| `annotationhub_AH106283.json` (Homo_sapiens.GRCh38.dna.primary_assembly.2bit, Ensembl 107) | AH`/ahid/AH106283` (the newest human Ensembl genome 2bit in the hub) |
| `annotationhub_AH14104.json` (sacCer3.2bit, UCSC) | AH`/ahid/AH14104` |
| `annotationhub_AH106802.json` (Saccharomyces_cerevisiae.R64-1-1.dna_sm.toplevel.2bit, Ensembl 107) | AH`/ahid/AH106802` |
| `annotationhub_AH49186.json` (Homo_sapiens.GRCh38.dna.toplevel.fa, Ensembl 81, removed 2019) | AH`/ahid/AH49186`. Chosen because it has two `rdatapaths` (`.fa.rz` plus `.fai`). |
| `annotationhub_metadata_EpiTxDb.Hs.hg38_metadata.csv`, `..._metadata-snoRNA-targets.csv` | `inst/extdata/*.csv` from BIOC`/EpiTxDb.Hs.hg38_0.99.7.tar.gz`. The snoRNA-targets row is hub record AH83362, an hg38 FASTA. |
| `annotationhub_metadata_EpiTxDb.Sc.sacCer3_metadata.csv`, `..._metadata-snoRNAdb.csv` | `inst/extdata/*.csv` from BIOC`/EpiTxDb.Sc.sacCer3_0.99.5.tar.gz`. The FASTA row is AH89327. |

I chose the hub records by querying the sqlite database for
`genome IN (hg38, GRCh38*, sacCer3, R64-1-1)` and `rdataclass IN
(TwoBitFile, FaFile)`.

The EpiTxDb files are the only anchor-genome contributor CSVs I found. The
Bioconductor GitHub mirror has no repos for these annotation packages, and
code.bioconductor.org timed out, so they came from the release tarballs.

### examples/constructed/

`seqinfo_hg38.tsv` and `seqinfo_sacCer3.tsv` are **not served by
Bioconductor**, because Seqinfo has no file form. I made them from the real
`chrominfo_ucsc_*.tab` files:

- `chrom` became `seqnames`
- `size` became `seqlengths`
- `circular` became `isCircular`
- `genome` was set to the UCSC genome name

This mirrors what `getChromInfoFromUCSC(genome, as.Seqinfo=TRUE)` builds in
R. R was not available, so I could not capture real `show()` output.

## What identifies a record

- **NCBI registration:** `assembly_accession` (GCF_ or GCA_). Assembly names
  are also unique in practice.
- **UCSC registration:** `GENOME` (UCSC name, which is also the file name).
- **Seqinfo / chrominfo / style tables:** the sequence name, which is unique
  only within one table. A table as a whole is one sequence collection.
  Bioconductor has no digest or ID for a collection.
- **BSgenome seed / DESCRIPTION:** `Package`, which is globally unique in
  Bioconductor. `Version` tells releases apart.
- **AnnotationHub:** `ah_id` (AH + integer), unique for good. Removed
  resources keep their ID; for example, AH49186 is still served.

## Levels covered

- **assembly:** the NCBI registration (`assembly`, `assembly_accession`,
  `date`, `assembly_level`, strain in `extra_info`). Also `organism`,
  `common_name` and `release_date` in seeds and DESCRIPTION files, and
  `species`/`taxonomyid` in AnnotationHub.
- **collection:** the UCSC registration (`GENOME`, `ASSEMBLED_MOLECULES`,
  `CIRC_SEQS`, `NCBI_LINKER.unmapped_seqs`), the seed's `genome` or
  `provider_version`, `seqnames` and `circ_seqs`, and a whole Seqinfo table.
- **sequence:** Seqinfo rows, chrominfo rows (NCBI rows carry GenBank and
  RefSeq accessions and the UCSC alias), seqlevelsStyle rows (the same
  chromosome named in NCBI, UCSC, dbSNP and Ensembl styles), and the
  special-mapping exceptions.
- **copy:** AnnotationHub (`location_prefix` + `rdatapaths[].rdatapath` is
  the hub copy's URL, `input_sources[].sourceurl` is the upstream file).
  Also the seed's `source_url`, `SrcDataFiles` and `seqfile_name`.
- **deployment:** the BSgenome package name and version, AnnotationHub IDs,
  `dispatchclass`, `biocversions`, `preparerclass` and recipe.

**No checksums anywhere.** BSgenome packages carry no file or sequence
checksums. AnnotationHub has a `sourcemd5` field, but only 1 of its 153,056
input sources has a value.

## Quirks that matter for mapping

1. **"genome" means four things.**
   - In Seqinfo it is a free-text label stored per sequence. It is usually
     a UCSC name (`hg38`), but can be an NCBI assembly name (`GRCh38.p14`).
     After renaming hg38 to NCBI style, two sequences show `GRCh38.p13`
     (see the hg38 seed's PkgExamples).
   - In a seed or DESCRIPTION it is the UCSC name or NCBI assembly name.
   - In AnnotationHub it is free text. Human GRCh38 appears as `hg38`,
     `GRCh38`, `GRCh38.p12` and `GRCh38.p13`.
   - In a UCSC registration file, `GENOME` is the UCSC name only.
2. **hg38 is not GRCh38.p14.** UCSC rebased hg38 on GRCh38.p14 in Jan 2023
   but kept two GRCh38.p13 fix patches (`chr11_KQ759759v1_fix`,
   `chr22_KQ759762v1_fix`). So hg38 has 711 sequences and GCF_000001405.40
   has 709. GenomeInfoDb records this in `NCBI_LINKER.unmapped_seqs`.
3. **Which accession.** GenomeInfoDb registers human by RefSeq GCF and
   versions it per patch (GRCh38 = GCF_000001405.26, GRCh38.p14 = .40). It
   registers yeast R64 by GenBank GCA_000146045.2, to match Ensembl. The
   NCBI-provided BSgenome GRCh38 was built from GCA_000001405.15 (no
   patches), yet its `provider_version` is just `GRCh38`.
4. **Same thing, different names.**
   - Yeast R64 at NCBI is R64-1-1 at Ensembl and UCSC.
   - The yeast mitochondrion is `MT` (NCBI), `chrM` (UCSC) and `Mito`
     (Ensembl).
   - The yeast style table lists `2micron`, which exists only in sacCer2.
     That row also has `sex=T`, which looks like a mistake in the file.
5. **No taxon ID in GenomeInfoDb registration files.** The task suggested
   `TAXON_ID` and `ASSEMBLY_ACCESSION` fields, but neither exists. The real
   names are lower-case `assembly_accession` inside each `ASSEMBLIES`
   entry, or `assembly_accession` inside `NCBI_LINKER` for UCSC files.
   Taxonomy appears only in AnnotationHub, and GenomeInfoDb gets it from
   the GenomeInfoDbData package. AnnotationHub gives yeast taxon 4932
   (species) for sacCer3 and 559292 (strain S288C) for Ensembl R64-1-1.
6. **Renamed BSgenome fields.** `species` became `common_name`, and
   `provider_version` became `genome`; `release_name` is deprecated. Old
   packages keep the old names. The released sacCer3 package is 1.4.0, built
   in 2014, while its seed in BSgenomeForge says 1.4.2.
7. **Dates come in many forms:** `2022/02/03` (registration files),
   `April 2011`, `2023/01/31` and `2013-12-17` (seeds), `Sept.2019`
   (genomeMappingTbl), and ISO in AnnotationHub.
8. **genomeMappingTbl.csv has suspect rows.** NCBI36 maps to hg19 and
   GRCh37.p13 maps to hg38. Its `ensemblID` is Ensembl's assembly name,
   not an accession.
9. **AnnotationHub `coordinate_1_based` is meaningless for sequence files.**
   UCSC 2bit records say FALSE and Ensembl ones say TRUE. `species` case
   varies (`homo sapiens` vs `Homo sapiens`). Record status (Public,
   Defunct, ...) is in the database (`status_id`) but not in the `/ahid/`
   JSON. Instead, `rdatadateremoved` is set.
10. **R files are code.** Six old UCSC files (apiMel2, galGal3, hg15–hg18)
    build `NCBI_LINKER` with helper variables or `setNames()`. For those,
    the adapter keeps the raw R text under the key `NCBI_LINKER`. All 60
    NCBI and 96 UCSC registration files in GenomeInfoDb 1.49.3 parse, and
    write/read round-trips them (checked by a scratch script, not in the
    test suite).

## Adapter conventions

The adapter is
[`tools/refmeta/formats/bioconductor.py`](../../tools/refmeta/formats/bioconductor.py).
It follows these conventions:

- **R and table values.** R logicals (`TRUE/FALSE/T/F`) become JSON
  booleans, and `NA` becomes null. Writers put them back (`T/F` for style
  tables, `TRUE/FALSE` elsewhere).
- **R vectors.** Fields that are R vectors (`circ_seqs`, `CIRC_SEQS`,
  `ASSEMBLED_MOLECULES`, `NCBI_LINKER.AssemblyUnits`) are always lists.
  Named vectors and named lists become objects.
- **NCBI registration.** `ORGANISM` (one per file) is copied onto each
  assembly record.
- **UCSC registration.** `NCBI_LINKER` parts become `NCBI_LINKER.<part>`.
- **AnnotationHub JSON.** The array members are flattened to
  `rdatapaths[].rdatapath`, `input_sources[].sourceurl` and so on. Each
  value is a list with one item per array member, and the writer zips them
  back together.
- **DCF files.** These are read like R's `read.dcf()`: continuation lines
  lose their leading whitespace and are joined with `\n`, and values are
  trimmed. The writer indents continuation lines with a tab.
- **Seed R expressions.** `seqnames`, `circ_seqs`, `mseqnames` and
  `citation_file` in seeds are R expressions. They are kept as raw text.
