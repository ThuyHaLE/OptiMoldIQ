# PendingProcessor

## 1. Overview

The **PendingProcessor Workflow** orchestrates intelligent mold-machine assignment optimization for pending production orders through a sophisticated two-tier optimization strategy. It transforms pending production data into actionable manufacturing assignments by combining historical performance patterns with technical compatibility analysis, ensuring optimal resource allocation while maintaining production quality and efficiency standards.

---

## 2. Architecture

### 2.1 Core Components

1. **PendingProcessor** -- Main workflow orchestrator and assignment optimizer
2. **HistBasedMoldMachineOptimizer** -- Primary optimization engine using historical performance data
3. **CompatibilityBasedMoldMachineOptimizer** -- Secondary optimization engine for technical compatibility
4. **MachineAssignmentProcessor** -- Assignment result processing and summary generation
5. **DataValidator** -- Schema validation and data quality assurance framework
6. **DataExporter** -- Versioned output management and Excel generation

### 2.2 Two-Tier Optimization Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              [ PendingProcessor ]                                               │
│                    Orchestrates two-tier mold-machine optimization                              │
└────────────────────────────────────┬────────────────────────────────────────────────────────────┘
        ┌───────────┬────────────────┴─────┬─────────────┬───────────────┐
        ▼ Phase 1   ▼ Phase 2              ▼ Phase 3     ▼ Phase 4       ▼ Phase 5
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Data Loading │ │ History-Based│ │ Compatibility│ │ Assignment   │ │ Export &     │
│ & Validation │ │ Optimization │ │ Optimization │ │ Processing   │ │ Versioning   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
📂 Load & Validate  🎯 Tier 1 Optimize  🔧 Tier 2 Optimize 📊 Process Results 💾 Save Results
• Schema loading    • Priority matrix   • Compatibility    • Summary creation • Excel export
• Report ingestion  • Historical data   • Technical specs  • Priority adjust  • Version control
• Data preparation  • Capacity analysis • Fallback logic   • Result combining • Change tracking
• Quality checks    • Invalid tracking  • Unassigned molds • Final validation • Backup system
```

### 2.3 Two-Tier Optimization Strategy

#### Tier 1: History-Based Optimization (Primary Engine)

  ----------------------------------------------------------------------------------------------------------
  Priority   Optimization Basis                        Success Criteria
  ---------- ---------------------------------------- ----------------------------------------------------
  **HIGH**   Historical Performance Matrix             Molds assigned based on proven machine compatibility

  **HIGH**   Production Capacity Analysis              Lead time calculations using balanced capacity data

  **HIGH**   Machine Load Balancing                   Load distribution within threshold limits

  **MEDIUM** Quality Performance History              Priority scoring based on past production success
  -----------------------------------------------------------------------------------------------------------

**Optimization Logic:**
```python
# Historical priority matrix application
priority_scores = mold_machine_priority_matrix.loc[moldNo, machineCode]
assigned_machines = select_optimal_machines(
    priority_scores, 
    current_load, 
    max_load_threshold=30
)

# Capacity-based assignment
lead_time = totalQuantity / balancedMoldHourCapacity
machine_assignment = assign_by_capacity_and_priority(
    mold_lead_times, 
    machine_availability,
    priority_matrix
)
```

#### Tier 2: Compatibility-Based Optimization (Fallback Engine)

  ----------------------------------------------------------------------------------------------------------
  Priority   Optimization Basis                        Activation Criteria
  ---------- ---------------------------------------- ----------------------------------------------------
  **HIGH**   Technical Compatibility Matrix           Unassigned molds from Tier 1 optimization

  **HIGH**   Machine-Mold Physical Constraints       Tonnage, size, and technical specifications

  **MEDIUM** Priority Order Configuration            PRIORITY_1, PRIORITY_2, or PRIORITY_3 modes

  **MEDIUM** Remaining Capacity Analysis             Available capacity after Tier 1 assignments
  -----------------------------------------------------------------------------------------------------------

**Optimization Logic:**
```python
# Technical compatibility matrix creation
compatibility_matrix = create_mold_machine_compatibility_matrix(
    machineInfo_df, 
    moldInfo_df, 
    validate_data=True
)

# Compatibility-based assignment
remaining_capacity = max_load_threshold - current_assignments
compatible_machines = filter_compatible_machines(
    unassigned_molds, 
    compatibility_matrix,
    remaining_capacity
)
```

### 2.4 Detailed Phase Breakdown

#### Phase 1: Data Loading & Validation

  ----------------------------------------------------------------------------------------------------------
  Step         Process                                  Details
  ------------ ---------------------------------------- ----------------------------------------------------
  1            Schema Configuration                     Load database schemas for validation framework

  2            Base DataFrame Loading                   Load machineInfo and moldInfo with schema validation

  3            Production Report Ingestion              Read producing processor report from change log

  4            Excel Sheet Validation                   Verify required sheets exist and load all data

  5            Invalid Molds Processing                 Parse invalid molds into categorized dictionary
  -----------------------------------------------------------------------------------------------------------

**Success Criteria:** All required data loaded with validated schemas and processed invalid molds.
**Failure Modes:** Missing Excel sheets, schema validation failures, file access errors.

**Input Sources:**
- `change_log.txt` → Latest producing processor report path
- `producing_status_data` → Current production status
- `pending_status_data` → Orders waiting for assignment
- `mold_machine_priority_matrix` → Historical performance matrix
- `mold_estimated_capacity_df` → Capacity estimates per mold
- `invalid_molds` → Quality exclusion lists

**Output:**
- Validated DataFrames ready for optimization
- Processed invalid molds dictionary
- Mold-item lead time calculations

#### Phase 2: History-Based Optimization (Tier 1)

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Initialize HistBasedMoldMachineOptimizer   Setup optimization engine with historical data

  2           Priority Matrix Application                Apply learned performance patterns for assignments

  3           Capacity-Based Load Balancing             Distribute molds based on machine capacity and load limits

  4           Assignment Quality Analysis               Track successful assignments and optimization failures

  5           Unassigned Mold Identification           Identify molds requiring Tier 2 processing
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Maximum possible molds assigned using historical performance data.
**Failure Modes:** Empty priority matrix, capacity calculation errors, load threshold violations.

**Optimization Parameters:**
- `max_load_threshold: 30` → Maximum machine load percentage
- `mold_machine_priority_matrix` → Historical performance scores
- `producing_status_data` → Current machine utilization
- `machine_info_df` → Machine specifications and capacity

**Output:**
- `assigned_matrix` → Machine-mold assignment matrix
- `hist_based_assigned_molds` → List of successfully assigned molds
- `hist_based_unassigned_molds` → List requiring Tier 2 processing

#### Phase 3: Compatibility-Based Optimization (Tier 2)

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Unassigned Data Preparation               Filter data for unassigned molds from Tier 1

  2           Compatibility Matrix Creation             Generate technical compatibility matrix

  3           Initialize CompatibilityBasedOptimizer    Setup fallback optimization engine

  4           Technical Constraint Application          Apply machine-mold physical compatibility rules

  5           Secondary Assignment Execution            Assign remaining molds based on technical feasibility
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Maximum technical compatibility assignments for remaining unassigned molds.
**Failure Modes:** No compatible machines available, capacity constraints, technical mismatches.

**Processing Decision Logic:**
```python
def _should_run_compatibility_optimization(self, unassigned_molds):
    unassigned_count = len(unassigned_molds)
    
    # Force compatibility optimization for sample data testing
    if self.config.use_sample_data:
        return True
        
    # Run only if molds remain unassigned from Tier 1
    return unassigned_count > 0
