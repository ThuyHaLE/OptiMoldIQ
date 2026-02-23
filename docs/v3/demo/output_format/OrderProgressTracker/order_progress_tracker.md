# OrderProgressTracker Output

The `OrderProgressTracker` consolidates production records into a per-PO progress view, with expanded detail sheets for mold usage, machine output, daily output, and material components. Warning sheets flag data inconsistencies detected during tracking.

---

## `progress_tracker_result.xlsx`

### Sheet: `productionStatus`

One row per PO. Summarizes the full production history and current status of each order.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `str` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity to produce |
| `startedDate` | `str` | First production date |
| `actualFinishedDate` | `str` | Last production date (or `None` if still in progress) |
| `proStatus` | `str` | Production status (e.g. `MOLDED`) |
| `etaStatus` | `str` | Delivery status (`ONTIME`, `LATE`, etc.) |
| `itemType` | `str` | Product type classification |
| `machineHist` | `str` | JSON list of machines used (e.g. `['NO.01_MD50S-000']`) |
| `moldList` | `str` | Primary mold identifier |
| `moldHist` | `str` | JSON list of molds used |
| `moldCavity` | `str` | JSON list of cavity counts per mold |
| `totalMoldShot` | `float` | Total mold shots across all runs |
| `totalDay` | `float` | Total working days |
| `totalShift` | `float` | Total working shifts |
| `plasticResinCode` | `str` | JSON list of resin codes used |
| `colorMasterbatchCode` | `str` | JSON list of color masterbatch codes used |
| `additiveMasterbatchCode` | `str` | JSON list of additive masterbatch codes used |
| `moldShotMap` | `str` | JSON dict: `{moldNo: totalShots}` |
| `machineQuantityMap` | `str` | JSON dict: `{machineCode: moldedQuantity}` |
| `dayQuantityMap` | `str` | JSON dict: `{date: moldedQuantity}` |
| `shiftQuantityMap` | `str` | JSON dict: `{date_shift_N: moldedQuantity}` |
| `materialComponentMap` | `str` | JSON list of material component combos used |
| `lastestRecordTime` | `datetime` | Timestamp of the most recent production record |
| `lastestMachineNo` | `str` | Machine slot of the most recent record |
| `lastestMoldNo` | `str` | Mold used in the most recent record |
| `warningNotes` | `str` | Warning messages if data issues were detected |

---

### Sheet: `materialComponentMap`

Exploded view of `productionStatus.materialComponentMap` — one row per PO per material combination used.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `str` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity |
| `startedDate` | `str` | First production date |
| `actualFinishedDate` | `str` | Last production date |
| `plasticResinCode` | `str` | Resin code for this component combo |
| `colorMasterbatchCode` | `str` | Color masterbatch code (`None` if not used) |
| `additiveMasterbatchCode` | `float` | Additive masterbatch code (`None` if not used) |
| `numOfMaterialComponent` | `int` | Total distinct material combos used for this PO |

---

### Sheet: `moldShotMap`

Exploded view of `productionStatus.moldShotMap` — one row per PO per mold used.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `str` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity |
| `startedDate` | `str` | First production date |
| `actualFinishedDate` | `str` | Last production date |
| `moldNo` | `str` | Mold identifier |
| `shotCount` | `int` | Total shots by this mold for this PO |
| `numOfMold` | `int` | Total distinct molds used for this PO |

---

### Sheet: `machineQuantityMap`

Exploded view of `productionStatus.machineQuantityMap` — one row per PO per machine used.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `str` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity |
| `startedDate` | `str` | First production date |
| `actualFinishedDate` | `str` | Last production date |
| `machineCode` | `str` | Machine identifier (format: `{machineNo}_{machineCode}`) |
| `moldedQuantity` | `int` | Quantity produced by this machine for this PO |
| `numOfMachine` | `int` | Total distinct machines used for this PO |

---

### Sheet: `dayQuantityMap`

Exploded view of `productionStatus.dayQuantityMap` — one row per PO per working day.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `str` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | PO due date |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity |
| `startedDate` | `str` | First production date |
| `actualFinishedDate` | `str` | Last production date |
| `workingDay` | `str` | Production date (`YYYY-MM-DD`) |
| `moldedQuantity` | `int` | Quantity produced on this day for this PO |
| `numOfDay` | `int` | Total working days for this PO |

---

### Sheet: `notWorkingStatus`

Raw production records where output was zero — machines that were set up but produced nothing. Useful for detecting idle time or setup issues.

| Column | Type | Description |
|---|---|---|
| `recordDate` | `str` | Production date |
| `workingShift` | `int` | Shift number |
| `machineNo` | `str` | Machine slot (e.g. `NO.02`) |
| `machineCode` | `str` | Machine identifier |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `colorChanged` | `float` | Color change flag |
| `moldChanged` | `float` | Mold change flag |
| `machineChanged` | `float` | Machine change flag |
| `poNote` | `str` | Purchase order number |
| `moldNo` | `str` | Mold identifier |
| `moldShot` | `float` | Number of mold shots (0 for not-working records) |
| `moldCavity` | `float` | Number of cavities |
| `itemTotalQuantity` | `float` | Total items produced (0 for not-working records) |
| `itemGoodQuantity` | `float` | Good items (0 for not-working records) |
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
| `dateShiftCombined` | `str` | Combined key: `{date}_shift_{N}` |
| `machineHist` | `str` | Machine identifier: `{machineNo}_{machineCode}` |

---

### Sheet: `po_mismatch_warnings`

PO-level data inconsistencies detected during tracking.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Affected purchase order |
| `warningType` | `str` | Warning category |
| `mismatchType` | `str` | Specific mismatch type |
| `requiredAction` | `str` | Suggested corrective action |
| `message` | `str` | Full human-readable warning message |

---

### Sheet: `item_invalid_warnings`

Item-level data issues where product records could not be matched against reference data.

| Column | Type | Description |
|---|---|---|
| `itemInfo` | `str` | Affected item (`itemCode, itemName`) |
| `warningType` | `str` | Warning category |
| `mismatchType` | `str` | Specific mismatch type |
| `requiredAction` | `str` | Suggested corrective action |
| `message` | `str` | Full human-readable warning message |