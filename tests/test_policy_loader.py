"""Tests for schemadiff.policy_loader."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from schemadiff.policy import PolicyRule
from schemadiff.policy_loader import (
    PolicyError,
    load_policy_from_dict,
    load_policy_from_file,
    load_policy_from_string,
)


_SIMPLE_POLICY = {
    "rules": [
        {"change_type": "removed", "message": "No column drops"},
        {"change_type": "type_changed", "tables": ["users"], "message": "Careful"},
    ]
}


def test_load_from_dict_returns_rules():
    rules = load_policy_from_dict(_SIMPLE_POLICY)
    assert len(rules) == 2
    assert all(isinstance(r, PolicyRule) for r in rules)


def test_load_from_dict_preserves_fields():
    rules = load_policy_from_dict(_SIMPLE_POLICY)
    assert rules[0].change_type == "removed"
    assert rules[1].tables == ["users"]
    assert rules[1].message == "Careful"


def test_load_from_dict_empty_rules():
    rules = load_policy_from_dict({"rules": []})
    assert rules == []


def test_load_from_dict_missing_rules_raises():
    with pytest.raises(PolicyError, match="'rules' list"):
        load_policy_from_dict({"version": 1})


def test_load_from_dict_not_a_dict_raises():
    with pytest.raises(PolicyError):
        load_policy_from_dict([])  # type: ignore


def test_load_from_dict_invalid_change_type_raises():
    with pytest.raises(PolicyError, match="Invalid change_type"):
        load_policy_from_dict({"rules": [{"change_type": "unknown"}]})


def test_load_from_string_valid_json():
    text = json.dumps(_SIMPLE_POLICY)
    rules = load_policy_from_string(text)
    assert len(rules) == 2


def test_load_from_string_invalid_json_raises():
    with pytest.raises(PolicyError, match="Invalid JSON"):
        load_policy_from_string("{not valid json")


def test_load_from_file_roundtrip(tmp_path):
    policy_file = tmp_path / "policy.json"
    policy_file.write_text(json.dumps(_SIMPLE_POLICY), encoding="utf-8")
    rules = load_policy_from_file(str(policy_file))
    assert len(rules) == 2


def test_load_from_file_missing_raises():
    with pytest.raises(PolicyError, match="not found"):
        load_policy_from_file("/nonexistent/path/policy.json")


def test_load_from_dict_default_message():
    rules = load_policy_from_dict({"rules": [{"change_type": "added"}]})
    assert rules[0].message == "Policy violation"
