# MoldMachinePriorityMatrixCalculator

## 1. Overview

`MoldMachinePriorityMatrixCalculator` is a manufacturing analytics component that creates optimal mold-machine assignment recommendations based on historical production performance and weighted scoring algorithms.

It ensures:
- Analysis of **historical production data** for completed orders.
- Calculation of **performance metrics** for each mold-machine combination.
- Application of **weighted scoring** based on multiple performance factors.
- Generation of **priority rankings** to support optimal production planning.

---

## 2. Class: `MoldMachinePriorityMatrixCalculator`

### 2.1 Initialization

```python
calculator = MoldMachinePriorityMatrixCalculator(
    mold_machine_feature_weights=...,
    mold_estimated_capacity_df=...,
    databaseSchemas_data=...,
    sharedDatabaseSchemas_data=...,
    source_path='agents/shared_db/DataLoaderAgent/newest',
    efficiency=0.85,
    loss=0.03
)
```

- `mold_machine_feature_weights`: Series containing weights for performance metrics.
- `mold_estimated_capacity_df`: Estimated capacity data for each mold.
- `databaseSchemas_data`: Database schema for validation of core DataFrames.
- `sharedDatabaseSchemas_data`: Shared database schema for validation.
- `source_path`: Path to parquet files containing historical data.
- `efficiency`: Production efficiency factor (default: 0.85).
- `loss`: Production loss factor (default: 0.03).

**Validation**:
- Uses decorators to enforce schema integrity for all DataFrames.
- Validates required columns: `shiftNGRate`, `shiftCavityRate`, `shiftCycleTimeRate`, `shiftCapacityRate`.
- Checks data consistency and accessibility at initialization.

### 2.2 Main Methods

`process() -> Tuple[pd.DataFrame, List[str]]`

- Prepares historical data from completed production orders.
- Calculates performance metrics for each mold-machine combination.
- Applies weighted scoring based on feature weights.
- Creates priority matrix with rankings (1 = highest priority).
- Returns invalid molds that couldn't be processed.

**Output Example**

```python
priority_matrix, invalid_molds = calculator.process()
# priority_matrix: DataFrame with moldNo as index, machineCode as columns, rankings as values
# invalid_molds: List of mold numbers that couldn't be processed
```

`process_and_save_result() -> None`

- Executes the full calculation pipeline.
- Saves results to Excel file with automatic versioning.
- Exports both priority matrix and invalid molds list.

---

### 2.3 Processing Steps

#### `_load_dataframes()`
- Loads required DataFrames from parquet files:
  - `productRecords_df`: Historical production records
  - `machineInfo_df`: Machine specifications and capabilities
  - `moldInfo_df`: Detailed mold information
- Validates file existence and accessibility.
- Provides detailed logging for debugging.

#### `_prepare_mold_machine_historical_data()`
- Filters to completed orders (`itemRemain == 0`).
- Merges machine information with production status.
- Filters meaningful production data (`itemTotalQuantity > 0`).
- Standardizes column names for consistency.

#### `summarize_mold_machine_history()` (from core_helpers)
- Analyzes performance of each mold-machine pair.
- Calculates key metrics:
  - `shiftNGRate`: Defect rate performance
  - `shiftCavityRate`: Cavity utilization efficiency  
  - `shiftCycleTimeRate`: Cycle time performance
  - `shiftCapacityRate`: Overall capacity utilization

#### `_create_mold_machine_priority_matrix()`
- Applies weighted scoring:
  - `total_score = (metrics × weights).sum()`
- Creates pivot table: molds as rows, machines as columns
- Converts scores to priority rankings using `rank_nonzero()`
- Handles zero values appropriately (no ranking assigned)

---

### 2.4 Helper Methods

- `_check_series_columns(series)` → Validates feature weights Series structure.
- `_check_mold_dataframe_columns(df)` → Ensures mold DataFrame has required columns.
- Path annotation loading for flexible data source configuration.
- Comprehensive error handling with detailed logging.

---

## 3. Data Safety & Performance

- **DataFrame validation** enforced through decorators before processing.
- **Parquet format** used for efficient data loading and storage.
- **Vectorized operations** for performance optimization.
- **Path annotations** allow flexible configuration without code changes.
- **Versioned outputs** prevent accidental data overwrites.

---

## 4. Error Handling

- Missing or inaccessible data files trigger detailed error messages.
- Schema validation failures are logged with specific missing columns.
- Invalid molds are tracked separately and reported in results.
- Comprehensive try-catch blocks with context-aware logging.
- Graceful handling of edge cases in ranking calculations.

---

## 5. Output & Reporting

**Priority Matrix**:
- **Rows**: Mold numbers (`moldNo`)
- **Columns**: Machine codes (`machineCode`)
- **Values**: Priority rankings (1 = highest priority, 0 = not suitable)

**Invalid Molds**:
- List of mold numbers that couldn't be processed due to data issues.

**Export Format**:
- Excel file with automatic versioning
- Separate sheets for priority matrix and invalid molds
- Saved in configured output directory with timestamp

---

## 6. Usage & Integration

- **Production Planning**: Provides data-driven machine assignment recommendations.
- **Resource Optimization**: Identifies best-performing mold-machine combinations.
- **Continuous Improvement**: Updates automatically as new historical data becomes available.
- **Integration Ready**: Can be extended to include real-time machine availability or shift-specific factors.

---

## 7. Configuration Constants

```python
ESTIMATED_MOLD_REQUIRED_COLUMNS = [
    'moldNo', 'moldName', 'acquisitionDate', 'machineTonnage',
    'moldCavityStandard', 'moldSettingCycle', 'cavityStabilityIndex',
    'cycleStabilityIndex', 'theoreticalMoldHourCapacity',
    'effectiveMoldHourCapacity', 'estimatedMoldHourCapacity',
    'balancedMoldHourCapacity', 'totalRecords', 'totalCavityMeasurements',
    'totalCycleMeasurements', 'firstRecordDate', 'lastRecordDate',
    'itemCode', 'itemName', 'itemType', 'moldNum', 'isPriority'
]

FEATURE_WEIGHTS_REQUIRED_COLUMNS = [
    'shiftNGRate', 'shiftCavityRate', 'shiftCycleTimeRate', 'shiftCapacityRate'
]
```
These constants ensure data consistency and provide clear requirements for input DataFrames.