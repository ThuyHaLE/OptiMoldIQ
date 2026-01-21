> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# DayLevelDataProcessor

## Purpose

- Process and analyze daily production records to generate comprehensive reports on manufacturing operations.
- Aggregate production data by mold and item to track performance metrics.
- Classify production changes (mold changes, color changes, machine idle states).
- Calculate defect rates and efficiency metrics across machines, shifts, and products.
- Save processed data with version control and historical tracking.

## Core Responsibilities

- Load and validate production records and purchase order data with schema validation.
- Filter data by specific record date or use the latest available date.
- Merge production records with purchase order information.
- Create composite information fields (machineInfo, itemInfo, itemComponent).
- Calculate count metrics (items, molds, components) by machine and shift.
- Compute job metrics including job counts and late delivery status.
- Classify change types in production flow.
- Generate mold-based and item-based aggregated reports.
- Produce summary statistics and analysis reports for daily operations.
- Manage file versioning with automatic archiving to historical database.

## Input Parameters

### Constructor (`__init__`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `record_date` | `Optional[str]` | `None` | Specific date to process (YYYY-MM-DD). If None, uses latest available date. |
| `source_path` | `str` | `'agents/shared_db/DataLoaderAgent/newest'` | Path to data source directory. |
| `annotation_name` | `str` | `"path_annotations.json"` | Name of path annotation file. |
| `databaseSchemas_path` | `str` | `'database/databaseSchemas.json'` | Path to database schema JSON file. |
| `default_dir` | `str` | `"agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"` | Default output directory. |

### Main Method (`data_process`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `save_output` | `bool` | `False` | Whether to save output files (Excel, summary, logs). |

## Output

### Return Values from `data_process()`

When `save_output=False`:
- `latest_record_date`: The date used for processing
- `merged_df`: Enriched production records with calculated metrics
- `mold_based_record_df`: Aggregated report by mold
- `item_based_record_df`: Aggregated report by item
- `summary_stats`: Dictionary of daily statistics
- `analysis_summary`: Formatted text summary
- `None`: No log entries

When `save_output=True`:
- Same as above, plus:
- `log_entries`: List of file operation log messages

### Saved Files (when `save_output=True`)

| File | Location | Format | Description |
|------|----------|--------|-------------|
| `{timestamp}_{filename_prefix}_insights_{record_date}.xlsx` | `output_dir/newest/` | Excel | Multi-sheet workbook with all analysis results |
| `{timestamp}_{filename_prefix}_summary_{record_date}.txt` | `output_dir/newest/` | Text | Human-readable analysis summary |
| `change_log.txt` | `output_dir/` | Text | Append-only log of all file operations |

### Excel Workbook Sheets

| Sheet Name | Content | Source |
|------------|---------|--------|
| `selectedDateFilter` | All filtered records for the date | `merged_df` |
| `moldBasedRecords` | Mold-level aggregated data | `mold_based_record_df` |
| `itemBasedRecords` | Item-level aggregated data | `item_based_record_df` |
| `summaryStatics` | Summary statistics KPIs | `summary_stats` |

## Class Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `GROUP_COLS` | `['machineInfo', 'workingShift']` | Columns used for grouping operations |
| `COMPONENT_COLS` | `['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']` | Material component columns |
| `COUNT_CONFIGS` | `{'itemCount': 'itemInfo', 'moldCount': 'moldNo', 'itemComponentCount': 'itemComponent'}` | Configuration for counting distinct entities |
| `REQUIRED_CONFIGS` | `{'mold': [...], 'item': [...]}` | Required columns for mold-based and item reports |

### REQUIRED_CONFIGS Details

**Mold-based required fields:**
```python
['machineInfo', 'workingShift', 'moldNo', 'moldShot',
 'moldCavity', 'itemTotalQuantity', 'itemGoodQuantity', 'changeType']
```

**Item-based required fields:**
```python
['machineInfo', 'workingShift', 'itemInfo',
 'moldNo', 'moldShot', 'moldCavity',
 'itemTotalQuantity', 'itemGoodQuantity', 'itemComponent']
```

## Main Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `data_process(save_output=False)` | `Tuple[str, DataFrame, DataFrame, DataFrame, dict, str, Optional[list]]` | Main entry point: processes data and optionally saves outputs. |
| `product_record_processing()` | `Tuple[str, DataFrame, DataFrame, DataFrame, dict, str]` | Core processing pipeline: filters, merges, calculates, classifies, and aggregates. |
| `generate_summary_stats(merged_df, record_date)` | `dict` | Generates comprehensive statistics including active jobs, machines, products, molds, and late orders. |
| `_log_analysis_summary(stats)` | `str` | Converts summary statistics dictionary to formatted text report. |
| `_load_dataframe(df_name)` | `DataFrame` | Loads a specific DataFrame from path annotation with error handling. |

