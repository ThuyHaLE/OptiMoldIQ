## MultiLevelPerformanceAnalyzer

- **Purpose**:
  
  - Orchestrate and coordinate multi-level performance analytics processing across day, month, and year timeframes.
  - Provide unified interface for hierarchical data analysis that supports different temporal granularities.
  - Serve as the service layer connecting data processors to downstream consumers (dashboard builders, planning agents).


- **Core responsibilities**:
  
  - Conditionally execute time-based data processors based on configuration settings.
  - Coordinate three specialized processors: [DayLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_dayLevelDataProcessor_overview.md), [MonthLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_monthLevelDataProcessor_overview.md), and [YearLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_yearLevelDataProcessor_overview.md).
  - Generate consolidated performance logs across all processing levels.
  - Provide error isolation to ensure failures at one level don't affect other levels.
  - Aggregate analysis summaries and metrics for multi-level reporting.

- **Input**:
  - **Configuration object** (PerformanceAnalyticflowConfig):
    
    - `source_path`: Directory containing the newest database files (default: 'agents/shared_db/DataLoaderAgent/newest')
    - `annotation_name`: JSON file mapping database names to file paths (default: "path_annotations.json")
    - `databaseSchemas_path`: JSON schema definition file (default: 'database/databaseSchemas.json')


  - **Time parameters** (conditional execution):

    - `record_date`: Date for day-level analysis (optional, uses default if not specified)
    - `record_month`: Month string for month-level analysis (format: "YYYY-MM", optional)
    - `record_year`: Year string for year-level analysis (format: "YYYY", optional)
    - `month_analysis_date`: Timestamp for month-level snapshot (optional)
    - `year_analysis_date`: Timestamp for year-level snapshot (optional)


  - **Output control flags**:
    
    - `day_save_output`: Enable/disable saving day-level outputs (default: False)
    - `month_save_output`: Enable/disable saving month-level outputs (default: False)
    - `year_save_output`: Enable/disable saving year-level outputs (default: False)
    - `save_multi_level_performance_analyzer_log`: Enable/disable consolidated log saving (default: True)

  - **Output directory**:
  
    - `multi_level_performance_analyzer_dir`: Base directory for all analytics outputs

- **Output**: 
  
  - Multi-level results dictionary:

    ```json
    {
        "day_level_results": {
            "record_date": Timestamp,
            "processed_records": DataFrame,
            "mold_based_records": DataFrame,
            "item_based_records": DataFrame,
            "summary_stats": dict,
            "analysis_summary": dict,
            "log_entries": str
        },
        "month_level_results": {
            "record_month": str,
            "month_analysis_date": Timestamp,
            "finished_records": DataFrame,
            "unfinished_records": DataFrame,
            "analysis_summary": dict,
            "log_entries": str
        } or None,
        "year_level_results": {
            "record_year": str,
            "year_analysis_date": Timestamp,
            "finished_records": DataFrame,
            "unfinished_records": DataFrame,
            "analysis_summary": dict,
            "log_entries": str
        } or None
    }
    ```

- **Consolidated performance log** (optional):
    - Saved to `{multi_level_performance_analyzer_dir}/change_log.txt`
    - Contains formatted log entries from all executed processing levels
    - Appended to existing log file for historical tracking

- **Main Methods**:
  
    | Method | Description |
    |--------|-------------|
    | `data_process()` | Main entry point for multi-level processing pipeline. Conditionally executes day/month/year processors based on config, collects results, generates consolidated log, and optionally saves log file. Returns `(results_dict, log_entries_str)`. |
    | `day_level_process()` | Processes day-level production data using `DayLevelDataProcessor`. Generates processed records, mold-based aggregations, item-based aggregations, and summary statistics. Supports default date if not specified. Returns dictionary with processed data and analysis summary. |
    | `month_level_process()` | Processes month-level order tracking data using `MonthLevelDataProcessor`. Separates finished and unfinished orders for the specified month. Returns dictionary with order status data and analysis summary. |
    | `year_level_process()` | Processes year-level performance trends using `YearLevelDataProcessor`. Analyzes yearly production patterns and order completion. Returns dictionary with yearly data and analysis summary. |
    | `_safe_process(process_func, level_name)` | Wrapper for safe execution of level processors with error isolation. Catches exceptions, logs errors, and returns None on failure to prevent one level's failure from affecting others. |

