"""Tests for schemadiff.diff_graph."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Dict

import pytest

from schemadiff.diff_graph import DiffGraph, GraphError, build_graph, _infer_edges


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table(col_names):
    """Return a fake table object with a .columns mapping."""
    return SimpleNamespace(columns={c: object() for c in col_names})


def _make_result(
    added: Dict[str, list] | None = None,
    removed: Dict[str, list] | None = None,
    modified: Dict[str, list] | None = None,
    unchanged: Dict[str, list] | None = None,
):
    """Build a minimal ComparisonResult-like object."""
    def _build(spec):
        return {name: _table(cols) for name, cols in (spec or {}).items()}

    return SimpleNamespace(
        tables_added=_build(added),
        tables_removed=_build(removed),
        tables_modified=_build(modified),
        tables_unchanged=_build(unchanged),
    )


# ---------------------------------------------------------------------------
# Unit tests for _infer_edges
# ---------------------------------------------------------------------------

def test_infer_edges_no_fk_columns():
    edges = _infer_edges("orders", ["id", "amount"], {"orders", "users"})
    assert edges == []


def test_infer_edges_detects_fk():
    edges = _infer_edges("orders", ["id", "user_id"], {"orders", "user"})
    assert "user" in edges


def test_infer_edges_ignores_self_reference():
    edges = _infer_edges("user", ["user_id"], {"user"})
    assert edges == []


def test_infer_edges_ignores_missing_table():
    edges = _infer_edges("orders", ["product_id"], {"orders", "user"})
    assert edges == []  # 'product' not in all_tables


# ---------------------------------------------------------------------------
# build_graph tests
# ---------------------------------------------------------------------------

def test_build_graph_empty_result():
    result = _make_result()
    graph = build_graph(result)
    assert isinstance(graph, DiffGraph)
    assert len(graph.nodes) == 0


def test_build_graph_nodes_populated():
    result = _make_result(
        added={"orders": ["id", "user_id"]},
        unchanged={"user": ["id", "name"]},
    )
    graph = build_graph(result)
    assert "orders" in graph.nodes
    assert "user" in graph.nodes


def test_build_graph_changed_flags():
    result = _make_result(
        added={"orders": ["id"]},
        removed={"legacy": ["id"]},
        modified={"products": ["id", "price"]},
        unchanged={"user": ["id"]},
    )
    graph = build_graph(result)
    assert graph.changed["orders"] is True
    assert graph.changed["legacy"] is True
    assert graph.changed["products"] is True
    assert graph.changed["user"] is False


def test_build_graph_changed_tables_list():
    result = _make_result(
        modified={"products": ["id"]},
        unchanged={"user": ["id"]},
    )
    graph = build_graph(result)
    assert graph.changed_tables() == ["products"]


def test_build_graph_edge_inferred():
    result = _make_result(
        added={"orders": ["id", "user_id"]},
        unchanged={"user": ["id", "name"]},
    )
    graph = build_graph(result)
    assert "user" in graph.neighbours("orders")


def test_build_graph_no_spurious_edges():
    result = _make_result(
        added={"orders": ["id", "amount"]},
        unchanged={"user": ["id"]},
    )
    graph = build_graph(result)
    assert graph.neighbours("orders") == []


# ---------------------------------------------------------------------------
# DiffGraph.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_structure():
    result = _make_result(
        modified={"orders": ["id", "user_id"]},
        unchanged={"user": ["id"]},
    )
    graph = build_graph(result)
    d = graph.to_dict()
    assert "nodes" in d
    assert "edges" in d
    assert "changed" in d
    assert "orders" in d["nodes"]
    assert "user" in d["nodes"]
    assert d["changed"]["orders"] is True
    assert d["changed"]["user"] is False
