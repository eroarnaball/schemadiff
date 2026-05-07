"""Tag schemas and comparison results with arbitrary metadata labels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when tagging operations fail."""


@dataclass
class TagSet:
    """An immutable-ish collection of string tags attached to a schema or result."""

    tags: Dict[str, str] = field(default_factory=dict)

    def add(self, key: str, value: str) -> "TagSet":
        """Return a new TagSet with the given key/value added."""
        if not key or not isinstance(key, str):
            raise TagError(f"Tag key must be a non-empty string, got {key!r}")
        if not isinstance(value, str):
            raise TagError(f"Tag value must be a string, got {value!r}")
        return TagSet({**self.tags, key: value})

    def remove(self, key: str) -> "TagSet":
        """Return a new TagSet without the given key."""
        updated = {k: v for k, v in self.tags.items() if k != key}
        return TagSet(updated)

    def get(self, key: str) -> Optional[str]:
        return self.tags.get(key)

    def keys(self) -> List[str]:
        return list(self.tags.keys())

    def to_dict(self) -> Dict[str, str]:
        return dict(self.tags)

    def __len__(self) -> int:
        return len(self.tags)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TagSet):
            return self.tags == other.tags
        return NotImplemented

    def __repr__(self) -> str:
        return f"TagSet({self.tags!r})"


def tag_set_from_dict(data: Dict[str, str]) -> TagSet:
    """Create a TagSet from a plain dictionary, validating all entries."""
    if not isinstance(data, dict):
        raise TagError(f"Expected a dict, got {type(data).__name__}")
    ts = TagSet()
    for k, v in data.items():
        ts = ts.add(k, v)
    return ts


def merge_tag_sets(*tag_sets: TagSet) -> TagSet:
    """Merge multiple TagSets left-to-right; later values overwrite earlier ones."""
    merged: Dict[str, str] = {}
    for ts in tag_sets:
        merged.update(ts.tags)
    return TagSet(merged)
