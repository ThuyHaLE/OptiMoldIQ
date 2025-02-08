# **Resin Tracking Agent**  

## **Role**  
Tracks **resin stock levels**, updates accumulated resin quantities, and flags potential shortages or refill needs based on active production. Ensures that finished POs have sufficient resin provision and monitors **actual vs. default resin usage** for shortages or excess resin returns.  

## **Input Data**  
- **`resinReceivingRecord`** – Logs received resin stock.  
- **`productRecord`** – Tracks actual resin consumption per shift.  
- **`PO_list`** – Contains active and completed POs with item quantities.  
- **`historicalResinUsage`** – Provides past resin consumption trends.  
- **`resinPO_list`** – Records **default resin quantity per PO** and received status.  

## **Process**  

### **1. Resin Stock Update (`resinStock`)**  
- **Increase stock** when resin is received.  
- **Decrease stock** based on resin consumption in production.  
- Maintain **real-time resin stock levels** for tracking and reporting.  

### **2. Historical Resin Usage Tracking**  
- Record **past resin consumption** to support demand forecasting.  

### **3. Active PO Monitoring for Early Shortage Alerts**  
- Estimate **short-term resin needs** (2-3 working days).  
- Adjust alerts dynamically if a PO is **paused or resumed**.  

### **4. Stock Refill Alerts**  
- Compare **current resinStock vs. estimated requirements**.  
- Trigger **early warnings** if stock is insufficient for upcoming production.  

### **5. Resin PO Fulfillment & Usage Validation**  
- **Process shortage cases only for finished POs**:  
  - If **received resin status = Yes**, compare **default vs. actual usage**.  
  - If **actual usage > default**, calculate **shortage**.  
  - If **actual usage < default**, flag **excess resin** for return.  
- **Flag missing resin for completed POs**:  
  - If **PO is finished but resin received status = No**, raise a flag to **import resin before item export** (ensuring resin provision aligns with production logic).  

---

## **Output Format**  

### **1. Updated Resin Stock Report**  
| Date       | Resin Code | Received Qty (kg) | Used Qty (kg) | Remaining Stock (kg) |
|------------|-----------|-------------------|---------------|----------------------|
| 2025-02-01 | R001      | 500               | 400           | 3,200                |
| 2025-02-02 | R001      | 0                 | 450           | 2,750                |
| 2025-02-03 | R002      | 600               | 300           | 5,200                |

---

### **2. Resin Shortage Alert Report**  
| Date       | Resin Code | Required Qty (Next 3 Days) | Available Stock (kg) | Status         |
|------------|-----------|--------------------------|----------------------|---------------|
| 2025-02-03 | R001      | 1,500                    | 1,200                | 🔴 Low Stock  |
| 2025-02-03 | R002      | 2,000                    | 5,200                | ✅ Sufficient |

---

### **3. Resin PO Tracking Report**  
| PO Number  | Item Code | Default Resin Qty (kg) | Actual Used (kg) | Received Status | Shortage/Excess (kg) | Resin Import Needed? |
|------------|----------|-----------------------|------------------|----------------|------------------|----------------------|
| PO1001     | I001     | 500                   | 470              | ✅ Yes         | -30 (Excess)     | ❌ No               |
| PO1002     | I002     | 700                   | 750              | ✅ Yes         | +50 (Shortage)   | ❌ No               |
| PO1003     | I003     | 600                   | 0                | ❌ No          | +600 (Shortage)  | 🔴 Yes              |

**Notes:**  
- **Shortage/Excess Calculation:**  
  - **Negative (-)** → Excess resin available for return.  
  - **Positive (+)** → Additional resin needed beyond default allocation.  
- **Resin Import Needed?**  
  - **🔴 Yes** → The PO is completed but no resin was recorded as received.  
  - **❌ No** → The PO either had resin provision or does not require additional import.  

---

## **Benefits**  
✅ Ensures **resin stock is updated in real time**.  
✅ Flags **early refill needs** based on active POs.  
✅ Helps prevent **overstocking** when POs are paused.  
✅ Supports **resin PO monitoring** to track provision and excess resin for return.  
✅ Ensures **resin import aligns with production logic** before exporting finished items.  