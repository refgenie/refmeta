UCSC Genome Browser: Hub Basics

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

# Track Hub Basics

Track Hubs are web-accessible directories of genomic data that can be viewed on
the UCSC Genome Browser.  They allow you to display a set of custom annotations
on an assembly (or assemblies) of your choice and offer several advantages over
custom tracks, including more display configuration options, more track
organization options, more control over your data, and easier updates to that
data.

This page covers the basics of setting up your own hub:

- Creating your hub.txt

- Common track types and their configuration

- Grouping tracks

- Creating description pages

- Sharing and linking to your hub

As you build your hub, use the "Hub Development" tab on the Track Data Hub page to
check for errors or to disable file caching to
see your changes immediately, rather than after the 300ms refresh
rate.

## Example hub.txt

To begin, here is  an example hub.txt that has been created in a way
to make it easy to swap in your data URLs in place of our examples. It
indicates what settings are required and includes many optional settings that
can help elevate your tracks beyond the basics. Alongside these settings, it
includes short explanations of how those settings work and how to configure
them. There is also a version provided without the explanations.

- Minimal hub.txt

- Detailed hub.txt with setting explanations or
  without explanations

- Visualize this example hub.txt

## Creating your own hub.txt

The first step in creating a track hub is to create your hub.txt file. Download the
example hub.txt
and use this as a starting point, changing our default values to those for your hub.
These settings control how your hub is labeled in the interface
and contact information:

```
hub myExampleHub # a short, unique internal identifier for your hub, no spaces
# shortLabel and longLabel are how your hub is labeled in the Genome Browser interface
# shortLabels should be under 20 characters and longLabels under 70
shortLabel Example Hub
longLabel Example Hub for useOneFile option
useOneFile on
email genome-www@soe.ucsc.edu

genome hg38

If you have tracks across multiple assemblies,
see the full track hub documentation.

## Common Track Types

The most common track types are bigBed and bigWig. Compressed, binary versions of
the corresponding plain-text formats. Together, they should cover most
of what you might want to display in the Genome Browser, from transcription peaks to
RNA-seq signals.

## bigBed Tracks

You can use bigBed tracks to display discrete annotations, such as genes, transcription
start sites, or conserved genomic elements. The bigBed format builds off the
plain-text BED format and is thus flexible in terms of what fields are included.
Your file must start with a minimum of 3, and up to 12, standard fields, but
can also extend the format with any number of additional fields.

### Building a bigBed

- Download the bedToBigBed utility for your system type from
      our download
      server.

- Use bedToBigBed to build your bigBed:

```
bedToBigBed -sort in.bed chrom.sizes myBigBed.bb

- If your assembly is a UCSC-hosted assembly (e.g. hg38), chrom.sizes can
          be a URL (replace "genNom" with the assembly name (e.g. hg38)):
          http://hgdownload.gi.ucsc.edu/goldenPath/genNom/bigZips/genNom.chrom.sizes.
          If you're working with a
          GenArk assembly hub (e.g. GCF/GCA), then the chrom.sizes
          file can be found under the "Data file downloads" section on the
          assembly gateway page.

- If you have custom fields in your bed file, you will need to create a custom .as file.
          You can download the basic BED .as
          and modify this by adding new fields below those in your file.

- Put your bigBed file alongside your hub.txt in a web-accessible location,
      either through the 10GB of space we
      make available to users or through one of several
      other services.

- You will use the file name (e.g. "myBigBed.bb") with the bigDataUrl setting in your hub.txt.

### bigBed track hub configuration

Once you have built your bigBed files, it is time to create a stanza in your
hub.txt file for that track. Here is what the required settings discussed above
might look like for a basic bigBed track:

```
track bigBedRequiredSettings
shortLabel bigBed Required Settings
longLabel A bigBed Example with Required Settings
visibility pack
type bigBed 12 +
bigDataUrl gtexCaviar.chr7_155799529-155812871.bb

The type line consists of three parts:

- "bigBed" is the basic track type.

- "12" indicates how many standard BED fields are included in
  your file. You may need to change this to match the number of standard BED
  fields in your file.

- "+" tells the genome browser there are extra fields beyond the
  standard fields. If your file has no extra fields, replace this with a
  "." (e.g. type bigBed 12 .).

Here is a screenshot of what this basic bigBed track looks like displayed in the Genome Browser:

The bigBed format also offers a wide range of customization options for the
display, from decorators to highlights. Additionally, it offers extensive

filter controls,
searching options, and mouseover configurations. Our trackDb documentation contains a full listing of
settings available for the format.

Here is the bigBed configuration with some commonly used settings, including
filtering and mouseover configuration.

```
track bigBedCommonSettings
shortLabel bigBed Common Settings
longLabel A bigBed Example with Commonly Used Settings
visibility pack
type bigBed 12 +
bigDataUrl gtexCaviar.chr7_155799529-155812871.bb
filterLabel.cpp CPP (Causal Posterior Probability)
filter.cpp 0
filterLabel.geneName Gene Symbol
filterText.geneName *
mouseOver $name; CPP: $cpp

And here is what that track looks like in the Genome Browser:

These common settings added options to the track configuration pop-up:

## bigWig Tracks

You can use bigWig to tracks to display continuous
annotations, such as RNA-seq expression, conservation scores, or other
genome signal scores. You can build a bigWig using one of two plain-text formats:
wiggle or
bedGraph.

### Building a bigWig

- Download the wigToBigWig utility for your system type from
  our download
  server.

- Use this utility to build your bigWig:

