# DayLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive daily production analysis dashboards with multiple visualization perspectives, combining machine-level, shift-level, mold-level, and item-level performance metrics into a unified reporting system.

- **Core responsibilities**:
  
    - Process and aggregate daily production records through integrated data pipeline.
    - Generate 8 distinct visualization types covering yield efficiency, mold analysis, and operational metrics.
    - Create mold-based, item-based, and machine-based analytical views from raw production data.
    - Manage parallel/sequential plotting execution based on system resources.
    - Archive historical visualization files while maintaining latest versions.
    - Track all file operations and updates through detailed change logging.
    - Export processed records and summary statistics to Excel with timestamp versioning.

- **Input**:
  
    - `selected_date`: Target date for analysis (string format).
    - `source_path` (optional): Directory containing input data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: auto-detected).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dashboardBuilder/DayLevelDataPlotter))
  
    - Excel file: Extracted records with 4 sheets (selected date filter, mold-based records, item-based records, summary statistics).
    - PNG visualizations: 8 different plots covering change times, yield efficiency, mold analysis, and overview dashboards.
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: processes data, generates all visualizations, manages file archiving, and updates change log.     |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing settings automatically.        |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (moldInfo) from annotated paths with error handling.                                   |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking.                                          |
| `_prepare_plot_tasks()`                   | Creates list of plotting tasks with data, functions, and output paths for parallel/sequential execution.              |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with timing and error handling (used by parallel executor).          |

- **Data flow**:
  
    - Input date selection → `DayLevelDataProcessor` initialization
    - Raw production records → processing pipeline → 3 aggregated DataFrames (`processed_df`, `mold_based_record_df`, `item_based_record_df`)
    - Summary statistics generation → console logging
    - Base DataFrames loading (`moldInfo_df`) → merge operations
    - Task preparation → parallel/sequential execution router
    - Visualization generation → file saving with timestamps
    - Archive old files → save new versions → update change log

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging
    
    - **Worker Optimization**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems: Uses 75% of available cores (with RAM-based limits)
        - Caps workers at number of plots (8) to avoid over-parallelization
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Data Processing Pipeline**:
  
    1. **DayLevelDataProcessor Integration**:
        - Initializes with selected date and data paths
        - Calls `product_record_processing()` to generate:
            - `processed_df`: Detailed production records for selected date
            - `mold_based_record_df`: Aggregated by mold number
            - `item_based_record_df`: Aggregated by item code
            - `summary_stats`: Statistical summary dictionary
    
    2. **Base DataFrame Loading**:
        - Loads `moldInfo_df` from annotated path
        - Validates file existence and accessibility
        - Performs schema validation against database configuration
    
    3. **Plotting Data Preparation**:
        - Prepares data tuples for each visualization function
        - Bundles visualization config paths with each task
        - Creates output file paths with timestamp and date suffix

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{date}`
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of file operations and timestamps
    - Supports both Excel (via openpyxl) and PNG exports through unified pipeline
    - Each Excel export contains multiple sheets with different data aggregation levels

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Excel writing error handling with sheet-level diagnostics
    - Individual plot failure tracking with success/failure counters
    - All errors logged with timestamps and execution context