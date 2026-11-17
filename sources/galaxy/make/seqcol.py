"""Compute seqcol level 0/1/2 digests for a FASTA (plain or .gz)."""
import base64, gzip, hashlib, json, sys

def t24u(b):
    return base64.urlsafe_b64encode(hashlib.sha512(b).digest()[:24]).decode()

def canon(x):
    return json.dumps(x, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode()

def read_fasta(path):
    op = gzip.open if path.endswith(".gz") else open
    name, h, n = None, None, 0
    md5 = None
    with op(path, "rb") as f:
        for line in f:
            line = line.rstrip(b"\r\n")
            if line.startswith(b">"):
                if name is not None:
                    yield name, n, h.digest(), md5.hexdigest()
                name = line[1:].split()[0].decode()
                h, n, md5 = hashlib.sha512(), 0, hashlib.md5()
            else:
                s = line.upper()
                h.update(s); md5.update(s); n += len(s)
    if name is not None:
        yield name, n, h.digest(), md5.hexdigest()

def seqcol(path):
    names, lengths, seqs, md5s = [], [], [], []
    for name, n, d, m in read_fasta(path):
        names.append(name); lengths.append(n)
        seqs.append("SQ." + base64.urlsafe_b64encode(d[:24]).decode()); md5s.append(m)
    nlp = [{"length": l, "name": nm} for nm, l in zip(names, lengths)]
    l1 = {
        "names": t24u(canon(names)),
        "lengths": t24u(canon(lengths)),
        "sequences": t24u(canon(seqs)),
        "name_length_pairs": t24u(canon(nlp)),
        "sorted_name_length_pairs": t24u(canon(sorted(t24u(canon(p)) for p in nlp))),
        "sorted_sequences": t24u(canon(sorted(seqs))),
    }
    l0 = t24u(canon({"names": l1["names"], "sequences": l1["sequences"]}))
    return {"level_0": l0, "level_1": l1, "level_2": {"names": names, "lengths": lengths, "sequences": seqs}}, md5s

if __name__ == "__main__":
    out, md5s = seqcol(sys.argv[1])
    json.dump(out, sys.stdout, indent=2); print()
