>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# HybridSuggestOptimizer

## 1. Agent Info
- **Name**: HybridSuggestOptimizer
- **Purpose**: 
  - Optimize mold-machine allocation using hybrid historical analysis and real-time compatibility matching
  - Provide data-driven recommendations for production planning and capacity estimation
- **Owner**: 
- **Status**: Active
- **Location**: `agents/autoPlanner/initialPlanner/`

---

## 2. What it does
The `HybridSuggestOptimizer` combines multiple optimization strategies to suggest optimal production configurations. It integrates (1) `historical-based mold capacity estimation` ([ItemMoldCapacityOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_itemMoldCapacityOptimizer_review.md)) using performance data, and (2) `feature weight-based mold-machine priority matrix calculation` ([MoldMachinePriorityMatrixCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_moldMachinePriorityMatrixCalculator_review.md)). The system helps manufacturing operations make intelligent decisions about mold selection, machine allocation, and production scheduling.

---

## 3. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Historical Data │ -> │ HybridSuggest    │ -> │ Optimization    │
│ & Stability     │    │ Optimizer        │    │ Results         │
│ Index           │    └──────────────────┘    └─────────────────┘
└─────────────────┘             │                       │
         │                      v                       v
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ Mold Specs  │        │ Capacity    │        │ Priority    │
   │ Feature     │        │ Estimation  │        │ Matrix &    │
   │ Weights     │        │ Engine      │        │ Reports     │
   └─────────────┘        └─────────────┘        └─────────────┘
```
→ See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_hybridSuggestOptimizerWorkflow.md)

---

## 4. Pre-requisites Checklist
Before running the optimizer, ensure:

- [ ] **Source data available**: Mold specifications (.parquet) and stability indices (.xlsx)
- [ ] **Schema validation**: `databaseSchemas.json` and `sharedDatabaseSchemas.json` accessible
- [ ] **Path annotations**: `path_annotations.json` with correct file mappings
- [ ] **Historical data**: Feature weights and stability index files exist
- [ ] **Write permissions**: Access to `agents/shared_db/` directory
- [ ] **Python dependencies**: pandas, loguru, pathlib, dataclasses
- [ ] **Configuration**: Valid efficiency (0-1) and loss (0-1) parameters

---

## 5. Optimization Scenarios

| Scenario | Capacity Estimation | Priority Matrix | Final Status | Action Required |
|----------|-------------------|-----------------|--------------|-----------------|
| Full Success | ✅ Valid molds | ✅ Complete matrix | `success` | None |
| Partial Capacity Issues | ⚠️ Some invalid molds | ✅ Reduced matrix | `partial_success` | Review invalid molds |
| Priority Calculation Fail | ✅ Good capacity data | ❌ Matrix failed | `capacity_only` | Check feature weights |
| Historical Data Missing | ⚠️ Default structure | ⚠️ Default weights | `degraded_mode` | Collect more data |
| Complete Failure | ❌ No valid data | ❌ No matrix | `failed` | Full data review |

---

## 6. Input & Output
- **Input**: Historical production data, mold specifications, stability indices, feature weights
- **Output**: Optimization results with capacity estimates and priority matrices
- **Format**: `OptimizationResult` dataclass with structured components

---

## 7. Simple Workflow
```
Config Validation → Load Historical Data → Estimate Mold Capacities → Calculate Priority Matrix → Generate Results
```

**Detailed Steps:**
1. **Initialization**: Load and validate all required DataFrames with schema checking
2. **Data Loading**: Import mold stability indices and feature weights from latest available sources
3. **Capacity Estimation**: Use `ItemMoldCapacityOptimizer` to analyze historical performance
4. **Priority Calculation**: Apply `MoldMachinePriorityMatrixCalculator` with weighted features
5. **Validation**: Verify results against expected schemas and data quality standards
6. **Results Assembly**: Package all outputs into structured `OptimizationResult` container

---

## 8. Dependencies
- **ItemMoldCapacityOptimizer**: Estimates production capacity from historical data
- **MoldMachinePriorityMatrixCalculator**: Creates compatibility priority matrices
- **Schema Validators**: Ensures data integrity with `@validate_init_dataframes`
- **Data Utilities**: File loading, change log reading, path annotation management
- **loguru**: Contextual logging with class-specific binding

---

## 9. How to Run

### 9.1 Basic Usage
```python
# Initialize with database schemas
optimizer = HybridSuggestOptimizer(
    databaseSchemas_data=db_schemas,
    sharedDatabaseSchemas_data=shared_schemas
)

# Run complete optimization
result = optimizer.process()

# Check optimization results
print(f"Invalid capacity molds: {len(result.estimated_capacity_invalid_molds)}")
print(f"Invalid priority molds: {len(result.priority_matrix_invalid_molds)}")
print(f"Estimated capacity shape: {result.mold_estimated_capacity_df.shape}")
```

### 9.2 Custom Configuration
```python
# Initialize with custom parameters
optimizer = HybridSuggestOptimizer(
    databaseSchemas_data=db_schemas,
    sharedDatabaseSchemas_data=shared_schemas,
    efficiency=0.90,  # Higher efficiency target
    loss=0.02,        # Lower loss expectation
    source_path="custom/data/path",
    mold_machine_weights_hist_path="custom/weights.xlsx"
)

