# HybridSuggestOptimizer Agent Documentation

## Overview

The `HybridSuggestOptimizer` is a sophisticated manufacturing optimization system that combines historical data analysis with mold-machine compatibility matching to suggest optimal production configurations. This agent serves as a critical component in smart manufacturing systems, enabling data-driven decisions for production planning and resource allocation.

## Key Features

### Multi-Strategy Optimization
- **Historical-based mold capacity estimation**: Analyzes past performance data to predict future production capabilities
- **Mold stability index analysis**: Evaluates consistency and reliability of mold performance
- **Feature weight calculation**: Determines optimal importance factors for mold-machine priority matrix
- **Production efficiency optimization**: Maximizes overall equipment effectiveness (OEE)

### Data Integration
- Seamless integration with multiple data sources including parquet files and Excel spreadsheets
- Robust error handling and validation for data integrity
- Flexible configuration system supporting various file formats and locations

## Architecture

### Core Components

1. **HybridSuggestOptimizer (Main Class)**
   - Central orchestrator for the optimization process
   - Manages data loading, validation, and processing coordination

2. **HistBasedItemMoldOptimizer**
   - Processes historical production data to estimate mold capacities
   - Calculates stability indices for performance consistency

3. **HistoryProcessor**
   - Analyzes historical performance data
   - Generates mold-machine priority matrices

### Data Flow

```
Input Data Sources → Data Validation → Historical Analysis → Optimization → Output Results
```

## Configuration Parameters

### Default Feature Weights

The system uses predefined weights for different performance metrics:

| Metric | Weight | Description |
|--------|--------|-------------|
| `shiftNGRate_weight` | 0.1 (10%) | Defect rate impact |
| `shiftCavityRate_weight` | 0.25 (25%) | Cavity utilization importance |
| `shiftCycleTimeRate_weight` | 0.25 (25%) | Cycle time efficiency weight |
| `shiftCapacityRate_weight` | 0.4 (40%) | Overall capacity priority (highest) |

### Production Parameters

- **Efficiency**: Default 0.85 (85% OEE)
- **Loss Rate**: Default 0.03 (3% material/time loss)

## Initialization Parameters

### Constructor Arguments

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Base path for data source files |
| `annotation_name` | str | `"path_annotations.json"` | JSON file containing path mappings |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Path to database schema definitions |
| `default_dir` | str | `"agents/shared_db"` | Default directory for shared database files |
| `folder_path` | str | `"agents/OrderProgressTracker"` | Path for order progress tracking files |
| `target_name` | str | `"change_log.txt"` | Name of the change log file |
| `mold_stability_index_folder` | str | `"agents/HistoryProcessor/mold_stability_index"` | Folder containing mold stability indices |
| `mold_stability_index_target_name` | str | `"change_log.txt"` | Target file name for stability index |
| `mold_machine_weights_hist_path` | str | `"agents/FeatureWeightCalculator/weights_hist.xlsx"` | Path to historical feature weights |
| `efficiency` | float | `0.85` | Expected production efficiency (85%) |
| `loss` | float | `0.03` | Expected production loss rate (3%) |

## Data Requirements

### Required DataFrames

#### 1. moldSpecificationSummary_df
- **Purpose**: Contains mold-item compatibility mappings
- **Format**: Parquet file
- **Validation**: Schema validation against database specifications

#### 2. moldInfo_df
- **Purpose**: Detailed mold information including tonnage requirements
- **Format**: Parquet file
- **Validation**: Schema validation against database specifications

### Output Data Structures

#### 1. Estimated Mold Capacity DataFrame
Contains the following required columns:

| Column Name | Description |
|-------------|-------------|
| `moldNo` | Unique mold identifier |
| `moldName` | Human-readable mold name |
| `acquisitionDate` | Date when mold was acquired |
| `machineTonnage` | Required machine tonnage |
| `moldCavityStandard` | Standard number of cavities |
| `moldSettingCycle` | Standard cycle time setting |
| `cavityStabilityIndex` | Consistency metric for cavity performance |
| `cycleStabilityIndex` | Consistency metric for cycle time |
| `theoreticalMoldHourCapacity` | Maximum theoretical production rate |
| `effectiveMoldHourCapacity` | Realistic production rate |
| `estimatedMoldHourCapacity` | Predicted production rate |
| `balancedMoldHourCapacity` | Optimized production rate |
| `totalRecords` | Number of historical records analyzed |
| `totalCavityMeasurements` | Total cavity measurements available |
| `totalCycleMeasurements` | Total cycle measurements available |
| `firstRecordDate` | Earliest historical data point |
| `lastRecordDate` | Latest historical data point |

#### 2. Feature Weights
Performance metrics for mold-machine combinations:

| Column Name | Description |
|-------------|-------------|
| `shiftNGRate` | Rate of defective products per shift |
| `shiftCavityRate` | Cavity utilization rate per shift |
| `shiftCycleTimeRate` | Cycle time performance rate per shift |
| `shiftCapacityRate` | Overall production capacity rate per shift |

## Method Documentation

### Core Methods

#### `__init__(self, **kwargs)`
Initializes the optimizer with configuration parameters and loads required data structures.

**Workflow:**
1. Initialize logger for debugging and monitoring
2. Load database schema for validation
3. Set production parameters
4. Load path annotations for flexible file configuration
5. Initialize all required DataFrames
6. Create HistoryProcessor instance

