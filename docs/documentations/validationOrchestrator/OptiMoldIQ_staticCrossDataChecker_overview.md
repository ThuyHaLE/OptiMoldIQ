# StaticCrossDataChecker

## 1. Overview

`StaticCrossDataChecker` is an agent in the data pipeline orchestrator, responsible for validating **dynamic production/purchase order data** against **static reference datasets** (`itemInfo`, `resinInfo`, `itemCompositionSummary`).

It ensures: 
- Existence and correctness of `itemCode` & `itemName`. 
- Correctness of resin references (`plasticResin`, `colorMasterbatch`, `additiveMasterbatch`). 
- Validity of full `item-resin composition` against the reference summary. 
- Generation of `structured warnings` for mismatches. 
- Export of results as `Excel reports` with versioning.

---

## 2. Class: `StaticCrossDataChecker`

### 2.1 Initialization

``` python
checker = StaticCrossDataChecker(
    checking_df_name=["productRecords", "purchaseOrders"],
    source_path="agents/shared_db/DataLoaderAgent/newest",
    annotation_name="path_annotations.json",
    databaseSchemas_path="database/databaseSchemas.json",
    default_dir="agents/shared_db"
)
```

-   `checking_df_name`: List of dynamic datasets to validate (`productRecords`, `purchaseOrders`).
-   `source_path`: Base path for parquet data sources.
-   `annotation_name`: JSON file containing path annotations.
-   `databaseSchemas_path`: Database schema definition file.
-   `default_dir`: Directory for storing validation outputs.

---

### 2.2 Main Method

`run_validations() -> Dict[str, pd.DataFrame]`

-   Runs the validation pipeline for each dataset in `checking_df_name`.
-   Executes three levels of checks:
    -   Item info validation.
    -   Resin info validation.
    -   Composition validation.
-   Produces structured warnings.

**Output Example**

``` json
{
  "productRecords": [
    {"poNo": "PO123", "warningType": "item_info_warnings", "message": "..."}
  ],
  "purchaseOrders": []
}
```

`run_validations_and_save_results() -> None`

-   Executes validations and writes results to Excel with versioning.
-   Uses filename prefix `static_cross_checker`.
-   Logs summary statistics for each validation type.

---

### 2.3 Processing Steps

#### `_process_checking_data(df_name)`
-   For `productRecords`:
    -   Removes rows with null `poNote`.
    -   Renames `poNote → poNo`.
-   For `purchaseOrders`: returns as-is.

#### `_check_item_info_matches(df_name, checking_df)`
-   Validates `(itemCode, itemName)` pairs against `itemInfo_df`.
-   Produces `item_info_warnings`.

#### `_check_resin_info_matches(df_name, checking_df)`
-   Validates resin references against `resinInfo_df`:
    -   Plastic resin.
    -   Color masterbatch.
    -   Additive masterbatch.
-   Produces `resin_info_warnings`.

#### `_check_composition_matches(df_name, checking_df)`
-   Validates complete composition against `itemCompositionSummary_df`.
-   Produces `composition_warnings`.

---

### 2.4 Helper Methods

-   `_process_item_warnings(mismatches_df, df_name)` → formats item mismatch warnings.
-   `_process_resin_warnings(mismatches_df, df_name)` → formats resin mismatch warnings.
-   `_process_composition_warnings(mismatches_df, df_name, fields)` → formats composition mismatch warnings.

---

## 3. Validation Dimensions

  -----------------------------------------------------------------------
  Dimension     Purpose
  ------------- ---------------------------------------------------------
  Item Info     Ensures `itemCode` & `itemName` pairs exist in reference

  Resin Info    Ensures resin codes & names match reference resin master

  Composition   Confirms full item--resin composition is valid
  -----------------------------------------------------------------------

---

## 4. Error Handling & Invalid Data

-   Missing file paths trigger **FileNotFoundError**.
-   Invalid dataframe names trigger **ValueError**.
-   Empty subsets (no data after filtering) return empty results.
-   All mismatches are structured with: [poNo, warningType, mismatchType, requiredAction, message]

---

## 5. Output & Reporting

-   **Three categories of warnings**:
    1.  Item info warnings.
    2.  Resin info warnings.
    3.  Composition warnings.
-   Exported to Excel with versioning:
    -   `static_cross_checker_v1.xlsx`
    -   `static_cross_checker_v2.xlsx`
-   Logs include counts by category per dataset.

---

## 6. Monitoring & Usage

-   Warnings support **quality assurance teams** in checking invalid/mismatched reference data.
-   Integrated into the **data pipeline** before final loading.
-   Can be extended to trigger **automated notifications** (e.g. Slack, email).