<!-- Converted to text by refmeta from https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/dataformat/tsv/dataformat_tsv_genome/ (retrieved 2026-11-17). Tags stripped; tables flattened to pipe rows. -->

# genome
Convert an NCBI Datasets Genome Assembly Data Report (JSONL) to a tabular (TSV) format
Contents

# genome
Convert an NCBI Datasets Genome Assembly Data Report (JSONL) to a tabular (TSV) format

### Name
dataformat tsv genome - Convert an NCBI Datasets Genome Assembly Data Report (JSONL) to a tabular (TSV) format

### Synopsis
dataformat tsv genome [flags]

### Description
Convert an NCBI Datasets Genome Assembly Data Report (JSONL) to a tabular (TSV) format.
For more details on how to generate tables and field descriptions, see https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/using-dataformat/

### Examples

```
  dataformat tsv genome --inputfile human/ncbi_dataset/data/assembly_data_report.jsonl --fields accession,'organism*','*busco*'
  dataformat tsv genome --package human.zip

```

### Options

```
      --elide-header       Do not output header
      --fields strings     Comma-separated list of field names that supports wildcards (*). Names with wildcards must be quoted, for example: accession,'organism*','*busco*'
      --force              Force dataformat to run without type check prompt
  -h, --help               help for genome
      --inputfile string   Input file (default "/dev/stdin")
      --package string     Data package (zip archive), inputfile parameter is relative to the root path inside the archive

```

