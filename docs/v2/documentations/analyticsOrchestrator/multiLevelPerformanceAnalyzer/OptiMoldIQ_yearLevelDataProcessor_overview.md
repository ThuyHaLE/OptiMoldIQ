> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# YearLevelDataProcessor

## Purpose

- Analyze yearly manufacturing operations and purchase order fulfillment status.
- Track backlog orders from previous years and assess their impact on current production.
- Estimate production capacity based on mold specifications and historical usage.
- Detect capacity constraints and identify orders at risk of delay.
- Classify order status (finished, in-progress, not-started) and timeliness (ontime, late).
- Provide monthly breakdown of production progress within the target year.
- Save processed data with version control and historical tracking.

## Core Responsibilities

- Load and validate production records, purchase orders, mold info, and mold specifications with schema validation.
- Validate analysis parameters to ensure temporal consistency between analysis date and available data.
- Filter purchase orders by target year and identify backlog from previous years.
- Merge production records with purchase order data to determine fulfillment status.
- Calculate remaining quantities and production progress for unfinished orders.
- Track overproduction cases explicitly.
- Estimate production capacity using mold technical specifications (cavity, cycle time).
- Analyze unfinished orders by mold usage to detect overcapacity and predict lead times.
- Generate comprehensive summary statistics with monthly breakdowns and validation reports.
- Manage file versioning with automatic archiving to historical database.

## Input Parameters

### Constructor (`__init__`)

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `record_year` | `str` | - | **Yes** | Target analysis year in `"YYYY"` format. Example: `"2024"` |
| `analysis_date` | `str` | `None` | No | Analysis cutoff date in `"YYYY-MM-DD"` format. If None, uses end of record_year. |
| `source_path` | `str` | `'agents/shared_db/DataLoaderAgent/newest'` | No | Path to data source directory. |
| `annotation_name` | `str` | `"path_annotations.json"` | No | Name of path annotation file. |
| `databaseSchemas_path` | `str` | `'database/databaseSchemas.json'` | No | Path to database schema JSON file. |
| `default_dir` | `str` | `"agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"` | No | Default output directory. |

### Main Method (`data_process`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `save_output` | `bool` | `False` | Whether to save output files (Excel, summary, logs). |

## Output

### Return Values from `data_process()`

When `save_output=False`:
- `analysis_timestamp`: Validated analysis date (pd.Timestamp)
- `adjusted_record_year`: Validated record year string (possibly adjusted)
- `finished_df`: Completed orders with ETA status
- `unfinished_df`: In-progress and not-started orders with capacity analysis
- `final_summary`: Combined validation and analysis summary text
- `None`: No log entries

When `save_output=True`:
- Same as above, plus:
- `log_entries`: List of file operation log messages

### Saved Files (when `save_output=True`)

| File | Location | Format | Description |
|------|----------|--------|-------------|
| `{timestamp}_year_level_insights_{record_year}.xlsx` | `output_dir/newest/` | Excel | Multi-sheet workbook with finished and unfinished orders |
| `{timestamp}_year_level_summary_{record_year}.txt` | `output_dir/newest/` | Text | Combined validation and analysis summary |
| `change_log.txt` | `output_dir/` | Text | Append-only log of all file operations |

### Excel Workbook Sheets

| Sheet Name | Content | Source |
|------------|---------|--------|
| `finishedRecords` | Completed orders with ETA status | `finished_df` |
| `unfinishedRecords` | In-progress and not-started orders with capacity analysis | `unfinished_df` |

## Business Logic

### Validation Rules

| Validation Rule | Action |
|-----------------|--------|
| Analysis date looking at past/current year | ✅ Proceed normally |
| Analysis date looking at future year | ❌ Reject - cannot analyze future from past perspective |
| Analysis date > max available recordDate | Adjust analysis_date to latest recordDate, adjust record_year accordingly |
| No historical data available | ❌ Raise ValueError |
| Requested year not in available data | Raise ValueError with available years list |
| All recordDate values are null | ❌ Raise ValueError |

### Order Classification

| Order Status | Condition | Description |
|--------------|-----------|-------------|
| `finished` | `itemRemainQuantity <= 0` | All quantities produced or overproduced |
| `in_progress` | `itemRemainQuantity > 0` AND `moldHist` exists | Production started but not complete |
| `not_started` | `itemRemainQuantity > 0` AND no `moldHist` | Not yet in production |

