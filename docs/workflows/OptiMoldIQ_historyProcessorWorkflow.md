# HistoryProcessor Workflow Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HistoryProcessor                                 │
│                    Historical Data Analysis Pipeline                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🔧 INITIALIZATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Load configuration files (schemas, annotations)                           │
│ • Validate and load 5 core datasets                                        │
│ • Setup stability analysis parameters                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 DUAL ANALYSIS PIPELINE                               │
│                ┌─────────────────┬─────────────────┐                       │
│                │  Mold Stability │ Priority Matrix │                       │
│                │    Analysis     │   Generation    │                       │
│                └─────────────────┴─────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Steps

### Phase 1: Initialization & Data Loading

```
┌──────────────────────────────────────┐
│        Class Constructor             │
│      HistoryProcessor()              │
└──────────────┬───────────────────────┘
               │
               ├─ Load path_annotations.json
               ├─ Load databaseSchemas.json
               ├─ Load change_log.txt
               ├─ Set efficiency & loss parameters
               │
               ▼
┌──────────────────────────────────────┐
│     Load Core Datasets              │
├──────────────────────────────────────┤
│ 📄 productRecords_df                │
│ 📄 machineInfo_df                   │
│ 📄 moldSpecificationSummary_df      │
│ 📄 moldInfo_df                      │
│ 📄 proStatus_df (from change_log)   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   @validate_init_dataframes          │
│   Dual Schema Validation             │
│   • Main datasets validation         │
│   • Production status validation     │
└──────────────────────────────────────┘
```

### Phase 2A: Mold Stability Analysis Pipeline

```
              calculate_mold_stability_index() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 1: Data Preprocessing                │
    │ Method: df_processing()                                │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Filter records with moldShot > 0                    │
    │ 🧮 Calculate moldCycle = 28800 / moldShot              │
    │ 📊 Group by moldNo + recordDate                        │
    │ 🔗 Merge with moldInfo for standards                   │
    │ 📋 Fields: moldNo, moldName, recordDate,              │
    │           moldCavity, moldCavityStandard,              │
    │           moldCycle, moldSettingCycle                  │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │             Step 2: Cavity Stability Analysis          │
    │ Method: calculate_cavity_stability()                   │
    ├────────────────────────────────────────────────────────┤
    │ 📏 Accuracy Rate (40%):                               │
    │    • Count values matching standard                    │
    │    • accuracy_rate = correct_count / total_values      │
    │ 📈 Consistency Score (30%):                           │
    │    • Calculate coefficient of variation               │
    │    • consistency_score = max(0, 1 - cv)               │
    │ ⚡ Utilization Rate (20%):                            │
    │    • avg_cavity / standard_cavity                     │
    │ 📊 Data Completeness (10%):                           │
    │    • Penalty for insufficient records                 │
    │ Final Score: Weighted combination                      │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │             Step 3: Cycle Stability Analysis           │
    │ Method: calculate_cycle_stability()                    │
    ├────────────────────────────────────────────────────────┤
    │ 🎯 Accuracy Score (30%):                              │
    │    • Deviation from standard cycle time               │
    │    • accuracy_score = max(0, 1 - avg_deviation)       │
    │ 📊 Consistency Score (25%):                           │
    │    • Coefficient of variation of cycle times          │
    │ ✅ Range Compliance (25%):                            │
    │    • % values within ±20% of standard                │
    │ ⚠️ Outlier Penalty (10%):                             │
    │    • Penalty for extreme deviations (>100%)          │
    │ 📋 Data Completeness (10%):                           │
    │    • Record volume adequacy factor                    │
    │ Final Score: Weighted combination                      │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │           Step 4: Capacity Calculations                │
    ├────────────────────────────────────────────────────────┤
    │ 🏭 Theoretical Hour Capacity:                          │
    │    • 3600 / standard_cycle * standard_cavity          │
    │ ⚡ Effective Hour Capacity:                            │
    │    • theoretical * overall_stability                   │
    │ 📊 Estimated Hour Capacity:                           │
    │    • theoretical * (efficiency - loss)                │
    │ ⚖️ Balanced Hour Capacity:                             │
    │    • α * effective + (1-α) * estimated                │
    │    • α = trust coefficient from data volume           │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 5: Results Compilation               │
    ├────────────────────────────────────────────────────────┤
    │ 📊 Create comprehensive stability report:              │
    │    • Stability indices (cavity & cycle)               │
    │    • Capacity metrics (4 types)                       │
    │    • Record statistics & date ranges                  │
    │    • Mold metadata (tonnage, acquisition date)        │
    └────────────────────────────────────────────────────────┘
```

