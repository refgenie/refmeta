Assembly Hubs - genomewiki

-

-

-

-

-

# Assembly Hubs

				From genomewiki

Jump to navigationJump to search

## Contents

- 1 Preface

- 2 Overview

- 3 Web Server

- 4 Linking to your assembly hub

- 5 hub.txt

- 6 genomes.txt

- 7 2bit file

- 8 groups.txt

- 9 Building Tracks

- 9.1 Cytoband Track

- 10 Assembly Hub Resources

- 10.1 G-OnRamp

- 10.2 MakeHub

- 10.3 Example NCBI assembly hubs

- 10.3.1 Example loading African bush elephant assembly hub and looking at the related genomes.txt and trackDb.txt

- 11 Adding BLAT servers

- 11.1 Configuring assembly hubs to use a dedicated gfServer

- 11.2 Troubleshooting BLAT servers

- 11.2.1 Process check

- 11.2.2 Check for correct path/filename

- 11.2.3 Check "gfServer status" check

- 11.2.4 Testing with gfClient

- 11.3 Configuring assembly hubs to use a dynamic gfServer

- 11.3.1 Check gfServer status for dynamic servers

## Preface

Please note, if you are working with a genome that has already been submitted
to the NCBI Assembly system, it may
already be available in the UCSC Genome Browser

Please examine the GenArk Assembly Hub collection
to see if your genome of interest is already available.  In the case it can not
be found there, you can use the
UCSC Assembly Request page
to request a genome assembly be added to the UCSC Genome Browser.

## Overview

The Assembly Hub function allows you to display your novel genome sequence using the UCSC Genome Browser.

## Web Server

To display your novel genome sequence, use a web server at your institution (or free services like Cyverse, for usage behind a firewall you can also load them locally through GBiB) to supply your files to the UCSC Genome Browser. Note that hosting hub files on HTTP is highly recommended and much more efficient than FTP.  You then establish a hierarchy of directories and files to host your novel genome sequence.  For example:

```
myHub/ - directory to organize your files on this hub
     hub.txt – primary reference text file to define the hub, refers to:
     genomes.txt – definitions for each genome assembly on this hub
          newOrg1/ - directory of files for this specific genome assembly
               newOrg1.2bit – ‘2bit’ file constructed from your fasta sequence
               description.html – information about this assembly for users
               trackDb.txt – definitions for tracks on this genome assembly
               groups.txt – definitions for track groups on this assembly
               bigWig and bigBed files – data for tracks on this assembly
               external track hub data tracks can be displayed on this assembly

The URL to reference this hub would be: http://yourLab.yourInstitution.edu/myHub/hub.txt

Note: there is now a useOneFile on hub setting that allows the hub properties to be specified in a single file. More information about this setting can be found on the Genome Browser User Guide.

You can view a working example hierarchy of files at:
Plants

A smaller slice of this hub is represented in a Quick Start Guide to Assembly Hubs.

## Linking to your assembly hub

You can build direct links to the genome(s) in your assembly hub:

- The hub connect page

- http://genome.ucsc.edu/cgi-bin/hgHubConnect?hgHub_do_redirect=on&hgHubConnect.remakeTrackHub=on&hgHub_do_firstDb=1&hubUrl=http://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/hub.txt

- The genome gateway page

- http://genome.ucsc.edu/cgi-bin/hgGateway?genome=araTha1&hubUrl=http://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/hub.txt

- Directly to the genome browser

- http://genome.ucsc.edu/cgi-bin/hgTracks?genome=araTha1&hubUrl=http://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubAssembly/plantAraTha1/hub.txt

## hub.txt

The initial file hub.txt is the primary URL reference for your assembly hub.  The format of the file:

```
hub hubName
shortLabel genome
longLabel Comment describing this hub contents
genomesFile genomes.txt
email contactEmail@institution.edu
descriptionUrl aboutHub.html

The shortLabel is the name that will appear in the genome pull-down menu at the UCSC gateway page.  Example: Plants

