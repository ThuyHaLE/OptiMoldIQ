## HardwareChangeAnalyzer

- **Purpose**:
  
    - Orchestrate and coordinate the detection of hardware-related data changes in production records, specifically tracking machine layout changes and machine-mold pair relationships over time.
    - Provide configurable, modular execution of change detection components.
    - Serve as the main entry point for hardware change analysis workflows.
  
- **Core responsibilities**:
  
    - Load and validate production records, mold information, and machine information from database sources..
    - Initialize and coordinate two sub-analyzers: ([MachineLayoutTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineLayoutTracker_overview.md)) and ([MachineMoldPairTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineMoldPairTracker_overview.md)).

    - Execute change detection tasks sequentially with error isolation..
    - Generate comprehensive change logs and analysis summaries.
    - Provide configurable enable/disable controls for each analysis component.
  
- **Input**:
  - **Configuration object** (ChangeAnalyticflowConfig):
    - `source_path`: Directory containing the newest database files (default: 'agents/shared_db/DataLoaderAgent/newest')
    - `annotation_name`: JSON file mapping database names to file paths (default: "path_annotations.json")
    - `databaseSchemas_path`: JSON schema definition file (default: 'database/databaseSchemas.json')
  
  - **Component enable flags**:
    - enable_machine_layout_tracker: Enable/disable layout change analysis (default: True)
    - enable_machine_mold_pair_tracker: Enable/disable machine-mold pair analysis (default: True)
 
  - **Output directories**:
    - `machine_layout_tracker_dir`: Directory for layout change outputs (default: "agents/shared_db/UpdateHistMachineLayout")
    - `machine_layout_tracker_change_log_name`: Change log filename for layout tracker
    - `machine_mold_pair_tracker_dir`: Directory for mold-machine pair outputs (default: "agents/shared_db/UpdateHistMoldOverview")
    - `machine_mold_pair_tracker_change_log_name`: Change log filename for pair tracker
    - `hardware_change_analyzer_dir`: Directory for consolidated analyzer logs
    - `save_hardware_change_analyzer_log`: Flag to enable/disable log saving (default: True)

- **Output**: 
  
  - **Analysis results dictionary**:
     ```python
     {
          "machine_layout_tracker": {
               "has_new_layout_change": bool,
               "machine_layout_hist_change": dict,
               "log_entries": str
          },
          "machine_mold_pair_tracker": {
               "has_new_pair_change": bool,
               "mold_tonnage_summary": DataFrame,
               "first_mold_usage": DataFrame,
               "first_paired_mold_machine": DataFrame,
               "log_entries": str
          }
     }
     ```

  - **Consolidated change log** (optional):
    - Saved to `{hardware_change_analyzer_dir}/change_log.txt`
    - Contains formatted log entries from all enabled analyzers
    - Appended to existing log file for historical tracking
    - Parallel processing configuration used
    
- **Main Methods**:

     | Method | Description |
     |--------|-------------|
     | `_load_database_schemas(databaseSchemas_path)` | Loads database schema definitions with error handling and logging. Returns schema dictionary. |
     | `_load_path_annotations(source_path, annotation_name)` | Loads path annotations mapping database names to file locations. Returns annotation dictionary. |
     | `_load_dataframe(df_name)` | Loads a specific DataFrame from parquet file with validation and error handling. Checks file existence, validates path, and logs success/failure. Returns loaded DataFrame. |
     | `analyze_changes()` | Main entry point for change analysis. Executes enabled analysis components sequentially, collects results, generates consolidated log, and optionally saves log file. Returns `(results_dict, log_entries_str)`. |
     | `analyze_layout_changes(save_output=False)` | Analyzes machine layout changes using `MachineLayoutTracker`. Detects new layout configurations and generates change history. Returns dictionary with change status, history, and log entries. |
     | `analyze_machine_mold_pair_changes()` | Analyzes machine-mold pair relationships using `MachineMoldPairTracker`. Detects new pairings and generates summary dataframes. Returns dictionary with change status, summary data, and log entries. |
     | `_safe_process(process_func, component_name)` | Wrapper for safe execution of analysis components with error isolation. Catches exceptions, logs errors, and returns None on failure to prevent one component's failure from affecting others. |

