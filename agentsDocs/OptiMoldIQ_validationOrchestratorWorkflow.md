## I. Workflow: PORequiredCriticalValidator
```
                                                 ┌──────────────────────────────────────────────────────────────┐
                                                 │              [ ValidationOrchestrator ]                      │
                                                 │   Coordinate static, dynamic, and critical PO validations    │
                                                 └──────────────────────────────────────────────────────────────┘
                                                                                │
                                                          Load database schema and path annotations JSON
                                                                                │
                                                              ┌────────────────────────────────────┐
                                                              │ Load 8 parquet files into memory   │
                                                              └────────────────────────────────────┘
                                                                                │
                                                         Validate schema with `@validate_init_dataframes`
                                                                                │
                                                                                ▼
                  ┌─────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┐
┌───────────────────────────────────┐                          ┌──────────────────────────────────┐                           ┌─────────────────────────────────────────────┐
│    [ StaticCrossDataChecker ]     │                          │  [ PORequiredCriticalValidator ] │                           │      [ DynamicCrossDataValidator ]          │
│ Cross-validate static master data │                          │  Validate whether productRecords │                           │ Validate production records against         │
│     against dynamic records       │                          │      are aligned with PO DB      │                           │ standard references (mold, machine, resin)  │
└───────────────────────────────────┘                          └──────────────────────────────────┘                           └─────────────────────────────────────────────┘
                  │                                                             │                                                                     │
  Load schema & path annotations                             Load database schemas and path annotations                                 Load schema & path annotations
                  │                                                             │                                                                     │
 Validate input DataFrames by schema                         ┌────────────────────────────────────────┐                        Validate input DataFrames by schema (decorator)
                  │                                          │ Validate input DataFrames using schema │                                               │
Load all required DataFrames from path annotations           └────────────────────────────────────────┘                        Load required DataFrames from path annotations:
                  │                                                             │                                                                     │
┌──────────────────────────────────────────┐              ┌─────────────────────────────────────────────────────┐                         ┌────────────────────────┐
│ For each checking_df_name (productRecords│              │ Load productRecords and purchaseOrders parquet files│                         │ Prepare production data│
│ or purchaseOrders):                      │              └─────────────────────────────────────────────────────┘                         └────────────────────────┘
└──────────────────────────────────────────┘                                    │                                                                     │
                 │                                                Rename poNote → poNo in productRecords                                   ┌──────────────────────┐
┌─────────────────────────────────────────┐                       Remove rows with null poNo                                               │ Prepare standard data│
│ Process dataframe (rename poNote → poNo)│                                     │                                                          └──────────────────────┘
│ Drop rows with null values if needed    │                     Compare PO numbers across both datasets                                               │
└─────────────────────────────────────────┘                                     ▼                                               ┌────────────────────────────────────────────────┐ 
                │                                         ┌──────────────────────────────────────────────────────┐              │ Check for invalid data (nulls in critical cols)│
Run static validations in sequence:                       │ Identify missing POs in purchaseOrders → log warnings│              │ → Generate invalid warnings if found           │  
                ▼                                         └──────────────────────────────────────────────────────┘              └────────────────────────────────────────────────┘    
┌───────────────────────────────────────────────────┐                           │                                                                     │
│ [1] Validate itemInfo consistency                 │     ┌──────────────────────────────────────────────────────────────┐               ┌────────────────────────────┐ 
│→ Check if (itemCode + itemName) exists in itemInfo│     │ Filter valid POs from both datasets                          │               │ Compare production vs.     │
└───────────────────────────────────────────────────┘     │ Merge productRecords and purchaseOrders on poNo              │               │ standard at multiple levels│ 
                ▼                                         │ Vectorized comparison for overlapping fields (excluding poNo)│               └────────────────────────────┘   
┌───────────────────────────────────┐                     │   → Generate match columns per field and final_match column  │                            │
│ [2] Validate resinInfo consistency│                     └──────────────────────────────────────────────────────────────┘             ┌───────────────────────────────────────────┐
│ → Check each resin type (plastic, │                                           │                                                      │ Generate mismatch warnings for each level:│      
│color, additive) in resinInfo      │                     ┌───────────────────────────────────────────────────────────────────────┐    │ • item_warnings                           │   
└───────────────────────────────────┘                     │ Identify rows with mismatched fields → generate mismatchType & warning│    │ • item_mold_warnings                      │    
                ▼                                         │ Format warning messages with context: poNo, date, shift, machineNo    │    │ • mold_machine_tonnage_warnings           │     
┌──────────────────────────────────────────┐              └───────────────────────────────────────────────────────────────────────┘    │ • item_composition_warnings               │      
│ [3] Validate itemCompositionSummary      │                                    │                                                      └───────────────────────────────────────────┘
│ → Validate full composition of itemCode, │                Combine invalid PO warnings + field mismatch warnings into a list                          │
│resins against summary table              │                                    │                                                                      │
└──────────────────────────────────────────┘              ┌─────────────────────────────────────────────────────────────────────┐                      │
                ▼                                         │ Output result as DataFrame with columns:                            │                      │ 
┌──────────────────────────────────────┐                  │ ['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message']│                      │ 
│ Generate warnings for all mismatches:│                  └─────────────────────────────────────────────────────────────────────┘                      │ 
│ - Include poNo, mismatchType,        │                                        │                                                                      │
│requiredAction, and context message   │                                        │                                                                      │
└──────────────────────────────────────┘                                        │                                                                      │
               ▼                                                                │                                                                      ▼
Combine all warning entries into                                                │                                                    Combine all invalid + mismatch warnings
one result per checking_df_name                                                 │                                                                      ▼           
               ▼                                                                │                                                          Return results as DataFrames
Return or export result DataFrames                                              │                                                                      ▼
to Excel with version control                                     Save to Excel file with versioning if enabled                          Save result to versioned Excel file
               └────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────┘
                                                                                │
                                                              Merge all warnings: static + dynamic + PO
                                                                                ▼
                                              ┌──────────────────────────────────────────────────────────────────┐
                                              │ Export merged results to Excel using save_output_with_versioning │
                                              └──────────────────────────────────────────────────────────────────┘
```

