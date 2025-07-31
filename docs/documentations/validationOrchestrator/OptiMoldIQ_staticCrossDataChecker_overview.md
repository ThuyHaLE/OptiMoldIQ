# StaticCrossDataChecker Agent Documentation

## Overview

The `StaticCrossDataChecker` is a specialized data validation agent designed to cross-reference and validate data consistency between dynamic operational data (production records and purchase orders) and static reference data (item information, resin specifications, and composition summaries).

This agent ensures data integrity by validating that all item codes, resin specifications, and material compositions referenced in operational data exist and match exactly in the corresponding reference tables.

## Purpose and Scope

### Primary Functions
- **Item Information Validation**: Ensures itemCode and itemName combinations exist in the itemInfo reference table
- **Resin Information Validation**: Validates resin codes and names across three categories (plastic resin, color masterbatch, additive masterbatch)
- **Composition Validation**: Verifies complete item composition matches against the itemCompositionSummary reference table

### Data Sources
- **Dynamic Data**: `productRecords`, `purchaseOrders`
- **Static Reference Data**: `itemInfo`, `resinInfo`, `itemCompositionSummary`

## Architecture and Design

### Class Structure
```python
@validate_init_dataframes(lambda self: {
    "productRecords_df": [...],
    "purchaseOrders_df": [...],
    "itemInfo_df": [...],
    "resinInfo_df": [...],
    "itemCompositionSummary_df": [...]
})
class StaticCrossDataChecker
```

### Key Components
1. **Initialization and Configuration**
2. **Data Loading and Validation**
3. **Cross-Reference Validation Engine**
4. **Warning Generation and Reporting**
5. **Output Management**

## Configuration Parameters

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `checking_df_name` | List[str] | Required | List of dataframes to validate ("productRecords", "purchaseOrders") |
| `source_path` | str | 'agents/shared_db/DataLoaderAgent/newest' | Path to data files directory |
| `annotation_name` | str | "path_annotations.json" | JSON file containing path annotations |
| `databaseSchemas_path` | str | 'database/databaseSchemas.json' | Database schema definition file path |
| `default_dir` | str | "agents/shared_db" | Default output directory |

### Example Initialization
```python
checker = StaticCrossDataChecker(
    checking_df_name=["productRecords", "purchaseOrders"],
    source_path="agents/shared_db/DataLoaderAgent/newest",
    annotation_name="path_annotations.json"
)
```

## Data Schema Requirements

### Required DataFrames

#### Dynamic Data
- **productRecords_df**: Production records with item and resin information
- **purchaseOrders_df**: Purchase order data with material specifications

#### Static Reference Data
- **itemInfo_df**: Master item information (itemCode, itemName)
- **resinInfo_df**: Resin specifications (resinCode, resinName)
- **itemCompositionSummary_df**: Complete item compositions

### Key Fields

#### Item Information Fields
- `itemCode`: Unique item identifier
- `itemName`: Item description/name

#### Resin Information Fields
- `plasticResinCode`, `plasticResin`: Primary plastic material
- `colorMasterbatchCode`, `colorMasterbatch`: Color additives
- `additiveMasterbatchCode`, `additiveMasterbatch`: Performance additives

#### Context Fields (productRecords)
- `poNo`: Purchase order number
- `recordDate`: Production date
- `workingShift`: Production shift
- `machineNo`: Machine identifier

#### Context Fields (purchaseOrders)
- `poNo`: Purchase order number

## Validation Logic

### 1. Item Information Validation

**Purpose**: Ensures all itemCode + itemName combinations exist in the itemInfo reference table.

**Process**:
1. Extract unique itemCode/itemName pairs from checking data
2. Remove records with missing item information
3. Perform left join with itemInfo reference table
4. Identify mismatches where combinations don't exist in reference data

**Warning Type**: `item_info_warnings`

### 2. Resin Information Validation

**Purpose**: Validates three types of resin information against the resinInfo reference table.

**Resin Categories**:
- Plastic Resin (primary material)
- Color Masterbatch (coloring agents)
- Additive Masterbatch (performance enhancers)

**Process**:
1. For each resin category, extract code/name pairs
2. Normalize field names to resinCode/resinName
3. Cross-reference with resinInfo table
4. Generate warnings for non-matching combinations

**Warning Type**: `resin_info_warnings`

### 3. Composition Validation

**Purpose**: Validates complete item compositions against the itemCompositionSummary reference table.

**Composition Fields**:
- Item information (code, name)
- All resin specifications (plastic, color, additive)

**Process**:
1. Extract complete composition records
2. Perform exact match validation against itemCompositionSummary
3. Identify compositions that don't exist in reference data

**Warning Type**: `composition_warnings`

## Warning Structure

All warnings follow a standardized format compatible with the PORequiredCriticalValidator pattern:

