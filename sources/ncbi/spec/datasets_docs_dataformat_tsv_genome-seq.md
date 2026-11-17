<!-- Converted to text by refmeta from https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/dataformat/tsv/dataformat_tsv_genome-seq/ (retrieved 2026-11-17). Tags stripped; tables flattened to pipe rows. -->

# genome-seq
Convert an NCBI Datasets Genome Assembly Sequence Report (JSONL) to a tabular (TSV) format
Contents

# genome-seq
Convert an NCBI Datasets Genome Assembly Sequence Report (JSONL) to a tabular (TSV) format

### Name
dataformat tsv genome-seq - Convert an NCBI Datasets Genome Assembly Sequence Report (JSONL) to a tabular (TSV) format

### Synopsis
dataformat tsv genome-seq [flags]

### Description
Convert an NCBI Datasets Genome Assembly Sequence Report (JSONL) to a tabular (TSV) format.
For more details on how to generate tables and field descriptions, see https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/using-dataformat/

### Examples

```
  dataformat tsv genome-seq --inputfile human_package/ncbi_dataset/data/GCF_000001405.40/sequence_report.jsonl --fields accession,'gc*','*count'
  dataformat tsv genome-seq --package human.zip --inputfile GCF_000001405.40/sequence_report.jsonl

```

### Options

```
      --elide-header       Do not output header
      --fields strings     Comma-separated list of field names that supports wildcards (*). Names with wildcards must be quoted, for example: accession,'gc*','*count'
      --force              Force dataformat to run without type check prompt
  -h, --help               help for genome-seq
      --inputfile string   Input file (default "/dev/stdin")
      --package string     Data package (zip archive), inputfile parameter is relative to the root path inside the archive

```

### Fields
| | Mnemonic| Name |
| accession| Assembly Accession |
| assembly-unplaced-count| Assembly Unplaced Count |
| assm-unit-acc| Assembly-unit name |
| chr-name| Chromosome name |
| gc-percent| GC Percent |
| genbank-seq-acc| GenBank seq accession |
| mol-type| Molecule type |
| ordering| Ordering |
| refseq-seq-acc| RefSeq seq accession |
| role| Role |
| seq-length| Seq length |
| sequence-name| Sequence name |
| ucsc-style-name| UCSC style name |
| unlocalized-count| Unlocalized Count |

Generated November 12, 2026
