# refmeta core model: proposal

Status: draft for review, 2026-11-17. Files in this folder: `core.schema.json` (the model),
`namespaces.yaml` (the official namespaces), `CROSSWALK_FORMAT.md` (how a format maps to it),
`crosswalk/*.yaml` (100 crosswalks, one per format with an adapter), `coverage.md` (what each
format fills).

Decided since the first draft (2026-11-17): an assembly has a list of accessions, each with a
namespace, instead of `accession` and `pairedAccession` slots; and namespaces come from an
official list in `namespaces.yaml`, with custom ones allowed.

## The short version

One refmeta record is a bundle with five optional blocks, one per level: **assembly**,
**collection**, **sequences**, **copies** and **deployments**. Each block has its own
identifier: an accession, a seqcol digest, a refget digest, a location plus checksum, a
system plus key. A source fills only the blocks it knows about. Names are split into
**aliases** (point to exactly one thing in their namespace) and **labels** (may point to
several). Relations between collections are optional and meant to be computed with seqcol
comparison. Every record says where its facts came from, and native fields with no core home
are kept in `extras`, so a round trip through one format loses nothing.

All 100 formats map. 1,138 of 2,036 native fields have a core home. Almost everything that
does not is annotation, sample metadata, or tool and browser settings.

## Goal

Convert a reference genome record from any of ten schemas into any other, and say plainly
what is lost on the way.

## Problem

"A reference genome" means different things in different schemas, and most schemas mix the
meanings in one record:

| Level | What it is | Example | Identified by |
|---|---|---|---|
| Assembly | What an archive registered | GRCh38, GCA_000001405.15 | accession |
| Collection | One exact list of named sequences | hg38 no-alt analysis set (195 sequences) | seqcol digest |
| Sequence | One sequence | chr1 of GRCh38 | refget digest (SQ.…) or md5 |
| Copy | One file | hg38.fa.gz on UCSC's server | location + file checksum |
| Deployment | An entry in a system that uses the files | Galaxy all_fasta row `hg38canon` | system + key |

The collected data shows why mixing them breaks things. The name `hg38` points to at least
four different things (see "Biggest mismatches" below). The only identifier that pins one
exact list of sequences is the seqcol digest, and only refgenie, GA4GH and Galaxy's new IDC
files carry it.

## Solution: the core model

```
record
├── refmeta: "0.1", subject: assembly|collection|sequence|copy|deployment
├── assembly      accessions[], name, version, taxon{id,name,commonName,speciesId,strain},
│                 level, type, status, releaseDate, submitter, bioproject, biosample,
│                 FHR fields (assemblyAuthor, assemblySoftware, scholarlyArticle, vitalStats, ...),
│                 labels[]
├── collection    digest, level1{names,lengths,sequences,...}, nSequences, totalLength,
│                 provider, providerVersion, namingAuthority, relationToAssembly,
│                 relations[], aliases[], labels[], description
├── sequences[]   name, length, digest (SQ.), md5, aliases[] (the name map), role, molecule,
│                 assignedMolecule, assemblyUnit, circular, placement{chromosome,range,region}
├── copies[]      location, kind, provider, checksums{md5,sha256,fhr,...},
│                 uncompressedChecksums{}, size, modified, masking, toolVersion
├── deployments[] system, scope, table, key, displayName, location
├── provenance[]  id, source, format, authority, url/file, retrieved, authors[], recordDate
├── fieldSources, conflicts       (filled when records are merged)
└── extras        {format_id: {native path: value}}  (and per sequence/copy/deployment)
```

A real record, converted from refgenie's `/v4/aliases/R64-1-1` (trimmed to one sequence):

