"""Load PolicyRule definitions from a YAML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from schemadiff.policy import PolicyError, PolicyRule

_VALID_CHANGE_TYPES = {
    "added",
    "removed",
    "modified",
    "type_changed",
    "nullable_changed",
}


def _rule_from_dict(raw: dict) -> PolicyRule:
    if not isinstance(raw, dict):
        raise PolicyError(f"Each rule must be a mapping, got {type(raw).__name__}")
    change_type = raw.get("change_type", "")
    if change_type not in _VALID_CHANGE_TYPES:
        raise PolicyError(
            f"Invalid change_type {change_type!r}. "
            f"Valid values: {sorted(_VALID_CHANGE_TYPES)}"
        )
    return PolicyRule(
        change_type=change_type,
        tables=list(raw.get("tables") or []),
        columns=list(raw.get("columns") or []),
        message=str(raw.get("message", "Policy violation")),
    )


def load_policy_from_dict(data: dict) -> List[PolicyRule]:
    """Parse a policy document (already deserialised) into a list of rules."""
    if not isinstance(data, dict):
        raise PolicyError("Policy document must be a JSON/YAML object")
    rules_raw = data.get("rules")
    if not isinstance(rules_raw, list):
        raise PolicyError("Policy document must contain a 'rules' list")
    return [_rule_from_dict(r) for r in rules_raw]


def load_policy_from_string(text: str) -> List[PolicyRule]:
    """Parse a JSON string into policy rules."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PolicyError(f"Invalid JSON in policy: {exc}") from exc
    return load_policy_from_dict(data)


def load_policy_from_file(path: str) -> List[PolicyRule]:
    """Load policy rules from a JSON file on disk."""
    p = Path(path)
    if not p.exists():
        raise PolicyError(f"Policy file not found: {path}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyError(f"Cannot read policy file: {exc}") from exc
    return load_policy_from_string(text)
