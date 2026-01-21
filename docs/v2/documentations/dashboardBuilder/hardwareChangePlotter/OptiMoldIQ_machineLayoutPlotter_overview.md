> Status: Introduced in v2  
> Purpose: Introduce analytics and visualization as first-class domains

# MachineLayoutPlotter

## Purpose

Track and visualize historical changes in machine layout configurations — i.e., which machines occupy which physical positions (machine numbers) — over time across different production shifts.

## Core Responsibilities

- Parse and clean production records containing `machineCode`, `machineNo`, `recordDate`, and `workingShift`
- Detect layout changes by comparing machine position configurations across shifts
- Build and maintain a cumulative historical layout record showing each machine's position over time
- Generate comprehensive visualizations with parallel processing support for improved performance
- Save layout records to Excel with versioned backups and maintain a change log
- Archive old visualization files to historical database while keeping latest versions accessible

## Input

- `productRecords_df`: DataFrame containing production records (must include recordDate, workingShift, machineNo, machineName, and machineCode)
- `output_dir` (optional): Output directory to store plots, Excel files, and logs (default: `agents/shared_db/UpdateHistMachineLayout`)

## Output

- **Excel file**: Pivot table showing machine positions across all detected layout change dates
- **PNG visualizations**: 
  - Individual machine layout change timeline dashboard
  - Overall machine layout change dashboard
- **Change log**: Tracking all file versions and updates with timestamps
- **Archived files**: Historical versions stored in `historical_db/` subdirectory

---

## Main Classes

### MachineLayoutPlotter

Plotter class for machine-level dashboard with visualization and reporting capabilities, including parallel processing support.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `machine_layout_hist_change_df` | pd.DataFrame | Required | Historical machine layout change data |
| `default_dir` | str | `"agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineLayoutPlotter"` | Output directory path |
| `visualization_config_path` | str | `None` | Path to visualization config JSON (auto-defaults if None) |
| `enable_parallel` | bool | `True` | Enable parallel processing for plot generation |
| `max_workers` | int | `None` | Maximum worker processes (auto-optimized if None) |

#### Required DataFrame Columns

- `machineCode`: Unique machine identifier
- `machineName`: Human-readable machine name
- `changedDate`: Date when layout changed
- `machineNo`: Physical position number
- `machineNo_numeric`: Numeric version of machine position

---

## Main Methods

### MachineLayoutPlotter Methods

| Method | Description |
|--------|-------------|
| `__init__(...)` | Initialize plotter with data validation and parallel processing configuration |
| `_setup_parallel_config()` | Auto-detect system resources and optimize worker count for plotting |
| `_prepare_data(df)` | Convert wide-format layout data to long format with date parsing |
| `plot_all(**kwargs)` | Generate all plots with parallel or sequential execution |
| `_prepare_plot_tasks(...)` | Prepare plotting tasks for parallel execution |
| `_execute_plots_parallel(tasks)` | Execute plotting tasks using ProcessPoolExecutor |
| `_execute_plots_sequential(tasks)` | Execute plotting tasks sequentially (fallback) |
| `_plot_single_chart(args)` | Static worker function to create a single plot (used by both parallel/sequential) |

### UpdateHistMachineLayout Methods

| Method | Description |
|--------|-------------|
| `update_and_plot()` | Main orchestrator: detects layout changes, updates historical records, and generates all visualizations |
| `_record_hist_layout_changes(df)` | Static method to detect layout changes by comparing machine configurations across shifts |
| `update_layout_changes()` | Iterates through detected layout changes and builds cumulative historical layout record |
| `_machine_layout_record(df, recordDate, workingShift)` | Static method to extract and pivot machine layout for a specific date and shift |
| `_update_hist_machine_layout_record(df_old, df_new)` | Static method to merge old and new layout records, preserving historical data |
| `plot_all()` | Delegates to MachineLayoutPlotter for visualization generation |

---

## Data Flow

```
Input productRecords_df 
    ↓
_record_hist_layout_changes()  # Detect all layout change points
    ↓
update_layout_changes()  # Build cumulative layout records
    ↓
_machine_layout_record() + _update_hist_machine_layout_record()
    ↓
MachineLayoutPlotter initialization  # Prepare data for visualization
    ↓
plot_all()  # Generate visualizations (parallel/sequential)
    ↓
    ├─ individual_machine_layout_change_plotter()
    └─ machine_layout_change_plotter()
    ↓
Archive old files and save new versions with timestamp
```

