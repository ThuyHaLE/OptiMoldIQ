# HistBasedItemMoldOptimizer Documentation

## Overview

The `HistBasedItemMoldOptimizer` is a Python class designed to optimize mold production capacity based on historical manufacturing data. This system analyzes mold specifications, calculates production capacities, identifies unused resources, and assigns priority molds for efficient production planning.

## Key Features

- **Capacity Calculation**: Computes theoretical and estimated production capacities for molds
- **Resource Optimization**: Identifies unused molds and integrates them into production planning
- **Priority Assignment**: Automatically selects the best mold for each item code based on capacity and acquisition date
- **Data Validation**: Robust error handling and data validation throughout the process

## Dependencies

```python
import pandas as pd
import numpy as np
import warnings
from typing import List
from loguru import logger
```

## Class Structure

### Constructor

```python
def __init__(self):
    self.logger = logger.bind(class_="HistBasedItemMoldOptimizer")
```

Initializes the optimizer with a bound logger for tracking operations.

## Methods

### 1. `compute_hourly_capacity(df, efficiency, loss)`

**Purpose**: Calculates mold production capacity per hour based on cycle time and cavity specifications.

**Parameters**:
- `df` (pd.DataFrame): Mold information dataframe containing:
  - `moldSettingCycle`: Cycle time in seconds
  - `moldCavityStandard`: Number of cavities in the mold
- `efficiency` (float): Production efficiency factor (0.0 to 1.0)
- `loss` (float): Production loss factor (0.0 to 1.0)

**Returns**: Updated dataframe with calculated capacity columns:
- `theoreticalMoldHourCapacity`: Maximum theoretical production per hour
- `estimatedMoldHourCapacity`: Realistic production considering efficiency and loss
- `balancedMoldHourCapacity`: Balanced capacity (currently same as estimated)

**Calculations**:
- Theoretical Capacity = (3600 seconds/hour) ÷ (cycle time) × (number of cavities)
- Estimated Capacity = Theoretical Capacity × (efficiency - loss)

**Error Handling**:
- Validates required columns presence
- Handles zero, infinite, and negative values
- Ensures non-negative output values

### 2. `merge_with_unused_molds(moldInfo_df, unused_molds, used_molds_df, efficiency, loss)`

**Purpose**: Integrates unused molds with historically used molds data for comprehensive analysis.

**Parameters**:
- `moldInfo_df` (pd.DataFrame): Complete mold information dataset
- `unused_molds` (List[str]): List of mold numbers that haven't been used historically
- `used_molds_df` (pd.DataFrame): Historical mold usage data
- `efficiency` (float): Production efficiency factor
- `loss` (float): Production loss factor

**Returns**: Combined dataframe containing both used and unused molds with capacity calculations.

**Process**:
1. Calculates capacity for all molds in the master dataset
2. Filters unused molds and matches column structure
3. Combines used and unused molds into a unified dataset

### 3. `assign_priority_mold(df)`

**Purpose**: Identifies and marks the optimal mold for each item code based on production capacity.

**Parameters**:
- `df` (pd.DataFrame): Dataframe with mold information containing:
  - `itemCode`: Product identifier
  - `balancedMoldHourCapacity`: Production capacity per hour
  - `acquisitionDate`: Mold acquisition date

**Returns**: Dataframe with added `isPriority` boolean column indicating the selected mold for each item.

**Selection Logic**:
1. **Primary Criteria**: Highest production capacity
2. **Tiebreaker**: Latest acquisition date (most modern mold)
3. **Fallback**: First available mold if no valid capacity data

**Error Handling**:
- Validates required columns
- Handles missing or invalid dates
- Manages cases with zero or NaN capacity values

### 4. `process_mold_info(used_molds_df, moldSpecificationSummary_df, moldInfo_df, efficiency, loss)`

**Purpose**: Main processing method that orchestrates the complete mold optimization workflow.

