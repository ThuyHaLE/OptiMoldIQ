# DataLoader Documentation

## Overview

The `DataLoader` is a comprehensive data management component responsible for loading, processing, and managing database files within a data pipeline orchestration system. It handles both static and dynamic databases, provides change detection capabilities, and includes robust error handling with recovery mechanisms.

## Key Features

- **Multi-Database Support**: Handles both static (Excel) and dynamic (Parquet) database formats
- **Change Detection**: Efficiently compares current and existing data to identify updates
- **Error Recovery**: Comprehensive error handling with configurable recovery actions
- **File Versioning**: Automatic versioning system for changed files
- **Performance Monitoring**: Memory and disk usage tracking
- **Healing System**: Self-recovery mechanisms with status reporting

## Architecture

### Core Components

1. **DataLoaderAgent**: Main class handling database operations
2. **Healing System**: Error recovery and status management
3. **File Management**: Versioning and storage operations
4. **Comparison Engine**: Fast dataframe comparison using hash-based methods

## Class Reference

### DataLoaderAgent

The main agent class that orchestrates all data loading operations.

#### Constructor

```python
DataLoaderAgent(
    databaseSchemas_path: str = "database/databaseSchemas.json",
    annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
    default_dir: str = "agents/shared_db"
)
```

**Parameters:**
- `databaseSchemas_path`: Path to database schema configuration file
- `annotation_path`: Path to file storing database path annotations
- `default_dir`: Default directory for shared database files

#### Main Methods

##### `process_all_data() -> Dict[str, Any]`

Main processing method that handles all databases and returns structured response.

**Returns:**
- Dictionary containing execution information including status, results, and metadata

**Key Features:**
- Processes all configured databases
- Detects data changes
- Saves modified files with versioning
- Provides comprehensive status reporting

##### `_process_database(db_name: str, db_type: str) -> Dict[str, Any]`

Processes a single database with comprehensive error handling.

**Parameters:**
- `db_name`: Name of the database to process
- `db_type`: Type of database (static or dynamic)

**Returns:**
- Dictionary containing processing results and status information

#### Database Loading Methods

##### `_load_dynamic_db(db_name: str, db_type: str) -> Dict[str, Any]`

Loads dynamic database files in Parquet format.

**Features:**
- File existence validation
- Parquet file reading
- Error handling with recovery actions

##### `_load_static_db(db_name: str, db_type: str) -> Dict[str, Any]`

Loads and processes static database files in Excel format.

**Features:**
- Excel file processing
- Data type conversion
- Schema validation

##### `_load_existing_df(file_path: str) -> Dict[str, Any]`

Loads existing dataframe from file for comparison purposes.

**Parameters:**
- `file_path`: Path to the existing dataframe file

#### Comparison and Change Detection

##### `_compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]`

Compares two dataframes to detect changes using fast hash-based comparison.

**Parameters:**
- `df1`: First dataframe (current data)
- `df2`: Second dataframe (existing data)

##### `_dataframes_equal_fast(df1, df2) -> bool`

Static method for fast dataframe comparison using MD5 hashing.

**Features:**
- Quick shape comparison
- Hash-based comparison for performance
- Fallback to regular comparison if hashing fails

#### File Management

##### `_save_changed_files() -> Dict[str, Any]`

Saves files that have changed with versioning support.

**Features:**
- Change detection validation
- Versioning system integration
- Comprehensive error handling

##### `save_output_with_versioning(data, path_annotation, output_dir, file_format='parquet')`

Static method for saving dataframes with versioning support and file management.

**Parameters:**
- `data`: Dictionary mapping database names to dataframes
- `path_annotation`: Dictionary tracking file paths
- `output_dir`: Output directory path
- `file_format`: File format for saving (default: parquet)

**Features:**
- Automatic timestamp generation
- Historical file archiving
- Change log maintenance
- Path annotation updates

## Data Processing

### Static Database Processing

The `_process_data()` static method handles Excel file processing with:

#### Data Cleaning Features

1. **Null Value Detection**: Identifies and cleans null-like string values
2. **Type Conversion**: Safe conversion of numeric values to strings for specific fields
3. **Schema Application**: Applies configured data types from schema

#### Special Cases Handling