# Run optimization
result = optimizer.process()
```

### 9.3 Development/Testing Mode
```python
# Validate configuration before running
optimizer = HybridSuggestOptimizer(db_schemas, shared_schemas)
is_valid = optimizer.validate_configuration()

if is_valid:
    result = optimizer.process()
else:
    print("Configuration validation failed")

# Check individual components
capacity_invalid, capacity_df = optimizer._estimate_mold_capacities(stability_index)
priority_matrix, priority_invalid = optimizer._calculate_priority_matrix(weights, capacity_df)
```

---

## 10. Result Structure
```python
@dataclass
class OptimizationResult:
    estimated_capacity_invalid_molds: List[str]        # Molds with estimation issues
    priority_matrix_invalid_molds: List[str]           # Molds with priority issues  
    mold_estimated_capacity_df: pd.DataFrame           # Capacity estimates per mold
    mold_machine_priority_matrix: pd.DataFrame         # Compatibility priority scores

# Example result access
result = optimizer.process()
valid_molds = len(result.mold_estimated_capacity_df)
total_invalid = len(result.estimated_capacity_invalid_molds) + len(result.priority_matrix_invalid_molds)
success_rate = valid_molds / (valid_molds + total_invalid)
```

---

## 11. Configuration Paths
- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (data source location)
- **annotation_name**: `path_annotations.json` (file path mappings)
- **default_dir**: `agents/shared_db` (base shared database directory)
- **folder_path**: `agents/OrderProgressTracker` (progress tracking location)
- **mold_stability_index_folder**: `agents/MoldStabilityIndexCalculator/mold_stability_index`
- **mold_machine_weights_hist_path**: `agents/MoldMachineFeatureWeightCalculator/weights_hist.xlsx`

---

## 12. Common Issues & Solutions

| Problem | Symptoms | Quick Fix | Prevention |
|---------|----------|-----------|------------|
| Schema validation fails | DataFrame columns mismatch | Check database schema files | Regular schema updates |
| Stability index missing | Warning logs, empty DataFrame | Run MoldStabilityIndexCalculator | Automated data collection |
| Feature weights invalid | Default weights used | Validate weights_hist.xlsx format | Weight calculation monitoring |
| High invalid mold count | Many molds excluded from results | Review data quality and thresholds | Improve data collection |
| Efficiency/Loss out of range | Configuration validation error | Adjust parameters (0 < efficiency ≤ 1, 0 ≤ loss < 1) | Parameter validation in config |
| Path annotations missing | FileNotFoundError | Check DataLoaderAgent output | Ensure pipeline execution order |

---

## 13. Feature Weights Configuration

### 13.1 Default Weight Distribution
```python
DEFAULTS = {
    'shiftNGRate_weight': 0.1,       # Defect rate (10%)
    'shiftCavityRate_weight': 0.25,  # Cavity utilization (25%)  
    'shiftCycleTimeRate_weight': 0.25, # Cycle time efficiency (25%)
    'shiftCapacityRate_weight': 0.4   # Overall capacity (40% - highest priority)
}
```

### 13.2 Weight Validation Rules
- All weights must be numeric and non-negative
- Total weight sum should be between 0.5 and 2.0 (flexible range around 1.0)
- All required columns must be present in the weights series
- Missing or invalid weights trigger fallback to defaults

---

## 14. Monitoring & Observability

### 14.1 Log Levels & Indicators
- **🚀 INFO**: Optimizer startup and component initialization
- **📊 DEBUG**: DataFrame shapes and column information
- **✅ INFO**: Successful optimization completion with metrics
- **⚠️ WARNING**: Data quality issues and fallback actions
- **❌ ERROR**: Critical failures in optimization process
- **🔄 INFO**: Data loading and processing milestones

### 14.2 Key Metrics to Track
- **Invalid Mold Rates**: Percentage of molds excluded from optimization
- **Capacity Estimation Success**: Ratio of valid capacity estimates
- **Priority Matrix Coverage**: Percentage of mold-machine combinations covered
- **Feature Weight Stability**: Changes in historical weight patterns
- **Processing Performance**: Execution time trends and bottlenecks
- **Data Freshness**: Age of stability index and feature weight data

### 14.3 Health Checks
```python
# Optimization health check
def optimizer_health_check():
    optimizer = HybridSuggestOptimizer(db_schemas, shared_schemas)
    
    # Validate configuration
    config_valid = optimizer.validate_configuration()
    
    # Check data availability
    has_stability_data = Path(optimizer.mold_stability_index_folder).exists()
    has_feature_weights = Path(optimizer.mold_machine_weights_hist_path).exists()
    
    # Test optimization (dry run)
    try:
        result = optimizer.process()
        optimization_success = True
        invalid_rate = (len(result.estimated_capacity_invalid_molds) + 
                       len(result.priority_matrix_invalid_molds)) / max(1, len(result.mold_estimated_capacity_df))
    except Exception:
        optimization_success = False
        invalid_rate = 1.0
    
    return {
        "configuration_valid": config_valid,
        "data_sources_available": has_stability_data and has_feature_weights,
        "optimization_success": optimization_success,
        "invalid_mold_rate": invalid_rate,
        "service_status": "healthy" if all([config_valid, optimization_success, invalid_rate < 0.3]) else "degraded"
    }
```