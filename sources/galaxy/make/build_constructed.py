"""Write examples/constructed/ files (hand-built or computed; documented in README)."""
import json, os, sys
import yaml
RAW = os.path.expanduser("~/work/refmeta/raw/galaxy")
C = os.path.join(sys.argv[1], "examples", "constructed")
os.makedirs(C, exist_ok=True)

def alias(row):
    s = lambda v: v.replace("/", "!")
    return {"galaxy_unique_build_id": s(row["value"]), "galaxy_dbkey": s(row["dbkey"]), "galaxy_name": s(row["name"]),
            "galaxy_loc_file": s(row["loc_file"]), "galaxy_tool_data_table_conf": s(row["xml_file"])}

rows = {
 "hg38canon": {"dbkey": "hg38", "loc_file": "/cvmfs/data.galaxyproject.org/byhand/location/all_fasta.loc",
               "name": "Human (Homo sapiens) (b38): hg38 Canonical", "value": "hg38canon",
               "xml_file": "/cvmfs/data.galaxyproject.org/byhand/location/tool_data_table_conf.xml"},
 "sacCer3": {"dbkey": "sacCer3", "loc_file": "/cvmfs/data.galaxyproject.org/byhand/location/all_fasta.loc",
             "name": "Yeast (Saccharomyces cerevisiae): sacCer3", "value": "sacCer3",
             "xml_file": "/cvmfs/data.galaxyproject.org/byhand/location/tool_data_table_conf.xml"},
}
summ = {}
for uid, src in [("hg38canon", "hg38canon_seqcol.json"), ("sacCer3", "sacCer3_ucsc_seqcol.json")]:
    sc = json.load(open(os.path.join(RAW, "fasta", src)))
    blob = {"level_0": sc["level_0"], "level_1": sc["level_1"], "level_2": sc["level_2"], "aliases": alias(rows[uid])}
    with open(os.path.join(C, f"idc_pr88_json_{uid}.json"), "w") as f:
        json.dump(blob, f, indent=2); print(file=f)
    l2 = sc["level_2"]
    summ[uid] = {"level_0": sc["level_0"], "level_1": sc["level_1"],
                 "level_2_peek": {"sequence_count": len(l2["sequences"]), "first_name": l2["names"][0],
                                  "first_length": l2["lengths"][0], "first_sequence": l2["sequences"][0]},
                 "aliases": blob["aliases"]}
with open(os.path.join(C, "idc_pr88_yaml_all_fasta.yml"), "w") as f:
    yaml.dump(summ, f, sort_keys=False, default_flow_style=False)

# .len files rebuilt from usegalaxy.org /api/genomes/<id> chrom_info (same order as served)
for gid in ["hg38", "sacCer3", "GCF_000001405.40", "GCF_000146045.2"]:
    d = json.load(open(os.path.join(RAW, f"api_genomes_{gid}.json")))
    with open(os.path.join(C, f"{gid}.len"), "w") as f:
        for c in d["chrom_info"]:
            f.write(f"{c['chrom']}\t{c['len']}\n")

# data manager JSON for the anchors, as fetch_genome_all_fasta_dbkey would write it (relative paths)
dm = {"data_tables": {"all_fasta": [{"value": "hg38canon", "dbkey": "hg38",
                                     "name": "Human (Homo sapiens) (b38): hg38 Canonical", "path": "hg38canon.fa"}]}}
json.dump(dm, open(os.path.join(C, "dm_fetch_genome_all_fasta_hg38canon.data_manager_json"), "w"))
dm = {"data_tables": {"all_fasta": [{"value": "sacCer3", "dbkey": "sacCer3",
                                     "name": "Yeast (Saccharomyces cerevisiae): sacCer3", "path": "sacCer3.fa"}]}}
json.dump(dm, open(os.path.join(C, "dm_fetch_genome_all_fasta_sacCer3.data_manager_json"), "w"))

# IDC request for sacCer3 (no real one exists in the IDC repo)
open(os.path.join(C, "idc_request_all_fasta_sacCer3.yaml"), "w").write("""# CONSTRUCTED by refmeta 2026-11-17, modelled on data-managers/all_fasta/hg38canon.yaml.
# Not in the IDC repo. No sha256 because the served file's checksum is not known to us.
tool_id: toolshed.g2.bx.psu.edu/repos/devteam/data_manager_fetch_genome_dbkeys_all_fasta/data_manager_fetch_genome_all_fasta_dbkey/0.0.6
data_tables:
  - all_fasta
params:
  dbkey_source:
    dbkey_source_selector: existing
    dbkey: sacCer3
  reference_source:
    reference_source_selector: ucsc
    requested_dbkey: sacCer3
  sequence_id: sacCer3
  sequence_name: "Yeast (Saccharomyces cerevisiae): sacCer3"
description: Yeast sacCer3 (UCSC), all sequences
""")
print(sorted(os.listdir(C)))
