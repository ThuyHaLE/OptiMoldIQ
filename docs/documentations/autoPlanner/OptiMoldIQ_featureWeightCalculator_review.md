# FeatureWeightCalculator Documentation

## Overview

The `FeatureWeightCalculator` is a sophisticated statistical analysis tool designed for manufacturing process optimization. It analyzes historical production data to calculate feature weights and confidence scores that evaluate manufacturing performance, supporting optimal production planning through data-driven insights.

---

## Class Overview

### Purpose
The `FeatureWeightCalculator` serves as a core component in manufacturing analytics pipelines, providing:
- **Performance Classification**: Categorizes production runs into good/bad performance groups
- **Statistical Analysis**: Uses bootstrap sampling and confidence intervals for robust analysis
- **Feature Weight Calculation**: Generates weighted importance scores for manufacturing metrics
- **Confidence Assessment**: Provides statistical confidence measures for decision reliability

### Core Workflow
```
Historical Data → Performance Classification → Statistical Analysis → Weight Calculation → Confidence Reports
```

### Constructor

```python
calculator = FeatureWeightCalculator(
                source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                annotation_name: str = "path_annotations.json",
                databaseSchemas_path: str = 'database/databaseSchemas.json',
                folder_path: str = 'agents/shared_db/OrderProgressTracker',
                target_name: str = "change_log.txt",
                default_dir: str = "agents/shared_db",
                efficiency: float = 0.85,
                loss: float = 0.03,
                scaling: Literal['absolute', 'relative'] = 'absolute',
                confidence_weight: float = 0.3,
                n_bootstrap: int = 500,
                confidence_level: float = 0.95,
                min_sample_size: int = 10,
                feature_weights: Optional[Dict[str, float]] = None,
                targets = {'shiftNGRate': 'minimize',
                           'shiftCavityRate': 1.0,
                           'shiftCycleTimeRate': 1.0,
                           'shiftCapacityRate': 1.0}
                           )
```

---

## Constructor Parameters

### Basic Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_path` | str | `'agents/shared_db/DataLoaderAgent/newest'` | Path to annotation data directory |
| `annotation_name` | str | `"path_annotations.json"` | Filename of path annotation file |
| `databaseSchemas_path` | str | `'database/databaseSchemas.json'` | Database schema validation file path |

### Data Source Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | str | `'agents/shared_db/OrderProgressTracker'` | Production status log directory |
| `target_name` | str | `"change_log.txt"` | Production status log filename |
| `default_dir` | str | `"agents/shared_db"` | Base directory for report storage |

### Analysis Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `efficiency` | float | `0.85` | Efficiency threshold for performance classification |
| `loss` | float | `0.03` | Acceptable production loss threshold |
| `scaling` | Literal['absolute', 'relative'] | `'absolute'` | Feature impact scaling method |

### Statistical Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confidence_weight` | float | `0.3` | Weight of confidence in final calculation |
| `n_bootstrap` | int | `500` | Number of bootstrap samples |
| `confidence_level` | float | `0.95` | Statistical confidence level |
| `min_sample_size` | int | `10` | Minimum samples for reliable estimation |

### Advanced Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `feature_weights` | Optional[Dict[str, float]] | `None` | Preset feature weights |
| `targets` | Dict | See below | Target metrics configuration |

#### Default Targets Configuration
```python
targets = {
    'shiftNGRate': 'minimize',       # Minimize defect rate
    'shiftCavityRate': 1.0,          # Target cavity utilization
    'shiftCycleTimeRate': 1.0,       # Target cycle time efficiency
    'shiftCapacityRate': 1.0         # Target capacity utilization
}
```

---

## Key Methods

### 1. Primary Analysis Methods

#### `calculate(mold_stability_index_folder, mold_stability_index_target_name)`
**Purpose**: Main calculation method that orchestrates the entire analysis pipeline.

**Parameters**:
- `mold_stability_index_folder` (str): Path to mold stability index data
- `mold_stability_index_target_name` (str): Filename of stability index log

**Returns**:
- `confidence_scores` (Dict): Statistical confidence metrics per feature
- `overall_confidence` (Dict): Aggregated confidence assessment  
- `enhanced_weights` (Dict): Final calculated feature weights

**Usage**:
```python
calculator = FeatureWeightCalculator()
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()
```

#### `calculate_and_save_report(mold_stability_index_folder, mold_stability_index_target_name)`
**Purpose**: Wrapper method that performs calculation and saves formatted report.

**Returns**: None (saves report to configured output directory)

**Usage**:
```python
calculator = FeatureWeightCalculator()
calculator.calculate_and_save_report()
```

### 2. Data Loading Methods

#### `_load_dataframes()`
**Purpose**: Loads all required DataFrames from parquet files with validation.

**Loaded DataFrames**:
- `productRecords_df`: Production records with item, mold, machine data
- `machineInfo_df`: Machine specifications and tonnage information
- `moldSpecificationSummary_df`: Mold specifications and compatible items
- `moldInfo_df`: Detailed mold information including tonnage requirements
- `itemCompositionSummary_df`: Item composition details (resin, masterbatch, etc.)

