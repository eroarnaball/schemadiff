"""Filter utilities for narrowing schema diff results."""

from typing import Optional, List
from schemadiff.comparator import ComparisonResult


def filter_result(
    result: ComparisonResult,
    include_tables: Optional[List[str]] = None,
    exclude_tables: Optional[List[str]] = None,
    change_types: Optional[List[str]] = None,
) -> "FilteredResult":
    """Return a filtered view of a ComparisonResult.

    Args:
        result: The full comparison result to filter.
        include_tables: If provided, only include these table names.
        exclude_tables: If provided, exclude these table names.
        change_types: Subset of ('added', 'removed', 'modified') to include.
    """
    allowed_types = set(change_types) if change_types else {"added", "removed", "modified"}

    tables_added = [
        t for t in result.tables_added()
        if "added" in allowed_types
        and _table_allowed(t, include_tables, exclude_tables)
    ]
    tables_removed = [
        t for t in result.tables_removed()
        if "removed" in allowed_types
        and _table_allowed(t, include_tables, exclude_tables)
    ]
    tables_modified = {
        name: diff
        for name, diff in result.tables_modified().items()
        if "modified" in allowed_types
        and _table_allowed(name, include_tables, exclude_tables)
    }

    return FilteredResult(
        tables_added=tables_added,
        tables_removed=tables_removed,
        tables_modified=tables_modified,
    )


def _table_allowed(
    name: str,
    include_tables: Optional[List[str]],
    exclude_tables: Optional[List[str]],
) -> bool:
    if include_tables is not None and name not in include_tables:
        return False
    if exclude_tables is not None and name in exclude_tables:
        return False
    return True


class FilteredResult:
    """A filtered subset of a ComparisonResult."""

    def __init__(self, tables_added, tables_removed, tables_modified):
        self._tables_added = tables_added
        self._tables_removed = tables_removed
        self._tables_modified = tables_modified

    def has_changes(self) -> bool:
        return bool(self._tables_added or self._tables_removed or self._tables_modified)

    def tables_added(self) -> List[str]:
        return list(self._tables_added)

    def tables_removed(self) -> List[str]:
        return list(self._tables_removed)

    def tables_modified(self) -> dict:
        return dict(self._tables_modified)

    def summary(self) -> str:
        parts = []
        if self._tables_added:
            parts.append(f"{len(self._tables_added)} table(s) added")
        if self._tables_removed:
            parts.append(f"{len(self._tables_removed)} table(s) removed")
        if self._tables_modified:
            parts.append(f"{len(self._tables_modified)} table(s) modified")
        return ", ".join(parts) if parts else "no changes"
