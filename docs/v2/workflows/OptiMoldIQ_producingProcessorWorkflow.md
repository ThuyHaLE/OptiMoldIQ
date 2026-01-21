>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# ProducingProcessor

## 1. Overview

The **ProducingProcessor Workflow** orchestrates comprehensive manufacturing data processing by integrating production status analysis with advanced optimization algorithms. It transforms raw production data into actionable manufacturing plans through a multi-stage pipeline that handles data loading, optimization execution, production analysis, and plan generation with robust error handling and quality validation.

---

## 2. Architecture

### 2.1 Core Components

1. **ProducingProcessor** -- Main workflow orchestrator and data processor
2. **HybridSuggestOptimizer** -- Advanced mold-machine optimization engine
3. **ProductionStatusAnalyzer** -- Production status classification and filtering
4. **TimeMetricsCalculator** -- Production time and progress computation engine
5. **PlanGenerator** -- Multi-dimensional plan creation (Production, Mold, Plastic)
6. **DataExporter** -- Versioned output management and Excel generation

### 2.2 Five-Phase Processing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              [ ProducingProcessor ]                                             │
│                    Orchestrates complete manufacturing data processing                          │
└───────────────────────────────────────┬─────────────────────────────────────────────────────────┘
        ┌───────────┬───────────────────┴──────────────────┬─────────────┬───────────────┐
        ▼ Phase 1   ▼ Phase 2                              ▼ Phase 3     ▼ Phase 4       ▼ Phase 5
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Data Loading │ │ Optimization │ │ Production   │ │ Plan         │ │ Export &     │
│ & Validation │ │ Execution    │ │ Processing   │ │ Generation   │ │ Versioning   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
📂 Load Schemas    🎯 Execute Hybrid   📊 Analyze Status  📋 Create Plans   💾 Save Results
• Schema loading    • Capacity          • Split orders      • Production      • Excel export
• Path validation   • Priority matrix   • Calculate         • Mold usage      • Version control
• DataFrame load    • Quality checks    • Time metrics      • Plastic req.    • Data structure
• Error handling    • Invalid tracking  • Progress calc.    • Machine alloc.  • Backup system
```

### 2.3 Detailed Phase Breakdown

#### Phase 1: Data Loading & Validation

  ----------------------------------------------------------------------------------------------------------
  Step         Process                                  Details
  ------------ ---------------------------------------- ----------------------------------------------------
  1            Schema Configuration                     Load database schemas for validation framework

  2            Path Annotation Loading                  Process file path mappings from JSON configuration

  3            DataFrame Initialization                 Load parquet files with schema validation decorators

  4            Data Quality Validation                  Verify column presence, types, and data integrity

  5            Machine Layout Update                    Check and update latest machine configuration
  -----------------------------------------------------------------------------------------------------------

**Success Criteria:** All required DataFrames loaded with validated schemas.
**Failure Modes:** Missing files, schema mismatches, corrupted parquet data, path resolution errors.

**Input Sources:**
- `databaseSchemas.json` → Schema definitions and validation rules
- `sharedDatabaseSchemas.json` → Shared schema configurations
- `path_annotations.json` → File path mappings and locations
- `machineInfo.parquet` → Machine specifications and tonnage data
- `itemCompositionSummary.parquet` → Material composition definitions

**Output:**
- Validated DataFrames ready for processing
- Error logs for any loading issues

#### Phase 2: Optimization Execution

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Initialize HybridSuggestOptimizer          Setup optimization engine with validated parameters

  2           Configuration Validation                   Verify efficiency, loss parameters, and data availability

  3           Execute Optimization Pipeline              Run two-phase optimization (capacity + priority matrix)

  4           Quality Assessment                         Analyze optimization results and invalid mold tracking

  5           Results Integration                        Package optimization data for downstream processing
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Valid optimization results with capacity estimates and priority matrix.
**Failure Modes:** Optimization algorithm failures, invalid parameters, insufficient historical data.

**Input Sources:**
- Production status data from OrderProgressTracker
- Historical stability indices
- Feature weight configurations
- Machine-mold compatibility data

**Output:**
- `mold_estimated_capacity_df` → Capacity estimates per mold-item combination
- `mold_machine_priority_matrix` → Compatibility priority scores
- `estimated_capacity_invalid_molds` → List of molds with capacity issues
- `priority_matrix_invalid_molds` → List of molds with priority calculation issues

#### Phase 3: Production Processing

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Status Classification                      Split orders by production status (MOLDING/PAUSED/PENDING)

  2           Data Enrichment                           Merge with mold info, machine info, and optimization results

  3           Time Metrics Calculation                   Compute lead time, remain time, progress percentages

  4           Production Analysis                        Analyze current production state and capacity utilization

  5           Quality Validation                         Verify processed data against expected schemas
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Complete production analysis with enriched data and calculated metrics.
**Failure Modes:** Empty production data, merge failures, calculation errors, invalid time computations.

**Processing Logic:**
```python
# Status classification logic
producing_orders = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'MOLDING')
]

