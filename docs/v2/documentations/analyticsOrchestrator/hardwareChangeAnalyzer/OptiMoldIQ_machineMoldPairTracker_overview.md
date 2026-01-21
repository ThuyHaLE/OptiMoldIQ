# MachineMoldPairTracker

##  Purpose
  
- Track machine-mold pairing changes over time in a manufacturing environment, analyzing which molds are used on which machines and monitoring tonnage compatibility.

## Core responsibilities
  
- **Data Processing**: Prepare and validate production records with machine-mold pairing information
- **Pair Detection**: Identify new machine-mold combinations across time periods
- **Historical Tracking**: Maintain versioned history of all pairing configurations
- **Compatibility Analysis**: Verify mold tonnage requirements match machine capabilities
- **Usage Analysis**: Track mold acquisition dates, first use dates, and utilization patterns
- **Persistence**: Save/load pairing history with automatic versioning and archival

## Input
  
| **Parameter** | **Type** | **Description** |
|-----------|------|-------------|
| `productRecords_df` | pd.DataFrame | Production records with columns: recordDate, machineCode, moldNo |
| `moldInfo_df` | pd.DataFrame | Mold specifications with columns: moldNo, machineTonnage, acquisitionDate |
| `machineInfo_df` | pd.DataFrame | Machine specifications with columns: machineCode, machineName |
| `databaseSchemas_path` | pd.DataFrame | Path to database schema JSON (default: 'database/databaseSchemas.json') |
| `output_dir` | pd.DataFrame | Directory for storing pairing change files (default: 'agents/shared_db/HardwareChangeAnalyzer/MachineMoldPairTracker') |
| `change_log_name` | pd.DataFrame | Name of change log file (default: 'change_log.txt') |

- **DataFrame Schema Validation**: Uses @validate_init_dataframes decorator to ensure DataFrames match schemas defined in databaseSchemas.json:
  
  - `productRecords_df` → dynamicDB.productRecords.dtypes
  - `moldInfo_df` → staticDB.moldInfo.dtypes
  - `machineInfo_df` → staticDB.machineInfo.dtypes

## Output

- **File Structure**

  ```python
  output_dir/
  ├── change_log.txt                          # Timestamped log of all operations
  ├── newest/                                 # Current version files
  │   ├── pair_changes/                       # Individual pairing change files
  │   │   ├── YYYY-MM-DD_mold_machine_pairing_YYYY-MM-DD.json
  │   │   └── ...
  │   ├── YYYYMMDD_HHMM_mold_machine_pairing_YYYY-MM-DD.xlsx
  │   └── YYYYMMDD_HHMM_mold_machine_pairing_summary_YYYY-MM-DD.txt
  └── historical_db/                          # Archived previous versions
      ├── [previous version files]
      └── pair_changes/                       # Archived pairing files
  ```

- **JSON Output Format** (per change date) 

  ```json
  {
    "MOLD001": ["MC01", "MC02"],
    "MOLD002": ["MC03"],
    "MOLD003": ["MC01", "MC04", "MC05"]
  }
  ```
  
  *Format: `{moldNo: [list of machineCodes that use this mold]}`*

- **Excel Output Format**: Three sheets:
    
  - **1. moldTonageUnmatched**: Molds used on incompatible machines

  | recordDate | machineCode | moldNo | suitedMachineTonnages | acquisitionDate | machineType | tonnageMatched |
  |------------|-------------|--------|----------------------|-----------------|-------------|----------------|
  | 2024-01-15 | MC250       | M001   | 150/200              | 2023-12-01      | MC          | False          |

  - **2. machineMoldFirstRunPair**: Pivot table (machines × molds)

  |             | MOLD001    | MOLD002    | MOLD003    |
  |-------------|------------|------------|------------|
  | **MC01**    | 2024-01-10 | NaN        | 2024-02-15 |
  | **MC02**    | 2024-01-12 | 2024-01-20 | NaN        |

  - **3. moldMachineFirstRunPair**: Pivot table (molds × machines)

  |             | MC01       | MC02       | MC03       |
  |-------------|------------|------------|------------|
  | **MOLD001** | 2024-01-10 | 2024-01-12 | NaN        |
  | **MOLD002** | NaN        | 2024-01-20 | 2024-01-18 |

