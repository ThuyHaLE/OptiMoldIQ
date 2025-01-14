# Static Database Schema Documentation
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

---***---

# Dynamic Database Schema Documentation

## Table: `poList`
| Field                       | Type      | Description                                          |
|-----------------------------|-----------|------------------------------------------------------|
| plasticResinCode            | varchar   | Code for the plastic resin ordered.                  |
| colorMasterbatchCode        | varchar   | Code for the color masterbatch ordered.              |
| additiveMasterbatchCode     | varchar   | Code for the additive masterbatch ordered.           |
| plasticResin                | varchar   | Name of the plastic resin ordered.                   |
| colorMasterbatch            | varchar   | Name of the color masterbatch ordered.               |
| additiveMasterbatch         | varchar   | Name of the additive masterbatch ordered.            |
| plasticResinQuantity        | integer   | Quantity of plastic resin ordered (in kg).           |
| colorMasterbatchQuantity    | integer   | Quantity of color masterbatch ordered (in kg).       |
| additiveMasterbatchQuantity | integer   | Quantity of additive masterbatch ordered (in kg).    |
| poDate                      | timestamp | Date when the purchase order was created.            |
| itemCode                    | varchar   | Code of the item ordered.                            |
| itemName                    | varchar   | Name of the item ordered.                            |
| itemQuantity                | integer   | Total quantity of items ordered.                     |
| poETA                       | timestamp | Expected arrival date of the purchase order.         |
| poNo                        | varchar   | Unique identifier for the purchase order.            |
| poReceivedDate              | timestamp | Date when the purchase order was received.           |

---

## Table: `productRecords`
| Field                   | Type      | Description                                            |
|-------------------------|-----------|--------------------------------------------------------|
| recordDate              | timestamp | Date when the production record was created.           |
| workingShift            | varchar   | Shift during which the production record was logged.   |
| machineNo               | varchar   | Unique identifier for the machine used.                |
| machineCode             | varchar   | Internal code for the machine.                         |
| itemCode                | varchar   | Code of the item being produced.                       |
| itemName                | varchar   | Name of the item being produced.                       |
| colorChanged            | varchar   | Whether the color of the resin was changed.            |
| moldChanged             | varchar   | Whether the mold was changed during the shift.         |
| machineChanged          | varchar   | Whether the machine was changed during the shift.      |
| poNote                  | varchar   | Notes related to the production order for this record. |
| moldNo                  | varchar   | Unique identifier for the mold used.                   |
| moldShot                | integer   | Number of shots taken with the mold during the shift.  |
| moldCavity              | integer   | Number of cavities in the mold.                        |
| itemTotalQuantity       | integer   | Total number of items produced.                        |
| itemGoodQuantity        | integer   | Number of good-quality items produced.                 |
| itemBlackSpot           | integer   | Count of items with black spots.                       |
| itemOilDeposit          | integer   | Count of items with oil deposits.                      |
| itemScratch             | integer   | Count of scratched items.                              |
| itemCrack               | integer   | Count of cracked items.                                |
| itemSinkMark            | integer   | Count of items with sink marks.                        |
| itemShort               | integer   | Count of short-shot items.                             |
| itemBurst               | integer   | Count of burst items.                                  |
| itemBend                | integer   | Count of bent items.                                   |
| itemStain               | integer   | Count of stained items.                                |
| otherNG                 | integer   | Count of other non-good (NG) items.                    |
| plasticResin            | varchar   | Name of the plastic resin used.                        |
| plasticResinCode        | varchar   | Code for the plastic resin used.                       |
| plasticResinLot         | varchar   | Lot number of the plastic resin used.                  |
| colorMasterbatch        | varchar   | Name of the color masterbatch used.                    |
| colorMasterbatchCode    | varchar   | Code for the color masterbatch used.                   |
| additiveMasterbatch     | varchar   | Name of the additive masterbatch used.                 |
| additiveMasterbatchCode | varchar   | Code for the additive masterbatch used.                |

---***---

# Main Data Schema Documentation

## Table: `productionStatus`
| Field              | Type       | Description                                           |
|--------------------|------------|-------------------------------------------------------|
| poReceivedDate     | timestamp  | Date when the purchase order was received.            |
| poNo               | varchar    | Unique identifier for the purchase order.             |
| poDate             | timestamp  | Date when the purchase order was created.             |
| poETA              | timestamp  | Expected arrival date of the purchase order.          |
| itemCode           | varchar    | Code of the item being produced.                      |
| itemName           | varchar    | Name of the item being produced.                      |
| itemType           | varchar    | Type/category of the item.                            |
| moldNo             | varchar    | Unique identifier for the mold used in production.    |
| moldList           | varchar    | List of molds associated with the item.               |
| moldName           | varchar    | Name of the mold used in production.                  |
| machineNo          | varchar    | Unique identifier for the machine used in production. |
| itemQuantity       | integer    | Total quantity of items to produce.                   |
| itemRemain         | integer    | Quantity of items remaining to produce.               |
| startedDate        | timestamp  | Date when production started.                         |
| actualFinishedDate | timestamp  | Date when production was completed.                   |
| proStatus          | varchar    | Current production status (e.g., molding, molded).    |