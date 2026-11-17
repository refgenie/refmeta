"""Assemble sources/galaxy/spec and examples from raw downloads in ~/work/refmeta/raw/galaxy (all data, never executed).

Usage: python -I build_folder.py <sources/galaxy>. Run build_constructed.py and make_fields.py after it.
"""
import json, os, re, shutil, sys
import yaml

RAW = os.path.expanduser("~/work/refmeta/raw/galaxy")
OUT = sys.argv[1]
SPEC, EX = os.path.join(OUT, "spec"), os.path.join(OUT, "examples")

def cp(src, dst):
    dst = os.path.join(OUT, dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(RAW, src), dst)

def write(dst, text):
    dst = os.path.join(OUT, dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(text)

# ---------- spec: galaxy core ----------
for f in ["builds.txt.sample", "tool_data_table_conf.xml.sample"]:
    cp(f, f"spec/galaxy/{f}")
for f in ["manual_builds.txt.sample", "all_fasta.loc.sample", "twobit.loc.sample", "ucsc_build_sites.txt.sample", "dbkeys.loc.test"]:
    cp(f"galaxy_repo/{f}", f"spec/galaxy/{f}")
# code is stored as .txt so nothing imports or runs it
cp("galaxy_repo/data_init.py", "spec/galaxy/lib_galaxy_tools_data__init__.py.txt")
cp("galaxy_repo/managers_dbkeys.py", "spec/galaxy/lib_galaxy_managers_dbkeys.py.txt")
cp("galaxy_repo/api_genomes.py", "spec/galaxy/lib_galaxy_webapps_galaxy_api_genomes.py.txt")
cp("galaxy_repo/test_refgenie_data_table.py", "spec/galaxy/test_unit_app_tools_test_refgenie_data_table.py.txt")
cp("galaxy_repo/refgenie.yml", "spec/galaxy/test_integration_refgenie.yml")
cp("galaxy_repo/visualization_genomes.py", "spec/galaxy/lib_galaxy_visualization_genomes.py.txt")
cp("galaxy_repo/managers_tool_data.py", "spec/galaxy/lib_galaxy_managers_tool_data.py.txt")
cp("galaxy_repo/api_tool_data.py", "spec/galaxy/lib_galaxy_webapps_galaxy_api_tool_data.py.txt")
src = open(os.path.join(RAW, "galaxy_repo/tool_util_data_init.py")).read().splitlines(keepends=True)
# excerpt: ToolDataTable base init + TabularToolDataTable (lines 243-720)
write("spec/galaxy/lib_galaxy_tool_util_data__init__.excerpt.py.txt",
      "# Excerpt (lines 243-720) of lib/galaxy/tool_util/data/__init__.py, galaxyproject/galaxy dev, 2026-11-17\n" + "".join(src[242:720]))

# ---------- spec: tools-iuc data managers ----------
TI = os.path.join(RAW, "tools_iuc")
for root, _, files in os.walk(TI):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), TI)
        dst = rel + (".txt" if rel.endswith(".py") else "")
        cp(os.path.join("tools_iuc", rel), os.path.join("spec/tools-iuc", dst))

# ---------- spec: IDC main ----------
for f in ["README.md", "genomes.yml", "data_managers.yml", "config/tool_data_table_conf.xml",
          "cvmfs_current_managed/cvmfs_data_managers.yml", "cvmfs_current_managed/cvmfs_managed_genomes.yml",
          "docs/genome-indexing.md", "docs/requesting-reference-data.md", "docs/architecture.md",
          "docs/using-idc-data.md", "schemas/data_managers.yml",
          "data-managers/all_fasta/hg38canon.yaml", "data-managers/fasta_indexes/hg38canon.yaml",
          "data-managers/rnastar_index2x_versioned/hg38canon.yaml"]:
    cp(f"idc_main/{f}", f"spec/idc/{f}")
sch = json.load(open(os.path.join(RAW, "idc_main/schemas/request.schema.json")))
keep = [k for k in sch["$defs"] if any(s in k for s in ["fetch_genome_dbkeys_all_fasta", "sam_fasta_index_builder",
        "bwa_mem_index_builder", "bowtie2_index_builder", "star_index_builder"])]