The genomesFile is a reference to the next definition file in this chain that will describe the assemblies and tracks available
at this hub.  Typically genomes.txt is at the same directory level as this hub.txt, however it can also be a relative path
reference to a different directory level.

The email address provides users a contact point for queries related to this assembly hub.

The descriptionUrl provides a relative path or URL link to a webpage describing the overall hub.

## genomes.txt

The genomes.txt  file provides the references to the
genome assemblies and tracks available at this assembly hub.  The example file indicates the typical contents:

```
genome ricCom1
trackDb ricCom1/trackDb.txt
groups ricCom1/groups.txt
description July 2011 Castor bean
twoBitPath ricCom1/ricCom1.2bit
organism Ricinus communis
defaultPos EQ973772:1000000-2000000
orderKey 4800
scientificName Ricinus communis
htmlPath ricCom1/description.html
transBlat yourLab.yourInstitution.edu 17777
blat yourLab.yourInstitution.edu 17779
isPcr yourLab.yourInstitution.edu 17779

There can be multiple assembly definitions in this single file.  Separate these stanzas with blank lines.  The references to other files are relative path references.  In this example there is a sub-directory here called ricCom1 which contains the files for this specific assembly.

- The genome name is the equivalent to the UCSC database name.  The genome browser displays this database name in title pages in the genome browser.

- The trackDb refers to a file which defines the tracks to place on this genome assembly.  The format of this file is described in the Track Hub help reference documentation.

- The groups refers to a file which defines the track groups on this genome browser.  Track groups are the sections of related tracks grouped together under the primary genome browser graphics display image.

- The description will be displayed for user information on the gateway page and most title pages of this genome assembly browser.  It is the name displayed in the assembly pull-down menu on the browser gateway page.

- The twoBitPath refers to the .2bit file containing the sequence for this assembly.  Typically this file is constructed from the original fasta files for the sequence using the kent program faToTwoBit.  This line can also point to a URL, for example, if you are duplicating an existing Assembly Hub, you can use the original hub's 2bit file's URL location here.

- The organism string is displayed along with the description on most title pages in the genome browser.  Adjust your names in organism and description until they are appropriate.  This example is very close to what the genome browser normally displays.  This organism name is the name that appears in the genome pull-down menu on the browser gateway page.

- The defaultPos specifies the default position the genome browser will open when a user first views this assembly.  This is usually selected to highlight a popular gene or region of interest in the genome assembly.

- The orderKey is used with other genome definitions at this hub to order the pull-down menu ordering the genome pull-down menu.

- The htmlPath refers to an html file that is used on the gateway page to display information about the assembly.

- The transBlat refers to a gfServer that will allow searching amino acids more here.

- The blat refers to a gfServer that will allow blat more here.

- The isPcr refers to a gfServer that will allow PCR searches more here.

Note that it is strongly encouraged to give each of your genomes stanza's a line for defaultPos, scientificName, organism, description (along with other above settings) so that when your hub is attached it will load a specified default location and have text to be more easily searched from the Gateway page.

## 2bit file

The .2bit file is constructed from the fasta sequence for the assembly.  The kent source program faToTwoBit is used to construct this file.  Download the program from the downloads section of the Browser.
For example:

```
faToTwoBit ricCom1.fa ricCom1.2bit

Use the twoBitInfo to verify the sequences in this assembly and create a chrom.sizes file which is not used in the hub, but is useful in later processing to
construct the big* files:

```
twoBitInfo ricCom1.2bit stdout | sort -k2rn > ricCom1.chrom.sizes

The .2bit commands can function with the .2bit file at a URL:

```
twoBitInfo -udcDir=. http://genome-test.gi.ucsc.edu/~hiram/hubs/Plants/ricCom1/ricCom1.2bit stdout | sort -k2nr > ricCom1.chrom.sizes

Sequence can be extracted from the .2bit file with the twoBitToFa command, for example:

