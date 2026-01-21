> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# MonthLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive monthly Purchase Order (PO) performance dashboards with multi-dimensional analysis covering production progress, capacity warnings, machine efficiency, and mold utilization across entire month of operations.

- **Core responsibilities**:
  
    - Process and validate monthly PO results from multi-level analyzer.
    - Generate 3 distinct visualization types covering month performance, machine-based metrics, and mold-based analytics.
    - Filter production records by analysis date and target month.
    - Create progress tracking dashboards showing completion rates, backlog status, and ETA compliance.
    - Generate machine-level performance reports with yield, efficiency, and utilization metrics.
    - Produce mold-level analysis dashboards tracking shot counts, cavity usage, and quality performance.
    - Generate text-based early warning reports and final summary statistics for management review.
    - Manage parallel/sequential plotting execution based on system resources with Colab optimization.
    - Archive historical visualization files while maintaining latest versions with timestamp tracking.
    - Export comprehensive PO analysis data to Excel with multiple sheet perspectives.

- **Input**:
  
    - `month_level_results`: Dictionary containing analyzer output with keys:
        - `record_month`: Target month in YYYY-MM format
        - `month_analysis_date`: Datetime of analysis execution
        - `finished_records`: DataFrame with completed PO records
        - `unfinished_records`: DataFrame with in-progress PO records
        - `analysis_summary`: Text summary with statistics
    - `source_path` (optional): Directory containing base data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: `agents/dashboardBuilder/visualize_data/month_level/visualization_config.json`).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs).

- **Output**: 
  
    - Excel file: Extracted records with 5 sheets (finished_df, unfinished_df, short_unfinished_df, all_progress_df, filtered_records).
    - TXT reports: Final summary statistics and early warning report with capacity alerts.
    - PNG visualizations: 3 comprehensive dashboards (month performance, machine-based, mold-based).
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.
    - Returns list of log entries documenting all file operations.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: generates visualizations, saves reports, manages archiving, updates log. Returns log entries.      |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing for month-level tasks.         |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (productRecords) from annotated paths with error handling.                             |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking and logging.                              |
| `_prepare_data()`                         | Creates filtered dataframes for visualization: short unfinished summary and combined progress tracking.               |
| `_prepare_plot_tasks()`                   | Creates list of plotting tasks with data tuples, functions, and output paths for parallel/sequential execution.       |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with multi-page support and timing/error handling.                   |

