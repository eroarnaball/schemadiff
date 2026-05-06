"""CLI sub-commands for baseline management (save / compare)."""

from __future__ import annotations

import argparse
import sys

from schemadiff.baseline import save_baseline, load_baseline, BaselineError
from schemadiff.loader import load_schema_from_file, LoadError
from schemadiff.comparator import compare_schemas
from schemadiff.reporter import format_diff


def build_baseline_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'baseline' sub-commands onto *subparsers*."""
    bl = subparsers.add_parser("baseline", help="Manage schema baselines")
    bl_sub = bl.add_subparsers(dest="bl_command", required=True)

    # save
    save_p = bl_sub.add_parser("save", help="Save current schema as baseline")
    save_p.add_argument("schema", help="Path to schema JSON file")
    save_p.add_argument(
        "--output", "-o", default=None, help="Baseline output path (default: .schemadiff_baseline.json)"
    )

    # compare
    cmp_p = bl_sub.add_parser("compare", help="Compare schema against saved baseline")
    cmp_p.add_argument("schema", help="Path to current schema JSON file")
    cmp_p.add_argument(
        "--baseline", "-b", default=None, help="Baseline file path (default: .schemadiff_baseline.json)"
    )
    cmp_p.add_argument(
        "--exit-code", action="store_true", help="Exit with code 1 when drift is detected"
    )


def run_baseline_command(args: argparse.Namespace) -> int:
    """Dispatch baseline sub-command; return exit code."""
    if args.bl_command == "save":
        return _cmd_save(args)
    if args.bl_command == "compare":
        return _cmd_compare(args)
    print(f"Unknown baseline command: {args.bl_command}", file=sys.stderr)
    return 2


def _cmd_save(args: argparse.Namespace) -> int:
    try:
        schema = load_schema_from_file(args.schema)
    except LoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2
    try:
        path = save_baseline(schema, args.output)
        print(f"Baseline saved to '{path}'.")
        return 0
    except BaselineError as exc:
        print(f"Error saving baseline: {exc}", file=sys.stderr)
        return 2


def _cmd_compare(args: argparse.Namespace) -> int:
    try:
        current = load_schema_from_file(args.schema)
    except LoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2
    try:
        baseline = load_baseline(args.baseline)
    except BaselineError as exc:
        print(f"Error loading baseline: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(baseline, current)
    print(format_diff(result))

    if args.exit_code and result.has_changes():
        return 1
    return 0