### ETA Status Classification

| ETA Status | Condition | Description |
|------------|-----------|-------------|
| `ontime` | (Finished before ETA) OR (In-progress with `avgCumsumLT < poRLT`) | On schedule |
| `late` | (Finished after ETA) OR (In-progress with `avgCumsumLT >= poRLT`) | Behind schedule |
| `expected_ontime` | Not started AND `avgCumsumLT < poRLT` | Expected to complete on time |
| `unknown` | Cannot determine (missing data) | Status unclear |

### Capacity Severity Levels

| Severity | Condition | Description | Action Required |
|----------|-----------|-------------|-----------------|
| `normal` | `overTotalCapacity == False` | Within 1-mold capacity, production on track | None |
| `high` | `overAvgCapacity == True` AND `overTotalCapacity == False` | Exceeds avg capacity, need parallel molds | Deploy additional resources or extended shifts |
| `critical` | `overTotalCapacity == True` | Exceeds total capacity, cannot complete with current resources | Reschedule or outsource production |

## Main Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `data_process(save_output=False)` | `Tuple[Timestamp, str, DataFrame, DataFrame, str, Optional[list]]` | Main entry point: processes data and optionally saves outputs. |
| `product_record_processing()` | `Tuple[Timestamp, str, DataFrame, DataFrame, str]` | Main pipeline: validates, filters, calculates, analyzes, and summarizes. |
| `_validate_analysis_parameters()` | `Tuple[Timestamp, str, str]` | Validates and adjusts analysis date and record year, returns validation summary. |
| `_detect_backlog(record_year, analysis_timestamp, product_records)` | `DataFrame` | Identifies orders with ETA before target year that remain unfinished. |
| `_calculate_backlog_quantity(backlog_df, product_records, cutoff, analysis)` | `DataFrame` | Recalculates backlog quantities using latest production data. |
| `_filter_data(record_year, analysis_timestamp)` | `DataFrame` | Filters POs for target year, merges with production status, combines with backlog. |
| `_compute_mold_capacity(df, mold_col, mold_num_col)` | `DataFrame` | Calculates production capacity based on mold specifications. |
| `_estimate_item_capacity()` | `DataFrame` | Estimates capacity for not-started orders using available mold list. |
| `_calculate_mold_capacity(in_progress_df)` | `DataFrame` | Calculates capacity for in-progress orders using actual mold history. |
| `_load_dataframe(df_name)` | `DataFrame` | Loads a specific DataFrame from path annotation with error handling. |

### Static Methods

| Method | Parameters | Return Type | Description |
|--------|------------|-------------|-------------|
| `_create_item_code_name(df)` | `df: DataFrame` | `Series` | Creates combined item identifier: `"itemCode(itemName)"`. |
| `_process_pro_status(product_records_df)` | `product_records_df: DataFrame` | `DataFrame` | Aggregates production records per PO (date range, quantity, mold usage). |
| `_merge_purchase_status(purchase_orders, product_records)` | `purchase_orders: DataFrame, product_records: DataFrame` | `DataFrame` | Merges POs with production data, determines completion status. |
| `_analyze_unfinished_pos(unfinished_df, analysis_timestamp)` | `unfinished_df: DataFrame, analysis_timestamp: Timestamp` | `DataFrame` | Analyzes unfinished orders: cumulative loads, lead times, capacity warnings. |
| `_log_analysis_summary(...)` | `analysis_timestamp: Timestamp, adjusted_record_year: str, df: DataFrame` | `str` | Generates formatted analysis summary with monthly breakdowns. |
| `_log_validation_summary(...)` | `record_year: str, original_analysis_date: Timestamp, ...` | `str` | Generates formatted validation summary text. |

## Data Flow

