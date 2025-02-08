# **Mold Tracking Agent**  

## **Role:**  
Tracks mold usage, accumulates shot counts, and monitors maintenance status.  

---

## **Inputs:**  
- **PO_list** → Provides mold usage data from production orders.  
- **productRecord** → Tracks actual shots per mold.  
- **Maintenance records** → Checks if maintenance has been completed.  
- **moldInfo** → Contains details such as mold ID, name, cavity standard, and maintenance threshold.  

---

## **Workflow:**  

1. **Track Mold Usage:**  
   - Extract **mold usage data** from `PO_list`.  
   - Count **actual shots per mold** from `productRecord`.  

2. **Update Shot Counts:**  
   - **Accumulated Shots** → Total shots since the mold was introduced.  
   - **Updated Shots** → Shots counted since the last maintenance.  

3. **Monitor Maintenance Status:**  
   - Check **maintenance records** for completed maintenance.  
   - If maintenance is **completed**, reset `Updated Shots = 0`.  
   - If **no maintenance is recorded**, keep `Updated Shots = Accumulated Shots`.  

4. **Check Maintenance Threshold:**  
   - Compare **Updated Shots** with the **Max Shots before maintenance**.  
   - Flag **ALERT** if a mold exceeds its maintenance limit.  

5. **Generate Reports:**  
   - Create a **Mold Usage Report** for tracking shot counts and maintenance needs.  
   - Generate **alerts for overdue maintenance** if thresholds are exceeded.  

---

## **Predictive Maintenance & Optimization Strategies:**  

### **Predictive Maintenance Based on Shot Counts and NG Rates**  

#### **Core Features:**  
1. **Shot Count Monitoring**: Track shot counts in real time.  
2. **NG Rate Analysis**: Analyze defects (e.g., cracks, short shots, black spots).  
3. **Threshold-Based Predictions**: Set limits for NG rates and shot counts.  
4. **Recommendation System**: Suggest maintenance schedules based on predictive modeling.  

---

## **Mold Tracking Agent Output Format**  

### **Mold Usage Report:**  

| Field Name                | Type         | Description                                                 |
|---------------------------|--------------|-------------------------------------------------------------|
| moldNo                    | String       | Unique identifier for the mold.                            |
| moldName                  | String       | Name of the mold.                                          |
| accumulatedShots          | Integer      | Total shots since mold introduction.                       |
| updatedShots              | Integer      | Shots counted since last maintenance.                      |
| maxShotsBeforeMaintenance | Integer      | Threshold for required maintenance.                        |
| status                    | String       | Status (OK / ALERT for overdue maintenance).               |
| lastMaintenanceDate       | Date         | Last date maintenance was performed.                       |
| nextMaintenanceDue        | Date         | Estimated next maintenance date based on shot counts.      |

#### **Example Report:**  

| Mold No | Mold Name | Accumulated Shots | Updated Shots | Max Shots (Before Maintenance) | Status  | Last Maintenance Date | Next Maintenance Due |
|---------|----------|-------------------|--------------|----------------------------|---------|---------------------|---------------------|
| M001    | Mold A   | 150,000          | 10,500       | 12,000                     | OK      | 2025-01-10         | 2025-02-15         |
| M002    | Mold B   | 250,000          | 250,000      | 12,000                     | ALERT   | 2024-12-20         | 2025-01-25         |

---

## **Mold Maintenance Alert Report**  

| Mold No | Mold Name | Updated Shots | Max Shots Before Maintenance | Status  | Action Required         |
|---------|----------|--------------|----------------------------|---------|----------------------|
| M002    | Mold B   | 250,000      | 12,000                     | ALERT   | Immediate Maintenance |

---

## **Tracking and Feedback Loop**  

- **Tracking Agents:** The Mold Tracking Agent continuously updates shot counts and maintenance status.  
- **Feedback Integration:** If maintenance is **approved**, the system resets `Updated Shots = 0`. If rejected, the agent re-evaluates and reschedules.  
- **Integration with Maintenance Scheduler:** If a mold is **overdue for maintenance**, it sends an alert to the **Maintenance Scheduler Agent**.  