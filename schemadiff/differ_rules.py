"""Rule-based drift detection: map ComparisonResult changes to named rule violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RuleViolation:
    rule_name: str
    table: str
    column: Optional[str]
    message: str
    severity: str = "warning"  # info | warning | error

    def to_dict(self) -> dict:
        return {
            "rule": self.rule_name,
            "table": self.table,
            "column": self.column,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class RuleReport:
    violations: List[RuleViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    def by_severity(self, severity: str) -> List[RuleViolation]:
        return [v for v in self.violations if v.severity == severity]

    def to_dict(self) -> dict:
        return {
            "has_violations": self.has_violations,
            "total": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


def apply_rules(result, rules: Optional[List[str]] = None) -> RuleReport:
    """Apply built-in drift rules to a ComparisonResult and return a RuleReport.

    Supported rule names (pass None to enable all):
        - no_table_removed
        - no_column_removed
        - no_type_change
        - no_nullable_loosened
    """
    _all_rules = {"no_table_removed", "no_column_removed", "no_type_change", "no_nullable_loosened"}
    active = _all_rules if rules is None else _all_rules & set(rules)

    violations: List[RuleViolation] = []

    for table_name in result.tables_removed:
        if "no_table_removed" in active:
            violations.append(RuleViolation(
                rule_name="no_table_removed",
                table=table_name,
                column=None,
                message=f"Table '{table_name}' was removed.",
                severity="error",
            ))

    for table_name, table_diff in result.columns_changed.items():
        for col_name, col_diff in table_diff.items():
            if "no_column_removed" in active and col_diff.old is not None and col_diff.new is None:
                violations.append(RuleViolation(
                    rule_name="no_column_removed",
                    table=table_name,
                    column=col_name,
                    message=f"Column '{col_name}' removed from table '{table_name}'.",
                    severity="error",
                ))
            if "no_type_change" in active and col_diff.old is not None and col_diff.new is not None:
                if col_diff.old.col_type != col_diff.new.col_type:
                    violations.append(RuleViolation(
                        rule_name="no_type_change",
                        table=table_name,
                        column=col_name,
                        message=(
                            f"Column '{col_name}' in '{table_name}' changed type "
                            f"from '{col_diff.old.col_type}' to '{col_diff.new.col_type}'."
                        ),
                        severity="warning",
                    ))
            if "no_nullable_loosened" in active and col_diff.old is not None and col_diff.new is not None:
                if not col_diff.old.nullable and col_diff.new.nullable:
                    violations.append(RuleViolation(
                        rule_name="no_nullable_loosened",
                        table=table_name,
                        column=col_name,
                        message=(
                            f"Column '{col_name}' in '{table_name}' changed from NOT NULL to nullable."
                        ),
                        severity="warning",
                    ))

    return RuleReport(violations=violations)
