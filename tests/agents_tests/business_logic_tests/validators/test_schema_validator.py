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
# Empty schema path edge cases
# =========================

def test_validate_empty_string_path(tmp_path):
    """Test that empty string path is handled correctly"""
    validator = SchemaValidator("")
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.FILE_NOT_VALID


# =========================
# Non-dict JSON handling
# =========================

def test_validate_json_is_list(tmp_path):
    """Test that JSON arrays are rejected"""
    path = write_json(tmp_path, ["item1", "item2"])
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_JSON
    assert "must be a JSON object" in result.error_message


def test_validate_json_is_string(tmp_path):
    """Test that JSON strings are rejected"""
    path = write_json(tmp_path, "just a string")
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_JSON


# =========================
# Top-level structure validation
# =========================

def test_top_level_dynamicdb_not_dict(tmp_path):
    """Test that non-dict dynamicDB is rejected"""
    schema = {
        "dynamicDB": "not a dict",
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "dynamicDB" in result.error_message


def test_top_level_staticdb_not_dict(tmp_path):
    """Test that non-dict staticDB is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": ["not", "a", "dict"]
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "staticDB" in result.error_message


# =========================
# Empty database warnings
# =========================

def test_empty_dynamicdb_warning(tmp_path):
    """Test that empty dynamicDB generates warning"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": valid_static_table()
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.SUCCESS
    assert "dynamicDB is empty" in result.metadata.get("warnings", [])


def test_empty_staticdb_warning(tmp_path):
    """Test that empty staticDB generates warning"""
    schema = {
        "dynamicDB": {
            "table1": valid_dynamic_table()
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.SUCCESS
    assert "staticDB is empty" in result.metadata.get("warnings", [])


# =========================
# Table config type validation
# =========================

def test_dynamic_table_not_dict(tmp_path):
    """Test that non-dict table config is rejected"""
    schema = {
        "dynamicDB": {
            "table1": "not a dict"
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_static_table_not_dict(tmp_path):
    """Test that non-dict static table config is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": ["path", "dtypes"]
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


# =========================
# Path field validation
# =========================

def test_path_not_string(tmp_path):
    """Test that non-string path is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": 123,  # Not a string
                "dtypes": {"a": "string"}
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "path" in result.error_message


def test_path_empty_string(tmp_path):
    """Test that empty path string is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "   ",  # Empty/whitespace only
                "dtypes": {"a": "string"}
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "path" in result.error_message


# =========================
# Dtypes field validation
# =========================

def test_dtypes_not_dict(tmp_path):
    """Test that non-dict dtypes is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": ["string", "int"]  # Not a dict
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "dtypes" in result.error_message


def test_dtypes_empty(tmp_path):
    """Test that empty dtypes dict is rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {}  # Empty
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_dtypes_value_not_string(tmp_path):
    """Test that non-string dtype values are rejected"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {"a": 123}  # Not a string
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE


def test_dtypes_multiple_invalid_types(tmp_path):
    """Test that multiple invalid dtypes are caught"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {
                    "a": "string",
                    "b": "invalid_type",
                    "c": 456,
                    "d": "another_invalid"
                }
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.UNSUPPORTED_DATA_TYPE


# =========================
# Dynamic-specific field validation
# =========================

def test_name_start_not_string(tmp_path):
    """Test that non-string name_start is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": 123,
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a"],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "name_start" in result.error_message


def test_name_start_empty_string(tmp_path):
    """Test that empty name_start is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "  ",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a"],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_extension_not_string(tmp_path):
    """Test that non-string extension is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": 123,
                "sheet_name": "Sheet1",
                "required_fields": ["a"],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE
    assert "extension" in result.error_message


def test_sheet_name_not_string(tmp_path):
    """Test that non-string sheet_name is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": None,
                "required_fields": ["a"],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_sheet_name_empty(tmp_path):
    """Test that empty sheet_name is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "",
                "required_fields": ["a"],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_required_fields_not_list(tmp_path):
    """Test that non-list required_fields is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": "not a list",
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_required_fields_empty_warning(tmp_path):
    """Test that empty required_fields generates warning"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": [],
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.WARNING
    assert result.metadata["warnings_count"] >= 1


def test_required_fields_not_in_dtypes(tmp_path):
    """Test that required_fields not in dtypes is rejected"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a", "b", "c"],
                "dtypes": {"a": "string"}  # Missing b and c
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH


def test_required_fields_duplicates_warning(tmp_path):
    """Test that duplicate required_fields generates warning"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a", "b", "a", "c", "b"],
                "dtypes": {"a": "string", "b": "Int64", "c": "Float64"}
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
# Field name normalization
# =========================

def test_normalize_field_name_with_typo(tmp_path):
    """Test that field name normalization handles known typos"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["plasticResine"],
                "dtypes": {"plasticResin": "string"}  # Correct spelling
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    # Should succeed because normalize_field_name corrects the typo
    assert result.status == ProcessingStatus.SUCCESS


# =========================
# File read error handling
# =========================

def test_file_read_permission_error(tmp_path):
    """Test handling of file read permission errors"""
    path = tmp_path / "schema.json"
    path.write_text('{"dynamicDB": {}, "staticDB": {}}')
    path.chmod(0o000)  # Remove all permissions
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    # Restore permissions for cleanup
    path.chmod(0o644)
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.FILE_READ_ERROR


# =========================
# Multiple tables validation
# =========================

def test_multiple_tables_mixed_errors(tmp_path):
    """Test validation with multiple tables where some fail"""
    schema = {
        "dynamicDB": {
            "good_table": valid_dynamic_table(),
            "bad_table": {
                "path": "./data",
                # Missing required fields
                "dtypes": {"a": "string"}
            }
        },
        "staticDB": {
            "another_good": valid_static_table()
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["error_count"] == 1


# =========================
# All valid dtypes test
# =========================

def test_all_valid_dtypes(tmp_path):
    """Test that all documented valid dtypes are accepted"""
    valid_dtypes_schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {
                    "col1": "string",
                    "col2": "Int64",
                    "col3": "Float64",
                    "col4": "bool",
                    "col5": "datetime64[ns]",
                    "col6": "timedelta64[ns]",
                    "col7": "Int8",
                    "col8": "Int16",
                    "col9": "Int32",
                    "col10": "Float32",
                    "col11": "UInt8",
                    "col12": "UInt16",
                    "col13": "UInt32",
                    "col14": "UInt64"
                }
            }
        }
    }
    path = write_json(tmp_path, valid_dtypes_schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.SUCCESS


# =========================
# Metadata validation
# =========================

def test_success_metadata_completeness(tmp_path):
    """Test that successful validation includes all expected metadata"""
    schema = {
        "dynamicDB": {
            "dyn1": valid_dynamic_table(),
            "dyn2": valid_dynamic_table()
        },
        "staticDB": {
            "stat1": valid_static_table()
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.SUCCESS
    assert "schema_path" in result.metadata
    assert "dynamicDB_tables" in result.metadata
    assert "staticDB_tables" in result.metadata
    assert "total_tables" in result.metadata
    assert "validation_passed" in result.metadata
    assert result.metadata["dynamicDB_tables"] == 2
    assert result.metadata["staticDB_tables"] == 1
    assert result.metadata["total_tables"] == 3
    assert result.metadata["validation_passed"] is True