```
twoBitToFa -seq=chrCp -udcDir=. http://genome-test.gi.ucsc.edu/~hiram/hubs/Plants/ricCom1/ricCom1.2bit stdout > ricCom1.chrCp.fa

## groups.txt

The groups.txt file defines the grouping of track controls under the primary genome browser image display.  The example referenced here has the usual definitions as found in the UCSC Genome Browser.

Each group is defined, for example the Mapping group:

```
name map
label Mapping
priority 2
defaultIsClosed 0

- The name is used in the trackDb.txt track definition group, to assign a particular track to this group.

- The label is displayed on the genome browser as the title of this group of track controls

- The priority orders this track group with the other track groups

- The defaultIsClosed determines if this track group is expanded or closed by default.  Values to use are 0 or 1

## Building Tracks

Tracks are defined in the trackDb.txt where each stanza describes how tracks are displayed (shortLabel/longLabel/color/visibility) and other information such as what group the track should belong to (referencing the groups.txt) and if any additional html should display when one clicks into the track or a track item:

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

For more informations about the syntax of the trackDb.txt file, use UCSC's Hub Track Database Definition page

It helps to have a cluster super computer to process the genomes to construct tracks.  It can be done for small genomes
on single computers that have multiple cores.  The process for each track is unique.  Please note the continuing
document: Browser Track Construction for a discussion of constructing tracks for your assembly hub.

### Cytoband Track

Assembly hubs can have a Cytoband track that can allow for quicker navigation of individual chromosomes and display banding pattern information if known.

A quick version of the track can be built using the existing chrom.sizes files for your assembly
(the banding options include gneg, gpos25, gpos50, gpos75, gpos100, acen, gvar, or stalk).

cat araTha1.chrom.sizes | sort -k1,1 -k2,2n | awk '{print $1,0,$2,$1,"gneg"}' > cytoBandIdeo.bed

The resulting bed file can be turned into a big bed and given a .as file (example here)
to inform the browser it is not a normal bed.

 bedToBigBed -type=bed4 cytoBandIdeo.bed -as=cytoBand.as araTha1.chrom.sizes cytoBandIdeo.bigBed

In the trackDb, as long as the track is named cytoBandIdeo (track cytoBandIdeo
example)
it will load in the assembly hub.

## Assembly Hub Resources

There are resources for automatically building assembly hubs available from G-OnRamp and MakeHub.

There is also a collection of Example NCBI assembly hubs that are already working and can either be used or copied as
a template to build further hubs.

### G-OnRamp

G-OnRamp is a Galaxy workflow that turns a genome assembly and RNA-Seq data into a Genome Browser with multiple
evidence tracks. Because G-OnRamp is based on the Galaxy platform, developing some familiarity with the key concepts
and functionalities of Galaxy would be beneficial prior to using G-OnRamp.  Here is a link to their
instruction page that gives an overview of their process.

### MakeHub

MakeHub is a command line tool for the fully automatic generation of track data hubs for visualizing genomes with the UCSC genome browser.
https://github.com/Gaius-Augustus/MakeHub

### Example NCBI assembly hubs

There are a collection of assembly hubs built by an automatic script that can be viewed on our development server (links default to the genome-test site) or if the link to the hub.txt is copied and pasted, it can be manually changed to load on the public site.

The following table provides links pages to launch various assembly hubs grouped by species subset, where if you scroll down on the page you will find rows for each assembly hub (or groups of further assembly hubs for the bacteria page) allowing one to load individual assemblies by clicking the "common name" hyperlink such as "African bush elephant" on the Vertebrate Mammalian page (please note the statistics in this table below may change as more hubs are added in the future).

   | species
subset
   | number of
species
   | number of
assemblies
   | total contig
count
   | total nucleotide
count
   | average
contig size
   | average
