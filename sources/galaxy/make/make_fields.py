"""Generate sources/galaxy/fields.json. Examples are filled from the example files via the adapter."""
import json
import os
import sys

TOOLS = sys.argv[1]
G = sys.argv[2]
sys.path.insert(0, TOOLS)
from refmeta.formats import galaxy  # noqa: E402

FMT = {f.id: f for f in galaxy.FORMATS}

LOC_SPEC = {
    "all_fasta": ["spec/galaxy/all_fasta.loc.sample", "spec/galaxy/tool_data_table_conf.xml.sample",
                  "spec/tools-iuc/data_manager_fetch_genome_dbkeys_all_fasta/tool-data/all_fasta.loc.sample"],
    "fasta_indexes": ["spec/tools-iuc/data_manager_sam_fasta_index_builder/tool-data/fasta_indexes.loc.sample",
                      "spec/tools-iuc/data_manager_sam_fasta_index_builder/tool_data_table_conf.xml.sample"],
    "bwa_mem_indexes": ["spec/tools-iuc/data_manager_bwa_mem_index_builder/tool-data/bwa_mem_index.loc.sample",
                        "spec/tools-iuc/data_manager_bwa_mem_index_builder/tool_data_table_conf.xml.sample"],
    "bowtie2_indexes": ["spec/tools-iuc/data_manager_bowtie2_index_builder/tool-data/bowtie2_indices.loc.sample",
                        "spec/tools-iuc/data_manager_bowtie2_index_builder/tool_data_table_conf.xml.sample"],
    "rnastar_index2x_versioned": ["spec/tools-iuc/data_manager_star_index_builder/tool-data/rnastar_index2x_versioned.loc.sample",
                                  "spec/tools-iuc/data_manager_star_index_builder/tool_data_table_conf.xml.sample"],
    "__dbkeys__": ["spec/tools-iuc/data_manager_fetch_genome_dbkeys_all_fasta/tool-data/dbkeys.loc.sample",
                   "spec/galaxy/dbkeys.loc.test",
                   "spec/tools-iuc/data_manager_fetch_genome_dbkeys_all_fasta/tool_data_table_conf.xml.sample"],
}
TDTC_CODE = "spec/galaxy/lib_galaxy_tool_util_data__init__.excerpt.py.txt"

formats = [
    dict(id="galaxy_builds_txt", description="builds.txt: the static list of genome builds (dbkeys) Galaxy offers in its dbkey picker. Two TAB-separated columns, no header.",
         media_type="text/tab-separated-values", extensions=[".txt"],
         spec_files=["spec/galaxy/builds.txt.sample", "spec/galaxy/manual_builds.txt.sample", "spec/galaxy/lib_galaxy_managers_dbkeys.py.txt"],
         example_files=["examples/builds.txt"], record_key="dbkey (not unique: a dbkey may repeat with another display_name)"),
    dict(id="galaxy_len", description=".len file: one line per sequence, name TAB length. The __dbkeys__ table points to it (len_path); /api/genomes/{id} reads it.",
         media_type="text/tab-separated-values", extensions=[".len"],
         spec_files=["spec/galaxy/lib_galaxy_visualization_genomes.py.txt", "spec/galaxy/dbkeys.loc.test"],
         example_files=["examples/constructed/sacCer3.len", "examples/constructed/hg38.len",
                        "examples/constructed/GCF_000146045.2.len", "examples/constructed/GCF_000001405.40.len"],
         record_key="chrom (unique within one file)"),
    dict(id="galaxy_api_genomes", description="GET /api/genomes on a Galaxy server: JSON array of [display name, dbkey] pairs for every known build.",
         media_type="application/json", extensions=[".json"],
         spec_files=["spec/galaxy/lib_galaxy_webapps_galaxy_api_genomes.py.txt", "spec/galaxy/lib_galaxy_managers_dbkeys.py.txt"],
         example_files=["examples/usegalaxy_org_api_genomes.excerpt.json"], record_key="[1] (dbkey; may repeat)"),
    dict(id="galaxy_api_genome", description="GET /api/genomes/{dbkey} on a Galaxy server: the build's sequence names and lengths (from its .len file).",
         media_type="application/json", extensions=[".json"],
         spec_files=["spec/galaxy/lib_galaxy_visualization_genomes.py.txt", "spec/galaxy/lib_galaxy_webapps_galaxy_api_genomes.py.txt"],
         example_files=["examples/usegalaxy_org_api_genomes_sacCer3.json", "examples/usegalaxy_org_api_genomes_hg38.json",
                        "examples/usegalaxy_org_api_genomes_GCF_000146045.2.json", "examples/usegalaxy_org_api_genomes_GCF_000001405.40.json"],
         record_key="id"),
    dict(id="galaxy_api_tool_data", description="GET /api/tool_data/{table} on a Galaxy server: one data table's column names and all its rows (merged from every .loc file). One native record per row.",
         media_type="application/json", extensions=[".json"],
         spec_files=["spec/galaxy/lib_galaxy_webapps_galaxy_api_tool_data.py.txt", "spec/galaxy/lib_galaxy_managers_tool_data.py.txt"],
         example_files=["examples/usegalaxy_org_api_tool_data_all_fasta.excerpt.json", "examples/usegalaxy_org_api_tool_data_fasta_indexes.excerpt.json",
                        "examples/usegalaxy_org_api_tool_data_bwa_mem_indexes.excerpt.json", "examples/usegalaxy_org_api_tool_data_bowtie2_indexes.excerpt.json",
                        "examples/usegalaxy_org_api_tool_data_rnastar_index2x_versioned.excerpt.json", "examples/usegalaxy_org_api_tool_data___dbkeys__.excerpt.json",
                        "examples/usegalaxy_eu_api_tool_data_all_fasta.excerpt.json", "examples/usegalaxy_eu_api_tool_data___dbkeys__.excerpt.json"],
         record_key="name + fields[].value (value is meant to be unique per table, but duplicates are served)"),
    dict(id="galaxy_tool_data_table_conf", description="tool_data_table_conf.xml: declares each data table (name, column names, comment character, the .loc files or refgenie config that fill it). One native record per <table>.",
         media_type="application/xml", extensions=[".xml"],
         spec_files=["spec/galaxy/tool_data_table_conf.xml.sample", TDTC_CODE, "spec/galaxy/lib_galaxy_tools_data__init__.py.txt"],
         example_files=["examples/galaxy_tool_data_table_conf.xml.sample", "examples/idc_tool_data_table_conf.xml"],
         record_key="name (the same name may appear in several conf files; Galaxy merges them if the columns match)"),
]
LOC_EX = {"all_fasta": "cvmfs_all_fasta.loc", "fasta_indexes": "cvmfs_fasta_indexes.loc", "bwa_mem_indexes": "cvmfs_bwa_mem_index.loc",
          "bowtie2_indexes": "cvmfs_bowtie2_indices.loc", "rnastar_index2x_versioned": "cvmfs_rnastar_index2x_versioned.loc",
          "__dbkeys__": "cvmfs_dbkeys.loc"}
