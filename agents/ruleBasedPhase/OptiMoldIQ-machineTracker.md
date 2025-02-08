# **Machine Tracking Agent**

## **Role**  
Tracks the continuous production of each machine per shift, monitors mold changes, and generates a **Mold-Machine Pair Matrix** based on first usage records.  

## **Input Data**  
- **Production Records**: Contains machine usage per shift, mold usage, and yield data.  
- **Mold Usage Data**: Extracted from production records to track mold changes.  
- **Shift Schedule**: Defines the working shifts for tracking machine idle periods.  

## **Process**  
1. **Continuous Production Monitoring**  
   - Track each machine's production status per shift.  
   - Identify shifts where the machine was idle (i.e., no production records or yield = 0).  

2. **Mold Change Tracking**  
   - Compare mold usage per machine per shift.  
   - If a different mold is recorded in the next shift, flag it as a mold change.  

3. **Mold-Machine Pair Matrix Generation**  
   - Identify the first production record for each **mold-machine pair** by date.  
   - Create a matrix summarizing mold usage history across machines.  

---

## **Output Format**  

### **1. Machine Production Tracking Report**
| Date       | Shift | Machine ID | Production Status | Mold ID | Mold Change | Yield (pcs) |
|------------|-------|------------|------------------|---------|------------|-------------|
| 2025-02-01 | 1     | M01        | Active           | MoldA   | No         | 2,500       |
| 2025-02-01 | 2     | M01        | Active           | MoldA   | No         | 2,700       |
| 2025-02-01 | 3     | M01        | Idle             | -       | -          | 0           |
| 2025-02-02 | 1     | M01        | Active           | MoldB   | Yes        | 2,300       |
| 2025-02-02 | 2     | M01        | Active           | MoldB   | No         | 2,400       |

**Notes:**  
- **Production Status:** "Active" if there is production, "Idle" if no records or yield = 0.  
- **Mold Change:** "Yes" if the mold changes between shifts.  
- **Yield (pcs):** Total number of good parts produced in the shift.  

---

### **2. Mold-Machine Pair Matrix (First Usage Record)**
| Mold ID | First Used Date | Machine ID |
|---------|----------------|------------|
| MoldA   | 2025-01-15     | M01        |
| MoldA   | 2025-01-20     | M02        |
| MoldB   | 2025-02-02     | M01        |

**Notes:**  
- This table records the first time a **mold** was used on a **machine** for planning reference.  

---

## **Benefits**
✅ Helps identify **idle machines** for better utilization.  
✅ Tracks **mold changes** to optimize mold usage.  
✅ Provides a **historical record** of mold-machine compatibility for planning.  