"""High-level schema comparison API for schemadiff."""

from typing import Optional
from schemadiff.models import Schema
from schemadiff.differ import SchemaDiff, diff_schemas
from schemadiff.loader import load_schema_from_file, load_schema_from_string
from schemadiff.reporter import format_diff


class ComparisonResult:
    """Wraps a SchemaDiff with convenience methods."""

    def __init__(self, diff: SchemaDiff, source_name: str = "source", target_name: str = "target"):
        self.diff = diff
        self.source_name = source_name
        self.target_name = target_name

    @property
    def has_changes(self) -> bool:
        return self.diff.has_changes()

    @property
    def tables_added(self) -> list:
        return list(self.diff.tables_added)

    @property
    def tables_removed(self) -> list:
        return list(self.diff.tables_removed)

    @property
    def tables_modified(self) -> list:
        return [name for name, td in self.diff.tables_modified.items() if td.has_changes()]

    def summary(self) -> str:
        parts = []
        if self.tables_added:
            parts.append(f"{len(self.tables_added)} table(s) added")
        if self.tables_removed:
            parts.append(f"{len(self.tables_removed)} table(s) removed")
        if self.tables_modified:
            parts.append(f"{len(self.tables_modified)} table(s) modified")
        if not parts:
            return f"No schema drift detected between '{self.source_name}' and '{self.target_name}'."
        return f"Schema drift between '{self.source_name}' and '{self.target_name}': " + ", ".join(parts) + "."

    def report(self) -> str:
        return format_diff(self.diff)

    def __repr__(self) -> str:
        return f"ComparisonResult(has_changes={self.has_changes})"


def compare_schemas(source: Schema, target: Schema,
                    source_name: str = "source",
                    target_name: str = "target") -> ComparisonResult:
    """Compare two Schema objects and return a ComparisonResult."""
    diff = diff_schemas(source, target)
    return ComparisonResult(diff, source_name=source_name, target_name=target_name)


def compare_files(source_path: str, target_path: str) -> ComparisonResult:
    """Load two schema files and compare them."""
    source = load_schema_from_file(source_path)
    target = load_schema_from_file(target_path)
    return compare_schemas(source, target, source_name=source_path, target_name=target_path)


def compare_strings(source_json: str, target_json: str,
                    source_name: str = "source",
                    target_name: str = "target") -> ComparisonResult:
    """Parse two JSON strings as schemas and compare them."""
    source = load_schema_from_string(source_json)
    target = load_schema_from_string(target_json)
    return compare_schemas(source, target, source_name=source_name, target_name=target_name)