- **Data Flow**:
  
     ```
     Configuration (ChangeAnalyticflowConfig)
          ↓
     __init__() - Load and validate data
          ↓
     Load database schemas and path annotations
          ↓
     Load DataFrames (productRecords, moldInfo, machineInfo)
          ↓
     Identify latest record date
          ↓
     analyze_changes() - Main orchestrator
          ↓
     Check enabled components
          ↓
     ┌─────────────────────────────────────────────┐
     │  enable_machine_layout_tracker?             │
     │  → Yes: _safe_process(analyze_layout_changes) │
     └─────────────────────────────────────────────┘
          ↓
     MachineLayoutTracker.data_process()
          ↓
     Collect layout change results
          ↓
     ┌─────────────────────────────────────────────────────┐
     │  enable_machine_mold_pair_tracker?                  │
     │  → Yes: _safe_process(analyze_machine_mold_pair_changes) │
     └─────────────────────────────────────────────────────┘
          ↓
     MachineMoldPairTracker.data_process()
          ↓
     Collect pair change results
          ↓
     build_hardware_change_analyzer_log()
          ↓
     Generate consolidated log string
          ↓
     ┌─────────────────────────────────────────┐
     │  save_hardware_change_analyzer_log?     │
     │  → Yes: Save to change_log.txt          │
     └─────────────────────────────────────────┘
          ↓
     Return (results_dict, log_entries_str)
     ```

- **Execution Mode Selection**:
  - **Sequential execution**: All enabled components run in order, one after another
  - **Error isolation**: Each component wrapped in _safe_process() to prevent cascading failures
  - **Configurable components**: Each analyzer can be independently enabled/disabled via config flags
  - **Early exit**: If no components are enabled, analysis exits immediately with informational log

- **Error Handling**:
  - **DataFrame loading**:
    - Validates file paths in annotations
    - Checks file existence before reading
    - Handles parquet read errors with detailed logging
    - Raises appropriate exceptions (KeyError, FileNotFoundError) with context

  - **Schema validation**:
    - Uses @validate_init_dataframes decorator to ensure required columns are present
    - Validates against schema definitions from databaseSchemas.json

  - **Component isolation**:
    - Each analysis component runs in _safe_process() wrapper
    - Exceptions caught and logged without stopping other components
    - Failed components return None instead of crashing the analyzer

  - **Log saving**:
    - Creates output directory if it doesn't exist
    - Catches and logs file write errors without failing the analysis
    - Uses append mode to preserve historical logs

- **Analysis Summary Structure**:
  
     ```python
     # Successful execution with both components enabled
     {
     "machine_layout_tracker": {
          "has_new_layout_change": True,
          "machine_layout_hist_change": {
               '2024-11-06': {'M001': 'MC01', 'M002': 'MC02'}
          },
          "log_entries": "[2024-11-06] Layout changes detected: 2 machines\n"
     },
     "machine_mold_pair_tracker": {
          "has_new_pair_change": True,
          "mold_tonnage_summary": pd.DataFrame(...),
          "first_mold_usage": pd.DataFrame(...),
          "first_paired_mold_machine": pd.DataFrame(...),
          "log_entries": "[2024-11-06] New pairs detected: 3 combinations\n"
     }
     }

     # Component disabled or failed
     {
     "machine_layout_tracker": None,  # Disabled or failed
     "machine_mold_pair_tracker": {...}  # Successful
     }
     ```

- **Logging Strategy**:
  
  - **Class-bound logger**: Uses logger.bind(class_="HardwareChangeAnalyzer") for consistent context
  - **Component-level logs**: Each sub-analyzer generates its own log entries
  - **Consolidated log**: build_hardware_change_analyzer_log() combines all component logs
  - **Persistent logging**: Optional append-mode file logging for audit trail
  - **Structured messages**: Clear prefixes (✅, ❌, ✓, ✗) for success/failure indication

- **Performance Characteristics**:
  
    - **Execution mode**: Sequential only (no parallel processing)
    - **Typical runtime**: Depends on dataset size and number of enabled components
    - **Memory footprint**: Minimal - single process, no data duplication
    - **Scalability**: Handles datasets with thousands of records efficiently
    - **Component overhead**: Each disabled component adds negligible overhead (config check only)

