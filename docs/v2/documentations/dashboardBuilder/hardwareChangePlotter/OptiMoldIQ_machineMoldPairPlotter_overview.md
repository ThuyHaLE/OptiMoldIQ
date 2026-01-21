# UpdateHistMoldOverview

## Purpose

Analyze and visualize comprehensive mold usage patterns, including machine-mold compatibility, tonnage matching, acquisition timing, and historical pairing relationships across the production system.

## Core Responsibilities

- Merge production records with mold specifications and machine information to create unified analysis dataset
- Validate tonnage compatibility between molds and machines they run on
- Track mold acquisition dates and analyze time gaps until first production use
- Generate machine-mold pairing matrices showing first-run dates for all combinations
- Analyze tonnage variety per mold (how many different machine types each mold has run on)
- Create comprehensive visualizations with parallel processing support for improved performance
- Save analysis results to Excel with versioned backups and maintain a change log
- Archive old visualization files to historical database while keeping latest versions accessible

## Input

- `productRecords_df`: DataFrame containing production records (must include recordDate, machineCode, and moldNo)
- `moldInfo_df`: DataFrame with mold specifications (must include moldNo, machineTonnage, acquisitionDate)
- `machineInfo_df`: DataFrame with machine specifications (must include machineCode, machineName)
- `output_dir` (optional): Output directory to store plots, Excel files, and logs (default: `agents/shared_db/UpdateHistMoldOverview`)

## Output

- **Excel files**: 
  - Tonnage mismatches report
  - Machine-mold pairing matrices (bidirectional)
- **PNG visualizations**: 
  - Mold utilization dashboard (acquisition timing analysis)
  - Mold-machine first pairing dashboard (compatibility matrices)
  - Machine tonnage-based mold utilization dashboard (usage patterns)
- **Change log**: Tracking all file versions and updates with timestamps
- **Archived files**: Historical versions stored in `historical_db/` subdirectory

---

## Main Classes

### MachineMoldPairPlotter

Plotter class for mold-level dashboard with visualization and reporting capabilities, including parallel processing support.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `first_mold_usage` | pd.DataFrame | Required | First usage data for each mold (acquisition timing) |
| `first_paired_mold_machine` | pd.DataFrame | Required | First pairing dates for mold-machine combinations |
| `mold_tonnage_summary` | pd.DataFrame | Required | Tonnage variety summary per mold |
| `default_dir` | str | `"agents/shared_db/DashboardBuilder/HardwareChangePlotter/MachineMoldPairPlotter"` | Output directory path |
| `visualization_config_path` | str | `None` | Path to visualization config JSON (auto-defaults if None) |
| `enable_parallel` | bool | `True` | Enable parallel processing for plot generation |
| `max_workers` | int | `None` | Maximum worker processes (auto-optimized if None) |

#### Required DataFrame Columns

**first_mold_usage**:
- `moldNo`: Unique mold identifier
- `acquisitionDate`: Date when mold was acquired
- `firstDate`: Date of first production use
- `daysDifference`: Gap between acquisition and first use

**first_paired_mold_machine**:
- `firstDate`: Date of first pairing
- `machineCode`: Machine identifier
- `moldNo`: Mold identifier
- `acquisitionDate`: Mold acquisition date

**mold_tonnage_summary**:
- `moldNo`: Mold identifier
- `usedMachineTonnage`: List of machine tonnages used
- `usedTonnageCount`: Number of different tonnages

---

## Main Methods

### MachineMoldPairPlotter Methods

| Method | Description |
|--------|-------------|
| `__init__(...)` | Initialize plotter with data validation and parallel processing configuration |
| `_setup_parallel_config()` | Auto-detect system resources and optimize worker count for plotting |
| `plot_all(**kwargs)` | Generate all plots with parallel or sequential execution |
| `_prepare_plot_tasks(...)` | Prepare plotting tasks for parallel execution (3 dashboard types) |
| `_execute_plots_parallel(tasks)` | Execute plotting tasks using ProcessPoolExecutor |
| `_execute_plots_sequential(tasks)` | Execute plotting tasks sequentially (fallback) |
| `_plot_single_chart(args)` | Static worker function to create a single plot (used by both parallel/sequential) |

### UpdateHistMoldOverview Methods