#### `_load_dataframes(self) -> None`
Loads all required DataFrames from parquet files with comprehensive error handling.

**Features:**
- Validates file existence before loading
- Provides detailed error logging
- Uses parquet format for efficient data storage
- Dynamic attribute setting for flexibility

**Raises:**
- `FileNotFoundError`: If required data files are missing
- `Exception`: If there are issues reading parquet files

#### `_load_mold_stability_index(self) -> pd.DataFrame`
Loads mold stability index data from the most recent file or creates initial structure.

**Returns:**
- `pd.DataFrame`: Mold stability index with performance consistency metrics

**Behavior:**
- Attempts to load from change log first
- Creates empty structure if no historical data exists
- Logs warnings and information appropriately

#### `_load_feature_weights(self) -> pd.Series`
Loads the latest feature weights for calculating mold-machine priority matrix.

**Returns:**
- `pd.Series`: Feature weights for different performance metrics

**Fallback Behavior:**
- Uses predefined default weights if historical data unavailable
- Logs detailed weight information for verification

#### `process(self) -> tuple`
Executes the complete hybrid optimization process.

**Returns:**
- `tuple`: Three-element tuple containing:
  - `invalid_molds`: List of molds that couldn't be processed
  - `mold_estimated_capacity_df`: DataFrame with estimated capacities
  - `mold_machine_priority_matrix`: Matrix showing optimal combinations

**Workflow:**
1. Load mold stability index
2. Estimate mold capacities using historical data
3. Load feature weights
4. Calculate mold-machine priority matrix

## Usage Examples

### Basic Usage

```python
from agents.autoPlanner.hybrid_suggest_optimizer import HybridSuggestOptimizer

# Initialize with default parameters
optimizer = HybridSuggestOptimizer()

# Execute optimization process
invalid_molds, capacity_df, priority_matrix = optimizer.process()

# Use results for production planning
print(f"Invalid molds found: {len(invalid_molds)}")
print(f"Capacity estimates for {len(capacity_df)} molds")
print(f"Priority matrix shape: {priority_matrix.shape}")
```

### Custom Configuration

```python
# Initialize with custom parameters
optimizer = HybridSuggestOptimizer(
    source_path='custom/data/path',
    efficiency=0.90,  # Higher efficiency target
    loss=0.02,        # Lower loss expectation
)

# Process with custom settings
results = optimizer.process()
```

### Error Handling

```python
try:
    optimizer = HybridSuggestOptimizer()
    results = optimizer.process()
except FileNotFoundError as e:
    print(f"Required data file not found: {e}")
except Exception as e:
    print(f"Optimization failed: {e}")
```

## Dependencies

### Required Packages
- `pandas`: Data manipulation and analysis
- `pathlib`: Path handling and file operations
- `loguru`: Advanced logging capabilities
- `os`: Operating system interface

### Internal Dependencies
- `agents.decorators.validate_init_dataframes`: DataFrame validation
- `agents.utils`: Utility functions for data loading
- `agents.autoPlanner.hist_based_item_mold_optimizer`: Historical optimization
- `agents.autoPlanner.initialPlanner.history_processor`: Historical data processing

## Error Handling

### Common Error Scenarios

1. **Missing Data Files**
   - `FileNotFoundError` raised when required parquet files are missing
   - Detailed logging shows which files are missing
   - Recommendation: Verify file paths and permissions

2. **Schema Validation Failures**
   - Decorator validates DataFrame schemas against requirements
   - Missing columns or incorrect data types trigger validation errors
   - Recommendation: Check data source integrity

3. **Parquet Reading Issues**
   - Corrupt files or permission issues prevent data loading
   - Comprehensive error logging provides debugging information
   - Recommendation: Verify file integrity and access permissions

### Logging Levels

- **DEBUG**: DataFrame shapes and column information
- **INFO**: Process status and completion messages
- **WARNING**: Missing files or fallback behavior
- **ERROR**: Critical failures and exceptions

## Performance Considerations

### Memory Usage
- Large DataFrames loaded into memory simultaneously
- Consider data size when setting system memory allocation
- Parquet format provides efficient storage and loading

### Processing Time
- Historical analysis can be computationally intensive
- Processing time scales with historical data volume
- Consider implementing progress indicators for long-running operations

### Optimization Tips
- Use appropriate data types in parquet files
- Implement data partitioning for very large datasets
- Consider caching frequently used calculations

## Best Practices

### Configuration Management
- Use environment variables for sensitive paths
- Implement configuration validation
- Maintain separate configs for different environments

### Data Quality
- Implement comprehensive data validation
- Monitor data freshness and completeness
- Use data profiling to detect anomalies

### Monitoring and Logging
- Set appropriate logging levels for different environments
- Monitor optimization performance metrics
- Implement alerting for critical failures

### Testing
- Unit tests for individual methods
- Integration tests for complete workflows
- Performance tests for large datasets

## Troubleshooting

### Common Issues

1. **"Path not found" errors**
   - Verify file paths in configuration
   - Check file permissions and accessibility
   - Ensure parquet files exist and are not corrupted

2. **Schema validation failures**
   - Compare DataFrame columns with required schema
   - Check for missing or renamed columns
   - Verify data types match expectations

3. **Memory errors with large datasets**
   - Monitor system memory usage
   - Consider data sampling for development/testing
   - Implement chunked processing for very large files

4. **Performance issues**
   - Profile code to identify bottlenecks
   - Optimize DataFrame operations
   - Consider parallel processing for independent calculations