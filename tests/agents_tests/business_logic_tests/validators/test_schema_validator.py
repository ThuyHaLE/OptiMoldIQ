import json
import pytest
from pathlib import Path

from agents.dataPipelineOrchestrator.validators.schema_validator import SchemaValidator
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    ProcessingStatus,
    ErrorType,
)


# =========================
# Helpers
# =========================

def write_json(tmp_path: Path, data, name="schema.json"):
    path = tmp_path / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def minimal_valid_schema():
    return {
        "dynamicDB": {},
        "staticDB": {}
    }


def valid_dynamic_table():
    return {
        "path": "./data",
        "name_start": "file_",
        "extension": ".csv",
        "sheet_name": "Sheet1",
        "required_fields": ["a"],
        "dtypes": {"a": "string"}
    }


def valid_static_table():
    return {
        "path": "./file.csv",
        "dtypes": {"a": "string"}
    }


# =========================
# validate() – early exits
# =========================

def test_validate_file_not_found(tmp_path):
    validator = SchemaValidator(str(tmp_path / "missing.json"))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.FILE_NOT_FOUND


def test_validate_invalid_extension(tmp_path):
    path = tmp_path / "schema.txt"
    path.write_text("x")

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.FILE_NOT_VALID


def test_validate_invalid_json(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text("{ invalid json }")

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_JSON


def test_validate_empty_json(tmp_path):
    path = write_json(tmp_path, {})

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.MISSING_FIELDS


# =========================
# Top-level structure
# =========================

def test_missing_top_level_keys(tmp_path):
    path = write_json(tmp_path, {"dynamicDB": {}})

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.MISSING_FIELDS


def test_extra_top_level_keys_warning(tmp_path):
    schema = {
        "dynamicDB": {
            "table1": valid_dynamic_table()
        },
        "staticDB": {
            "table2": valid_static_table()
        },
        "extra": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    # Fix assertions:
    assert result.status == ProcessingStatus.WARNING
    assert result.metadata["warnings_count"] == 1
    assert "extra" in result.metadata["warnings"][0].lower()


# =========================
# dynamicDB validation
# =========================

def test_dynamic_db_invalid_table(tmp_path):
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                # missing required fields
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH


def test_dynamic_db_valid_with_warning(tmp_path):
    schema = {
        "dynamicDB": {
            "table1": {
                **valid_dynamic_table(),
                "extension": ".weird"
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.WARNING
    assert result.metadata["warnings_count"] >= 1


# =========================
# staticDB validation
# =========================

def test_static_db_invalid_dtypes(tmp_path):
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {"a": "invalid_dtype"}
            }
        }
    }
    path = write_json(tmp_path, schema)

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH


# =========================
# Full success path
# =========================

def test_validate_full_success(tmp_path):
    schema = {
        "dynamicDB": {
            "dyn1": valid_dynamic_table()
        },
        "staticDB": {
            "stat1": valid_static_table()
        }
    }
    path = write_json(tmp_path, schema)

    validator = SchemaValidator(str(path))
    result = validator.validate()

    assert result.status == ProcessingStatus.SUCCESS
    assert result.metadata["validation_passed"] is True
    assert result.metadata["total_tables"] == 2
