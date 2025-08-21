# DataPipelineOrchestrator

## Agent Info
- **Name**: DataPipelineOrchestrator
- **Purpose**: 
  - Manage a comprehensive two-phase data pipeline process (collect → load)
  - Provide robust error handling with automated recovery mechanisms and notification systems
- **Owner**: 
- **Status**: Active
- **Location**: `agents/dataPipelineOrchestrator/`

---

## What it does
The `DataPipelineOrchestrator` manages a complete data pipeline consisting of two sequential phases: collecting raw data from various sources ([DataCollector](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataCollector_review.md)), then processing and loading it into target systems ([DataLoader](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataLoader_review.md)). It includes intelligent rollback mechanisms and notification systems for comprehensive error handling.

---

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DataCollector │ -> │ DataPipeline     │ -> │ DataLoaderAgent │
│   (Phase 1)     │    │ Orchestrator     │    │   (Phase 2)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ Raw Data    │        │ Error       │        │ Processed   │
   │ Sources     │        │ Handling &  │        │ Data &      │
   │ (.xlsx/.xlsb)│       │ Notifications│       │ Reports     │
   └─────────────┘        └─────────────┘        └─────────────┘
```

---

## Directory Structure

```
agents/
├── database/
│   ├── databaseSchemas.json                                     # Schema definitions (Data Loader input)
│   ├── staticDatabase/
│   └── dynamicDatabase/                                         # Raw data sources (Data Collector input)
│       ├── monthlyReports_history/                              # Product records source
│       │   └── monthlyReports_YYYYMM.xlsb
│       └── purchaseOrders_history/                              # Purchase orders source
│           └── purchaseOrder_YYYYMM.xlsx
└── shared_db/
    ├── dynamicDatabase/                                         # Phase 1 outputs
    |    ├── productRecords.parquet                              # Processed product records
    |    └── purchaseOrders.parquet                              # Processed purchase orders
    ├── DataLoaderAgent/                                         # Phase 2 outputs
    |   ├── historical_db/                                       # Archived previous versions
    |   ├── newest/                                              # Current processed data
    |   |    ├── YYYYMMDD_HHMM_itemCompositionSummary.parquet   
    |   |    ├── YYYYMMDD_HHMM_itemInfo.parquet                 
    |   |    ├── YYYYMMDD_HHMM_machineInfo.parquet              
    |   |    ├── YYYYMMDD_HHMM_moldInfo.parquet                 
    |   |    ├── YYYYMMDD_HHMM_moldSpecificationSummary.parquet 
    |   |    ├── YYYYMMDD_HHMM_productRecords.parquet           
    |   |    ├── YYYYMMDD_HHMM_purchaseOrders.parquet           
    |   |    ├── YYYYMMDD_HHMM_resinInfo.parquet                
    |   |    └── path_annotations.json                           # File path annotations
    |   └── change_log.txt                                       # Change tracking log
    └── DataPipelineOrchestrator/                                # Orchestrator outputs & reports
        ├── historical_db/                                       # Archived reports
        ├── newest/                                              # Current execution reports
        |    ├── YYYYMMDD_HHMM_DataCollector_(report_type).txt           
        |    ├── YYYYMMDD_HHMM_DataLoader_(report_type).txt              
        |    └── YYYYMMDD_HHMM_DataPipelineOrchestrator_final_report.txt 
        └── change_log.txt                                       # Orchestrator change log
```

---

## Pre-requisites Checklist
Before running the pipeline, ensure:

- [ ] **Source directory exists**: `database/dynamicDatabase/`
- [ ] **Source data available**: Monthly reports (.xlsb) and purchase orders (.xlsx)
- [ ] **Schema file accessible**: `database/databaseSchemas.json` 
- [ ] **Write permissions**: Full access to `agents/shared_db/`
- [ ] **Python dependencies**: loguru, pathlib, pandas, pyarrow
- [ ] **Disk space**: At least 2x input data size available

---

## Error Handling Scenarios

| Scenario | Phase 1 Status | Rollback | Phase 2 | Final Status | Action Required |
|----------|----------------|----------|---------|--------------|-----------------|
| Happy Path | ✅ Success | N/A | ✅ Success | `success` | None |
| Collector Fail + Rollback OK | ❌ Failed | ✅ Success | ✅ Success | `partial_success` | Monitor logs |
| Collector Fail + Rollback Fail | ❌ Failed | ❌ Failed | ⏹️ Skipped | `failed` | Manual intervention |
| Collector OK + Loader Fail | ✅ Success | N/A | ❌ Failed | `failed` | Check data quality |
| Both Phases Fail | ❌ Failed | ❌ Failed | ❌ Failed | `failed` | Full system check |

---

## Input & Output
- **Input**: Configuration paths, raw data files (Excel formats)
- **Output**: Pipeline execution results with comprehensive status reporting
- **Format**: Python dictionary with hierarchical status information

---

## Simple Workflow
```
Config Validation → Phase 1 (DataCollector) → Error Check & Recovery → Phase 2 (DataLoaderAgent) → Results + Notifications + Reports
```
- See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_dataPipelineOrchestratorWorkflow.md)

**Detailed Steps:**
1. **Initialization**: Load configuration and validate all paths
2. **Phase 1**: Run DataCollector to process raw Excel files into Parquet format
3. **Error Handling**: If Phase 1 fails, attempt rollback and send notifications
4. **Phase 2**: Run DataLoaderAgent (only if Phase 1 succeeds OR rollback succeeds)
5. **Reporting**: Generate comprehensive execution reports and archive previous versions
6. **Final Result**: Create pipeline summary with overall status and detailed phase information

---

## Dependencies
- **DataCollector**: Processes raw data from `database/dynamicDatabase`
- **DataLoaderAgent**: Loads processed data using schemas and annotations
- **ManualReviewNotifier**: Sends notifications for manual intervention requirements
- **MockNotificationHandler**: Development/testing notification system
- **loguru**: Structured logging with contextual information

---

## Performance Notes

### Typical Processing Times
- **Phase 1 (DataCollector)**: 2-5 minutes (depends on file sizes)
- **Phase 2 (DataLoaderAgent)**: 5-10 minutes (depends on data complexity)
- **Total Pipeline**: 7-15 minutes end-to-end
- **Report Generation**: < 30 seconds

### Resource Requirements
- **Memory**: ~500MB peak usage during processing
- **Disk**: 2x input data size (for intermediate and backup files)
- **CPU**: Single-threaded processing (optimization opportunity)
- **Network**: Minimal (local file operations only)

---

## How to Run

### Basic Usage
```python
# Initialize with default configuration
orchestrator = DataPipelineOrchestrator()

