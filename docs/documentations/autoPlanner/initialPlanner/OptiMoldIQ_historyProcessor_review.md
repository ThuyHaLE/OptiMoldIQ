# HistoryProcessor Documentation

## Overview

The `HistoryProcessor` is designed to process historical production data for evaluating mold performance and generating priority matrices for optimal mold-machine allocation in manufacturing processes.

---

## Main Functions

### 1. Mold Stability Evaluation
- Analyzes mold stability based on the number of active cavities and actual cycle time
- Applies criteria such as accuracy, consistency, compliance with standard limits, and data completeness
- Calculates key indicators: theoretical output, actual output, efficiency, and normalized productivity

### 2. Mold-Machine Priority Matrix Generation
- Uses historical production data to assess the performance of each mold-machine pair
- Scores each pair based on historical weight and actual efficiency
- Results are presented as a priority matrix to support optimal production planning

---

## Initialization

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Path to the data source directory containing parquet files |
| `annotation_name` | str | `"path_annotations.json"` | Name of the JSON file containing path annotations |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Path to database schema configuration file |
| `folder_path` | str | `'agents/shared_db/OrderProgressTracker'` | Path to folder containing change log for production status |
| `target_name` | str | `"change_log.txt"` | Name of the change log file to read production status from |
| `default_dir` | str | `"agents/shared_db"` | Default directory for output files |
| `efficiency` | float | `0.85` | Expected efficiency coefficient (85%) |
| `loss` | float | `0.03` | Expected loss coefficient (3%) |

### Initialization Example

```python
processor = HistoryProcessor(
    source_path='data/production_records',
    efficiency=0.80,
    loss=0.05
)
```

---

## Configuration Constants

### Cavity Stability Weights

```python
CAVITY_STABILITY_WEIGHTS = {
    'accuracy_rate_weight': 0.4,        # 40% - Accuracy rate
    'consistency_score_weight': 0.3,    # 30% - Consistency score
    'utilization_rate_weight': 0.2,     # 20% - Utilization rate
    'data_completeness_weight': 0.1     # 10% - Data completeness
}
```

### Cycle Stability Weights

```python
CYCLE_STABILITY_WEIGHTS = {
    'accuracy_score_weight': 0.3,       # 30% - Accuracy score
    'consistency_score_weight': 0.25,   # 25% - Consistency score
    'range_compliance_weight': 0.25,    # 25% - Range compliance
    'outlier_penalty_weight': 0.1,      # 10% - Outlier penalty
    'data_completeness_weight': 0.1     # 10% - Data completeness
}
```

### Thresholds and Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `SECONDS_PER_HOUR` | 3600 | Seconds in one hour |
| `CYCLE_TIME_TOLERANCE` | 0.2 | Cycle time tolerance (±20%) |
| `EXTREME_DEVIATION_THRESHOLD` | 1.0 | Extreme deviation threshold (100%) |

---

## Main Methods

### 1. calculate_mold_stability_index()

**Purpose:** Calculate stability indices for molds based on historical data

**Parameters:**
- `cavity_stability_threshold` (float, default=0.6): Weight threshold for cavity stability
- `cycle_stability_threshold` (float, default=0.4): Weight threshold for cycle stability  
- `total_records_threshold` (int, default=30): Minimum number of records threshold

**Returns:** `pandas.DataFrame` with columns:

| Column | Type | Description |
|--------|------|-------------|
| `moldNo` | str | Mold number identifier |
| `moldName` | str | Mold name |
| `cavityStabilityIndex` | float | Cavity stability index (0-1) |
| `cycleStabilityIndex` | float | Cycle stability index (0-1) |
| `theoreticalMoldHourCapacity` | float | Theoretical capacity per hour |
| `effectiveMoldHourCapacity` | float | Effective capacity per hour |
| `estimatedMoldHourCapacity` | float | Estimated capacity per hour |
| `balancedMoldHourCapacity` | float | Balanced capacity per hour |
| `totalRecords` | int | Total number of records |
| `totalCavityMeasurements` | int | Total cavity measurements |
| `totalCycleMeasurements` | int | Total cycle measurements |
| `firstRecordDate` | datetime | First record date |
| `lastRecordDate` | datetime | Last record date |

**Usage Example:**
```python
stability_results = processor.calculate_mold_stability_index(
    cavity_stability_threshold=0.7,
    cycle_stability_threshold=0.5,
    total_records_threshold=50
)
```

