# MachineMoldPairTracker

- **Purpose**:
  
    - Track and record historical relationships between machines and molds — i.e., which molds have been used on which machines — over time.

- **Core responsibilities**:
  
    - Parse and clean production records containing `machineCode`, `moldNo`, and `recordDate`.
    - Detect all historical mappings between machines and molds.
    - Identify new machine–mold combinations appearing over time.
    - Save mapping history to JSON (with versioned backups) and maintain a change log.
    - Load and compare latest mappings to detect new pairs.
    - Provide summary DataFrames for statistical or analytical visualization.

- **Input**:
  
    - `productRecords_df`: DataFrame containing production records (must include recordDate, machineCode, and moldNo).
    - `output_dir` (optional): Output directory to store mapping files and logs.
    - `json_name` (optional): Name of the JSON file storing machine–mold mappings.
    - `change_log_name` (optional): Name of the log file recording history updates.

- **Output**:
  
    - JSON files: mapping of each mold to list of associated machines by date.
    - Summary DataFrame for historical trends.
    - Set of newly detected (machine, mold) pairs (if any). 

- **Main Methods**:
  
| Method                                    | Description                                                                                                           |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `_prepare_data()`                         | Ensures that `recordDate` is in datetime format.                                                                      |
| `detect_all_machine_molds()`              | Scans entire dataset to build complete machine–mold history dictionary keyed by change dates.                         |
| `_get_machine_molds_at_date(target_date)` | Returns machine–mold mapping as of a specific date.                                                                   |
| `save_machine_molds(machine_molds_dict)`  | Saves mappings to JSON files under `newest/` and archives old versions to `historical_db/`. Updates `change_log.txt`. |
| `load_machine_molds()`                    | Reads the latest mapping JSON file based on log history.                                                              |
| `check_new_pairs(new_record_date)`        | Compares current data to latest stored state; detects and saves newly appeared machine–mold pairs.                    |
| `_extract_all_pairs()`                    | Extracts all machine–mold pairs across all recorded dates.                                                            |
| `_extract_latest_pairs()`                 | Extracts all pairs from the most recent recorded mapping.                                                             |
| `get_latest_mapping()`                    | Returns latest machine–mold mapping dictionary.                                                                       |
| `get_summary()`                           | Builds summary DataFrame of historical changes, showing total pairs and average molds per machine.                    |

- **Data flow**:
  
    - Input `productRecords_df` → `_prepare_data()`
    - Generate mappings → `detect_all_machine_molds()`
    - Save and version control → `save_machine_molds()`
    - Compare new records → `check_new_pairs()`
    - Produce summary report → `get_summary()`

- **Example Output Structure** (`machine_molds.json`):
  
```json
{
  "2024-11-06": {
    "MOLD_A": ["MC01", "MC02"],
    "MOLD_B": ["MC03"]
  },
  "2025-01-15": {
    "MOLD_A": ["MC01", "MC04"],
    "MOLD_B": ["MC03", "MC05"]
  }
}
```
→ On `2025-01-15`, mold `MOLD_A` gained a new machine `MC04`, and mold `MOLD_B` gained `MC05`.

- **Error handling**:
  
    - Automatically archives old JSONs into historical_db to preserve history.
    - Handles missing or invalid JSON files.
    - Maintains a plain-text change log (change_log.txt) with timestamps of save actions.
    - Logs all key operations for traceability.
