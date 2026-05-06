"""Tests for schemadiff.formatter module."""

import pytest
from schemadiff.summary import SchemaSummary
from schemadiff.formatter import format_summary, format_summary_text, format_summary_markdown


def _make_summary(**kwargs) -> SchemaSummary:
    s = SchemaSummary()
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


def test_format_text_no_changes():
    s = SchemaSummary()
    out = format_summary_text(s)
    assert "Schema Diff Summary" in out
    assert "no changes detected" in out
    assert "Total changes   : 0" in out


def test_format_text_with_changes():
    s = _make_summary(tables_added=2, columns_removed=1)
    out = format_summary_text(s)
    assert "Tables added    : 2" in out
    assert "Columns removed : 1" in out
    assert "no changes detected" not in out


def test_format_text_total_changes():
    s = _make_summary(tables_added=1, columns_modified=3)
    out = format_summary_text(s)
    assert "Total changes   : 4" in out


def test_format_markdown_structure():
    s = _make_summary(tables_removed=1, columns_added=2)
    out = format_summary_markdown(s)
    assert "## Schema Diff Summary" in out
    assert "| Metric | Count |" in out
    assert "| Tables Removed | 1 |" in out
    assert "| Columns Added | 2 |" in out


def test_format_markdown_total_row():
    s = _make_summary(tables_added=1, columns_added=1)
    out = format_summary_markdown(s)
    assert "**Total Changes**" in out
    assert "| **Total Changes** | 2 |" in out


def test_format_dispatch_text():
    s = SchemaSummary()
    out = format_summary(s, fmt="text")
    assert "Schema Diff Summary" in out


def test_format_dispatch_markdown():
    s = SchemaSummary()
    out = format_summary(s, fmt="markdown")
    assert "##" in out


def test_format_dispatch_unknown_raises():
    s = SchemaSummary()
    with pytest.raises(ValueError, match="Unknown summary format"):
        format_summary(s, fmt="xml")
