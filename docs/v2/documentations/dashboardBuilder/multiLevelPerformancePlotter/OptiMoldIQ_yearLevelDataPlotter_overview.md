> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# YearLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive annual Purchase Order (PO) performance dashboards with year-wide analysis covering monthly trends, yearly aggregations, machine efficiency patterns, and mold utilization metrics across entire fiscal year operations.

- **Core responsibilities**: 
  
    - Process and validate yearly PO results from multi-level analyzer.
    - Generate 9 distinct visualization types covering monthly performance, year performance, machine-based year view, mold-based year view, and detailed month-view dashboards by field.
    - Filter production records by analysis date and target year.
    - Create monthly trend dashboards showing completion rates, backlog evolution, and seasonal patterns.
    - Produce machine-level year-view analysis with utilization patterns and efficiency trends across 12 months.
    - Create mold-level year-view dashboards tracking annual shot counts, cavity usage, and quality performance.
    - Generate detailed month-view dashboards for specific fields (machine/mold) with up to 10 items per page (multi-page support).
    - Generate text-based final summary statistics for annual management review.
    - Manage parallel/sequential plotting execution based on system resources with optimization for 9 plot types.
    - Archive historical visualization files while maintaining latest versions with timestamp tracking.
    - Export comprehensive PO analysis data to Excel with multiple sheet perspectives.

- **Input**:
  
    - `year_level_results`: Dictionary containing analyzer output with keys:
        - `record_year`: Target year in YYYY format (string)
        - `year_analysis_date`: Datetime of analysis execution
        - `finished_records`: DataFrame with completed PO records
        - `unfinished_records`: DataFrame with in-progress PO records
        - `analysis_summary`: Text summary with annual statistics
    - `source_path` (optional): Directory containing base data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: `agents/dashboardBuilder/visualize_data/year_level/visualization_config.json`).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs, capped at 10).

- **Output**: 
  
    - Excel file: Extracted records with 5 sheets (finished_df, unfinished_df, short_unfinished_df, all_progress_df, filtered_records).
    - TXT report: Final summary statistics with annual performance KPIs.
    - PNG visualizations: 9+ comprehensive dashboards (2 PO performance views, 2 year views, 5 detailed month-view series) with multi-page outputs for month-view dashboards.
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.
    - Returns list of log entries documenting all file operations.
    - **Potentially generates 20+ PNG files** if all month-view dashboards have multiple pages.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: generates visualizations, saves reports, manages archiving, updates log. Returns log entries.     |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing, capped at 10 workers.         |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (productRecords) from annotated paths with error handling.                             |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking and logging.                              |
| `_prepare_data()`                         | Creates filtered dataframes for visualization: short unfinished summary and combined progress tracking.               |
| `_prepare_plot_tasks()`                   | Creates list of 9 plotting tasks with data tuples, functions, and output paths for parallel/sequential execution.     |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with multi-page support and timing/error handling.                   |