paused_orders = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'PAUSED')
]

pending_orders = proStatus_df[
    (proStatus_df['itemRemain'] > 0) & 
    (proStatus_df['proStatus'] == 'PENDING')
]

# Combined pending = paused + pending
pending_combined = pd.concat([paused_orders, pending_orders])
```

**Output:**
- `producing_status_data` → Currently active production orders
- `pending_status_data` → Orders waiting to start or resume production

#### Phase 4: Plan Generation

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Production Plan Creation                   Generate machine-based production scheduling plan

  2           Mold Plan Creation                        Create mold utilization and allocation plan

  3           Plastic Plan Creation                      Calculate material consumption and plastic requirements

  4           Resource Allocation Analysis               Analyze resource utilization and bottlenecks

  5           Plan Validation                           Verify plan consistency and data completeness
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Three comprehensive plans generated with complete resource allocation.
**Failure Modes:** Missing composition data, calculation errors, plan generation failures.

**Plan Types:**

1. **Production Plan:**
   - Machine assignments
   - Production schedules
   - Remaining time estimates
   - Item-PO combinations

2. **Mold Plan:**
   - Mold assignments per machine
   - Mold utilization rates
   - Changeover requirements
   - Capacity planning

3. **Plastic Plan:**
   - Material consumption estimates
   - Resin requirements (KG)
   - Masterbatch quantities (KG)
   - Daily material planning

**Output:**
- `producing_pro_plan` → Production scheduling plan
- `producing_mold_plan` → Mold utilization plan  
- `producing_plastic_plan` → Material consumption plan

#### Phase 5: Export & Versioning

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Data Structure Preparation                 Format all outputs into standardized structure

  2           Invalid Molds Processing                   Create comprehensive invalid molds DataFrame

  3           Priority Matrix Formatting                 Process priority matrix for Excel compatibility

  4           Excel Export Generation                    Create multi-sheet Excel workbook with all plans

  5           Version Control Management                 Apply versioning and backup strategies
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Complete Excel export with versioned backup and structured data.
**Failure Modes:** File permission errors, disk space issues, export format problems.

**Export Structure:**
```python
export_data = {
    "producing_status_data": producing_status_data,
    "producing_pro_plan": producing_pro_plan,
    "producing_mold_plan": producing_mold_plan,
    "producing_plastic_plan": producing_plastic_plan,
    "pending_status_data": pending_status_data,
    "mold_machine_priority_matrix": priority_matrix,
    "mold_estimated_capacity_df": capacity_data,
    "invalid_molds": invalid_molds_summary
}
```

**Output:**
- Versioned Excel file (multiple sheets) with timestamp
- Backup copies in historical directory
- Change log entries for tracking

---

## 3. Workflow State Management

### 3.1 Processing State Transitions

| State | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Result Status | Recovery Action |
|-------|---------|---------|---------|---------|---------|---------------|-----------------|
| **🎯 Optimal** | ✅ All data loaded | ✅ Optimization success | ✅ Full processing | ✅ All plans generated | ✅ Export complete | `success` | None |
| **⚠️ Degraded** | ✅ Partial data | ⚠️ Some invalid molds | ✅ Reduced processing | ⚠️ Partial plans | ✅ Export complete | `partial_success` | Monitor data quality |
| **🔄 Recovery** | ⚠️ Fallback data | ⚠️ Default optimization | ✅ Basic processing | ⚠️ Minimal plans | ✅ Export complete | `degraded_mode` | Data collection |
| **❌ Failed** | ❌ Load failure | ❌ No optimization | ❌ No processing | ❌ No plans | ❌ Export failed | `failed` | Full system check |

### 3.2 Error Handling Strategy

```
[Start] → Phase 1: Data Loading
              │
              ▼
        ┌─────────────┐
        │ Data Load   │
        │ Successful? │
        └─────┬───────┘
          YES │ NO
              ▼  └──→ [Graceful Degradation]
        Phase 2: Optimization          │
              │                        │
              ▼                        │
        ┌─────────────┐                │
        │ Optimization│                │
        │ Successful? │                │
        └─────┬───────┘                │
          YES │ NO                     │
              ▼  └─────────────────────┼──→ [Partial Processing]
        Phase 3: Production Analysis   │
              │                        │
              ▼                        │
        ┌─────────────┐                │
        │ Processing  │                │
        │ Successful? │                │
        └─────┬───────┘                │
          YES │ NO                     │
              ▼  └─────────────────────┼──→ [Minimal Output]
        Phase 4: Plan Generation       │
              │                        │
              ▼                        │
        ┌─────────────┐                │
        │ Plans       │                │
        │ Generated?  │                │
        └─────┬───────┘                │
          YES │ NO                     │
              ▼  └─────────────────────┼──→ [Status Only]
        Phase 5: Export                │
              │                        │
              ▼                        │
        [Success/Partial Success] ←────┘
