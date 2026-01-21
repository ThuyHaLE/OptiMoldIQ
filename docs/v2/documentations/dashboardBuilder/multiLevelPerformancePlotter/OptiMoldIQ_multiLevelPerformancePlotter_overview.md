## MultiLevelPerformancePlotter

- **Purpose**:

    - Orchestrate and coordinate the visualization of multi-level performance analytics across different time granularities (day, month, year).
    - Provide a unified interface for generating performance plots, reports, and dashboards from production data.
    - Serve as the main entry point for multi-level performance visualization workflows in the dashboard layer.

- **Core responsibilities**:

    - Configure and initialize the AnalyticsOrchestrator to execute required multi-level performance analysis.
    - Apply auto-configuration rules to propagate plotter enable flags and time-based parameters to underlying analyzers.
    - Coordinate three visualization sub-components: DayLevelDataPlotter, MonthLevelDataPlotter, and YearLevelDataPlotter.
    - Execute visualization tasks conditionally based on enabled plotters and data availability.
    - Generate comprehensive visualization logs and processing summaries.
    - Provide configurable enable/disable controls for each time-level visualization component.

- **Input**:

    - **Configuration object** (PerformancePlotflowConfig):

        - `enable_day_level_plotter`: Enable/disable day-level performance visualization (default: False)
        - `enable_month_level_plotter`: Enable/disable month-level performance visualization (default: False)
        - `enable_year_level_plotter`: Enable/disable year-level performance visualization (default: False)

    - **Day Level Plotter settings**:

        - `day_level_visualization_config_path`: JSON configuration for day-level visualizations (default: None)

    - **Month Level Plotter settings**:

        - `month_level_visualization_config_path`: JSON configuration for month-level visualizations (default: None)

    - **Year Level Plotter settings**:

        - `year_level_visualization_config_path`: JSON configuration for year-level visualizations (default: None)

    - **General settings**:

        - `save_multi_level_performance_plotter_log`: Flag to enable/disable log saving (default: True)
        - `multi_level_performance_plotter_dir`: Directory for consolidated plotter logs (default: "agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter")
        - `enable_parallel`: Enable parallel processing for visualizations (default: True)
        - `max_workers`: Maximum worker threads for parallel processing (default: None, auto-detect)

    - **Dependencies**:

        - `analytics_orchestrator_config`: Configuration object for AnalyticsOrchestrator (default: AnalyticsOrchestratorConfig())

        - Contains nested `performance_config` (PerformanceAnalyticflowConfig) with:
  
            ```
            `record_date`: Date for day-level analysis (default: None)
            `record_month`: Month for month-level analysis (default: None)
            `record_year`: Year for year-level analysis (default: None)
            `source_path`: Database file directory
            `annotation_name`: Path annotations file
            `databaseSchemas_path`: Schema definitions file
            ```
            
- **Output**:

    - Visualization results dictionary:

    ```python
    {
        "day_level_results": {
            "status": "completed",
            "result": {
                "day_level_processor": str,    # Processor log entries
                "day_level_plotter": str       # Plotter log entries
            }
        },
        "month_level_results": {
            "status": "completed",
            "result": {
                "month_level_processor": str,  # Processor log entries
                "month_level_plotter": str     # Plotter log entries
            }
        },
        "year_level_results": {
            "status": "completed",
            "result": {
                "year_level_processor": str,   # Processor log entries
                "year_level_plotter": str      # Plotter log entries
            }
        }
     }
    ```

- **Consolidated visualization log** (optional):
    - Saved to `{multi_level_performance_plotter_dir}/change_log.txt`
    - Contains formatted log entries from all enabled plotters
    - Includes auto-configuration summary
    - Appended to existing log file for historical tracking
    
- **Main Methods**:

    | Method | Description |
    |--------|-------------|
    | `__init__(config)` | Initializes MultiLevelPerformancePlotter with configuration. Applies auto-configuration, creates AnalyticsOrchestrator, and runs required analytics. Stores orchestrator results for downstream visualization. |
    | `_apply_auto_configuration()` | Applies auto-configuration rules to analytics_orchestrator_config based on plotter enable flags and time parameters. Propagates plotter settings to analyzer components and configures save_output flags based on record date availability. Returns summary string of configuration changes. |
    | `data_process()` | Main entry point for visualization processing. Executes enabled visualization components conditionally, collects results, generates consolidated log, and optionally saves log file. Returns `(results_dict, log_entries_str)`. |
    | `day_level_process()` | Processes and visualizes day-level performance data using DayLevelDataPlotter. Extracts day-level results from orchestrator, initializes plotter with configuration, and generates dashboards. Returns dictionary with processing status and log entries. |
    | `month_level_process()` | Processes and visualizes month-level performance data using MonthLevelDataPlotter. Extracts month-level results from orchestrator, initializes plotter with configuration, and generates dashboards. Returns dictionary with processing status and log entries. |
    | `year_level_process()` | Processes and visualizes year-level performance data using YearLevelDataPlotter. Extracts year-level results from orchestrator, initializes plotter with configuration, and generates dashboards. Returns dictionary with processing status and log entries. |
    | `_safe_process(process_func, level_name)` | Wrapper for safe execution of visualization components with error isolation. Catches exceptions, logs errors, and returns None on failure to prevent one component's failure from affecting others. |

