"""Schema drift scoring — assigns a numeric severity score to a ComparisonResult."""

from dataclasses import dataclass
from typing import Dict

# Weights for each type of change (higher = more severe)
_WEIGHTS: Dict[str, int] = {
    "table_added": 2,
    "table_removed": 5,
    "column_added": 1,
    "column_removed": 4,
    "column_modified": 3,
}


@dataclass
class DriftScore:
    """Holds the computed drift score and a breakdown by change type."""

    total: int
    breakdown: Dict[str, int]

    @property
    def severity(self) -> str:
        """Human-readable severity label based on total score."""
        if self.total == 0:
            return "none"
        if self.total <= 5:
            return "low"
        if self.total <= 15:
            return "medium"
        return "high"

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "severity": self.severity,
            "breakdown": self.breakdown,
        }


def score_result(result) -> DriftScore:
    """Compute a DriftScore from a ComparisonResult (or FilteredResult).

    The *result* object must expose:
      - tables_added(), tables_removed() — iterables of table names
      - column_changes(table) — iterable of ColumnDiff-like objects with
        attributes: added (bool), removed (bool)
    """
    breakdown: Dict[str, int] = {k: 0 for k in _WEIGHTS}

    for _ in result.tables_added():
        breakdown["table_added"] += _WEIGHTS["table_added"]

    for _ in result.tables_removed():
        breakdown["table_removed"] += _WEIGHTS["table_removed"]

    for table_name in list(result.tables_added()) + list(result.tables_removed()):
        # Skip per-column scoring for wholly added/removed tables
        pass

    # Score column-level changes on tables that exist in both schemas
    changed_tables = (
        set(result.tables_added())
        | set(result.tables_removed())
    )
    # column_changes is expected to return diffs only for surviving tables
    for col_diff in _iter_all_column_diffs(result, changed_tables):
        if getattr(col_diff, "added", False):
            breakdown["column_added"] += _WEIGHTS["column_added"]
        elif getattr(col_diff, "removed", False):
            breakdown["column_removed"] += _WEIGHTS["column_removed"]
        else:
            breakdown["column_modified"] += _WEIGHTS["column_modified"]

    total = sum(breakdown.values())
    return DriftScore(total=total, breakdown=breakdown)


def _iter_all_column_diffs(result, skip_tables):
    """Yield every ColumnDiff from tables not in *skip_tables*."""
    get_col_changes = getattr(result, "column_changes", None)
    if get_col_changes is None:
        return
    # Try to get all modified table names via a helper attribute
    modified = getattr(result, "tables_modified", lambda: [])()
    for table_name in modified:
        if table_name not in skip_tables:
            yield from get_col_changes(table_name)