```json
{
  "refmeta": "0.1",
  "subject": "collection",
  "collection": {
    "digest": "ia9g4Myony-xxLsSc7eQOC_NdClGgPGu",
    "aliases": [{"namespace": "refgenie", "value": "R64-1-1"}],
    "labels": [{"namespace": "fhr.genome", "value": "R64-1-1"},
               {"namespace": "fhr.synonym", "value": "saccharomyces_cerevisiae_ENSEMBL_release_81"}],
    "provider": "Ensembl",
    "nSequences": 17,
    "totalLength": 12157105
  },
  "sequences": [{"name": "I", "length": 230218, "digest": "SQ.lZyxiD_ByprhOUzrR1o1bq0ezO_1gkrn"}],
  "assembly": {"accessions": [{"namespace": "insdc.gca", "value": "GCA_000146045.2"}],
               "version": "2", "level": "chromosome",
               "taxon": {"id": 4932, "name": "Saccharomyces cerevisiae"}},
  "provenance": [{"id": "p1", "source": "refgenie", "format": "refgenie_api_alias",
                  "file": "api_alias_R64-1-1.json", "retrieved": "2026-11-17"}]
}
```

The same yeast chromosome from NCBI's assembly report lands in the same `sequences[]` shape,
but with names only in aliases (`assembly: I`, `insdc: BK006935.2`, `refseq: NC_001133.9`,
`ucsc: chrI`), because an assembly report is not one FASTA's name list.

## Why it is shaped this way

**One block per level.** A source fills the blocks it knows. Galaxy's `.loc` rows fill
`deployments` and `copies`; NCBI fills `assembly` and the name map; seqcol fills `collection`
and `sequences`. Nothing forces a source to claim a level it does not describe. The `subject`
field says which level the source record is mainly about.

**Each level keeps its own identifier.** Merging two records is allowed only through a shared
identifier at some level (`CROSSWALK_FORMAT.md` section 5.5). An assembly accession never
identifies a collection: several refgenie entries share GCA_000001405.15.

**Aliases versus labels.** Every name is `{namespace, value, scope?}`. A name goes in
`aliases` if it points to exactly one thing within its namespace and scope, and in `labels`
if it may point to several. This is the main fix for the Galaxy dbkey problem: `hg38` as a
dbkey is a label, `hg38canon` as an IDC build id is an alias, and neither is a collection id.

**Accessions are a list.** `assembly.accessions` holds every identifier an archive issued for
the assembly version, each as `{namespace, value}`: a GenBank and RefSeq pair is two items
(`insdc.gca`, `insdc.gcf`), and another archive's id is one more item with its own namespace.
There is no separate slot per archive, so a new archive needs no new field. The first item is
the accession the source record is about (an NCBI RefSeq report lists its GCF first, then the
paired GCA), so a format with one accession slot (FHR `accessionID`, the refgenie registry)
writes the first item and a round trip keeps the order. A GenBank/RefSeq pair is not always
identical (RefSeq sometimes adds or drops a sequence); the collection digest, not the
accession, says which sequences a file holds.

**The sequence-name map lives on each sequence.** `sequences[].name` is the name this
collection uses. `sequences[].aliases` holds the same sequence's names in other styles. This
makes renaming a plain operation: pick a namespace, copy those aliases into `name`, and drop
the digests that depend on names (the result is a different collection).

**Relations are optional and computed.** `collection.relations[]` holds `identical`,
`reordered`, `renamed`, `same_sequences`, `same_coordinates`, `subset_of`, `superset_of`,
`overlaps` and `derived_from`, each marked `computed` or `asserted`. All but `derived_from`
come straight out of a seqcol comparison. No source states them today, so no crosswalk fills
them; a tool fills them after conversion. Example: R64-1-1 and sacCer3 are `renamed` (same
sequences in the same order, different names).

**Provenance at two depths.** A record made from one file has one provenance entry and needs
nothing more. When records are merged, `fieldSources` says which entry gave each value and
`conflicts` lists values that disagreed. FHR's `metadataAuthor` and dates such as ENA's
last-updated fill `provenance[0].authors` and `provenance[0].recordDate`: they are "who says
so", not facts about the genome.

