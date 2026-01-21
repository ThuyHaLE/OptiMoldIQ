# DayLevelDataPlotter

- **Purpose**:
  
    - Generate comprehensive daily production analysis dashboards with multiple visualization perspectives, combining machine-level, shift-level, mold-level, and item-level performance metrics into a unified reporting system.

- **Core responsibilities**:
  
    - Process and validate daily production results from multi-level analyzer.
    - Generate 8 distinct visualization types covering yield efficiency, mold analysis, and operational metrics.
    - Manage parallel/sequential plotting execution based on system resources.
    - Archive historical visualization files while maintaining latest versions.
    - Track all file operations and updates through detailed change logging.

- **Input**:
  
    - `day_level_results`: Dictionary containing analyzer output with keys:
        - `record_date`: Target date for analysis
        - `processed_records`: DataFrame with detailed production records
        - `mold_based_records`: DataFrame aggregated by mold number
        - `item_based_records`: DataFrame aggregated by item code
        - `summary_stats`: Dictionary of statistical summaries
        - `analysis_summary`: Analysis summary information
    - `source_path` (optional): Directory containing base data files (default: `agents/shared_db/DataLoaderAgent/newest`).
    - `annotation_name` (optional): JSON file mapping data paths (default: `path_annotations.json`).
    - `databaseSchemas_path` (optional): Database schema configuration file (default: `database/databaseSchemas.json`).
    - `default_dir` (optional): Base output directory (default: `agents/shared_db/DashboardBuilder/MultiLevelPerformancePlotter`).
    - `visualization_config_path` (optional): Visualization styling configuration (default: `agents/dashboardBuilder/visualize_data/day_level/visualization_config.json`).
    - `enable_parallel` (optional): Enable parallel plotting (default: `True`).
    - `max_workers` (optional): Maximum parallel workers (default: auto-detected from system specs).

- **Output**: 
  
    - PNG visualizations: 8 different plots covering change times, yield efficiency, mold analysis, and overview dashboards.
    - Change log tracking all file versions and operations with timestamps.
    - Archived historical versions in `historical_db/` subdirectory.
    - Returns list of log entries documenting all file operations.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `plot_all()`                              | Main orchestrator: generates all visualizations, manages file archiving, and updates change log. Returns log entries.     |
| `_setup_parallel_config()`                | Analyzes system resources (CPU cores, RAM) and configures optimal parallel processing settings automatically.        |
| `_setup_schemas()`                        | Loads database schema configuration for column validation and data integrity checks.                                   |
| `_load_base_dataframes()`                 | Loads required base DataFrames (moldInfo) from annotated paths with error handling.                                   |
| `_load_single_dataframe()`                | Helper method to load individual DataFrame with comprehensive error checking.                                          |
| `_prepare_plot_tasks()`                   | Creates list of plotting tasks with data, functions, and output paths for parallel/sequential execution.              |
| `_execute_plots_parallel()`               | Executes plotting tasks using ProcessPoolExecutor with concurrent futures and progress tracking.                      |
| `_execute_plots_sequential()`             | Fallback method for sequential plot generation when parallel processing is disabled or fails.                          |
| `_plot_single_chart()`                    | Static worker function to create individual plot with timing and error handling (used by parallel executor).          |

- **Data flow**:
  
    - Input validation → Extract day_level_results components
    - Load base DataFrames (`moldInfo_df`) from annotated paths
    - Create output directories (`newest/` and `historical_db/`)
    - Archive existing files → Move old files to historical_db
    - Task preparation → Parallel/sequential execution router
    - Visualization generation → File saving with timestamps
    - Update change log with all operations
    - Return log entries

