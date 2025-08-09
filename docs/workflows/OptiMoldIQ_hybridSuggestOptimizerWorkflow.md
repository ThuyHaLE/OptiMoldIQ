# Phase 03 - Hybrid Suggest Optimization Workflow Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HybridSuggestOptimizer                               │
│                     Production Optimization Pipeline                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       🔧 INITIALIZATION PHASE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Configuration validation and parameter setup                              │
│ • Load database schemas and path annotations                                │
│ • Initialize core components and validate data sources                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 HYBRID OPTIMIZATION PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Steps

### Phase 1: Initialization & Configuration

```
┌──────────────────────────────────────┐
│        Class Constructor             │
│    HybridSuggestOptimizer()          │
└──────────────┬───────────────────────┘
               │
               ├─ Load databaseSchemas.json
               ├─ Load path_annotations.json
               ├─ Validate file paths and parameters
               │
               ▼
┌──────────────────────────────────────┐
│     Load Core Datasets               │
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
│   for Priority Matrix Generation     │
└──────────────────────────────────────┘
```

### Phase 2: Hybrid Optimization Processing

```
                    process() Method Called
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 1: Load Mold Stability Index         │
    │ Method: _load_mold_stability_index()                   │
    ├────────────────────────────────────────────────────────┤
    │ 📂 Read change_log.txt from stability index folder     │
    │ 📊 Load latest mold_stability_index.xlsx               │
    │ 🔄 Fallback to empty structure if file missing         │
    │ ✅ Validate required columns and data format           │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 2: Estimate Mold Capacities          │
    │ Method: _estimate_mold_capacities()                    │
    │ Component: HistBasedItemMoldOptimizer                  │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Process mold stability data with specifications     │
    │ 🧮 Calculate capacity metrics:                         │
    │    • theoreticalMoldHourCapacity                       │
    │    • effectiveMoldHourCapacity                         │
    │    • estimatedMoldHourCapacity                         │
    │    • balancedMoldHourCapacity                          │
    │ 📊 Apply trust coefficient: α = min(1.0, records/30)   │
    │ 🚫 Identify invalid molds (insufficient data)          │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 3: Load Feature Weights              │
    │ Method: _load_feature_weights()                        │
    ├────────────────────────────────────────────────────────┤
    │ 📂 Read weights_hist.xlsx from FeatureWeightCalculator │
    │ 📊 Extract latest weight row using get_latest_change_row│
    │ ✅ Validate weight columns and ranges                  │
    │ 🔄 Use default weights if file missing/invalid:       │
    │    • shiftCapacityRate: 0.4 (40%)                     │
    │    • shiftCavityRate: 0.25 (25%)                      │
    │    • shiftCycleTimeRate: 0.25 (25%)                   │
    │    • shiftNGRate: 0.1 (10%)                           │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 4: Calculate Priority Matrix         │
    │ Method: _calculate_priority_matrix()                   │
    │ Component: HistoryProcessor                            │
    ├────────────────────────────────────────────────────────┤
    │ 🔍 Prepare historical mold-machine data               │
    │ 📊 Filter completed orders (itemRemain = 0)           │
    │ 🧮 Calculate performance metrics per combination:      │
    │    • shiftNGRate, shiftCavityRate                     │
    │    • shiftCycleTimeRate, shiftCapacityRate            │
    │ ⚖️  Apply weighted scoring using feature weights       │
    │ 🏆 Convert scores to priority rankings (1=best)       │
    │ 📋 Create mold-machine priority matrix                 │
    └────────────────────┬───────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────────────────────┐
    │              Step 5: Result Compilation                │
    │ Return: OptimizationResult                             │
    ├────────────────────────────────────────────────────────┤
    │ 📦 Package results into structured container:          │
    │    • invalid_molds: List[str]                         │
    │    • mold_estimated_capacity_df: DataFrame            │
    │    • mold_machine_priority_matrix: DataFrame          │
    │ 📊 Log optimization summary and statistics            │
    │ ⏱️  Record processing time and performance metrics     │
    └────────────────────────────────────────────────────────┘
```

## Key Data Transformations

### Input Data Sources
```
Historical Stability Index  ──┐
                              ├─► Capacity Estimation
Feature Weights             ──┤
                              │
Mold Specifications         ──┤
                              ├─► Priority Matrix
Production Records          ──┤
                              │
Machine Information         ──┘
```

### Capacity Calculation Logic
```
Capacity Flow:
┌─────────────────┐    ┌─────────────────┐     ┌─────────────────┐
│   Theoretical   │───▶│   Effective     │───▶│   Balanced      │
│   Capacity      │    │   Capacity      │     │   Capacity      │
│3600/cycle*cavity│    │theoretical*     │     │α*effective +    │
│                 │    │stability        │     │(1-α)*estimated  │
└─────────────────┘    └─────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Estimated     │
                       │   Capacity      │
                       │theoretical*     │
                       │(efficiency-loss)│
                       └─────────────────┘

Trust Coefficient Logic:
• α = max(0.1, min(1.0, total_records / 30))
• More historical data → Higher trust in effective capacity
• Less historical data → Rely more on estimated capacity
```

