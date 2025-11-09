# YearLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive annual Purchase Order (PO) performance dashboards with year-wide analysis covering monthly trends, yearly aggregations, machine efficiency patterns, and mold utilization metrics across entire fiscal year operations.

- **Core responsibilities**: 
  
    - Process and aggregate yearly PO records through integrated data pipeline with historical trend analysis.
    - Generate 9 distinct visualization types covering `monthly performance`, `year performance`, `machine-based year view`, `mold-based year view`, and detailed month-view dashboards by field.
    - Track finished and unfinished PO status with capacity analysis and annual delivery performance.
    - Create monthly trend dashboards showing completion rates, backlog evolution, and seasonal patterns.
    - Produce machine-level year-view analysis with utilization patterns and efficiency trends across 12 months.
    - Create mold-level year-view dashboards tracking annual shot counts, cavity usage, and quality performance.
    - Generate detailed month-view dashboards for specific fields (machine/mold) with up to 10 items per page (multi-page support).
    - Manage parallel/sequential plotting execution based on system resources with optimization for 9 plot types.
    - Archive historical visualization files while maintaining latest versions with timestamp tracking.
    - Export comprehensive PO analysis data to Excel with multiple sheet perspectives.
    - Generate text-based final summary statistics for annual management review.

- **Input**:
  
    - `record_year`: Target year for analysis in `YYYY` format (string, required).
    - `analysis_date` (optional): Date of analysis execution (defaults to current date, format: `YYYY-MM-DD`).
    - `source_path` (optional): Directory containing input data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: auto-detected).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs, capped at 10).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/YearLevelDataPlotter))
  
    - Excel file: Extracted records with 5 sheets (`finished POs`, `unfinished POs`, `short unfinished summary`, `all progress`, `filtered records`).
    - TXT report: `Final summary` statistics with annual performance KPIs.
    - PNG visualizations: 9+ comprehensive dashboards (2 PO performance views, 2 year views, 5 detailed month-view series) with multi-page outputs for month-view dashboards.
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: processes PO data, generates all visualizations, saves reports, manages archiving, updates log.   |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing, capped at 10 workers.         |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (`productRecords`) from annotated paths with error handling.                             |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking and logging.                              |
| `_validate_record_year()`                 | Validates record_year format matches `YYYY` pattern using regex validation.                                              |
| `_prepare_data()`                         | Creates filtered dataframes for visualization: short unfinished summary and combined progress tracking.               |
| `_prepare_plot_tasks()`                   | Creates list of 9 plotting tasks with data tuples, functions, and output paths for parallel/sequential execution.     |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with multi-page support and timing/error handling.                   |

