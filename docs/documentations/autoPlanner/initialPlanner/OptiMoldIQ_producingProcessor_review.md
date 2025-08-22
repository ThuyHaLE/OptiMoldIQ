# ProducingProcessor

## 1. Agent Info
- **Name**: ProducingProcessor
- **Purpose**: 
  - Comprehensive processing of `manufacturing/molding/producing` data including `mold capacity`, `production planning`, and `plastic usage` calculations
  - Generate `detailed production, mold, and plastic plans` based on current production status and optimization results
- **Owner**: 
- **Status**: Active
- **Location**: `agents/autoPlanner/initialPlanner/`

---

## 2. What it does
The `ProducingProcessor` integrates production status data with optimization results from `hybrid_suggest_optimization`   ([HybridSuggestOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/dataPipelineOrchestrator/OptiMoldIQ_hybridSuggestOptimizer_review.md)) to create comprehensive manufacturing plans. It processes current production status (MOLDING, PAUSED, PENDING), calculates time metrics, estimates material consumption, and generates three distinct planning outputs: production schedules, mold utilization plans, and plastic material requirements. The system provides critical insights for manufacturing operations including production progress, capacity utilization, and resource allocation.

---

## 3. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Production      │ -> │ ProducingProcess │ -> │ Manufacturing   │
│ Status Data     │    │ or               │    │ Plans           │
│ & Schemas       │    └──────────────────┘    └─────────────────┘
└─────────────────┘             │                       │
         │                      v                       v
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ Mold Info & │        │ Hybrid      │        │ Production, │
   │ Machine     │        │ Suggest     │        │ Mold &      │
   │ Data        │        │ Optimizer   │        │ Plastic     │
   └─────────────┘        └─────────────┘        └─────────────┘
```
→ See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_producingProcessorWorkflow.md)

---

## 4. Pre-requisites Checklist
Before running the processor, ensure:

- [ ] **Production status data**: Current production status from OrderProgressTracker (.xlsx)
- [ ] **Schema validation**: `databaseSchemas.json` and `sharedDatabaseSchemas.json` accessible
- [ ] **Path annotations**: `path_annotations.json` with correct file mappings for parquet files
- [ ] **Machine layout data**: Latest machine information with tonnage specifications
- [ ] **Item composition data**: Material composition for plastic calculation
- [ ] **Write permissions**: Access to `agents/shared_db/ProducingProcessor/` directory
- [ ] **Python dependencies**: pandas, numpy, loguru, pathlib
- [ ] **Efficiency parameters**: Valid efficiency (0-1) and loss (0-1) configuration

---

## 5. Processing Scenarios

| Scenario | Production Data | Optimization | Final Status | Action Required |
|----------|----------------|--------------|--------------|-----------------|
| Full Production | ✅ MOLDING orders | ✅ Valid optimization | `complete_plans` | None |
| Mixed Status | ✅ MOLDING + PENDING | ✅ Valid optimization | `partial_production` | Review pending orders |
| Empty Production | ❌ No MOLDING orders | ✅ Valid optimization | `pending_only` | Start production |
| Optimization Failed | ✅ Production data | ❌ Optimization failed | `data_only` | Fix optimization |
| No Data | ❌ Empty status | ❌ No optimization | `failed` | Check data sources |

---

## 6. Input & Output
- **Input**: Production status data, machine specifications, item compositions, optimization results
- **Output**: Production plans, mold allocation plans, plastic consumption estimates
- **Format**: Excel files with multiple sheets and structured DataFrames

---

## 7. Simple Workflow
```
Load Data → Run Optimization → Process Production → Calculate Metrics → Generate Plans → Save Results
```

**Detailed Steps:**
1. **Initialization**: Load schemas, path annotations, and initialize HybridSuggestOptimizer
2. **Data Loading**: Import production status, machine info, and item composition data
3. **Optimization**: Execute hybrid suggest optimization for capacity and priority matrix
4. **Status Processing**: Split orders by status (MOLDING, PAUSED, PENDING)
5. **Metrics Calculation**: Compute time metrics, progress percentages, and estimates
6. **Plan Generation**: Create production, mold, and plastic utilization plans
7. **Results Export**: Save structured output with versioning control

---

## 8. Directory Structure

```
agents/shared_db/                                                                
└── ProducingProcessor                                # ProducingProcessor outputs  
    ├── historical_db/                                      
    ├── newest/                                             
    |   └── YYYYMMDD_HHMM_producing_processor.xlsx        
    └── change_log.txt                                # ProducingProcessor change log
