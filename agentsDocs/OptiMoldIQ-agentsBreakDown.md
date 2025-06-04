## Workflows for All Agents in the OptiMoldIQ System

### 1. AutoStatus Agent  

#### Role
Tracks and updates real-time **production status**.  

#### Input
- **PO_list** (Purchase order data)  
- **productRecord** (Production execution data)  

#### Process
1. Summarize `productRecord` by **PO and working day**.  
2. Cross-check **mold usage** with `moldInfo`.  
3. Log invalidations (e.g., incorrect mold usage, data inconsistencies).  

#### Output
- **ProductionStatus Report** (Real-time production tracking).  
- **Invalidation Logs** (Error records for review).  

#### Key Features
- **Data validation** for consistency.  

#### Healing Actions
- **Recheck and auto-correct** invalid entries.  

---

### 2. InitialSched Agent
#### Role:
Drafts the initial production plan.
#### Input:
- productionStatus from AutoStatus Agent
#### Process:
- Analyze production status and pending POs.
- Allocate molds, machines, and resin.
- Flag resource shortages.
#### Output:
- Draft Production Plan
- Issue Logs
#### Key Features:
- Resource allocation with basic checks.
#### Healing Actions:
- Retry plan generation if issues arise.

---

### 3. FinalSched Agent

#### Role:
The **FinalSched Agent** is responsible for **optimizing the production schedule**, ensuring a balance between **efficiency, continuity, and resilience**.  
#### Input:
- **Draft Plan from InitialSched Agent** (Initial rule-based schedule).  
- **Reports from Tracking Agents:**  
   - **Resin Tracking Agent** → Monitors resin stock levels.  
   - **Mold Tracking Agent** → Tracks mold status and maintenance schedules.  
   - **Machine Tracking Agent** → Tracks machine status and capacity.  
- **Production History** (for Offline Learning).  
#### Process:
##### **Buffer Layer (Adjustment Mechanism):**  
- **Plan A:** Adjusts Initial Schedule based on **rule-based logic** (ensures stability).  
- **Plan B:** Incorporates **Offline Learning output** for deeper optimization.  
- **If Offline Learning produces incorrect outputs,** the system can **disable Plan B and fallback to Plan A,** ensuring Beta remains functional.  
##### **Production Schedule Optimization:**  
- **Load balancing** across machines.  
- **Resin stock optimization** to avoid shortages or excess inventory.  
- **Prioritizing mold and machine continuity** to reduce setup time.  
- **Addressing flagged issues** from tracking agents.  
#### Output:
**Optimized Production Plan** (Refined and validated schedule).  
#### Key Features:
- **Multi-agent collaboration** for improved scheduling.  
- **Automated plan adjustments** when issues arise.  
- **Built-in buffer mechanism** to ensure system stability.  
#### Healing Actions:
- **Auto-adjust plans** when disruptions occur (machine failures, resin shortages, mold issues).  
- **Recalculate schedules** if tracking agents detect bottlenecks.  
- **Fallback to Plan A** if Offline Learning encounters errors.  
**FinalSched Agent ensures the system remains optimal, stable, and adaptable to real-world conditions!**  

---

### 4. ResinTracking Agent
#### Role:
Tracks resin stock and usage trends.
#### Input:
- PO_list, productRecord
- historicalResinUsage, resinReceivingRecord
#### Process:
- Monitor resin consumption and stock levels.
- Flag shortages based on 2-3 days' demand.
#### Output:
- Resin Stock Report
- Resin Shortage Alert
#### Key Features:
- Predictive restocking based on usage trends.
#### Healing Actions:
- Highlight discrepancies in resin allocation.

---

### 5. MoldTracking Agent
#### Role:
Monitors mold usage and maintenance.
#### Input:
- PO_list, productRecord
- historical mold maintenance data
#### Process:
- Track mold shots and maintenance thresholds.
#### Output:
- Mold Usage Report with flagged risks.
#### Key Features:
- Reinforcement learning for better scheduling.
#### Healing Actions:
- Alert excessive mold usage or incorrect assignments.

---

### 6. MachineTracking Agent
#### Role:
Tracks machine uptime, mold changes, and yield issues.
#### Input:
- PO_list, productRecord
- historical machine operation data
#### Process:
- Monitor machine output, downtime, and mold changes.
- Build a Mold-Machine Pair Matrix.
#### Output:
- Machine Production Report
- Mold-Machine Pair Matrix
#### Key Features:
- Predictive downtime analysis.
#### Healing Actions:
- Auto-adjust schedules for prolonged downtimes.

---

### 7. ResinCoordinate Agent
#### Role:
Optimizes resin usage and recycling.
#### Input:
- FinalSched Agent’s plan, ResinTracking Agent’s report
- historical runner data, granulator processing rates
#### Process:
- Forecast resin needs, including recycled resin.
- Automate runner recycling and optimize reuse ratios.
#### Output:
- Resin Usage & Recycling Report
#### Key Features:
- AI-driven resin reuse predictions.
#### Healing Actions:
- Adjust resin forecasts based on recycling efficiency.

---

### 8. MaintenanceScheduler Agent
#### Role:
Schedules mold/machine maintenance.
#### Input:
- FinalSched Agent’s plan
- Mold and Machine Tracking Reports
#### Process:
- Align maintenance with production to minimize downtime.
#### Output:
- Maintenance Schedule
#### Key Features:
- Smart scheduling based on real-time data.
#### Healing Actions:
- Reschedule dynamically based on live feedback.

---