```

---

## 4. Data Flow Pipeline

### 4.1 Input Data Sources

```
Production Status Data Flow:
OrderProgressTracker → change_log.txt → latest Excel file → proStatus_df

Static Data Flow:
DataLoaderAgent → path_annotations.json → parquet files → DataFrames
├── machineInfo.parquet → machineInfo_df
└── itemCompositionSummary.parquet → itemCompositionSummary_df

Optimization Data Flow:
MoldStabilityIndexCalculator → mold_stability_index.xlsx
MoldMachineFeatureWeightCalculator → weights_hist.xlsx
HybridSuggestOptimizer → optimization_results
```

### 4.2 Processing Data Transformations

#### Status Classification Transform
```python
# Input: Raw production status
proStatus_df.columns = ['poNo', 'itemCode', 'itemName', 'proStatus', 'itemRemain', ...]

# Transform: Split by status
producing_df = filter(proStatus == 'MOLDING' AND itemRemain > 0)
pending_df = filter(proStatus IN ['PAUSED', 'PENDING'] AND itemRemain > 0)

# Output: Classified production data
producing_status_data.columns = PRODUCING_BASE_COLS
pending_status_data.columns = PENDING_BASE_COLS
```

#### Time Metrics Transform
```python
# Input: Production data with capacity info
producing_data = merge(producing_status, mold_capacity, machine_info)

# Transform: Calculate time metrics  
leadTime = itemQuantity / balancedMoldHourCapacity (hours)
remainTime = itemRemain / balancedMoldHourCapacity (hours)
proProgressing = (itemQuantity - itemRemain) * 100 / itemQuantity (%)
finishedEstimatedDate = startedDate + leadTime

# Output: Enriched production data with time metrics
```

#### Material Consumption Transform
```python
# Input: Production data + Item composition
plastic_data = merge(producing_data, itemCompositionSummary)

# Transform: Calculate material requirements
estimatedOutputQuantity = min(itemRemain, theoreticalMoldHourCapacity * 24)
plasticResinQuantity_KG = (plasticResinQuantity / 10000) * estimatedOutputQuantity
colorMasterbatchQuantity_KG = (colorMasterbatchQuantity * 1000 / 10000) * estimatedOutputQuantity

