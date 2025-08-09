# DataPipelineOrchestrator Workflow Documentation

## Overview

The **DataPipelineOrchestrator** is the main coordinator agent responsible for managing a comprehensive two-phase data pipeline process. It orchestrates data collection, processing, loading operations, and provides robust error handling with automated recovery mechanisms and notification systems.

---

## Architecture

### Core Components

1. **DataPipelineOrchestrator** - Main orchestrator class
2. **MockNotificationHandler** - Notification system for testing
3. **ManualReviewNotifier** - Handles manual review notifications
4. **DataCollector** - Phase 1: Data collection agent
5. **DataLoaderAgent** - Phase 2: Data processing and loading agent

### Two-Phase Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             [ DataPipelineOrchestrator ]                                        │
│                    Orchestrates the entire batch data processing flow                           │
└──────────────┬──────────────────────────────────────────────────────────────────────────────────┘
               ▼ Phase 1                                                           
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │   DataCollector      │                                            │   DataLoaderAgent    │
        │ (Process Dynamic DB) │────── Phase 2 ───────────────────────────⯈│ (Load All Databases) │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Process Excel Reports                                           🔍 Check Database Changes
    • Read .xlsb/.xlsx files                                          • Compare with schema
    • Merge & validate data                                           • Compare with annotations  
    • Compare hash with existing                                      • Save new versions if changed
    • Save as .parquet if changed                                     • Update path_annotations.json
```

### Detailed Phase Breakdown

#### 🔄 Phase 1: DataCollector (Dynamic Database Processing)

| Step | Process | Details |
|------|---------|---------|
| **1** | **Read Source Files** | Process `monthlyReports_history` and `purchaseOrders_history` folders |
| **2** | **Data Normalization** | Handle missing columns, normalize dates, shifts, resin codes |
| **3** | **Data Cleaning** | Remove duplicates and validate data integrity |
| **4** | **Change Detection** | Compare new data with existing `.parquet` using hash comparison |
| **5** | **File Generation** | Save new `.parquet` files using atomic write + snappy compression |

**Input Sources:**
- `monthlyReports_history/` → `.xlsb`/`.xlsx` files
- `purchaseOrders_history/` → `.xlsb`/`.xlsx` files

**Output:**
- `productRecords.parquet`
- `purchaseOrders.parquet`

#### 📋 Phase 2: DataLoaderAgent (All Database Loading)

| Step | Process | Details |
|------|---------|---------|
| **1** | **Schema Loading** | Load `databaseSchemas.json` for schema definitions |
| **2** | **Annotations Loading** | Load `path_annotations.json` for version references |
| **3** | **Data Processing** | For each database:<br>• **Dynamic DB**: Load `.parquet` from Phase 1<br>• **Static DB**: Load `.xlsx` from configured paths |
| **4** | **Change Detection** | Compare new vs old content using hash comparison |
| **5** | **Version Management** | If different:<br>• Move old → `historical_db/`<br>• Save new → `newest/` with timestamp<br>• Update `path_annotations.json` |

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

## Class Reference

### DataPipelineOrchestrator

The main orchestrator class that coordinates the entire data pipeline process.

#### Constructor

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

#### Key Methods

##### `run_pipeline(**kwargs) -> Dict[str, Any]`

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

##### `_run_data_collector() -> Any`

Executes Phase 1: DataCollector to gather raw data from sources.

**Process:**
1. Initialize DataCollector with source directory
2. Process all available data sources
3. Handle collection errors
4. Trigger notifications on failure

##### `_run_data_loader(collector_result: Any) -> Any`

Executes Phase 2: DataLoaderAgent to process and load collected data.

**Conditional Logic:**
- Proceeds if Phase 1 was successful
- Proceeds if Phase 1 failed but rollback was successful  
- Skips if Phase 1 failed without successful rollback

##### `_should_proceed_to_data_loader(collector_result: Any) -> bool`

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

## Error Handling & Recovery

### Error Handling Strategy

The orchestrator implements a comprehensive error handling approach with automatic recovery mechanisms:

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

#### Multi-Layer Error Handling
1. **Try-Catch Blocks**: Wrap each phase execution with exception handling
2. **Status Validation**: Check phase results before proceeding  
3. **Rollback Detection**: Automatic detection of successful recovery actions
4. **Notification System**: Alert administrators for manual intervention
5. **Pipeline Continuation Logic**: Smart decision-making for Phase 2 execution

#### Pipeline Continuation Decision Matrix

| Phase 1 Status | Rollback Status | Phase 2 Action | Reasoning |
|----------------|-----------------|-----------------|-----------|
| ✅ **Success** | N/A | ✅ **Proceed** | Normal flow - continue to Phase 2 |
| ❌ **Failed** | ✅ **Success** | ✅ **Proceed** | Recovery successful - safe to continue |
| ❌ **Failed** | ❌ **Failed** | ⏹️ **Skip** | Cannot recover - stop pipeline |
| ❌ **Failed** | ❓ **None** | ⏹️ **Skip** | No recovery attempted - stop pipeline |

#### Rollback Mechanism
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

## Notification System

### MockNotificationHandler

Simulates notification sending for testing purposes.

```python
def send_notification(
    recipient: str, 
    subject: str, 
    message: str, 
    priority: str
) -> bool
```

### ManualReviewNotifier

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

## Configuration

### Directory Structure

```
project_root/
├── database/
│   ├── dynamicDatabase/                    # Phase 1 output (.parquet files)
│   ├── databaseSchemas.json               # Database schema definitions
│   ├── monthlyReports_history/            # Input: Monthly report files
│   └── purchaseOrders_history/            # Input: Purchase order files
├── agents/
│   └── shared_db/
│       ├── DataLoaderAgent/
│       │   ├── newest/                    # Latest database versions
│       │   │   └── path_annotations.json  # Version tracking
│       │   └── historical_db/             # Previous database versions
│       └── DataPipelineOrchestrator/      # Orchestrator output
└── configs/
    └── recovery/
        └── dataPipelineOrchestrator/
            └── data_pipeline_orchestrator_configs.py
