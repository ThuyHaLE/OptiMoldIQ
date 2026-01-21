>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# ItemMoldCapacityOptimizer

## 1. Overview

`ItemMoldCapacityOptimizer` is a manufacturing analytics component that optimizes mold utilization capacity based on historical stability data and technical specifications.

It ensures: 
- Identification of **invalid** or **unused** molds. 
- Calculation of **theoretical and estimated capacities** for each mold. 
- Consolidation of product--mold mappings into structured datasets. 
- **Priority assignment** to the most efficient molds for each item.

---

## 2. Class: `ItemMoldCapacityOptimizer`

### 2.1 Initialization

``` python
optimizer = ItemMoldCapacityOptimizer(
    mold_stability_index=...,
    moldSpecificationSummary_df=...,
    moldInfo_df=...
)
```

-   `mold_stability_index`: Historical mold stability records.
-   `moldSpecificationSummary_df`: Mapping of products to mold lists.
-   `moldInfo_df`: Detailed mold specifications (cycle time, cavities,
    acquisition date).

**Validation**: 
- Uses decorators to enforce schema integrity. 
- Checks mandatory columns and data consistency at load.

### 2.2 Main Methods

`process() -> Dict[str, pd.DataFrame]`

-   Classifies molds:
    -   **Invalid molds**: Appearing in history but missing in specs.
    -   **Unused molds**: In specs but absent in history.
-   Computes hourly capacity using cycle time, cavity count, efficiency, and loss factors.
-   Merges used and unused molds into a unified dataset.
-   Explodes product--mold lists into one row per mold.
-   Assigns **priority molds** per item.

**Output Example**

``` json
{
  "invalid_molds": ["M123", "M234"],
  "result_df": [
    {"itemCode": "I001", "moldNo": "M001", "balancedMoldHourCapacity": 120.0, "isPriority": true},
    ...
  ]
}
```

---

### 2.3 Processing Steps

#### `_find_invalid_molds()` 
- Compares `mold_stability_index` vs. `moldInfo_df`. 
- Flags molds with missing specs.

#### `_find_unused_molds()` 
- Detects molds in `moldInfo_df` not present in historical records.

#### `_compute_hourly_capacity(df, efficiency, loss)` 
- Formula: 
  - `theoreticalCapacity = (3600 / cycle_time) * cavity_count` 
  - `estimatedCapacity = theoreticalCapacity * (efficiency - loss)` 
  - `balancedCapacity = estimatedCapacity`
  - Handles 0, NaN, and infinity values; clips negatives to 0.

#### `_merge_with_unused_molds()` 
- Combines capacity data of used and unused molds into one DataFrame.

#### `_expand_mold_list()` 
- Splits `moldList` by `/` and expands into individual rows. 
- Merges with updated capacity information.

#### `_assign_priority_mold()` 
- For each `itemCode`: 
  - Selects mold with **highest capacity**. 
  - Resolves ties by **latest acquisition date**. 
  - Falls back to **first mold** if no valid capacity. 
- Flags chosen mold as `isPriority = True`.

---

### 2.4 Helper Methods

-   `_validate_dataframe(df, required_columns)` → Ensures required fields are present.
-   `_safe_replace_and_clip(df, columns)` → Handles invalid numeric values.
-   `_copy_and_merge(df1, df2)` → Maintains data safety by working on copies.
-   Logging methods for debugging and traceability.

---

## 3. Data Safety & Performance

-   Works with **copies of DataFrames** to avoid mutation.
-   Vectorized Pandas operations for efficiency.
-   Groupby operations used for priority assignment.
-   Invalid values (NaN, ±∞, 0) are sanitized before calculations.

---

## 4. Error Handling

-   Empty or missing DataFrames trigger early warnings.
-   Missing required columns raise validation errors.
-   Invalid records are logged separately.
-   Suppresses non-critical warnings to ensure smooth execution.

---

## 5. Output & Reporting

-   **invalid_molds**: List of molds requiring verification.
-   **result_df**: Final DataFrame with:
    -   `itemCode`
    -   `moldNo`
    -   `balancedMoldHourCapacity`
    -   `isPriority` flag
-   Can be exported to Excel or integrated with downstream analytics.

---

## 6. Usage & Integration

-   Used in production planning and mold resource allocation.
-   Supports **continuous updates** as new stability data is collected.
-   Can be extended to include **machine availability** or **shift-based performance factors**.