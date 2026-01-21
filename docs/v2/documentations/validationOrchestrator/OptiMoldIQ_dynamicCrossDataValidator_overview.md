>Status: Inherited from v1  
>No structural or behavioral changes in v2.

# DynamicCrossDataValidator

## 1. Overview
`DynamicCrossDataValidator` is an agent in the data pipeline orchestrator, responsible for validating production records against reference datasets (mold specifications, machine info, item compositions).

It ensures:
- Consistency of `item – mold – machine – composition mappings`.
- Detection of `mismatches and missing (invalid) reference data`.
- Generation of `structured warnings` for downstream quality control.
- Export of results as `Excel reports` with versioning.

---

## 2. Class: `DynamicCrossDataValidator`
### 2.1 Initialization
```python
validator = DynamicCrossDataValidator(
    source_dir="database/dynamicDatabase",
    schema_file="database/databaseSchemas.json",
    annotation_file="database/path_annotations.json"
)
```
- `source_dir`: Base directory containing parquet data sources.
- `schema_file`: JSON schema for database structure.
- `annotation_file`: Path annotations (mapping references).

### 2.2 Main Method
`run_validations() -> Dict[str, pd.DataFrame]`

- Orchestrates the validation pipeline.
- Prepares production and reference datasets.
- Runs multi-level mismatch analysis.
- Generates structured warnings and invalid data reports.
  
**Output Example**
```json
{
  "invalid_warnings": [...],
  "mismatch_warnings": [...]
}
```

`run_validations_and_save_results(output_file: str) -> None`

- Executes full validation pipeline.
- Writes results to Excel with versioning (e.g. dynamic_cross_validator_v1.xlsx).
- Logs summary: counts of mismatches, invalid records, categories of warnings.

### 2.3 Processing Steps
`_prepare_production_data()`

- Reads `productRecords_df`.
- Filters out invalid `poNote`.
- Builds `item_composition` string (resin + masterbatch).
- Merges with `machineInfo_df` to add `machineTonnage`.

`_prepare_reference_data()`

- Reads `moldSpecificationSummary_df` and expands mold list.
- Merges with `moldInfo_df` to attach machine tonnage.
- Prepares item compositions from `itemCompositionSummary_df`.
- Produces `standard_df` (reference baseline).

`_analyze_mismatches(production_df, standard_df)`

- Compares production vs. reference at multiple levels:
    - Items (`itemCode`, `itemName`)
    - Item–Mold pairs
    - Mold–Machine tonnage
    - Item composition
    - Full combination
    - Returns mismatched records.

`_generate_warnings(mismatches, production_df, reference_df)`

- Transforms mismatches into structured warnings:
    - `item_warnings`
    - `item_mold_warnings`
    - `mold_machine_tonnage_warnings`
    - `item_composition_warnings`
  
### 2.4 Helper Methods
- `_check_invalid(df, label)` → finds rows with missing reference values.
- `_build_component_string(resin, color, additive)` → creates standardized material composition string.
- `_convert_results(warnings)` → normalizes warning DataFrames.
- `_create_empty_warning_dataframe(type)` → ensures consistent schema for empty results.

---

## 3. Validation Dimensions

| Dimension            | Purpose                                  |
| -------------------- | ---------------------------------------- |
| Item                 | Ensures `itemCode` & `itemName` exist.   |
| Item–Mold            | Validates allowed combinations.          |
| Mold–Machine Tonnage | Ensures mold is used on correct machine. |
| Item Composition     | Confirms material formula correctness.   |
| Full Combination     | Cross-checks all fields together.        |

---

## 4. Error Handling & Invalid Data

- Records with **null / missing reference values** are flagged as `INVALID`.
- Separate DataFrame `invalid_warnings` is produced.
- Mismatches are categorized and logged for **downstream monitoring**.

---

## 5. Output & Reporting

- Two main outputs:
  1. **Mismatch Warnings** (unexpected deviations).
  2. **Invalid Warnings** (missing reference data).
- Exported to Excel with versioning.
- Log summary includes counts per warning type.

---

## 6. Monitoring & Usage
- Warnings are intended for **QA teams** to review before final data loading.
- Supports **continuous integration** in the pipeline.
- Can be extended to trigger notification agents (e.g. email/Slack).