# refmeta crosswalk format (version 1)

A crosswalk tells a conversion engine how one native format maps to the refmeta core
record (`core.schema.json`). There is one file per format:
`mapping/crosswalk/<format_id>.yaml`. This document is the whole contract. An engine
written from it, plus the adapters in `tools/refmeta/formats/`, can convert any format to
the core and back.

## 1. Words used here

- **Native record**: one flat dict that an adapter's `read(text)` returns. Its keys are the
  field paths in `sources/<source>/fields.json` for that format. Keys are opaque strings:
  the engine never splits them on `.`, `[]`, `/` or anything else. Values are JSON values.
- **Core record**: one JSON object valid against `core.schema.json`.
- **to_core**: native records to core records. **from_core**: core records to native records.
- **Row**: one native record when the format has one record per sequence (or per file, or
  per alias). A file of rows becomes one core record (see section 5).

## 2. File layout

```yaml
crosswalk: 1                     # this document's version
format: ncbi_assembly_report_sequences   # format id from fields.json
source: ncbi                     # source folder under sources/
core: "0.1"                      # core.schema.json version
subject: assembly                # value written to the core record's 'subject'
description: "..."               # the format's description, copied from fields.json
records:                         # how native records group into core records (section 5)
  mode: group                    # each | group
  group_by: []                   # group mode: native paths that split a file into records
  rows:                          # group mode only
    target: sequences            # core array that rows fill (no brackets)
    key: null                    # native path: rows with the same value merge into one element
    explode: null                # {field: <native path>, sep: ","}: copy a row once per value
notes: "..."                     # optional: what a reader of this crosswalk must know
constants: {}                    # core path -> value; set on to_core (section 6)
derive: []                       # derivations to run (section 8)
rules: [...]                     # section 3
unmapped: [...]                  # section 9
```

Every field that fields.json lists for the format appears exactly once in the file: either as
the `native` of one or more rules, or in `unmapped`. A native path may appear in several rules
(one native value can fill several core fields).

## 3. Rules

```yaml
- native: assembly_info.assembly_level      # native path, exactly as in fields.json
  core: assembly.level                      # core path (section 4)
  direction: both                           # both | to_core | from_core
  transform: {map: {values: {Chromosome: chromosome, Complete Genome: complete genome}}}
  missing: null                             # native token meaning "no value"
  fallback: []                              # from_core only: other core paths to try
  lossy: null                               # what is lost or changed, in words; null = nothing
  example: {native: Chromosome, core: chromosome, file: examples/datasets_dataset_report_GCF_000001405.40.json}
```

| Key | Required | Meaning |
|---|---|---|
| `native` | yes | Native path. |
| `core` | yes, unless `compute` | Core path. |
| `compute` | no | from_core only: build the native value with a fixed function instead of reading a core path (section 8.2). |
| `direction` | yes | `both`: used in both directions; `to_core`: only when reading; `from_core`: only when writing. |
| `transform` | no | One transform `{name: params}` or a list of them, applied in order (section 7). `null` means copy the value. |
| `missing` | no | A string, number or list of them. On to_core a native value equal to one of them is treated as absent. On from_core, if the core value is absent and the rule is the only rule for that native path, the first token is written. |
| `fallback` | no | List of core paths. On from_core, if `core` has no value, try these in order. |
| `lossy` | no | Plain text saying what this rule loses or bends. `null` means a both-way rule round-trips exactly. |
| `example` | yes | A real value from the format's example files and what the rule turns it into: `{native, core, file}`, where `file` is relative to `sources/<source>/`. `truncated: true` means a long list was cut to its first 3 items or a long string to 157 characters for display. For a `from_core` rule `core` is `null`. `example: null` only when no example file has a value; then `note` says so. |
| `note` | no | Anything else a reader needs. |
| `match` | no | How closely the native field matches the core field, for the SSSOM export (`mapping/sssom/`): `exact`, `close`, `broad` (the core field is broader), `narrow` (the core field is narrower) or `related`. Leave it out and the export uses `exact` for a `both` rule with `lossy: null` (the round-trip tests hold those to exact) and `close` for the rest. The engine ignores it. |

Applying a rule:

