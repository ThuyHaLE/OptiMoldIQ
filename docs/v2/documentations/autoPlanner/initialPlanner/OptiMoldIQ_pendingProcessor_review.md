>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# PendingProcessor

## 1. Agent Info
- **Name**: PendingProcessor
- **Purpose**: 
  - Two-tier optimization system for pending production assignments using `history-based` and `compatibility-based` algorithms
  - Generate comprehensive manufacturing assignments by `matching molds to machines` based on historical performance and technical compatibility
- **Owner**: 
- **Status**: Active
- **Location**: `agents/autoPlanner/initialPlanner/`

---

## 2. What it does
The `PendingProcessor` processes pending production orders through a sophisticated two-tier optimization approach. First, it uses `history-based optimization` ([HistBasedMoldMachineOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_histBasedMoldMachineOptimizer_review.md)) leveraging past mold-machine performance data to make primary assignments. For unassigned molds (lack of historical insights), it employs `compatibility-based optimization` ([CompatibilityBasedMoldMachineOptimizer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_compatibilityBasedMoldMachineOptimizer_review.md)) using technical specifications to maximize machine utilization. The system integrates with existing production status, validates data integrity, and generates detailed assignment summaries with priority scheduling for manufacturing execution.

---

## 3. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Production      │ -> │ PendingProcessor │ -> │ Manufacturing   │
│ Status & Pending│    │                  │    │ Assignments     │
│ Orders Data     │    └──────────────────┘    └─────────────────┘
└─────────────────┘             │                       │
         │                      v                       v
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ Machine &   │        │ History +   │        │ Assignment  │
   │ Mold Info + │        │ Compatibility│        │ Summary +   │
   │ Priority    │        │ Optimization │        │ Priority    │
   │ Matrix      │        │              │        │ Schedule    │
   └─────────────┘        └─────────────┘        └─────────────┘
```
→ See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_pendingProcessorWorkflow.md)

---

## 4. Pre-requisites Checklist
Before running the processor, ensure:

- [ ] **Producing processor output**: Latest producing processor report (.xlsx) with 5 required sheets
- [ ] **Schema validation**: `databaseSchemas.json` and `sharedDatabaseSchemas.json` accessible
- [ ] **Path annotations**: `path_annotations.json` with correct file mappings for parquet files
- [ ] **Machine & mold data**: Latest machine layout and mold information with compatibility specs
- [ ] **Priority matrix**: Historical mold-machine priority performance data
- [ ] **Write permissions**: Access to `agents/shared_db/PendingProcessor/` directory
- [ ] **Python dependencies**: pandas, loguru, typing, dataclasses, pathlib
- [ ] **Optimization parameters**: Valid max_load_threshold and priority_order configuration

---

## 5. Processing Scenarios

| Scenario | History Assignment | Compatibility Assignment | Final Status | Action Required |
|----------|-------------------|--------------------------|--------------|-----------------|
| Complete Assignment | ✅ All molds assigned | ❌ Not needed | `history_complete` | Execute production |
| Partial Assignment | ✅ Some molds assigned | ✅ Remaining assigned | `two_tier_complete` | Review compatibility assignments |
| History Only | ✅ Some molds assigned | ❌ Compatibility failed | `history_partial` | Check compatibility matrix |
| Assignment Failed | ❌ No history assignments | ❌ Compatibility failed | `assignment_failed` | Review mold/machine data |
| No Pending Orders | ❌ No pending data | ❌ Not applicable | `no_pending` | Check pending order status |

---

## 6. Input & Output
- **Input**: Production status data, pending orders, mold-machine priority matrix, capacity estimates, machine/mold specifications
- **Output**: Assignment summary with machine priorities, invalid molds categorization, assignment history tracking
- **Format**: Excel files with multiple sheets and structured ProcessingResult dataclass

---

## 7. Simple Workflow
```
Load Data → Validate Schemas → History Optimization → Compatibility Optimization → Combine Results → Generate Summary
```

**Detailed Steps:**
1. **Data Loading**: Load production status, pending orders, priority matrix, capacity estimates, and invalid molds
2. **Schema Validation**: Validate all DataFrames against predefined schemas for data integrity
3. **Mold-Item Matching**: Match pending molds with items and calculate lead times
4. **History-based Optimization**: Run primary optimization using historical mold-machine performance
5. **Compatibility-based Optimization**: Process unassigned molds using technical compatibility matrix
6. **Assignment Processing**: Generate detailed assignment summaries with machine priorities
7. **Result Combination**: Merge history and compatibility assignments with proper priority adjustment
8. **Output Generation**: Create ProcessingResult with comprehensive assignment tracking

---

## 8. Directory Structure

```
agents/shared_db/                                                                
└── PendingProcessor/                                 # PendingProcessor outputs  
    ├── historical_db/                                      
    ├── newest/                                             
    |   └── YYYYMMDD_HHMM_pending_processor.xlsx      # Assignment results
    └── change_log.txt                                # PendingProcessor change log