```

**Compatibility Parameters:**
- `priority_order: PRIORITY_1` → Assignment priority configuration
- `compatibility_matrix` → Technical feasibility matrix
- `max_load_threshold` → Remaining capacity constraints
- `verbose: True` → Detailed logging for optimization tracking

**Output:**
- `comp_assigned_matrix` → Additional assignments matrix
- `comp_assigned_molds` → Successfully assigned molds from Tier 2
- `comp_unassigned_molds` → Final unassigned molds requiring manual intervention

#### Phase 4: Assignment Processing & Integration

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Assignment Summary Generation             Create comprehensive assignment summaries

  2           Priority Adjustment Calculation          Adjust priorities between Tier 1 and Tier 2 assignments

  3           Result Validation & Quality Check         Verify assignment consistency and data integrity

  4           Assignment Combination                    Merge Tier 1 and Tier 2 results with proper sequencing

  5           Final Assignment Summary Creation         Generate complete assignment plan with all metadata
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Complete assignment summary with proper priority sequencing and no conflicts.
**Failure Modes:** Priority conflicts, duplicate assignments, data merge failures.

**Assignment Combination Logic:**
```python
def _combine_assignments(self, hist_based_df, compatibility_based_df):
    # Add source tracking notes
    hist_based_df['Note'] = 'histBased'
    compatibility_based_df['Note'] = 'compatibilityBased'
    
    # Calculate priority adjustments to avoid conflicts
    max_priority_by_machine = hist_based_df.groupby('Machine No.')['Priority in Machine'].max()
    compatibility_based_df['Priority in Machine'] += max_priority_by_machine
    
    # Combine and sort by machine and priority
    combined_df = pd.concat([hist_based_df, compatibility_based_df])
    return combined_df.sort_values(['Machine No.', 'Priority in Machine'])
```

**Processing Components:**
- `MachineAssignmentProcessor` → Assignment summary generation
- `producing_mold_list` → Current production context
- `machine_info_df` → Machine specifications for validation

**Output:**
- `final_assignment_summary` → Complete assignment plan
- `assignment_metadata` → Assignment source tracking and quality metrics

#### Phase 5: Export & Versioning

  ------------------------------------------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -----------------------------------------------------------
  1           Processing Result Creation                Package all optimization results and metadata

  2           Invalid Molds Summary Generation          Consolidate invalid molds from all optimization stages

  3           Excel Data Structure Preparation          Format all outputs for multi-sheet Excel export

  4           Versioned Export Generation               Create timestamped Excel output with version control

  5           Change Log Update                         Update system change log with processing status
  -------------------------------------------------------------------------------------------------------------------

**Success Criteria:** Complete Excel export with all assignment plans and quality tracking data.
**Failure Modes:** File permission errors, disk space issues, export format problems.

**Export Data Structure:**
```python
@dataclass
class ProcessingResult:
    used_producing_report_name: str                           # Source report tracking
    final_assignment_summary: pd.DataFrame                    # Complete assignment plan
    invalid_molds_dict: Dict[str, List]                      # Categorized invalid molds
    hist_based_assigned_molds: List                          # Tier 1 assignments
    hist_based_unassigned_molds: List                        # Tier 1 unassigned
    compatibility_based_assigned_molds: Optional[List]       # Tier 2 assignments
    compatibility_based_unassigned_molds: Optional[List]     # Final unassigned
    not_matched_pending: Optional[pd.DataFrame]              # Unmatched items
```

**Output Files:**
- `YYYYMMDD_HHMM_pending_processor.xlsx` → Multi-sheet assignment results
- Historical backup in `historical_db/` directory
- Updated `change_log.txt` with processing timestamp

---

## 3. Optimization Decision Flow

### 3.1 Two-Tier Decision Logic

```
[Start] → Phase 1: Data Loading
              │
              ▼
        ┌─────────────┐
        │ Data Load   │
        │ Successful? │
        └─────┬───────┘
          YES │ NO
              ▼  └──→ [Processing Failed]
        Phase 2: Tier 1 Optimization
              │
              ▼
        ┌─────────────┐
        │ History-Based│
        │ Assignment  │
        │ Complete    │
        └─────┬───────┘
              │
              ▼
        ┌─────────────┐
        │ Unassigned  │    NO     ┌─────────────────┐
        │ Molds > 0?  │──────────→│ All Assigned    │
        └─────┬───────┘           │ Export Results  │
          YES │                   └─────────────────┘
              ▼                           │
        Phase 3: Tier 2 Optimization      │
              │                           │
              ▼                           │
        ┌─────────────┐                   │
        │ Compatibility│                  │
        │ Assignment  │                   │
        │ Complete    │                   │
        └─────┬───────┘                   │
              │                           │
              ▼                           │
        Phase 4: Combine Results          │
              │                           │
              ▼                           │
        ┌─────────────┐                   │
        │ Priority    │                   │
        │ Adjustment &│                   │
        │ Integration │                   │
        └─────┬───────┘                   │
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
                 Phase 5: Export & Version
                          │
                          ▼
                  [Processing Complete]