## II. Detailed Steps

### Initialization

- 📂 Load database schema: `databaseSchemas.json`
- 📂 Load path annotations: `path_annotations.json`

- 📊 Load 8 required datasets:
  - **Dynamic**:
    - `productRecords`
    - `purchaseOrders`
  - **Static**:
    - `itemInfo`
    - `resinInfo`
    - `machineInfo`
    - `moldSpecificationSummary`
    - `moldInfo`
    - `itemCompositionSummary`

- ✅ Validate required columns via `@validate_init_dataframes` decorator

---

## III. Validation Stages

### 📌 Stage 1. StaticCrossDataChecker
- Ensures static master data (`itemInfo`, `machineInfo`, etc.) align with actual entries in `productRecords` and `purchaseOrders`

#### Detailed Steps

##### Initialization

- ✅ Accepts checking target: either `productRecords` or `purchaseOrders`  
- 📂 Load:
  - `databaseSchemas.json`  
  - `path_annotations.json`
- 📊 Load required datasets:
  - `itemInfo`
  - `resinInfo`
  - `itemCompositionSummary`
  - `productRecords`
  - `purchaseOrders`

##### Preprocessing

- Rename `poNote` → `poNo` (only for `productRecords`)
- Drop rows with:
  - `null` PO
  - `null` component values

---
##### Validation
1. **Item Info Validation**

- Match `(itemCode, itemName)` pairs with `itemInfo`
- ⚠️ Warn on mismatches

---

2.  **Resin Info Validation**

- For each resin type:
  - `plasticResin`
  - `colorMasterbatch`
  - `additiveMasterbatch`
- Validate code-name pairs

---

3.  **Composition Validation**

- Match full compositions against `itemCompositionSummary`

---

###### Output

- 📝 Warnings formatted consistently as:  
  `poNo`, `warningType`, `mismatchType`, `requiredAction`, `message`
- 📤 Export results:
  - Version-controlled Excel file per dataset

---

###### Input/Output

| Stage           | Input                              | Output                        |
|------------------|-------------------------------------|-------------------------------|
| **Initialization** | `databaseSchemas.json`, `path_annotations.json` | Validated schema & paths     |
| **Loading**        | All referenced `.parquet` files    | Internal DataFrames           |
| **Validation**     | `productRecords` / `purchaseOrders` | Warning DataFrame             |
| **Export**         | Combined result                   | Versioned Excel output        |


---

### 📌 Stage 2. PORequiredCriticalValidator