### Phase 2B: Priority Matrix Generation Pipeline

```
          calculate_mold_machine_priority_matrix() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │            Step 1: Load Feature Weights                │
    │ Method: _load_mold_machine_feature_weights()           │
    ├────────────────────────────────────────────────────────┤
    │ 📂 Read weights_hist.xlsx                              │
    │ 📊 Extract latest weight calculation                   │
    │ ✅ Validate weights file existence                     │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │          Step 2: Prepare Historical Data               │
    │ Method: _prepare_mold_machine_historical_data()        │
    ├────────────────────────────────────────────────────────┤
    │ 🏭 Get newest machine layout                           │
    │ 📋 Filter completed orders (itemRemain = 0)            │
    │ 🔗 Merge production status with machine info           │
    │ 📊 Prepare production records:                         │
    │    • Rename poNote → poNo                             │
    │    • Filter meaningful production data                 │
    │    • Include: dates, shifts, machines, items,         │
    │      POs, molds, shots, cavities, quantities          │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │         Step 3: Calculate Performance Metrics          │
    │ Method: _calculate_mold_machine_performance_metrics()  │
    ├────────────────────────────────────────────────────────┤
    │ 📊 Load/Calculate Mold Stability Index:               │
    │    • Try to read from change log                      │
    │    • If not found, calculate new index                │
    │ 🔧 Process mold information:                          │
    │    • Use HistBasedItemMoldOptimizer                   │
    │    • Generate capacity_mold_info_df                   │
    │ 📈 Summarize mold-machine history:                    │
    │    • Calculate performance results                     │
    │    • Generate historical summaries                     │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │           Step 4: Create Priority Matrix               │
    │ Method: _create_mold_machine_priority_matrix()         │
    ├────────────────────────────────────────────────────────┤
    │ ⚖️ Apply Weighted Scoring:                             │
    │    • total_score = Σ(feature × weight)                │
    │ 🔄 Create Pivot Table:                                │
    │    • Rows: moldNo, Columns: machineCode               │
    │    • Values: total_score                              │
    │ 🏆 Generate Priority Rankings:                        │
    │    • Apply rank_nonzero function                      │
    │    • 1 = highest priority, ascending order            │
    └────────────────────────────────────────────────────────┘
```

### Phase 3: Export & Versioning

```
                    save_output_with_versioning() Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │              Mold Stability Export                     │
    │ Method: calculate_and_save_mold_stability_index()      │
    ├────────────────────────────────────────────────────────┤
    │ 📁 Directory: agents/shared_db/HistoryProcessor/       │
    │              mold_stability_index/                     │
    │ 📊 Sheet: moldStabilityIndex                          │
    │ 🏷️  Filename: mold_stability_index_YYYYMMDD_HHMMSS.xlsx│
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Priority Matrix Export                    │
    │ Method: calculate_and_save_mold_machine_priority_matrix()│
    ├────────────────────────────────────────────────────────┤
    │ 📁 Directory: agents/shared_db/HistoryProcessor/       │
    │              priority_matrix/                          │
    │ 📊 Sheet: priorityMatrix                              │
    │ 🏷️  Filename: priority_matrix_YYYYMMDD_HHMMSS.xlsx    │
    └────────────────────────────────────────────────────────┘
```