```

---

## 9. Dependencies
- **HistBasedMoldMachineOptimizer**: Primary optimization using historical performance data
- **CompatibilityBasedMoldMachineOptimizer**: Secondary optimization using technical compatibility
- **MachineAssignmentProcessor**: Assignment summary generation and priority scheduling
- **Schema Validators**: Data integrity validation with `@validate_init_dataframes` decorators
- **Machine Layout Checker**: Machine configuration validation and updates
- **Mold-Item Matching**: Capacity calculation and lead time estimation utilities
- **loguru**: Structured logging with class-specific context binding

---

## 10. How to Run

### 10.1 Basic Usage
```python
# Initialize with default parameters
processor = PendingProcessor()

# Run complete processing pipeline
result = processor.run()

print(f"History assigned: {len(result.hist_based_assigned_molds)}")
print(f"History unassigned: {len(result.hist_based_unassigned_molds)}")
print(f"Compatibility assigned: {len(result.compatibility_based_assigned_molds or [])}")
print(f"Final assignments: {len(result.final_assignment_summary)}")

# Process and save all results
data = processor.run_and_save_results()
```

### 10.2 Custom Configuration
```python
from agents.autoPlanner.initialPlanner.compatibility_based_mold_machine_optimizer import PriorityOrder

# Custom configuration
config = ProcessingConfig(
    max_load_threshold=25,        # Lower threshold for stricter load control
    priority_order=PriorityOrder.PRIORITY_2,  # Alternative priority strategy
    log_progress_interval=10,     # More frequent logging
    verbose=True,                 # Detailed output
    use_sample_data=False         # Use real data
)

# Custom sheet mapping
sheet_mapping = ExcelSheetMapping(
    producing_status_data='custom_producing_data',
    pending_status_data='custom_pending_data',
    mold_machine_priority_matrix='custom_priority_matrix',
    mold_estimated_capacity_df='custom_capacity_data',
    invalid_molds='custom_invalid_molds'
)

# Initialize with custom configuration
processor = PendingProcessor(
    config=config,
    sheet_mapping=sheet_mapping,
    source_path="custom/data/path"
)

result = processor.run()
```

### 10.3 Development/Testing Mode
```python
# Initialize processor with sample data
config = ProcessingConfig(use_sample_data=True)
processor = PendingProcessor(config=config)

# Test individual phases
processor._load_and_validate_data()

# Test history-based optimization
hist_matrix, hist_summary, hist_assigned, hist_unassigned = processor._process_history_based_phase()

# Test compatibility-based optimization  
if hist_unassigned:
    comp_summary, comp_assigned, comp_unassigned = processor._process_compatibility_based_phase(
        hist_matrix, hist_unassigned
    )

# Validate schema compliance
validate_dataframe(processor.pending_status_data, 
                  list(processor.sharedDatabaseSchemas_data["pending_data"]['dtypes'].keys()))
```

---

## 11. Result Structure
```python
# ProcessingResult dataclass
@dataclass
class ProcessingResult:
    used_producing_report_name: str                      # Source report filename
    final_assignment_summary: pd.DataFrame               # Complete assignment plan
    invalid_molds_dict: Dict[str, List]                  # Categorized invalid molds
    hist_based_assigned_molds: List                      # History optimization results
    hist_based_unassigned_molds: List                    # History unassigned molds
    compatibility_based_assigned_molds: Optional[List]   # Compatibility assigned molds
    compatibility_based_unassigned_molds: Optional[List] # Final unassigned molds
    not_matched_pending: Optional[pd.DataFrame]          # Unmatched pending items

# Assignment Summary DataFrame Structure
final_assignment_summary = {
    "Machine No.": str,              # Machine identifier
    "Priority in Machine": int,       # Execution priority (1=highest)
    "Machine Code": str,             # Machine code reference
    "Mold No.": str,                # Assigned mold identifier
    "Item Code": str,               # Item to be produced
    "Item Name": str,               # Item description
    "PO Number": str,               # Purchase order reference
    "PO Quantity": int,             # Order quantity
    "Lead Time": float,             # Estimated production time (hours)
    "Note": str                     # Assignment method (histBased/compatibilityBased)
}