exc = {k: v for k, v in sch.items() if k not in ("$defs", "allOf")}
exc["$comment"] = ("EXCERPT made 2026-11-17 by refmeta: top level kept whole; $defs and allOf cut to the 5 genome "
                   "data managers (all_fasta, fasta_indexes, bwa_mem, bowtie2, rnastar). Full file: 630 KB, 98 $defs.")
exc["$defs"] = {k: sch["$defs"][k] for k in keep}
exc["allOf"] = [a for a in sch["allOf"] if a["then"]["properties"]["params"]["$ref"].split("/")[-1] in keep]
write("spec/idc/schemas/request.schema.excerpt.json", json.dumps(exc, indent=1) + "\n")

# ---------- spec: IDC PR #88 ----------
P = "idc_pr88/sync"
cp(f"{P}/README.md", "spec/idc_pr88/sync/README.md")
cp(f"{P}/ADMINS.md", "spec/idc_pr88/sync/ADMINS.md")
for f in ["tool_data_table_conf_to_yaml.py", "all_fasta_files_to_refget_store.py",
          "all_tables_content_to_fasta_based_yaml.py", "all_tables_content_add_hashes.py"]:
    cp(f"{P}/{f}", f"spec/idc_pr88/sync/{f}.txt")

# ---------- examples ----------
# builds.txt excerpt
lines = open(os.path.join(RAW, "builds.txt.sample")).read().splitlines()
keep = [l for l in lines if l.startswith("#Harvested") or l.split("\t")[0] in ("hg38", "sacCer3")]
write("examples/builds.txt", "\n".join(keep) + "\n")

# /api/genomes excerpt (keeps original order)
g = json.load(open(os.path.join(RAW, "api_genomes.json")))
g2 = [x for x in g if x[1] in ("?", "hg38", "sacCer3", "GCF_000001405.40", "GCF_000146045.2")]
write("examples/usegalaxy_org_api_genomes.excerpt.json", json.dumps(g2) + "\n")
for gid in ["hg38", "sacCer3", "GCF_000001405.40", "GCF_000146045.2"]:
    cp(f"api_genomes_{gid}.json", f"examples/usegalaxy_org_api_genomes_{gid}.json")

# /api/tool_data/<table> excerpts
ANCHOR_VALUES = {"hg38", "hg38canon", "hg38female", "sacCer3", "GCF_000001405.40", "GCF_000146045.2"}
for inst, tables in [("org", ["all_fasta", "fasta_indexes", "bwa_mem_indexes", "bowtie2_indexes",
                              "rnastar_index2x_versioned", "__dbkeys__"]),
                     ("eu", ["all_fasta", "__dbkeys__"])]:
    for t in tables:
        d = json.load(open(os.path.join(RAW, f"api/usegalaxy_{inst}_tool_data_{t}.json")))
        keep = ANCHOR_VALUES | ({"GRCh38"} if inst == "eu" else set())  # EU lookalike: GRCh38 = transcriptome + ERCC
        rows = [r for r in d["fields"] if r[0] in keep]
        d["fields"] = rows
        write(f"examples/usegalaxy_{inst}_api_tool_data_{t}.excerpt.json", json.dumps(d) + "\n")

# .loc files rebuilt from PR #88 cvmfs_20260715.yml (tab-joined in declared column order)
big = yaml.load(open(os.path.join(RAW, P, "cvmfs_20260715.yml")), Loader=yaml.CSafeLoader)
COLS = {"all_fasta": ["value", "dbkey", "name", "path"], "fasta_indexes": ["value", "dbkey", "name", "path"],
        "bwa_mem_indexes": ["value", "dbkey", "name", "path"], "bowtie2_indexes": ["value", "dbkey", "name", "path"],
        "rnastar_index2x_versioned": ["value", "dbkey", "name", "path", "with_gene_model", "version"],
        "__dbkeys__": ["value", "name", "len_path"]}
FN = {"all_fasta": "all_fasta.loc", "fasta_indexes": "fasta_indexes.loc", "bwa_mem_indexes": "bwa_mem_index.loc",
      "bowtie2_indexes": "bowtie2_indices.loc", "rnastar_index2x_versioned": "rnastar_index2x_versioned.loc",
      "__dbkeys__": "dbkeys.loc"}
pat = re.compile(r"^(hg38|hg38canon|hg38female|sacCer3|GCF_000001405\.40|GCF_000146045\.2)$")
def anchor(r):
    return bool(pat.match(str(r.get("value", ""))) or pat.match(str(r.get("dbkey", ""))))
