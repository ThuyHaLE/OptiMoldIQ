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


# =========================
# ErrorType.FILE_READ_ERROR
# =========================

def test_file_read_error_permission(tmp_path):
    """Test FILE_READ_ERROR when file cannot be read due to permissions"""
    path = tmp_path / "schema.json"
    path.write_text('{"dynamicDB": {}, "staticDB": {}}')
    
    # Make file unreadable (Unix-like systems)
    import os
    if os.name != 'nt':  # Skip on Windows
        path.chmod(0o000)
        
        validator = SchemaValidator(str(path))
        result = validator.validate()
        
        # Restore permissions for cleanup
        path.chmod(0o644)
        
        assert result.status == ProcessingStatus.ERROR
        assert result.error_type == ErrorType.FILE_READ_ERROR


# =========================
# ErrorType.INVALID_SCHEMA_STRUCTURE
# =========================

def test_invalid_schema_structure_top_level_not_dict(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when top-level key is not a dict"""
    schema = {
        "dynamicDB": [],  # Should be dict, not list
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.INVALID_SCHEMA_STRUCTURE


def test_invalid_schema_structure_table_config_not_dict(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when table config is not a dict"""
    schema = {
        "dynamicDB": {
            "table1": "not_a_dict"  # Should be dict
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    # Table-level errors are wrapped in SCHEMA_MISMATCH
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    # But underlying error in table_errors is INVALID_SCHEMA_STRUCTURE
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_path_not_string(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when path is not a string"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": 123,  # Should be string
                "dtypes": {"a": "string"}
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_empty_path(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when path is empty"""
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
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_dtypes_not_dict(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when dtypes is not a dict"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": ["string"]  # Should be dict
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_empty_dtypes(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when dtypes is empty"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {}  # Empty dict
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_name_start_not_string(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when name_start is not a string"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": 123,  # Should be string
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
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_extension_not_string(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when extension is not a string"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": 123,  # Should be string
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
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_sheet_name_empty(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when sheet_name is empty"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "",  # Empty
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
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


def test_invalid_schema_structure_required_fields_not_list(tmp_path):
    """Test INVALID_SCHEMA_STRUCTURE when required_fields is not a list"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": "not_a_list",  # Should be list
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
    assert result.metadata["table_errors"][0]["error_type"] == "invalid_schema_structure"


# =========================
# ErrorType.UNSUPPORTED_DATA_TYPE
# =========================

def test_unsupported_data_type_invalid_dtype(tmp_path):
    """Test UNSUPPORTED_DATA_TYPE when dtype is not in VALID_DTYPES"""
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
    assert result.metadata["table_errors"][0]["error_type"] == "unsupported_data_type"


def test_unsupported_data_type_dtype_not_string(tmp_path):
    """Test UNSUPPORTED_DATA_TYPE when dtype value is not a string"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": {"a": 123}  # Should be string
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "unsupported_data_type"


def test_unsupported_data_type_multiple_invalid(tmp_path):
    """Test UNSUPPORTED_DATA_TYPE when multiple dtypes are invalid"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a", "b"],
                "dtypes": {
                    "a": "wrong_type",
                    "b": 999,
                    "c": "string"
                }
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "unsupported_data_type"


# =========================
# ErrorType.SCHEMA_MISMATCH
# =========================

def test_schema_mismatch_required_fields_missing_in_dtypes(tmp_path):
    """Test SCHEMA_MISMATCH when required_fields contain fields not in dtypes"""
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


def test_schema_mismatch_multiple_table_errors(tmp_path):
    """Test SCHEMA_MISMATCH when multiple tables have errors"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["missing"],
                "dtypes": {"a": "string"}
            },
            "table2": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["also_missing"],
                "dtypes": {"b": "string"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["error_count"] == 2


# =========================
# ErrorType.MISSING_FIELDS
# =========================

"""
IMPORTANT: Error Wrapping Behavior in SchemaValidator

There are TWO levels of errors:

1. TOP-LEVEL ERRORS (returned directly with their ErrorType):
   - File path validation errors (FILE_NOT_FOUND, FILE_NOT_VALID)
   - JSON parsing errors (INVALID_JSON, FILE_READ_ERROR)
   - Top-level structure errors (MISSING_FIELDS for missing dynamicDB/staticDB)
   - INVALID_SCHEMA_STRUCTURE when top-level keys are not dicts

2. TABLE-LEVEL ERRORS (wrapped in SCHEMA_MISMATCH):
   - Any error from _validate_table_config() and its helper methods
   - The actual error type is preserved in metadata["table_errors"][]["error_type"]
   - The top-level error_type will be SCHEMA_MISMATCH
   - This includes:
     * MISSING_FIELDS (missing table fields)
     * INVALID_SCHEMA_STRUCTURE (wrong types in table config)
     * UNSUPPORTED_DATA_TYPE (invalid dtypes)
     * SCHEMA_MISMATCH (required_fields not in dtypes)

Example:
  If a table has invalid dtype, the result will be:
  - result.error_type == ErrorType.SCHEMA_MISMATCH
  - result.metadata["table_errors"][0]["error_type"] == "unsupported_data_type"
"""

def test_missing_fields_dynamic_table(tmp_path):
    """Test MISSING_FIELDS when dynamicDB table is missing required fields"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "dtypes": {"a": "string"}
                # Missing: name_start, extension, sheet_name, required_fields
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "missing_fields"


def test_missing_fields_static_table(tmp_path):
    """Test MISSING_FIELDS when staticDB table is missing required fields"""
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv"
                # Missing: dtypes
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.SCHEMA_MISMATCH
    assert result.metadata["table_errors"][0]["error_type"] == "missing_fields"


def test_missing_fields_top_level_missing_staticdb(tmp_path):
    """Test MISSING_FIELDS when top-level is missing staticDB"""
    schema = {
        "dynamicDB": {}
        # Missing: staticDB
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.MISSING_FIELDS
    assert "staticDB" in result.metadata["missing_keys"]


def test_missing_fields_top_level_missing_dynamicdb(tmp_path):
    """Test MISSING_FIELDS when top-level is missing dynamicDB"""
    schema = {
        "staticDB": {}
        # Missing: dynamicDB
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.ERROR
    assert result.error_type == ErrorType.MISSING_FIELDS
    assert "dynamicDB" in result.metadata["missing_keys"]


# =========================
# Warnings (not errors)
# =========================

def test_warning_empty_required_fields(tmp_path):
    """Test warning when required_fields is empty"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": [],  # Empty but valid
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
    assert any("required_fields" in w for w in result.metadata["warnings"])


def test_warning_duplicate_required_fields(tmp_path):
    """Test warning when required_fields contains duplicates"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["a", "a", "b"],  # Duplicate 'a'
                "dtypes": {"a": "string", "b": "Int64"}
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.WARNING
    assert result.metadata["warnings_count"] >= 1
    assert any("Duplicate" in w for w in result.metadata["warnings"])


def test_warning_empty_dynamicdb_and_staticdb(tmp_path):
    """Test warning when both dynamicDB and staticDB are empty"""
    schema = {
        "dynamicDB": {},
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.WARNING
    assert result.metadata["warnings_count"] >= 2
    assert any("dynamicDB is empty" in w for w in result.metadata["warnings"])
    assert any("staticDB is empty" in w for w in result.metadata["warnings"])


# =========================
# Edge cases
# =========================

def test_normalize_field_name_fixes_typos(tmp_path):
    """Test that normalize_field_name handles known typos"""
    schema = {
        "dynamicDB": {
            "table1": {
                "path": "./data",
                "name_start": "file_",
                "extension": ".csv",
                "sheet_name": "Sheet1",
                "required_fields": ["plasticResine"],  # Typo
                "dtypes": {"plasticResin": "string"}  # Correct
            }
        },
        "staticDB": {}
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    # Should pass because normalize_field_name fixes the typo
    assert result.status == ProcessingStatus.SUCCESS


def test_all_valid_dtypes_accepted(tmp_path):
    """Test that all valid dtypes are accepted"""
    all_dtypes = {
        "f1": "string",
        "f2": "Int64",
        "f3": "Float64",
        "f4": "bool",
        "f5": "datetime64[ns]",
        "f6": "timedelta64[ns]",
        "f7": "Int8",
        "f8": "Int16",
        "f9": "Int32",
        "f10": "Float32",
        "f11": "UInt8",
        "f12": "UInt16",
        "f13": "UInt32",
        "f14": "UInt64"
    }
    
    schema = {
        "dynamicDB": {},
        "staticDB": {
            "table1": {
                "path": "./file.csv",
                "dtypes": all_dtypes
            }
        }
    }
    path = write_json(tmp_path, schema)
    
    validator = SchemaValidator(str(path))
    result = validator.validate()
    
    assert result.status == ProcessingStatus.SUCCESS


def test_all_valid_extensions_accepted(tmp_path):
    """Test that all valid extensions are accepted without warning"""
    extensions = [".xlsx", ".xlsb", ".csv", ".parquet"]
    
    for ext in extensions:
        schema = {
            "dynamicDB": {
                "table1": {
                    "path": "./data",
                    "name_start": "file_",
                    "extension": ext,
                    "sheet_name": "Sheet1",
                    "required_fields": ["a"],
                    "dtypes": {"a": "string"}
                }
            },
            "staticDB": {}
        }
        path = write_json(tmp_path, schema, f"schema_{ext}.json")
        
        validator = SchemaValidator(str(path))
        result = validator.validate()
        
        # Should not have warnings about extension
        extension_warnings = [w for w in result.metadata.get("warnings", []) if "extension" in w.lower()]
        assert len(extension_warnings) == 0, f"Extension {ext} should be valid"