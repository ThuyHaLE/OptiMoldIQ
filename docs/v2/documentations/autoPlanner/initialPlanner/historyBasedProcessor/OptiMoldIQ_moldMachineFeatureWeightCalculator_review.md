>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# MoldMachineFeatureWeightCalculator

## 1. Agent Info

- **Name**: MoldMachineFeatureWeightCalculator
- **Purpose**:
  - Calculate feature weights for evaluating manufacturing process performance by analyzing production history
  - Generate confidence-based metrics using statistical bootstrap sampling methods
  - Provide enhanced weight calculations for Mold-Machine Priority Matrix Generation to support optimal production planning
- **Owner**: 
- **Status**: Active
- **Location**: `agents/autoPlanner/initialPlanner/historyBasedProcessor/`

---

## 2. What it does

The `MoldMachineFeatureWeightCalculator` processes **production history records** and **mold-machine performance data** against **efficiency thresholds** to generate confidence-weighted feature importance scores. It analyzes good vs bad production performance patterns using statistical methods to determine optimal weights for production planning priority matrices.

The calculator integrates bootstrap sampling, statistical significance testing, and confidence interval analysis to provide robust feature weight recommendations for manufacturing optimization decisions.

### Key Features

- **Performance Classification**
  - `GOOD`: Production achieving efficiency targets with acceptable loss rates
  - `BAD`: Production failing to meet efficiency or exceeding loss thresholds
  - Statistical separation based on shift utilization vs estimated requirements
  
- **Confidence Score Calculation**
  - Bootstrap sampling with configurable iterations (default: 500)
  - 95% confidence intervals for statistical reliability
  - Mann-Whitney U tests for group separation significance
  
- **Multi-Dimensional Feature Analysis**
  - `shiftNGRate`: Defect rate minimization (target: minimize)
  - `shiftCavityRate`: Cavity utilization efficiency (target: 1.0)
  - `shiftCycleTimeRate`: Cycle time performance (target: 1.0)  
  - `shiftCapacityRate`: Overall capacity utilization (target: 1.0)
  
- **Enhanced Weight Generation**
  - Traditional deviation-based weights
  - Confidence-adjusted weight enhancement
  - Normalized output for priority matrix integration
  
- **Statistical Validation**
  - Minimum sample size requirements (default: 10)
  - Bootstrap confidence interval estimation
  - Statistical significance testing integration

---

## 3. Architecture Overview

```
                    ┌─────────────────────────────┐
                    │ MoldMachineFeatureWeight    │
                    │ Calculator (Main Engine)    │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Production      │    │ Machine & Mold  │    │ Mold Stability  │
│ Records History │    │ Specifications  │    │ Index Data      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                                 v
                    ┌─────────────────────────┐
                    │ Performance Classifier  │
                    │ (Good vs Bad Analysis)  │
                    └─────────────┬───────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        v                         v                         v
┌───────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Bootstrap     │      │ Confidence Score │      │ Statistical     │
│ Sampling      │      │ Calculation      │      │ Testing Engine  │
│ Engine        │      │ Engine           │      │                 │
└───────┬───────┘      └─────────┬────────┘      └─────────┬───────┘
        │                        │                         │
        └────────────────────────┼─────────────────────────┘
                                 │
                                 v
                    ┌─────────────────────────┐
                    │ Enhanced Weight         │
                    │ Generation Engine       │
                    └─────────────┬───────────┘
                                  │
                                  v
                    ┌─────────────────────────┐
                    │ Confidence Report       │
                    │ Generation & Export     │
                    └─────────────────────────┘
```

---

## 4. Pre-requisites Checklist

Before running the calculator, ensure:

- [ ] **DataLoader output available**: Latest parquet files in `agents/shared_db/DataLoaderAgent/newest`
- [ ] **Path annotations accessible**: `path_annotations.json` with correct file paths
- [ ] **Core datasets available**: productRecords, machineInfo, moldSpecificationSummary, moldInfo
- [ ] **Production status logs**: Latest production status from OrderProgressTracker
- [ ] **Mold stability index**: Output from MoldStabilityIndexCalculator
- [ ] **Database schema files**: Both databaseSchemas.json and sharedDatabaseSchemas.json
- [ ] **Write permissions**: Full access to `agents/shared_db/MoldMachineFeatureWeightCalculator/`
- [ ] **Python dependencies**: pandas, numpy, scipy, loguru, pathlib
- [ ] **Statistical requirements**: Minimum sample sizes for reliable confidence calculation

