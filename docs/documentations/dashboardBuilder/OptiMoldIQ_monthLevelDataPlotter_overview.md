# MonthLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive monthly Purchase Order (PO) performance dashboards with multi-dimensional analysis covering production progress, capacity warnings, machine efficiency, and mold utilization across entire month of operations.

- **Core responsibilities**:
  
    - Process and aggregate monthly PO records through integrated data pipeline with early warning system.
    - Generate 3 distinct visualization types covering month performance, machine-based metrics, and mold-based analytics.
    - Track finished and unfinished PO status with capacity analysis and delivery risk assessment.
    - Create progress tracking dashboards showing completion rates, backlog status, and ETA compliance.
    - Generate machine-level performance reports with yield, efficiency, and utilization metrics.
    - Produce mold-level analysis dashboards tracking shot counts, cavity usage, and quality performance.
    - Manage parallel/sequential plotting execution based on system resources with Colab optimization.
    - Archive historical visualization files while maintaining latest versions with timestamp tracking.
    - Export comprehensive PO analysis data to Excel with multiple sheet perspectives.
    - Generate text-based early warning reports and final summary statistics for management review.

- **Input**:
  
    - `record_month`: Target month for analysis in YYYY-MM format (string, required).
    - `analysis_date` (optional): Date of analysis execution (defaults to current date, format: YYYY-MM-DD).
    - `source_path` (optional): Directory containing input data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: auto-detected).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/MonthLevelDataPlotter))
  
    - Excel file: Extracted records with 5 sheets (finished POs, unfinished POs, short unfinished summary, all progress, filtered records).
    - TXT reports: Final summary statistics and early warning report with capacity alerts.
    - PNG visualizations: 3 comprehensive dashboards (month performance, machine-based, mold-based).
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: processes PO data, generates all visualizations, saves reports, manages archiving, updates log.   |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing for month-level tasks.         |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (productRecords) from annotated paths with error handling.                             |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking and logging.                              |
| `_validate_record_month()`                | Validates record_month format matches YYYY-MM pattern using regex validation.                                          |
| `_prepare_data()`                         | Creates filtered dataframes for visualization: short unfinished summary and combined progress tracking.               |
| `_prepare_plot_tasks()`                   | Creates list of plotting tasks with data tuples, functions, and output paths for parallel/sequential execution.       |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with multi-page support and timing/error handling.                   |

- **Data flow**:
  
    - Input month validation (YYYY-MM format) → format check
    - `MonthLevelDataProcessor` initialization with month and analysis date
    - Raw production records → PO processing pipeline → finished/unfinished DataFrames
    - Capacity analysis → early warning report generation
    - productRecords_df filtering by date and month → filtered_df
    - Data preparation → short_unfinished_df and all_progress_df creation
    - Task preparation → parallel/sequential execution router
    - Visualization generation → file saving with timestamps
    - Report generation (final summary + early warning) → TXT file exports
    - Excel export with 5 sheets → newest directory
    - Archive old files → historical_db migration
    - Change log update with detailed operation history

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging and optimization
    
    - **Worker Optimization for Month-Level**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems: Uses 75% of available cores (with RAM-based limits)
        - **Caps workers at 3** (number of month-level plots) to avoid over-parallelization
        - More conservative than day-level due to heavier computational load per plot
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Handles multi-page plot outputs (saves each page separately)
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Data Processing Pipeline**:
  
    1. **MonthLevelDataProcessor Integration**:
        - Initializes with record_month (YYYY-MM) and analysis_date
        - Calls `product_record_processing()` to generate:
            - `analysis_timestamp`: Datetime of analysis execution
            - `adjusted_record_month`: Validated and adjusted month string
            - `finished_df`: Completed PO records with full metrics
            - `unfinished_df`: In-progress PO records with capacity warnings
            - `final_summary`: Statistical summary dictionary with KPIs
    
    2. **Early Warning Report Generation**:
        - Calls `generate_early_warning_report()` with unfinished_df
        - Analyzes capacity risks, overdue POs, and delivery threats
        - Generates formatted text report with severity classifications
        - Uses non-colored output for text file compatibility
    
    3. **Record Filtering**:
        - Filters productRecords_df by analysis_timestamp (records before analysis date)
        - Filters by record_month matching adjusted_record_month
        - Creates filtered_df with recordMonth column for aggregation
        - Used for machine-level and mold-level dashboard generation
    
    4. **Data Preparation** (`_prepare_data()`):
        - Creates `short_unfinished_df`: Subset of unfinished_df with essential columns only
        - Creates `all_progress_df`: Concatenation of finished and unfinished progress columns
        - Both used for month performance dashboard visualization
    
- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{month}`
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of file operations and timestamps
    - Supports Excel (via openpyxl), PNG, and TXT exports through unified pipeline
    - Excel export contains 5 sheets with different aggregation perspectives
    - TXT reports saved for easy management review and email distribution

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Excel writing error handling with sheet-level diagnostics
    - Individual plot failure tracking with success/failure counters
    - Record month format validation with regex checking (YYYY-MM pattern)
    - Multi-page plot handling with iteration error protection
    - Report generation failures logged as warnings (non-blocking)
    - All errors logged with timestamps and execution context

- **PO Status Tracking**:
  
    - **Finished POs**: Completed production, full metrics available, archived for reference
    - **Unfinished POs**: In-progress orders with:
        - Capacity warnings (Critical/High/Medium/Low severity)
        - Progress tracking (completion percentage, accumulated quantity)
        - Lead time estimates (average and total)
        - Overdue flags and ETA status monitoring
        - Capacity vs. demand analysis (over capacity indicators)
    - **Progress Dashboard**: Unified view combining both finished and unfinished for trend analysis
    - **Backlog Tracking**: Identifies carried-over orders from previous periods
    - **ETA Compliance**: Monitors on-time delivery performance against promised dates

- **Early Warning System**:
  
    - Analyzes unfinished_df for capacity risks
    - Severity classifications: Critical, High, Medium, Low
    - Risk factors:
        - Overdue POs (passed ETA without completion)
        - Over-capacity demand (exceeds available mold capacity)
        - Insufficient lead time (estimated completion after ETA)
        - Low completion progress (behind schedule)
    - Generates actionable report with:
        - PO identification and current status
        - Specific risk explanation
        - Recommended actions or priority escalation
    - Enables proactive production planning and resource allocation