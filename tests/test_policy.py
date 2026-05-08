"""Tests for schemadiff.policy — evaluate_policy."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Dict, List, Optional

import pytest

from schemadiff.policy import PolicyRule, PolicyViolation, evaluate_policy


# ---------------------------------------------------------------------------
# Minimal fakes that mimic ComparisonResult / TableDiff / ColumnDiff
# ---------------------------------------------------------------------------

def _col_diff(type_changed=False, nullable_changed=False):
    return SimpleNamespace(type_changed=type_changed, nullable_changed=nullable_changed)


def _table_diff(added=(), removed=(), modified=None):
    return SimpleNamespace(
        columns_added=list(added),
        columns_removed=list(removed),
        columns_modified=dict(modified or {}),
    )


def _result(tables_added=(), tables_removed=(), tables_modified=None):
    return SimpleNamespace(
        tables_added=list(tables_added),
        tables_removed=list(tables_removed),
        tables_modified=dict(tables_modified or {}),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_rules_returns_empty():
    result = _result(tables_added=["users"])
    assert evaluate_policy([], result) == []


def test_table_added_violation():
    rules = [PolicyRule(change_type="added", message="No new tables")]
    result = _result(tables_added=["orders"])
    violations = evaluate_policy(rules, result)
    assert len(violations) == 1
    assert violations[0].table == "orders"
    assert violations[0].column is None
    assert violations[0].change_type == "added"


def test_table_removed_violation():
    rules = [PolicyRule(change_type="removed", message="No dropped tables")]
    result = _result(tables_removed=["legacy"])
    violations = evaluate_policy(rules, result)
    assert len(violations) == 1
    assert violations[0].table == "legacy"


def test_rule_scoped_to_specific_table_no_match():
    rules = [PolicyRule(change_type="added", tables=["payments"], message="x")]
    result = _result(tables_added=["orders"])
    assert evaluate_policy(rules, result) == []


def test_column_removed_violation():
    rules = [PolicyRule(change_type="removed", message="No column drops")]
    result = _result(
        tables_modified={"users": _table_diff(removed=["email"])}
    )
    violations = evaluate_policy(rules, result)
    assert len(violations) == 1
    assert violations[0].column == "email"


def test_type_changed_violation():
    rules = [PolicyRule(change_type="type_changed", message="No type changes")]
    result = _result(
        tables_modified={
            "users": _table_diff(modified={"age": _col_diff(type_changed=True)})
        }
    )
    violations = evaluate_policy(rules, result)
    assert len(violations) == 1
    assert violations[0].change_type == "type_changed"


def test_nullable_changed_violation():
    rules = [PolicyRule(change_type="nullable_changed", message="No nullability changes")]
    result = _result(
        tables_modified={
            "orders": _table_diff(modified={"total": _col_diff(nullable_changed=True)})
        }
    )
    violations = evaluate_policy(rules, result)
    assert len(violations) == 1


def test_violation_to_dict():
    rule = PolicyRule(change_type="removed", message="No drops")
    v = PolicyViolation(rule=rule, table="t", column="c", change_type="removed")
    d = v.to_dict()
    assert d["message"] == "No drops"
    assert d["table"] == "t"
    assert d["column"] == "c"


def test_multiple_rules_multiple_violations():
    rules = [
        PolicyRule(change_type="added"),
        PolicyRule(change_type="removed"),
    ]
    result = _result(
        tables_added=["new_table"],
        tables_removed=["old_table"],
    )
    violations = evaluate_policy(rules, result)
    assert len(violations) == 2