for fid, table, cols, _tok, desc in galaxy._LOC_TABLES:
    formats.append(dict(id=fid, description=desc + " TAB-separated, '#' comments, no header; column names come from tool_data_table_conf.xml: " + ", ".join(cols) + ".",
                        media_type="text/tab-separated-values", extensions=[".loc"],
                        spec_files=LOC_SPEC[table] + [TDTC_CODE], example_files=["examples/" + LOC_EX[table]],
                        record_key="value (unique_build_id) within this table on one server"))
formats += [
    dict(id="galaxy_data_manager_json", description="Data manager output JSON: what a data manager tool writes so Galaxy can add rows to data tables. Paths are relative here; data_manager_conf.xml moves the files and rewrites them to absolute paths. One native record per entry.",
         media_type="application/json", extensions=[".json", ".data_manager_json"],
         spec_files=["spec/tools-iuc/data_manager_fetch_genome_dbkeys_all_fasta/data_manager_conf.xml",
                     "spec/tools-iuc/data_manager_fetch_genome_dbkeys_all_fasta/data_manager/data_manager_fetch_genome_all_fasta_dbkeys.py.txt",
                     "spec/tools-iuc/data_manager_sam_fasta_index_builder/data_manager_conf.xml",
                     "spec/tools-iuc/data_manager_bwa_mem_index_builder/data_manager_conf.xml",
                     "spec/tools-iuc/data_manager_bowtie2_index_builder/data_manager_conf.xml",
                     "spec/tools-iuc/data_manager_star_index_builder/data_manager_conf.xml"],
         example_files=["examples/constructed/dm_fetch_genome_all_fasta_hg38canon.data_manager_json",
                        "examples/constructed/dm_fetch_genome_all_fasta_sacCer3.data_manager_json",
                        "examples/dm_fetch_genome_all_fasta_phiX174.data_manager_json", "examples/dm_fetch_genome_all_fasta_phiX174Variant1.data_manager_json",
                        "examples/dm_sam_fasta_index_phiX174.json", "examples/dm_bwa_mem_index_phiX174.json",
                        "examples/dm_bowtie2_index_phiX174.json", "examples/dm_rnastar_index_phiX174.data_manager_json"],
         record_key="data_table + value"),
    dict(id="galaxy_refgenie_table", description="RefgenieToolDataTable (lib/galaxy/tools/data/__init__.py): a data table with type=\"refgenie\" is filled from a refgenie config instead of a .loc file. Each <field> is a Cheetah template over these variables. Prose/code only: there is no file of these records.",
         media_type="text/x-python", extensions=[],
         spec_files=["spec/galaxy/lib_galaxy_tools_data__init__.py.txt", "spec/galaxy/tool_data_table_conf.xml.sample",
                     "spec/galaxy/test_unit_app_tools_test_refgenie_data_table.py.txt", "spec/galaxy/test_integration_refgenie.yml"],
         example_files=[], record_key="__REFGENIE_UUID__ (refgenie:<genome>/<asset>:<tag>@<digest>)", adapter=False),
    dict(id="galaxy_idc_genomes", description="IDC genomes.yml (older pipeline): genomes to fetch and the indexers to run. cvmfs_current_managed/cvmfs_managed_genomes.yml uses the same entries inside a list of {genomes: [...]} blocks.",
         media_type="application/yaml", extensions=[".yml", ".yaml"],
         spec_files=["spec/idc/README.md", "spec/idc/genomes.yml", "spec/idc/cvmfs_current_managed/cvmfs_managed_genomes.yml", "spec/idc/docs/genome-indexing.md"],
         example_files=["examples/idc_genomes_sacCer3.excerpt.yml", "examples/idc_cvmfs_managed_genomes_hg38_sacCer3.excerpt.yml"],
         record_key="id"),
    dict(id="galaxy_idc_data_managers", description="IDC data_managers.yml (older pipeline): data manager short name to Tool Shed tool id, tags that genomes.yml indexers refer to, and fixed parameters.",
         media_type="application/yaml", extensions=[".yml", ".yaml"],
         spec_files=["spec/idc/README.md", "spec/idc/data_managers.yml", "spec/idc/cvmfs_current_managed/cvmfs_data_managers.yml", "spec/idc/schemas/data_managers.yml"],
         example_files=["examples/idc_data_managers.yml"], record_key="data_manager"),
    dict(id="galaxy_idc_request", description="IDC request file data-managers/<data_table>/<version>.yaml (current pipeline): one data manager run that builds one data table entry. Validated by schemas/request.schema.json.",
         media_type="application/yaml", extensions=[".yml", ".yaml"],
         spec_files=["spec/idc/schemas/request.schema.excerpt.json", "spec/idc/docs/requesting-reference-data.md", "spec/idc/docs/genome-indexing.md", "spec/idc/schemas/data_managers.yml"],
         example_files=["examples/idc_request_all_fasta_hg38canon.yaml", "examples/idc_request_fasta_indexes_hg38canon.yaml",
                        "examples/idc_request_rnastar_index2x_versioned_hg38canon.yaml", "examples/constructed/idc_request_all_fasta_sacCer3.yaml",
                        "examples/constructed/idc_request_all_fasta_GCF_000001405.40.from_docs.yaml"],
         record_key="file path data-managers/<data_table>/<version>.yaml (not inside the file)"),
    dict(id="galaxy_idc_all_tables", description="IDC PR #88 all_tables YAML (sync/tool_data_table_conf_to_yaml.py): every row of every data table on a server, keyed by table, with the .loc and conf file it came from. One native record per row.",
         media_type="application/yaml", extensions=[".yml", ".yaml"],
         spec_files=["spec/idc_pr88/sync/README.md", "spec/idc_pr88/sync/tool_data_table_conf_to_yaml.py.txt"],
         example_files=["examples/idc_pr88_cvmfs_20260715_all_tables.excerpt.yml"], record_key="table + value + loc_file"),
    dict(id="galaxy_idc_refget_json", description="IDC PR #88 json/<unique_build_id>.json (sync/all_fasta_files_to_refget_store.py): seqcol level 0/1/2 digests of one all_fasta FASTA plus its Galaxy aliases.",
         media_type="application/json", extensions=[".json"],
         spec_files=["spec/idc_pr88/sync/README.md", "spec/idc_pr88/sync/all_fasta_files_to_refget_store.py.txt"],
         example_files=["examples/constructed/idc_pr88_json_hg38canon.json", "examples/constructed/idc_pr88_json_sacCer3.json",
                        "examples/idc_pr88_test_dig_json_phiX174.json"],
         record_key="level_0 (seqcol digest) or aliases.galaxy_unique_build_id"),
    dict(id="galaxy_idc_refget_yaml", description="IDC PR #88 yaml/all_fasta.yml: the same digests for every processed FASTA in one file, keyed by unique_build_id, with a peek at the first sequence instead of the full level 2 arrays.",
         media_type="application/yaml", extensions=[".yml", ".yaml"],
         spec_files=["spec/idc_pr88/sync/README.md", "spec/idc_pr88/sync/all_fasta_files_to_refget_store.py.txt"],
         example_files=["examples/constructed/idc_pr88_yaml_all_fasta.yml", "examples/idc_pr88_test_dig_yaml_all_fasta.yml"],
         record_key="unique_build_id (the YAML mapping key)"),
]
for f in formats:
    f.setdefault("adapter", True)

