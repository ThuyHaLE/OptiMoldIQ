# OptiMoldIQ Workflow Process

## Workflow Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               [ OptiMoldIQWorkflow ]                                            │
│                    Main orchestrator coordinating all manufacturing workflow phases              │
└──────────────┬──────────────────────────────────────────────────────────────────────────────────┘
               ▼ PHASE 1: DATA COLLECTION                                           
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │ DataPipelineOrch.    │                                            │   Update Detection   │
        │ (Collect & Process)  │────── Process Pipeline ──────────────────⯈│ (Analyze Changes)    │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Execute Data Collection                                             🔍 Detect Database Updates
    • Run DataPipelineOrchestrator                                         • Check collector results
    • Process dynamic databases                                            • Check loader results  
    • Generate pipeline report                                             • Identify changed databases
    • Handle collection errors                                             • Return trigger flag & details

               ▼ PHASE 2: SHARED DB BUILDING (Conditional)
        ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
        │ ValidationOrch.      │      │ OrderProgressTracker │      │ Historical insight   │      │ ProducingProcessor   │
        │ (Data Validation)    │────⯈│ (Progress Monitoring)│────⯈ │ adding phase         │────⯈│ (Production Analysis)│
        └──────────────────────┘      └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
               │                              │                              │                                │
               ▼                              ▼                              ▼                                ▼
    ✅ Validate Data Quality          📈 Track Order Status       📈 Generate Historical Insights   🏭 Process Production Data
    • Run validation checks            • Monitor order progress     • Calculate:                      • Analyze production metrics
    • Generate mismatch reports        • Track milestones           1. mold stability index           • Calculate efficiency & loss
    • Ensure data integrity            • Update progress logs       2. mold machine feature weight    • Generate production reports
    • Save validation results          • Generate progress reports                                    • Process stability indices

               ▼ PHASE 3: INITIAL PLANNING (Conditional)
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │   Purchase Order     │                                            │   PendingProcessor   │
        │   Change Detection   │────── If PO Changes Detected ─────────────⯈│ (Order Processing)   │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    🛒 Check Purchase Orders                                           ⚡ Process Pending Orders
    • Analyze updated databases                                        • Apply priority ordering
    • Look for 'purchaseOrders' changes                               • Respect load thresholds
    • Determine if planning needed                                     • Optimize processing schedule
    • Trigger or skip processing                                       • Generate planning reports

        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                                📋 REPORTING SYSTEM                                  │
        │  • Generate comprehensive workflow reports                                          │
        │  • Include data collection, validation, progress, and planning results              │
        │  • Save timestamped reports with UTF-8 encoding                                     │
        │  • Provide audit trails and operational summaries                                   │
        └─────────────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Phases

### Phase 1: Data Collection

**Purpose**: Collects and processes manufacturing data from various sources.

**Components**:
- DataPipelineOrchestrator
- Update Detection System

**Process Flow**:
1. Initialize DataPipelineOrchestrator with configuration parameters
2. Execute data collection pipeline
3. Generate data pipeline report
4. Detect changes in collected data
5. Trigger subsequent phases based on detected changes

**Directory Structure**:
```
agents/database
├── databaseSchemas.json                                     # Source directory (Data Loader)
└── dynamicDatabase/                                         # Source directory (Data Collection)
    ├── monthlyReports_history/                              # Product records source (Data Collection)
    │   └── monthlyReports_YYYYMM.xlsb
    └── purchaseOrders_history/                              # Purchase orders source (Data Collection)
        └── purchaseOrder_YYYYMM.xlsx

agents/shared_db
├── dynamicDatabase/                                         # Output directory (Data Collection)
|    ├── productRecords.parquet                              # Processed product records (Data Collection)
|    └── purchaseOrders.parquet                              # Processed purchase orders (Data Collection)
└── DataLoaderAgent/                                         # Output directory (Data Collection)
     ├── historical_db/                                      # store historical versions
     ├── newest/                                             # store newest versions
     |    ├── YYYYMMDD_HHMM_itemCompositionSummary.parquet   # Processed item composition (Data Loader)
     |    ├── YYYYMMDD_HHMM_itemInfo.parquet                 # Processed item information (Data Loader)
     |    ├── YYYYMMDD_HHMM_machineInfo.parquet              # Processed machine information (Data Loader)
     |    ├── YYYYMMDD_HHMM_moldInfo.parquet                 # Processed mold information (Data Loader)
     |    ├── YYYYMMDD_HHMM_moldSpecificationSummary.parquet # Processed mold specifications (Data Loader)
     |    ├── YYYYMMDD_HHMM_productRecords.parquet           # Processed product records (Data Loader)
     |    ├── YYYYMMDD_HHMM_purchaseOrders.parquet           # Processed purchase orders (Data Loader)
     |    ├── YYYYMMDD_HHMM_resinInfo.parquet                # Processed resin information (Data Loader)
     |    └── path_annotations.json                          # File path annotations (Data Loader)
     └── change_log.txt                                      # Change tracking log (Data Loader)
```

