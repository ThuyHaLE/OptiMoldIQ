# **QualityControl Agent**  

## **Role**  
Monitors production quality by tracking yield deviations, mold changes, and color changes.  

## **Input Data**  
- **productRecord** – Tracks production quantities, NG rates, and machine usage.  
- **historical quality data** – Helps analyze recurring defects and trends.  
- **moldInfo (static database)** – Provides cycle time and cavity data for expected yield calculation.  

---

## **Process**  

### **1. Expected Yield Calculation**  
1. Identify **molds used per shift** and their **cycle times**.  
2. Calculate **expected yield per mold**:  
   \[
   \text{Expected Yield per Mold} = \left(\frac{\text{Shift Time (mins)}}{\text{Cycle Time (mins)}}\right) \times \text{Mold Cavity}
   \]  
3. Compute final **expected yield** using the **average yield method**:  
   \[
   \text{Final Expected Yield} = \frac{\sum \text{Expected Yield per Mold}}{\text{Number of Molds Used}}
   \]  

### **2. Estimated Setup Time Calculation**  
✅ **Setup time is estimated only if:**  
   - **Mold Change** occurs.  
   - **Color Change** occurs.  
   - **Yield deviation exists (Actual Yield < Expected Yield)**.  

⛔ **Setup time is NOT estimated if:**  
   - Yield deviation exists but there’s **no mold or color change**.  

#### **Formula for Estimated Setup Time:**  
\[
\text{Estimated Setup Time (mins)} = \left(\frac{\text{Expected Yield} - \text{Actual Yield}}{\text{Expected Yield}}\right) \times \text{Shift Time}
\]

**Notes:**  
- Setup time is proportional to the yield drop.  
- If the yield drop is minor (within acceptable variation), **setup time is ignored**.  
- The more significant the yield drop, the **higher the estimated setup time**.  

### **3. Flagging Issues**  
- ⚠ **Yield Drop:** If **actual yield < expected yield by more than 3%**.  
- ⚠ **NG Rate Warning:** If **any NG type exceeds 3%**.  
- ⚠ **Setup Time Adjustment Needed:** If an unexpected mold/color change affects production.  

---

## **Output Format**  

### **1. Quality Control Report**  

| Date       | Shift | Machine ID | **Molds Used**        | **Mold Change** | **Color Used**    | **Color Change** | **Yield (pcs)** | **Expected Yield (pcs)** | **Yield Deviation (%)** | **Estimated Setup Time (mins)** | **NG Rate (%)** | **Issue Flags** |  
|------------|-------|------------|----------------------|----------------|------------------|--------------|-------------|----------------------|--------------------|----------------------|------------|--------------|  
| 2025-02-01 | 1     | M01        | **MoldA → MoldB**    | ✅ Yes         | **Blue → Blue**  | ❌ No        | 3,200       | **3,600**              | **-11.1% ⚠**      | **53 mins ⚠**        | **2.5%**   | Yield Drop ⚠ |  
| 2025-02-01 | 2     | M02        | **MoldC**            | ❌ No         | **Red**          | ❌ No        | 1,500       | **1,800**              | **-16.7% ⚠**      | **-** ✅              | **3.2% ⚠** | Yield Drop ⚠, NG Rate ⚠ |  
| 2025-02-01 | 3     | M03        | **MoldD → MoldE**    | ✅ Yes         | **Black → Green** | ✅ Yes        | 2,000       | **2,400**              | **-16.7% ⚠**      | **80 mins ⚠**        | **4.5% ⚠** | Yield Drop ⚠, NG Rate ⚠ |  