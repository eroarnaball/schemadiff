"""CLI sub-command: notify — send a drift report to a webhook."""
from __future__ import annotations

import argparse
import sys

from schemadiff.loader import load_schema_from_file, LoadError
from schemadiff.comparator import compare_schemas
from schemadiff.summary import summarize
from schemadiff.notifier import NotifierConfig, NotifyError, notify


def build_notifier_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser(
        "notify",
        help="Compare two schemas and POST drift summary to a webhook.",
    )
    p.add_argument("base", help="Path to the base schema JSON file.")
    p.add_argument("head", help="Path to the head schema JSON file.")
    p.add_argument(
        "--webhook",
        required=True,
        metavar="URL",
        help="Webhook URL to POST the drift summary to.",
    )
    p.add_argument(
        "--min-severity",
        type=int,
        default=1,
        metavar="N",
        help="Minimum total_changes required to trigger notification (default: 1).",
    )
    return p


def run_notifier_command(args: argparse.Namespace) -> int:
    """Execute the notify sub-command.  Returns an exit code."""
    try:
        base_schema = load_schema_from_file(args.base)
        head_schema = load_schema_from_file(args.head)
    except LoadError as exc:
        print(f"[schemadiff notify] load error: {exc}", file=sys.stderr)
        return 2

    result = compare_schemas(base_schema, head_schema)
    summary = summarize(result)

    config = NotifierConfig(
        webhook_url=args.webhook,
        min_severity=args.min_severity,
    )

    try:
        sent = notify(summary, config)
    except NotifyError as exc:
        print(f"[schemadiff notify] webhook error: {exc}", file=sys.stderr)
        return 3

    if sent:
        print(f"Drift notification sent ({summary.total_changes} change(s) detected).")
    else:
        print("No notification sent (changes below min-severity threshold).")

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="schemadiff-notify")
    sub = parser.add_subparsers(dest="command")
    build_notifier_parser(sub)
    args = parser.parse_args()
    sys.exit(run_notifier_command(args))
