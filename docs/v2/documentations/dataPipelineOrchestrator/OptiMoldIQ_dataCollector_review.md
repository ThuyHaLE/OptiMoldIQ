>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# DataCollector

## 1. Overview
`DataCollector` is an agent in the **data pipeline orchestrator**, responsible for **collecting, processing, and standardizing data** from Excel files (monthly reports, purchase orders) and exporting the results as **Parquet** files.

It supports:
- Reading `.xlsb` and `.xlsx` files.
- Standardizing schema according to business rules.
- Merging data, removing duplicates, handling null values.
- **Healing/rollback** mechanism when errors occur (backup/retry).
- Produces results with metadata and triggers downstream agents.

---

## 2. Class: `DataCollector`

### 2.1 Initialization
```python
collector = DataCollector(
    source_dir="database/dynamicDatabase",
    default_dir="agents/shared_db"
)
```
- `source_dir`: Directory containing source Excel files.
- `default_dir`: Base directory for output files.
- `output_dir`: automatically set to `default_dir/dynamicDatabase`.

---

### 2.2 Main Method

#### `process_all_data() -> Dict[str, Any]`
- Processes all datasets (productRecords + purchaseOrders).
- Calls `_process_data_type()` for each dataset.
- Aggregates results (status, summary, metadata).
- Determines downstream agents to trigger and recovery actions.

**Output Example**
```json
{
  "agent_id": "DATA_COLLECTOR",
  "status": "SUCCESS",
  "summary": {
    "total_datasets": 2,
    "successful": 2,
    "failed": 0,
    "warnings": 1
  },
  "details": [...],
  "healing_actions": [],
  "trigger_agents": ["DATA_LOADER"],
  "metadata": {
    "processing_duration": null,
    "disk_usage": {
      "output_directory_mb": 12.5,
      "available_space_mb": 10240.0
    }
  }
}
```

---

### 2.3 Processing Methods

#### `_process_data_type(...)`
- Input: folder path, output path, pattern, sheet, data_type.
- Checks folder, required fields, reads source files.
- Returns result (success / partial / error).
- Healing mechanism: **rollback from backup**.

#### `_process_single_file(file_path, sheet, required_fields)`
- Reads Excel → DataFrame.
- Validates required columns.
- Returns filtered dataframe according to schema.

#### `_merge_and_process_data(merged_dfs, summary_file_path, existing_df)`
- Merges multiple DataFrames.
- Removes duplicates, applies schema, standardizes nulls, converts datatypes.
- Checks changes against existing data.
- Saves parquet (atomic write).

#### `_save_parquet_file(df, summary_file_path)`
- Saves dataframe to parquet safely (temp file + move).
- Compresses with `snappy`.
- Returns file size (MB).

---

### 2.4 Helper Methods

- `_get_source_files(folder, name_start, ext)` → finds valid files.
- `_load_existing_data(file)` → loads existing parquet file.
- `_get_healing_actions(results)` → determines required recovery actions.
- `_get_trigger_agents(results)` → determines downstream agents to trigger.
- `_get_disk_usage()` → output directory disk usage info.
- `_dataframes_equal_fast(df1, df2)` → fast hash-based comparison.
- `_get_required_fields()` → schema definitions for each dataset.
- `_data_prosesssing(df, summary_file_path)` → cleans and standardizes data.

---

## 3. Supported Data Types

### 3.1 Product Records (`monthlyReports_*.xlsb`)
- Sheet: `Sheet1`
- Schema:
  - `recordDate` (Excel serial → datetime)
  - `workingShift` (UPPERCASE)
  - `machineNo`, `machineCode`, `itemCode`, `itemName`, ...
  - Defects: `itemBlackSpot`, `itemOilDeposit`, `itemScratch`, ...
  - Material info: `plasticResinCode`, `colorMasterbatchCode`, `additiveMasterbatchCode`

### 3.2 Purchase Orders (`purchaseOrder_*.xlsx`)
- Sheet: `poList`
- Schema:
  - `poReceivedDate`, `poETA` (datetime)
  - `poNo`, `itemCode`, `itemName`
  - `plasticResinCode`, `colorMasterbatchCode`, `additiveMasterbatchCode`
  - Quantity fields: `plasticResinQuantity`, `colorMasterbatchQuantity`, `additiveMasterbatchQuantity`

---

## 4. Error Handling & Healing

| Error Type              | Action                          |
|--------------------------|---------------------------------|
| FILE_NOT_FOUND          | Rollback from local backup      |
| UNSUPPORTED_DATA_TYPE   | Rollback                        |
| FILE_READ_ERROR         | Rollback                        |
| MISSING_FIELDS          | Rollback                        |
| DATA_PROCESSING_ERROR   | Rollback                        |
| PARQUET_SAVE_ERROR      | Rollback                        |

---

## 5. Triggers

- If `SUCCESS`: trigger `DATA_LOADER`.
- If `ERROR`: trigger `ADMIN_NOTIFICATION`.
- If `PARTIAL_SUCCESS`: add `RETRY_PROCESSING`.

---

## 6. Metadata & Monitoring
- `disk_usage`: parquet file size, free disk space.
- `processing_duration`: optional execution time measurement.
- `warnings`: e.g. `"Removed 25 duplicate rows"`.

---