## Key Data Transformations

### Input Data Sources
```
productRecords_df           ──┐
                              ├─► Mold Stability Analysis
moldInfo_df                 ──┤
                              │
proStatus_df               ──┤
                              ├─► Priority Matrix Generation
machineInfo_df             ──┤
                              │
moldSpecificationSummary_df ──┤
                              │
weights_hist.xlsx          ──┘
```

### Stability Analysis Logic
```
Mold Stability Calculation:
┌─────────────────┐    ┌─────────────────┐
│ Cavity Analysis │    │ Cycle Analysis  │
│ • Accuracy 40%  │    │ • Accuracy 30%  │
│ • Consistency 30%│    │ • Consistency 25%│
│ • Utilization 20%│    │ • Compliance 25%│
│ • Completeness10%│    │ • Outlier Pen10%│
│                 │    │ • Completeness10%│
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     ▼
         ┌─────────────────────────┐
         │   Overall Stability     │
         │ cavity×0.6 + cycle×0.4  │
         └─────────────────────────┘
```

### Priority Matrix Logic
```
Performance Scoring Flow:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Historical Data │───▶│ Feature Weights │───▶│ Priority Matrix │
│ • Efficiency     │    │ • Weight factors│    │ • Rankings 1-N  │
│ • Productivity   │    │ • Latest config │    │ • Mold×Machine  │
│ • Quality metrics│    │                 │    │ • Pivot format  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Algorithm Details

### Cavity Stability Scoring
```
Algorithm: calculate_cavity_stability()
Input: cavity_values[], standard_cavity, total_records

1. Accuracy Rate = correct_matches / total_values
2. Consistency = max(0, 1 - coefficient_of_variation)
3. Utilization = min(1.0, avg_cavity / standard_cavity)
4. Data Completeness = min(1.0, total_records / threshold)

Final Score = 0.4×accuracy + 0.3×consistency + 0.2×utilization + 0.1×completeness
```

### Cycle Stability Scoring
```
Algorithm: calculate_cycle_stability()
Input: cycle_values[], standard_cycle, total_records

1. Accuracy = max(0, 1 - avg_relative_deviation)
2. Consistency = max(0, 1 - coefficient_of_variation)
3. Range Compliance = in_range_count / total_values (±20%)
4. Outlier Penalty = max(0, 1 - extreme_outliers_ratio) (>100% dev)
5. Data Completeness = min(1.0, total_records / threshold)

Final Score = 0.3×accuracy + 0.25×consistency + 0.25×compliance + 0.1×penalty + 0.1×completeness
```

### Capacity Calculations
```
Theoretical Capacity = 3600 / standard_cycle × standard_cavity
Effective Capacity = theoretical × overall_stability
Estimated Capacity = theoretical × (efficiency - loss)
Balanced Capacity = α × effective + (1-α) × estimated

Where: α = trust_coefficient = min(1.0, total_records / threshold)
```

## Configuration Parameters

### Stability Analysis Constants
```python
SECONDS_PER_HOUR = 3600
CYCLE_TIME_TOLERANCE = 0.2  # ±20%
EXTREME_DEVIATION_THRESHOLD = 1.0  # 100%

# Default thresholds
cavity_stability_threshold = 0.6
cycle_stability_threshold = 0.4  
total_records_threshold = 30

# Default efficiency parameters
efficiency = 0.85  # 85%
loss = 0.03       # 3%
```

### Weight Configurations
```python
CYCLE_STABILITY_WEIGHTS = {
    'accuracy_score_weight': 0.3,
    'consistency_score_weight': 0.25,
    'range_compliance_weight': 0.25,
    'outlier_penalty_weight': 0.1,
    'data_completeness_weight': 0.1
}