- **Data flow**:
  
    - Input validation → Extract month_level_results components
    - Generate early warning report from unfinished_df
    - Load base DataFrames (productRecords_df) from annotated paths
    - Filter productRecords_df by analysis date and target month → filtered_df
    - Data preparation → short_unfinished_df and all_progress_df creation
    - Create output directories (newest/ and historical_db/)
    - Archive existing files → Move old files to historical_db
    - Save Excel file with 5 sheets
    - Save TXT reports (final summary + early warning)
    - Task preparation → Parallel/sequential execution router
    - Visualization generation → File saving with timestamps
    - Update change log with all operations
    - Return log entries

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging and optimization
    
    - **Worker Optimization for Month-Level**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems with <4GB RAM: max(1, min(2, cores//2)) workers
        - Multi-core systems with 4-8GB RAM: max(2, min(3, cores//2)) workers
        - Multi-core systems with ≥8GB RAM: max(2, cores * 0.75) workers
        - **Caps workers at 3** (number of month-level plots) to avoid over-parallelization
        - More conservative than day-level due to heavier computational load per plot
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Handles multi-page plot outputs (saves each page separately with _pageN suffix)
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Input Data Pipeline**:
  
    1. **Month Level Results Validation**:
        - Validates input dictionary contains all required keys using `validate_multi_level_analyzer_result()`
        - Required keys: `record_month`, `month_analysis_date`, `finished_records`, `unfinished_records`, `analysis_summary`
        - Extracts and stores each component as instance attributes
    
    2. **Early Warning Report Generation**:
        - Calls `generate_early_warning_report()` with unfinished_df immediately after validation
        - Analyzes capacity risks, overdue POs, and delivery threats
        - Generates formatted text report with severity classifications
        - Uses non-colored output (colored=False) for text file compatibility
        - Stored as `self.early_warning_report` for later export
    
    3. **Base DataFrame Loading**:
        - Loads `productRecords_df` from path annotations
        - Validates file existence and accessibility
        - Applies DataFrame schema validation via `@validate_init_dataframes` decorator
        - Validates against database schema configuration
    
    4. **Record Filtering**:
        - Filters productRecords_df by conditions:
            - `recordDate < analysis_timestamp.date()` (records before analysis)
            - `recordDate month == adjusted_record_month` (same month)
        - Creates filtered_df with added `recordMonth` column
        - Used for machine-level and mold-level dashboard generation
    
    5. **Data Preparation** (`_prepare_data()`):
        - Creates `short_unfinished_df`: Subset of unfinished_df with REQUIRED_UNFINISHED_SHORT_COLUMNS only
        - Creates `all_progress_df`: Concatenates finished_df and unfinished_df with REQUIRED_PROGRESS_COLUMNS
        - Both dataframes used for month performance dashboard visualization
        - Returns tuple: (short_unfinished_df, all_progress_df)

- **Visualization Tasks**:
  
    The plotter generates 3 distinct visualizations with different data requirements:
    
    1. **Month Performance Dashboard**: `month_performance_plotter`
        - Input: `(short_unfinished_df, all_progress_df, fig_title)`
        - Shows PO completion progress, backlog status, ETA compliance
        - Tracks finished vs unfinished POs with status breakdown
    
    2. **Machine-Based Dashboard**: `machine_based_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title)`
        - Metrics: totalQuantity, goodQuantity, totalMoldShot, avgNGRate, workingDays, notProgressDays, workingShifts, notProgressShifts, poNums, itemNums, itemComponentNums
        - Analyzes machine-level efficiency and utilization
    
    3. **Mold-Based Dashboard**: `mold_based_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title)`
        - Metrics: totalShots, cavityNums, avgCavity, machineNums, totalQuantity, goodQuantity, totalNG, totalNGRate
        - Tracks mold performance and quality metrics

- **Schema Validation**:
  
    Uses dual `@validate_init_dataframes` decorators for comprehensive validation:
    
    1. **Base DataFrame Validation** (First decorator):
        - Validates `productRecords_df` against database schema
        - Schema loaded from `databaseSchemas.json`
        - Checks all required columns from `dynamicDB.productRecords.dtypes`
    
    2. **Derived DataFrame Validation** (Second decorator):
        - Validates `finished_df` against REQUIRED_FINISHED_COLUMNS
        - Validates `unfinished_df` against REQUIRED_UNFINISHED_COLUMNS
        - Validates `short_unfinished_df` against REQUIRED_UNFINISHED_SHORT_COLUMNS
        - Validates `all_progress_df` against REQUIRED_PROGRESS_COLUMNS
        - Ensures data integrity throughout processing pipeline

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{month}`
    - File types with naming conventions:
        - Excel: `{timestamp}_extracted_records_{month}.xlsx`
        - Final summary: `{timestamp}_final_summary_{month}.txt`
        - Early warning: `{timestamp}_early_warning_report_{month}.txt`
        - Plots: `{timestamp}_{plotname}_{month}.png` (or `_pageN.png` for multi-page)
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history:
        - Timestamp of operation
        - Files moved to historical_db
        - Excel file saved
        - TXT reports saved
        - New plots created with execution time and path
    - Supports Excel (via openpyxl), PNG, and TXT exports through unified pipeline
    - Returns log entries as list for external tracking

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Input validation via `validate_multi_level_analyzer_result()` with required keys check
    - Dual schema validation via `@validate_init_dataframes` decorators
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages (OSError for critical operations)
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Excel writing error handling with sheet-level diagnostics
    - Individual plot failure tracking with success/failure counters
    - Multi-page plot iteration with exception protection
    - Report generation failures logged as warnings (non-blocking for summary and early warning reports)
    - All errors logged with timestamps and execution context
    - Failed plots raise OSError with summary of all failures

- **PO Status Tracking**:
  
    - **Finished POs** (finished_df):
        - Columns: poReceivedDate, poNo, poETA, itemCode, itemName, itemQuantity, itemCodeName, firstRecord, lastRecord, itemGoodQuantity, moldHistNum, moldHist, proStatus, is_backlog, itemNGQuantity, itemRemainQuantity, poStatus, overproduction_quantity, etaStatus
        - Completed production, full metrics available
        - Used for historical analysis and trend comparison
    
    - **Unfinished POs** (unfinished_df):
        - All finished columns PLUS capacity analysis columns:
        - moldNum, moldList, totalItemCapacity, avgItemCapacity, accumulatedQuantity, completionProgress, totalRemainByMold, accumulatedRate, totalEstimatedLeadtime, avgEstimatedLeadtime, poOTD, poRLT, avgCumsumLT, totalCumsumLT, overTotalCapacity, overAvgCapacity, is_overdue, capacityWarning, capacitySeverity, capacityExplanation
        - In-progress orders with real-time tracking
    
    - **Progress Tracking** (all_progress_df):
        - Combined view: REQUIRED_PROGRESS_COLUMNS
        - Columns: poNo, itemCodeName, is_backlog, poStatus, poETA, itemNGQuantity, itemQuantity, itemGoodQuantity, etaStatus, proStatus, moldHistNum
        - Unified view for trend analysis across finished and unfinished
    
    - **Short Unfinished Summary** (short_unfinished_df):
        - Essential monitoring columns only
        - Used for dashboard display without overwhelming detail

- **Early Warning System**:
  
    - Generated by `generate_early_warning_report()` function
    - Input: unfinished_df, record_month, analysis_timestamp
    - Output: Formatted text report string
    - Analyzes unfinished_df for capacity risks:
        - **Severity classifications**: Critical, High, Medium, Low
        - **Risk factors**:
            - Overdue POs (is_overdue flag, passed ETA)
            - Over-capacity demand (overTotalCapacity, overAvgCapacity flags)
            - Capacity warnings (capacityWarning field)
            - Low completion progress (completionProgress percentage)
        - **Report sections**:
            - PO identification (poNo, itemCodeName)
            - Current status (completion progress, accumulated quantity)
            - Specific risk explanation (capacityExplanation field)
            - Severity level and recommended actions
    - Saved as TXT file for easy email distribution
    - Non-blocking: Failures logged as warnings, don't stop execution

- **Key Differences from Day Level Plotter**:
  
    - Processes PO-level data (not production records)
    - Requires productRecords_df as base DataFrame (not moldInfo_df)
    - Generates early warning reports (not in day level)
    - Creates progress tracking dashboards (finished vs unfinished)
    - Exports 5 Excel sheets (vs 4 in day level)
    - Only 3 plots vs 8 plots in day level
    - Handles multi-page plot outputs
    - More text report generation (final summary + early warning)
    - Focused on PO completion and capacity management
    - Filters productRecords by date and month (additional filtering step)