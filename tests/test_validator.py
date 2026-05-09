"""Tests for schemadiff.validator module."""

import pytest
from schemadiff.validator import (
    validate_column_dict,
    validate_table_dict,
    validate_schema_dict,
    ValidationError,
)


# --- validate_column_dict ---

def test_valid_column_passes():
    validate_column_dict({"name": "id", "type": "integer", "nullable": False})


def test_column_missing_name_raises():
    with pytest.raises(ValidationError, match="missing required field 'name'"):
        validate_column_dict({"type": "integer"})


def test_column_empty_name_raises():
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_column_dict({"name": "  ", "type": "text"})


def test_column_missing_type_raises():
    with pytest.raises(ValidationError, match="missing required field 'type'"):
        validate_column_dict({"name": "col"})


def test_column_nullable_not_bool_raises():
    with pytest.raises(ValidationError, match="'nullable' must be a bool"):
        validate_column_dict({"name": "col", "type": "text", "nullable": "yes"})


def test_column_not_dict_raises():
    with pytest.raises(ValidationError, match="must be a dict"):
        validate_column_dict(["name", "id"])


def test_column_context_included_in_error():
    with pytest.raises(ValidationError, match="table 'users'"):
        validate_column_dict({"type": "text"}, context="table 'users'")


def test_column_name_not_string_raises():
    """Ensure a non-string 'name' value is rejected with a clear message."""
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_column_dict({"name": 42, "type": "integer"})


def test_column_type_not_string_raises():
    """Ensure a non-string 'type' value is rejected with a clear message."""
    with pytest.raises(ValidationError, match="non-empty string"):
        validate_column_dict({"name": "col", "type": 123})


# --- validate_table_dict ---

def test_valid_table_passes():
    validate_table_dict({
        "name": "users",
        "columns": [{"name": "id", "type": "integer"}],
    })


def test_table_missing_name_raises():
    with pytest.raises(ValidationError, match="missing required field 'name'"):
        validate_table_dict({"columns": []})


def test_table_columns_not_list_raises():
    with pytest.raises(ValidationError, match="'columns' must be a list"):
        validate_table_dict({"name": "t", "columns": {}})


def test_table_invalid_column_propagates():
    with pytest.raises(ValidationError, match="table 'orders'"):
        validate_table_dict({
            "name": "orders",
            "columns": [{"type": "integer"}],
        })


def test_table_no_columns_key_passes():
    validate_table_dict({"name": "empty_table"})


# --- validate_schema_dict ---

def test_valid_schema_passes():
    validate_schema_dict({
        "tables": [
            {"name": "a", "columns": [{"name": "id", "type": "integer"}]},
            {"name": "b", "columns": []},
        ]
    })


def test_schema_not_dict_raises():
    with pytest.raises(ValidationError, match="must be a dict"):
        validate_schema_dict(["tables"])


def test_schema_tables_not_list_raises():
    with pytest.raises(ValidationError, match="'tables' must be a list"):
        validate_schema_dict({"tables": "all"})


def test_schema_duplicate_table_name_raises():
    with pytest.raises(ValidationError, match="duplicate table name: 'users'"):
        validate_schema_dict({
            "tables": [
                {"name": "users", "columns": []},
                {"name": "users", "columns": []},
            ]
        })
