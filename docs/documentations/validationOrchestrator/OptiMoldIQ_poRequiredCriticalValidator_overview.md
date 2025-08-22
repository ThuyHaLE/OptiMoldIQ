# PORequiredCriticalValidator

## 1. Overview

`PORequiredCriticalValidator` is an agent in the data pipeline orchestrator, responsible for validating **Purchase Order (PO)** consistency between `productRecords` and `purchaseOrders` datasets.

It ensures: 
- All product records reference **valid PO numbers** that exist in purchase orders. 
- Product record details are **consistent** with corresponding purchase orders. 
- Detection of **mismatches and missing/invalid PO** data. 
- Generation of **structured warnings** for downstream quality control. 
- Export of results as **Excel reports** with versioning.

---

## 2. Class: `PORequiredCriticalValidator`

### 2.1 Initialization

``` python
validator = PORequiredCriticalValidator(
    source_path="agents/shared_db/DataLoaderAgent/newest",
    annotation_name="path_annotations.json",
    databaseSchemas_path="database/databaseSchemas.json",
    default_dir="agents/shared_db"
)
```

-   `source_path`: Directory containing annotated paths to parquet datasets.
-   `annotation_name`: JSON file defining mappings of dataset names to paths.
-   `databaseSchemas_path`: Schema configuration (JSON) describing database structure.
-   `default_dir`: Base directory for output reports.

### 2.2 Main Methods

#### `run_validations() -> pd.DataFrame`

-   Executes PO consistency checks.
-   Identifies:
    -   **Invalid POs** (referenced in product records but absent in purchase orders).
    -   **Field mismatches** (same PO exists in both but with different values).
-   Generates structured warnings per record.

**Output Example**

``` json
[
  {
    "poNo": "PO12345",
    "warningType": "product_info_not_matched",
    "mismatchType": "quantity_not_matched",
    "requiredAction": "stop progressing or double check productRecords",
    "message": "(PO12345, 2024-01-15, ShiftA, M1) - Mismatch: quantity: 500 vs 520. Please stop progressing or double check productRecords"
  }
]
```

#### `run_validations_and_save_results() -> None`

-   Runs full validation pipeline.
-   Saves results to Excel with versioning (`po_required_critical_validator_v1.xlsx`).
-   Logs a **summary report**:
    -   Total processed POs.
    -   Valid vs. invalid counts.
    -   Breakdown by mismatch type.

### 2.3 Processing Steps

#### `_process_product_records()`

-   Standardizes product records:
    -   Renames `poNote` → `poNo`.
    -   Removes records with null PO numbers.

#### PO Validation Flow (`run_validations`)

1.  **Identify common fields** between `productRecords_df` and `purchaseOrders_df`.
1.  **Separate PO numbers** into:
    -   Valid: exist in both datasets.
    -   Invalid: exist only in product records.
2.  **Compare valid PO records**:
    -   Merge by `poNo`.
    -   For each field: check equality (null-safe).
    -   Generate `*_match` flags and `final_match` status.
3.  **Generate warnings**:
    -   Field mismatch warnings → `_process_warnings`.
    -   Invalid PO warnings → `_process_invalid_po_warnings`.

### 2.4 Helper Methods

-   `_process_warnings(merged_df, comparison_cols)` → Creates warnings for **field mismatches** in valid PO numbers.
-   `_process_invalid_po_warnings(invalid_productRecords)` → Creates warnings for **non-existent PO numbers**.

---

## 3. Validation Dimensions

  -----------------------------------------------------------------------
  Dimension      Purpose
  -------------- --------------------------------------------------------
  Invalid POs    Ensure all referenced POs exist in `purchaseOrders`.

  Field Matches  Validate consistency across overlapping fields.

  Record Context Each warning includes `recordDate`, `workingShift`, and
                 `machineNo` for traceability.
  -----------------------------------------------------------------------

---

## 4. Error Handling & Invalid Data

-   Missing `productRecords` or `purchaseOrders` files → raises `FileNotFoundError`.
-   Records with null `poNo` → filtered out before validation.
-   Invalid and mismatched records are **logged** and **returned as structured warnings**.

---

## 5. Output & Reporting

-   **Two types of warnings**:
    1.  `product_info_not_matched`: Field-level mismatches in valid POs.
    1.  `PO_invalid`: PO numbers not found in purchase orders.
-   Results exported as versioned Excel file.
-   Logs include detailed counts:
    -   Total processed POs.
    -   Valid vs. invalid.
    -   Mismatch vs. missing PO counts.

---

## 6. Monitoring & Usage

-   Warnings are intended for **QA and operations teams** to review before downstream processing.
-   Prevents continuation with invalid PO data.
-   Can be extended for **automated alerts** (e.g. email, Slack, dashboards).