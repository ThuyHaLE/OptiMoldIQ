# FeatureWeightCalculator Agent Documentation

## Overview

The **FeatureWeightCalculator** is a sophisticated manufacturing analytics agent designed to evaluate production performance by analyzing historical data and computing confidence-based feature weights. This agent helps optimize manufacturing processes by identifying key performance indicators and their reliability in predicting production outcomes.

## Key Features

- **Performance Classification**: Automatically separates production records into good and bad performance categories based on efficiency and loss thresholds
- **Statistical Confidence Analysis**: Uses bootstrap sampling to calculate confidence scores for feature reliability
- **Dynamic Weight Calculation**: Generates feature weights that combine traditional statistical methods with confidence scoring
- **Comprehensive Reporting**: Produces detailed confidence reports with statistical insights
- **Manufacturing-Specific Metrics**: Tailored for injection molding and similar manufacturing processes

## Architecture

### Class Structure

```python
class FeatureWeightCalculator:
    """
    Calculates feature weights for manufacturing process performance evaluation
    by analyzing production history and computing confidence-based metrics.
    """
```

### Dependencies

The agent integrates with several core components:
- **Database Schema Validation**: Ensures data integrity across multiple manufacturing databases
- **History Processor**: Analyzes mold stability and machine performance history
- **Auto Planner**: Provides item-mold optimization recommendations
- **Report Generator**: Creates formatted confidence reports

## Initialization Parameters

### Core Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Path to annotation data |
| `annotation_name` | str | `"path_annotations.json"` | File name of path annotation |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Path to database schema for validation |
| `folder_path` | str | `'agents/shared_db/OrderProgressTracker'` | Path to production status log folder |
| `target_name` | str | `"change_log.txt"` | Filename of production status log |
| `default_dir` | str | `"agents/shared_db"` | Base directory for storing reports |

### Performance Thresholds

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `efficiency` | float | `0.85` | Efficiency threshold to classify good/bad records |
| `loss` | float | `0.03` | Allowable production loss threshold |

### Statistical Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_bootstrap` | int | `500` | Number of bootstrap samples for confidence estimation |
| `confidence_level` | float | `0.95` | Desired confidence level for statistical tests |
| `min_sample_size` | int | `10` | Minimum sample size for reliable estimation |
| `confidence_weight` | float | `0.3` | Weight assigned to confidence scores in final calculation |

### Feature Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scaling` | Literal['absolute', 'relative'] | `'absolute'` | Method to scale feature impacts |
| `feature_weights` | Optional[Dict[str, float]] | `None` | Optional preset weights for features |
| `targets` | dict | See below | Target metrics and optimization directions |

#### Default Target Configuration

```python
targets = {
    'shiftNGRate': 'minimize',        # Minimize defect rate
    'shiftCavityRate': 1.0,           # Target cavity utilization rate
    'shiftCycleTimeRate': 1.0,        # Target cycle time efficiency
    'shiftCapacityRate': 1.0          # Target capacity utilization
}
```

## Data Sources

The agent requires access to the following manufacturing databases:

### Required DataFrames

1. **productRecords_df**: Historical production records
   - Contains item, mold, machine, and shift data
   - Key fields: `poNo`, `recordDate`, `workingShift`, `machineNo`, `itemCode`, `moldNo`

2. **machineInfo_df**: Machine specifications
   - Machine tonnage, capabilities, and status information
   - Updated with newest machine layout configurations

3. **moldSpecificationSummary_df**: Mold specifications
   - Compatible items, cavity counts, cycle times
   - Links items to appropriate molds

4. **moldInfo_df**: Detailed mold information
   - Tonnage requirements, cavity standards, setting cycles
   - Critical for performance calculations

5. **itemCompositionSummary_df**: Item composition details
   - Material requirements (resin, masterbatch, additives)
   - Quantity specifications per unit

6. **proStatus_df**: Production status tracking
   - Current production orders and their status
   - Links to machine and mold assignments

## Core Methods

### Main Calculation Methods

#### `calculate(mold_stability_index_folder, mold_stability_index_target_name)`

Primary method that orchestrates the entire analysis process:

```python
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()
```

**Returns:**
- `confidence_scores`: Detailed confidence metrics per feature
- `overall_confidence`: Aggregated confidence assessment
- `enhanced_weights`: Optimized feature weights with confidence adjustment

#### `calculate_and_save_report(mold_stability_index_folder, mold_stability_index_target_name)`

Wrapper method that performs calculation and saves formatted reports:

```python
calculator.calculate_and_save_report()
```

### Statistical Analysis Methods