```

### Data Flow Overview

| Agent | Input Files | Output Files | Purpose |
|-------|-------------|--------------|---------|
| **DataCollector** | `monthlyReports_*.xlsb/xlsx`<br>`purchaseOrders_*.xlsb/xlsx` | `productRecords.parquet`<br>`purchaseOrders.parquet` | Process and consolidate dynamic data |
| **DataLoaderAgent** | Phase 1 `.parquet` files<br>Static `.xlsx` files<br>`databaseSchemas.json`<br>`path_annotations.json` | Versioned `.parquet` files<br>Updated `path_annotations.json` | Load and version all databases |

### Dependencies

```python
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datetime import datetime
from dataclasses import dataclass

# Internal dependencies
from agents.dataPipelineOrchestrator.data_collector import DataCollector
from agents.dataPipelineOrchestrator.data_loader import DataLoaderAgent
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import AgentExecutionInfo
```

---

## Usage Examples

### Basic Usage

```python
# Initialize orchestrator with default settings
orchestrator = DataPipelineOrchestrator()

# Run the complete pipeline
result = orchestrator.run_pipeline()

# Check results
if result['overall_status'] == 'success':
    print("Pipeline completed successfully")
elif result['overall_status'] == 'partial_success':
    print("Pipeline completed with collector failure but successful recovery")
else:
    print("Pipeline failed")
```

### Custom Configuration

```python
# Initialize with custom paths
orchestrator = DataPipelineOrchestrator(
    dynamic_db_source_dir="custom/data/sources",
    databaseSchemas_path="custom/schemas.json",
    annotation_path="custom/annotations.json",
    default_dir="custom/shared"
)

# Run with additional parameters
result = orchestrator.run_pipeline(
    custom_param="value",
    retry_count=3
)
```

### Error Handling

```python
try:
    orchestrator = DataPipelineOrchestrator()
    result = orchestrator.run_pipeline()
    
    # Handle different result statuses
    match result['overall_status']:
        case 'success':
            handle_success(result)
        case 'partial_success':
            handle_partial_success(result)
        case 'failed':
            handle_failure(result)
            
except Exception as e:
    logger.error(f"Orchestrator initialization failed: {e}")
```

---

## Logging

The orchestrator uses structured logging with the `loguru` library:

```python
# Class-specific logger binding
self.logger = logger.bind(class_="DataPipelineOrchestrator")

# Emoji-enhanced log messages for better visibility
self.logger.info("🚀 Starting DataPipelineOrchestrator...")
self.logger.info("✅ Phase 1: DataCollector completed successfully")
self.logger.warning("⚠️ Phase 2: DataLoaderAgent failed")
self.logger.error("❌ Phase 1: DataCollector error")
```

---

## Best Practices

### 1. Error Resilience
- Always check phase results before proceeding
- Implement proper rollback detection
- Use structured error result objects

### 2. Monitoring
- Enable comprehensive logging
- Set up notification handlers for production
- Monitor file system usage and permissions

### 3. Configuration Management
- Use environment-specific configuration files
- Validate paths and permissions during initialization
- Implement configuration validation

### 4. Testing
- Use MockNotificationHandler for testing
- Test both success and failure scenarios
- Verify rollback detection logic

---

## Troubleshooting

### Common Issues

1. **Path Configuration Errors**
   - Verify all directory paths exist
   - Check file permissions
   - Validate JSON schema files

2. **Phase Execution Failures**
   - Check DataCollector and DataLoaderAgent logs
   - Verify data source availability
   - Monitor system resources

3. **Notification Issues**
   - Verify notification handler configuration
   - Check output directory permissions
   - Monitor notification delivery

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or with loguru
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

---

## Performance Considerations

### Resource Management
- Monitor memory usage during large data processing
- Implement data chunking for large datasets
- Clean up temporary files after processing

### Scalability
- Consider parallel processing for independent data sources
- Implement connection pooling for database operations
- Use asynchronous operations where appropriate

### Monitoring Metrics
- Pipeline execution duration
- Memory and disk usage
- Success/failure rates
- Rollback frequency

---

## Security Considerations

### Data Protection
- Secure handling of sensitive data in notifications
- Proper file permissions for output directories
- Sanitize error messages in notifications

### Access Control
- Implement proper authentication for notification recipients
- Secure configuration file access
- Monitor pipeline execution logs