```

### 3.2 Optimization Success Patterns

| Scenario | Tier 1 Success | Tier 2 Activation | Final Result | Processing Mode |
|----------|----------------|-------------------|--------------|-----------------|
| **🎯 Optimal** | 90-100% assigned | Not needed | Complete assignment | `histBased_only` |
| **⚖️ Hybrid** | 60-89% assigned | Activated | Combined assignment | `hybrid_optimization` |
| **🔧 Technical** | 30-59% assigned | High utilization | Technical fallback | `compatibility_heavy` |
| **⚠️ Constrained** | 10-29% assigned | Limited success | Partial assignment | `capacity_limited` |
| **❌ Failed** | <10% assigned | Minimal impact | Manual intervention | `optimization_failed` |

### 3.3 Load Balancing Strategy

```
Machine Load Distribution Logic:

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Available     │    │   Historical    │    │   Technical     │
│   Capacity      │    │   Performance   │    │   Constraints   │
│   Analysis      │    │   Weighting     │    │   Validation    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Current Load    │    │ Priority Score  │    │ Compatibility   │
│ ≤ 30% threshold │    │ Matrix Lookup   │    │ Matrix Check    │
│ per machine     │    │ (0.0 to 1.0)    │    │ (True/False)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬──────────────────┬───────────────┘
                     │                  │
                     ▼                  ▼
              ┌─────────────────────────────────┐
              │     Final Assignment Score      │
              │                                 │
              │ Score = (Historical_Priority *  │
              │          Load_Factor *          │
              │          Compatibility_Factor)  │
              └─────────────────────────────────┘
```

---

## 4. Data Flow Pipeline

### 4.1 Input Data Sources

```
Production Report Data Flow:
ProducingProcessor → change_log.txt → latest Excel file → Multi-sheet data
├── producing_status_data → Current production context
├── pending_status_data → Orders awaiting assignment
├── mold_machine_priority_matrix → Historical performance data
├── mold_estimated_capacity_df → Capacity calculations
└── invalid_molds → Quality exclusion data

Static Reference Data Flow:
DataLoaderAgent → path_annotations.json → parquet files → Reference DataFrames
├── machineInfo.parquet → Machine specifications and capacity
└── moldInfo.parquet → Mold specifications and constraints

Schema Validation Data Flow:
databaseSchemas.json → Column validation rules
sharedDatabaseSchemas.json → Shared schema definitions
```

### 4.2 Processing Data Transformations

#### Mold-Item Lead Time Calculation
```python
# Input: Pending orders + Capacity estimates
pending_status_data.columns = ['poNo', 'itemCode', 'itemName', 'poETA', 'itemQuantity', ...]
mold_estimated_capacity_df.columns = ['itemCode', 'moldNo', 'balancedMoldHourCapacity', ...]

# Transform: Match items to molds and calculate lead times
mold_lead_times, not_matched_pending = mold_item_plan_a_matching(
    pending_status_data, 
    mold_estimated_capacity_df
)

# Output: Lead time calculations
mold_lead_times.columns = ['itemCode', 'moldNo', 'totalQuantity', 'moldLeadTime', ...]
```

#### Assignment Matrix Generation
```python
# Input: Optimization results
assigned_matrix = optimization_results.assigned_matrix  # Machine x Mold matrix

# Transform: Convert matrix to assignment summaries
assignment_processor = MachineAssignmentProcessor(
    assigned_matrix,
    mold_lead_times, 
    pending_data,
    machine_info_df,
    producing_context
)

# Output: Assignment summaries with priorities and scheduling
assignment_summary.columns = ['Machine No.', 'Machine Code', 'Priority in Machine', 
                              'moldNo', 'itemCode', 'PO Quantity', ...]
```

#### Invalid Molds Processing
```python
# Input: Raw invalid molds data from Excel
invalid_molds_excel.columns = ['estimated_capacity_invalid_molds', 'priority_matrix_invalid_molds', ...]

# Transform: Convert to categorized dictionary
invalid_molds_dict = {
    col: invalid_molds[col].dropna().tolist() 
    for col in invalid_molds.columns
}

# Additional processing results
invalid_molds_dict['mold_machine_optimizer'] = comp_unassigned_molds

# Output: Categorized invalid molds for quality tracking
```

### 4.3 Production Plans Hierarchy

```
agents/shared_db/          
├── ProducingProcessor
|     └── change_log.txt                                  # ProducingProcessor changes (PendingProcessor input)
└── PendingProcessor                                      # PendingProcessor outputs  
    ├── historical_db/                                      
    ├── newest/                                             
    |   └── YYYYMMDD_HHMM_pending_processor.xlsx           
    └── change_log.txt                                    # PendingProcessor change log