| Method | Description |
|--------|-------------|
| `update_and_plot()` | Main orchestrator: processes all data and generates complete set of visualizations and exports |
| `process_data()` | Core data processing pipeline: merges datasets, validates tonnage matching, calculates statistics, creates pivots |
| `save_outputs()` | Manages file versioning, archiving, and saves all visualizations and Excel exports with timestamps |
| `plot_top_molds_tonnage(...)` | Static method to visualize top N molds that run on the most different machine tonnage types |
| `plot_bottom_molds_tonnage(...)` | Static method to visualize bottom N molds with least tonnage variety (highlights single-tonnage molds) |
| `plot_tonnage_distribution(...)` | Static method to create histogram showing distribution of tonnage variety across all molds |
| `plot_tonnage_proportion_pie(...)` | Static method to create pie chart showing proportional breakdown of molds by tonnage variety |
| `compare_acquisition_firstuse(...)` | Static method to create scatter plot comparing acquisition dates vs. first use dates for all molds |
| `timegap_acquisition_firstuse(...)` | Static method to visualize distribution of time gaps between mold acquisition and first production use |
| `top_bot_mold_gaptime_analysis(...)` | Static method to create dual bar charts showing molds with longest and shortest acquisition-to-use gaps |
| `machine_level_mold_count(...)` | Static method to visualize number of unique molds that have run on each machine (first-run counts) |

---

## Data Flow

