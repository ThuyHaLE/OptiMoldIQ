# OrderProgressTracker Agent Documentation

## Overview

The **OrderProgressTracker** is a production monitoring agent designed to track and analyze manufacturing order progress in an injection molding environment. It processes production records, purchase orders, and mold specifications to generate comprehensive status reports with Excel export capabilities.

## Key Features

- **Real-time Production Status Tracking**: Monitor order completion progress and production status
- **Multi-dimensional Analysis**: Analyze production data by shift, machine, mold, and date
- **Automated Status Classification**: Categorize orders as PENDING, MOLDING, PAUSED, or MOLDED
- **ETA Compliance Monitoring**: Track delivery performance against expected dates
- **Warning Integration**: Incorporate validation warnings from other system components
- **Excel Report Generation**: Export detailed production reports with multiple worksheets

## Architecture

### Class Structure
```
OrderProgressTracker
├── Initialization & Configuration
├── Data Processing Pipeline
├── Status Analysis Engine
├── Warning Integration System
└── Report Generation Module
```

### Dependencies
- **pandas**: Data manipulation and analysis
- **loguru**: Advanced logging capabilities
- **pathlib**: File system path handling
- **agents.decorators**: Custom validation decorators
- **agents.utils**: Utility functions for data loading

### Workflow
```
                                               ┌──────────────────────────────┐
                                               │     OrderProgressTracker     │
                                               └────────────┬─────────────────┘
                                                            │
                                                            ▼
                                          ┌────────────────────────────────────────┐
                                          │         Load Datasets & Configs        │
                                          │ (purchaseOrders, productRecords, mold) │
                                          └─────────────────┬──────────────────────┘
                                                            │
                                                            ▼
                                            ┌────────────────────────────────────┐
                                            │    _extract_product_records()      │
                                            │  → Extract & group production data │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │     _pro_status_processing()       │
                                            │  → Compute proStatus & etaStatus   │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │         _get_change()              │
                                            │  → Load latest po_mismatch file    │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │  _add_warning_notes_column()       │
                                            │  → Annotate orders with warnings   │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │   save_output_with_versioning()    │
                                            │  → Save to Excel with 3 sheets     │
                                            └────────────────────────────────────┘
```
- See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_orderProgressTrackerWorkflow.md)

## Initialization

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Path to source data directory |
| `annotation_name` | str | `"path_annotations.json"` | Annotation file containing data paths |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Database schema definitions |
| `folder_path` | str | `'agents/shared_db/ValidationOrchestrator'` | Validation warnings directory |
| `target_name` | str | `"change_log.txt"` | Change log file name |
| `default_dir` | str | `"agents/shared_db"` | Default output directory |

### Required DataFrames
The agent automatically loads and validates three core datasets:

1. **productRecords_df**: Production activity records
2. **purchaseOrders_df**: Purchase order information
3. **moldSpecificationSummary_df**: Mold and product specifications

## Core Functionality

### 1. Production Status Processing

#### Status Categories
- **PENDING**: Orders waiting to start production
- **MOLDING**: Currently in production
- **PAUSED**: Production temporarily stopped
- **MOLDED**: Production completed

#### ETA Status Tracking
- **ONTIME**: Completed on or before expected delivery date
- **LATE**: Completed after expected delivery date
- **PENDING**: Not yet completed

### 2. Shift Management

The system supports multiple production shifts:

| Shift Code | Start Time | Description |
|------------|------------|-------------|
| 1 | 06:00 | Morning shift |
| 2 | 14:00 | Afternoon shift |
| 3 | 22:00 | Night shift |
| HC | 08:00 | Administrative shift |

### 3. Data Aggregation

The agent creates comprehensive aggregation maps:

- **moldShotMap**: Mold shots by mold number
- **machineQuantityMap**: Production quantities by machine
- **dayQuantityMap**: Daily production quantities
- **shiftQuantityMap**: Production quantities by shift
- **materialComponentMap**: Material component combinations

## Main Methods

### `pro_status(**kwargs)`
The primary method that orchestrates the entire production status analysis pipeline.

**Process Flow:**
1. Merge order data with mold specifications
2. Extract and aggregate production records
3. Calculate production status and remaining quantities
4. Integrate validation warnings
5. Generate and export Excel reports

**Output Data Structure:**
```python
{
    "productionStatus": DataFrame,           # Main status report
    "materialComponentMap": DataFrame,       # Material usage details
    "moldShotMap": DataFrame,               # Mold shot analysis
    "machineQuantityMap": DataFrame,        # Machine utilization
    "dayQuantityMap": DataFrame,            # Daily production breakdown
    "notWorkingStatus": DataFrame,          # Non-production records
    # Additional warning sheets if available
}
```
- See details: [Data Structure](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs\agents_output_overviews\orderProgressTracker_output_overviews.md)

## Static Methods Reference

### Data Processing Methods

