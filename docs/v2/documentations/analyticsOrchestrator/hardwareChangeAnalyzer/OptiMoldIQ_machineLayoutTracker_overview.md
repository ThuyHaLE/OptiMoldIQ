# MachineLayoutTracker

## Purpose

Track machine layout changes over time in a manufacturing environment, including machine additions, removals, relocations, and code changes.

## Core Responsibilities

- **Data Processing**: Prepare and validate production records with machine layout information
- **Change Detection**: Identify layout changes across time periods (by date and shift)
- **Historical Tracking**: Maintain versioned history of all layout configurations
- **Change Analysis**: Generate detailed reports on specific machine changes between versions
- **Persistence**: Save/load layout history with automatic versioning and archival

## Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `productRecords_df` | `pd.DataFrame` | Production records with columns: `recordDate`, `workingShift`, `machineNo`, `machineCode` |
| `databaseSchemas_path` | `str` | Path to database schema JSON (default: `'database/databaseSchemas.json'`) |
| `output_dir` | `str` | Directory for storing layout change files (default: `'agents/shared_db/HardwareChangeAnalyzer/MachineLayoutTracker'`) |
| `change_log_name` | `str` | Name of change log file (default: `"change_log.txt"`) |

**DataFrame Schema Validation**: Uses `@validate_init_dataframes` decorator to ensure `productRecords_df` matches the schema defined in `databaseSchemas.json` under `dynamicDB.productRecords.dtypes`.

## Output

### File Structure
```
output_dir/
├── change_log.txt                          # Timestamped log of all operations
├── newest/                                 # Current version files
│   ├── YYYYMMDD_HHMM_machine_layout_changes_YYYY-MM-DD.json
│   └── YYYYMMDD_HHMM_machine_layout_changes_YYYY-MM-DD.xlsx
└── historical_db/                          # Archived previous versions
    ├── [previous version files]
    └── ...
```

### JSON Output Format
```json
{
  "2023-10-01T00:00:00": {
    "M001": "MC01",
    "M002": "MC02"
  },
  "2023-12-15T00:00:00": {
    "M001": "MC03",
    "M002": "MC02",
    "M003": "MC04"
  }
}
```

### Excel Output Format
Single sheet `machineLayoutChange` with pivoted layout history:

| 2023-10-01 | 2023-12-15 | ... | machineName | machineCode |
|------------|------------|-----|-------------|-------------|
| M001       | M003       | ... | MC          | MC01        |
| M002       | M002       | ... | MC          | MC02        |
| -          | M004       | ... | MC          | MC04        |

## Main Methods

### Public Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `data_process(record_date)` | `(bool, pd.DataFrame, list)` | Main entry point: checks for changes, saves files if detected, updates logs. Returns `(has_change, machine_layout_hist_change, log_entries)` |
| `load_layout_changes()` | `Optional[Dict]` | Loads most recent layout changes JSON from `newest/` directory |
| `check_new_layout_change(new_record_date)` | `(str, bool, Dict)` | Compares current layout at date with stored history. Returns `(date_str, has_change, layout_dict)` |
| `detect_all_layout_changes()` | `Dict[str, Dict[str, str]]` | Scans entire DataFrame to find all unique layout configurations |
| `get_layout_summary(layout_changes_dict)` | `pd.DataFrame` | Generates summary with date, machine count, and layout signature hash |
| `detect_machine_changes(layout_changes_dict)` | `pd.DataFrame` | Produces detailed change report: added/removed machines and code changes between versions |
| `record_machine_layout_hist_change()` | `pd.DataFrame` | Generates pivoted historical layout table across all detected change points |

### Private Helper Methods

