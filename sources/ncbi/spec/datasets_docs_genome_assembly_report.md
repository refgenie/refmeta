<!-- Converted to text by refmeta from https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/genome-assembly/ (retrieved 2026-11-17). Tags stripped; tables flattened to pipe rows. -->

# Genome assembly report
Genome record accession, organism, assembly statistics, and annotation info
Contents

# Genome assembly report
Genome record accession, organism, assembly statistics, and annotation info
The downloaded genome package contains a genome assembly
data report in JSON Lines
format in the file:

ncbi_dataset/data/assembly_data_report.jsonl

Each line of the genome assembly data report file is a hierarchical JSON
object that represents a single genome assembly record. The schema of the genome assembly record is defined in the tables
below where each row describes a single field in the report or a sub-structure, which is a collection of fields.
The outermost structure of the report is AssemblyDataReport.
Table fields that include a Table Field Mnemonic can be used with the
dataformat command-line tool's --fields option
Refer to the dataformat CLI tool reference to see how you can use this
tool to transform assembly data reports from JSON Lines to tabular formats.

### Sample report

```
{
  "assemblyInfo": {
    "assemblyLevel": "Chromosome",
    "assemblyName": "GRCh38.p14",
    "assemblyType": "haploid-with-alt-loci",
    "description": "Genome Reference Consortium Human Build 38 patch release 14 (GRCh38.p14)",
    "submitter": "Genome Reference Consortium",
    "refseqCategory": "reference genome",
    "synonym": "hg38",
    "bioprojectLineage": [
      {
        "bioprojects": [
          {
            "accession": "PRJNA31257",
            "title": "The Human Genome Project, currently maintained by the Genome Reference Consortium (GRC)"
          }
        ]
      }
    ],
    "blastUrl": "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastSearch&PROG_DEF=blastn&BLAST_SPEC=GDH_GCF_000001405.40",
    "comments": "Assembly Name: GRCh38.p14 Primary Assembly\nThe DNA sequence is composed of genomic sequence, primarily finished clones that were sequenced as part of the Human Genome Project. PCR products and WGS shotgun sequence have been added where necessary to fill gaps or correct errors. All such additions are manually curated by GRC staff. For more information see: https://genomereference.org",
    "assemblyStatus": "current",
    "pairedAssembly": {
      "accession": "GCA_000001405.29",
      "status": "current",
      "onlyGenbank": "4 unlocalized and unplaced scaffolds",
      "manualDiff": "RefSeq dropped two scaffolds that are predominantly rodent or bacterial in origin (KI270752.1/NT_187507.1 and KI270825.1/NT_187580.1), and dropped two unlocalized scaffolds that are now thought to be redundant with assembled chromosome sequence (KI270721.1/NT_187376.1 and KI270734.1/NT_187389.1)",
      "refseqGenbankAreDifferent": true,
      "differences": "Removed 4 unlocalized and unplaced scaffolds; RefSeq dropped two scaffolds that are predominantly rodent or bacterial in origin (KI270752.1/NT_187507.1 and KI270825.1/NT_187580.1), and dropped two unlocalized scaffolds that are now thought to be redundant with assembled chromosome sequence (KI270721.1/NT_187376.1 and KI270734.1/NT_187389.1)"
    },
    "bioprojectAccession": "PRJNA31257",
    "releaseDate": "2022-02-03"
  },
  "assemblyStats": {
    "totalNumberOfChromosomes": 24,
    "totalSequenceLength": "3099441038",
    "totalUngappedLength": "2948318359",
    "numberOfContigs": 996,
    "contigN50": 57879411,
    "contigL50": 18,
    "numberOfScaffolds": 470,
    "scaffoldN50": 67794873,
    "scaffoldL50": 16,
    "gapsBetweenScaffoldsCount": 349,
    "numberOfComponentSequences": 35611,
    "gcCount": "1374283647",
    "gcPercent": 41,
    "numberOfOrganelles": 1,
    "atgcCount": "3357952943"
  },
  "organelleInfo": [
    {
      "description": "Mitochondrion",
      "totalSeqLength": "16569",
      "submitter": "Genome Reference Consortium"
    }
  ],
  "annotationInfo": {
    "name": "GCF_000001405.40-RS_2025_08",
    "provider": "NCBI RefSeq",
    "releaseDate": "2025-08-01",
    "reportUrl": "https://www.ncbi.nlm.nih.gov/genome/annotation_euk/Homo_sapiens/GCF_000001405.40-RS_2025_08.html",
    "stats": {
      "geneCounts": {
        "total": 59792,
        "proteinCoding": 20076,
        "nonCoding": 22235,
        "pseudogene": 17070,
        "other": 411
      }
    },
    "busco": {
      "buscoLineage": "primates_odb10",
      "buscoVer": "5.7.1",
      "complete": 0.98867923,
      "singleCopy": 0.979317844,
      "duplicated": 0.00936139375,
      "fragmented": 0.00464441208,
      "missing": 0.00667634234,
      "totalCount": "13780"
    },
    "method": "Best-placed RefSeq; Gnomon; RefSeqFE; cmsearch; tRNAscan-SE",
    "pipeline": "NCBI Eukaryotic Genome Annotation Pipeline (EGAP)",
    "softwareVersion": "10.4",
    "status": "Updated annotation"
  },
  "currentAccession": "GCF_000001405.40",
  "accession": "GCF_000001405.40",
  "pairedAccession": "GCA_000001405.29",
  "sourceDatabase": "SOURCE_DATABASE_REFSEQ",
  "organism": {
    "taxId": 9606,
    "commonName": "human",
    "organismName": "Homo sapiens"
  }
}
```

