# HistBasedItemMoldOptimizer Documentation

## Overview

The `HistBasedItemMoldOptimizer` is designed to optimize mold production capacity based on historical data. This optimizer can calculate theoretical and estimated production capacities, identify unused molds, and assign priority molds for each item code.

## Core Methods

### 1. `compute_hourly_capacity()`

**Purpose**: Calculate mold production capacity per hour

```python
@staticmethod
def compute_hourly_capacity(df: pd.DataFrame, efficiency: float, loss: float) -> pd.DataFrame
```

**Parameters**:
- `df`: DataFrame containing mold information with columns:
  - `moldSettingCycle`: Mold setting cycle time (seconds)
  - `moldCavityStandard`: Number of standard cavities
- `efficiency`: Production efficiency factor (0.0 to 1.0)
- `loss`: Production loss factor (0.0 to 1.0)

**Returns**: Updated DataFrame with capacity calculations

**Calculation Formulas**:
```
theoreticalMoldHourCapacity = (3600 / moldSettingCycle) * moldCavityStandard
estimatedMoldHourCapacity = theoreticalMoldHourCapacity * (efficiency - loss)
balancedMoldHourCapacity = estimatedMoldHourCapacity
```

**Error Handling**:
- Replaces 0, inf, -inf values with NaN
- Ensures estimated capacity is non-negative
- Rounds results to 2 decimal places

### 2. `merge_with_unused_molds()`

**Purpose**: Merge unused molds data with used molds data

```python
@staticmethod
def merge_with_unused_molds(
    moldInfo_df: pd.DataFrame,
    unused_molds: List[str],
    used_molds_df: pd.DataFrame,
    efficiency: float,
    loss: float
) -> pd.DataFrame
```

**Parameters**:
- `moldInfo_df`: Complete mold information DataFrame
- `unused_molds`: List of unused mold numbers
- `used_molds_df`: DataFrame of historically used molds
- `efficiency`: Production efficiency factor
- `loss`: Production loss factor

**Processing Flow**:
1. Calculate capacity for all molds
2. Filter unused molds
3. Create compatible DataFrame structure
4. Combine used and unused molds data

### 3. `assign_priority_mold()`

**Purpose**: Mark the mold with highest capacity for each item code

```python
@staticmethod
def assign_priority_mold(df: pd.DataFrame) -> pd.DataFrame
```

**Priority Criteria**:
1. **Primary**: Mold with highest capacity (`balancedMoldHourCapacity`)
2. **Secondary**: In case of tie, select mold with latest acquisition date (`acquisitionDate`)

**Added Column**: `isPriority` (Boolean)

**Special Case Handling**:
- NaN or ≤ 0 capacity: Select first mold as fallback
- Invalid acquisition dates: Select first mold in group

### 4. `process_mold_info()` - Main Method

**Purpose**: Process and combine mold information from multiple data sources

```python
def process_mold_info(
    self,
    used_molds_df: pd.DataFrame,
    moldSpecificationSummary_df: pd.DataFrame,
    moldInfo_df: pd.DataFrame,
    efficiency: float,
    loss: float
) -> pd.DataFrame
```

**Parameters**:
- `used_molds_df`: Historical mold usage data
- `moldSpecificationSummary_df`: Summary table mapping product codes to mold lists
- `moldInfo_df`: Detailed table with mold technical information
- `efficiency`: Production efficiency factor (0.0-1.0)
- `loss`: Production loss factor (0.0-1.0)

**Processing Workflow**:

1. **Input Data Validation**
   ```python
   if moldSpecificationSummary_df.empty or moldInfo_df.empty:
       return pd.DataFrame()
   ```

2. **Invalid Molds Analysis**
   - Find molds in historical data but not in moldInfo
   - Log for review and database updates

3. **Unused Molds Analysis**
   - Find molds in moldInfo but never used historically
   - Log count and list for tracking

4. **Data Merge and Capacity Calculation**
   - Call `merge_with_unused_molds()` to combine data
   - Calculate capacity for all molds

