"""Human-readable explanations for individual diff entries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Explanation:
    """A human-readable explanation for a single schema change."""

    change_type: str  # 'table_added', 'table_removed', 'column_added',
                      # 'column_removed', 'column_modified'
    table_name: str
    column_name: Optional[str]
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "message": self.message,
            "suggestion": self.suggestion,
        }


def _explain_column_diff(table_name: str, col_name: str, col_diff) -> Explanation:
    """Return an Explanation for a single ColumnDiff."""
    if col_diff.added:
        return Explanation(
            change_type="column_added",
            table_name=table_name,
            column_name=col_name,
            message=f"Column '{col_name}' was added to table '{table_name}'.",
            suggestion="Ensure downstream consumers handle the new column.",
        )
    if col_diff.removed:
        return Explanation(
            change_type="column_removed",
            table_name=table_name,
            column_name=col_name,
            message=f"Column '{col_name}' was removed from table '{table_name}'.",
            suggestion="Verify no existing queries depend on this column.",
        )
    parts: List[str] = []
    if col_diff.type_changed:
        old = getattr(col_diff, "old_type", "unknown")
        new = getattr(col_diff, "new_type", "unknown")
        parts.append(f"type changed from '{old}' to '{new}'")
    if col_diff.nullable_changed:
        parts.append("nullability changed")
    if col_diff.default_changed:
        parts.append("default value changed")
    detail = "; ".join(parts) if parts else "attributes changed"
    return Explanation(
        change_type="column_modified",
        table_name=table_name,
        column_name=col_name,
        message=f"Column '{col_name}' in table '{table_name}' was modified: {detail}.",
        suggestion="Review migration scripts to handle the attribute change safely.",
    )


def explain_result(result) -> List[Explanation]:
    """Generate explanations for every change in *result*.

    *result* is expected to expose the same interface as
    ``comparator.ComparisonResult``.
    """
    explanations: List[Explanation] = []

    for tname in result.tables_added:
        explanations.append(
            Explanation(
                change_type="table_added",
                table_name=tname,
                column_name=None,
                message=f"Table '{tname}' is new in the target schema.",
                suggestion="Confirm the table is intentional and apply any required grants.",
            )
        )

    for tname in result.tables_removed:
        explanations.append(
            Explanation(
                change_type="table_removed",
                table_name=tname,
                column_name=None,
                message=f"Table '{tname}' was removed from the target schema.",
                suggestion="Check that no application code still references this table.",
            )
        )

    for tname, table_diff in result.tables_modified.items():
        for col_name, col_diff in table_diff.column_diffs.items():
            explanations.append(_explain_column_diff(tname, col_name, col_diff))

    return explanations
