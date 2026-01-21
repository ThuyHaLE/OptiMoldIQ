>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# OptiMoldIQ System Documentation

## 1. Overview

The OptiMoldIQ System is an intelligent orchestration platform designed for manufacturing operations management. It automates daily data pipeline processing, validation, progress tracking, and production planning for mold manufacturing environments.

### Key Features
- **Automated Data Pipeline**: Collects and processes manufacturing data from multiple sources
- **Intelligent Change Detection**: Only processes updates when changes are detected
- **Multi-Agent Coordination**: Orchestrates specialized agents for different manufacturing tasks
- **Comprehensive Reporting**: Generates detailed operational reports with audit trails
- **Configurable Parameters**: Flexible configuration for different manufacturing environments
- **Error Resilience**: Robust error handling and recovery mechanisms

---

## 2. System Architecture

The OptiMoldIQ System implements a **conditional three-phase architecture** optimized for efficiency:

- **🔄 Smart Conditional Processing**: Each phase only executes when relevant changes are detected, preventing unnecessary resource consumption.
- **📊 Phase 1 - Data Collection**: Always executes to collect and analyze current manufacturing data state.
- **🏗️ Phase 2 - Shared DB Building**: Only executes when data changes are detected, ensuring shared databases are updated when needed.
- **🏗️ Phase 2.5 - Historical Insights Generation**: Generates historical insights and analytical data when sufficient historical records are available.
- **📋 Phase 3 - Initial Planning**: Only executes when purchase order changes are detected, optimizing production planning cycles.
- **📈 Comprehensive Reporting**: Generates detailed reports with complete workflow execution summaries and audit trails.

---

## 3. Configuration

### 3.1 WorkflowConfig Class

The `WorkflowConfig` dataclass provides centralized configuration management:

```python
@dataclass
class WorkflowConfig:
    # Basic paths
    db_dir: str = 'database'
    dynamic_db_dir: str = 'database/dynamicDatabase'
    shared_db_dir: str = 'agents/shared_db'
    
    # Processing parameters
    efficiency: float = 0.85
    loss: float = 0.03
    historical_insight_threshold: int = 30
    
    # PendingProcessor configuration
    max_load_threshold: int = 30
    priority_order: PriorityOrder = PriorityOrder.PRIORITY_1
    verbose: bool = True
    use_sample_data: bool = False
    
    # MoldStabilityIndexCalculator configuration
    cavity_stability_threshold: float = 0.6
    cycle_stability_threshold: float = 0.4
    total_records_threshold: int = 30
    
    # MoldMachineFeatureWeightCalculator configuration
    scaling: Literal['absolute', 'relative'] = 'absolute'
    confidence_weight: float = 0.3
    n_bootstrap: int = 500
    confidence_level: float = 0.95
    min_sample_size: int = 10
    feature_weights: Optional[Dict[str, float]] = None
    targets: dict = field(default_factory=lambda: {
        'shiftNGRate': 'minimize',
        'shiftCavityRate': 1.0,
        'shiftCycleTimeRate': 1.0,
        'shiftCapacityRate': 1.0
    })
```

### 3.2 Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Basic Paths** |
| `db_dir` | str | 'database' | Main database directory path |
| `dynamic_db_dir` | str | 'database/dynamicDatabase' | Dynamic database source directory |
| `shared_db_dir` | str | 'agents/shared_db' | Shared database directory for agents |
| **Processing Parameters** |
| `efficiency` | float | 0.85 | Manufacturing efficiency target (85%) |
| `loss` | float | 0.03 | Acceptable loss percentage (3%) |
| `historical_insight_threshold` | int | 30 | Threshold for triggering historical insights |
| **PendingProcessor Configuration** |
| `max_load_threshold` | int | 30 | Maximum load threshold for processing |
| `priority_order` | PriorityOrder | PRIORITY_1 | Processing priority order |
| `verbose` | bool | True | Enable detailed logging |
| `use_sample_data` | bool | False | Use sample data for testing |
| **MoldStabilityIndexCalculator Configuration** |
| `cavity_stability_threshold` | float | 0.6 | Threshold for cavity stability analysis |
| `cycle_stability_threshold` | float | 0.4 | Threshold for cycle stability analysis |
| `total_records_threshold` | int | 30 | Minimum records required for stability calculation |
| **MoldMachineFeatureWeightCalculator Configuration** |
| `scaling` | Literal | 'absolute' | Scaling method ('absolute' or 'relative') |
| `confidence_weight` | float | 0.3 | Weight for confidence calculations |
| `n_bootstrap` | int | 500 | Number of bootstrap samples |
| `confidence_level` | float | 0.95 | Statistical confidence level |
| `min_sample_size` | int | 10 | Minimum sample size for calculations |
| `feature_weights` | Dict[str, float] | None | Custom feature weights (optional) |
| `targets` | dict | See code | Target metrics for optimization |