**Error Handling**: Raises `FileNotFoundError` for missing files or paths.

---

## Statistical Methods

### 1. Performance Classification

#### `_group_hist_by_performance(proStatus_df, productRecords_df, moldInfo_df, efficiency, loss)`
**Purpose**: Classifies historical production data into good/bad performance categories.

**Algorithm**:
1. **Data Preparation**: Filters valid production records with required fields
2. **Aggregation**: Groups by PO, mold, and machine for shift statistics
3. **Theoretical Calculation**: Computes expected performance using mold specifications
4. **Classification**: Compares actual vs. expected performance accounting for efficiency/loss

**Performance Criteria**:
```python
net_efficiency = efficiency - loss
estimated_shifts = theoretical_shifts / net_efficiency
is_bad_performance = actual_shifts > estimated_shifts
```

**Returns**: 
- `good_hist` (DataFrame): Records from well-performing production runs
- `bad_hist` (DataFrame): Records from poorly-performing production runs

### 2. Confidence Score Calculation

#### `_calculate_confidence_scores(good_hist_df, bad_hist_df, targets, n_bootstrap, confidence_level, min_sample_size)`
**Purpose**: Calculates statistical confidence scores using bootstrap sampling.

**Algorithm Components**:

1. **Bootstrap Sampling**:
   - Generates `n_bootstrap` resampled datasets
   - Calculates mean for each bootstrap sample
   - Creates distribution of bootstrap means

2. **Confidence Intervals**:
   ```python
   alpha = 1 - confidence_level
   ci_lower = percentile(bootstrap_means, (alpha/2) * 100)
   ci_upper = percentile(bootstrap_means, (1-alpha/2) * 100)
   ```

3. **Target-Based Scoring**:
   - **Minimize targets**: Rewards lower values in good group
   - **Fixed targets**: Rewards proximity to target value

4. **Separation Analysis**:
   ```python
   overlap = max(0, min(good_ci_upper, bad_ci_upper) - max(good_ci_lower, bad_ci_lower))
   separation_confidence = 1 - (overlap / total_range)
   ```

5. **Statistical Testing**:
   - Uses Mann-Whitney U test for group differences
   - Provides p-value for significance testing

**Confidence Score Formula**:
```python
confidence = (
    target_achievement * 0.4 +      # How well group meets targets
    separation_confidence * 0.3 +    # How well groups separate
    statistical_significance * 0.2 + # Statistical test results
    distance_penalty * 0.1           # Penalty for deviation
)
```

**Returns**: Dictionary with detailed confidence metrics per feature.

### 3. Weight Calculation Methods

#### `_suggest_weights_standard_based(good_hist_df, bad_hist_df, targets, scaling)`
**Purpose**: Calculates feature weights based on deviation from performance standards.

**Algorithm**:
1. **Deviation Calculation**:
   - For "minimize" targets: `|mean_value|`
   - For fixed targets: `|mean_value - target|`

2. **Score Calculation**:
   ```python
   score = |deviation_bad - deviation_good|
   ```

3. **Scaling Application**:
   - **Absolute**: Raw deviation differences
   - **Relative**: Normalized by target magnitude

#### `_suggest_weights_with_confidence(good_hist_df, bad_hist_df, targets, scaling, confidence_weight, ...)`
**Purpose**: Enhanced weight calculation incorporating statistical confidence.

**Algorithm**:
1. Calculate traditional weights using standard method
2. Calculate confidence scores using bootstrap sampling
3. Enhance weights with confidence factor:
   ```python
   enhanced_weight = traditional_weight * (1 + confidence_factor * confidence_weight)
   ```
4. Normalize final weights to sum to 1.0

### 4. Overall Confidence Assessment

#### `_calculate_overall_confidence(confidence_scores, feature_weights)`
**Purpose**: Aggregates individual feature confidences into overall model reliability.

**Metrics Calculated**:
- `overall_good_confidence`: Weighted average of good group confidences
- `overall_bad_confidence`: Weighted average of bad group confidences  
- `overall_separation_confidence`: Weighted average separation quality
- `model_reliability`: Combined reliability score
- `valid_features_ratio`: Proportion of features with sufficient data

---

## Usage Examples

### Basic Usage
```python
# Initialize with default parameters
calculator = FeatureWeightCalculator()

# Run analysis and get results
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()

# Print results
print("Enhanced Weights:", enhanced_weights)
print("Overall Confidence:", overall_confidence['model_reliability'])
```

### Custom Configuration
```python
# Initialize with custom parameters
calculator = FeatureWeightCalculator(
    efficiency=0.90,           # Higher efficiency threshold
    loss=0.02,                 # Lower loss tolerance
    confidence_weight=0.4,     # Higher confidence influence
    n_bootstrap=1000,          # More bootstrap samples
    scaling='relative'         # Relative scaling
)

# Custom targets
custom_targets = {
    'shiftNGRate': 'minimize',
    'shiftCycleTimeRate': 0.95,    # Custom target value
    'shiftCapacityRate': 0.98      # Custom target value
}

calculator.targets = custom_targets
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()
```