- Validates that every `poNo` in `productRecords` exists in `purchaseOrders`
- Compares overlapping fields for consistency

#### Detailed Steps

##### Initialization

* Load `databaseSchemas.json` and `path_annotations.json`
* Validate presence of required parquet files for `productRecords` and `purchaseOrders`

##### Preprocessing

* Rename `poNote` to `poNo`
* Drop rows with null `poNo`

##### Validation

1. **PO Number Validation**

   * Identify PO numbers in `productRecords` that do not exist in `purchaseOrders`
   * Log warnings for these missing PO numbers

2. **Field Value Validation**

   * Identify overlapping fields between the two datasets
   * Merge records on `poNo`
   * Vectorized comparison of overlapping fields
   * Flag rows where values do not match
   * Build warning entries for each mismatched row

##### Output

* Combine warnings into a final DataFrame
* Generate summary statistics (valid, invalid, mismatches)
* Export results to an Excel file with automatic version control

---

##### Input/Output

| Stage          | Input                                              | Output                 |
| -------------- | -------------------------------------------------- | ---------------------- |
| Initialization | `databaseSchemas.json`, `path_annotations.json`    | Validated DataFrames   |
| Validation     | `productRecords.parquet`, `purchaseOrders.parquet` | Warning DataFrame      |
| Export         | Final results                                      | Versioned Excel report |

---

### 📌 Stage 3. DynamicCrossDataValidator

- Checks logical consistency between dynamic dataframes
- Flags item mismatches or missing references

#### Detailed Steps

##### Initialization

- Load `databaseSchemas.json` → Validate expected columns  
- Load `path_annotations.json` → Locate `.parquet` paths  
- Ensure required data is available and accessible

---

Load 5 required datasets:
- `productRecords_df` *(dynamic)*
- `machineInfo_df`
- `moldSpecificationSummary_df`
- `moldInfo_df`
- `itemCompositionSummary_df`

---

##### Preprocessing

🔸 Production Data:

- Remove entries with missing `poNote`.
- Generate `item_composition` from `plastic`, `color`, `additive` info.
- Merge with `machineInfo_df` to include `machineTonnage`.

🔸 Standard Reference Data:

- Explode multiple `moldNo` per item.
- Merge `moldSpecificationSummary_df` + `moldInfo_df` → build standard mold-machine map.
- Join with `itemCompositionSummary_df` to build valid item compositions.

---
##### Validation
1. **Item Info Validation**

- Match `(itemCode, itemName)` against `itemInfo`
- ⚠️ Warn on mismatches

2. **Item Specification Cross-check**

- Match `(itemCode, itemName)` against `itemSpecificationSummary`
- Validate composition: resin, masterbatch, additive
- ⚠️ Warn on composition mismatches

3. **Mold Info Validation**

- Check `(moldCode, moldType)` against `moldInfo_df`
- Optionally validate `cavity` count
- ⚠️ Warn on:
  - Unknown moldCode
  - Mismatched moldType

4. **Mold Specification Cross-check**

- Match `(itemCode, moldCode)` against `moldSpecificationSummary_df`
- Validate:
  - Item–mold compatibility
  - Mold tonnage vs assigned machine
- ⚠️ Warn on mismatches

---

##### Input/Output

| Stage             | Input                                | Output                        |
|------------------|---------------------------------------|-------------------------------|
| **Initialization** | `databaseSchemas.json`, `path_annotations.json` | Validated schema & paths     |
| **Loading**        | All referenced `.parquet` files      | Internal DataFrames           |
| **Validation**     | `productRecords` / `purchaseOrders`  | Warning DataFrame             |
| **Export**         | Combined result                      | Versioned Excel output        |


---

## IV. Output Summary

- Combine all warnings into categories:
  - `static_mismatch`: issues in static data
  - `po_required_mismatch`: mismatches or missing POs
  - `dynamic_mismatch`: invalid items or fields

- 📤 Save final results as Excel report with **automatic versioning**

---

## V. Input/Output

| Stage          | Input Files                        | Output                              |
|----------------|------------------------------------|-------------------------------------|
| **Initialization** | Parquet datasets + JSON annotations | Loaded & validated DataFrames        |
| **Validation**     | Dynamic and Static DataFrames       | Dict of mismatch warning DataFrames |
| **Export**         | Combined results                    | Excel file with versioned filename  |
