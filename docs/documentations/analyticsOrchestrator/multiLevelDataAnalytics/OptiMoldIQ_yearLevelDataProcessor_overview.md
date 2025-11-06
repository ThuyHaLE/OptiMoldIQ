# YearLevelDataProcessor

- **Purpose**:
  
    - Analyze yearly manufacturing operations and purchase order fulfillment status.
    - Track backlog orders from previous years and assess their impact on current production.
    - Estimate production capacity based on mold specifications and historical usage.
    - Detect capacity constraints and identify orders at risk of delay.
    - Classify order status (finished, in-progress, not-started) and timeliness (ontime, late).

- **Core responsibilities**:
  
    - Load and validate production records, purchase orders, mold info, and mold specifications.
    - Validate analysis parameters to ensure temporal consistency between analysis date and available data.
    - Filter purchase orders by target year and identify backlog from previous years.
    - Merge production records with purchase order data to determine fulfillment status.
    - Calculate remaining quantities and production progress for unfinished orders.
    - Estimate production capacity using mold technical specifications (cavity, cycle time).
    - Analyze unfinished orders by mold usage to detect overcapacity and predict lead times.
    - Generate comprehensive summary statistics and validation reports.

- **Input**:
  
    - `productRecords_df`: Production records containing machine operations, quantities, and mold usage.
    - `purchaseOrders_df`: Purchase orders with order details, quantities, and ETAs.
    - `moldInfo_df`: Mold technical specifications (cavity count, cycle time).
    - `moldSpecificationSummary_df`: Summary of available molds per item type.
    - `record_year`: Target analysis year in `"YYYY"` format.
    - `analysis_date` (optional): Analysis cutoff date in `"YYYY-MM-DD"` format. If None, uses end of record_year.

- **Output**:
  
    - `analysis_timestamp`: Validated analysis date (possibly adjusted).
    - `adjusted_record_year`: Validated record year (possibly adjusted).
    - `finished_df`: Completed orders with ETA status (ontime/late).
    - `unfinished_df`: In-progress and not-started orders with capacity analysis and risk assessment.
    - `final_summary`: Text summary combining validation results and analysis statistics.

- **Business Logic**:

| Validation Rule                              | Action                                                          |
| -------------------------------------------- | --------------------------------------------------------------- |
| Analysis date looking at past/current year   | ✅ Proceed normally                                             |
| Analysis date looking at future year         | ❌ Reject (cannot analyze future from past perspective)         |
| Analysis date > max available recordDate     | Adjust analysis_date to latest recordDate, adjust record_year   |
| No historical data available                 | ❌ Raise error                                                  |
| Requested date not in available data         | Fall back to latest available date with warning                 |

- **Order Classification**:

| Order Status    | Condition                                           | Description                      |
| --------------- | --------------------------------------------------- | -------------------------------- |
| `finished`      | `itemRemainQuantity <= 0`                           | All quantities produced or over  |
| `in_progress`   | `itemRemainQuantity > 0` and `moldHist` exists      | Production started, not complete |
| `not_started`   | `itemRemainQuantity > 0` and no `moldHist`          | Not yet in production            |

- **ETA Status Classification**:

| ETA Status         | Condition                                                    | Description                           |
| ------------------ | ------------------------------------------------------------ | ------------------------------------- |
| `ontime`           | Finished before ETA, or in-progress within capacity          | On schedule                           |
| `late`             | Finished after ETA, or exceeds capacity                      | Behind schedule                       |
| `expected_ontime`  | Not started but sufficient time remaining                    | Expected to complete on time          |
| `unknown`          | Cannot determine (missing data)                              | Status unclear                        |

- **Capacity Severity Levels**:

| Severity    | Condition                        | Description                              | Action Required                    |
| ----------- | -------------------------------- | ---------------------------------------- | ---------------------------------- |
| `normal`    | Within 1-mold capacity           | Production on track                      | None                               |
| `high`      | Exceeds avg capacity             | Need parallel molds or extended shifts   | Deploy additional resources        |
| `critical`  | Exceeds total capacity           | Cannot complete with current resources   | Reschedule or outsource production |

- **Main Methods**:

