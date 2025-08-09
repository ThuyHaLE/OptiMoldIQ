# DataCollector Documentation

## Overview

The `DataCollector` is a critical component of the data pipeline orchestrator system responsible for collecting, processing, and converting data from various Excel sources into standardized Parquet format. It handles two primary data types: product records from monthly reports and purchase orders, with comprehensive error handling and recovery mechanisms.

---

## Key Features

- **Multi-format Excel Support**: Handles both `.xlsx` and `.xlsb` file formats
- **Atomic File Operations**: Uses temporary files and atomic moves to prevent data corruption
- **Duplicate Detection**: Automatically removes duplicate records during processing
- **Data Validation**: Validates required fields and data types according to predefined schemas
- **Error Recovery**: Implements local healing mechanisms with backup rollback capabilities
- **Change Detection**: Only updates files when actual data changes are detected
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

---

## Architecture

### Directory Structure

```
database/dynamicDatabase/          # Source directory
├── monthlyReports_history/        # Product records source
│   └── monthlyReports_YYYYMM.xlsb
└── purchaseOrders_history/        # Purchase orders source
    └── purchaseOrder_YYYYMM.xlsx

agents/shared_db/dynamicDatabase/  # Output directory
├── productRecords.parquet         # Processed product records
└── purchaseOrders.parquet         # Processed purchase orders
```

---

## Data Processing Flow

### 1. Initialization
- Sets up source and output directories
- Creates output directories if they don't exist
- Loads agent configuration for error handling

### 2. Main Processing (`process_all_data`)
- Processes product records from monthly reports
- Processes purchase orders from purchase order files
- Determines overall status based on individual results
- Returns comprehensive execution information

### 3. Data Type Processing (`_process_data_type`)
- Validates source folder existence
- Loads existing data for comparison
- Processes each file individually
- Handles partial failures gracefully
- Applies local healing mechanisms when errors occur

### 4. File Processing (`_process_single_file`)
- Reads Excel files using appropriate engines
- Validates required fields presence
- Filters columns to include only required fields
- Returns structured processing results

### 5. Data Merging (`_merge_and_process_data`)
- Concatenates multiple dataframes
- Removes duplicate records
- Applies data type conversions and cleaning
- Performs change detection against existing data
- Saves to Parquet format only if changes detected

---

## Data Schemas

### Product Records Schema
```python
required_fields = [
    'recordDate', 'workingShift', 'machineNo', 'machineCode', 
    'itemCode', 'itemName', 'colorChanged', 'moldChanged', 
    'machineChanged', 'poNote', 'moldNo', 'moldShot', 
    'moldCavity', 'itemTotalQuantity', 'itemGoodQuantity',
    'itemBlackSpot', 'itemOilDeposit', 'itemScratch', 
    'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst',
    'itemBend', 'itemStain', 'otherNG', 'plasticResine',
    'plasticResineCode', 'plasticResineLot', 'colorMasterbatch',
    'colorMasterbatchCode', 'additiveMasterbatch', 
    'additiveMasterbatchCode'
]
```

### Purchase Orders Schema
```python
required_fields = [
    'poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName',
    'itemQuantity', 'plasticResinCode', 'plasticResin',
    'plasticResinQuantity', 'colorMasterbatchCode', 
    'colorMasterbatch', 'colorMasterbatchQuantity',
    'additiveMasterbatchCode', 'additiveMasterbatch',
    'additiveMasterbatchQuantity'
]
```

---

## Error Handling and Recovery

### Error Types
- `FILE_NOT_FOUND`: Source folder or files don't exist
- `UNSUPPORTED_DATA_TYPE`: Unknown data type processing request
- `FILE_READ_ERROR`: Cannot read Excel files
- `MISSING_FIELDS`: Required columns missing from source data
- `DATA_PROCESSING_ERROR`: General processing failures
- `PARQUET_SAVE_ERROR`: Cannot save output files

### Recovery Mechanisms
The agent implements local healing through the `check_local_backup_and_update_status` function:

1. **Backup Validation**: Checks for existence of backup Parquet files
2. **Status Updates**: Updates recovery action statuses based on backup availability
3. **Rollback Capability**: Can restore from backup when local recovery is possible