---

## 5. Error Handling Scenarios

| Scenario | Data Load | Performance Classification | Confidence Calculation | Weight Generation | Final Status | Action Required |
|----------|-----------|---------------------------|------------------------|-------------------|--------------|-----------------|
| Happy Path | ✅ Success | ✅ Success | ✅ Success | ✅ Success | `success` | None |
| Missing Data | ❌ Failed | - | - | - | `failed` | Check input data sources |
| Schema Mismatch | ✅ Success | ❌ Failed | - | - | `failed` | Validate schema definitions |
| Insufficient Samples | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Review sample size requirements |
| No Performance Separation | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Check efficiency thresholds |
| Statistical Test Failure | ✅ Success | ✅ Success | ⚠️ Warning | ✅ Success | `partial_success` | Review data distribution |

---

## 6. Processing Pipeline

```
Data Loading → Capacity Optimization → Performance Classification → 
Bootstrap Sampling → Confidence Calculation → Weight Enhancement → Report Generation
```

**Detailed Steps**:

1. **Data Loading & Validation**
   - Load productRecords, machineInfo, moldInfo, moldSpecificationSummary from parquet
   - Validate schema compliance using decorators
   - Load mold stability index from previous calculation steps

2. **Mold Capacity Optimization**
   - Process ItemMoldCapacityOptimizer for estimated capacities
   - Merge with production records for comprehensive analysis
   - Validate output schema compliance

3. **Performance Classification**
   - Calculate theoretical production requirements (shots, time, shifts)
   - Apply efficiency and loss thresholds (default: 85% efficiency, 3% loss)
   - Classify production history into GOOD vs BAD performance groups
   - Group by PO, mold, and machine for aggregated analysis

4. **Statistical Bootstrap Sampling**
   - Generate bootstrap samples (default: 500 iterations) for each feature
   - Calculate bootstrap means and confidence intervals
   - Ensure reproducible results with fixed random seed

5. **Confidence Score Calculation**
   - Target-based scoring for each feature (minimize vs target achievement)
   - Separation confidence using CI overlap analysis
   - Statistical significance testing with Mann-Whitney U tests
   - Composite confidence scoring with weighted components

6. **Enhanced Weight Generation**
   - Calculate traditional weights based on performance deviation
   - Apply confidence factors to enhance weight reliability
   - Normalize final weights for priority matrix integration

7. **Report Generation & Export**
   - Generate comprehensive confidence reports
   - Export enhanced weights with versioning
   - Save detailed analysis results for audit and review

---

## 7. Input & Output

- **Input**: 
  - Production records (productRecords_df)
  - Machine specifications (machineInfo_df, moldInfo_df)
  - Mold specifications (moldSpecificationSummary_df)
  - Production status logs (proStatus_df)
  - Mold stability index data
  
- **Output**: 
  - Confidence scores dictionary with detailed statistics
  - Overall confidence metrics for model reliability
  - Enhanced feature weights for priority matrix generation
  - Text confidence report with analysis summary
  
- **Format**: 
  - Structured dictionaries with nested metrics
  - Versioned text reports with timestamp
  - Normalized weight arrays for downstream integration

---

## 8. Configuration Parameters

### 8.1 Performance Thresholds

```python
efficiency = 0.85      # 85% expected efficiency rate
loss = 0.03           # 3% allowable production loss
net_efficiency = 0.82  # Combined efficiency threshold
```

### 8.2 Statistical Parameters

```python
n_bootstrap = 500         # Bootstrap sampling iterations
confidence_level = 0.95   # 95% confidence intervals
min_sample_size = 10      # Minimum samples for reliability
confidence_weight = 0.3   # Weight of confidence in final calculation
```