### AssemblyDataReport Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| accession| accession| Assembly Accession| string| The GenColl assembly accession| GCF_000001405.40
 |
| currentAccession| current-accession| Current Accession| string| The latest GenColl assembly accession for this revision chain| GCF_000001405.40
 |
| sourceDatabase| source_database| Source Database| SourceDatabase| Source of the accession. The paired accession, if it exists, is from the other database.| REFSEQ
GENBANK
 |
| organism| organism-| Organism| Organism| |  |
| assemblyInfo| assminfo-| Assembly| AssemblyInfo| Metadata for the genome assembly submission|  |
| assemblyStats| assmstats-| Assembly Stats| AssemblyStats| Global statistics for the genome assembly|  |
| organelleInfo repeated| organelle-| Organelle| OrganelleInfo| Metadata for all associated organelle genomes|  |
| additionalSubmitters repeated| | | AdditionalSubmitter| Submitter data for all associated extra sequences|  |
| annotationInfo| annotinfo-| Annotation| AnnotationInfo| Metadata and statistics for the genome assembly annotation, when available|  |
| wgsInfo| wgs-| WGS| WGSInfo| Metadata pertaining to the Whole Genome Shotgun (WGS) record for the genome assemblies that are complete genomes. Those that are clone-based do not have WGS-master records.|  |
| typeMaterial| type_material-| Type Material| TypeMaterial| |  |
| checkmInfo| checkm-| CheckM| CheckM| Metadata on the completeness and contamination of this assembly|  |
| averageNucleotideIdentity| ani-| ANI| AverageNucleotideIdentity| |  |

### ANIMatch Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| assembly| assembly| Assembly| string| Accession of the submitted organism best match type-strain assembly or best match type-strain assembly| GCA_010191885.1
 |
| organismName| organism| Organism| string| Taxonomic name of the submitted organism or best match type-strain organism| Salmonella enterica subsp. enterica serovar Typhimurium
 |
| category| category| Type Category| ANITypeCategory| Type category| Type material
 |
| ani| ani| ANI| float| Percent average nucleotide identity| 98.5
 |
| assemblyCoverage| assembly_coverage| Assembly Coverage| float| Percent coverage of the query assembly by the submitted organism or best match type assembly| 90.75
 |
| typeAssemblyCoverage| type_assembly_coverage| Type Assembly Coverage| float| Percent coverage of the submitted organism or best match type assembly by the query assembly| 89.60
 |

### AdditionalSubmitter Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| genbankAccession| coming soon| coming soon| string| genbank accession of extra sequence|  |
| refseqAccession| coming soon| coming soon| string| genbank accession of extra sequence|  |
| chrName| coming soon| coming soon| string| chromosome name|  |
| moleculeType| coming soon| coming soon| string| molecule type|  |
| submitter| coming soon| coming soon| string| Name of submitter|  |
| bioprojectAccession| coming soon| coming soon| string| Bioproject accession|  |