---

## Parallel Processing

### Auto-Optimization Logic

The plotter automatically optimizes parallel processing based on system resources:

#### CPU Core Detection
- **Single core**: Parallel processing disabled
- **Dual core (e.g., Colab)**: Uses both cores if RAM ≥ 8GB
- **Multi-core**: Uses 75% of available cores

#### Memory-Based Adjustments
- **< 4GB RAM**: Limits to 1-2 workers
- **4-8GB RAM**: Limits to 2-3 workers
- **≥ 8GB RAM**: Uses optimal worker count based on CPU

#### Smart Worker Allocation
- Never exceeds number of plotting tasks (currently 3 plot types)
- Logs system specs and chosen configuration
- Falls back to sequential processing on detection failure

### Execution Methods

1. **Parallel Execution** (`ProcessPoolExecutor`)
   - Uses separate processes for CPU-bound plotting operations
   - Collects results as they complete with detailed timing
   - Handles failures gracefully without blocking other plots

2. **Sequential Execution** (Fallback)
   - Used when parallel is disabled or only 1 worker
   - Processes plots one at a time
   - Same error handling and logging as parallel mode

---

## Layout Change Detection Logic

1. Creates unique shift keys: `YYYY-MM-DD-S{shift_number}` (e.g., `2024-11-06-S1`)
2. Generates layout strings by concatenating all machine configurations: `machineCode-machineNo-machineName|...`
3. Compares consecutive shift layout strings to detect changes
4. Records each change point with date and shift information

---

## File Management

### Directory Structure
```
output_dir/
├── newest/                    # Current versions
│   ├── YYYYMMDD_HHMM_*.png
│   └── YYYYMMDD_HHMM_*.xlsx
├── historical_db/             # Archived versions
│   ├── old_versions...
└── change_log.txt            # Version history
```

### File Naming Convention
- Format: `YYYYMMDD_HHMM_{description}.png`
- Timestamp format: `%Y%m%d_%H%M` for filenames, `%Y-%m-%d %H:%M:%S` for logs

### Versioning Process
1. Create `newest/` and `historical_db/` directories
2. Move all existing files from `newest/` to `historical_db/`
3. Save new files to `newest/` with current timestamp
4. Log all operations to `change_log.txt`

---

## Error Handling

### Comprehensive Error Management
- **Data validation**: Uses `@validate_init_dataframes` decorator to ensure required columns exist
- **File operations**: Detailed error messages for file move/save failures with proper exception raising
- **Plot generation**: Catches exceptions per plot, logs traceback, continues with other plots
- **Parallel processing**: Handles worker failures gracefully, provides detailed error reporting

### Logging System
- Uses loguru logger with class binding for context
- Logs system specs, worker configuration, and execution times
- Different emoji indicators: ✅ for success, ❌ for failures
- Tracks execution time for each plot individually

---

## Performance Optimizations

### Data Processing
- Efficient pandas operations (melt, pivot, merge)
- Single-pass data validation with decorators
- Numeric conversion for machine numbers cached in dataframe

### Visualization
- Parallel plot generation using multiprocessing
- Process pooling reduces overhead for multiple plots
- Smart worker allocation prevents resource waste
- Reuses figure configurations across similar plots

### Memory Management
- Explicit `plt.close()` after each plot to free memory
- Separate processes prevent memory leaks between plots
- RAM-aware worker count limits

---

## Special Features

### Adaptive Configuration
- **Auto resource detection**: Optimizes for Colab, local machines, servers
- **Flexible worker count**: Manually override auto-detection if needed
- **Graceful degradation**: Falls back to sequential if parallel fails

### Plot Generation
- Supports both single figure and multi-page outputs
- Proper handling of tuple vs list return types from plotters
- High-quality output (300 DPI) with proper margins

### Extensibility
- Easy to add new plot types in `_prepare_plot_tasks()`
- Configurable visualization settings via JSON config file
- Decorator-based validation for clean code