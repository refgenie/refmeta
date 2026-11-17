# refmeta

refmeta is a draft metadata model for reference genomes, plus tools that convert a
genome's metadata between the formats people already use: Galaxy, refgenie, FHR, NCBI,
ENA, Ensembl, UCSC, nf-core, Bioconductor and GA4GH.

**Explore it in your browser:** <https://refgenie.github.io/refmeta/>

- [Terms](https://refgenie.github.io/refmeta/): about 2,100 terms from 106 formats, side
  by side, each with its definition, an example, the shared field it maps to, and a link to
  the original documentation.
- [Namespaces](https://refgenie.github.io/refmeta/#namespaces): the official namespaces for
  names and identifiers.
- [Converter](https://refgenie.github.io/refmeta/convert.html): drop a file in one format
  and get it back in any other. It runs in the browser; nothing is uploaded.

This is a draft for discussion. [REVIEW.md](REVIEW.md) lists what works, what loses
information, and which mappings are wrong or doubtful.

## The idea

"A reference genome" means different things, and each is identified a different way:

| Level | Example | Identified by |
|---|---|---|
| Assembly | GRCh38 | accession (GCA_000001405.15) |
| Collection | hg38, hg38_primary, Ensembl-named GRCh38 | seqcol digest |
| Sequence | chr1 of GRCh38 | refget digest or md5 |
| Copy | UCSC hg38.fa, an S3 copy | location + file checksum |
| Deployment | a Galaxy data table row | system + key |

Each existing format mixes these levels in its own way. refmeta keeps the formats as
they are and maps each one's fields onto the levels, so a record can move from one
format to another and say what it lost on the way.

## What is here

| Path | What |
|---|---|
| [`mapping/PROPOSAL.md`](mapping/PROPOSAL.md) | The model, why it is shaped this way, and open questions. Start here. |
| [`mapping/core.schema.json`](mapping/core.schema.json) | The model as JSON Schema |
| [`mapping/namespaces.yaml`](mapping/namespaces.yaml) | Official namespaces (custom ones are allowed) |
| [`mapping/crosswalk/`](mapping/crosswalk/) | One mapping file per format (100 formats) |
| [`mapping/CROSSWALK_FORMAT.md`](mapping/CROSSWALK_FORMAT.md) | How a mapping file works |
| [`mapping/coverage.md`](mapping/coverage.md) | What each format fills, and what it leaves out |
| [`sources/`](sources/) | One folder per source: where it came from (`README.md`), its terms (`fields.json`), copies of its specs (`spec/`) and real records (`examples/`) |
| [`sources/CANDIDATES.md`](sources/CANDIDATES.md) | Other sources worth adding |
| [`tools/`](tools/) | The `refmeta` Python package: readers and writers for each format, the converter, a command line, and tests |
| [`web/`](web/) | The website (terms explorer and converter) |
| [`REVIEW.md`](REVIEW.md) | An independent check of all of the above |

The examples cover two genomes in every source that has them, so conversions can be
checked across sources: human GRCh38 (GCA_000001405.15, GCF_000001405.40, UCSC hg38) and
yeast S288C R64 (GCA_000146045.2, GCF_000146045.2, UCSC sacCer3, Ensembl R64-1-1).

## Command line

```bash
cd tools
uv sync
uv run refmeta formats                              # list the 100 formats
uv run refmeta core ../sources/refgenie/examples/api_alias_R64-1-1.json   # print the shared record
uv run refmeta convert FILE --to fhr_json           # convert to another format
uv run pytest                                       # run the tests
```

The package needs only Python 3.10+ and PyYAML, so the same code runs in the browser
through Pyodide.

## Building the website

`web/` is static. After changing anything in `mapping/` or `sources/`, rebuild its data
files:

```bash
cd tools
uv run python sync_data.py     # copy mapping files into the package
uv run python build_web.py     # web/refmeta_bundle.js (converter)
uv run python build_terms.py   # web/terms_data.js (terms explorer)
```

Each script has a `--check` mode, which CI runs. Pushing to `master` publishes the site.

## License

Code and documentation: BSD 2-Clause ([LICENSE](LICENSE)). Files copied from other
projects (specs and example records under `sources/`) keep their own terms; see
[NOTICE.md](NOTICE.md).
