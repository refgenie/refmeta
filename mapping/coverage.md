# refmeta coverage

Which core fields each format can fill, and which native fields have no core home. Generated on 2026-11-17 from
`mapping/crosswalk/*.yaml` (100 formats, every format with an adapter).

## How to read the matrix

- **F** (filled): at least one rule fills a field in this group and round-trips exactly (`direction: both`, no `lossy` note).
- **P** (partial): the group is filled only by lossy or one-way rules, or by a constant the format implies.
- **d** (derived): no rule fills it, but a derivation computes it from other fields (seqcol digests from
  names, lengths and sequence digests; counts from the sequence list).
- empty: the format says nothing about this group.

Columns (core field groups):

| Column | Core fields |
|---|---|
| A.acc | assembly accession |
| A.name | assembly name / labels |
| A.tax | taxon |
| A.facts | level, type, status, dates, submitter, project |
| A.fhr | FHR provenance (authors, software, article, license, links) |
| A.stats | vitalStats |
| C.dig | collection digest |
| C.l1 | seqcol level 1 |
| C.n | nSequences / totalLength |
| C.prov | provider, version, naming authority |
| C.names | collection aliases / labels |
| C.desc | collection description |
| S.name | sequence name |
| S.len | length |
| S.dig | refget digest |
| S.md5 | md5 |
| S.alias | name map (sequence aliases) |
| S.role | role, molecule, unit, placement |
| S.circ | circular |
| S.etc | description, gcPercent, ungappedLength |
| K.loc | copy location |
| K.sum | copy checksum / size / date |
| K.etc | copy kind, masking, provider, tool version |
| D | deployment entry |
| P | record provenance (authors, record date) |

## Summary by source

| Source | Formats | Native fields | Mapped by a rule | No core home |
|---|---|---|---|---|
| galaxy | 19 | 141 | 97 | 44 |
| refgenie | 7 | 205 | 170 | 35 |
| fhr | 7 | 324 | 309 | 15 |
| ncbi | 8 | 281 | 119 | 162 |
| ena | 9 | 313 | 110 | 203 |
| ensembl | 13 | 277 | 87 | 190 |
| ucsc | 12 | 98 | 61 | 37 |
| nfcore | 6 | 174 | 66 | 108 |
| bioconductor | 11 | 164 | 73 | 91 |
| ga4gh | 8 | 59 | 46 | 13 |
| **all** | 100 | 2036 | 1138 | 898 |

Most fields with no core home are about annotation (gene counts, BUSCO), sample metadata (ENA portal
fields=all), browser or pipeline settings, and tool parameters. They are kept in `extras` so a round trip
through the same format loses nothing.

## Matrix: core field groups by format

