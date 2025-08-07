# HybridSuggestOptimizer Workflow Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HybridSuggestOptimizer                              │
│                   Manufacturing Production Configuration Pipeline           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🔧 INITIALIZATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Load configuration files (schemas, path annotations)                     │
│ • Validate and load core manufacturing datasets                            │
│ • Setup production parameters (efficiency: 85%, loss: 3%)                 │
│ • Initialize HistoryProcessor for mold-machine analysis                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   📊 HYBRID OPTIMIZATION PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Steps

### Phase 1: Initialization & Configuration Loading

```
┌──────────────────────────────────────┐
│        Class Constructor             │
│    HybridSuggestOptimizer()          │
└──────────────┬───────────────────────┘
               │
               ├─ Load path_annotations.json
               ├─ Load databaseSchemas.json
               ├─ Set production parameters (efficiency=0.85, loss=0.03)
               ├─ Configure mold stability index path
               │
               ▼
┌──────────────────────────────────────┐
│     Load Core Manufacturing Data     │
├──────────────────────────────────────┤
│ 📄 moldSpecificationSummary_df       │
│ 📄 moldInfo_df                       │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   @validate_init_dataframes          │
│   Schema Validation                  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Initialize HistoryProcessor        │
│   Setup logging system               │
└──────────────────────────────────────┘
```

### Phase 2: Hybrid Optimization Pipeline

```
                    process() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │                 Step 1: Load Mold Stability Index      │
    │ Method: _load_mold_stability_index()                   │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Check for existing stability index:                │
    │    • Load from HistoryProcessor/mold_stability_index   │
    │    • Handle change_log.txt for version tracking        │
    │ 📊 Fallback Strategy:                                  │
    │    • Create empty DataFrame if no data exists           │
    │    • Log warning for missing historical data            │
    │ 🏷️  Output: mold_stability_index DataFrame             │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 2: Historical Mold Capacity Analysis │
    │ Method: HistBasedItemMoldOptimizer().process()         │
    ├────────────────────────────────────────────────────────┤
    │ 🔧 Initialize HistBasedItemMoldOptimizer:              │
    │    • Pass core DataFrames and stability index          │
    │    • Configure efficiency and loss parameters          │
    │ 🧮 Mold Capacity Estimation Process:                   │
    │    • Analyze historical production performance         │
    │    • Calculate theoretical vs actual capacity          │
    │    • Generate mold stability metrics                   │
    │ 📈 Capacity Calculations:                              │
    │    • theoreticalMoldHourCapacity                       │
    │    • effectiveMoldHourCapacity                         │
    │    • estimatedMoldHourCapacity                         │
    │    • balancedMoldHourCapacity                          │
    │ 📊 Output: invalid_molds, mold_estimated_capacity_df   │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 3: Feature Weights Loading           │
    │ Method: _load_feature_weights()                        │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Load Historical Weights:                            │
    │    • Check agents/FeatureWeightCalculator/weights_hist.xlsx │
    │    • Extract latest calculated weights                 │
    │ ⚖️  Default Weight Fallback:                           │
    │    • shiftNGRate_weight: 0.1 (10%)                    │
    │    • shiftCavityRate_weight: 0.25 (25%)               │
    │    • shiftCycleTimeRate_weight: 0.25 (25%)            │
    │    • shiftCapacityRate_weight: 0.4 (40%)              │
    │ 📊 Validation:                                         │
    │    • Ensure weights sum to 1.0                        │
    │    • Log weight configuration for verification        │
    │ 🏷️  Output: feature_weights Series                     │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 4: Mold-Machine Priority Matrix      │
    │ Method: HistoryProcessor.get_mold_machine_priority()   │
    ├────────────────────────────────────────────────────────┤
    │ 🔗 Data Integration:                                   │
    │    • Merge mold_estimated_capacity_df with weights    │
    │    • Include machine compatibility information        │
    │ 🧮 Priority Score Calculation:                         │
    │    • Weighted sum of performance metrics:             │
    │      priority = Σ(weight_i × performance_metric_i)    │
    │ 📊 Matrix Generation:                                  │
    │    • Rows: Molds (moldNo, moldName)                   │
    │    • Columns: Machines (machineNo, tonnage)           │
    │    • Values: Priority scores (1-N scale)              │
    │ 🎯 Optimization Criteria:                              │
    │    • High capacity utilization                        │
    │    • Low defect rates                                 │
    │    • Optimal cycle times                              │
    │    • Machine-mold tonnage compatibility               │
    │ 🏷️  Output: mold_machine_priority_matrix DataFrame     │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 5: Results Compilation & Validation  │
    │ Method: process() return statement                     │
    ├────────────────────────────────────────────────────────┤
    │ ✅ Quality Validation:                                 │
    │    • Verify mold capacity estimates completeness       │
    │    • Validate priority matrix dimensions              │
    │    • Check for invalid mold entries                   │
    │ 📊 Performance Metrics:                                │
    │    • Total molds processed vs invalid count           │
    │    • Matrix density (non-zero priority scores)        │
    │    • Processing time and memory usage                 │
    │ 📋 Return Tuple:                                       │
    │    • invalid_molds: List[str]                         │
    │    • mold_estimated_capacity_df: DataFrame            │
    │    • mold_machine_priority_matrix: DataFrame          │
    │ 📝 Logging Summary:                                    │
    │    • Process completion status                        │
    │    • Key statistics and warnings                      │
    └────────────────────────────────────────────────────────┘
```

