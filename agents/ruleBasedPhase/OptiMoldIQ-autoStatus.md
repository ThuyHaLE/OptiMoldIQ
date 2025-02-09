# AutoStatus Agent  

## **Role**  
- Tracks and updates real-time **production status**.  
- **Validates mold usage** by cross-checking with `moldInfo.xlsx`.  
- **Logs invalidations** for incorrect mold usage, missing data, and inconsistencies.  
- **Healing Mechanism**: Auto-corrects minor errors, flags major issues for review.  

---

## **Inputs**  
- **PO_list** (Purchase order data)  
- **productRecord** (Production execution data)  
- **moldInfo** (Reference for mold validation)  

---

## **Process Flow**  
1. **Summarize production progress** by PO and working day.  
2. **Cross-check mold usage** with `moldInfo.xlsx` to detect incorrect mold assignments.  
3. **Log invalidations** for data inconsistencies and incorrect mold usage.  
4. **Apply healing actions** (auto-correction where possible).  
5. **Generate reports** for real-time tracking and error logs.  

---

## **Outputs (Reports)**  

### **1. Production Status Report (Main Output)**  
This report provides **real-time tracking** of production progress for each PO.  

| **Field**            | **Type**    | **Description**                                           |
|----------------------|------------|-----------------------------------------------------------|
| poReceivedDate       | timestamp  | Date when the purchase order was received.               |
| poNo                | varchar    | Unique identifier for the purchase order.                |
| poDate             | timestamp  | Date when the purchase order was created.                |
| poETA               | timestamp  | Expected arrival date of the purchase order.             |
| itemCode           | varchar    | Code of the item being produced.                         |
| itemName           | varchar    | Name of the item being produced.                         |
| itemType           | varchar    | Type/category of the item.                               |
| moldNo             | varchar    | Unique identifier for the mold used in production.       |
| moldList           | varchar    | List of molds associated with the item.                  |
| moldName           | varchar    | Name of the mold used in production.                     |
| machineNo          | varchar    | Unique identifier for the machine used in production.    |
| itemQuantity       | integer    | Total quantity of items to produce.                      |
| itemRemain         | integer    | Quantity of items remaining to produce.                  |
| producedQuantity   | integer    | Number of items successfully produced.                   |
| NGQuantity         | integer    | Number of defective items produced.                      |
| startedDate        | timestamp  | Date when production started.                            |
| actualFinishedDate | timestamp  | Date when production was completed.                      |
| operator           | varchar    | Name or ID of the operator running the production.       |
| shift             | varchar    | Shift during which production took place.                |
| proStatus         | varchar    | Current production status (`Pending`, `Molding`, `Molded`). |

---

### **2. Invalidation Logs (Error Report)**  
This report logs **data inconsistencies**, including incorrect mold usage and missing information.  

| **Field**          | **Type**    | **Description**                                             |
|--------------------|------------|-------------------------------------------------------------|
| logID             | varchar    | Unique identifier for the log entry.                       |
| timestamp        | timestamp  | Date and time of the logged issue.                         |
| poNo             | varchar    | Purchase order related to the issue.                       |
| itemCode         | varchar    | Item code associated with the error.                       |
| moldNo           | varchar    | Mold number used (if incorrect).                           |
| expectedMoldNo   | varchar    | Correct mold number based on `moldInfo.xlsx`.             |
| issueType        | varchar    | Type of issue (`Invalid Mold`, `Missing Data`, etc.).     |
| issueDetails     | text       | Description of the inconsistency.                         |
| autoCorrected    | boolean    | Indicates if the system corrected the issue automatically. |
| correctiveAction | text       | Action taken (`Auto-Corrected`, `Flagged for Review`, etc.). |
| reviewedBy       | varchar    | Admin or user who reviewed the issue (if applicable).     |

---

## **Key Features**  
- **Real-time tracking of production progress** by PO.  
- **Validates mold usage** by cross-checking `moldInfo.xlsx`.  
- **Logs inconsistencies** and applies **healing actions** (auto-correct minor errors).  
- **Provides reports** for monitoring and review.  

---

## **Future Enhancements**  
- **Threshold-based alerts** for NG rates or mold inconsistencies (optional).  
- **Integration with other agents** for **machine downtime tracking** and **resin management**.  
- **Automated notifications** for flagged issues.  