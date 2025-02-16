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
Optimizes the production plan.
#### Input:
- Draft plan from InitialSched Agent
- Reports from tracking agents
#### Process:
- Address flagged issues and optimize workload.
- Balance resin stock and machine capacity.
- Prioritize mold/machine continuity.
#### Output:
- Optimized Production Plan
#### Key Features:
- Multi-agent collaboration for better scheduling.
#### Healing Actions:
- Auto-adjust plans for stock/machine failures.

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
Evaluates production data to identify key performance indicators (KPIs) and potential inefficiencies.  

#### **Input:**  
- **Production Data:** productRecord, moldInfo, resinUsage, NG rate, machineStatus.  
- **Operational Data:** Shift schedules, downtime records, maintenance logs.  

#### **Process:**  
1. **Yield Performance:** Actual vs. expected production rates.  
2. **Resin Consumption:** Compare with standard usage.  
3. **Machine Utilization:** Runtime vs. downtime percentages.  
4. **Cycle Time Variations:** Identify inconsistencies.  
5. **NG Rate Trends:** Compare across different molds, machines, and resins.  
6. **Production Interruptions:** Downtime causes and frequency.  

#### **Output:**  
- **Analytics Report:** Quantitative assessment of key performance metrics.  
- **Visualization Dashboard:** Charts and tables summarizing efficiency and performance.  
- **KPI Breakdown:**  
  - Yield efficiency (%)  
  - Resin consumption per unit  
  - Machine utilization rate (%)  
  - Average cycle time (s)  
  - NG rate (%)  
  - Downtime per shift (min)  

#### **Key Features:**  
- Works with both historical and real-time data.  
- Provides statistical insights without recommending specific actions.  
- Allows further analysis by other agents (e.g., YieldOptimization, MaintenanceScheduler).  

#### **Healing Actions:**  
🔄 **Self-Diagnosis & Recovery:**  
- **Data Integrity Check:** Verifies missing, duplicate, or inconsistent data before processing.  
- **Auto-Recalibration:** Adjusts baseline expectations if new patterns emerge in data.  
- **Fallback Mode:** If real-time data is unavailable, switches to historical trend analysis.  
- **Alert System:** Notifies system admins if data anomalies exceed predefined thresholds.  
- **Redundant Processing:** Runs cross-validation with past reports to ensure consistency.  

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
