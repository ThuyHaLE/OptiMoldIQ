# OptiMoldIQ Database Schema Documentation

## 1. Static Database Schema

### Table: `itemInfo`
| Field    | Type    | Description |
|----------|--------|-------------|
| itemCode | VARCHAR | Unique identifier for the item (**Primary Key**). |
| itemName | VARCHAR | Descriptive name of the item. |

---

### Table: `moldInfo`
| Field             | Type    | Description |
|------------------|--------|-------------|
| moldNo          | VARCHAR | Unique identifier for the mold (**Primary Key**). |
| moldName        | VARCHAR | Name of the mold. |
| cavityStandard  | INT     | Standard number of cavities in the mold. |
| settingCycleTime | INT    | Standard cycle time for the mold (in seconds). |
| machineTonnage  | VARCHAR | Required tonnage of the machine for this mold. |

**Foreign Keys:**  
- `moldNo` references `moldSpecification.moldNo`.

---

### Table: `resinInfo`
| Field      | Type    | Description |
|-----------|--------|-------------|
| resinCode | VARCHAR | Unique code for the resin (**Primary Key**). |
| resinName | VARCHAR | Name of the resin. |
| resinType | VARCHAR | Type/category of the resin. |
| colorType | VARCHAR | Color classification of the resin. |

---

### Table: `machineInfo`
| Field             | Type      | Description |
|-------------------|----------|-------------|
| machineNo        | INT       | Unique identifier for the machine (**Primary Key**). |
| machineCode      | VARCHAR   | Internal code for tracking the machine. |
| machineName      | VARCHAR   | Name or model of the machine. |
| manufacturerName | VARCHAR   | Name of the machine manufacturer. |
| machineTonnage   | INT       | Tonnage rating of the machine. |
| changedTime      | INT       | Time duration for which the machine was operational. |
| layoutStartDate  | DATETIME  | Date when the machine was placed in the current layout. |
| layoutEndDate    | DATETIME  | Date when the machine was removed from the layout. |
| previousMachineCode | VARCHAR | Code of the machine replaced by this machine. |

**Foreign Keys:**  
- `machineNo` references `productionStatus.machineNo`.

---

### Table: `itemCompositionSummary`
| Field                     | Type    | Description |
|---------------------------|--------|-------------|
| itemCode                  | VARCHAR | Item code (**Foreign Key** references `itemInfo.itemCode`). |
| resinCode                 | VARCHAR | Code for the resin used (**Foreign Key** references `resinInfo.resinCode`). |
| resinQuantity             | INT     | Quantity of resin used (kg). |
| colorMasterbatchCode      | VARCHAR | Code for the color masterbatch. |
| colorMasterbatchQuantity  | INT     | Quantity of color masterbatch used (kg). |
| additiveMasterbatchCode   | VARCHAR | Code for the additive masterbatch. |
| additiveMasterbatchQuantity | INT   | Quantity of additive masterbatch used (kg). |

---

### Table: `moldSpecification`
| Field     | Type    | Description |
|----------|--------|-------------|
| itemCode | VARCHAR | Item code (**Foreign Key** references `itemInfo.itemCode`). |
| itemType | VARCHAR | Type/category of the item. |
| moldNo   | VARCHAR | Mold number used for this item (**Foreign Key** references `moldInfo.moldNo`). |
| moldName | VARCHAR | Name of the mold. |
| moldNum  | INT     | Number of molds required for this item. |
| moldList | VARCHAR | List of molds related to this item. |

---

## 2. Dynamic Database Schema (Frequent Updates)

### Table: `poList`
| Field          | Type      | Description |
|--------------|----------|-------------|
| poNo        | VARCHAR   | Unique purchase order number (**Primary Key**). |
| poDate      | DATETIME  | Date when the purchase order was created. |
| poETA       | DATETIME  | Expected arrival date of the purchase order. |
| poReceivedDate | DATETIME | Date when the purchase order was received. |
| itemCode    | VARCHAR   | Code of the item ordered (**Foreign Key** references `itemInfo.itemCode`). |
| itemQuantity | INT      | Total quantity of items ordered. |
| resinCode   | VARCHAR   | Resin used (**Foreign Key** references `resinInfo.resinCode`). |
| resinQuantity | INT     | Quantity of resin ordered (kg). |

---

### Table: `productRecords`
| Field          | Type      | Description |
|--------------|----------|-------------|
| recordDate   | DATETIME  | Date when the production record was created. |
| shift        | VARCHAR   | Shift during which the production record was logged. |
| machineNo    | INT       | Machine used (**Foreign Key** references `machineInfo.machineNo`). |
| itemCode     | VARCHAR   | Item produced (**Foreign Key** references `itemInfo.itemCode`). |
| moldNo       | VARCHAR   | Mold used (**Foreign Key** references `moldInfo.moldNo`). |
| moldShot     | INT       | Number of shots taken with the mold. |
| itemTotalQty | INT       | Total number of items produced. |
| itemGoodQty  | INT       | Number of good-quality items produced. |
| itemDefects  | JSON      | Defect data (e.g., black spots, oil deposits, etc.). |
| resinCode    | VARCHAR   | Resin used (**Foreign Key** references `resinInfo.resinCode`). |

---

## 3. Main Database Schema (Live Tracking)

### Table: `productionStatus`
| Field        | Type      | Description |
|------------|----------|-------------|
| poNo       | VARCHAR   | Purchase order number (**Foreign Key** references `poList.poNo`). |
| itemCode   | VARCHAR   | Item being produced (**Foreign Key** references `itemInfo.itemCode`). |
| moldNo     | VARCHAR   | Mold in use (**Foreign Key** references `moldInfo.moldNo`). |
| machineNo  | INT       | Machine in use (**Foreign Key** references `machineInfo.machineNo`). |
| itemQuantity | INT     | Total quantity to be produced. |
| itemRemain | INT       | Remaining quantity to be produced. |
| startedDate | DATETIME  | Production start date. |
| finishedDate | DATETIME | Production completion date. |
| proStatus  | VARCHAR   | Current production status (e.g., "Molding", "Completed"). |

---

## 4. Additional Tables for Tracking & Analytics

### Table: `moldUsageHistory` (Tracks mold lifespan)
| Field     | Type      | Description |
|----------|----------|-------------|
| moldNo   | VARCHAR   | Mold used (**Foreign Key** references `moldInfo.moldNo`). |
| machineNo | INT       | Machine in use (**Foreign Key** references `machineInfo.machineNo`). |
| startDate | DATETIME  | Start date of mold usage. |
| endDate   | DATETIME  | End date of mold usage. |
| shotCount | INT       | Number of shots used before maintenance. |

---

### Table: `downtimeRecords` (Tracks production downtime)
| Field         | Type      | Description |
|-------------|----------|-------------|
| machineNo   | INT       | Machine affected (**Foreign Key** references `machineInfo.machineNo`). |
| downtimeStart | DATETIME | Start time of the downtime. |
| downtimeEnd | DATETIME | End time of the downtime. |
| reason      | VARCHAR   | Reason for the downtime. |