```
1. Initialize
   └─> Load 4 DataFrames (with schema validation)
       ├─> productRecords_df
       ├─> purchaseOrders_df
       ├─> moldInfo_df
       └─> moldSpecificationSummary_df

2. Validate parameters
   └─> _validate_analysis_parameters()
       ├─> Check temporal consistency
       ├─> Validate date formats (YYYY and YYYY-MM-DD)
       ├─> Adjust dates if needed (future or beyond data)
       └─> Generate validation_summary

3. Filter data
   └─> _filter_data(record_year, analysis_timestamp)
       ├─> Filter POs by record_year (poETA in target year)
       ├─> Detect backlog
       │   └─> _detect_backlog()
       │       ├─> Find POs with poETA <= cutoff_date (last day of previous year)
       │       ├─> Filter unfinished orders
       │       └─> _calculate_backlog_quantity()
       │           ├─> Get production between cutoff and analysis date
       │           ├─> Recalculate remaining quantities
       │           └─> Update status
       ├─> Merge POs with production status
       │   └─> _merge_purchase_status()
       │       ├─> _process_pro_status() aggregates production
       │       └─> Determine proStatus (finished/unfinished)
       └─> Combine backlog + current year POs

4. Calculate remaining quantities
   └─> itemRemainQuantity = itemQuantity - itemGoodQuantity (or full qty if no production)
   └─> Track overproduction: overproduction_quantity = abs(itemRemainQuantity) if negative

5. Classify order status
   └─> finished: itemRemainQuantity <= 0
   └─> in_progress: has moldHist
   └─> not_started: no moldHist

6. Generate analysis summary (before split)
   └─> _log_analysis_summary()
       ├─> Total production progress
       ├─> PO status distribution
       └─> Monthly breakdown with backlog flags

7. Split by status
   ├─> finished_df
   │   └─> Calculate etaStatus (ontime/late based on lastRecord vs poETA)
   │
   └─> in_progress_df + not_started_df
       ├─> Estimate capacities
       │   ├─> not_started: _estimate_item_capacity()
       │   │   └─> Use moldSpecificationSummary (available molds)
       │   └─> in_progress: _calculate_mold_capacity()
       │       └─> Use actual moldHist
       │
       ├─> Both use _compute_mold_capacity()
       │   ├─> Explode mold list to individual molds
       │   ├─> Merge with moldInfo (cavity, cycle time)
       │   ├─> Calculate moldMaxHourCapacity
       │   └─> Aggregate: totalItemCapacity, avgItemCapacity
       │
       ├─> Combine in_progress + not_started
       └─> _analyze_unfinished_pos()
           ├─> Sort by moldList + poReceivedDate
           ├─> Calculate cumulative quantities per mold
           ├─> Estimate lead times (hours → days)
           ├─> Calculate poOTD and poRLT
           ├─> Detect overcapacity (overAvgCapacity, overTotalCapacity)
           ├─> Flag overdue orders
           ├─> Classify etaStatus
           └─> Assign capacitySeverity

8. Combine summaries
   └─> final_summary = validation_summary + analysis_summary

9. Save outputs (if save_output=True)
   ├─> Move old files to historical_db
   ├─> Save Excel workbook (finishedRecords, unfinishedRecords)
   ├─> Save text summary
   └─> Update change_log
```

## Capacity Calculation Formula

```python
# Per-mold hourly capacity
moldMaxHourCapacity = (3600 / moldSettingCycle) × moldCavityStandard

# Total capacity (all molds combined)
totalItemCapacity = sum(moldMaxHourCapacity for all molds)

# Average capacity (per mold)
avgItemCapacity = totalItemCapacity / moldNum

# Estimated lead time (convert hours to days)
HOURS_PER_DAY = 24
totalEstimatedLeadtime = accumulatedQuantity / totalItemCapacity / HOURS_PER_DAY
avgEstimatedLeadtime = accumulatedQuantity / avgItemCapacity / HOURS_PER_DAY
```

## Backlog Detection Logic

```python
# Cutoff date = last day before record_year starts
record_period = pd.Period(record_year, freq="Y")
period_timestamp = record_period.to_timestamp(how="start")
cutoff_date = period_timestamp - pd.Timedelta(days=1)

# Example: record_year = "2024"
# → cutoff_date = 2023-12-31
# → Backlog = orders with ETA in 2023 or earlier that are still unfinished

# Backlog orders criteria:
# 1. poETA <= cutoff_date (expected before target year)
# 2. proStatus != 'finished' (not completed yet)

# Recalculate backlog quantities:
# Filter production records: cutoff_date < recordDate <= analysis_timestamp
remaining_backlog_qty = original_backlog_qty - qty_produced_before_cutoff
current_good_qty = qty_produced_between_cutoff_and_analysis
current_ng_qty = ng_produced_between_cutoff_and_analysis
itemRemainQuantity = remaining_backlog_qty - current_good_qty
```