### AnnotationInfo Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| name| name| Name| string| Annotation name|  |
| provider| provider| Provider| string| Source of the annotation|  |
| releaseDate| release-date| Release Date| string| Annotation release date|  |
| reportUrl| report-url| Report URL| string| Annotation report web address|  |
| stats| featcount-| Count| FeatureCounts| |  |
| busco| busco-| BUSCO| BuscoStat| |  |
| method| method| Method| string| Software tools used to calculate annotation|  |
| pipeline| pipeline| Pipeline| string| NCBI annotation pipeline used to calculate annotation|  |
| softwareVersion| software-version| Software Version| string| NCBI annotation pipeline software version|  |
| status| status| Status| string| Type of annotation|  |

### AssemblyInfo Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| assemblyLevel| level| Level| string| The level at which a genome has been assembled| chromosome
scaffold
contig
 |
| assemblyStatus| status| Status| AssemblyStatus| The GenColl assembly status| current
 |
| pairedAssembly| paired-assm-| Paired Assembly| PairedAssembly| Metadata from the GenBank or RefSeq assembly paired with this one|  |
| assemblyName| name| Name| string| The assembly submitter's name for the genome assembly, when provided. Otherwise, a default name in the form ASM#####v# is assigned| GRCh38.p14
ASM985889v3
 |
| assemblyLongName| long-name| LongName| string| | Genome Reference Consortium Human Build 38 patch release 14 (GRCh38.p14)
 |
| assemblyType| type| Type| string| Chromosome content of the submitted genome assembly| haploid-with-alt-loci
haploid
 |
| bioprojectLineage repeated| bioproject-| BioProject| BioProjectLineage| The lineage of BioProject accessions. The specific BioProject that produced the sequences in the genome assembly is listed first, followed in order by its antecedents.|  |
| bioprojectAccession| bioproject| BioProject Accession| string| |  |
| releaseDate| release-date| Release Date| string| Date the assembly was made available by NCBI. This field is not returned by versions of the datasets Command Line Interface (CLI) program < 15.|  |
| description| description| Description| string| Long description for this genome|  |
| submitter| submitter| Submitter| string| The submitting consortium or organization. Full submitter information is available in the BioProject|  |
| refseqCategory| refseq-category| Refseq Category| string| The RefSeq Category, if present, indicates whether the assembly is a reference genome| reference genome
 |
| synonym| synonym| Synonym| string| Genome name ascribed to this assembly by the UC Santa Cruz genome browser| hg38
 |
| linkedAssemblies repeated| linked-assm-| Linked Assembly| LinkedAssembly| Genome assemblies derived from the same diploid individual|  |
| atypical| atypical| Atypical| AtypicalInfo| Information on atypical genomes - genomes that have assembly issues or are otherwise atypical|  |
| genomeNotes repeated| notes| Notes| string| All the RefSeq messages associated with this assembly|  |
| sequencingTech| sequencing-tech| Sequencing Tech| string| Sequencing technology used to sequence this genome|  |
| assemblyMethod| assembly-method| Assembly Method| string| Genome assembly method|  |
| groupingMethod| grouping-method| Grouping Method| string| Version of the NCBI Virus segmented genome grouping pipeline, which groups nucleotide sequences for segmented viruses into a single genome assembly. For more information, see the NCBI Virus Help Documentation| NCBI Virus Segmented Genome Grouping Pipeline VG-AUTO-v2.0
 |
| biosample| biosample-| BioSample| BioSampleDescriptor| NCBI BioSample from which the sequences in the genome assembly were obtained.|  |
| blastUrl| blast-url| Blast URL| string| URL to blast page for this assembly|  |
| comments| coming soon| coming soon| string| Freeform comments|  |
| suppressionReason| suppression-reason| Suppression Reason| string| The reason for the assembly is suppressed, for suppressed assemblies|  |
| diploidRole| diploid-role| Diploid Role| LinkedAssemblyType| |  |

