# UpdateHistMoldOverview

- **Purpose**:
  
    - Analyze and visualize comprehensive mold usage patterns, including machine-mold compatibility, tonnage matching, acquisition timing, and historical pairing relationships across the production system.

- **Core responsibilities**:
  
    - Merge production records with mold specifications and machine information to create unified analysis dataset.
    - Validate tonnage compatibility between molds and machines they run on.
    - Track mold acquisition dates and analyze time gaps until first production use.
    - Generate machine-mold pairing matrices showing first-run dates for all combinations.
    - Analyze tonnage variety per mold (how many different machine types each mold has run on).
    - Create comprehensive visualizations covering compatibility issues, timing analysis, and usage patterns.
    - Save analysis results to Excel with versioned backups and maintain a change log.
    - Archive old visualization files to historical database while keeping latest versions accessible.

- **Input**:
  
    - `productRecords_df`: DataFrame containing production records (must include recordDate, machineCode, and moldNo).
    - `moldInfo_df`: DataFrame with mold specifications (must include moldNo, machineTonnage, acquisitionDate).
    - `machineInfo_df`: DataFrame with machine specifications (must include machineCode, machineName).
    - `output_dir` (optional): Output directory to store plots, Excel files, and logs (default: `agents/shared_db/UpdateHistMoldOverview`).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dataChangeAnalyzer/UpdateHistMoldOverview))
  
    - Excel files: Tonnage mismatches, machine-mold pairing matrices (bidirectional).
    - PNG visualizations: 10 different plots covering acquisition timing, tonnage analysis, and usage patterns.
    - Change log tracking all file versions and updates.
    - Archived historical versions of all outputs in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `update_and_plot()`                       | Main orchestrator: processes all data and generates complete set of visualizations and exports.                        |
| `process_data()`                          | Core data processing pipeline: merges datasets, validates tonnage matching, calculates statistics, creates pivots.    |
| `save_outputs()`                          | Manages file versioning, archiving, and saves all visualizations and Excel exports with timestamps.                    |
| `plot_top_molds_tonnage(...)`             | Static method to visualize top N molds that run on the most different machine tonnage types.                          |
| `plot_bottom_molds_tonnage(...)`          | Static method to visualize bottom N molds with least tonnage variety (highlights single-tonnage molds).               |
| `plot_tonnage_distribution(...)`          | Static method to create histogram showing distribution of tonnage variety across all molds.                           |
| `plot_tonnage_proportion_pie(...)`        | Static method to create pie chart showing proportional breakdown of molds by tonnage variety.                         |
| `compare_acquisition_firstuse(...)`       | Static method to create scatter plot comparing acquisition dates vs. first use dates for all molds.                   |
| `timegap_acquisition_firstuse(...)`       | Static method to visualize distribution of time gaps between mold acquisition and first production use.               |
| `top_bot_mold_gaptime_analysis(...)`      | Static method to create dual bar charts showing molds with longest and shortest acquisition-to-use gaps.              |
| `machine_level_mold_count(...)`           | Static method to visualize number of unique molds that have run on each machine (first-run counts).                   |

- **Data flow**:
  
    - Input DataFrames → merge on moldNo and machineCode → `process_data()`
    - Tonnage validation → `_check_match()` helper function
    - Statistical summaries → console logging with detailed metrics
    - Pivot table generation → bidirectional machine-mold matrices
    - Visualization generation → `save_outputs()` → individual plot methods
    - Archive old files and save new versions with timestamp

- **Tonnage Matching Logic**:
  
    - Extracts tonnage values from `machineCode` (e.g., "MC150" contains tonnage "150")
    - Splits `suitedMachineTonnages` field by "/" delimiter to get list of compatible tonnages
    - Checks if any compatible tonnage value appears in the machine code string
    - Creates boolean `tonnageMatched` column for compatibility validation
    - Exports all mismatched records to Excel for quality review

- **Statistical Analysis**:
  
    1. **Tonnage Variety Statistics**:
        - Total molds analyzed
        - Average tonnage types per mold
        - Max/Min/Median tonnage variety
        - Standard deviation of tonnage usage
    
    2. **Acquisition Timing Statistics**:
        - Total molds with timing data
        - Average days between acquisition and first use
        - Median gap time
        - Standard deviation of gap times
        - Min/Max gap durations
        - Warning detection for negative gaps (data quality issues)

- **Data Structures Generated**:
  
    1. **mold_machine_df**: 
        - Unified dataset with columns: recordDate, machineCode, moldNo, suitedMachineTonnages, acquisitionDate, machineType, tonnageMatched
        - Basis for all subsequent analysis
    
    2. **first_use_mold_df**:
        - Shows first production date for each mold
        - Includes acquisition date and calculated gap (daysDifference)
        - Used for timing analysis
    
    3. **paired_mold_machine_df**:
        - Records first occurrence date for each unique (machineCode, moldNo) pair
        - Foundation for pairing matrices
    
    4. **used_mold_machine_df**:
        - Summary showing which machine types each mold has run on
        - Includes `usedMachineTonnage` (list) and `usedTonnageCount` (integer)
    
    5. **pivot_machine_mold**:
        - Rows: machineCode, Columns: moldNo, Values: first-run dates
        - Shows which molds have run on which machines
    
    6. **pivot_mold_machine**:
        - Rows: moldNo, Columns: machineCode, Values: first-run dates
        - Inverse perspective of machine-mold relationships

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}`
    - Before saving new files, moves existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of all file operations
    - Supports both Excel and PNG exports through unified pipeline

- **Error handling**:
  
    - Comprehensive logging at each processing step using loguru logger
    - Graceful handling of file move operations with detailed error messages
    - Exception handling for tonnage matching with try-except blocks
    - Data quality warnings for negative time gaps (molds used before acquisition)
    - Validates merge operations between multiple DataFrames
    - All errors are logged with context and raised with descriptive messages

- **Data Quality Checks**:
  
    - Automatically detects and logs molds with negative time gaps (data inconsistencies)
    - Validates tonnage matching compatibility across all records
    - Exports mismatched records for manual review
    - Removes duplicate machine-mold pairs before analysis
    - Handles missing or malformed tonnage data gracefully

- **Performance optimizations**:
  
    - Uses efficient pandas groupby and aggregation operations
    - Generates color palette once and reuses across all plots
    - Vectorized operations for tonnage matching (lambda with apply)
    - Optimized pivot table creation for large datasets
    - Minimizes redundant DataFrame operations through method chaining

- **Special features**:
  
    - **Flexible tonnage matching**: Handles multi-tonnage molds (e.g., "150/200/250")
    - **Bidirectional analysis**: Creates both machine→mold and mold→machine perspectives
    - **Statistical depth**: Comprehensive metrics with mean, median, std, min, max
    - **Visual consistency**: Uniform styling across all 8 visualizations
    - **Quality indicators**: Red highlights for anomalies (single-tonnage molds, mismatches)
    - **Reference lines**: Contextual markers (10-mold threshold, mean/median lines)
    - **Configurable parameters**: Top/bottom N values, figure sizes, bin counts all adjustable