## Overproduction Tracking

```python
# Detect overproduction cases
overproduction_quantity = np.where(
    itemRemainQuantity < 0,
    abs(itemRemainQuantity),
    0
)

# Interpretation:
# - itemRemainQuantity < 0: Production exceeded ordered quantity
# - overproduction_quantity: Explicit tracking of excess production
# - Still classified as 'finished' status
# - Useful for quality control and inventory management
```

## Finished Orders Output Structure

```python
# Key fields in finished_df:
{
    'poNo': str,                    # Purchase order number
    'poReceivedDate': datetime,     # Order received date
    'poETA': datetime,              # Expected time of arrival
    'itemCode': str,                # Item code
    'itemName': str,                # Item name
    'itemCodeName': str,            # "itemCode(itemName)"
    'itemQuantity': float,          # Original order quantity
    'itemGoodQuantity': float,      # Total produced quantity
    'itemNGQuantity': float,        # Total defective quantity
    'itemRemainQuantity': float,    # <= 0 for finished
    'overproduction_quantity': float, # Absolute value if itemRemainQuantity < 0
    'firstRecord': datetime,        # First production date
    'lastRecord': datetime,         # Last production date
    'moldHistNum': int,             # Number of unique molds used
    'moldHist': str,                # "Mold1/Mold2/Mold3"
    'poStatus': str,                # 'finished'
    'etaStatus': str,               # 'ontime' or 'late'
    'is_backlog': bool              # True if from previous year
}
```

## Unfinished Orders Output Structure

```python
# Key fields in unfinished_df (identical to MonthLevelDataProcessor):
{
    # Basic PO info
    'poNo': str,
    'poReceivedDate': datetime,
    'poETA': datetime,
    'itemCodeName': str,
    'itemQuantity': float,
    'itemGoodQuantity': float,      # May be NaN if not_started
    'itemNGQuantity': float,
    'itemRemainQuantity': float,    # > 0 for unfinished
    'poStatus': str,                # 'in_progress' or 'not_started'
    'is_backlog': bool,
    
    # Mold info
    'moldHistNum': int,             # For in_progress
    'moldHist': str,                # For in_progress
    'moldNum': int,                 # Expected molds to use
    'moldList': str,                # "Mold1/Mold2/Mold3" (sorted)
    
    # Capacity estimates
    'totalItemCapacity': float,     # Combined capacity (items/hour)
    'avgItemCapacity': float,       # Per-mold capacity (items/hour)
    
    # Progress tracking
    'completionProgress': float,    # 0.0 to 1.0 (1 - remain/total)
    'accumulatedQuantity': float,   # Cumulative remain qty in mold queue
    'totalRemainByMold': float,     # Total remain qty for this mold group
    'accumulatedRate': float,       # Progress in mold queue (0.0 to 1.0)
    
    # Lead time estimates (timedelta)
    'totalEstimatedLeadtime': timedelta,  # Using all molds
    'avgEstimatedLeadtime': timedelta,    # Using avg 1 mold
    'totalCumsumLT': timedelta,           # Cumulative LT (total capacity)
    'avgCumsumLT': timedelta,             # Cumulative LT (avg capacity)
    
    # Timing analysis (timedelta)
    'poOTD': timedelta,             # Order-to-Delivery time
    'poRLT': timedelta,             # Remaining Lead Time (0 if past ETA)
    
    # Risk flags
    'overTotalCapacity': bool,      # Exceeds total mold capacity
    'overAvgCapacity': bool,        # Exceeds average mold capacity
    'is_overdue': bool,             # Past ETA or insufficient time
    'capacityWarning': bool,        # Any capacity constraint
    'capacitySeverity': str,        # 'normal', 'high', 'critical'
    'capacityExplanation': str,     # Human-readable description
    'etaStatus': str                # 'ontime', 'late', 'expected_ontime', 'unknown'
}
```

## Analysis Summary Output Structure

The `_log_analysis_summary()` method generates a comprehensive report with:

### Total Production Progress
- Overall production progress across all orders
- PO status distribution (finished/in_progress/not_started)

### Temporal Context
- Unique months in poReceivedDate (when orders were received)
- Unique months in poETA (when orders are expected)

### Monthly Production Breakdown
For each month within the target year:
- ETA period with backlog flag if applicable
- Production progress (good quantity / total quantity)
- PO status breakdown for that month

