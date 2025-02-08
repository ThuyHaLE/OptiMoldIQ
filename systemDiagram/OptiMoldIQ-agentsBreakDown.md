m## Workflows for All Agents in the OptiMoldIQ System

### 1. AutoStatus Agent
#### Role: 
Tracks and updates real-time production status.
#### Input: 
- PO_list
- productRecord
#### Process:
- Summarize productRecord by PO and working day
- Cross-check data with moldInfo to validate mold usage for each PO
- Log invalidations (e.g., incorrect mold usage, data inconsistencies)
#### Output:
- Generate productionStatus
- Log invalidations for review
#### Key Scalable Features: 
Logs inconsistencies for validation and future auditing, critical for building trust in the data pipeline.
#### Healing System Actions: 
Recheck invalid entries and auto-correct based on predefined rules.

### 2. InitialSched Agent
#### Role: 
Drafts the initial production plan.
#### Input:
productionStatus (report) from AutoStatus Agent
#### Process:
- Analyze current production status and pending POs
- Generate a draft production plan, including:
  - Allocation of molds and machines
  - Resin requirements per PO
  - Highlight potential issues (e.g., resource shortages) in logs
#### Output:
- Draft Production Plan
- Logs highlighting flagged issues
#### Key Scalable Features: 
Flags resource shortages and issues for cross-agent review.
#### Healing System Actions: 
Retry plan generation if errors occur in flagged data.

### 3. FinalSched Agent
#### Role: 
Refines and optimizes the production plan.
#### Input:
- Draft plan (report) from InitialSched Agent
- Reports from Resin Tracking Agent, Mold Tracking Agent, and Machine Tracking Agent
#### Process:
Optimize the draft plan by addressing flagged issues and integrating tracking reports. Ensure:
- Resin quantities align with stock capacity (e.g., limited to 3–4 days of production)
- Over-capacity POs are distributed across multiple molds or machines if possible
- Molds with larger cavities are prioritized
- Continuous production by prioritizing molds/machines already in use
- Consolidate small-quantity POs to minimize machine downtime
#### Output:
Optimized Production Plan
#### Key Scalable Features: 
Incorporates multi-agent feedback and balances workloads dynamically.
#### Healing System Actions: 
Auto-adjust plans when critical data changes (e.g., sudden stock depletion or machine failure).

### 4. ResinTracking Agent

#### **Role:**  
Tracks **resin stock levels** and usage trends to flag shortages, prevent overstocking, and support resin provision for production.  

#### **Input:**  
- **PO_list** – Tracks active and completed POs.  
- **productRecord** – Logs actual resin usage.  
- **historicalResinUsage** – Monitors past consumption trends.  
- **resinReceivingRecord** – Updates received resin stock.  

#### **Process:**  
- **Update resin stock** by tracking received and consumed quantities.  
- **Identify risks** (e.g., low stock) based on **2-3 days of active PO needs**.  
- **Validate resin provision** for completed POs and flag mismatches.  
- **Highlight shortages/excess** by comparing **default vs. actual usage**.  

#### **Output:**  
- **Resin Stock Report** – Tracks stock levels and consumption.  
- **Resin Shortage Alert Report** – Flags upcoming resin risks.  
- **Resin PO Tracking Report** – Monitors provision and excess resin return.  

#### **Key Scalable Features:**  
- **Predictive analytics** for resin restocking based on usage patterns.  
- **Optimized resin allocation** by integrating with production planning.  

#### **Healing System Actions:**  
- Highlight and adjust for **mismatched resin data** in POs.  
- Raise **import flags** for completed POs without recorded resin provision.  


### 5. MoldTracking Agent
**Role:**  
Tracks mold usage and maintenance.  

**Input:**  
- `PO_list`  
- `productRecord`  
- `historical mold maintenance data`  

**Process:**  
- Monitor mold usage, accumulated shots, and maintenance history.  
- Identify molds nearing maintenance thresholds or used beyond capacity.  

**Output:**  
- **Mold Usage Report** with flagged risks.  

**Key Scalable Features:**  
- Reinforcement learning for smarter maintenance scheduling.  

**Healing System Actions:**  
- Alert for molds exceeding shot limits or incorrect usage.  

### 6. MachineTracking Agent
**Role:**  
Tracks machine production continuity, mold changes, and first usage records.  

**Input:**  
- `PO_list`  
- `productRecord`  
- `historical machine operation data`  

**Process:**  
- Monitor machine production per shift, flag idle periods, and yield = 0 cases.  
- Track mold changes per shift.  
- Generate a **Mold-Machine Pair Matrix** (first usage records).  

**Output:**  
- **Machine Production Report** with flagged downtime and mold changes.  
- **Mold-Machine Pair Matrix** for planning.  

**Key Scalable Features:**  
- Machine learning for downtime prediction.  

**Healing System Actions:**  
- Auto-adjust schedules if machine downtime exceeds thresholds.  

