# AutoPlanner Output

The `AutoPlanner` runs two workflows: **HistoricalFeaturesExtractor** (computing mold stability metrics and feature weights from historical data) and **InitialPlanner** (generating production schedules for pending and in-progress orders).

---

## HistoricalFeaturesExtractor

### `mold_stability_index_calculator_result.xlsx`

Stability indices and capacity estimates for each mold, derived from historical production records.

**Sheet: `moldStabilityIndex`**

| Column | Type | Description |
|---|---|---|
| `moldNo` | `str` | Mold identifier |
| `moldName` | `str` | Mold name |
| `acquisitionDate` | `datetime` | Date mold was acquired |
| `machineTonnage` | `str` | Compatible machine tonnages (e.g. `50/100/130/180`) |
| `moldCavityStandard` | `int` | Standard cavity count |
| `moldSettingCycle` | `int` | Standard cycle time setting (seconds) |
| `cavityStabilityIndex` | `float` | Cavity stability score (0–1). Higher = more consistent cavity usage across records |
| `cycleStabilityIndex` | `float` | Cycle time stability score (0–1). Higher = more consistent cycle times |
| `theoreticalMoldHourCapacity` | `float` | Theoretical max output (items/hour) based on standard cavity and cycle |
| `effectiveMoldHourCapacity` | `float` | Effective output (items/hour) based on observed cavity and cycle averages |
| `estimatedMoldHourCapacity` | `float` | Estimated output (items/hour) blending theoretical and effective values |
| `balancedMoldHourCapacity` | `float` | Final balanced capacity used for planning, conservative estimate |
| `totalRecords` | `int` | Number of production records used |
| `totalCavityMeasurements` | `int` | Number of cavity observations |
| `totalCycleMeasurements` | `int` | Number of cycle time observations |
| `firstRecordDate` | `datetime` | Earliest production record date |
| `lastRecordDate` | `datetime` | Latest production record date |

---

### `weights_hist.xlsx`

Cumulative log of feature weight changes over time. Unlike other outputs, this file is **not versioned** — it is appended to on each run and lives directly under the `MoldMachineFeatureWeightCalculator/` directory, outside of `newest/`.

**Sheet: `Sheet1`**

| Column | Type | Description |
|---|---|---|
| `shiftNGRate` | `float` | Weight assigned to shift NG rate feature |
| `shiftCavityRate` | `float` | Weight assigned to shift cavity rate feature |
| `shiftCycleTimeRate` | `float` | Weight assigned to shift cycle time rate feature |
| `shiftCapacityRate` | `float` | Weight assigned to shift capacity rate feature |
| `change_timestamp` | `str` | Timestamp of this weight update (`YYYY-MM-DD HH:MM:SS`) |

Each row represents one update. Weights are used by the mold-machine priority scoring model.

---

## InitialPlanner

### `pending_order_planner_result.xlsx`

Initial machine assignment plan for pending (not yet started) orders.

**Sheet: `mold_machine_priority_matrix`**

Priority score matrix: rows = molds, columns = machines. Each cell contains an integer priority score indicating how well-suited that mold is for that machine. Higher score = higher priority. Zero means incompatible or not prioritized.

| Axis | Values |
|---|---|
| Rows | Mold numbers (index) |
| Columns | Machine codes (e.g. `MD50S-000`) |
| Cell value | `int` — priority score |

**Sheet: `initial_plan`**

The resulting machine assignment plan for pending orders.

| Column | Type | Description |
|---|---|---|
| `Machine No.` | `str` | Machine slot (e.g. `NO.01`) |
| `Machine Code` | `str` | Machine identifier |
| `Assigned Mold` | `str` | Mold assigned to this machine |
| `PO No.` | `str` | Purchase order number |
| `Item Name` | `str` | Product name |
| `PO Quantity` | `int` | Order target quantity |
| `ETA (PO Date)` | `datetime` | Order due date |
| `Mold Lead Time` | `int` | Estimated lead time for this mold (days) |
| `Priority in Machine` | `int` | Queue priority for this machine |
| `Note` | `str` | Planning basis note (e.g. `histBased`) |

**Sheet: `not_matched_pending`**

Pending orders that could not be matched to any machine.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `date` | Order due date |
| `itemQuantity` | `int` | Order target quantity |

**Sheet: `note`**

Summary of mold assignment outcomes for this planning run.

| Column | Type | Description |
|---|---|---|
| `invalid_molds` | `str` | Comma-separated molds excluded due to invalid data |
| `assigned_molds` | `str` | Comma-separated molds successfully assigned |
| `unassigned_molds` | `str` | Molds that could not be assigned |
| `overloaded_machines` | `str` | Machines with more assignments than capacity |