| Method                                                            | Description                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `product_record_processing()`                                     | Main pipeline: validates parameters, filters data, calculates capacities, analyzes orders, generates summary.      |
| `_validate_analysis_parameters()`                                 | Validates and adjusts analysis date and record year based on available data and business rules.                    |
| `_detect_backlog(record_year, analysis_timestamp, product_records)` | Identifies orders with ETA before target year that remain unfinished (backlog detection).                          |
| `_calculate_backlog_quantity(backlog_df, product_records, cutoff, analysis)` | Recalculates backlog quantities using latest production data between cutoff and analysis dates.                    |
| `_filter_data(record_year, analysis_timestamp)`                   | Filters purchase orders for target year, merges with production status, and combines with backlog.                 |
| `_compute_mold_capacity(df, mold_col, mold_num_col)`              | Calculates production capacity based on mold specifications (cavity × cycle time).                                 |
| `_estimate_item_capacity()`                                       | Estimates capacity for not-started orders using available mold list per item.                                      |
| `_calculate_mold_capacity(in_progress_df)`                        | Calculates capacity for in-progress orders using actual mold history.                                              |
| `_create_item_code_name(df)`                                      | Creates combined item identifier: `"itemCode(itemName)"`.                                                          |
| `_process_pro_status(product_records_df)`                         | Aggregates production records per PO (date range, total quantity, mold usage).                                     |
| `_merge_purchase_status(purchase_orders, product_records)`        | Merges purchase orders with production data, determines completion and ETA status.                                 |
| `_analyze_unfinished_pos(unfinished_df, analysis_timestamp)`      | Analyzes unfinished orders: calculates cumulative loads, estimates lead times, detects capacity warnings.          |
| `_log_analysis_summary(...)`                                      | Generates formatted analysis summary with order counts, completion rates, capacity warnings.                       |
| `_log_validation_summary(...)`                                    | Generates formatted validation summary showing requested vs adjusted parameters.                                   |

- **Data flow**:
  
    - Initialize → Load 4 DataFrames (`productRecords`, `purchaseOrders`, `moldInfo`, `moldSpecificationSummary`)
    - Validate parameters → `_validate_analysis_parameters()`
      - Check temporal consistency
      - Adjust dates if needed
      - Generate validation summary
    - Filter data → `_filter_data()`
      - Filter POs by record_year (based on poETA year)
      - Detect backlog → `_detect_backlog()`
      - Recalculate backlog quantities → `_calculate_backlog_quantity()`
      - Merge with production status
    - Calculate remaining quantities → `itemRemainQuantity = itemQuantity - itemGoodQuantity`
    - Classify order status → finished / in_progress / not_started
    - Identify overproduction → `overproduction_quantity = abs(itemRemainQuantity)` if negative
    - Split by status:
      - → `finished_df`: Calculate ETA status
      - → `in_progress_df` + `not_started_df`:
        - Estimate capacities → `_estimate_item_capacity()` / `_calculate_mold_capacity()`
        - Merge capacity data
        - Analyze → `_analyze_unfinished_pos()`
          - Calculate cumulative quantities per mold
          - Estimate lead times
          - Detect capacity warnings
          - Classify ETA status and severity
    - Generate summary → `_log_analysis_summary()`

- **Capacity Calculation Formula**:

```python
# Per-mold hourly capacity
moldMaxHourCapacity = (3600 / moldSettingCycle) × moldCavityStandard

# Total capacity (all molds combined)
totalItemCapacity = sum(moldMaxHourCapacity for all molds)

# Average capacity (per mold)
avgItemCapacity = totalItemCapacity / moldNum

# Estimated lead time (days)
estimatedLeadtime = accumulatedQuantity / capacity / 24
```

- **Backlog Detection Logic**:

```python
# Cutoff date = last day before record_year starts
cutoff_date = record_year_start - 1 day

# Backlog orders criteria:
# 1. poETA <= cutoff_date (expected before target year)
# 2. proStatus != 'finished' (not completed yet)
# 3. Has production history during analysis period

# Recalculate backlog quantities:
remaining_backlog_qty = original_order_qty - qty_produced_before_cutoff
current_good_qty = qty_produced_between_cutoff_and_analysis
current_ng_qty = total_qty - current_good_qty
itemRemainQuantity = remaining_backlog_qty - current_good_qty
```

- **Overproduction Tracking**:

```python
# Detect overproduction cases
overproduction_quantity = abs(itemRemainQuantity) if itemRemainQuantity < 0 else 0

# When itemRemainQuantity < 0, it indicates:
# - Production exceeded the ordered quantity
# - The absolute value represents excess production
# - Still classified as 'finished' status
```

- **Unfinished Orders Analysis Output**:

```python
# Key calculated fields:
accumulatedQuantity      # Cumulative remaining qty per mold group
accumulatedRate          # Progress ratio (0-1) within mold group
completionProgress       # PO completion percentage
totalRemainByMold        # Total remaining qty for all POs using same mold

# Capacity estimates:
totalEstimatedLeadtime   # Days needed using all molds
avgEstimatedLeadtime     # Days needed using avg 1 mold
totalCumsumLT            # Cumulative leadtime across PO queue (total capacity)
avgCumsumLT              # Cumulative leadtime across PO queue (avg capacity)

# Timing analysis:
poOTD                    # Order-to-Delivery time (poETA - poReceivedDate)
poRLT                    # Remaining Lead Time (poETA - analysis_timestamp)

# Risk flags:
overTotalCapacity        # Exceeds total mold capacity
overAvgCapacity          # Exceeds average mold capacity
is_overdue               # Past ETA or insufficient time
capacityWarning          # Any capacity constraint detected
capacitySeverity         # normal / high / critical
etaStatus                # ontime / late / expected_ontime / unknown
```

- **Summary Output Structure**:

```text
============================================================
VALIDATION SUMMARY
============================================================
Record year (requested): 2024
Analysis date (validated): 2024-12-31
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
Unique months in poETA: ['2024-01', '2024-02', '2024-03', ...]
------------------------------
MONTHLY PRODUCTION PROGRESS
- ETA period: 2024-01 (BACKLOG): Production progress: 8,000/10,000 (80.00%)
  Finished POs: 5/8 (62.50%)
  In-progress POs: 2/8 (25.00%)
  Not-start POs: 1/8 (12.50%)
- ETA period: 2024-02: Production progress: 12,000/15,000 (80.00%)
  Finished POs: 7/10 (70.00%)
  In-progress POs: 3/10 (30.00%)
  Not-start POs: 0/10 (0.00%)
[... continues for each month ...]
============================================================
```

- **Error handling**:
  
    - `FileNotFoundError`: Raised when required data files not found in path annotations.
    - `KeyError`: Raised when required columns missing from DataFrames.
    - `ValueError`: Raised for invalid date formats, future year analysis, or no historical data.
    - Date adjustment: Automatically adjusts to latest available date with detailed logging.
    - Missing data handling: Uses safe aggregation with null checks.
    - Capacity calculation protection: Guards against division by zero in cycle time calculations.
    - Backlog recalculation: Handles missing production data gracefully.

- **Key Assumptions**:
  
    - **24-hour operation**: Lead time calculations assume continuous production.
    - **Constant cycle time**: Uses mold specification cycle time (no degradation).
    - **Sequential processing**: Orders processed in queue order per mold group.
    - **No setup time**: Mold changes assumed instantaneous in capacity estimates.
    - **Overproduction allowed**: `itemRemainQuantity` can be negative.
    - **Yearly granularity**: Analysis performed at year level with monthly breakdowns.

- **Differences from MonthLevelDataProcessor**:

| Aspect                  | YearLevelDataProcessor                           | MonthLevelDataProcessor                          |
| ----------------------- | ------------------------------------------------ | ------------------------------------------------ |
| **Time Granularity**    | Analyzes full year with monthly breakdowns       | Analyzes single month                            |
| **Date Format**         | `record_year: "YYYY"`                            | `record_month: "YYYY-MM"`                        |
| **Cutoff Calculation**  | Last day of previous year                        | Last day of previous month                       |
| **Period Type**         | `pd.Period(freq="Y")`                            | `pd.Period(freq="M")`                            |
| **Backlog Scope**       | Orders from all previous years                   | Orders from previous months                      |
| **Summary Output**      | Includes monthly breakdown within year           | Single month analysis only                       |
| **Overproduction**      | Explicitly tracked with `overproduction_quantity`| Handled via negative `itemRemainQuantity`        |
| **Use Case**            | Strategic planning, annual performance review    | Operational tracking, monthly targets            |