## dataChangeAnalyzer

- **Purpose**:
  
    - Orchestrate and coordinate the detection of data changes in production records, specifically tracking machine layout changes and machine-mold pair relationships over time.
    - Provide intelligent parallel or sequential processing based on system resource availability.
    - Serve as the main entry point for change analysis workflows.
  
- **Core responsibilities**:
  
    - Load and validate production records, mold information, and machine information from database sources.
    - Initialize and coordinate two sub-analyzers: ([MachineLayoutTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_machineLayoutTracker_overview.md)) and ([MachineMoldPairTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_machineMoldPairTracker_overview.md)).

    - Monitor system resources (CPU, memory) to determine optimal processing strategy.
    - Execute change detection tasks in parallel or sequential mode based on resource availability.
    - Trigger update workflows when new changes are detected.
    - Provide comprehensive analysis summaries for downstream consumers.
  
- **Input**:
  
  - **Database paths**:
    - `source_path`: Directory containing the newest database files (default: 'agents/shared_db/DataLoaderAgent/newest')
    - `annotation_name`: JSON file mapping database names to file paths (default: "path_annotations.json")
    - `databaseSchemas_path`: JSON schema definition file (default: 'database/databaseSchemas.json')

  - **Output directories**:
    - `machine_layout_output_dir`: Directory for layout change outputs (default: "agents/shared_db/UpdateHistMachineLayout")
    - `mold_overview_output_dir`: Directory for mold-machine pair outputs (default: "agents/shared_db/UpdateHistMoldOverview")

  - **Parallel processing configuration**:
    - `min_workers`: Minimum workers required for parallel execution (default: 2)
    - `max_workers`: Maximum workers allowed (default: min(cpu_count, 4))
    - `parallel_mode`: Execution mode - "process" or "thread" (default: "process")

  - **DataFrames (loaded automatically)**:
    - `productRecords_df`: Production records with columns `recordDate`, `machineNo`, `machineCode`, `moldNo`, etc.
    - `moldInfo_df`: Static mold information
    - `machineInfo_df`: Static machine information

- **Output**:
  
  - **Analysis artifacts**:
    - Layout change history JSON files (via MachineLayoutTracker)
    - Machine-mold pair mapping JSON files (via MachineMoldPairTracker)
    - Updated visualization plots and reports

  - **Analysis summary dictionary containing**:
    - Latest record date processed
    - Layout change detection results
    - Machine-mold pair change results
    - Output directory paths
    - Parallel processing configuration used
    
- **Main Methods**:
  
| Method | Description |
|--------|-------------|
| `_load_database_schemas(databaseSchemas_path)` | Loads database schema definitions with error handling and logging. |
| `_load_path_annotations(source_path, annotation_name)` | Loads path annotations mapping database names to file locations. |
| `_load_dataframe(df_name)` | Loads a specific DataFrame from parquet file with validation and error handling. |
| `_check_system_resources()` | Analyzes CPU usage, memory availability, and logical CPU count to determine optimal worker count and whether parallel processing is feasible. Returns `(can_run_parallel, optimal_workers)`. |
| `_analyze_layout_changes_task()` | Isolated task function for layout change detection. Creates `MachineLayoutTracker` instance and checks for new changes. Returns `(task_name, has_changes, changes_dict)`. |
| `_analyze_machine_mold_pair_changes_task()` | Isolated task function for machine-mold pair detection. Creates `MachineMoldPairTracker` instance and checks for new pairs. Returns `(task_name, has_changes, new_pairs, pair_data)`. |
| `analyze_changes(force_parallel)` | Main entry point for change analysis. Determines execution strategy (parallel/sequential) based on system resources and `force_parallel` flag, then delegates to appropriate execution method. |
| `_analyze_changes_parallel(num_workers)` | Executes both analysis tasks concurrently using `ProcessPoolExecutor` or `ThreadPoolExecutor`. Handles task completion, error recovery, and automatic fallback to sequential mode on failure. |
| `_analyze_changes_sequential()` | Executes analysis tasks sequentially (original behavior). Calls `_analyze_layout_changes()` and `_analyze_machine_mold_pair_changes()` in order. |
| `_analyze_layout_changes()` | Sequential wrapper for layout analysis. Initializes tracker, detects changes, and triggers update workflow if needed. |
| `_analyze_machine_mold_pair_changes()` | Sequential wrapper for machine-mold pair analysis. Initializes tracker, detects changes, and triggers update workflow if needed. |
| `_update_layout_changes()` | Triggers `UpdateHistMachineLayout` workflow to process and visualize detected layout changes. |
| `_update_mold_overview()` | Triggers `UpdateHistMoldOverview` workflow to process and visualize detected machine-mold pair changes. |
| `get_analysis_summary()` | Returns comprehensive dictionary summarizing all analysis results, configurations, and output locations. |