### AssemblyStats Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| totalNumberOfChromosomes| total-number-of-chromosomes| Total Number of Chromosomes| uint32| Count of nuclear chromosomes, organelles and plasmids in a submitted genome assembly|  |
| totalSequenceLength| total-sequence-len| Total Sequence Length| uint64| Total sequence length of the nuclear genome including unplaced and unlocalized sequences|  |
| totalUngappedLength| total-ungapped-len| Total Ungapped Length| uint64| Total length of all top-level sequences ignoring gaps. Any stretch of 10 or more Ns in a sequence is treated like a gap|  |
| numberOfContigs| number-of-contigs| Number of Contigs| uint32| Total number of sequence contigs in the assembly. Any stretch of 10 or more Ns in a sequence is treated as a gap between two contigs in a scaffold when counting contigs and calculating contig N50 & L50 values|  |
| contigN50| contig-n50| Contig N50| uint32| Length such that sequence contigs of this length or longer include half the bases of the assembly|  |
| contigL50| contig-l50| Contig L50| uint32| Number of sequence contigs that are longer than, or equal to, the N50 length and therefore include half the bases of the assembly|  |
| numberOfScaffolds| number-of-scaffolds| Number of Scaffolds| uint32| Number of scaffolds including placed, unlocalized, unplaced, alternate loci and patch scaffolds|  |
| scaffoldN50| scaffold-n50| Scaffold N50| uint32| Length such that scaffolds of this length or longer include half the bases of the assembly|  |
| scaffoldL50| scaffold-l50| Scaffold L50| uint32| Number of scaffolds that are longer than, or equal to, the N50 length and therefore include half the bases of the assembly|  |
| gapsBetweenScaffoldsCount| gaps-between-scaffolds-count| Gaps Between Scaffolds Count| uint32| Number of unspanned gaps between scaffolds|  |
| numberOfComponentSequences| number-of-component-sequences| Number of Component Sequences| uint32| Total number of component WGS or clone sequences in the assembly|  |
| atgcCount| atgc-count| ATGC Count| uint64| The number of AT and GC base-pairs in the assembly|  |
| gcPercent| gc-percent| GC Percent| float| The percentage of GC base-pairs in the assembly, rounded to the nearest 0.5%|  |
| genomeCoverage| genome-coverage| Genome Coverage| string| Genome assembly coverage|  |
| numberOfOrganelles| number-of-organelles| Number of Organelles| uint32| number of organelles|  |

### AtypicalInfo Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| isAtypical| is-atypical| Is Atypical| bool| If true there are assembly issues or the assembly is in some way non-standard|  |
| warnings repeated| warnings| Warnings| string| The reasons that the assembly is considered atypical|  |

### AverageNucleotideIdentity Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| taxonomyCheckStatus| check-status| Check status| AverageNucleotideIdentity.TaxonomyCheckStatus| Indicates whether the ANI result is consistent with the submitted organism| ok
failed
inconclusive
 |
| matchStatus| best-match-status| Best match status| AverageNucleotideIdentity.MatchStatus| Indicates the specific type of ANI result that supports the Taxonomy check status| derived-species-match
 |
| submittedOrganism| submitted-organism| Submitted organism| string| Taxonomic name of the query assembly| Salmonella enterica subsp. enterica serovar Tennessee str. CDC07-0191
 |
| submittedSpecies| submitted-species| Submitted species| string| Species name of the query assembly| Salmonella enterica
 |
| category| category| Category| ANITypeCategory| Category of type or validated assembly| syntype
 |
| submittedAniMatch| submitted-ani-match-| Declared ANI match| ANIMatch| |  |
| bestAniMatch| best-ani-match-| Best ANI match| ANIMatch| |  |
| comment| comment| Comment| string| Additional information about the ANI result|  |

### BioProject Structure
A BioProject is a collection of biological data related to a
single initiative, originating from a single organization or from a
consortium. A BioProject record provides users a single place to find links
to the diverse data types generated for that project. The record can be
retrieved from NCBI BioProject
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| accession| accession| Accession| string| BioProject accession| PRJEB35387
 |
| title| title| Title| string| Title of the BioProject provided by the submitter| Sciurus carolinensis (grey squirrel) genome assembly, mSciCar1
 |
| parentAccessions repeated| parent-accessions| Parent Accessions| string| BioProject accession containing multiple children BioProjects| ["PRJNA489243","PRJEB33226","PRJEB40665"]
 |