### 8.3 Feature Targets Configuration

```python
targets = {
    'shiftNGRate': 'minimize',        # Minimize defect rates
    'shiftCavityRate': 1.0,          # Target 100% cavity utilization
    'shiftCycleTimeRate': 1.0,       # Target 100% cycle efficiency
    'shiftCapacityRate': 1.0         # Target 100% capacity utilization
}
```

---

## 9. Statistical Engine

### 9.1 Performance Classification Logic

```python
# Calculate theoretical requirements
moldFullTotalShots = itemQuantity / moldCavityStandard
moldFullTotalSeconds = moldFullTotalShots × moldSettingCycle
moldFullShiftUsed = moldFullTotalSeconds / (60×60×8)

# Apply efficiency adjustments
net_efficiency = efficiency - loss
moldEstimatedShiftUsed = moldFullShiftUsed / net_efficiency

# Classification logic
if actual_shifts > estimated_shifts:
    classification = 'BAD'
else:
    classification = 'GOOD'
```

### 9.2 Confidence Score Composition

| Component | Weight | Description |
|-----------|--------|-------------|
| **Target Achievement** | 40% | How well good group achieves targets vs bad group |
| **Separation Confidence** | 30% | Statistical separation between group confidence intervals |
| **Statistical Significance** | 20% | Mann-Whitney U test p-value significance |
| **Distance from Ideal** | 10% | Proximity to theoretical optimal performance |

### 9.3 Bootstrap Sampling Methodology

1. **Sample Generation**: Random sampling with replacement from good/bad groups
2. **Mean Estimation**: Calculate bootstrap mean for each iteration
3. **Confidence Intervals**: Percentile method for CI estimation
4. **Reproducibility**: Fixed random seed (42) for consistent results

---

## 10. Directory Structure

```
agents/shared_db                                              
└── MoldMachineFeatureWeightCalculator/ 
    ├── historical_db/                                      
    ├── newest/ 
    |   └── YYYYMMDD_HHMM_confidence_report.txt
    ├── change_log.txt      
    └── weights_hist.xlsx                          #auto update by adding rows                                       
```

---

## 11. Data Schema & Output Structure

### 11.1 Confidence Scores Output

```python
confidence_scores = {
    'feature_name': {
        'good_confidence': float,          # Confidence in good group performance
        'bad_confidence': float,           # Confidence in bad group performance  
        'separation_confidence': float,    # Statistical separation strength
        'statistical_significance': float, # Mann-Whitney U significance
        'sample_size_good': int,           # Good group sample count
        'sample_size_bad': int,            # Bad group sample count
        'good_mean': float,                # Good group mean value
        'bad_mean': float,                 # Bad group mean value
        'good_ci_lower': float,            # Good group CI lower bound
        'good_ci_upper': float,            # Good group CI upper bound
        'bad_ci_lower': float,             # Bad group CI lower bound
        'bad_ci_upper': float,             # Bad group CI upper bound
        'p_value': float                   # Statistical test p-value
    }
}
```

### 11.2 Overall Confidence Metrics

```python
overall_confidence = {
    'overall_good_confidence': float,      # Weighted overall good performance
    'overall_bad_confidence': float,       # Weighted overall bad performance
    'overall_separation_confidence': float, # Overall statistical separation
    'model_reliability': float,            # Combined model reliability score
    'valid_features_ratio': float,         # Ratio of reliable features
    'total_features': int,                 # Total features analyzed
    'valid_features': int                  # Features meeting reliability criteria
}
```

### 11.3 Enhanced Weights Output

```python
enhanced_weights = {
    'shiftNGRate': float,          # Normalized weight for NG rate
    'shiftCavityRate': float,      # Normalized weight for cavity rate
    'shiftCycleTimeRate': float,   # Normalized weight for cycle time
    'shiftCapacityRate': float     # Normalized weight for capacity
}
```

---

## 12. Dependencies

