# DataPipelineOrchestrator

## 1. Overview

The **DataPipelineOrchestrator** is the main coordinator agent responsible for managing a comprehensive two-phase data pipeline process. It orchestrates data collection, processing, loading operations, and provides robust error handling with automated recovery mechanisms and notification systems.

---

## 2. Architecture

### 2.1 Core Components

1. **DataPipelineOrchestrator** -- Main orchestrator class
2. **DataCollector** -- Phase 1 agent: data collection and normalization
3. **DataLoaderAgent** -- Phase 2 agent: data loading and version management
4. **ManualReviewNotifier** -- Notification handler for manual review
5. **MockNotificationHandler** -- Mock system for testing notifications

### 2.2 Two-Phase Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             [ DataPipelineOrchestrator ]                                        │
│                    Orchestrates the entire batch data processing flow                           │
└───────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                ┌───────────────────────────┴─────────────────────────────────────────┐
                ▼ Phase 1                                                             ▼                 
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │   DataCollector      │                                            │   DataLoaderAgent    │
        │ (Process Dynamic DB) │────── Phase 2 ───────────────────────────⯈│ (Load All Databases) │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Process Excel Reports                                           🔍 Check Database Changes
    • Read .xlsb/.xlsx files                                            • Compare with schema
    • Merge & validate data                                             • Compare with annotations  
    • Compare hash with existing                                        • Save new versions if changed
    • Save as .parquet if changed                                       • Update path_annotations.json
```

### 2.3 Detailed Phase Breakdown

#### 🔄 Phase 1: DataCollector (Dynamic Database Processing)

  ------------------------------------------------------------------------
  Step         Process                                  Details
  ------------ ---------------------------------------- ------------------
  1            Read Source Files                        Process
                                                        `.xlsb`/`.xlsx`
                                                        from history
                                                        folders

  2            Data Normalization                       Normalize dates,
                                                        resin codes,
                                                        missing columns

  3            Data Cleaning                            Remove duplicates,
                                                        validate integrity

  4            Change Detection                         Hash comparison
                                                        against existing
                                                        parquet

  5            File Generation                          Save `.parquet`
                                                        with snappy
                                                        compression
  ------------------------------------------------------------------------

**Success Criteria:** Hash detects new data, `.parquet` saved.\
**Failure Modes:** File not found, corrupted Excel, schema mismatch.

**Input Sources:**
- `monthlyReports_history/` → `.xlsb`/`.xlsx` files
- `purchaseOrders_history/` → `.xlsb`/`.xlsx` files

**Output:**
- `productRecords.parquet`
- `purchaseOrders.parquet`

#### 📋 Phase 2: DataLoaderAgent (All Database Loading)

  --------------------------------------------------------------------------------
  Step        Process                                    Details
  ----------- ------------------------------------------ -------------------------
  1           Schema Loading                             Load
                                                         `databaseSchemas.json`

  2           Annotations Loading                        Load
                                                         `path_annotations.json`

  3           Data Processing                            Load parquet (dynamic) +
                                                         xlsx (static)

  4           Change Detection                           Hash comparison new vs
                                                         old

  5           Version Management                         Save new to `newest/`,
                                                         archive old →
                                                         `historical_db/`
  --------------------------------------------------------------------------------

**Failure Modes:** Schema mismatch, corrupted `.xlsx`, rollback
detection failure.

**Input Sources:**
- Dynamic: `.parquet` files from Phase 1
- Static: `.xlsx` files from configured paths
- Schema: `databaseSchemas.json`
- Annotations: `path_annotations.json`

**Output:**
- Versioned `.parquet` files in `newest/`
- Updated `path_annotations.json`
- Historical files in `historical_db/`

---

## 3. Class DataPipelineOrchestrator

### 3.1 Constructor

```python
DataPipelineOrchestrator(
    dynamic_db_source_dir: str = "database/dynamicDatabase",
    databaseSchemas_path: str = "database/databaseSchemas.json", 
    annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
    default_dir: str = "agents/shared_db"
)
```

**Parameters:**
- `dynamic_db_source_dir`: Directory containing dynamic database source files
- `databaseSchemas_path`: Path to the database schemas JSON file
- `annotation_path`: Path to data annotations file used by DataLoaderAgent
- `default_dir`: Default directory for shared database operations

### 3.2 Key Methods

#### `run_pipeline(**kwargs) -> Dict[str, Any]`

Main entry point that executes the complete data pipeline.

**Process Flow:**
1. Execute Phase 1 (DataCollector)
2. Evaluate Phase 1 results
3. Conditionally execute Phase 2 (DataLoaderAgent)
4. Handle errors and notifications
5. Return comprehensive results

**Returns:**
```python
{
    'overall_status': 'success' | 'partial_success' | 'failed',
    'collector_result': Any,  # Phase 1 results
    'loader_result': Any,     # Phase 2 results
    'timestamp': str          # ISO format timestamp
}
```

**Status Definitions:**
- `success`: Both phases completed successfully
- `partial_success`: Phase 1 failed but Phase 2 succeeded due to rollback
- `failed`: Either phase failed without recovery

#### `_run_data_collector() -> Any`

Executes Phase 1: DataCollector to gather raw data from sources.

**Process:**
1. Initialize DataCollector with source directory
2. Process all available data sources
3. Handle collection errors
4. Trigger notifications on failure

#### `_run_data_loader(collector_result: Any) -> Any`

Executes Phase 2: DataLoaderAgent to process and load collected data.

**Conditional Logic:**
- Proceeds if Phase 1 was successful
- Proceeds if Phase 1 failed but rollback was successful  
- Skips if Phase 1 failed without successful rollback

#### `_should_proceed_to_data_loader(collector_result: Any) -> bool`

Decision logic for Phase 2 execution:

```python
if collector_result.status == 'success':
    return True