# Output: Material consumption estimates
```

### 4.3 Output Data Structure

#### Production Plans Hierarchy

```
agents/shared_db                                              # Output directory
├── OrderProgressTracker
|     └── change_log.txt                                      # Progress changes (ProducingProcessor input)  
├── MoldStabilityIndexCalculator/ 
|    └── change_log.txt                                       # Stability index changes (ProducingProcessor input)  
├── MoldMachineFeatureWeightCalculator/     
|   └── weights_hist.xlsx                                     # Machine weight history (ProducingProcessor input)   
└── ProducingProcessor
      ├── historical_db/                                                                
      ├── newest/                                                                                  
      |    └──  YYYYMMDD_HHMM_producing_processor.xlsx        # Production analysis report (ProducingProcessor)
      └── change_log.txt                                      # Production changes
```

---

## 5. Quality Assurance Framework

### 5.1 Multi-Level Validation Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input         │    │   Processing    │    │   Output        │    │   Export        │
│   Validation    │    │   Validation    │    │   Validation    │    │   Validation    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │                      │
          ▼                      ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Schema Check    │    │ Calculation     │    │ Plan            │    │ File Format     │
│ File Existence  │    │ Validation      │    │ Completeness    │    │ Version Control │
│ Data Types      │    │ Range Checks    │    │ Data Integrity  │    │ Backup Success  │
│ Column Presence │    │ Logic Validation│    │ Schema Compliance│    │ Access Rights   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5.2 Validation Checkpoints

#### Input Validation (Phase 1)
- **Schema Compliance**: `@validate_init_dataframes` decorator verification
- **File Integrity**: Parquet file corruption detection
- **Data Completeness**: Required columns and non-null critical fields
- **Type Consistency**: Data type matching with schema definitions

#### Processing Validation (Phases 2-4)
- **Optimization Quality**: Invalid mold percentage thresholds
- **Calculation Accuracy**: Division by zero prevention, range validation
- **Merge Success**: Left join integrity and key matching validation
- **Time Logic**: Lead time > remain time, positive progress values

#### Output Validation (Phase 5)
- **Plan Consistency**: All machines represented, no orphaned data
- **Schema Compliance**: Output DataFrames match expected schemas
- **Data Completeness**: Required fields populated, no unexpected nulls
- **Export Success**: File creation, proper formatting, version tracking

### 5.3 Error Recovery Strategies

#### Graceful Degradation Levels

1. **Full Functionality** (100% success)
   - All phases complete successfully
   - Complete plans with optimization results
   - Full data export with all components

2. **Degraded Mode** (70-99% success)
   - Some invalid molds excluded
   - Plans generated with available data
   - Warning logs for quality issues

3. **Minimal Mode** (30-69% success)
   - Basic production status only
   - Empty plan structures with correct schemas
   - Error reporting for downstream systems

4. **Failure Mode** (0-29% success)
   - System-wide processing failure
   - Emergency logging and notification
   - Manual intervention required

---

## 6. Performance Optimization

### 6.1 Processing Efficiency Strategies

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Loading  │    │   Processing    │    │   Memory        │
│   Optimization  │    │   Optimization  │    │   Management    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Lazy Loading    │    │ Vectorized Ops  │    │ DataFrame Copy  │
│ Column Subset   │    │ Batch Processing│    │ Memory Release  │
│ Parquet Format  │    │ Efficient Joins │    │ Garbage Collection│
│ Path Caching    │    │ Parallel Compute│    │ Resource Monitor│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 6.2 Scalability Considerations

#### Data Volume Handling
- **Chunked Processing**: Handle large production datasets in batches
- **Memory Monitoring**: Track memory usage during processing phases
- **Disk I/O Optimization**: Efficient parquet reading with column selection
- **Caching Strategy**: Cache frequently accessed reference data

#### Computation Optimization
- **Vectorized Operations**: Use pandas vectorized functions over loops
- **Efficient Merges**: Optimize join strategies and key selection
- **Conditional Processing**: Skip unnecessary calculations for empty datasets
- **Parallel Execution**: Multi-threading for independent processing tasks

---

## 7. Monitoring & Observability

### 7.1 Key Performance Indicators

| Metric Category | Metric Name | Target Value | Alert Threshold |
|----------------|-------------|--------------|-----------------|
| **Processing Speed** | Total Execution Time | < 5 minutes | > 10 minutes |
| **Data Quality** | Invalid Mold Rate | < 5% | > 15% |
| **System Health** | Success Rate | > 95% | < 80% |
| **Resource Usage** | Memory Peak | < 2GB | > 4GB |
| **Output Quality** | Plan Completeness | 100% | < 90% |

### 7.2 Logging Strategy

```
Log Level Hierarchy:
├── 🚀 INFO: Workflow milestones and phase completion
├── 📊 DEBUG: Data shapes, column info, and processing details
├── ✅ SUCCESS: Successful operations and quality metrics
├── ⚠️ WARNING: Data quality issues and degraded mode activation
├── ❌ ERROR: Processing failures and error conditions
└── 🔥 CRITICAL: System-wide failures requiring immediate attention
```

### 7.3 Health Check Implementation

```python
def producing_processor_health_check():
    """Comprehensive health check for ProducingProcessor workflow"""
    
    health_status = {
        "timestamp": datetime.now(),
        "overall_status": "unknown",
        "phase_status": {},
        "performance_metrics": {},
        "data_quality_metrics": {},
        "system_resources": {}
    }
    
    try:
        # Phase 1: Data Loading Health
        processor = ProducingProcessor()
        processor._setup_schemas()
        processor._load_dataframes()
        health_status["phase_status"]["data_loading"] = "healthy"
        
        # Phase 2: Optimization Health  
        optimization_results = processor.execute_hybrid_suggest_optimization()
        invalid_rate = len(optimization_results['estimated_capacity_invalid_molds']) / max(1, len(optimization_results['capacity_data']))
        health_status["phase_status"]["optimization"] = "healthy" if invalid_rate < 0.15 else "degraded"
        
        # Phase 3-5: Full Processing Health
        start_time = time.time()
        data = processor.process()
        processing_time = time.time() - start_time
        
        health_status["phase_status"]["full_processing"] = "healthy"
        health_status["performance_metrics"]["processing_time_seconds"] = processing_time
        health_status["data_quality_metrics"]["producing_orders"] = len(data[1]) if len(data) > 1 else 0
        health_status["data_quality_metrics"]["pending_orders"] = len(data[0]) if len(data) > 0 else 0
        health_status["data_quality_metrics"]["invalid_mold_rate"] = invalid_rate
        
        # Overall health assessment
        if all(status == "healthy" for status in health_status["phase_status"].values()):
            health_status["overall_status"] = "healthy"
        elif any(status == "healthy" for status in health_status["phase_status"].values()):
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "failed"
            
    except Exception as e:
        health_status["overall_status"] = "failed"
        health_status["error"] = str(e)
    
    return health_status