S, I, N, B, A, O, D, U = "string", "integer", "number", "boolean", "array", "object", "date", "uri"


def F(fmt, path, typ, desc, level, card="one", req=True, uniq="none", notes=""):
    return dict(format=fmt, path=path, type=typ, description=desc, level=level, cardinality=card,
                required=req, unique=uniq, notes=notes)


DUP_NOTE = ("Meant to be unique within a data table on one server (tools store it in workflows), but not enforced: "
            "usegalaxy.org serves all_fasta 'hg38canon' twice and usegalaxy.eu serves 'hg38canon' twice with different names. "
            "Index tables usually reuse the all_fasta value, but not always (all_fasta 'hg38' points to hg38.fa while bwa_mem and bowtie2 'hg38' point to hg38full).")
DBKEY_NOTE = ("Build key: groups several entries (e.g. hg38, hg38canon, hg38female all have dbkey hg38). Not unique. "
              "Galaxy uses it to mark datasets as compatible and to link to UCSC. Mostly UCSC database names; newer BRC/VGP entries use RefSeq/GenBank assembly accessions (GCF_000001405.40).")
NAME_NOTE = ("Free-text display label. Often embeds species, assembly name and a subset hint ('Canonical', 'Female', 'full'), "
             "but is not parsed by Galaxy and differs between servers for the same value.")
fields = []

