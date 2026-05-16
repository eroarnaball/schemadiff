"""Build a dependency/relationship graph from a ComparisonResult.

Each table is a node; edges represent foreign-key-style column name
patterns (col ending with '_id' treated as a potential FK to another
table).  The graph is intentionally lightweight – it only uses the
standard library.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


class GraphError(Exception):
    """Raised when graph construction fails."""


@dataclass
class DiffGraph:
    """Directed graph of tables and their drift relationships."""

    nodes: Set[str] = field(default_factory=set)
    # edges: source_table -> list of target_table names
    edges: Dict[str, List[str]] = field(default_factory=dict)
    # per-node change flag
    changed: Dict[str, bool] = field(default_factory=dict)

    def neighbours(self, table: str) -> List[str]:
        return self.edges.get(table, [])

    def changed_tables(self) -> List[str]:
        return [t for t, v in self.changed.items() if v]

    def to_dict(self) -> dict:
        return {
            "nodes": sorted(self.nodes),
            "edges": {k: sorted(v) for k, v in sorted(self.edges.items())},
            "changed": {k: v for k, v in sorted(self.changed.items())},
        }


def _infer_edges(table_name: str, column_names: List[str], all_tables: Set[str]) -> List[str]:
    """Return tables that *table_name* likely references via FK columns."""
    targets: List[str] = []
    for col in column_names:
        if col.endswith("_id"):
            candidate = col[:-3]  # strip '_id'
            if candidate in all_tables and candidate != table_name:
                targets.append(candidate)
    return targets


def build_graph(result) -> DiffGraph:
    """Build a DiffGraph from a ComparisonResult (or compatible object).

    Parameters
    ----------
    result:
        Any object exposing ``tables_added``, ``tables_removed``,
        ``tables_modified``, ``tables_unchanged`` collections and where
        each table entry has a ``.columns`` mapping.
    """
    graph = DiffGraph()

    def _register(table_name: str, column_names: List[str], is_changed: bool) -> None:
        graph.nodes.add(table_name)
        graph.changed[table_name] = is_changed
        graph.edges.setdefault(table_name, [])
        for col in column_names:
            graph.edges[table_name]  # ensure key exists

    # Collect all table names first so edge inference works
    all_tables: Set[str] = set()
    for collection in (
        result.tables_added,
        result.tables_removed,
        result.tables_modified,
        result.tables_unchanged,
    ):
        for tname in collection:
            all_tables.add(tname)

    def _cols(collection, tname):
        obj = collection[tname]
        if hasattr(obj, "columns"):
            return list(obj.columns.keys())
        return []

    for tname in result.tables_added:
        cols = _cols(result.tables_added, tname)
        _register(tname, cols, True)
        graph.edges[tname] = _infer_edges(tname, cols, all_tables)

    for tname in result.tables_removed:
        cols = _cols(result.tables_removed, tname)
        _register(tname, cols, True)
        graph.edges[tname] = _infer_edges(tname, cols, all_tables)

    for tname in result.tables_modified:
        cols = _cols(result.tables_modified, tname)
        _register(tname, cols, True)
        graph.edges[tname] = _infer_edges(tname, cols, all_tables)

    for tname in result.tables_unchanged:
        cols = _cols(result.tables_unchanged, tname)
        _register(tname, cols, False)
        graph.edges[tname] = _infer_edges(tname, cols, all_tables)

    return graph
