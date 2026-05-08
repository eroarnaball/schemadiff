"""Policy engine: define rules that flag specific schema drift as violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class PolicyError(Exception):
    """Raised when a policy cannot be parsed or evaluated."""


@dataclass
class PolicyRule:
    """A single rule that matches drift by change_type and optional table/column patterns."""

    change_type: str  # 'added', 'removed', 'modified', 'type_changed', 'nullable_changed'
    tables: List[str] = field(default_factory=list)   # empty = all tables
    columns: List[str] = field(default_factory=list)  # empty = all columns
    message: str = "Policy violation"

    def matches(self, change_type: str, table: str, column: Optional[str] = None) -> bool:
        if self.change_type != change_type:
            return False
        if self.tables and table not in self.tables:
            return False
        if self.columns and column not in self.columns:
            return False
        return True


@dataclass
class PolicyViolation:
    rule: PolicyRule
    table: str
    column: Optional[str]
    change_type: str

    def to_dict(self) -> dict:
        return {
            "message": self.rule.message,
            "change_type": self.change_type,
            "table": self.table,
            "column": self.column,
        }


def evaluate_policy(rules: List[PolicyRule], result) -> List[PolicyViolation]:
    """Evaluate *rules* against a comparison *result* and return all violations."""
    violations: List[PolicyViolation] = []

    for table_name in result.tables_added:
        for rule in rules:
            if rule.matches("added", table_name):
                violations.append(PolicyViolation(rule, table_name, None, "added"))

    for table_name in result.tables_removed:
        for rule in rules:
            if rule.matches("removed", table_name):
                violations.append(PolicyViolation(rule, table_name, None, "removed"))

    for table_name, table_diff in result.tables_modified.items():
        for col_name in table_diff.columns_added:
            for rule in rules:
                if rule.matches("added", table_name, col_name):
                    violations.append(PolicyViolation(rule, table_name, col_name, "added"))

        for col_name in table_diff.columns_removed:
            for rule in rules:
                if rule.matches("removed", table_name, col_name):
                    violations.append(PolicyViolation(rule, table_name, col_name, "removed"))

        for col_name, col_diff in table_diff.columns_modified.items():
            for change_type in ("type_changed", "nullable_changed"):
                attr = change_type.replace("_changed", "")
                if getattr(col_diff, f"{attr}_changed", False):
                    for rule in rules:
                        if rule.matches(change_type, table_name, col_name):
                            violations.append(
                                PolicyViolation(rule, table_name, col_name, change_type)
                            )

    return violations