```python
{
    'poNo': str,                    # Purchase order number
    'warningType': str,             # Category of warning
    'mismatchType': str,            # Specific mismatch type
    'requiredAction': str,          # Recommended corrective action
    'message': str                  # Detailed warning message
}
```

### Warning Types

| Warning Type | Mismatch Type | Description |
|--------------|---------------|-------------|
| `item_info_warnings` | `item_code_and_name_not_matched` | ItemCode/itemName combination not found |
| `resin_info_warnings` | `resin_code_and_name_not_matched` | ResinCode/resinName combination not found |
| `composition_warnings` | `item_composition_not_matched` | Complete composition not found |

### Required Actions

| Action Pattern | Description |
|----------------|-------------|
| `update_itemInfo_or_double_check_{df_name}` | Update reference data or verify source data |
| `update_resinInfo_or_double_check_{df_name}` | Update resin reference or verify source data |
| `update_itemCompositionSummary_or_double_check_{df_name}` | Update composition reference or verify source data |

## Usage Examples

### Basic Validation
```python
# Initialize checker for both data types
checker = StaticCrossDataChecker(
    checking_df_name=["productRecords", "purchaseOrders"]
)

# Run validations and get results
results = checker.run_validations()

# Access results for each dataframe
product_warnings = results["productRecords"]
purchase_warnings = results["purchaseOrders"]
```

### Validation with Output
```python
# Run validations and save to Excel
checker = StaticCrossDataChecker(
    checking_df_name=["productRecords"],
    default_dir="output/validation_results"
)

# This will create versioned Excel output
checker.run_validations_and_save_results()
```

### Single Dataframe Validation
```python
# Validate only purchase orders
checker = StaticCrossDataChecker(
    checking_df_name=["purchaseOrders"]
)

results = checker.run_validations()
```

## Output Format

### Console Output
```
INFO: Starting static cross data validation...
INFO: Processing validations for: productRecords
INFO: Processed productRecords: removed null poNote, 1500 rows remaining
INFO: Summary for productRecords: Total warnings: 25 (Item: 10, Resin: 8, Composition: 7)
```

### Excel Output
The agent generates versioned Excel files with separate sheets for each validated dataframe:

**File Structure**:
- Filename: `static_cross_checker_v{version}.xlsx`
- Sheets: One per validated dataframe
- Columns: poNo, warningType, mismatchType, requiredAction, message

## Error Handling

### Validation Errors
- **Invalid dataframe names**: Only "productRecords" and "purchaseOrders" are allowed
- **Missing files**: All required parquet files must exist
- **Schema validation**: DataFrames must match expected schema (via decorator)

### Data Processing Errors
- **Missing reference data**: Empty reference tables will cause validation failures
- **Data type mismatches**: Automatic handling of null values and type conversion
- **Memory constraints**: Large datasets are processed efficiently using pandas operations

## Performance Considerations

### Optimization Features
- **Efficient joins**: Uses pandas merge operations for fast cross-referencing
- **Memory management**: Processes data in chunks where applicable
- **Duplicate handling**: Removes duplicate reference entries for faster lookups

### Scalability
- Designed to handle production-scale datasets
- Memory-efficient processing of large parquet files
- Optimized for typical manufacturing data volumes

## Dependencies

### Required Libraries
```python
import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List
import os
```

### Custom Modules
```python
from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path, save_output_with_versioning
```

## Integration Guidelines

### Pre-requisites
1. All required parquet files must be available
2. Database schema configuration must be properly defined
3. Path annotations must be correctly configured

### Integration Steps
1. **Setup**: Ensure all data files and configurations are in place
2. **Initialize**: Create StaticCrossDataChecker instance with appropriate parameters
3. **Execute**: Run validations using `run_validations()` or `run_validations_and_save_results()`
4. **Process Results**: Handle warnings and take corrective actions as needed

### Best Practices
- Run validation after data loading/updating operations
- Review and address warnings promptly to maintain data quality
- Regular validation of reference data completeness
- Monitor validation results for data quality trends

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| FileNotFoundError | Missing parquet files | Verify file paths and data loading |
| ValueError (invalid df names) | Wrong checking_df_name | Use only "productRecords" or "purchaseOrders" |
| Schema validation errors | Incorrect DataFrame structure | Check DataFrame columns match expected schema |
| Empty results | No mismatches found | Normal behavior - indicates good data quality |

### Debugging Tips
- Enable debug logging to see detailed processing information
- Check path annotations for correct file locations
- Verify reference data completeness before running validations
- Monitor memory usage for large datasets

## Maintenance and Updates

### Regular Maintenance
- Update reference data as new items/resins are introduced
- Monitor validation results for patterns indicating systemic issues
- Review and update required actions based on operational changes

### Version Control
- Track changes to validation logic
- Maintain compatibility with existing data schemas
- Document any breaking changes in validation behavior