# MonthLevelDataProcessor

## Purpose

- Analyze monthly manufacturing operations and purchase order fulfillment status.
- Track backlog orders from previous months and assess their impact on current production.
- Estimate production capacity based on mold specifications and historical usage.
- Detect capacity constraints and identify orders at risk of delay.
- Classify order status (finished, in-progress, not-started) and timeliness (ontime, late).
- Save processed data with version control and historical tracking.

## Core Responsibilities

- Load and validate production records, purchase orders, mold info, and mold specifications with schema validation.
- Validate analysis parameters to ensure temporal consistency between analysis date and available data.
- Filter purchase orders by target month and identify backlog from previous months.
- Merge production records with purchase order data to determine fulfillment status.
- Calculate remaining quantities and production progress for unfinished orders.
- Estimate production capacity using mold technical specifications (cavity, cycle time).
- Analyze unfinished orders by mold usage to detect overcapacity and predict lead times.
- Generate comprehensive summary statistics and validation reports.
- Manage file versioning with automatic archiving to historical database.

## Input Parameters

### Constructor (`__init__`)

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `record_month` | `str` | - | **Yes** | Target analysis month in `"YYYY-MM"` format. Example: `"2024-03"` |
| `analysis_date` | `str` | `None` | No | Analysis cutoff date in `"YYYY-MM-DD"` format. If None, uses end of record_month. |
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
- `adjusted_record_month`: Validated record month string (possibly adjusted)
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
| `{timestamp}_{filename_prefix}_insights_{record_month}.xlsx` | `output_dir/newest/` | Excel | Multi-sheet workbook with finished and unfinished orders |
| `{timestamp}_{filename_prefix}_summary_{record_month}.txt` | `output_dir/newest/` | Text | Combined validation and analysis summary |
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
| Analysis date looking at past/current month | ✅ Proceed normally |
| Analysis date looking at future month | ❌ Reject - cannot analyze future from past perspective |
| Analysis date > max available recordDate | Adjust analysis_date to latest recordDate, adjust record_month accordingly |
| No historical data available | ❌ Raise ValueError |
| Requested date not in available data | Log warning, fall back to latest available date |
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
| `_validate_analysis_parameters()` | `Tuple[Timestamp, str, str]` | Validates and adjusts analysis date and record month, returns validation summary. |
| `_detect_backlog(record_month, analysis_timestamp, product_records)` | `DataFrame` | Identifies orders with ETA before target month that remain unfinished. |
| `_calculate_backlog_quantity(backlog_df, product_records, cutoff, analysis)` | `DataFrame` | Recalculates backlog quantities using latest production data. |
| `_filter_data(record_month, analysis_timestamp)` | `DataFrame` | Filters POs for target month, merges with production status, combines with backlog. |
| `_compute_mold_capacity(df, mold_col, mold_num_col)` | `DataFrame` | Calculates production capacity based on mold specifications. |
| `_estimate_item_capacity()` | `DataFrame` | Estimates capacity for not-started orders using available mold list. |
| `_calculate_mold_capacity(in_progress_df)` | `DataFrame` | Calculates capacity for in-progress orders using actual mold history. |
| `_load_dataframe(df_name)` | `DataFrame` | Loads a specific DataFrame from path annotation with error handling. |

### Static Methods

| Method | Parameters | Return Type | Description |
|--------|------------|-------------|-------------|
| `_create_item_code_name(df)` | `df: DataFrame` | `Series` | Creates combined item identifier: `"itemCode(itemName)"`. |
| `_process_pro_status(product_records_df)` | `product_records_df: DataFrame` | `DataFrame` | Aggregates production records per PO (date range, quantity, mold usage). |
| `_merge_purchase_status(purchase_orders, product_records)` | `purchase_orders: DataFrame, product_records: DataFrame` | `DataFrame` | Merges POs with production data, determines completion and ETA status. |
| `_analyze_unfinished_pos(unfinished_df, analysis_timestamp)` | `unfinished_df: DataFrame, analysis_timestamp: Timestamp` | `DataFrame` | Analyzes unfinished orders: cumulative loads, lead times, capacity warnings. |
| `_log_analysis_summary(...)` | `record_month: str, analysis_timestamp: Timestamp, ...` | `str` | Generates formatted analysis summary text. |
| `_log_validation_summary(...)` | `record_month: str, original_analysis_date: Timestamp, ...` | `str` | Generates formatted validation summary text. |

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
       ├─> Validate date formats
       ├─> Adjust dates if needed (future or beyond data)
       └─> Generate validation_summary

