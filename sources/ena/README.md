# ENA: European Nucleotide Archive assembly and sequence records

## What it is

The European Nucleotide Archive (ENA) is the European member of the
International Nucleotide Sequence Database Collaboration (INSDC). It is run by
the ENA team at EMBL-EBI (Hinxton, UK). The other two members are NCBI GenBank
(USA) and DDBJ (Japan). The three exchange data every day, so they hold the
same records under the same accessions.

What that means for refmeta:

- **GCA_ assembly accessions and sequence accessions (CM000663.2, BK006935.2)
  are INSDC-wide.** ENA, GenBank and DDBJ use the same values. NCBI's Genome
  Collections (GenColl) assigns the GCA, including for assemblies submitted to
  ENA (see `spec/docs_webin_genome_assembly.rst.txt`, "released on agreement
  with GenCol").
- **RefSeq is not INSDC.** GCF_ accessions and NC_/NT_ sequence accessions
  never appear in ENA. Neither do UCSC-style names (`chr1`,
  `chr1_KI270706v1_random`). The `ncbi` source covers those.
- **DDBJ** serves the same INSDC sequence records but has no separate
  assembly-report format worth adding here. It was not collected.

ENA serves assembly metadata through four channels, plus one for sequences
and one for submissions. Each has its own shape, so each is its own format.

## Formats

| Format id | What | Record = | Record key | Levels |
|---|---|---|---|---|
| `ena_assembly_xml` | Browser API XML, `/ena/browser/api/xml/<GCA>` | one assembly version | `@accession` (GCA_000001405.15) | assembly, collection (chromosome list), copy (WGS links) |
| `ena_browser_summary` | Browser API JSON, `/ena/browser/api/summary/<GCA>` | one assembly version | `accession` + `version` | assembly, collection |
| `ena_portal_assembly` | Portal API `search?result=assembly&fields=all` (TSV or JSON) | one assembly version | `assembly_set_accession` | assembly, collection |
| `ena_portal_sequence` | Portal API `search?result=sequence&fields=all` (TSV) | one INSDC sequence | `sequence_accession` | sequence (with md5) |
| `ena_sequence_report` | FTP `<GCA>_sequence_report.txt` | one sequence of the assembly | `accession` | sequence, collection (assembly units) |
| `ena_regions` | FTP `<GCA>_regions.txt` | one alt-locus scaffold placement | `accession` | sequence |
| `ena_refget_metadata` | CRAM Reference Registry (refget 2.0), `/ena/cram/sequence/<id>/metadata` | one sequence | `metadata.md5` | sequence |
| `ena_webin_chromosome_list` | Webin-CLI submission chromosome list | one chromosome | `OBJECT_NAME` | sequence (naming rules) |
| `ena_webin_unlocalised_list` | Webin-CLI submission unlocalised list | one unlocalised sequence | `OBJECT_NAME` | sequence |

All nine have adapters in `tools/refmeta/formats/ena.py`. `fields.json`
lists 313 fields.

### How the adapter names fields

- XML: a path relative to `<ASSEMBLY>`, with `/` between elements and `@`
  for attributes (`TAXON/TAXON_ID`, `IDENTIFIERS/SUBMITTER_ID/@namespace`).
  `ASSEMBLY_ATTRIBUTE` TAG/VALUE pairs become `ASSEMBLY_ATTRIBUTES/<TAG>`.
  Repeated groups (`CHROMOSOMES/CHROMOSOME`, `WGS_SET`,
  `ASSEMBLY_LINKS/ASSEMBLY_LINK`) are lists of objects. `fields.json` lists
  their inner fields as `<group>/<inner key>`.
- JSON: `.` between keys (`metadata.md5`). Summary `attributes` tag/value
  pairs become `attributes.<tag>`.
- TSV: the column name, exactly as served.
- Empty values, `NA` in the sequence report's replicon columns, and nulls in
  the refget metadata are dropped on read and put back on write.
- A few values are typed: taxon IDs, lengths, versions and digit-only
  statistics become integers; `germline` and `environmental_sample` become
  booleans; the portal assembly `sequence_accession` (`;`-separated) becomes
  a list. Everything else stays a string as served.

## Where every file came from

All files were downloaded with curl on 2026-11-17. The full raw set,
including extra assemblies used only for checking, is in
a local download folder (not in this repository). Every file here is a whole, unedited download,
except where the table says otherwise. Nothing was cut out of an example.

### spec/

| File | URL | Notes |
|---|---|---|
| `ENA.assembly.xsd` | https://ftp.ebi.ac.uk/pub/databases/ena/doc/xsd/sra_1_5/ENA.assembly.xsd | Schema of the assembly XML. Server date 2026-02-04. Apache-2.0 header. |
| `SRA.common.xsd` | https://ftp.ebi.ac.uk/pub/databases/ena/doc/xsd/sra_1_5/SRA.common.xsd | Imported by ENA.assembly.xsd (ObjectType, IdentifierType, LinkType, AttributeType). Also defines `ReferenceAssemblyType`/`ReferenceSequenceType`, see "Not collected". |
| `SRA.analysis.xsd` | https://ftp.ebi.ac.uk/pub/databases/ena/doc/xsd/sra_1_5/SRA.analysis.xsd | Submission-side `SEQUENCE_ASSEMBLY` analysis: declares TYPE, COVERAGE, PROGRAM, PLATFORM, which the served assembly XML uses but ENA.assembly.xsd does not declare. |
| `browser_api_openapi.json` | https://www.ebi.ac.uk/ena/browser/api/v3/api-docs | OpenAPI 3 for the Browser API; `Summary`, `Chromosome`, `Attribute`, `Link` schemas describe the summary JSON. |
| `portal_api_openapi.json` | https://www.ebi.ac.uk/ena/portal/api/api-docs | OpenAPI 3 for the Portal API (search, returnFields). |
| `portal_returnFields_assembly.tsv` | https://www.ebi.ac.uk/ena/portal/api/returnFields?result=assembly | Name, description and type of all 117 assembly result fields. |
| `portal_returnFields_sequence.tsv` | https://www.ebi.ac.uk/ena/portal/api/returnFields?result=sequence | Same for the 65 sequence result fields. |
| `cram_refget_service-info.json` | https://www.ebi.ac.uk/ena/cram/sequence/service-info | Refget service-info: refget 2.0.0, algorithms `md5` only, identifier_types `insdc`. |
| `docs_browser-api.rst.txt` | https://raw.githubusercontent.com/enasequence/read_docs/master/retrieval/programmatic-access/browser-api.rst | ENA docs source (read_docs repo). |
| `docs_ena-ftp-structure.rst.txt` | https://raw.githubusercontent.com/enasequence/read_docs/master/retrieval/file-download/ena-ftp-structure.rst | Says where the assembly reports live on FTP. There is no column-by-column spec for the sequence report or regions file; descriptions in fields.json come from the data and from NCBI's equivalent report. |
| `docs_webin_fileprep_assembly.rst.txt` | https://ena-docs.readthedocs.io/en/latest/_sources/submit/fileprep/assembly.rst.txt | Chromosome list and unlocalised list file formats, chromosome naming rules, term definitions (including "assembly chain"). |
| `docs_webin_genome_assembly.rst.txt` | https://ena-docs.readthedocs.io/en/latest/_sources/submit/assembly/genome.rst.txt | Webin-CLI genome submission: manifest fields, assembly levels, accession numbers. |

The chromosome-list column handling in the adapter (topology prefix split on
`-`, whitespace columns, 3 or 4 columns) follows ENA's own reader,
https://github.com/enasequence/sequencetools/blob/master/src/main/java/uk/ac/ebi/embl/flatfile/reader/genomeassembly/ChromosomeListFileReader.java
(read as text only, kept in the raw folder, never run).

### examples/ (real records, both anchors)

| File | URL |
|---|---|
| `assembly_xml_GCA_000001405.15.xml`, `assembly_xml_GCA_000146045.2.xml` | https://www.ebi.ac.uk/ena/browser/api/xml/GCA_000001405.15 (and GCA_000146045.2) |
| `browser_summary_GCA_000001405.15.json`, `browser_summary_GCA_000146045.2.json` | https://www.ebi.ac.uk/ena/browser/api/summary/GCA_000001405.15 (and .2) |
| `portal_assembly_<GCA>.tsv` / `.json` | https://www.ebi.ac.uk/ena/portal/api/search?result=assembly&query=assembly_set_accession%3D%22GCA_000001405.15%22&fields=all&format=tsv (and `format=json`; same for GCA_000146045.2) |
| `portal_sequence_<GCA>.tsv` | POST https://www.ebi.ac.uk/ena/portal/api/search with `result=sequence`, `fields=all`, `format=tsv`, `includeAccessions=<every accession in that assembly's sequence report>`. 455 rows (human), 16 rows (yeast). |
| `sequence_report_GCA_000001405.15.txt` | https://ftp.ebi.ac.uk/pub/databases/ena/assembly/GCA_000/GCA_000001/GCA_000001405.15_sequence_report.txt |
| `sequence_report_GCA_000146045.2.txt` | https://ftp.ebi.ac.uk/pub/databases/ena/assembly/GCA_000/GCA_000146/GCA_000146045.2_sequence_report.txt |
| `regions_GCA_000001405.15.txt` | https://ftp.ebi.ac.uk/pub/databases/ena/assembly/GCA_000/GCA_000001/GCA_000001405.15_regions.txt (yeast has no regions file: it has no alt loci) |
| `refget_metadata_<GCA>.jsonl` | https://www.ebi.ac.uk/ena/cram/sequence/insdc:<accession>/metadata, once per assembled molecule (25 human, 16 yeast). Each line is one response exactly as served; the lines are joined into one file. |

### examples/other/ (real records, not anchors)

The anchors are NCBI-submitted curated references, so they lack the elements
that ENA-submitted WGS assemblies carry (ASSEMBLY_TYPE, PLATFORM, PROGRAM,
non-zero COVERAGE, SAMPLE_REF, WGS_SET, ASSEMBLY_LINKS). To give those fields a
real example value, one ENA-submitted reference was added: maize
Zm-B73-REFERENCE-NAM-5.0, GCA_902167145.1.

- `assembly_xml_GCA_902167145.1.xml`: https://www.ebi.ac.uk/ena/browser/api/xml/GCA_902167145.1
- `browser_summary_GCA_902167145.1.json`: https://www.ebi.ac.uk/ena/browser/api/summary/GCA_902167145.1
- `portal_assembly_GCA_902167145.1.tsv`: portal search as above with `assembly_set_accession="GCA_902167145.1"`

### examples/constructed/ (hand-made, NOT real records)

Webin chromosome and unlocalised lists are files a submitter uploads. ENA
never serves them back, and GRCh38 and R64 were submitted through NCBI anyway,
so no real one exists. These were generated from the real ENA sequence
reports above: OBJECT_NAME = `sequence-name`, CHROMOSOME_NAME =
`replicon-name`, type `linear-chromosome`, and MT as
`circular-chromosome Mitochondrion`. Yeast has no unlocalised sequences, so
there is no yeast unlocalised list.

- `webin_chromosome_list_GCA_000001405.15.txt`, `webin_chromosome_list_GCA_000146045.2.txt`
- `webin_unlocalised_list_GCA_000001405.15.txt`

## What identifies a record

- **Assembly version:** the versioned GCA (`GCA_000001405.15`). ENA calls the
  part before the dot the "assembly chain" (`GCA_000001405`); every patch
  release of GRCh38 is a new version of the same chain (.15 = GRCh38, .29 =
  GRCh38.p14).
- **Sequence:** the versioned INSDC accession (`CM000663.2`). Its content is
  identified by `sequence_md5` / `metadata.md5`.
- **Sequence name inside an assembly:** `sequence-name` in the sequence
  report, unique within one assembly.

## Levels covered

- **assembly:** well covered by all three assembly formats.
- **collection:** partly. ENA gives the chromosome list (name to accession),
  the assembly units (Primary Assembly, ALT_REF_LOCI_n, non-nuclear) and the
  full sequence list (sequence report). It has no seqcol digests and no
  alternate naming styles: only INSDC names (`1`, `MT`, `I`) and GRC
  sequence names (`HSCHR1_CTG1_UNLOCALIZED`).
- **sequence:** well covered: accession, name, length, role, md5, topology,
  replicon, alt-locus placement.
- **copy:** thin. Only `ASSEMBLY_LINKS` (WGS set FASTA and flat file URLs, no
  checksums), and only for WGS assemblies. ENA also serves FASTA by
  URL pattern, `https://www.ebi.ac.uk/ena/browser/api/fasta/<accession>`,
  with headers like `>ENA|BK006935|BK006935.2 TPA_inf: Saccharomyces
  cerevisiae S288C chromosome I, complete sequence.` There is no file
  checksum for these.
- **deployment:** none.

## Quirks that matter for mapping

1. **Versioned or not depends on the endpoint.** XML `@accession` is
   versioned (`GCA_000001405.15`). Summary `accession`, portal `accession` and
   portal `assembly_accession` are the unversioned chain (`GCA_000001405`);
   the version is separate (`version` = 15) and the versioned form is
   `assembly_set_accession`. On sequence records, portal `assembly_accession`
   is also unversioned, so it cannot tell GRCh38 from GRCh38.p14.
2. **Query by `assembly_set_accession`, not `assembly_accession`.**
   `assembly_accession="GCA_000001405.15"` returns nothing;
   `assembly_accession="GCA_000001405"` returns all versions. A text query
   `assembly_name="GRCh38"` also matches GRCh38.p1 to .p14.
3. **The XML chromosome list collapses ranges.** `<CHROMOSOME
   accession="KI270706.1-KI270714.1">` stands for 9 sequences. The summary
   keeps the range string inside `chromosomes.accession` and gives a `count`.
   Unlocalised scaffolds share their chromosome's NAME, so NAME is not unique
   in the XML.
4. **"All sequences" means different things.** XML chromosome list and
   portal `sequence_accession`: 67 GRCh38 sequences (25 assembled + 42
   unlocalised). Sequence report: all 455 (adds 127 unplaced and 261 alt
   scaffolds). Portal sequence records with `assembly_accession` filled: 69.
5. **The yeast GCA has no mitochondrion.** ENA's R64 (GCA_000146045.2) has 16
   nuclear chromosomes only. NCBI's GCA assembly report lists MT with GenBank
   accession `na`, and the RefSeq side adds NC_001224.1. So a sacCer3 or
   RefSeq-based set with chrM has one more sequence than anything from ENA.
6. **Spelling: `unlocalised-scaffold`** (ENA) vs `unlocalized-scaffold`
   (NCBI assembly_report.txt). Same meaning.
7. **INSDC chromosome names never contain "chr".** Webin rejects or fixes
   names with `chr`, `chrom`, `chromosome`, `plasmid`, `linkage group`. So
   `chr1`, `chrM` are never INSDC names; INSDC uses `1`, `MT`.
8. **The served XML does not validate against the published XSD.**
   ASSEMBLY_TYPE, PLATFORM, PROGRAM and COVERAGE are served but not declared
   in ENA.assembly.xsd. WGS_SET/VERSION is `xs:integer` but served as `01`.
9. **COVERAGE 0 means unknown** for the curated anchors. The summary omits
   `assemblyCoverage` in that case.
10. **Strain-level taxon for yeast.** R64 uses taxon 559292 ("Saccharomyces
    cerevisiae S288C"), not the species taxon 4932.
11. **Portal `status` is declared "number" but served as text** (`public`).
    The summary has both `status` (4) and `statusDescription` (`public`).
12. **ENA refget is md5-only.** `ga4gh` and `trunc512` are always null, so
    ENA cannot answer refget lookups by GA4GH `SQ.` digest. Lookups work by
    md5 or `insdc:<accession.version>`; a bare accession gives 404. Aliases
    hold only the INSDC accession, never chromosome names.
13. **md5 agrees everywhere.** For all 41 assembled molecules checked, portal
    `sequence_md5`, refget `md5`, and lengths in the sequence report, portal
    and refget agree. One GRCh38 alt scaffold (KI270825.1) has no md5 in the
    portal.
14. **The sequence report has no assembly accession inside it.** It is only
    in the file name (`GCA_000001405.15_sequence_report.txt`). The adapter
    reads text, so it cannot recover it.
15. **Assembly statistics** (`ASSEMBLY_ATTRIBUTES/*`) use NCBI's names and
    match NCBI's values. ENA does not document them. `n50` looks like
    scaffold N50; `count-regions` (207 for GRCh38) matches neither the 178
    distinct regions nor the 261 rows in regions.txt.
16. **`newAccession`** in the summary points to the newest version of the
    chain (GRCh38 .15 points to .29). It is the only place ENA says "this is
    superseded".

## Reuse terms

The XSD files carry an Apache License 2.0 header (Copyright 2018 EMBL-EBI).
The OpenAPI documents and ENA docs pages state no license in the files
retrieved. INSDC records themselves are distributed without use
restrictions under the INSDC policy, and EMBL-EBI's general terms of use
apply to the services. Neither of those was saved here.

## Not collected

- **How ENA analyses name reference sequences.** `SRA.common.xsd` defines
  `ReferenceAssemblyType` (STANDARD `refname`/`accession`, or CUSTOM with URL)
  and `ReferenceSequenceType` (per-sequence `accession` plus `label`, "the SQ
  label in BAM"). This is ENA's mapping from BAM/VCF sequence names to INSDC
  accessions, close to the "deployment" level. No real record was fetched,
  because a portal search for analyses tied to the anchors found none quickly.
  Worth a look later.
- **Webin genome manifest** (ASSEMBLYNAME, ASSEMBLY_TYPE, COVERAGE, PROGRAM,
  PLATFORM, ...). Described in `spec/docs_webin_genome_assembly.rst.txt`, but
  no adapter: its fields come back as the XML elements of the same name.
- EMBL flat files, FASTA files and the per-sequence XML. These are sequence
  data, not metadata records.
- The generic Browser API `Summary` schema has 43 properties shared by every
  record type. `fields.json` lists only the ones assembly summaries actually
  use.