# Invalid Molds Dictionary Structure
invalid_molds_dict = {
    "capacity_estimation_issues": List[str],    # Molds with capacity problems
    "priority_matrix_missing": List[str],       # Molds not in priority matrix
    "compatibility_issues": List[str],          # Molds with machine incompatibility
    "mold_machine_optimizer": List[str]         # Final unassigned molds
}
```

---

## 12. Configuration Paths
- **source_path**: `agents/shared_db/DataLoaderAgent/newest` (parquet data location)
- **annotation_name**: `path_annotations.json` (file path mappings)
- **databaseSchemas_path**: `database/databaseSchemas.json` (schema definitions)
- **sharedDatabaseSchemas_path**: `database/sharedDatabaseSchemas.json` (shared schemas)
- **default_dir**: `agents/shared_db` (base directory)
- **producing_processor_folder_path**: `agents/shared_db/ProducingProcessor` (input source location)
- **producing_processor_target_name**: `change_log.txt` (source tracking file)
- **output_dir**: `agents/shared_db/PendingProcessor` (results output location)

---

## 13. Common Issues & Solutions

| Problem | Symptoms | Quick Fix | Prevention |
|---------|----------|-----------|------------|
| Missing producing report | FileNotFoundError on report loading | Check ProducingProcessor output | Run ProducingProcessor first |
| Schema validation fails | DataFrame columns mismatch error | Update schema files or data format | Regular schema synchronization |
| Empty pending data | No assignments generated | Check pending order status in source | Verify pending orders exist |
| Priority matrix missing | History optimization fails | Check mold_machine_priority_matrix sheet | Validate producing report completeness |
| Machine compatibility fails | All molds unassigned in tier 2 | Verify machineInfo and moldInfo data | Check machine-mold compatibility specs |
| Assignment combination fails | Priority conflicts in final summary | Check priority adjustment logic | Monitor priority range overlap |
| Invalid molds excessive | High percentage of excluded molds | Review mold data quality | Improve mold-item matching |
| Memory issues with large datasets | Performance degradation | Implement data chunking | Monitor dataset sizes |

---

## 14. Two-Tier Optimization Logic

### 14.1 History-Based Optimization (Tier 1)
```python
# Primary assignment using historical performance
class HistBasedMoldMachineOptimizer:
    def run_optimization(self):
        # Use mold_machine_priority_matrix for assignments
        # Consider current machine load from producing_status_data  
        # Respect max_load_threshold constraints
        # Return assigned_matrix, assignments, unassigned_molds
```

**Key Features:**
- Leverages historical mold-machine performance data
- Considers current machine workload
- Prioritizes proven mold-machine combinations
- Respects machine capacity constraints

### 14.2 Compatibility-Based Optimization (Tier 2)  
```python
# Secondary assignment using technical compatibility
class CompatibilityBasedMoldMachineOptimizer:
    def run_optimization(self, mold_machine_assigned_matrix, unassigned_mold_lead_times):
        # Create compatibility matrix from machine/mold specs
        # Process only unassigned molds from tier 1
        # Apply priority_order strategy (PRIORITY_1, PRIORITY_2)
        # Return updated assigned_matrix, new_assignments, final_unassigned
```

**Key Features:**
- Processes only molds unassigned by history-based optimization
- Uses technical machine-mold compatibility specifications
- Supports multiple priority ordering strategies
- Updates existing assignment matrix without conflicts

### 14.3 Assignment Processing Logic
```python
# Priority adjustment for combined results
max_priority_by_machine = hist_based_df.groupby('Machine No.')['Priority in Machine'].max()
compatibility_based_df['Priority in Machine'] += compatibility_based_df['Machine No.'].map(max_priority_by_machine).fillna(0)

# Duplicate handling
mask_multi = combined_df.groupby('Machine Code')['Machine Code'].transform('count') > 1
filtered_df = combined_df[~((mask_multi) & (combined_df['PO Quantity'] == 0))]
```

---

## 15. Data Validation Framework

### 15.1 Schema Validation Decorators
```python
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})
@validate_init_dataframes(lambda self: {
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
})
class PendingProcessor:
    # Class implementation with automatic validation
