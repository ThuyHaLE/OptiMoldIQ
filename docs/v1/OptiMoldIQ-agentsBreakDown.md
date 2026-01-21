# Agent Breakdown

## 1. DataPipelineOrchestrator
**Roles:**
- **Collector**: Automatically gathers data from distributed sources on a monthly basis (POs, production logs, mold/machine/resin info).
- **Loader**: Standardizes and merges data into the shared database.

**Inputs:** Excel/CSV files or internal storage tables.  
**Outputs:** Standardized, unified database shared across agents.  
**Dependencies:** First step in the pipeline, responsible for triggering the entire process.

**Key Features:**
- Monthly auto-scheduling for raw data ingestion.
- Schema validation and format unification.
- Handles multiple input types (Excel, CSV, JSON).
 
**Healing Actions:**
🔄 Upcoming

---

## 2. ValidationOrchestrator
**Roles:**
- **PORequiredCriticalValidator**: Verifies links between productRecords and purchaseOrders.
- **StaticCrossDataChecker**: Cross-checks with static tables like mold-machine-resin.
- **DynamicCrossDataValidator**: Validates against real production data.

**Inputs:** Data from the shared DB provided by DataPipelineOrchestrator.  
**Outputs:** Error/warning lists, validity reports.  
**Interactions:** Feeds back to AutoPlanner for refinement.

**Key Features:**
- Multi-source rule-based validation engine.
- Reports missing, inconsistent, or conflicting records.
- Sends structured validation results to other agents.
 
**Healing Actions:**
🔄 Upcoming

---

## 3. OrderProgressTracker
**Roles:**
- Tracks production output per machine and per shift.
- Back-maps logs to PO to verify plan-reality alignment.

**Inputs:** Daily production logs, PO data.  
**Outputs:** Progress reports, order status, mismatch alerts.  
**Dependencies:** Supports ValidationOrchestrator and AutoPlanner for plan refinement.

**Key Features:**
- Real-time sync with production logs.
- Generates alerts for missed or delayed orders.
- Cross-checks plan execution vs actual production.
 
**Healing Actions:**
🔄 Upcoming

---

## 4. AutoPlanner
**Roles:**
- **InitialPlanner**: Creates initial plans based on static data (resin, mold, machine specs) and historical insights (if date records are sufficient for historical insights).
- **PlanRefiner**: Optimizes and adjusts plans using real-time data and validation feedback.

**Inputs:** PO, stock, machine/mold/resin capabilities and historical records.  
**Outputs:** Detailed production schedules by machine.  
**Interactions:** Integrates feedback from TaskOrchestrator, ValidationOrchestrator, and Tracker.

**Key Features:**
- Rule-based planning using constraints.
- Refinement loop based on actual shop floor feedback.
- Suggests alternative plans during constraints/conflicts.
 
**Healing Actions:**
🔄 Upcoming

---

## 5. AnalyticsOrchestrator
**Roles:**
- **DataChangeAnalyzer**: Tracks changes over time (machine relocation, mold changes...).
- **MultiLevelDataAnalytics**: Aggregates insights at various time levels (year/month/day/shift).

**Inputs:** Historical production logs, validation results.  
**Outputs:** Dashboards, trend reports, anomaly alerts.  
**Dependencies:** Feeds insights to DashBoardBuilder and improvement suggestions to AutoPlanner.

**Key Features:**
- Time-series analysis and historical comparison.
- Detects usage trends and irregularities.
- Supports performance benchmarking and forecasting.
 
**Healing Actions:**
🔄 Upcoming

---

## 6. TaskOrchestrator
**Roles:**
- **ResinCoordinator**: Manages resin inventory and consumption forecasts.
- **MoldCoordinator**: Tracks molds, maintenance schedule, and cavity adjustments.
- **MachineCoordinator**: Monitors machine activity, idle time, and efficiency.
- **ProductQualityCoordinator**: Analyzes NG rate and yield.
- **MaintenanceCoordinator**: Suggests maintenance schedules for molds/machines.
- **YieldOptimizator**: Proposes optimization based on cycles, NG, and resin usage.

**Inputs:** Real shop floor data, shared DB.  
**Outputs:** Alerts, improvement suggestions, maintenance plans.  
**Interactions:** Supplies constraints and recommendations to AutoPlanner.

**Key Features:**
- Acts as a bridge between operation floor and planning logic.
- Monitors real-time performance, waste, and capacity.
- Sends optimization flags for low-yield or underutilization.
  
**Healing Actions:**
🔄 Upcoming

---

## 7. DashBoardBuilder
**Roles:**
- Builds real-time dashboards for monitoring and decision support.

**Inputs:** Analytics data from AnalyticsOrchestrator, progress from Tracker, alerts from TaskOrchestrator.  
**Outputs:** Interactive dashboards, visualized KPIs, charts.  
**Users:** Managers, technicians, and production coordinators.

**Key Features:**
- Live data sync and filtering capabilities.
- Custom views per department (QA, production, planning).
- Supports export and reporting features (PDF, Excel).

**Healing Actions:**
🔄 Upcoming