# UCSC Genome Browser

**What it is.** The UCSC Genome Browser shows genome assemblies and their
annotation. It is maintained by the UCSC Genome Browser Group (Genomics
Institute, University of California Santa Cruz; contact genome-www@soe.ucsc.edu).
Its genome metadata lives in four places:

1. **Native databases** such as `hg38` and `sacCer3`. Each is a row in the
   central `dbDb` table, and the REST API serves it at `/list/ucscGenomes`.
2. **Download files** on hgdownload: `chrom.sizes`, `chromAlias.txt`,
   `md5sum.txt`, and the `chromAlias` database table dump.
3. **Track and assembly hubs**: `hub.txt` and `genomes.txt` stanza files. A
   hub can carry a whole genome: its 2bit, sizes, aliases and naming authority.
4. **GenArk**, UCSC's collection of more than 54,000 assembly hubs built from
   NCBI assemblies. Each one is named by its GCA_/GCF_ accession, for example
   `hubs/GCF/000/146/045/GCF_000146045.2/`.

All files were retrieved on **2026-11-17**.

## Formats

| id | What one record is | Identified by | Levels |
|---|---|---|---|
| `ucsc_dbdb` | One UCSC database genome (dbDb row), from `/list/ucscGenomes` | `name` (hg38) | collection label, assembly facts, deployment |
| `ucsc_api_chromosomes` | One sequence (name, length) of a genome, from `/list/chromosomes` | `genome` + `chrom` | sequence |
| `ucsc_chrom_sizes` | One row of a `chrom.sizes` file | `chrom` | sequence |
| `ucsc_chromalias_txt` | One sequence with its names under each authority (`chromAlias.txt`) | first column | sequence |
| `ucsc_chromalias_table` | One alias row of the `chromAlias` database table | `alias` | sequence |
| `ucsc_hub_txt` | The `hub` stanza of a hub.txt | `hub`, but really the hub URL | deployment |
| `ucsc_genomes_txt` | One `genome` stanza, from genomes.txt or a single-file hub.txt | `genome` within a hub | collection, copy, assembly, deployment |
| `ucsc_api_genark` | One GenArk assembly hub, from `/list/genarkGenomes` | `gcAccession` | assembly, deployment |
| `ucsc_api_findgenome` | One genome search match, from `/findGenome` | `name` | assembly, deployment |
| `ucsc_api_hubgenomes` | One hub genome as the API parsed it, from `/list/hubGenomes` | `hubUrl` + `genome` | deployment, copy |
| `ucsc_api_files` | One download file (path, size, time), from `/list/files` | `url` | copy |
| `ucsc_md5sum` | One file checksum in a download directory's `md5sum.txt` | `file` | copy |

Every format has an adapter in `tools/refmeta/formats/ucsc.py`, and every
format can be written back out. Binary files (`.2bit`, `chromAlias.bb`) are
not covered.

## Naming: chr1 vs 1 vs NC_000001.11

This is the main mapping issue for UCSC.

- **UCSC databases name sequences in UCSC style.** Examples: `chr1`,
  `chrM`, `chr10_GL383545v1_alt`, `chrUn_KI270322v1`, `chrI` (yeast). Ensembl
  calls the same sequences `1`, `MT`, `KI270322.1` and `Mito` (yeast chrM).
  NCBI calls them `NC_000001.11` (RefSeq) or `CM000663.2` (GenBank). The
  sequences are identical; only the names differ.
- **chromAlias maps the names.** It comes in two shapes:
  - `chromAlias.txt` has one row per sequence and one column per naming
    authority. The `#` header names the columns: `ucsc`, `assembly`,
    `genbank`, `refseq`, `ensembl`, `ncbi`, and `VEuPathDB` in GenArk. The
    **first column is the name the genome itself uses.** Empty cells mean
    that authority has no name for the sequence.
  - The database table has one row per alias, in three columns: `alias`,
    `chrom` and `source`. `source` can list several authorities separated by
    commas. For example, `1` is `assembly,ensembl` and `KI270322.1` is
    `ensembl,genbank`.
