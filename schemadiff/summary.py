"""Summary statistics for schema comparison results."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SchemaSummary:
    total_tables_old: int = 0
    total_tables_new: int = 0
    tables_added: int = 0
    tables_removed: int = 0
    tables_modified: int = 0
    tables_unchanged: int = 0
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0
    change_breakdown: Dict[str, int] = field(default_factory=dict)

    @property
    def total_changes(self) -> int:
        return (
            self.tables_added
            + self.tables_removed
            + self.columns_added
            + self.columns_removed
            + self.columns_modified
        )

    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0

    def to_dict(self) -> dict:
        return {
            "total_tables_old": self.total_tables_old,
            "total_tables_new": self.total_tables_new,
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "tables_modified": self.tables_modified,
            "tables_unchanged": self.tables_unchanged,
            "columns_added": self.columns_added,
            "columns_removed": self.columns_removed,
            "columns_modified": self.columns_modified,
            "total_changes": self.total_changes,
            "change_breakdown": self.change_breakdown,
        }


def summarize(result) -> SchemaSummary:
    """Build a SchemaSummary from a ComparisonResult or FilteredResult."""
    summary = SchemaSummary()

    added_tables = list(result.tables_added())
    removed_tables = list(result.tables_removed())
    modified_tables = list(result.tables_modified())

    summary.tables_added = len(added_tables)
    summary.tables_removed = len(removed_tables)
    summary.tables_modified = len(modified_tables)

    for table_diff in modified_tables:
        summary.columns_added += len(table_diff.columns_added)
        summary.columns_removed += len(table_diff.columns_removed)
        summary.columns_modified += len(table_diff.columns_modified)

    summary.change_breakdown = {
        "tables_added": summary.tables_added,
        "tables_removed": summary.tables_removed,
        "columns_added": summary.columns_added,
        "columns_removed": summary.columns_removed,
        "columns_modified": summary.columns_modified,
    }

    return summary
