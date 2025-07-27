# orderProgressTracker Reports Output Format

## Overview
The `orderProgressTracker` generates an Excel file (.xlsx) with **eight main sheets**, providing a comprehensive view of injection molding operations:
- `productionStatus`
- `materialComponentMap`
- `moldShotMap`
- `machineQuantityMap`
- `dayQuantityMap`
- `notWorkingStatus`
- `item_invalid_warnings`
- `po_mismatch_warnings`
  
**Demo**: [🔗View orderProgressTracker Dashboard (Live Demo - CodeSandbox.io)](https://z86fl6.csb.app/)

## Sheet Descriptions

### 1. `productionStatus`
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

### 2. `machineQuantityMap`
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

### 3. `moldShotMap`
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

### 4. `dayQuantityMap`
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

### 5. `materialComponentMap`
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

### 6. `notWorkingStatus`
**Purpose**: Log shifts without production

**Main Columns**:
- `recordDate`: Record date
- `workingShift`: Shift number (1, 2, 3)
- `machineNo`: Machine number
- `itemCode`: Product code (if any)
- Other related info: material, mold, NG, etc.

**Use case**: Analyze downtime

**Demo**: Updating...

### 7. `item_invalid_warnings`
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

### 8. `po_mismatch_warnings`
**Purpose**: Warnings for mismatched PO data

**Types**:
- `item_warnings`: Item data mismatch
- `item_mold_warnings`: Item and mold mapping mismatch

**Use case**: Data validation, process improvement

**Demo**: Updating...
