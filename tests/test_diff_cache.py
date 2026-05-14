"""Tests for schemadiff.diff_cache."""

from __future__ import annotations

import json
import pytest

from schemadiff.diff_cache import (
    CacheError,
    _cache_key,
    _content_hash,
    clear_cache,
    get_cached,
    invalidate,
    put_cached,
)

SCHEMA_A = '{"tables": [{"name": "users"}]}'
SCHEMA_B = '{"tables": [{"name": "orders"}]}'
RESULT = {"has_changes": True, "tables_added": ["orders"]}


def test_content_hash_is_deterministic():
    assert _content_hash(SCHEMA_A) == _content_hash(SCHEMA_A)


def test_content_hash_differs_for_different_inputs():
    assert _content_hash(SCHEMA_A) != _content_hash(SCHEMA_B)


def test_cache_key_is_deterministic():
    assert _cache_key(SCHEMA_A, SCHEMA_B) == _cache_key(SCHEMA_A, SCHEMA_B)


def test_cache_key_differs_when_inputs_swapped():
    assert _cache_key(SCHEMA_A, SCHEMA_B) != _cache_key(SCHEMA_B, SCHEMA_A)


def test_get_cached_returns_none_when_missing(tmp_path):
    result = get_cached(tmp_path, SCHEMA_A, SCHEMA_B)
    assert result is None


def test_put_and_get_roundtrip(tmp_path):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    loaded = get_cached(tmp_path, SCHEMA_A, SCHEMA_B)
    assert loaded == RESULT


def test_put_creates_json_file(tmp_path):
    path = put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["has_changes"] is True


def test_put_cached_creates_directory(tmp_path):
    cache_dir = tmp_path / "nested" / "cache"
    put_cached(cache_dir, SCHEMA_A, SCHEMA_B, RESULT)
    assert cache_dir.exists()


def test_invalidate_removes_entry(tmp_path):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    removed = invalidate(tmp_path, SCHEMA_A, SCHEMA_B)
    assert removed is True
    assert get_cached(tmp_path, SCHEMA_A, SCHEMA_B) is None


def test_invalidate_returns_false_when_not_present(tmp_path):
    removed = invalidate(tmp_path, SCHEMA_A, SCHEMA_B)
    assert removed is False


def test_clear_cache_removes_all_entries(tmp_path):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    put_cached(tmp_path, SCHEMA_B, SCHEMA_A, RESULT)
    count = clear_cache(tmp_path)
    assert count == 2
    remaining = list(tmp_path.glob("*.json"))
    assert remaining == []


def test_clear_cache_returns_zero_for_missing_dir(tmp_path):
    count = clear_cache(tmp_path / "nonexistent")
    assert count == 0


def test_get_cached_raises_on_corrupt_file(tmp_path):
    put_cached(tmp_path, SCHEMA_A, SCHEMA_B, RESULT)
    key = _cache_key(SCHEMA_A, SCHEMA_B)
    corrupt = tmp_path / f"{key}.json"
    corrupt.write_text("NOT JSON", encoding="utf-8")
    with pytest.raises(CacheError):
        get_cached(tmp_path, SCHEMA_A, SCHEMA_B)
