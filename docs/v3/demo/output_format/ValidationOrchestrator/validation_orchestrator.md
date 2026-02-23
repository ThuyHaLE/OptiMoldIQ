# ValidationOrchestrator Output

The `ValidationOrchestrator` cross-checks production records against reference databases and flags inconsistencies that require manual review or data correction before downstream modules can process them reliably.

---

## `validation_orchestrator_result.xlsx`

### Sheet: `po_mismatch_warnings`

PO-level inconsistencies where production record data does not match the reference item database.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Affected purchase order number |
| `warningType` | `str` | Warning category (e.g. `item_warnings`) |
| `mismatchType` | `str` | Specific mismatch type (e.g. `item_info_not_matched`) |
| `requiredAction` | `str` | Suggested corrective action (e.g. `update_itemInfo_or_double_check_productRecords`) |
| `message` | `str` | Full human-readable description of the mismatch, including the affected record context |

---

### Sheet: `item_invalid_warnings`

Item-level issues where a product referenced in production records does not exist in the item composition reference database.

| Column | Type | Description |
|---|---|---|
| `itemInfo` | `str` | Affected item, formatted as `{itemCode}, {itemName}` |
| `warningType` | `str` | Warning category (e.g. `item_invalid_in_itemCompositionSummary`) |
| `mismatchType` | `str` | Specific mismatch type (e.g. `item_does_not_exist_in_itemCompositionSummary`) |
| `requiredAction` | `str` | Suggested corrective action (e.g. `update_itemCompositionSummary_or_double_check_related_databases`) |
| `message` | `str` | Full human-readable description of the issue |