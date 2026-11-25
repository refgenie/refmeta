# LinkML-Map trial

A test of whether refmeta's crosswalks could be written as
[LinkML-Map](https://linkml.io/linkml-map/) transformation specifications instead.
Tried on 2026-11-24 with linkml-map 0.6.0. The conclusions are in
[mapping/STANDARDS.md](../../mapping/STANDARDS.md).

| File | What |
|---|---|
| `alias_src.yaml` | Hand-written LinkML schema for the `refgenie_api_alias` format |
| `core_tgt.yaml` | Hand-written LinkML schema for part of the refmeta core |
| `alias_to_core.yaml` | The `refgenie_api_alias` crosswalk (to core only) as a LinkML-Map spec |
| `refmeta_fns.py` | Python helpers the spec needs (regex, accession namespace, zipping arrays) |
| `len_src.yaml`, `len_to_core.yaml` | The `galaxy_len` crosswalk (rows grouped into one record) |

Run from this folder, with linkml-map installed:

```bash
linkml-map map-data -T alias_to_core.yaml -s alias_src.yaml --target-schema core_tgt.yaml \
  --source-type AliasResponse --functions refmeta_fns.py -f yaml \
  ../../sources/refgenie/examples/api_alias_R64-1-1.json
```

The output matches `refmeta core` for the fields covered. `linkml-map invert` on the same
spec fails on the expressions (strict mode) or drops the nested fields (`--no-strict`), so
the reverse direction would need a second, hand-written spec.

`len_to_core.yaml` works only on a JSON file that wraps the rows (`{"rows": [...]}`). Given
the `.len` file as a table, LinkML-Map writes one record per row.