- **Data Flow**:
    ```
    Configuration (PerformanceAnalyticflowConfig)
         ↓
    __init__() - Initialize analyzer
         ↓
    data_process() - Main orchestrator
         ↓
    ┌─────────────────────────────────────────────┐
    │  Day Level (Always Runs)                    │
    │  _safe_process(day_level_process)           │
    └─────────────────────────────────────────────┘
         ↓
    DayLevelDataProcessor.data_process()
         ↓
    - Processed daily records
    - Mold-based aggregations
    - Item-based aggregations
    - Summary statistics
         ↓
    ┌─────────────────────────────────────────────┐
    │  Month Level (Conditional: record_month?)   │
    │  _safe_process(month_level_process)         │
    └─────────────────────────────────────────────┘
         ↓
    MonthLevelDataProcessor.data_process()
         ↓
    - Finished orders for month
    - Unfinished orders for month
    - Monthly analysis summary
         ↓
    ┌─────────────────────────────────────────────┐
    │  Year Level (Conditional: record_year?)     │
    │  _safe_process(year_level_process)          │
    └─────────────────────────────────────────────┘
         ↓
    YearLevelDataProcessor.data_process()
         ↓
    - Finished orders for year
    - Unfinished orders for year
    - Yearly analysis summary
         ↓
    Collect all level results
         ↓
    build_multi_level_performance_analyzer_log()
         ↓
    Generate consolidated log string
         ↓
    ┌─────────────────────────────────────────────────┐
    │  save_multi_level_performance_analyzer_log?     │
    │  → Yes: Save to change_log.txt                  │
    └─────────────────────────────────────────────────┘
         ↓
    Return (results_dict, log_entries_str)
    ```

- **Execution Strategy**:
  
  - **Conditional execution**: Each processing level runs only if its corresponding time parameter is provided
    
    - *Day level*: Always executes (supports default date fallback)
    - *Month level*: Only executes if record_month is specified
    - *Year level*: Only executes if record_year is specified
  
  - **Sequential processing**: Levels execute in order (day → month → year)
    
    - *Error isolation*: Each level wrapped in _safe_process() to prevent cascading failures
    - *Independent results*: Failed levels return None without stopping other levels


- **Error Handling**:
  
  - **Level isolation**:
    
    - Each processing level runs in _safe_process() wrapper
    - Exceptions caught and logged without stopping other levels
    - Failed levels return None in results dictionary
    - Successful levels continue execution regardless of failures in other levels


  - **Processor errors**:

    - Data loading errors handled by individual processors
    - Schema validation errors logged with detailed context
    - Processing errors captured with level identification


  - **Log saving**:

    - Creates output directory if it doesn't exist
    - Catches and logs file write errors without failing the analysis
    - Uses append mode to preserve historical logs
    - Log save failures don't affect processing results

- **Processing Level Details**:

  - **Day Level Processing**
    
    ```
    Always executes (default date supported)

    - Input: `record_date` (optional)
    - Processor: `DayLevelDataProcessor`
    - Output components:

        - `processed_records`: Main production records with calculations
        - `mold_based_records`: Aggregated by mold
        - `item_based_records`: Aggregated by item
        - `summary_stats`: Statistical summaries
        - `analysis_summary`: High-level insights
    ```


  - **Month Level Processing**

    ```
    Conditional execution: Only if `record_month` provided

    Input: `record_month` (YYYY-MM), `month_analysis_date` (optional)
    Processor: `MonthLevelDataProcessor`
    Output components:

    `finished_records`: Completed orders in month
    `unfinished_records`: In-progress orders
    `analysis_summary`: Monthly performance metrics
    ```


  - **Year Level Processing**
    ```
    Conditional execution: Only if record_year provided

    Input: `record_year` (YYYY), `year_analysis_date` (optional)
    Processor: `YearLevelDataProcessor`
    Output components:

    `finished_records`: Completed orders in year
    `unfinished_records`: In-progress orders
    `analysis_summary`: Yearly trends and patterns
    ```

