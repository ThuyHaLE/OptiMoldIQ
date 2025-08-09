# Shared Database Building Workflow

## Overview

The *Shared Database Building* is the first stage of the **OptiMoldIQ** system, responsible for processing raw Excel data into a standardized shared database for use by other agents. The workflow consists of three orchestrators executed sequentially:

```
Raw Excel Data → dataPipelineOrchestrator → validationOrchestrator → orderProgressTracker → Final Reports
```


---

## Key Components

### 1. `dataPipelineOrchestrator`
**Purpose**: Aggregate and standardize raw data into a shared database (Parquet format)

**Operations**:
- **Phase 1**: Aggregate monthly dynamic database
- **Phase 2**: Standardize from Excel to Parquet format

**Output**:
- 6 Static databases (`.parquet`):  
  `itemInfo`, `moldInfo`, `machineInfo`, `resinInfo`, `itemCompositionSummary`, `moldSpecification`
- 2 Dynamic databases (`.parquet`):  
  `purchaseOrders`, `productRecords`

📋 *Details: [dataPipelineOrchestrator documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/)*

---

### 2. `validationOrchestrator`
**Purpose**: Cross-validate databases to detect mismatches and provide recommendations

**Operations**:
- `StaticCrossDataChecker`: Validates against static reference datasets
- `PORequiredCriticalValidator`: Validates required fields in purchase orders
- `DynamicCrossDataValidator`: Checks consistency among dynamic datasets

**Output**:  
Validation results with detailed warnings (used by `orderProgressTracker`)

📋 *Details: [validationOrchestrator documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/)*

---

### 3. `orderProgressTracker`
**Purpose**: Aggregate production data by purchase order and generate a comprehensive Excel report

**Operations**:
- Real-time production status tracking
- Multi-dimensional analysis by shift, machine, mold, and date
- Automated classification into: `PENDING`, `MOLDING`, `PAUSED`, or `MOLDED`
- ETA compliance monitoring
- Integration of validation warnings
- Excel report generation with multiple worksheets

**Output**:  
`orderProgressTracker.xlsx` with 8 sheets:  
- `productionStatus`  
- `materialComponentMap`  
- `moldShotMap`  
- `machineQuantityMap`  
- `dayQuantityMap`  
- `notWorkingStatus`  
- `item_invalid_warnings`  
- `po_mismatch_warnings`

📋 *Details: [orderProgressTracker documentation](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/)*

---

## Data Flow

### Input
- **Raw Excel files**:
  - Static: product specs, mold info, machine capabilities  
  - Dynamic: purchase orders, shift-level production records

### Processing Steps
1. **Aggregation**: Combine monthly data
2. **Standardization**: Convert Excel → Parquet with unified schema
3. **Validation**: Cross-check consistency across databases
4. **Reporting**: Generate detailed Excel reports by PO

### Output Directory Structure

```
./shared_db/
├── DataLoaderAgent/
|   ├── historical_db/*.parquet
|   ├── newest/*.parquet           # 8 configuration databases 
|   |   └── path_annotations.json  # paths of 8 configuration databases
|   └── change_log.txt
├── dynamicDatabase/
|   ├── productRecords.parquet
|   └── purchaseOrders.parquet
├── OrderProgressTracker/
|   ├── historical_db/ *.parquet
|   ├── newest/
|   |   └── auto_status.xlsx
|   └── change_log.txt
├── ValidationOrchestrator /
|   ├── historical_db/ *.parquet
|   ├── newest/
|   |   └── validation_orchestrator.xlsx
|   └── change_log.txt
```

---

## Workflow Diagrams

📊 **Detailed workflows**:
- [dataPipelineOrchestrator Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_dataPipelineOrchestratorWorkflow.md)  
- [validationOrchestrator Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_validationOrchestratorWorkflow.md)  
- [orderProgressTracker Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_orderProgressTrackerWorkflow.md)

---

## Trigger Mechanism

### Trigger Logic

Phases are triggered **only when data updates are detected**:

```python
# 1. Run DataPipelineOrchestrator
data_pipeline_report = DataPipelineOrchestrator(...).run_pipeline()

# 2. Detect update
def detect_updates(data_pipeline_report):
    trigger = False
    updated_db_details = []
    for db in data_pipeline_report['collector_result'].details:
        if db['data_updated']:
            updated_db_details.append(db['data_type'])
    for db in data_pipeline_report['loader_result'].details[:-1]:
        if db['data_updated']:
            updated_db_details.append(db['database_name'])
    if len(updated_db_details) > 0:
        trigger = True
    return trigger

# 3. Trigger downstream processes
if detect_updates(data_pipeline_report):
    ValidationOrchestrator(...).run_validations_and_save_results()
    OrderProgressTracker(...).pro_status()
```

### Execution Flow
1. **DataPipelineOrchestrator** runs first and returns update report
2. If data changes detected → trigger next phases
3. **Sequential execution**: validationOrchestrator → orderProgressTracker

This logic ensures optimal performance by running only when needed.

## Key Benefits

- **Data Quality**: Cross-validated inputs ensure trustable datasets
- **Standardization**: Unifies schema for downstream agents
- **Visibility**: Tracks production progress per PO
- **Insights**: Includes actionable warnings
- **Efficiency**: Trigger-based execution avoids redundant processing

---

## Optional: Dashboard Report Processing

After generating `orderProgressTracker.xlsx`, an optional post-processing step can be triggered to prepare summarized reports optimized for dashboards or visualizations.

### Module
```python
from agents.orderProgressTracker.process_dashboard_reports import ProcessDashboardReports

processor = ProcessDashboardReports(
    excel_file_path=None,
    folder_path=f"{shared_db_dir}/OrderProgressTracker",
    target_name="change_log.txt",
    limit_range=(0, 2)  # Use (None, None) to process all logs
)

# Generate all reports at once
all_reports = processor.generate_all_reports()

for report_name, report_content in all_reports.items():
    print(f"Report name: {report_name}")
    print(f"Report content:\n{report_content}")
    print("-" * 80)
```
📋 *Details: [processDashboardReports Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_processDashboardReports_overview.md)  
  
### Output
- A dictionary of key-value pairs where:
  - Key = report name
  - Value = report content (as a DataFrame or table)
- Dashboard-ready insights include:
  - Purchase order progress summaries
  - Delay tracking and ETA compliance
  - Machine downtime or inactive periods
  - Mold performance breakdowns

### Use Cases
- Feeding into front-end dashboards (e.g., Streamlit, React, Superset)
- Embedding into management reports
- Periodic data monitoring

This module enhances the usability of orderProgressTracker outputs by summarizing complex Excel data into structured insights.