## Key Data Transformations

### Input Data Sources
```
moldSpecificationSummary_df    ──┐
moldInfo_df                    ──┼─► Production Optimization
mold_stability_index           ──|
feature_weights                ──┘
```

### Capacity Estimation Logic
```
Mold Capacity Analysis Flow:
┌─────────────────────┐    ┌──────────────────────┐
│   Historical Data:  │───▶│   Capacity Types:    │
│   • Production      │    │   • Theoretical      │
│     records         │    │   • Effective        │
│   • Cycle times     │    │   • Estimated        │
│   • Mold cavity     │    │   • Balanced         │
└─────────────────────┘    └──────────────────────┘
```

### Priority Score Calculation
```
Mold-Machine Priority Matrix:
┌─────────────────────┐    ┌──────────────────────┐
│   Performance       │───▶│   Weighted Score:    │
│   Metrics:          │    │                      │
│   • shiftNGRate     │    │   priority_score =   │
│   • shiftCavityRate │    │   Σ(weight_i ×       │
│   • shiftCycleTime  │    │     metric_i)        │
│   • shiftCapacity   │    │                      │
└─────────────────────┘    └──────────────────────┘
```

## Statistical Analysis Components

### Mold Stability Assessment
```
🔍 Stability Index Methodology:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Historical    │───▶│   Consistency    │──▶│   Stability     │
│   Performance   │    │   Metrics:       │    │   Classification│
│   Data          │    │   • Cavity       │    │   • High        │
│                 │    │   • Cycle Time   │    │   • Medium      │
└─────────────────┘    └──────────────────┘    │   • Low         │
                                               └─────────────────┘
```

### Capacity Reliability Scoring
```
For each mold:
├── 📊 cavityStabilityIndex: Consistency of cavity utilization
├── 📊 cycleStabilityIndex: Consistency of cycle times
├── 📈 totalRecords: Historical data depth
├── 📈 totalCavityMeasurements: Cavity data points
├── 📈 totalCycleMeasurements: Cycle time data points
└── 📅 firstRecordDate - lastRecordDate: Time span coverage
```

## Output Structure

### Mold Estimated Capacity DataFrame Columns
```
📋 mold_estimated_capacity_df Structure:
├── 🔑 moldNo: Unique mold identifier
├── 📝 moldName: Human-readable mold name  
├── 📅 acquisitionDate: Mold procurement date
├── 🏋️ machineTonnage: Required machine tonnage
├── 🕳️ moldCavityStandard: Standard cavity count
├── ⏱️ moldSettingCycle: Standard cycle time (seconds)
├── 📊 cavityStabilityIndex: Cavity consistency metric
├── 📊 cycleStabilityIndex: Cycle time consistency metric
├── 🎯 theoreticalMoldHourCapacity: Maximum possible rate
├── ⚡ effectiveMoldHourCapacity: Efficiency-adjusted rate
├── 📈 estimatedMoldHourCapacity: Predicted actual rate
├── ⚖️ balancedMoldHourCapacity: Optimized production rate
├── 📊 totalRecords: Historical data count
├── 📊 totalCavityMeasurements: Cavity data points
├── 📊 totalCycleMeasurements: Cycle data points
├── 📅 firstRecordDate: Earliest historical record
└── 📅 lastRecordDate: Latest historical record
```

### Priority Matrix Structure  
```
📊 mold_machine_priority_matrix Structure:
├── Index: Multi-level (moldNo, moldName)
├── Columns: Machine identifiers or tonnage groups
├── Values: Priority scores
├── Special Values:
│   ├── 0: Incompatible combination
│   ├── NaN: No historical data
│   └── 1,2,3...: Viable priority ranking
```

### Invalid Molds Tracking
```
📋 invalid_molds List Content:
├── Molds without historical production data
├── Molds with insufficient data points
├── Molds with corrupted performance records
├── Molds incompatible with any available machines
└── Molds with missing essential specifications
```

## Error Handling & Validation

### Pre-execution Checks
- ✅ Schema validation for all input DataFrames
- ✅ Required column presence verification
- ✅ Path existence validation for stability index
- ✅ Feature weights file accessibility check
- ✅ Production parameter bounds validation

