> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

## HardwareChangePlotter

- **Purpose**:

    - Orchestrate and coordinate the visualization of hardware-related changes detected in production systems.
    - Provide a unified interface for generating plots, reports, and dashboards from hardware change analytics.
    - Serve as the main entry point for hardware change visualization workflows in the dashboard layer.

- **Core responsibilities**:

    - Configure and initialize the AnalyticsOrchestrator to execute required hardware change analysis.
    - Apply auto-configuration rules to propagate plotter enable flags to underlying analyzers.
    - Coordinate two visualization sub-components: (MachineLayoutPlotter) and (MachineMoldPairPlotter).
    - Execute visualization tasks conditionally based on change detection results.
    - Generate comprehensive visualization logs and processing summaries.
    - Provide configurable enable/disable controls for each visualization component.

- **Input**:

    - **Configuration object** (HardwareChangePlotflowConfig):

        - `enable_machine_layout_plotter`: Enable/disable machine layout change visualization (default: False)
        - `enable_machine_mold_pair_plotter`: Enable/disable machine-mold pair visualization (default: False)

    - **Machine Layout Plotter settings**:

        - `machine_layout_plotter_result_dir`: Directory for layout visualization outputs (default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter")
        - `machine_layout_visualization_config_path`: JSON configuration for layout visualizations (default: None)

    - **Machine-Mold Pair Plotter settings**:

        - `machine_mold_pair_plotter_result_dir`: Directory for mold pair visualization outputs (default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter")
        - `machine_mold_pair_visualization_config_path`: JSON configuration for mold pair visualizations (default: None)

    - **General settings**:

        - `save_hardware_change_plotter_log`: Flag to enable/disable log saving (default: True)
        - `hardware_change_plotter_dir`: Directory for consolidated plotter logs (default: "agents/shared_db/DashboardBuilder/HardwareChangePlotter")
        - `enable_parallel`: Enable parallel processing for visualizations (default: True)
        - `max_workers`: Maximum worker threads for parallel processing (default: None, auto-detect)

    - **Dependencies**:

        - `analytics_orchestrator_config`: Configuration object for AnalyticsOrchestrator (default: AnalyticsOrchestratorConfig())

- **Output**:

    - Visualization results dictionary:

    ```python
    {
        "machine_level_results": {
            "status": "completed" | "skipped",
            "result": {
                "machine_layout_tracker": str,  # Tracker log entries
                "machine_layout_plotter": str   # Plotter log entries
            }
        },
        "mold_level_results": {
            "status": "completed" | "skipped",
            "result": {
                "mold_layout_tracker": str,     # Tracker log entries
                "mold_layout_plotter": str      # Plotter log entries
            }
        }
    }
    ```

- **Consolidated visualization log** (optional):
  
    - Saved to `{hardware_change_plotter_dir}/change_log.txt`
    - Contains formatted log entries from all enabled plotters
    - Includes auto-configuration summary
    - Appended to existing log file for historical tracking
    
- **Main Methods**:

    | Method | Description |
    |--------|-------------|
    | `__init__(config)` | Initializes HardwareChangePlotter with configuration. Applies auto-configuration, creates AnalyticsOrchestrator, and runs required analytics. Stores orchestrator results for downstream visualization. |
    | `_apply_auto_configuration()` | Applies auto-configuration rules to analytics_orchestrator_config based on plotter enable flags. Propagates plotter settings to analyzer components. Returns summary string of configuration changes. |
    | `data_process()` | Main entry point for visualization processing. Executes enabled visualization components conditionally, collects results, generates consolidated log, and optionally saves log file. Returns `(results_dict, log_entries_str)`. |
    | `machine_level_process()` | Processes and visualizes machine layout changes using MachineLayoutPlotter. Checks for layout changes from orchestrator results and generates dashboards if changes detected. Returns dictionary with processing status and log entries. |
    | `mold_level_process()` | Processes and visualizes machine-mold pair relationships using MachineMoldPairPlotter. Checks for pair changes from orchestrator results and generates dashboards if changes detected. Returns dictionary with processing status and log entries. |
    | `_safe_process(process_func, level_name)` | Wrapper for safe execution of visualization components with error isolation. Catches exceptions, logs errors, and returns None on failure to prevent one component's failure from affecting others. |

- **Data Flow**:
    ```
    Configuration (HardwareChangePlotflowConfig)
        ↓
    __init__() - Initialize and configure
        ↓
    _apply_auto_configuration()
        ↓
    Generate auto-config summary string
        ↓
    Log auto-config changes to console
        ↓
    Create AnalyticsOrchestrator with modified config
        ↓
    orchestrator.run_analytics()
        ↓
    Store orchestrator_results and orchestrator_log_str
        ↓
    data_process() - Main visualization orchestrator
        ↓
    Check enabled components
        ↓
    ┌─────────────────────────────────────────────┐
    │  enable_machine_layout_plotter?             │
    │  → Yes: _safe_process(machine_level_process) │
    └─────────────────────────────────────────────┘
        ↓
    Check orchestrator_results for layout changes
        ↓
    has_new_layout_change? → Yes
        ↓
    Extract machine_layout_hist_change
        ↓
    Initialize MachineLayoutPlotter
        ↓
    MachineLayoutPlotter.plot_all()
        ↓
    Collect machine-level visualization results
        ↓
    ┌─────────────────────────────────────────────────────┐
    │  enable_machine_mold_pair_plotter?                  │
    │  → Yes: _safe_process(mold_level_process)           │
    └─────────────────────────────────────────────────────┘
        ↓
    Check orchestrator_results for pair changes
        ↓
    has_new_pair_change? → Yes
        ↓
    Extract first_mold_usage, first_paired_mold_machine, mold_tonnage_summary
        ↓
    Initialize MachineMoldPairPlotter
        ↓
    MachineMoldPairPlotter.plot_all()
        ↓
    Collect mold-level visualization results
        ↓
    build_hardware_change_plotter_log()
        ↓
    Generate consolidated log string with auto-config summary
        ↓
    ┌─────────────────────────────────────────┐
    │  save_hardware_change_plotter_log?      │
    │  → Yes: Save to change_log.txt          │
    └─────────────────────────────────────────┘
        ↓
    Return (results_dict, log_entries_str)
    ```

- **Auto-Configuration Rules**: The `_apply_auto_configuration()` method automatically propagates plotter enable flags to underlying analyzer components:

    - **Enable HardwareChangeAnalyzer**: If either `enable_machine_layout_plotter` OR `enable_machine_mold_pair_plotter `is True
        - Sets `analytics_orchestrator_config.enable_hardware_change_analysis = True`

    - **Enable MachineLayoutTracker**: If `enable_machine_layout_plotter` is True
        - Sets `analytics_orchestrator_config.enable_hardware_change_machine_layout_tracker = True`

    - **Enable MachineMoldPairTracker**: If `enable_machine_mold_pair_plotter` is True
        - Sets `analytics_orchestrator_config.enable_hardware_change_machine_mold_pair_tracker = True`

    - **Force disable intermediate logs**:
        - Sets `analytics_orchestrator_config.save_analytics_orchestrator_log = False`
        - Sets `analytics_orchestrator_config.change_config.save_hardware_change_analyzer_log = False`

**Note**: Manual configuration of nested components will be overridden by auto-configuration at initialization.

- **Execution Mode Selection**:

    - **Conditional execution**: Components only run if corresponding enable flags are True AND changes are detected
    - **Sequential processing**: Machine-level and mold-level visualizations run one after another
    - **Error isolation**: Each visualization component wrapped in _safe_process() to prevent cascading failures
    - **Configurable components**: Each plotter can be independently enabled/disabled via config flags
    - **Early skip**: If no changes detected by analyzers, visualization is skipped with status "skipped"

- **Error Handling**:

    - **Initialization errors**:

        - Auto-configuration failures are logged and raised immediately
        - AnalyticsOrchestrator creation failures halt initialization
        - Analytics execution failures are caught, logged, and re-raised

    - **Component isolation**:

        - Each visualization component runs in _safe_process() wrapper
        - Exceptions caught and logged without stopping other components
        - Failed components return None instead of crashing the plotter

    - **Visualization execution**:

        - Checks for change detection results before running plotters
        - Validates data availability (machine_layout_hist_change, first_mold_usage, etc.)
        - Handles plotter initialization and execution errors gracefully

    - **Log saving**:

        - Creates output directory if it doesn't exist
        - Catches and logs file write errors without failing the visualization
        - Uses append mode to preserve historical logs

- **Visualization Summary Structure**:
    ```python
    # Successful execution with both plotters enabled and changes detected
    {
        "machine_level_results": {
            "status": "completed",
            "result": {
                "machine_layout_tracker": "[2024-11-06] Layout changes detected: 2 machines\n",
                "machine_layout_plotter": "[2024-11-06] Generated 5 layout dashboards\n"
            }
        },
        "mold_level_results": {
            "status": "completed",
            "result": {
                "mold_layout_tracker": "[2024-11-06] New pairs detected: 3 combinations\n",
                "mold_layout_plotter": "[2024-11-06] Generated 3 mold pair dashboards\n"
            }
        }
    }

    # No changes detected
    {
        "machine_level_results": {
            "status": "skipped",
            "result": {
                "machine_layout_tracker": "No changes detected.",
                "machine_layout_plotter": "No changes detected."
            }
        },
        "mold_level_results": None  # Disabled
    }

    # Component disabled or failed
    {
        "machine_level_results": None,  # Disabled or failed
        "mold_level_results": {...}     # Successful
    }
    ```

- **Logging Strategy**:
  
  - **Class-bound logger**: Uses logger.bind(class_="HardwareChangePlotter") for consistent context
  - **Auto-configuration logging**: Detailed summary of config propagation logged at initialization
  - **Component-level logs**: Each sub-plotter generates its own log entries
  - **Consolidated log**: build_hardware_change_plotter_log() combines all component logs with auto-config summary
  - **Persistent logging**: Optional append-mode file logging for audit trail
  - **Structured messages**: Clear prefixes (✓, ✗) for success/failure indication

- **Performance Characteristics**:
  
    - **Execution mode**: Sequential visualization processing (machine → mold)
    - **Parallel processing support**: Individual plotters can use parallel processing if enabled
    - **Typical runtime**: Depends on number of detected changes and visualization complexity
    - **Memory footprint**: Moderate - stores orchestrator results and visualization outputs
    - **Scalability**: Handles large change datasets efficiently with optional parallel rendering
    - **Component overhead**: Disabled components add negligible overhead (config check only)

- **Integration Points**:
  
    - **Upstream dependencies**: 
        - **AnalyticsOrchestrator** → Provides hardware change analysis results via [HardwareChangeAnalyzer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_hardwareChangeAnalyzer_overview.md)
        - **HardwareChangePlotflowConfig** → Configuration management for visualization parameters
        - **HardwareChangeAnalyzer** → Source of change detection data and analytics
    
    - **Parent orchestrator**:
        - **DashboardBuilder** → Invokes HardwareChangePlotter as part of the dashboard generation workflow
    
    - **Analysis layer dependencies** (via AnalyticsOrchestrator):
        - [MachineLayoutTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineLayoutTracker_overview.md) → Provides machine layout change data
        - [MachineMoldPairTracker](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/analyticsOrchestrator/hardwareChangeAnalyzer/OptiMoldIQ_machineMoldPairTracker_overview.md) → Provides machine-mold pairing data

    - **Visualization sub-components**:
        - [MachineLayoutPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_machineLayoutPlotter_overview.md) → Generates machine layout change dashboards and visualizations
        - [MachineMoldPairPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/v2/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_machineMoldPairPlotter_overview.md) → Generates mold pairing dashboards and reports

    - **Persistence**: 
        - Consolidated visualization log in `{hardware_change_plotter_dir}/change_log.txt`
        - Component-specific visualizations saved by individual plotters
        - All logs stored in text format for audit trail

- **System Integration Flow**:
  
    ```
    DashboardBuilder
        ↓
    HardwareChangePlotter ← (YOU ARE HERE)
        ↓
    _apply_auto_configuration()
        ↓
    AnalyticsOrchestrator (initialized with modified config)
        ↓
    HardwareChangeAnalyzer (triggered by auto-config)
        ↓
    ┌────────────────────────────┐
    ↓                            ↓
    MachineLayoutTracker    MachineMoldPairTracker
    (analysis)              (analysis)
        ↓                            ↓
    Store orchestrator_results
        ↓
    data_process() - Visualization orchestrator
        ↓
    ┌────────────────────────────┐
    ↓                            ↓
    machine_level_process    mold_level_process
        ↓                            ↓
    MachineLayoutPlotter    MachineMoldPairPlotter
    (visualization)         (visualization)
        ↓                            ↓
    └────────────────────────────┘
                ↓
    Consolidated visualization results
                ↓
    Layout change dashboards + Mold pairing dashboards
    ```

- **Configuration Example**:
  
    ```python
    from agents.analyticsOrchestrator.analyticsConfigs.change_analyticflow_config import ChangeAnalyticflowConfig
    from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
    from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

    # Step 1: Configure ChangeAnalyticflowConfig (nested dependency)
    change_analytic_config = ChangeAnalyticflowConfig(
        source_path = "tests/shared_db/DataLoaderAgent/newest",
        annotation_name = "path_annotations.json",
        databaseSchemas_path = "tests/mock_database/databaseSchemas.json",
        
        # These will be auto-configured by HardwareChangePlotter
        enable_machine_layout_tracker = False,
        enable_machine_mold_pair_tracker = False,
        save_hardware_change_analyzer_log = False,
        
        machine_layout_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutTracker",
        machine_mold_pair_tracker_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairTracker",
        hardware_change_analyzer_dir = "tests/shared_db/DashboardBuilder/HardwareChangeAnalyzer"
    )

    # Step 2: Configure AnalyticsOrchestratorConfig (nested dependency)
    analytics_orchestrator_config = AnalyticsOrchestratorConfig(
        # These will be auto-configured by HardwareChangePlotter
        enable_hardware_change_analysis = False,
        enable_hardware_change_machine_layout_tracker = False,
        enable_hardware_change_machine_mold_pair_tracker = False,
        save_analytics_orchestrator_log = False,
        
        analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder',
        change_config = change_analytic_config
    )

    # Step 3: Configure HardwareChangePlotflowConfig (main config)
    hardware_change_plotflow_config = HardwareChangePlotflowConfig(
        # Enable visualization components
        enable_machine_layout_plotter = True,
        enable_machine_mold_pair_plotter = True,
        
        # Visualization output directories
        machine_layout_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter",
        machine_mold_pair_plotter_result_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter",
        
        # Optional visualization config paths
        machine_layout_visualization_config_path = None,
        machine_mold_pair_visualization_config_path = None,
        
        # General settings
        save_hardware_change_plotter_log = True,
        hardware_change_plotter_dir = "tests/shared_db/DashboardBuilder/HardwareChangePlotter",
        
        # Parallel processing
        enable_parallel = True,
        max_workers = None,  # Auto-detect
        
        # Dependency injection
        analytics_orchestrator_config = analytics_orchestrator_config
    )

    # Step 4: Initialize plotter (auto-config happens here)
    plotter = HardwareChangePlotter(hardware_change_plotflow_config)
    
    # Step 5: Execute visualization pipeline
    results, plotter_log = plotter.data_process()
    ```

- **Architecture Design**:

    - **Service Layer Pattern**: HardwareChangePlotter acts as a service layer coordinating analysis and visualization
    - **Dependency Injection**: Receives AnalyticsOrchestratorConfig for flexible configuration
    - **Auto-Configuration**: Intelligent propagation of enable flags reduces configuration complexity
    - **Separation of Concerns**:

        - Analysis layer (HardwareChangeAnalyzer + trackers) handles data processing
        - Visualization layer (HardwareChangePlotter + plotters) handles rendering

    - **Error Isolation**: Independent component failures don't cascade to other components
    - **Lazy Visualization**: Only generates dashboards when changes are detected