--- 

## 4. Utility Classes

### 4.1 PathManager

**Purpose**: Centralized path management for all workflow components.

**Constructor**:
```python
def __init__(self, config: WorkflowConfig)
```

**Key Methods**:
- `get_database_schemas_path()`: Returns path to database schemas
- `get_data_loader_path()`: Returns path to DataLoaderAgent output
- `get_annotation_path()`: Returns path to annotations file
- `get_validation_orchestrator_path()`: Returns ValidationOrchestrator directory
- `get_order_progress_tracker_path()`: Returns OrderProgressTracker directory
- `get_producing_processor_path()`: Returns ProducingProcessor directory
- `get_pending_processor_path()`: Returns PendingProcessor directory
- `get_mold_stability_index_path()`: Returns MoldStabilityIndexCalculator directory
- `get_mold_machine_weights_path()`: Returns machine weights file path

### 4.2 ReportManager

**Purpose**: Manages report generation, formatting, and file operations.

**Constructor**:
```python
def __init__(self, output_dir: str, filename_prefix: str)
```

**Key Methods**:

#### Content Management
- `add_header(title: str, separator_type: str = "full")`: Add formatted headers
- `add_section(content: List[str])`: Add content sections
- `add_message(message: str)`: Add single messages
- `add_details_list(details: List[str], prefix: str)`: Add bulleted details

#### File Operations
- `get_report_content() -> str`: Get complete report as string
- `save_report(filename: Optional[str] = None) -> str`: Save report with versioning

**Features**:
- Automatic file versioning with timestamps
- Historical backup management
- UTF-8 encoding for Vietnamese content
- Change log tracking

### 4.3 WorkflowConstants

**Purpose**: Centralized constants for consistent formatting and file naming.

**Key Constants**:

#### Separators
- `FULL_SEPARATOR`: 80-character separator for major sections
- `PARTIAL_SEPARATOR`: 60-character separator for subsections
- `MEDIUM_SEPARATOR`: 35-character separator for minor sections
- `SHORT_SEPARATOR`: 30-character separator for small sections

#### File Names
- `ANNOTATION_FILE`: 'path_annotations.json'
- `CHANGE_LOG_FILE`: 'change_log.txt'
- `DATABASE_SCHEMAS_FILE`: 'databaseSchemas.json'
- `SHARED_DATABASE_SCHEMAS_FILE`: 'sharedDatabaseSchemas.json'
- `WEIGHTS_HIST_FILE`: 'weights_hist.xlsx'

#### Report Headers
- `DATA_COLLECTION_HEADER`: "Starting Daily Data Collecting"
- `SHARED_DB_HEADER`: "Starting Daily Shared DB Building"
- `HISTORICAL_INSIGHTS_HEADER`: "Starting Historical Insights Generating"
- `INITIAL_PLANNER_HEADER`: "Starting InitialPlanner"
- Various progress report headers

### 4.4 WorkflowError

**Purpose**: Custom exception class for workflow-specific errors.

**Usage**:
```python
raise WorkflowError(f"Failed to execute {operation_name}: {e}") from e
```

**Features**:
- Provides clear error context
- Maintains error chain with `from e`
- Used consistently across all workflow operations

---

## 5. Agent Components

### 5.1 DataPipelineOrchestrator
- **Purpose**: Primary data collection agent
- **Input**: Database schemas and annotations
- **Output**: Comprehensive data pipeline report
- **Configuration**: Dynamic database directory, schema paths
  
→ See details: [DataPipelineOrchestrator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md)

### 5.2 ValidationOrchestrator
- **Purpose**: Data validation and quality assurance
- **Input**: Collected data and validation schemas
- **Output**: Validation results and mismatch reports
- **Features**: Automated data quality checks, anomaly detection
  
→ See details: [ValidationOrchestrator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/validationOrchestrator/OptiMoldIQ_validationOrchestrator_overview.md)

### 5.3 OrderProgressTracker
- **Purpose**: Manufacturing order progress monitoring
- **Input**: Order data and change logs
- **Output**: Progress reports and status updates
- **Features**: Real-time progress tracking, milestone monitoring
  
