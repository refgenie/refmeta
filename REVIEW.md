# refmeta review

Reviewed 2026-11-17, after the mapping, engine and web page were built. I re-ran every
claim I could instead of trusting the stage summaries. This file says what holds up, what
does not, and what nobody has tested yet.

**Bottom line.** The engine, CLI and web page work and are well tested on their own terms.
The mapping is mostly faithful to the source specs. But I found 2 wrong mappings and
7 doubtful ones, and most converted files are not valid in the target format's own schema.
I fixed 3 small bugs in `tools/`. Nothing in `mapping/` was changed.

**Update, later on 2026-11-17 (after Nathan's decisions).** Accessions are now a list
(`assembly.accessions`, each `{namespace, value, url?}`), and `mapping/namespaces.yaml` lists
the official namespaces, with custom ones allowed. This fixes wrong item 1 below and answers
design question 1. 20 crosswalks changed; tests: 826 passed, 7 skipped. The web page was
rebuilt and re-checked headless from `file://` (the NCBI R64 report sample now shows its
accession).

## What works (with evidence)

**Tests.** The full suite passes: 814 passed, 7 skipped before my fixes; 817 passed,
7 skipped after (I added 3 regression tests). Command:
`cd tools && uv run pytest -q`.
The 7 skips are example files that no adapter reads, as the build stage said.

**CLI on every example to every format.** I ran `refmeta convert FILE --to F` (in process,
through `cli.main`) for all 325 example files and all 102 targets (100 formats plus core
YAML and JSON): 33,150 runs.

| | Before my fixes | After |
|---|---|---|
| Wrote a file | 11,832 | 11,587 |
| Refused with a clear message (exit 2) | 21,216 | 21,563 |
| Crashed with a Python traceback | 102 | 0 |

Most refusals are "nothing to write", which is correct: a chrom.sizes file has nothing to
put in an FHR record. 510 refusals are the 5 files no detector knows (formats with no
adapter). No written file was empty.

**Forced reads.** I fed 30 wrong inputs (empty text, junk, other formats' files) to every
reader with `--from`. Before my fix, 828 of 3,000 runs crashed with raw errors
(JSONDecodeError, XML ParseError, AttributeError, even RecursionError). After: 0.

**Counts in the stage summaries are right.** 100 crosswalks, 1,170 rules, 140 rules with
no example, 2,036 native fields, 1,138 with a rule, 177 rules with a lossy note,
16 formats that can give a seqcol digest. `sync_data.py --check` and
`build_web.py --check` both exit 0.

**Facts in PROPOSAL.md that I checked against the files:**
- UCSC `hg38.chrom.sizes` has 455 lines; `latest/hg38.chrom.sizes` has 711.
- NCBI pairs GCA .15 with GCF .26 and GCA .29 with GCF .40 (the report headers say so).
- Ensembl golden path minus NCBI total = 16,569 bp, exactly chrM.
- 14 human chromosomes share name and length but differ in md5 between the iGenomes
  NCBI/GRCh38 and UCSC/hg38 `.dict` files (chr1, chr2, chr3, ...).
- The refgenie registry md5 for hg38 equals NCBI's md5 of the compressed no-alt `.fna.gz`.
  The registry sha256 is of the uncompressed FASTA (registry schema says so).
- Galaxy's `hg38` row in all_fasta points to `hg38.fa`; in bwa_mem it points to `hg38full.fa`.

**Source folders.** Every spec and example file that a `fields.json` lists exists (0 missing).
Folder sizes are 0.4 to 1.4 MB, all under 5 MB. Hand-made examples sit in
`examples/constructed/` and each README says so; NCBI, Ensembl, refgenie and nf-core say
they have none, and none were found. The one stray file (`nfcore/examples/local/`) is
labeled as belonging to no format. Most "missing" paths in READMEs are upstream URLs or
patterns, not local files.

**Web page.** `build_web.py` runs and its bundle holds all 117 package files, byte for byte
the same as `tools/refmeta/`, plus the glue module. I ran my own headless Chrome test
from `file://` (separate from the build stage's script): the page boots in 2 to 3 seconds,
reads the NCBI report with its companion table, writes chrom.sizes with UCSC names, shows a
clean message for an unreadable file, and logs no console errors.

## Fixes I made (all in `tools/`)

1. **Unreadable input crashed the CLI.** `read_native()` in `refmeta/convert.py` now turns
   any reader error into a `ConversionError`, so the CLI exits 2 with a message instead of a
   traceback. Example: `refmeta convert sources/fhr/examples/upstream_example.fhr.export.jsonld --to ucsc_chrom_sizes`
   crashed for all 102 targets.
2. **seqcol writers wrote invalid collections.** A level 2 collection was written with only
   names and lengths (no `sequences`), which the seqcol schema rejects. 109 written files
   failed `seqcol_minimal_v1.0.0.json`; now 0 do. The writers in `refmeta/formats/ga4gh.py`
   refuse records missing names, lengths or sequences.
3. **Legacy refgenie config writer dropped rows silently.** Galaxy `all_fasta.loc` to
   `refgenie_genome_config` gave `genomes: {}`, losing all 6 FASTA paths with no warning.
   The writer in `refmeta/formats/refgenie.py` now refuses when a row has genome data but
   no genome key.

Each fix has a test in `tools/tests/test_convert.py`. I rebuilt `web/refmeta_bundle.js`
afterward, and re-checked the page in the browser.

## What is lossy (by design, and documented)

- 177 rules carry a `lossy` note. The main kinds: free-text fields (SAM `AS`, VCF
  `assembly`, AnnotationHub `genome`), taxon names that include the strain, several
  per-sequence URLs kept as one, ENA's collapsed name ranges, and totals that count
  different sequence sets.
- 898 of 2,036 native fields have no core home. They survive only a round trip back to the
  same format (through `extras`), not a conversion to another format.
- Two lossless-marked fields change on a round trip (known, listed in the tests):
  `ncbi_assembly_summary` isolate and `refgenie_registry_genome` provider list.
- 47 native fields get filled on write even though the source left them empty, because two
  native fields share one core path. Example: NCBI Datasets to NCBI report header writes
  `Isolate: S288C` for yeast, which is a strain, not an isolate.

## What is wrong or doubtful

**Wrong (2):**

1. **Fixed (accessions list).** **The NCBI FTP assembly report never fills `assembly.accession`.** Its GenBank and
   RefSeq accessions go only to `assembly.aliases`. So an NCBI report converted to any of
   the 28 formats that hold an accession loses it, including NCBI's own Datasets report, FHR,
   ENA, Ensembl and refgenie. The reverse also loses it: Datasets to report header writes
   no accession lines. (`mapping/crosswalk/ncbi_assembly_report_header.yaml`)
2. **BSgenome seed `release_date` maps to `assembly.releaseDate`.** In the hg38 seed it is
   2023/01/31, the date of UCSC's p14 files, not of GRCh38. The NCBI GRCh38 seed has the true
   date (2013-12-17), but that form is not `YYYY/MM/DD`, so it goes to extras. The result
   keeps the wrong date and drops the right one. (`bioconductor_bsgenome_seed.yaml`)

**Doubtful (7):**

1. **Isolate becomes strain.** NCBI `Isolate` (report, summary, Datasets) maps to
   `taxon.strain`. T2T's isolate is CHM13, a cell line. On write it invents isolate values.
2. **`numberChromosomes` counts differently with no note.** For GCA_000001405.15, NCBI says
   24 (nuclear only); ENA and Ensembl say 25 (with MT). No rule has a lossy note and the
   tests' cross-source check does not look at this field.
3. **`assembly.version` means two things.** ENA, Ensembl and refgenie sidecars put the
   accession version there ("2", "15", "40"). FHR puts a free-form genome version ("0.0.1").
4. **Galaxy ids land in two places.** A `.loc` row's `value` becomes a deployment key; the
   same id in IDC JSON (`galaxy_unique_build_id`) becomes a collection alias. So
   `.loc` to IDC JSON keeps only the dbkey (6 rows that all say `hg38`), and IDC JSON to
   `all_fasta.loc` writes a row with empty value, name and path.
5. **BSgenome `release_name` maps to `assembly.description`.** "SGD April 2011 sequence"
   describes a sequence release, not the assembly.
6. **SeqRepo assembly-prefixed aliases make new namespaces.** `GRCh38:chr1` becomes
   namespace `grch38`, which is not in the namespace table, so `--names` cannot use it.
7. **AnnotationHub `dataprovider` becomes `collection.provider` even for non-genome
   resources.** An EpiTxDb record gives provider "RMBase v2.0", which then shows up as the
   refgenie registry's `assembly.source`.

**Converted files are mostly not valid in their target format.** I checked outputs
against each target's own published schema where one exists:

| Target | Written | Valid in target schema |
|---|---|---|
| FHR JSON (`fhr.json`) | 155 | 2 (FHR's own upstream examples) |
| refgenie registry (`genome.schema.yaml`) | 229 | 5 |
| seqcol level 2 | 14 after fix 2 | 14 |

The engine refuses only when nothing fits, not when required fields are missing. Even the
FHR files under `examples/constructed/` fail the FHR schema (no `metadataAuthor`,
`assemblyAuthor`, `dateCreated`, `masking`, `checksum`), and the 6 real refgenie sidecars
fail it too (`schemaVersion` is the number 1.0, required fields missing).

## What is untested

- **No real tool reads the outputs.** Nobody loaded a written `.loc`, BSgenome seed, VCF
  header, `.dict` or refgenie config into Galaxy, R, samtools or refgenie.
- **Target-format validity is not in the test suite.** My schema check above was a one-off.
- **Only two anchor genomes.** Human and yeast, plus a few extras. No plant, polyploid or
  many-scaffold assembly.
- **Web page:** tested only in Chromium. Not tested: Firefox, Safari, a real drag-and-drop
  event (tests used the file picker), files near the 64 MB limit, and the "CDN unreachable"
  message. The build stage's 2,040-conversion parity check ran before my fixes; the page
  runs the same code, and I re-checked it with 3 smoke runs only.
- **Detection:** 7 example files detect as a sibling format (5 iGenomes `.dict` files as SAM
  headers, a single-file hub as `genomes.txt`, the FHR schema.org export as FHR JSON-LD).
  Results look right but nobody checked them field by field.
- **`merge()`:** `fieldSources` paths have no array indexes, and `scope` is never filled.
- **`validate_core` with `jsonschema` installed:** that branch never ran (not in the env).
- **The README's `uv run pytest` command:** checked later; it works, and CI runs it.

## Five open design questions for Nathan

1. **Answered.** ~~Which accession is "the" assembly accession?~~ Accessions are one list
   with a namespace per item; the first item is the one the source record is about.
2. **Should writers check the target's required fields?** Refuse, warn, or write a partial
   file? Today almost no FHR or registry output is valid FHR or registry YAML. I made seqcol
   and the legacy refgenie config refuse; the rest still write partial files silently.
3. **Where do counting-dependent numbers live?** `totalBasePairs` and `numberChromosomes`
   differ by source only because sources count different sequence sets. Should they carry
   "what was counted", or move to the collection, where the sequence set is explicit?
4. **One home for Galaxy ids, and who fills `scope`?** A Galaxy build id is a deployment key
   in `.loc` files and a collection alias in IDC JSON. Pick one so it survives conversion.
5. **How to say "derived from" and "built from"?** The analysis sets are GRCh38 with masks
   and extra sequences; Galaxy indexes and refgenie assets are built from a FASTA. Without
   these links, `hg38` the label cannot be tied to the actual collection.

PROPOSAL.md lists 10 open questions; these five are the ones the review found most
pressing. Its questions on FHR naming (1 and 2) also bear on doubtful item 3 above.
