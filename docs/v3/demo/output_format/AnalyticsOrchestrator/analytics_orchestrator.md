# AnalyticsOrchestrator Output

The `AnalyticsOrchestrator` runs two independent workflows: **Hardware Change Analysis** (tracking machine layout and mold-machine pairing history) and **Multi-Level Performance Analysis** (aggregating production records at day, month, and year granularity).

---

## HardwareChangeAnalyzer

### `machine_layout_tracker_result.xlsx`

Tracks which machine slot (e.g. `NO.10`) each machine was assigned to at each recorded layout change date.

**Sheet: `machineLayoutChange`**

| Column | Type | Description |
|---|---|---|
| `machineName` | `str` | Machine model name (e.g. `CNS50`) |
| `machineCode` | `str` | Unique machine identifier (e.g. `CNS50-000`) |
| `{date}` *(dynamic)* | `str` | Machine slot assigned on that layout change date. Empty if no change on that date |

> Column headers after `machineName` / `machineCode` are layout change dates (`YYYY-MM-DD`), one column per recorded change event.

---

### `mold_machine_pair_tracker_result.xlsx`

Tracks when each mold was first paired with each machine, and flags tonnage mismatches.

**Sheet: `moldTonageUnmatched`**

Records where a mold was run on a machine with incompatible tonnage.

| Column | Type | Description |
|---|---|---|
| `recordDate` | `date` | Date the mismatch was recorded |
| `machineCode` | `str` | Machine identifier |
| `moldNo` | `str` | Mold identifier |
| `suitedMachineTonnages` | `str` | Tonnage range the mold is suited for |
| `acquisitionDate` | `date` | Date the mold was acquired |
| `machineType` | `str` | Machine type |
| `tonnageMatched` | `bool` | Whether tonnage matched |

**Sheet: `machineMoldFirstRunPair`**

Matrix of first run dates: rows = machines, columns = molds. Cell value is the first date that machine ran that mold. Empty if the pair never ran.

| Axis | Values |
|---|---|
| Rows | Machine codes (e.g. `CNS50-000`) |
| Columns | Mold numbers (e.g. `14000CBQ-M-001`) |
| Cell value | `datetime` — first run date, or empty if never paired |

**Sheet: `moldMachineFirstRunPair`**

Transposed version of the above: rows = molds, columns = machines.

| Axis | Values |
|---|---|
| Rows | Mold numbers |
| Columns | Machine codes |
| Cell value | `datetime` — first run date, or empty if never paired |

---

## MultiLevelPerformanceAnalyzer

### `day_level_data_processor_result.xlsx`

Detailed production records for a single requested date.

**Sheet: `selectedDateFilter`** — Full job-level records for the requested date.

| Column | Type | Description |
|---|---|---|
| `recordDate` | `datetime` | Production date |
| `workingShift` | `int` | Shift number |
| `machineNo` | `str` | Machine slot (e.g. `NO.01`) |
| `machineCode` | `str` | Machine identifier |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `colorChanged` | `str` | Color change flag |
| `moldChanged` | `float` | Mold change flag |
| `machineChanged` | `float` | Machine change flag |
| `changeType` | `str` | Change classification (`no_change`, etc.) |
| `poNo` | `str` | Purchase order number |
| `moldNo` | `str` | Mold identifier |
| `moldShot` | `float` | Number of mold shots |
| `moldCavity` | `float` | Number of cavities |
| `itemTotalQuantity` | `float` | Total items produced |
| `itemGoodQuantity` | `float` | Good items |
| `itemBlackSpot` | `float` | Defect: black spot count |
| `itemOilDeposit` | `float` | Defect: oil deposit count |
| `itemScratch` | `float` | Defect: scratch count |
| `itemCrack` | `float` | Defect: crack count |
| `itemSinkMark` | `float` | Defect: sink mark count |
| `itemShort` | `float` | Defect: short shot count |
| `itemBurst` | `float` | Defect: burst count |
| `itemBend` | `float` | Defect: bend count |
| `itemStain` | `float` | Defect: stain count |
| `otherNG` | `float` | Other NG quantity |
| `plasticResin` | `str` | Resin material name |
| `plasticResinCode` | `float` | Resin code |
| `plasticResinLot` | `str` | Resin lot number |
| `colorMasterbatch` | `str` | Color masterbatch name |
| `colorMasterbatchCode` | `float` | Color masterbatch code |
| `additiveMasterbatch` | `float` | Additive masterbatch code |
| `additiveMasterbatchCode` | `float` | Additive masterbatch identifier |
| `itemQuantity` | `float` | PO target quantity |
| `poETA` | `datetime` | PO due date |
| `machineInfo` | `str` | Combined label: `{machineNo} ({machineCode})` |
| `itemInfo` | `str` | Combined label: `{itemCode} ({itemName})` |
| `itemComponent` | `str` | Tuple of material codes used |
| `itemCount` | `int` | Number of items in record |
| `moldCount` | `int` | Number of molds in record |
| `itemComponentCount` | `int` | Number of distinct material combos |
| `jobCount` | `int` | Number of jobs |
| `lateStatus` | `bool` | Whether PO is late |

**Sheet: `moldBasedRecords`** — Aggregated by mold per shift.