**Small core, room for extras.** The core has 138 leaf fields, and about a quarter of them
are FHR's assembly fields and statistics reused as is. Everything else stays in
`extras[format_id]`, so writing back to the same format restores it.

**FHR names where FHR covers the fact.** The assembly block reuses FHR names unchanged:
`assemblyAuthor`, `dateCreated`, `voucherSpecimen`, `instrument`, `scholarlyArticle`,
`funding`, `reuseConditions`, `assemblySoftware`, `assemblyProtocol`, `documentation`,
`identifier`, `relatedLink`, `vitalStats`, `version`, `taxon.name`. Two deliberate changes:
FHR's one `accessionID {name, url}` becomes the first item of `accessions` (with its `url`),
and `taxon.id` is a number (FHR `taxon.uri`), because every other source that has a taxon
gives the bare number. Both convert exactly. An FHR accession that matches no official
pattern (the upstream example has `PBARC`) gets the namespace `unspecified`.
refmeta adds three `vitalStats` keys FHR lacks: `ungappedLength`, `numberChromosomes`,
`coverage`.

## Namespaces

`namespaces.yaml` lists the official namespaces: 36 of them, each with the lists it may
appear in, where an alias is unique, a value pattern where one exists, and the matching
Bioregistry prefix. Any other lower-case id is allowed as a custom namespace. The validator
(`refmeta core -v`, or `check_namespaces()` in Python) reports custom namespaces, official
ones used in the wrong list, and values that break a pattern, as notes rather than errors.
Custom namespaces need no special prefix, so one can become official later without being
renamed.

| Level | List | Official namespaces |
|---|---|---|
| Assembly | `accessions` | `insdc.gca`, `insdc.gcf` (Bioregistry prefixes, with patterns), `unspecified` |
| Assembly | `labels` | `ucsc`, `ensembl`, `ucsc.assembly`, `ena.chain`, `sam.as`, `vcf.assembly`, `refgenie.genome_assembly` |
| Collection | `aliases` | `refgenie` (one server), `refgenie.legacy_digest`, `galaxy.build_id` (one table on one server) |
| Collection | `labels` | `galaxy.dbkey`, `galaxy.name`, `ucsc`, `fhr.genome`, `fhr.synonym`, `refgenie.synonym`, `nfcore`, `igenomes`, `bioconductor`, `annotationhub` |
| Sequence | `aliases` | `insdc`, `refseq`, `gi`, `md5`, `ga4gh`, `sha512t24u`, `sha1`, `vmc`, `seguid`, `accession` (global); `ucsc`, `ensembl`, `assembly`, `ncbi`, `dbsnp`, `veupathdb`, `unspecified` (one assembly) |

Run over every example file, the check finds three things today: SeqRepo's assembly-prefixed
aliases make custom namespaces (`grch38`, `grch38.p1`, `hs37d5`, ...); refgenie's
`/sequences` API gives a collection alias in namespace `genome_assembly`; and one Ensembl
REST record gives the RefSeq synonym `na`, which breaks the `refseq` pattern.

## How each source fits