elif rollback_successful:
    return True
else:
    return False
```

---

## 4. Error Handling & Recovery

Error Handling Strategy: The orchestrator implements a comprehensive error handling approach with automatic recovery mechanisms:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phase 1       │    │   Phase 2       │    │   Notification  │
│  DataCollector  │    │ DataLoaderAgent │    │    System       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Error Detection │    │ Error Detection │    │ Manual Review   │
│ & Recovery      │    │ & Recovery      │    │ Notification    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ROLLBACK_TO_    │    │ Continue/Skip   │    │ Admin Alert     │
│ BACKUP          │    │ Based on Status │    │ + File Log      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Multi-Layer Error Handling
1. **Try-Catch Blocks**: Wrap each phase execution with exception handling
2. **Status Validation**: Check phase results before proceeding  
3. **Rollback Detection**: Automatic detection of successful recovery actions
4. **Notification System**: Alert administrators for manual intervention
5. **Pipeline Continuation Logic**: Smart decision-making for Phase 2 execution

### Pipeline Continuation Decision Matrix

| Phase 1 Status | Rollback Status | Phase 2 Action | Reasoning |
|----------------|-----------------|-----------------|-----------|
| ✅ **Success** | N/A | ✅ **Proceed** | Normal flow - continue to Phase 2 |
| ❌ **Failed** | ✅ **Success** | ✅ **Proceed** | Recovery successful - safe to continue |
| ❌ **Failed** | ❌ **Failed** | ⏹️ **Skip** | Cannot recover - stop pipeline |
| ❌ **Failed** | ❓ **None** | ⏹️ **Skip** | No recovery attempted - stop pipeline |

### Rollback Mechanism
The system automatically detects successful `ROLLBACK_TO_BACKUP` actions in:
- **Healing Actions**: Primary recovery actions from execution info
- **Recovery Actions**: Detailed recovery attempts within error records

**Detection Process:**
```python
# Pseudo-code for rollback detection
for action in healing_actions:
    if action.type == "ROLLBACK_TO_BACKUP" and action.status == "SUCCESS":
        return True  # Safe to proceed to Phase 2
```

---

## 5. Notification System

### 5.1 MockNotificationHandler

Simulates notification sending for testing purposes.

```python
def send_notification(
    recipient: str, 
    subject: str, 
    message: str, 
    priority: str
) -> bool
```

### 5.2 ManualReviewNotifier

Handles comprehensive manual review notifications.

#### Key Features

1. **Structured Notifications**: Creates detailed notification messages
2. **File Persistence**: Saves notifications to timestamped files
3. **Rollback Verification**: Checks for successful rollback operations
4. **Multi-format Support**: Handles various enum and status formats

#### Notification Structure

```
================================================================================
                    MANUAL REVIEW NOTIFICATION