3. Filter data
   └─> _filter_data(record_month, analysis_timestamp)
       ├─> Filter POs by record_month (poETA in target month)
       ├─> Detect backlog
       │   └─> _detect_backlog()
       │       ├─> Find POs with poETA <= cutoff_date
       │       ├─> Filter unfinished orders
       │       └─> _calculate_backlog_quantity()
       │           ├─> Get production between cutoff and analysis date
       │           ├─> Recalculate remaining quantities
       │           └─> Update status
       ├─> Merge POs with production status
       │   └─> _merge_purchase_status()
       │       ├─> _process_pro_status() aggregates production
       │       └─> Determine proStatus (finished/unfinished)
       └─> Combine backlog + current month POs

4. Calculate remaining quantities
   └─> itemRemainQuantity = itemQuantity - itemGoodQuantity
   └─> Flag overproduction (itemRemainQuantity < 0)

5. Classify order status
   └─> finished: itemRemainQuantity <= 0
   └─> in_progress: has moldHist
   └─> not_started: no moldHist

6. Split by status
   ├─> finished_df
   │   └─> Calculate etaStatus (ontime/late)
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

7. Generate summaries
   ├─> _log_analysis_summary()
   └─> Combine validation_summary + analysis_summary

8. Save outputs (if save_output=True)
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
# Cutoff date = last day before record_month starts
record_period = pd.Period(record_month, freq="M")
period_timestamp = record_period.to_timestamp(how="start")
cutoff_date = period_timestamp - pd.Timedelta(days=1)

# Backlog orders criteria:
# 1. poETA <= cutoff_date (expected before target month)
# 2. proStatus != 'finished' (not completed yet)

# Example: record_month = "2024-03"
# → cutoff_date = 2024-02-29
# → Backlog = orders with ETA in Jan, Feb, etc. that are still unfinished

# Recalculate backlog quantities:
# Filter production records: cutoff_date < recordDate <= analysis_timestamp
remaining_backlog_qty = original_backlog_qty - qty_produced_before_cutoff
current_good_qty = qty_produced_between_cutoff_and_analysis
current_ng_qty = ng_produced_between_cutoff_and_analysis
itemRemainQuantity = remaining_backlog_qty - current_good_qty
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
    'is_backlog': bool              # True if from previous month
}
```

## Unfinished Orders Output Structure

```python
# Key fields in unfinished_df:
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

## Unfinished Orders Analysis Details

### Cumulative Calculation Logic

```python
# Orders are sorted by: moldList → poReceivedDate → poETA
# This creates a production queue per mold group

# Example mold group "MoldA/MoldB":
# PO1: remain=1000 → accumulatedQuantity=1000
# PO2: remain=500  → accumulatedQuantity=1500
# PO3: remain=800  → accumulatedQuantity=2300

# accumulatedRate shows position in queue:
# PO1: 1000/2300 = 0.43
# PO2: 1500/2300 = 0.65
# PO3: 2300/2300 = 1.00
```

### Capacity Warning Detection

```python
# avgCumsumLT: cumulative lead time using avg 1 mold
# totalCumsumLT: cumulative lead time using all molds
# poRLT: remaining time until ETA

overAvgCapacity = (avgCumsumLT > poRLT) AND (poRLT >= 0)
overTotalCapacity = (totalCumsumLT > poRLT) AND (poRLT >= 0)

capacityWarning = overAvgCapacity OR overTotalCapacity

capacitySeverity = 
    'critical' if overTotalCapacity      # Cannot meet deadline even with all molds
    'high' if overAvgCapacity            # Need multiple molds running in parallel
    'normal' otherwise                   # Within 1-mold capacity
```

### ETA Status Classification Logic

```python
is_in_progress = (poStatus == "in_progress")
is_finished = (itemRemainQuantity == 0)
is_on_eta = (lastRecord <= poETA)
is_within_eta = (avgCumsumLT < poRLT)

etaStatus = 
    'ontime'           if in_progress AND finished AND is_on_eta
    'late'             if in_progress AND finished AND NOT is_on_eta
    'ontime'           if in_progress AND NOT finished AND is_within_eta
    'late'             if in_progress AND NOT finished AND NOT is_within_eta
    'expected_ontime'  if NOT in_progress AND is_within_eta
    'late'             if NOT in_progress AND NOT is_within_eta
    'unknown'          otherwise
```

## Summary Output Format

