<!-- Converted to text by refmeta from https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-sequence/ (retrieved 2026-11-17). Tags stripped; tables flattened to pipe rows. -->

# Genome sequence report
Genome assembly sequence accessions, chromosome, and length
Contents

# Genome sequence report
Genome assembly sequence accessions, chromosome, and length
The downloaded genome package contains a genome sequence data report in
JSON Lines
format in the file:

ncbi_dataset/data/<assembly>/sequence_report.jsonl

Each line of the genome assembly sequence data report file is a
JSON
object that represents a single genome assembly sequence record. The schema of the genome assembly sequence record
is defined in the table below where each row in SequenceInfo describes a single field in the report.Table fields that include a Table Field Mnemonic can be used with the
dataformat command-line tool's
--fields option. Refer to the
dataformat CLI tool reference to see
how you can use this tool to transform assembly sequence data reports from JSON Lines to tabular formats.

### Sample report

```
{
  "assemblyAccession": "GCF_000001405.40",
  "assemblyUnit": "Primary Assembly",
  "assignedMoleculeLocationType": "Chromosome",
  "chrName": "1",
  "gcCount": "103674491",
  "gcPercent": 41.5,
  "genbankAccession": "CM000663.2",
  "length": 248956422,
  "refseqAccession": "NC_000001.11",
  "role": "assembled-molecule",
  "sequenceName": "1",
  "sortOrder": 1,
  "ucscStyleName": "chr1",
  "unlocalizedCount": 9
}
```

### SequenceInfo Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| assemblyAccession| accession| Assembly Accession| string| The genome assembly accession| GCF_000001405.40
 |
| chrName| chr-name| Chromosome name| string| The name of the associated chromosome. The name "Un" indicates that the chromosome is unknown.| 21
MT
Un
 |
| ucscStyleName| ucsc-style-name| UCSC style name| string| Name ascribed to this sequence by the UC Santa Cruz genome browser| chr21
chrM
Un
 |
| sortOrder| ordering| Ordering| uint32| A sort order value assigned to the sequence| 1
25
 |
| assignedMoleculeLocationType| mol-type| Molecule type| string| The type of molecule represented by the sequence| Chromosome
Mitochondrion
 |
| refseqAccession| refseq-seq-acc| RefSeq seq accession| string| The RefSeq accession of the sequence| NC_000021.9
 |
| assemblyUnit| assm-unit-acc| Assembly-unit name| string| Name of the assembly unit, or set of sequences that comprise the assembly.| Primary Assembly
non-nuclear
 |
| length| seq-length| Seq length| uint32| The length of the sequence in nucleotides| 46709983
 |
| genbankAccession| genbank-seq-acc| GenBank seq accession| string| The GenBank accession of the sequence| CM000683.2
 |
| gcPercent| gc-percent| GC Percent| float| The percentage of GC base-pairs in the chromosome|  |
| unlocalizedCount| unlocalized-count| Unlocalized Count| uint32| Number of scaffolds that are unlocalized on a given chromosome|  |
| assemblyUnplacedCount| assembly-unplaced-count| Assembly Unplaced Count| uint32| Number of unplaced scaffolds for a given assembly accession|  |
| role| role| Role| string| |  |
| sequenceName| sequence-name| Sequence name| string| The sequence name|  |

### Scalar Value Types
| | Protocol buffers type| Notes| C++| Python| Java| Go |
| double| | double| float| double| float64 |
| float| | float| float| float| float32 |
| int32| Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead.| int32| int| int| int32 |
| int64| Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead.| int64| int/long| long| int64 |
| uint32| Uses variable-length encoding.| uint32| int/long| int| uint32 |
| uint64| Uses variable-length encoding.| uint64| int/long| long| uint64 |
| sint32| Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s.| int32| int| int| int32 |
| sint64| Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s.| int64| int/long| long| int64 |
| fixed32| Always four bytes. More efficient than uint32 if values are often greater than 2^28.| uint32| int| int| uint32 |
| fixed64| Always eight bytes. More efficient than uint64 if values are often greater than 2^56.| uint64| int/long| long| uint64 |
| sfixed32| Always four bytes.| int32| int| int| int32 |
| sfixed64| Always eight bytes.| int64| int/long| long| int64 |
| bool| | bool| boolean| boolean| bool |
| string| A string must always contain UTF-8 encoded or 7-bit ASCII text.| string| str/unicode| String| string |
| bytes| May contain any arbitrary sequence of bytes.| string| str| ByteString| []byte |

Generated November 12, 2026