### Priority Matrix Generation
```
Performance Metrics Calculation:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Historical Data  │───▶│Mold-Machine     │───▶│Weighted Score   │
│Processing       │    │Performance      │    │Calculation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │Priority Ranking │
                       │(1=highest)      │
                       └─────────────────┘

Weighted Score Formula:
total_score = Σ(metric_value × feature_weight)
where metrics = [NGRate, CavityRate, CycleTimeRate, CapacityRate]
```

## Output Structure

### OptimizationResult Container
```
📦 OptimizationResult
├── 🚫 invalid_molds (List[str])
│   └── Molds with insufficient historical data
├── 📊 mold_estimated_capacity_df (DataFrame)
│   ├── Basic Info: moldNo, moldName, acquisitionDate
│   ├── Specifications: moldCavityStandard, moldSettingCycle
│   ├── Stability: cavityStabilityIndex, cycleStabilityIndex
│   ├── Capacities: theoretical, effective, estimated, balanced
│   └── Quality: totalRecords, measurements, date ranges
└── 🏆 mold_machine_priority_matrix (DataFrame)
    ├── Rows: Mold identifiers (moldNo)
    ├── Columns: Machine codes (machineCode)
    └── Values: Priority rankings (1=best, 0=incompatible)
```

### Key Performance Indicators
```
For each Mold:
├── 📊 Capacity Estimates: Multiple calculation methods
├── 🎯 Stability Indices: Consistency metrics (0-1 scale)
├── 📈 Trust Level: Data quality coefficient (0.1-1.0)
├── 🏆 Machine Priorities: Ranked compatibility list
└── ⚠️ Data Quality: Record counts and time spans
```

## Error Handling & Validation

### Pre-execution Checks
- ✅ Configuration parameter validation (efficiency: 0-1, loss: 0-1)
- ✅ File path accessibility verification
- ✅ Database schema compliance
- ✅ Required DataFrame column presence

### Runtime Safety
- 🛡️ Missing stability index file handling
- 🛡️ Invalid feature weights recovery
- 🛡️ Empty DataFrame protection
- 🛡️ Division by zero prevention in calculations
- 🛡️ Data type conversion error handling

### Fallback Mechanisms
```
Stability Index Missing → Create empty structure
Feature Weights Missing → Use scientific defaults
Invalid Data → Skip with logging
Processing Errors → Graceful degradation
```

## Configuration Validation

### validate_configuration() Method
```
┌─────────────────┐    ┌─────────────────┐     ┌─────────────────┐
│Path Validation  │───▶│Parameter Check  │───▶│Data Availability│
│• source_path    │    │• 0<efficiency≤1 │     │• stability data │
│• schema_path    │    │• 0≤loss<1       │     │• feature weights│
│• stability_path │    │• weight ranges  │     │• DataFrames     │
└─────────────────┘    └─────────────────┘     └─────────────────┘
```

## Usage Example

```python
# Initialize optimizer with production parameters
optimizer = HybridSuggestOptimizer(
    source_path=f"{shared_db_dir}/DataLoaderAgent/newest",
    efficiency=0.85,  # 85% expected efficiency
    loss=0.03         # 3% expected loss
)

# Validate configuration before processing
if optimizer.validate_configuration():
    # Execute hybrid optimization
    result = optimizer.process()
    
    # Access optimization results
    invalid_molds = result.invalid_molds
    capacity_data = result.mold_estimated_capacity_df
    priority_matrix = result.mold_machine_priority_matrix
else:
    # Handle configuration issues
    logger.error("Configuration validation failed")
```

## Performance Optimization

### Efficiency Features
- ⚡ Vectorized pandas operations for data processing
- 💾 Memory-efficient data types (int8, int32, float32)
- 🔄 Lazy loading of large datasets
- 📊 Batch processing for capacity calculations

### Resource Management
- 🧠 Memory usage monitoring during processing
- ⏱️ Processing time tracking and optimization
- 📈 Performance metrics logging
- 🔧 Automatic garbage collection for large operations

## Integration Points

### Upstream Dependencies
- **HistoryProcessor**: Provides mold stability indices and performance analysis
- **FeatureWeightCalculator**: Supplies statistical feature importance weights
- **DataLoaderAgent**: Core production data through newest directory
- **OrderProgressTracker**: Current production status and progress tracking

### Downstream Consumers
- **Production Planning Systems**: Uses capacity estimates for resource allocation
- **Machine Assignment Algorithms**: Leverages priority matrix for optimal scheduling
- **Decision Support Dashboards**: Displays optimization insights for management
- **Performance Analytics**: Utilizes optimization data for continuous improvement