→ See details: [OrderProgressTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_orderProgressTracker_overview.md)

### 5.4 ProducingProcessor
- **Purpose**: Production data analysis and processing
- **Input**: Production data, stability indices, machine weights
- **Output**: Production analysis reports
- **Features**: Efficiency calculations, loss analysis
  
→ See details: [ProducingProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_producingProcessor_review.md)

### 5.5 PendingProcessor
- **Purpose**: Pending order processing and optimization
- **Input**: Pending orders, configuration parameters
- **Output**: Optimized processing schedules
- **Features**: Priority-based processing, load balancing
  
→ See details: [PendingProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/OptiMoldIQ_pendingProcessor_review.md)

### 5.6 MoldStabilityIndexCalculator

**Purpose**: Analyzes historical production data to calculate stability indices for molds.

**Key Features**:
- Cavity stability analysis based on production consistency
- Cycle time stability evaluation
- Statistical thresholds for reliability assessment

**Configuration Parameters**:
- `cavity_stability_threshold`: Minimum threshold for cavity stability (default: 0.6)
- `cycle_stability_threshold`: Minimum threshold for cycle stability (default: 0.4)
- `total_records_threshold`: Minimum records required for calculation (default: 30)

**Output**: Excel report with mold stability indices and recommendations

→ See details: [MoldStabilityIndexCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/historyBasedProcessor/OptiMoldIQ_moldStabilityIndexCalculator_review.md)

### 5.7 MoldMachineFeatureWeightCalculator

**Purpose**: Calculates feature importance weights for mold-machine combinations using statistical analysis.

**Key Features**:
- Bootstrap statistical analysis for confidence intervals
- Feature weight calculation based on production metrics
- Confidence-weighted optimization targets

**Configuration Parameters**:
- `scaling`: Scaling method - 'absolute' or 'relative'
- `confidence_weight`: Weight for confidence calculations (default: 0.3)
- `n_bootstrap`: Number of bootstrap samples (default: 500)
- `confidence_level`: Statistical confidence level (default: 0.95)
- `min_sample_size`: Minimum sample size for valid calculations (default: 10)

**Optimization Targets**:
- `shiftNGRate`: Minimize defect rates
- `shiftCavityRate`: Target cavity utilization rate
- `shiftCycleTimeRate`: Target cycle time efficiency
- `shiftCapacityRate`: Target capacity utilization

**Output**: 
- Confidence report with statistical analysis
- Historical weights file (`weights_hist.xlsx`)

→ See details: [MoldMachineFeatureWeightCalculator](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/autoPlanner/initialPlanner/historyBasedProcessor/OptiMoldIQ_moldMachineFeatureWeightCalculator_review.md)

---

## 6. `OptiMoldIQWorkflow` Class

### 6.1 Constructor
```python
def __init__(self, config: WorkflowConfig)
```
Initializes the workflow with specified configuration.

### 6.2 Methods

#### `detect_updates(data_pipeline_report) -> Tuple[bool, List[str], bool]`
Detects updates in the data pipeline report. Returns: trigger, updated_db_details, historical_insight_request

**Parameters**:
- `data_pipeline_report`: Report from DataPipelineOrchestrator

**Returns**:
- `bool`: Trigger flag indicating if updates were found
- `List[str]`: List of updated database details
- `bool`: Trigger flag indicating if historical insights were requested

**Logic**:
- Checks collector and loader results for data changes
- Evaluates if productRecords has sufficient historical data
- Historical insights triggered when records % historical_insight_threshold == 0

#### `run_workflow() -> Dict[str, Any]`
Executes the complete daily workflow.

**Returns**:
- `Dict[str, Any]`: Complete workflow execution report

**Raises**:
- `Exception`: Critical errors during workflow execution

---

## 7. Usage Examples

### 7.1 Basic Usage

```python
from optimoldiq_workflow import OptiMoldIQWorkflow, WorkflowConfig

# Create configuration
config = WorkflowConfig(
    db_dir='production/database',
    efficiency=0.90,
    max_load_threshold=50,
    verbose=True
)

# Initialize workflow
workflow = OptiMoldIQWorkflow(config)

# Execute daily workflow
try:
    report = workflow.run_workflow()
    print("Workflow completed successfully")
except Exception as e:
    print(f"Workflow failed: {e}")
```

### 7.2 Custom Configuration

```python
# High-performance configuration
config = WorkflowConfig(
    efficiency=0.95,
    loss=0.01,
    max_load_threshold=100,
    priority_order=PriorityOrder.PRIORITY_2,
    verbose=False
)

workflow = OptiMoldIQWorkflow(config)
```