CAVITY_STABILITY_WEIGHTS = {
    'accuracy_rate_weight': 0.4,
    'consistency_score_weight': 0.3,
    'utilization_rate_weight': 0.2,
    'data_completeness_weight': 0.1
}
```

## Output Structure

### Mold Stability Index Excel
```
📋 mold_stability_index_YYYYMMDD_HHMMSS.xlsx
└── 📊 moldStabilityIndex
    ├── 🏭 Basic Info: moldNo, moldName, acquisitionDate
    ├── 📏 Standards: moldCavityStandard, moldSettingCycle
    ├── 📊 Stability: cavityStabilityIndex, cycleStabilityIndex
    ├── ⚡ Capacity: theoretical, effective, estimated, balanced
    └── 📈 Statistics: totalRecords, measurements, date ranges
```

### Priority Matrix Excel
```
📋 priority_matrix_YYYYMMDD_HHMMSS.xlsx
└── 📊 priorityMatrix
    ├── 📋 Rows: moldNo (mold identifiers)
    ├── 📋 Columns: machineCode (machine identifiers)  
    └── 🏆 Values: Priority rankings (1=highest, 2=second, etc.)
```

## Error Handling & Validation

### Pre-execution Checks
- ✅ File path validation for all data sources
- ✅ Schema compliance for 5 core datasets
- ✅ Production status column validation
- ✅ Weights file existence verification

### Runtime Safety
- 🛡️ Division by zero protection (cycle times, cavities)
- 🛡️ Empty list handling in stability calculations
- 🛡️ Missing standard values management
- 🛡️ Automatic mold stability recalculation if files missing

### Data Quality Safeguards
- 📊 Minimum record threshold enforcement
- 📈 Outlier detection and handling
- 🔍 Standard value validation
- ⚠️ Logging for invalid mold configurations

## Usage Examples

### Basic Mold Stability Analysis
```python
# Initialize processor
processor = HistoryProcessor()

# Calculate and save mold stability index
processor.calculate_and_save_mold_stability_index(
    cavity_stability_threshold=0.6,
    cycle_stability_threshold=0.4,
    total_records_threshold=30
)
```

### Complete Priority Matrix Generation
```python
# Initialize processor with custom parameters
processor = HistoryProcessor(
    efficiency=0.85,
    loss=0.03
)

# Generate priority matrix
processor.calculate_and_save_mold_machine_priority_matrix(
    weights_hist_path='agents/shared_db/FeatureWeightCalculator/weights_hist.xlsx'
)
```

### Custom Configuration
```python
# Initialize with custom paths
processor = HistoryProcessor(
    source_path='custom/data/path',
    efficiency=0.90,
    loss=0.02
)

# Run both analyses
processor.calculate_and_save_mold_stability_index()
processor.calculate_and_save_mold_machine_priority_matrix()
```

## Integration Points

### Upstream Dependencies
- **DataLoaderAgent**: Provides productRecords, machineInfo, moldInfo datasets
- **OrderProgressTracker**: Supplies production status via change_log.txt
- **FeatureWeightCalculator**: Provides feature weights for priority matrix
- **ValidationOrchestrator**: Database schema definitions

### Downstream Consumers
- **AutoPlanner**: Uses priority matrix for optimal scheduling
- **Production Engineers**: Mold stability analysis for maintenance planning
- **Quality Control**: Stability metrics for process improvement
- **Capacity Planning**: Balanced capacity calculations for resource allocation

## Performance Optimization

### Data Processing Efficiency
- 📊 Vectorized operations using pandas/numpy
- 🔄 Efficient groupby operations for aggregations
- 📈 Minimal data copying through method chaining
- 🎯 Selective column loading to reduce memory usage

### Computational Complexity
- 🏭 Mold Stability: O(n×m) where n=molds, m=records per mold
- 🔄 Priority Matrix: O(p×q) where p=mold-machine pairs, q=features
- 📊 Overall: Linear scalability with production history size