### BioProjectLineage Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| bioprojects repeated| lineage-| Lineage| BioProject| A BioProject is a collection of biological data related to a single initiative, originating from a single organization or from a consortium|  |

### BioSampleAttribute Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| name| name| Name| string| |  |
| value| value| Value| string| |  |

### BioSampleContact Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| lab| lab| Lab| string| Submitter lab name.|  |

### BioSampleDescription Structure
Description of the BioSample object
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| title| title| Title| string| |  |
| organism| organism-| Organism| Organism| |  |
| comment| comment| Comment| string| |  |

### BioSampleDescriptor Structure
This describes BioSample data that is included in the genome assembly data report
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| accession| accession| Accession| string| | SAMN20055006
 |
| lastUpdated| last-updated| Last updated| string| |  |
| publicationDate| publication-date| Publication date| string| |  |
| submissionDate| submission-date| Submission date| string| |  |
| sampleIds repeated| ids-| Sample Identifiers| BioSampleId| |  |
| description| description-| Description| BioSampleDescription| |  |
| owner| owner-| Owner| BioSampleOwner| |  |
| models repeated| models| Models| string| |  |
| bioprojects repeated| bioproject-| BioProject| BioProject| |  |
| package| package| Package| string| | MIGS.ba.air.4.0
 |
| attributes repeated| attribute-| Attribute| BioSampleAttribute| |  |
| status| status-| Status| BioSampleStatus| |  |
| age| age| Age| string| Age at the time of sampling|  |
| biomaterialProvider| biomaterial-provider| Biomaterial provider| string| Name and address of the lab or PI|  |
| breed| breed| Breed| string| Breed name|  |
| collectedBy| collected-by| Collected by| string| Name of persons or institute who collected the sample|  |
| collectionDate| collection-date| Collection date| string| Date on which the sample was collected|  |
| cultivar| cultivar| Cultivar| string| Cultivated variety of plant|  |
| devStage| development-stage| Development stage| string| Developmental stage at the time of sampling|  |
| ecotype| ecotype| Ecotype| string| Population within a given species adapted to a local habitat|  |
| geoLocName| geo-loc-name| Geographic location| string| Geographical origin of the sample|  |
| host| host| Host| string| The natural host to the organism|  |
| hostDisease| host-disease| Host disease| string| Name of relevant disease|  |
| identifiedBy| identified-by| Identified by| string| Name of the taxonomist who identified the specimen|  |
| ifsacCategory| ifsac-category| IFSAC category| string| Interagency Food Safety Analytics Collaboration (IFSAC) category|  |
| isolate| isolate| Isolate| string| Description of the specific individual from which the sample was derived|  |
| isolateNameAlias| isolate-name-alias| Isolate name alias| string| Other IDs associated with this isolate|  |
| isolationSource| isolation-source| Isolation source| string| Source of the sample|  |
| latLon| lat-lon| Latitude and Longitude| string| Geographic coordinates of the location where the sample was collected|  |
| projectName| project-name| Project name| string| Name of the project|  |
| sampleName| sample-name| Sample name| string| Sample name in source database|  |
| serovar| serovar| Serovar| string| Taxonomic name below subspecies. Same as serotype.|  |
| sex| sex| Sex| string| Physical sex of sampled organism|  |
| sourceType| source-type| Source type| string| Controlled vocabulary describing the isolation source|  |
| strain| strain| Strain| string| Strain name|  |
| subSpecies| sub-species| Sub-species| string| Sub-species taxonomic name|  |
| tissue| tissue| Tissue| string| Type of tissue from which the sample was derived|  |
| serotype| serotype| Serotype| string| Taxonomic name below subspecies. Same as serovar|  |

### BioSampleId Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| db| db| Database| string| | Wellcome Sanger Institute
 |
| label| label| Label| string| | Sample name
 |
| value| value| Value| string| | COG-UK/ALDP-17A6A8C
 |

### BioSampleOwner Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| name| name| Name| string| |  |
| contacts repeated| contact-| Contact| BioSampleContact| |  |

### BioSampleStatus Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| status| status| Status| string| | live
 |
| when| when| When| string| |  |

