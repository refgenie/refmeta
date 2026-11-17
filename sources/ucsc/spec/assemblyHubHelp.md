Assembly Hub User Guide

-

-

-

-

-

-
Skip to main content

☰Login

- Home

- Genomes

- Human GRCh38/hg38

- Human GRCh37/hg19

- Human T2T-CHM13/hs1

- Mouse GRCm39/mm39

- Mouse GRCm38/mm10

- Genome Repository GenArk

- Other

- Genome Browser

- Back to Genome Browser

- Configure

- Track Search

- Short Exact DNA Match

- Reset All User Settings

- Tools

- Blat

- In-Silico PCR

- Table Browser

- LiftOver

- Variant Annotation Integrator

- Data Integrator

- Gene Interactions

- Other Tools

- Mirrors

- Euro/Asia Mirrors

- Mirroring Instructions

- Downloads

- Genome Data

- Source Code

- Genome Browser Store

- Utilities

- FTP

- MySQL Access

- Cloud Access

- REST API

- My Data

- Custom Tracks

- My Sessions

- Track Hubs

- Hub Upload

- Track Collection Builder

- Public Sessions

- Projects

- Genotype Tissue Expression (GTEx)

- Encyclopedia of DNA Elements (ENCODE)

- UCSC Cell Browser

- UCSC COVID-19 Research

- Help

- FAQs & Search

- Browser Documentation

- Training

- Contact Us

- About Us

- News

- Cite Us

- Release Log

- Staff

- Conditions of Use

- Our History

- Licenses

- Contact Us

# Assembly Hub User Guide

## Overview

An Assembly Data Hub is a set of Internet-accessible data files that define the reference sequence
to be used for a browser instance, as well as all the data files that define the annotation for
that sequence. Assembly Data Hubs allow researchers to use the UCSC Genome Browser to view their
own sequences with associated annotation, without the requirement that UCSC support a browser on that sequence.

Note: if you are working with a genome that has already been submitted
to the NCBI Assembly system, it may
already be available in the UCSC Genome Browser.
Please check the GenArk Assembly Hub collection
to see if your genome of interest is already available. If it is not listed there, you can use the
UCSC Assembly Request page to request that the genome assembly be
added.

## Contents

###### Web Server

###### Assembly Hub Components

- hub.txt

- genomes.txt

- 2bit File

- chromAlias

- groups.txt

- Single-File Track Hub

###### Checking Your Hub

###### Linking to Your Assembly Hub

###### Building Tracks

- Cytoband Track

###### Assembly Hub Resources

- G-OnRamp

- MakeHub

- Example NCBI Assembly Hubs

- Exploring the Files Behind the Hub

###### Adding BLAT Servers

- Configuring Assembly Hubs to Use a Dedicated gfServer

- Troubleshooting BLAT Servers

- Configuring Assembly Hubs to Use a Dynamic gfServer

- Check gfServer Status for Dynamic Servers

## Web Server

To display a novel genome sequence in the UCSC Genome Browser, a web server hosted by the
institution (or a free service such as Cyverse)
can be used. For environments operating behind a firewall, hub files can also be loaded locally
through GBiB to provide access to the UCSC Genome
Browser. Hosting hub files over HTTP is strongly recommended, as it is
significantly more efficient than FTP. A hierarchical directory structure must then be
established to organize the files associated with the genome sequence. For example:

```

myHub/ - directory to organize your files on this hub
    hub.txt - primary reference text file to define the hub, refers to:
    genomes.txt - definitions for each genome assembly on this hub
        newOrg1/ - directory of files for this specific genome assembly
            newOrg1.2bit - '2bit' file constructed from your fasta sequence
            description.html - information about this assembly for users
            trackDb.txt - definitions for tracks on this genome assembly
            groups.txt - definitions for track groups on this assembly
            bigWig and bigBed files - data for tracks on this assembly
            external track hub data tracks

The hub can be referenced by a URL such as: http://yourLab.yourInstitution.edu/myHub/hub.txt

## Assembly Hub Components

### hub.txt

The initial file, hub.txt is the primary URL reference for the assembly hub:

Format of the file:

```

hub hubName
shortLabel genome
longLabel Comment describing this hub contents
genomesFile genomes.txt
email contactEmail@institution.edu
descriptionUrl aboutHub.html

shortLabel is the name that will appear in the genome pull-down menu at the
UCSC gateway page.