```
Input DataFrames (productRecords, moldInfo, machineInfo)
    ↓
Merge on moldNo and machineCode
    ↓
process_data()  # Core processing pipeline
    ↓
    ├─ Tonnage validation (_check_match)
    ├─ Statistical summaries (console logging)
    ├─ Pivot table generation (bidirectional matrices)
    └─ Data structure creation (5 key DataFrames)
    ↓
MachineMoldPairPlotter initialization  # Prepare 3 datasets
    ↓
plot_all()  # Generate visualizations (parallel/sequential)
    ↓
    ├─ mold_utilization_plotter()
    ├─ mold_machine_first_pairing_plotter()
    └─ machine_ton_based_mold_utilization_plotter()
    ↓
save_outputs()  # Archive & save with timestamp
    ↓
Excel exports + PNG files + change_log.txt update
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
- Never exceeds number of plotting tasks (currently 3 dashboard types)
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

## Tonnage Matching Logic

1. **Extract tonnage from machineCode**: Parse numeric value (e.g., "MC150" → "150")
2. **Parse suitedMachineTonnages**: Split by "/" delimiter to get compatible list
3. **Compatibility check**: Verify if any compatible tonnage appears in machine code
4. **Boolean flag**: Create `tonnageMatched` column for validation
5. **Export mismatches**: Save all incompatible records to Excel for quality review

---

## Statistical Analysis

### Tonnage Variety Statistics
- Total molds analyzed
- Average tonnage types per mold
- Max/Min/Median tonnage variety
- Standard deviation of tonnage usage

### Acquisition Timing Statistics
- Total molds with timing data
- Average days between acquisition and first use
- Median gap time
- Standard deviation of gap times
- Min/Max gap durations
- Warning detection for negative gaps (data quality issues)

---

## Data Structures Generated

### 1. mold_machine_df
Unified dataset combining production, mold, and machine information:
- **Columns**: recordDate, machineCode, moldNo, suitedMachineTonnages, acquisitionDate, machineType, tonnageMatched
- **Purpose**: Basis for all subsequent analysis

### 2. first_use_mold_df
First production date for each mold:
- **Columns**: moldNo, acquisitionDate, firstDate, daysDifference
- **Purpose**: Timing analysis (acquisition → first use)
- **Input to**: `mold_utilization_plotter()`

### 3. paired_mold_machine_df
First occurrence date for each unique (machineCode, moldNo) pair:
- **Columns**: machineCode, moldNo, firstDate, acquisitionDate
- **Purpose**: Foundation for pairing matrices
- **Input to**: `mold_machine_first_pairing_plotter()`

### 4. used_mold_machine_df
Summary of machine types each mold has run on:
- **Columns**: moldNo, usedMachineTonnage (list), usedTonnageCount (int)
- **Purpose**: Tonnage variety analysis
- **Input to**: `machine_ton_based_mold_utilization_plotter()`

### 5. pivot_machine_mold
Machine-centric pairing matrix:
- **Rows**: machineCode
- **Columns**: moldNo
- **Values**: first-run dates
- **Purpose**: Shows which molds have run on which machines

### 6. pivot_mold_machine
Mold-centric pairing matrix:
- **Rows**: moldNo
- **Columns**: machineCode
- **Values**: first-run dates
- **Purpose**: Inverse perspective of machine-mold relationships

---

## File Management

### Directory Structure
```
output_dir/
├── newest/                    # Current versions
│   ├── YYYYMMDD_HHMM_Mold_utilization_dashboard.png
│   ├── YYYYMMDD_HHMM_Mold_machine_first_pairing_dashboard.png
│   ├── YYYYMMDD_HHMM_Machine_tonage_based_mold_utilization_dashboard.png
│   └── YYYYMMDD_HHMM_*.xlsx
├── historical_db/             # Archived versions
│   └── old_versions...
└── change_log.txt             # Version history
```

### File Naming Convention
- **Format**: `YYYYMMDD_HHMM_{description}.png` or `.xlsx`
- **Timestamp format**: 
  - Filenames: `%Y%m%d_%H%M`
  - Log entries: `%Y-%m-%d %H:%M:%S`

### Versioning Process
1. Create `newest/` and `historical_db/` directories
2. Move all existing files from `newest/` to `historical_db/`
3. Save new files to `newest/` with current timestamp
4. Log all operations to `change_log.txt`

---

## Error Handling

### Comprehensive Error Management
- **Data validation**: Uses `@validate_init_dataframes` decorator to ensure required columns exist for all 3 input DataFrames
- **File operations**: Detailed error messages for file move/save failures with proper exception raising
- **Plot generation**: Catches exceptions per plot, logs traceback, continues with other plots
- **Parallel processing**: Handles worker failures gracefully, provides detailed error reporting
- **Tonnage matching**: Try-except blocks for malformed tonnage data

### Logging System
- Uses loguru logger with class binding for context
- Logs system specs, worker configuration, and execution times
- Different emoji indicators: ✅ for success, ❌ for failures
- Tracks execution time for each plot individually
- Logs statistical summaries to console

---

## Data Quality Checks

- **Negative time gaps**: Automatically detects molds used before acquisition
- **Tonnage validation**: Checks compatibility across all records
- **Mismatch export**: Saves incompatible records for manual review
- **Duplicate removal**: Cleans machine-mold pairs before analysis
- **Missing data handling**: Gracefully handles malformed tonnage fields

---

## Performance Optimizations

### Data Processing
- Efficient pandas groupby and aggregation operations
- Vectorized tonnage matching (lambda with apply)
- Optimized pivot table creation for large datasets
- Method chaining to minimize redundant operations

### Visualization
- Parallel plot generation using multiprocessing
- Process pooling reduces overhead for multiple plots
- Smart worker allocation prevents resource waste
- Reuses color palettes across similar plots

### Memory Management
- Explicit `plt.close()` after each plot to free memory
- Separate processes prevent memory leaks between plots
- RAM-aware worker count limits

---

## Special Features

### Flexible Tonnage Matching
- Handles multi-tonnage molds (e.g., "150/200/250")
- String-based matching for robustness
- Exports mismatches for quality review

### Bidirectional Analysis
- Creates both machine→mold and mold→machine perspectives
- Enables comprehensive relationship exploration

### Statistical Depth
- Comprehensive metrics: mean, median, std, min, max
- Console logging of key statistics
- Quality indicators embedded in visualizations

### Visual Consistency
- Uniform styling across all dashboards
- High-quality output (300 DPI)
- Proper margins and spacing (pad_inches=0.5)

### Adaptive Configuration
- Auto resource detection for optimal performance
- Flexible worker count with manual override
- Graceful degradation to sequential processing

### Extensibility
- Easy to add new dashboard types in `_prepare_plot_tasks()`
- Configurable visualization settings via JSON config file
- Decorator-based validation for clean code

---

## Dashboard Types

### 1. Mold Utilization Dashboard
**Function**: `mold_utilization_plotter()`  
**Input**: `first_mold_usage` DataFrame  
**Visualizations**:
- Scatter plot: Acquisition date vs. first use date
- Histogram: Distribution of time gaps
- Bar charts: Top/bottom molds by gap duration

### 2. Mold-Machine First Pairing Dashboard
**Function**: `mold_machine_first_pairing_plotter()`  
**Input**: `first_paired_mold_machine` DataFrame  
**Visualizations**:
- Heatmap: First pairing dates matrix
- Bar chart: Number of unique molds per machine
- Timeline: Pairing chronology

### 3. Machine Tonnage-Based Mold Utilization Dashboard
**Function**: `machine_ton_based_mold_utilization_plotter()`  
**Input**: `mold_tonnage_summary` DataFrame  
**Visualizations**:
- Bar chart: Top molds by tonnage variety
- Bar chart: Bottom molds (single-tonnage)
- Histogram: Tonnage variety distribution
- Pie chart: Proportional breakdown