### 7. ResinCoordinate Agent
#### Role:
Optimizes resin usage and manages runner recycling.
#### Input:
- Optimized Production Plan from FinalSched Agent
- Resin Stock Report from Resin Tracking Agent
- Historical Runner Data
- Granulator/Shredder Processing Rate
#### Process:
- Forecast resin usage, accounting for new and recycled resin
- Automate runner recycling with granulators/shredders
- Predict optimal resin reuse ratios using historical data
- Integrate runner reuse data with Yield Optimization Agent
#### Output:
Resin Usage and Recycling Report
#### Key Scalable Features:
- Automated runner recycling workflow
- Predictive reuse models for resin optimization
- Integration with Yield Optimization for production efficiency
#### Healing System Actions:
- Adjust resin forecasts based on recycling efficiency and yield optimization data

### 8. MaintenanceScheduler Agent
#### Role: 
Schedules mold and machine maintenance.
#### Input:
- Optimized Production Plan from FinalSched Agent
- Mold and Machine Usage Reports from tracking agents
#### Process:
- Develop a maintenance schedule for molds and machines
- Ensure maintenance aligns with production needs to minimize downtime
#### Output:
Maintenance Schedule
#### Key Scalable Features: 
Aligns with production needs to minimize downtime.
#### Healing System Actions: 
Proactively reschedule based on real-time agent feedback.

### 9. QualityControl Agent  

**Role:**  
Monitors production quality by tracking yield deviations, mold changes, and color changes.  

**Input:**  
- productRecord  
- historical quality data  
- moldInfo (static database)  

**Process:**  
- Calculate **expected yield** based on mold cycle time and cavity.  
- Identify **yield deviations** and **estimate setup time** if mold/color changes occur.  
- Track **NG rates** and flag issues exceeding thresholds.  

**Output:**  
- **Quality Control Report** with:  
  - Expected vs. actual yield  
  - Mold/color change tracking  
  - Estimated setup time  
  - NG rate warnings  

**Key Scalable Features:**  
- Adaptive **yield and NG analysis** with adjustable thresholds.  
- Setup time estimation based on **actual production data**.  

**Healing System Actions:**  
- Auto-flag mold/color changes affecting production.  
- Adjust thresholds for **yield deviation** and **NG rate warnings** dynamically.  

### 10. YieldOptimization Agent
#### Role:
Optimizes yield and resin allocation.
#### Input:
- productRecord
- historical yield data
#### Process:
- Monitor actual yield vs. default yield
- Evaluate impact of cycle time changes on yield and NG rates
- Suggest optimized cycle times and resin quantities
#### Output:
Yield Optimization Report for long-term insights
#### Key Scalable Features:
- Cycle time and resin optimization
- Efficiency trade-offs and NG minimization
#### Healing System Actions:
Revert to default settings if optimizations lead to excessive NG rates


### 11. DashBoardBuilder Agent
#### Role: 
Visualizes system data for decision-making.
#### Input: 
Reports from all agents
#### Process:
- Generate daily production reports using AutoStatus Agent data
- Visualize plans (Production, Mold, Material, Machine) from FinalSched Agent, ResinRestock Agent, and MaintenanceScheduler Agent
- Provide insights from Quality Control Agent and YieldOptimization Agent for decision-making
- Optionally visualize logs/flags for quick issue identification
#### Output:
Comprehensive dashboards for daily operations, plans, and long-term insights
#### Key Scalable Features: 
Expand dashboard capabilities with AI-driven insights and prediction models.
#### Healing System Actions: 
Highlight inconsistencies or missing data in reports for quick resolution.

#### Note:
1. Shared Database Implementation:
- Consider a hybrid approach (SQL + NoSQL) where structured data (production status, schedules) remains in SQL, while flexible, high-volume data (logs, agent reports) uses NoSQL for better performance.

2. Agent Communication & Coordination:
- Define an event-driven mechanism where agents trigger actions based on specific conditions (e.g., machine failure prompts rescheduling).
- Use a message queue system (e.g., RabbitMQ, Kafka) for efficient agent interaction in real-time.

3. Healing System Enhancements:
- Implement automated rollback mechanisms in case of faulty optimizations (e.g., if YieldOptimization Agent suggests a cycle time that increases NG rates).
- Introduce periodic agent health checks to detect slow performance or missing updates.

4. Reinforcement Learning (RL) Roadmap:
- Phase 1: Collect historical feedback data for supervised learning.
- Phase 2: Integrate RL into YieldOptimization Agent to refine cycle times dynamically.
- Phase 3: Expand RL to FinalSched Agent for optimizing production sequences.

5. Performance & Scalability:
- Introduce parallel processing for critical agents (e.g., FinalSched Agent, MaintenanceScheduler Agent).
- Optimize database queries for agents requiring frequent updates (e.g., AutoStatus Agent).