- **Data flow**:
  
    - Input validation → Extract year_level_results components
    - Load base DataFrames (productRecords_df) from annotated paths
    - Filter productRecords_df by analysis date and target year → filtered_df with recordMonth column
    - Data preparation → short_unfinished_df and all_progress_df creation
    - Create output directories (newest/ and historical_db/)
    - Archive existing files → Move old files to historical_db
    - Save Excel file with 5 sheets
    - Save TXT report (final summary)
    - Task preparation (9 plot types) → Parallel/sequential execution router
    - Visualization generation (with multi-page support) → File saving with timestamps
    - Update change log with all operations
    - Return log entries

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging and optimization
    
    - **Worker Optimization for Year-Level**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems with <4GB RAM: max(1, min(2, cores//2)) workers
        - Multi-core systems with 4-8GB RAM: max(2, min(3, cores//2)) workers
        - Multi-core systems with ≥8GB RAM: max(2, cores * 0.75) workers
        - **Caps workers at 10** (number of year-level plot types) to avoid over-parallelization
        - More aggressive than month-level (10 vs 3) due to higher number of independent plots
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Handles multi-page plot outputs (saves each page separately for month-view dashboards)
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Input Data Pipeline**:
  
    1. **Year Level Results Validation**:
        - Validates input dictionary contains all required keys using `validate_multi_level_analyzer_result()`
        - Required keys: `record_year`, `year_analysis_date`, `finished_records`, `unfinished_records`, `analysis_summary`
        - Extracts and stores each component as instance attributes
    
    2. **Base DataFrame Loading**:
        - Loads `productRecords_df` from path annotations
        - Validates file existence and accessibility
        - Applies DataFrame schema validation via `@validate_init_dataframes` decorator
        - Validates against database schema configuration
    
    3. **Record Filtering**:
        - Filters productRecords_df by conditions:
            - `recordDate < analysis_timestamp.date()` (records before analysis)
            - `recordDate.year == int(adjusted_record_year)` (same year)
        - Creates filtered_df with added `recordMonth` column (YYYY-MM format)
        - recordMonth column enables monthly aggregation for year-view and month-view dashboards
        - Used for all machine-level and mold-level visualizations
    
    4. **Data Preparation** (`_prepare_data()`):
        - Creates `short_unfinished_df`: Subset of unfinished_df with REQUIRED_UNFINISHED_SHORT_COLUMNS only
        - Creates `all_progress_df`: Concatenates finished_df and unfinished_df with REQUIRED_PROGRESS_COLUMNS
        - Both dataframes used for monthly and yearly performance dashboards
        - Returns tuple: (short_unfinished_df, all_progress_df)

- **Visualization Tasks**:
  
    The plotter generates 9 distinct visualizations with different data requirements:
    
    1. **Monthly Performance Dashboard**: `monthly_performance_plotter`
        - Input: `(short_unfinished_df, all_progress_df, record_year, analysis_timestamp)`
        - Shows monthly completion trends, backlog evolution, seasonal patterns
        - May return multiple pages for extensive data
    
    2. **Year Performance Dashboard**: `year_performance_plotter`
        - Input: `(short_unfinished_df, all_progress_df, record_year, analysis_timestamp)`
        - Cumulative annual view of PO performance metrics
        - May return multiple pages for comprehensive analysis
    
    3. **Machine-Based Year View Dashboard**: `machine_based_year_view_dashboard_plotter`
        - Input: `(filtered_df, fig_title)`
        - Aggregated machine performance across entire year
        - Single-page overview of all machines
    
    4. **Mold-Based Year View Dashboard**: `mold_based_year_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title)`
        - Metrics: totalShots, cavityNums, avgCavity, machineNums, totalNGRate
        - Aggregated mold performance across entire year
    
    5. **Machine Working Days Dashboard** (month-view): `field_based_month_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title, field='machineCode', subfig_per_page=10)`
        - Metrics: workingDays, notProgressDays, workingShifts, notProgressShifts
        - 12 monthly subplots per machine, up to 10 machines per page
    
    6. **Machine PO/Item Dashboard** (month-view): `field_based_month_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title, field='machineCode', subfig_per_page=10)`
        - Metrics: poNums, itemNums, moldNums, itemComponentNums, avgNGRate
        - Monthly trends for each machine
    
    7. **Machine Quantity Dashboard** (month-view): `field_based_month_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title, field='machineCode', subfig_per_page=10)`
        - Metrics: totalQuantity, goodQuantity, totalMoldShot
        - Production quantity trends by machine
    
    8. **Mold Shots Dashboard** (month-view): `field_based_month_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title, field='moldNo', subfig_per_page=10)`
        - Metrics: totalShots, cavityNums, avgCavity, machineNums, totalNGRate
        - Monthly shot tracking per mold
    
    9. **Mold Quantity Dashboard** (month-view): `field_based_month_view_dashboard_plotter`
        - Input: `(filtered_df, metrics_list, fig_title, field='moldNo', subfig_per_page=10)`
        - Metrics: totalQuantity, goodQuantity, totalNG
        - Production quantity trends by mold

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
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{year}`
    - File types with naming conventions:
        - Excel: `{timestamp}_extracted_records_{year}.xlsx`
        - Final summary: `{timestamp}_final_summary_{year}.txt`
        - Plots: `{timestamp}_{plotname}_{year}.png` (or `_pageN.png` for multi-page)
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history:
        - Timestamp of operation
        - Files moved to historical_db
        - Excel file saved
        - TXT report saved
        - New plots created with execution time and paths (including all pages)
    - **Multi-page handling**: Each page logged separately on new line with " - " prefix
    - Supports Excel (via openpyxl), PNG, and TXT exports through unified pipeline
    - Returns log entries as list for external tracking

- **Multi-Page Plot Handling**:
  
    - `_plot_single_chart()` can handle functions returning:
        - Single figure: Saved directly to specified path
        - Tuple `(summary, fig)`: Extracts fig, saves to path
        - Tuple `(summary, [fig1, fig2, ...])`: Multiple figures (common for year-level)
            - Iterates through list with enumerate
            - Saves each figure with `_pageN` suffix (N starts from 1)
            - Example: `20241130_1500_machine_working_days_dashboard_2024_page1.png`
    - **Common multi-page scenarios**:
        - Field-based month-view dashboards: 25 machines → 3 pages (10+10+5)
        - Monthly/yearly performance: Extensive data split across multiple pages
    - All figures closed via `plt.close()` after saving to prevent memory leaks
    - Individual timing tracked per plot task (not per page)
    - Path collection returned as list for change log
    - **Change log formatting**: Multi-page paths listed on separate lines with " - " prefix for readability

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
    - Report generation failures logged as warnings (non-blocking for final summary)
    - All errors logged with timestamps and execution context
    - Failed plots raise OSError with summary of all failures

- **PO Status Tracking (Annual Perspective)**:
  
    - **Finished POs** (finished_df):
        - Columns: poReceivedDate, poNo, poETA, itemCode, itemName, itemQuantity, itemCodeName, firstRecord, lastRecord, itemGoodQuantity, moldHistNum, moldHist, proStatus, is_backlog, itemNGQuantity, itemRemainQuantity, poStatus, overproduction_quantity, etaStatus
        - Completed production within the year
        - Used for historical analysis and annual trend comparison
    
    - **Unfinished POs** (unfinished_df):
        - All finished columns PLUS capacity analysis columns:
        - moldNum, moldList, totalItemCapacity, avgItemCapacity, accumulatedQuantity, completionProgress, totalRemainByMold, accumulatedRate, totalEstimatedLeadtime, avgEstimatedLeadtime, poOTD, poRLT, avgCumsumLT, totalCumsumLT, overTotalCapacity, overAvgCapacity, is_overdue, capacityWarning, capacitySeverity, capacityExplanation
        - In-progress orders at end of analysis date
    
    - **Progress Tracking** (all_progress_df):
        - Combined view: REQUIRED_PROGRESS_COLUMNS
        - Columns: poNo, itemCodeName, is_backlog, poStatus, poETA, itemNGQuantity, itemQuantity, itemGoodQuantity, etaStatus, proStatus, moldHistNum
        - Unified view for monthly and yearly trend analysis
    
    - **Short Unfinished Summary** (short_unfinished_df):
        - Essential monitoring columns only
        - Used for performance dashboard displays

- **Field-Based Month View Dashboard System**:
  
    - **Generic Plotter**: `field_based_month_view_dashboard_plotter()` supports any grouping field
    - **Signature**: `(filtered_df, metrics_list, fig_title, field, subfig_per_page)`
    - **Parameters**:
        - `field`: Column name to group by (e.g., 'machineCode', 'moldNo')
        - `subfig_per_page=10`: Maximum items displayed per page
        - `metrics_list`: List of metric column names to plot
    - **Current Implementations**:
        - Machine perspective: 3 dashboards (working days, PO/item, quantity)
        - Mold perspective: 2 dashboards (shots, quantity)
    - **Layout**: 12 monthly subplots per item, grid arrangement
    - **Multi-page Logic**:
        - If field has ≤10 unique values: Single page
        - If field has >10 unique values: Multiple pages (10 items each, remainder on last page)
        - Example: 25 machines → Page 1 (machines 1-10), Page 2 (machines 11-20), Page 3 (machines 21-25)
    - **Extensibility**: Can easily add new field-based dashboards by adding tasks in `_prepare_plot_tasks()`
    - **Performance**: Efficient aggregation using filtered_df with recordMonth column pre-computed

- **Year-Level vs Month-Level Differences**:
  
    - **No Early Warning Report**: Year-level focuses on historical analysis, not immediate capacity risks
    - **Monthly Trend Analysis**: Additional monthly_performance_plotter shows seasonal patterns across 12 months
    - **Yearly Aggregate View**: year_performance_plotter shows cumulative annual metrics
    - **Month-View Dashboards**: 5 additional field-based month-view dashboards (machine and mold perspectives)
    - **RecordMonth Column**: Filtered_df enriched with YYYY-MM format for monthly aggregation (critical for year-level)
    - **More Visualizations**: 9 plot types vs 3 in month-level
    - **Higher Parallelization**: Up to 10 workers vs 3 in month-level
    - **Larger Datasets**: Full year of data vs single month (performance considerations)
    - **Multi-page Emphasis**: Month-view dashboards commonly generate multiple pages (field-based pagination)
    - **Fewer Text Reports**: Only final summary (no early warning report)
    - **Different Time Filter**: Filters by year (int) vs month (YYYY-MM string)

- **Key Differences from Day Level Plotter**:
  
    - Processes PO-level data (not production records)
    - Requires productRecords_df as base DataFrame (not moldInfo_df)
    - No early warning reports (focus on historical analysis)
    - Creates progress tracking dashboards (finished vs unfinished)
    - Exports 5 Excel sheets (vs 4 in potential day level Excel export)
    - 9 plots vs 8 plots in day level
    - Handles multi-page plot outputs extensively
    - More comprehensive report generation (final summary)
    - Focused on PO completion and annual trend analysis
    - Filters productRecords by date and year (additional filtering step)
    - RecordMonth aggregation for monthly trend visualization