```

---

## 9. Dependencies
- **HybridSuggestOptimizer**: Provides mold capacity estimation and priority matrices
- **Schema Validators**: Ensures data integrity with `@validate_init_dataframes` decorators
- **Machine Layout Checker**: Validates and updates machine configuration
- **Data Utilities**: Path annotations, change log reading, versioned output saving
- **loguru**: Structured logging with class-specific context binding

---

## 10. How to Run

### 10.1 Basic Usage
```python
# Initialize with default parameters
processor = ProducingProcessor()

# Run complete processing pipeline
optimization_results, pending_data, producing_data, pro_plan, mold_plan, plastic_plan = processor.process()

# Process and save all results
data = processor.process_and_save_results()

print(f"Producing orders: {producing_data.shape[0]}")
print(f"Pending orders: {pending_data.shape[0]}")
```

### 10.2 Custom Configuration
```python
# Initialize with custom parameters
processor = ProducingProcessor(
    source_path="custom/data/path",
    efficiency=0.90,  # Higher efficiency target
    loss=0.02,        # Lower loss expectation
    default_dir="custom/output/path"
)

# Run optimization only
optimization_results = processor.execute_hybrid_suggest_optimization()

# Check optimization status
print(f"Invalid molds: {len(optimization_results['estimated_capacity_invalid_molds'])}")
```

### 10.3 Development/Testing Mode
```python
# Initialize processor
processor = ProducingProcessor()

# Test individual components
producing_data, pending_data = ProducingProcessor._split_producing_and_pending_orders(
    status_df, 
    RequiredColumns.PRODUCING_BASE_COLS,
    RequiredColumns.PENDING_BASE_COLS
)

# Validate schema compliance
cols = list(processor.sharedDatabaseSchemas_data["producing_data"]['dtypes'].keys())
validate_dataframe(producing_data, cols)
```

---

## 11. Result Structure
```python
# Main processing results
optimization_results = {
    'estimated_capacity_invalid_molds': List[str],     # Molds with capacity issues
    'priority_matrix_invalid_molds': List[str],        # Molds with priority issues
    'capacity_data': pd.DataFrame,                     # Mold capacity estimates
    'priority_matrix': pd.DataFrame,                   # Machine-mold priority matrix
    'timestamp': datetime                              # Processing timestamp
}

# Output data structure
data = {
    "producing_status_data": pd.DataFrame,             # Current production orders
    "producing_pro_plan": pd.DataFrame,                # Production schedule plan
    "producing_mold_plan": pd.DataFrame,               # Mold utilization plan
    "producing_plastic_plan": pd.DataFrame,            # Plastic consumption plan
    "pending_status_data": pd.DataFrame,               # Pending/paused orders
    "mold_machine_priority_matrix": pd.DataFrame,      # Priority matrix
    "mold_estimated_capacity_df": pd.DataFrame,        # Capacity estimates
    "invalid_molds": pd.DataFrame                      # Invalid mold summary
}
```

---

## 12. Configuration Paths
- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (parquet data location)
- **annotation_name**: `path_annotations.json` (file path mappings)
- **default_dir**: `agents/shared_db` (base directory)
- **folder_path**: `agents/shared_db/OrderProgressTracker` (production status location)
- **output_dir**: `agents/shared_db/ProducingProcessor` (results output location)
- **mold_stability_index_folder**: `agents/shared_db/MoldStabilityIndexCalculator/mold_stability_index`
- **mold_machine_weights_hist_path**: `agents/shared_db/MoldMachineFeatureWeightCalculator/weights_hist.xlsx`

---

## 13. Common Issues & Solutions

| Problem | Symptoms | Quick Fix | Prevention |
|---------|----------|-----------|------------|
| Schema validation fails | DataFrame columns mismatch error | Check databaseSchemas.json files | Regular schema updates |
| Empty production data | All plans return empty DataFrames | Check production status values | Ensure MOLDING orders exist |
| Missing machine info | Machine merge fails, missing tonnage | Verify machineInfo.parquet exists | Run DataLoaderAgent first |
| Composition data missing | Plastic plan incomplete | Check itemCompositionSummary.parquet | Validate data pipeline |
| Optimization failure | HybridSuggestOptimizer errors | Check mold stability and weights data | Monitor optimization dependencies |
| Path annotation errors | FileNotFoundError during data loading | Validate path_annotations.json | Ensure DataLoaderAgent completion |
| Time calculation errors | NaN values in leadTime/remainTime | Check balancedMoldHourCapacity for zeros | Data quality validation |

---

## 14. Production Status Processing

### 14.1 Status Classification Logic
```python
# PRODUCING: Currently in production
producing = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'MOLDING')
]