| Format | subject | A.acc | A.name | A.tax | A.facts | A.fhr | A.stats | C.dig | C.l1 | C.n | C.prov | C.names | C.desc | S.name | S.len | S.dig | S.md5 | S.alias | S.role | S.circ | S.etc | K.loc | K.sum | K.etc | D | P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| galaxy_builds_txt | deployment |  |  |  |  |  |  |  |  |  |  | P |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| galaxy_len | collection |  |  |  |  |  |  |  |  | d |  |  |  | F | F |  |  |  |  |  |  |  |  |  |  |  |
| galaxy_api_genomes | deployment |  |  |  |  |  |  |  |  |  |  | P |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| galaxy_api_genome | collection |  |  |  |  |  |  |  |  |  |  | F |  | P |  |  |  |  |  |  |  |  |  |  |  |  |
| galaxy_api_tool_data | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  | F | F |  |
| galaxy_tool_data_table_conf | deployment |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| galaxy_loc_all_fasta | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_loc_fasta_indexes | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_loc_bwa_mem_indexes | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_loc_bowtie2_indexes | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_loc_rnastar_index2x_versioned | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  | F | F |  |
| galaxy_loc_dbkeys | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_data_manager_json | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  | F | F |  |
| galaxy_idc_genomes | deployment |  |  |  |  | P |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  |  | P |  | F |  |
| galaxy_idc_data_managers | deployment |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| galaxy_idc_request | deployment | F |  |  |  |  |  |  |  |  |  | F | P | P |  |  |  |  |  |  |  | F |  |  | F |  |
| galaxy_idc_all_tables | deployment |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | F |  | F | F |  |
| galaxy_idc_refget_json | collection |  |  |  |  |  |  | F | F | d |  | F |  | F | F | F |  |  |  |  |  |  |  |  |  |  |
| galaxy_idc_refget_yaml | collection |  |  |  |  |  |  | F | F | F |  | F |  | F | F | F |  |  |  |  |  |  |  |  |  |  |
| refgenie_registry_genome | collection | F |  | F | F | F | F | F |  | F | P | F | F |  |  |  |  |  |  |  |  | F | F | F | F | F |
| refgenie_store_sources | collection | P | P | P |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  |  | F |  |  |  |  |
| refgenie_api_genome | collection | F |  | F | F | F | F | F |  |  | P | F | F |  |  |  |  |  |  |  |  | F | F | F | F | F |
| refgenie_api_genome_list | collection | F |  | F | F |  |  | F |  |  | P | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |
| refgenie_api_alias | collection | F |  | F | F | F | F | F | d | d | P | F |  | F | F | F |  |  |  |  |  |  | F | F |  | F |
| refgenie_api_sequences | collection |  |  |  |  |  |  | F | F | F |  | F |  | F | F | F | F | F |  |  | P |  |  |  |  |  |
| refgenie_genome_config | deployment |  |  |  |  |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  | F | F | P | F |  |
| fhr_json | assembly | F |  | F | F | F | F | P |  |  | P | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_yaml | assembly | F |  | F | F | F | F | P |  |  | P | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_fasta_header | copy | F |  | F | F | F | F | P |  |  | P | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_gfa_header | copy | F |  | F | F | F | F | P |  |  | P | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_jsonld | assembly | F |  | F | F | F | F | P |  |  |  | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_microdata | assembly | F |  | F | F | F | F | P |  |  |  | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| fhr_refgetstore_sidecar | collection | F |  | F | F | F | F | F |  |  | P | P |  |  |  |  |  |  |  |  |  |  | P | F |  | F |
| ncbi_datasets_assembly_report | assembly | F | F | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ncbi_datasets_sequence_report | assembly | F |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  | F | F |  | F |  |  |  |  |  |
| ncbi_assembly_report_header | assembly | F | F | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ncbi_assembly_report_sequences | assembly |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  | F | F |  |  |  |  |  |  |  |
| ncbi_assembly_summary | assembly | F | F | F | F |  | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |
| ncbi_md5checksums | copy |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F | F |  |  |  |
| ncbi_uncompressed_checksums | copy |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F | F |  |  |  |
| ncbi_analysis_set_defline | collection |  | F |  |  |  |  |  |  | d | P |  |  | F | F |  | F | F | P | P |  |  |  |  |  |  |
| ena_assembly_xml | assembly | F | F | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |
| ena_browser_summary | assembly | P | F |  | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |
| ena_portal_assembly | assembly | F | F | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |
| ena_portal_sequence | assembly |  | P | F | F |  |  |  |  |  |  |  |  |  | F |  | F | F | P | F | F |  |  |  |  |  |
| ena_sequence_report | assembly |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  | F | F |  |  |  |  |  |  |  |
| ena_regions | assembly |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  | F | F |  |  |  |  |  |  |  |
| ena_refget_metadata | assembly |  |  |  |  |  |  |  |  |  |  |  |  |  | F | F | F | P |  |  |  |  |  |  |  |  |
| ena_webin_chromosome_list | assembly |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  | F | F |  |  |  |  |  |  |
| ena_webin_unlocalised_list | assembly |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  | F |  |  |  |  |  |  |  |
| ensembl_rest_info_assembly | assembly | F | F |  | F |  | P |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ensembl_rest_toplevel_region | collection |  |  |  |  |  |  |  |  | d | P |  |  | F | F |  |  | P |  |  |  |  |  |  |  |  |
| ensembl_rest_info_assembly_region | sequence |  | F |  |  |  |  |  |  |  |  |  |  |  | F |  |  | P |  | F |  |  |  |  |  |  |
| ensembl_rest_info_genomes | assembly | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ensembl_core_meta | assembly | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ensembl_species_list | assembly | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ensembl_fasta_header | collection |  | F |  |  |  |  |  |  | d | P |  |  | F | F |  |  |  |  |  |  |  |  | P |  |  |
| ensembl_chromosomes_tsv | collection |  |  |  |  |  |  |  |  |  | P |  |  | F | F |  |  |  |  |  |  |  |  |  |  |  |
| ensembl_web_genome | assembly | F | F | F | F |  | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ensembl_web_karyotype | collection |  |  |  |  |  |  |  |  |  | P |  |  | F | F |  |  |  |  | P |  |  |  |  |  |  |
| ensembl_web_genome_stats | assembly |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ensembl_web_ftplinks | copy |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |
| ensembl_ftp_species_json | assembly | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |
| ucsc_dbdb | collection | P | P | F | F |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ucsc_api_chromosomes | collection |  |  |  |  |  |  |  |  |  |  | F |  | F | F |  |  |  |  |  |  |  |  |  | F |  |
| ucsc_chrom_sizes | collection |  |  |  |  |  |  |  |  | d |  |  |  | F | F |  |  |  |  |  |  |  |  |  |  |  |
| ucsc_chromalias_txt | collection |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  | F |  |  |  |  |  |  |  |  |
| ucsc_chromalias_table | collection |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  |  | F |  |  |  |  |  |  |  |  |
| ucsc_hub_txt | deployment |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ucsc_genomes_txt | collection |  |  | F |  |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  | F |  |  | F |  |
| ucsc_api_genark | assembly | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ucsc_api_findgenome | assembly |  |  | F | F |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  |  |  |  | F |  |
| ucsc_api_hubgenomes | collection |  |  |  |  |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  | F |  |  | F |  |
| ucsc_api_files | copy |  |  |  |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  | P | F |  |  |  |
| ucsc_md5sum | copy |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F | F |  |  |  |
| nfcore_igenomes_config | deployment |  |  |  |  |  |  |  |  |  |  | P |  | P |  |  |  |  |  |  |  | F |  |  | F |  |
| nfcore_references_datasheet | collection | P |  | F |  |  |  |  |  |  | F | P |  | P |  |  |  |  |  |  |  | F |  |  | F |  |
| nfcore_igenomes_manifest | copy |  |  | F |  |  |  |  |  |  | P | F |  |  |  |  |  |  |  |  |  | F |  |  |  |  |
| nfcore_igenomes_genomesize | collection |  |  | F |  |  |  |  |  | d |  | F | F | F | F |  | F |  | P |  | F | F |  |  |  |  |
| nfcore_igenomes_dict | collection |  | P | F |  |  |  |  |  | d |  |  |  | F | F |  | F |  |  |  |  | P |  |  |  |  |
| nfcore_igenomes_fai | collection |  |  |  |  |  |  |  |  | d |  |  |  | F | F |  |  |  |  |  |  |  |  |  |  |  |
| bioconductor_seqinfo | collection |  |  |  |  |  |  |  |  | d |  | P |  | F | F |  |  |  |  | F |  |  |  |  |  |  |
| bioconductor_chrominfo_ucsc | collection |  |  |  |  |  |  |  |  | d | P |  |  | F | F |  |  |  | P | F |  |  |  |  |  |  |
| bioconductor_chrominfo_ncbi | assembly |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  |  | F | F | F |  |  |  |  |  |  |
| bioconductor_seqlevels_style | sequence |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | F |  | F |  |  |  |  |  |  |
| bioconductor_genome_mapping_tbl | assembly |  | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| bioconductor_registered_ncbi | assembly | F | F | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| bioconductor_registered_ucsc | collection | P |  | F |  |  |  |  |  |  |  | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| bioconductor_bsgenome_seed | deployment |  |  | F | F |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  |  | P |  |  | F |  |
| bioconductor_bsgenome_description | deployment |  |  | F | F |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  |  | P |  |  | F |  |
| bioconductor_annotationhub_record | copy |  |  | F |  |  |  |  |  |  | F | P |  |  |  |  |  |  |  |  |  | F | F |  | F |  |
| bioconductor_annotationhub_metadata_csv | copy |  |  | F |  |  |  |  |  |  | F | F |  |  |  |  |  |  |  |  |  | F |  |  | F |  |
| ga4gh_seqcol_level2 | collection |  |  |  |  |  |  | d | d | d |  |  |  | F | F | F |  | P |  |  |  |  |  |  |  |  |
| ga4gh_seqcol_level1 | collection |  |  |  |  |  |  | d | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ga4gh_refget_metadata | sequence |  |  |  |  |  |  |  |  |  |  |  |  |  | F | F | F | F |  |  |  |  |  |  |  |  |
| ga4gh_seqrepo_metadata | sequence |  |  |  |  |  |  |  |  |  |  |  |  |  | F | P | P | P |  |  |  |  |  |  |  |  |
| ga4gh_vrs_sequence_reference | sequence |  |  |  |  |  |  |  |  |  |  |  |  | F |  | F |  | P |  | F | F |  |  |  |  |  |
| ga4gh_sam_header_sq | collection |  | P | P |  |  |  |  |  | d |  |  |  | F | F |  | F | P | P | F | F | P |  |  |  |  |
| ga4gh_vcf_header_contig | collection |  | P | F |  |  |  |  |  | d |  |  |  | F | F |  | F | F |  |  |  | P |  |  |  |  |
| ga4gh_vcf_header_reference | copy | F | F |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | P |  |  |  |  |

