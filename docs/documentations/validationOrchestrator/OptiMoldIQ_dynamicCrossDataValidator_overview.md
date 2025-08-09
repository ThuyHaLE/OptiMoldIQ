# DynamicCrossDataValidator Documentation

## Overview

The `DynamicCrossDataValidator` is designed to cross-reference production records against standard reference data in manufacturing environments. It ensures data integrity by validating that production records (items, molds, machines, compositions) match against predefined standards and generates detailed warnings for any mismatches.

---

## Purpose

This agent addresses critical data quality challenges in manufacturing by:
- Validating production records against multiple reference databases
- Identifying inconsistencies between actual production and standard specifications
- Generating actionable warnings for data quality issues
- Providing comprehensive audit trails for compliance and quality control

---

## Key Features

### 🔍 Multi-Level Validation
- **Item Validation**: Ensures items exist in reference data
- **Mold Validation**: Verifies item-mold compatibility
- **Machine Validation**: Checks mold-machine tonnage requirements
- **Composition Validation**: Validates item composition specifications
- **Full Record Validation**: Comprehensive validation of complete production records

### 📊 Data Integration
- Processes multiple data sources (production records, machine info, mold specifications, item compositions)
- Handles complex data relationships and dependencies
- Manages null values and incomplete data gracefully

### ⚠️ Warning System
- Generates categorized warnings for different mismatch types
- Provides actionable recommendations for resolving issues
- Creates detailed audit trails with context information

### 📈 Export Capabilities
- Exports validation results to Excel files with versioning
- Structured output for easy analysis and reporting
- Maintains data lineage and validation history

---

## Architecture

### Data Flow Pipeline

```
Production Records → Data Preparation → Cross-Reference Validation → Warning Generation → Export Results
                ↗                   ↗
Reference Data ────┘                │
(Machines, Molds, Compositions) ────┘
```

### Core Components

1. **Data Loader**: Loads and validates input DataFrames
2. **Data Processor**: Prepares and transforms data for validation
3. **Validation Engine**: Performs cross-reference checks
4. **Warning Generator**: Creates structured warning messages
5. **Export Manager**: Saves results with versioning

---

## Data Sources

### Required Input Data

| Data Source | Purpose | Key Columns |
|-------------|---------|-------------|
| `productRecords_df` | Production records to validate | recordDate, workingShift, poNote, itemCode, itemName, machineNo, moldNo |
| `machineInfo_df` | Machine specifications | machineCode, machineTonnage |
| `moldSpecificationSummary_df` | Mold-item compatibility | itemCode, itemName, moldList |
| `moldInfo_df` | Mold specifications | moldNo, moldName, machineTonnage |
| `itemCompositionSummary_df` | Item material compositions | itemCode, itemName, plasticResin, colorMasterbatch, additiveMasterbatch |

### Data Requirements

- All DataFrames must follow the schema defined in `databaseSchemas.json`
- Production records must have valid PO notes (`poNote` not null)
- Machine tonnage data must be properly formatted (e.g., "100T", "200T")
- Mold lists can contain multiple molds separated by "/" (e.g., "MOLD1/MOLD2/MOLD3")

---

## Usage

### Basic Usage

```python
from agents.dynamic_cross_validator import DynamicCrossDataValidator

# Initialize the validator
validator = DynamicCrossDataValidator(
    source_path='agents/shared_db/DataLoaderAgent/newest',
    annotation_name="path_annotations.json",
    databaseSchemas_path='database/databaseSchemas.json',
    default_dir="agents/shared_db"
)

# Run validation and save results
validator.run_validations_and_save_results()
```

### Advanced Usage

