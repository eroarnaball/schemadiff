"""Tests for schemadiff.tagged_result."""

import pytest

from schemadiff.tagger import TagSet
from schemadiff.tagged_result import TaggedResult


# ---------------------------------------------------------------------------
# Minimal stub that mimics a ComparisonResult
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, changed: bool = False):
        self._changed = changed

    def has_changes(self) -> bool:
        return self._changed

    def to_dict(self):
        return {"has_changes": self._changed}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_tags_are_empty():
    tr = TaggedResult(_FakeResult())
    assert len(tr.tags) == 0


def test_explicit_tags_stored():
    ts = TagSet().add("env", "prod")
    tr = TaggedResult(_FakeResult(), ts)
    assert tr.tags.get("env") == "prod"


# ---------------------------------------------------------------------------
# with_tag / without_tag immutability
# ---------------------------------------------------------------------------

def test_with_tag_returns_new_instance():
    tr = TaggedResult(_FakeResult())
    tr2 = tr.with_tag("env", "staging")
    assert tr2 is not tr
    assert tr2.tags.get("env") == "staging"
    assert tr.tags.get("env") is None


def test_without_tag_removes_key():
    tr = TaggedResult(_FakeResult(), TagSet().add("env", "prod").add("team", "data"))
    tr2 = tr.without_tag("env")
    assert tr2.tags.get("env") is None
    assert tr2.tags.get("team") == "data"


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------

def test_delegates_has_changes_false():
    tr = TaggedResult(_FakeResult(changed=False))
    assert tr.has_changes() is False


def test_delegates_has_changes_true():
    tr = TaggedResult(_FakeResult(changed=True))
    assert tr.has_changes() is True


def test_missing_attribute_raises():
    tr = TaggedResult(_FakeResult())
    with pytest.raises(AttributeError):
        _ = tr.nonexistent_attribute


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def test_to_dict_includes_tags():
    ts = TagSet().add("env", "prod")
    tr = TaggedResult(_FakeResult(changed=True), ts)
    d = tr.to_dict()
    assert d["tags"] == {"env": "prod"}
    assert d["has_changes"] is True


def test_to_dict_empty_tags():
    tr = TaggedResult(_FakeResult())
    d = tr.to_dict()
    assert d["tags"] == {}


def test_from_dict_restores_tags():
    result = _FakeResult()
    data = {"tags": {"region": "us-east-1", "env": "staging"}}
    tr = TaggedResult.from_dict(result, data)
    assert tr.tags.get("region") == "us-east-1"
    assert tr.tags.get("env") == "staging"


def test_from_dict_missing_tags_key_gives_empty():
    result = _FakeResult()
    tr = TaggedResult.from_dict(result, {})
    assert len(tr.tags) == 0


def test_repr_contains_class_name():
    tr = TaggedResult(_FakeResult())
    assert "TaggedResult" in repr(tr)
