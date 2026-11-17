REST API data interface

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

# REST API data interface

## Contents

###### Why you may not want to use this API

###### What are REST and JSON?

###### What is the access URL?

###### What type of data can be accessed?

###### Endpoint functions

###### Parameters to endpoint functions

###### Required and optional parameters

###### Supported track types

###### Using the API on mirrors and local installations

###### Example data access, list functions

###### Example data access, getData functions

###### Example data access, Search functions

###### Error return examples

###### Practical examples

## Why you may not want to use this API

Genomic data is considerably large, and computational biologists generally need all the
data that is available for their analyses. Web APIs, as a technology, were designed for retrieving
relatively small pieces of data, often from Javascript. Consequently, Web APIs
may not be the best way to get data from the UCSC Genome Browser.

For this reason, we also provide alternative methods to access our data:

-
    The Table Browser for
    custom exports and reports as tab-separated files and can be joined with other tables.

-
    For tracks that are stored in MySQL, our MySQL/MariaDB server is
    publicly
    accessible.

-
    Dumps of SQL-stored tracks, as well as tracks in binary file formats, can be found on our
    download server.

-
    All binary files on the download server (bigBed, bigWig and derivatives like bigPsl, bigChain,
    etc) can even be streamed over HTTP.

All these options offer faster bulk downloads and are often easier to parse from scripting
languages. If, however, you write Javascript clients or need only a few features within a given
range, then the endpoints documented on this page may address your needs. If you require an
option or endpoint not listed below for your specific use case, contact us and we can try and implement the feature.

### Conditions of use

-
  Avoid excessive or heavy queries that may impact the server performance. Inappropriate query use
  will result in a restriction of access.

-
  We generally recommend a maximum of one hit every second, but there is no strict limit on queries
  using the API. A botDelay system is in place to avoid overloads on the system.

-
  If you begin to notice a significant delay between requests, adjust your code or try an
  alternative method to retrieve our data.

For more details about the Conditions of Use, please refer to the following page,
Genome Browser Conditions of Use.
If you plan to execute a query that you think may be excessive, contact UCSC first to avoid the possibility of temporarily restricting your
access to the REST API.

## What are REST and JSON?

REST is an acronym for REpresentational State Transfer. It states architectural guidelines for how
an API will operate. See also: Principles
of REST.
Like most APIs, ours returns data in JSON format. JSON data is a data transfer
syntax almost identical to the Javascript object and array syntax.
See also: JSON Introduction

## What is the access URL?

This access URL: https://api.genome.ucsc.edu/ is used to access
the endpoint functions.  For example:

```

    wget -O- 'https://api.genome.ucsc.edu/list/publicHubs'

## What type of data can be accessed?

The following data sets can be accessed at this time:

- Find a genome in the UCSC browser with a search string

- List of available public hubs

- List of available UCSC Genome Browser genome assemblies

- List of files available for download for UCSC Browser genome assemblies

- List of genomes from a specified assembly or track hub

- List of available data tracks from a specified hub or UCSC Genome Browser genome assembly
(see also: track definition help)

- List of chromosomes contained in an assembly hub or UCSC Genome Browser genome assembly

- List of chromosomes contained in a specific track of an assembly or track hub, or UCSC Genome
Browser genome assembly

- Return DNA sequence from an assembly hub 2bit file, or UCSC Genome Browser assembly

- Return track data from a specified assembly or track hub, or UCSC Genome Browser assembly

- Return search matches to words in track data, track names, track descriptions, public hub
track names, and public hub descriptions within a UCSC Genome Browser genome assembly

Note: BLAT also supports programmatic URL queries which return in JSON format. See our
BLAT FAQ for more info.

## Endpoint functions to return data

The URL https://api.genome.ucsc.edu/ is used to access
the endpoint functions.  For example:

```

    curl -L 'https://api.genome.ucsc.edu/list/ucscGenomes'

- /findGenome - search for a genome in the UCSC browser

- /list/publicHubs - list public hubs

