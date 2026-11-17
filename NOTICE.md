# Third-party files

The `spec/` and `examples/` folders under `sources/` hold copies of other projects'
documentation, schemas and public metadata records. They are here so that anyone can
check each mapping against the text it is based on, and so the tests can run on real
records. Files under `examples/constructed/` were made by refmeta, and each folder's
README says how.

These copies are not covered by refmeta's BSD license. They stay under the terms of the
people who made them. Each source's `README.md` lists where every file came from and when
it was retrieved.

| Folder | Copied from |
|---|---|
| `sources/bioconductor/` | Bioconductor packages (Seqinfo, GenomeInfoDb, BSgenome, BSgenomeForge, AnnotationHub) |
| `sources/ena/` | European Nucleotide Archive, EMBL-EBI |
| `sources/ensembl/` | Ensembl, EMBL-EBI |
| `sources/fhr/` | FAIR-bioHeaders (FHR) project |
| `sources/ga4gh/` | GA4GH refget and VRS specifications, samtools hts-specs (SAM, VCF), biocommons SeqRepo |
| `sources/galaxy/` | Galaxy Project (galaxy, tools-iuc, idc repositories) and the usegalaxy.org and usegalaxy.eu servers |
| `sources/ncbi/` | NCBI (Datasets and the genomes FTP site) |
| `sources/nfcore/` | nf-core pipelines and nf-core/references, Illumina iGenomes |
| `sources/refgenie/` | refgenie projects (refgenie, refgenie-registry, api.refgenie.org) |
| `sources/ucsc/` | UCSC Genome Browser (downloads site and REST API) |

If you maintain one of these projects and want a file removed or credited differently,
please open an issue.