```python
# Run validation only (without saving)
results = validator.run_validations()

# Access specific warning types
invalid_warnings = results['invalid_warnings']
mismatch_warnings = results['mismatch_warnings']

# Process results manually
print(f"Found {len(invalid_warnings)} invalid items")
print(f"Found {len(mismatch_warnings)} production mismatches")
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | 'agents/shared_db/DataLoaderAgent/newest' | Path to data source directory |
| `annotation_name` | str | "path_annotations.json" | JSON file with path annotations |
| `databaseSchemas_path` | str | 'database/databaseSchemas.json' | Database schema configuration |
| `default_dir` | str | "agents/shared_db" | Default output directory |

---

## Validation Logic

### 1. Data Preparation Phase

#### Production Data Processing
- Filters records with valid PO notes
- Builds standardized item composition strings
- Merges with machine information for tonnage data
- Ensures consistent data types for matching

#### Reference Data Processing
- Expands mold lists into individual records
- Merges mold specifications with machine requirements
- Groups item compositions by item
- Creates comprehensive reference dataset

### 2. Validation Phase

The validator performs hierarchical validation at multiple levels:

#### Level 1: Item Validation
- **Purpose**: Verify items exist in reference data
- **Columns**: `itemCode`, `itemName`
- **Action**: Identifies unknown or invalid items

#### Level 2: Mold Validation
- **Purpose**: Check item-mold compatibility
- **Columns**: `itemCode`, `itemName`, `moldNo`
- **Action**: Validates mold assignments to items

#### Level 3: Machine Validation
- **Purpose**: Verify mold-machine tonnage compatibility
- **Columns**: `itemCode`, `itemName`, `moldNo`, `machineTonnage`
- **Action**: Ensures proper machine selection

#### Level 4: Composition Validation
- **Purpose**: Validate item composition specifications
- **Columns**: `itemCode`, `itemName`, `item_composition`
- **Action**: Checks material composition accuracy

#### Level 5: Full Record Validation
- **Purpose**: Complete production record validation
- **Columns**: All validation columns combined
- **Action**: Comprehensive validation of entire records

### 3. Warning Generation

For each validation level, the system generates structured warnings with:
- **Context Information**: PO number, date, shift, machine details
- **Mismatch Type**: Specific type of validation failure
- **Required Action**: Recommended remediation steps
- **Human-readable Message**: Clear description of the issue

---

## Output Structure

### Warning Types

#### Invalid Item Warnings
Generated when items don't exist in reference databases:

```json
{
    "itemInfo": "ITEM001, Sample Item Name",
    "warningType": "item_invalid_in_moldSpecificationSummary",
    "mismatchType": "item_does_not_exist_in_moldSpecificationSummary",
    "requiredAction": "update_moldSpecificationSummary_or_double_check_related_databases",
    "message": "Detailed warning message with context"
}
```

#### Production Mismatch Warnings
Generated when production records don't match reference data:

```json
{
    "poNo": "PO12345",
    "warningType": "item_mold_warnings",
    "mismatchType": "item_and_mold_not_matched",
    "requiredAction": "update_moldInfo_or_double_check_productRecords",
    "message": "Detailed warning message with full context"
}
```

### Export Files

Results are exported to Excel files with automatic versioning:
- **Location**: `{default_dir}/DynamicCrossDataValidator/`
- **Naming**: `dynamic_cross_validator_v{X}.xlsx`
- **Sheets**: 
  - `invalid_warnings`: Items not found in reference data
  - `mismatch_warnings`: Production records that don't match standards

---

## Error Handling

### Data Loading Errors
- Validates file paths before loading
- Provides clear error messages for missing files
- Handles corrupted parquet files gracefully

### Validation Errors
- Manages null values and incomplete data
- Handles schema mismatches
- Provides detailed logging for troubleshooting

### Processing Errors
- Catches and logs processing exceptions
- Maintains data integrity during transformations
- Provides rollback capabilities for failed operations

---

## Best Practices

### Data Quality
- Ensure all reference databases are up-to-date
- Regularly validate schema compliance
- Monitor data completeness and consistency

### Performance Optimization
- Use appropriate chunk sizes for large datasets
- Implement data caching where appropriate
- Monitor memory usage during processing

### Maintenance
- Regularly review and update validation rules
- Monitor warning trends to identify systemic issues
- Keep database schemas synchronized

---

## Troubleshooting

### Common Issues

#### 1. Schema Validation Failures
**Problem**: DataFrame columns don't match expected schema
**Solution**: Check `databaseSchemas.json` and ensure data sources comply

#### 2. Missing Reference Data
**Problem**: High number of invalid item warnings
**Solution**: Update reference databases or verify data source accuracy

#### 3. Performance Issues
**Problem**: Slow validation processing
**Solution**: Check data volume, optimize queries, consider data partitioning

#### 4. Export Failures
**Problem**: Cannot save results to Excel
**Solution**: Verify output directory permissions and disk space

### Logging

The validator uses structured logging with different levels:
- **DEBUG**: Detailed processing information
- **INFO**: High-level operation status
- **WARNING**: Data quality issues found
- **ERROR**: Processing failures and exceptions

---

## Integration with Other Agents
- Can be integrated with data loading agents for automated workflows
- Results can feed into reporting and alerting systems
- Compatible with quality management systems

---

## Version History
- Multi-level hierarchical validation
- Comprehensive warning system
- Excel export with versioning
- Schema validation support
- Structured logging and error handling