### 2. calculate_mold_machine_priority_matrix()

**Purpose:** Generate priority matrix for mold-machine allocation

**Parameters:**
- `mold_machine_feature_weights` (pandas.Series): Feature weights for scoring
- `capacity_mold_info_df` (pandas.DataFrame): Mold capacity information DataFrame

**Returns:** `pandas.DataFrame` - Priority matrix with:
- Rows: Mold numbers (moldNo)
- Columns: Machine codes (machineCode)  
- Values: Priority rankings (1 = highest priority)

**Usage Example:**
```python
# Prepare feature weights
weights = pd.Series({
    'shiftNGRate': 0.25,
    'shiftCavityRate': 0.25,
    'shiftCycleTimeRate': 0.25,
    'shiftCapacityRate': 0.25
})

priority_matrix = processor.calculate_mold_machine_priority_matrix(
    weights, 
    mold_capacity_data
)
```

### 3. Save Methods

#### calculate_and_save_mold_stability_index()
Calculates and saves mold stability index to Excel file with automatic versioning.

#### calculate_and_save_mold_machine_priority_matrix()
Calculates and saves priority matrix to Excel file with automatic versioning.

---

## Calculation Formulas

### Cavity Stability Index

```
cavity_stability = (accuracy_rate × 0.4) + 
                  (consistency_score × 0.3) + 
                  (utilization_rate × 0.2) + 
                  (data_completeness × 0.1)
```

Where:
- **accuracy_rate**: Proportion of actual cavities matching standard
- **consistency_score**: 1 - (std_dev / mean) of cavity values
- **utilization_rate**: average_cavity / standard_cavity
- **data_completeness**: min(1.0, total_records / threshold)

### Cycle Stability Index

```
cycle_stability = (accuracy_score × 0.3) + 
                 (consistency_score × 0.25) + 
                 (range_compliance × 0.25) + 
                 (outlier_penalty × 0.1) + 
                 (data_completeness × 0.1)
```

Where:
- **accuracy_score**: 1 - average_deviation_from_standard
- **consistency_score**: 1 - coefficient_of_variation
- **range_compliance**: proportion_within_20%_tolerance
- **outlier_penalty**: 1 - proportion_of_extreme_outliers
- **data_completeness**: min(1.0, total_records / threshold)

### Capacity Calculations

```python
# Theoretical capacity
theoretical_capacity = 3600 / standard_cycle × standard_cavity

# Effective capacity  
effective_capacity = theoretical_capacity × overall_stability

# Estimated capacity
estimated_capacity = theoretical_capacity × (efficiency - loss)

# Balanced capacity
alpha = max(0.1, min(1.0, total_records / threshold))
balanced_capacity = alpha × effective_capacity + (1-alpha) × estimated_capacity
```

---

## Data Structure Requirements

### Required Input Data

#### productRecords_df
- `moldNo`: Mold identifier
- `recordDate`: Record date
- `moldShot`: Number of mold shots
- `moldCavity`: Actual cavity count
- `itemTotalQuantity`: Total production quantity
- `itemGoodQuantity`: Good production quantity

#### moldInfo_df  
- `moldNo`: Mold identifier
- `moldName`: Mold name
- `moldCavityStandard`: Standard cavity count
- `moldSettingCycle`: Set cycle time
- `machineTonnage`: Machine tonnage requirement

#### machineInfo_df
- `machineNo`: Machine number
- `machineCode`: Machine code  
- `machineName`: Machine name
- `machineTonnage`: Machine tonnage capacity

#### proStatus_df
Required columns (validated by decorator):
```python
['poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
 'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate',
 'proStatus', 'etaStatus', 'machineHist', 'itemType', 'moldList',
 'moldHist', 'moldCavity', 'totalMoldShot', 'totalDay', 'totalShift',
 'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
 'moldShotMap', 'machineQuantityMap', 'dayQuantityMap',
 'shiftQuantityMap', 'materialComponentMap', 'lastestRecordTime',
 'machineNo', 'moldNo', 'warningNotes']
```

---

## Error Handling

### Exception Types

1. **FileNotFoundError**: When required data files are missing
2. **Schema Validation Error**: When DataFrames don't have required columns
3. **Data Processing Error**: When errors occur during data processing

### Logging