#### `_extract_product_records(productRecords_df, shift_start_map)`
Processes raw production records into aggregated summaries.

**Returns:**
- `aggregated_df`: Summarized production data
- `producing_po_list`: Currently active purchase orders
- `notWorking_productRecords_df`: Non-production records

#### `_pro_status_processing(pro_status_df, pro_status_fields, producing_po_list, pro_status_dtypes)`
Processes production status and applies data type conversions.

**Key Operations:**
- Calculates remaining item quantities
- Determines production and ETA status
- Applies data type validation
- Handles datetime formatting

### Utility Methods

#### `_get_shift_start(row, shift_start_map, date_field_name, shift_field_name)`
Calculates shift start datetime from date and shift code.

#### `_create_aggregation_maps(df)`
Creates various production aggregation maps from DataFrame.

#### `_extract_material_codes(df)`
Extracts material component combinations from production records.

### Warning Integration Methods

#### `_get_change(folder_path, target_name)`
Processes validation warnings from external change logs.

#### `_add_warning_notes_column(df, warning_dict)`
Adds warning information to the production status DataFrame.

### Data Flattening Methods

#### `_pro_status_fattening(df, field_name)`
Flattens complex mapping fields into tabular format for Excel export.

**Supported Fields:**
- `moldShotMap`
- `machineQuantityMap`
- `dayQuantityMap`
- `materialComponentMap`

## Output Schema

### Production Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `poReceivedDate` | datetime | Purchase order received date |
| `poNo` | string | Purchase order number |
| `itemCode` | string | Product item code |
| `itemName` | string | Product name |
| `poETA` | datetime | Expected delivery date |
| `itemQuantity` | Int64 | Total ordered quantity |
| `itemRemain` | Int64 | Remaining quantity to produce |
| `startedDate` | datetime | Production start date |
| `actualFinishedDate` | datetime | Actual completion date |
| `proStatus` | string | Production status |
| `etaStatus` | string | ETA compliance status |
| `machineHist` | list | Production machines used |
| `moldList` | list | Molds assigned to item |
| `moldHist` | list | Molds actually used |
| `moldCavity` | list | Mold cavity counts |
| `totalMoldShot` | Int64 | Total mold shots |
| `totalDay` | Int64 | Total production days |
| `totalShift` | Int64 | Total production shifts |
| `plasticResinCode` | list | Plastic resin materials |
| `colorMasterbatchCode` | list | Color masterbatch materials |
| `additiveMasterbatchCode` | list | Additive masterbatch materials |

## Error Handling

### Validation Checks
- **Empty DataFrame Detection**: Validates input data availability
- **Schema Validation**: Ensures required columns exist
- **Data Type Enforcement**: Applies proper data types with error handling
- **Path Validation**: Checks file and directory existence

### Logging Strategy
The agent uses structured logging with different levels:
- **DEBUG**: Detailed processing information
- **INFO**: General progress updates
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures requiring attention

## Usage Example

```python
# Initialize the tracker
tracker = OrderProgressTracker(
    source_path='data/production',
    annotation_name='paths.json',
    databaseSchemas_path='schemas/db_schema.json'
)

# Generate production status report
tracker.pro_status()

# Output will be saved to: agents/shared_db/OrderProgressTracker/auto_status_YYYYMMDD_HHMMSS.xlsx
```

## Excel Output Structure

The generated Excel file contains multiple worksheets:

1. **productionStatus**: Main production status overview
2. **materialComponentMap**: Material usage breakdown
3. **moldShotMap**: Mold shot analysis by mold
4. **machineQuantityMap**: Production by machine
5. **dayQuantityMap**: Daily production summary
6. **notWorkingStatus**: Non-production records
7. **Additional Warning Sheets**: If validation warnings exist

## Performance Considerations

### Optimization Features
- **Vectorized Operations**: Uses pandas vectorization for better performance
- **Memory Efficient Processing**: Processes data in chunks where possible
- **Cached Calculations**: Reuses computed values across methods
- **Selective Column Processing**: Only processes required fields

### Scalability Notes
- Suitable for medium to large production datasets
- Memory usage scales with number of unique purchase orders
- Processing time depends on production record volume and complexity

## Integration Points

### Input Dependencies
- **DataLoaderAgent**: Provides core production data
- **ValidationOrchestrator**: Supplies validation warnings
- **Database Schemas**: Defines data structure requirements

### Output Consumers
- **Production Management Systems**: Status reports
- **Quality Control**: Warning analysis
- **Planning Systems**: Capacity and scheduling data

## Troubleshooting

### Common Issues
1. **Missing Data Files**: Check path annotations and file existence
2. **Schema Validation Errors**: Verify database schema compatibility
3. **Date Format Issues**: Ensure consistent datetime formats
4. **Memory Errors**: Consider processing in smaller batches for large datasets

### Debug Information
Enable debug logging to get detailed processing information:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")
```