```text
============================================================
VALIDATION SUMMARY
============================================================
Record month (requested): 2024-03
Analysis date (validated): 2024-03-31
  └─ Adjusted from: 2024-04-15
============================================================

============================================================
Analysis Results for 2024-03
Analysis date: 2024-03-31
Total Orders: 45
Completed Orders Rate: 28/45
Remaining Orders Rate: 17/45
Orders with Capacity Warning: 5
Capacity Severity Distribution: {'normal': 10, 'high': 4, 'critical': 3}
Backlog Orders: 3-(['PO001', 'PO002', 'PO003'])
============================================================
```

## File Management System

### Directory Structure
```
default_dir/
├── MonthLevelDataProcessor/
│   ├── newest/                    # Current version
│   │   ├── {timestamp}_day_level_insights_{record_month}.xlsx
│   │   └── {timestamp}_day_level_summary_{record_month}.txt
│   ├── historical_db/             # Archived versions
│   │   ├── {old_timestamp}_day_level_insights_{record_month}.xlsx
│   │   └── {old_timestamp}_day_level_summary_{record_month}.txt
│   └── change_log.txt             # Operation history
```

### Timestamp Formats
- **For display/logs:** `%Y-%m-%d %H:%M:%S` → "2024-03-31 14:30:00"
- **For filenames:** `%Y%m%d_%H%M` → "20240331_1430"

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
| `ValueError` | Invalid record_month format | Raise "Expected 'YYYY-MM'" |
| `ValueError` | Invalid analysis_date format | Raise "Expected 'YYYY-MM-DD'" |
| `ValueError` | Analysis date before record_month | Raise "Cannot analyze future month from past date" |
| `ValueError` | Requested month not in data | Raise with available months list |
| `ValueError` | No data for target month | Raise with earliest available date |
| `OSError` | File move/save failure | Log error and raise with details |
| Date adjustment | analysis_date > max recordDate | Log warning, adjust to max date, adjust record_month |
| Missing columns | Required PO/production columns missing | Raise KeyError |

### Safe Operations
- **Division by zero:** Guards in capacity calculations (`moldSettingCycle > 0`, `moldCavityStandard > 0`)
- **Null handling:** Uses `notna()` checks, fills with 0 or appropriate defaults
- **Empty DataFrames:** Returns empty DataFrame with correct columns
- **Date parsing:** Wrapped in try-except with detailed error messages
- **Backlog calculation:** Uses `validate_dataframe` decorator for column validation

## Schema Validation

Uses `@validate_init_dataframes` decorator to ensure DataFrames match expected schema:
- **productRecords_df:** Validated against `dynamicDB.productRecords.dtypes`
- **purchaseOrders_df:** Validated against `dynamicDB.purchaseOrders.dtypes`
- **moldInfo_df:** Validated against `staticDB.moldInfo.dtypes`
- **moldSpecificationSummary_df:** Validated against `staticDB.moldSpecificationSummary.dtypes`

Additional runtime validation using `@validate_dataframe`:
- Used in `_calculate_backlog_quantity()` to verify required columns exist

## Logging

Uses `loguru` logger with class binding:
```python
self.logger = logger.bind(class_="MonthLevelDataProcessor")
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
5. **Overproduction allowed**: `itemRemainQuantity` can be negative (system tracks overproduction).
6. **Single item per PO**: Each PO contains only one item type.
7. **Mold sharing**: Multiple POs can use the same mold(s), creating queue effects.
8. **Static capacity**: Mold capacity doesn't change during the analysis period.

## Usage Example

```python
# Initialize processor with required month
processor = MonthLevelDataProcessor(
    record_month="2024-03",
    analysis_date="2024-03-31",  # Optional: defaults to end of month
    source_path="agents/shared_db/DataLoaderAgent/newest"
)

# Process without saving
timestamp, month, finished, unfinished, summary, _ = processor.data_process(save_output=False)

# Process and save all outputs
timestamp, month, finished, unfinished, summary, logs = processor.data_process(save_output=True)

# Access results
print(f"Analysis performed on: {timestamp.date()}")
print(f"Completed orders: {len(finished)}")
print(f"Orders with capacity warning: {unfinished['capacityWarning'].sum()}")
print(f"Critical capacity issues: {(unfinished['capacitySeverity'] == 'critical').sum()}")

# Analyze capacity warnings
warnings = unfinished[unfinished['capacityWarning'] == True]
for _, row in warnings.iterrows():
    print(f"PO {row['poNo']}: {row['capacitySeverity']} - {row['capacityExplanation']}")
```

## Dependencies

```python
import numpy as np
import pandas as pd
from typing import Tuple
from loguru import logger
from pathlib import Path
import os
from datetime import datetime
import shutil
from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.utils import load_annotation_path
```