- **DataLoaderAgent**: Provides processed production and machine data
- **OrderProgressTracker**: Supplies production status logs
- **MoldStabilityIndexCalculator**: Provides mold stability metrics
- **ItemMoldCapacityOptimizer**: Generates capacity optimization data
- **Database Schemas**: Ensures data type consistency and validation
- **External Libraries**: pandas, numpy, scipy.stats, loguru

---

## 13. How to Run

### 13.1 Basic Usage

```python
# Initialize calculator
calculator = MoldMachineFeatureWeightCalculator()

# Run complete analysis
confidence_scores, overall_confidence, enhanced_weights = calculator.calculate()

# Generate and save report
calculator.calculate_and_save_report()
```

### 13.2 Custom Configuration

```python
# Custom parameters
calculator = MoldMachineFeatureWeightCalculator(
    efficiency=0.90,           # Higher efficiency requirement
    loss=0.02,                 # Lower loss tolerance
    confidence_weight=0.4,     # Higher confidence emphasis
    n_bootstrap=1000,          # More bootstrap iterations
    scaling='relative'         # Relative scaling method
)

# Run with custom settings
result = calculator.calculate()
```

### 13.3 Advanced Configuration

```python
# Custom targets and feature weights
custom_targets = {
    'shiftNGRate': 'minimize',
    'shiftCavityRate': 0.95,      # Target 95% instead of 100%
    'shiftCycleTimeRate': 1.05,   # Allow 5% cycle time variation
    'shiftCapacityRate': 0.98     # Target 98% capacity
}

calculator = MoldMachineFeatureWeightCalculator(
    targets=custom_targets,
    confidence_level=0.99,        # 99% confidence intervals
    min_sample_size=15           # Higher minimum sample requirement
)
```

---

## 14. Result Structure

```python
{
    # Detailed confidence analysis per feature
    "confidence_scores": {
        "shiftNGRate": {...},
        "shiftCavityRate": {...},
        "shiftCycleTimeRate": {...},
        "shiftCapacityRate": {...}
    },
    
    # Overall model performance metrics
    "overall_confidence": {
        "model_reliability": float,
        "overall_separation_confidence": float,
        "valid_features_ratio": float,
        ...
    },
    
    # Final enhanced weights for priority matrix
    "enhanced_weights": {
        "shiftNGRate": float,
        "shiftCavityRate": float,
        "shiftCycleTimeRate": float,  
        "shiftCapacityRate": float
    }
}
```

---

## 15. Configuration Paths

- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (processed parquet files)
- **annotation_name**: `path_annotations.json` (file path mappings)
- **databaseSchemas_path**: `database/databaseSchemas.json` (main data schemas)
- **sharedDatabaseSchemas_path**: `database/sharedDatabaseSchemas.json` (shared schemas)
- **folder_path**: `agents/shared_db/OrderProgressTracker` (production status logs)
- **target_name**: `change_log.txt` (production status source)
- **default_dir**: `agents/shared_db` (base output directory)
- **output_dir**: `agents/shared_db/MoldMachineFeatureWeightCalculator` (reports and logs)

---

## 16. Monitoring & Alerts

### 16.1 Key Performance Indicators

- **Model Reliability**: Overall confidence in feature weight calculations
- **Statistical Separation**: Strength of good vs bad group differentiation
- **Sample Size Adequacy**: Percentage of features meeting minimum sample requirements
- **Confidence Consistency**: Stability of confidence scores across bootstrap iterations
- **Weight Distribution**: Balance and reasonableness of final feature weights

### 16.2 Statistical Quality Metrics

- **Bootstrap Convergence**: Stability of bootstrap sampling results
- **P-Value Distribution**: Statistical significance across feature tests  
- **Confidence Interval Width**: Precision of statistical estimates
- **Feature Correlation**: Independence assumptions for weight calculations
- **Historical Stability**: Consistency of weight calculations over time

### 16.3 Operational Monitoring

- **Monthly Weight Updates**: Automated recalculation with new production data
- **Exception Handling**: Structured logging for statistical edge cases
- **Data Quality Integration**: Validation warnings impact on confidence scores
- **Performance Tracking**: Feature weight effectiveness in downstream applications
- **Audit Trail**: Versioned reports for reproducibility and compliance