### BuscoStat Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| buscoLineage| lineage| Lineage| string| BUSCO Lineage|  |
| buscoVer| version| Version| string| BUSCO Version|  |
| complete| complete| Complete| float| BUSCO score: Complete|  |
| singleCopy| singlecopy| Single Copy| float| BUSCO score: Single Copy|  |
| duplicated| duplicated| Duplicated| float| BUSCO score: Duplicated|  |
| fragmented| fragmented| Fragmented| float| BUSCO score: Fragmented|  |
| missing| missing| Missing| float| BUSCO score: Missing|  |
| totalCount| totalcount| Total Count| uint64| BUSCO score: Total Count|  |

### CheckM Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| checkmMarkerSet| marker-set| marker set| string| What taxonomic group is used as the basis for comparison with this assembly with regards to checkM values| Mycobacterium avium
 |
| checkmSpeciesTaxId| species-tax-id| species tax id| uint32| The species-level taxid for this assemblies checkM dataset| 1764
 |
| checkmMarkerSetRank| marker-set-rank| marker set rank| string| CheckM taxonomic rank of checkm_marker_set| species
genus
 |
| checkmVersion| version| version| string| CheckM software version| v1.2.0
 |
| completeness| completeness| completeness| float| What percent complete is this assembly| 86.83
 |
| contamination| contamination| contamination| float| What is the contamination percentage for this assembly| 5.18
 |
| completenessPercentile| completeness-percentile| completeness percentile| float| The percent of assemblies under the taxonomic grouping 'checkm_marker_set' that this assembly is as-or-more complete than.| 79
 |

### FeatureCounts Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| geneCounts| gene-| Gene| GeneCounts| Counts of gene types|  |

### GeneCounts Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| total| total| Total| uint32| Total number of annotated genes|  |
| proteinCoding| protein-coding| Protein-coding| uint32| Count of annotated genes that encode a protein|  |
| nonCoding| non-coding| Non-coding| uint32| Count of transcribed non-coding genes (e.g. lncRNAs, miRNAs, rRNAs, etc...) excludes transcribed pseudogenes|  |
| pseudogene| pseudogene| Pseudogene| uint32| Count of transcribed and non-transcribed pseudogenes|  |
| other| other| Other| uint32| Count of genic region GeneIDs and non-genic regulatory GeneIDs|  |

### InfraspecificNames Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| breed| breed| Breed| string| A homogenous group of animals within a domesticated species| Hereford
boxer
 |
| cultivar| cultivar| Cultivar| string| A variety of plant within a species produced and maintained by cultivation| B73
 |
| ecotype| ecotype| Ecotype| string| A population or subspecies occupying a distinct habitat| Alpine
 |
| isolate| isolate| Isolate| string| The individual isolate from which the sequences in the genome assembly were derived| L1 Dominette 01449 registration number 42190680
Pmale09
 |
| sex| sex| Sex| string| Physical sex of sampled organism| female
 |
| strain| strain| Strain| string| A genetic variant, subtype or culture within a species| SE11
 |

### LinkedAssembly Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| linkedAssembly| accession| Accession| string| The linked assembly accession| GCA_000212995.1
 |
| assemblyType| type| Type| LinkedAssemblyType| The linked assembly type|  |

### OrganelleInfo Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| infraspecificName| infraspecific-name| Infraspecific Name| string| The strain, breed, cultivar or ecotype of the organism from which the sequences in the assembly were derived|  |
| bioproject repeated| bioproject-accessions| BioProject Accessions| string| The associated BioProject accession, when available|  |
| description| description| Description| string| Long description of the organelle genome|  |
| totalSeqLength| total-seq-length| Total Seq Length| uint64| Sequence length of the organelle genome|  |
| submitter| submitter| Submitter| string| Name of submitter|  |

### PairedAssembly Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| accession| accession| Accession| string| The GenColl assembly accession of the GenBank or RefSeq assembly paired with this one| GCF_000001405.40
 |
| status| status| Status| AssemblyStatus| GenColl Assembly status from paired record| current
 |
