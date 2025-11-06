# MachineLayoutTracker

- **Purpose**:
  
    - Track layout or positional changes of machines within the factory (e.g., when machines are moved, replaced, or renamed).

- **Core responsibilities**:
  
    - Prepare and clean production record data to include machine layout information.
    - Detect all layout changes across recorded dates.
    - Identify specific machine changes (added, removed, or renamed/moved).
    - Save and load layout change history to/from JSON for persistence.
    - Provide layout summary DataFrames for analytics or visualization.

- **Input**:
  
    - `productRecords_df`: Production records DataFrame containing columns like recordDate, machineNo, and machineCode.
    - `output_dir` (optional): Directory to store layout change history JSON file.
    - `json_name` (optional): Name of the JSON file to store layout history.

- **Output**:
  
    - JSON file (`layout_changes.json`) containing layout snapshots by date.
    - Summary DataFrame of layout versions.
    - Change DataFrame showing added, removed, and renamed machines per version.
  
- **Main Methods**:
  
| Method                                        | Description                                                                                            |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `_prepare_data()`                             | Ensures data consistency by creating `machineInfo` column and converting `recordDate` to datetime.     |
| `detect_all_layout_changes()`                 | Detects all historical layout changes and builds a dictionary of layouts by date.                      |
| `_get_layout_at_date(target_date)`            | Returns the machine layout as of a specific date (most recent state before or at that date).           |
| `save_layout_changes(layout_changes_dict)`    | Saves layout history to JSON file with error handling and backup support.                              |
| `load_layout_changes()`                       | Loads layout history from JSON file if available, handling invalid JSON cases gracefully.              |
| `check_new_layout_change(new_record_date)`    | Checks if a new layout change occurred at a given date, updating the JSON if necessary.                |
| `_layouts_different(layout1, layout2)`        | Compares two layout dictionaries to detect differences.                                                |
| `get_layout_summary(layout_changes_dict)`     | Builds a DataFrame summarizing each layout version (date, number of machines, hash signature).         |
| `detect_machine_changes(layout_changes_dict)` | Produces a detailed DataFrame listing machines added, removed, or with changed codes between versions. |

- **Data flow**:
  
    - Input `productRecords_df` → `_prepare_data()`
    - Detect layout states → `detect_all_layout_changes()`
    - Store results → `save_layout_changes()`
    - Compare new state → `check_new_layout_change()`
    - Generate reports → `get_layout_summary()` and `detect_machine_changes()`
  
- **Example Output Structure** (`layout_changes.json`):
  
```json
{
  "2023-10-01": {"M001": "MC01", "M002": "MC02"},
  "2023-12-15": {"M001": "MC03", "M002": "MC02"}
}
```
→ From this, `M001` changed from `MC01` → `MC03` on `2023-12-15`.

- **Error handling**:
  
    - Safe JSON save with backup restoration if write fails.
    - Handling for missing or invalid JSON files.
    - Logs all key operations for traceability.