"""Rebuild hg38canon order from UCSC chromFa tar in memory; report sha256 and seqcol."""
import base64, hashlib, json, sys, tarfile
sys.path.insert(0, sys.argv[2])
from seqcol import t24u, canon
order = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY", "chrM"]
want = {f"./chroms/{c}.fa": c for c in order}
data = {}
with tarfile.open(sys.argv[1], "r:gz") as tf:
    for m in tf:
        if m.name in want:
            data[want[m.name]] = tf.extractfile(m).read()
sha = hashlib.sha256()
names, lengths, seqs = [], [], []
for c in order:
    b = data[c]
    sha.update(b)
    lines = b.split(b"\n")
    assert lines[0] == b">" + c.encode(), lines[0]
    s = b"".join(lines[1:]).upper()
    names.append(c); lengths.append(len(s))
    seqs.append("SQ." + base64.urlsafe_b64encode(hashlib.sha512(s).digest()[:24]).decode())
nlp = [{"length": l, "name": n} for n, l in zip(names, lengths)]
l1 = {"names": t24u(canon(names)), "lengths": t24u(canon(lengths)), "sequences": t24u(canon(seqs)),
      "name_length_pairs": t24u(canon(nlp)),
      "sorted_name_length_pairs": t24u(canon(sorted(t24u(canon(p)) for p in nlp))),
      "sorted_sequences": t24u(canon(sorted(seqs)))}
l0 = t24u(canon({"names": l1["names"], "sequences": l1["sequences"]}))
print("sha256", sha.hexdigest(), file=sys.stderr)
json.dump({"level_0": l0, "level_1": l1, "level_2": {"names": names, "lengths": lengths, "sequences": seqs}}, sys.stdout, indent=2)
print()