- **Data Flow**:
    ```
    Configuration (PerformancePlotflowConfig)
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
    │  enable_day_level_plotter?                  │
    │  → Yes: _safe_process(day_level_process)    │
    └─────────────────────────────────────────────┘
        ↓
    Extract day_level_results from orchestrator_results
        ↓
    Initialize DayLevelDataPlotter with:
    - day_level_results
    - source_path, annotation_name, databaseSchemas_path
    - visualization_config_path
    - parallel processing settings
        ↓
    DayLevelDataPlotter.plot_all()
        ↓
    Collect day-level visualization results
        ↓
    ┌─────────────────────────────────────────────┐
    │  enable_month_level_plotter?                │
    │  → Yes: _safe_process(month_level_process)  │
    └─────────────────────────────────────────────┘
        ↓
    Extract month_level_results from orchestrator_results
        ↓
    Initialize MonthLevelDataPlotter
        ↓
    MonthLevelDataPlotter.plot_all()
        ↓
    Collect month-level visualization results
        ↓
    ┌─────────────────────────────────────────────┐
    │  enable_year_level_plotter?                 │
    │  → Yes: _safe_process(year_level_process)   │
    └─────────────────────────────────────────────┘
        ↓
    Extract year_level_results from orchestrator_results
        ↓
    Initialize YearLevelDataPlotter
        ↓
    YearLevelDataPlotter.plot_all()
        ↓
    Collect year-level visualization results
        ↓
    build_multi_level_performance_plotter_log()
        ↓
    Generate consolidated log string with auto-config summary
        ↓
    ┌─────────────────────────────────────────────────┐
    │  save_multi_level_performance_plotter_log?      │
    │  → Yes: Save to change_log.txt                  │
    └─────────────────────────────────────────────────┘
        ↓
    Return (results_dict, log_entries_str)
    ```

- **Auto-Configuration Rules**: The `_apply_auto_configuration()` method automatically propagates plotter enable flags and time-based parameters to underlying analyzer components:

    - **Enable MultiLevelPerformanceAnalyzer**: If any of `enable_day_level_plotter`, `enable_month_level_plotter`, OR `enable_year_level_plotter` is True

        - Sets `analytics_orchestrator_config.enable_multi_level_analysis = True`

    - **Enable DayLevelDataProcessor**: If `enable_day_level_plotter` is True

        - Sets `analytics_orchestrator_config.enable_multi_level_day_level_processor = True`
        - Sets `analytics_orchestrator_config.performance_config.day_save_output = True if record_date is not None`

    - **Enable MonthLevelDataProcessor**: If `enable_month_level_plotter` is True

        - Sets `analytics_orchestrator_config.enable_multi_level_month_level_processor = True`
        - Sets `analytics_orchestrator_config.performance_config.month_save_output = True if record_month is not None`

    - **Enable YearLevelDataProcessor**: If `enable_year_level_plotter` is True

        - Sets `analytics_orchestrator_config.enable_multi_level_year_level_processor = True`
        - Sets `analytics_orchestrator_config.performance_config.year_save_output = True if record_year is not None`

    - **Force enable analyzer log**:

        - Sets `analytics_orchestrator_config.performance_config.save_multi_level_performance_analyzer_log = True`

**Note**: Manual configuration of nested components will be overridden by auto-configuration at initialization. The auto-configuration summary is logged to console at startup.

- **Execution Mode Selection**:

    - **Conditional execution**: Components only run if corresponding enable flags are True
    - **Sequential processing**: Day, month, and year-level visualizations run one after another
    - **Error isolation**: Each visualization component wrapped in _safe_process() to prevent cascading failures
    - **Configurable components**: Each plotter can be independently enabled/disabled via config flags
    - **Time-based filtering**: Processors only analyze data if corresponding record dates are provided

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

        - Extracts level-specific results from orchestrator_results
        - Validates data availability before initializing plotters
        - Handles plotter initialization and execution errors gracefully
        - Checks for None values in plotter log entries

    - **Log saving**:

        - Creates output directory if it doesn't exist
        - Catches and logs file write errors without failing the visualization
        - Uses append mode to preserve historical logs

