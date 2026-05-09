"""CLI sub-commands for the audit log feature.

Usage examples:
    schemadiff-audit show audit.log
    schemadiff-audit record --source old.json --target new.json \
        --source-label prod-2024-01 --target-label prod-2024-02 \
        --log audit.log
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemadiff.auditor import AuditError, load_audit_log, record_comparison
from schemadiff.comparator import compare_schemas
from schemadiff.loader import LoadError, load_schema_from_file


def build_audit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemadiff-audit",
        description="Manage the schemadiff audit log.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="Compare two schemas and append an audit entry.")
    rec.add_argument("--source", required=True, help="Path to source schema JSON.")
    rec.add_argument("--target", required=True, help="Path to target schema JSON.")
    rec.add_argument("--source-label", default="source", help="Human label for source.")
    rec.add_argument("--target-label", default="target", help="Human label for target.")
    rec.add_argument("--log", required=True, help="Path to audit log file.")
    rec.add_argument("--meta", default="{}", help="Extra metadata as a JSON object string.")

    show = sub.add_parser("show", help="Print audit log entries.")
    show.add_argument("log", help="Path to audit log file.")
    show.add_argument("--json", dest="as_json", action="store_true",
                      help="Output as JSON array.")

    return parser


def _cmd_record(args: argparse.Namespace) -> int:
    try:
        source = load_schema_from_file(Path(args.source))
        target = load_schema_from_file(Path(args.target))
    except LoadError as exc:
        print(f"Load error: {exc}", file=sys.stderr)
        return 1

    try:
        meta = json.loads(args.meta)
    except json.JSONDecodeError as exc:
        print(f"Invalid --meta JSON: {exc}", file=sys.stderr)
        return 1

    result = compare_schemas(source, target)
    try:
        entry = record_comparison(
            result,
            source_label=args.source_label,
            target_label=args.target_label,
            log_path=Path(args.log),
            metadata=meta,
        )
    except AuditError as exc:
        print(f"Audit error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(entry.to_dict(), indent=2))
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        entries = load_audit_log(Path(args.log))
    except AuditError as exc:
        print(f"Audit error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        if not entries:
            print("No audit entries found.")
        for e in entries:
            print(
                f"[{e.timestamp}] {e.event} "
                f"{e.source_label} -> {e.target_label} "
                f"changes={e.total_changes} host={e.hostname}"
            )
    return 0


def run_audit_command(args: argparse.Namespace) -> int:
    if args.command == "record":
        return _cmd_record(args)
    if args.command == "show":
        return _cmd_show(args)
    return 1


def main() -> None:
    parser = build_audit_parser()
    args = parser.parse_args()
    sys.exit(run_audit_command(args))


if __name__ == "__main__":
    main()