assembly size

 | non-Mammalian other Vertebrate assembly hub
   | 156
   | 172
   | 18,548,615
   | 193,684,015,605
   | 10,441
   | 1,126,069,858

 |  Vertebrate Mammalian assembly hub
   | 118
   | 204
   | 30,643,657
   | 498,264,459,566
   | 16,259
   | 2,442,472,841

 | Plant assembly hub
   | 190
   | 269
   | 34,577,423
   | 145,341,422,954
   | 4,203
   | 540,302,687

 | Protozoa assembly hub
   | 282
   | 338
   | 3,939,128
   | 16,816,724,183
   | 4,269
   | 49,753,621

 | Invertebrates assembly hub
   | 392
   | 492
   | 32,264,511
   | 170,439,035,382
   | 5,282
   | 346,420,803

 | Fungi assembly hub
   | 1,106
   | 1,215
   | 4,143,097
   | 38,677,096,556
   | 9,335
   | 31,833,001

 | Archaea assembly  hub
   | 688
   | 742
   | 57,569
   | 2,010,246,046
   | 34,918
   | 2,709,226

 | Bacteria assembly hub
   | 34,005
   | 58,658
   | 8,397,216
   | 234,147,691,500
   | 27,883
   | 3,991,743

These assemblies use the NCBI accession naming patterns on chromosomes.  Please note his is a prototype work in progress. Not all assemblies are represented here yet. Prototype gene tracks from the NCBI gene predictions delivered with the assembly are available on a few assemblies. There are no blat servers on these assemblies. Users could copy the hub skeleton structure of a specific assembly to local systems and run a blat server at their location with their own assembly hub of that specific genome, brief instructions exist on each assembly gateway page under the "Download files for this assembly hub:" section.

#### Example loading African bush elephant assembly hub and looking at the related genomes.txt and trackDb.txt

Here are some quick steps to load an example hub from this collection, and an attempt to explain how to look at the files behind the hub.

- Click the above  Vertebrate Mammalian assembly hub link.

- Scroll down and find the "common name" column and click the hyperlink for "African bush elephant" after looking at the other information on that row.

- Note that you have arrived a gateway page that has "African bush elephant Genome Browser - GCA_000001905.1_Loxafr3.0 assembly" displayed, where you can see a "Download files for this assembly hub:"' section if you desired to access these specific files and notably a http://genome-test.gi.ucsc.edu/gbdb/hubs/genbank/vertebrate_mammalian/GCA_000001905.1_Loxafr3.0/ link.

- Click "Go" or the top "Genome Browser" blue bar menu to arrive at viewing this assembly hub (note this is on our genome-test site).

- To load this hub on our public site, at the earlier step you can copy the hyperlink for "African bush elephant" and paste it in a browser and change the very first "http://genome-test.gi.ucsc.edu/cgi-bin/..." to "http://genome.ucsc.edu/cgi-bin/..." instead.

Now to investigate the files behind the hub to understand the process involved.

- Click the     http://genome-test.gi.ucsc.edu/gbdb/hubs/genbank/vertebrate_mammalian/GCA_000001905.1_Loxafr3.0/ link found in the ""Download files for this assembly hub:" section on a loaded assembly hub's gateway page.

- Note the "GCA_000001905.1_Loxafr3.0.ncbi.2bit" file, this is the binary indexed remote file that is allowing the Browser to display this genome.

- Find the "GCA_000001905.1_Loxafr3.0.genomes.ncbi.txt" file and click the link to look at it.

- Review this genomes.txt file, which be used if copied in a new hub to show where the to find the above 2bit on the "twoBitPath" line and also defines where to find all track database to display data on this genome in the "trackDb " line (the real genomes.txt for this massive hub is up one directory as this hub has 204 assemblies -where you will find this stanza included). Note how the genomes.txt has the "organism" and "scientificName" lines that help annotate how to display this assembly hub, and "groups" line that points to a further file that helps define the grouping of tracks that will be fully described in the trackDb.txt.

- From the earlier link to all the files, click the GCA_000001905.1_Loxafr3.0.trackDb.ncib.txt

- Review this trackDb.txt file which defines the tracks to display on this hub, and also has "bigDataUrl" lines to tell the Browser where to find the data to display for each track, as well as other features such on some tracks as "searchIndex" and "searchTrix" lines to help support finding data in the hub and "url" and "urlLabel" lines on some tracks to help create links out on items in the hub to other external resources and "html" lines to a file that will have information to display about the data for users who click into tracks.

