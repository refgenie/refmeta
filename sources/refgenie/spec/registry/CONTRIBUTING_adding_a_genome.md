# Contributing to refgenie-registry

## Overview

Contributions are welcome via pull requests. You can:

1. **Add a genome**, define a new genome assembly, and say how far to build it
2. **Add a recipe**, define how to build an asset (e.g., an aligner index)
3. **Suggest a species name**, add or fix a species' names in the species list
   (see [Species names](#species-names))

## Adding a Genome

Adding a genome is **one file and one PR**. The YAML says what the genome is and,
in its `build:` block, what the registry should do with it. There is no second
file to edit and no build request to open.

1. Fork this repo and create a branch.
2. Create `genomes/<organism>/<assembly>.yaml` following the schema.
3. Open a PR with title: "Add genome: \<organism\> \<assembly\>"

**Required fields:** `name`, `description`, `organism.scientific_name`,
`organism.taxon_id`, `fasta` (at least one `sources[].url` or a `checksum`),
`seqcol` (a `digest`, or `compute: true`), and `build` (a `store` and a `tier`)

**The species must be on the species list.** `organism.taxon_id` must appear in
[`tools/taxon_ids.json`](tools/taxon_ids.json); validation fails otherwise. If
your genome's species is new, add its entry in the same PR (see
[Species names](#species-names)).

### The `build:` block

```yaml
build:
  store: jungle          # which store holds this genome's sequence
  tier: standard         # how far to take it
  add: [suffixerator_index]   # optional: extra assets beyond the tier
  drop: [star_index]          # optional: assets to skip from the tier
```

**`store`** must name an existing directory under [`stores/`](stores/):

| Store | Contents |
|---|---|
| `legacy` | The genomes the old refgenomes.databio.org server published |
| `jungle` | Human and mouse reference assemblies (the reference-jungle dataset) |
| `plantcore` | Plants and model organisms (one well-assembled genome per species) |
| `plantsup` | Other plant assemblies (not published) |
| `vgp` | Vertebrate Genomes Project assemblies |
| `pangenome` | HPRC pangenome haplotypes |
| `igenomes` | AWS iGenomes references |
| `refseq` | NCBI protein and transcript sequences |
| `salmon_txomes` | Salmon/tximeta transcriptomes |
| `vrs` | VRS allele-identification reference sequences |
| `decoys` | Decoy and spike-in sequences |
| `demo` | Test data for development |

The store must actually hold the sequence, there must be a row for it in that
store's `sources.csv`. `python build/sync_stores.py` reports any genome whose
store does not. If no existing store fits, see
[Adding a new store](stores/README.md#adding-a-new-store).

**`tier`** says how far to take the genome. Each tier includes every tier below
it; the definitions live in [`pep/tiers.yaml`](pep/tiers.yaml):

| Tier | What gets built |
|---|---|
| `store_only` | Nothing. The sequence is loaded into its store and is browsable. |
| `sequence_only` | + `fasta`, `fasta_index` |
| `standard` | + `bwa_index`, `bowtie2_index`, `hisat2_index` |
| `full` | + `suffixerator_index` |

**`store_only` is the right default for a new genome.** It registers the genome,
gives it organism and taxonomy metadata, and loads its sequence, with no build
cost. Most of the registry sits there. Ask for a build tier when you actually need
the indexes.

A genome in a build tier needs its FASTA **staged** and a matching `<genome>_fa`
key in [`pep/config.yaml`](pep/config.yaml) `derive.sources`. Generation fails
loudly and names the genome if that key is missing, so a build tier on an unstaged
genome is caught on the PR, not at 3am.

> `star_index` and `tallymer_index` appear in the `standard` and `full` tier
> definitions but are **unproven** in this pipeline, so existing genomes carry a
> temporary `drop:` removing them. Match the neighbouring genomes in your file's
> directory.

The schema is aligned to the [FAIR Headers Reference genome (FHR)](https://github.com/FAIR-bioHeaders/FHR-Specification)
vocabulary. The registry-native keys below are the source of truth for the FHR
core; the optional `fhr:` block is an escape hatch for pure-FHR provenance
fields that have no registry-native home. See [`schema/README.md`](schema/README.md)
for the field-by-field YAML → `.fhr.json` mapping.

The FHR metadata that ends up in the store is **generated during the build from
this YAML**, you never write or commit a `.fhr.json` yourself. The build derives
one FHR record per genome and publishes it into the store alongside the sequence,
so what the API serves is exactly what you wrote here.

**Example** (see `genomes/human/hg38.yaml` for a complete reference):

```yaml
name: my_genome                 # required; must equal the filename stem
aliases:
  - alternative_name            # optional

description: |                  # required
  Brief description of this genome assembly.

organism:
  scientific_name: Genus species  # required
  taxon_id: 12345                 # required NCBI Taxonomy ID (integer)

assembly:                       # optional but recommended
  source: NCBI
  accession: GCF_...
  level: chromosome

masking: not-masked             # optional: soft-masked | hard-masked | not-masked | unknown

fasta:                          # required (need sources[].url OR a checksum)
  sources:
    - provider: NCBI
      url: https://ftp.ncbi.nlm.nih.gov/...
  checksum:
    sha256: compute_on_registration   # sentinel, or the 64-hex sha256 of the uncompressed FASTA
    md5: <optional 32-hex md5 of the compressed FASTA>

seqcol:                         # required
  compute: true                 # or: digest: <seqcol digest>

build:                          # required: what the registry does with this genome
  store: jungle                 # a directory under stores/ that holds the sequence
  tier: store_only              # store_only | sequence_only | standard | full

fhr:                            # optional: pure-FHR provenance (all fields optional)
  license: CC0-1.0
  funding: NIH
  scholarly_article: 10.1038/nature...
  date_created: 2013-12-17
  metadata_author:
    - { name: Jane Doe, uri: https://orcid.org/0000-0002-1825-0097 }

metadata:                       # optional registry bookkeeping (not exported to FHR)
  added: 2026-01-01
  added_by: your_github_username
```

**Notes:**
- Provide at least one download URL under `fasta.sources[]` (each with an
  optional `provider`). Use NCBI, Ensembl, or UCSC as the source where possible.
- The checksum, when present, must be the SHA-256 of the **uncompressed** FASTA
  file (64 lowercase hex chars), or the sentinel `compute_on_registration`.
- `organism.taxon_id` is required; the exporter derives the resolvable
  `taxon.uri` (`https://identifiers.org/taxonomy:<id>`) from it.
- The `name` field must match the filename (without `.yaml`).
- The `build:` block is registry pipeline state and is **not** exported to FHR, the
  same way `metadata:` is not. It describes what we do with the genome, not what
  the genome is.
- `pep/samples.csv` and `pep/metadata/` are **generated** from the genome YAMLs by
  `build/generate_samples.py` and `build/generate_genome_metadata.py`. Never edit
  them by hand, the nightly regenerates both and fails on any diff.