- **Integration Points**:
  
    - **Upstream dependencies**: 
        - **DataPipelineOrchestrator** → Provides fresh database files via [DataLoaderAgent](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md)
        - **ChangeAnalyticflowConfig** → Configuration management for analysis parameters
    
    - **Parent orchestrator**:
        - **AnalyticsOrchestrator** → Invokes HardwareChangeAnalyzer as part of the analytics workflow
        - Triggered when `enable_hardware_change_plotter` is enabled in DashboardBuilder
    
    - **Sub-component orchestration** (Analysis layer):
        - [MachineLayoutTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineLayoutTracker_overview.md) → Analyzes machine layout configuration changes over time
        - [MachineMoldPairTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineMoldPairTracker_overview.md) → Analyzes machine-mold pairing relationships and first usage patterns

    - **Downstream consumers** (Visualization layer):
        - [HardwareChangePlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_hardwareChangePlotter_overview.md) → Top-level plotter coordinating hardware change visualizations
            - [MachineLayoutPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_machineLayoutPlotter_overview.md) → Generates machine layout change dashboards using results from MachineLayoutTracker
            - [MachineMoldPairPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_machineMoldPairPlotter_overview.md) → Generates mold pairing dashboards using results from MachineMoldPairTracker

    - **Persistence**: 
        - Component-level change logs (managed by MachineLayoutTracker and MachineMoldPairTracker)
        - Consolidated change log in `{hardware_change_analyzer_dir}/change_log.txt`
        - All changes stored in JSON/text format for audit trail and visualization consumption

- **System Integration Flow**:
     ```
     DataPipelineOrchestrator
          ↓
     DashboardBuilder
          ↓
     enable_hardware_change_plotter? (Yes)
          ↓
     AnalyticsOrchestrator
          ↓
     HardwareChangeAnalyzer ← (YOU ARE HERE)
          ↓
     ┌────────────────────────────┐
     ↓                            ↓
     MachineLayoutTracker    MachineMoldPairTracker
     (analysis)              (analysis)
     ↓                            ↓
     └────────────────────────────┘
                    ↓
          HardwareChangePlotter
                    ↓
     ┌────────────────────────────┐
     ↓                            ↓
     MachineLayoutPlotter    MachineMoldPairPlotter
     (visualization)         (visualization)
     ↓                            ↓
     Layout change dashboards    Mold pairing dashboards

- **Configuration Example**:
     ```python  
     from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig

     change_analytic_config = ChangeAnalyticflowConfig(
        
        # Enable HardwareChangeAnalyzer components

        #------------------------#
        # MACHINE LAYOUT TRACKER #
        #------------------------#

        # Trigger HardwareChangeAnalyzer-MachineLayoutTracker if True
        enable_machine_layout_tracker = False, # Default: False

        machine_layout_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker", 
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker"
        machine_layout_tracker_change_log_name = "change_log.txt", 
        #Default: "change_log.txt"

        #---------------------------#
        # MACHINE-MOLD PAIR TRACKER #
        #---------------------------#

        # Trigger HardwareChangeAnalyzer-MachineMoldPairTracker if True
        enable_machine_mold_pair_tracker = False, # Default: False

        machine_mold_pair_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker", 
        #Default: "agents/shared_db/HardwareChangeAnalyzer/MachineMoldPairTracker"
        machine_mold_pair_tracker_change_log_name = "change_log.txt" ,
        #Default: "change_log.txt"

        #-----------------------------------------#
        # HARDWARE CHANGE ANALYZER GENERAL CONFIG #
        #-----------------------------------------#

        source_path = "tests/shared_db/DataLoaderAgent/newest", # Default: 'agents/shared_db/DataLoaderAgent/newest'
        annotation_name = "path_annotations.json", # Default: "path_annotations.json"
        databaseSchemas_path = "tests/mock_database/databaseSchemas.json", # Default: 'database/databaseSchemas.json'

        save_hardware_change_analyzer_log = True, # Default: True
        hardware_change_analyzer_dir = "tests/shared_db/DashboardBuilder/HardwareChangeAnalyzer", 
        # Default: "agents/shared_db/HardwareChangeAnalyzer"

    )

     analyzer = HardwareChangeAnalyzer(change_analytic_config)
     results, log_str = analyzer.analyze_changes()
     ```
    