## Adding BLAT servers

BLAT servers (gfServer) are configured as either dedicated or dynamic servers.
Dedicated BLAT serves index a genome when started and remain running in memory to quickly respond to request.  Dynamic BLAT servers pre-index genomes to files
and are run on demand to handle a BLAT request and then exit.

Dedicated gfServer are easier to configure and faster to respond. However, the server
continually uses memory.  A dynamic gfServer is more appropriate with multiple
assemblies and infrequent use.  Their response time is usually acceptable; however, it varies with the speed of the disk containing the index.  With
repeated access, the operating system will cache the indexes in memory,
improving response time.

### Configuring assembly hubs to use a dedicated gfServer

By running your own BLAT server, you can add lines to the genomes.txt file of your assembly hub to enable the browser to access the server and activate blat searches.

Please see Running your own gfServer for details on installing and configuring both dedicated and dynamic gfServers.

- Next edit your genomes.txt stanza that references yourAssembly to have two lines to inform the browser of where the blat servers are located and what ports to use. See an example of commented out lines here. Please note the capital "B" in transBlat.

```
transBlat yourServer.yourInstitution.edu 17777
blat yourServer.yourInstitution.edu 17779
isPcr yourServer.yourInstitution.edu 17779

- You should now be able to load and perform blat and PCR operations on your assembly. For example, a URL such as the following would bring up the blat CGI and have your assembly listed at the bottom of the "Genome:" drop-down menu:  http://genome.ucsc.edu/cgi-bin/hgBlat?hubUrl=http://yourServer.yourInstitution.edu/myHub/hub.txt Also note the separate isPcr line provides the option to use a different gfServer than the blat host if desired.

- Some institutions have firewalls that will prevent the browser from sending multiple inquiries to your blat servers, in which case you may need to request your admins add this IP range as exceptions that are not limited: 128.114.119.*   That will cover the U.S. genome.ucsc.edu site.  In case you may wish the requests to work from our European Mirror genome-euro.ucsc.edu site, you would want to include 129.70.40.120 also to the exception list.

Please see more about configuring your blat gfServer here to replicate the UCSC Browser's settings, which will also have information about optimizing PCR results. The Source Downloads page offers access to utilities with pre-compiled binaries such as gfserver found in a blat/ directory for your machine type here and further blat documentation here, and the gfServer usage statement for further options.

Please also know you can set up gfservers on a GBiB and run it locally. Please see this GBiB assembly blat step-by-step set up page for details.

Note: You can stop your instance of gfServer with a command. For example:

```
gfServer stop localhost 17860

### Troubleshooting BLAT servers

You can see this error if you have the translatedBlat / nucleotideBlat port numbers the wrong way around:

```
   Expecting 6 words from server got 2

The following is an example of an error message

when attempting to run a DNA sequence query

via the web-based BLAT tool after loading a hub,

after starting a gfServer instance (from the same dir as the .2bit file).

For example, a command to start an instance of gfServer:

```
 gfServer start localhost 17779 -stepSize=5 contigsRenamed.2bit &

Example of a possible error message, from web-based BLAT

after attempting a web-based BLAT query:

```
Error in TCP non-blocking connect() 111 - Connection refused
Operation now in progress
Sorry, the BLAT/iPCR server seems to be down. Please try again later.

Check the following:

#### Process check

First, make sure your gfServer instance is running.

Type the following command to check for your running gfServer process:

```
 ps aux | grep gfServer

#### Check for correct path/filename

In your genomes.txt file, does your twoBitPath/filename match what you specified in your command to start gfServer?

In your genomes.txt file, is the location of the instance to your gfServer correct?
To check this, you can cd into the directory where you started your gfServer, then type the command:

```
 hostname -i

```
Your result should be an IP address, for example, "132.249.245.79".

Now you can test the connection to your port that you specified, with a simple telnet command.

Type in the following command: telnet yourIP yourPort. For example:

```
$ telnet 132.249.245.79 17777

The results should read, "Connected to 132.249.245.79".

Otherwise, if gfServer isn't running or if you typed the wrong location in your telnet command, telnet will say, "Connection refused."

In this example, check your genomes.txt file, and make sure your blat line reads, "blat 132.249.245.79 17777".

You may need to change your genomes.txt file from, for example, "blat localhost 17777" to "blat 132.249.245.79 17777" (use your specific IP/host name where gfServer is running).

#### Check "gfServer status" check

To request status from the gfServer process, run: gfServer status yourLocation yourPort.

For example:

```
$ gfServer status 132.249.245.79 17777

You should see output like this:

```
version 36x2
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
noSig 1
trimmed 0
warnings 0

#### Testing with gfClient

The best troubleshooting test is to take the webpage out of the equation, and use the command line utility, gfClient, to run the query on your instance of gfServer. If you can successfully connect gfClient to gfServer, you will know that your location and port specification are correct.

From the directory that holds your hub's .2bit file (should be the same directory where your instance of gfServer was launched), perform a query using gfClient:
You can type "gfClient" on your command line to see the usage statement.

Use the following command: gfClient yourLocation yourPort pathOf2bitFile yourFastaQuery.fa nameOfOutputFile.psl

FYI: For testing with gfClient, you only need the gfServer binary on your server, not blat.

For example:

```
gfClient localhost 17777 . query.fa gfOutput.psl

Note the " . " after the port, to specify that the query will use the .2bit file in the current directory.

After running this command, take a look at the gfOutput.psl file. If successful, you will see BLAT results.

Another example:

- Note: In the example below, "yourServer.yourInstitution.edu" is the name of their machine where you run the gfServer command.

From the test machine: Test the DNA alignment, where test.fa is some sequence to find:

```
gfClient yourServer.yourInstitution.edu 17779 `pwd` test.fa dnaTestOut.psl

From the test machine: Test the protein alignment, where proteinSequence.fa is the sequence to find:

```
gfClient -t=dnax -q=prot yourServer.yourInstitution.edu 17777 `pwd` proteinSequence.fa proteinOutput.psl

- NOTE: the yourAssembly.2bit file needs to be on this test machine also.

- The `pwd` says to find the yourAssembly.2bit file in this directory.

### Configuring assembly hubs to use a dynamic gfServer

A dynamic BLAT server is specified with the "dynamic" argument to
the blat, transBlat, isPcr definitions in the hub genomes.txt file, followed by
the gfServer root-relative path of the directory
containing the 2bit and gfidx files.

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

See Building gfServer indexes for instructions in building the index

For large hubs, it is possible to have more deeply nest directory, for
instance, the following NCBI convention:

```
   blat yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3
   transBlat yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3
   isPcr yourServer.yourInstitution.edu 4096 dynamic GCF/000/181/335/GCF_000181335.3

Which will reference these genome files and indexes:

```
    $rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.2bit
    $rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.untrans.gfidx
    $rootdir/GCF/000/181/335/GCF_000181335.3/GCF_000181335.3.trans.gfidx

#### Check gfServer status for dynamic servers

A query without specifying a genome is an "I am alive" check:

```
% gfServer status myserver 4040
version 37x1
serverType dynamic

Specifying a genome checks that is is valid and gives information on how to the index was built:

```
% gfServer -genome=mm10 -genomeDataDir=test/mm10 status myserver 4040
version 37x1
serverType dynamic
type nucleotide
tileSize 11
stepSize 5
minMatch 2

Using -trans checks the translated index:

```
% gfServer -genome=mm10 -genomeDataDir=test/mm10 -trans status myserver 4040
version 37x1
serverType dynamic
type translated
tileSize 4
stepSize 4
minMatch 3

Retrieved from "https://genomewiki.ucsc.edu/index.php?title=Assembly_Hubs&oldid=25992"

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

-  This page was last edited on 18 November 2022, at 23:20.

- Privacy policy
- About genomewiki
- Disclaimers
