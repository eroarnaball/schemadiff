"""High-level pipeline combining load, compare, filter, and export."""

from typing import Optional, List

from schemadiff.loader import load_schema_from_file
from schemadiff.comparator import compare_schemas
from schemadiff.filter import filter_result, FilteredResult
from schemadiff.exporter import export_to_json, export_to_markdown, export_to_csv


SUPPORTED_FORMATS = ("json", "markdown", "csv")


def run_pipeline(
    source_path: str,
    target_path: str,
    include_tables: Optional[List[str]] = None,
    exclude_tables: Optional[List[str]] = None,
    change_types: Optional[List[str]] = None,
    output_format: str = "json",
) -> str:
    """Load two schema files, compare them, apply filters, and return formatted output.

    Args:
        source_path: Path to the source (baseline) schema JSON file.
        target_path: Path to the target (new) schema JSON file.
        include_tables: Optional whitelist of table names to include.
        exclude_tables: Optional blacklist of table names to exclude.
        change_types: Subset of ('added', 'removed', 'modified') to report.
        output_format: One of 'json', 'markdown', or 'csv'.

    Returns:
        Formatted string representation of the filtered diff.

    Raises:
        ValueError: If output_format is not supported.
    """
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{output_format}'. Choose from {SUPPORTED_FORMATS}."
        )

    source = load_schema_from_file(source_path)
    target = load_schema_from_file(target_path)

    comparison = compare_schemas(source, target)

    filtered = filter_result(
        comparison,
        include_tables=include_tables,
        exclude_tables=exclude_tables,
        change_types=change_types,
    )

    return _export_filtered(filtered, comparison, output_format)


def _export_filtered(filtered: FilteredResult, original_comparison, output_format: str) -> str:
    """Delegate export to the appropriate exporter using the original comparison.

    The exporters operate on the full ComparisonResult, so we rebuild a minimal
    proxy that restricts to the filtered tables.
    """
    proxy = _FilteredComparisonProxy(filtered)

    if output_format == "json":
        return export_to_json(proxy)
    elif output_format == "markdown":
        return export_to_markdown(proxy)
    elif output_format == "csv":
        return export_to_csv(proxy)
    raise ValueError(f"Unknown format: {output_format}")


class _FilteredComparisonProxy:
    """Thin adapter exposing FilteredResult via the ComparisonResult interface."""

    def __init__(self, filtered: FilteredResult):
        self._filtered = filtered

    def has_changes(self) -> bool:
        return self._filtered.has_changes()

    def tables_added(self):
        return self._filtered.tables_added()

    def tables_removed(self):
        return self._filtered.tables_removed()

    def tables_modified(self):
        return self._filtered.tables_modified()