---

### `producing_order_planner_result.xlsx`

Planning data for orders currently in production, including capacity estimates, progress status, and material requirements.

**Sheet: `mold_estimated_capacity`**

Capacity estimates for all molds relevant to active orders.

| Column | Type | Description |
|---|---|---|
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `itemType` | `str` | Product type classification |
| `moldNum` | `int` | Number of molds for this item |
| `moldNo` | `str` | Mold identifier |
| `moldName` | `str` | Mold name |
| `acquisitionDate` | `datetime` | Mold acquisition date |
| `moldCavityStandard` | `int` | Standard cavity count |
| `moldSettingCycle` | `int` | Standard cycle time (seconds) |
| `machineTonnage` | `str` | Compatible machine tonnages |
| `theoreticalMoldHourCapacity` | `float` | Theoretical max output (items/hour) |
| `balancedMoldHourCapacity` | `float` | Balanced capacity used for planning (items/hour) |
| `isPriority` | `bool` | Whether this mold is flagged as priority |

**Sheet: `invalid_mold_list`**

Molds excluded from planning due to missing or invalid data.

| Column | Type | Description |
|---|---|---|
| `invalid_molds` | `str` | Mold identifier |

**Sheet: `producing_status_data`**

Current production status for each in-progress order.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | Order due date |
| `moldNo` | `str` | Mold currently in use |
| `itemQuantity` | `int` | Order target quantity |
| `itemRemain` | `int` | Remaining quantity to produce |
| `machineNo` | `str` | Machine slot |
| `startedDate` | `datetime` | Production start date |
| `moldName` | `str` | Mold name |
| `theoreticalMoldHourCapacity` | `int` | Theoretical output (items/hour) |
| `balancedMoldHourCapacity` | `float` | Balanced output (items/hour) |
| `machineCode` | `str` | Machine identifier |
| `machineName` | `str` | Machine model name |
| `machineTonnage` | `int` | Machine tonnage |
| `leadTime` | `float` | Total estimated lead time (days) |
| `remainTime` | `float` | Remaining time to completion (days) |
| `finishedEstimatedDate` | `str` | Estimated completion datetime |
| `proProgressing` | `float` | Completion percentage (0–100) |
| `itemName_poNo` | `str` | Combined label: `{itemName} ({poNo})` |

**Sheet: `pending_status_data`**

Pending orders queued behind current in-production orders.

| Column | Type | Description |
|---|---|---|
| `poNo` | `str` | Purchase order number |
| `itemCode` | `str` | Product code |
| `itemName` | `str` | Product name |
| `poETA` | `str` | Order due date |
| `itemQuantity` | `int` | Order target quantity |

**Sheet: `producing_pro_plan`**

Per-machine view of current production order and remaining time.

| Column | Type | Description |
|---|---|---|
| `machineNo` | `str` | Machine slot |
| `machineCode` | `str` | Machine identifier |
| `machineName` | `str` | Machine model name |
| `machineTonnage` | `int` | Machine tonnage |
| `itemName_poNo` | `str` | Active order label |
| `remainTime` | `float` | Remaining production time (days) |

**Sheet: `producing_mold_plan`**

Per-machine view of current mold in use and remaining time.

| Column | Type | Description |
|---|---|---|
| `machineNo` | `str` | Machine slot |
| `machineCode` | `str` | Machine identifier |
| `machineName` | `str` | Machine model name |
| `machineTonnage` | `int` | Machine tonnage |
| `moldName` | `str` | Mold currently running |
| `remainTime` | `float` | Remaining production time (days) |

**Sheet: `producing_plastic_plan`**

Per-machine material requirements for the remaining production run.

| Column | Type | Description |
|---|---|---|
| `machineNo` | `str` | Machine slot |
| `machineCode` | `str` | Machine identifier |
| `machineName` | `str` | Machine model name |
| `machineTonnage` | `int` | Machine tonnage |
| `itemName_poNo` | `str` | Active order label |
| `estimatedOutputQuantity` | `float` | Estimated remaining output (items) |
| `plasticResin` | `str` | Plastic resin material |
| `estimatedPlasticResinQuantity` | `float` | Estimated resin needed (kg) |
| `colorMasterbatch` | `str` | Color masterbatch material (`NONE` if not used) |
| `estimatedColorMasterbatchQuantity` | `int` | Estimated color masterbatch needed (kg). `None` if not used |
| `additiveMasterbatch` | `str` | Additive masterbatch material (`NONE` if not used) |
| `estimatedAdditiveMasterbatchQuantity` | `int` | Estimated additive masterbatch needed (kg). `None` if not used |