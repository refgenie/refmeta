<!-- refmeta excerpt of https://genome.ucsc.edu/goldenPath/help/trackDb/trackDbHub.html (retrieved 2026-11-17):
     the intro (hub.txt / genomes.txt / useOneFile) and the 'General hub configuration settings' +
     'Assembly hub genome settings' sections. Track-type settings omitted. -->

# Hub Track Database Definition (v3)

## How to declare Dataset Display Settings in Genome Browser Hubs

This page describes all of the settings one might use in creating a
track or assembly hub.
Hubs display your own data in the Genome Browser by hosting your files on a web
server and connecting them with a simple text configuration file, giving you
more control and permanence than custom tracks.
This initial section touches on the files and settings needed in creating
a hub before providing a listing of settings separated by track type.

For those new to creating hubs: Our Hub Basics page provides a simple introduction to creating hubs.

For returning readers: We keep a list of changes
to the trackDb specification below.

### Start with a hub.txt

All hubs must include a top-level hub.txt file. This file contains general settings that
identify your hub in our internal databases and in the Genome Browser interface.
The URL to the hub.txt is used to load your hub. Our Hub Basics describes how to create a hub.txt.
A full listing of hub.txt settings can be found in the
General hub configuration settings section below.

If your hub contains tracks on a single genome assembly, then you can put all of the
hub, genome, and track configuration settings into a single file with
useOneFile.

### Defining your hub's genomes

A genomes.txt is only necessary if you are NOT using the useOneFile setting
as described below. When using useOneFile, one only needs
to include the genome line. This line will reference
a UCSC assembly name (e.g. hg38) or a GenBank assembly available through our
GenArk repository
beginning with GCF or GCA (e.g. GCF_000891275.1). If an assembly is not available in GenArk,
request it.

If your hub contains tracks for more than one
genome, you will need to define a genomes.txt. A full listing of
genomes.txt settings, including those needed for an assembly hub, settings can be found in the Assembly hub "genome" settings section below.

### Use useOneFile on for hubs with only one genome

If your hub is only displaying one genome, one can use the useOneFile on setting
to put all hub, genome, and track configuration settings into a single file.
Load a working example here.

### Declaring track settings

This document describes how to set dataset display characteristics
using "track database" or "trackDb" settings through name-value pair
associations used in a Track Hub's trackDb.txt file.

The text file format for trackDb settings starts by creating a
text block, or "stanza", for each track dataset. These stanzas should be structured
according to the following format specification:

- Lines consist of name-value pairs. The first line of the stanza
      establishes the track name. Additional
      lines will contain further "setting" names followed
      by "values" of one or more words of numbers.

- All trackDb stanzas must begin with a track line and a stanza ends
      with a blank line.

- Periods should be avoided in track names, although there are some
      settings that include periods in the name, e.g. filter.fieldName.

- The format supports '\' continuation characters. If the setting
      is long or complex, break it into several lines using terminating
      '\' characters to make it more readable.

- Text should be ASCII characters, but a limited set of Unicode characters are
      supported for longLabel and
      shortLabel settings.

Here is an example:

```

    track myFirstTrack
    type bigBed 3
    bigDataUrl myFirstTrack.bb
    shortLabel Example Data
    longLabel The data in this track is format "bigBed 3".

Every track stanza should have these five settings
(track type bigDataUrl shortLabel longLabel).
The first line's track key value (myFirstTrack) is the
identifier for the dataset given to the Browser and it must be
unique for each track within your data hub.  After the track key,
the most important setting is the type key. This value
(bigBed 3) tells the Browser the type of format the
data is in, defines how to display it, and determines
which options are available for fine control of that display.
For some configurable features, like filters, an additional
period or plus may be needed (bigBed 5 .) or (bigBed 9 +).

Running hubCheck on your hub.txt file identifies errors in settings, file
paths, and formatting that could prevent your hub from loading correctly. Download hubCheck from the utilities download page and
see the hubCheck
documentation and related
blog post
for more information on validating hubs.

### Using trackDb include statements

Hubs also support the use of include
statements, allowing one to insert a file containing a set of trackDb
stanzas into a primary trackDb. Use this when you have the same track across
several assemblies, or several large, complex tracks.

### Assembly Hubs

Assembly hubs can display novel genome assemblies and annotations in the UCSC
Genome Browser. Note: Many genome assemblies available in GenBank are also available in our
GenArk repository.
If an assembly is not available in GenArk, but is available in GenBank,
request it.
However, if your genome assembly is not yet publicly available, you can make a custom assembly hub.
To create an assembly hub, refer to our
Assembly Hub User Guide or our Quick Start Guide to Assembly Hubs.


[... track settings omitted ...]

### General hub configuration settings

These settings control basic, top-level information regarding your hub, such as
how it is labeled in the Genome Browser interface. Nearly every hub will make
use of these settings.

### Assembly hub "genome" settings

Assembly hubs allow users to
display custom genome assemblies in the Genome Browser.

blat <url> <port>

    Indicates the server and port to be used for the BLAT tool.
    See our documentation for more details about setting up BLAT for your hub.

    Example:

```
   blat yourServer.yourInstitution.edu 17777