### 7.3 Testing Mode

```python
# Testing configuration with sample data
test_config = WorkflowConfig(
    use_sample_data=True,
    verbose=True,
    db_dir='test/database'
)

test_workflow = OptiMoldIQWorkflow(test_config)
```

---

## 8. Error Handling

### 8.1 `_safe_execute` Method
The workflow implements a centralized error handling mechanism through the `_safe_execute` method:

```python
def _safe_execute(self, operation_name: str, operation_func, *args, **kwargs) -> Any
```

**Features**:
- Consistent error logging across all operations
- Automatic WorkflowError wrapping with context
- Operation timing and status logging
- Error chain preservation with `from e`

**Usage Pattern**:
```python
return self._safe_execute("OperationName", _execute_operation_function)
```

### 8.2 Exception Hierarchy
- **WorkflowError**: Base workflow exception
  - Wraps all operation-specific errors
  - Provides clear error context
  - Maintains original error chain
- **Configuration Errors**: Invalid configuration parameters
- **Database Access Errors**: Database connection or permission issues  
- **Processing Errors**: Agent execution failures
- **File System Errors**: File access or storage issues

### 8.3 Error Recovery Strategy
1. **Phase-level isolation**: Errors in one phase don't affect others
2. **Detailed logging**: All errors logged with full context
3. **Graceful degradation**: Workflow continues where possible
4. **Comprehensive reporting**: Error details included in final reports

---

## 9. Monitoring and Reporting

### 9.1 Report Generation
The system generates comprehensive reports including:
- Data collection summaries
- Validation results
- Progress tracking updates
- Production analysis
- Order processing status

### 9.2 Report Format
Reports are generated for operational staff and include:
- Timestamped headers
- Detailed section breakdowns
- Change detection summaries
- Processing results
- System attribution footer

### 9.3 Log Management
- Uses `loguru` library for structured logging
- Configurable log levels (INFO, DEBUG, ERROR)
- Automatic log rotation and archival
- Integration with monitoring systems

### 9.4 File Outputs
- Reports saved as timestamped text files
- Format: `YYYYMMDD_HHMM_OptiMoldIQWorkflow_report.txt`
- UTF-8 encoding for Vietnamese language support

---

## 10. Deployment Guide

### 10.1 Installation Steps

1. **Environment Setup**
```bash
pip install loguru
# Install other required dependencies
```

2. **Directory Structure**
```
agents/shared_db/
└── OptiMoldIQWorkflow
    ├── historical_reports/                                                              
    ├── latest/                                                                             
    |    └── YYYYMMDD_HHMM_OptiMoldIQWorkflow_report.txt 
    └── change_log.txt         
```

3. **Configuration**
- Create configuration file with environment-specific parameters
- Set appropriate database paths and permissions
- Configure logging levels and output directories

4. **Validation**
- Run test workflow with sample data
- Verify database connections
- Check report generation functionality

### 10.2 Production Deployment

1. **Scheduling**
   - Set up daily cron jobs or task scheduler
   - Configure appropriate execution times
   - Implement monitoring and alerting

2. **Resource Management**
   - Ensure adequate disk space for reports
   - Monitor memory usage during execution
   - Configure database connection pooling

3. **Backup and Recovery**
   - Implement database backup procedures
   - Maintain configuration version control
   - Document recovery procedures

---

## 11. Troubleshooting

### 11.1 Common Issues

**Issue**: Workflow fails to start
- **Cause**: Missing configuration or database access
- **Solution**: Verify configuration parameters and database permissions

**Issue**: Agents fail to execute
- **Cause**: Missing dependencies or file permissions
- **Solution**: Check agent imports and file system permissions

**Issue**: Reports not generated
- **Cause**: File system permissions or disk space
- **Solution**: Verify output directory permissions and available space

**Issue**: Data not updating
- **Cause**: Change detection not triggering
- **Solution**: Review database update mechanisms and timestamps

### 11.2 Debug Mode
Enable verbose logging and sample data mode for troubleshooting:

```python
debug_config = WorkflowConfig(
    verbose=True,
    use_sample_data=True
)
```

### 11.3 Performance Optimization
- Monitor execution times for each phase
- Optimize database queries and indexing
- Implement caching for frequently accessed data
- Consider parallel processing for independent agents

### 11.4 Support and Maintenance
- Regular system health checks
- Performance monitoring and optimization
- Database maintenance and cleanup procedures
- Documentation updates and version control