- **Visualization Summary Structure**:

    ```python
    # Successful execution with all plotters enabled
    {
        "day_level_results": {
            "status": "completed",
            "result": {
                "day_level_processor": "[2018-11-06] Processed 150 records\n",
                "day_level_plotter": "[2018-11-06] Generated 8 day-level dashboards\n"
            }
        },
        "month_level_results": {
            "status": "completed",
            "result": {
                "month_level_processor": "[2019-01] Processed 4,500 records\n",
                "month_level_plotter": "[2019-01] Generated 6 month-level dashboards\n"
            }
        },
        "year_level_results": {
            "status": "completed",
            "result": {
                "year_level_processor": "[2019] Processed 54,000 records\n",
                "year_level_plotter": "[2019] Generated 4 year-level dashboards\n"
            }
        }
    }

    # Partial execution - only day level enabled
    {
        "day_level_results": {
            "status": "completed",
            "result": {
                "day_level_processor": "[2018-11-06] Processed 150 records\n",
                "day_level_plotter": "[2018-11-06] Generated 8 dashboards\n"
            }
        },
        "month_level_results": None,  # Disabled
        "year_level_results": None    # Disabled
    }

    # Component failed
    {
        "day_level_results": None,    # Failed
        "month_level_results": {...}, # Successful
        "year_level_results": {...}   # Successful
    }
    ```

- **Logging Strategy**:
  
    - **Class-bound logger**: Uses logger.bind(class_="MultiLevelPerformancePlotter") for consistent context
    - **Auto-configuration logging**: Detailed summary of config propagation logged at initialization, including input configs (enable flags and record dates) and applied changes
    - **Component-level logs**: Each sub-plotter generates its own log entries
    - **Consolidated log**: build_multi_level_performance_plotter_log() combines all component logs with auto-config summary
    - **Persistent logging**: Optional append-mode file logging for audit trail
    - **Structured messages**: Clear prefixes (✓, ✗) for success/failure indication

- **Performance Characteristics**:
  
    - **Execution mode**: Sequential visualization processing (day → month → year)
    - **Parallel processing support**: Individual plotters can use parallel processing if enabled
    - **Typical runtime**: Depends on number of enabled levels and data volume for each time period
    - **Memory footprint**: Moderate to high - stores orchestrator results and visualization outputs for multiple time levels
    - **Scalability**: Handles large datasets efficiently with optional parallel rendering at plotter level
    - **Component overhead**: Disabled components add negligible overhead (config check only)

- **Integration Points**:
  
    - **Upstream dependencies**: 
        - **AnalyticsOrchestrator** → Provides multi-level performance analysis results via MultiLevelPerformanceAnalyzer
        - **PerformancePlotflowConfig** → Configuration management for visualization parameters
        - **MultiLevelPerformanceAnalyzer** → Source of day/month/year-level performance data and analytics
        - **PerformanceAnalyticflowConfig** → Nested configuration containing time parameters (record_date, record_month, record_year)
    
    - **Parent orchestrator**:
        - **DashboardBuilder** → Invokes MultiLevelPerformancePlotter as part of the dashboard generation workflow
    
    - **Analysis layer dependencies** (via AnalyticsOrchestrator):
        - DayLevelDataProcessor → Provides day-level performance analysis data
        - MonthLevelDataProcessor → Provides month-level performance analysis data
        - YearLevelDataProcessor → Provides year-level performance analysis data

    - **Visualization sub-components**:
        - DayLevelDataPlotter → Generates day-level performance dashboards and visualizations
        - MonthLevelDataPlotter → Generates month-level performance dashboards and reports
        - YearLevelDataPlotter → Generates year-level performance dashboards and analytics

    - **Persistence**: 
        - Consolidated visualization log in `{multi_level_performance_plotter_dir}/change_log.txt`
        - Component-specific visualizations saved by individual plotters
        - All logs stored in text format for audit trail

- **System Integration Flow**:
    ```
    DashboardBuilder
        ↓
    MultiLevelPerformancePlotter ← (YOU ARE HERE)
        ↓
    _apply_auto_configuration()
        ↓
    AnalyticsOrchestrator (initialized with modified config)
        ↓
    MultiLevelPerformanceAnalyzer (triggered by auto-config)
        ↓
    ┌────────────────────────────────────────────┐
    ↓                      ↓                     ↓
    DayLevelData      MonthLevelData      YearLevelData
    Processor         Processor           Processor
    (analysis)        (analysis)          (analysis)
        ↓                      ↓                     ↓
    Store orchestrator_results with multi_level_analytics
        ↓
    data_process() - Visualization orchestrator
        ↓
    ┌────────────────────────────────────────────┐
    ↓                      ↓                     ↓
    day_level_process month_level_process year_level_process
        ↓                      ↓                     ↓
    DayLevelData      MonthLevelData      YearLevelData
    Plotter           Plotter             Plotter
    (visualization)   (visualization)     (visualization)
        ↓                      ↓                     ↓
    └────────────────────────────────────────────┘
                ↓
    Consolidated visualization results
                ↓
    Day/Month/Year performance dashboards
    ```

