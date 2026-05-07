"""Wrap a ComparisonResult (or any result-like object) with a TagSet."""

from __future__ import annotations

from typing import Any, Dict

from schemadiff.tagger import TagSet, tag_set_from_dict


class TaggedResult:
    """A comparison result decorated with metadata tags.

    Delegates all result attributes to the wrapped *result* object so that
    existing code that consumes a plain result continues to work unchanged.
    """

    def __init__(self, result: Any, tags: TagSet | None = None) -> None:
        self._result = result
        self._tags = tags if tags is not None else TagSet()

    # ------------------------------------------------------------------
    # Tag management
    # ------------------------------------------------------------------

    @property
    def tags(self) -> TagSet:
        return self._tags

    def with_tag(self, key: str, value: str) -> "TaggedResult":
        """Return a new TaggedResult with the additional tag applied."""
        return TaggedResult(self._result, self._tags.add(key, value))

    def without_tag(self, key: str) -> "TaggedResult":
        """Return a new TaggedResult with the given tag removed."""
        return TaggedResult(self._result, self._tags.remove(key))

    # ------------------------------------------------------------------
    # Delegation to wrapped result
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # Avoid infinite recursion for private attrs not yet set
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._result, name)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation including tags."""
        base: Dict[str, Any] = {}
        if hasattr(self._result, "to_dict"):
            base = self._result.to_dict()
        base["tags"] = self._tags.to_dict()
        return base

    @classmethod
    def from_dict(cls, result: Any, data: Dict[str, Any]) -> "TaggedResult":
        """Re-attach tags from a serialised dict onto an existing result."""
        raw_tags = data.get("tags", {})
        ts = tag_set_from_dict(raw_tags)
        return cls(result, ts)

    def __repr__(self) -> str:
        return f"TaggedResult(result={self._result!r}, tags={self._tags!r})"
