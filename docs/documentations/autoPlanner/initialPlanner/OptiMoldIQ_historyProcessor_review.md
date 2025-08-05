# HistoryProcessor Agent Documentation

## Overview

The **HistoryProcessor** is a specialized agent designed for manufacturing analytics that processes historical production data to optimize mold-machine assignments in injection molding operations. It provides two main functionalities:

1. **Mold Performance Analysis**: Evaluates mold stability based on cavity utilization and cycle time consistency
2. **Priority Matrix Generation**: Creates optimized mold-machine assignment recommendations based on historical performance data

## Architecture

### Core Components

```
HistoryProcessor
├── Data Loading & Validation
├── Mold Stability Analysis
│   ├── Cavity Stability Calculation
│   └── Cycle Time Stability Calculation
└── Priority Matrix Generation
    ├── Historical Performance Analysis
    └── Weighted Scoring System
```

### Key Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **loguru**: Advanced logging capabilities
- **pathlib**: Path handling
- Custom modules:
  - `agents.decorators`: DataFrame validation
  - `agents.utils`: File I/O utilities
  - `agents.core_helpers`: Manufacturing-specific helpers
  - `agents.autoPlanner.hist_based_item_mold_optimizer`: Optimization algorithms

## Class Definition

```python
class HistoryProcessor:
    """
    Agent responsible for processing historical production data to:
    1. Evaluate Mold Performance and Stability
    2. Generate Mold-Machine Priority Matrix
    """
```

### Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `SECONDS_PER_HOUR` | 3600 | Time conversion factor |
| `CYCLE_TIME_TOLERANCE` | 0.2 | Acceptable cycle time deviation (±20%) |
| `EXTREME_DEVIATION_THRESHOLD` | 1.0 | Threshold for extreme outliers (100%) |

### Stability Scoring Weights

#### Cycle Stability Weights
- **Accuracy Score**: 30% - Deviation from standard cycle time
- **Consistency Score**: 25% - Variation in cycle times
- **Range Compliance**: 25% - Percentage within tolerance
- **Outlier Penalty**: 10% - Penalty for extreme deviations
- **Data Completeness**: 10% - Volume of historical data

#### Cavity Stability Weights
- **Accuracy Rate**: 40% - Match with standard cavity count
- **Consistency Score**: 30% - Variation in cavity usage
- **Utilization Rate**: 20% - Average vs. standard cavities
- **Data Completeness**: 10% - Volume of historical data

## Initialization

### Constructor Parameters

```python
def __init__(self,
             source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
             annotation_name: str = "path_annotations.json",
             databaseSchemas_path: str = 'database/databaseSchemas.json',
             folder_path: str = 'agents/shared_db/OrderProgressTracker',
             target_name: str = "change_log.txt",
             default_dir: str = "agents/shared_db",
             efficiency: float = 0.85,
             loss: float = 0.03)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | 'agents/shared_db/DataLoaderAgent/newest' | Path to data source directory |
| `annotation_name` | str | "path_annotations.json" | JSON file with path mappings |
| `databaseSchemas_path` | str | 'database/databaseSchemas.json' | Schema configuration file |
| `folder_path` | str | 'agents/shared_db/OrderProgressTracker' | Production status folder |
| `target_name` | str | "change_log.txt" | Change log filename |
| `default_dir` | str | "agents/shared_db" | Default output directory |
| `efficiency` | float | 0.85 | Expected production efficiency |
| `loss` | float | 0.03 | Expected production loss rate |

### Required DataFrames

The agent automatically loads and validates the following DataFrames:

1. **productRecords_df**: Historical production records
2. **machineInfo_df**: Machine specifications and capabilities
3. **moldSpecificationSummary_df**: Mold-item compatibility data
4. **moldInfo_df**: Detailed mold specifications
5. **proStatus_df**: Current production status and orders

## Core Methods

### 1. Mold Stability Analysis

#### `calculate_mold_stability_index()`

Calculates comprehensive stability metrics for each mold based on historical performance.

```python
def calculate_mold_stability_index(self,
                                   cavity_stability_threshold=0.6,
                                   cycle_stability_threshold=0.4,
                                   total_records_threshold=30) -> pd.DataFrame
```

**Parameters:**
- `cavity_stability_threshold` (float): Weight for cavity stability in overall score
- `cycle_stability_threshold` (float): Weight for cycle stability in overall score  
- `total_records_threshold` (int): Minimum records needed for reliable analysis

**Returns:**
DataFrame with columns:
- `moldNo`: Mold identifier
- `moldName`: Mold name
- `cavityStabilityIndex`: Cavity performance score (0-1)
- `cycleStabilityIndex`: Cycle time performance score (0-1)
- `theoreticalMoldHourCapacity`: Maximum theoretical output
- `effectiveMoldHourCapacity`: Stability-adjusted capacity
- `balancedMoldHourCapacity`: Balanced capacity estimate

#### Stability Calculation Logic

**Cavity Stability:**
1. **Accuracy Rate**: Percentage of measurements matching standard cavity count
2. **Consistency**: Coefficient of variation in cavity usage
3. **Utilization Rate**: Average active cavities vs. standard
4. **Data Completeness**: Penalty for insufficient historical data

**Cycle Time Stability:**
1. **Accuracy Score**: Average deviation from standard cycle time
2. **Consistency**: Variation in cycle times
3. **Range Compliance**: Percentage within ±20% tolerance
4. **Outlier Penalty**: Penalty for extreme deviations (>100%)
5. **Data Completeness**: Volume-based reliability factor

### 2. Priority Matrix Generation

#### `calculate_mold_machine_priority_matrix()`

Creates optimized priority rankings for mold-machine combinations.

```python
def calculate_mold_machine_priority_matrix(self,
                                           weights_hist_path: str,
                                           mold_stability_index_folder: str,
                                           mold_stability_index_target_name: str,
                                           cavity_stability_threshold=0.6,
                                           cycle_stability_threshold=0.4,
                                           total_records_threshold=30) -> pd.DataFrame