### Recovery Actions
- `ROLLBACK_TO_BACKUP`: Restore from previously saved backup files
- `RETRY_PROCESSING`: Attempt processing again
- Various other actions based on error type and configuration

---

## Processing Statuses

- `SUCCESS`: All operations completed successfully
- `PARTIAL_SUCCESS`: Some files processed successfully, others failed
- `WARNING`: Processing completed with warnings
- `ERROR`: Critical failures preventing processing
- `PENDING`: Recovery actions awaiting execution

---

## Output Format

### Execution Information Structure
```python
{
    "agent_id": "DATA_COLLECTOR",
    "status": "SUCCESS|PARTIAL_SUCCESS|WARNING|ERROR",
    "summary": {
        "total_datasets": 2,
        "successful": 2,
        "failed": 0,
        "warnings": 0
    },
    "details": [
        {
            "data_type": "productRecords|purchaseOrders",
            "status": "...",
            "files_processed": 10,
            "files_successful": 10,
            "files_failed": 0,
            "records_processed": 5000,
            "output_file": "/path/to/output.parquet",
            "file_size_mb": 2.5,
            "data_updated": true,
            "warnings": ["Removed 5 duplicate rows"]
        }
    ],
    "healing_actions": ["RETRY_PROCESSING"],
    "trigger_agents": ["DATA_LOADER"],
    "metadata": {
        "processing_duration": null,
        "disk_usage": {
            "output_directory_mb": 10.5,
            "available_space_mb": 1024.0
        }
    }
}
```

---

## Data Processing Rules

### Data Type Conversions
- **Product Records**: Excel serial dates converted to datetime objects
- **Purchase Orders**: Date columns converted using pandas datetime parsing
- **Material Codes**: Numeric codes safely converted to strings
- **String Columns**: Object types converted to pandas string dtype
- **Numeric Columns**: Appropriate nullable integer/float types assigned

### Data Cleaning
- Null-like string values (`"nan"`, `"null"`, `"none"`, `""`, `"n/a"`) replaced with pandas NA
- Working shift values normalized to uppercase
- Column name standardization for consistency
- Duplicate row removal across all processed files

---

## Performance Optimizations

### Fast DataFrame Comparison
Uses MD5 hash-based comparison for detecting data changes instead of element-wise comparison for better performance on large datasets.

### Atomic File Operations
- Saves to temporary files first
- Uses atomic move operations to prevent corruption
- Automatic cleanup of temporary files on errors

### Memory Efficient Processing
- Processes files individually before merging
- Filters columns early to reduce memory footprint
- Uses efficient Parquet compression (Snappy)

---

## Usage Example

```python
# Initialize the DataCollector
collector = DataCollector(
    source_dir = "database/dynamicDatabase",
    default_dir = "agents/shared_db"
)

# Process all data types
execution_info = collector.process_all_data()

# Check results
if execution_info['status'] == 'SUCCESS':
    print("All data processed successfully")
elif execution_info['status'] == 'PARTIAL_SUCCESS':
    print("Some files failed to process")
    print(f"Failed files: {execution_info['details'][0]['failed_files']}")
else:
    print(f"Processing failed: {execution_info['summary']}")
```

---

## Monitoring and Maintenance

### Key Metrics to Monitor
- Processing success rates
- File processing times
- Disk usage in output directory
- Duplicate detection rates
- Recovery action success rates

### Maintenance Tasks
- Regular backup validation
- Log file rotation and cleanup
- Monitoring of source directory growth
- Performance optimization based on processing volumes

### Troubleshooting Common Issues

1. **Files Not Found**: Check source directory permissions and file naming conventions
2. **Missing Fields**: Verify Excel file structure matches expected schema
3. **Memory Issues**: Consider processing files in smaller batches for very large datasets
4. **Parquet Save Errors**: Check disk space and directory permissions
5. **Recovery Failures**: Ensure backup files exist and are accessible

---

## Integration Points

### Upstream Dependencies
- Excel file generation processes that create source files
- File system monitoring for new data availability

### Downstream Dependencies
- Data loading agents that consume the Parquet files
- Analytics systems that depend on processed data
- Notification systems for error reporting