- **GenArk turns the naming around.** A GenArk genome's own sequence names
  are RefSeq accessions (`NC_001133.9`). They appear in the 2bit,
  `chrom.sizes`, `/list/chromosomes` and `defaultPos`. The hub's genome stanza
  sets `chromAuthority ucsc`, so the browser *displays* `chrI`. GenArk
  `GCF_000146045.2` and native `sacCer3` have the same 17 sequence lengths
  once names are mapped through chromAlias. But their names differ, so their
  name-based seqcol digests differ. The sequence content was not compared,
  because the 2bit files were not downloaded.
- **The two yeast alias files disagree on chrM.**
  - In `sacCer3.chromAlias.txt`, chrM is `ensembl Mito`, `genbank
    AJ011856.1`, `refseq NC_001224.1`.
  - In the GenArk file, MT is `refseq NC_001224.1`, `VEuPathDB KP263414`, and
    `genbank` is empty.
- **The old hg38 alias file has no column labels.** In
  `bigZips/hg38.chromAlias.txt` (2021) the header is `# sequenceName<TAB>alias
  names<TAB>UCSC database: hg38`. Each row's aliases are *sorted*, not placed
  by authority. For example, chrX reads `CM000685.2 NC_000023.11 X`. The
  adapter reads this file as `sequenceName` plus a list `alias names`. Use
  `bigZips/latest/hg38.chromAlias.txt` (labeled) or the database table to
  learn which alias belongs to which authority.
- **Ensembl has no names for GRCh38 alt and fix sequences.** Their `ensembl`
  cell is empty. For unplaced sequences, Ensembl uses the GenBank accession.

## Quirks that matter for mapping

- **`hg38` is a label, not one fixed sequence set.**
  - `bigZips/hg38.chrom.sizes` (2013; same as `bigZips/initial/`) has 455
    sequences.
  - `bigZips/latest/hg38.chrom.sizes` (p14) and `/list/chromosomes`
    (chromInfo) have 711.
  - There are also `p11/`, `p12/` and `p13/` versions.
  - So one UCSC name maps to several seqcol digests. fields.json gives
    UCSC genome names the level "collection" because the refmeta README does,
    but treat them as names for a family of collections.
- **Assembly accessions are buried in free text.**
  - dbDb `sourceName` ends with `(GCA_000001405.15)` or `(GCA_000146045.2)`.
  - `/findGenome`'s `description` lists more tokens. For hg38 these are
    `GCA_000001405.28`, `GCA_000001405.29`, `GCF_000001405.40` and
    `GRCh38.p14`. So a search for `GCF_000001405.40` returns `hg38`.
  - findGenome marks hg38 `versionStatus: replaced`, because it is tied to the
    original GCA_000001405.15.
- **Names that look the same can mean different things.**
  - dbDb `genome` is a menu group such as "Human". The API/hub `genome` is a
    database or hub genome name such as hg38.
  - The hub `organism` setting is documented as a common name. GenArk writes
    `R64 Dec. 2014` there instead, which is an assembly name and date.
  - `scientificName` is species only in dbDb ("Saccharomyces cerevisiae"). In
    GenArk it includes the strain ("Saccharomyces cerevisiae S288C").
  - `description` is "Dec. 2013 (GRCh38/hg38)" in dbDb but "baker's yeast
    S288C (2014)" in GenArk.
- **Taxon:** sacCer3 and GenArk both use the strain taxon 559292, not the
  species taxon 4932.
- **Year:** findGenome `year` is 2011 for sacCer3 (UCSC build) and 2014 for
  GCF_000146045.2 (NCBI release). This is the same R64 assembly.
- **The GenArk hub id breaks its own spec.** The spec says `hub` has no
  spaces. GenArk writes `hub GCF_000146045.2 genome assembly`. The hub's
  identity is its URL.
