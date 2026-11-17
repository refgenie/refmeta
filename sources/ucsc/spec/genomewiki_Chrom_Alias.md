Chrom Alias - genomewiki

-

-

-

-

-

# Chrom Alias

				From genomewiki

Jump to navigationJump to search

## Contents

- 1 Usage

- 2 Format

- 3 Example

- 4 assembly hub

- 5 best performance

- 6 set default

## Usage

The chrom alias mechanism functions automatically in the genome browser for custom
track data and assembly hub data.  It will convert chromosome names in the submitted
custom track data from alternate naming schemes to the names used in the assembly in the genome browser.

## Format

The first line of the chromAlias.txt file begins with the pound symbol #
followed by a blank space.  Subsequent words, separated by a tab character,
on this first line are the identification of the source authority for names
in that column of the file.  The first column set of names are the names of
sequences used in the genome browser sequence.  Subsequent columns are alternate
naming schemes.

The lines following that first column header title line are columns of sequence
names separated by a tab character.  For the case of no equivalent name in
that name space, the column is empty, there will be two adjacent tab characters.

## Example

```
# ucsc  assembly        genbank ncbi    refseq  ensembl
chr1    1       CM000663.2      1       NC_000001.11    1
chr10   10      CM000672.2      10      NC_000010.11    10
chrM    MT      J01415.2        MT      NC_012920.1     MT
chrX    X       CM000685.2      X       NC_000023.11    X

In this example, the columns are:

- ucsc - UCSC style chrN names

- assembly - names from NCBI file assembly_report.txt

- genbank - INSDC names

- ncbi - from chr2acc file in assembly_structure/ hierarchy

- refseq - names from RefSeq annotations

- ensembl - names from Ensembl assembly

## assembly hub

To use the chromAlias.txt file in an assembly hub, in the genome stanza, specify

```
 chromAlias thisGenome.chromAlias.txt

which is a relative path reference from this hub.txt file.

For example:

```
genome GCF_000001405.39
taxId 9606
groups groups.txt
description human
twoBitPath GCF_000001405.39.2bit
twoBitBptUrl GCF_000001405.39.2bit.bpt
chromSizes GCF_000001405.39.chrom.sizes.txt
chromAlias GCF_000001405.39.chromAlias.txt
organism human
defaultPos chr1:82985474-82995474
scientificName Homo sapiens
htmlPath html/GCF_000001405.39_GRCh38.p13.description.html

Working examples:

```
hub.txt
chromAlias.txt

## best performance

For best usage performance, the chromAlias.txt file can be converted to a bigBed format
file to allow appropriate searching for names without reading the entire text file.  This is
important for assemblies with high count numbers of sequences.  The perl script:

```
 aliasTextToBed.pl

can convert the chromAlias.txt file into a bed file and the bigBed file:

```
 aliasTextToBed.pl -chromSizes=asmId.chrom.sizes -aliasText=asmId.chromAlias.txt \
   -aliasBed=asmId.chromAlias.bed -aliasAs=asmId.chromAlias.as -aliasBigBed=asmId.chromAlias.bb

The inputs are the chrom.sizes and the chromAlias.txt files, the outputs are the chromAlias.bed,
chromAlias.as and chromAlias.bb file.

Specify the chromAlias.bb file in genome stanza of the hub.txt definition:

```
chromAliasBb GCF_000001405.39.chromAlias.bb

instead of the chromAlias.txt file and not using the chromAlias specification.

## set default

A default naming scheme can be set in the hub.txt file with the chromAuthority setting:

```
chromAuthority ucsc

Where the name specified, in this example ucsc is the column header from
the chromAlias.txt file.  This will cause the names in that column to be
the display names in the genome browser.

Retrieved from "https://genomewiki.ucsc.edu/index.php?title=Chrom_Alias&oldid=27365"

## Navigation menu

### Page actions

- Page
- Discussion
- Read
- View source
- History

### Page actions

- Page
- Discussion
- More
- Tools

### Personal tools

- Log in

### Navigation

- Main Page
- Help
- Categories
- New Pages
- Recent changes
- User Listing
- My Preferences

### Search

### related sites

- Science And Justice

### hosted projects

- Encode Project
- Opsin Evolution

### Tools

- What links here
- Related changes
- Special pages
- Printable version
- Permanent link
- Page information

-  This page was last edited on 17 September 2025, at 20:56.

- Privacy policy
- About genomewiki
- Disclaimers