```

---

## 8. Usage Examples

### 8.1 Standard Production Processing

```python
# Initialize processor with default settings
processor = ProducingProcessor()

# Execute complete workflow
results = processor.process_and_save_results()

# Monitor results
print(f"Producing orders: {len(results['producing_status_data'])}")
print(f"Production plan machines: {len(results['producing_pro_plan'])}")
print(f"Mold utilization entries: {len(results['producing_mold_plan'])}")
print(f"Plastic consumption plans: {len(results['producing_plastic_plan'])}")

# Check data quality
invalid_capacity = len(results['invalid_molds']['estimated_capacity_invalid_molds'].dropna())
invalid_priority = len(results['invalid_molds']['priority_matrix_invalid_molds'].dropna())
print(f"Data quality - Invalid molds: {invalid_capacity + invalid_priority}")
```

### 8.2 High-Efficiency Production Mode

```python
# Configure for high-efficiency operation
processor = ProducingProcessor(
    efficiency=0.92,  # 92% efficiency target
    loss=0.015,       # 1.5% loss expectation
    source_path="production/high_priority/data"
)

# Execute optimization first
optimization_results = processor.execute_hybrid_suggest_optimization()

# Validate optimization quality before proceeding
capacity_success_rate = len(optimization_results['capacity_data']) / (
    len(optimization_results['capacity_data']) + 
    len(optimization_results['estimated_capacity_invalid_molds'])
)

