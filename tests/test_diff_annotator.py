"""Tests for schemadiff.diff_annotator."""

from __future__ import annotations

import pytest
from schemadiff.diff_annotator import (
    Annotation,
    AnnotatedResult,
    annotate_result,
    _classify_col_diff,
    _col_diff_message,
)


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class _ColDiff:
    def __init__(self, column_name, old=object(), new=object()):
        self.column_name = column_name
        self.old = old
        self.new = new


class _MockResult:
    def __init__(self, added=(), removed=(), cols_changed=None):
        self._added = list(added)
        self._removed = list(removed)
        self._cols_changed = cols_changed or {}

    def has_changes(self):
        return bool(self._added or self._removed or self._cols_changed)

    def tables_added(self):
        return self._added

    def tables_removed(self):
        return self._removed

    def columns_changed(self):
        return self._cols_changed

    def to_dict(self):
        return {}


# ---------------------------------------------------------------------------
# Annotation dataclass
# ---------------------------------------------------------------------------

def test_annotation_to_dict_has_all_keys():
    ann = Annotation(target="table:t", kind="added", message="msg")
    d = ann.to_dict()
    assert set(d.keys()) == {"target", "kind", "message", "severity", "meta"}


def test_annotation_default_severity_is_info():
    ann = Annotation(target="x", kind="added", message="y")
    assert ann.severity == "info"


# ---------------------------------------------------------------------------
# annotate_result — table-level
# ---------------------------------------------------------------------------

def test_no_changes_produces_empty_annotations():
    result = _MockResult()
    ar = annotate_result(result)
    assert ar.annotations == []
    assert not ar.has_changes()


def test_table_added_annotation():
    result = _MockResult(added=["orders"])
    ar = annotate_result(result)
    assert len(ar.annotations) == 1
    ann = ar.annotations[0]
    assert ann.kind == "added"
    assert ann.target == "table:orders"
    assert ann.severity == "info"
    assert "orders" in ann.message


def test_table_removed_annotation_is_critical():
    result = _MockResult(removed=["legacy"])
    ar = annotate_result(result)
    assert len(ar.annotations) == 1
    ann = ar.annotations[0]
    assert ann.severity == "critical"
    assert ann.kind == "removed"


# ---------------------------------------------------------------------------
# annotate_result — column-level
# ---------------------------------------------------------------------------

def test_column_added_annotation():
    col = _ColDiff("email", old=None, new=object())
    result = _MockResult(cols_changed={"users": [col]})
    ar = annotate_result(result)
    ann = ar.annotations[0]
    assert ann.kind == "added"
    assert ann.target == "column:users.email"
    assert ann.severity == "info"


def test_column_removed_annotation_is_critical():
    col = _ColDiff("old_col", old=object(), new=None)
    result = _MockResult(cols_changed={"users": [col]})
    ar = annotate_result(result)
    ann = ar.annotations[0]
    assert ann.kind == "removed"
    assert ann.severity == "critical"


def test_column_modified_annotation_is_warning():
    col = _ColDiff("age", old=object(), new=object())
    result = _MockResult(cols_changed={"users": [col]})
    ar = annotate_result(result)
    ann = ar.annotations[0]
    assert ann.kind == "modified"
    assert ann.severity == "warning"


def test_multiple_tables_and_columns():
    cols = [_ColDiff("x", old=None, new=object()), _ColDiff("y", old=object(), new=None)]
    result = _MockResult(added=["tbl1"], cols_changed={"tbl2": cols})
    ar = annotate_result(result)
    assert len(ar.annotations) == 3


# ---------------------------------------------------------------------------
# AnnotatedResult.to_dict
# ---------------------------------------------------------------------------

def test_annotated_result_to_dict_structure():
    result = _MockResult(added=["t"])
    ar = annotate_result(result)
    d = ar.to_dict()
    assert "result" in d
    assert "annotations" in d
    assert isinstance(d["annotations"], list)