chromAlias <url/relativePath>

    Enables the Genome Browser to automatically convert chromosome names in
    submitted custom track data from alternate naming schemes to the names used
    in the assembly. This functionality applies to both custom track data and
    assembly hub data.

    See our chromAlias
    documentation for details on the required file format.

    Example:

```
   chromAlias thisGenome.chromAlias.txt

chromAliasBb <url/relativePath>

    Like chromAlias, except the file is in the compressed, binary bigBed
    format. This allows efficient searching for sequence names without
    requiring the entire text file to be read, which is important
    for assemblies with a large number of sequences.

    See our chromAlias
    documentation for details on the required file format.

    Example:

```
   chromAliasBb thisGenome.chromAlias.bb

chromAuthority <str>

    Indicates which chromosome naming scheme from the chromAlias
    file to be used as the default in the Genome Browser display. The string must
    match a name defined in the chromAlias header.

    Example:

```
   chromAuthority ucsc

chromSizes <url/relativePath>

    Defines a file to be used when displaying the sequences contained in an
    assembly. These are visible from the "View Sequences" link
    on the Gateway page, or with the "vs" keyboard shortcut
    when looking at the main Genome Browser image.

    Example:

```
   chromSizes thisGenome.chromSizes.txt

codonTable default=<id> <sequenceName>=<id> ...

    By default the Genome Browser translates codons to amino acids with the standard
    genetic code, except for sequences named chrM or chrMT, which
    use the vertebrate mitochondrial code. An assembly hub can assign a different
    NCBI
    genetic code to individual sequences with the codonTable setting in the
    genome stanza.

    The value is a space-separated list of sequenceName=id pairs, where
    id is an NCBI translation table number (for example 1 for the standard code,
    2 for vertebrate mitochondrial, 13 for ascidian mitochondrial). The special name
    default sets the code used for any sequence not listed. Sequences with no
    assignment keep the default behavior described above. This affects amino acid display in
    the base position track's three-frame translation, in codon-colored annotation tracks such
    as gene predictions, and on the details pages.

    Note: sequenceName must be the sequence's own name as stored in the
    assembly's .2bit file (the same name used in chrom.sizes), for
    example a RefSeq or GenBank accession such as NC_017929.1. This is the
    internal name even when a chromAlias and chromAuthority cause a
    different name (such as chrM) to be displayed. Because the special
    chrM/chrMT mitochondrial default only applies to sequences whose
    own name is literally chrM or chrMT, an assembly whose
    mitochondrial sequence has an accession name needs an explicit codonTable
    entry to translate it with a mitochondrial code.

    See our assembly hub codonTable documentation for
    more details.

    Example:

```
   codonTable default=1 NC_017929.1=13

defaultPos <chr:start-end>

    Defines the initial view in the Genome Browser, usually highlighting a
    popular gene or region of interest.

    Example:

```
   defaultPos chr7:155799529-155812871

description <str>

    Description of the assembly version that is displayed on the Gateway
    page and title pages for this assembly. It also appears in the assembly
    pull-down menu.

    Example:

```
   description July 2011 Castor bean

descriptionUrl <url/relativePath>

    Specify a relative path or URL link to a webpage (e.g. a paper)
    describing the hub.  For public hubs, this can be used to highlight key
    words to make searching easier and direct users to your hub.

    Example:

```
   descriptionUrl castorBeanHubDescription.html

email <email address>

    Provides users with a contact point for questions related to the hub.

    Example:

