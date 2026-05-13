"""CLI entry-point: print schema-diff statistics."""
from __future__ import annotations

import argparse
import json
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.differ_stats import compute_stats


def build_stats_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="schemadiff-stats",
        description="Print statistical summary of schema drift.",
    )
    parser.add_argument("base", help="Path to the base schema JSON file.")
    parser.add_argument("head", help="Path to the head schema JSON file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def run_stats_command(args: argparse.Namespace) -> int:
    try:
        base = load_schema_from_file(args.base)
        head = load_schema_from_file(args.head)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(base, head)
    stats = compute_stats(result)

    if args.format == "json":
        print(json.dumps(stats.to_dict(), indent=2))
    else:
        d = stats.to_dict()
        print("Schema Diff Statistics")
        print("=======================")
        print(f"Tables added:      {d['tables_added']}")
        print(f"Tables removed:    {d['tables_removed']}")
        print(f"Tables modified:   {d['tables_modified']}")
        print(f"Columns added:     {d['columns_added']}")
        print(f"Columns removed:   {d['columns_removed']}")
        print(f"Columns modified:  {d['columns_modified']}")
        print(f"Total changes:     {d['total_changes']}")

    return 0


def main() -> None:
    parser = build_stats_parser()
    args = parser.parse_args()
    sys.exit(run_stats_command(args))


if __name__ == "__main__":
    main()