Formats that fill each group: A.acc 32, A.name 25, A.tax 40, A.facts 29, A.fhr 16, A.stats 19, C.dig 16, C.l1 6, C.n 18, C.prov 22, C.names 46, C.desc 9, S.name 29, S.len 30, S.dig 9, S.md5 10, S.alias 20, S.role 12, S.circ 11, S.etc 6, K.loc 34, K.sum 17, K.etc 16, D 34, P 14.

## Native fields with no core home, per format

Grouped by the reason given in each crosswalk. Long groups are shortened; the crosswalk file lists every field.

### galaxy

- **galaxy_builds_txt**: none.
- **galaxy_len**: none.
- **galaxy_api_genomes**: none.
- **galaxy_api_genome** (4): `reference` (Whether the server can serve sequence for the dbkey (a twobit entry exists); server capability); `prev_chroms`, `next_chroms` (Paging flag); `start_index` (Paging offset).
- **galaxy_api_tool_data** (3): `model_class` (Python class of the table; server internals); `columns` (Column order of the table; implied by the rule paths); `fields[].with_gene_model` (Whether a STAR index was built with a GTF; no core field).
- **galaxy_tool_data_table_conf** (11): `comment_char` (Parsing setting for .loc files); `allow_duplicate_entries`, `separator`, `empty_field_value` (Parsing setting); `type` (Table type (tabular or refgenie)); `asset` (refgenie asset that fills a refgenie-type table); `user_accessible` (Access setting); `columns` (Column names of the table); `column` (Column declarations); `file` (.loc files that fill the table); `field` (Template fields of a refgenie-type table).
- **galaxy_loc_all_fasta**: none.
- **galaxy_loc_fasta_indexes**: none.
- **galaxy_loc_bwa_mem_indexes**: none.
- **galaxy_loc_bowtie2_indexes**: none.
- **galaxy_loc_rnastar_index2x_versioned** (1): `with_gene_model` (Whether the index was built with a GTF; no core field).
- **galaxy_loc_dbkeys**: none.
- **galaxy_data_manager_json** (1): `with_gene_model` (Whether a STAR index was built with a GTF; no core field).
- **galaxy_idc_genomes** (5): `source` (Where to fetch the FASTA: 'ucsc', an NCBI accession or a URL; mixed kinds, so no single core field); `version` (Free-text version information); `blob` (Free text); `indexers` (Data managers to run: a build plan); `skiplist` (Data managers to skip: a build plan).
- **galaxy_idc_data_managers** (4): `data_manager` (Short name of a data manager tool); `tool_id` (Tool Shed id of the data manager); `tags` (Tags used to pick data managers); `parameters` (Fixed tool parameters).
- **galaxy_idc_request** (7): `tool_id` (Tool Shed id of the data manager to run); `params.dbkey_source.dbkey_source_selector` (Tool form choice (existing or new dbkey)); `params.reference_source.reference_source_selector` (Tool form choice (ucsc, ncbi, url)); `params.sorting.sort_selector` (Tool form choice for sequence order); `params.sorting.handle_not_listed_selector` (Tool form choice); `doi` (DOI of the data source; no example has one); `depends_on.all_fasta` (The all_fasta entry an index is built from. Core has no 'built from' link between copies yet (open question)).
- **galaxy_idc_all_tables** (4): `with_gene_model` (Whether a STAR index was built with a GTF; no core field); `line_type` (sam_fa_indexes column, always 'index'); `loc_file` (The .loc file the row came from; server configuration); `xml_file` (The tool_data_table_conf.xml that declared it; server configuration).
- **galaxy_idc_refget_json** (2): `aliases.galaxy_loc_file` (The .loc file the row came from, with '/' written as '!'; server configuration); `aliases.galaxy_tool_data_table_conf` (The tool_data_table_conf.xml, with '/' written as '!'; server configuration).
- **galaxy_idc_refget_yaml** (2): `aliases.galaxy_loc_file` (The .loc file the row came from, with '/' written as '!'; server configuration); `aliases.galaxy_tool_data_table_conf` (The tool_data_table_conf.xml, with '/' written as '!'; server configuration).

