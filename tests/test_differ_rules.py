"""Tests for schemadiff.differ_rules."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Dict

import pytest

from schemadiff.differ_rules import apply_rules, RuleReport, RuleViolation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _ColDiff:
    def __init__(self, old_type=None, old_nullable=False, new_type=None, new_nullable=False,
                 old_exists=True, new_exists=True):
        self.old = SimpleNamespace(col_type=old_type, nullable=old_nullable) if old_exists else None
        self.new = SimpleNamespace(col_type=new_type, nullable=new_nullable) if new_exists else None


class _MockResult:
    def __init__(self, tables_removed=(), tables_added=(), columns_changed: Dict | None = None):
        self.tables_removed = list(tables_removed)
        self.tables_added = list(tables_added)
        self.columns_changed = columns_changed or {}


# ---------------------------------------------------------------------------
# RuleReport
# ---------------------------------------------------------------------------

def test_rule_report_no_violations():
    report = RuleReport()
    assert not report.has_violations
    assert report.to_dict()["total"] == 0


def test_rule_report_by_severity():
    v1 = RuleViolation("r1", "t", None, "msg", "error")
    v2 = RuleViolation("r2", "t", "c", "msg", "warning")
    report = RuleReport([v1, v2])
    assert len(report.by_severity("error")) == 1
    assert len(report.by_severity("warning")) == 1
    assert len(report.by_severity("info")) == 0


# ---------------------------------------------------------------------------
# no_table_removed
# ---------------------------------------------------------------------------

def test_no_table_removed_violation():
    result = _MockResult(tables_removed=["orders"])
    report = apply_rules(result)
    assert report.has_violations
    v = report.violations[0]
    assert v.rule_name == "no_table_removed"
    assert v.table == "orders"
    assert v.severity == "error"


def test_no_table_removed_passes_when_nothing_removed():
    result = _MockResult()
    report = apply_rules(result, rules=["no_table_removed"])
    assert not report.has_violations


# ---------------------------------------------------------------------------
# no_column_removed
# ---------------------------------------------------------------------------

def test_no_column_removed_violation():
    result = _MockResult(columns_changed={
        "users": {"email": _ColDiff(old_type="text", new_exists=False)}
    })
    report = apply_rules(result, rules=["no_column_removed"])
    assert report.has_violations
    assert report.violations[0].column == "email"


# ---------------------------------------------------------------------------
# no_type_change
# ---------------------------------------------------------------------------

def test_no_type_change_violation():
    result = _MockResult(columns_changed={
        "users": {"age": _ColDiff(old_type="int", new_type="text")}
    })
    report = apply_rules(result, rules=["no_type_change"])
    assert report.has_violations
    v = report.violations[0]
    assert v.rule_name == "no_type_change"
    assert v.severity == "warning"


def test_no_type_change_passes_same_type():
    result = _MockResult(columns_changed={
        "users": {"age": _ColDiff(old_type="int", new_type="int")}
    })
    report = apply_rules(result, rules=["no_type_change"])
    assert not report.has_violations


# ---------------------------------------------------------------------------
# no_nullable_loosened
# ---------------------------------------------------------------------------

def test_no_nullable_loosened_violation():
    result = _MockResult(columns_changed={
        "users": {"name": _ColDiff(old_type="text", old_nullable=False, new_type="text", new_nullable=True)}
    })
    report = apply_rules(result, rules=["no_nullable_loosened"])
    assert report.has_violations
    assert report.violations[0].rule_name == "no_nullable_loosened"


def test_nullable_tightened_is_not_a_violation():
    result = _MockResult(columns_changed={
        "users": {"name": _ColDiff(old_type="text", old_nullable=True, new_type="text", new_nullable=False)}
    })
    report = apply_rules(result, rules=["no_nullable_loosened"])
    assert not report.has_violations


# ---------------------------------------------------------------------------
# Rule filtering
# ---------------------------------------------------------------------------

def test_only_requested_rules_fire():
    result = _MockResult(
        tables_removed=["old_table"],
        columns_changed={"users": {"age": _ColDiff(old_type="int", new_type="text")}},
    )
    report = apply_rules(result, rules=["no_type_change"])
    # only type-change rule active; table removal should NOT appear
    assert all(v.rule_name == "no_type_change" for v in report.violations)


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_violation_to_dict_keys():
    v = RuleViolation("no_table_removed", "orders", None, "removed", "error")
    d = v.to_dict()
    assert set(d.keys()) == {"rule", "table", "column", "message", "severity"}