Excel Sheet Structure:
├── initialPlan                                       # Main assignment plan
└── invalid_molds                                     # Quality tracking data
```

---

## 5. Quality Assurance Framework

### 5.1 Multi-Level Validation Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Schema        │    │   Optimization  │    │   Assignment    │    │   Export        │
│   Validation    │    │   Validation    │    │   Validation    │    │   Validation    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │                      │
          ▼                      ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ DataFrame Schema│    │ Matrix Quality  │    │ Priority        │    │ File Format     │
│ Excel Sheets    │    │ Capacity Checks │    │ Consistency     │    │ Version Control │
│ Column Presence │    │ Load Thresholds │    │ Assignment Logic│    │ Data Completeness│
│ Data Types      │    │ Invalid Tracking│    │ Merge Integrity │    │ Export Success  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5.2 Validation Checkpoints

#### Schema Validation (Phase 1)
- **DataFrame Validation**: `@validate_init_dataframes` decorator enforcement
- **Excel Sheet Validation**: Required sheets existence and structure verification
- **Column Validation**: `validate_dataframe()` function for expected columns
- **Data Type Validation**: Schema compliance checking against database definitions

#### Optimization Validation (Phases 2-3)
- **Priority Matrix Quality**: Valid priority scores and matrix completeness
- **Capacity Calculation Validation**: Positive lead times and valid capacity values
- **Load Threshold Compliance**: Machine load within configured limits (≤30%)
- **Assignment Logic Validation**: No duplicate assignments or priority conflicts

#### Integration Validation (Phase 4)
- **Assignment Combination**: Successful merge without data loss
- **Priority Adjustment**: Proper sequencing between Tier 1 and Tier 2 assignments
- **Data Completeness**: All required columns populated in final summary
- **Assignment Consistency**: No orphaned assignments or missing machine data

#### Export Validation (Phase 5)
- **File Creation Success**: Excel file generated without errors
- **Data Integrity**: All sheets exported with complete data
- **Version Control**: Proper timestamp and backup creation
- **Schema Compliance**: Output matches expected ProcessingResult structure

### 5.3 Error Recovery Strategies

#### Graceful Degradation Levels

1. **Full Optimization** (90-100% assignment rate)
   - Both Tier 1 and Tier 2 successfully complete
   - Complete assignment coverage with minimal invalid molds
   - Full export with comprehensive data

2. **Hybrid Success** (70-89% assignment rate)
   - Tier 1 successful with partial Tier 2 completion
   - Some unassigned molds requiring manual intervention
   - Complete export with quality warnings

3. **Historical Only** (50-69% assignment rate)
   - Tier 1 successful but Tier 2 fails or skipped
   - Higher unassigned mold count requiring review
   - Export with historical assignments only

4. **Minimal Processing** (30-49% assignment rate)
   - Limited optimization success with high invalid rate
   - Significant manual intervention required
   - Export with error reporting and fallback data

5. **Processing Failure** (<30% assignment rate)
   - System-wide optimization failure
   - Emergency logging and notification protocols
   - Manual takeover required for assignment planning

---

## 6. Configuration Management

### 6.1 Configuration Classes

#### ProcessingConfig
```python
@dataclass
class ProcessingConfig:
    max_load_threshold: int = 30                    # Machine load limit (%)
    priority_order: PriorityOrder = PRIORITY_1      # Assignment priority mode
    log_progress_interval: int = 5                  # Logging frequency
    verbose: bool = True                            # Detailed logging flag
    use_sample_data: bool = False                   # Testing mode flag
```

#### ExcelSheetMapping
```python
@dataclass
class ExcelSheetMapping:
    producing_status_data: str = 'producing_status_data'
    pending_status_data: str = 'pending_status_data'  
    mold_machine_priority_matrix: str = 'mold_machine_priority_matrix'
    mold_estimated_capacity_df: str = 'mold_estimated_capacity_df'
    invalid_molds: str = 'invalid_molds'
    
    def get_sheets_requiring_index(self) -> List[str]:
        return [self.mold_machine_priority_matrix]  # Special index processing
```

### 6.2 Optimization Parameters

#### Tier 1 Parameters (History-Based)
- **max_load_threshold**: `30%` → Maximum machine utilization limit
- **priority_matrix**: Historical performance weights (0.0-1.0 scale)
- **capacity_balancing**: Lead time calculations with balanced capacity
- **invalid_tracking**: Quality exclusion and tracking mechanisms

#### Tier 2 Parameters (Compatibility-Based)  
- **priority_order**: `PRIORITY_1`, `PRIORITY_2`, `PRIORITY_3` modes
- **compatibility_matrix**: Technical feasibility constraints
- **log_progress_interval**: Progress logging frequency for long operations
- **verbose_mode**: Detailed optimization step logging

### 6.3 Sample Data Configuration

```python
# Sample data for testing (Round 3 configuration)
sample_unassigned_molds = [
    '15300CBS-M-001', 'PSSC-M-001', '12002CBS-M-001', 
    'PGXSR-M-001', 'PSPH2-M-001', '14102CAJ-M-003',
    'PXNLG5-M-001', '12000CBG-M-001', '16200CBG-M-001'
]

sample_test_quantities = [100000, 10000, 15000, 44000, 2516, 
                         180000, 155000, 340000, 175000]

# Force compatibility optimization for sample testing
if config.use_sample_data:
    return True  # Always run Tier 2 for comprehensive testing
```

---

## 7. Monitoring & Performance

### 7.1 Key Performance Indicators

| Metric Category | Metric Name | Target Value | Alert Threshold |
|----------------|-------------|--------------|-----------------|
| **Assignment Efficiency** | Tier 1 Assignment Rate | > 80% | < 60% |
| **Overall Coverage** | Total Assignment Rate | > 90% | < 70% |
| **Processing Speed** | Total Execution Time | < 3 minutes | > 8 minutes |
| **Data Quality** | Invalid Mold Rate | < 10% | > 25% |
| **System Health** | Processing Success Rate | > 95% | < 85% |

### 7.2 Optimization Performance Tracking

```
Assignment Rate Analysis:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tier 1        │    │   Tier 2        │    │   Overall       │
│   Performance   │    │   Performance   │    │   Performance   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Historical      │    │ Compatibility   │    │ Combined        │
│ Assignment %    │    │ Assignment %    │    │ Coverage %      │
│ Target: >80%    │    │ Target: >70%    │    │ Target: >90%    │
│ Alert: <60%     │    │ Alert: <50%     │    │ Alert: <70%     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 7.3 Quality Metrics Dashboard

```python
def calculate_quality_metrics(processing_result: ProcessingResult) -> Dict:
    """Calculate comprehensive quality metrics for monitoring"""
    
    metrics = {
        "timestamp": datetime.now(),
        "assignment_metrics": {},
        "data_quality": {},
        "processing_performance": {}
    }
    
    # Assignment efficiency calculations
    total_molds = (len(processing_result.hist_based_assigned_molds) + 
                   len(processing_result.hist_based_unassigned_molds))
    
    metrics["assignment_metrics"] = {
        "tier1_assignment_rate": len(processing_result.hist_based_assigned_molds) / max(1, total_molds),
        "tier2_assignment_rate": len(processing_result.compatibility_based_assigned_molds or []) / 
                                max(1, len(processing_result.hist_based_unassigned_molds or [])),
        "overall_coverage": len(processing_result.final_assignment_summary) / max(1, total_molds),
        "final_unassigned": len(processing_result.compatibility_based_unassigned_molds or [])
    }
    
    # Data quality assessment
    invalid_categories = list(processing_result.invalid_molds_dict.keys())
    total_invalid = sum(len(molds) for molds in processing_result.invalid_molds_dict.values())
    
    metrics["data_quality"] = {
        "invalid_mold_categories": len(invalid_categories),
        "total_invalid_molds": total_invalid,
        "invalid_rate": total_invalid / max(1, total_molds + total_invalid),
        "not_matched_pending": len(processing_result.not_matched_pending or [])
    }
    
    return metrics
```