- **to_core** (`both` or `to_core`): read the native value. If it is absent, `null`, or equal
  to a `missing` token, skip the rule. Apply the transforms forward. If the result is absent
  (for example a regex did not match), skip and log a warning; if no rule could use the value,
  it goes to extras (section 9). Write the result to `core`
  (section 4.2).
- **from_core** (`both` or `from_core`): read the core value at `core` (then `fallback`). If
  absent, skip. For a `both` rule apply the inverse of each transform in reverse order. For a
  `from_core` rule apply the transforms forward (the input is the core value). Write the
  result to `native`, shaped as section 4.3 says.

Rules run in file order. When two rules write the same core scalar, the first value wins and
the second, if different, is added to `conflicts`. On from_core, when several rules write the
same native path, the first rule (in file order) that yields a value wins.

## 4. Core paths

### 4.1 Grammar

```
path      := segment ("." segment)*
segment   := name selector?
name      := [A-Za-z_][A-Za-z0-9_]*
selector  := "[]" | "[+]" | "[" digits "]" | "[" cond ("," cond)* "]"
cond      := name "=" value        # value: any characters except "]" and ","
```

Split a path on `.` only outside brackets: `collection.labels[namespace=galaxy.dbkey].value`
has three segments. Every path must resolve against `core.schema.json`: each `name` is a
property of the object at that point, and a selector may follow only a name whose schema type
is `array`. Keys of `checksums`, `uncompressedChecksums`, `level1` and `extras` are free names.

| Selector | On write (to_core) | On read (from_core) |
|---|---|---|
| none, on an array field at the end of the path | The value must be a list: append each item that is not already in the array (objects are compared whole). | The whole array. |
| none, elsewhere | Create the object if missing; set the member. | The member. |
| `[]` | **Spread.** The value is a list; item *i* goes to element *i* (elements are created as `{}` when missing; `null` items are skipped). Several rules spreading into the same array fill the same elements, so aligned native lists zip into objects. In group mode, the first `[]` right after `rows.target` means "this row's element" instead (section 5). | A list with the value from every element, in order (elements without the value give `null`). |
| `[+]` | Group mode only. A new element appended for this row. All rules of the same row that use `[+]` on the same array path share that one element. | One native row per element of that array (section 5.3). |
| `[n]` | Element *n* (0-based); create elements up to *n* if missing. | Element *n*. |
| `[k=v,...]` | **Keyed element.** Conditions compare a member's text form (strings as is; numbers and booleans as JSON text, so `circular=true`) with `v`. When an element is created, each condition value is converted to the member's schema type. If the rest of the path is one member name (`aliases[namespace=insdc].value`), the pair (conditions, member value) is treated as a set item: use the first element that matches the conditions and whose member is absent or already equal to the value; otherwise append a new element. A list value makes one such item per list entry: `labels[namespace=galaxy.dbkey].value` with `["hg38","hg19"]` gives two elements. If the rest of the path is longer (`copies[kind=fasta].checksums.md5`), use the first element that matches, creating it if needed. | All matching elements. |

### 4.2 Writing values (to_core)

After transforms, a value is written with the selector rules above. Extra cases:

- A list written to a core scalar: if the list has one item, write the item; if it has none,
  skip; if it has more, write the first and add the rest to `conflicts`.
- A scalar written where a list is expected (an array field with no selector): wrap it as a
  one-item list.
- Types must match the core schema after transforms. The engine does not cast silently; a
  crosswalk that needs a cast says so with the `cast` transform.

### 4.3 Shaping native values (from_core)

The native shape follows the field's `type` and `cardinality` in fields.json:

- `type: array` or `cardinality: many`: write a list (wrap a single value).
- otherwise: write a scalar. If the core read gave a list, write its first non-null item.

## 5. Records and rows

### 5.1 `mode: each`

Each native record becomes one core record, and each core record becomes one native record.
`[]` paths spread native lists (the seqcol `names` array becomes `sequences[].name`).

### 5.2 `mode: group` (to_core)

Used for formats with one native record per sequence, per file, or per alias (chrom.sizes,
.fai, SAM `@SQ` lines, md5sum files, alias tables), and for formats whose rows must be
gathered (an S3 manifest).

1. If `rows.explode` is set, copy each native row once per value of `explode.field` split on
   `explode.sep` (trimmed, empty parts dropped); each copy holds one value.
2. Split the rows into groups by the tuple of `group_by` values (absent = `null`), keeping the
   order in which groups first appear. An empty `group_by` puts the whole file in one group.