### refgenie

- **refgenie_registry_genome** (5): `seqcol.compute` (Instruction to the registry build (compute the digest), not a fact); `build.tier` (Registry build plan (which assets to build)); `build.add`, `build.drop` (Registry build plan); `metadata.last_verified` (When a curator last checked the URL; no core field).
- **refgenie_store_sources** (4): `group` (Folder-like label for organizing a store); `pep_sample_name` (Sample name in the PEP the row came from (some stores only)); `sha256` (A legacy Salmon index hash, not a FASTA checksum); `population` (Population of the HPRC sample (pangenome store only); no core field).
- **refgenie_api_genome** (3): `fhr.schema` (FHR schema URL written by the exporter); `fhr.schemaVersion` (FHR version written by the exporter (the number 1.0)); `species.synonyms` (Other names of the species (baker's yeast); core keeps one common name).
- **refgenie_api_genome_list** (2): `asset_count` (How many assets this server built; a server statistic); `species.synonyms` (Other names of the species; core keeps one common name).
- **refgenie_api_alias** (3): `source` (Where the alias was resolved; always 'server'); `fhr.schema` (FHR schema URL written by the exporter); `fhr.schemaVersion` (FHR version written by the exporter (the number 1.0)).
- **refgenie_api_sequences** (1): `alphabet` (RefgetStore storage encoding (dna2bit, dnaio); a deployment detail).
- **refgenie_genome_config** (17): `config_version` (Config file format version); `genome_servers` (Servers this install pulls from; client setting); `genome_server` (Pre-0.4 single server setting); `remotes` (Server setting for archive URL prefixes); `genome_archive_folder`, `genome_archive_config`, `remote_url_base` (Server setting); `genomes.{genome}.assets.{asset}.asset_description` (Describes the asset type, not this genome); `genomes.{genome}.assets.{asset}.default_tag` (Client default; not a fact about the files); `genomes.{genome}.assets.{asset}.tags.{tag}.seek_keys` (File names inside the asset folder; they would need one copy each, relative to the asset folder); `genomes.{genome}.assets.{asset}.tags.{tag}.asset_parents` (Asset build graph (which asset was built from which); core has no 'built from' link yet); `genomes.{genome}.assets.{asset}.tags.{tag}.asset_children` (Asset build graph; core has no 'built from' link yet); `genomes.{genome}.assets.{asset}.tags.{tag}.archive_digest` (Checksum of the server's .tgz archive, a different file whose location is not in the record); `genomes.{genome}.assets.{asset}.tags.{tag}.legacy_archive_digest` (Older archive checksum); `genomes.{genome}.assets.{asset}.tags.{tag}.asset_size` (Human-readable rounded size (2.9GB); not convertible to bytes exactly); `genomes.{genome}.assets.{asset}.tags.{tag}.archive_size` (Human-readable rounded size of the archive); `genomes.{genome}.assets.{asset}.tags.{tag}.tag_description` (Free text about the tag).

### fhr

- **fhr_json** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format).
- **fhr_yaml** (3): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format); `x-example-pipeline` (Upstream example extension with no meaning outside its file).
- **fhr_fasta_header** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format).
- **fhr_gfa_header** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format).
- **fhr_jsonld** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format).
- **fhr_microdata** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version (1, 2.0, 2.1): a property of the record format).
- **fhr_refgetstore_sidecar** (2): `schema` (URL of the FHR schema the record follows: a property of the record format, not of the genome); `schemaVersion` (FHR contract version, written as the number 1.0 by gtars: a property of the record format).

### ncbi