---

## 8. Usage Examples

### 8.1 Standard Pending Order Processing

```python
# Initialize processor with default settings
processor = PendingProcessor()

# Execute complete two-tier optimization workflow
result = processor.run()

# Monitor optimization results
print(f"Report source: {result.used_producing_report_name}")
print(f"Tier 1 assigned: {len(result.hist_based_assigned_molds)}")
print(f"Tier 1 unassigned: {len(result.hist_based_unassigned_molds)}")

if result.compatibility_based_assigned_molds:
    print(f"Tier 2 assigned: {len(result.compatibility_based_assigned_molds)}")
    print(f"Tier 2 unassigned: {len(result.compatibility_based_unassigned_molds)}")

print(f"Final assignment summary: {len(result.final_assignment_summary)} entries")
print(f"Invalid molds categories: {list(result.invalid_molds_dict.keys())}")

# Export with versioning
final_data = processor.run_and_save_results()
print(f"Export complete: {list(final_data.keys())}")
```

### 8.2 High-Efficiency Configuration

```python
# Configure for maximum assignment efficiency
config = ProcessingConfig(
    max_load_threshold=35,        # Higher capacity utilization
    priority_order=PriorityOrder.PRIORITY_1,  # Highest priority assignments
    verbose=True,                 # Detailed optimization logging
    use_sample_data=False        # Production data mode
)

sheet_mapping = ExcelSheetMapping()  # Use default sheet mappings

# Initialize with high-efficiency configuration
processor = PendingProcessor(
    config=config,
    sheet_mapping=sheet_mapping
)

# Execute optimization with performance monitoring
start_time = time.time()
result = processor.run()
processing_time = time.time() - start_time

# Analyze efficiency metrics
tier1_efficiency = len(result.hist_based_assigned_molds) / (
    len(result.hist_based_assigned_molds) + len(result.hist_based_unassigned_molds)
)

print(f"Processing completed in {processing_time:.2f} seconds")
print(f"Tier 1 efficiency: {tier1_efficiency:.1%}")

if tier1_efficiency > 0.85:
    print("✅ High-efficiency target achieved")
else:
    print("⚠️ Efficiency below target, investigating...")
    # Analyze invalid molds for efficiency bottlenecks
    for category, molds in result.invalid_molds_dict.items():
        if molds:
            print(f"  - {category}: {len(molds)} invalid molds")
```

### 8.3 Development and Testing Workflow

```python
# Enable comprehensive logging for development
import logging
logging.getLogger("PendingProcessor").setLevel(logging.DEBUG)

# Configure for testing with sample data
test_config = ProcessingConfig(
    max_load_threshold=25,       # Conservative load for testing
    priority_order=PriorityOrder.PRIORITY_1,
    log_progress_interval=1,     # Detailed progress logging
    verbose=True,
    use_sample_data=True         # Force sample data usage
)

# Initialize processor with test configuration
processor = PendingProcessor(
    source_path="test/data/path",
    default_dir="test/output/path",
    config=test_config
)

# Test individual workflow phases
try:
    # Phase 1: Data loading test
    processor._load_and_validate_data()
    print("✅ Phase 1: Data loading and validation successful")
    print(f"  - Producing orders: {len(processor.producing_status_data)}")
    print(f"  - Pending orders: {len(processor.pending_status_data)}")
    print(f"  - Invalid mold categories: {list(processor.invalid_molds_dict.keys())}")
    
    # Phase 2: Tier 1 optimization test
    (hist_assigned_matrix, 
     hist_assignment_summary, 
     hist_assigned_molds, 
     hist_unassigned_molds) = processor._process_history_based_phase()
    
    print("✅ Phase 2: History-based optimization successful")
    print(f"  - Assigned molds: {len(hist_assigned_molds)}")
    print(f"  - Unassigned molds: {len(hist_unassigned_molds)}")
    
    # Phase 3: Tier 2 optimization test (conditional)
    if processor._should_run_compatibility_optimization(hist_unassigned_molds):
        (comp_assignment_summary,
         comp_assigned_molds,
         comp_unassigned_molds) = processor._process_compatibility_based_phase(
            hist_assigned_matrix, hist_unassigned_molds)
        
        print("✅ Phase 3: Compatibility-based optimization successful")
        print(f"  - Additional assignments: {len(comp_assigned_molds)}")
        print(f"  - Final unassigned: {len(comp_unassigned_molds)}")
        
        # Phase 4: Assignment combination test
        final_summary = processor._combine_assignments(
            hist_assignment_summary, comp_assignment_summary)
        print("✅ Phase 4: Assignment combination successful")
        print(f"  - Final assignment entries: {len(final_summary)}")
    else:
        print("ℹ️  Phase 3: Compatibility optimization skipped (no unassigned molds)")
        final_summary = hist_assignment_summary
    
    # Phase 5: Export test
    result = processor._create_processing_result(
        final_summary, hist_assigned_molds, hist_unassigned_molds,
        comp_assigned_molds if 'comp_assigned_molds' in locals() else None,
        comp_unassigned_molds if 'comp_unassigned_molds' in locals() else None
    )
    
    export_data = processor.run_and_save_results()
    print("✅ Phase 5: Export and versioning successful")
    print(f"  - Export sheets: {list(export_data.keys())}")
    
except Exception as e:
    print(f"❌ Workflow test failed: {e}")
    
    # Diagnostic information
    if hasattr(processor, 'producing_status_data'):
        print(f"  - Debug: Producing data shape: {processor.producing_status_data.shape}")
    if hasattr(processor, 'pending_status_data'):
        print(f"  - Debug: Pending data shape: {processor.pending_status_data.shape}")
    if hasattr(processor, 'invalid_molds_dict'):
        print(f"  - Debug: Invalid molds: {processor.invalid_molds_dict}")
```

### 8.4 Production Monitoring Integration

