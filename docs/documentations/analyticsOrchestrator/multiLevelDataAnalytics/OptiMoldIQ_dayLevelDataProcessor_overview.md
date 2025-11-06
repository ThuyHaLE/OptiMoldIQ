# DayLevelDataProcessor

- **Purpose**:
  
    - Process and analyze daily production records to generate comprehensive reports on manufacturing operations.
    - Aggregate production data by mold and item to track performance metrics.
    - Classify production changes (mold changes, color changes, machine idle states).
    - Calculate defect rates and efficiency metrics across machines, shifts, and products.

- **Core responsibilities**:
  
    - Load and validate production records and purchase order data.
    - Filter data by specific record date or use the latest available date.
    - Merge production records with purchase order information.
    - Create composite information fields (machineInfo, itemInfo, itemComponent).
    - Calculate count metrics (items, molds, components) by machine and shift.
    - Compute job metrics including job counts and late delivery status.
    - Classify change types in production flow.
    - Generate mold-based and item-based aggregated reports.
    - Produce summary statistics for daily operations.

- **Input**:
  
    - `productRecords_df`: Production records DataFrame containing machine operations, items, quantities, and components.
    - `purchaseOrders_df`: Purchase orders DataFrame with order details, quantities, and ETAs.
    - `record_date` (optional): Specific date to process (YYYY-MM-DD format). If None, uses latest available date.
    - `source_path`: Path to data source directory.
    - `databaseSchemas_path`: Path to database schema JSON file.

- **Output**:
  
    - `merged_df`: Enriched production records with calculated metrics and classifications.
    - `mold_based_record_df`: Aggregated report by mold showing performance per machine/shift/mold.
    - `item_based_record_df`: Aggregated report by item showing total production across all machines.
    - `summary_stats`: Dictionary containing daily operation statistics and KPIs.

- **Class Constants**:

| Constant           | Value                                                                           | Description                                      |
| ------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| `GROUP_COLS`       | `['machineInfo', 'workingShift']`                                               | Columns used for grouping operations             |
| `COMPONENT_COLS`   | `['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']`       | Material component columns                       |
| `COUNT_CONFIGS`    | `{'itemCount': 'itemInfo', 'moldCount': 'moldNo', 'itemComponentCount': ...}`   | Configuration for counting distinct entities     |
| `REQUIRED_CONFIGS` | `{'mold': [...], 'item': [...]}`                                                | Required columns for mold-based and item reports |

- **Main Methods**:

| Method                                              | Description                                                                                                      |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `product_record_processing()`                       | Main processing pipeline: filters data, merges POs, calculates metrics, classifies changes, generates reports.   |
| `generate_summary_stats(merged_df, record_date)`    | Generates comprehensive statistics including active jobs, machines, products, molds, and late orders.            |
| `_classify_change(row)`                             | Classifies production change type: mold&color change, mold change, color change, machine idle, or no change.    |
| `_create_info_fields(df)`                           | Creates composite fields: machineInfo (machine + code), itemInfo (item + name), itemComponent (material tuple). |
| `_calculate_counts(df)`                             | Calculates distinct counts of items, molds, and components per machine and shift.                               |
| `_calculate_job_metrics(df)`                        | Computes job count per group and late status based on ETA comparison.                                           |
| `_mold_based_processing(record_df, required_fields)` | Aggregates data by mold, handling different change types, calculates defect quantities and rates.               |
| `_item_based_processing(record_df, required_fields)` | Aggregates data by item across all machines, calculates usage statistics and defect metrics.                    |

- **Change Type Classification**:

| Change Type        | Condition                                    | Description                    |
| ------------------ | -------------------------------------------- | ------------------------------ |
| `mold&color_change` | Both `moldChanged` and `colorChanged` exist  | Changed both mold and color    |
| `mold_change`      | Only `moldChanged` exists                    | Changed mold only              |
| `color_change`     | Only `colorChanged` exists                   | Changed color/material only    |
| `machine_idle`     | `jobCount == 0`                              | Machine not running            |
| `no_change`        | None of the above                            | Continuous production run      |

- **Data flow**:
  
    - Load data → `productRecords_df` + `purchaseOrders_df`
    - Filter by date → Latest or specified `record_date`
    - Merge data → Combine production records with purchase orders
    - Enrich data → `_create_info_fields()` creates composite fields
    - Calculate metrics → `_calculate_counts()` + `_calculate_job_metrics()`
    - Classify changes → `_classify_change()` determines production change types
    - Split processing:
      - → `_mold_based_processing()` generates mold-level report
      - → `_item_based_processing()` generates item-level report
    - Generate summary → `generate_summary_stats()` produces KPIs

- **Mold-Based Report Structure**:

```python
# Output columns:
machineInfo         # Machine identifier with code
workingShift        # Shift number
moldNo              # Mold identifier
changeType          # Type of production change
itemTotalQuantity   # Total items produced
itemGoodQuantity    # Good quality items
moldShot            # Number of shots (avg for color_change)
moldCavity          # Number of cavities (avg for color_change)
defectQuantity      # itemTotalQuantity - itemGoodQuantity
defectRate          # (defectQuantity / itemTotalQuantity) * 100
```

- **Item-Based Report Structure**:

```python
# Output columns:
itemInfo            # Item identifier with name
itemTotalQuantity   # Total quantity produced
itemGoodQuantity    # Good quality quantity
usedMachineNums     # Number of distinct machines used
totalShifts         # Total number of shifts
usedMoldNums        # Number of distinct molds used
moldTotalShots      # Sum of all shots
avgCavity           # Average number of cavities
usedComponentNums   # Number of distinct component configurations
defectQuantity      # Total defects
defectRate          # Defect percentage
```

- **Summary Statistics Output**:

```python
{
    'record_date': '2024-01-15',
    'total_records': 150,
    'active_jobs': 45,
    'working_shifts': 3,
    'machines': 12,
    'purchase_orders': 28,
    'products': 18,
    'molds': 15,
    'late_pos': 5,
    'total_pos_with_eta': 25,
    'change_type_distribution': {
        'no_change': 100,
        'color_change': 30,
        'mold_change': 15,
        'machine_idle': 5
    }
}
```

- **Error handling**:
  
    - `FileNotFoundError`: Raised when productRecords or purchaseOrders files not found.
    - `ValueError`: Raised when productRecords_df is empty or missing required columns.
    - Date fallback: Automatically uses latest date if specified date not available.
    - Safe aggregation: Handles null values in groupby operations with `dropna=False`.
    - Missing column warnings: Logs warnings for optional columns (e.g., poETA).
    - Division by zero protection: Uses `np.where()` for defect rate calculation.