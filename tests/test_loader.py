"""Tests for schemadiff.loader."""

import json
import os
import tempfile

import pytest

from schemadiff.loader import load_schema_from_file, load_schema_from_string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_SCHEMA = {
    "name": "mydb",
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "integer", "nullable": False, "default": None},
                {"name": "email", "type": "varchar", "nullable": False, "default": None},
            ],
        }
    ],
}


def _write_tmp_json(data: dict) -> str:
    """Write *data* to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    return path


# ---------------------------------------------------------------------------
# load_schema_from_string
# ---------------------------------------------------------------------------

def test_load_schema_from_string_basic():
    schema = load_schema_from_string(json.dumps(SAMPLE_SCHEMA))
    assert schema.name == "mydb"
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "users"


def test_load_schema_from_string_columns():
    schema = load_schema_from_string(json.dumps(SAMPLE_SCHEMA))
    table = schema.tables[0]
    assert len(table.columns) == 2
    assert table.columns[0].name == "id"
    assert table.columns[1].type == "varchar"


def test_load_schema_from_string_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_schema_from_string("{not valid json}")


def test_load_schema_from_string_not_a_dict():
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_schema_from_string(json.dumps([1, 2, 3]))


def test_load_schema_from_string_missing_keys():
    with pytest.raises(ValueError, match="missing required keys"):
        load_schema_from_string(json.dumps({"name": "mydb"}))


# ---------------------------------------------------------------------------
# load_schema_from_file
# ---------------------------------------------------------------------------

def test_load_schema_from_file_basic():
    path = _write_tmp_json(SAMPLE_SCHEMA)
    try:
        schema = load_schema_from_file(path)
        assert schema.name == "mydb"
        assert len(schema.tables) == 1
    finally:
        os.unlink(path)


def test_load_schema_from_file_not_found():
    with pytest.raises(FileNotFoundError, match="Schema file not found"):
        load_schema_from_file("/nonexistent/path/schema.json")


def test_load_schema_from_file_invalid_json():
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        fh.write("{bad json")
    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_schema_from_file(path)
    finally:
        os.unlink(path)


def test_load_schema_from_file_missing_keys():
    path = _write_tmp_json({"name": "only_name"})
    try:
        with pytest.raises(ValueError, match="missing required keys"):
            load_schema_from_file(path)
    finally:
        os.unlink(path)