**Key Methods**:
- `run_data_collection()`: Executes the data collection process
- `detect_updates()`: Analyzes pipeline reports for changes

**Data Flow**: `Raw Data` → `DataPipelineOrchestrator` → `Processed Parquet Files` → `Change Detection`

### Phase 2: Shared Database Building

**Purpose**: Validates collected data and builds shared databases for operational use.

**Components**:
- ValidationOrchestrator: Ensures data integrity
- OrderProgressTracker: Monitors manufacturing progress
- ProducingProcessor: Processes production data

**Process Flow**:
1. Check for detected updates from Phase 1
2. If updates found:
   - Run ValidationOrchestrator
   - Execute OrderProgressTracker
   - Process ProducingProcessor
3. If no updates: Skip processing (efficiency optimization)

**Directory Structure**:
```
agents                                 # Source directory
├── database
|    ├── databaseSchemas.json          # Schema definitions (ValidationOrchestrator, OrderProgressTracker, ProducingProcessor)
|    └── sharedDatabaseSchemas.json    # Shared schema definitions (ProducingProcessor)
└── shared_db                  
    ├── dynamicDatabase/                                         
    |    └── ...                                                       
    └── DataLoaderAgent/                                      
        ├── historical_db/                                      
        ├── newest/                                             
        |   ├── ...          
        |   └── path_annotations.json  # File path annotations (ValidationOrchestrator, OrderProgressTracker, ProducingProcessor)                     
        └── change_log.txt                          
          
agents/shared_db                                              # Output directory
├── ValidationOrchestrator
|     ├── historical_db/                                      # Historical validation results                                   
|     ├── newest/                                             # Latest validation results                                          
|     |    └──  YYYYMMDD_HHMM_validation_orchestrator.xlsx    # Validation report (ValidationOrchestrator)
|     └── change_log.txt                                      # Validation changes (OrderProgressTracker source) 
├── OrderProgressTracker
|     ├── historical_db/                                      # Historical progress data                                   
|     ├── newest/                                             # Latest progress data                                          
|     |    └──  YYYYMMDD_HHMM_auto_status.xlsx                # Progress status report (OrderProgressTracker)
|     └── change_log.txt                                      # Progress changes (ProducingProcessor source)  
├── MoldStabilityIndexCalculator/ 
|    ├── historical_db/                                      
|    ├── newest/ 
|    |   └── YYYYMMDD_HHMM_mold_stability_index.xlsx
|    └── change_log.txt                                       # Stability index changes (ProducingProcessor, MoldMachineFeatureWeightCalculator source)  
├── MoldMachineFeatureWeightCalculator/ 
|   ├── historical_db/                                      
|   ├── newest/ 
|   |   └── YYYYMMDD_HHMM_confidence_report.txt
|   ├── change_log.txt      
|   └── weights_hist.xlsx                                     # Machine weight history (ProducingProcessor source)   
└── ProducingProcessor
      ├── historical_db/                                      # Historical production data                                   
      ├── newest/                                             # Latest production data                                          
      |    └──  YYYYMMDD_HHMM_producing_processor.xlsx        # Production analysis report (ProducingProcessor)
      └── change_log.txt                                      # Production changes
```

**Key Methods**:
- `run_shared_db_building()`: Coordinates shared database building
- `run_validation_orchestrator()`: Executes data validation
- `run_order_progress_tracker()`: Tracks order progress
- `run_producing_processor()`: Processes production data

**Data Flow**: `Processed Data` → `Validation/Progress/Production Agents` → `Analysis Reports` → `Change Logs`

### Phase 2.5: Historical Insights Generation (Conditional)

**Purpose**: Generates historical insights and analytical data when sufficient historical records are available.

**Trigger Condition**: Executes when the number of unique record dates is divisible by `historical_insight_threshold` (default: 30).

**Components**:
- MoldStabilityIndexCalculator: Calculates mold stability indices
- MoldMachineFeatureWeightCalculator: Calculates machine feature weights

