## Workflow: DataPipelineOrchestrator

```

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             [ DataPipelineOrchestrator ]                                        │
│                    Orchestrates the entire batch data processing flow                           │
└──────────────┬───────────────────────────────────────────────────────────────────┬──────────────┘
               ▼ Phase 1                                                           ▼ Phase 2
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │   DataCollector      │                                            │   DataLoaderAgent    │
        │ (Process Dynamic DB) │                                            │ (Load All Databases) │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               │                                                                        ▼
               │                                                           Check for changes in content of each database
               ▼                                                                        ▼
    1. Read report files `.xlsb`/`.xlsx`                                                If data has changed:
    2. Merge and process based on `monthlyReports_` and `purchaseOrder_`                     1. Compare with schema from `databaseSchemas.json`
    3. Validate missing fields, normalize datatypes                                          2. Compare new content with `path_annotations.json`
    4. Compare with existing parquet using hash                                              3. If different → Save new version
    5. If changed → save as new `.parquet` file                                              4. Log changes + update path_annotation.json                                                                 

```

---

### 🔍 Details of Each Phase

#### Phase 1: `DataCollector`

| Step | Description                                                                  |
| ---- | ---------------------------------------------------------------------------- |
| 1    | Read data from `monthlyReports_history` and `purchaseOrders_history` folders |
| 2    | Handle missing columns, normalize date format, shifts, resin codes, etc.     |
| 3    | Remove duplicated data                                                       |
| 4    | Compare new data with existing `.parquet` using hash                         |
| 5    | If changed → save new `.parquet` using atomic write and snappy compression   |

---

#### Phase 2: `DataLoaderAgent`

| Step | Description                                                                                                                                   |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Load `databaseSchemas.json` to get schema definitions                                                                                         |
| 2    | Load `path_annotations.json` for existing version references                                                                                  |
| 3    | For each database:<br>- If `dynamicDB` → load `.parquet` from Phase 1<br>- If `staticDB` → load `.xlsx` from path                             |
| 4    | Compare new and old content using hash                                                                                                        |
| 5    | If different:<br>→ Move old file to `historical_db`<br>→ Save new file to `newest` with timestamp<br>→ Log and update `path_annotations.json` |

---

### Input/Output Overview

| Agent             | Input                                          | Output                                                 |
| ----------------- | ---------------------------------------------- | ------------------------------------------------------ |
| `DataCollector`   | Folders with `.xlsb`, `.xlsx` reports          | `productRecords.parquet`, `purchaseOrders.parquet`     |
| `DataLoaderAgent` | `.parquet` from Phase 1 + static `.xlsx` files | Versioned `.parquet` + updated `path_annotations.json` |
