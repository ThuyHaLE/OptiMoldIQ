# DataLoader

## 1. Overview

The `DataLoader` is responsible for loading, processing, and managing database files within the data pipeline. It supports:
- Static databases (Excel files)
- Dynamic databases (Parquet files)
- Change detection between versions
- File versioning and historical backups
- Error handling with recovery mechanisms
- Triggering downstream agents after updates

This agent is part of the data pipeline orchestrator and integrates with the healing system for automated recovery.

### Key Features

- **Database Processing**
  - Handles multiple database types (static/dynamic)
  - Validates schema consistency
  - Detects data changes using hash-based comparison
- **Version Control**
  - Saves updated files with timestamp-based versioning
  - Moves old files to a historical directory
  - Maintains annotation mapping for file paths
- **Error Handling & Recovery**
  - Supports rollback and recovery actions
  - Captures error metadata (e.g., file not found, read errors, schema mismatches)
  - Provides healing actions and trigger agents for orchestration
**Monitoring & Logging**
  - Tracks memory and disk usage
  - Maintains change logs
  - Provides execution summaries

---

## 2. Class: `DataLoader`

### 2.1 Constructor

```python
DataLoaderAgent(
    databaseSchemas_path: str = "database/databaseSchemas.json",
    annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
    default_dir: str = "agents/shared_db"
)
```

**Parameters:**
- `databaseSchemas_path`: Path to database schema configuration
- `annotation_path`: Path to file storing database path annotations
- `default_dir`: Default directory for shared database files

### 2.1 Primary Methods

#### `process_all_data() -> Dict[str, Any]`

Main processing method that orchestrates the entire data loading pipeline.

**Returns:**
```python
{
    "agent_id": str,
    "status": str,  # SUCCESS, ERROR, WARNING, PARTIAL_SUCCESS
    "summary": {
        "total_databases": int,
        "successful": int,
        "failed": int,
        "warnings": int,
        "changed_files": int,
        "files_saved": int
    },
    "details": List[Dict],  # Individual database processing results
    "healing_actions": List[str],  # Recovery actions to execute
    "trigger_agents": List[str],  # Downstream agents to trigger
    "metadata": {
        "processing_duration_seconds": float,
        "memory_usage": Dict,
        "disk_usage": Dict
    }
}
```

---

## 3. Configuration

### 3.1 Database Schema Structure

```json
{
    "staticDB": {
        "database_name": {
            "path": "path/to/excel/file.xlsx",
            "dtypes": {
                "column1": "str",
                "column2": "int64",
                "column3": "float64"
            }
        }
    },
    "dynamicDB": {
        "database_name": {
            "path": "path/to/parquet/file.parquet"
        }
    }
}
```

### 3.2 Path Annotations Structure

```json
{
    "database_name1": "/full/path/to/saved/file1.parquet",
    "database_name2": "/full/path/to/saved/file2.parquet"
}
```

---

## 4. Error Handling

### 4.1 Error Types

| Error Type | Description | Recovery Actions |
|------------|-------------|------------------|
| `FILE_NOT_FOUND` | Database file doesn't exist | Rollback to backup, Manual review |
| `FILE_READ_ERROR` | Cannot read database file | Retry processing, Check permissions |
| `SCHEMA_MISMATCH` | Data doesn't match expected schema | Validate schema, Manual intervention |
| `DATA_CORRUPTION` | Data integrity issues detected | Rollback to backup, Data validation |
| `HASH_COMPARISON_ERROR` | Change detection failure | Retry comparison, Manual review |
| `PARQUET_SAVE_ERROR` | Cannot save processed data | Check disk space, Retry save |

### 4.2 Processing Status

- **SUCCESS**: All operations completed successfully
- **WARNING**: Minor issues detected but processing continued
- **ERROR**: Critical failure preventing completion
- **PARTIAL_SUCCESS**: Some databases processed successfully, others failed

---

## 5. File Management

### 5.1 Directory Structure

```
agents/shared_db/DataLoaderAgent/
├── historical_db/
├── newest/
│   ├── 20241201_1430_database1.parquet
│   ├── 20241201_1430_database2.parquet
│   └── path_annotations.json
└── change_log.txt
```

### 5.2 Versioning System

Files are saved with timestamp prefixes in the format: `YYYYMMDD_HHMM_databasename.parquet`

- **newest/**: Contains current versions of all databases
- **historical_db/**: Archives previous versions when new data is detected
- **change_log.txt**: Audit trail of all file operations

---

## 6. Usage Examples

### 6.1 Basic Usage

```python
from data_loader_agent import DataLoaderAgent

# Initialize agent
agent = DataLoaderAgent()

# Process all configured databases
result = agent.process_all_data()

# Check results
if result['status'] == 'SUCCESS':
    print(f"Successfully processed {result['summary']['successful']} databases")
    if result['summary']['changed_files'] > 0:
        print(f"Detected changes in {result['summary']['changed_files']} files")
else:
    print(f"Processing failed: {result['status']}")
    for action in result['healing_actions']:
        print(f"Recovery action needed: {action}")
```

### 6.2 Custom Configuration

```python
# Initialize with custom paths
agent = DataLoaderAgent(
    databaseSchemas_path="config/my_schemas.json",
    annotation_path="data/annotations.json",
    default_dir="output/processed"
)

result = agent.process_all_data()
```

---

## 7. Integration Guidelines

### 7.1 Downstream Agent Triggering

When data changes are detected, the agent can trigger downstream agents:

```python
# Check which agents should be triggered
if result['trigger_agents']:
    for agent_id in result['trigger_agents']:
        # Trigger downstream agent
        trigger_agent(agent_id)
```

### 7.2 Error Recovery Integration

```python
# Handle recovery actions
for action in result['healing_actions']:
    if action == 'ROLLBACK_TO_BACKUP':
        # Implement rollback logic
        rollback_database()
    elif action == 'TRIGGER_MANUAL_REVIEW':
        # Notify administrators
        send_alert_to_admins()
```