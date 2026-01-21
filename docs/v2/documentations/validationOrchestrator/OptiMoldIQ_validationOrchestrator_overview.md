>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# ValidationOrchestrator

## 1. Agent Info

- **Name**: ValidationOrchestrator
- **Purpose**:
  - Coordinate multiple validation processes (static, dynamic, and required field validation)
  - Ensure manufacturing data quality and schema consistency across datasets
  - Provide consolidated reporting and version-controlled validation results
- **Owner**:
- **Status**: Active
- **Location**: agents/validationOrchestrator/

---

## 2. What it does
The `ValidationOrchestrator` coordinates validation workflows across both dynamic data (e.g., product records, purchase orders) and static reference data (e.g., item, resin, machine, and mold information). 
It integrates three main validation components:

-  [StaticCrossDataChecker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_staticCrossDataChecker_overview.md) – ensures consistency against reference datasets
- [PORequiredCriticalValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_poRequiredCriticalValidator_overview.md) – verifies required fields in purchase orders
- [DynamicCrossDataValidator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_dynamicCrossDataValidator_overview.md)  – validates relationships across dynamic datasets
  
The orchestrator consolidates all results into structured reports, exports them with versioning, and logs detailed execution outcomes for monitoring and recovery.

### Key Features

- **Multi-Stage Validation**
  - Static cross-data validation against reference datasets
  - Purchase order required field validation
  - Dynamic cross-data validation across frequently updated datasets
- **Schema Enforcement**
  - Ensures loaded DataFrames conform to database schema definitions
  - Validates parquet files against annotated schema metadata
- **Consolidated Reporting**
  - Aggregates validation results from multiple checks
  - Produces combined DataFrame for unified reporting
- **Versioned Output**
  - Exports validation results with timestamp-based versioning
  - Prevents overwriting through automated file management
- **Error Handling & Logging**
  - Structured error handling for missing files or schema mismatches
  - Detailed logging for each DataFrame load and validation step

---

## 3. Architecture Overview
```
                    ┌─────────────────────────┐
                    │   ValidationOrchestrator│
                    │   (Main Coordinator)    │
                    └───────────────┬─────────┘
                                    │
                    ┌──────────────┼──────────────────────────────┐
                    │              │                              │
                    v              v                              v
┌──────────────────────┐   ┌──────────────────────┐   ┌─────────────────────────┐
│ StaticCrossDataChecker│   │PORequiredCriticalVal.│   │DynamicCrossDataValidator│
│ (Reference Consistency)│ │ (PO Required Fields) │   │ (Cross-Dataset Checks)  │
└─────────────┬────────┘   └────────────┬────────┘   └──────────────┬─────────┘
              │                         │                           │
              v                         v                           v
       ┌──────────────┐         ┌──────────────┐            ┌──────────────┐
       │ Static Mismatch│       │ PO Field Warn │            │ Dynamic Issues│
       └──────────────┘         └──────────────┘            └──────────────┘
                      \            |            /
                       \           |           /
                        \          v          /
                         ┌──────────────────┐
                         │ Consolidated      │
                         │ Validation Report │
                         └──────────────────┘
```

---

## 4. Pre-requisites Checklist
Before running the pipeline, ensure:

- [ ] **Annotation path (DataLoaderAgent) available**: `path_annotations.json`
- [ ] **Static reference data available**: Item, Resin, Machine, and Mold datasets
- [ ] **Dynamic data available**: Purchase Orders, product master, monthly reports
- [ ] **Schema file accessible**: `database/databaseSchemas.json` 
- [ ] **Write permissions**: Full access to `agents/shared_db/`
- [ ] **Python dependencies**: loguru, pathlib, pandas, pyarrow
- [ ] **Disk space**: At least 2x input data size available

---

