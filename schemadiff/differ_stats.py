"""Compute statistical metrics over a ComparisonResult."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiffStats:
    """Aggregated counts from a schema comparison."""

    tables_added: int = 0
    tables_removed: int = 0
    tables_modified: int = 0
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0

    @property
    def total_table_changes(self) -> int:
        return self.tables_added + self.tables_removed + self.tables_modified

    @property
    def total_column_changes(self) -> int:
        return self.columns_added + self.columns_removed + self.columns_modified

    @property
    def total_changes(self) -> int:
        return self.total_table_changes + self.total_column_changes

    def to_dict(self) -> dict[str, Any]:
        return {
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "tables_modified": self.tables_modified,
            "columns_added": self.columns_added,
            "columns_removed": self.columns_removed,
            "columns_modified": self.columns_modified,
            "total_table_changes": self.total_table_changes,
            "total_column_changes": self.total_column_changes,
            "total_changes": self.total_changes,
        }


def compute_stats(result: Any) -> DiffStats:
    """Derive a DiffStats from any ComparisonResult-compatible object.

    The *result* object is expected to expose:
        - tables_added()  -> iterable of table names
        - tables_removed() -> iterable of table names
        - tables_modified() -> iterable of table names
        - column_diffs(table_name) -> iterable of ColumnDiff-like objects
          each with attributes: added (bool), removed (bool)
    """
    stats = DiffStats()

    stats.tables_added = len(list(result.tables_added()))
    stats.tables_removed = len(list(result.tables_removed()))

    modified = list(result.tables_modified())
    stats.tables_modified = len(modified)

    for table_name in modified:
        for col_diff in result.column_diffs(table_name):
            if getattr(col_diff, "added", False):
                stats.columns_added += 1
            elif getattr(col_diff, "removed", False):
                stats.columns_removed += 1
            else:
                stats.columns_modified += 1

    return stats