```
wigToBigWig in.bedGraph chrom.sizes myBigWig.bw

- If your assembly is a UCSC-hosted assembly (e.g. hg38), chrom.sizes can
          be a URL (e.g. hg38):

          https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes.
          If you're working with a
          GenArk assembly hub (e.g. GCF/GCA), then the chrom.sizes
          file can be found under the "Data file downloads" section on the
          assembly gateway page.

- Put your bigWig file alongside your hub.txt in a web-accessible location,
      either through the 10GB of space we
      make available to users or through one of several
      other services.

- You will use the file name (e.g. "myBigWig.bw") with the bigDataUrl setting.

### bigWig track hub configuration

The basic trackDb configuration for a bigWig track is similar to a bigBed track, as
all tracks require the same basic settings (track, shortLabel, longLabel, type, bigDataUrl).
This is what the configuration for a bigWig track might look like (the example
hub.txt includes other useful settings):

```
track bigWigExample
shortLabel bigWig Example
longLabel A bigWig Example with Commonly Used Settings
visibility pack
type bigWig -20 10.003
bigDataUrl hg38.phyloP100way.chr7_155799529-155812871.bw
color 60,60,140

The type line consists of two parts:

- "bigWig" is the basic track type

- "-20 10.003" indicates the minimum and maximum of the data in the bigWig

Here is what this looks like visualized in the Genome Browser:

## Grouping tracks

Next, we'll provide a basic overview of how to group your tracks using
composite tracks and super tracks. This will allow you to pull similar data
together under a single container.

### Composite Tracks

Composite tracks can hold multiple tracks of the same type. For example, you
use a composite to group together a set of RNA-seq experiments, including
replicates.

Here's what the configuration might look like for a composite containing two
bigWig tracks. There are two key components of a composite: (1) the line
"compositeTrack on" in the parent track stanza, and (2) including "parent
compositeName" for each track that will be part of the composite.

```
track compositeExample
shortLabel Example Composite Track
longLabel Example composite track using bigWigs
visibility dense
type bigWig
compositeTrack on

    track compositeBigWig1
    bigDataUrl a.chr7_155799529-155812871.bw
    shortLabel bigWig #1
    longLabel bigWig in Composite Track Example #1
    parent compositeExample
    type bigWig 0 1
    color 255,0,0
    autoScale group
    visibility dense

    track compositeBigWig2
    bigDataUrl c.chr7_155799529-155812871.bw
    shortLabel bigWig #2
    longLabel bigWig in Composite Track Example #2
    parent compositeExample
    type bigWig 0 1
    color 0,255,0
    autoScale group
    visibility dense

This composite track configuration will display like so:

### Super Tracks

Super tracks are a more general type of container. They can contain tracks of
different types and even composites.

Configuring a basic super track is quite similar to composite tracks.
There are two key components of a composite: (1) the line
"superTrack on" in the parent track stanza, and (2) including "parent
superTrackName" for each track that will be part of the super track.

```
track superTrackExample
shortLabel Super Track Example
longLabel A super-track of related data of various types together: individual, multiWig, and composite
superTrack on show
html examplePage

    track superTrackbigBed
    parent superTrackExample
    bigDataUrl gtexCaviar.chr7_155799529-155812871.bb
    shortLabel ST bigBed example
    longLabel A super-track-contained bigBed
    type bigBed 12 +
    visibility squish
    priority 30

    track superTrackCompositeBigWig
    parent superTrackExample
    compositeTrack on
    shortLabel ST Composite bigWig
    longLabel A composite track in a super track grouping bigWigs
    visibility dense
    type bigWig
    priority 60

        track superTrackCompositeBigWig1
        bigDataUrl a.chr7_155799529-155812871.bw
        shortLabel ST bigWig composite #1
        longLabel A composite-contained bigWig in a super track example #1
        parent superTrackCompositeBigWig on
        type bigWig 0 1

        track superTrackCompositeBigWig2
        bigDataUrl c.chr7_155799529-155812871.bw
        shortLabel ST bigWig composite #2
        longLabel A composite-contained bigWig in a super track example #2
        parent superTrackCompositeBigWig on
        type bigWig 0 1

Loading the example hub with this super track configuration looks like this:

## Creating description pages

If you plan to share your track hub more widely, you will want to create a description page for your tracks.
A description page could contain a short description of what the data represents, how the data was generated,
a link to the associated paper, or a contact email for questions regarding the data. Multiple tracks can use
the same description page.

We provide an example description html that you can modify with
the details for your track. Once you've modified this example html for your
track, add an html to the corresponding track stanza:

```
track bigWigExample
shortLabel bigWig Example
longLabel A bigWig Example with Commonly Used Settings
type bigWig -20 10.003
bigDataUrl hg38.phyloP100way.chr7_155799529-155812871.bw
html bigWigDescription.html

## Sharing your hub

Once you have a functional hub that you would like to share with others, you
can create links that you give to others in two ways.

The first option is to create a session link,
which requires a Genome Browser account.
Load your hub, configure the genome browser as you'd like (e.g. position and
data tracks), select "My Sessions" under "My Data", and use the option to save
the current settings as a session. You will then be provided with a URL that
you can share with others.

The other option is to create a URL to the Genome Browser that loads your hub
on the assembly of interest. There are three URL parameters
you will want to use:

- db - UCSC assembly name (e.g. hg38)

- position - chromosome position to load

- hubUrl - URL to your hub

You will then append these to a genome browser URL. For example, this url loads the example hub:

```
https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=chr7:155799529-155812871&hubUrl=https://genome.ucsc.edu/goldenPath/help/examples/hubExamples/hubBasicSettings/hub.txt

If you feel that your hub would be of general use to the research community,
you can contact us about making it a public hub. Note that public hubs have to meet
more stringent requirements than the basics described here.
Check that your hub meets the public hub requirements
and then follow the directions on that page for submitting it to us for review.

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
