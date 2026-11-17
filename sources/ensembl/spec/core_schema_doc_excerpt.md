<!-- Source: https://jun2026.archive.ensembl.org/info/docs/api/core/core_schema.html (www.ensembl.org/info/docs/api/core/core_schema.html redirects there), retrieved 2026-11-17. HTML converted to text; only the tables listed below are kept, and the per-table "List of species with populated data" lists are removed. -->
# Ensembl Core schema documentation (excerpt)

## assembly_exception

Allows multiple sequence regions to point to the same sequence, analogous to a symbolic link in a filesystem pointing to the actual file. This mechanism has been implemented specifically to support haplotypes and PARs, but may be useful for other similar structures in the future.

| Column  | Type  | Default value  | Description  | Index

| assembly_exception_id  | INT(10)  | -  | Assembly exception sequence region id. Primary key, internal identifier.  | primary key

| seq_region_id  | INT(10)  | -  | Sequence region id. Foreign key references to the seq_region table.  | key: sr_idx

| seq_region_start  | INT(10)  | -  | Sequence start position.  | key: sr_idx

| seq_region_end  | INT(10)  | -  | Sequence end position.  |

| exc_type  | ENUM:

- HAP

-  PAR

- PATCH_FIX

-  PATCH_NOVEL

| NULL  | Exception type, e.g. PAR, HAP - haplotype.  |

| exc_seq_region_id  | INT(10)  | -  | Exception sequence region id. Foreign key references to the seq_region table.  | key: ex_idx

| exc_seq_region_start  | INT(10)  | -  | Exception sequence start position.  | key: ex_idx

| exc_seq_region_end  | INT(10)  | -  | Exception sequence end position.  |

| ori  | INT  | -  | Orientation: 1 - sense; -1 - antisense.  |

|
See also:

- assembly

- seq_region

coord_system

Stores information about the available co-ordinate systems for the species identified through the species_id field. Note that for each species, there must be one co-ordinate system that has the attribute "top_level" and one that has the attribute "sequence_level".

| Column  | Type  | Default value  | Description  | Index

| coord_system_id  | INT(10)  | -  | Primary key, internal identifier.  | primary key

| species_id  | INT(10)  | 1  | Indentifies the species for multi-species databases.  | unique key: rank_idx

unique key: name_idx

key: species_idx

| name  | VARCHAR(40)  | -  | Co-oridinate system name, e.g. 'chromosome', 'contig', 'scaffold' etc.  | unique key: name_idx

| version  | VARCHAR(255)  | NULL  | Assembly.  | unique key: name_idx

| rank  | INT  | -  | Co-oridinate system rank.  | unique key: rank_idx

| attrib  | SET:

- default_version

-  sequence_level

| NULL  | Co-oridinate system attrib (e.g. "top_level", "sequence_level").  |

|
See also:

- seq_region

- meta_coord

- meta

|   |

## coord_system

Stores information about the available co-ordinate systems for the species identified through the species_id field. Note that for each species, there must be one co-ordinate system that has the attribute "top_level" and one that has the attribute "sequence_level".

| Column  | Type  | Default value  | Description  | Index

| coord_system_id  | INT(10)  | -  | Primary key, internal identifier.  | primary key

| species_id  | INT(10)  | 1  | Indentifies the species for multi-species databases.  | unique key: rank_idx

unique key: name_idx

key: species_idx

| name  | VARCHAR(40)  | -  | Co-oridinate system name, e.g. 'chromosome', 'contig', 'scaffold' etc.  | unique key: name_idx

| version  | VARCHAR(255)  | NULL  | Assembly.  | unique key: name_idx

| rank  | INT  | -  | Co-oridinate system rank.  | unique key: rank_idx

| attrib  | SET:

- default_version

-  sequence_level

| NULL  | Co-oridinate system attrib (e.g. "top_level", "sequence_level").  |

|
See also:

- seq_region

- meta_coord

- meta

|   |

## dna

Contains DNA sequence. This table has a 1:1 relationship with the seq_region table.

| Column  | Type  | Default value  | Description  | Index

| seq_region_id  | INT(10)  | -  | Primary key, internal identifier. Foreign key references to the seq_region table.  | primary key

| sequence  | LONGTEXT  | -  | DNA sequence.  |

|
See also:

- seq_region

|   |

## karyotype

Describes bands that can be stained on the chromosome.

| Column  | Type  | Default value  | Description  | Index

| karyotype_id  | INT(10)  | -  | Primary key, internal identifier.  | primary key

| seq_region_id  | INT(10)  | -  | Foreign key references to the seq_region table.  | key: region_band_idx

| seq_region_start  | INT(10)  | -  | Sequence start position.  |

| seq_region_end  | INT(10)  | -  | Sequence end position.  |

| band  | VARCHAR(40)  | NULL  | Band.  | key: region_band_idx

| stain  | VARCHAR(40)  | NULL  | Stain.  |

|
See also:

- seq_region

|   |

## meta

Stores data about the data in the current schema. Taxonomy information, version information and the default value for the type column in the assembly table are stored here. Unlike other tables, data in the meta table is stored as key-value pairs. Also stores (via assembly.mapping keys) the relationships between co-ordinate systems in the assembly table. The species_id field of the meta table is used in multi-species databases and makes it possible to have species-specific meta key-value pairs. The species-specific meta key-value pairs needs to be repeated for each species_id. Entries in the meta table that are not specific to any one species, such as the schema_version key and any other schema-related information must have their species_id field set to NULL. The default species_id, and the only species_id value allowed in single-species databases, is 1.