```text
============================================================
VALIDATION SUMMARY
============================================================
Record year (requested): 2024
Analysis date (validated): 2024-12-31
  └─ Adjusted from: 2025-03-15
============================================================

============================================================
ANALYSIS SUMMARY
============================================================
Record year (requested): 2024
Analysis date (validated): 2024-12-31
------------------------------
TOTAL PRODUCTION PROGRESS
Production progress: 150,000 / 200,000 (75.00%)
Finished POs: 35/60 (58.33%)
In_progress POs: 20/60 (33.33%)
Not_started POs: 5/60 (8.33%)
------------------------------
Unique months in poReceivedDate: ['2024-01', '2024-02', '2024-03', ...]
Unique months in poETA: ['2023-12', '2024-01', '2024-02', ...]
------------------------------
MONTHLY PRODUCTION PROGRESS
- ETA period: 2023-12 (BACKLOG): Production progress: 8,000/10,000 (80.00%)
  Finished POs: 5/8 (62.50%)
  In-progress POs: 2/8 (25.00%)
  Not-start POs: 1/8 (12.50%)
- ETA period: 2024-01: Production progress: 12,000/15,000 (80.00%)
  Finished POs: 7/10 (70.00%)
  In-progress POs: 3/10 (30.00%)
  Not-start POs: 0/10 (0.00%)
- ETA period: 2024-02: Production progress: 15,000/18,000 (83.33%)
  Finished POs: 8/12 (66.67%)
  In-progress POs: 3/12 (25.00%)
  Not-start POs: 1/12 (8.33%)
[... continues for each month in the year ...]
============================================================
```

## File Management System

### Directory Structure
```
default_dir/
├── YearLevelDataProcessor/
│   ├── newest/                    # Current version
│   │   ├── {timestamp}_year_level_insights_{record_year}.xlsx
│   │   └── {timestamp}_year_level_summary_{record_year}.txt
│   ├── historical_db/             # Archived versions
│   │   ├── {old_timestamp}_year_level_insights_{record_year}.xlsx
│   │   └── {old_timestamp}_year_level_summary_{record_year}.txt
│   └── change_log.txt             # Operation history
```

### Timestamp Formats
- **For display/logs:** `%Y-%m-%d %H:%M:%S` → "2024-12-31 14:30:00"
- **For filenames:** `%Y%m%d_%H%M` → "20241231_1430"

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
| `ValueError` | Empty productRecords_df | Raise "No historical production data available" |
| `ValueError` | All recordDate values are null | Raise "Cannot proceed with analysis" |
| `ValueError` | Invalid record_year format | Raise "Expected 'YYYY'" |
| `ValueError` | Invalid analysis_date format | Raise "Expected 'YYYY-MM-DD'" |
| `ValueError` | Analysis date before record_year | Raise "Cannot analyze future year from past date" |
| `ValueError` | Requested year not in data | Raise with available years list |
| `ValueError` | No data for target year | Raise with earliest available date |
| `OSError` | File move/save failure | Log error and raise with details |
| Date adjustment | analysis_date > max recordDate | Log warning, adjust to max date, adjust record_year |
| Missing columns | Required PO/production columns missing | Raise KeyError |

### Safe Operations
- **Division by zero:** Guards in capacity calculations (`moldSettingCycle > 0`, `moldCavityStandard > 0`)
- **Null handling:** Uses `notna()` checks, fills with 0 or appropriate defaults
- **Empty DataFrames:** Returns empty DataFrame with correct columns
- **Date parsing:** Wrapped in try-except with detailed error messages
- **Backlog calculation:** Uses `validate_dataframe` decorator for column validation
- **Overproduction:** Uses `np.maximum(0, ...)` to prevent negative quantities in most fields

## Schema Validation

Uses `@validate_init_dataframes` decorator to ensure DataFrames match expected schema:
- **productRecords_df:** Validated against `dynamicDB.productRecords.dtypes`
- **purchaseOrders_df:** Validated against `dynamicDB.purchaseOrders.dtypes`
- **moldInfo_df:** Validated against `staticDB.moldInfo.dtypes`
- **moldSpecificationSummary_df:** Validated against `staticDB.moldSpecificationSummary.dtypes`

Additional runtime validation using `@validate_dataframe`:
- Used in `_calculate_backlog_quantity()` to verify required columns exist
- Used in `_log_analysis_summary()` to verify DataFrame structure