### Fields
| | Mnemonic| Name |
| accession| Assembly Accession |
| ani-best-ani-match-ani| ANI Best ANI match ANI |
| ani-best-ani-match-assembly| ANI Best ANI match Assembly |
| ani-best-ani-match-assembly_coverage| ANI Best ANI match Assembly Coverage |
| ani-best-ani-match-category| ANI Best ANI match Type Category |
| ani-best-ani-match-organism| ANI Best ANI match Organism |
| ani-best-ani-match-type_assembly_coverage| ANI Best ANI match Type Assembly Coverage |
| ani-best-match-status| ANI Best match status |
| ani-category| ANI Category |
| ani-check-status| ANI Check status |
| ani-comment| ANI Comment |
| ani-submitted-ani-match-ani| ANI Declared ANI match ANI |
| ani-submitted-ani-match-assembly| ANI Declared ANI match Assembly |
| ani-submitted-ani-match-assembly_coverage| ANI Declared ANI match Assembly Coverage |
| ani-submitted-ani-match-category| ANI Declared ANI match Type Category |
| ani-submitted-ani-match-organism| ANI Declared ANI match Organism |
| ani-submitted-ani-match-type_assembly_coverage| ANI Declared ANI match Type Assembly Coverage |
| ani-submitted-organism| ANI Submitted organism |
| ani-submitted-species| ANI Submitted species |
| annotinfo-busco-complete| Annotation BUSCO Complete |
| annotinfo-busco-duplicated| Annotation BUSCO Duplicated |
| annotinfo-busco-fragmented| Annotation BUSCO Fragmented |
| annotinfo-busco-lineage| Annotation BUSCO Lineage |
| annotinfo-busco-missing| Annotation BUSCO Missing |
| annotinfo-busco-singlecopy| Annotation BUSCO Single Copy |
| annotinfo-busco-totalcount| Annotation BUSCO Total Count |
| annotinfo-busco-version| Annotation BUSCO Version |
| annotinfo-featcount-gene-non-coding| Annotation Count Gene Non-coding |
| annotinfo-featcount-gene-other| Annotation Count Gene Other |
| annotinfo-featcount-gene-protein-coding| Annotation Count Gene Protein-coding |
| annotinfo-featcount-gene-pseudogene| Annotation Count Gene Pseudogene |
| annotinfo-featcount-gene-total| Annotation Count Gene Total |
| annotinfo-method| Annotation Method |
| annotinfo-name| Annotation Name |
| annotinfo-pipeline| Annotation Pipeline |
| annotinfo-provider| Annotation Provider |
| annotinfo-release-date| Annotation Release Date |
| annotinfo-report-url| Annotation Report URL |
| annotinfo-software-version| Annotation Software Version |
| annotinfo-status| Annotation Status |
| assminfo-assembly-method| Assembly Assembly Method |
| assminfo-atypicalis-atypical| Assembly Atypical Is Atypical |
| assminfo-atypicalwarnings| Assembly Atypical Warnings |
| assminfo-bioproject| Assembly BioProject Accession |
| assminfo-bioproject-lineage-accession| Assembly BioProject Lineage Accession |
| assminfo-bioproject-lineage-parent-accessions| Assembly BioProject Lineage Parent Accessions |
| assminfo-bioproject-lineage-title| Assembly BioProject Lineage Title |
| assminfo-biosample-accession| Assembly BioSample Accession |
| assminfo-biosample-age| Assembly BioSample Age |
| assminfo-biosample-attribute-name| Assembly BioSample Attribute Name |
| assminfo-biosample-attribute-value| Assembly BioSample Attribute Value |
| assminfo-biosample-biomaterial-provider| Assembly BioSample Biomaterial provider |
| assminfo-biosample-bioproject-accession| Assembly BioSample BioProject Accession |
| assminfo-biosample-bioproject-parent-accessions| Assembly BioSample BioProject Parent Accessions |
| assminfo-biosample-bioproject-title| Assembly BioSample BioProject Title |
| assminfo-biosample-breed| Assembly BioSample Breed |
| assminfo-biosample-collected-by| Assembly BioSample Collected by |
| assminfo-biosample-collection-date| Assembly BioSample Collection date |
| assminfo-biosample-cultivar| Assembly BioSample Cultivar |
| assminfo-biosample-description-comment| Assembly BioSample Description Comment |
| assminfo-biosample-description-organism-common-name| Assembly BioSample Description Organism Common Name |
| assminfo-biosample-description-organism-infraspecific-breed| Assembly BioSample Description Organism Infraspecific Names Breed |
| assminfo-biosample-description-organism-infraspecific-cultivar| Assembly BioSample Description Organism Infraspecific Names Cultivar |
| assminfo-biosample-description-organism-infraspecific-ecotype| Assembly BioSample Description Organism Infraspecific Names Ecotype |
| assminfo-biosample-description-organism-infraspecific-isolate| Assembly BioSample Description Organism Infraspecific Names Isolate |
| assminfo-biosample-description-organism-infraspecific-sex| Assembly BioSample Description Organism Infraspecific Names Sex |
| assminfo-biosample-description-organism-infraspecific-strain| Assembly BioSample Description Organism Infraspecific Names Strain |
| assminfo-biosample-description-organism-name| Assembly BioSample Description Organism Name |
| assminfo-biosample-description-organism-pangolin| Assembly BioSample Description Organism Pangolin Classification |
| assminfo-biosample-description-organism-tax-id| Assembly BioSample Description Organism Taxonomic ID |
| assminfo-biosample-description-title| Assembly BioSample Description Title |
| assminfo-biosample-development-stage| Assembly BioSample Development stage |
| assminfo-biosample-ecotype| Assembly BioSample Ecotype |
| assminfo-biosample-geo-loc-name| Assembly BioSample Geographic location |
| assminfo-biosample-host| Assembly BioSample Host |
| assminfo-biosample-host-disease| Assembly BioSample Host disease |
| assminfo-biosample-identified-by| Assembly BioSample Identified by |
| assminfo-biosample-ids-db| Assembly BioSample Sample Identifiers Database |
| assminfo-biosample-ids-label| Assembly BioSample Sample Identifiers Label |
| assminfo-biosample-ids-value| Assembly BioSample Sample Identifiers Value |
| assminfo-biosample-ifsac-category| Assembly BioSample IFSAC category |
| assminfo-biosample-isolate| Assembly BioSample Isolate |
| assminfo-biosample-isolate-name-alias| Assembly BioSample Isolate name alias |
| assminfo-biosample-isolation-source| Assembly BioSample Isolation source |
| assminfo-biosample-last-updated| Assembly BioSample Last updated |
| assminfo-biosample-lat-lon| Assembly BioSample Latitude and Longitude |
| assminfo-biosample-models| Assembly BioSample Models |
| assminfo-biosample-owner-contact-lab| Assembly BioSample Owner Contact Lab |
| assminfo-biosample-owner-name| Assembly BioSample Owner Name |
| assminfo-biosample-package| Assembly BioSample Package |
| assminfo-biosample-project-name| Assembly BioSample Project name |
| assminfo-biosample-publication-date| Assembly BioSample Publication date |
| assminfo-biosample-sample-name| Assembly BioSample Sample name |
| assminfo-biosample-serotype| Assembly BioSample Serotype |
| assminfo-biosample-serovar| Assembly BioSample Serovar |
| assminfo-biosample-sex| Assembly BioSample Sex |
| assminfo-biosample-source-type| Assembly BioSample Source type |
| assminfo-biosample-status-status| Assembly BioSample Status Status |
| assminfo-biosample-status-when| Assembly BioSample Status When |
| assminfo-biosample-strain| Assembly BioSample Strain |
| assminfo-biosample-sub-species| Assembly BioSample Sub-species |
| assminfo-biosample-submission-date| Assembly BioSample Submission date |
| assminfo-biosample-tissue| Assembly BioSample Tissue |
| assminfo-blast-url| Assembly Blast URL |
| assminfo-description| Assembly Description |
| assminfo-diploid-role| Assembly Diploid Role |
| assminfo-grouping-method| Assembly Grouping Method |
| assminfo-level| Assembly Level |
| assminfo-linked-assm-accession| Assembly Linked Assembly Accession |
| assminfo-linked-assm-type| Assembly Linked Assembly Type |
| assminfo-long-name| Assembly LongName |
| assminfo-name| Assembly Name |
| assminfo-notes| Assembly Notes |
| assminfo-paired-assm-accession| Assembly Paired Assembly Accession |
| assminfo-paired-assm-changed| Assembly Paired Assembly Changed |
| assminfo-paired-assm-diff| Assembly Paired Assembly Differences |
| assminfo-paired-assm-manual-diff| Assembly Paired Assembly Manual Diff |
| assminfo-paired-assm-name| Assembly Paired Assembly Name |
| assminfo-paired-assm-only-genbank| Assembly Paired Assembly Only Genbank |
| assminfo-paired-assm-only-refseq| Assembly Paired Assembly Only RefSeq |
| assminfo-paired-assm-refseq-genbank-are-different| Assembly Paired Assembly RefSeq GenBank Are Different |
| assminfo-paired-assm-status| Assembly Paired Assembly Status |
| assminfo-refseq-category| Assembly Refseq Category |
| assminfo-release-date| Assembly Release Date |
| assminfo-sequencing-tech| Assembly Sequencing Tech |
| assminfo-status| Assembly Status |
| assminfo-submitter| Assembly Submitter |
| assminfo-suppression-reason| Assembly Suppression Reason |
| assminfo-synonym| Assembly Synonym |
| assminfo-type| Assembly Type |
| assmstats-atgc-count| Assembly Stats ATGC Count |
| assmstats-contig-l50| Assembly Stats Contig L50 |
| assmstats-contig-n50| Assembly Stats Contig N50 |
| assmstats-gaps-between-scaffolds-count| Assembly Stats Gaps Between Scaffolds Count |
| assmstats-gc-percent| Assembly Stats GC Percent |
| assmstats-genome-coverage| Assembly Stats Genome Coverage |
| assmstats-number-of-component-sequences| Assembly Stats Number of Component Sequences |
| assmstats-number-of-contigs| Assembly Stats Number of Contigs |
| assmstats-number-of-organelles| Assembly Stats Number of Organelles |
| assmstats-number-of-scaffolds| Assembly Stats Number of Scaffolds |
| assmstats-scaffold-l50| Assembly Stats Scaffold L50 |
| assmstats-scaffold-n50| Assembly Stats Scaffold N50 |
| assmstats-total-number-of-chromosomes| Assembly Stats Total Number of Chromosomes |
| assmstats-total-sequence-len| Assembly Stats Total Sequence Length |
| assmstats-total-ungapped-len| Assembly Stats Total Ungapped Length |
| checkm-completeness| CheckM completeness |
| checkm-completeness-percentile| CheckM completeness percentile |
| checkm-contamination| CheckM contamination |
| checkm-marker-set| CheckM marker set |
| checkm-marker-set-rank| CheckM marker set rank |
| checkm-species-tax-id| CheckM species tax id |
| checkm-version| CheckM version |
| current-accession| Current Accession |
| organelle-bioproject-accessions| Organelle BioProject Accessions |
| organelle-description| Organelle Description |
| organelle-infraspecific-name| Organelle Infraspecific Name |
| organelle-submitter| Organelle Submitter |
| organelle-total-seq-length| Organelle Total Seq Length |
| organism-common-name| Organism Common Name |
| organism-infraspecific-breed| Organism Infraspecific Names Breed |
| organism-infraspecific-cultivar| Organism Infraspecific Names Cultivar |
| organism-infraspecific-ecotype| Organism Infraspecific Names Ecotype |
| organism-infraspecific-isolate| Organism Infraspecific Names Isolate |
| organism-infraspecific-sex| Organism Infraspecific Names Sex |
| organism-infraspecific-strain| Organism Infraspecific Names Strain |
| organism-name| Organism Name |
| organism-pangolin| Organism Pangolin Classification |
| organism-tax-id| Organism Taxonomic ID |
| source_database| Source Database |
| type_material-display_text| Type Material Display Text |
| type_material-label| Type Material Label |
| wgs-contigs-url| WGS contigs URL |
| wgs-project-accession| WGS project accession |
| wgs-url| WGS URL |

Generated November 12, 2026
