# FeatureWeightCalculator Workflow Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FeatureWeightCalculator                             │
│                   Manufacturing Performance Analysis Pipeline               │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🔧 INITIALIZATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Load configuration files (schemas, annotations)                           │
│ • Validate and load 5 core datasets + production status                    │
│ • Setup efficiency/loss thresholds and statistical parameters              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   📊 CONFIDENCE-WEIGHTED ANALYSIS PIPELINE                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Steps

### Phase 1: Initialization & Data Loading

```
┌──────────────────────────────────────┐
│        Class Constructor             │
│    FeatureWeightCalculator()        │
└──────────────┬───────────────────────┘
               │
               ├─ Load path_annotations.json
               ├─ Load databaseSchemas.json
               ├─ Load production status from OrderProgressTracker
               ├─ Set statistical parameters (n_bootstrap, confidence_level)
               │
               ▼
┌──────────────────────────────────────┐
│     Load Core Datasets              │
├──────────────────────────────────────┤
│ 📄 productRecords_df                │
│ 📄 machineInfo_df                   │
│ 📄 moldSpecificationSummary_df      │
│ 📄 moldInfo_df                      │
│ 📄 itemCompositionSummary_df        │
│ 📄 proStatus_df                     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   @validate_init_dataframes          │
│   Schema Validation                  │
└──────────────────────────────────────┘
```

### Phase 2: Performance Analysis Pipeline

```
                    calculate() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │                 Step 1: Load Mold Stability Index      │
    │ Source: HistoryProcessor/mold_stability_index          │
    │ Result: mold_stability_index DataFrame                 │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 2: Process Mold Information          │
    │ Method: HistBasedItemMoldOptimizer().process_mold_info()│
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Analyze mold-item compatibility                     │
    │ 📊 Calculate capacity and efficiency metrics           │
    │ 🏷️  Generate capacity_mold_info_df                     │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 3: Performance Grouping              │
    │ Method: _group_hist_by_performance()                   │
    ├────────────────────────────────────────────────────────┤
    │ 🧮 Calculate theoretical vs actual production:         │
    │    • moldFullTotalShots = itemQuantity / moldCavity    │
    │    • moldFullTotalSeconds = shots × moldSettingCycle   │
    │    • moldFullShiftUsed = seconds / (8 hours)           │
    │    • moldEstimatedShiftUsed considering efficiency     │
    │ 🏷️  Classify Performance:                              │
    │    • Good: actualShifts ≤ estimatedShifts             │
    │    • Bad: actualShifts > estimatedShifts              │
    │ 📊 Output: good_hist, bad_hist DataFrames              │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 4: Historical Data Summarization     │
    │ Method: summarize_mold_machine_history()               │
    ├────────────────────────────────────────────────────────┤
    │ 📈 Calculate performance metrics:                      │
    │    • shiftNGRate, shiftCavityRate                     │
    │    • shiftCycleTimeRate, shiftCapacityRate            │
    │ 🔧 Merge with capacity_mold_info_df                    │
    │ 📊 Result: good_sample, bad_sample DataFrames          │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 5: Confidence Score Calculation      │
    │ Method: _calculate_confidence_scores()                 │
    ├────────────────────────────────────────────────────────┤
    │ 🎲 Bootstrap Sampling (n_bootstrap iterations):        │
    │    • Sample from good_sample and bad_sample           │
    │    • Calculate bootstrap means for each feature       │
    │ 📊 Statistical Analysis:                               │
    │    • Confidence intervals (95% default)               │
    │    • Mann-Whitney U test for significance             │
    │    • Target achievement scoring                       │
    │ 🎯 Target-based Evaluation:                           │
    │    • 'minimize': Lower values preferred               │
    │    • Numeric targets: Closer to target preferred      │
    │ 📈 Confidence Metrics:                                │
    │    • good_confidence, bad_confidence                  │
    │    • separation_confidence, statistical_significance   │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 6: Overall Confidence Assessment     │
    │ Method: _calculate_overall_confidence()                │
    ├────────────────────────────────────────────────────────┤
    │ 🧮 Weighted Average Calculation:                       │
    │    • Use feature_weights if provided                   │
    │    • Normalize weights to sum = 1                     │
    │ 📊 Model Reliability Metrics:                         │
    │    • overall_good_confidence                          │
    │    • overall_bad_confidence                           │
    │    • model_reliability                                │
    │    • valid_features_ratio                             │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 7: Enhanced Weight Generation        │
    │ Method: _suggest_weights_with_confidence()             │
    ├────────────────────────────────────────────────────────┤
    │ 🔢 Traditional Weight Calculation:                     │
    │    • _suggest_weights_standard_based()                │
    │    • Based on deviation from targets                  │
    │    • Supports 'absolute' or 'relative' scaling        │
    │ 🎯 Confidence Enhancement:                             │
    │    • enhanced_weight = traditional × (1 + confidence × confidence_weight) │
    │    • Uses separation_confidence as confidence_factor   │
    │ ⚖️  Weight Normalization:                              │
    │    • Ensure sum of all weights = 1                    │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 8: Report Generation                 │
    │ Method: calculate_and_save_report()                    │
    ├────────────────────────────────────────────────────────┤
    │ 📄 Generate Confidence Report:                         │
    │    • generate_confidence_report()                     │
    │    • Detailed statistical summary                     │
    │ 💾 Save Output:                                        │
    │    • save_text_report_with_versioning()               │
    │    • Text report + enhanced_weights JSON              │
    │ 📁 Output Location:                                    │
    │    • agents/shared_db/FeatureWeightCalculator/        │
    └────────────────────────────────────────────────────────┘
```

