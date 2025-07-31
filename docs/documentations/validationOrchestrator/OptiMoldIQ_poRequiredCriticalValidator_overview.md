# PORequiredCriticalValidator Documentation

## Overview

The `PORequiredCriticalValidator` is a data validation agent designed to ensure consistency between product records and purchase orders in a manufacturing or inventory management system. This validator performs critical checks to identify discrepancies that could indicate data quality issues or process violations.

## Purpose

This validator addresses the following business requirements:
- **Data Integrity**: Ensures that all product records reference valid purchase orders
- **Process Compliance**: Validates that production activities align with authorized purchase orders
- **Quality Assurance**: Identifies mismatches between product specifications and purchase order requirements
- **Risk Management**: Flags potential issues that could impact production or inventory accuracy

## Key Features

### 1. Schema Validation
- Automatically validates DataFrame schemas against predefined database schemas
- Ensures data consistency and structure compliance
- Prevents processing of malformed data

### 2. Data Cross-Referencing
- Validates that product records reference existing purchase orders
- Identifies orphaned product records with invalid PO numbers
- Ensures referential integrity between related datasets

### 3. Field-Level Validation
- Compares overlapping fields between product records and purchase orders
- Detects discrepancies in critical data fields
- Provides detailed mismatch information for troubleshooting

### 4. Comprehensive Reporting
- Generates structured warning reports with actionable insights
- Categorizes validation issues by type and severity
- Exports results to Excel format for further analysis

## Class Architecture

### Initialization Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Directory containing data file annotations |
| `annotation_name` | str | `"path_annotations.json"` | JSON file with data file paths |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Database schema configuration file |
| `default_dir` | str | `"agents/shared_db"` | Default output directory |

### Core Components

#### Data Loading
- **Product Records**: Manufacturing or production data with PO references
- **Purchase Orders**: Authorized purchase order information
- **Schema Validation**: Automatic validation against predefined schemas

#### Validation Logic
- **Null Filtering**: Removes invalid records with missing PO numbers
- **Cross-Reference Check**: Validates PO existence across datasets
- **Field Comparison**: Performs vectorized field-level validation
- **Mismatch Detection**: Identifies and categorizes data discrepancies

## Validation Types

### 1. Invalid PO Numbers
**Issue**: Product records reference non-existent purchase orders
- **Warning Type**: `PO_invalid`
- **Action**: Stop processing or verify product records
- **Impact**: High - indicates potential data corruption or process violation

### 2. Field Mismatches
**Issue**: Product record data doesn't match corresponding purchase order data
- **Warning Type**: `product_info_not_matched`
- **Action**: Stop processing or double-check product records
- **Impact**: Medium to High - could indicate specification errors or data entry mistakes

## Usage Examples

### Basic Usage
```python
from agents.PORequiredCriticalValidator import PORequiredCriticalValidator

# Initialize validator with default settings
validator = PORequiredCriticalValidator()

# Run validation and save results
validator.run_validations_and_save_results()
```

### Custom Configuration
```python
# Initialize with custom paths
validator = PORequiredCriticalValidator(
    source_path='custom/data/path',
    annotation_name='custom_annotations.json',
    databaseSchemas_path='custom/schemas.json'
)

# Run validation only (without saving)
warnings_df = validator.run_validations()
print(f"Found {len(warnings_df)} validation issues")
```

## Output Format

### Warning Structure
Each validation warning contains the following fields:

| Field | Description |
|-------|-------------|
| `poNo` | Purchase Order Number |
| `warningType` | Category of validation issue |
| `mismatchType` | Detailed description of the mismatch |
| `requiredAction` | Recommended corrective action |
| `message` | Human-readable warning message with context |

### Example Warning Messages
```
(PO12345, 2024-01-15, Morning, Machine01) - Mismatch: quantity: 100 vs 150, unitPrice: 25.0 vs 30.0. Please stop progressing or double check productRecords

(PO99999, 2024-01-16, Evening, Machine03) - Mismatch: PO99999 does not exist in purchaseOrders. Please stop progressing or double check productRecords
```

## File Outputs

### Excel Report
- **Location**: `{default_dir}/PORequiredCriticalValidator/`
- **Naming**: `po_required_critical_validator_v{version}.xlsx`
- **Content**: Detailed validation warnings with full context
- **Versioning**: Automatic version increment to prevent overwrites

## Error Handling

### File Not Found
- Validates existence of required data files during initialization
- Raises `FileNotFoundError` with descriptive messages
- Logs detailed error information for troubleshooting

### Data Quality Issues
- Gracefully handles null values and missing data
- Provides comprehensive logging for debugging
- Continues processing when possible, documenting issues

## Performance Considerations

### Optimization Features
- **Vectorized Operations**: Uses pandas vectorized operations for efficient field comparisons
- **Memory Management**: Processes data in chunks when dealing with large datasets
- **Selective Loading**: Only loads necessary columns for validation

### Scalability
- Designed to handle enterprise-scale datasets
- Efficient memory usage through strategic DataFrame filtering
- Optimized merge operations for large data volumes

## Integration Guidelines

### Prerequisites
- Python 3.7+
- Required packages: pandas, loguru, pathlib
- Access to structured data files (Parquet format)
- Valid database schema configuration

### Deployment Considerations
- Ensure proper file permissions for data access
- Configure logging levels appropriately for production
- Set up monitoring for validation failure alerts
- Implement error notification systems for critical issues

## Troubleshooting

### Common Issues

#### Schema Mismatch
**Symptom**: Validation fails during initialization
**Solution**: Verify database schema configuration matches actual data structure

#### Missing Data Files
**Symptom**: FileNotFoundError during initialization
**Solution**: Check path annotations and ensure all referenced files exist

#### Performance Issues
**Symptom**: Slow validation processing
**Solution**: Consider data preprocessing or chunked processing for large datasets

### Logging and Debugging
- Enable debug logging: `logger.enable("agents.PORequiredCriticalValidator")`
- Monitor log messages for data quality insights
- Use shape and column information for data structure validation

## Best Practices

### Data Management
- Maintain consistent data schemas across environments
- Implement regular data quality checks
- Keep purchase order data synchronized and up-to-date

### Validation Workflow
- Run validations before critical production processes
- Implement automated validation in CI/CD pipelines
- Set up alerts for validation failures

### Result Analysis
- Review validation reports regularly
- Track validation trends over time
- Use validation results to improve data quality processes