# 1. Overview
The `orderProgressTracker` generates an Excel file (.xlsx) with **eight main sheets**, providing a comprehensive view of injection molding operations:
| Sheet Name              | Description                            |
| ----------------------- | -------------------------------------- |
| `productionStatus`      | Main production status tracking        |
| `materialComponentMap`  | Material and component mappings        |
| `moldShotMap`           | Mold shot tracking and equipment usage |
| `machineQuantityMap`    | Machine capacity and quantity mappings |
| `dayQuantityMap`        | Daily production quantity tracking     |
| `notWorkingStatus`      | Non-working time and downtime tracking |
| `item_invalid_warnings` | Data validation warnings for items     |
| `po_mismatch_warnings`  | Purchase order mismatch alerts         |

  
**Demo**: [🔗View orderProgressTracker Dashboard (Live Demo - CodeSandbox.io)](https://z86fl6.csb.app/)

# 2. Output Format:

## 2.1. Raw Reports Format:

- See overview: [orderProgressTracker Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_orderProgressTracker_overview.md)

### 2.1.1. productionStatus
**Purpose**: Tracks PO production status, materials, machines, molds, and shift/day-level outputs.

🧪 **Sample**:

|index|poReceivedDate|poNo|itemCode|itemName|poETA|itemQuantity|itemRemain|startedDate|actualFinishedDate|proStatus|etaStatus|machineHist|itemType|moldList|moldHist|moldCavity|totalMoldShot|totalDay|totalShift|plasticResinCode|index|colorMasterbatchCode|additiveMasterbatchCode|moldShotMap|machineQuantityMap|dayQuantityMap|shiftQuantityMap|materialComponentMap|lastestRecordTime|lastestMachineNo|lastestMoldNo|warningNotes|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|MOLDED|LATE|\['NO\.01\_MD50S-000'\]|CT-CA-BASE|14000CBQ-M-001|\['14000CBQ-M-001'\]|\[8\]|36180\.0|11\.0|30\.0|\['10045'\]|\['10190'\]|\[\]|\{'14000CBQ-M-001': 36180\}|\{'NO\.01\_MD50S-000': 280000\}|\{'2018-11-01': 29021, '2018-11-02': 27932, '2018-11-03': 29368, '2018-11-05': 28728, '2018-11-06': 29480, '2018-11-07': 27931, '2018-11-08': 27977, '2018-11-09': 29566, '2018-12-17': 13997, '2018-12-18': 29000, '2018-12-19': 7000\}|\{'2018-11-01\_shift\_1': 9620, '2018-11-01\_shift\_2': 9698, '2018-11-01\_shift\_3': 9703, '2018-11-02\_shift\_1': 9489, '2018-11-02\_shift\_2': 9775, '2018-11-02\_shift\_3': 8668, '2018-11-03\_shift\_1': 11384, '2018-11-03\_shift\_2': 9421, '2018-11-03\_shift\_3': 8563, '2018-11-05\_shift\_1': 9536, '2018-11-05\_shift\_2': 9656, '2018-11-05\_shift\_3': 9536, '2018-11-06\_shift\_1': 8553, '2018-11-06\_shift\_2': 10664, '2018-11-06\_shift\_3': 10263, '2018-11-07\_shift\_1': 9180, '2018-11-07\_shift\_2': 10000, '2018-11-07\_shift\_3': 8751, '2018-11-08\_shift\_1': 8632, '2018-11-08\_shift\_2': 9736, '2018-11-08\_shift\_3': 9609, '2018-11-09\_shift\_1': 9891, '2018-11-09\_shift\_2': 9891, '2018-11-09\_shift\_3': 9784, '2018-12-17\_shift\_2': 7000, '2018-12-17\_shift\_3': 6997, '2018-12-18\_shift\_1': 10000, '2018-12-18\_shift\_2': 10000, '2018-12-18\_shift\_3': 9000, '2018-12-19\_shift\_1': 7000\}|\[\{'plasticResinCode': '10045', 'colorMasterbatchCode': '10190', 'additiveMasterbatchCode': None\}\]|2018-12-19 06:00:00|NO\.01|14000CBQ-M-001|NaN|
|1|2018-10-20|IM1811008|24720318M|CT-CAX-UPPER-CASE-BLUE|2018-11-05|30000|0|2018-11-01|2018-11-02|MOLDED|ONTIME|\['NO\.08\_MD130S-000'\]|CT-CAX-UPPER-CASE|10100CBR-M-001|\['10100CBR-M-001'\]|\[4\]|7666\.0|2\.0|6\.0|\['10048'\]|\['10115'\]|\[\]|\{'10100CBR-M-001': 7666\}|\{'NO\.08\_MD130S-000': 30000\}|\{'2018-11-01': 16180, '2018-11-02': 13820\}|\{'2018-11-01\_shift\_1': 5608, '2018-11-01\_shift\_2': 5068, '2018-11-01\_shift\_3': 5504, '2018-11-02\_shift\_1': 5652, '2018-11-02\_shift\_2': 5068, '2018-11-02\_shift\_3': 3100\}|\[\{'plasticResinCode': '10048', 'colorMasterbatchCode': '10115', 'additiveMasterbatchCode': None\}\]|2018-11-02 22:00:00|NO\.08|10100CBR-M-001|NaN|
|2|2018-10-20|IM1811015|24720325M|CT-CAX-LOCK-BUTTON-GRAY|2018-11-05|15000|0|2018-11-01|2018-11-02|MOLDED|ONTIME|\['NO\.02\_MD50S-001'\]|CT-CAX-LOCK-BUTTON|16500CBR-M-001|\['16500CBR-M-001'\]|\[7\]|2185\.0|2\.0|2\.0|\['9915740199'\]|\['10106'\]|\[\]|\{'16500CBR-M-001': 2185\}|\{'NO\.02\_MD50S-001': 15000\}|\{'2018-11-01': 11080, '2018-11-02': 3920\}|\{'2018-11-01\_shift\_3': 11080, '2018-11-02\_shift\_1': 3920\}|\[\{'plasticResinCode': '9915740199', 'colorMasterbatchCode': '10106', 'additiveMasterbatchCode': None\}\]|2018-11-02 06:00:00|NO\.02|16500CBR-M-001|NaN|

### 2.1.2. materialComponentMap
**Purpose**: Maps materials (resin, color, additive) used in production.

🧪 **Sample**:

|index|poReceivedDate|poNo|itemCode|itemName|poETA|itemQuantity|itemRemain|startedDate|actualFinishedDate|plasticResinCode|colorMasterbatchCode|additiveMasterbatchCode|numOfMaterialComponent|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|10045|10190|NaN|1|
|1|2018-10-20|IM1811008|24720318M|CT-CAX-UPPER-CASE-BLUE|2018-11-05|30000|0|2018-11-01|2018-11-02|10048|10115|NaN|1|
|2|2018-10-20|IM1811015|24720325M|CT-CAX-LOCK-BUTTON-GRAY|2018-11-05|15000|0|2018-11-01|2018-11-02|9915740199|10106|NaN|1|

### 2.1.3. moldShotMap
**Purpose**: Logs number of shots taken by each mold.

🧪 **Sample**:

|index|poReceivedDate|poNo|itemCode|itemName|poETA|itemQuantity|itemRemain|startedDate|actualFinishedDate|moldNo|shotCount|numOfMold|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|14000CBQ-M-001|36180|1|
|1|2018-10-20|IM1811008|24720318M|CT-CAX-UPPER-CASE-BLUE|2018-11-05|30000|0|2018-11-01|2018-11-02|10100CBR-M-001|7666|1|
|2|2018-10-20|IM1811015|24720325M|CT-CAX-LOCK-BUTTON-GRAY|2018-11-05|15000|0|2018-11-01|2018-11-02|16500CBR-M-001|2185|1|

### 2.1.4. machineQuantityMap
**Purpose**: Maps molded quantity produced by each machine.

🧪 **Sample**:

|index|poReceivedDate|poNo|itemCode|itemName|poETA|itemQuantity|itemRemain|startedDate|actualFinishedDate|machineCode|moldedQuantity|numOfMachine|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|NO\.01\_MD50S-000|280000|1|
|1|2018-10-20|IM1811008|24720318M|CT-CAX-UPPER-CASE-BLUE|2018-11-05|30000|0|2018-11-01|2018-11-02|NO\.08\_MD130S-000|30000|1|
|2|2018-10-20|IM1811015|24720325M|CT-CAX-LOCK-BUTTON-GRAY|2018-11-05|15000|0|2018-11-01|2018-11-02|NO\.02\_MD50S-001|15000|1|

### 2.1.5. dayQuantityMap
**Purpose**: Tracks total molded quantity per working day.

🧪 **Sample**:

|index|poReceivedDate|poNo|itemCode|itemName|poETA|itemQuantity|itemRemain|startedDate|actualFinishedDate|workingDay|moldedQuantity|numOfDay|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|2018-11-01|29021|11|
|1|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|2018-11-02|27932|11|
|2|2018-10-20|IM1811001|26001122M|CT-CA-BASE-T\.SMOKE\(NO-PRINT\)|2018-11-05|280000|0|2018-11-01|2018-12-19|2018-11-03|29368|11|

### 2.1.6. notWorkingStatus
**Purpose**: Captures downtime and NG conditions per shift.

🧪 **Sample**:

|index|recordDate|workingShift|machineNo|machineCode|itemCode|itemName|colorChanged|moldChanged|machineChanged|poNote|moldNo|moldShot|moldCavity|itemTotalQuantity|itemGoodQuantity|itemBlackSpot|itemOilDeposit|itemScratch|itemCrack|itemSinkMark|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|2018-11-01|1|NO\.02|MD50S-001|24720325M|CT-CAX-LOCK-BUTTON-GRAY|NaN|NaN|NaN|IM1811015|16500CBR-M-001|0\.0|NaN|0\.0|0\.0|NaN|NaN|NaN|NaN|NaN|
|1|2018-11-01|1|NO\.09|MD130S-001|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|NaN|
|2|2018-11-01|2|NO\.02|MD50S-001|24720325M|CT-CAX-LOCK-BUTTON-GRAY|NaN|NaN|NaN|IM1811015|16500CBR-M-001|0\.0|NaN|0\.0|0\.0|NaN|NaN|NaN|NaN|NaN|

### 2.1.7. item_invalid_warnings
**Purpose**: Highlights items missing in reference tables.

🧪 **Sample**:

|index|itemInfo|warningType|mismatchType|requiredAction|message|
|---|---|---|---|---|---|
|0|10242M, AB-TP-LARGE-CAP-055-YW|item\_invalid\_in\_itemCompositionSummary|item\_does\_not\_exist\_in\_itemCompositionSummary|update\_itemCompositionSummary\_or\_double\_check\_related\_databases|\(10242M, AB-TP-LARGE-CAP-055-YW\) - Mismatch: 10242M\_and\_AB-TP-LARGE-CAP-055-YW\_does\_not\_exist\_in\_itemCompositionSummary\. Please update\_itemCompositionSummary\_or\_double\_check\_related\_databases|

### 2.1.8. po_mismatch_warnings
**Purpose**: Flags PO-related inconsistencies across multiple data sources.

🧪 **Sample**:

|index|poNo|warningType|mismatchType|requiredAction|message|
|---|---|---|---|---|---|
|0|IM1901044|item\_warnings|item\_info\_not\_matched|update\_itemInfo\_or\_double\_check\_productRecords|\(IM1901044, 2019-01-31, 3, NO\.11, 260501M1, CT-PXN-HEAD-COVER-4\.2MM\) - Mismatch: \(260501M1, CT-PXN-HEAD-COVER-4\.2MM\)\_not\_matched\. Please update\_itemInfo\_or\_double\_check\_productRecords|
|1|IM1901044|item\_mold\_warnings|item\_and\_mold\_not\_matched|update\_moldInfo\_or\_double\_check\_productRecords|\(IM1901044, 2019-01-31, 3, NO\.11, 260501M1, CT-PXN-HEAD-COVER-4\.2MM, PXNHC4-M-002\) - Mismatch: PXNHC4-M-002\_and\_\(260501M1,CT-PXN-HEAD-COVER-4\.2MM\)\_not\_matched\. Please update\_moldInfo\_or\_double\_check\_productRecords|
|2|IM1901044|mold\_machine\_tonnage\_warnings|mold\_and\_machine\_tonnage\_not\_matched|update\_moldSpecificationSummary\_or\_double\_check\_productRecords|\(IM1901044, 2019-01-31, 3, NO\.11, 260501M1, CT-PXN-HEAD-COVER-4\.2MM, PXNHC4-M-002, 50\) - Mismatch: 50\_and\_PXNHC4-M-002\_not\_matched\. Please update\_moldSpecificationSummary\_or\_double\_check\_productRecords|

## 2.2. Dashboard Report Format: 

- See overview: [processDashboardReports Overview](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/orderProgressTracker/OptiMoldIQ_processDashboardReports.overview.md)

### 2.2.1. `productionStatus`
**Purpose**: Track the overall status of each Purchase Order (PO)

**Main Columns**:
- `poNo`: Purchase Order number (e.g., IM1811001)
- `itemCode`: Product code (e.g., 26001122M)
- `itemName`: Product name (e.g., CT-CA-BASE-T.SMOKE(NO-PRINT))
- `poETA`: Required delivery date
- `itemQuantity`: Required quantity
- `itemRemain`: Remaining quantity
- `proStatus`: Production status (MOLDED, MOLDING, PAUSED, PENDING, etc.)
- `etaStatus`: ETA comparison (ONTIME, LATE)
- `machineHist`: List of used machines,
- `moldHist`: List of used molds,
- `moldCavity`: List of actual mold cavities,
- `totalMoldShot`: Total number of shots performed
- `totalDay`: Number of production days
- `lastestMachineNo`: Last machine used

**Use case**: Main dashboard to monitor order progress

**Demo**: [🔗View productionStatus Dashboard (Live Demo - CodeSandbox.io)](https://qvcrm8.csb.app/)

### 2.2.2. `machineQuantityMap`
**Purpose**: Track output by machine

**Structure**:
```json
{
  "machineNo": "NO.01",
  "details": "MD50S-000", 
  "items": [
    {
      "poItemInfo": "IM1811001 | 26001122M | CT-CA-BASE-T.SMOKE(NO-PRINT)",
      "moldedQuantity": 280000
    }
  ]
}
```

**Use case**: Analyze machine performance

**Demo**: [🔗View machineQuantityMap Dashboard (Live Demo - CodeSandbox.io)](https://ncwkvl.csb.app/)

### 2.2.3. `moldShotMap`
**Purpose**: Track shot counts per mold

**Structure**:
```json
{
  "moldNo": "10000CBR",
  "details": "M-001",
  "items": [
    {
      "poItemInfo": "IM1811010 | 24720320M | CT-CAX-LOWER-CASE-NL",
      "shotCount": 18424
    }
  ]
}
```

**Use case**: Analyze mold performance

**Demo**: [🔗View moldShotMap Dashboard (Live Demo - CodeSandbox.io)](https://yjdwkl.csb.app)

### 2.2.4. `dayQuantityMap`
**Purpose**: Track daily production output

**Structure**:
```json
{
  "workingDay": "2018-11-01",
  "details": [
    {
      "poItemInfo": "IM1811001 | 26001122M | CT-CA-BASE-T.SMOKE(NO-PRINT)",
      "moldedQuantity": 29021
    }
  ]
}
```

**Use case**: Monitor daily productivity

**Demo**: [🔗View dayQuantityMap Dashboard (Live Demo - CodeSandbox.io)](https://kvjlkk.csb.app/)

### 2.2.5. `materialComponentMap`
**Purpose**: Map materials to products
**Structure**:
```json
{
  "poNo": "IM1811001",
  "itemCode": "26001122M",
  "itemName": "CT-CA-BASE-T.SMOKE(NO-PRINT)",
  "details": [
    {
      "materialComponentInfo": "10045 | 10190 | nan"
    }
  ]
}
```

**Use case**: Monitor the material component used for each PO (item)

**Demo**: [🔗View moldShotMap Dashboard (Live Demo - CodeSandbox.io)](https://3mmsy9.csb.app)

### 2.2.6. `notWorkingStatus`
**Purpose**: Log shifts without production

**Main Columns**:
- `recordDate`: Record date
- `workingShift`: Shift number (1, 2, 3)
- `machineNo`: Machine number
- `itemCode`: Product code (if any)
- Other related info: material, mold, NG, etc.

**Use case**: Analyze downtime

**Demo**: Updating...

### 2.2.7. `item_invalid_warnings`
**Purpose**: Warnings for invalid product data

**Structure**:
```json
{
  "itemInfo": "10242M, AB-TP-LARGE-CAP-055-YW",
  "warningType": "item_invalid_in_itemCompositionSummary",
  "mismatchType": "item_does_not_exist_in_itemCompositionSummary",
  "requiredAction": "update_itemCompositionSummary_or_double_check_related_databases",
  "message": "Detailed error message"
}
```

**Use case**: Data quality control, database maintenance

**Demo**: Updating...

### 2.2.8. `po_mismatch_warnings`
**Purpose**: Warnings for mismatched PO data

**Types**:
- `item_warnings`: Item data mismatch
- `item_mold_warnings`: Item and mold mapping mismatch

**Use case**: Data validation, process improvement

**Demo**: Updating...