```python
# Continuous monitoring setup with alerting
import schedule
import time
from datetime import datetime, timedelta

def monitor_pending_processor():
    """Automated pending processor monitoring with quality alerts"""
    
    monitoring_start = time.time()
    
    try:
        # Health check before processing
        processor = PendingProcessor()
        
        # Validate data availability
        try:
            processor._load_and_validate_data()
            data_health = "healthy"
        except Exception as data_error:
            data_health = "degraded"
            logger.warning(f"Data loading issues: {data_error}")
        
        # Execute processing based on health
        if data_health == "healthy":
            # Standard processing
            result = processor.run()
            processing_success = True
            
            # Calculate quality metrics
            quality_metrics = calculate_quality_metrics(result)
            
            # Quality assessment
            tier1_rate = quality_metrics["assignment_metrics"]["tier1_assignment_rate"]
            overall_coverage = quality_metrics["assignment_metrics"]["overall_coverage"]
            invalid_rate = quality_metrics["data_quality"]["invalid_rate"]
            
            # Generate alerts based on quality thresholds
            alerts = []
            
            if tier1_rate < 0.60:
                alerts.append(f"🚨 CRITICAL: Tier 1 assignment rate below 60%: {tier1_rate:.1%}")
            elif tier1_rate < 0.80:
                alerts.append(f"⚠️  WARNING: Tier 1 assignment rate below target: {tier1_rate:.1%}")
            
            if overall_coverage < 0.70:
                alerts.append(f"🚨 CRITICAL: Overall coverage below 70%: {overall_coverage:.1%}")
            elif overall_coverage < 0.90:
                alerts.append(f"⚠️  WARNING: Overall coverage below target: {overall_coverage:.1%}")
            
            if invalid_rate > 0.25:
                alerts.append(f"🚨 CRITICAL: Invalid mold rate above 25%: {invalid_rate:.1%}")
            elif invalid_rate > 0.10:
                alerts.append(f"⚠️  WARNING: Invalid mold rate above target: {invalid_rate:.1%}")
            
            # Export results
            export_data = processor.run_and_save_results()
            
            # Update monitoring dashboard
            monitoring_data = {
                "timestamp": datetime.now(),
                "status": "success" if not alerts or all("WARNING" in alert for alert in alerts) else "degraded",
                "processing_time_seconds": time.time() - monitoring_start,
                "quality_metrics": quality_metrics,
                "alerts": alerts,
                "export_sheets": list(export_data.keys()) if export_data else [],
                "source_report": result.used_producing_report_name
            }
            
            # Log success and metrics
            logger.info(f"Pending processor monitoring successful")
            logger.info(f"Assignment coverage: {overall_coverage:.1%}")
            logger.info(f"Processing time: {monitoring_data['processing_time_seconds']:.2f}s")
            
            # Send alerts if any
            for alert in alerts:
                if "CRITICAL" in alert:
                    send_critical_alert(f"PendingProcessor: {alert}")
                else:
                    send_warning_alert(f"PendingProcessor: {alert}")
            
        else:
            # Degraded mode processing
            logger.warning("Attempting degraded mode processing")
            
            # Try with conservative settings
            fallback_config = ProcessingConfig(
                max_load_threshold=20,    # Very conservative load
                verbose=False,            # Reduce logging overhead
                use_sample_data=False     # Still use production data if available
            )
            
            fallback_processor = PendingProcessor(config=fallback_config)
            result = fallback_processor.run()
            
            monitoring_data = {
                "timestamp": datetime.now(),
                "status": "degraded",
                "processing_time_seconds": time.time() - monitoring_start,
                "mode": "fallback_processing",
                "source_report": result.used_producing_report_name
            }
            
            send_warning_alert("PendingProcessor running in degraded mode")
            
    except Exception as e:
        # Complete processing failure
        logger.error(f"Pending processor monitoring failed: {e}")
        
        monitoring_data = {
            "timestamp": datetime.now(),
            "status": "failed",
            "processing_time_seconds": time.time() - monitoring_start,
            "error": str(e)
        }
        
        send_critical_alert(f"PendingProcessor complete failure: {e}")
        
        # Attempt emergency data collection
        try:
            emergency_processor = PendingProcessor()
            emergency_processor._load_and_validate_data()
            logger.info("Emergency data validation successful - system recoverable")
        except Exception as emergency_error:
            logger.critical(f"Emergency validation also failed: {emergency_error}")
    
    # Update system monitoring dashboard
    update_monitoring_dashboard("pending_processor", monitoring_data)

def calculate_quality_metrics(processing_result):
    """Calculate comprehensive quality metrics for the processing result"""
    
    # Total molds calculation
    total_hist_molds = (len(processing_result.hist_based_assigned_molds) + 
                       len(processing_result.hist_based_unassigned_molds))
    
    tier1_unassigned = len(processing_result.hist_based_unassigned_molds)
    tier2_assigned = len(processing_result.compatibility_based_assigned_molds or [])
    tier2_unassigned = len(processing_result.compatibility_based_unassigned_molds or [])
    
    # Calculate assignment rates
    tier1_rate = len(processing_result.hist_based_assigned_molds) / max(1, total_hist_molds)
    tier2_rate = tier2_assigned / max(1, tier1_unassigned) if tier1_unassigned > 0 else 1.0
    overall_coverage = len(processing_result.final_assignment_summary) / max(1, total_hist_molds)
    
    # Invalid molds analysis
    total_invalid = sum(len(molds) for molds in processing_result.invalid_molds_dict.values())
    invalid_rate = total_invalid / max(1, total_hist_molds + total_invalid)
    
    return {
        "assignment_metrics": {
            "tier1_assignment_rate": tier1_rate,
            "tier2_assignment_rate": tier2_rate,
            "overall_coverage": overall_coverage,
            "final_unassigned_count": tier2_unassigned
        },
        "data_quality": {
            "invalid_mold_categories": len(processing_result.invalid_molds_dict),
            "total_invalid_molds": total_invalid,
            "invalid_rate": invalid_rate,
            "not_matched_pending_count": len(processing_result.not_matched_pending or [])
        },
        "processing_statistics": {
            "total_molds_processed": total_hist_molds,
            "final_assignment_entries": len(processing_result.final_assignment_summary),
            "source_report": processing_result.used_producing_report_name
        }
    }

# Schedule automated processing and monitoring
schedule.every(30).minutes.do(monitor_pending_processor)        # Every 30 minutes
schedule.every().day.at("07:00").do(monitor_pending_processor)  # Daily morning run
schedule.every().day.at("13:00").do(monitor_pending_processor)  # Daily afternoon run
schedule.every().day.at("19:00").do(monitor_pending_processor)  # Daily evening run

# Continuous monitoring loop
def start_pending_processor_monitoring():
    """Start the continuous monitoring system"""
    logger.info("Starting PendingProcessor continuous monitoring system")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Monitoring system stopped by user")
            break
        except Exception as monitor_error:
            logger.error(f"Monitoring system error: {monitor_error}")
            time.sleep(300)  # Wait 5 minutes before retrying

# Health check endpoint for system status
def pending_processor_health_check():
    """Quick health check for external monitoring systems"""
    
    try:
        processor = PendingProcessor()
        processor._setup_schemas()
        
        # Test data loading
        start_time = time.time()
        processor._load_and_validate_data()
        load_time = time.time() - start_time
        
        # Basic system health indicators
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "data_loading_time_seconds": load_time,
            "system_components": {
                "schema_validation": "operational",
                "data_sources": "accessible",
                "optimization_engines": "ready"
            },
            "data_summary": {
                "producing_orders": len(processor.producing_status_data) if processor.producing_status_data is not None else 0,
                "pending_orders": len(processor.pending_status_data) if processor.pending_status_data is not None else 0,
                "invalid_mold_categories": len(processor.invalid_molds_dict)
            }
        }
        
        # Performance indicators
        if load_time > 30:  # Alert if loading takes more than 30 seconds
            health_status["overall_status"] = "degraded"
            health_status["warnings"] = ["Data loading performance below optimal"]
            
        return health_status
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "failed",
            "error": str(e),
            "system_components": {
                "schema_validation": "error",
                "data_sources": "error",
                "optimization_engines": "error"
            }
        }

# Example usage for monitoring integration
if __name__ == "__main__":
    # Run health check
    health = pending_processor_health_check()
    print(f"System health: {health['overall_status']}")
    
    if health['overall_status'] == 'healthy':
        # Start continuous monitoring
        start_pending_processor_monitoring()
    else:
        print(f"System health check failed: {health}")
```