### Static Methods

| Method | Parameters | Return Type | Description |
|--------|------------|-------------|-------------|
| `_classify_change(row)` | `row: Series` | `str` | Classifies production change type based on row data. |
| `_create_info_fields(df)` | `df: DataFrame` | `DataFrame` | Creates composite information fields. |
| `_calculate_counts(df)` | `df: DataFrame` | `DataFrame` | Calculates distinct counts per machine and shift. |
| `_calculate_job_metrics(df)` | `df: DataFrame` | `DataFrame` | Computes job count and late status metrics. |
| `_mold_based_processing(record_df, required_fields)` | `record_df: DataFrame, required_fields: list` | `DataFrame` | Aggregates data by mold with change type handling. |
| `_item_based_processing(record_df, required_fields)` | `record_df: DataFrame, required_fields: list` | `DataFrame` | Aggregates data by item across all machines. |

## Change Type Classification

| Change Type | Condition | Description |
|-------------|-----------|-------------|
| `mold&color_change` | Both `moldChanged` and `colorChanged` exist (not NA) | Changed both mold and color |
| `mold_change` | Only `moldChanged` exists (not NA) | Changed mold only |
| `color_change` | Only `colorChanged` exists (not NA) | Changed color/material only |
| `machine_idle` | `jobCount == 0` | Machine not running |
| `no_change` | None of the above | Continuous production run |

## Data Flow

```
1. Load data
   └─> productRecords_df + purchaseOrders_df (with schema validation)

2. Filter by date
   └─> Latest or specified record_date
   └─> Fallback to latest if specified date unavailable

3. Merge data
   └─> Combine production records with purchase orders
   └─> Handle missing poNo column (rename from poNote if needed)

4. Enrich data
   └─> _create_info_fields() creates composite fields
       ├─> machineInfo: "machineNo (machineCode)"
       ├─> itemInfo: "itemCode (itemName)"
       └─> itemComponent: tuple of component codes

5. Calculate metrics
   ├─> _calculate_counts(): itemCount, moldCount, itemComponentCount
   └─> _calculate_job_metrics(): jobCount, lateStatus

6. Classify changes
   └─> _classify_change() determines production change types

7. Split processing
   ├─> _mold_based_processing()
   │   ├─> Separate by changeType
   │   ├─> Aggregate color_change records
   │   ├─> Combine all groups
   │   └─> Calculate defects and rates
   │
   └─> _item_based_processing()
       ├─> Group by itemInfo
       ├─> Aggregate across all machines/shifts
       └─> Calculate defects and rates

8. Generate summary
   └─> generate_summary_stats() produces KPIs
   └─> _log_analysis_summary() formats text report

9. Save outputs (if save_output=True)
   ├─> Move old files to historical_db
   ├─> Save Excel workbook
   ├─> Save text summary
   └─> Update change log
```

## Mold-Based Report Structure

```python
# Output columns from _mold_based_processing():
{
    'machineInfo': str,          # "Machine123 (MC-001)"
    'workingShift': int,         # 1, 2, or 3
    'moldNo': str,               # Mold identifier
    'changeType': str,           # Change classification
    'itemTotalQuantity': float,  # Total items produced
    'itemGoodQuantity': float,   # Good quality items
    'moldShot': float,           # Avg for color_change, direct for others
    'moldCavity': float,         # Avg for color_change, direct for others
    'defectQuantity': float,     # itemTotalQuantity - itemGoodQuantity
    'defectRate': float          # (defectQuantity / itemTotalQuantity) * 100
}
```

**Processing Logic:**
- `no_change`: Records passed through as-is
- `mold_change`: Records passed through as-is
- `machine_idle`: Records passed through as-is
- `color_change`: Aggregated by (machineInfo, workingShift, moldNo, changeType)
  - `itemTotalQuantity`: sum
  - `itemGoodQuantity`: sum
  - `moldShot`: mean
  - `moldCavity`: mean

## Item-Based Report Structure

```python
# Output columns from _item_based_processing():
{
    'itemInfo': str,             # "ITEM001 (Product Name)"
    'itemTotalQuantity': float,  # Total quantity produced
    'itemGoodQuantity': float,   # Good quality quantity
    'usedMachineNums': int,      # Number of distinct machines used
    'totalShifts': int,          # Total number of shift records
    'usedMoldNums': int,         # Number of distinct molds used
    'moldTotalShots': float,     # Sum of all shots
    'avgCavity': float,          # Average number of cavities
    'usedComponentNums': int,    # Number of distinct component configs
    'defectQuantity': float,     # Total defects
    'defectRate': float          # Defect percentage
}
```