The class uses `loguru` for detailed logging:
- **DEBUG**: DataFrame shape and column information
- **INFO**: Processing progress notifications
- **ERROR**: Error messages and debug information

### Validation Decorators

The class uses two validation decorators:

1. **@validate_init_dataframes**: Validates schema compliance for core DataFrames
2. **@validate_init_dataframes**: Additional validation for production status DataFrame

---

## Best Practices

### 1. Data Preparation
```python
# Ensure sufficient records for analysis
min_records = 30  # Minimum 30 records per mold

# Filter meaningful data
meaningful_data = data[data['moldShot'] > 0]

# Check for required columns
required_cols = ['moldNo', 'recordDate', 'moldShot', 'moldCavity']
assert all(col in data.columns for col in required_cols)
```

### 2. Weight Configuration
```python
# Adjust weights based on business requirements
custom_weights = pd.Series({
    'shiftNGRate': 0.3,          # Higher weight for NG rate
    'shiftCavityRate': 0.2,
    'shiftCycleTimeRate': 0.3,   # Higher weight for cycle time
    'shiftCapacityRate': 0.2
})
```

### 3. Data Validation
```python
# Validate data before processing
assert not df.empty, "DataFrame cannot be empty"
assert 'moldNo' in df.columns, "Missing moldNo column"
assert df['moldShot'].sum() > 0, "No meaningful production data"
```

---

## Complete Usage Example

```python
# 1. Initialize processor
processor = HistoryProcessor(
                source_path = 'agents/shared_db/DataLoaderAgent/newest',
                annotation_name = "path_annotations.json",
                databaseSchemas_path = 'database/databaseSchemas.json',
                folder_path = 'agents/shared_db/OrderProgressTracker',
                target_name = "change_log.txt",
                default_dir = "agents/shared_db",
                efficiency = 0.85,
                loss = 0.03,
                )

# 2. Calculate mold stability index
stability_results = processor.calculate_mold_stability_index(
    cavity_stability_threshold=0.6,
    cycle_stability_threshold=0.4,
    total_records_threshold=30
)

# 3. Prepare feature weights for priority matrix
feature_weights = pd.Series({
    'shiftNGRate': 0.25,
    'shiftCavityRate': 0.25,
    'shiftCycleTimeRate': 0.25,
    'shiftCapacityRate': 0.25
})

# 4. Calculate priority matrix
priority_matrix = processor.calculate_mold_machine_priority_matrix(
    feature_weights,
    stability_results
)

# 5. Save results with automatic versioning
processor.calculate_and_save_mold_stability_index()
processor.calculate_and_save_mold_machine_priority_matrix(
    feature_weights,
    stability_results
)

# 6. Access results
print(f"Analyzed {len(stability_results)} molds")
print(f"Priority matrix shape: {priority_matrix.shape}")
```

---

## Troubleshooting

### Common Issues

1. **"Path not found"**
   - Verify file paths are correct
   - Ensure annotation JSON file exists
   - Check file permissions

2. **"Missing columns"**  
   - Verify DataFrame schema matches requirements
   - Ensure all required columns are present
   - Check column name spelling and case

3. **"Invalid mold standard"**
   - Check moldCavityStandard and moldSettingCycle > 0
   - Clean data before processing
   - Handle missing or null values

4. **"Insufficient data"**
   - Ensure minimum record thresholds are met
   - Filter for meaningful production data (moldShot > 0)
   - Check date ranges for historical data

### Performance Tips

1. **Filter early**: Remove unnecessary records before processing
2. **Use chunking**: Process large datasets in batches
3. **Cache results**: Save intermediate results to avoid recalculation
4. **Optimize data types**: Use appropriate dtypes for memory efficiency

### Debug Information

Enable debug logging to get detailed information:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")

# Initialize with debug info
processor = HistoryProcessor(source_path='data/production')
```

---

## Performance Characteristics

### Time Complexity
- **Mold Stability Calculation**: O(n × m) where n = molds, m = average records per mold
- **Priority Matrix Generation**: O(p × q) where p = molds, q = machines

### Memory Usage
- Loads all required DataFrames into memory
- Peak memory usage depends on dataset size
- Consider chunked processing for very large datasets

### Scalability Considerations
- Suitable for datasets up to millions of production records
- For larger datasets, consider distributed processing
- Memory usage scales linearly with data size