### Analysis with Report Generation
```python
# Generate analysis with automatic report saving
calculator = FeatureWeightCalculator(
    default_dir="output/analysis_reports"
)

calculator.calculate_and_save_report()
# This saves a detailed confidence report to the specified directory
```

### Advanced Feature Analysis
```python
# Access detailed confidence metrics
confidence_scores, _, _ = calculator.calculate()

for feature, metrics in confidence_scores.items():
    if 'warning' not in metrics:
        print(f"\nFeature: {feature}")
        print(f"  Good Group Confidence: {metrics['good_confidence']:.3f}")
        print(f"  Bad Group Confidence: {metrics['bad_confidence']:.3f}")
        print(f"  Statistical Significance: {metrics['statistical_significance']:.3f}")
        print(f"  Sample Sizes: Good={metrics['sample_size_good']}, Bad={metrics['sample_size_bad']}")
```

---

## Configuration Guide

### Performance Thresholds

#### Efficiency Setting
```python
efficiency = 0.85  # 85% efficiency expectation
```
- **Higher values (0.90-0.95)**: Stricter performance standards
- **Lower values (0.70-0.85)**: More lenient classification
- **Impact**: Affects good/bad group classification boundary

#### Loss Tolerance
```python
loss = 0.03  # 3% acceptable loss
```
- **Lower values**: Stricter quality requirements
- **Higher values**: More tolerance for production losses
- **Impact**: Combined with efficiency to set net performance expectations

### Statistical Parameters

#### Bootstrap Configuration
```python
n_bootstrap = 500      # Number of bootstrap samples
confidence_level = 0.95  # 95% confidence intervals
```
- **Higher n_bootstrap**: More stable confidence estimates (slower computation)
- **Higher confidence_level**: Wider confidence intervals, more conservative estimates

#### Sample Size Requirements
```python
min_sample_size = 10  # Minimum samples for analysis
```
- **Higher values**: More reliable but may exclude some features
- **Lower values**: Include more features but potentially less reliable

### Feature Weight Tuning

#### Confidence Weight Influence
```python
confidence_weight = 0.3  # 30% confidence influence
```
- **Higher values (0.4-0.6)**: Prioritize statistically reliable features
- **Lower values (0.1-0.3)**: Focus more on raw performance differences

#### Scaling Method Selection
```python
scaling = 'absolute'  # or 'relative'
```
- **Absolute**: Better for features with similar scales
- **Relative**: Better when features have very different magnitudes

### Target Configuration Examples

#### Quality-Focused Configuration
```python
targets = {
    'shiftNGRate': 'minimize',      # Primary quality focus
    'shiftCycleTimeRate': 0.95,     # Allow some cycle time variation
    'shiftCapacityRate': 0.90       # Accept lower capacity for quality
}
```

#### Efficiency-Focused Configuration
```python
targets = {
    'shiftNGRate': 'minimize',      # Still minimize defects
    'shiftCycleTimeRate': 1.0,      # Demand optimal cycle times
    'shiftCapacityRate': 1.0        # Demand full capacity utilization
}
```

---

## Error Handling

### Common Exceptions

#### FileNotFoundError
```python
try:
    calculator = FeatureWeightCalculator()
    results = calculator.calculate()
except FileNotFoundError as e:
    print(f"Data file missing: {e}")
    # Handle missing data files
```

#### ValueError
```python
try:
    calculator = FeatureWeightCalculator(scaling='invalid_method')
except ValueError as e:
    print(f"Invalid parameter: {e}")
    # Handle invalid configuration
```

### Data Quality Issues

#### Insufficient Sample Sizes
The class automatically handles insufficient sample sizes:
```python
# Features with insufficient data receive warning flags
if 'warning' in confidence_scores[feature]:
    print(f"Feature {feature}: {confidence_scores[feature]['warning']}")
```

#### Missing Features
Missing features in data are handled gracefully:
```python
# Missing features receive neutral confidence scores
missing_feature_score = {
    'good_confidence': 0.5,
    'bad_confidence': 0.5,
    'separation_confidence': 0.0,
    'warning': 'Feature not found in data'
}
```

---

## Performance Considerations

### Computational Complexity

#### Bootstrap Sampling
- **Time Complexity**: O(n_bootstrap × sample_size × n_features)
- **Memory Usage**: O(n_bootstrap × n_features)
- **Optimization**: Reduce `n_bootstrap` for faster execution

#### Data Loading
- **I/O Operations**: Multiple parquet file reads
- **Memory Usage**: Proportional to historical data size
- **Optimization**: Use data preprocessing to reduce file sizes

### Scalability Guidelines

#### Small Datasets (< 10,000 records)
```python
calculator = FeatureWeightCalculator(
    n_bootstrap=200,           # Reduced bootstrap samples
    min_sample_size=5          # Lower minimum sample size
)
```

#### Large Datasets (> 100,000 records)
```python
calculator = FeatureWeightCalculator(
    n_bootstrap=1000,          # More bootstrap samples for stability
    min_sample_size=50         # Higher minimum for reliability
)
```