- **Data flow**:
  
    - Input year validation (YYYY format) → regex format check
    - `YearLevelDataProcessor` initialization with year and analysis date
    - Raw production records → PO processing pipeline → `finished`/`unfinished` DataFrames
    - productRecords_df filtering by date and year → `filtered_df` with recordMonth column
    - Data preparation → `short_unfinished_df` and `all_progress_df` creation
    - Task preparation (9 plot types) → parallel/sequential execution router
    - Visualization generation (with multi-page support for month-view dashboards) → file saving with timestamps
    - Report generation (final summary) → TXT file export
    - Excel export with 5 sheets → newest directory
    - Archive old files → historical_db migration
    - Change log update with detailed operation history

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging and optimization
    
    - **Worker Optimization for Year-Level**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems: Uses 75% of available cores (with RAM-based limits)
        - **Caps workers at 10** (number of year-level plot types) to avoid over-parallelization
        - More aggressive than month-level (10 vs 3) due to higher number of independent plots
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Handles multi-page plot outputs (saves each page separately for month-view dashboards)
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Data Processing Pipeline**:
  
    1. **YearLevelDataProcessor Integration**:
        - Initializes with record_year (YYYY) and analysis_date
        - Calls `product_record_processing()` to generate:
            - `analysis_timestamp`: Datetime of analysis execution
            - `adjusted_record_year`: Validated and adjusted year string
            - `finished_df`: Completed PO records with full annual metrics
            - `unfinished_df`: In-progress PO records with capacity analysis
            - `final_summary`: Statistical summary dictionary with annual KPIs
    
    2. **Record Filtering**:
        - Filters `productRecords_df` by `analysis_timestamp` (records before analysis date)
        - Filters by `record year` matching `adjusted_record_year`
        - Creates `filtered_df` with `recordMonth` column (`YYYY-MM` format) for monthly aggregation
        - Used for `machine-level` and `mold-level` `year-view` and `month-view` dashboards
    
    3. **Data Preparation** (`_prepare_data()`):
        - Creates `short_unfinished_df`: Subset of unfinished_df with essential columns only
        - Creates `all_progress_df`: Concatenation of finished and unfinished progress columns
        - Both used for monthly and yearly performance dashboards

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{year}`
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of file operations and timestamps
    - Supports Excel (via openpyxl), PNG, and TXT exports through unified pipeline
    - **Multi-page handling**: Automatically saves multi-page plots as separate PNG files with `_page{N}` suffix
    - Excel export contains 5 sheets with different aggregation perspectives
    - TXT report saved for management review (final summary only)
    - **Potentially generates 20+ PNG files** if all month-view dashboards have multiple pages

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Excel writing error handling with sheet-level diagnostics
    - Individual plot failure tracking with success/failure counters
    - Record year format validation with regex checking (YYYY pattern)
    - Multi-page plot handling with iteration error protection
    - Report generation failures logged as warnings (non-blocking)
    - All errors logged with timestamps and execution context

- **Multi-Page Plot Handling**:
  
    - **Monthly performance plotter** may return tuple: `(summary, [fig1, fig2, ...])`
    - **Year performance plotter** may return tuple: `(summary, [fig1, fig2, ...])`
    - **Field-based month-view plotters** return multiple pages when field has >10 unique values:
        - Example: 25 machines → 3 pages (10 + 10 + 5 machines)
        - Each page shows up to 10 items with 12 monthly subplots each
    - `_plot_single_chart()` detects list of figures and saves each as separate page
    - Page files named: `{timestamp}_{name}_{year}_page1.png`, `_page2.png`, etc.
    - Each figure closed individually after saving to prevent memory leaks
    - Enables comprehensive dashboards that can display dozens of machines/molds with monthly trends
    - All pages logged separately in change log for traceability

- **PO Status Tracking (Annual Perspective)**:
  
    - **Finished POs**: Completed production within the year, full annual metrics available
    - **Unfinished POs**: In-progress orders at end of analysis date with:
        - Capacity warnings (Critical/High/Medium/Low severity)
        - Progress tracking (completion percentage, accumulated quantity)
        - Lead time estimates (average and total)
        - Overdue flags and ETA status monitoring
        - Capacity vs. demand analysis (over capacity indicators)
    - **Monthly Progress Dashboard**: Shows completion trends across 12 months
    - **Yearly Progress Dashboard**: Cumulative view of annual performance
    - **Backlog Tracking**: Identifies carried-over orders from previous year
    - **ETA Compliance**: Monitors annual on-time delivery performance

- **Year-Level vs Month-Level Differences**:
  
    - **No Early Warning Report**: Year-level focuses on historical analysis, not immediate capacity risks
    - **Monthly Trend Analysis**: Additional monthly_performance_plotter shows seasonal patterns
    - **Yearly Aggregate View**: year_performance_plotter shows cumulative annual metrics
    - **Month-View Dashboards**: 5 additional field-based month-view dashboards (machine and mold perspectives)
    - **RecordMonth Column**: Filtered_df enriched with YYYY-MM format for monthly aggregation
    - **More Visualizations**: 9+ plot types vs 3 in month-level
    - **Higher Parallelization**: Up to 10 workers vs 3 in month-level
    - **Larger Datasets**: Full year of data vs single month
    - **Multi-page Emphasis**: Month-view dashboards designed for multi-page output (10 items per page)

- **Field-Based Month View Dashboard System**:
  
    - **Generic Plotter**: `field_based_month_view_dashboard_plotter()` supports any grouping field
    - **Current Implementations**:
        - Machine perspective: 3 dashboards (working days, PO/item, quantity)
        - Mold perspective: 2 dashboards (shots, quantity)
    - **Layout**: 12 monthly subplots per item, up to 10 items per page
    - **Extensibility**: Can easily add new field-based dashboards by adding tasks in `_prepare_plot_tasks()`
    - **Performance**: Efficient aggregation using filtered_df with recordMonth column