#### `_group_hist_by_performance(proStatus_df, productRecords_df, moldInfo_df, efficiency, loss)`

Classifies production records into performance categories:

**Algorithm:**
1. Calculates theoretical production requirements based on mold specifications
2. Adjusts for efficiency and loss factors
3. Compares actual vs. estimated shift usage
4. Labels records exceeding estimates as "bad performance"

**Returns:** Tuple of (good_hist_df, bad_hist_df)

#### `_calculate_confidence_scores(good_hist_df, bad_hist_df, targets, n_bootstrap, confidence_level, min_sample_size)`

Performs bootstrap sampling to calculate confidence metrics:

**Statistical Methods:**
- Bootstrap resampling for distribution estimation
- Confidence interval calculation
- Mann-Whitney U test for significance
- Target-based achievement scoring

**Output Structure:**
```python
{
    'feature_name': {
        'good_confidence': float,      # Confidence in good group performance
        'bad_confidence': float,       # Confidence in bad group performance
        'separation_confidence': float, # Confidence in group separation
        'statistical_significance': float,
        'sample_size_good': int,
        'sample_size_bad': int,
        'good_mean': float,
        'bad_mean': float,
        'good_ci_lower': float,        # Confidence interval bounds
        'good_ci_upper': float,
        'bad_ci_lower': float,
        'bad_ci_upper': float,
        'p_value': float
    }
}
```

#### `_calculate_overall_confidence(confidence_scores, feature_weights)`

Aggregates individual feature confidences into overall model reliability:

**Metrics:**
- Overall good/bad confidence (weighted average)
- Model reliability (separation × feature validity ratio)
- Valid features ratio

### Weight Calculation Methods

#### `_suggest_weights_standard_based(good_hist_df, bad_hist_df, targets, scaling)`

Traditional weight calculation based on deviation from targets:

**Algorithm:**
- For 'minimize' targets: Uses absolute deviation from zero
- For numeric targets: Uses absolute deviation from target value
- Applies absolute or relative scaling
- Normalizes weights to sum to 1

#### `_suggest_weights_with_confidence(good_hist_df, bad_hist_df, targets, scaling, confidence_weight, ...)`

Enhanced weight calculation incorporating confidence scores:

**Formula:**
```
enhanced_weight = traditional_weight × (1 + separation_confidence × confidence_weight)
```

**Benefits:**
- Reduces weights for unreliable features
- Amplifies weights for highly confident discriminators
- Maintains statistical rigor while improving practical applicability

## Usage Examples

### Basic Usage

```python
# Initialize calculator
calculator = FeatureWeightCalculator(
    efficiency=0.85,
    loss=0.03,
    confidence_weight=0.3
)

# Calculate weights and confidence scores
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()

# Generate and save report
calculator.calculate_and_save_report()
```

### Custom Configuration

```python
# Custom targets and parameters
custom_targets = {
    'shiftNGRate': 'minimize',
    'shiftCycleTimeRate': 0.95,  # Target 95% cycle time efficiency
    'machineUtilization': 0.90   # Target 90% machine utilization
}

calculator = FeatureWeightCalculator(
    efficiency=0.90,              # Higher efficiency threshold
    loss=0.02,                    # Lower loss tolerance
    targets=custom_targets,
    n_bootstrap=1000,            # More bootstrap samples
    confidence_level=0.99,       # Higher confidence level
    scaling='relative'           # Relative scaling
)
```

### Integration with Manufacturing Systems

```python
# Production line optimization
def optimize_production_weights():
    calculator = FeatureWeightCalculator()
    
    # Calculate current weights
    _, _, weights = calculator.calculate()
    
    # Apply weights to production scheduling
    scheduler.update_optimization_weights(weights)
    
    return weights

# Quality control integration
def assess_process_reliability():
    calculator = FeatureWeightCalculator()
    
    # Get confidence assessment
    _, overall_confidence, _ = calculator.calculate()
    
    reliability_score = overall_confidence['model_reliability']
    
    if reliability_score < 0.7:
        logger.warning("Low model reliability: {:.1%}".format(reliability_score))
        return "REVIEW_REQUIRED"
    elif reliability_score > 0.9:
        return "HIGH_CONFIDENCE"
    else:
        return "MODERATE_CONFIDENCE"
```

## Output Reports

### Confidence Report Structure

The agent generates comprehensive reports including:

1. **Executive Summary**
   - Overall model reliability score
   - Key performance indicators
   - Confidence level assessment

2. **Feature Analysis**
   - Individual feature confidence scores
   - Statistical significance tests
   - Sample size validation

