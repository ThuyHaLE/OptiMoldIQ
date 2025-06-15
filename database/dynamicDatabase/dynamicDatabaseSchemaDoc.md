# Database Schema Documentation
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