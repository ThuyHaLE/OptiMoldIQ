# DataPipelineOrchestrator Agent Documentation

## Overview

The **DataPipelineOrchestrator** is the main coordinator agent responsible for managing a comprehensive two-phase data pipeline process. It orchestrates data collection, processing, loading operations, and provides robust error handling with automated recovery mechanisms and notification systems.

## Architecture

### Core Components

1. **DataPipelineOrchestrator** - Main orchestrator class
2. **MockNotificationHandler** - Notification system for testing
3. **ManualReviewNotifier** - Handles manual review notifications
4. **DataCollector** - Phase 1: Data collection agent
5. **DataLoaderAgent** - Phase 2: Data processing and loading agent

### Two-Phase Pipeline Design

```
Phase 1: Data Collection → Phase 2: Data Loading
     ↓                           ↓
Error Handling ←→ Rollback ←→ Notifications
```

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

- See details: [Workflow](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/workflows/OptiMoldIQ_dataPipelineOrchestratorWorkflow.md)
  
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

Executes Phase 1: `DataCollector` to gather raw data from sources.

**Process:**
1. Initialize DataCollector with source directory
2. Process all available data sources
3. Handle collection errors
4. Trigger notifications on failure

- See details: [DataCollector](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataCollector_review.md)

##### `_run_data_loader(collector_result: Any) -> Any`

Executes Phase 2: `DataLoaderAgent` to process and load collected data.
  
**Conditional Logic:**
- Proceeds if Phase 1 was successful
- Proceeds if Phase 1 failed but rollback was successful  
- Skips if Phase 1 failed without successful rollback

- See details: [DataLoader](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataLoader_review.md)

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

## Error Handling & Recovery

### Error Handling Strategy

The orchestrator implements a multi-layered error handling approach:

1. **Try-Catch Blocks**: Wrap each phase execution
2. **Status Checking**: Evaluate phase results
3. **Rollback Detection**: Check for successful recovery actions
4. **Notification System**: Alert administrators of failures

### Recovery Mechanisms

#### Rollback Detection
The system checks for successful `ROLLBACK_TO_BACKUP` actions in:
- Healing actions from the execution info
- Recovery actions within detail records

#### Decision Matrix
| Phase 1 Status | Rollback Status | Phase 2 Action |
|---------------|----------------|----------------|
| Success | N/A | Proceed |
| Failed | Success | Proceed |
| Failed | Failed/None | Skip |

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

## Configuration

### Directory Structure

```
project_root/
├── database/
│   ├── dynamicDatabase/          # Source data directory
│   └── databaseSchemas.json      # Database schemas
├── agents/
│   └── shared_db/
│       ├── DataLoaderAgent/
│       │   └── newest/
│       │       └── path_annotations.json
│       └── DataPipelineOrchestrator/  # Output directory
└── configs/
    └── recovery/
        └── dataPipelineOrchestrator/
            └── data_pipeline_orchestrator_configs.py
```

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

## Security Considerations

### Data Protection
- Secure handling of sensitive data in notifications
- Proper file permissions for output directories
- Sanitize error messages in notifications

### Access Control
- Implement proper authentication for notification recipients
- Secure configuration file access
- Monitor pipeline execution logs