3. **Performance Classification**
   - Good vs. bad group characteristics
   - Separation confidence metrics
   - Bootstrap confidence intervals

4. **Weight Recommendations**
   - Enhanced feature weights
   - Traditional vs. confidence-adjusted weights
   - Scaling methodology explanation

### Sample Report Output

```
=== MANUFACTURING PROCESS CONFIDENCE ANALYSIS ===

Model Reliability: 87.3%
Overall Confidence: High

Feature Performance Summary:
┌─────────────────────┬──────────────┬─────────────┬────────────────┐
│ Feature             │ Confidence   │ Separation  │ Enhanced Weight│
├─────────────────────┼──────────────┼─────────────┼────────────────┤
│ shiftNGRate         │ 92.1%        │ 89.4%       │ 0.342          │
│ shiftCycleTimeRate  │ 85.7%        │ 78.2%       │ 0.287          │
│ shiftCapacityRate   │ 79.3%        │ 71.6%       │ 0.234          │
│ shiftCavityRate     │ 74.8%        │ 68.9%       │ 0.137          │
└─────────────────────┴──────────────┴─────────────┴────────────────┘

Recommendations:
- shiftNGRate shows highest discriminative power
- Consider monitoring cycle time efficiency closely
- Sufficient sample sizes for all features (>10 samples)
```

## Error Handling and Validation

### Data Validation

The agent includes comprehensive validation:

```python
@validate_init_dataframes(lambda self: {
    "productRecords_df": [...],  # Required columns
    "machineInfo_df": [...],
    # ... other DataFrames
})
```

### Common Error Scenarios

1. **Missing Data Files**
   - Validates file existence before loading
   - Provides clear error messages with file paths

2. **Insufficient Sample Sizes**
   - Warns when sample sizes < `min_sample_size`
   - Assigns neutral confidence scores for small samples

3. **Missing Features**
   - Handles features not present in data
   - Sets appropriate default weights and warnings

4. **Schema Mismatches**
   - Validates DataFrame schemas against expected structure
   - Fails fast with descriptive error messages

## Performance Considerations

### Computational Complexity

- **Bootstrap Sampling**: O(n_bootstrap × sample_size)
- **Statistical Tests**: O(n × log(n)) per feature
- **Memory Usage**: Proportional to historical data size

### Optimization Recommendations

1. **Adjust Bootstrap Samples**: Reduce `n_bootstrap` for faster execution
2. **Sample Size Limits**: Bootstrap uses max 50 samples per iteration
3. **Feature Selection**: Focus on most relevant features to reduce computation
4. **Data Preprocessing**: Clean data before analysis for better performance

## Integration Points

### Upstream Dependencies

- **DataLoaderAgent**: Provides current manufacturing data
- **HistoryProcessor**: Supplies mold stability indices
- **OrderProgressTracker**: Maintains production status logs

### Downstream Consumers

- **AutoPlanner**: Uses weights for optimization decisions
- **QualityControlAgent**: Monitors confidence thresholds
- **ReportingSystem**: Incorporates confidence metrics in dashboards

## Configuration Best Practices

### Production Environment

```python
production_config = {
    'efficiency': 0.85,           # Conservative efficiency target
    'loss': 0.03,                 # Realistic loss allowance
    'confidence_level': 0.95,     # Standard confidence level
    'n_bootstrap': 500,           # Balanced accuracy/speed
    'min_sample_size': 15,        # Adequate statistical power
    'confidence_weight': 0.3      # Moderate confidence adjustment
}
```

### Development/Testing

```python
dev_config = {
    'efficiency': 0.80,           # More lenient for testing
    'loss': 0.05,                 # Higher loss tolerance
    'confidence_level': 0.90,     # Faster computation
    'n_bootstrap': 100,           # Quick iterations
    'min_sample_size': 5,         # Smaller samples acceptable
    'confidence_weight': 0.5      # Higher confidence emphasis
}
```

## Troubleshooting

### Common Issues

1. **Low Model Reliability**
   - **Cause**: Insufficient data separation between good/bad groups
   - **Solution**: Adjust efficiency/loss thresholds, collect more data

2. **High Variance in Weights**
   - **Cause**: Unstable bootstrap samples
   - **Solution**: Increase `n_bootstrap`, check data quality

3. **Missing Feature Warnings**
   - **Cause**: Database schema changes or data quality issues
   - **Solution**: Verify data pipeline, update feature configurations

4. **Memory Issues with Large Datasets**
   - **Cause**: Large historical datasets
   - **Solution**: Implement data sampling, use chunked processing