================================================================================

Agent ID     : [agent_identifier]
Status       : [FAILED/ERROR]
Timestamp    : [iso_timestamp]

------------------------------ SUMMARY ------------------------------
Total Databases     : [count]
Successful          : [count]
Failed              : [count]
Warnings            : [count]
Changed Files       : [count]
Files Saved         : [count]

------------------------- ERROR DETAILS -------------------------
ERROR #1:
  Data Type      : [data_type]
  Error Type     : [error_classification]
  Error Message  : [detailed_error_message]
  
  Recovery Actions:
    1. [PRIORITY] Action_Name at Scale → Status: [SUCCESS/FAILED]

---------------------- HEALING ACTIONS ----------------------
1. [HIGH] ROLLBACK_TO_BACKUP at database → Status: SUCCESS

-------------------------- METADATA --------------------------
Duration (s)        : [execution_time]
Memory Usage (MB)   : [memory_usage] ([percentage]%)
Disk Output (MB)    : [disk_usage]
Disk Free Space (MB): [available_space]
Trigger Agents      : [triggering_agents]

================================================================================
```

---

## 6. Configuration

### 6.1 Directory Structure

```
agents/
├── database/
│   ├── databaseSchemas.json               # Database schema definitions (DataLoader input)    
│   ├── staticDatabase/
│   └── dynamicDatabase/                   # DataCollector input
│       ├── monthlyReports_history/        # Input: Monthly report files
│       └── purchaseOrders_history/        # Input: Purchase order files
├── agents/
│   └── shared_db/
|       ├── dynamicDatabase/               # DataCollector output (.parquet files)
|       |    ├── productRecords.parquet                     
|       |    └── purchaseOrders.parquet        
│       ├── DataLoaderAgent/               # DataLoader output (.parquet files)
│       |   ├── historical_db/                                       
│       |   ├── newest/                                              
│       |   |    ├── ...          
│       |   |    └── path_annotations.json # Version tracking
│       |   └── change_log.txt             # DataLoaderAgent change log
│       └── DataPipelineOrchestrator/      # Orchestrator reports
│           ├── historical_db/                                     
│           ├── newest/                                             
│           |    ├── YYYYMMDD_HHMM_DataCollector_(report_type).txt           
│           |    ├── YYYYMMDD_HHMM_DataLoader_(report_type).txt              
│           |    └── YYYYMMDD_HHMM_DataPipelineOrchestrator_final_report.txt 
│           └── change_log.txt             # Orchestrator change log
└── configs/
    └── recovery/
        └── dataPipelineOrchestrator/
            └── data_pipeline_orchestrator_configs.py
```

### 6.2 Data Flow Overview

| Agent | Input Files | Output Files | Purpose |
|-------|-------------|--------------|---------|
| **DataCollector** | `monthlyReports_*.xlsb/xlsx`<br>`purchaseOrders_*.xlsb/xlsx` | `productRecords.parquet`<br>`purchaseOrders.parquet` | Process and consolidate dynamic data |
| **DataLoaderAgent** | Phase 1 `.parquet` files<br>Static `.xlsx` files<br>`databaseSchemas.json`<br>`path_annotations.json` | Versioned `.parquet` files<br>Updated `path_annotations.json` | Load and version all databases |

---

## 7. Usage Examples

```python
# Basic usage
orchestrator = DataPipelineOrchestrator()
result = orchestrator.run_pipeline()
if result['overall_status'] == 'success':
    print("Pipeline OK")
elif result['overall_status'] == 'partial_success':
    print("Collector failed but rollback succeeded")
else:
    print("Pipeline failed")
```

```python
# Custom paths
orchestrator = DataPipelineOrchestrator(
    dynamic_db_source_dir="custom/data",
    databaseSchemas_path="custom/schemas.json",
    annotation_path="custom/annotations.json",
    default_dir="custom/shared"
)
result = orchestrator.run_pipeline()
```