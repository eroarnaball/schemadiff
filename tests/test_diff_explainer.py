"""Tests for schemadiff.diff_explainer."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Dict

import pytest

from schemadiff.diff_explainer import Explanation, explain_result, _explain_column_diff


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------

def _col_diff(added=False, removed=False, type_changed=False,
              nullable_changed=False, default_changed=False,
              old_type="int", new_type="varchar"):
    return SimpleNamespace(
        added=added, removed=removed,
        type_changed=type_changed, nullable_changed=nullable_changed,
        default_changed=default_changed,
        old_type=old_type, new_type=new_type,
    )


def _table_diff(column_diffs: Dict):
    return SimpleNamespace(column_diffs=column_diffs)


def _result(tables_added=(), tables_removed=(), tables_modified=None):
    return SimpleNamespace(
        tables_added=list(tables_added),
        tables_removed=list(tables_removed),
        tables_modified=tables_modified or {},
    )


# ---------------------------------------------------------------------------
# Explanation.to_dict
# ---------------------------------------------------------------------------

def test_explanation_to_dict_has_all_keys():
    exp = Explanation(
        change_type="table_added",
        table_name="users",
        column_name=None,
        message="Table 'users' is new.",
        suggestion="Check grants.",
    )
    d = exp.to_dict()
    assert set(d) == {"change_type", "table_name", "column_name", "message", "suggestion"}


# ---------------------------------------------------------------------------
# _explain_column_diff
# ---------------------------------------------------------------------------

def test_explain_column_added():
    exp = _explain_column_diff("orders", "status", _col_diff(added=True))
    assert exp.change_type == "column_added"
    assert "status" in exp.message
    assert "orders" in exp.message
    assert exp.suggestion is not None


def test_explain_column_removed():
    exp = _explain_column_diff("orders", "legacy_id", _col_diff(removed=True))
    assert exp.change_type == "column_removed"
    assert "legacy_id" in exp.message


def test_explain_column_type_changed():
    exp = _explain_column_diff(
        "products", "price",
        _col_diff(type_changed=True, old_type="int", new_type="decimal")
    )
    assert exp.change_type == "column_modified"
    assert "int" in exp.message
    assert "decimal" in exp.message


def test_explain_column_nullable_changed():
    exp = _explain_column_diff("users", "email", _col_diff(nullable_changed=True))
    assert exp.change_type == "column_modified"
    assert "nullability" in exp.message


# ---------------------------------------------------------------------------
# explain_result
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_list():
    assert explain_result(_result()) == []


def test_table_added_produces_one_explanation():
    exps = explain_result(_result(tables_added=["audit_log"]))
    assert len(exps) == 1
    assert exps[0].change_type == "table_added"
    assert exps[0].table_name == "audit_log"


def test_table_removed_produces_one_explanation():
    exps = explain_result(_result(tables_removed=["legacy_table"]))
    assert len(exps) == 1
    assert exps[0].change_type == "table_removed"


def test_column_diff_included_in_explanations():
    mods = {
        "users": _table_diff({
            "email": _col_diff(added=True),
            "phone": _col_diff(removed=True),
        })
    }
    exps = explain_result(_result(tables_modified=mods))
    types = {e.change_type for e in exps}
    assert "column_added" in types
    assert "column_removed" in types
    assert all(e.table_name == "users" for e in exps)


def test_mixed_changes_all_explained():
    mods = {
        "orders": _table_diff({"status": _col_diff(type_changed=True)})
    }
    exps = explain_result(_result(
        tables_added=["new_tbl"],
        tables_removed=["old_tbl"],
        tables_modified=mods,
    ))
    assert len(exps) == 3
    change_types = [e.change_type for e in exps]
    assert "table_added" in change_types
    assert "table_removed" in change_types
    assert "column_modified" in change_types