**Process Flow**:
```
Check Historical Records
         ↓
[Records % threshold == 0] ?
         ↓ YES                    ↓ NO
Run Stability Calculator    Skip Historical Insights
         ↓
Run Weight Calculator
         ↓
Update Historical Database
```

**Benefits**:
- Provides data-driven insights for production optimization
- Enables predictive maintenance scheduling
- Improves mold-machine matching efficiency
- Supports long-term capacity planning

### Phase 3: Initial Planning

**Purpose**: Performs production planning and optimization based on current data state.

**Components**:
- PendingProcessor: Handles pending order processing

**Process Flow**:
1. Check for purchase order changes
2. If changes detected:
   - Initialize PendingProcessor with configuration
   - Execute order processing and optimization
3. Generate planning reports

**Directory Structure**:
```
agents                                                    # Source directory
├── database
|    ├── databaseSchemas.json                             # Schema definitions (PendingProcessor)              
|    └── sharedDatabaseSchemas.json                       # Shared schema definitions (PendingProcessor)
└── shared_db                  
    ├── dynamicDatabase/                                  # Dynamic data source                                                       
    |   └── ...                           
    ├── DataLoaderAgent/                                  # Loaded data source                              
    |   ├── historical_db/                                      
    |   ├── newest/                                              
    |   |   ├── ...          
    |   |   └── path_annotations.json                     # File path annotations (PendingProcessor source)                  
    |   └── change_log.txt             
    ├── ValidationOrchestrator/                           # Validation results
    |   └── ...   
    ├── OrderProgressTracker/
    |   └── ...       
    ├── MoldStabilityIndexCalculator/                     # Stability calculations                
    |   └── ...                   
    ├── MoldMachineFeatureWeightCalculator/               # Weight calculations               
    |   └── ...                    
    └── ProducingProcessor                                # Production analysis
        ├── historical_db/                                      
        ├── newest/                                             
        |   └── YYYYMMDD_HHMM_producing_processor.xlsx        
        └── change_log.txt                                # Production changes (PendingProcessor source)

agents/shared_db/PendingProcessor                         # Output directory
    ├── historical_db/                                    # Historical planning data                               
    ├── newest/                                           # Latest planning data                                        
    |    └──  YYYYMMDD_HHMM_PendingProcessor.xlsx         # Planning optimization report (PendingProcessor)
    └── change_log.txt                                    # Planning changes
```

**Key Methods**:
- `run_initial_planner()`: Orchestrates initial planning phase
- `run_pending_processor()`: Processes pending orders

**Data Flow**: `Analysis Results` → `PendingProcessor` → `Optimized Planning` → `Final Reports`

## Comprehensive Reporting System

**Purpose**: Generates detailed reports with complete workflow execution summaries and audit trails.

**Directory Structure**:
```
agents/shared_db/OptiMoldIQWorkflow
    ├── historical_reports/                               # Historical workflow reports                                   
    ├── latest/                                           # Latest workflow reports                                          
    |    └── YYYYMMDD_HHMM_OptiMoldIQWorkflow_report.txt  # Workflow execution summary (OptiMoldIQWorkflow)
    └── change_log.txt                                    # Workflow execution log
```

**Data Flow**: `All Phases` → `Comprehensive Report Generation` → `Timestamped Vietnamese Reports`

## Workflow Execution Logic

### Main Workflow Method

```python
def run_workflow() -> Dict[str, Any]:
    """
    Executes the complete daily workflow with conditional phase processing.
    
    Returns:
        Dict[str, Any]: Complete workflow execution report
    """
    
    # PHASE 1: Always execute data collection
    data_pipeline_report = self.run_data_collection()
    
    # Detect changes to determine if subsequent phases should run
    trigger, updated_db_details, historical_insight_request = self.detect_updates(data_pipeline_report)
    
    # PHASE 2: Conditional shared database building
    shared_db_report = None
    if trigger:
        shared_db_report = self.run_shared_db_building(historical_insight_request)
    
    # PHASE 3: Conditional initial planning
    initial_planner_report = None
    if trigger and self._should_run_initial_planner(updated_db_details):
        initial_planner_report = self.run_initial_planner()
    
    # Generate comprehensive workflow report
    workflow_report = self._generate_workflow_report(
        data_pipeline_report, 
        shared_db_report, 
        initial_planner_report,
        trigger,
        updated_db_details,
        historical_insight_request
    )
    
    return workflow_report
```

### Change Detection Logic