genomesFile is a reference to the next definition file in this chain that will
describe the assemblies and tracks available at this hub. Typically, genomes.txt is at
the same directory level as this hub.txt; however, it can also be a relative path
reference to a different directory level.

email provides users with a contact point for questions related to this assembly hub.

descriptionUrl specifies a relative path or URL link to a webpage describing the hub.

You can view a working example at hub.txt

### genomes.txt

The genomes.txt file provides references to the genome assemblies and tracks available in
the assembly hub.

```

genome ricCom1
trackDb ricCom1/trackDb.txt
groups ricCom1/groups.txt
description July 2011 Castor bean
twoBitPath ricCom1/ricCom1.2bit
organism Ricinus communis
defaultPos E09R7372:1000000-2000000
orderKey 4800
scientificName Ricinus communis
htmlPath ricCom1/description.html
transBlat yourLab.yourInstitution.edu 17777
blat yourLab.yourInstitution.edu 17779
isPcr yourLab.yourInstitution.edu 17779

Multiple assembly definitions can be included in a single file, separated by blank lines. The file
references are relative paths. In this example, the subdirectory ricCom1 contains
the files for this specific assembly.

- genome is equivalent to the UCSC database name. This name appears on title
	    pages in the Genome Browser.

- trackDb points to the file that defines the tracks for this genome
	    assembly (see the
	    Track Hub
	    help documentation for details).

- groups points to the file defining track groups, which are collections of
	    related tracks displayed together under the main Genome Browser image.

- description is displayed on the Gateway page and title pages for this
	    assembly. It also appears in the assembly pull-down menu.

- twoBitPath points to the .2bit sequence file for the assembly.
	    This file is typically generated from FASTA files using the faToTwoBit
	    kent program. The path can also point to a URL.

- organism is displayed alongside the description on title pages. It also
	    appears in the assembly pull-down menu.

- defaultPos defines the initial view in the Genome Browser, usually
	    highlighting a popular gene or region of interest.

- orderKey controls the ordering of assemblies in the pull-down menu.

- htmlPath points to the HTML file with assembly information. The HTML file
	    is displayed on the Gateway page.

- transBlat, blat, and isPcr configure
	    different gfServer instances for amino acid searches, BLAT alignments, and PCR.
	     More here.

- codonTable assigns genetic codes (translation tables) to sequences for
	    amino acid display. More here.

Note: it is strongly recommended that each genome stanza includes defaultPos,
scientificName, organism, description, so that the hub loads with
meaningful defaults and can be more easily searched from the Gateway page.

### 2bit File

The .2bit file is constructed from the FASTA sequence for the assembly using the
faToTwoBit kent program (available from the
downloads page).

Example:

```

faToTwoBit ricCom1.fa ricCom1.2bit

Use twoBitInfo to verify sequences and create a chrom.sizes file,
which is not used in the hub itself but is helpful for constructing big* files:

```

twoBitInfo ricCom1.2bit stdout | sort -k2rn > ricCom1.chrom.sizes

The .2bit file can also be read directly from a URL, so these commands work against a
hosted hub without downloading the file first:

```

twoBitInfo https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubPlants/cshl2013/ricCom1/ricCom1.2bit stdout | sort -k2nr > ricCom1.chrom.sizes

Add -udcDir=/your/cache/dir to control where the downloaded blocks are cached. Note
that this option takes a directory, not the URL of the .2bit file.

To extract sequences from a .2bit file:

```

twoBitToFa -seq=chrCp https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubPlants/cshl2013/ricCom1/ricCom1.2bit stdout > ricCom1.chrCp.fa

### chromAlias

The chromAlias setting enables the Genome Browser to automatically convert chromosome
names in submitted custom track data from alternate naming schemes to the names used in the
assembly. The chromAlias setting uses a chromAlias.txt file. This
functionality applies to both custom track data and assembly hub data.

chromAlias.txt Format

The first line of the chromAlias.txt file begins with a pound symbol (#)
followed by a blank space. Each subsequent word on this line, separated by tab characters,
specifies the source authority for the sequence names in that column. The first column contains the
sequence names used in the Genome Browser assembly, while the subsequent columns provide alternate
naming schemes.

All lines following the header line consist of columns of sequence names separated by a tab
character. If no equivalent name exists in a particular naming scheme, the column remains empty,
resulting in two adjacent tab characters.

Example:

```