**Parameters**:
- `used_molds_df` (pd.DataFrame): Historical mold usage data
- `moldSpecificationSummary_df` (pd.DataFrame): Product-to-mold mapping with:
  - `moldList`: Slash-separated list of compatible molds per product
- `moldInfo_df` (pd.DataFrame): Technical specifications for all molds
- `efficiency` (float): Production efficiency factor (0.0 to 1.0)
- `loss` (float): Production loss factor (0.0 to 1.0)

**Returns**: Tuple containing:
- `invalid_molds` (List): Molds in historical data but missing from master data
- `result_df` (pd.DataFrame): Complete processed dataset with priority assignments

**Workflow**:
1. **Data Validation**: Identifies invalid and unused molds
2. **Capacity Integration**: Merges unused molds with historical data
3. **Specification Processing**: Explodes mold lists and creates product-mold relationships
4. **Data Merging**: Combines specification and technical data
5. **Priority Assignment**: Selects optimal molds for each product

## Usage Example

```python
# Initialize the optimizer
optimizer = HistBasedItemMoldOptimizer()

# Process mold information
invalid_molds, optimized_df = optimizer.process_mold_info(
    used_molds_df=historical_usage_data,
    moldSpecificationSummary_df=product_mold_mapping,
    moldInfo_df=mold_specifications,
    efficiency=0.85,  # 85% efficiency
    loss=0.05         # 5% loss
)

# Review results
print(f"Found {len(invalid_molds)} invalid molds requiring attention")
priority_molds = optimized_df[optimized_df['isPriority'] == True]
print(f"Assigned {len(priority_molds)} priority molds")
```

## Data Requirements

### Input DataFrames Structure

#### `moldInfo_df` (Master Mold Data)
- `moldNo`: Unique mold identifier
- `moldName`: Mold name/description
- `acquisitionDate`: Date of mold acquisition
- `moldCavityStandard`: Number of cavities
- `moldSettingCycle`: Cycle time in seconds
- `machineTonnage`: Machine tonnage requirements

#### `moldSpecificationSummary_df` (Product-Mold Mapping)
- `itemCode`: Product identifier
- `moldList`: Slash-separated list of compatible molds (e.g., "M001/M002/M003")

#### `used_molds_df` (Historical Usage)
- `moldNo`: Mold identifier
- Additional historical usage columns

### Output DataFrame Structure

The processed result includes all input columns plus:
- `theoreticalMoldHourCapacity`: Maximum theoretical production rate
- `estimatedMoldHourCapacity`: Realistic production rate
- `balancedMoldHourCapacity`: Balanced capacity calculation
- `isPriority`: Boolean flag indicating optimal mold selection

## Best Practices

### Parameter Selection
- **Efficiency**: Typically 0.80-0.95 (80-95%) based on historical performance
- **Loss**: Usually 0.03-0.10 (3-10%) accounting for defects and downtime

### Data Quality
- Ensure `moldSettingCycle` values are positive and realistic
- Validate `acquisitionDate` formatting for proper tie-breaking
- Clean `moldList` data to remove extra spaces and empty entries

### Performance Considerations
- For large datasets, consider processing in chunks
- Monitor memory usage with extensive mold catalogs
- Log invalid molds for data quality improvement

## Error Handling

The system provides comprehensive error handling:
- **Missing Columns**: Clear error messages for required column validation
- **Invalid Data**: Graceful handling of zero, negative, or infinite values
- **Empty Datasets**: Safe processing of empty input dataframes
- **Date Parsing**: Robust date conversion with error tolerance

## Logging

The class uses structured logging to track:
- Invalid mold identification
- Unused mold discovery
- Processing progress and completion
- Error conditions and warnings

## Integration Notes

This optimizer is designed to integrate with manufacturing execution systems (MES) and production planning tools. The output data structure supports direct integration with scheduling algorithms and capacity planning systems.