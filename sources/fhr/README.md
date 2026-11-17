# FHR: FAIR Header Reference genome

FHR is a metadata standard for one reference genome file. A record says what genome is in the
file (name, species, version, authors, accession, assembly statistics), and a checksum ties the
record to the exact bytes of one FASTA or GFA file. The same record can be written as JSON, YAML,
a header block inside the FASTA/GFA file, JSON-LD, or HTML microdata.

This folder also covers a second, related format: the **RefgetStore FHR sidecar** that gtars
writes and that refgenie's public stores serve, one JSON file per sequence collection.

Retrieved 2026-11-17.

## Who maintains it

- **FAIR-bioHeaders project** (GitHub org `FAIR-bioHeaders`). David Molik and Adam Wright hold
  schema authority (spec/README.upstream.md, "Project guidance").
  - Released spec: <https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification>, latest release
    **v0.6.0** (2026-11-13/14). FHR `schemaVersion` there is `"2.1"`; `fhr.json` is byte-identical
    to v0.5.0.
  - Development repo: <https://github.com/FAIR-bioHeaders/FHR-Specification>. The released repo
    used this name until 2026-10-14. Old `.../FHR-Specification/main/fhr.json` URLs still work
    and still identify FHR. On 2026-11-17 its `fhr.json` is identical to v0.6.0.
  - Paper: Wright A, ... Molik DC. "FAIR Header Reference genome: a TRUSTworthy standard."
    *Briefings in Bioinformatics* 25(3):bbae122, 2024. doi:10.1093/bib/bbae122 (PMC10981671).
    The abstract describes FHR as a FAIR/TRUST-guided metadata standard with "an extensive set of
    data serialisation methods and minimum data field requirements while still maintaining
    extensibility". I did not copy the paper; the spec docs below are more detailed and newer.
- **RefgetStore sidecar**: databio's gtars (`gtars-refget/src/store/fhr_metadata.rs`) defines the
  type; refgenie-registry (`stores/build_fhr.py`, `tools/genome_to_fhr.py`) writes the files for
  refgenie's public stores.

**Reuse terms.** The spec repo is MPL-2.0 for contributions from March 2025 on. Older USDA work
remains public domain in the United States (spec/LICENSE, spec/README.upstream.md "Licensing").
gtars' LICENSE file is BSD-style text, while gtars-refget's Cargo.toml declares MIT; only a short excerpt is copied here.

## Versions you will meet

| What a record says | Meaning |
|---|---|
| 2022 draft "FFRGS" (tag `1`) | Different field names: `author`, `assembler`, `place`, `taxa`, `physicalSample`, `licence`, `checksum: md5:...`. See spec/history/tag_1/. |
| `schema` = raw-main `fhr.json` URL and `schemaVersion: 1` (or `1.0`) | **FHR 1**. Releases up to v0.3.1. Readers check it against v0.3.1's schema (rule V6) and warn that it is deprecated. |
| `schemaVersion: "2.0"` | FHR 2.0 (v0.4.x). Stricter: closed nested objects, anchored patterns, canonical base64 checksum. |
| `schemaVersion: "2.1"` | FHR 2.1 (v0.5.0, v0.6.0). Adds extension fields: top-level keys starting `x-`. |

`schemaVersion` is the version of the metadata contract. The release tag (v0.6.0) is the version
of the spec repo. `version` is the version of the genome. These are three different things.

## Formats

| id | What it is | Adapter | Examples |
|---|---|---|---|
| `fhr_json` | Standalone JSON metadata file | read/write | upstream JSON examples; constructed hg38, R64-1-1 |
| `fhr_yaml` | Standalone YAML metadata file | read/write | upstream YAML examples (one with extension fields); constructed anchors |
| `fhr_fasta_header` | YAML in `;~` lines at the top of a FASTA file | read; write emits the header block only | upstream FASTA; constructed anchors (header only) |
| `fhr_gfa_header` | YAML in `#~` lines at the top of a GFA file | read; write emits the header block only | upstream GFA; constructed anchors (header only) |
| `fhr_jsonld` | The record plus the FHR `@context` and `@type` keys (rules J1-J9) | read/write | upstream JSON-LD; constructed anchors |
| `fhr_microdata` | HTML microdata with `data-fhr-type` annotations (rules M1-M5) | read/write | upstream HTML; constructed anchors |
| `fhr_schemaorg_export` | One-way schema.org export: the record split into typed nodes in an `@graph` | **no** (cannot be read back by design) | upstream export example |
| `fhr_refgetstore_sidecar` | gtars `FhrMetadata` JSON at `<store>/fhr/<seqcol digest>.fhr.json` | read/write | 6 real sidecars from refgenie's S3 stores |

