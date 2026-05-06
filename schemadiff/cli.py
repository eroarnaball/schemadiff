"""Command-line interface for schemadiff."""

import argparse
import sys

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.exporter import export_to_json, export_to_markdown, export_to_csv


FORMATS = ("text", "json", "markdown", "csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemadiff",
        description="Compare and report schema drift between database versions.",
    )
    parser.add_argument("old_schema", help="Path to the baseline schema file (JSON).")
    parser.add_argument("new_schema", help="Path to the target schema file (JSON).")
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when schema changes are detected.",
    )
    return parser


def run(argv=None) -> int:
    """Entry point; returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        old = load_schema_from_file(args.old_schema)
        new = load_schema_from_file(args.new_schema)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(old, new)

    if args.format == "json":
        print(export_to_json(result))
    elif args.format == "markdown":
        print(export_to_markdown(result))
    elif args.format == "csv":
        print(export_to_csv(result), end="")
    else:
        # Default human-readable text via existing reporter
        from schemadiff.reporter import print_diff  # lazy import
        from schemadiff.differ import diff_schemas

        print_diff(diff_schemas(old, new))

    if args.exit_code and result.has_changes():
        return 1
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
