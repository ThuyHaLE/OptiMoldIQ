## Workflow: DataPipelineOrchestrator

```
                                               ┌──────────────────────────────┐
                                               │     OrderProgressTracker     │
                                               └────────────┬─────────────────┘
                                                            │
                                                            ▼
                                          ┌────────────────────────────────────────┐
                                          │         Load Datasets & Configs        │
                                          │ (purchaseOrders, productRecords, mold) │
                                          └─────────────────┬──────────────────────┘
                                                            │
                                                            ▼
                                            ┌────────────────────────────────────┐
                                            │    _extract_product_records()      │
                                            │  → Extract & group production data │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │     _pro_status_processing()       │
                                            │  → Compute proStatus & etaStatus   │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │         _get_change()              │
                                            │  → Load latest po_mismatch file    │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │  _add_warning_notes_column()       │
                                            │  → Annotate orders with warnings   │
                                            └────────────────┬───────────────────┘
                                                             │
                                                             ▼
                                            ┌────────────────────────────────────┐
                                            │   save_output_with_versioning()    │
                                            │  → Save to Excel with 3 sheets     │
                                            └────────────────────────────────────┘
```

## Objective
Track production progress of purchase orders (`purchaseOrders`) using actual production data (`productRecords`) and mold information (`moldSpecificationSummary`). The goal is to determine production status and evaluate on-time delivery.

## Main Execution

### 1. **Class Initialization**
- ✅ Load configs and annotations:
  - `path_annotations.json`
  - `databaseSchemas.json`
- 📂 Load required datasets:
  - `productRecords`
  - `purchaseOrders`
  - `moldSpecificationSummary`
- 🧾 Validate schemas with `@validate_init_dataframes`
- ⚙️ Setup metadata (shift map, dtypes)

---

### 2. **Call `pro_status()`**

```python
tracker = OrderProgressTracker()
tracker.pro_status()
```

---

## Step-by-step Processing

### 2.1. Merge Purchase Orders with Mold Info
- Join `purchaseOrders` with `moldSpecificationSummary` → `ordersInfo_df`

### 2.2. Analyze Production Records
- `_extract_product_records()`:
  - Separate working vs. non-working records
  - Compute molded qty, start/end, machine/mold used
  - Generate aggregation by date/shift

### 2.3. Generate Production Status
- `_pro_status_processing()`:
  - Compute:
    - `itemRemain` = `orderQty` - `moldedQty`
    - `proStatus`: `PENDING`, `MOLDING`, `MOLDED`
    - `etaStatus`: `PENDING`, `ONTIME`, `LATE`

### 2.4. Load Warning Log
- `_get_change()`:
  - Load latest PO mismatch warning
  - Parse into dictionary format

### 2.5. Attach Warnings to Orders
- `_add_warning_notes_column()`:
  - Add `warningNotes` column to annotated output

### 2.6. Export Results
- `save_output_with_versioning()`:
  - Save to Excel (with timestamp)
  - Sheets:
    - `productionStatus`
    - `notWorkingStatus`
    - `po_mismatch_warnings`

---

## Output: Excel File

| Sheet Name             | Content                                    |
|------------------------|--------------------------------------------|
| `productionStatus`     | Final production and ETA status per PO     |
| `notWorkingStatus`     | Orders with no actual production           |
| `po_mismatch_warnings` | Log of mismatch issues (if available)      |