## Key Data Transformations

### Input Data Sources
```
productRecords_df              ──┐
machineInfo_df                 ──┤
moldSpecificationSummary_df    ──┼─► Performance Analysis
moldInfo_df                    ──┤
itemCompositionSummary_df      ──┤
proStatus_df                   ──┘
mold_stability_index           ──┘
```

### Performance Classification Logic
```
Production Efficiency Flow:
┌─────────────────────┐    ┌──────────────────────┐
│   Calculate:        │───▶│   Performance        │
│   • Theoretical     │    │   Classification:    │
│     shifts needed   │    │   • actualShifts ≤   │
│   • Actual shifts   │    │     estimatedShifts  │
│     used           │    │     → GOOD           │
└─────────────────────┘    │   • actualShifts >   │
                           │     estimatedShifts  │
                           │     → BAD            │
                           └──────────────────────┘

Efficiency Calculation:
net_efficiency = efficiency - loss
estimatedShifts = theoreticalShifts / net_efficiency
```

### Target Evaluation Framework
```
Feature Targets:
├── 🎯 shiftNGRate: 'minimize' (Lower is better)
├── 🎯 shiftCavityRate: 1.0 (Target value)
├── 🎯 shiftCycleTimeRate: 1.0 (Target value)
└── 🎯 shiftCapacityRate: 1.0 (Target value)

Confidence Scoring (per feature):
confidence = target_achievement × 0.4 +
            separation_confidence × 0.3 +
            statistical_significance × 0.2 +
            distance_from_ideal × 0.1
```

## Statistical Analysis Components

### Bootstrap Sampling Process
```
🎲 Bootstrap Methodology:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Good Sample   │───▶│   n_bootstrap    │───▶│  Confidence     │
│   Bad Sample    │    │   iterations     │    │  Intervals      │
│                 │    │   (default: 500) │    │  (95% level)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Statistical     │
                       │  Significance    │
                       │  (Mann-Whitney)  │
                       └──────────────────┘
```

### Confidence Score Components
```
For each feature:
├── 📊 good_confidence: How well good samples meet targets
├── 📊 bad_confidence: How well bad samples deviate from targets  
├── 📊 separation_confidence: Statistical separation between groups
├── 📊 statistical_significance: P-value from Mann-Whitney U test
├── 📈 sample_size_good: Number of good performance records
├── 📈 sample_size_bad: Number of bad performance records
└── ⚠️ warnings: Issues with data quality or sample size
```

## Output Structure