3. Each group becomes one core record. For each row, in file order:
   - Pick the row's element of `rows.target`. If `rows.key` is set and an earlier row of the
     group had the same key value, reuse that element. Otherwise append a new element `{}`.
   - **Per-row rules** are the rules whose core path starts with `<rows.target>[]`. The `[]`
     right after the target binds to this row's element. Any later `[]` in the path spreads
     as usual.
   - **Record rules** are all other rules. They take their value from the first row that has
     one. A later row with a different value adds an entry to `conflicts` (the engine does
     not stop).
4. Constants, unmapped fields and derivations are then handled once per record.

### 5.3 `mode: group` (from_core)

1. One core record becomes one group of native rows. By default there is one row per element
   of `rows.target`, in array order.
2. If any per-row rule uses `[+]` (for example `sequences[].aliases[+].value`), emit one row
   per element of that inner array instead, for each target element. Rules that use `[+]` on
   the same inner array read the same element. Per-row rules without `[+]` read the parent
   element and repeat on each of its rows.
3. Record rules are written on every row (adapters for these formats repeat collection fields
   on each row, or ignore them).
4. If `rows.explode` is set, merge rows that are equal except for `explode.field`, joining
   those values with `explode.sep` in first-seen order.
5. `group_by` fields are written like any other record rule.

### 5.4 One core record to several native records

Some formats split one core record across several native records of the same file. Handled
by 5.3 for group mode. For mode `each`, a core record gives one native record. The engine
writes a file from a list of core records by concatenating the native records they give and
calling the adapter's `write(records)`.

### 5.5 Combining records from different formats

Converting one file never needs merging. Merging two core records (for example an NCBI
assembly report and a refgenie alias record for the same genome) is a separate step:

1. Records merge only if they share an identifier at some level: an item of
   `assembly.accessions` (same namespace and value), `collection.digest`, a sequence
   `digest`/`md5`, or a copy `location`+checksum.
2. Objects merge member by member. Scalars that differ go to `conflicts`, first value kept.
3. Arrays of `Name` merge as sets. `assembly.accessions` merge by namespace + value (so a
   `url` from one record joins the same accession from the other). `copies` merge by `location`; `deployments` by
   `system`+`scope`+`table`+`key`; `sequences` merge by index only when the two
   `collection.digest` values are equal, otherwise by `digest`, then `md5`, then an alias in a
   global namespace (`insdc`, `refseq`).
4. `provenance` lists are joined (ids renumbered) and `fieldSources` is filled for every value.

## 6. Constants

`constants` maps core paths to fixed values that the format implies but does not write, for
example `collection.provider: Ensembl` for an Ensembl FASTA header. They are set on to_core
after the rules, only where the rules left the path empty. On from_core they are ignored.
Keyed selectors in rule paths also act as constants: writing
`deployments[system=galaxy,table=all_fasta].key` creates the element with `system` and
`table` set.

## 7. Transforms

There are eleven transforms: `cast`, `map`, `regex`, `prefix`, `replace`, `split`, `date`,
`curie`, `rekey`, `entries` and `accession`. Each has a forward function (used on to_core, and on from_core for
`from_core` rules) and an inverse (used on from_core for `both` rules). A transform without an
inverse can only be used in a one-way rule. When the input is a list, `cast`, `map`, `regex`,
`prefix`, `replace` and `date` apply to each item and drop items that give no value; `split`, `curie`,
`rekey`, `entries` and `accession` handle lists as stated below.

### 7.1 `cast`

Params: `to` (core type) and `from` (native type), each one of `integer`, `number`,
`string`, `boolean`.

- Forward: convert to `to`. Strings to integer/number with base-10 parsing (surrounding space
  ignored); `"true"/"false"` (any case), `1/0`, `"1"/"0"` to boolean. A value that cannot be
  converted gives no value.
- Inverse: convert back to `from`. Integers to string with no decimal point; booleans to
  string as `true`/`false`.

| Forward input | Params | Output |
|---|---|---|
| `"3099441038"` | `{to: integer, from: string}` | `3099441038` |
| `"9606"` | `{to: integer, from: string}` | `9606` |
| `3099441038` (inverse) | `{to: integer, from: string}` | `"3099441038"` |

### 7.2 `map`