# builds.txt
fields += [
    F("galaxy_builds_txt", "dbkey", S, "Build key (first column). Stored on every dataset as its 'dbkey'.", "deployment", uniq="namespace",
      notes="Not a header name: the file has no header; name taken from Galaxy's dbkeys.loc sample header '<dbkey>'. read_dbnames() treats an all-digit dbkey as a 'manual' (microbial) build and '?' as 'unspecified'. Lines starting with '#' are skipped."),
    F("galaxy_builds_txt", "display_name", S, "Label shown in the build picker (second column).", "deployment",
      notes="UCSC-harvested labels follow 'Species Mon. YYYY (AssemblyName/dbkey) (dbkey)', e.g. 'Human Dec. 2013 (GRCh38/hg38) (hg38)'; this is the only place builds.txt carries the assembly name. Columns after the second are ignored (manual_builds.txt.sample has a third column of name=length pairs)."),
]
# .len
fields += [
    F("galaxy_len", "chrom", S, "Sequence name.", "sequence", uniq="namespace",
      notes="Unique within one .len file. Naming follows the build: UCSC style for UCSC dbkeys (chr1, chr1_KI270706v1_random); RefSeq accessions for the BRC GCF_000146045.2 (NC_001133.9). The BRC GCF_000001405.40 .len uses UCSC-style names (455 sequences), unlike its accession."),
    F("galaxy_len", "len", I, "Sequence length in bases.", "sequence"),
]
# /api/genomes
fields += [
    F("galaxy_api_genomes", "[0]", S, "Display name of the build (first item of each pair).", "deployment",
      notes="Same text as builds.txt display_name or the __dbkeys__ name. Custom user builds get ' [Custom]' and history .len datasets get ' [History]' appended."),
    F("galaxy_api_genomes", "[1]", S, "dbkey (second item of each pair).", "deployment", uniq="none",
      notes="The list merges builds.txt, the __dbkeys__ table, user custom builds and history .len files, so a dbkey can appear more than once. The first pair is always ['unspecified (?)', '?']."),
]
# /api/genomes/{id}
fields += [
    F("galaxy_api_genome", "id", S, "The dbkey asked for.", "deployment", uniq="namespace"),
    F("galaxy_api_genome", "reference", B, "True when the server has reference sequence for this dbkey (a twobit table entry), so sequence can be served.", "deployment"),
    F("galaxy_api_genome", "chrom_info", A, "Sequence names and lengths: array of {chrom, len} read from the dbkey's .len file.", "collection",
      notes="Sorted by Galaxy with a natural sort on the name (split_by_number), NOT in .len or FASTA order, so it cannot give seqcol 'names' order. Paged with query parameters num/chrom/low; the whole list comes back when num is not given. The .len may not match any one FASTA under the same dbkey (hg38 .len lists 711 sequences incl. patches; hg38canon has 25)."),
    F("galaxy_api_genome", "prev_chroms", B, "Paging flag: sequences exist before this page.", "other", notes="Paging only."),
    F("galaxy_api_genome", "next_chroms", B, "Paging flag: sequences exist after this page.", "other", notes="Paging only."),
    F("galaxy_api_genome", "start_index", I, "Paging: line index in the .len file where this page starts.", "other", notes="Paging only."),
]
# /api/tool_data/{table}
fields += [
    F("galaxy_api_tool_data", "name", S, "Data table name (e.g. all_fasta, __dbkeys__).", "deployment", uniq="namespace",
      notes="Top-level key of the response, repeated on every native record. Do not confuse with fields[].name (the row's display name)."),
    F("galaxy_api_tool_data", "model_class", S, "Python class of the table (TabularToolDataTable, RefgenieToolDataTable).", "deployment"),
    F("galaxy_api_tool_data", "columns", A, "Column names of the table, in order; each row in 'fields' is a list in this order.", "deployment"),
    F("galaxy_api_tool_data", "fields[].value", S, "Row's unique_build_id (column 'value').", "deployment", uniq="namespace", notes=DUP_NOTE),
    F("galaxy_api_tool_data", "fields[].dbkey", S, "Row's dbkey (column 'dbkey'; absent in __dbkeys__, where value is the dbkey).", "deployment", req=False, notes=DBKEY_NOTE),
    F("galaxy_api_tool_data", "fields[].name", S, "Row's display name (column 'name').", "deployment", notes=NAME_NOTE),
    F("galaxy_api_tool_data", "fields[].path", S, "Row's file path (column 'path'), cut to the file name for non-admin callers.", "copy", req=False,
      notes="Galaxy strips the directory of the column named 'path' for non-admins (managers/tool_data.py), so this is 'hg38canon.fa', not the CVMFS path. For index tables it is the index file prefix or directory, not a FASTA."),
    F("galaxy_api_tool_data", "fields[].len_path", S, "__dbkeys__ only: path of the .len file.", "copy", req=False,
      notes="Not stripped (only a column literally named 'path' is), so the full server path shows."),
    F("galaxy_api_tool_data", "fields[].with_gene_model", S, "rnastar_index2x_versioned only: '1' if the index was built with a GTF, else '0'.", "other", req=False),
    F("galaxy_api_tool_data", "fields[].version", S, "rnastar_index2x_versioned only: oldest STAR version that can read the index.", "other", req=False),
]
# tool_data_table_conf.xml
fields += [
    F("galaxy_tool_data_table_conf", "name", S, "Data table name (<table name=...>). Tools refer to tables by this name.", "deployment", uniq="namespace",
      notes="Several conf files (Galaxy's own, the shed conf, CVMFS byhand/managed/brc/vgp) may each declare the same table; Galaxy merges them if the columns are identical."),
    F("galaxy_tool_data_table_conf", "comment_char", S, "Lines whose first non-blank character is this are skipped in the .loc files. Default '#'.", "deployment", req=False),
    F("galaxy_tool_data_table_conf", "allow_duplicate_entries", S, "'False' makes Galaxy drop rows that exactly repeat another row. Default true.", "deployment", req=False,
      notes="String in XML; Galaxy reads it with asbool. It removes exact duplicate rows only; two rows with the same value but different names both stay."),
    F("galaxy_tool_data_table_conf", "type", S, "Table type: 'tabular' (default, .loc files) or 'refgenie' (filled from a refgenie config).", "deployment", req=False),
    F("galaxy_tool_data_table_conf", "asset", S, "type=refgenie only: refgenie asset whose entries fill the table (fasta, bowtie2_index, ...).", "deployment", req=False),
    F("galaxy_tool_data_table_conf", "separator", S, "Field separator in the .loc files. Default TAB.", "deployment", req=False, notes="Not used by any table in the collected files."),
    F("galaxy_tool_data_table_conf", "empty_field_value", S, "Value written for missing fields. Default ''.", "deployment", req=False, notes="Not used by any table in the collected files."),
    F("galaxy_tool_data_table_conf", "user_accessible", S, "'true' lets user-defined tools read the table.", "deployment", req=False,
      notes="Only mentioned in a comment of the Galaxy sample; no table in the collected files sets it."),
    F("galaxy_tool_data_table_conf", "columns", A, "Column names in file order (<columns>value, dbkey, name, path</columns>, split on commas).", "deployment", req=False,
      notes="A column named 'value' is required. The .loc files themselves carry no column names; this is the only place they are declared."),
    F("galaxy_tool_data_table_conf", "column", A, "Alternative to <columns>: list of <column name= index= [empty_field_value=]/> attributes.", "deployment", req=False,
      notes="Not used in the collected files."),
    F("galaxy_tool_data_table_conf", "file", A, "List of <file> attributes: path (a .loc file, relative to tool_data_path, may use ${__HERE__}), url (fetched at start-up), or from_config (name of a Galaxy config option, e.g. refgenie_config_file).", "deployment", card="many"),
    F("galaxy_tool_data_table_conf", "field", A, "type=refgenie only: list of <field name= template= [strip=] [column_index=]> with the template text as 'text'.", "deployment", req=False,
      notes="Templates use the variables of format galaxy_refgenie_table, e.g. ${__REFGENIE_UUID__}."),
]
# .loc formats
for fid, table, cols, _tok, _desc in galaxy._LOC_TABLES:
    if table == "__dbkeys__":
        fields += [
            F(fid, "value", S, "dbkey being defined (column 1).", "deployment", uniq="namespace",
              notes="In this table value IS the dbkey; there is no dbkey column. Several .loc files fill it (CVMFS managed dbkeys.loc and dbkeys_ucsc.loc, brc, vgp), so one dbkey can be listed by more than one file."),
            F(fid, "name", S, "Display name of the dbkey (column 2).", "deployment",
              notes="UCSC-derived entries copy the builds.txt label ('Human Dec. 2013 (GRCh38/hg38) (hg38)'); RefSeq-based entries look like 'Homo sapiens (GCF_000001405.40)'."),
            F(fid, "len_path", S, "Absolute path of the .len chromosome-length file (column 3).", "copy",
              notes="Defines the coordinate system Galaxy shows for the dbkey. The data manager writes it under genomes/<dbkey>/len/. Can contain ${__HERE__}."),
        ]
        continue
    what = {"all_fasta": "the FASTA file", "fasta_indexes": "the FASTA file next to its .fai (tools add .fai)",
            "bwa_mem_indexes": "the BWA index prefix (a .fa name; .amb/.ann/.bwt/... files share it)",
            "bowtie2_indexes": "the Bowtie2 index basename (files <path>.1.bt2 ...)",
            "rnastar_index2x_versioned": "the STAR index directory"}[table]
    fields += [
        F(fid, "value", S, "unique_build_id: the identifier tools store in workflows and jobs (column 1).", "deployment", uniq="namespace", notes=DUP_NOTE),
        F(fid, "dbkey", S, "Build key this entry belongs to (column 2).", "deployment", notes=DBKEY_NOTE),
        F(fid, "name", S, "Display name shown in tool forms (column 3).", "deployment", notes=NAME_NOTE),
        F(fid, "path", S, f"Absolute path of {what} (column 4).", "copy", uniq="namespace",
          notes="Server-specific (CVMFS paths here). Data managers write genomes/<dbkey>/<index_type>/<version>/<value>/...; older byhand entries use other layouts. Can contain ${__HERE__}."
          + (" This is the copy of the sequence collection; the only Galaxy field that points at actual sequence." if table == "all_fasta" else " Points at a derived index, not a FASTA; which FASTA it was built from is not recorded.")),
    ]
    if table == "rnastar_index2x_versioned":
        fields += [
            F(fid, "with_gene_model", S, "'1' if built with annotations (--sjdbGTFfile), '0' if not (column 5).", "other", notes="Index build parameter."),
            F(fid, "version", S, "STAR version that introduced this index format, i.e. the oldest STAR that can use it (column 6).", "other", notes="Index build parameter, e.g. 2.7.4a."),
        ]