### 9. QualityControl Agent
#### Role:
Monitors yield deviations, mold changes, and color changes.
#### Input:
- productRecord, historical quality data
- moldInfo (static database)
#### Process:
- Calculate expected yield and compare with actual yield.
- Identify deviations and estimate setup time.
#### Output:
- Quality Control Report
#### Key Features:
- Adaptive yield analysis and threshold tuning.
#### Healing Actions:
- Auto-flag mold/color changes affecting yield.

---

### 10. YieldOptimization Agent
#### Role:
Optimizes yield and resin allocation.
#### Input:
- productRecord, historical yield data
#### Process:
- Analyze yield trends and NG rates.
- Suggest optimized cycle times and resin usage.
#### Output:
- Yield Optimization Report
#### Key Features:
- AI-based cycle time and resin adjustments.
#### Healing Actions:
- Revert to default settings if NG rates rise.

---

### 11. DashBoardBuilder Agent
#### Role:
Visualizes system data for decision-making.
#### Input:
- Reports from all agents
#### Process:
- Generate production dashboards and highlight key metrics.
- Visualize logs for quick issue identification.
#### Output:
- Comprehensive system dashboards
#### Key Features:
- Expandable AI-driven insights.
#### Healing Actions:
- Flag inconsistencies and missing data.

---

### 12. ChangeTracking Agent  

#### Role  
Tracks and logs **modifications** to production records, ensuring changes are **approved** before updating the main database.  

#### Input  
- **productionStatus** (Real-time production records)  
- **permissionControl** (User permissions)  
- **Static Database** (Reference for validation)  

#### Process  
1. **Monitor** changes after each working shift.  
2. **Validate** modifications based on permission levels and reference data.  
3. **Apply healing actions** (auto-correct minor errors, flag major issues).  
4. **Request admin approval** for flagged changes before updating records. 

#### Output  
- **Change Log Report** (Modification history).  
- **Unauthorized Modification Log** (Invalid change records).  

#### Key Features  
- **Modification approval system** to prevent unauthorized changes.  
- **Real-time tracking of changes** after each working shift.  

#### Healing Actions  
- **Auto-correct minor issues** (e.g., format errors).  
- **Flag and suggest corrections** for invalid entries (e.g., incorrect machine numbers).  

---

### 13. Analytics Agent  
#### **Role:**  
Evaluates production data and PO data to identify key performance indicators (KPIs), potential inefficiencies, and capacity planning insights.

---

#### **Input:**  
- **productionStatus** (Real-time production records)  
- **poList** (Historical POs records)  
  
---

#### **Process:**  
##### 1. Overall Equipment Effectiveness (OEE):  
- **Availability:** Based on machine runtime and planned production time.  
- **Performance:** Actual vs. theoretical max output (using cycle time & shot counts).  
- **Quality:** Good items vs. total items produced.

##### 2. Production Capacity & PO Fulfillment
- **PO Completion Rate:** Compare actual output with PO requirements.  
- **Overcapacity Alerts:** Identify products exceeding machine or mold limits.  
- **Capacity Gap Analysis:** Recommend capacity increases (e.g., new molds).

##### 3. NG (Defect) Analysis:  
- Track NG rate by mold, machine, and resin.  
- Identify common defect types and their distribution.  
- Highlight underperforming molds/machines.

##### 4. Breakdown Time & Downtime Analysis:  
- Calculate downtime due to mold changes, machine shifts, and color changes.  
- Correlate downtime with production loss.

##### 5. Shift & Machine Performance Trends:  
- Compare performance and NG rates across shifts and machines.  
- Identify shifts or machines with recurrent issues.

##### 6. KPI Breakdown:  
- **Yield Efficiency (%):** Good Quantity / Total Quantity  
- **Resin Consumption per Unit**  
- **Machine Utilization Rate (%)**  
- **Cycle Time Deviation**  
- **NG Rate (%)**  
- **Downtime per Shift (min)**  
- **PO Fulfillment Rate (%)**

---

#### **Output:**  
- **Analytics Report:** Detailed KPI metrics and insights.  
- **Visualization Dashboard:** Real-time charts/tables for trend analysis.  
- **Capacity Planning Alerts:** Recommendations for production scaling or adjustments.

---

#### **Key Features:**  
- Handles both historical and real-time data.  
- Dynamic PO tracking and capacity gap detection.  
- Supports decision-making for mold/machine investments and efficiency improvements.

#### **Healing Actions:**  
- **Data Integrity Check:** Detect missing, duplicate, or inconsistent data.  
- **Auto-Recalibration:** Adjusts KPIs if operational patterns shift.  
- **Fallback Mode:** Utilizes historical trends if real-time data is unavailable.  
- **Alert System:** Notifies when anomalies breach thresholds.  
- **Redundant Processing:** Cross-validates current data with historical reports.

---

## Additional Considerations:
1. **Shared Database Implementation**  
   - Hybrid SQL-NoSQL approach for structured and flexible data handling.  
2. **Agent Communication**  
   - Event-driven mechanism with a message queue (e.g., RabbitMQ, Kafka).  
3. **Healing System Enhancements**  
   - Automated rollbacks for faulty optimizations.  
4. **Reinforcement Learning (RL) Roadmap**  
   - Phase 1: Historical data training.  
   - Phase 2: RL for YieldOptimization Agent.  
   - Phase 3: RL for FinalSched Agent.  
5. **Performance & Scalability**  
   - Parallel processing for key agents.  
   - Optimized database queries for frequent updates.  