Params: `values` (object: native value -> core value), `other` (`keep` or `drop`, default
`keep`).

- Forward: look up the value's text form (strings as is; numbers and booleans as JSON text:
  `1`, `1.0`, `true`; `null` never reaches a transform). Found: return the mapped value
  (which may be any JSON value, including `null`, meaning absent). Not found: return the value
  unchanged (`keep`) or nothing (`drop`).
- Inverse: the first native key whose mapped value equals the core value. YAML keys are text,
  so the key is converted to the native field's fields.json type when that type is integer,
  number or boolean (`"1"` becomes `1` for Ensembl's integer `is_circular`). Not found: `keep`
  returns the core value, `drop` returns nothing.

| Forward input | Params | Output |
|---|---|---|
| `"Complete Genome"` | `{values: {Complete Genome: complete genome, Chromosome: chromosome}}` | `"complete genome"` |
| `"1"` | `{values: {"1": true, "0": false}}` | `true` |
| `"unlocalised-scaffold"` | `{values: {unlocalised-scaffold: unlocalized-scaffold}}` | `"unlocalized-scaffold"` |
| `true` (inverse) | `{values: {"1": true, "0": false}}` | `"1"` |

### 7.3 `regex`

Params: `pattern` (regular expression in the common subset of Python `re` and JavaScript
`RegExp`; crosswalks use only numbered groups), `group` (integer, default `1`), `as` (`string`, `integer` or `number`, default
`string`), `template` (optional).

- Forward: search the value's text for `pattern` (unanchored search). No match gives no value.
  Return the group's text, converted with `as`.
- Inverse: only if `template` is given: replace every `{}` in `template` with the core value's
  text. Without `template` there is no inverse.

| Forward input | Params | Output |
|---|---|---|
| `"https://identifiers.org/taxonomy:9606"` | `{pattern: 'taxonomy:(\d+)$', as: integer, template: 'https://identifiers.org/taxonomy:{}'}` | `9606` |
| `"Homo sapiens (human)"` | `{pattern: '^(.*?)(?: \(.*\))?$'}` | `"Homo sapiens"` |
| `"strain=S288C"` | `{pattern: '=(.*)$'}` | `"S288C"` |
| `9606` (inverse) | same as first row | `"https://identifiers.org/taxonomy:9606"` |

### 7.4 `prefix`

Params: exactly one of `add` or `strip` (a string).

- `add: P`. Forward: `P + v`, unless `v` already starts with `P`. Inverse: remove a leading
  `P` if present.
- `strip: P`. Forward: remove a leading `P` if present. Inverse: `P + v` unless `v` already
  starts with `P`.

| Forward input | Params | Output |
|---|---|---|
| `"Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"` | `{add: "SQ."}` | `"SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"` |
| `"./GCA_000146045.2_R64_genomic.fna.gz"` | `{strip: "./"}` | `"GCA_000146045.2_R64_genomic.fna.gz"` |
| `"SQ.Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"` (inverse) | `{add: "SQ."}` | `"Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"` |

### 7.5 `replace`

Params: `old`, `new` (strings).

- Forward: replace every `old` with `new`.
- Inverse: replace every `new` with `old`. This is exact only when the native value never
  holds `new`; crosswalks that use it say so in `lossy` if that can happen.

| Forward input | Params | Output |
|---|---|---|
| `"Homo_sapiens"` | `{old: "_", new: " "}` | `"Homo sapiens"` |
| `"Saccharomyces cerevisiae"` (inverse) | `{old: "_", new: " "}` | `"Saccharomyces_cerevisiae"` |

### 7.6 `split`

Params: `sep` (string).

- Forward: a string becomes a list: split on `sep`, trim each part, drop empty parts. A list
  input is returned unchanged.
- Inverse: join the list's items (as text) with `sep`.

| Forward input | Params | Output |
|---|---|---|
| `"7219534;10508508;10830953"` | `{sep: ";"}` | `["7219534", "10508508", "10830953"]` |
| `"chrMT,M,chrM"` | `{sep: ","}` | `["chrMT", "M", "chrM"]` |
| `["a", "b"]` (inverse) | `{sep: ";"}` | `"a;b"` |

### 7.7 `date`

Params: `format`, a pattern using only `%Y` (4 digits), `%m` (2), `%d` (2), `%H` (2),
`%M` (2), `%S` (2) and literal characters.

- Forward: parse the value with `format`. If the format has no time part, return
  `YYYY-MM-DD`; otherwise `YYYY-MM-DDTHH:MM:SS`. No match gives no value.
- Inverse: parse the core ISO value (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`) and print it with
  `format`.

Partial ISO dates that are already in ISO form (`2013-12`) need no transform.

| Forward input | Params | Output |
|---|---|---|
| `"2022/02/03"` | `{format: "%Y/%m/%d"}` | `"2022-02-03"` |
| `"2014/01/15T21:14:12"` | `{format: "%Y/%m/%dT%H:%M:%S"}` | `"2014-01-15T21:14:12"` |
| `"2022-02-03"` (inverse) | `{format: "%Y/%m/%d"}` | `"2022/02/03"` |

### 7.8 `curie`

Params: `sep` (default `":"`), `namespaces` (optional object: native prefix -> core namespace).

- Forward: a string `prefix<sep>rest` (split at the first `sep`) becomes
  `{namespace: <mapped prefix>, value: rest}`. A prefix not in `namespaces` is lower-cased.
  A string without `sep` gives no value. A list gives a list.
- Inverse: `{namespace, value}` becomes `<native prefix><sep><value>`, using the first native
  prefix that maps to the namespace, or the namespace itself.

| Forward input | Params | Output |
|---|---|---|
| `"refseq:NC_000001.11"` | `{namespaces: {NCBI: refseq}}` | `{namespace: refseq, value: NC_000001.11}` |
| `["GRCh38:chr1", "MD5:6aef897c3d6ff0c78aff06ac189178dd"]` | `{}` | `[{namespace: grch38, value: chr1}, {namespace: md5, value: 6aef897c3d6ff0c78aff06ac189178dd}]` |
| `{namespace: refseq, value: NC_000001.11}` (inverse) | `{namespaces: {NCBI: refseq}}` | `"NCBI:NC_000001.11"` |

### 7.9 `rekey`

Params: `keys` (object: native member -> core member; native members not listed are
dropped), `values` (optional object: core member -> {native value: core value}).

- Forward: an object, or a list of objects, with members renamed by `keys`; then each member
  listed in `values` is mapped like `map` with `other: keep`.
- Inverse: the reverse renaming and value maps.

| Forward input | Params | Output |
|---|---|---|
| `[{"dbname": "UCSC", "name": "chr1"}]` | `{keys: {dbname: namespace, name: value}, values: {namespace: {UCSC: ucsc}}}` | `[{"namespace": "ucsc", "value": "chr1"}]` |
| `[{"chrom": "chrI", "len": 230218}]` | `{keys: {chrom: name, len: length}}` | `[{"name": "chrI", "length": 230218}]` |

### 7.10 `entries`

Params: `key` and `value`: core member names; `value` may be dotted (`checksums.sha256`) to
build a nested object.

- Forward: an object `{k1: v1, k2: v2}` becomes `[{<key>: k1, <value>: v1}, {<key>: k2, <value>: v2}]`
  in the object's key order.
- Inverse: a list of objects becomes `{<key>: <value>}`, skipping items that lack either
  member.

| Forward input | Params | Output |
|---|---|---|
| `{"hg38canon.fa": "87b0ea46...b335"}` | `{key: location, value: checksums.sha256}` | `[{"location": "hg38canon.fa", "checksums": {"sha256": "87b0ea46...b335"}}]` |
| `{"fasta": "hg38.fa", "fai": "hg38.fa.fai"}` | `{key: kind, value: location}` | `[{"kind": "fasta", "location": "hg38.fa"}, {"kind": "fai", "location": "hg38.fa.fai"}]` |

### 7.11 `accession`

Turns a plain accession string into an `assembly.accessions` item, using the patterns in
`mapping/namespaces.yaml`. Params: `namespaces` (optional list of official namespace ids;
default: every official accession namespace that has a pattern, in registry order), `other`
(optional namespace for a value that matches no pattern), `index` (integer, default `0`).

- Forward: the first namespace in `namespaces` whose pattern matches the whole value gives
  `{namespace, value}`. No match gives `{namespace: <other>, value}`, or no value when
  `other` is not set. A list gives a list (items with no value are dropped).
- Inverse: the input is the `assembly.accessions` list (or one item). Keep the items whose
  namespace is in `namespaces` or is `other` when the rule lists `namespaces`, and all items
  when it does not. Return item `index`'s value (for a native field of type `array`, the
  values of all items from `index` on). No such item gives no value.

Use the rule path `assembly.accessions` (no selector), so to_core appends the item and
from_core reads the whole list. Rules run in file order, so a format's main accession must
come before its paired one: the main rule uses `index: 0`, the paired rule
`{namespaces: [insdc.gca, insdc.gcf], index: 1}`. A native field that holds only one kind
needs no transform: `assembly.accessions[namespace=insdc.gcf].value`.

| Forward input | Params | Output |
|---|---|---|
| `"GCF_000001405.40"` | `{}` | `{namespace: insdc.gcf, value: GCF_000001405.40}` |
| `"PBARC"` | `{other: unspecified}` | `{namespace: unspecified, value: PBARC}` |
| `[{insdc.gcf, GCF_000001405.40}, {insdc.gca, GCA_000001405.29}]` (inverse) | `{}` | `"GCF_000001405.40"` |
| the same list (inverse) | `{namespaces: [insdc.gca, insdc.gcf], index: 1}` | `"GCA_000001405.29"` |

## 8. Derivations and computed native fields

### 8.1 `derive` (core side)

A crosswalk lists the derivations that are valid for its records. The engine runs them after
the rules on to_core, and before writing on from_core (so a writer can use them). A derivation
never overwrites a value that is present; if it computes a different value from data in the
record, it adds a `conflicts` entry.

| Name | Needs | Sets |
|---|---|---|
| `seqcol_digests` | every `sequences[]` has `name`, `length` and `digest`; or `collection.level1.names` and `.sequences` | `collection.level1.*` (all six attributes when level 2 data is there) and `collection.digest`, by the GA4GH seqcol rules: canonical JSON (RFC 8785), sha512t24u, level 0 over the inherent attributes `names` and `sequences`. `refmeta.formats.ga4gh.level0_digest()` and `level1_digests()` are the reference implementation. |
| `counts` | every `sequences[]` element is one sequence of the collection, and lengths are known | `collection.nSequences` and `collection.totalLength`. |
| `accession_version` | an `insdc.gca`/`insdc.gcf` item of `assembly.accessions` has no version (`^GC[AF]_\d{9}$`) and `assembly.version` is all digits | that item's value = accession + `.` + version. |

### 8.2 `compute` (native side)

A `from_core` rule may use `compute: <name>` instead of `core`. These native fields are pure
functions of other data and are rebuilt rather than stored:

| Name | Native value |
|---|---|
| `seqcol_name_length_pairs` | `[{"length": l, "name": n}, ...]` from `sequences[].name` and `.length`, in order. |
| `seqcol_sorted_sequences` | `sequences[].digest` sorted by Unicode code point. |
| `seqcol_sorted_name_length_pairs` | the sorted list of the sha512t24u digests of each canonical `{length, name}` object. |

## 9. Unmapped fields

```yaml
unmapped:
  - native: Relationship
    per: row          # group mode: row -> element extras; record -> record extras
    reason: "..."
```

On to_core, every native field that no rule reads, or whose value no rule could use (all
transforms gave no value), is copied into `extras[<format_id>][<native path>]`: in group mode, `per: row` fields go to the row's
element (`sequences[i].extras`, `copies[i].extras`, `deployments[i].extras`), and
`per: record` fields to the record's `extras` (first row's value). In mode `each` all go to
the record's `extras`. On from_core, extras for the same format id are written back
unchanged. Extras for other formats are ignored. Native fields named by a `compute` rule are
not copied to extras: they are rebuilt on write. This makes a round trip through the same
format lossless even where the core has no field.

## 10. Checks a crosswalk must pass

1. Every fields.json path of the format is a rule `native` or an `unmapped` entry.
2. Every core path resolves against `core.schema.json` (section 4.1).
3. Each rule's `example.native` is a value the adapter returns for one of the format's
   example files, and `example.core` is the forward transform of it.
4. A `both` rule with `lossy: null` gives back `example.native` when its inverse is applied
   to `example.core`.
5. to_core on every example file gives records that validate against `core.schema.json`.

The crosswalks in `mapping/crosswalk/` were checked this way on 2026-11-17.