---

## 9. Integration Patterns

### 9.1 Upstream Integration (ProducingProcessor)

```python
# Integration with ProducingProcessor workflow
class PendingProcessorIntegration:
    
    def __init__(self):
        self.producing_processor = ProducingProcessor()
        self.pending_processor = PendingProcessor()
    
    def integrated_workflow(self):
        """Execute integrated producing and pending processing workflow"""
        
        # Phase 1: Execute producing processor
        logger.info("Starting integrated workflow with ProducingProcessor")
        producing_results = self.producing_processor.process_and_save_results()
        
        # Phase 2: Validate producing processor output
        producing_report_path = self.producing_processor._get_report_path()
        
        if not producing_report_path or not os.path.exists(producing_report_path):
            raise IntegrationError("ProducingProcessor output not available for PendingProcessor")
        
        # Phase 3: Execute pending processor with fresh data
        logger.info("Starting PendingProcessor with ProducingProcessor output")
        pending_results = self.pending_processor.run_and_save_results()
        
        # Phase 4: Create integrated summary
        integrated_summary = {
            "workflow_timestamp": datetime.now(),
            "producing_processor": {
                "status": "success",
                "output_sheets": list(producing_results.keys()),
                "report_path": producing_report_path
            },
            "pending_processor": {
                "status": "success",
                "output_sheets": list(pending_results.keys()),
                "assignment_count": len(pending_results['initialPlan'])
            },
            "integration_metrics": {
                "total_processing_time": "calculated_in_implementation",
                "data_consistency_check": "passed"
            }
        }
        
        return integrated_summary
```

### 9.2 Downstream Integration (Production Planning)

```python
# Integration with downstream production planning systems
def integrate_with_production_planning(pending_processor_result: ProcessingResult):
    """Integrate PendingProcessor results with production planning systems"""
    
    # Extract assignment plan for production scheduling
    assignment_plan = pending_processor_result.final_assignment_summary
    
    # Transform to production planning format
    production_schedule = []
    
    for _, assignment in assignment_plan.iterrows():
        schedule_entry = {
            "machine_code": assignment['Machine Code'],
            "machine_number": assignment['Machine No.'],
            "mold_number": assignment['moldNo'],
            "item_code": assignment['itemCode'],
            "priority": assignment['Priority in Machine'],
            "quantity": assignment['PO Quantity'],
            "assignment_source": assignment.get('Note', 'unknown'),
            "scheduling_date": datetime.now().date(),
            "estimated_start_time": "calculated_based_on_priority",
            "estimated_completion_time": "calculated_based_on_capacity"
        }
        production_schedule.append(schedule_entry)
    
    # Quality control integration
    quality_alerts = []
    
    # Check for high invalid mold rates
    total_invalid = sum(len(molds) for molds in pending_processor_result.invalid_molds_dict.values())
    if total_invalid > 0:
        quality_alerts.append({
            "alert_type": "invalid_molds",
            "severity": "warning" if total_invalid < 10 else "critical",
            "message": f"{total_invalid} molds excluded from optimization",
            "details": pending_processor_result.invalid_molds_dict
        })
    
    # Check for unassigned orders
    if pending_processor_result.compatibility_based_unassigned_molds:
        quality_alerts.append({
            "alert_type": "unassigned_orders",
            "severity": "critical",
            "message": f"{len(pending_processor_result.compatibility_based_unassigned_molds)} orders require manual assignment",
            "details": pending_processor_result.compatibility_based_unassigned_molds
        })
    
    return {
        "production_schedule": production_schedule,
        "quality_alerts": quality_alerts,
        "integration_timestamp": datetime.now(),
        "source_report": pending_processor_result.used_producing_report_name
    }
```

---

## 10. Troubleshooting Guide

### 10.1 Common Issues and Solutions

#### Data Loading Issues

| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| **Missing Excel Sheets** | `DataValidationError: Missing required sheets` | ProducingProcessor output incomplete | Verify ProducingProcessor execution and output structure |
| **Schema Validation Failure** | `@validate_init_dataframes` errors | Column mismatches or data type issues | Check database schema updates and data source changes |
| **File Access Errors** | `FileNotFoundError` or permission errors | File system permissions or path issues | Verify file paths and system permissions |
| **Corrupted Data** | `ParquetInvalidError` or similar | Data file corruption | Restore from backup or regenerate data files |

#### Optimization Issues

| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| **High Invalid Mold Rate** | >25% invalid molds | Data quality or historical data issues | Review data sources and historical performance data |
| **Low Assignment Rate** | <70% overall coverage | Capacity constraints or compatibility issues | Adjust `max_load_threshold` or review machine-mold constraints |
| **Tier 1 Failure** | History-based optimization fails completely | Priority matrix or capacity data issues | Check `mold_machine_priority_matrix` data quality |
| **Tier 2 Failure** | Compatibility optimization fails | Machine-mold compatibility data issues | Verify `machineInfo_df` and `moldInfo_df` completeness |

#### Processing Issues

| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| **Assignment Conflicts** | Duplicate priorities or assignments | Priority calculation errors | Check `_combine_assignments()` logic and priority adjustment |
| **Memory Issues** | `MemoryError` or performance degradation | Large dataset processing | Implement batch processing or increase system memory |
| **Export Failures** | Excel generation errors | File system or formatting issues | Check disk space and file permissions |
| **Performance Degradation** | >8 minute processing times | Data volume or system resource issues | Optimize queries and implement performance monitoring |

### 10.2 Diagnostic Commands

```python
# Comprehensive diagnostic suite
def run_pending_processor_diagnostics():
    """Run comprehensive diagnostics for PendingProcessor"""
    
    diagnostics = {
        "timestamp": datetime.now(),
        "system_health": {},
        "data_quality": {},
        "performance_metrics": {},
        "recommendations": []
    }
    
    try:
        # System health checks
        processor = PendingProcessor()
        
        # Check 1: Schema validation
        try:
            processor._setup_schemas()
            diagnostics["system_health"]["schema_loading"] = "✅ Pass"
        except Exception as e:
            diagnostics["system_health"]["schema_loading"] = f"❌ Fail: {e}"
            diagnostics["recommendations"].append("Review database schema files")
        
        # Check 2: Data source accessibility
        try:
            report_path = processor._get_report_path()
            if os.path.exists(report_path):
                diagnostics["system_health"]["data_source"] = "✅ Pass"
                diagnostics["data_quality"]["report_path"] = report_path
            else:
                diagnostics["system_health"]["data_source"] = f"❌ Fail: Report not found at {report_path}"
                diagnostics["recommendations"].append("Check ProducingProcessor execution")
        except Exception as e:
            diagnostics["system_health"]["data_source"] = f"❌ Fail: {e}"
        
        # Check 3: Data loading performance
        try:
            start_time = time.time()
            processor._load_and_validate_data()
            load_time = time.time() - start_time
            
            diagnostics["performance_metrics"]["data_loading_time"] = f"{load_time:.2f}s"
            if load_time < 30:
                diagnostics["system_health"]["data_loading_performance"] = "✅ Pass"
            else:
                diagnostics["system_health"]["data_loading_performance"] = "⚠️ Slow"
                diagnostics["recommendations"].append("Investigate data loading performance")
            
            # Data quality assessment
            diagnostics["data_quality"]["producing_orders"] = len(processor.producing_status_data) if processor.producing_status_data is not None else 0
            diagnostics["data_quality"]["pending_orders"] = len(processor.pending_status_data) if processor.pending_status_data is not None else 0
            diagnostics["data_quality"]["invalid_categories"] = list(processor.invalid_molds_dict.keys())
            
        except Exception as e:
            diagnostics["system_health"]["data_loading_performance"] = f"❌ Fail: {e}"
        
        # Check 4: Optimization readiness
        try:
            # Test Tier 1 readiness
            if (processor.mold_machine_priority_matrix is not None and 
                not processor.mold_machine_priority_matrix.empty):
                diagnostics["system_health"]["tier1_readiness"] = "✅ Pass"
            else:
                diagnostics["system_health"]["tier1_readiness"] = "❌ Fail: Priority matrix not available"
                diagnostics["recommendations"].append("Check historical performance data")
            
            # Test Tier 2 readiness  
            if (processor.machineInfo_df is not None and processor.moldInfo_df is not None):
                diagnostics["system_health"]["tier2_readiness"] = "✅ Pass"
            else:
                diagnostics["system_health"]["tier2_readiness"] = "❌ Fail: Machine or mold info not available"
                diagnostics["recommendations"].append("Check static data sources")
                
        except Exception as e:
            diagnostics["system_health"]["tier1_readiness"] = f"❌ Fail: {e}"
            diagnostics["system_health"]["tier2_readiness"] = f"❌ Fail: {e}"
        
    except Exception as e:
        diagnostics["system_health"]["overall"] = f"❌ Critical Failure: {e}"
        diagnostics["recommendations"].append("System requires immediate attention")
    
    # Generate summary recommendations
    failed_checks = sum(1 for check in diagnostics["system_health"].values() if "❌" in str(check))
    warning_checks = sum(1 for check in diagnostics["system_health"].values() if "⚠️" in str(check))
    
    if failed_checks == 0 and warning_checks == 0:
        diagnostics["summary"] = "✅ All systems operational"
    elif failed_checks == 0:
        diagnostics["summary"] = f"⚠️ System operational with {warning_checks} warnings"
    else:
        diagnostics["summary"] = f"❌ System issues detected: {failed_checks} failures, {warning_checks} warnings"
    
    return diagnostics

# Usage example
if __name__ == "__main__":
    print("Running PendingProcessor Diagnostics...")
    diagnostics = run_pending_processor_diagnostics()
    
    print(f"\n{diagnostics['summary']}")
    print(f"\nSystem Health Checks:")
    for check, result in diagnostics["system_health"].items():
        print(f"  {check}: {result}")
    
    if diagnostics["recommendations"]:
        print(f"\nRecommendations:")
        for i, rec in enumerate(diagnostics["recommendations"], 1):
            print(f"  {i}. {rec}")
    
    print(f"\nData Quality Metrics:")
    for metric, value in diagnostics["data_quality"].items():
        print(f"  {metric}: {value}")
```