```

**Returns:**
Priority matrix DataFrame with:
- **Rows**: Mold numbers (`moldNo`)
- **Columns**: Machine codes (`machineCode`)
- **Values**: Priority rankings (1 = highest priority, 0 = not compatible)

### 3. Export Methods

#### `calculate_and_save_mold_stability_index()`

Calculates mold stability metrics and exports to Excel with versioning.

#### `calculate_and_save_mold_machine_priority_matrix()`

Generates priority matrix and exports to Excel with versioning.

## Data Processing Pipeline

### 1. Data Loading Phase
```
Raw Data Sources → Path Annotations → DataFrame Validation → Loaded DataFrames
```

### 2. Stability Analysis Phase
```
Production Records → Cavity Analysis → Cycle Time Analysis → Stability Indices
```

### 3. Priority Matrix Phase
```
Historical Data → Performance Metrics → Weight Application → Priority Rankings
```

## Output Files

### Mold Stability Index Output
- **File Pattern**: `mold_stability_index_YYYYMMDD_HHMMSS.xlsx`
- **Sheet**: `moldStabilityIndex`
- **Content**: Comprehensive mold performance metrics

### Priority Matrix Output
- **File Pattern**: `priority_matrix_YYYYMMDD_HHMMSS.xlsx`
- **Sheet**: `priorityMatrix`
- **Content**: Mold-machine priority rankings

## Usage Examples

### Basic Usage

```python
# Initialize the processor
processor = HistoryProcessor()

# Calculate and save mold stability analysis
processor.calculate_and_save_mold_stability_index()

# Generate priority matrix
processor.calculate_and_save_mold_machine_priority_matrix()
```

### Custom Configuration

```python
# Initialize with custom parameters
processor = HistoryProcessor(
    efficiency=0.90,
    loss=0.02,
    default_dir="custom_output"
)

# Calculate with custom thresholds
stability_index = processor.calculate_mold_stability_index(
    cavity_stability_threshold=0.7,
    cycle_stability_threshold=0.3,
    total_records_threshold=50
)
```

## Error Handling

The agent implements comprehensive error handling for:

- **File Not Found**: Missing data files or configuration files
- **Schema Validation**: DataFrame structure validation
- **Data Quality**: Invalid or missing values in critical fields
- **Calculation Errors**: Mathematical operations on edge cases

## Performance Considerations

### Optimization Strategies

1. **Data Filtering**: Early filtering of irrelevant records
2. **Vectorized Operations**: NumPy operations for numerical calculations
3. **Memory Management**: Efficient DataFrame operations
4. **Caching**: Reuse of intermediate calculations

### Scalability

- **Large Datasets**: Handles production databases with millions of records
- **Memory Efficiency**: Optimized for memory usage with large DataFrames
- **Processing Speed**: Vectorized calculations for performance

## Integration Points

### Input Dependencies
- **DataLoaderAgent**: Provides cleaned production data
- **OrderProgressTracker**: Current production status
- **FeatureWeightCalculator**: Weighting factors for priority scoring

### Output Consumers
- **Production Planning Systems**: Priority matrix for scheduling
- **Quality Control**: Mold stability metrics for maintenance planning
- **Reporting Systems**: Performance analytics and dashboards

## Configuration Management

### Path Annotations
The system uses JSON-based path annotations for flexible file location management:

```json
{
  "productRecords": "/path/to/production_records.parquet",
  "machineInfo": "/path/to/machine_info.parquet",
  "moldInfo": "/path/to/mold_specifications.parquet"
}
```

### Schema Validation
Automatic validation ensures data consistency:
- Column presence verification
- Data type validation
- Required field checking

## Troubleshooting

### Common Issues

1. **Missing Data Files**
   - Check path annotations
   - Verify file permissions
   - Ensure parquet file integrity

2. **Schema Validation Failures**
   - Compare actual vs. expected columns
   - Check data types in source files
   - Verify database schema configuration

3. **Calculation Errors**
   - Validate input data ranges
   - Check for division by zero conditions
   - Ensure sufficient historical data

### Logging and Debugging

The agent uses structured logging with contextual information:
- Class-level logger binding
- Detailed error messages with context
- Performance metrics logging

## Best Practices

### Data Quality
- Ensure consistent data collection across production systems
- Implement data validation at source systems
- Regular data quality audits

### Configuration Management
- Use version control for configuration files
- Document configuration changes
- Test configuration changes in development environment

### Performance Monitoring
- Monitor processing times for large datasets
- Track memory usage patterns
- Set up alerts for processing failures