| annotationName| name| Name| string| Annotation name from paired record|  |
| onlyGenbank| only-genbank| Only Genbank| string| Sequences that are only included in the GenBank assembly|  |
| onlyRefseq| only-refseq| Only RefSeq| string| Sequences that are only included in the RefSeq assembly|  |
| changed| changed| Changed| string| Sequences present on both the GenBank and the RefSeq assemblies that have been changed, e.g., contaminated sequence in the GenBank assembly has been replaced with a gap|  |
| manualDiff| manual-diff| Manual Diff| string| Manually curated description of differences between the GenBank and RefSeq assemblies|  |
| refseqGenbankAreDifferent| refseq-genbank-are-different| RefSeq GenBank Are Different| bool| boolean indication on whether there are any differences between the GenBank and RefSeq assemblies|  |
| differences| diff| Differences| string| Concatenation of all differences between the GenBank and RefSeq assemblies, including manually curated description and other fields|  |

### TypeMaterial Structure
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| typeLabel| label| Label| string| |  |
| typeDisplayText| display_text| Display Text| string| |  |

### WGSInfo Structure
Whole Genome Shotgun (WGS) projects are genome assemblies of incomplete genomes or incomplete chromosomes of prokaryotes
or eukaryotes that are generally being sequenced by a whole genome shotgun strategy.
| | Field| Table Field Mnemonic| Table Column Name| Type| Description| Examples |
| wgsProjectAccession| project-accession| project accession| string| WGS project accession| AAEX03
CABHLF01
 |
| masterWgsUrl| url| URL| string| WGS project Nucleotide web address| https://www.ncbi.nlm.nih.gov/nuccore/AAEX00000000.3
 |
| wgsContigsUrl| contigs-url| contigs URL| string| WGS project Sequence set browser web address| https://www.ncbi.nlm.nih.gov/Traces/wgs/AAEX03
 |

### ANITypeCategory Enumeration
| | Name| Number| Description |
| ANI_CATEGORY_UNKNOWN| 0|  |
| claderef| 1|  |
| category_na| 2|  |
| neotype| 3|  |
| no_type| 4|  |
| pathovar| 5|  |
| reftype| 6|  |
| suspected_type| 7|  |
| synonym| 8|  |
| syntype| 8|  |
| type| 9|  |

### AssemblyStatus Enumeration
| | Name| Number| Description |
| ASSEMBLY_STATUS_UNKNOWN| 0|  |
| current| 1|  |
| previous| 2|  |
| suppressed| 3|  |
| retired| 4| This is deprecated - should no longer be seen in the data |

### AverageNucleotideIdentity.MatchStatus Enumeration
| | Name| Number| Description |
| BEST_MATCH_STATUS_UNKNOWN| 0|  |
| approved_mismatch| 1|  |
| below_threshold_match| 2|  |
| below_threshold_mismatch| 3|  |
| best_match_status| 4|  |
| derived_species_match| 5|  |
| genus_match| 6|  |
| low_coverage| 7|  |
| mismatch| 8|  |
| status_na| 9|  |
| species_match| 10|  |
| subspecies_match| 11|  |
| synonym_match| 12|  |
| lineage_match| 13|  |
| below_threshold_lineage_match| 14|  |

### AverageNucleotideIdentity.TaxonomyCheckStatus Enumeration
| | Name| Number| Description |
| TAXONOMY_CHECK_STATUS_UNKNOWN| 0|  |
| OK| 1|  |
| Failed| 2|  |
| Inconclusive| 3|  |

### LinkedAssemblyType Enumeration
| | Name| Number| Description |
| LINKED_ASSEMBLY_TYPE_UNKNOWN| 0|  |
| alternate_pseudohaplotype_of_diploid| 1| SEQUI-5245 |
| principal_pseudohaplotype_of_diploid| 2|  |
| maternal_haplotype_of_diploid| 3|  |
| paternal_haplotype_of_diploid| 4|  |
| haplotype_1| 6|  |
| haplotype_2| 7|  |
| haplotype_3| 8|  |
| haplotype_4| 9|  |
| haploid| 10| Catch all for any value that is not explicitly listed above |

### SourceDatabase Enumeration
| | Name| Number| Description |
| SOURCE_DATABASE_UNSPECIFIED| 0|  |
| SOURCE_DATABASE_GENBANK| 1|  |
| SOURCE_DATABASE_REFSEQ| 2|  |

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