```

### 15.2 Excel Sheet Validation
```python
def _validate_excel_sheets(self, report_path: str) -> List[str]:
    available_sheets = pd.ExcelFile(report_path).sheet_names
    sheet_mappings = self.sheet_mapping.get_sheet_mappings()
    missing_sheets = [sheet for sheet in sheet_mappings.keys() if sheet not in available_sheets]
    
    if missing_sheets:
        raise DataValidationError(f"Missing required sheets: {missing_sheets}")
```

### 15.3 Required Excel Sheets
```python
class ExcelSheetMapping:
    producing_status_data: str = 'producing_status_data'     # Current production status
    pending_status_data: str = 'pending_status_data'         # Pending/paused orders
    mold_machine_priority_matrix: str = 'mold_machine_priority_matrix'  # Historical priorities
    mold_estimated_capacity_df: str = 'mold_estimated_capacity_df'      # Capacity estimates
    invalid_molds: str = 'invalid_molds'                     # Invalid mold categories
```

---

## 16. Monitoring & Observability

### 16.1 Log Levels & Indicators
- **🚀 INFO**: Processor initialization and optimization phase starts
- **📊 DEBUG**: DataFrame shapes, column validation, and data loading results
- **✅ INFO**: Successful assignment completion with mold counts and assignment ratios
- **⚠️ WARNING**: Data quality issues, missing sheets, unassigned molds
- **❌ ERROR**: Critical failures in optimization, data validation, or file operations
- **💾 INFO**: File export, versioning milestones, and processing pipeline completion

### 16.2 Key Metrics to Track
- **History Assignment Rate**: Percentage of molds assigned by tier 1 optimization
- **Compatibility Assignment Rate**: Percentage of remaining molds assigned by tier 2
- **Total Assignment Success**: Overall molds successfully assigned vs total pending
- **Invalid Mold Rate**: Percentage of molds excluded due to data issues
- **Priority Distribution**: Assignment spread across machine priority levels
- **Processing Time**: Time taken for each optimization tier and overall pipeline

### 16.3 Health Checks
```python
# Processing health check
def pending_processor_health_check():
    processor = PendingProcessor()
    
    try:
        # Test data loading and validation
        processor._load_and_validate_data()
        data_loading_success = True
        pending_count = len(processor.pending_status_data)
        producing_count = len(processor.producing_status_data)
    except Exception:
        data_loading_success = False
        pending_count = 0
        producing_count = 0
    
    try:
        # Test history-based optimization
        hist_matrix, hist_summary, hist_assigned, hist_unassigned = processor._process_history_based_phase()
        history_success = True
        history_assignment_rate = len(hist_assigned) / max(1, len(hist_assigned) + len(hist_unassigned))
    except Exception:
        history_success = False
        history_assignment_rate = 0.0
    
    try:
        # Test compatibility-based optimization (if needed)
        if hist_unassigned:
            comp_summary, comp_assigned, comp_unassigned = processor._process_compatibility_based_phase(
                hist_matrix, hist_unassigned
            )
            compatibility_success = True
            final_assignment_rate = (len(hist_assigned) + len(comp_assigned or [])) / max(1, pending_count)
        else:
            compatibility_success = True  # Not needed
            final_assignment_rate = history_assignment_rate
    except Exception:
        compatibility_success = False
        final_assignment_rate = history_assignment_rate
    
    try:
        # Test full processing pipeline
        result = processor.run()
        processing_success = True
        total_assignments = len(result.final_assignment_summary)
        invalid_mold_count = sum(len(molds) for molds in result.invalid_molds_dict.values())
    except Exception:
        processing_success = False
        total_assignments = 0
        invalid_mold_count = 0
    
    return {
        "data_loading_success": data_loading_success,
        "history_optimization_success": history_success,
        "compatibility_optimization_success": compatibility_success,
        "processing_success": processing_success,
        "pending_orders": pending_count,
        "producing_orders": producing_count,
        "history_assignment_rate": history_assignment_rate,
        "final_assignment_rate": final_assignment_rate,
        "total_assignments": total_assignments,
        "invalid_mold_count": invalid_mold_count,
        "service_status": "healthy" if all([data_loading_success, history_success, processing_success]) else "degraded"
    }
```

### 16.4 Performance Benchmarks
- **Data Loading**: < 10 seconds for standard dataset sizes
- **History Optimization**: < 30 seconds for 100-500 pending molds
- **Compatibility Optimization**: < 60 seconds for remaining unassigned molds
- **Assignment Processing**: < 15 seconds for result generation
- **Total Pipeline**: < 2 minutes for complete end-to-end processing
- **Memory Usage**: < 2GB for typical production datasets
- **Assignment Success Rate**: > 85% for well-configured systems