```python
def detect_updates(self, data_pipeline_report) -> Tuple[bool, List[str], bool]:
    """
    Detects updates in data pipeline report to determine phase execution.
    
    Args:
        data_pipeline_report: Report from DataPipelineOrchestrator
        
    Returns:
        tuple: (trigger_flag, updated_databases, historical_insight_flag)
    """
    
    trigger = False
    updated_db_details = []
    historical_insight_request = False
    
    # Check collector results for changes
    if 'DataCollectorAgent' in data_pipeline_report:
        collector_results = data_pipeline_report['DataCollectorAgent']
        # Analyze collector change indicators
        
    # Check loader results for changes  
    if 'DataLoaderAgent' in data_pipeline_report:
        loader_results = data_pipeline_report['DataLoaderAgent']
        # Analyze loader change indicators
        
    # Check for historical insights trigger
    if self._should_generate_historical_insights():
        historical_insight_request = True
        
    return trigger, updated_db_details, historical_insight_request
```

### Historical Insights Trigger Logic

```python
def _should_generate_historical_insights(self) -> bool:
    """
    Determines if historical insights should be generated based on record count.
    
    Returns:
        bool: True if insights should be generated
    """
    
    # Check if productRecords has sufficient historical data
    product_records_path = self.path_manager.get_product_records_path()
    
    if product_records_path.exists():
        # Load and analyze record dates
        df = pd.read_parquet(product_records_path)
        unique_dates = df['date'].nunique() if 'date' in df.columns else 0
        
        # Trigger when divisible by threshold
        if unique_dates > 0 and unique_dates % self.config.historical_insight_threshold == 0:
            return True
            
    return False
```

### Purchase Order Change Detection

```python
def _should_run_initial_planner(self, updated_db_details: List[str]) -> bool:
    """
    Determines if initial planner should run based on purchase order changes.
    
    Args:
        updated_db_details: List of updated database details
        
    Returns:
        bool: True if planner should execute
    """
    
    # Look for purchase order related changes
    po_keywords = ['purchaseOrders', 'purchase_orders', 'PO']
    
    for detail in updated_db_details:
        for keyword in po_keywords:
            if keyword.lower() in detail.lower():
                return True
                
    return False
```

## Phase Execution Details

### Phase 1: Data Collection Execution

```python
def run_data_collection(self) -> Dict[str, Any]:
    """Execute Phase 1: Data Collection"""
    
    def _execute_data_collection():
        # Initialize DataPipelineOrchestrator
        orchestrator = DataPipelineOrchestrator(
            db_dir=self.config.db_dir,
            dynamic_db_dir=self.config.dynamic_db_dir,
            shared_db_dir=self.config.shared_db_dir
        )
        
        # Execute data pipeline
        report = orchestrator.run_pipeline()
        
        # Log collection results
        logger.info(f"Data collection completed: {len(report)} components processed")
        
        return report
    
    return self._safe_execute("DataCollection", _execute_data_collection)
```

### Phase 2: Shared Database Building Execution

```python
def run_shared_db_building(self, historical_insight_request: bool = False) -> Dict[str, Any]:
    """Execute Phase 2: Shared Database Building"""
    
    def _execute_shared_db_building():
        results = {}
        
        # Execute ValidationOrchestrator
        results['ValidationOrchestrator'] = self.run_validation_orchestrator()
        
        # Execute OrderProgressTracker
        results['OrderProgressTracker'] = self.run_order_progress_tracker()
        
        # Execute Historical Insights (if requested)
        if historical_insight_request:
            results['HistoricalInsights'] = self._run_historical_insights()
        
        # Execute ProducingProcessor
        results['ProducingProcessor'] = self.run_producing_processor()
        
        return results
    
    return self._safe_execute("SharedDBBuilding", _execute_shared_db_building)
```

### Phase 2.5: Historical Insights Execution

```python
def _run_historical_insights(self) -> Dict[str, Any]:
    """Execute Phase 2.5: Historical Insights Generation"""
    
    def _execute_historical_insights():
        results = {}
        
        # Run MoldStabilityIndexCalculator
        stability_calculator = MoldStabilityIndexCalculator(
            cavity_stability_threshold=self.config.cavity_stability_threshold,
            cycle_stability_threshold=self.config.cycle_stability_threshold,
            total_records_threshold=self.config.total_records_threshold
        )
        results['MoldStabilityIndex'] = stability_calculator.calculate()
        
        # Run MoldMachineFeatureWeightCalculator
        weight_calculator = MoldMachineFeatureWeightCalculator(
            scaling=self.config.scaling,
            confidence_weight=self.config.confidence_weight,
            n_bootstrap=self.config.n_bootstrap,
            confidence_level=self.config.confidence_level,
            min_sample_size=self.config.min_sample_size,
            targets=self.config.targets
        )
        results['MoldMachineWeights'] = weight_calculator.calculate()
        
        return results
    
    return self._safe_execute("HistoricalInsights", _execute_historical_insights)
```