| Source | Formats | Fills mainly | Fit |
|---|---|---|---|
| Galaxy | 19 | deployments, copies, collection labels | Good for deployments. A row has a key (`value`), a label (`dbkey`) and a path, and no checksum or digest. IDC PR #88 JSON adds the seqcol digest and full level 2. |
| refgenie | 7 | collection, sequences, assembly, copies | Best fit. Digest, aliases, level 1 and 2, sequence digests with md5 and accession aliases, FHR block. Legacy 0.x config fits as deployments plus a legacy-digest alias. |
| FHR | 7 | assembly (names reused), one copy, collection digest | Direct. Only `genome`/`genomeSynonym` need a level decision (see open questions). |
| NCBI | 8 | assembly, name map, copies | Rich assembly facts and the best name map (assembly / insdc / refseq / ucsc). No collection digests anywhere. Analysis-set deflines give a collection with md5s. |
| ENA | 9 | assembly, name map, md5s | Like NCBI with INSDC names only. Summary and portal give the unversioned accession chain; a derivation rebuilds the versioned one. |
| Ensembl | 13 | assembly (GCA .29), Ensembl-named collections, deployments | REST synonyms fill the name map. Three different human sequence sets (194, 706, 2,030) under one assembly. |
| UCSC | 12 | collection labels, name map, copies | chromAlias files are a name map. A UCSC name is a label, not a collection. md5sum.txt and /list/files fill copies. |
| nf-core | 6 | deployments, copies, collections with md5 | `--genome` keys are labels per pipeline. iGenomes .dict, .fai and GenomeSize.xml are collections with md5s. |
| Bioconductor | 11 | collections, name map, deployments | Seqinfo and chrominfo are collections; seqlevelsStyle is a name map; BSgenome and AnnotationHub are deployments with source copies. |
| GA4GH | 8 | collection, sequences | seqcol maps exactly. refget, SeqRepo and VRS give single sequences. SAM and VCF headers give collections with md5s. |

## What does not fit

- **Annotation**: gene counts, BUSCO, genebuild dates, GENCODE and MANE versions. Out of scope.
- **Sample metadata**: ENA's 114 portal sample fields and NCBI's BioSample block. Only the
  BioSample accession is kept.
- **Tool and browser settings**: MACS2 genome size, STAR build parameters, VEP and snpEff
  names, BLAT servers, menu order, Galaxy table declarations. `galaxy_idc_data_managers` maps
  nothing at all.
- **"Built from" links between files**: which FASTA a Galaxy index or a refgenie asset was built
  from (`depends_on.all_fasta`, `asset_parents`). The core has no field for this yet.
- **Relations between assemblies**: newest version of a chain (.15 to .29), how the GenBank
  and RefSeq members differ, liftOver chains.
- **Facts split over two native fields**: AnnotationHub's `location_prefix` + `rdatapath`, the
  iGenomes species/source/build path. Rules map one field each, so these stay apart.
- **Per-sequence file layout and masks**: .fai offsets and line widths, the analysis sets'
  hard-masked spans.
- **Collapsed lists**: ENA's chromosome lists that write ranges like `KI270706.1-KI270714.1`.

## Biggest mismatches the data shows

**1. `hg38` names four different things.**

| Who says hg38 | What it is |
|---|---|
| UCSC database | 455 sequences at release, 711 at p14, same name |
| refgenie | the NCBI no-alt analysis set, 195 sequences, UCSC names, digest EiFob05a… |
| Galaxy dbkey | a label over hg38, hg38canon and hg38female; bwa_mem `hg38` is hg38full while all_fasta `hg38` is hg38.fa |
| NCBI synonym | on all four GRCh38 accessions (GCA .15, .29; GCF .26, .40) |

**2. Sources anchor GRCh38 to different accessions.** refgenie and UCSC dbDb cite
GCA_000001405.15. Ensembl uses GCA_000001405.29 and fails lookups by .15. Bioconductor's hg38 link and Galaxy's BRC
dbkey use GCF_000001405.40. And GCA .15 with GCF .40 is not an NCBI pair: pairing is version
to version (.15 with .26, .29 with .40).

**3. "Total length" counts different sequence sets.** For GRCh38: NCBI 3,099,734,149 (nuclear,
no alt loci), Ensembl golden path 3,099,750,718 (the same plus chrM, 16,569 bp), ENA
3,209,286,105 (with alt loci), Ensembl's new API 3,298,912,062 (matches nothing we found).
All map to `vitalStats.totalBasePairs` with a lossy note; they are not comparable.

**4. "Source" means the distributor, not the assembler.** refgenie's `assembly.source`, FHR's
`assemblySource` and nf-core's `reference_source` all say who shipped the sequence set (UCSC vs
Ensembl for the same R64). They map to `collection.provider`, not to the assembly.