- **Paths:** most hub paths are relative to the hub.txt URL.
  - The API's `/list/hubGenomes` resolves them to absolute URLs.
  - `/list/chromosomes` gives GenArk hubs as internal `/gbdb/genark/...` paths.
  - GenArk `md5sum.txt` lists internal `/mirrordata/hubs/...` paths.
  - To get a public URL, swap the internal prefix for
    `https://hgdownload.soe.ucsc.edu/hubs/`.
- **Checksums:** `md5sum.txt` gives the MD5 of each *file* (the gzipped
  `hg38.fa.gz`). These are copy-level checksums, not sequence digests.
  `/list/files` gives size and time but no checksum.
- **Timestamps:** `/list/files` `dateTime` uses `YYYY/MM/DDThh:mm:ss`. The
  API envelope `downloadTime` uses `YYYY:MM:DDThh:mm:ssZ`. Neither is ISO
  8601.
- **GenArk `clade` is unreliable.** Some values in
  `api_list_genarkGenomes_first5.json` are pieces of other text
  (`"8224 2008 genbank)"`, `"25"`) or wrong (horse is listed as
  "invertebrate").
- **Human GRCh38 is not in GenArk.** `/list/genarkGenomes?genome=GCF_000001405.40`
  returns 404, and `hubs/GCF/000/001/405/` does not exist. Human is served
  only as the native `hg38`. Only the yeast anchor has a real GenArk hub.
- **The API wraps records in an envelope.** Fields like `downloadTime`,
  `dataTime`, `itemCount` and `totalAssemblies` describe the HTTP response.
  The adapter drops them. It copies only `genome`, `hubUrl`, `track` and
  `rsyncHost` onto each record.

## Adapter conventions

- Native records are flat dicts. Where the API uses an object key as the
  record id, the adapter stores it under the name of the matching table
  column:
  - `name` for dbDb and findGenome (assemblyList),
  - `gcAccession` for GenArk,
  - `genome` for hubGenomes,
  - `chrom` and `size` for `/list/chromosomes` and `chrom.sizes` (chromInfo
    columns). The `chrom.sizes` file itself has no header.
- `chromAlias.txt` keys are the column headers, exactly as written. Empty
  cells become `null`, and key order keeps the column order.
- Hub stanzas: values are strings, except that `taxId` and `orderKey` are
  turned into integers. Track stanzas are skipped.
  - A useOneFile hub.txt holds both stanzas. `ucsc_hub_txt` reads the `hub`
    stanza, and `ucsc_genomes_txt` reads the `genome` stanza.
  - Detection prefers `ucsc_genomes_txt` for such files.
- One fields.json path is a glob: `liftOver.*`. GenArk writes one
  `liftOver.<target>` key per target genome, for example
  `liftOver.GCF_000002945.1`. tests/test_ucsc.py matches it with fnmatch.

## Settings not inventoried (no real example found)

- **Hub stanza:** `version` and `level`. kent trackHub.c reads them.
- **Genome stanza:** `metaDb` and `metaTab`, which point to track metadata
  tables.

These describe tracks, not genomes, so they do not matter for mapping.

## Where every file came from (all retrieved 2026-11-17)

### examples/