## 5. Error Handling Scenarios
| Scenario       | Static Validation | PO Validation | Dynamic Validation | Final Status      | Action Required                 |
| -------------- | ----------------- | ------------- | ------------------ | ----------------- | ------------------------------- |
| Happy Path     | ✅ Success         | ✅ Success     | ✅ Success          | `success`         | None                            |
| Static Fail    | ❌ Failed          | ✅ Success     | ✅ Success          | `partial_success` | Fix static reference data       |
| PO Fail        | ✅ Success         | ❌ Failed      | ✅ Success          | `failed`          | Check missing/invalid PO fields |
| Dynamic Fail   | ✅ Success         | ✅ Success     | ❌ Failed           | `failed`          | Inspect relational integrity    |
| Multiple Fails | ❌ Failed          | ❌ Failed      | ❌ Failed           | `failed`          | Full manual review              |

---

## 6. Input & Output
- **Input**: Dynamic datasets (PO, master records, reports), static reference datasets, schema files
- **Output**: Validation results (reports + structured JSON summary)
- **Format**: Hierarchical dictionary with status and detailed error messages

---

## 7. Simple Workflow
```
Config Validation → StaticCrossDataChecker → PORequiredCriticalValidator → DynamicCrossDataValidator → Results + Reports
```
→ See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_validationOrchestratorWorkflow.md)

**Detailed Steps**:
1. **Initialization**: Load schema + configuration paths
2. **Static Validation**: Verify static datasets (item, resin, machine, mold)
3. **PO Validation**: Check required PO fields and critical constraints
4. **Dynamic Validation**: Run cross-dataset relational checks
5. **Reporting**: Merge all results into consolidated reports (with version control)
6. **Final Result**: Return orchestrator summary with error categories

---

## 8. Directory Structure
```
agents/shared_db/                                    
└── ValidationOrchestrator/                                  
    ├── historical_db/                                       
    ├── newest/                                              
    |    └── YYYYMMDD_HHMM_validation_orchestrator.xlsx 
    └── change_log.txt                                       
```

---

## 9. Dependencies
- `StaticCrossDataChecker`: Validates static reference datasets
- `PORequiredCriticalValidator`: Ensures required PO fields are filled and consistent
- `DynamicCrossDataValidator`: Validates relational consistency across dynamic datasets
- `loguru`: Structured logging with contextual information

---

## 10. How to Run
### 10.1 Basic Usage

```python
# Initialize orchestrator
orchestrator = ValidationOrchestrator()

# Run validation
result = orchestrator.run_validation()

# Inspect results
print(f"Validation status: {result['overall_status']}")
print(f"Completed at: {result['timestamp']}")
```

### 10.2 Custom Configuration

```python
orchestrator = ValidationOrchestrator(
    dynamic_db_source_dir="custom/source/path",
    schema_path="custom/validationSchemas.json",
    default_dir="custom/output"
)

result = orchestrator.run_validation(
    enable_notifications=True
)
```

---

## 11. Development/Testing Mode

```python
# Debug mode with verbose logging
import logging
logging.getLogger("ValidationOrchestrator").setLevel(logging.DEBUG)

# Run test validation
orchestrator = ValidationOrchestrator()
result = orchestrator.run_validation()
```

---

## 12. Result Structure
```json
{
    "overall_status": "success|partial_success|failed",
    "static_result": {
        "status": "success|error",
        "issues": ["missing_mold_record", "invalid_resin_id"],
        "execution_time": "00:00:45"
    },
    "po_result": {
        "status": "success|error",
        "missing_fields": ["customer_code", "delivery_date"],
        "execution_time": "00:01:30"
    },
    "dynamic_result": {
        "status": "success|error",
        "violations": ["orphan_product_entry"],
        "execution_time": "00:04:00"
    },
    "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## 13. Configuration Paths
- **dynamic_db_source_dir**: `database/dynamicDatabase` (raw dynamic datasets)
- **schema_path**: `database/validationSchemas.json` (database schema definitions)
- **default_dir**: `agents/shared_db` (base output directory)
- **output_dir**: `agents/shared_db/ValidationOrchestrator` (validation reports & logs)