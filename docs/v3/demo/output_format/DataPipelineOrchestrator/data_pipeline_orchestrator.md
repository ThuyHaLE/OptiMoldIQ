# DataPipelineOrchestrator Output

The `DataPipelineOrchestrator` collects and normalizes raw data from the source database into a set of clean reference and transactional tables. All outputs are stored as `.parquet` files — the foundational input for all downstream modules.

---

## Reference Tables

### `itemInfo.parquet`

Master list of all product items.

| Column | Type | Description |
|---|---|---|
| `itemCode` | `str` | Unique product code |
| `itemName` | `str` | Product name |

---

### `machineInfo.parquet`

Machine registry including layout history. Each row represents one machine slot assignment period.

| Column | Type | Description |
|---|---|---|
| `machineNo` | `str` | Machine slot (e.g. `NO.01`) |
| `machineCode` | `str` | Unique machine identifier (e.g. `MD50S-000`) |
| `machineName` | `str` | Machine model name |
| `manufacturerName` | `str` | Manufacturer name |
| `machineTonnage` | `int` | Machine tonnage (tons) |
| `changedTime` | `int` | Number of layout changes for this machine |
| `layoutStartDate` | `datetime` | Start date of this slot assignment |
| `layoutEndDate` | `datetime` | End date of this slot assignment (`NaT` if currently active) |
| `previousMachineCode` | `str` | Machine code that previously occupied this slot |

---

### `moldInfo.parquet`

Master list of all molds with physical specifications.

| Column | Type | Description |
|---|---|---|
| `moldNo` | `str` | Unique mold identifier |
| `moldName` | `str` | Mold name |
| `moldCavityStandard` | `int` | Standard cavity count |
| `moldSettingCycle` | `int` | Standard cycle time setting (seconds) |
| `machineTonnage` | `str` | Compatible machine tonnages (e.g. `50/100/130/180`) |
| `acquisitionDate` | `datetime` | Date mold was acquired |
| `itemsWeight` | `float` | Weight of items per shot (kg) |
| `runnerWeight` | `float` | Weight of runner per shot (kg) |

---

### `resinInfo.parquet`

Master list of all plastic resin materials.

| Column | Type | Description |
|---|---|---|
| `resinCode` | `str` | Unique resin code |
| `resinName` | `str` | Resin material name |
| `resinType` | `str` | Resin type classification |
| `colorType` | `str` | Color type (e.g. natural, colored) |

---

### `moldSpecificationSummary.parquet`

Mapping of items to their assigned molds.

| Column | Type | Description |
|---|---|---|
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `itemType` | `str` | Product type classification |
| `moldNum` | `int` | Number of molds assigned to this item |
| `moldList` | `str` | Comma-separated list of assigned mold identifiers |

---

### `itemCompositionSummary.parquet`

Material composition for each item — the resin and masterbatch combination used per product.

| Column | Type | Description |
|---|---|---|
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `plasticResinCode` | `str` | Resin code |
| `plasticResin` | `str` | Resin material name |
| `plasticResinQuantity` | `float` | Resin quantity per shot (kg) |
| `colorMasterbatchCode` | `str` | Color masterbatch code (`None` if not used) |
| `colorMasterbatch` | `str` | Color masterbatch name (`None` if not used) |
| `colorMasterbatchQuantity` | `float` | Color masterbatch quantity per shot (kg). `None` if not used |
| `additiveMasterbatchCode` | `str` | Additive masterbatch code (`None` if not used) |
| `additiveMasterbatch` | `str` | Additive masterbatch name (`None` if not used) |
| `additiveMasterbatchQuantity` | `float` | Additive masterbatch quantity per shot (kg). `None` if not used |

---

## Transactional Tables

### `purchaseOrders.parquet`

All purchase orders with target quantities and material requirements.

| Column | Type | Description |
|---|---|---|
| `poReceivedDate` | `datetime` | Date PO was received |
| `poNo` | `str` | Purchase order number |
| `poETA` | `datetime` | PO due date |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `itemQuantity` | `int` | Order target quantity |
| `plasticResinCode` | `str` | Required resin code |
| `plasticResin` | `str` | Required resin name |
| `plasticResinQuantity` | `float` | Required resin quantity (kg) |
| `colorMasterbatchCode` | `str` | Required color masterbatch code (`None` if not used) |
| `colorMasterbatch` | `str` | Required color masterbatch name (`None` if not used) |
| `colorMasterbatchQuantity` | `float` | Required color masterbatch quantity (kg). `None` if not used |
| `additiveMasterbatchCode` | `str` | Required additive masterbatch code (`None` if not used) |
| `additiveMasterbatch` | `str` | Required additive masterbatch name (`None` if not used) |
| `additiveMasterbatchQuantity` | `float` | Required additive masterbatch quantity (kg). `None` if not used |

---

### `productRecords.parquet`

Raw production records — one row per machine per shift per job. The primary transactional table used by all analytical modules.

| Column | Type | Description |
|---|---|---|
| `recordDate` | `datetime` | Production date |
| `workingShift` | `str` | Shift identifier |
| `machineNo` | `str` | Machine slot (e.g. `NO.01`) |
| `machineCode` | `str` | Machine identifier |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `colorChanged` | `str` | Color change flag |
| `moldChanged` | `str` | Mold change flag |
| `machineChanged` | `str` | Machine change flag |
| `poNote` | `str` | Associated purchase order number |
| `moldNo` | `str` | Mold identifier |
| `moldShot` | `int` | Number of mold shots |
| `moldCavity` | `int` | Number of cavities |
| `itemTotalQuantity` | `int` | Total items produced |
| `itemGoodQuantity` | `int` | Good items produced |
| `itemBlackSpot` | `int` | Defect: black spot count |
| `itemOilDeposit` | `int` | Defect: oil deposit count |
| `itemScratch` | `int` | Defect: scratch count |
| `itemCrack` | `int` | Defect: crack count |
| `itemSinkMark` | `int` | Defect: sink mark count |
| `itemShort` | `int` | Defect: short shot count |
| `itemBurst` | `int` | Defect: burst count |
| `itemBend` | `int` | Defect: bend count |
| `itemStain` | `int` | Defect: stain count |
| `otherNG` | `int` | Other NG quantity |
| `plasticResin` | `str` | Resin material name used |
| `plasticResinCode` | `str` | Resin code used |
| `plasticResinLot` | `str` | Resin lot number |
| `colorMasterbatch` | `str` | Color masterbatch name used (`None` if not used) |
| `colorMasterbatchCode` | `str` | Color masterbatch code used (`None` if not used) |
| `additiveMasterbatch` | `str` | Additive masterbatch name used (`None` if not used) |
| `additiveMasterbatchCode` | `str` | Additive masterbatch code used (`None` if not used) |