- **Data Flow**:
  
```
Input DataFrames (productRecords, moldInfo, machineInfo)
         ↓
    __init__() - Load and validate data
         ↓
    analyze_changes() - Main orchestrator
         ↓
    _check_system_resources() - Resource assessment
         ↓
    ┌────────────────────────────────────┐
    │  Parallel Mode  │  Sequential Mode │
    └────────────────────────────────────┘
         ↓                    ↓
    Concurrent execution  Sequential execution
         ↓                    ↓
    ┌─────────────────────────────────────┐
    │  Layout Analysis  │  Pair Analysis  │
    └─────────────────────────────────────┘
         ↓                    ↓
    MachineLayoutTracker  MachineMoldPairTracker
         ↓                    ↓
    Detect changes       Detect new pairs
         ↓                    ↓
    ┌─────────────────────────────────────┐
    │    Has changes?    │  Has new pairs? │
    └─────────────────────────────────────┘
         ↓ (Yes)              ↓ (Yes)
    _update_layout_changes()  _update_mold_overview()
         ↓                    ↓
    UpdateHistMachineLayout   UpdateHistMoldOverview
         ↓                    ↓
    Output artifacts and visualizations
```

- **Execution Mode Selection**:
  
    - **Parallel mode** (default): Uses `ProcessPoolExecutor` or `ThreadPoolExecutor` based on `parallel_mode` setting
    - **Sequential mode**: Fallback when system resources are insufficient or parallel execution fails
    - **Force parallel**: Override resource checks with `force_parallel=True` parameter

- **Error Handling**:
  
    - **DataFrame loading**: Validates file paths, checks file existence, handles parquet read errors with detailed logging
    - **Schema validation**: Uses `@validate_init_dataframes` decorator to ensure required columns are present
    - **Task isolation**: Each analysis task runs in try-except blocks; failures in one task don't affect the other
    - **Automatic fallback**: Parallel execution automatically falls back to sequential mode on failure
    - **Resource monitoring**: Safe handling of resource check failures with warning logs
    - **Update workflow errors**: Catches and logs errors from update modules without crashing the main process

- **Analysis Summary Structure**:
  
```python
{
    'latest_record_date': Timestamp('2024-11-06'),
    'has_new_layout_change': True,
    'layout_changes': {
        '2024-11-06': {'M001': 'MC01', 'M002': 'MC02'}
    },
    'machine_layout_output_dir': 'agents/shared_db/UpdateHistMachineLayout',
    'has_new_pair_change': True,
    'new_pairs': [('MC01', 'MOLD_A'), ('MC02', 'MOLD_B')],
    'mold_overview_output_dir': 'agents/shared_db/UpdateHistMoldOverview',
    'parallel_config': {
        'min_workers': 2,
        'max_workers': 4,
        'parallel_mode': 'process'
    }
}
```

- **Performance Characteristics**:
  
    - **Sequential mode**: ~X seconds for typical dataset (baseline)
    - **Parallel mode**: Typically 40-60% faster when system resources permit
    - **Memory footprint**: Minimal additional overhead in thread mode; process mode duplicates data per worker
    - **CPU utilization**: Dynamically adjusts worker count to avoid system overload
    - **Scalability**: Handles datasets with thousands of records and hundreds of machines/molds efficiently

- **Integration Points**:
  
    - **Upstream**: Depends on ([DataLoaderAgent](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md)) for fresh database files
  
    - **Downstream**: Outputs consumed by:
      - ([UpdateHistMachineLayout](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_updateHistMachineLayout_overview.md)) - Generates layout change visualizations
      - ([UpdateHistMoldOverview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_updateHistMoldOverview_overview.md)) - Generates machine-mold relationship visualizations
    
    - **Persistence**: All changes stored in JSON format for audit trail and future reference