### Phase 3: Initial Planning Execution

```python
def run_initial_planner(self) -> Dict[str, Any]:
    """Execute Phase 3: Initial Planning"""
    
    def _execute_initial_planner():
        # Initialize PendingProcessor
        processor = PendingProcessor(
            max_load_threshold=self.config.max_load_threshold,
            priority_order=self.config.priority_order,
            verbose=self.config.verbose,
            use_sample_data=self.config.use_sample_data
        )
        
        # Execute pending order processing
        results = processor.process_pending_orders()
        
        # Generate optimization reports
        optimization_report = processor.generate_optimization_report()
        
        return {
            'processing_results': results,
            'optimization_report': optimization_report
        }
    
    return self._safe_execute("InitialPlanner", _execute_initial_planner)
```

## Error Handling and Recovery

### Safe Execution Framework

```python
def _safe_execute(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
    """
    Safely executes workflow operations with comprehensive error handling.
    
    Args:
        operation_name: Human-readable operation name for logging
        operation_func: Function to execute safely
        *args, **kwargs: Arguments to pass to operation_func
        
    Returns:
        Any: Result from operation_func
        
    Raises:
        WorkflowError: Wrapped exception with context
    """
    
    start_time = time.time()
    logger.info(f"Starting {operation_name}")
    
    try:
        result = operation_func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Completed {operation_name} in {execution_time:.2f} seconds")
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Failed {operation_name} after {execution_time:.2f} seconds: {e}")
        raise WorkflowError(f"Failed to execute {operation_name}: {e}") from e
```

### Error Recovery Strategies

1. **Phase Isolation**: Each phase is independent and can continue even if previous phases fail
2. **Graceful Degradation**: System continues with available data when components fail
3. **Comprehensive Logging**: All errors are logged with full context and stack traces
4. **Report Integration**: Error details are included in final workflow reports

### Monitoring and Alerting

```python
def _monitor_workflow_health(self) -> Dict[str, Any]:
    """
    Monitors workflow health and generates alerts for critical issues.
    
    Returns:
        Dict[str, Any]: Health status and alerts
    """
    
    health_status = {
        'status': 'healthy',
        'alerts': [],
        'warnings': [],
        'metrics': {}
    }
    
    # Check disk space
    if self._check_disk_space() < 0.1:  # Less than 10% free
        health_status['alerts'].append("Low disk space detected")
        health_status['status'] = 'critical'
    
    # Check database connectivity
    if not self._check_database_connectivity():
        health_status['alerts'].append("Database connectivity issues")
        health_status['status'] = 'critical'
    
    # Check recent execution times
    recent_times = self._get_recent_execution_times()
    if max(recent_times) > self.config.max_execution_time:
        health_status['warnings'].append("Long execution times detected")
    
    return health_status
```

## Performance Optimization

### Conditional Processing Benefits

- **Resource Efficiency**: Only processes when changes are detected
- **Time Optimization**: Skips unnecessary operations when no updates exist
- **Cost Reduction**: Minimizes computational overhead for routine checks
- **Scalability**: Maintains performance as data volume grows

### Execution Time Monitoring

```python
def _track_execution_metrics(self, phase_name: str, execution_time: float, success: bool):
    """
    Tracks execution metrics for performance analysis.
    
    Args:
        phase_name: Name of executed phase
        execution_time: Time taken in seconds
        success: Whether execution was successful
    """
    
    metrics = {
        'phase': phase_name,
        'execution_time': execution_time,
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'memory_usage': self._get_memory_usage(),
        'cpu_usage': self._get_cpu_usage()
    }
    
    # Store metrics for analysis
    self._store_performance_metrics(metrics)
```

### Optimization Recommendations

1. **Database Indexing**: Ensure proper indexing on frequently queried columns
2. **Parallel Processing**: Consider parallel execution for independent agents
3. **Caching Strategy**: Implement caching for frequently accessed data
4. **Resource Monitoring**: Monitor CPU, memory, and disk usage during execution
5. **Data Partitioning**: Partition large datasets by date or other relevant dimensions