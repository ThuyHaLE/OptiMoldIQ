# UpdateHistMachineLayout

- **Purpose**:
  
    - Track and visualize historical changes in machine layout configurations — i.e., which machines occupy which physical positions (machine numbers) — over time across different production shifts.

- **Core responsibilities**:
  
    - Parse and clean production records containing `machineCode`, `machineNo`, `recordDate`, and `workingShift`.
    - Detect layout changes by comparing machine position configurations across shifts.
    - Build and maintain a cumulative historical layout record showing each machine's position over time.
    - Generate comprehensive visualizations (timeline plots, top changers, individual machine details).
    - Save layout records to Excel with versioned backups and maintain a change log.
    - Archive old visualization files to historical database while keeping latest versions accessible.

- **Input**:
  
    - `productRecords_df`: DataFrame containing production records (must include recordDate, workingShift, machineNo, machineName, and machineCode).
    - `output_dir` (optional): Output directory to store plots, Excel files, and logs (default: `agents/shared_db/UpdateHistMachineLayout`).

- **Output**: ([→ see overviews](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/agents_output_overviews/dataChangeAnalyzer/UpdateHistMachineLayout))
  
    - Excel file: Pivot table showing machine positions across all detected layout change dates.
    - PNG visualizations: Timeline chart, top changers bar chart, and individual machine detail plots.
    - Change log tracking all file versions and updates.
    - Archived historical versions of all outputs in `historical_db/` subdirectory.

- **Main Methods**:
  
| Method                                              | Description                                                                                                     |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `update_and_plot()`                                 | Main orchestrator: detects layout changes, updates historical records, and generates all visualizations.        |
| `_record_hist_layout_changes(df)`                   | Static method to detect layout changes by comparing machine configurations across shifts.                       |
| `update_layout_changes()`                           | Iterates through detected layout changes and builds cumulative historical layout record.                        |
| `_machine_layout_record(df, recordDate, workingShift)` | Static method to extract and pivot machine layout for a specific date and shift.                             |
| `_update_hist_machine_layout_record(df_old, df_new)` | Static method to merge old and new layout records, preserving historical data while updating with new info.   |
| `plot_all()`                                        | Generates and saves all visualizations: timeline, top changers, individual machine details, and Excel export.   |
| `_plot_machine_timeline(...)`                       | Static method to create timeline visualization showing all machines' position changes over time.                |
| `_plot_top_changes(...)`                            | Static method to create bar chart showing machines with most frequent layout changes.                           |
| `_plot_individual_machines(...)`                    | Static method to create detailed subplot grid showing each machine's layout change history individually.        |

- **Data flow**:
  
    - Input `productRecords_df` → `_record_hist_layout_changes()`
    - Detect all layout change points → `update_layout_changes()`
    - Build cumulative layout records → `_machine_layout_record()` + `_update_hist_machine_layout_record()`
    - Generate visualizations → `plot_all()` → `_plot_machine_timeline()`, `_plot_top_changes()`, `_plot_individual_machines()`
    - Archive old files and save new versions with timestamp

- **Layout Change Detection Logic**:
  
    - Creates unique shift keys in format: `YYYY-MM-DD-S{shift_number}` (e.g., `2024-11-06-S1`)
    - Generates layout strings by concatenating all machine configurations per shift: `machineCode-machineNo-machineName|...`
    - Compares consecutive shift layout strings to detect changes
    - Records each change point with its date and shift information

- **Example Historical Layout Record** (Excel format):
  
```
| 2024-11-06 | 2024-11-15 | 2025-01-20 | machineName | machineCode |
|------------|------------|------------|-------------|-------------|
| NO.01      | NO.01      | NO.03      | MC          | MC01        |
| NO.02      | NO.05      | NO.05      | MC          | MC02        |
| NO.03      | NO.03      | NO.01      | MC          | MC03        |
```
→ Shows `MC01` moved from position `01` to `03`, `MC02` moved from `02` to `05`, and `MC03` moved from `03` to `01` over time.

- **Visualization Outputs**:
  
    1. **Machine_change_layout_timeline.png**: 
        - Timeline plot showing all machines' position changes
        - Color-coded by machine with legend
        - Adaptive layout for large machine counts (up to multi-column legends)
        - Y-axis shows all machine numbers, X-axis shows dates
    
    2. **Top_machine_change_layout.png**:
        - Bar chart of top 15 machines with most layout changes
        - Includes statistics: total changes and average changes per machine
        - Color-coded bars for visual distinction
    
    3. **Machine_level_change_layout_details.png**:
        - Grid of individual subplots (one per machine)
        - Shows detailed change timeline for each machine
        - Highlights machines exceeding change threshold (≥5 changes) with red borders
        - Adaptive grid layout: max 2 columns for readability
        - Annotated data points showing machine number at each change
    
    4. **Machine_level_change_layout_pivot.xlsx**:
        - Complete pivot table of all layout records
        - Rows: machine codes
        - Columns: change dates + machine metadata

- **File Management**:
  
    - Creates two subdirectories: `newest/` for current versions, `historical_db/` for archives
    - Timestamps all files in format: `YYYYMMDD_HHMM_{filename}`
    - Before saving new files, moves existing files from `newest/` to `historical_db/`
    - Maintains `change_log.txt` with detailed history of all file operations

- **Error handling**:
  
    - Comprehensive logging at each step using loguru logger
    - Graceful handling of file move operations with detailed error messages
    - Validates data preprocessing steps (date conversion, duplicate removal)
    - Raises descriptive exceptions on plot creation or file export failures
    - All errors are logged with context for debugging

- **Performance optimizations**:
  
    - Uses efficient pandas operations for data manipulation (groupby, pivot, merge)
    - Generates color palette once and reuses across all plots
    - Optimizes plot layouts based on machine count (adaptive columns/grid sizing)
    - Reduces Y-axis label font size for dense machine number displays
    - Implements smart legend handling for large datasets (multi-column when needed)

- **Special features**:
  
    - Automatic machine name extraction from machine codes using regex pattern
    - Configurable change threshold for highlighting high-change machines
    - Adaptive subplot sizing based on total machine count
    - Smart annotation positioning to avoid overlaps in dense plots
    - Statistical summaries embedded in visualizations