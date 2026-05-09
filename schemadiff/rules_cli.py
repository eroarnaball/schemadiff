"""CLI entry-point for rule-based drift checking."""

from __future__ import annotations

import argparse
import json
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.differ_rules import apply_rules


def build_rules_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Check schema drift against built-in rules.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("rules", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("old", help="Path to old schema JSON file.")
    parser.add_argument("new", help="Path to new schema JSON file.")
    parser.add_argument(
        "--rules",
        nargs="+",
        metavar="RULE",
        help="Subset of rules to enable (default: all).\n"
             "Choices: no_table_removed, no_column_removed, no_type_change, no_nullable_loosened",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="Exit with code 1 when any violation is found.",
    )
    return parser


def run_rules_command(args: argparse.Namespace) -> int:
    try:
        old_schema = load_schema_from_file(args.old)
        new_schema = load_schema_from_file(args.new)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(old_schema, new_schema)
    report = apply_rules(result, rules=args.rules)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if not report.has_violations:
            print("No rule violations detected.")
        else:
            print(f"Found {len(report.violations)} violation(s):")
            for v in report.violations:
                col_part = f" [{v.column}]" if v.column else ""
                print(f"  [{v.severity.upper()}] {v.rule_name} | {v.table}{col_part}: {v.message}")

    if args.fail_on_violation and report.has_violations:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_rules_parser()
    args = parser.parse_args()
    sys.exit(run_rules_command(args))


if __name__ == "__main__":  # pragma: no cover
    main()