- **Results Structure Examples**:

    ```python
    # All levels executed successfully
    {
        "day_level_results": {
            "record_date": Timestamp('2025-11-16'),
            "processed_records": DataFrame(500 rows),
            "mold_based_records": DataFrame(50 rows),
            "item_based_records": DataFrame(30 rows),
            "summary_stats": {"total_quantity": 10000, ...},
            "analysis_summary": {"efficiency": 0.85, ...},
            "log_entries": "[2025-11-16] Processed 500 records\n"
        },
        "month_level_results": {
            "record_month": "2025-11",
            "month_analysis_date": Timestamp('2025-11-16'),
            "finished_records": DataFrame(200 rows),
            "unfinished_records": DataFrame(50 rows),
            "analysis_summary": {"completion_rate": 0.80, ...},
            "log_entries": "[2025-11] Analyzed 250 orders\n"
        },
        "year_level_results": {
            "record_year": "2025",
            "year_analysis_date": Timestamp('2025-11-16'),
            "finished_records": DataFrame(2000 rows),
            "unfinished_records": DataFrame(300 rows),
            "analysis_summary": {"annual_growth": 0.15, ...},
            "log_entries": "[2025] Processed 2300 orders\n"
        }
    }

    # Only day level executed (month/year not specified)
    {
        "day_level_results": {...},  # Successful
        "month_level_results": None,  # Not executed
        "year_level_results": None    # Not executed
    }

    # Month level failed
    {
        "day_level_results": {...},     # Successful
        "month_level_results": None,    # Failed
        "year_level_results": {...}     # Successful
    }
    ```

- **Logging Strategy**:

   -  **Class-bound logger**: Uses logger.bind(class_="MultiLevelDataAnalytics") for consistent context
   -  **Level-specific logs**: Each processor generates its own log entries
   -  **Consolidated log**: build_multi_level_performance_analyzer_log() combines all level logs
   -  **Persistent logging**: Optional append-mode file logging for audit trail
   -  **Structured messages**: Clear prefixes (✓, ✗) for success/failure indication
   -  **Hierarchical context**: Log entries maintain level identification (day/month/year)


- **Performance Characteristics**:

   -  **Execution mode**: Sequential only (no parallel processing)
   -  **Conditional overhead**: Skipped levels add negligible overhead (config check only)
   -  **Memory efficiency**: Each level processes independently, allows garbage collection between levels
   -  **Scalability**:

       -  *Day level*: Handles thousands of daily records
       -  *Month level*: Processes hundreds of orders per month
       -  *Year level*: Analyzes thousands of yearly orders

   -  **Typical runtime**: Varies by enabled levels and data volume


- **Integration Points**:
  
    - **Upstream dependencies**: 
        - **DataPipelineOrchestrator** → Provides fresh database files via [DataLoaderAgent](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dataPipelineOrchestrator/OptiMoldIQ_dataPipelineOrchestrator_overview.md)
        - **ChangeAnalyticflowConfig** → Configuration management for analysis parameters
    
    - **Parent orchestrator**:
        - **AnalyticsOrchestrator** → Invokes MultiLevelPerformanceAnalyzer as part of the analytics workflow
        - Triggered when `enable_multi_level_plotter` is enabled in DashboardBuilder
    
    - **Sub-component orchestration** (Analysis layer):
        - [DayLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_dayLevelDataProcessor_overview.md) - Processes daily production metrics
        - [MonthLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_monthLevelDataProcessor_overview.md) - Tracks monthly order progress
        - [YearLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelPerformanceAnalyzer/OptiMoldIQ_yearLevelDataProcessor_overview.md) - Analyzes yearly performance trends

    - **Downstream consumers** (Visualization layer):
        - [MultiLevelPerformancePlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/multiLevelPerformancePlotter/OptiMoldIQ_multiLevelPerformancePlotter_overview.md) → Top-level plotter coordinating multi-level performance visualizations
      - D:\OptiMoldIQ\docs\documentations\dashboardBuilder\multiLevelPerformancePlotter
            - [DayLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/multiLevelPerformancePlotter/OptiMoldIQ_dayLevelDataPlotter_overview.md) - Generate dashboard for daily production.
            - [MonthLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/multiLevelPerformancePlotter/OptiMoldIQ_monthLevelDataPlotter_overview.md) - Generate dashboard for monthly order progress.
            - [YearLevelDataPlotter](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/multiLevelPerformancePlotter/OptiMoldIQ_yearLevelDataPlotter_overview.md) - Generate dashboard for yearly performance trends.

    - **Persistence**: 
        - Component-level change logs (managed by DayLevelDataProcessor, MonthLevelDataProcessor and YearLevelDataProcessor)
        - Consolidated change log in `{multi_level_performance_analyzer_dir}/change_log.txt`
        - All changes stored in JSON/text format for audit trail and visualization consumption