# data manager JSON
fields += [
    F("galaxy_data_manager_json", "data_table", S, "Data table the entry is for: the key under 'data_tables'.", "deployment",
      notes="Not a literal key inside the entry; the enclosing object key. One output can fill several tables (fetch genome writes all_fasta and __dbkeys__)."),
    F("galaxy_data_manager_json", "value", S, "unique_build_id of the new entry (all_fasta: the sequence_id parameter).", "deployment", uniq="namespace",
      notes="Index data managers default it to the input FASTA's value or dbkey depending on tool version (sam_fasta_index_builder 1.21+galaxy0 defaults to the dbkey), so it can silently differ from the all_fasta value."),
    F("galaxy_data_manager_json", "dbkey", S, "Build key. Present even in __dbkeys__ entries, where the table has no dbkey column (used only for the target path).", "deployment", notes=DBKEY_NOTE),
    F("galaxy_data_manager_json", "name", S, "Display name.", "deployment", notes=NAME_NOTE),
    F("galaxy_data_manager_json", "path", S, "File name or relative path inside the job's output directory.", "copy", req=False,
      notes="Relative here; data_manager_conf.xml moves it to ${GALAXY_DATA_MANAGER_DATA_PATH}/genomes/${dbkey}/seq/${path} (all_fasta) or genomes/${dbkey}/<index>/<v>/${value}/ and writes that absolute path into the .loc."),
    F("galaxy_data_manager_json", "len_path", S, "__dbkeys__ entries: .len file name, later moved to genomes/${dbkey}/len/.", "copy", req=False),
    F("galaxy_data_manager_json", "with_gene_model", S, "rnastar entries: '1' if built with a GTF, else '0'.", "other", req=False),
    F("galaxy_data_manager_json", "version", S, "rnastar entries: STAR index format version.", "other", req=False),
]
# refgenie (prose)
RG = "galaxy_refgenie_table"
fields += [
    F(RG, "__REFGENIE_UUID__", S, "Identifier Galaxy builds for one refgenie asset: refgenie:<genome>/<asset>:<tag>@<digest>. The sample conf puts it in column 'value'.", "deployment", uniq="global",
      notes="Pattern from code: f\"refgenie:{genome}/{self.rg_asset}:{tag}@{digest}\". No real record collected."),
    F(RG, "__REFGENIE_GENOME__", S, "refgenie genome name (alias), e.g. hg38. The sample conf puts it in 'dbkey' (and in __dbkeys__ 'value').", "deployment", notes="No real record collected."),
    F(RG, "__REFGENIE_TAG__", S, "refgenie asset tag (e.g. default).", "other", notes="No real record collected."),
    F(RG, "__REFGENIE_DISPLAY_NAME__", S, "'<genome_description> (refgenie: <genome>@<digest>)' when the genome has a description, else '<genome>/<asset>:<tag>@<digest>'. Goes in 'name'.", "deployment", notes="No real record collected."),
    F(RG, "__REFGENIE_ASSET__", S, "Local path of the asset (rgc.seek(genome, asset, tag)). Goes in 'path'.", "copy", notes="No real record collected."),
    F(RG, "__REFGENIE_ASSET_NAME__", S, "Asset name (the table's asset= attribute, e.g. fasta).", "other", notes="No real record collected."),
    F(RG, "__REFGENIE_DIGEST__", S, "refgenie asset digest: rgc.id(genome, asset, tag).", "other", uniq="global",
      notes="A refgenie asset digest, not a seqcol or refget digest. No real record collected."),
    F(RG, "__REFGENIE_GENOME_ATTRIBUTES__", O, "All genome attributes from the refgenie config (includes genome_description).", "other", notes="No real record collected."),
    F(RG, "__REFGENIE_SEEK_KEY__", S, "Function: __REFGENIE_SEEK_KEY__('chrom_sizes') returns the path of another seek key of the same asset; the sample conf uses it for __dbkeys__ len_path.", "copy", notes="A callable, not a value. No real record collected."),
]
# IDC genomes.yml
GN = "galaxy_idc_genomes"
fields += [
    F(GN, "dbkey", S, "dbkey of the data.", "deployment", notes=DBKEY_NOTE),
    F(GN, "description", S, "Description incl. taxonomy, version and date (README); becomes the display name.", "deployment", req=False,
      notes="Empty with comment '# set from UCSC' for UCSC genomes in genomes.yml."),
    F(GN, "id", S, "Unique id of the data in Galaxy (becomes the all_fasta value / unique_build_id).", "deployment", uniq="namespace"),
    F(GN, "source", S, "Where to fetch the FASTA: 'ucsc', an NCBI accession, or a URL.", "other", req=False,
      notes="Mixed kinds: 'ucsc' means fetch by dbkey from UCSC; NC_021902 is a single-sequence accession, not an assembly accession; URLs are copies."),
    F(GN, "doi", S, "Any DOI for the data.", "other", req=False, notes="Empty in every entry collected."),
    F(GN, "version", S, "Any version information for the data.", "other", req=False, notes="Empty in every entry collected."),
    F(GN, "checksum", S, "SHA256 of the original downloaded file.", "copy", req=False, notes="Empty for UCSC entries; set for URL/accession entries in genomes.yml."),
    F(GN, "blob", S, "Free text for other information.", "other", req=False),
    F(GN, "indexers", A, "Data managers (or tags) to run on this genome.", "deployment", card="many", req=False),
    F(GN, "skiplist", A, "Data manager tags not to run.", "deployment", card="many", req=False),
]
# IDC data_managers.yml
DM = "galaxy_idc_data_managers"
fields += [
    F(DM, "data_manager", S, "Short name of the data manager (the YAML mapping key), e.g. data_manager_bwa_mem_index_builder.", "deployment", uniq="namespace",
      notes="Mapping key, not a literal field. genomes.yml 'indexers' lists these names."),
    F(DM, "tool_id", S, "Tool Shed GUID of the data manager tool incl. version.", "deployment"),
    F(DM, "tags", A, "Tags (genome, fetch_source, ...) used to select data managers.", "deployment", card="many"),
    F(DM, "parameters", O, "Fixed tool parameters for every run; may contain Jinja like '{{ item.id }}'.", "deployment", req=False),
]
# IDC request
RQ = "galaxy_idc_request"
fields += [
    F(RQ, "tool_id", S, "Version-pinned Tool Shed GUID of the data manager.", "deployment", notes="Pattern toolshed.g2.bx.psu.edu/repos/<owner>/<repo>/<tool id>/<version>."),
    F(RQ, "data_tables", A, "Data tables the data manager writes; the request's directory must be one of them.", "deployment", card="many"),
    F(RQ, "params.dbkey_source.dbkey_source_selector", S, "'existing' (dbkey already defined) or 'new' (also write a __dbkeys__ entry).", "deployment", req=False),
    F(RQ, "params.dbkey_source.dbkey", S, "dbkey the new FASTA belongs to.", "deployment", req=False, notes=DBKEY_NOTE),
    F(RQ, "params.dbkey_source.dbkey_name", S, "Display name for a new dbkey.", "deployment", req=False, notes="Only with dbkey_source_selector: new."),
    F(RQ, "params.reference_source.reference_source_selector", S, "Where to fetch the sequence: ucsc, ncbi, url, (history, directory).", "other", req=False,
      notes="Provenance of the copy. Example comment in the docs lists ucsc, ncbi, url."),
    F(RQ, "params.reference_source.requested_dbkey", S, "UCSC genome database to download (ucsc source).", "assembly", req=False,
      notes="A UCSC database name (hg38). The data manager fetches <db>.chromFa.tar.gz (or similar) from hgdownload; it says which UCSC release, i.e. assembly plus UCSC naming."),
    F(RQ, "params.reference_source.requested_identifier", S, "NCBI identifier to download (ncbi source).", "assembly", req=False,
      notes="An assembly accession in the IDC docs example (GCF_000001405.40)."),
    F(RQ, "params.sequence_id", S, "unique_build_id to write (all_fasta value; also used by index builders to set their output value).", "deployment", req=False, uniq="namespace",
      notes="Leaving it empty lets the tool pick a default (dbkey or input value) - a known source of mismatched values."),
    F(RQ, "params.sequence_name", S, "Display name to write.", "deployment", req=False, notes=NAME_NOTE),
    F(RQ, "params.sorting.sort_selector", S, "How to order sequences: as_is, lexicographical, gatk, custom.", "collection", req=False,
      notes="Changes sequence order and therefore the seqcol digest of the written FASTA."),
    F(RQ, "params.sorting.sequence_identifiers", A, "custom sort: ordered list of {identifier: <sequence name>}.", "collection", card="many", req=False,
      notes="With handle_not_listed_selector: discard this also chooses WHICH sequences are kept, i.e. defines the collection (hg38canon = chr1-22, X, Y, M)."),
    F(RQ, "params.sorting.handle_not_listed_selector", S, "custom sort: what to do with sequences not listed (discard, keep_append, keep_prepend).", "collection", req=False),
    F(RQ, "sha256", O, "Expected SHA-256 per file name, as Galaxy lists the entry's files.", "copy", req=False,
      notes="Map {file name: sha256}. File-level checksum of the copy; depends on line width and header text, unlike a seqcol digest. Verified for hg38canon.fa: rebuilding from UCSC hg38.chromFa.tar.gz gives this exact sha256."),
    F(RQ, "description", S, "What the data is, for reviewers.", "other", req=False),
    F(RQ, "doi", S, "DOI of the publication or dataset the data comes from.", "other", req=False, notes="In the schema; not set in any collected request."),
    F(RQ, "depends_on.all_fasta", S, "For index builds: the all_fasta request (file stem = value) this build uses as input.", "deployment", req=False,
      notes="Wires the input only; does not set the output value (docs/genome-indexing.md). Other upstream tables appear as depends_on.<table>."),
]
# all_tables
AT = "galaxy_idc_all_tables"
fields += [
    F(AT, "table", S, "Data table name (the YAML key the row is listed under).", "deployment", notes="Enclosing key, not a literal field."),
    F(AT, "value", S, "Row's value column (unique_build_id; in __dbkeys__ the dbkey; in twobit the dbkey).", "deployment", uniq="namespace", notes=DUP_NOTE),
    F(AT, "dbkey", S, "Row's dbkey column (absent for __dbkeys__, twobit, sam_fa_indexes).", "deployment", req=False, notes=DBKEY_NOTE),
    F(AT, "name", S, "Row's name column.", "deployment", req=False, notes=NAME_NOTE),
    F(AT, "path", S, "Row's path column (full server path).", "copy", req=False, notes="Unlike the public API, full paths."),
    F(AT, "len_path", S, "__dbkeys__ rows: .len file path.", "copy", req=False),
    F(AT, "with_gene_model", S, "rnastar rows: '1' or '0'.", "other", req=False),
    F(AT, "version", S, "rnastar rows: STAR index version.", "other", req=False),
    F(AT, "line_type", S, "sam_fa_indexes rows: always 'index' in practice.", "other", req=False, notes="Legacy table used by htseq_count and bamtools (PR #88 README)."),
    F(AT, "loc_file", S, "The .loc file this row was read from (added by the script).", "deployment",
      notes="Shows which repository serves the row (byhand, managed, brc, vgp on CVMFS)."),
    F(AT, "xml_file", S, "The tool_data_table_conf.xml that declared the .loc file (added by the script).", "deployment"),
]
# refget json / yaml
L1 = {
    "names": "digest of the names array",
    "lengths": "digest of the lengths array",
    "sequences": "digest of the sequences array (SQ.-prefixed refget digests)",
    "name_length_pairs": "digest of the array of {length, name} objects",
    "sorted_name_length_pairs": "digest of the sorted array of digests of each {length, name} pair (order-free coordinate system id)",
    "sorted_sequences": "digest of the sorted sequences array (order-free content id)",
}
ALIAS = {
    "galaxy_unique_build_id": ("all_fasta value of the FASTA.", "namespace"),
    "galaxy_dbkey": ("all_fasta dbkey.", "none"),
    "galaxy_name": ("all_fasta display name.", "none"),
    "galaxy_loc_file": ("The .loc file the row came from.", "none"),
    "galaxy_tool_data_table_conf": ("The tool_data_table_conf.xml that declared the .loc.", "none"),
}
ALIAS_NOTE = "Every '/' is replaced by '!' so the value can sit in a seqcol API URL; this also changes display names (e.g. 'Amel_4.5!apiMel4')."
for fid in ("galaxy_idc_refget_json", "galaxy_idc_refget_yaml"):
    if fid == "galaxy_idc_refget_yaml":
        fields.append(F(fid, "unique_build_id", S, "all_fasta value of the FASTA (the YAML mapping key).", "deployment", uniq="namespace",
                        notes="Mapping key, not a literal field. Equals aliases.galaxy_unique_build_id; a repeated value overwrites the earlier entry."))
    fields.append(F(fid, "level_0", S, "seqcol top-level digest of the FASTA's sequence collection (gtars RefgetStore).", "collection", uniq="global",
                    notes="Computed from names and sequences only (lengths are not inherent in the current seqcol schema): checked by recomputing phiX174. Same FASTA content and order give the same digest on any server."))
    for k, d in L1.items():
        fields.append(F(fid, f"level_1.{k}", S, f"seqcol level 1: {d}.", "collection", uniq="global"))
    if fid == "galaxy_idc_refget_json":
        fields += [
            F(fid, "level_2.names", A, "Sequence names in FASTA order (first word of each header).", "sequence", card="many"),
            F(fid, "level_2.lengths", A, "Sequence lengths, same order.", "sequence", card="many"),
            F(fid, "level_2.sequences", A, "GA4GH refget sequence digests ('SQ.' + sha512t24u of the uppercased sequence), same order.", "sequence", card="many", uniq="global"),
        ]
    else:
        fields += [
            F(fid, "level_2_peek.sequence_count", I, "Number of sequences.", "collection"),
            F(fid, "level_2_peek.first_name", S, "Name of the first sequence.", "sequence"),
            F(fid, "level_2_peek.first_length", I, "Length of the first sequence.", "sequence"),
            F(fid, "level_2_peek.first_sequence", S, "refget digest of the first sequence.", "sequence", uniq="global"),
        ]
    for k, (d, u) in ALIAS.items():
        fields.append(F(fid, f"aliases.{k}", S, f"RefgetStore collection alias in namespace '{k}': {d}", "deployment", uniq=u, notes=ALIAS_NOTE))