- **Parallel Processing Logic**:
  
    - **System Detection**:
        - Automatically detects CPU cores using `multiprocessing.cpu_count()`
        - Measures available RAM using `psutil.virtual_memory()`
        - Logs system specifications for debugging
    
    - **Worker Optimization**:
        - Single-core systems: Parallel disabled, 1 worker
        - Dual-core (Colab-style): 2 workers if RAM ≥ 8GB, else 1 worker
        - Multi-core systems with <4GB RAM: max(1, min(2, cores//2)) workers
        - Multi-core systems with 4-8GB RAM: max(2, min(3, cores//2)) workers
        - Multi-core systems with ≥8GB RAM: max(2, cores * 0.75) workers
        - Caps workers at number of plots (8) to avoid over-parallelization
    
    - **Execution Strategy**:
        - Uses `ProcessPoolExecutor` for CPU-bound matplotlib operations
        - Submits all tasks via `concurrent.futures` with future tracking
        - Collects results as completed with individual timing metrics
        - Graceful fallback to sequential processing on errors
        - Comprehensive error handling and logging for each worker

- **Input Data Pipeline**:
  
    1. **Day Level Results Validation**:
        - Validates input dictionary contains all required keys using `validate_multi_level_analyzer_result()`
        - Required keys: `record_date`, `processed_records`, `mold_based_records`, `item_based_records`, `summary_stats`, `analysis_summary`
        - Extracts and stores each component as instance attributes
    
    2. **Base DataFrame Loading**:
        - Loads `moldInfo_df` from path annotations
        - Validates file existence and accessibility
        - Applies DataFrame schema validation via `@validate_init_dataframes` decorator
        - Validates against database schema configuration
    
    3. **Plotting Data Preparation**:
        - Prepares data tuples for each visualization function
        - Bundles visualization config paths with each task
        - Creates output file paths with timestamp and date suffix

- **Visualization Tasks**:
  
    The plotter generates 8 distinct visualizations:
    
    1. **Change Times (All Types)**: `change_times_all_types_plotter`
        - Input: `processed_df`
        - Shows timing analysis for different change types
    
    2. **Item-Based Overview Dashboard**: `item_based_overview_plotter`
        - Input: `item_based_record_df`
        - Aggregated view by item code
    
    3. **Machine-Level Yield Efficiency**: `machine_level_yield_efficiency_plotter`
        - Input: `processed_df`
        - Machine performance metrics
    
    4. **Machine-Level Mold Analysis**: `machine_level_mold_analysis_plotter`
        - Input: `processed_df`
        - Mold usage and efficiency by machine
    
    5. **Shift-Level Yield Efficiency**: `shift_level_yield_efficiency_plotter`
        - Input: `processed_df`
        - Shift comparison of yield metrics
    
    6. **Shift-Level Detailed Yield Efficiency**: `shift_level_detailed_yield_efficiency_plotter`
        - Input: `processed_df`
        - Detailed shift-level breakdown
    
    7. **Mold-Based Overview Dashboard**: `mold_based_overview_plotter`
        - Input: `mold_based_record_df`
        - Aggregated view by mold number
    
    8. **Shift-Level Mold Efficiency**: `shift_level_mold_efficiency_plotter`
        - Input: `(processed_df, moldInfo_df)` tuple
        - Combined analysis using multiple DataFrames

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}_{date}.png`
    - Before saving new files, moves ALL existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of file operations and timestamps
    - Each log entry includes:
        - Timestamp of operation
        - Files moved to historical_db
        - New plots created with execution time
        - Absolute file paths
    - Returns log entries as list for external tracking

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger with class binding
    - Input validation via `validate_multi_level_analyzer_result()` with required keys check
    - Schema validation via `@validate_init_dataframes` decorator
    - Exception handling in parallel worker functions with traceback capture
    - Graceful fallback from parallel to sequential execution on worker failures
    - File operation error handling with descriptive context messages (OSError)
    - DataFrame loading validation with FileNotFoundError for missing paths
    - Individual plot failure tracking with success/failure counters
    - All errors logged with timestamps and execution context
    - Failed plots raise OSError with summary of all failures

- **Key Differences from External Interfaces**:
  
    - Does NOT process raw production data (expects pre-processed results)
    - Does NOT export to Excel (removed from this class)
    - Does NOT contain `DayLevelDataProcessor` (expects processed input)
    - Only handles visualization generation and file management
    - Focuses on plotting orchestration and parallel execution
    - Lighter weight with single responsibility: visualization