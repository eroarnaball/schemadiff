"""Tests for schemadiff.tagger."""

import pytest

from schemadiff.tagger import (
    TagError,
    TagSet,
    merge_tag_sets,
    tag_set_from_dict,
)


# ---------------------------------------------------------------------------
# TagSet basics
# ---------------------------------------------------------------------------

def test_empty_tag_set_has_zero_length():
    ts = TagSet()
    assert len(ts) == 0


def test_add_returns_new_tag_set():
    ts = TagSet()
    ts2 = ts.add("env", "production")
    assert ts2.get("env") == "production"
    assert ts.get("env") is None  # original unchanged


def test_add_multiple_tags():
    ts = TagSet().add("env", "staging").add("team", "data")
    assert ts.get("env") == "staging"
    assert ts.get("team") == "data"
    assert len(ts) == 2


def test_remove_existing_key():
    ts = TagSet().add("env", "prod").add("region", "us-east-1")
    ts2 = ts.remove("env")
    assert ts2.get("env") is None
    assert ts2.get("region") == "us-east-1"


def test_remove_nonexistent_key_is_noop():
    ts = TagSet().add("env", "prod")
    ts2 = ts.remove("missing")
    assert ts2 == ts


def test_keys_returns_list():
    ts = TagSet().add("a", "1").add("b", "2")
    assert sorted(ts.keys()) == ["a", "b"]


def test_to_dict_returns_copy():
    ts = TagSet().add("x", "y")
    d = ts.to_dict()
    assert d == {"x": "y"}
    d["extra"] = "z"
    assert ts.get("extra") is None  # original not mutated


def test_equality():
    ts1 = TagSet().add("env", "prod")
    ts2 = TagSet().add("env", "prod")
    assert ts1 == ts2


def test_inequality():
    ts1 = TagSet().add("env", "prod")
    ts2 = TagSet().add("env", "staging")
    assert ts1 != ts2


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_add_empty_key_raises():
    with pytest.raises(TagError):
        TagSet().add("", "value")


def test_add_non_string_value_raises():
    with pytest.raises(TagError):
        TagSet().add("env", 42)  # type: ignore


# ---------------------------------------------------------------------------
# tag_set_from_dict
# ---------------------------------------------------------------------------

def test_tag_set_from_dict_basic():
    ts = tag_set_from_dict({"env": "prod", "team": "infra"})
    assert ts.get("env") == "prod"
    assert ts.get("team") == "infra"


def test_tag_set_from_dict_empty():
    ts = tag_set_from_dict({})
    assert len(ts) == 0


def test_tag_set_from_dict_non_dict_raises():
    with pytest.raises(TagError):
        tag_set_from_dict(["env", "prod"])  # type: ignore


# ---------------------------------------------------------------------------
# merge_tag_sets
# ---------------------------------------------------------------------------

def test_merge_two_disjoint_tag_sets():
    ts1 = TagSet().add("env", "prod")
    ts2 = TagSet().add("region", "eu-west-1")
    merged = merge_tag_sets(ts1, ts2)
    assert merged.get("env") == "prod"
    assert merged.get("region") == "eu-west-1"


def test_merge_later_overwrites_earlier():
    ts1 = TagSet().add("env", "staging")
    ts2 = TagSet().add("env", "production")
    merged = merge_tag_sets(ts1, ts2)
    assert merged.get("env") == "production"


def test_merge_zero_tag_sets_returns_empty():
    merged = merge_tag_sets()
    assert len(merged) == 0