- **ncbi_datasets_assembly_report** (137): `current_accession` (Newest version of the accession chain: a relation between assembly versions, which the core does not model); `source_database` (GenBank or RefSeq; implied by the accession prefix); `organism.lineage` (Lineage list; no core field); `organism.pangolin_classification` (Virus lineage; no core field); `organism.infraspecific_names.sex` (Sex of the sample; sample metadata); `assembly_info.paired_assembly.status`, `assembly_info.paired_assembly.annotation_name`, `assembly_info.paired_assembly.only_genbank`, `assembly_info.paired_assembly.only_refseq`, `assembly_info.paired_assembly.changed`, `assembly_info.paired_assembly.manual_diff`, `assembly_info.paired_assembly.refseq_genbank_are_different`, `assembly_info.paired_assembly.differences` (How the GenBank and RefSeq members differ (only_genbank, only_refseq, differences). Core has no relation between assemblies yet; see the open questions); `assembly_info.assembly_long_name` (No example; long name); `assembly_info.bioproject_lineage` (Parent BioProjects; the core keeps the assembly's own BioProject); `assembly_info.submission_date` (Submission date; core keeps the release date); `assembly_info.linked_assembly` (Linked assembly (e.g. other haplotype); no core relation between assemblies); `assembly_info.linked_assemblies` (Linked assemblies; no core relation between assemblies); `assembly_info.atypical.is_atypical`, `assembly_info.atypical.warnings` (Atypical-assembly warnings; no core field); `assembly_info.genome_notes` (Notes; no example); `assembly_info.grouping_method` (Virus segment grouping); `assembly_info.biosample.last_updated`, `assembly_info.biosample.publication_date`, `assembly_info.biosample.submission_date`, `assembly_info.biosample.sample_ids`, `assembly_info.biosample.description.title` and 48 more (BioSample details beyond the accession; sample metadata is out of scope); `assembly_info.blast_url` (BLAST page link); `assembly_info.suppression_reason`, `assembly_info.diploid_role` (No core field); `assembly_stats.gaps_between_scaffolds_count` (Gap count; no core field); `assembly_stats.number_of_component_sequences` (Component count; no core field); `assembly_stats.atgc_count` (Base counts; no core field); `assembly_stats.gc_count` (Base counts; gcContent holds the percent); `assembly_stats.number_of_organelles` (Count of organelles; no core field); `organelle_info` (Organelle summaries; per-sequence facts are in the sequence report); `additional_submitters` (Who submitted organelle sequences; no core field); `annotation_info.name`, `annotation_info.provider`, `annotation_info.release_date`, `annotation_info.report_url`, `annotation_info.stats.gene_counts.total` and 17 more (Gene annotation; refmeta covers sequences, not annotation); `wgs_info.wgs_project_accession`, `wgs_info.master_wgs_url`, `wgs_info.wgs_contigs_url` (WGS project links; no core field); `type_material.type_label`, `type_material.type_display_text` (Type material; no core field); `checkm_info.checkm_marker_set`, `checkm_info.checkm_species_tax_id`, `checkm_info.checkm_marker_set_rank`, `checkm_info.checkm_version`, `checkm_info.completeness`, `checkm_info.contamination`, `checkm_info.completeness_percentile` (CheckM completeness (prokaryotes); no core field); `average_nucleotide_identity.taxonomy_check_status`, `average_nucleotide_identity.match_status`, `average_nucleotide_identity.submitted_organism`, `average_nucleotide_identity.submitted_species`, `average_nucleotide_identity.category` and 13 more (Taxonomy check results; no core field).
- **ncbi_datasets_sequence_report** (4): `sort_order` (Sort key; core keeps order as array order); `gc_count` (Base count; gcPercent holds the percent); `unlocalized_count` (Count of unlocalized scaffolds on a chromosome; derivable from the rows); `assembly_unplaced_count` (Count of unplaced scaffolds; derivable from the rows).
- **ncbi_assembly_report_header** (5): `RefSeq assembly and GenBank assemblies identical` (yes/no comparison of the pair; no core relation between assemblies); `Assembly-Unit names` (Assembly units; per-sequence assemblyUnit holds the unit of each sequence); `Assembly-Units` (Assembly unit accessions; no core field); `Sex` (Sex of the sample; sample metadata); `Expected final version` (Submitter's expectation; no core field).
- **ncbi_assembly_report_sequences** (1): `Relationship` ('=' when the GenBank and RefSeq sequence are identical; no core field).
- **ncbi_assembly_summary** (13): `wgs_master` (WGS master record; no core field); `paired_asm_comp` (identical/different comparison of the pair; no core relation between assemblies); `excluded_from_refseq` (RefSeq exclusion reasons); `relation_to_type_material` (Type material); `asm_not_live_date` (When the version stopped being latest; core keeps status only); `group` (Taxonomic group label); `annotation_provider`, `annotation_name`, `annotation_date`, `total_gene_count`, `protein_coding_gene_count`, `non_coding_gene_count` (Annotation; out of scope); `pubmed_id` (PubMed ids; core scholarlyArticle holds one DOI).
- **ncbi_md5checksums**: none.
- **ncbi_uncompressed_checksums**: none.
- **ncbi_analysis_set_defline** (2): `hm` (Hard-masked spans; core has masking only per file); `SP` (Species of a non-human sequence (chrEBV); core has one taxon per record).

### ena

- **ena_assembly_xml** (25): `@broker_name` (Submission broker); `IDENTIFIERS/SECONDARY_ID` (Secondary ids; no example); `IDENTIFIERS/EXTERNAL_ID` (External ids; no example); `IDENTIFIERS/UUID` (UUIDs; no example); `ASSEMBLY_TYPE` ('clone or isolate', 'primary metagenome': a different vocabulary from NCBI's assembly type (haploid ...)); `WGS_SET` (WGS contig sets; no core field); `WGS_SET/PREFIX` (WGS contig set prefix); `WGS_SET/VERSION` (WGS contig set version); `CHROMOSOMES/CHROMOSOME` (Chromosome list with unlocalized scaffolds collapsed into accession ranges; use the sequence report for sequences); `CHROMOSOMES/CHROMOSOME/@accession`, `CHROMOSOMES/CHROMOSOME/NAME`, `CHROMOSOMES/CHROMOSOME/TYPE` (Part of the collapsed chromosome list); `ASSEMBLY_LINKS/ASSEMBLY_LINK` (Links to WGS set files); `ASSEMBLY_LINKS/ASSEMBLY_LINK/URL_LINK/LABEL` (Link label); `ASSEMBLY_LINKS/ASSEMBLY_LINK/URL_LINK/URL` (Link URL); `ASSEMBLY_LINKS/ASSEMBLY_LINK/XREF_LINK/DB`, `ASSEMBLY_LINKS/ASSEMBLY_LINK/XREF_LINK/ID` (Cross-reference; no example); `ASSEMBLY_ATTRIBUTES/spanned-gaps`, `ASSEMBLY_ATTRIBUTES/unspanned-gaps`, `ASSEMBLY_ATTRIBUTES/contig-n75`, `ASSEMBLY_ATTRIBUTES/scaf-n75`, `ASSEMBLY_ATTRIBUTES/count-non-chromosome-replicon`, `ASSEMBLY_ATTRIBUTES/count-alt-loci-units`, `ASSEMBLY_ATTRIBUTES/count-regions`, `ASSEMBLY_ATTRIBUTES/count-patches` (Assembly statistic with no FHR or core field (gap counts, N75, alt-loci and region counts)).
- **ena_browser_summary** (22): `dataType` (Record type (ASSEMBLY)); `status` (Numeric public status); `statusDescription` (Status text); `assemblyType` ('clone or isolate'; a different vocabulary from NCBI's assembly type); `wgsSet` (WGS contig set); `newAccession` (Newest version of the chain; the core does not model relations between assembly versions); `chromosomes` (Collapsed chromosome list; use the sequence report); `chromosomes.accession`, `chromosomes.name`, `chromosomes.type`, `chromosomes.count` (Part of the collapsed chromosome list); `links` (Links to WGS set files); `links.label` (Link label); `links.url` (Link URL); `attributes.spanned-gaps`, `attributes.unspanned-gaps`, `attributes.contig-n75`, `attributes.scaf-n75`, `attributes.count-non-chromosome-replicon`, `attributes.count-alt-loci-units`, `attributes.count-regions`, `attributes.count-patches` (Assembly statistic with no FHR or core field (gap counts, N75, alt-loci and region counts)).
- **ena_portal_assembly** (96): `accession` (The unversioned chain (GCA_000001405); assembly_set_accession is the versioned id); `experimental_factor`, `environment_biome`, `dev_stage`, `binning_software`, `location_start` and 79 more (Sample or environment field from the portal's fields=all; sample metadata is out of scope); `sequence_accession` (Partial list of sequence accessions (67 of 455 for GRCh38)); `status` (public); `tax_lineage` (Lineage taxids); `assembly_accession` (The unversioned chain again); `tax_division` (Taxonomic division (HUM, FUN)); `assembly_type` ('clone or isolate'; a different vocabulary); `study_name`, `study_title`, `study_description` (Study metadata); `wgs_set` (WGS contig set); `category` (Taxonomic category).
- **ena_portal_sequence** (54): `accession` (Unversioned sequence accession; sequence_accession is versioned); `collection_date`, `country`, `sample_accession`, `dev_stage`, `run_accession` and 36 more (Sample or environment field; sample metadata is out of scope); `keywords` (INSDC keywords (ALTERNATE_LOCUS); role is not stated directly); `dataclass` (INSDC data class (CON, STD)); `pubmed_id`, `doi` (Citations of the sequence record); `last_updated` (Record update date); `mol_type` (genomic DNA for all); `status` (public); `tax_lineage` (Lineage taxids); `first_public` (Record public date); `tax_division` (Taxonomic division); `indexed_date` (Portal index date); `sequence_version` (Version part of sequence_accession).
- **ena_sequence_report**: none.
- **ena_regions** (1): `sequence-range` (Part of the alt scaffold covered by the placement; core has only the chromosome range).
- **ena_refget_metadata** (4): `metadata.id` (Echo of the identifier the client asked for); `metadata.trunc512` (Deprecated digest form; ENA always sends null); `metadata.aliases.alias`, `metadata.aliases.naming_authority` (Member of metadata.aliases; mapped through the metadata.aliases rule).
- **ena_webin_chromosome_list** (1): `CHROMOSOME_TYPE` (chromosome, plasmid, linkage_group ...: Webin's own vocabulary, which overlaps CHROMOSOME_LOCATION in sequences[].molecule).
- **ena_webin_unlocalised_list**: none.

### ensembl

- **ensembl_rest_info_assembly** (6): `genebuild_initial_release_date`, `genebuild_start_date`, `genebuild_last_geneset_update`, `genebuild_method` (Gene annotation; out of scope); `coord_system_versions` (Every coordinate system version in the database (GRCh37, NCBI36 ...); history, not this assembly); `karyotype` (Names of the karyotype sequences only, a subset; split out per region in ensembl_rest_toplevel_region).
- **ensembl_rest_toplevel_region** (1): `coord_system` (chromosome or scaffold: Ensembl's coordinate system, not a sequence role).
- **ensembl_rest_info_assembly_region** (3): `coordinate_system` (chromosome or scaffold: Ensembl's coordinate system); `assembly_exception_type` (REF, or empty for alt and patch scaffolds; does not tell alt from patch); `is_chromosome` (Whether the region is in the chromosome coordinate system).
- **ensembl_rest_info_genomes** (16): `has_genome_alignments`, `has_synteny`, `has_microarray`, `has_other_alignments`, `has_variations`, `has_pan_compara`, `has_peptide_compara` (Data availability flag); `data_release_id`, `assembly_id`, `organism_id` (Internal database row id); `serotype` (Serotype; no example); `reference` (Name of the genome this one is a strain or variant of; a relation between assemblies the core does not model. No example); `genebuild` (Gene annotation label; out of scope); `url_name` (Website URL name); `base_count` (Length of all toplevel regions in the core database, LRGs included (3398673745 for human); matches no sequence set); `website_packed` (Website flag).
- **ensembl_core_meta** (56): `species_id`, `schema_type`, `schema_version`, `patch`, `genebuild.id` and 43 more (Database, annotation or website setting; no core field); `assembly.mapping` (Coordinate system mappings inside the database); `assembly.coverage_depth` (Historical depth class (high/low)); `assembly.web_accession_source` (Website link setting); `assembly.web_accession_type` (Website link label); `species.alias` (Species aliases used by the website); `species.classification` (Lineage names); `assembly.provider_url` (Provider web page); `species.species_name` (Species name without strain; core keeps one name).
- **ensembl_species_list** (9): `genebuild` (Gene annotation label); `variation`, `microarray`, `pan_compara`, `peptide_compara`, `genome_alignments`, `other_alignments` (Data availability flag); `core_db` (Core database name); `species_id` (Species id inside the core database).
- **ensembl_fasta_header** (6): `coord_system_name` (chromosome or scaffold: Ensembl's coordinate system); `slice.coord_system_name` (Repeats coord_system_name); `slice.seq_region_name` (Repeats id); `slice.start`, `slice.strand` (Always 1); `assembly_exception_type` (REF, or empty for alt and patch scaffolds; does not tell alt from patch).
- **ensembl_chromosomes_tsv**: none.
- **ensembl_web_genome** (21): `genome_tag` (Readable genome alias; equals the accession for the anchors); `type`, `suppression_details` (Site field with no core home); `is_reference` (Whether the site treats it as its species' reference); `is_suppressed` (Site flag); `release.type` (Site release type); `assembly_provider.url` (Provider web page); `annotation_provider.name`, `annotation_provider.url`, `annotation_method`, `annotation_version`, `annotation_date`, `coding_genes_count`, `annotation_provider` (Gene annotation; out of scope); `number_of_genomes_in_group` (Site statistic); `type.kind` (Kind of type.value (strain, breed ...); core keeps the value only); `has_variation`, `has_regulation` (Data availability flag); `organism_id` (Organism UUID in the site database); `rank` (Search rank); `release_version` (Metadata release version).
- **ensembl_web_karyotype** (1): `type` (Always 'chromosome' (also for MT); not a molecule type).
- **ensembl_web_genome_stats** (64): `genome_stats.assembly_stats.total_genome_length` (3298912062 for human matches no known sequence set; left out rather than guessed); `genome_stats.assembly_stats.total_coding_sequence_length` (Annotation; out of scope); `genome_stats.assembly_stats.total_gap_length` (Gap length; no core field); `genome_stats.assembly_stats.spanned_gaps` (Gap count; no core field); `genome_stats.assembly_stats.toplevel_sequences` (709 for human matches neither the 706-sequence FASTA nor the 194 REST regions); `genome_stats.assembly_stats.component_sequences` (Component count; no core field); `genome_stats.coding_stats.coding_genes`, `genome_stats.coding_stats.average_genomic_span`, `genome_stats.coding_stats.average_sequence_length`, `genome_stats.coding_stats.average_cds_length`, `genome_stats.coding_stats.shortest_gene_length` and 53 more (Annotation, variation or regulation statistic; out of scope).
- **ensembl_web_ftplinks** (1): `dataset` (Dataset type of the directory (assembly, genebuild, homologies, short_variants); not a file kind).
- **ensembl_ftp_species_json** (6): `species.{species}` (Species key of the file (Homo_sapiens)); `species.{species}.strain` (Species-level value; for human it is one pangenome sample (HG03540), not GRCh38's); `species.{species}.strain_type` (Kind of the species-level strain value); `species.{species}.biosample_id` (Species-level value; for human it belongs to one pangenome sample, not GRCh38); `species.{species}.assemblies.{accession}.genebuild_providers` (Gene annotation releases; out of scope); `species.{species}.assemblies.{accession}.assembly` (Tree of files on the FTP; paths only, no checksums).

### ucsc

- **ucsc_dbdb** (7): `defaultPos` (Browser start position); `active` (Browser flag); `orderKey` (Menu order); `genome` (Menu group shared by all builds of an organism (Human), not the genome name); `htmlPath` (Server path of the description page); `hgNearOk`, `hgPbOk` (Browser feature flag).
- **ucsc_api_chromosomes** (1): `track` (Track filter of the request).
- **ucsc_chrom_sizes**: none.
- **ucsc_chromalias_txt**: none.
- **ucsc_chromalias_table**: none.
- **ucsc_hub_txt** (5): `longLabel` (Longer hub label); `useOneFile` (Hub layout setting); `email` (Hub contact); `descriptionUrl` (Hub description page); `genomesFile` (Path of genomes.txt; hub layout).
- **ucsc_genomes_txt** (12): `trackDb` (Track definitions file); `groups` (Track groups file); `chromAuthority` (Which names the browser displays. In GenArk the 2bit uses RefSeq names and chromAuthority ucsc only changes the display, so it is not the collection's naming authority); `organism` (GenArk writes '<asmName> <date>' (R64 Dec. 2014) here, not an organism); `defaultPos` (Browser start position); `orderKey` (Menu order); `htmlPath` (Description page); `blat` (BLAT server); `transBlat` (Translated BLAT server); `isPcr` (In-silico PCR server); `codonTable` (Genetic code per sequence; no core field); `liftOver.*` (Per-target liftOver chain files (key pattern liftOver.<target>); relations between assemblies by alignment, not seqcol relations).
- **ucsc_api_genark** (2): `priority` (Search ranking); `clade` (GenArk clade group; unreliable values).
- **ucsc_api_findgenome** (4): `priority` (Search ranking); `clade` (Approximate clade); `description` (Free search text mixing names, accessions and dates); `browserExists` (Whether UCSC shows the genome now).
- **ucsc_api_hubgenomes** (5): `organism` (The stanza's organism setting (GenArk writes '<asmName> <date>')); `trackDbFile` (Track definitions file); `groups` (Track groups file); `defaultPos` (Browser start position); `orderKey` (Menu order).
- **ucsc_api_files** (1): `rsyncHost` (rsync host of the download server; envelope).
- **ucsc_md5sum**: none.

### nfcore

- **nfcore_igenomes_config** (39): `star_legacy` (Pipeline flag for old STAR indexes); `bed12`, `blacklist`, `ascat_alleles`, `ascat_loci`, `ascat_loci_gc` and 26 more (Pipeline resource that is not the genome itself (annotation BED, variant sets, intervals, model files, tool parameters)); `macs_gsize` (Effective genome size for MACS2: a tool parameter); `readme` (README of the iGenomes build); `ascat_genome`, `snpeff_db`, `vep_cache_version` (Tool parameter); `vep_genome` (Assembly name VEP expects: a tool parameter); `vep_species` (Species name VEP expects: a tool parameter).
- **nfcore_references_datasheet** (60): `genes_bed`, `abundantsequences_fasta`, `genes_refflat`, `hairpin_fasta`, `mature_fasta` and 43 more (Pipeline resource that is not the genome itself (annotation, variant sets, intervals, model files, tool parameters)); `ascat_genome`, `snpeff_db`, `vep_cache_version`, `vep_genome`, `vep_species`, `macs_gsize` (Tool parameter); `readme` (README of the build); `annotation_version` (Annotation version, but it holds GCF assembly accessions in practice; ambiguous); `site` (Website of the provider); `star_sjdbOverhang`, `star_genomeSAindexNbases` (STAR build parameter); `source_version` (Older name of annotation_version).
- **nfcore_igenomes_manifest** (2): `section` (Path segment (Sequence, Annotation); part of the location); `subpath` (Rest of the path; part of the location).
- **nfcore_igenomes_genomesize** (2): `isCircular` (Placeholder: always false, even for chrM); `ploidy` (Placeholder: always 2).
- **nfcore_igenomes_dict** (2): `@HD/VN` (SAM format version); `@HD/SO` (Sort order; always unsorted).
- **nfcore_igenomes_fai** (3): `OFFSET` (Byte offset in one FASTA file: a fact about the copy's layout, per sequence); `LINEBASES` (FASTA line width of the copy; differs between copies (50, 60, 70, 100)); `LINEWIDTH` (FASTA line width in bytes, per copy).

### bioconductor

- **bioconductor_seqinfo**: none.
- **bioconductor_chrominfo_ucsc**: none.
- **bioconductor_chrominfo_ncbi** (1): `Relationship` ('=' when the GenBank and RefSeq sequence are identical; no core field).
- **bioconductor_seqlevels_style** (2): `auto` (Autosome flag; no core field); `sex` (Sex-chromosome flag; no core field).
- **bioconductor_genome_mapping_tbl** (5): `origEnsemblVersion` (First Ensembl release with this name; release history); `origEnsemblDate` (Release history, written like Sept.2019); `ensemblVersion`, `ensemblDate` (Release history); `ucscDate` (UCSC release date written like Dec.2013).
- **bioconductor_registered_ncbi** (3): `extra_info` (Named tags (strain=S288C); an object, not one field); `circ_seqs` (NCBI names of the circular sequences; marking them needs the sequence list); `NCBI2Ensembl_special_mappings` (NCBI to Ensembl name exceptions (MT -> Mito); a partial name map without the other sequences).
- **bioconductor_registered_ucsc** (9): `ASSEMBLED_MOLECULES` (Names of the assembled molecules, a subset of the collection); `CIRC_SEQS` (Names of the circular sequences); `FETCH_ORDERED_CHROM_SIZES` (R function source); `NCBI_LINKER.special_mappings` (UCSC to NCBI name exceptions; partial name map); `NCBI_LINKER.unmapped_seqs` (UCSC sequences with no NCBI match, grouped by role; core has no field for 'not in the linked assembly'); `NCBI_LINKER.AssemblyUnits` (Assembly units to match on); `NCBI_LINKER.drop_unmapped` (Mapping option); `NCBI_LINKER` (Raw R source when it could not be evaluated); `ENSEMBL_LINKER` (Name of the UCSC table used for Ensembl names).
- **bioconductor_bsgenome_seed** (34): `Title` (Package title); `Description` (Package description); `Version` (Package version); `Author` (Package author); `Maintainer` (Package maintainer); `Suggests` (Package dependency); `License` (Package license, not the genome's terms); `organism_biocview` (biocViews term); `BSgenomeObjname` (R object name); `seqnames` (R expression for the sequence names); `circ_seqs` (R expression for the circular sequences); `mseqnames` (R expression); `PkgDetails` (Man page text); `SrcDataFiles` (Free text naming the source files); `PkgExamples` (R code); `seqs_srcdir` (Local build folder); `seqfile_name` (Source 2bit file name in the build folder); `seqfiles_prefix`, `seqfiles_suffix`, `ondisk_seq_format`, `citation_file`, `RefPkgname` and 12 more (Package build setting (file name parts, mask sources)).
- **bioconductor_bsgenome_description** (12): `Title`, `Description`, `Version`, `Author`, `Maintainer` and 7 more (R package field (title, version, authors, dependencies, license of the package)).
- **bioconductor_annotationhub_record** (15): `id` (Internal row id); `description` (Free text); `coordinate_1_based` (Coordinate base of the resource); `maintainer` (Resource maintainer); `rdatadateadded` (When the hub added it); `rdatadateremoved` (When the hub removed it); `preparerclass` (Hub recipe class); `location_prefix` (Base URL for rdatapath; joining it needs two fields); `recipe` (Hub recipe); `recipe_package` (Hub recipe package); `rdatapaths[].rdataclass` (R class of the file); `rdatapaths[].dispatchclass` (How the hub loads the file); `input_sources[].sourcetype` (Format of the source (FASTA, TwoBit)); `tags` (Search tags); `biocversions` (Bioconductor versions that list the resource).
- **bioconductor_annotationhub_metadata_csv** (10): `Description` (Free text); `BiocVersion` (First Bioconductor version); `SourceType` (Format of the source); `SourceVersion` (Version of the source data); `Coordinate_1_based` (Coordinate base); `Maintainer` (Maintainer); `RDataClass` (R class); `DispatchClass` (Loader); `Location_Prefix` (Base URL); `Tags` (Search tags).

### ga4gh

- **ga4gh_seqcol_level2**: none.
- **ga4gh_seqcol_level1**: none.
- **ga4gh_refget_metadata** (2): `metadata.id` (Echo of the identifier the client asked for, not a fact about the sequence); `metadata.trunc512` (Deprecated hex form of the same SHA-512 digest; equal to digest after hex-to-base64url, which is not one of the fixed transforms).
- **ga4gh_seqrepo_metadata** (2): `added` (When this SeqRepo instance loaded the sequence: deployment fact with no core field); `alphabet` (Set of residue letters present; no core field).
- **ga4gh_vrs_sequence_reference** (6): `id` (Identifier in the producing system only); `type` (Always 'SequenceReference'; implied by the format); `extensions` (Free gkm-core extension objects); `residueAlphabet` (na/aa; core assumes nucleic acid); `sequence` (Literal sequence text; refmeta holds metadata, not sequence); `moleculeType` (RefSeq molecule type (genomic, mRNA); not the replicon type in sequences[].molecule).
- **ga4gh_sam_header_sq**: none.
- **ga4gh_vcf_header_contig** (1): `taxonomy` (Spec-example key with no defined meaning (value 'x')).
- **ga4gh_vcf_header_reference** (2): `fileformat` (VCF version of the file, not a fact about the genome); `assembly` (URL of a FASTA of structural-variant breakpoint assemblies, not the genome assembly).