- **Text Summary Output Format**: 

  ```
  ================================================================================
  MOLD ANALYSIS SUMMARY REPORT
  ================================================================================

  1. MOLD TONNAGE SUMMARY STATISTICS
  --------------------------------------------------------------------------------
    Total Molds: 45
    Average Tonnage Types per Mold: 2.34
    Max Tonnage Types: 5
    Min Tonnage Types: 1
    Median Tonnage Types: 2.00
    Standard Deviation: 0.87

  1. FIRST USE ANALYSIS STATISTICS
  --------------------------------------------------------------------------------
    Total Molds Analyzed: 45
    Average Days Between Acquisition and First Use: 12.45
    Median Days Between Acquisition and First Use: 8.00
    Standard Deviation: 15.23
    Min Gap (days): -5.00
    Max Gap (days): 67.00

  1. DATA QUALITY WARNINGS
  --------------------------------------------------------------------------------
    WARNING: 2 mold(s) have negative gap (used before acquisition)
    Affected Molds: MOLD023, MOLD031

  ================================================================================
  ```

## Main Methods

- **Public Methods**

| Method | Returns | Description |
|--------|---------|-------------|
| `data_process(record_date)` | `(bool, DataFrame, DataFrame, DataFrame, list)` | Main entry point: checks for new pairs, saves files if detected, updates logs. Returns `(has_change, mold_tonnage_summary_df, first_mold_usage_df, first_paired_mold_machine_df, log_entries)` |
| `check_new_pairs(new_record_date)` | `(str, bool, Set, Dict)` | Compares current pairs at date with stored history. Returns `(date_str, has_change, new_pairs_set, machine_molds_dict)` |
| `detect_all_machine_molds()` | `Dict[str, Dict[str, List[str]]]` | Scans entire DataFrame to find all unique pairing configurations at each change point |
| `load_machine_molds()` | `Optional[Dict]` | Loads most recent pairing changes JSON from `newest/pair_changes/` directory |
| `get_latest_mapping(machine_molds_dict)` | `Dict[str, List[str]]` | Extracts the most recent mold→machines mapping from history dictionary |
| `get_summary(machine_molds_dict)` | `pd.DataFrame` | Generates summary with date, machine count, total pairs, and average molds per machine |

- **Private Helper Methods**

| Method | Description |
|--------|-------------|
| `_prepare_data()` | Ensures `recordDate` column is datetime type |
| `_get_machine_molds_at_date(target_date)` | Returns snapshot of mold→machines mapping at specific date (all historical pairs up to that date) |
| `_extract_all_pairs(machine_molds_dict)` | Extracts all unique (mold, machine) tuples from complete history dictionary |
| `_extract_latest_pairs(machine_molds_dict)` | Extracts unique (mold, machine) tuples from latest mapping only |
| `_analyze_mold_machined_summary()` | Performs comprehensive analysis: tonnage matching, usage summaries, first pairing dates |
| `_check_tonnage_match(machineCode, suitedMachineTonnages)` | **Static method**: Verifies if machine tonnage matches mold requirements |
| `_generate_analyzed_results_summary(mold_tonnage_summary_df, first_mold_usage_df)` | **Static method**: Generates formatted text report with statistics and warnings |
| `_create_mold_tonnage_summary(mold_machine_df)` | **Static method**: Aggregates unique machine types used per mold |
| `_analyze_first_usage(mold_machine_df)` | **Static method**: Calculates first use date and gap from acquisition for each mold |
| `_create_first_paired_data(mold_machine_df)` | **Static method**: Creates DataFrame of first pairing dates for each machine-mold combination |

## Data Flow
  
```
productRecords_df + moldInfo_df + machineInfo_df
    ↓
┌───────────────────────────────────────────────┐
│ data_process(record_date)                     │
│   ├─ check_new_pairs()                        │
│   │    ├─ load_machine_molds()                │
│   │    ├─ _get_machine_molds_at_date()        │
│   │    ├─ _extract_latest_pairs()             │
│   │    └─ detect_all_machine_molds()          │
│   │         (if no existing data)             │
│   │                                           │
│   └─ if has_change:                           │
│        ├─ Move old files to historical_db/    │
│        ├─ Save JSON files (per change date)   │
│        │  to pair_changes/                    │
│        ├─ _analyze_mold_machined_summary()    │
│        │    ├─ Merge DataFrames               │
│        │    ├─ _check_tonnage_match()         │
│        │    ├─ _create_mold_tonnage_summary() │
│        │    ├─ _analyze_first_usage()         │
│        │    └─ _create_first_paired_data()    │
│        ├─ Create pivot tables                 │
│        ├─ Save Excel (3 sheets)               │
│        ├─ _generate_analyzed_results_summary()│
│        ├─ Save text summary                   │
│        └─ Update change_log.txt               │
└───────────────────────────────────────────────┘
    ↓
Returns: (has_change, 3 DataFrames, log_entries)
```