```
   email contactEmail@institution.edu

genome <str>

    For hubs on native assemblies, use the UCSC database name (e.g. hg38).
    Genome assemblies in our GenArk Repository can be referenced using their
    GCA_NNN or GCA_NNN identifier (e.g. GCF_000891275.1). If an assembly
    is not available in GenArk,
    request it.

    For custom assemblies, create your own name. This will appear on title pages
    in the Genome Browser.

    Example:

```
   genome ricCom1

genomesFile <url/relativePath>

    References the next definition file in this hub that will describe
    the assemblies and tracks available at this hub. Typically, genomes.txt is
    at the same directory level as this hub.txt; however, it can also be a
    relative path reference to a different directory level.

    Not needed if using useOneFile (recommended).

    Example:

```
   genomesFile genomes.txt

groups <url/relativePath>

    Relative path or URL that points to a file defining track groups, which are collections of
    related tracks displayed together under the main Genome Browser image.

    See our assembly hub groups.txt
    documentation for format details.

    Example:

```
   groups ricCom1/groups.txt

htmlPath <url/relativePath>

    Points to an HTML file with assembly information. The HTML file is
    displayed on the Gateway page.

    Example:

```
   htmlPath ricCom1/description.html

hub <str>

    A short, unique identifier for the hub used internally by the Genome
    Browser software to identify your hub. It must not contain any spaces.

    Example:

```
   hub myRnaSeqData

isPcr <url> <port>

    Indicates the server and port to be used for the In-Silico PCR
    tool. See our documentation for more details about setting up In-Silico
    PCR for your hub.

    Example:

```
   isPcr yourServer.yourInstitution.edu 17779

longLabel <str>

    A longer, more descriptive label for the hub. Should
    be under 70 characters long.

    Example:

```
   longLabel Comment describing this hub contents

orderKey <int>

    Controls the ordering of assemblies in the pull-down menu.
    Useful if you have several assemblies in your hub.

    Example:

```
   orderKey 4800

organism <str>

    Common name of the organism, displayed alongside the description on
    title pages. It also appears in the assembly pull-down menu.

    Example:

```
   organism Orangutan

scientificName <str>

    Scientific name of organism, displayed alongside the description on
    title pages. It also appears in the assembly pull-down menu.

    Example:

```
   scientificName Ricinus communis

shortLabel <str>

    A short description of the hub. Used as track group label
    below the main Genome Browser image. Should be under 20 characters.

    Example:

```
   shortLabel ENCODE3 RNA-seq Data

trackDb <url/relativePath>

    Relative path or URL to the file that defines the tracks for the assembly
    specified by the genome setting.

    Not necessary if using the useOneFile setting (recommended).

    Example:

```
   trackDb ricCom1/trackDb.txt

transBlat <url> <port>

    Indicates the server and port to be used for the "translated DNA/RNA" options
    in the BLAT interface.
    See our documentation for more details about setting up BLAT for your hub.

    Example:

```
   transBlat yourServer.yourInstitution.edu 17778

twoBitPath <url/relativePath>

    Relative path or URL to the .2bit sequence file for the assembly. This
    file is typically generated from FASTA files using the faToTwoBit command-line
    program, available from our download
    server.

    Example:

```
   twoBitPath ricCom1/ricCom1.2bit

useOneFile <on>

    If the hub only has tracks on a single genome, useOneFile
    allows all hub and track configuration settings to be in a single file.
    See our documentation for more details.

    Example:

```
   useOneFile on

Example of an opening hub stanza

```

    hub hubName
    shortLabel genome
    longLabel Comment describing this hub contents
    genomesFile genomes.txt
    email contactEmail@institution.edu
    descriptionUrl aboutHub.html

Example of a genome stanza

```

    genome ricCom1
    trackDb ricCom1/trackDb.txt
    groups ricCom1/groups.txt
    description July 2011 Castor bean
    twoBitPath ricCom1/ricCom1.2bit
    organism Castor bean
    defaultPos E09R7372:1000000-2000000
    orderKey 4800
    scientificName Ricinus communis
    htmlPath ricCom1/description.html
    transBlat yourLab.yourInstitution.edu 17777
    blat yourLab.yourInstitution.edu 17777
    isPcr yourLab.yourInstitution.edu 17779

    This is the configuration needed for an assembly hub displaying
    a custom genome assembly. To display tracks on a UCSC-hosted assembly,
    you will only need the genome setting if you are using
    useOneFile.

