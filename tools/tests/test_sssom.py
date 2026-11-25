"""The SSSOM export: every crosswalk field appears, ids are valid CURIEs, and the
predicate follows the rule's lossy note."""
import re

import pytest

from refmeta import sssom
from refmeta.convert import crosswalk_ids

LOCAL_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:[A-Za-z0-9._~%-]+$")


@pytest.mark.parametrize("fid", crosswalk_ids())
def test_every_field_exported(fid):
    cw = sssom._raw(fid)
    _, rows = sssom.mapping_set(fid)
    assert len(rows) == len(cw["rules"]) + len(cw.get("unmapped", []))
    for r in rows:
        assert LOCAL_ID.match(r["subject_id"]), r["subject_id"]
        assert LOCAL_ID.match(r["object_id"]), r["object_id"]
    for rule, row in zip(cw["rules"], rows):
        if rule.get("match"):
            assert row["predicate_id"] == sssom.MATCH[rule["match"]]
        elif rule.get("lossy") or rule["direction"] != "both":
            assert row["predicate_id"] == "skos:closeMatch"
        else:
            assert row["predicate_id"] == "skos:exactMatch"
