# refmeta and mapping standards

refmeta keeps its own crosswalk format as the source of truth and publishes each crosswalk
as an SSSOM mapping set too (`mapping/sssom/`). This page says why, what was tried, and
what is left to do to meet the RDA FAIR Mappings recommendations. Written 2026-11-24.

## What kind of mapping refmeta is

The RDA FAIR Mappings Working Group sorts mappings into two kinds
([model](../references/rda-fair-mappings/model.md)):

- **Entity mappings** link terms to terms: an ontology class to another ontology class
  (Mondo to OMIM), or one identifier to another for the same thing. Each row stands on its
  own, so a flat table works. SSSOM is the recommended format for these.
- **Proposition mappings** link one schema's fields to another schema's fields (DCAT-AP to
  Schema.org). They usually need value changes, splitting, grouping and lookups, and the
  rows depend on each other. The group lists LinkML-Map, XSLT, SPARQL CONSTRUCT and
  scripts as formats for these.

refmeta's crosswalks are proposition mappings. They map fields, not terms, and they do work
that a table of matches cannot hold:

| What a crosswalk does | Rules (of 1,170) or files (of 100) |
|---|---|
| Works in both directions (native to core and back) | 1,142 rules |
| Writes into a keyed list element, e.g. `labels[namespace=galaxy.dbkey].value` | 297 rules |
| Zips parallel lists into objects, e.g. seqcol `names` + `lengths` into `sequences[]` | 252 rules |
| Changes the value (regex, value map, accession parsing, dates, casts, ...) | 125 rules |
| Says in words what it loses (`lossy`) | 177 rules |
| Groups many rows of a file into one record | 37 files |
| Lists every field it does not map, with a reason | 898 fields |

## SSSOM: used as an export, not as the format

SSSOM can hold one part of a crosswalk: "native field X matches core field Y, this
closely." It cannot hold transforms, directions, keyed list elements, row grouping or
fallbacks. Its ids cannot even contain brackets, so a target like
`labels[namespace=galaxy.dbkey].value` has to be shortened to `labels.value` in the id.

So `refmeta sssom` (and `tools/build_sssom.py`) writes one SSSOM mapping set per crosswalk,
generated from the crosswalk:

- one row per rule: native field, core field, predicate, and a comment that names the
  transform and repeats the `lossy` note;
- the full core path, with its conditions, in `object_label`;
- one `sssom:NoTermFound` row per unmapped field, with the reason;
- the predicate from the rule's optional `match` key (`exact`, `close`, `broad`, `narrow`,
  `related`). Without one, a both-way rule with no `lossy` note is `skos:exactMatch` (the
  round-trip tests already hold those rules to exact), and anything else is
  `skos:closeMatch`.

Today the export has 980 exact matches, 187 close matches and 901 no-match rows. All 100
files pass `sssom validate` (sssom-py 0.4.17) with no warnings, and `sssom convert` turns
them into RDF and JSON.

The close matches are where curation helps: many are really broader or narrower (for
example FHR `accessionID` is any archive's id, refmeta's field is the assembly accession).
Setting `match` on those rules makes the export more useful without touching the engine.

## LinkML-Map: tried, not adopted

LinkML-Map is the format the working group names for proposition mappings, and it is
active (v0.6.0, November 2026). Its specification already carries the metadata the
recommendations ask for (id, title, license, version, authors, reviewers, content URL). We
wrote two crosswalks in it and ran them ([trial](../references/linkml-map-trial/)).

What worked:

- `refgenie_api_alias` to core gave the same core record as `refmeta core` for the fields
  covered, including nested objects, keyed lists and zipped arrays.
- `galaxy_len` rows became one record with a `sequences` list, once the rows were wrapped
  in a container object.

What did not:

1. **One direction only.** `linkml-map invert` refuses any spec with an expression, and in
   non-strict mode it drops the nested fields. 1,142 of refmeta's rules work both ways, so
   every format would need two hand-kept specs: 200 files that must agree.
2. **Python in the mapping.** Regex extraction, accession namespaces and zipping lists
   needed custom Python functions passed with `--functions`. Keyed list elements had to be
   written as list-and-dict expressions. The declarative part shrinks to plain copies.
3. **A LinkML schema for every format.** LinkML-Map reads data only through a LinkML schema
   and rejects any key the schema does not declare. refmeta has no LinkML schemas; it would
   need 100 source schemas plus the core. Converting `core.schema.json` automatically
   (schema-automator) failed on enums, constants and maps.
4. **Row grouping is partial.** A table input gives one output per row. Merging rows that
   share a key, or copying a row once per value, has no equivalent. The data model lists
   aggregation, but the transformer does not run it.
5. **Nowhere to say what is lost.** A slot derivation has no field for a lossy note, a
   match strength or a worked example. These are what refmeta is for.
6. **Weight.** linkml-map brings about 175 packages (duckdb, pint, pydantic, linkml). refmeta
   needs only PyYAML, which is what lets the converter run in the browser through Pyodide.

## Something else?

- **XSLT** works on XML, and **SPARQL CONSTRUCT** and **RML/YARRRML** produce RDF. refmeta's
  inputs are JSON, YAML and text tables, and its output is JSON, so none of these fit.
- **SeMRA** merges and reasons over large SSSOM term-mapping sets. It does not apply here.
  "Sesame" (now Eclipse RDF4J) is an RDF database, not a mapping format.
- **LinkML element mappings** (`exact_mappings`, `broad_mappings` on a slot) say the same
  thing as the SSSOM export. FHR uses them in `fhr_linkml.yml`. If the core ever gets a
  LinkML version, the same match data could be written there too.

## The FAIR Mappings recommendations: where refmeta stands

From [recommendation.md](../references/rda-fair-mappings/recommendation.md):

| Recommendation | Status |
|---|---|
| T-Rec 1.1 Use SSSOM | Done, as an export (`mapping/sssom/`) |
| T-Rec 1.2 Linked-data serialisations | Possible now (`sssom convert -O rdf`); not yet published |
| T-Rec 1.3 Metadata aligned with DC/DCAT | Partly: the SSSOM header maps to Dublin Core terms in RDF |
| T-Rec 2.1 Minimum metadata | Partly. Has: license, version, sources, justification, tool, labels, descriptions. Missing: dates and source versions. Authors, creators and reviewers are left out on purpose |
| T-Rec 3.1 Persistent, resolvable ids | Partly. Ids use the site, `https://refgenie.github.io/refmeta/`. The site serves each set at its `mapping_set_id` and the core schema at its `$id`, and a `refmeta:` field id opens that field on the terms page. Format and native-field ids are names only and do not resolve |
| T-Rec 3.2 PID policy | Not yet |
| T-Rec 4 Publish to a mapping repository (e.g. MSCR) | Not yet |

## Decisions

1. **Base URL.** Ids use `https://refgenie.github.io/refmeta/`. The Pages job copies
   `mapping/sssom/` to `/sssom/` and `mapping/core.schema.json` to
   `/core/0.1/core.schema.json`, so those ids resolve.
2. **Authors.** No authors, creators or reviewers are listed in the mapping sets.

## Open question

**`mapping_justification`.** The export says `semapv:ManualMappingCuration`. If
crosswalks were drafted by software and then reviewed, `semapv:MappingReview` plus the
drafting method may be more accurate.