- **System Integration Flow**:
     ```
                                DataPipelineOrchestrator
                                    ↓
                                DashboardBuilder
                                    ↓
                                enable_multi_level_plotter? (Yes)
                                    ↓
                                AnalyticsOrchestrator
                                    ↓
                                MultiLevelPerformanceAnalyzer ← (YOU ARE HERE)
     ┌──────────────────────────────┼───────────────────────────┐
     ↓                              ↓                           ↓
DayLevelDataProcessor     MonthLevelDataProcessor     YearLevelDataProcessor
  (analysis)                    (analysis)                 (analysis)
     ↓                              ↓                           ↓
     └──────────────────────────────┼───────────────────────────┘
                                    ↓
                        MultiLevelPerformancePlotter
                                    ↓
     ┌──────────────────────────────┼───────────────────────────┐
     ↓                              ↓                           ↓
     DayLevelDataPlotter   MonthLevelDataPlotter        YearLevelDataPlotter
        (visualization)         (visualization)            (visualization)   
     ↓                              ↓
     Daily Performance     Monthly Performance          Yearly Performance 
     dashboards            dashboards                   dashboards

- **Configuration Example**:

    ```python
    from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig

    performance_analytic_config = PerformanceAnalyticflowConfig(
        
        # Enable MultiLevelPerformanceAnalyzer components

        #--------------------------------#
        # DAY-LEVEL PERFORMANCE ANALYZER #
        #--------------------------------#

        # Trigger MultiLevelPerformanceAnalyzer-DayLevelDataProcessor if record_date is not None
        record_date="2018-11-06", # Default: None
        day_save_output = False, # Default: False

        #----------------------------------#
        # MONTH-LEVEL PERFORMANCE ANALYZER #
        #----------------------------------#

        # Trigger MultiLevelPerformanceAnalyzer-MonthLevelDataProcessor if record_month is not None
        record_month="2019-01", # Default: None
        month_analysis_date="2019-01-15", # Default: None    
        month_save_output = False, # Default: False

        #---------------------------------#
        # YEAR-LEVEL PERFORMANCE ANALYZER #
        #---------------------------------#     

        # Trigger MultiLevelPerformanceAnalyzer-YearLevelDataProcessor if record_year is not None
        record_year="2019", # Default: None
        year_analysis_date="2019-12-31", # Default: None
        year_save_output = False, # Default: False
        
        #-------------------------------------------------#
        # MULTI-LEVEL PERFORMANCE ANALYZER GENERAL CONFIG #
        #-------------------------------------------------#

        source_path = 'tests/shared_db/DataLoaderAgent/newest', # Default: 'agents/shared_db/DataLoaderAgent/newest' 
        annotation_name = "path_annotations.json", # Default: "path_annotations.json"
        databaseSchemas_path = 'database/databaseSchemas.json', # Default: 'database/databaseSchemas.json'
    
        save_multi_level_performance_analyzer_log = True, # Default: True
        multi_level_performance_analyzer_dir = "tests/shared_db/DashboardBuilder/MultiLevelPerformancePlotter", 
        #Default: "agents/shared_db/AnalyticsOrchestrator/MultiLevelPerformanceAnalyzer"
        )

    analyzer_day = MultiLevelPerformanceAnalyzer(performance_analytic_config)
    results_day, log_day = analyzer_day.data_process()

    ```