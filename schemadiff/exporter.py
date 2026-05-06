"""Export schema diffs to various output formats (JSON, Markdown, CSV)."""

import csv
import io
import json
from typing import Union

from schemadiff.comparator import ComparisonResult


def export_to_json(result: ComparisonResult, indent: int = 2) -> str:
    """Serialize a ComparisonResult to a JSON string."""
    data = {
        "has_changes": result.has_changes(),
        "tables_added": list(result.tables_added()),
        "tables_removed": list(result.tables_removed()),
        "tables_modified": {
            table_name: {
                "columns_added": list(diff.columns_added()),
                "columns_removed": list(diff.columns_removed()),
                "columns_modified": {
                    col_name: {
                        "old": _column_change_to_dict(change["old"]),
                        "new": _column_change_to_dict(change["new"]),
                    }
                    for col_name, change in diff.columns_modified().items()
                },
            }
            for table_name, diff in result.tables_modified().items()
        },
    }
    return json.dumps(data, indent=indent)


def export_to_markdown(result: ComparisonResult) -> str:
    """Render a ComparisonResult as a Markdown report."""
    lines = ["# Schema Diff Report", ""]

    if not result.has_changes():
        lines.append("_No schema changes detected._")
        return "\n".join(lines)

    if result.tables_added():
        lines.append("## Tables Added")
        for name in sorted(result.tables_added()):
            lines.append(f"- `{name}`")
        lines.append("")

    if result.tables_removed():
        lines.append("## Tables Removed")
        for name in sorted(result.tables_removed()):
            lines.append(f"- `{name}`")
        lines.append("")

    if result.tables_modified():
        lines.append("## Tables Modified")
        for table_name, diff in sorted(result.tables_modified().items()):
            lines.append(f"### `{table_name}`")
            for col in sorted(diff.columns_added()):
                lines.append(f"- **Added column**: `{col}`")
            for col in sorted(diff.columns_removed()):
                lines.append(f"- **Removed column**: `{col}`")
            for col, change in sorted(diff.columns_modified().items()):
                lines.append(f"- **Modified column**: `{col}`")
                lines.append(f"  - old: `{change['old']}`")
                lines.append(f"  - new: `{change['new']}`")
            lines.append("")

    return "\n".join(lines)


def export_to_csv(result: ComparisonResult) -> str:
    """Render a ComparisonResult as a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["change_type", "table", "column", "detail"])

    for name in sorted(result.tables_added()):
        writer.writerow(["table_added", name, "", ""])
    for name in sorted(result.tables_removed()):
        writer.writerow(["table_removed", name, "", ""])
    for table_name, diff in sorted(result.tables_modified().items()):
        for col in sorted(diff.columns_added()):
            writer.writerow(["column_added", table_name, col, ""])
        for col in sorted(diff.columns_removed()):
            writer.writerow(["column_removed", table_name, col, ""])
        for col, change in sorted(diff.columns_modified().items()):
            detail = f"old={change['old']} new={change['new']}"
            writer.writerow(["column_modified", table_name, col, detail])

    return output.getvalue()


def _column_change_to_dict(value) -> Union[dict, str]:
    """Convert a column object or primitive to a serialisable dict."""
    if hasattr(value, "__dict__"):
        return vars(value)
    return str(value)