- **Configuration Example**:

    ```python
    from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig
    from agents.analyticsOrchestrator.analyticsConfigs.analytics_orchestrator_config import AnalyticsOrchestratorConfig
    from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig

    # Step 1: Configure PerformanceAnalyticflowConfig (nested dependency)
    performance_analytic_config = PerformanceAnalyticflowConfig(
        # Time parameters - control which levels are analyzed
        record_date = "2018-11-06",      # Enables day-level analysis
        record_month = "2019-01",        # Enables month-level analysis
        record_year = "2019",            # Enables year-level analysis
        
        # Additional month/year parameters
        month_analysis_date = "2019-01-15",
        year_analysis_date = "2019-12-31",
        
        # These will be auto-configured by MultiLevelPerformancePlotter
        day_save_output = False,         # Auto-set based on record_date
        month_save_output = False,       # Auto-set based on record_month
        year_save_output = False,        # Auto-set based on record_year
        save_multi_level_performance_analyzer_log = False,  # Force enabled
        
        # Data source configuration
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',
        
        multi_level_performance_analyzer_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter"
    )

    # Step 2: Configure AnalyticsOrchestratorConfig (nested dependency)
    analytics_orchestrator_config = AnalyticsOrchestratorConfig(
        # These will be auto-configured by MultiLevelPerformancePlotter
        enable_multi_level_analysis = False,                    # Auto-enabled
        enable_multi_level_day_level_processor = False,         # Auto-set
        enable_multi_level_month_level_processor = False,       # Auto-set
        enable_multi_level_year_level_processor = False,        # Auto-set
        
        # Disable hardware change analysis
        enable_hardware_change_analysis = False,
        enable_hardware_change_machine_layout_tracker = False,
        enable_hardware_change_machine_mold_pair_tracker = False,
        
        analytics_orchestrator_dir = 'tests/shared_db/DashboardBuilder',
        performance_config = performance_analytic_config
    )

    # Step 3: Configure PerformancePlotflowConfig (main config)
    performance_plotflow_config = PerformancePlotflowConfig(
        # Enable visualization components
        enable_day_level_plotter = True,
        enable_month_level_plotter = True,
        enable_year_level_plotter = True,
        
        # Optional visualization config paths
        day_level_visualization_config_path = None,
        month_level_visualization_config_path = None,
        year_level_visualization_config_path = None,
        
        # General settings
        save_multi_level_performance_plotter_log = True,
        multi_level_performance_plotter_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter",
        
        # Parallel processing
        enable_parallel = True,
        max_workers = None,  # Auto-detect
        
        # Dependency injection
        analytics_orchestrator_config = analytics_orchestrator_config
    )

    # Step 4: Initialize plotter (auto-config happens here)
    plotter = MultiLevelPerformancePlotter(performance_plotflow_config)
    
    # Step 5: Execute visualization pipeline
    results, log_entries_str = plotter.data_process()
    ```

- **Architecture Design**:

    - **Service Layer Pattern**: MultiLevelPerformancePlotter acts as a service layer coordinating analysis and visualization across multiple time granularities
    - **Dependency Injection**: Receives AnalyticsOrchestratorConfig for flexible configuration
    - **Auto-Configuration**: Intelligent propagation of enable flags and time-based parameters reduces configuration complexity
    - **Time-Based Filtering**: Analysis and visualization only occur when corresponding record dates are provided
    - **Separation of Concerns**:

        - Analysis layer (MultiLevelPerformanceAnalyzer + processors) handles data processing at different time levels
        - Visualization layer (MultiLevelPerformancePlotter + plotters) handles rendering


    - **Error Isolation**: Independent component failures don't cascade to other time-level components
    - **Multi-Granularity Support**: Handles day, month, and year-level analytics independently and concurrently

- **Key Differences from [HardwareChangePlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/hardwareChangePlotter/OptiMoldIQ_hardwareChangePlotter_overview.md)**:

    - **Time-based execution**: Performance visualization depends on provided time parameters (`record_date`, `record_month`, `record_year`), while hardware changes depend on change detection
    - **Always executed**: Performance plotters always run when enabled (no "skipped" status based on data changes)
    - **Three time levels**: Day/Month/Year granularity vs Machine/Mold entity types
    - **Save output control**: Auto-configures save_output flags based on date availability
    - **Additional parameters**: Plotters receive source_path, annotation_name, and databaseSchemas_path for data loading