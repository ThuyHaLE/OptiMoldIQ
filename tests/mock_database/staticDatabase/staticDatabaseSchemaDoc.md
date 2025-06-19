# Database Schema Documentation
## Table: `itemInfo`
| Field      | Type     | Description                              |
|------------|----------|------------------------------------------|
| itemCode   | varchar  | Unique identifier for the item.          |
| itemName   | varchar  | Descriptive name of the item.            |

---

## Table: `moldInfo`
| Field                 | Type     | Description                                         |
|-----------------------|----------|-----------------------------------------------------|
| moldNo               | varchar  | Unique identifier for the mold.                      |
| moldName             | varchar  | Name of the mold.                                    |
| moldCavityStandard   | integer  | Standard number of cavities in the mold.             |
| moldSettingCycle     | integer  | Standard cycle time for the mold (in seconds).       |
| machineTonnage       | varchar  | Required tonnage of the machine for this mold.       |

---

## Table: `resineInfo`
| Field       | Type     | Description                               |
|-------------|----------|-------------------------------------------|
| resineCode  | varchar  | Unique code for the resin.                |
| resineName  | varchar  | Name of the resin.                        |
| resineType  | varchar  | Type/category of the resin.               |
| colorType   | varchar  | Color classification of the resin.        |

---

## Table: `machineInfo`
| Field              | Type     | Description                                             |
|--------------------|----------|---------------------------------------------------------|
| machineNo          | integer  | Unique identifier for the machine.                      |
| machineCode        | varchar  | Internal code for tracking the machine.                 |
| machineName        | varchar  | Name or model of the machine.                           |
| manufacturerName   | varchar  | Name of the machine manufacturer.                       |
| machineTonnage     | integer  | Tonnage rating of the machine.                          |
| changedTime        | integer  | Time duration for which the machine was operational.    |
| layoutStartDate    | datetime | Date when the machine was placed in the current layout. |
| layoutEndDate      | datetime | Date when the machine was removed from the layout.      |
| previousMachineCode| varchar  | Code of the machine replaced by this machine.           |

---

## Table: `itemCompositionSummary`
| Field                      | Type     | Description                                   |
|----------------------------|----------|-----------------------------------------------|
| plasticResinCode           | varchar  | Code for the plastic resin used.              |
| colorMasterbatchCode       | varchar  | Code for the color masterbatch used.          |
| additiveMasterbatchCode    | varchar  | Code for the additive masterbatch used.       |
| plasticResin               | varchar  | Name of the plastic resin used.               |
| colorMasterbatch           | varchar  | Name of the color masterbatch used.           |
| additiveMasterbatch        | varchar  | Name of the additive masterbatch used.        |
| plasticResinQuantity       | integer  | Quantity of plastic resin used (in kg).       |
| colorMasterbatchQuantity   | integer  | Quantity of color masterbatch used (in kg).   |
| additiveMasterbatchQuantity| integer  | Quantity of additive masterbatch used (in kg).|
| itemCode                   | varchar  | Item code for which these compositions apply. |
| itemName                   | varchar  | Name of the item for which compositions apply.|

---

## Table: `moldSpecification`
| Field       | Type     | Description                                                  |
|-------------|----------|--------------------------------------------------------------|
| itemCode    | varchar  | Item code associated with the mold.                          |
| itemName    | varchar  | Name of the item associated with the mold.                   |
| itemType    | varchar  | Type/category of the item.                                   |
| moldNo      | varchar  | Mold number used for this item.                              |
| moldName    | varchar  | Name of the mold.                                            |
| moldStatus  | varchar  | Current status of the mold (e.g., active, under maintenance).|
| moldNum     | integer  | Number of molds required for this item.                      |
| moldList    | varchar  | List of molds related to this item.                          |