# ucsc  assembly        genbank ncbi    refseq  ensembl
chr1    1       CM000663.2      1       NC_000001.11    1
chr10   10      CM000672.2      10      NC_000010.11    10
chrM    MT      J01415.2        MT      NC_012920.1     MT
chrX    X       CM000685.2      X       NC_000023.11    X

In this example, the columns represent:

- ucsc -  UCSC-style chrN names

- assembly - names from the NCBI assembly_report.txt file

- genbank - INSDC names

- ncbi - names from the chr2acc file in the assembly_structure/ hierarchy

- refseq - names from RefSeq annotations

- ensembl - names from the Ensembl assembly

Assembly Hub Usage

To use the chromAlias.txt file in an assembly hub, add the following line to the
genome stanza, which lives in genomes.txt in a multi-file hub or in
hub.txt itself in a single-file hub:

```
chromAlias thisGenome.chromAlias.txt

This is a relative path reference from the hub.txt file.

Example genome stanza:

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

Best Performance

For improved performance, the chromAlias.txt file can be converted to a bigBed format.
This enables efficient searching for sequence names without requiring the entire text file to be
read, which is particularly important for assemblies with large numbers of sequences.

The Perl script
aliasTextToBed.pl converts the chromAlias.txt file into the
corresponding bed and bigBed files:

```

aliasTextToBed.pl -chromSizes=asmId.chrom.sizes -aliasText=asmId.chromAlias.txt \
   -aliasBed=asmId.chromAlias.bed -aliasAs=asmId.chromAlias.as -aliasBigBed=asmId.chromAlias.bb

Inputs:

- chrom.sizes file

- chromAlias.txt file

Outputs:

- chromAlias.bed

- chromAlias.as

- chromAlias.bb

Replace the chromAlias setting with the chromAliasBb setting, and specify
the .bb file in the genome stanza of the hub definition:

```
chromAliasBb GCF_000001405.39.chromAlias.bb

This replaces the chromAlias.txt specification.

Default Naming Scheme

A default chromosome naming scheme can be set in the genome stanza using the
chromAuthority setting:

```
chromAuthority ucsc

In this example, the value ucsc corresponds to the column header from the
chromAlias.txt file. This setting ensures that names in the specified column are
displayed by default in the Genome Browser.

Example genome stanza:

```

genome GCF_000001405.39
taxId 9606
groups groups.txt
description human
twoBitPath GCF_000001405.39.2bit
twoBitBptUrl GCF_000001405.39.2bit.bpt
chromSizes GCF_000001405.39.chrom.sizes.txt
chromAlias GCF_000001405.39.chromAlias.txt
chromAuthority ucsc
organism human
defaultPos chr1:82985474-82995474
scientificName Homo sapiens
htmlPath html/GCF_000001405.39_GRCh38.p13.description.html

Genetic Codes (codon translation tables)

By default the Genome Browser translates codons to amino acids with the standard genetic code,
except for sequences named chrM or chrMT, which use the vertebrate
mitochondrial code. An assembly hub can assign a different
NCBI genetic
code to individual sequences with the codonTable setting in the genome stanza:

```
codonTable default=1 NC_017929.1=13

The value is a space-separated list of sequenceName=id pairs, where id
is an NCBI translation table number (for example 1 for the standard code, 2 for vertebrate
mitochondrial, 13 for ascidian mitochondrial). The special name default sets the code
used for any sequence not listed. Sequences with no assignment keep the default behavior described
above. This affects amino acid display in the base position track's three-frame translation, in
codon-colored annotation tracks such as gene predictions, and on the details pages.

Note: sequenceName must be the sequence's own name as stored in the assembly's
.2bit file (the same name used in chrom.sizes), for example a RefSeq or GenBank
accession such as NC_017929.1. This is the internal name even when a
chromAlias and chromAuthority cause a different name (such as
chrM) to be displayed. Because the special chrM/chrMT
mitochondrial default only applies to sequences whose own name is literally chrM or
chrMT, an assembly whose mitochondrial sequence has an accession name needs an explicit
codonTable entry to translate it with a mitochondrial code.

Example genome stanza (translating the mitochondrial sequence with the ascidian mitochondrial
code, table 13):