# ---------- fill examples from files ----------
ANCHOR = ("hg38", "sacCer3", "GCF_000001405", "GCF_000146045")


def pick(fid, path, files):
    best = None
    for rel in files:
        recs = FMT[fid].read(open(os.path.join(G, rel)).read())
        for r in recs:
            if path not in r or r[path] in (None, "", [], {}):
                continue
            v = r[path]
            anchor = any(a in json.dumps(r) for a in ANCHOR)
            size = len(json.dumps(v))
            key = (0 if anchor else 1, size if isinstance(v, (list, dict)) else 0)
            if isinstance(v, (list, dict)):
                key = (0 if size < 3000 else 1, size)
            if best is None or key < best[0]:
                best = (key, v)
    return None if best is None else best[1]


fmt_by_id = {f["id"]: f for f in formats}
for fl in fields:
    spec = fmt_by_id[fl["format"]]
    if spec["adapter"]:
        fl["example"] = pick(fl["format"], fl["path"], spec["example_files"])
        if fl["example"] is None:  # fall back to real files kept under spec/
            readable = [x for x in spec["spec_files"] if FMT[fl["format"]].detect(open(os.path.join(G, x)).read(), x) >= 0.5]
            fl["example"] = pick(fl["format"], fl["path"], readable)
            if fl["example"] is not None:
                fl["notes"] = (fl["notes"] + " " if fl["notes"] else "") + "Example taken from a file under spec/ (" + ", ".join(readable) + ")."
    else:
        fl["example"] = None
# order keys as in the contract
order = ["format", "path", "type", "description", "example", "level", "cardinality", "required", "unique", "notes"]
fields = [{k: fl[k] for k in order} for fl in fields]
fmt_order = ["id", "description", "media_type", "extensions", "spec_files", "example_files", "record_key", "adapter"]
formats = [{k: f[k] for k in fmt_order} for f in formats]
doc = {"source": "galaxy", "title": "Galaxy reference data (builds, data tables, .loc files, data managers, IDC)",
       "maintainer": "Galaxy Project (galaxyproject/galaxy), the IUC (galaxyproject/tools-iuc data managers) and the Intergalactic Data Commission (galaxyproject/idc)",
       "retrieved": "2026-11-17", "formats": formats, "fields": fields}
with open(os.path.join(G, "fields.json"), "w") as f:
    json.dump(doc, f, indent=1, ensure_ascii=False)
    f.write("\n")
missing = [(x["format"], x["path"]) for x in fields if x["example"] is None and fmt_by_id[x["format"]]["adapter"]]
print(len(formats), "formats", len(fields), "fields; no example:", missing)
for f in formats:
    for p in f["spec_files"] + f["example_files"]:
        if not os.path.exists(os.path.join(G, p)):
            print("MISSING FILE", p)