Every format holds exactly one record. The JSON-LD and microdata forms cannot carry extension
fields (writers drop `x-` keys, J9/M5).

### Native record shape (adapter)

Records are flat dicts. Paths follow the notation of the upstream mapping tables
(spec/mappings/*.yml):

- fixed nested objects become dotted keys: `taxon.name`, `accessionID.url`, `vitalStats.N50`;
- lists of objects become one list per sub-key, aligned by position, with `None` where an item
  lacks the key: `metadataAuthor[].name`, `metadataAuthor[].uri`. `assemblySoftware[].commandLineOption`
  is a list of lists;
- `assemblySoftware` holds either the legacy string (key `assemblySoftware`) or the object list
  (keys `assemblySoftware[].*`);
- extension values (`x-...` keys, and the sidecar's non-FHR keys such as `assemblySource`) keep
  their exact key and value, even when the value is an object. Extension keys may contain dots, so
  they are never split.

fields.json lists the extension keys that appear in the example files. Any other `x-` key is also
legal in FHR 2.1 JSON/YAML/FASTA/GFA, and any top-level key is kept by gtars.

## Where each file came from (all retrieved 2026-11-17)

**spec/** (FHR-related files only; FHP/FHGFF3 schemas, the conformance suite, CEDAR templates and
the tool survey were left out):

| File | Source |
|---|---|
| `fhr.json`, `fhr_linkml.yml`, `fhr_mappings.yml` (MIxS/MIGS projection), `LICENSE`, `CITATION.cff`, `CHANGELOG.md`, `llms.txt` | `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.6.0/<same path>` |
| `README.upstream.md` | `.../v0.6.0/README.md` |
| `schemas/core.yaml`, `schemas/shared.yaml`, `schemas/versions.json` | `.../v0.6.0/schemas/` (LinkML core shared by all header types; release-to-schemaVersion table) |
| `docs/*.md` (FORMAT, SCHEMA-VERSIONS, SCHEMA-CHANGES-v0.4, JSONLD, MICRODATA, MAPPINGS, TERMS, SCHEMAORG-EXPORT, SCHEMA-GAP-AUDIT, insdc-coverage, PROFILES), `docs/mappings/README.md` | `.../v0.6.0/docs/` |
| `jsonld/fhr.context.jsonld` | `.../v0.6.0/jsonld/` |
| `mappings/fhr-jsonld-dcmi.yml`, `mappings/fhr-schemaorg-export.yml` | `.../v0.6.0/mappings/` (field-by-field crosswalks to JSON-LD/Dublin Core and to schema.org) |
| `profiles/insdc-fhr.yaml`, `agbiodata-fhr.yaml`, `README.md` | `.../v0.6.0/profiles/` (draft community profiles; not adopted) |
| `history/fhr_v0.3.1.json` | `.../v0.3.1/fhr.json`, the last FHR 1 contract (used for FHR 1 records, rule V6) |
| `history/fhr_2026-02-08_ee8dc12365.json` | `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/ee8dc12365/fhr.json`, identical to refgenie-registry's vendored copy |
| `history/tag_1/` | `https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/1/` (2022 FFRGS draft: `ffrgs.json`, `README.md`, `examples/`). Its `example.json` is not valid JSON (a missing comma). |
| `refgetstore/gtars_fhr_metadata_excerpt.rs` | Lines 1-178 (types, serde attributes, sidecar extension) of `gtars-refget/src/store/fhr_metadata.rs` in the local clone `repos/gtars` (github.com/databio/gtars), commit `bffa41fa` (branch feat/fasta-export); the file is identical on origin/master. |
| `refgetstore/refgenie_registry_fhr_alignment.md` | The "FHR alignment" section of `schema/README.md` in `repos/refgenie-registry` (github.com/refgenie/refgenie-registry), commit `1647661d`. Gives the registry YAML to sidecar mapping table. |

**examples/**

| File | Source |
|---|---|
| `upstream_*` | `https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.6.0/examples/<name without upstream_>`. Official examples. Their content is synthetic (a 16-base "genome", placeholder checksum and seqcol_id in the standalone forms); the FASTA/GFA checksums are real and verify. |
| `sidecar_hg38_jungle_EiFob05aCWgVU_B_Ae0cypnQut3cxUP1.fhr.json` | `https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle/fhr/EiFob05aCWgVU_B_Ae0cypnQut3cxUP1.fhr.json` (human hg38 = GRCh38 no-alt analysis set, GCA_000001405.15) |
| `sidecar_GRCh38.p14-ncbi_jungle_u1HyLgIlq8M_XvEwy0oGqAvKGHJMGtxH.fhr.json` | `.../refget-store/jungle/fhr/u1HyLgIlq8M_XvEwy0oGqAvKGHJMGtxH.fhr.json` (NCBI GCF_000001405.40 genomic) |
| `sidecar_GRCh38-ensembl81_plantcore_EpUZgR6X_cEphzw9gboSc86rumZpXthc.fhr.json` | `.../refget-store/plantcore/fhr/EpUZgR6X_cEphzw9gboSc86rumZpXthc.fhr.json` (Ensembl 81 GRCh38 top level) |
| `sidecar_R64-1-1_plantcore_ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.fhr.json` | `.../refget-store/plantcore/fhr/ia9g4Myony-xxLsSc7eQOC_NdClGgPGu.fhr.json` (yeast R64-1-1, Ensembl names I..XVI, Mito) |
| `sidecar_sacCer3_igenomes_8zSJ7M2oerPcCKc8x310hjyfB5u8SJNJ.fhr.json` | `.../refget-store/igenomes/fhr/8zSJ7M2oerPcCKc8x310hjyfB5u8SJNJ.fhr.json` (UCSC sacCer3 via iGenomes, chrI..chrXVI, chrM) |
| `sidecar_sacCer-ncbi-build3.1_igenomes_WdaV-flgP58fZtp5r1I08coS-koI_71a.fhr.json` | `.../refget-store/igenomes/fhr/WdaV-flgP58fZtp5r1I08coS-koI_71a.fhr.json` (iGenomes NCBI build3.1) |
| `constructed/` | **Written by me, not served by anyone.** See below. |

How I found the sidecars: `https://api.refgenie.org/v4/aliases/<name>` gives the digest
(hg38 and GRCh38 both resolve to `EiFob05...`; R64-1-1 to `ia9g4My...`; sacCer3 to `8zSJ7M2...`),
`https://api.refgenie.org/v4/genomes/<digest>` gives `refget_store_url`, and the sidecar is at
`<refget_store_url>fhr/<digest>.fhr.json`. The extra human and yeast records came from
`/v4/genomes?taxon_id=9606` and `?taxon_id=4932`. Bucket listing is denied, so I fetched known
digests only. The API also embeds the same FHR object under `fhr` in `/v4/genomes/<digest>` and
`/v4/aliases/<name>`; those API responses belong to the refgenie source.

**Constructed anchors** (`examples/constructed/hg38.*`, `R64-1-1.*`). No FHR maintainer or genome
provider publishes an FHR record for GRCh38 or S288C, so there is no real upstream-form record for
the anchors. I re-expressed the two real refgenie sidecars in the upstream FHR 2.1 forms with the
adapter (scratch script, not kept): `schema` = w3id v0.6.0 URL, `schemaVersion` = `"2.1"`, the
sidecar's genome, genomeSynonym, taxon, version, accessionID, documentation and relatedLink
copied as is, `seqcol_id` = the digest from the sidecar's file name, and refgenie's
`assemblySource`/`assemblyLevel` moved to `x-refget-assemblySource`/`x-refget-assemblyLevel`
(the JSON-LD and HTML forms drop these, as the rules require). I added no other values, so these
records are **not schema-valid**: they lack the required `metadataAuthor`, `assemblyAuthor`,
`dateCreated` and `masking` (and `checksum` in the standalone forms). The FASTA and GFA files are
header blocks with no sequence lines; their checksum is the real FHR checksum of those header-only
bytes, so it does not identify the hg38 or R64-1-1 sequences.

**Raw downloads** are in a local download folder (not in this repository) (API responses, repo trees, the v0.3.1 and
historical schemas, the 81 valid FASTA/GFA/JSON-LD/microdata conformance vectors and their
manifest, the store manifests `rgstore.json`). Nothing big was excerpted; I chose which small files
to keep.

## What identifies a record

- **Upstream FHR**: the record describes one file. Its `checksum` is base64 SHA-512/256 over the
  exact (decompressed) bytes of the FASTA/GFA except the root `checksum` line (rules R1-R5), so
  metadata, comments and sequence all count. Change one header character and the checksum changes.
  A standalone JSON/YAML record has no identity of its own unless its checksum points at a file.
  `seqcol_id` (optional, user supplied, never computed or verified by FHR) names the sequence
  collection; `accessionID` names the assembly.
- **Sidecar**: the seqcol digest of the collection, which is the file name, not a JSON key. One
  sidecar per collection per store.

## Levels

- assembly: `genome`, `genomeSynonym`, `taxon.*`, `version`, `assemblyAuthor[]`, `dateCreated`,
  `voucherSpecimen`, `accessionID.*`, `instrument`, `scholarlyArticle`, `identifier`, `funding`,
  `vitalStats.*`, `assemblySoftware*`, `assemblyProtocol`; sidecar `assemblyLevel`.
- collection: `seqcol_id`; sidecar file-name digest (`seqcolDigest`) and `assemblySource`.
- copy: `checksum`, `masking`.
- other: `schema`, `schemaVersion`, `metadataAuthor[]` (who wrote the record), `documentation`,
  `relatedLink`, `reuseConditions`, sidecar `license`.
- sequence and deployment: nothing. FHR has no per-sequence fields.

## Quirks that matter for mapping

1. **One record, mixed levels.** FHR's descriptive fields are about the assembly, but its identity
   (the checksum) is about one file, and `masking` is about one file too. Soft-masked and unmasked
   copies have the same seqcol digest but different FHR checksums.
2. **`genome` is not a stable kind of name.** The upstream example uses a long descriptive name.
   refgenie writes collection names (`hg38`, `sacCer3`, `R64-1-1`, `hg38_p14_genomic`) and puts other
   names in `genomeSynonym`.
3. **`accessionID` came from a field called `place`.** The 2022 draft had
   `place: {name: PBARC, url: ...ars.usda.gov...}`; today's example has exactly those values under
   `accessionID`, and the schema description is garbled. Real users (refgenie) put the INSDC
   accession (`GCA_000001405.15`) there. Treat `accessionID.name` as "an accession, maybe".
4. **`version` is the assembly version**, free text. refgenie writes the accession version
   (`"15"`, `"2"`, `"40"`) and leaves it out when there is no accession.
5. **The schema is closed.** Unknown top-level keys are invalid, except `x-` keys from FHR 2.1.
   From 2.0, unknown keys inside `taxon`, authors, `accessionID`, `vitalStats` and software objects
   are invalid too.
6. **Three checksum styles.** FHR: base64 SHA-512/256 of file bytes (44 characters, ends `=`).
   Old FHR docs: `md5:<hex>`. The refgenie registry exporter: `sha256:<hex of the FASTA>`. None is a
   refget/seqcol digest (sha512t24u, base64url, 32 characters).
7. **YAML typing (R12).** `schemaVersion: '2.0'` must be quoted (unquoted it is the number 2.0).
   Dates stay strings. Values like `yes`, `010`, `1e3` must be quoted. The adapter reads dates as
   strings and quotes these on write.
8. **FASTA headers break tools.** Many FASTA tools (samtools faidx included) need the `;~` lines
   stripped first (spec docs/TOOL_COMPATIBILITY.md upstream, not copied). Values with `>` or `@`
   are written with `\x3E` / `\x40` escapes (R11) because some FASTA readers start a record at
   those characters.
9. **JSON-LD and microdata are lossy for extensions**, and JSON-LD writes a URL `documentation`
   as `subjectOf`. The schema.org export is one-way.
10. **Taxon.** `taxon.uri` is an identifiers.org NCBI Taxonomy URI. refgenie's yeast sidecars use
    4932 (*S. cerevisiae*), not 559292 (strain S288C), and have no strain field. FHR has no strain
    field either (only free-text `voucherSpecimen`).
11. **Required but empty is allowed by the 2.x schemas** (empty `genome`, empty author list), but
    such records are not conforming (SCHEMA-VERSIONS.md); FHR 3.0 plans to reject them.

## The RefgetStore sidecar variant (gtars)

- Type: `FhrMetadata` in gtars, serde camelCase. Every field is optional; gtars does not enforce
  the FHR schema. Named fields: `schema`, `schemaVersion` (a JSON number), `genome`, `taxon {name,
  uri}`, `version`, `metadataAuthor[] {name, uri}`, `assemblyAuthor[] {name, uri}`, `dateCreated`,
  `voucherSpecimen`, `masking`, `checksum`, `genomeSynonym`, `accessionID {name, url}`,
  `instrument`, `scholarlyArticle`, `documentation`, `identifier`, **`license`** (not an FHR field;
  FHR uses `reuseConditions`), `relatedLink`, `funding`, `vitalStats {L50, N50, L90,
  totalBasePairs, numberContigs, numberScaffolds, readTechnology}`.
- `extra`: a `#[serde(flatten)]` map that keeps every other **top-level** key verbatim. That is how
  refgenie's `assemblySource` and `assemblyLevel` survive, and also any upstream field gtars lacks
  (`reuseConditions`, `assemblySoftware`, `assemblyProtocol`, `seqcol_id`, `x-...`).
- **Nested keys gtars does not know are dropped** when it loads a file: author `nameType`,
  `vitalStats.N90`, `gcContent` and the `scaffold*` statistics. An FHR 2.x record loses them on a
  pass through a RefgetStore.
- `seqcolDigest`: the struct has `seqcol_digest` marked `#[serde(skip)]`; it never appears in the
  JSON. The digest is the file name `<digest>.fhr.json` under `<store>/fhr/`. In fields.json it is
  listed as `seqcolDigest` with this note; `read()` cannot see it (text only), and
  `refmeta.formats.fhr.sidecar_digest(filename)` extracts it.
- Layout: written with `serde_json::to_string_pretty` (2-space indent, no final newline), named
  fields in struct order, then `extra` keys in `HashMap` order, which is not stable: the hg38
  sidecar has `assemblyLevel` before `assemblySource`, R64-1-1 the reverse. The store manifest
  `rgstore.json` carries `fhr_digest`, a SHA-256 over all sidecars.
- refgenie-registry writes: `schema` = raw-main FHR-Specification URL, `schemaVersion: 1.0`,
  `genome` = the registry name, `genomeSynonym` = synonyms (can repeat a value: the GRCh38.p14
  sidecar lists the same synonym twice), `taxon` from its species list, `documentation`,
  `accessionID {name, url}`, `version` = accession version, `assemblySource` (not normalized:
  `ncbi`, `NCBI`, `Ensembl`, `UCSC`...), `assemblyLevel` (lowercased NCBI value, from a static
  map, never guessed). refgenie's `apply_fhr` reads `taxon`, `genomeSynonym`, `documentation`,
  `accessionID.name`, `assemblySource`, `assemblyLevel`; not `genome` or `version`.
- **Validity.** Raw-main URL plus `schemaVersion` 1.0 makes these FHR 1 records (rule V6), checked
  against v0.3.1. They fail it: no `metadataAuthor`, `assemblyAuthor`, `dateCreated`, `masking` or
  `checksum` (the sacCer3, Ensembl 81 and NCBI build3.1 records have no `version` either), and `assemblySource`/
  `assemblyLevel` are unknown keys. Under FHR 2.1 they would need a string `schemaVersion` and
  `x-` prefixes. The upstream extension example already uses `x-refget-assemblySource` and
  `x-refget-commonName`. The registry validates its exports against a relaxed profile instead
  (spec/refgetstore/refgenie_registry_fhr_alignment.md).

## Vendored schema vs upstream

`repos/refgenie-registry/schema/fhr.schema.json` is byte-identical to upstream
`FHR-Specification` commit `ee8dc12365` (2026-02-08), as the registry README says
(copy: spec/history/fhr_2026-02-08_ee8dc12365.json). That is an FHR 1 schema from before v0.3.

- vs **v0.3.1** (the FHR 1 contract readers now use for these records): v0.3.1 adds
  `assemblySoftware`, `assemblyProtocol`, `seqcol_id`, `vitalStats.N90` and `gcContent`, gives the
  ORCID definition `type: string`, and pins the checksum pattern to exactly 44 characters.
- vs **v0.6.0** (current, FHR 2.1): `schemaVersion` becomes a string enum `"2.0"|"2.1"`; patterns
  are anchored (taxon URI, ORCID, masking, identifier `^[A-Za-z0-9._-]+:.+$`, DOI
  `^10\.[0-9]+(\.[0-9]+)*/\S+$`); the checksum must be canonical padded base64 of 32 bytes; nested
  objects get `additionalProperties: false`; authors gain `nameType`; `vitalStats` gains N90,
  scaffoldN50/N90/L50/L90 and gcContent, all with `minimum: 0`; `x-` extension keys are allowed by
  `patternProperties` (but not when `schemaVersion` is `"2.0"`); key names may not contain a newline.
  Required fields are the same 10 in every FHR 1 and FHR 2 schema. `$id` is the raw-main URL in all of them.
- The registry relaxes the vendored copy further (no required list, adds `license`, accepts
  `sha256:<hex>` checksums, allows `assemblySource`/`assemblyLevel`).

## Adapter notes and limits (`tools/refmeta/formats/fhr.py`)

- Reads text only: no gzip/BGZF, so compress-wrapped FASTA/GFA must be decompressed first.
- FASTA/GFA `write()` emits only the header block, with the checksum line last (R3) and the
  record's checksum copied, not recomputed. To attach a header to real sequences, use the
  FAIR-bioHeaders toolkit (`bioheaders combine`), which recomputes it. `file_checksum(text, prefix)`
  computes the FHR checksum when Python's hashlib has `sha512_256`.
- The JSON, YAML, JSON-LD and microdata writers reproduce `upstream_example.fhr.{json,yaml,jsonld}`,
  `upstream_minimal.fhr.{json,jsonld}` and `upstream_example.microdata.fhr.html` byte for byte; the
  sidecar writer reproduces all six real sidecars byte for byte.
- Checked against the 81 valid FASTA, GFA, JSON-LD and microdata conformance vectors of v0.6.0
  (kept in `a local download folder (not in this repository)conformance/`): 80 read to the expected metadata and checksum.
  Expanded-form JSON-LD (full IRIs, no context) is not supported.
- Microdata parsing handles the common implied end tags (p, li, dt/dd, table cells) but is not a
  full HTML5 parser.
- No schema validation, duplicate-key (R8) or YAML 1.1/1.2 ambiguity (R12) checks on read.

## Related, not collected here

FAIR-bioHeaders also defines FHP (protein FASTA headers), FHGFF3 (a GFF3 annotation header that
links an annotation to its genome by FHR checksum, or by accession plus seqcol digest), and drafts
FHT (transcriptome) and FHGM (gene models). FHGFF3 is the closest to refmeta's interests if
annotation-to-genome links come up later. The toolkit is
<https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools> (`bioheaders`).