### Report File Organization
```
📋 agents/shared_db/FeatureWeightCalculator/
├── 📄 confidence_report_YYYYMMDD_HHMMSS.txt (Detailed analysis)
└── 📊 confidence_report_YYYYMMDD_HHMMSS_weights.json (Enhanced weights)
```

### Enhanced Weight Calculation
```
Enhanced Weight Formula:
enhanced_weight = traditional_weight × (1 + separation_confidence × confidence_weight)

Where:
├── traditional_weight: Based on deviation from targets
├── separation_confidence: Statistical separation between good/bad groups
└── confidence_weight: Adjustment factor (default: 0.3)
```

### Key Performance Indicators
```
Model Reliability Metrics:
├── 📊 overall_good_confidence: Weighted average confidence for good group
├── 📊 overall_bad_confidence: Weighted average confidence for bad group  
├── 📊 model_reliability: Overall model separation capability
├── 📈 valid_features_ratio: Proportion of features with reliable data
└── ⚠️ total_features vs valid_features: Data quality assessment
```

## Error Handling & Validation

### Pre-execution Checks
- ✅ File path validation for mold stability index
- ✅ Schema compliance verification for all DataFrames
- ✅ Required column presence validation
- ✅ Minimum sample size requirements

### Runtime Safety
- 🛡️ Bootstrap sampling error handling
- 🛡️ Division by zero protection in efficiency calculations
- 🛡️ Missing feature handling with warning generation
- 🛡️ Statistical test failure recovery
- 🛡️ Empty DataFrame handling for good/bad groups

### Data Quality Safeguards
```
Sample Size Validation:
├── Minimum required: min_sample_size (default: 10)
├── Insufficient data → Neutral confidence (0.5)
└── Warning generation for unreliable features

Statistical Robustness:
├── Bootstrap sampling with seed for reproducibility
├── Confidence interval calculation with configurable level
├── Non-parametric testing (Mann-Whitney U)
└── Outlier-resistant performance metrics
```

## Usage Examples

### Basic Usage
```python
# Initialize with default parameters
calculator = FeatureWeightCalculator(
    efficiency=0.85,
    loss=0.03,
    confidence_weight=0.3
)

# Calculate confidence scores and enhanced weights
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()
```

### Advanced Configuration
```python
# Custom configuration
calculator = FeatureWeightCalculator(
    efficiency=0.90,
    loss=0.02,
    scaling='relative',
    confidence_weight=0.4,
    n_bootstrap=1000,
    confidence_level=0.99,
    targets={
        'shiftNGRate': 'minimize',
        'shiftCavityRate': 0.95,
        'shiftCycleTimeRate': 1.05,
        'shiftCapacityRate': 0.98
    }
)

# Generate and save comprehensive report
calculator.calculate_and_save_report()
```

### Output Integration
```python
# Use enhanced weights in other systems
with open('enhanced_weights.json', 'r') as f:
    weights = json.load(f)
    
# Apply weights in optimization algorithms
optimizer.set_feature_weights(weights)
```

## Integration Points

### Upstream Dependencies
- **OrderProgressTracker**: Provides production status data
- **HistoryProcessor**: Supplies mold stability index
- **HistBasedItemMoldOptimizer**: Processes mold information
- **DataLoaderAgent**: Provides core manufacturing datasets
- **Database Schemas**: Defines data structure contracts

### Downstream Consumers
- **Production Optimization**: Enhanced weight parameters
- **Quality Control**: Confidence-based feature selection
- **Performance Monitoring**: Statistical reliability metrics
- **Decision Support Systems**: Evidence-based weight recommendations

## Performance Characteristics

### Computational Complexity
```
Time Complexity: O(n × m × b)
Where:
├── n: Number of records in historical data
├── m: Number of features analyzed  
└── b: Number of bootstrap iterations

Space Complexity: O(n + b × m)
├── Historical data storage: O(n)
└── Bootstrap sample storage: O(b × m)
```

### Scalability Considerations
- **Bootstrap sampling**: Configurable iterations vs accuracy trade-off
- **Feature selection**: Automatic filtering of unreliable features
- **Memory management**: Efficient DataFrame operations with pandas
- **Statistical robustness**: Non-parametric methods for various data distributions