excerpt = {}
for t, cols in COLS.items():
    rows = [r for r in big[t] if anchor(r)]
    excerpt[t] = rows
    out, last = [], None
    for r in rows:
        if r["loc_file"] != last:
            out.append(f"# from {r['loc_file']} (table {t}, listed in {r['xml_file']})")
            last = r["loc_file"]
        out.append("\t".join(r[c] for c in cols))
    write(f"examples/cvmfs_{FN[t]}", "\n".join(out) + "\n")
# twobit + sam_fa_indexes also into all_tables excerpt for context
for t in ["twobit", "sam_fa_indexes", "picard_indexes"]:
    excerpt[t] = [r for r in big[t] if anchor(r)]
with open(os.path.join(EX, "idc_pr88_cvmfs_20260715_all_tables.excerpt.yml"), "w") as f:
    yaml.dump(dict(sorted(excerpt.items())), f)

# data manager JSON (tools-iuc test-data, real tool outputs used in tests)
for src, dst in [("data_manager_fetch_genome_dbkeys_all_fasta/test-data/fetch_data_manager.1.data_manager_json", "dm_fetch_genome_all_fasta_phiX174.data_manager_json"),
                 ("data_manager_fetch_genome_dbkeys_all_fasta/test-data/fetch_data_manager.2.data_manager_json", "dm_fetch_genome_all_fasta_phiX174Variant1.data_manager_json"),
                 ("data_manager_sam_fasta_index_builder/test-data/sam_fasta_data_manager.1.json", "dm_sam_fasta_index_phiX174.json"),
                 ("data_manager_bwa_mem_index_builder/test-data/bwa_mem_data_manager.1.json", "dm_bwa_mem_index_phiX174.json"),
                 ("data_manager_bowtie2_index_builder/test-data/bowtie2_data_manager.1.json", "dm_bowtie2_index_phiX174.json"),
                 ("data_manager_star_index_builder/test-data/test_star_01.data_manager_json", "dm_rnastar_index_phiX174.data_manager_json")]:
    cp(f"tools_iuc/{src}", f"examples/{dst}")

# tool_data_table_conf.xml: Galaxy sample (has refgenie tables) and a real deployment (IDC build Galaxy)
cp("tool_data_table_conf.xml.sample", "examples/galaxy_tool_data_table_conf.xml.sample")
cp("idc_main/config/tool_data_table_conf.xml", "examples/idc_tool_data_table_conf.xml")

# IDC genomes.yml excerpt: sacCer3 entry (text block, exact)
gtext = open(os.path.join(RAW, "idc_main/genomes.yml")).read()
blocks = re.split(r"(?m)^(?=  - dbkey: )", gtext)
sac = [b for b in blocks if b.startswith("  - dbkey: sacCer3")]
write("examples/idc_genomes_sacCer3.excerpt.yml", "genomes:\n" + "".join(sac))
mtext = open(os.path.join(RAW, "idc_main/cvmfs_current_managed/cvmfs_managed_genomes.yml")).read()
mblocks = re.split(r"(?m)^(?=    - )", mtext)
mkeep = [b.rstrip() + "\n" for b in mblocks if re.match(r"    - dbkey: (hg38|sacCer3)\n", b)]
write("examples/idc_cvmfs_managed_genomes_hg38_sacCer3.excerpt.yml", "- genomes:\n" + "\n".join(mkeep))

# IDC requests (real, whole files)
cp("idc_main/data-managers/all_fasta/hg38canon.yaml", "examples/idc_request_all_fasta_hg38canon.yaml")
cp("idc_main/data-managers/fasta_indexes/hg38canon.yaml", "examples/idc_request_fasta_indexes_hg38canon.yaml")
cp("idc_main/data-managers/rnastar_index2x_versioned/hg38canon.yaml", "examples/idc_request_rnastar_index2x_versioned_hg38canon.yaml")
cp("idc_main/data_managers.yml", "examples/idc_data_managers.yml")

# PR #88 refget summaries (real test outputs)
cp(f"{P}/test_dig/json/phiX174.json", "examples/idc_pr88_test_dig_json_phiX174.json")
cp(f"{P}/test_dig/yaml/all_fasta.yml", "examples/idc_pr88_test_dig_yaml_all_fasta.yml")
print("done")
