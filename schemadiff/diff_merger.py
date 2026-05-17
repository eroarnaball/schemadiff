"""Merge multiple ComparisonResult objects into a single unified result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


class MergeError(Exception):
    """Raised when results cannot be merged."""


@dataclass
class MergedResult:
    """A unified view of several comparison results."""

    sources: List[str] = field(default_factory=list)
    _tables_added: List[str] = field(default_factory=list)
    _tables_removed: List[str] = field(default_factory=list)
    _column_changes: List[dict] = field(default_factory=list)

    # --- ComparisonResult-compatible interface ---

    def has_changes(self) -> bool:
        return bool(
            self._tables_added or self._tables_removed or self._column_changes
        )

    @property
    def tables_added(self) -> List[str]:
        return list(self._tables_added)

    @property
    def tables_removed(self) -> List[str]:
        return list(self._tables_removed)

    @property
    def column_changes(self) -> List[dict]:
        return list(self._column_changes)

    def to_dict(self) -> dict:
        return {
            "sources": self.sources,
            "tables_added": self._tables_added,
            "tables_removed": self._tables_removed,
            "column_changes": self._column_changes,
            "has_changes": self.has_changes(),
        }


def merge_results(results: Iterable, labels: Iterable[str] | None = None) -> MergedResult:
    """Merge an iterable of comparison results into one MergedResult.

    Duplicate table additions/removals are de-duplicated; column changes from
    all sources are collected in order.

    Args:
        results: Objects that expose ``tables_added``, ``tables_removed``,
                 and ``column_changes`` properties.
        labels:  Optional human-readable label for each source.

    Returns:
        A :class:`MergedResult` combining all inputs.
    """
    results = list(results)
    if not results:
        raise MergeError("No results provided to merge.")

    labels = list(labels) if labels is not None else [str(i) for i in range(len(results))]
    if len(labels) != len(results):
        raise MergeError("Number of labels must match number of results.")

    seen_added: set = set()
    seen_removed: set = set()
    merged = MergedResult(sources=labels)

    for result in results:
        for tbl in result.tables_added:
            if tbl not in seen_added:
                seen_added.add(tbl)
                merged._tables_added.append(tbl)

        for tbl in result.tables_removed:
            if tbl not in seen_removed:
                seen_removed.add(tbl)
                merged._tables_removed.append(tbl)

        for change in result.column_changes:
            merged._column_changes.append(change)

    return merged