- /list/ucscGenomes - list UCSC Genome Browser database genomes from database host

- /list/genarkGenomes - list UCSC Genome Browser database genomes from assembly hub host

- /list/hubGenomes - list genomes from specified hub

- /list/files - list download files available for specified genome

- /list/tracks - list data tracks available in specified hub or database genome
(see also: track definition help)

- /list/chromosomes - list chromosomes from a data track in specified hub or database

- /list/schema - list the schema for a data track in specified hub or database
genome

- /getData/sequence - return sequence from specified hub or database genome

- /getData/track - return data from specified track in hub or database genome

- /search - return search matches within a UCSC Genome Browser genome assembly

## Parameters to endpoint functions

- maxItemsOutput=1000000 - limit number of items to output, default: 1,000,000, maximum limit:
1,000,000 (use -1 to get maximum output)

- hubUrl=<url> - specify track hub or assembly hub URL

- genome=<name> - specify genome assembly in UCSC Genome Browser or track/assembly hub.  Use with /list/genarkGenomes to test for existence.

- track=<trackName> - specify data track in track/assembly hub or UCSC database genome
assembly

- chrom=<chrN> - specify chromosome name for sequence or track data

- start=<123> - specify start coordinate (0 relative) for data from track or sequence
retrieval (start and end required together). See also: UCSC browser coordinate counting systems

- end=<456> - specify end coordinate (1 relative) for data from track or sequence
retrieval (start and end required together). See also: UCSC browser coordinate counting systems

- q=<search word(s)> - used with /findGenome, a search string

- browser=<mustExist|mayExist|notExist> - used with /findGenome, mustExist result only for assemblies in the UCSC browser, mayExist may exist in the UCSC browser, or may not, notExist not yet available in the browser.  default is mustExist

- statsOnly=1 - on /findGenome function, only show statistics about search result

- year=<2025> - on /findGenome function, only show search result for given year, default is any year

- category=<reference|representative> - on /findGenome function, show search result only for given NCBI category of assembly

- status=<reference|representative> - on /findGenome function, show search result only for given NCBI status of assembly

- level=<complete|chromosome|scaffold|contig> - on /findGenome function, show search result only for given NCBI level of assembly

- trackLeavesOnly=1 - on /list/tracks function, only show tracks, do not show
composite container information

- revComp=1 - on /getData/sequence function, return reverse complement of sequence data

- jsonOutputArrays=1 - on /getData/track function, JSON format is array type
for each item of data, instead of the default object type

- format=text - on /list/files function, return plain text listing
of download files instead of JSON format output (which includes more meta-data information).  Text output contains less meta-data in comment lines prefixed by the '#' hash character.

- search=<term>&genome=<name> - on /search function, specify term to be
search within a UCSC Genome Browser genome assembly

- categories=helpDocs - on /search?search=<term>&genome=<name> function, restrict the search
within the UCSC Genome Browser help documentation

- categories=publicHubs - on /search?search=<term>&genome=<name> function, restrict the search
within the UCSC Genome Browser Public Hubs

- categories=trackDb - on /search?search=<term>&genome=<name> function, restrict the search
within the track database (trackDb) settings

The parameters are added to the endpoint URL beginning with a
question mark ?, and multiple parameters are separated with
the semi-colon ;.  For example:

```

https://api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chrM

## Required and optional parameters

 | Endpoint function | Required | Optional

 | /findGenome | q | statsOnly, browser, year, category, status, level, maxItemsOutput

 | /list/publicHubs | (none) | (none)

 | /list/ucscGenomes | (none) | (none)

 | /list/genarkGenomes | (none) | genome, maxItemsOutput

 | /list/hubGenomes | hubUrl | (none)

 | /list/files | genome | format=text, maxItemsOutput

 | /list/tracks | genome or (hubUrl and genome) | trackLeavesOnly=1

 | /list/chromosomes | genome or (hubUrl and genome) | track

 | /list/schema | (genome or (hubUrl and genome)) and track | (none)

 | /getData/sequence | (genome or (hubUrl and genome)) and chrom | start, end, revComp=1

 | /getData/track | (genome or (hubUrl and genome)) and track | chrom,
(start and end), maxItemsOutput, jsonOutputArrays

 | /search | search and genome | categories=helpDocs,
categories=publicHubs, categories=trackDb

The hubUrl and genome parameters are required together to
specify a unique genome in an assembly or track hub.  The genome for
a track hub will usually be a UCSC database genome.  Assembly hubs will
have their own unique genome sequences.  Specify genome without
a hubUrl to refer to a UCSC Genome Browser assembly.

Using the chrom=<name> parameter will limit the request
to the single specified chromosome.  To limit the request to a specific
position, both start=4321 and end=5678 must be given together.
Using the revComp=1 parameter returns the reverse complement.

Use the genome argument with the /list/genarkGenomes function
to test for the existence of a specific genome assembly in the
Genark set
of assembly hubs.

The /list/files endpoint only works for UCSC hosted genome assemblies,
not for external hosted assembly hubs.

The /findGenome endpoint can find genome assemblies in the browser or
any other assembly available at NCBI even when not in the browser.  Note,
there are almost 4 million assemblies available at NCBI.  All searches are
case insensitive.  Force inclusion: Use a + sign before +word to ensure
it appears in the result.  Exclude words: Use a - sign before -word to
exclude it from the search result.  Wildcard search: Add an * (asterisk) at
end of word* to search for all terms starting with that prefix.

Any extra parameters not allowed in a function will be flagged as an error.

## Supported track types for getData functions

- altGraphX (e.g. 'sibTxGraph' for hg19)

- barChart/bigBarChart

- bed

- bigBed

- bigChain

- bigGenePred

- bigLolly

- bigNarrowPeak

- bigMethyl

- bigMaf

- bigNet

- bigPsl

- bigWig

- chain

- ctgPos (e.g. 'ctgPos2' for hg19)

- expRatio (e.g. 'gnfAtlas2' for mm9)

- factorSource (e.g. 'encRegTfbsClustered' for hg38)

- genePred

- gvf (e.g. 'cnvDevDelayCase' for hg19)

- interact/bigInteract

- narrowPeak

- netAlign

- peptideMapping

- pgSnp

- psl

- rmsk - repeat masker

- wiggle/wig

Work is underway to support additional track types

## Using the API on mirrors and local installations

In order to access the API from a mirror installation
or one of the UCSC official mirrors, the complete URL with the cgi-bin should be used:

- Europe: https://genome-euro.ucsc.edu/cgi-bin/hubApi/

- Asia: https://genome-asia.ucsc.edu/cgi-bin/hubApi/
-

- Mirror installation: https://your.server.edu/cgi-bin/hubApi/

The URL can then be passed any of the functions described in this page:

- list public hubs -
https://genome-euro.ucsc.edu/cgi-bin/hubApi/list/publicHubs

- list UCSC database genomes -
https://genome-asia.ucsc.edu/cgi-bin/hubApi/list/ucscGenomes

## Example data access

Your WEB browser can be configured to interpret JSON data and format
in a convenient browsing format.  Firefox has this function built in,
other browsers have add-ons that can be turned on to format JSON data.
With your browser thus configured, the following links can demonstrate
the functions of the API interface.

### Listing functions

- find any genome with the word 'dog' -
api.genome.ucsc.edu/findGenome?q=dog

- find any genome matching the search string: '+white +rhino* -southern' -
api.genome.ucsc.edu/findGenome?q=%2Bwhite%20%2Brhino%2A%20-southern

- find any genome with the accession id: GCF_028858775.2 -
api.genome.ucsc.edu/findGenome?q=GCF_028858775.2

- find any genome with the name: GRCh38 -
api.genome.ucsc.edu/findGenome?q=GRCh38

- list public hubs -
api.genome.ucsc.edu/list/publicHubs

- list UCSC database genomes -
api.genome.ucsc.edu/list/ucscGenomes

- list GenArk assembly hub genomes -
api.genome.ucsc.edu/list/genarkGenomes?maxItemsOutput=5

- test if genome GCF_028858775.2 exists in the GenArk assembly hub genomes -
api.genome.ucsc.edu/list/genarkGenomes?genome=GCF_028858775.2

- list genomes from specified hub -
api.genome.ucsc.edu/list/hubGenomes?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt

- list tracks from specified hub and genome -
api.genome.ucsc.edu/list/tracks?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ

- list tracks from UCSC database genome -
api.genome.ucsc.edu/list/tracks?genome=hg38

- list chromosomes from UCSC database genome -
api.genome.ucsc.edu/list/chromosomes?genome=hg38

- list chromosomes from specified track in UCSC database genome -
api.genome.ucsc.edu/list/chromosomes?genome=hg38;track=gold

- list chromosomes from assembly hub genome -

api.genome.ucsc.edu/list/chromosomes?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ

- list chromosomes from specified track in assembly hub genome -

api.genome.ucsc.edu/list/chromosomes?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=assembly

- list schema from specified track in UCSC database genome -

api.genome.ucsc.edu/list/schema?genome=hg38;track=knownGene

- list download files for UCSC GenArk genome 'GCF_000955945.1' in JSON format limit 5 items output -

api.genome.ucsc.edu/list/files?genome=GCF_000955945.1;maxItemsOutput=5

- list download files for UCSC genome 'hs1' in plain text format limit 5 items output -

api.genome.ucsc.edu/list/files?genome=hs1;format=text;maxItemsOutput=5

### getData functions

- Get DNA sequence from specified chromosome in UCSC database genome -

api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chrM

- Get DNA sequence from specified chromosome and start,end coordinates in UCSC database genome -

api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chrM;start=4321;end=5678

- Get the reverse complement of the DNA sequence from specified chromosome and start,end coordinates in UCSC database genome -

api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chrM;start=4321;end=5678;revComp=1

- Get DNA sequence from a track hub where 'genome' is a UCSC database -

api.genome.ucsc.edu/getData/sequence?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=mm10;chrom=chrM;start=4321;end=5678

- Get DNA sequence from specified chromosome and start,end coordinates in an assembly hub genome -

api.genome.ucsc.edu/getData/sequence?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;chrom=chr1;start=4321;end=5678

- Get track data for specified track in UCSC database genome -

api.genome.ucsc.edu/getData/track?genome=hg38;track=gold;maxItemsOutput=100

- Get track data for specified track and chromosome in UCSC database genome -

api.genome.ucsc.edu/getData/track?genome=hg38;track=gold;chrom=chrM

- Get track data for specified track, chromosome and start,end coordinates in UCSC database genome -

api.genome.ucsc.edu/getData/track?genome=hg38;track=gold;chrom=chr1;start=47000;end=48000

- Get track data for specified track in an assembly hub genome -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=assembly

- Get track data for specified track and chromosome in an assembly hub genome -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=assembly;chrom=chr1

- Get track data for specified track in a track hub -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=ensGene

- Get track data for specified track and chromosome in a track hub -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=ensGene;chrom=chr1

- Wiggle track data for specified track, chromosome with start and end limits in an assembly hub genome -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=gc5Base;chrom=chr1;start=4321;end=5678

- Wiggle track data for specified track in a UCSC database genome -

api.genome.ucsc.edu/getData/track?genome=galGal6;track=gc5BaseBw;maxItemsOutput=100

- bigBed data from a UCSC database, chrom and start,end limits -

api.genome.ucsc.edu/getData/track?genome=galGal6;track=ncbiRefSeqOther;chrom=chr1;start=750000;end=55700000

### Search functions

- Search matches within a UCSC Genome Browser genome assembly -

api.genome.ucsc.edu/search?search=brca1&genome=hg38

- Search matches within a UCSC Genome Browser genome assembly and restrict the
search within the UCSC Genome Browser help documentation -

api.genome.ucsc.edu/search?search=bigBed&genome=hg38&categories=helpDocs

- Search matches within a UCSC Genome Browser genome assembly and restrict the
search within the UCSC Genome Browser Public Hubs -

api.genome.ucsc.edu/search?search=cerebellum&genome=hg38&categories=publicHubs

- Search matches within a UCSC Genome Browser genome assembly and restrict the
search within the track database (trackDb) settings -

api.genome.ucsc.edu/search?search=signal&genome=hg38&categories=trackDb

### Error return examples

- Request track data for non-existent chromosome in an assembly hub genome -

api.genome.ucsc.edu/getData/track?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt;genome=CAST_EiJ;track=assembly;chrom=chrI;start=43521;end=54321

- Request track data from a restricted track. See FAQ -

api.genome.ucsc.edu/getData/track?genome=hg19;track=decipherSnvs

## Practical examples

### Looking up the schema of a specific track

The easiest way to get the schema for a track is to use the /list/schema function. This
can be used on both file tracks and table tracks:

Request schema for the hg38 CRISPR Targets track -

api.genome.ucsc.edu/list/schema?genome=hg38;track=crisprAllTargets

There is a second indirect way to get the schema which may be preferable in certain cases.
When querying track data with the /getData/track function, the jsonOutputArrays
can be used in conjunction to see the track schema. This includes a description of each field
present in the track. The data will also be returned in JSON array type.

Request data from hg38 gold track in array type -

api.genome.ucsc.edu/getData/track?genome=hg38;track=gold;chrom=chrM;jsonOutputArrays=1

### Hide track container information with trackLeavesOnly parameter

When using the /list/tracks function to see the available tracks in an assembly, it can
be useful to return all tracks in the same hierarchical level. By default, composite and
supertracks will have the subtracks nested below, however, the trackLeavesOnly=1 parameter
can be passed to hide the container information and display all tracks and subtracks at the
same level.

In the following example, the first link does not include the trackLeavesOnly parameter. The
output can be compared to the second link to see the difference, which can be observed in the
conservation track. In the first link, the multiz20way track is nested within the
cons20way track. In the second link, however, the multiz20way subtrack is seen at
an equivalent level with all other tracks, and the container, cons20way, is not
present in the list.

Request available tracks in the rn6 genome -

api.genome.ucsc.edu/list/tracks?genome=rn6

Request available tracks in the rn6 genome, hiding container information -

api.genome.ucsc.edu/list/tracks?genome=rn6;trackLeavesOnly=1

### Requesting track data with over one million (1M) items in output

Certain tracks may contain over 1M items. When these tracks are queried using the
/getData/track function, only the first million items are returned. The API assumes
this default value of 1M unless a different value (less than 1M) is specified with the
parameter maxItemsOutput.

One of these tracks is the knownGene track for hg19. Removing the maxItemsOutput
parameter from the following link will lead to a 384Mb download, and may cause certain
web browsers to time out.

Request items in knownGene track of hg19, remove maxItemsOutput parameter for 1M max return -

api.genome.ucsc.edu/getData/track?genome=hg19;track=knownGene;maxItemsOutput=5

There are different ways around this item limit, depending on how many items are in the track. For
the knownGene track, breaking it down to component chromosome queries using the chrom
parameter will suffice. In order to get a listing of the chrom names, and what chroms have data
for that track, the /list/chromosomes function can be used.

Request listing of chroms that have data for the knownGene track in hg19 -

api.genome.ucsc.edu/list/chromosomes?genome=hg19;track=knownGene

With the list of chrom names that have data, the /getData/track function can be used
again while specifying the chrom parameter. In the following example, chr1 is queried
and the itemsReturned field shows a total of 7967 items in the output, well below the
1M limit, meaning all data for chr1 has been extracted. This can then be repeated for all
chroms of interest.

Request items in knownGene track of hg19, only for chr1 -

api.genome.ucsc.edu/getData/track?genome=hg19;track=knownGene;chrom=chr1

For tracks that have additional items, such as SNP tracks, the query can be further broken
down using the additional start and end parameters.

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