| File | URL | Notes |
|---|---|---|
| `api_list_ucscGenomes_hg38_sacCer3.json` | https://api.genome.ucsc.edu/list/ucscGenomes | **Excerpt:** envelope plus the `hg38` and `sacCer3` entries only, written back with `json.dumps(indent=1)`. Values are unchanged. The full list has 239 genomes. |
| `api_list_chromosomes_hg38.json` | https://api.genome.ucsc.edu/list/chromosomes?genome=hg38 | verbatim |
| `api_list_chromosomes_sacCer3.json` | https://api.genome.ucsc.edu/list/chromosomes?genome=sacCer3 | verbatim |
| `api_list_chromosomes_sacCer3_track_gold.json` | https://api.genome.ucsc.edu/list/chromosomes?genome=sacCer3;track=gold | verbatim |
| `api_list_chromosomes_GCF_000146045.2.json` | https://api.genome.ucsc.edu/list/chromosomes?genome=GCF_000146045.2 | verbatim |
| `api_list_genarkGenomes_GCF_000146045.2.json` | https://api.genome.ucsc.edu/list/genarkGenomes?genome=GCF_000146045.2 | verbatim |
| `api_list_genarkGenomes_first5.json` | https://api.genome.ucsc.edu/list/genarkGenomes?maxItemsOutput=5 | verbatim; not an anchor genome, kept to show the `clade` quirk |
| `api_findGenome_q_hg38.json`, `..._sacCer3.json`, `..._GCF_000146045.2.json`, `..._GCF_000001405.40.json` | https://api.genome.ucsc.edu/findGenome?q=<term> | verbatim |
| `api_list_hubGenomes_GCF_000146045.2.json` | https://api.genome.ucsc.edu/list/hubGenomes?hubUrl=https://hgdownload.soe.ucsc.edu/hubs/GCF/000/146/045/GCF_000146045.2/hub.txt | verbatim |
| `api_list_files_GCF_000146045.2.json` | https://api.genome.ucsc.edu/list/files?genome=GCF_000146045.2 | verbatim |
| `api_list_files_hg38_bigZips_excerpt.json`, `api_list_files_sacCer3_bigZips_excerpt.json` | https://api.genome.ucsc.edu/list/files?genome=hg38 (and sacCer3) | **Excerpt:** only `urlList` entries directly under `goldenPath/<db>/bigZips/`. `itemsReturned` is set to the number kept; `totalBytes` still covers the full listing. The full hg38 listing (41,168 files, 5.8 MB) is in the raw folder. |
| `bigZips_hg38.chromAlias.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chromAlias.txt | verbatim; legacy unlabeled format, 2021 |
| `bigZips_latest_hg38.chromAlias.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/latest/hg38.chromAlias.txt | verbatim; labeled, p14 |
| `bigZips_sacCer3.chromAlias.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/sacCer3/bigZips/sacCer3.chromAlias.txt | verbatim |
| `genark_GCF_000146045.2.chromAlias.txt` | https://hgdownload.soe.ucsc.edu/hubs/GCF/000/146/045/GCF_000146045.2/GCF_000146045.2.chromAlias.txt | verbatim |
| `database_hg38_chromAlias.txt`, `database_sacCer3_chromAlias.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/<db>/database/chromAlias.txt.gz | decompressed, otherwise verbatim |
| `bigZips_hg38.chrom.sizes`, `bigZips_latest_hg38.chrom.sizes`, `bigZips_sacCer3.chrom.sizes` | https://hgdownload.soe.ucsc.edu/goldenPath/<db>/bigZips/[latest/]<db>.chrom.sizes | verbatim |
| `genark_GCF_000146045.2.chrom.sizes.txt` | https://hgdownload.soe.ucsc.edu/hubs/GCF/000/146/045/GCF_000146045.2/GCF_000146045.2.chrom.sizes.txt | verbatim |
| `genark_GCF_000146045.2_hub.txt` | https://hgdownload.soe.ucsc.edu/hubs/GCF/000/146/045/GCF_000146045.2/hub.txt | verbatim; a single-file (useOneFile) hub |
| `bigZips_hg38_md5sum.txt`, `bigZips_sacCer3_md5sum.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/<db>/bigZips/md5sum.txt | verbatim |
| `genark_GCF_000146045.2_md5sum.txt` | https://hgdownload.soe.ucsc.edu/hubs/GCF/000/146/045/GCF_000146045.2/md5sum.txt | verbatim |
| `constructed/docs_genome_stanzas.txt` | — | **Constructed, not a served record.** It holds two genome stanzas copied word for word from the examples in https://genome.ucsc.edu/goldenPath/help/assemblyHubHelp.html: `GCF_000001405.39` (GRCh38.p13) and `GCF_000224145.3`. It is here because no human GenArk hub exists. It supplies the only examples of the `chromAlias` and `codonTable` settings. |

### spec/

| File | Source URL |
|---|---|
| `ucsc_rest_api_help.md` | https://genome.ucsc.edu/goldenPath/help/api.html |
| `trackDbHub_hub_and_genome_settings.md` | https://genome.ucsc.edu/goldenPath/help/trackDb/trackDbHub.html. **Excerpt:** the introduction (hub.txt, genomes.txt, useOneFile) plus the "General hub configuration settings" and "Assembly hub genome settings" sections. Track-type settings are left out. |
| `assemblyHubHelp.md` | https://genome.ucsc.edu/goldenPath/help/assemblyHubHelp.html (Assembly Hub User Guide; includes the chromAlias format) |
| `hgTrackHubHelp.md` | https://genome.ucsc.edu/goldenPath/help/hgTrackHubHelp.html |
| `hubBasics.md` | https://genome.ucsc.edu/goldenPath/help/hubBasics.html |
| `genomewiki_Assembly_Hubs.md` | https://genomewiki.ucsc.edu/index.php/Assembly_Hubs |
| `genomewiki_Chrom_Alias.md` | https://genomewiki.ucsc.edu/index.php?title=Chrom_Alias |
| `genark_hubs_index.md` | https://hgdownload.soe.ucsc.edu/hubs/ |
| `conditions_of_use.md` | https://genome.ucsc.edu/conditions.html |
| `hg38_bigZips_README.txt`, `sacCer3_bigZips_README.txt` | https://hgdownload.soe.ucsc.edu/goldenPath/<db>/bigZips/README.txt |
| `hg38_database_chromAlias.sql`, `hg38_database_chromInfo.sql` | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/{chromAlias,chromInfo}.sql (MySQL table definitions) |
| `kent/*.as`, `kent/*.sql` | https://raw.githubusercontent.com/ucscGenomeBrowser/kent/master/src/hg/lib/{dbDb,chromInfo,chromAlias,genark,assemblyList}.{as,sql}. These are the autoSql table definitions with a comment for each column. The `assemblyList` table backs `/findGenome`. |
| `samples/plantAraTha1_hub.txt`, `samples/plantAraTha1_genomes.txt` | https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/{hub,genomes}.txt |
| `samples/groupsExample_hub.txt`, `samples/groupsExample_genomes.txt` | https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubGroupings/groupsExample/{hub,genomes}.txt (its genomes.txt names `hg38`) |
| `samples/singleFileHubExample.txt` | https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubUseOneFile/singleFileHubExample.txt |
| `samples/genArkTrackHub_hub.txt` | https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubGenArkExample/genArkTrackHub/hub.txt |

**How the `.md` files were made.** Each help page was converted from HTML to
text with a simple tag-stripping script: tags were removed, and headings,
lists and table cells were marked. The text is the maintainer's own wording,
not a summary.

**API JSON keys were checked against the source code.** They match kent
`src/hg/hubApi/list.c` and `findGenome.c` (raw copies in the raw folder).

**Raw downloads** are in a local download folder (not in this repository). They include the full
`/list/ucscGenomes`, the full hg38 `/list/files`, the HTML originals, the kent
sources, and the GenArk `trackDb.txt`, `groups.txt` and assembly report. I
also tried to download hgcentral.sql
(https://hgdownload.soe.ucsc.edu/admin/hgcentral.sql). I stopped after 894 MB
and deleted it; the kent `.as` files give the same column definitions.

## Reuse terms

- **Data:** the [Conditions of Use](spec/conditions_of_use.md) say the
  sequence and annotation data are "freely available for any use". They ask
  you to credit the data contributors. Some genomes and tracks have their own
  restrictions (see the Credits pages).
- **Software:** the Genome Browser and Blat software are free for academic,
  nonprofit and personal use. Commercial use needs a license.
- **API limits:** scripts may make at most one request every 15 seconds and
  5,000 requests per day.
- **GenArk:** UCSC asks you to cite Clawson et al., *Genome Biol* 24, 217
  (2023).
- **Help pages:** copyright The Regents of the University of California. No
  separate license is stated for the documentation text.
