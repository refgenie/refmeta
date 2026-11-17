This directory contains download files of the Saccharomyces
cerevisiae genome sequence and associated annotations. The data
is based on sequence dated April 2011 in the Saccharomyces Genome
Database (http://www.yeastgenome.org/) and was obtained from the site
ftp://ftp.ncbi.nlm.nih.gov/genbank/genomes/Eukaryotes/fungi/Saccharomyces_cerevisiae/SacCer_Apr2011/

The S288C strain was used in this sequencing project.

Files included in this directory:

sacCer3.2bit - contains the complete S. cerevisiae/sacCer3 genome sequence
    in the 2bit file format.  No masking has been applied to these sequences.
    The utility program, twoBitToFa (available from the kent src tree),
    can be used to extract .fa file(s) from this file.  A pre-compiled version
    of the command line tool can be found at:
        http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/
    See also:
        http://genome.ucsc.edu/admin/git.html
	http://genome.ucsc.edu/admin/jk-install.html

chromAgp.tar.gz - contains the list of accession identifiers for
    each chromosome, unpacking to one file per chromosome.

chromFa.tar.gz - The assembly sequence in one file per chromosome.
    No masking has been applied to these sequences.

There are NO RepeatMasker .out files for this assembly.

chromTrf.tar.gz - Tandem Repeats Finder locations, filtered to keep repeats
    with period less than or equal to 12, and translated into UCSC's BED 5+
    format (one file per chromosome).

est.fa.gz - S. cerevisiae ESTs in GenBank. This sequence data is updated once a
    week via automatic GenBank updates.

md5sum.txt - checksums of files in this directory

mrna.fa.gz - S. cerevisiae mRNA from GenBank. This sequence data is updated
    once a week via automatic GenBank updates.


sacCer3.chrom.sizes - Two-column tab-separated text file containing assembly
    sequence names and sizes.

sacCer3.gc5Base.wigVarStep.gz - ascii data wiggle variable step values used
                           - to construct the GC Percent track
sacCer3.gc5Base.wig.gz - wiggle database table for the GC Percent track
                    - this is an older standard alternative to the current
                    - bigWig format of the track, sometimes usefull for analysis
sacCer3.gc5Base.wib    - binary data to correspond with the gc5Base.wig file
    see also:  http://genome.ucsc.edu/goldenPath/help/wiggle.html
    and  http://genomewiki.ucsc.edu/index.php/Using_hgWiggle_without_a_database
         for a discussion of how to use the wig.gz and .wib files for
         interaction with the GC percent data values

sacCer3.chromAlias.txt - sequence name alias file, one line
    for each sequence name.  First column is sequence name followed by
    tab separated alias names.

------------------------------------------------------------------
If you plan to download a large file or multiple files from this
directory, we recommend that you use ftp rather than downloading the
files via our website. To do so, ftp to hgdownload.cse.ucsc.edu
[username: anonymous, password: your email address], then cd to the
directory goldenPath/sacCer3/bigZips. To download multiple files, use
the "mget" command:

    mget <filename1> <filename2> ...
    - or -
    mget -a (to download all the files in the directory)

Alternate methods to ftp access.

Using an rsync command to download the entire directory:
    rsync -avzP rsync://hgdownload.cse.ucsc.edu/goldenPath/sacCer3/bigZips/ .
For a single file, e.g. chromFa.tar.gz
    rsync -avzP 
        rsync://hgdownload.cse.ucsc.edu/goldenPath/sacCer3/bigZips/chromFa.tar.gz .

Or with wget, all files:
    wget --timestamping 
        'ftp://hgdownload.cse.ucsc.edu/goldenPath/sacCer3/bigZips/*'
With wget, a single file:
    wget --timestamping 
        'ftp://hgdownload.cse.ucsc.edu/goldenPath/sacCer3/bigZips/chromFa.tar.gz' 
        -O chromFa.tar.gz

To unpack the *.tar.gz files:
    tar xvzf <file>.tar.gz
To uncompress the fa.gz files:
    gunzip <file>.fa.gz

---------------------------------------------------------------------
All the tables in this directory are freely available for public use.
---------------------------------------------------------------------