# PAUSED: Temporarily stopped production  
paused = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'PAUSED')
]

# PENDING: Not yet started production
pending = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'PENDING')
]

# Combined pending = paused + pending
pending_combined = pd.concat([paused, pending])
```

### 14.2 Required Base Columns
```python
class RequiredColumns:
    PRODUCING_BASE_COLS = [
        'poNo', 'itemCode', 'itemName', 'poETA', 'moldNo',
        'itemQuantity', 'itemRemain', 'machineNo', 'startedDate'
    ]
    
    PENDING_BASE_COLS = [
        'poNo', 'itemCode', 'itemName', 'poETA', 'itemRemain'
    ]
```

---

## 15. Time Metrics Calculation

### 15.1 Key Time Calculations
```python
# Lead Time (total production time needed)
leadTime = itemQuantity / balancedMoldHourCapacity (hours)

# Remaining Time (time to complete remaining quantity)
remainTime = itemRemain / balancedMoldHourCapacity (hours)

# Production Progress Percentage
proProgressing = (itemQuantity - itemRemain) * 100 / itemQuantity

# Estimated Finish Date
finishedEstimatedDate = startedDate + leadTime

# Display Format
itemName_poNo = itemName + ' (' + poNo + ')'
```

### 15.2 Plastic Material Calculations
```python
# Daily Production Capacity
estimatedOutputQuantity = min(itemRemain, theoreticalMoldHourCapacity * 24)

# Plastic Resin (KG)
estimatedPlasticResinQuantity = (plasticResinQuantity / 10000) * estimatedOutputQuantity

# Color Masterbatch (KG)  
estimatedColorMasterbatchQuantity = (colorMasterbatchQuantity * 1000 / 10000) * estimatedOutputQuantity

# Additive Masterbatch (KG)
estimatedAdditiveMasterbatchQuantity = (additiveMasterbatchQuantity * 1000 / 10000) * estimatedOutputQuantity
```

---

## 16. Monitoring & Observability

### 16.1 Log Levels & Indicators
- **🚀 INFO**: Processor initialization and optimization start
- **📊 DEBUG**: DataFrame shapes and column validation results
- **✅ INFO**: Successful processing completion with order counts
- **⚠️ WARNING**: Data quality issues and empty DataFrame handling
- **❌ ERROR**: Critical failures in optimization or data processing
- **💾 INFO**: File export and versioning milestones

### 16.2 Key Metrics to Track
- **Production Orders Count**: Number of active MOLDING orders
- **Pending Orders Count**: Total PAUSED and PENDING orders waiting
- **Plan Generation Success**: All three plans (production, mold, plastic) created
- **Invalid Mold Rate**: Percentage of molds excluded from optimization
- **Time Calculation Accuracy**: Percentage of orders with valid time estimates
- **Material Calculation Coverage**: Orders with complete plastic composition data

### 16.3 Health Checks
```python
# Processing health check
def processor_health_check():
    processor = ProducingProcessor()
    
    try:
        # Test data loading
        processor._load_dataframes()
        data_loading_success = True
    except Exception:
        data_loading_success = False
    
    try:
        # Test optimization
        optimization_results = processor.execute_hybrid_suggest_optimization()
        optimization_success = True
        invalid_rate = len(optimization_results['estimated_capacity_invalid_molds']) / max(1, len(optimization_results['capacity_data']))
    except Exception:
        optimization_success = False
        invalid_rate = 1.0
    
    try:
        # Test full processing
        data = processor.process()
        processing_success = True
        producing_count = len(data[1]) if len(data) > 1 else 0
        pending_count = len(data[0]) if len(data) > 0 else 0
    except Exception:
        processing_success = False
        producing_count = 0
        pending_count = 0
    
    return {
        "data_loading_success": data_loading_success,
        "optimization_success": optimization_success,
        "processing_success": processing_success,
        "invalid_mold_rate": invalid_rate,
        "producing_orders": producing_count,
        "pending_orders": pending_count,
        "service_status": "healthy" if all([data_loading_success, optimization_success, processing_success]) else "degraded"
    }
```