| Column  | Type  | Default value  | Description  | Index

| meta_id  | INT  | -  | Primary key, internal identifier.  | primary key

| species_id  | INT  | 1  | Indentifies the species for multi-species databases.  | unique key: species_key_value_idx

key: species_value_idx

| meta_key  | VARCHAR(64)  | -  | Name of the meta entry, e.g. "schema_version".  | unique key: species_key_value_idx

| meta_value  | VARCHAR(255)  | -  | Corresponding value of the key, e.g. "61".  | unique key: species_key_value_idx

key: species_value_idx

|
See also:

- assembly

- coord_system

|   |

## seq_region

Stores information about sequence regions. The primary key is used as a pointer into the dna table so that actual sequence can be obtained, and the coord_system_id allows sequence regions of multiple types to be stored. Clones, contigs and chromosomes are all now stored in the seq_region table. Contigs are stored with the co-ordinate system 'contig'. The relationship between contigs and clones is stored in the assembly table. The relationships between contigs and chromosomes, and between contigs and supercontigs, are stored in the assembly table.

| Column  | Type  | Default value  | Description  | Index

| seq_region_id  | INT(10)  | -  | Primary key, internal identifier.  | primary key

| name  | VARCHAR(255)  | -  | Sequence region name.  | unique key: name_cs_idx

| coord_system_id  | INT(10)  | -  | Foreign key references to the coord_system table.  | unique key: name_cs_idx

key: cs_idx

| length  | INT(10)  | -  | Sequence length.  |

|
See also:

- dna

- coord_system

|   |

## seq_region_attrib

Allows "attributes" to be defined for certain seq_regions. Provides a way of storing extra information about particular seq_regions without adding extra columns to the seq_region table. e.g.

| Column  | Type  | Default value  | Description  | Index

| seq_region_id  | INT(10)  | '0'  | Foreign key references to the seq_region table.  | key: seq_region_idx

unique key: region_attribx

| attrib_type_id  | SMALLINT(5)  | '0'  | Foreign key references to the attrib_type table.  | key: type_val_idx

unique key: region_attribx

| value  | TEXT  | -  | Attribute value.  | key: type_val_idx

key: val_only_idx

unique key: region_attribx

|
See also:

- seq_region

- attrib_type

|   |

## seq_region_synonym

Allows for storing multiple names for sequence regions.

| Column  | Type  | Default value  | Description  | Index

| seq_region_synonym_id  | INT  | -  | Primary key, internal identifier.  | primary key

| seq_region_id  | INT(10)  | -  | Foreign key references to the seq_region table.  | unique key: syn_idx

key: seq_region_idx

| synonym  | VARCHAR(250)  | -  | Alternative name for sequence region.  | unique key: syn_idx

| external_db_id  | INT  | NULL  | Foreign key references to the external_db table.  |

|
See also:

- seq_region

- external_db

|   |

## external_db

Stores data about the external databases in which the objects described in the xref table are stored.

| Column  | Type  | Default value  | Description  | Index

| external_db_id  | INT  | -  | Primary key, internal identifier.  | primary key

| db_name  | VARCHAR(100)  | -  | Database name.  | unique key: db_name_db_release_idx

| db_release  | VARCHAR(255)  | NULL  | Database release.  | unique key: db_name_db_release_idx

| status  | ENUM:

- KNOWNXREF

- KNOWN

- XREF

- PRED

- ORTH

-  PSEUDO

| -  | Status, e.g. 'KNOWNXREF','KNOWN','XREF','PRED','ORTH','PSEUDO'.  |

| priority  | INT  | -  | Determines which one of the xrefs will be used as the gene name.  |

| db_display_name  | VARCHAR(255)  | NULL  | Database display name.  |

| type  | ENUM:

- ARRAY

-  ALT_TRANS

-  ALT_GENE

-  MISC

-  LIT

-  PRIMARY_DB_SYNONYM

-  ENSEMBL

| -  | Type, e.g. 'ARRAY', 'ALT_TRANS', 'ALT_GENE', 'MISC', 'LIT', 'PRIMARY_DB_SYNONYM', 'ENSEMBL'.  |

| secondary_db_name  | VARCHAR(255)  | NULL  | Secondary database name.  |

| secondary_db_table  | VARCHAR(255)  | NULL  | Secondary database table.  |

| description  | TEXT  | NULL  | Description.  |

|
See also:

- xref

- unmapped_object

- protein_align_feature

- dna_align_feature

|   |

## attrib_type

Provides codes, names and desctriptions of attribute types.

| Column  | Type  | Default value  | Description  | Index

| attrib_type_id  | SMALLINT(5)  | -  | Primary key, internal identifier.  | primary key

| code  | VARCHAR(20)  | ''  | Attribute code, e.g. 'GapExons'.  | unique key: code_idx

| name  | VARCHAR(255)  | ''  | Attribute name, e.g. 'gap exons'.  |

| description  | TEXT  | NULL  | Attribute description, e.g. 'number of gap exons'.  |

|
See also:

- seq_region_attrib

|   |