```

genome GCF_000224145.3
taxId 7719
groups groups.txt
description vase tunicate
twoBitPath GCF_000224145.3.2bit
codonTable default=1 NC_017929.1=13
organism KH Sep. 2013
defaultPos NC_020166.2:3347001-3357001
scientificName Ciona intestinalis

### groups.txt

The groups.txt file defines the grouping of track controls under the Genome Browser graphic
display.

Example:

```

name map
label Mapping
priority 2
defaultIsClosed 0

- The name setting is used in the trackDb.txt file to associate specific tracks with a
       group.

- The label setting specifies the title of the group in the genome browser. By default,
       groups are sorted alphabetically based on the label.

- The priority setting dictates the display order of the track groups, with lower
       numbers shown first.

- The defaultIsClosed setting controls whether the group is initially expanded or
       collapsed (0 for expanded, 1 for collapsed).

Refer to the Adding Groups to a Track hub section of the Track Hubs help page for more
details.

### Single-File Track Hub (useOneFile on)

Traditionally, an assembly hub required multiple configuration files (hub.txt,
genomes.txt, trackDb.txt, and optionally groups.txt), along
with a .2bit file for the sequence. The useOneFile on option simplifies
this by consolidating everything into a single configuration file. Note: The single-file
format supports one genome assembly per file. For multiple assemblies, use the traditional
multi-file setup. A single-file hub that defines a second genome does not report an error: the
Browser uses only the first genome stanza and attaches every track to it.

Example configuration:

```

hub mySingleFileHub
shortLabel My Single-File Hub
longLabel An example of a single-file UCSC track hub
useOneFile on
email myEmail@example.com

genome hg19

track exampleBigWig
shortLabel BigWig Coverage
longLabel Coverage data over hg19
type bigWig
visibility full
bigDataUrl http://myServer.com/data/example.bigWig

track exampleVCF
shortLabel VCF Variants
longLabel Variant calls over hg19 region
type vcfTabix
visibility pack
bigDataUrl http://myServer.com/data/example.vcf.gz

- The hub stanza with the useOneFile on setting replaces hub.txt.

- The genome line replaces genomes.txt.

- The track stanzas replace trackDb.txt.

If your hub requires a reference genome sequence, you can still provide a .2bit file
with twoBitPath. Grouping (previously in
groups.txt) can also be integrated here if needed.

Once hosted on a server, the single configuration file (and associated data files such as
.bigWig, .vcf.gz, .2bit) can be loaded into the UCSC Genome
Browser via the Connected Hubs tab of the
Track Data Hubs page.

## Building Tracks

Tracks are defined in the trackDb.txt file, where each stanza specifies how
tracks are displayed (shortLabel, longLabel, color, visibility), along with other information such
as the group the track belongs to (referencing groups.txt) and whether
additional HTML should be displayed when a user clicks into the track or a track item:

```

track gap_
longLabel Gap
shortLabel Gap
priority 11
visibility dense
color 0,0,0
bigDataUrl bbi/ricCom1.gap.bb
type bigBed 4
group map
html ../trackDescriptions/gap

For more information about the syntax of the trackDb.txt file, refer to the
Track Database Definition page.

Processing genomes to construct tracks often requires a cluster or supercomputer. Small
genomes can be processed on single computers with multiple cores. The process for each track is
unique. For details, refer to the

	Browser Track Construction page, which discusses constructing tracks for assembly
hubs.

### Cytoband Track

Assembly hubs can include a Cytoband track, which allows quicker navigation of chromosomes and
displays banding pattern information, if known.

A simple version of the track can be built using the existing chrom.sizes file for your assembly.
Banding options include: gneg, gpos25,
	gpos50, gpos75, gpos100, acen, gvar, or stalk).

Example:

```

cat araTha1.chrom.sizes | sort -k1,1 -k2,2n | awk '{print $1,0,$2,$1,"gneg"}' > cytoBandIdeo.bed

The resulting BED file can be converted into a BigBed file and associated with an .as
definition file (see
example)
to inform the browser that this is not a standard BED:

```

bedToBigBed -type=bed4 cytoBandIdeo.bed -as=cytoBand.as araTha1.chrom.sizes cytoBandIdeo.bigBed

In trackDb.txt, if the track is named cytoBandIdeo (e.g.,
track cytoBandIdeo), it will automatically load into the assembly
hub.

## Checking Your Hub

Before loading a new or edited hub in the Browser, run hubCheck against it. The utility is
available from the downloads
page. It reads the hub the way the Browser does and reports missing files, malformed stanzas,
settings the Browser does not recognize and data files it cannot open:

```

hubCheck https://yourLab.yourInstitution.edu/myHub/hub.txt

Problems are reported with the line number of the stanza they came from, which is usually quicker
than working backwards from a hub that loads but shows nothing. A clean run reports no problems;
purely cosmetic omissions, such as a missing hub description page, come back as warnings rather
than errors.

Note: hubCheck validates the files it is given, so it cannot catch every problem. In
particular it does not flag a single-file hub that defines more than
one genome, which fails silently in the Browser.

## Linking to Your Assembly Hub

Once the hub is hosted, you can link straight to a genome inside it. Give the
hubUrl of your hub.txt and the genome you want, and the Browser
loads the hub and opens that assembly.

-
	Directly to the genome browser:

	https://genome.ucsc.edu/cgi-bin/hgTracks?genome=araTha1&hubUrl=https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/hub.txt

-
	To the gateway page instead:

	https://genome.ucsc.edu/cgi-bin/hgGateway?genome=araTha1&hubUrl=https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/hub.txt

For hubs published in GenArk
there is a shorter form still, https://genome.ucsc.edu/h/ followed by the accession,
for example
https://genome.ucsc.edu/h/GCA_030020305.1.

A longer form exists that routes through the hub connect page. It is worth knowing about only when
you need the Browser to rebuild the hub's track list rather than reuse what it has already
cached, which is occasionally useful while a hub is still being developed:

```

https://genome.ucsc.edu/cgi-bin/hgHubConnect?hgHub_do_redirect=on&hgHubConnect.remakeTrackHub=on&hgHub_do_firstDb=1&hubUrl=yourHubUrl

## Assembly Hub Resources

Resources for automatically building assembly hubs include G-OnRamp and MakeHub.

### G-OnRamp

G-OnRamp is a Galaxy workflow that turns a genome assembly and RNA-Seq data into a Genome Browser
with multiple evidence tracks. Since G-OnRamp is based on the Galaxy platform, becoming familiar
with Galaxy concepts and functionalities is recommended. See their
instruction page
for an overview.

### MakeHub

MakeHub is a command-line tool for fully automatic generation of track data hubs for visualizing
genomes with the UCSC Genome Browser. More information is available on their
GitHub page.

### Example NCBI assembly hubs

UCSC builds assembly hubs from NCBI GenBank and RefSeq genomes and publishes them as
GenArk, the UCSC Genome
Repository. Every hub there is public. You can load one in the Genome Browser as it stands, or
copy its structure as a working template for a hub of your own.

The GenArk index groups assemblies by clade, covering primates, mammals, birds, fishes, other
vertebrates, invertebrates, plants, fungi, viruses, archaea and bacteria. It also lists curated
collections drawn from those clades, among them the Vertebrate Genomes Project, the California
Conservation Genomics Project and the Human Pangenome Reference Consortium. Assemblies that a
newer version has superseded move to a separate legacy collection. New assemblies are added
continuously, so the index is the place to check what exists today, not any list copied onto
this page.

Each clade page gives one row per assembly, with a common name, a scientific name, an NCBI
accession, a BioSample, a BioProject and a release date. The common name links to the assembly
open in the Genome Browser, and the scientific name links to the directory of files that make up
the hub.

These hubs follow NCBI accession naming patterns, so the genome name is an accession such
as GCA_030020305.1 instead of a UCSC database name such as hg38. Gene
predictions from NCBI RefSeq, Augustus and other sources are available for many of the
assemblies. BLAT and In-Silico PCR run on a shared dynamic gfServer, which is how
tens of thousands of assemblies can offer BLAT without a dedicated server each. If you want the
same arrangement for your own hub, see
Configuring assembly hubs to use a dynamic gfServer
below.

#### Example: loading an assembly hub and reading the hub.txt behind it

These steps load one GenArk assembly, the African savanna elephant, and then open the files it
was built from. Every other assembly in the index works the same way.

- Open the GenArk index
	    and click mammals.

- Search the page for African savanna elephant (hap1 mLoxAfr1 2023), accession
	    GCA_030020305.1.

- Click the common name to open the assembly in the Genome Browser. The same assembly is
	    also reachable at
	    https://genome.ucsc.edu/h/GCA_030020305.1, a short form of the
	    hub URL that works for any GenArk accession.