## Key Features
  
- **Automatic Versioning**

  - New detections automatically move old files to historical_db/
  - Timestamped filenames: YYYYMMDD_HHMM_mold_machine_pairing_YYYY-MM-DD.[xlsx|txt]
  - Individual JSON files per change date in pair_changes/ subdirectory
  - Change log maintains audit trail of all operations

- **Pairing-Level Granularity**

  - Pairing changes detected when new (machine, mold) combinations appear
  - Tracks first occurrence date of each unique pairing
  - Format: {moldNo: [machineCode1, machineCode2, ...]} (sorted)
  - Only stores change points (not every production record)

- **Compatibility Validation**

The `_check_tonnage_match()` method verifies:

1. Extracts tonnage values from machineTonnage (e.g., "150/200" → ["150", "200"])
2. Checks if any tonnage value appears in machineCode string
3. Returns True if compatible, False otherwise
4. Results stored in tonnageMatched column for filtering

- **Usage Analytics**
  
The `_analyze_mold_machined_summary()` method provides:

1. **Tonnage Summary**: Count of different machine types used per mold
2. **First Usage Analysis**: Days between mold acquisition and first production use
3. **Pairing History**: First date each machine-mold combination was used
4. **Data Quality Checks**: Identifies molds used before acquisition date (negative gap)

## Error Handling

All file operations wrapped in try-except blocks with:

- Logger error messages for debugging
- OSError exceptions raised with descriptive messages
- JSON validation on load (returns None if invalid)
- File move failures logged and raised immediately
- Missing data handling: Filters out records with null moldNo values

## Example Usage

  ```python
  from MachineMoldPairTracker import MachineMoldPairTracker
  import pandas as pd

  # Initialize with production records and reference data
  tracker = MachineMoldPairTracker(
      productRecords_df=production_df,
      moldInfo_df=mold_specs_df,
      machineInfo_df=machine_specs_df,
      output_dir='output/mold_pairs'
  )

  # Process new data
  latest_date = pd.Timestamp('2024-03-15')
  has_change, tonnage_summary, first_usage, pairing_history, logs = tracker.data_process(latest_date)

  if has_change:
      print("New mold-machine pairs detected!")
      print(f"Tonnage mismatches: {len(tonnage_summary[tonnage_summary['usedTonnageCount'] > 1])}")
      print(f"Average acquisition-to-use gap: {first_usage['daysDifference'].mean():.1f} days")
      
  # Get summary of all pairings
  pairing_dict = tracker.load_machine_molds()
  summary = tracker.get_summary(pairing_dict)
  latest_mapping = tracker.get_latest_mapping(pairing_dict)
  ```

## Change Detection Logic

- **Pairing Change Criteria**: A pairing change is detected when new (machine, mold) combinations appear that weren't present in historical data.

- **Examples of detected changes**:

  - Mold MOLD001 first used on machine MC01
  - Existing mold MOLD002 now also runs on new machine MC05
  - New mold MOLD010 introduced and paired with MC03

- **Not detected as changes**:

  - Continued use of existing pairs (MOLD001 runs again on MC01)
  - Production volume changes
  - Different products using same mold-machine pair

- **Data Structure**:

  - Stored as {moldNo: [machineCode1, machineCode2, ...]}
  - Compared as sets of (mold, machine) tuples
  - New pairs = current_pairs - historical_pairs

## Dependencies

- `pandas`: DataFrame operations and Excel export
- `loguru`: Structured logging
- `json`: Pairing persistence
- `shutil`: File archival
- `pathlib`: Cross-platform path handling
- `datetime`: Timestamp handling
- Custom: `agents.decorators.validate_init_dataframes`, `agents.utils.{read_change_log, load_annotation_path}`

## Data Quality Considerations
  
- **Negative Gap Warning**

Molds with negative `daysDifference` (used before acquisition) indicate:

  - Data entry errors (incorrect acquisition date)
  - Backdated production records
  - System timestamp issues

These are flagged in the text summary for manual review.

- **Tonnage Mismatch Analysis**

The `moldTonageUnmatched` sheet helps identify:

  - Process violations (using mold on incompatible machine)
  - Potential equipment damage risks
  - Incorrect machine/mold metadata