| Column | Type | Description |
|---|---|---|
| `machineInfo` | `str` | Machine label |
| `workingShift` | `int` | Shift number |
| `moldNo` | `str` | Mold identifier |
| `moldShot` | `float` | Total shots |
| `moldCavity` | `float` | Cavity count |
| `itemTotalQuantity` | `int` | Total produced |
| `itemGoodQuantity` | `int` | Good quantity |
| `changeType` | `str` | Change classification |
| `defectQuantity` | `int` | Total defects |
| `defectRate` | `float` | Defect rate (%) |

**Sheet: `itemBasedRecords`** — Aggregated by product across the full day.

| Column | Type | Description |
|---|---|---|
| `itemInfo` | `str` | Product label |
| `itemTotalQuantity` | `int` | Total produced |
| `itemGoodQuantity` | `int` | Good quantity |
| `usedMachineNums` | `int` | Number of machines used |
| `totalShifts` | `int` | Number of shifts worked |
| `usedMoldNums` | `int` | Number of molds used |
| `moldTotalShots` | `int` | Total mold shots |
| `avgCavity` | `float` | Average cavity count |
| `usedComponentNums` | `int` | Number of material combinations |
| `defectQuantity` | `int` | Total defects |
| `defectRate` | `float` | Defect rate (%) |

**Sheet: `summaryStatics`** — Day-level summary statistics.

| Column | Type | Description |
|---|---|---|
| `record_date` | `datetime` | The requested date |
| `total_records` | `int` | Total production records |
| `active_jobs` | `int` | Number of active jobs |
| `working_shifts` | `int` | Number of shifts |
| `machines` | `int` | Number of machines active |
| `purchase_orders` | `int` | Number of POs active |
| `products` | `int` | Number of distinct products |
| `molds` | `int` | Number of molds used |
| `late_pos` | `int` | Number of late POs |
| `total_pos_with_eta` | `int` | POs with an ETA set |
| `change_type_distribution` | `int` | Count of records with no change type |

---

### `month_level_data_processor_result.xlsx` / `year_level_data_processor_result.xlsx`

Both files share the same sheet structure. Month-level filters by the requested month; year-level filters by the requested year.

**Sheet: `filteredRecords`** — All PO records within the requested period.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `datetime` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `poETA` | `datetime` | PO due date |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `itemQuantity` | `int` | PO target quantity |
| `itemCodeName` | `str` | Combined label: `{itemCode}({itemName})` |
| `firstRecord` | `datetime` | First production date for this PO |
| `lastRecord` | `datetime` | Last production date for this PO |
| `itemGoodQuantity` | `float` | Good quantity produced |
| `itemNGQuantity` | `float` | NG quantity produced *(year-level only)* |
| `moldHistNum` | `float` | Number of distinct molds used |
| `moldHist` | `str` | Mold history list |
| `proStatus` | `str` | Production status (`finished`, `unfinished`) |
| `is_backlog` | `bool` | Whether this PO carried over from a prior period |
| `itemRemainQuantity` | `int` | Remaining quantity to produce |
| `poStatus` | `str` | PO status (`finished`, `not_started`, etc.) |
| `overproduction_quantity` | `int` | Quantity produced beyond PO target |

**Sheet: `finishedRecords`** — Subset of completed POs, with ETA status added.

Same columns as `filteredRecords`, plus:

| Column | Type | Description |
|---|---|---|
| `etaStatus` | `str` | Delivery status (`ontime`, `late`, etc.) |

**Sheet: `unfinishedRecords`** — Subset of incomplete POs, with capacity and lead time projections.

Same columns as `filteredRecords`, plus:

| Column | Type | Description |
|---|---|---|
| `moldNum` | `int` | Number of molds assigned |
| `moldList` | `str` | List of assigned molds |
| `totalItemCapacity` | `float` | Total daily capacity across all molds (items/day) |
| `avgItemCapacity` | `float` | Average daily capacity per mold (items/day) |
| `accumulatedQuantity` | `int` | Cumulative quantity needed |
| `completionProgress` | `float` | Completion rate (0–1) |
| `totalRemainByMold` | `int` | Remaining quantity per mold |
| `accumulatedRate` | `float` | Accumulated production rate |
| `totalEstimatedLeadtime` | `float` | Estimated lead time using total capacity (days) |
| `avgEstimatedLeadtime` | `float` | Estimated lead time using average capacity (days) |
| `poOTD` | `int` | Days until PO due date |
| `poRLT` | `int` | Remaining lead time (days) |
| `avgCumsumLT` | `float` | Average cumulative lead time |
| `totalCumsumLT` | `float` | Total cumulative lead time |
| `overTotalCapacity` | `bool` | Whether demand exceeds total capacity |
| `overAvgCapacity` | `bool` | Whether demand exceeds average capacity |
| `is_overdue` | `bool` | Whether PO is already overdue |
| `etaStatus` | `str` | Projected delivery status (`expected_ontime`, `expected_late`, etc.) |
| `capacityWarning` | `bool` | Whether a capacity warning is raised |
| `capacitySeverity` | `str` | Severity level (`normal`, `warning`, `critical`) |
| `capacityExplanation` | `str` | Human-readable capacity assessment |