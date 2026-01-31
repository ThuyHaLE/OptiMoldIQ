# agents/dataPipelineOrchestrator/validators/schema_validator.py

from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport, ProcessingStatus, ErrorType

from configs.shared.config_report_format import ConfigReportMixin
from typing import Dict, List, Set, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
import json

class SchemaValidator(ConfigReportMixin):
    """
    Validator for database schema configuration.
    
    Validates the structure and content of database schema JSON files,
    ensuring they conform to the expected format for both dynamicDB and staticDB.
    """
    
    # Required top-level keys
    REQUIRED_TOP_LEVEL_KEYS = {"dynamicDB", "staticDB"}
    
    # Required fields for dynamicDB tables
    DYNAMIC_DB_REQUIRED_FIELDS = {
        "path", "name_start", "extension", "sheet_name", 
        "required_fields", "dtypes"
    }
    
    # Required fields for staticDB tables
    STATIC_DB_REQUIRED_FIELDS = {"path", "dtypes"}
    
    # Valid pandas dtypes
    VALID_DTYPES = {
        "string", "Int64", "Float64", "bool", 
        "datetime64[ns]", "timedelta64[ns]",
        "Int8", "Int16", "Int32", 
        "Float32", "UInt8", "UInt16", "UInt32", "UInt64"
    }
    
    # Valid file extensions
    VALID_EXTENSIONS = {".xlsx", ".xlsb", ".csv", ".parquet"}
    
    def __init__(self, schema_path: str):
        """
        Initialize validator with schema file path.

        Schema Format: 
        {
            "dynamicDB": {
                "<DBname>": {
                    "path": "<folder_path>",        // e.g. "../folder_name"
                    "name_start": "<prefix>",
                    "extension": "<file_ext>",
                    "sheet_name": "<sheet>",
                    "required_fields": ["<field1>", "<field2>"],
                    "dtypes": { "<column>": "<dtype>" }
                }
            }, 
            "staticDB": {
                "<DBname>": {
                    "path": "<file_path>",          // e.g. "./file.xlsx"
                    "dtypes": { "<column>": "<dtype>" }
                }
            }
        }
        
        Args:
            schema_path: Path to the schema JSON file
        """
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger for this class
        self.logger = logger.bind(class_name="SchemaValidator")

        self.schema_path = Path(schema_path)
        self.schema_data: Optional[Dict] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> DataProcessingReport:
        """
        Run full validation pipeline.
        
        Validates file path, loads schema, and validates structure of both
        dynamicDB and staticDB configurations.
        
        Returns:
            DataProcessingReport with validation results, including:
            - status: SUCCESS, WARNING, or ERROR
            - data: Validated schema data (if successful)
            - metadata: Detailed validation information
        """
        class_id = self.__class__.__name__
        self.logger.info(f"Starting {class_id} validation...")
        
        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        # Step 1: Validate file path
        result = self._validate_file_path()
        if result.is_error:
            return result
        
        # Step 2: Load and parse JSON
        result = self._load_schema()
        if result.is_error:
            return result
        
        # Step 3: Validate top-level structure
        result = self._validate_top_level_structure()
        if result.is_error:
            return result
        
        # Step 4: Validate dynamicDB
        result = self._validate_dynamic_db()
        if result.is_error:
            return result
        
        # Step 5: Validate staticDB
        result = self._validate_static_db()
        if result.is_error:
            return result
        
        # All validations passed
        return self._create_success_report(class_id, config_header)
    
    def _create_success_report(self, 
                               class_id: str, 
                               config_header: str) -> DataProcessingReport:
        """
        Create final success report with summary.
        
        Args:
            class_id: Name of the validator class
            config_header: Configuration header for logging
            
        Returns:
            DataProcessingReport with final validation results
        """
        log_entries = self._process_log_entries(class_id, config_header)
        self.logger.info(log_entries)

        # Determine final status
        if self.errors:
            status = ProcessingStatus.ERROR
        elif self.warnings:
            status = ProcessingStatus.WARNING
        else:
            status = ProcessingStatus.SUCCESS
        
        # Count tables
        dynamic_count = len(self.schema_data.get("dynamicDB", {}))
        static_count = len(self.schema_data.get("staticDB", {}))
        
        return DataProcessingReport(
            status=status,
            data=self.schema_data,
            error_type=ErrorType.NONE,
            error_message="",
            metadata={
                "schema_path": str(self.schema_path),
                "dynamicDB_tables": dynamic_count,
                "staticDB_tables": static_count,
                "total_tables": dynamic_count + static_count,
                "warnings_count": len(self.warnings),
                "warnings": self.warnings,
                "errors_count": len(self.errors),
                "errors": self.errors,
                "validation_passed": len(self.errors) == 0,
                "log": log_entries
            }
        )
    
    def _process_log_entries(self, 
                             class_id: str, 
                             config_header: str) -> str:
        """
        Process and format log entries for final report.
        
        Args:
            class_id: Name of the validator class
            config_header: Configuration header
            
        Returns:
            Formatted log entries as a single string
        """
        log_entries = [
            config_header,
            f"--Processing Summary--",
            f"⤷ {class_id} results:"
        ]
        
        if self.warnings:
            log_entries.append(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                log_entries.append(f"  {i}. {warning}")
        
        if self.errors:
            log_entries.append(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                log_entries.append(f"  {i}. {error}")
            log_entries.append("\n❌ VALIDATION FAILED")
        else:
            log_entries.append("\n✅ VALIDATION PASSED")
            if self.warnings:
                log_entries.append(f"   ({len(self.warnings)} warning(s) found)")

        return "\n".join(log_entries)

    def _validate_file_path(self) -> DataProcessingReport:
        """
        Validate schema file path and extension.
        
        Checks:
        1. Path is provided (not empty)
        2. File extension is .json
        3. File exists on filesystem
        
        Returns:
            DataProcessingReport with validation result
        """
        self.logger.info("[1] Validating File Path...")
        
        #--------------------------------------#
        # Q: Is the data schema path provided? #
        #--------------------------------------#
        if not str(self.schema_path):
            error_msg = "Schema path is empty"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.FILE_NOT_VALID,
                error_message=error_msg,
                metadata={"step": "file_path_validation", "path": str(self.schema_path)}
            )
        
        self.logger.info(f"  ✅ Schema path provided: {self.schema_path}")
        
        #-------------------------------------------------------------------------#
        # Q: Is the file extension supported? (Currently only .json is supported) #
        #-------------------------------------------------------------------------#
        file_extension = self.schema_path.suffix.lower()
        if file_extension != '.json':
            error_msg = f"Invalid file extension: {file_extension}. Expected .json"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.FILE_NOT_VALID,
                error_message=error_msg,
                metadata={
                    "step": "file_path_validation",
                    "path": str(self.schema_path),
                    "extension": file_extension
                }
            )
        
        self.logger.info(f"  ✅ File extension is valid: {file_extension}")
        
        #-------------------------------------------------#
        # Q: Does the file path exist on the filesystem?  #
        #-------------------------------------------------#
        if not self.schema_path.exists():
            error_msg = f"Schema file not found: {self.schema_path}"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.FILE_NOT_FOUND,
                error_message=error_msg,
                metadata={"step": "file_path_validation", "path": str(self.schema_path)}
            )
        
        self.logger.info(f"  ✅ File exists: {self.schema_path}")
        
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={"step": "file_path_validation"}
        )
    
    def _load_schema(self) -> DataProcessingReport:
        """
        Load and parse JSON schema file.
        
        Validates:
        1. File is readable
        2. Content is valid JSON
        3. JSON root is a dictionary
        4. Dictionary is not empty
        
        Returns:
            DataProcessingReport with loaded schema or error
        """
        self.logger.info("[2] Loading Schema File...")
        
        try:
            #---------------------------------------#
            # Q: Is the file at this path loadable? #
            #---------------------------------------#
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self.schema_data = json.load(f)
            
            if not self.schema_data:
                error_msg = "Schema file is empty"
                self.logger.error(f"  ❌ {error_msg}")
                return DataProcessingReport(
                    status=ProcessingStatus.ERROR,
                    data=None,
                    error_type=ErrorType.INVALID_JSON,
                    error_message=error_msg,
                    metadata={"step": "load_schema", "path": str(self.schema_path)}
                )
            
            if not isinstance(self.schema_data, dict):
                error_msg = f"Schema must be a JSON object, got {type(self.schema_data).__name__}"
                self.logger.error(f"  ❌ {error_msg}")
                return DataProcessingReport(
                    status=ProcessingStatus.ERROR,
                    data=None,
                    error_type=ErrorType.INVALID_JSON,
                    error_message=error_msg,
                    metadata={
                        "step": "load_schema",
                        "path": str(self.schema_path),
                        "type": type(self.schema_data).__name__
                    }
                )
            
            self.logger.info(f"  ✅ Schema loaded successfully")
            self.logger.info(f"  ✅ Schema contains {len(self.schema_data)} top-level keys")
            
            return DataProcessingReport(
                status=ProcessingStatus.SUCCESS,
                data=self.schema_data,
                metadata={
                    "step": "load_schema",
                    "top_level_keys": list(self.schema_data.keys())
                }
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_JSON,
                error_message=error_msg,
                metadata={
                    "step": "load_schema",
                    "path": str(self.schema_path),
                    "json_error": str(e)
                }
            )
        except Exception as e:
            error_msg = f"Failed to load schema: {str(e)}"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.FILE_READ_ERROR,
                error_message=error_msg,
                metadata={
                    "step": "load_schema",
                    "path": str(self.schema_path),
                    "exception": str(e)
                }
            )
    
    def _validate_top_level_structure(self) -> DataProcessingReport:
        """
        Validate top-level schema structure.
        
        Ensures:
        1. Required keys 'dynamicDB' and 'staticDB' are present
        2. Each required key maps to a dictionary
        3. Warns about extra unexpected keys
        
        Returns:
            DataProcessingReport with validation result
        """
        self.logger.info("[3] Validating Top-Level Structure...")
        
        current_keys = set(self.schema_data.keys())

        # Check required keys
        missing_keys = self.REQUIRED_TOP_LEVEL_KEYS - current_keys
        if missing_keys:
            error_msg = f"Missing required top-level keys: {sorted(missing_keys)}"
            self.logger.error(f"  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.MISSING_FIELDS,
                error_message=error_msg,
                metadata={
                    "step": "top_level_structure",
                    "missing_keys": sorted(missing_keys),
                    "current_keys": sorted(current_keys),
                    "required_keys": sorted(self.REQUIRED_TOP_LEVEL_KEYS)
                }
            )
        
        self.logger.info(f"  ✅ All required top-level keys present: {sorted(self.REQUIRED_TOP_LEVEL_KEYS)}")
        
        # Check for extra keys (warning only)
        extra_keys = current_keys - self.REQUIRED_TOP_LEVEL_KEYS
        if extra_keys:
            warning_msg = f"Extra top-level keys found: {sorted(extra_keys)}"
            self.warnings.append(warning_msg)
            self.logger.warning(f"  ⚠️  {warning_msg}")
        
        # Validate each top-level key is a dict
        for key in self.REQUIRED_TOP_LEVEL_KEYS:
            if not isinstance(self.schema_data[key], dict):
                error_msg = f"'{key}' must be an object, got {type(self.schema_data[key]).__name__}"
                self.logger.error(f"  ❌ {error_msg}")
                return DataProcessingReport(
                    status=ProcessingStatus.ERROR,
                    data=None,
                    error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                    error_message=error_msg,
                    metadata={
                        "step": "top_level_structure",
                        "invalid_key": key,
                        "expected_type": "dict",
                        "actual_type": type(self.schema_data[key]).__name__
                    }
                )
        
        self.logger.info(f"  ✅ Top-level structure is valid")
        
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={
                "step": "top_level_structure",
                "extra_keys": sorted(extra_keys) if extra_keys else []
            }
        )
    
    def _validate_dynamic_db(self) -> DataProcessingReport:
        """
        Validate dynamicDB structure and all table configurations.
        
        Returns:
            DataProcessingReport with validation result
        """
        self.logger.info("[4] Validating dynamicDB...")
        
        dynamic_db = self.schema_data["dynamicDB"]
        
        if not dynamic_db:
            warning_msg = "dynamicDB is empty"
            self.warnings.append(warning_msg)
            self.logger.warning(f"  ⚠️  {warning_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.SUCCESS,
                data=None,
                metadata={"step": "dynamicDB_validation", "table_count": 0}
            )
        
        self.logger.info(f"  ℹ️  Found {len(dynamic_db)} table(s) in dynamicDB")
        
        table_errors = []
        for table_name, table_config in dynamic_db.items():
            self.logger.info(f"\n  Validating table: '{table_name}'")
            
            result = self._validate_table_config(
                table_name, 
                table_config, 
                self.DYNAMIC_DB_REQUIRED_FIELDS,
                is_dynamic=True
            )
            
            if result.is_error:
                table_errors.append({
                    "table": table_name,
                    "error": result.error_message,
                    "error_type": result.error_type.value
                })
                self.errors.append(f"Table '{table_name}': {result.error_message}")
        
        if table_errors:
            error_msg = f"Found {len(table_errors)} invalid table(s) in dynamicDB"
            self.logger.error(f"\n  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.SCHEMA_MISMATCH,
                error_message=error_msg,
                metadata={
                    "step": "dynamicDB_validation",
                    "table_count": len(dynamic_db),
                    "error_count": len(table_errors),
                    "table_errors": table_errors
                }
            )
        
        self.logger.info(f"\n  ✅ All dynamicDB tables are valid")
        
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={
                "step": "dynamicDB_validation",
                "table_count": len(dynamic_db),
                "tables": list(dynamic_db.keys())
            }
        )
    
    def _validate_static_db(self) -> DataProcessingReport:
        """
        Validate staticDB structure and all table configurations.
        
        Returns:
            DataProcessingReport with validation result
        """
        self.logger.info("[5] Validating staticDB...")
        
        static_db = self.schema_data["staticDB"]
        
        if not static_db:
            warning_msg = "staticDB is empty"
            self.warnings.append(warning_msg)
            self.logger.warning(f"  ⚠️  {warning_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.SUCCESS,
                data=None,
                metadata={"step": "staticDB_validation", "table_count": 0}
            )
        
        self.logger.info(f"  ℹ️  Found {len(static_db)} table(s) in staticDB")
        
        table_errors = []
        for table_name, table_config in static_db.items():
            self.logger.info(f"\n  Validating table: '{table_name}'")
            
            result = self._validate_table_config(
                table_name, 
                table_config, 
                self.STATIC_DB_REQUIRED_FIELDS,
                is_dynamic=False
            )
            
            if result.is_error:
                table_errors.append({
                    "table": table_name,
                    "error": result.error_message,
                    "error_type": result.error_type.value
                })
                self.errors.append(f"Table '{table_name}': {result.error_message}")
        
        if table_errors:
            error_msg = f"Found {len(table_errors)} invalid table(s) in staticDB"
            self.logger.error(f"\n  ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.SCHEMA_MISMATCH,
                error_message=error_msg,
                metadata={
                    "step": "staticDB_validation",
                    "table_count": len(static_db),
                    "error_count": len(table_errors),
                    "table_errors": table_errors
                }
            )
        
        self.logger.info(f"\n  ✅ All staticDB tables are valid")
        
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={
                "step": "staticDB_validation",
                "table_count": len(static_db),
                "tables": list(static_db.keys())
            }
        )
    
    def _validate_table_config(
            self, 
            table_name: str, 
            config: Any, 
            required_fields: Set[str],
            is_dynamic: bool
        ) -> DataProcessingReport:
        """
        Validate individual table configuration.
        
        Args:
            table_name: Name of the table
            config: Table configuration dict
            required_fields: Set of required field names
            is_dynamic: Whether this is a dynamicDB table
            
        Returns:
            DataProcessingReport with validation result
        """
        if not isinstance(config, dict):
            error_msg = f"Config must be an object, got {type(config).__name__}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "expected_type": "dict",
                    "actual_type": type(config).__name__
                }
            )
        
        # Check required fields
        current_fields = set(config.keys())
        missing_fields = required_fields - current_fields
        
        if missing_fields:
            error_msg = f"Missing required fields: {sorted(missing_fields)}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.MISSING_FIELDS,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "missing_fields": sorted(missing_fields),
                    "current_fields": sorted(current_fields),
                    "required_fields": sorted(required_fields)
                }
            )
        
        self.logger.info(f"    ✅ All required fields present")
        
        # Validate 'path' field
        result = self._validate_path_field(table_name, config.get("path"))
        if result.is_error:
            return result
        
        # Validate 'dtypes' field
        result = self._validate_dtypes_field(table_name, config.get("dtypes"))
        if result.is_error:
            return result
        
        # Dynamic DB specific validations
        if is_dynamic:
            result = self._validate_dynamic_specific_fields(table_name, config)
            if result.is_error:
                return result
        
        self.logger.info(f"    ✅ Table '{table_name}' is valid")
        
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={"table": table_name}
        )
    
    def _validate_path_field(self, 
                             table_name: str, 
                             path: Any) -> DataProcessingReport:
        """
        Validate 'path' field in table configuration.
        
        Args:
            table_name: Name of the table
            path: Path value to validate
            
        Returns:
            DataProcessingReport with validation result
        """
        if not isinstance(path, str):
            error_msg = f"'path' must be a string, got {type(path).__name__}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "field": "path",
                    "expected_type": "str",
                    "actual_type": type(path).__name__
                }
            )
        
        if not path.strip():
            error_msg = "'path' is empty"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "path"}
            )
        
        self.logger.info(f"    ✅ Valid path: {path}")
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={"table": table_name, "path": path}
        )
    
    def _validate_dtypes_field(self, 
                               table_name: str, 
                               dtypes: Any) -> DataProcessingReport:
        """
        Validate 'dtypes' field in table configuration.
        
        Args:
            table_name: Name of the table
            dtypes: Dtypes dictionary to validate
            
        Returns:
            DataProcessingReport with validation result
        """
        if not isinstance(dtypes, dict):
            error_msg = f"'dtypes' must be an object, got {type(dtypes).__name__}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "field": "dtypes",
                    "expected_type": "dict",
                    "actual_type": type(dtypes).__name__
                }
            )
        
        if not dtypes:
            error_msg = "'dtypes' is empty"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "dtypes"}
            )
        
        # Validate each dtype
        invalid_dtypes = {}
        for field, dtype in dtypes.items():
            if not isinstance(dtype, str):
                invalid_dtypes[field] = f"not a string (got {type(dtype).__name__})"
            elif dtype not in self.VALID_DTYPES:
                invalid_dtypes[field] = f"invalid dtype '{dtype}'"
        
        if invalid_dtypes:
            error_msg = f"Invalid dtypes found: {invalid_dtypes}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.UNSUPPORTED_DATA_TYPE,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "field": "dtypes",
                    "invalid_dtypes": invalid_dtypes,
                    "valid_dtypes": sorted(self.VALID_DTYPES)
                }
            )
        
        self.logger.info(f"    ✅ Valid dtypes ({len(dtypes)} fields)")
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={"table": table_name, "dtypes_count": len(dtypes)}
        )
    
    def _validate_dynamic_specific_fields(
            self, 
            table_name: str, 
            config: Dict
        ) -> DataProcessingReport:
        """
        Validate dynamicDB-specific fields.
        
        Validates: name_start, extension, sheet_name, required_fields
        
        Args:
            table_name: Name of the table
            config: Table configuration dict
            
        Returns:
            DataProcessingReport with validation result
        """
        # Validate 'name_start'
        name_start = config.get("name_start")
        if not isinstance(name_start, str) or not name_start.strip():
            error_msg = "'name_start' must be a non-empty string"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "name_start"}
            )
        
        # Validate 'extension'
        extension = config.get("extension")
        if not isinstance(extension, str):
            error_msg = "'extension' must be a string"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "extension"}
            )
        
        if extension.lower() not in self.VALID_EXTENSIONS:
            warning_msg = f"Uncommon extension '{extension}' (expected one of {self.VALID_EXTENSIONS})"
            self.warnings.append(f"Table '{table_name}': {warning_msg}")
            self.logger.warning(f"    ⚠️  {warning_msg}")
        
        # Validate 'sheet_name'
        sheet_name = config.get("sheet_name")
        if not isinstance(sheet_name, str) or not sheet_name.strip():
            error_msg = "'sheet_name' must be a non-empty string"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "sheet_name"}
            )
        
        # Validate 'required_fields'
        required_fields = config.get("required_fields")
        if not isinstance(required_fields, list):
            error_msg = "'required_fields' must be an array"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
                error_message=error_msg,
                metadata={"table": table_name, "field": "required_fields"}
            )
        
        if not required_fields:
            warning_msg = "'required_fields' is empty"
            self.warnings.append(f"Table '{table_name}': {warning_msg}")
            self.logger.warning(f"    ⚠️  {warning_msg}")
        
        # Check if all required_fields are in dtypes
        dtypes_fields = set(config.get("dtypes", {}).keys())
        required_fields_set = {self.normalize_field_name(f) for f in required_fields}
        # Handle with special cases (miss-spelling)

        missing_in_dtypes = required_fields_set - dtypes_fields
        if missing_in_dtypes:
            error_msg = f"Fields in 'required_fields' missing from 'dtypes': {sorted(missing_in_dtypes)}"
            self.logger.error(f"    ❌ {error_msg}")
            return DataProcessingReport(
                status=ProcessingStatus.ERROR,
                data=None,
                error_type=ErrorType.SCHEMA_MISMATCH,
                error_message=error_msg,
                metadata={
                    "table": table_name,
                    "missing_in_dtypes": sorted(missing_in_dtypes),
                    "required_fields": sorted(required_fields),
                    "dtypes_fields": sorted(dtypes_fields)
                }
            )
        
        # Check for duplicates in required_fields
        if len(required_fields) != len(required_fields_set):
            duplicates = [f for f in required_fields if required_fields.count(f) > 1]
            warning_msg = f"Duplicate fields in 'required_fields': {list(set(duplicates))}"
            self.warnings.append(f"Table '{table_name}': {warning_msg}")
            self.logger.warning(f"    ⚠️  {warning_msg}")
        
        self.logger.info(f"    ✅ Dynamic-specific fields are valid")
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data=None,
            metadata={"table": table_name}
        )
    
    def normalize_field_name(self, field: str) -> str:
        fixes = {
            "plasticResine": "plasticResin",
            "plasticResineCode": "plasticResinCode",
            "plasticResineLot": "plasticResinLot"}
        return fixes.get(field, field)