**Aggregation:** All records grouped by `itemInfo` across all machines and shifts.

## Summary Statistics Output

```python
{
    'record_date': str,                    # "2024-01-15"
    'total_records': int,                  # All records in filtered data
    'active_jobs': int,                    # Records with itemTotalQuantity > 0 and valid poNo
    'working_shifts': int,                 # Unique shifts with active jobs
    'machines': int,                       # Unique machines with active jobs
    'purchase_orders': int,                # Unique purchase orders
    'products': int,                       # Unique products (with itemCode)
    'molds': int,                          # Unique molds (with moldNo)
    'late_pos': int,                       # POs where recordDate >= poETA
    'total_pos_with_eta': int,             # Total POs with ETA available
    'change_type_distribution': {          # Count by change type
        'no_change': int,
        'color_change': int,
        'mold_change': int,
        'mold&color_change': int,
        'machine_idle': int
    }
}
```

## Analysis Summary Format

```
============================================================
DATA SUMMARY REPORT
============================================================
Record date: 2024-01-15
Total records: 150
Active jobs: 45
Working shifts: 3
Machines: 12
Purchase orders: 28
Products: 18
Molds: 15
POs delayed vs ETA: 5/25
Change type distribution:
  └─ no_change: 100
  └─ color_change: 30
  └─ mold_change: 15
  └─ machine_idle: 5
============================================================
```

## File Management System

### Directory Structure
```
default_dir/
├── DayLevelDataProcessor/
│   ├── newest/                    # Current version
│   │   ├── {timestamp}_day_level_insights_{date}.xlsx
│   │   └── {timestamp}_day_level_summary_{date}.txt
│   ├── historical_db/             # Archived versions
│   │   ├── {old_timestamp}_day_level_insights_{date}.xlsx
│   │   └── {old_timestamp}_day_level_summary_{date}.txt
│   └── change_log.txt             # Operation history
```

### Timestamp Formats
- **For display/logs:** `%Y-%m-%d %H:%M:%S` → "2024-01-15 14:30:00"
- **For filenames:** `%Y%m%d_%H%M` → "20240115_1430"

### Archiving Process
1. When saving new files, move ALL existing files from `newest/` to `historical_db/`
2. Log each move operation
3. Save new files to `newest/`
4. Update `change_log.txt`

## Error Handling

| Error Type | Trigger | Behavior |
|------------|---------|----------|
| `KeyError` | Path not found in annotations | Log error and raise with message |
| `FileNotFoundError` | DataFrame file doesn't exist | Log error and raise with message |
| `ValueError` | Empty productRecords_df | Log error and raise |
| `ValueError` | Missing recordDate column | Log error and raise |
| `OSError` | File move/save failure | Log error and raise with details |
| Missing date | Specified date not in data | Log warning, fallback to latest date |
| Missing poETA | Column not found | Log warning, set lateStatus=False |
| Date parse error | Invalid date format in lateStatus | Log warning, default to False |
| Empty filtered data | No records for date | Log warning, return empty results |
| Missing merge columns | PO columns unavailable | Log warning, skip merge |

### Safe Operations
- **Division by zero:** Uses `np.where()` for defect rate calculation
- **Null handling:** Uses `dropna=False` in groupby, `fillna(0)` for quantities
- **Missing columns:** Conditional checks before accessing optional columns
- **Empty DataFrames:** Checks and returns empty DataFrame if no data

## Schema Validation

Uses `@validate_init_dataframes` decorator to ensure DataFrames match expected schema:
- **productRecords_df:** Validated against `dynamicDB.productRecords.dtypes`
- **purchaseOrders_df:** Validated against `dynamicDB.purchaseOrders.dtypes`

## Logging

Uses `loguru` logger with class binding:
```python
self.logger = logger.bind(class_="DayLevelDataProcessor")
```

**Log Levels:**
- `INFO`: Successful operations, data loading, statistics
- `WARNING`: Missing columns, date fallbacks, empty results
- `ERROR`: File errors, validation failures, processing errors

## Usage Example

```python
# Initialize processor
processor = DayLevelDataProcessor(
    record_date="2024-01-15",  # Optional: specific date
    source_path="agents/shared_db/DataLoaderAgent/newest"
)

# Process without saving
date, merged, mold_report, item_report, stats, summary, _ = processor.data_process(save_output=False)

# Process and save all outputs
date, merged, mold_report, item_report, stats, summary, logs = processor.data_process(save_output=True)

# Access results
print(f"Processed date: {date}")
print(f"Active jobs: {stats['active_jobs']}")
print(f"Defect rate: {mold_report['defectRate'].mean():.2f}%")
```

## Dependencies

```python
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from loguru import logger
from pathlib import Path
import os
from datetime import datetime
import shutil
from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
```