- `plasticResinCode`
- `colorMasterbatchCode` 
- `additiveMasterbatchCode`

These fields receive special string conversion treatment using the `safe_convert()` function.

## Error Handling and Recovery

### Error Types

The system handles various error types:

- `FILE_NOT_FOUND`: Missing database files
- `FILE_READ_ERROR`: File reading failures
- `DATA_CORRUPTION`: Data integrity issues
- `SCHEMA_MISMATCH`: Schema validation failures
- `HASH_COMPARISON_ERROR`: Comparison operation failures
- `PARQUET_SAVE_ERROR`: File saving failures

### Processing Status Types

- `SUCCESS`: Operation completed successfully
- `ERROR`: Critical failure occurred
- `WARNING`: Non-critical issues detected
- `PARTIAL_SUCCESS`: Partial completion with some issues

### Recovery Actions

The system supports various recovery actions:

- `RETRY_PROCESSING`: Retry failed operations
- `ROLLBACK_TO_BACKUP`: Restore from backup files
- `TRIGGER_MANUAL_REVIEW`: Request human intervention

### Healing System Integration

The agent integrates with a healing system that:

1. **Checks Annotation Paths**: Validates backup file availability
2. **Updates Recovery Status**: Modifies recovery actions based on system state
3. **Triggers Downstream Agents**: Notifies other system components

## Configuration

### Database Schema Configuration

The agent expects a JSON configuration file with the following structure:

```json
{
  "staticDB": {
    "database_name": {
      "path": "/path/to/database.xlsx",
      "dtypes": {
        "column1": "string",
        "column2": "int64"
      }
    }
  },
  "dynamicDB": {
    "database_name": {
      "path": "/path/to/database.parquet"
    }
  }
}
```

### Path Annotations

The system maintains a JSON file tracking current file paths:

```json
{
  "database_name": "/path/to/current/file.parquet"
}
```

## File Structure

```
agents/shared_db/DataLoaderAgent/
├── newest/
│   ├── path_annotations.json
│   └── YYYYMMDD_HHMM_database_name.parquet
├── historical_db/
│   └── [archived files]
└── change_log.txt
```

## Usage Example

```python
# Initialize the agent
agent = DataLoaderAgent(
    databaseSchemas_path="config/schemas.json",
    annotation_path="db/annotations.json",
    default_dir="shared_db"
)

# Process all databases
result = agent.process_all_data()

# Check results
if result['status'] == 'SUCCESS':
    print(f"Processed {result['summary']['total_databases']} databases")
    print(f"Changed files: {result['summary']['changed_files']}")
else:
    print(f"Processing failed: {result['status']}")
    print(f"Healing actions: {result['healing_actions']}")
```

## Monitoring and Metrics

The agent provides comprehensive monitoring information:

### Summary Metrics
- Total databases processed
- Successful/failed operations
- Warning count
- Changed files count
- Files saved count

### Performance Metrics
- Processing duration
- Memory usage (MB and percentage)
- Disk usage (output directory size and available space)

### Healing Information
- Recovery actions taken
- Triggered downstream agents
- Error details and types

## Best Practices

1. **Regular Backup Maintenance**: Ensure backup files are available for recovery operations
2. **Schema Validation**: Keep database schemas up-to-date in configuration
3. **Monitoring**: Regularly check processing logs and status reports
4. **Error Response**: Address healing actions promptly to maintain system health
5. **Storage Management**: Monitor disk usage to prevent storage issues

## Dependencies

- `pandas`: Data manipulation and analysis
- `loguru`: Logging functionality
- `pathlib`: Path operations
- `hashlib`: Hash-based comparisons
- `psutil`: System monitoring (optional)
- `pyarrow`: Parquet file operations

## Error Scenarios and Troubleshooting

### Common Issues

1. **File Not Found**: Check file paths in schema configuration
2. **Permission Denied**: Verify file system permissions
3. **Memory Issues**: Monitor large file processing
4. **Schema Mismatches**: Validate data types in configuration
5. **Disk Space**: Ensure adequate storage for versioning

### Recovery Procedures

1. **Check Logs**: Review error messages and recovery actions
2. **Validate Paths**: Ensure all file paths are accessible
3. **Backup Restoration**: Use healing system for automatic recovery
4. **Manual Intervention**: Address complex issues requiring human review