| Method | Description |
|--------|-------------|
| `_prepare_data()` | Adds `machineInfo` column (format: `machineNo-machineCode`), ensures datetime types |
| `_get_layout_at_date(target_date)` | Returns snapshot of active machines at specific date (last known state per machine) |
| `_layouts_different(layout1, layout2)` | Compares two layout dictionaries for equality |
| `_record_layout_change_info(df)` | **Static method**: Detects layout changes by shift, returns dict of change points with `recordDate` and `workingShift` |
| `_pivot_machine_layout_record(df, recordDate, workingShift)` | **Static method**: Creates pivoted layout DataFrame for specific date/shift |
| `_update_hist_machine_layout_record(df_old, df_new)` | **Static method**: Merges old and new layout DataFrames, preferring new data |

## Data Flow
```
productRecords_df
    ↓
┌─────────────────────────────────────────┐
│ data_process(record_date)               │
│   ├─ check_new_layout_change()          │
│   │    ├─ load_layout_changes()         │
│   │    ├─ _get_layout_at_date()         │
│   │    └─ _layouts_different()          │
│   │                                     │
│   └─ if has_change:                     │
│        ├─ Move old files to historical/ │
│        ├─ Save JSON (layout dict)       │
│        ├─ record_machine_layout_hist_   │
│        │  change()                      │
│        │    ├─ _record_layout_change_   │
│        │    │  info()                   │
│        │    ├─ _pivot_machine_layout_   │
│        │    │  record()                 │
│        │    └─ _update_hist_machine_    │
│        │       layout_record()          │
│        ├─ Save Excel (pivoted history)  │
│        └─ Update change_log.txt         │
└─────────────────────────────────────────┘
    ↓
Returns: (has_change, DataFrame, log_entries)
```

## Key Features

### Automatic Versioning
- New detections automatically move old files to `historical_db/`
- Timestamped filenames: `YYYYMMDD_HHMM_machine_layout_changes_YYYY-MM-DD.[json|xlsx]`
- Change log maintains audit trail of all operations

### Shift-Level Granularity
- Layout changes detected per `recordDate` + `workingShift` combination
- Layout string format: `machineCode-machineNo-machineName|...` (sorted by machineCode)
- Only stores change points (not every shift)

### Historical Layout Reconstruction
The `record_machine_layout_hist_change()` method builds a comprehensive view:
1. Identifies all layout change points using `_record_layout_change_info()`
2. Creates pivoted snapshot for each change point
3. Merges snapshots chronologically, filling forward machine positions

## Error Handling

All file operations wrapped in try-except blocks with:
- **Logger error messages** for debugging
- **OSError exceptions** raised with descriptive messages
- **JSON validation** on load (returns `None` if invalid)
- **File move failures** logged and raised immediately

## Example Usage
```python
from MachineLayoutTracker import MachineLayoutTracker
import pandas as pd

# Initialize with production records
tracker = MachineLayoutTracker(
    productRecords_df=production_df,
    output_dir='output/layouts'
)

# Process new data
latest_date = pd.Timestamp('2024-03-15')
has_change, layout_df, logs = tracker.data_process(latest_date)

if has_change:
    print("New layout detected!")
    print(layout_df)  # Pivoted historical layout
    
# Get summary of all changes
layout_dict = tracker.load_layout_changes()
summary = tracker.get_layout_summary(layout_dict)
changes = tracker.detect_machine_changes(layout_dict)
```

## Change Detection Logic

**Layout Change Criteria**: A layout change is detected when the set of `{machineNo: machineCode}` mappings differs between time periods.

**Examples of detected changes**:
- Machine M001 moves from position MC01 → MC03
- New machine M004 added at position MC04  
- Machine M002 removed entirely
- Machine renamed (same position, different code)

**Not detected as changes**:
- Production volume changes
- Different products on same machine
- Shift changes without physical layout modification

## Dependencies

- `pandas`: DataFrame operations and Excel export
- `loguru`: Structured logging
- `json`: Layout persistence
- `shutil`: File archival
- `pathlib`: Cross-platform path handling
- Custom: `agents.decorators.validate_init_dataframes`, `agents.utils.{read_change_log, load_annotation_path}`