# Run complete pipeline
result = orchestrator.run_pipeline()

# Check execution status
print(f"Pipeline status: {result['overall_status']}")
print(f"Completed at: {result['timestamp']}")
```

### Custom Configuration
```python
# Initialize with custom paths
orchestrator = DataPipelineOrchestrator(
    dynamic_db_source_dir="custom/source/path",
    databaseSchemas_path="custom/schemas.json",
    annotation_path="custom/annotations.json",
    default_dir="custom/output"
)

# Run with additional parameters
result = orchestrator.run_pipeline(
    max_retries=3,
    enable_notifications=True
)
```

### Development/Testing Mode
```python
# Debug mode with verbose logging
import logging
logging.getLogger("DataPipelineOrchestrator").setLevel(logging.DEBUG)

# Mock notifications for testing
orchestrator = DataPipelineOrchestrator()
orchestrator.notification_handler = MockNotificationHandler()

# Test run
result = orchestrator.run_pipeline()
```

---

## Result Structure
```python
{
    "overall_status": "success|partial_success|failed",
    "collector_result": {
        "status": "success|error",
        "component": "DataCollector",
        "files_processed": 12,
        "records_count": 45000,
        "execution_time": "00:03:24",
        "healing_actions": [...]  # If any rollback actions taken
    },
    "loader_result": {
        "status": "success|error", 
        "component": "DataLoaderAgent",
        "tables_created": 8,
        "data_validation": "passed|failed",
        "execution_time": "00:07:45"
    },
    "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## Configuration Paths
- **dynamic_db_source_dir**: `database/dynamicDatabase` (raw Excel files)
- **databaseSchemas_path**: `database/databaseSchemas.json` (database schema definitions)
- **annotation_path**: `agents/shared_db/DataLoaderAgent/newest/path_annotations.json` (file mapping)
- **default_dir**: `agents/shared_db` (base output directory)
- **output_dir**: `agents/shared_db/DataPipelineOrchestrator` (reports and logs)

---

## Common Issues & Solutions

| Problem | Symptoms | Quick Fix | Prevention |
|---------|----------|-----------|------------|
| Phase 1 fails | Excel files not processed | Check file permissions & format | Validate source files regularly |
| Phase 2 skipped | Only Phase 1 runs | Verify rollback status in logs | Monitor rollback success rates |
| Notification fails | No alerts received | Check MockNotificationHandler config | Test notification system regularly |
| Path not found | FileNotFoundError in logs | Verify all config paths exist | Use absolute paths in production |
| Memory errors | Process killed/crashes | Reduce batch size or add memory | Monitor resource usage |
| Disk full | Write operations fail | Clean old files from historical_db | Implement automated cleanup |

---

## Monitoring & Observability

### Log Levels & Indicators
- **🚀 INFO**: Pipeline startup and major milestones
- **📊 INFO**: Phase transitions and progress updates
- **✅ INFO**: Successful completions
- **⚠️ WARNING**: Recoverable issues and rollbacks
- **❌ ERROR**: Critical failures requiring intervention
- **🔄 INFO**: Rollback operations
- **📧 INFO**: Notification sending

### Key Metrics to Track
- **Pipeline Success Rate**: Overall success percentage over time
- **Phase Success Rates**: Individual phase performance metrics
- **Rollback Frequency**: How often recovery mechanisms activate
- **Processing Time**: Performance trends and bottlenecks
- **Data Quality**: Record counts and validation results
- **Notification Triggers**: Manual intervention frequency

### Health Checks
```python
# Quick health check
def pipeline_health_check():
    orchestrator = DataPipelineOrchestrator()
    
    # Check all paths exist
    paths_ok = all([
        Path(orchestrator.dynamic_db_source_dir).exists(),
        Path(orchestrator.databaseSchemas_path).exists(),
        Path(orchestrator.annotation_path).exists()
    ])
    
    return {
        "paths_accessible": paths_ok,
        "last_run": get_last_execution_timestamp(),
        "disk_space": get_available_disk_space(),
        "service_status": "healthy" if paths_ok else "degraded"
    }
```