5. **MoldList Processing**
   ```python
   # Safe processing of moldList column
   moldSpec_df['moldList'] = moldSpec_df['moldList'].fillna('').astype(str)
   moldSpec_df['moldList'] = moldSpec_df['moldList'].str.split('/')
   moldSpec_df_exploded = moldSpec_df.explode('moldList', ignore_index=True)
   ```

6. **Data Merging**
   - Combine specification data with detailed mold information
   - Use left join to preserve all specifications

7. **Priority Assignment**
   - Call `assign_priority_mold()` to mark priority molds

**Returns**: Tuple `(invalid_molds, result_df)`
- `invalid_molds`: List of invalid molds requiring review
- `result_df`: Complete result DataFrame with priority indicators

## Data Structures

### Input DataFrames

**moldInfo_df** (Detailed mold information):
- `moldNo`: Mold number
- `moldName`: Mold name
- `acquisitionDate`: Acquisition date
- `machineTonnage`: Machine tonnage
- `moldCavityStandard`: Number of standard cavities
- `moldSettingCycle`: Setting cycle time (seconds)

**moldSpecificationSummary_df** (Specification summary):
- `itemCode`: Item/product code
- `moldList`: List of molds (separated by '/')

**used_molds_df** (Historical usage data):
- Similar structure to moldInfo_df
- Contains molds that have been used historically

### Output DataFrame

**result_df** (Final result):
- All columns from input DataFrames
- `theoreticalMoldHourCapacity`: Theoretical capacity per hour
- `estimatedMoldHourCapacity`: Estimated capacity per hour  
- `balancedMoldHourCapacity`: Balanced capacity per hour
- `isPriority`: Priority mold indicator (Boolean)

## Logging and Monitoring

The class uses `loguru` for comprehensive logging:

```python
self.logger = logger.bind(class_="HistBasedItemMoldOptimizer")
```

**Logged Events**:
- Invalid molds requiring review
- Unused molds never utilized
- Efficiency and loss parameters
- Process completion status
- Missing required columns errors

## Exception Handling

**ValueError**: Raised when required columns are missing
```python
if missing_cols:
    logger.error("Missing required columns: {}", missing_cols)
    raise ValueError(f"Missing required columns: {missing_cols}")
```

**Warnings Suppression**: Ignores calculation warnings to reduce noise
```python
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    # Calculations here
```

## Usage Example

```python
# Initialize optimizer
optimizer = HistBasedItemMoldOptimizer()

# Process mold data
invalid_molds, result_df = optimizer.process_mold_info(
    used_molds_df=historical_data,
    moldSpecificationSummary_df=spec_summary,
    moldInfo_df=mold_details,
    efficiency=0.85,
    loss=0.05
)

# Check results
print(f"Found {len(invalid_molds)} invalid molds")
print(f"Processed {len(result_df)} mold-item combinations")

# Filter priority molds
priority_molds = result_df[result_df['isPriority'] == True]
```

## Best Practices

1. **Input Data Validation**: Ensure DataFrames are not empty and contain required columns

2. **Handle Missing Values**: Class automatically handles NaN, but pre-validation is recommended

3. **Monitor Logs**: Track logs to identify invalid molds and required updates

4. **Reasonable Parameters**: 
   - `efficiency`: Typically 0.7-0.9
   - `loss`: Typically 0.05-0.15
   - Ensure `efficiency > loss` for positive capacity

5. **Result Processing**: Review invalid_molds for database updates

## Limitations and Notes

- Class assumes moldList is delimited by '/' character
- Only handles time units in seconds
- No validation of efficiency - loss logic
- Requires acquisitionDate in valid datetime format
- Static method design allows for independent usage but requires careful parameter management

## Performance Considerations

- Efficient pandas operations for large datasets
- Memory-conscious processing with copy() operations where needed
- Vectorized calculations for capacity computations
- Optimized groupby operations for priority assignment