### Runtime Safety Mechanisms
```
Data Quality Safeguards:
├── Empty DataFrame handling for stability index
├── Missing feature weights fallback to defaults
├── Invalid mold identification and exclusion
├── Division by zero protection in capacity calculations
├── Tonnage compatibility validation
└── Matrix dimension consistency checks

Processing Resilience:
├── 🛡️ Parquet file corruption recovery
├── 🛡️ Memory optimization for large datasets
├── 🛡️ Logging for debugging and monitoring
├── 🛡️ Graceful degradation with partial data
└── 🛡️ Configuration parameter validation
```

### Data Integrity Validation
```
Validation Checkpoints:
┌─────────────────────┐    ┌──────────────────────┐
│   Input Stage:      │───▶│   Processing Stage:  │
│   • Schema          │    │   • Capacity logic   │
│     compliance      │    │   • Weight bounds    │
│   • Required        │    │   • Matrix density   │
│     columns         │    │   • Score ranges     │
└─────────────────────┘    └──────────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────┐
                           │   Output Stage:      │
                           │   • Result           │
                           │     completeness     │
                           │   • Invalid mold     │
                           │     documentation    │
                           └──────────────────────┘
```

## Integration Points

### Upstream Dependencies
```
Data Sources:
├── 📊 DataLoaderAgent: Core manufacturing datasets
├── 📈 HistoryProcessor: Mold stability indices  
├── ⚖️ FeatureWeightCalculator: Performance weights
├── 📋 OrderProgressTracker: Production status
└── 🗂️ Database Schemas: Data structure contracts
```

### Downstream Consumers
```
Optimization Systems:
├── 🎯 Production Scheduler: Mold-machine assignments
├── 📊 Capacity Planner: Production volume estimation
├── 🔧 Resource Allocator: Equipment utilization
├── 📈 Performance Monitor: Efficiency tracking
└── 🎲 Decision Support: Strategic planning tools
```

## Performance Characteristics

### Computational Complexity
```
Time Complexity: O(M × N × H)
Where:
├── M: Number of unique molds
├── N: Number of available machines  
└── H: Historical data records per mold

Space Complexity: O(M × N + H)
├── Priority matrix storage: O(M × N)
└── Historical data processing: O(H)
```

### Scalability Considerations
```
Optimization Strategies:
├── 📊 Parquet format for efficient data I/O
├── 🔄 Incremental processing for large datasets
├── 💾 Memory-conscious DataFrame operations
├── 🎯 Selective loading based on date ranges
├── 🔧 Configurable batch processing sizes
└── ⚡ Parallel processing for independent molds
```

## Usage Examples

### Basic Usage
```python
# Initialize with default configuration
optimizer = HybridSuggestOptimizer()

# Execute complete optimization pipeline
invalid_molds, capacity_df, priority_matrix = optimizer.process()

# Analyze results
print(f"Successfully processed: {len(capacity_df)} molds")
print(f"Invalid molds: {len(invalid_molds)}")
print(f"Priority matrix shape: {priority_matrix.shape}")
```

### Advanced Configuration
```python
# Custom parameters for high-precision environment  
optimizer = HybridSuggestOptimizer(
    efficiency=0.90,           # Higher efficiency target
    loss=0.02,                 # Lower loss expectation
    source_path='custom/data', # Custom data location
    mold_stability_index_folder='custom/stability'
)

# Process with logging
results = optimizer.process()
capacity_df = results[1]

# Extract high-priority combinations
best_combinations = priority_matrix[priority_matrix > 0.8]
```

### Integration with Planning Systems
```python
# Initialize optimizer
optimizer = HybridSuggestOptimizer()
invalid_molds, capacity_df, priority_matrix = optimizer.process()

# Use in production planning
scheduler = ProductionScheduler()
scheduler.set_mold_capacities(capacity_df)
scheduler.set_priority_matrix(priority_matrix)

# Generate optimized production plan
production_plan = scheduler.generate_plan(orders_df)
```

## Key Performance Indicators

### Process Success Metrics
```
Optimization Quality KPIs:
├── 📊 Valid Mold Ratio: (Total - Invalid) / Total molds
├── 📊 Matrix Coverage: Non-zero priorities / Total combinations  
├── 📊 Capacity Estimation Accuracy: Theoretical vs Historical variance
├── 📊 Processing Time: Total pipeline execution duration
├── 📊 Memory Efficiency: Peak memory usage / Data size ratio
└── 📊 Data Freshness: Age of newest historical records used
```

### Business Impact Indicators  
```
Manufacturing Optimization Value:
├── 🎯 Production Efficiency: Capacity utilization improvement
├── 🎯 Resource Allocation: Machine-mold matching optimization
├── 🎯 Quality Improvement: Defect rate reduction potential
├── 🎯 Cycle Time Optimization: Production speed enhancement
├── 🎯 Equipment Utilization: Machine availability maximization
└── 🎯 Planning Accuracy: Forecast vs actual production alignment
```