if capacity_success_rate > 0.9:
    print("High-quality optimization achieved, proceeding with full processing")
    results = processor.process_and_save_results()
else:
    print(f"Optimization quality warning: {capacity_success_rate:.1%} success rate")
```

### 8.3 Development and Testing Workflow

```python
# Enable detailed logging for development
import logging
logging.getLogger("ProducingProcessor").setLevel(logging.DEBUG)

# Initialize with test configuration
processor = ProducingProcessor(
    source_path="test/data/path",
    default_dir="test/output/path"
)

# Test individual workflow phases
try:
    # Phase 1: Data loading test
    processor._setup_schemas()
    processor._load_dataframes()
    print("✅ Phase 1: Data loading successful")
    
    # Phase 2: Optimization test
    optimization_results = processor.execute_hybrid_suggest_optimization()
    print(f"✅ Phase 2: Optimization complete - {len(optimization_results['capacity_data'])} valid molds")
    
    # Phase 3-4: Processing and plan generation test
    data = processor.process()
    print(f"✅ Phase 3-4: Processing complete - {len(data)} result sets")
    
    # Phase 5: Export test
    final_results = processor.process_and_save_results()
    print(f"✅ Phase 5: Export complete - {len(final_results)} data sheets")
    
except Exception as e:
    print(f"❌ Workflow test failed at: {e}")
    
    # Individual component testing
    from agents.decorators import validate_dataframe
    
    # Test schema validation
    test_df = processor.proStatus_df
    expected_cols = list(processor.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys())
    
    try:
        validate_dataframe(test_df, expected_cols)
        print("✅ Schema validation passed")
    except Exception as schema_error:
        print(f"❌ Schema validation failed: {schema_error}")
```

### 8.4 Production Monitoring Integration

```python
# Continuous monitoring setup
import schedule
import time

def monitor_production_processing():
    """Automated production processing with monitoring"""
    
    health_check = producing_processor_health_check()
    
    if health_check["overall_status"] == "healthy":
        # Execute standard processing
        processor = ProducingProcessor()
        results = processor.process_and_save_results()
        
        # Log success metrics
        logger.info(f"Production processing successful: {len(results['producing_status_data'])} orders")
        
        # Update monitoring dashboard
        update_monitoring_dashboard({
            "status": "success",
            "timestamp": datetime.now(),
            "orders_processed": len(results['producing_status_data']),
            "processing_time": health_check["performance_metrics"].get("processing_time_seconds", 0)
        })
        
    elif health_check["overall_status"] == "degraded":
        # Execute with increased monitoring
        processor = ProducingProcessor(efficiency=0.80, loss=0.05)  # More conservative parameters
        results = processor.process_and_save_results()
        
        # Alert operations team
        send_alert(f"Production processing in degraded mode: {health_check}")
        
    else:
        # Failure mode - emergency protocols
        logger.error(f"Production processing failed: {health_check}")
        send_critical_alert("Production processing system failure")
        
        # Attempt recovery
        try:
            backup_processor = ProducingProcessor(source_path="backup/data/path")
            backup_results = backup_processor.process_and_save_results()
            logger.info("Recovery processing successful using backup data")
        except Exception as recovery_error:
            logger.critical(f"Recovery processing also failed: {recovery_error}")

# Schedule automated processing
schedule.every().hour.do(monitor_production_processing)
schedule.every().day.at("06:00").do(lambda: monitor_production_processing())  # Daily processing

while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
```