## Logging

Uses `loguru` logger with class binding:
```python
self.logger = logger.bind(class_="YearLevelDataProcessor")
```

**Log Levels:**
- `INFO`: Successful operations, data loading, validation steps, analysis results
- `WARNING`: Date adjustments, missing data, fallback operations
- `ERROR`: File errors, validation failures, missing columns
- `DEBUG`: Detailed backlog order numbers (when verbose debugging enabled)

## Key Assumptions

1. **24-hour operation**: Lead time calculations assume continuous production without breaks.
2. **Constant cycle time**: Uses mold specification cycle time without degradation or variation.
3. **Sequential processing**: Orders processed in FIFO order per mold group (sorted by poReceivedDate).
4. **No setup time**: Mold changes assumed instantaneous in capacity estimates.
5. **Overproduction allowed**: System tracks overproduction cases explicitly via `overproduction_quantity`.
6. **Single item per PO**: Each PO contains only one item type.
7. **Mold sharing**: Multiple POs can use the same mold(s), creating queue effects.
8. **Static capacity**: Mold capacity doesn't change during the analysis period.
9. **Yearly granularity**: Analysis performed at year level with monthly breakdown for visibility.

## Differences from MonthLevelDataProcessor

| Aspect | YearLevelDataProcessor | MonthLevelDataProcessor |
|--------|------------------------|-------------------------|
| **Time Granularity** | Analyzes full year with monthly breakdowns | Analyzes single month |
| **Date Format** | `record_year: "YYYY"` | `record_month: "YYYY-MM"` |
| **Cutoff Calculation** | Last day of previous year (`YYYY-01-01` - 1 day) | Last day of previous month |
| **Period Type** | `pd.Period(freq="Y")` | `pd.Period(freq="M")` |
| **Backlog Scope** | Orders from all previous years | Orders from previous months |
| **Summary Output** | Includes monthly breakdown within year | Single month analysis only |
| **Overproduction** | Explicitly tracked with `overproduction_quantity` field | Handled implicitly via negative `itemRemainQuantity` |
| **Analysis Summary** | Generated before splitting into finished/unfinished | Generated after all processing |
| **Use Case** | Strategic planning, annual performance review, budget allocation | Operational tracking, monthly targets, immediate action items |
| **Logging Detail** | Shows yearly trends, includes `year` in min/max dates | Shows monthly patterns, includes `date` in min/max dates |
| **Summary Detail** | Monthly PO status breakdown per ETA period | Overall statistics for the single month |

## Usage Example

```python
# Initialize processor with required year
processor = YearLevelDataProcessor(
    record_year="2024",
    analysis_date="2024-12-31",  # Optional: defaults to end of year
    source_path="agents/shared_db/DataLoaderAgent/newest"
)

# Process without saving
timestamp, year, finished, unfinished, summary, _ = processor.data_process(save_output=False)

# Process and save all outputs
timestamp, year, finished, unfinished, summary, logs = processor.data_process(save_output=True)

# Access results
print(f"Analysis performed on: {timestamp.date()}")
print(f"Target year: {year}")
print(f"Completed orders: {len(finished)}")
print(f"Overproduction cases: {(finished['overproduction_quantity'] > 0).sum()}")
print(f"Total overproduced quantity: {finished['overproduction_quantity'].sum():,.0f}")

# Analyze monthly trends
monthly_stats = unfinished.groupby(unfinished['poETA'].dt.to_period('M')).agg({
    'poNo': 'count',
    'itemRemainQuantity': 'sum',
    'capacityWarning': 'sum'
})
print(monthly_stats)

# Identify critical capacity issues
critical = unfinished[unfinished['capacitySeverity'] == 'critical']
print(f"Critical capacity warnings: {len(critical)}")
for _, row in critical.iterrows():
    print(f"  PO {row['poNo']}: {row['itemCodeName']} - ETA: {row['poETA'].date()}")

# Analyze backlog impact
backlog = finished[finished['is_backlog'] == True]
print(f"Backlog orders completed: {len(backlog)}")
print(f"Backlog late rate: {(backlog['etaStatus'] == 'late').sum() / len(backlog) * 100:.1f}%")
```

## Dependencies

```python
from typing import Tuple
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import load_annotation_path
from loguru import logger
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
import shutil
import os
```