- Back on the index, click the scientific name to open the
	    directory of files behind the hub. The path splits the
	    accession three digits at a time, so GCA_030020305.1 lives under
	    hubs/GCA/030/020/305/.

### Exploring the files behind the hub

That directory holds the complete hub. Reading a few of its files shows the components described
earlier on this page at work in a real example:

- hub.txt is a single-file hub. It sets
	    useOneFile on, so the hub stanza, the genome stanza and every track
	    stanza sit in this one file instead of being split across hub.txt,
	    genomes.txt and trackDb.txt.

- The genome stanza names the sequence and its indexes. twoBitPath points at
	    GCA_030020305.1.2bit, chromSizes and
	    chromAliasBb supply chromosome sizes and
	    alias names, and defaultPos sets the position
	    the browser opens on.

- The blat, transBlat and isPcr lines in that stanza
	    name a dynamic gfServer together with the assembly's path, which is what
	    lets one server answer for many assemblies.

- Every track stanza carries a bigDataUrl naming a file under
	    bbi/, the directory holding the bigBed and bigWig files with the actual
	    data.

- Optional track settings appear throughout, including
	    searchIndex and
	    searchTrix, which make a track searchable through the indexes
	    under ixIxx/;
	    url and
	    urlLabel, which turn item names into outbound links; and
	    html,
	    which attaches a description page from html/ to a track.

- groups.txt defines the track groups that organize the browser display, as covered
	    under groups.txt above.

A trackDb.txt holding the same track definitions sits next to hub.txt in the
directory. The assemblies also ship files that are not part of the hub definition, such as
GCA_030020305.1.fa.gz, the AGP, and RepeatMasker and RepeatModeler output.

## Adding BLAT servers

BLAT servers (gfServer) can be configured as either dedicated or
dynamic:

- Dedicated BLAT servers index a genome at startup and remain running in memory, allowing
		fast responses. The drawback is that they continuously consume memory.

- Dynamic BLAT servers pre-index genomes into files and start on demand to handle a
		request, exiting afterward. They are more memory-efficient and work well for hubs
		with many assemblies or infrequent use. Their response time depends on disk speed
		but improves with repeated access due to operating system caching.

### Configuring assembly hubs to use a dedicated gfServer

When running a local BLAT server, assembly hubs can be configured to support BLAT searches by
adding entries to the
 genomes.txt file.

Installation and configuration details for gfServer are provided in the
Running your own gfServer
page.

In the  genomes.txt stanza for the target assembly, include the following lines (note
the capital B in transBlat):

```

transBlat yourServer.yourInstitution.edu 17777
blat yourServer.yourInstitution.edu 17779
isPcr yourServer.yourInstitution.edu 17779

With this configuration, BLAT and PCR searches become available for the assembly.
For example:

```

http://genome.ucsc.edu/cgi-bin/hgBlat?hubUrl=http://yourServer.yourInstitution.edu/myHub/hub.txt

This URL opens the BLAT interface, where the assembly will appear in the Genome drop-down menu.
The isPcr line enables the use of a different gfServer instance for PCR queries if
desired.

Firewall note: Some institutions block repeated BLAT server queries. In such cases,
administrators must whitelist the following IP ranges:

- 128.114.119.* (U.S. site: genome.ucsc.edu)

- 129.70.40.37 (European mirror: genome-euro.ucsc.edu)

- 134.160.84.3 (Asian mirror: genome-asia.ucsc.edu)

- 128.114.198.32 (UCSC development server)

Further details on gfServer options are available from the
Source Downloads page
(pre-compiled binaries are located in the blat/ directory) and the
blat documentation.

gfServers may also be set up within
GBiB
for local operation; see the
GBiB assembly BLAT setup
guide for detailed instructions.

To terminate a gfServer instance, run:

```
gfServer stop localhost 17779

### Troubleshooting BLAT servers

Errors may occur if translatedBlat and nucleotideBlat port numbers are reversed. A typical
message in this case is:

```
Expecting 6 words from server got 2

If a gfServer instance is started from the same directory as the .2bit file, for example:

```

gfServer start localhost 17779 -stepSize=5 contigsRenamed.2bit &

an attempt to run a DNA sequence query through the web-based BLAT tool may return:

```

Error in TCP non-blocking connect() 111 - Connection refused
Operation now in progress
Sorry, the BLAT/iPCR server seems to be down. Please try again later.

- Process check

		Confirm that a gfServer process is running:

```
ps aux | grep gfServer

- Verify path and filename

		In the genomes.txt, the twoBitPath/filename must match the .2bit file
		used when starting gfServer. The location of the gfServer instance can
		be verified by changing into the directory where gfServer was launched and running
		the appropriate hostname command.

```
hostname -i

		This will return an IP address, for example:
		132.249.245.79

		Test the connection with telnet:
		telnet:

```
telnet yourIP yourPort

		For example:

```
telnet 132.249.245.79 17777

		A successful connection shows:

```
Connected to 132.249.245.79

		If Connection refused appears, gfServer may not be running, or the
		IP/port configuration is incorrect.

		The genomes.txt file should also be checked to confirm that the BLAT
		line matches the correct IP and port. For example:

```
blat 132.249.245.79 17777

		Instead of:

```
blat localhost 17777

- Check gfServer status

		Request status directly from gfServer:

```
gfServer status yourLocation yourPort

        	For example:

```
gfServer status 132.249.245.79 17777

        	Sample output might look like:

```

version 39x1
serverType static
type nucleotide
host localhost
port 17777
tileSize 11
stepSize 5
minMatch 2
pcr requests 0
blat requests 0
bases 0
misses 0
noSig 0
trimmed 0
warnings 0

- Test with gfClient

		A reliable troubleshooting method is to bypass the web interface and use the
		command-line utility gfClient. If gfClient successfully
		connects to gfServer, the IP/port configuration is correct. Running
		gfClient directly verifies connectivity independently of the browser
		interface. From the directory containing the hub's .2bit file, the
		command can be executed as follows:

```
gfClient yourLocation yourPort pathTo2bitFile yourFastaQuery.fa output.psl

		For example:

```
gfClient localhost 17777 . query.fa gfOutput.psl

		Note the . after the port, which tells gfClient to use
		the .2bit file in the current directory. Check gfOutput.psl for BLAT results.

			DNA test

```
gfClient yourServer.yourInstitution.edu 17779 `pwd` test.fa dnaTestOut.psl

                        Protein test

```
gfClient -t=dnaX -q=prot yourServer.yourInstitution.edu 17779 `pwd` proteinSequence.fa proteinOut.psl

		Ensure that the yourAssembly.2bit file is present on the test machine.

### Configuring assembly hubs to use a dynamic gfServer

A dynamic BLAT server is specified with the "dynamic" argument to the
blat, transBlat, and isPcr definitions in the hub
genomes.txt file, followed by the gfServer root-relative path of the
directory containing the .2bit and .gfidx files.

For example:

```

blat yourServer.yourInstitution.edu 4096 dynamic yourAssembly
transBlat yourServer.yourInstitution.edu 4096 dynamic yourAssembly
isPcr yourServer.yourInstitution.edu 4096 dynamic yourAssembly

The genome and gfServer indexes would be:

```

$rootdir/yourAssembly/yourAssembly.2bit
$rootdir/yourAssembly/yourAssembly.untrans.gfidx
$rootdir/yourAssembly/yourAssembly.trans.gfidx

Refer to the
Building gfServer indexes section for detailed instructions on building
   the index.

For large hubs, it is possible to have more deeply nested directories. For instance, the
following NCBI convention:

```

blat yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3
transBlat yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3
isPcr yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3

Which will reference these genome files and indexes:

```

$rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.2bit
$rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.untrans.gfidx
$rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.trans.gfidx

### Checking gfServer status for dynamic servers

A query without specifying genome acts as an "I am alive" check:

```

% gfServer status myserver 4040
version 39x1
serverType dynamic

Specifying a -genome checks that it is valid and provides information on how the index was
built:

```

% gfServer -genome=mm10 -genomeDataDir=test/mm10 status myserver 4040
version 39x1
serverType dynamic
type nucleotide
tileSize 11
stepSize 5
minMatch 2

Using -trans checks the translated index:

```

% gfServer -genome=mm10 -genomeDataDir=test/mm10 -trans status myserver 4040
version 39x1
serverType dynamic
type translated
tileSize 4
stepSize 4
minMatch 3

    UCSC Home

    BSOE Home

    Genomics Institute Home

    Licenses

    Training

    FAQs & Search

    Cite Us

    Publications

    Store

    Contact

    Suggestions

    Jobs

        

        

          Donate

    © 2000-2026 The Regents of the University of California. All Rights Reserved.

    Conditions of Use