**5. No shared collection id outside the seqcol world.** Only 16 of 100 formats can give a
collection digest. The key that the rest share is the per-sequence md5 (SAM M5, VCF md5,
ENA, iGenomes, NCBI analysis sets). Even that breaks for hard-masked sequences: the analysis
sets' M5 is the masked sequence's md5. 14 human sequences have different md5s in iGenomes
NCBI/GRCh38 and UCSC/hg38 with the same names and lengths.

**6. Checksums come in four kinds, none of them a refget digest.** FHR SHA-512/256 base64 over
the file without its checksum line; md5 of the compressed file (NCBI, UCSC, refgenie
registry); sha256 or md5 of the uncompressed file (IDC, NCBI uncompressed_checksums); and
legacy refgenie asset digests. The core keeps them apart (`checksums` vs
`uncompressedChecksums`, keyed by algorithm).

**7. Smaller ones.** Yeast taxon is 4932 in some sources and 559292 in others. The yeast
mitochondrion is Mito, MT, chrM or KP263414.1. Species names sometimes include the strain.
GenArk's `chromAuthority ucsc` only changes displayed names; its files use RefSeq accessions.
UCSC hg38's dbDb record cites GCA_000001405.15 although its current sequence list is p14.

## Open questions

1. **FHR `genome` and `genomeSynonym`: which level?** FHR calls it the genome's name;
   refgenie writes collection names there (hg38). I put both on `collection.labels`, with
   fallbacks when writing FHR. The alternative is `assembly.labels`. Your call.
2. **Keep the FHR taxon deviation?** `taxon.id` as a number is easier for every other
   source. If FHR alignment matters more, the core could use `taxon.uri` exactly, at the
   cost of a transform in most crosswalks that carry a taxon. (Accessions are settled: a
   list of `{namespace, value, url?}`.)
3. **Line up with RDA FGA-WG `GenomeAssembly` now?** It already has `seqcol_digest`,
   accessions and aliases. Matching its field names before this freezes is cheap.
4. **Add a "built from" link between copies** (`copies[].builtFrom: <location or digest>`)?
   Galaxy needs it to say which FASTA an index came from, and refgenie has asset parents.
5. **Model relations between assemblies** (version chain, GenBank/RefSeq pair differences,
   alt haplotypes)? Today a GenBank/RefSeq pair is two items of `assembly.accessions`,
   with nothing said about how they differ.
6. **Allow multi-field rules?** A small `join` rule (two native fields to one core field)
   would cover the ENA accession chain + version, AnnotationHub prefix + path, and the
   iGenomes path alias. It makes the engine a bit harder.
7. **Who fills `scope`?** A Galaxy build id is unique only per server, but no Galaxy file says
   which server it came from. The engine could copy the fetch URL from provenance into
   `scope`, or the user could pass it in.
8. **Per-row constants.** Every row of ENA's unlocalised list is an unlocalized scaffold, but
   constants are per record. A `row_constants` key would fix this one case.
9. **Namespace registry.** Decided: `namespaces.yaml`, with Bioregistry prefixes where one
   exists (`insdc.gca`, `insdc.gcf`, `insdc`, `refseq`). Still open: should SeqRepo's
   assembly prefixes (`GRCh38:`) map to one namespace with a scope instead of one custom
   namespace per patch release?
10. **Hard masking.** It changes sequence digests, so a hard-masked set is a different
    collection. Should `relationToAssembly: derived` plus a `derived_from` relation be the
    standard way to say "the analysis set is GCA_000001405.15 with masks and chrEBV"?

## How this was checked

Each crosswalk was run against every example file of its format with the adapters in
`tools/refmeta/formats/` (a scratch checker that follows `CROSSWALK_FORMAT.md`; not part of
this folder). For all 100 formats: every fields.json path is covered, every core path resolves
in `core.schema.json`, every both-way rule without a lossy note round-trips on every distinct
example value, and every converted record validates against the schema. 140 rules have no
example because no collected file sets that field; their `note` says so.
