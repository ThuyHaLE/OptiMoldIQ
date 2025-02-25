# 📊 Analytics Agent — Enhanced Design

## **Role:**  
Evaluates production data and PO data to identify key performance indicators (KPIs), potential inefficiencies, and capacity planning insights.

---

## **Input:**  
1. **Production Data:**  
   - Product Records: `recordDate`, `machineNo`, `itemCode`, `itemName`, `workingShift`, `cycleTime`, `itemTotalQuantity`, `itemGoodQuantity`, `itemNGQuantity`, `moldChanged`, `machineChanged`, `colorChanged`, `plasticResine`, `NG types`.  
   - Resin Usage, NG rate, machine status.

2. **PO Data:**  
   - PO Number (`poNote`), `itemCode`, ordered quantity, due date, priority, and status.

3. **Operational Data:**  
   - Shift schedules, downtime records, maintenance logs.

---

## **Process:**  

### ⚡ Overall Equipment Effectiveness (OEE):  
- **Availability:** Based on machine runtime and planned production time.  
- **Performance:** Actual vs. theoretical max output (using cycle time & shot counts).  
- **Quality:** Good items vs. total items produced.

### 🏗️ Production Capacity & PO Fulfillment:  
- **PO Completion Rate:** Compare actual output with PO requirements.  
- **Overcapacity Alerts:** Identify products exceeding machine or mold limits.  
- **Capacity Gap Analysis:** Recommend capacity increases (e.g., new molds).

### 💥 NG (Defect) Analysis:  
- Track NG rate by mold, machine, and resin.  
- Identify common defect types and their distribution.  
- Highlight underperforming molds/machines.

### ⏳ Breakdown Time & Downtime Analysis:  
- Calculate downtime due to mold changes, machine shifts, and color changes.  
- Correlate downtime with production loss.

### 📅 Shift & Machine Performance Trends:  
- Compare performance and NG rates across shifts and machines.  
- Identify shifts or machines with recurrent issues.

### 🏆 KPI Breakdown:  
- **Yield Efficiency (%):** Good Quantity / Total Quantity  
- **Resin Consumption per Unit**  
- **Machine Utilization Rate (%)**  
- **Cycle Time Deviation**  
- **NG Rate (%)**  
- **Downtime per Shift (min)**  
- **PO Fulfillment Rate (%)**

---

## **Output:**  
- 📋 **Analytics Report:** Detailed KPI metrics and insights.  
- 📊 **Visualization Dashboard:** Real-time charts/tables for trend analysis.  
- 📡 **Capacity Planning Alerts:** Recommendations for production scaling or adjustments.

---

## **Key Features:**  
- Handles both historical and real-time data.  
- Dynamic PO tracking and capacity gap detection.  
- Supports decision-making for mold/machine investments and efficiency improvements.

## **Healing Actions:**  
- **Data Integrity Check:** Detect missing, duplicate, or inconsistent data.  
- **Auto-Recalibration:** Adjusts KPIs if operational patterns shift.  
- **Fallback Mode:** Utilizes historical trends if real-time data is unavailable.  
- **Alert System:** Notifies when anomalies breach thresholds.  
- **Redundant Processing:** Cross-validates current data with historical reports.
