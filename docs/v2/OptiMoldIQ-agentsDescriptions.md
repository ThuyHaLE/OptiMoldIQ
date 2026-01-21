> Status: Introduced in v2  
> Purpose: Describe the responsibilities, data interactions, and orchestration roles of each agent, serving as a conceptual reference rather than an implementation specification.

# System Architecture Overview

OptiMoldIQ uses a **multi-agent architecture** to operationalize these orchestration layers:
```
optiMoldMaster (Mother Agent) 🔄                        # Overall system in progress
│
├─ Data Operations Layer ✅                             # This layer is complete
│  ├─ dataPipelineOrchestrator ✅                           # ETL: collect & load data
│  ├─ validationOrchestrator ✅                             # Multi-layer data validation
│  └─ orderProgressTracker ✅                               # Production tracking (daily batch)
│
├─ Production Planning Layer 🔄                          # This layer partially complete
│  └─ autoPlanner 🔄
│     ├─ initialPlanner ✅                                  # Generate optimal plans
│     └─ planRefiner 📝                                     # Refine with real-time data
│
├─ Insight Analytics Layer 🔄                            # This layer partially complete
│  └─ analyticsOrchestrator 🔄                              # Dual-mode: Standalone or backend service 
│     ├─ hardwareChangeAnalyzer ✅                          # Machine & mold change tracking
│     ├─ multiLevelPerformanceAnalyzer ✅                   # Day/Month/Year performance analytics
│     └─ crossLevelPerformanceAnalyzer 📝                   # Advanced cross-functional analytics
│
├─ Visualization & Report Generating Layer 🔄            # This layer partially complete
│  └─ dashboardBuilder 🔄                                   # Consumes Analytics Orchestrator
│     ├─ multiLevelPerformanceVisualizationService ✅         # Day/Month/Year static visualizations
│     ├─ hardwareChangeVisualizationService ✅                # Hardware change visualizations
│     └─ dynamicDashboardUI 📝                                # Interactive web dashboards
│
└─ Operational Task Coordinating Layer 📝                 # This layer fully planned 
    └─ taskOrchestrator 📝                                  # Consumes Analytics Orchestrator
       ├─ resinCoordinator 📝                                 # Resin inventory management
       ├─ maintenanceCoordinator 📝                           # Predictive mold-machine maintenance
       ├─ productQualityCoordinator 📝                        # Quality optimization
       └─ yieldOptimizer 📝                                   # Yield optimization
```

> **Note:** `optiMoldMaster` functions as the **mother-agent**, orchestrating all child agents. Each child agent operates autonomously but synchronizes through shared data and event channels.
>
> ---
> 
> **Analytics Orchestrator - Dual Architecture Modes:**
> 
> - **Standalone Mode**: 
>   ```
>   analyticsOrchestrator.run_analyzing() → Direct outputs (TXT, JSON, XLSX)
>   ```
> 
> - **Integrated Mode** (Config Injection Pipeline):
>   ```
>   Consumer Agent → [Component]Config → Auto-Config 
>   → AnalyticsOrchestrator.run_analyzing() → Analytics Results 
>   → Consumer Processing → Outputs
>   ```
>   
> ---
> 
> **Config-Driven Orchestration Pattern:**
> 
> Consumer agents embed `AnalyticsOrchestratorConfig` to trigger specific analyzers, then consume results:
> 
> - **dashboardBuilder**:
>   - `multiLevelPerformanceVisualizationService` → `multiLevelPerformanceAnalyzer` → day/month/year visualizations
>   - `hardwareChangeVisualizationService` → `hardwareChangeAnalyzer` → machineLayout/machineMoldPair visualizations
> 
> - **taskOrchestrator** (planning):
>   - `resinCoordinator` → relevant analyzers → inventory actions
>   - `maintenanceCoordinator` → relevant analyzers → maintenance scheduling
>   - *[similar pattern for other coordinators]*

# Agent Descriptions
> 👉 [Details](docs/OptiMoldIQ-agentsBreakDown.md)

| Agent | Type | Summary | Status |
|-------|------|----------|--------|
| optiMoldMaster | Mother Agent | Central coordinator managing all manufacturing operations | 🔄 |
| dataPipelineOrchestrator | Child Agent | 2-phase ETL pipeline for data collection and loading | ✅ |
| validationOrchestrator | Child Agent | Multi-layer data validation | ✅ |
| orderProgressTracker | Child Agent | Production tracking (daily batch) | ✅ |
| autoPlanner | Child Agent | Advanced production planning engine | 📝 |
| initialPlanner | Sub-component | Generates initial production plan | ✅ |
| planRefiner | Sub-component | Refines and adjusts initial production plans | 📝 |
| analyticsOrchestrator | Child Agent | Central analytics facade (dual-mode: standalone/backend service) | 🔄 |
| hardwareChangeAnalyzer | Sub-component | Tracks machine/mold layout and pairing changes | ✅ |
| multiLevelPerformanceAnalyzer | Sub-component | Day/Month/Year hierarchical performance analytics | ✅ |
| crossLevelPerformanceAnalyzer | Sub-component | Advanced cross-functional analytics service | 📝 |
| dashboardBuilder | Child Agent | Visualization facade consuming Analytics Orchestrator | 🔄 |
| multiLevelPerformanceVisualizationService | Sub-component | Day/Month/Year static reports & visualizations | ✅ |
| hardwareChangeVisualizationService | Sub-component | Machine/mold change visualizations | ✅ |
| dynamicDashboardUI | Sub-component | Interactive web-based dashboards | 📝 |
| taskOrchestrator | Child Agent | Coordinates operational tasks | 📝 |
| resinCoordinator | Sub-component | Manages resin inventory and consumption | 📝 |
| maintenanceCoordinator | Sub-component | Predictive mold-machine maintenance scheduling | 📝 |
| productQualityCoordinator | Sub-component | Tracks yield and defects | 📝 |
| yieldOptimizer | Sub-component | Optimizes cycle time and yield | 📝 |

---
 
## OptiMoldMaster (Mother Agent) 🔄

`optiMoldMaster` acts as the **central coordinator**, managing the entire OptiMoldIQ manufacturing operations system.  
It orchestrates all child agents to ensure seamless workflow across data processing, planning, analytics, reporting, and operational tasks.

**Responsibilities**
- End-to-end data processing:  
  - `dataPipelineOrchestrator` (data ingestion)  
  - `validationOrchestrator` (data integrity)  
  - `orderProgressTracker` (production tracking)
- Multi-stage production planning via `autoPlanner`
- Centralized analytics and reporting via `analyticsOrchestrator` + `dashboardBuilder`
- Task-level optimization and coordination via `analyticsOrchestrator` + `taskOrchestrator`

---

## Core Components (Child Agents) 🔄

### 2.1 dataPipelineOrchestrator ✅

**Role:**  
Manages the **two-phase ETL pipeline** for both static and dynamic manufacturing data.

**Functions**
- **Phase 1: Collection (via DataCollector):** Gathers distributed monthly data from multiple sources.  
- **Phase 2: Loading (via DataLoaderAgent):** Consolidates and loads into the shared manufacturing database.  
- Supports both **static (master data)** and **dynamic (production records)**.  
- Includes **error-recovery workflows** and **automated alerting** mechanisms.

**Purpose:**  
Ensures stable, reproducible, and traceable manufacturing data ingestion.

### 2.2 validationOrchestrator ✅

**Role:**  
Enforces multi-layer validation across all incoming manufacturing data streams.

**Validation Layers**
- **Static Validation:** Schema, datatype, integrity checks.  
- **Dynamic Validation:** Anomaly detection, cross-table consistency validation.  
- **Required-Field Validation:** Ensures critical data completeness.  
- Maintains **version-controlled validation reports** for traceability and audits.

**Purpose:**  
Guarantees high data integrity and reliability across all downstream processes.

### 2.3 orderProgressTracker ✅

**Role:**  
Provides **operational visibility** across production orders through daily batch processing.

**Functions**
- Tracks production progress and order lifecycle.  
- Monitors **status transitions**, **cycle completion**, and **schedule adherence**.  
- Aggregates per-machine and per-shift data.  
- Maps production records back to purchase orders and flags discrepancies.

**Output:**  
Consolidated production analytics and performance indicators.

### 2.4 autoPlanner 🔄

**Role:**  
Advanced production planning engine with two-stage optimization.

**Subcomponents**

1. **initialPlanner ✅**  
   - Generates initial production plans using historical patterns and compatibility analysis.  
   - Multi-stage pipeline transforming raw data → optimized mold–machine assignment plan.  
   - Two-tier optimization criteria:  
     - Historical machine performance  
     - Technical compatibility  
     - Load balancing  
     - Quality & efficiency constraints  
   - Includes plan-quality validation and error handling.

2. **planRefiner 📝**  
   - Refines initial plans using real-time analytics and operational data (e.g., resin stock, maintenance schedules).  
   - Performs **capacity shift analysis**, **conflict detection**, and **plan adjustments** based on live updates.

**Purpose:**  
Provides adaptive and intelligent scheduling aligned with real factory conditions.

### 2.5 analyticsOrchestrator 🔄

**Role:**  
Central analytics facade orchestrating multiple complementary analytics functions through a dual-mode architecture: (1) standalone analytics execution with direct output persistence, (2) shared backend service for visualization and operational layers. Provides comprehensive, multi-faceted data insights supporting dashboard generation, task coordination, and production planning refinement.

**Subcomponents**

1. **hardwareChangeAnalyzer ✅**
- Coordinates and executes **historical change analyses** for both machines and molds over time.  
- Generates **change tracking reports** capturing configuration evolution and operational patterns.  
- Operates in dual modes: standalone analytics or backend service for `hardwareChangeVisualizationService`.
- **Modules:**
  - *MachineLayoutTracker*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
  - *MachineMoldPairTracker*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
- **Output:** Historical change logs, configuration reports (TXT, JSON, XLSX).
- **Service-Consumer Relationship:**
  - `machineLayoutTracker` → `machineLayoutVisualizationPipeline` ✅
  - `machineMoldPairTracker` → `machineMoldPairPipeline` ✅

2. **multiLevelPerformanceAnalyzer ✅**
- Orchestrates and executes **comprehensive data processing pipeline** across multiple time granularities (day/month/year).
- Generates **structured analytics outputs** for consumption by dashboard builders and downstream agents (planRefiner, taskOrchestrator).
- Operates in dual modes: standalone analytics or backend service for `multiLevelPerformanceVisualizationService`.
- **Modules:**
  - *DayLevelDataProcessor*: Processes daily production data with mold-based and item-based aggregations, generating real-time operational metrics and summary statistics
  - *MonthLevelDataProcessor*: Analyzes monthly production patterns, distinguishing finished and unfinished orders to track completion rates and identify trends
  - *YearLevelDataProcessor*: Performs annual production analysis, providing long-term insights into finished/unfinished orders and yearly performance summaries
- **Output:** Multi-level processed DataFrames with aggregated records and statistical summaries (TXT, JSON, XLSX).
- **Service-Consumer Relationship:**
  - `dayLevelDataProcessor` → `dayLevelDataVisualizationPipeline` ✅
  - `monthLevelDataProcessor` → `monthLevelDataVisualizationPipeline` ✅
  - `yearLevelDataProcessor` → `yearLevelDataVisualizationPipeline` ✅
  - Future consumers: `planRefiner`, `taskOrchestrator`, `dynamicDashboardUI` 📝

3. **crossLevelPerformanceAnalyzer 📝 (Advanced Analytics)**
- **Purpose:** Advanced cross-functional analytics service
- **Target Users:** taskOrchestrator, planRefiner, dynamicDashboardUI
- **Status:** Specification in progress
- **Planned Features:** Predictive analytics, decision optimization, cross-level insights

**Operates in dual architecture:**
- **Mode 1 - Standalone Execution**: Direct analytics with output persistence (TXT, JSON, XLSX)
- **Mode 2 - Backend Service**: Config-driven orchestration for consumer agents via auto-config injection

```
  [Component]Config → Auto-Config → AnalyticsOrchestrator.run_analyzing() 
  → Analytics Results → Consumer Processing → Outputs
```

---

### 2.6 dashboardBuilder 🔄

**Role:**
Unified visualization facade providing dual-mode dashboard capabilities through config-driven orchestration: (1) static report generation for scheduled distribution and archival, (2) interactive web platform for real-time data exploration. Orchestrates `analyticsOrchestrator` as a shared backend service via config injection.

**Subcomponents**

1. **multiLevelPerformanceVisualizationService ✅ (Static Report Generator)**
- Coordinates **static dashboard generation** across multiple time resolutions (day/month/year).
- Manages **execution flow** with flexible configuration, auto-configuration, and error isolation.
- Operates as a **batch processing layer** — generates scheduled reports for distribution and archival.
- **Config Injection:** Embeds `AnalyticsOrchestratorConfig` to trigger `multiLevelPerformanceAnalyzer`, then consumes analytics results for visualization.

**Configuration (`PerformancePlotflowConfig`):**
  - Time parameters: `record_date`, `record_month`, `record_year`
  - Analysis dates: `month_analysis_date`, `year_analysis_date`
  - Shared paths: `source_path`, `annotation_name`, `databaseSchemas_path`
  - Performance: `enable_parallel`, `max_workers` (optional parallel processing)
  - Embedded: `analytics_orchestrator_config` (auto-configured)

**Modules:**
  - *DayLevelDataVisualizationPipeline*: Generates daily operational dashboards with real-time metrics visualization, production summaries, and mold performance reports
  - *MonthLevelDataVisualizationPipeline*: Creates monthly trend dashboards tracking completion rates, production patterns, and month-to-date performance analysis
  - *YearLevelDataVisualizationPipeline*: Produces annual strategic dashboards with long-term trends, yearly summaries, and performance comparisons

**Output:** 
  - Static PNG images for visual dashboards
  - TXT reports for quick summaries
  - XLSX spreadsheets for detailed data tables
  - Saved to configured directories for email distribution and archival

**Orchestration Flow:**
```
  **Config Injection Pipeline:**
  PerformancePlotflowConfig 
    → Embeds AnalyticsOrchestratorConfig 
    → Auto-triggers multiLevelPerformanceAnalyzer

  **Data Processing Flow:**
  Analytics: [day/month/year]LevelDataProcessor 
    → Analytics Results (DataFrames)
    → Visualization: [day/month/year]LevelDataVisualizationPipeline 
    → Outputs (PNG/TXT/XLSX)
```

2. **hardwareChangeVisualizationService ✅ (Hardware Change Visualization)**
- Coordinates **hardware change visualizations** for machine layouts and machine-mold pairs.
- Manages **execution flow** with flexible configuration, auto-configuration, and error isolation.
- Operates as a **batch processing layer** — generates change reports and visualizations.
- **Config Injection:** Embeds `AnalyticsOrchestratorConfig` to trigger `hardwareChangeAnalyzer`, then consumes analytics results for visualization.

**Configuration (`HardwareChangePlotflowConfig`):**
  - Shared paths: `source_path`, `annotation_name`, `databaseSchemas_path`
  - Performance: `enable_parallel`, `max_workers` (optional parallel processing)
  - Embedded: `analytics_orchestrator_config` (auto-configured)

**Modules:**
  - *MachineLayoutVisualizationPipeline*: Generates machine layout evolution visualizations and change reports
  - *MachineMoldPairVisualizationPipeline*: Creates mold-machine relationship visualizations and utilization reports

**Output:**
  - Static PNG images for change visualizations
  - TXT reports for change summaries
  - Saved to configured directories for distribution and archival

**Orchestration Flow:**
```
  HardwareChangePlotflowConfig → Auto-Config → AnalyticsOrchestrator.hardwareChangeAnalyzer
  → [machineLayout/machineMoldPair]Tracker → Analytics Results 
  → [machineLayout/machineMoldPair]VisualizationPipeline → Visualizations (PNG/TXT)
```

3. **dynamicDashboardUI 📝 (Interactive Dashboard Platform)**
- Provides **web-based interactive dashboards** with real-time data exploration. 📝
- Manages **live data streaming** and user interactions for dynamic analysis. 📝
- Operates as a **real-time service layer** — enables on-demand data visualization and drill-down analysis. 📝

**Service Layer Architecture:**
```
Analytics Orchestrator (Backend Service)          Dashboard Builder (Visualization Consumer)
        ↓                                                      ↓
┌─────────────────────────────────┐           ┌─────────────────────────────────────────────────────┐
│ multiLevelPerformanceAnalyzer   │           │ multiLevelPerformanceVisualizationService           │
│  ├─ dayLevelDataProcessor    ───┼──────────→│  ├─ dayLevelDataVisualizationPipeline (PNG/TXT/XLS) │
│  ├─ monthLevelDataProcessor  ───┼──────────→│  ├─ monthLevelDataVisualizationPipeline             │
│  └─ yearLevelDataProcessor   ───┼──────────→│  └─ yearLevelDataVisualizationPipeline              │
└─────────────────────────────────┘           └─────────────────────────────────────────────────────┘

┌─────────────────────────────────┐           ┌─────────────────────────────────────────────────────┐
│ hardwareChangeAnalyzer          │           │ hardwareChangeVisualizationService                  │
│  ├─ machineLayoutTracker     ───┼──────────→│  ├─ machineLayoutVisualizationPipeline (PNG/TXT)    │
│  └─ machineMoldPairTracker   ───┼──────────→│  └─ machineMoldPairVisualizationPipeline            │
└─────────────────────────────────┘           └─────────────────────────────────────────────────────┘

                                              ┌──────────────────────────────────────┐
                                              │ dynamicDashboardUI 📝               │
    Future: Real-time consumption ───────────→│  ├─ Interactive Web (Browser)        │
                                              │  ├─ Real-time Streaming (WebSocket)  │
                                              │  └─ Advanced Filtering & Drill-down  │
                                              └──────────────────────────────────────┘
```

#### 2.7 taskOrchestrator 📝

**Role:**  
Coordinates cross-dependent operational activities to prevent downtime and optimize production efficiency.

**Functions**
- Manages resource availability and production constraints.  
- Feeds critical operational data to `planRefiner` for real-time plan optimization.  
- Implements **proactive task management**, **maintenance scheduling**, and **escalation handling**.

**Subcomponents**

- **resinCoordinator:** Tracks resin stock, consumption, and forecasts material needs.  
- **maintenanceCoordinator:** Handles predictive mold-machine maintenance scheduling, working alongside `moldCoordinator` and `machineCoordinator`.
  - **moldTracker:** Tracks mold status, lifecycle, production and maintenance history.
  - **machineTracker:** Monitors machine conditions, performance metrics, activity schedules and maintenance history.
- **productQualityCoordinator:** Monitors yield, NG rates, and defect analysis.  
- **yieldOptimizer:** Evaluates cycle times and resin efficiency; recommends performance improvements.

**Purpose:**  
Maintains stable, optimized operations across all production assets.

### System Connectivity Summary

- **Data Layer** → powers → `Planning`, `Analytics`, and `Task` orchestration layers.  
- **Planning Layer** ↔ **Task Layer** → continuously refine and optimize schedules.  
- **Analytics Layer** (Service) → feeds → **Reporting Layer** (Consumer) through processor-to-plotter mapping.
- **Analytics Layer** → also feeds → `Planning` systems for plan refinement. 
- **Reporting Layer** → provides insights to human decision-makers.  

Together, these layers form a **closed feedback loop** where data → planning → execution → analytics → continuous improvement.

### Execution Flow

```
                                        RAW DATA
                                            ↓ 
                                    DATA OPERATIONS
                                            ├─→ VALIDATION ─────────┐
                                            |                       ├────────────────────────────────────────────────────────────→ TRACKING ─→ PLANNING
                                            └─→ SHARED DATABASE ────┘                                                                              ↓
                                                      ↓                                                                                    ┌────────────────┐          
        ┌─────────────────────────────────────────────┼───────────────────────────────────────────────────┐                                ↓                ↓           
        ↓                                             ↓                                                   ↓                          INITIAL PLAN     REFINER PLAN 📝
    ANALYTICS ORCHESTRATOR                    DASHBOARD BUILDER                                   TASK ORCHESTRATOR                                    (Consumer)   
   (Dual-Mode: Standalone/Backend)         (Visualization Consumer)                             (Operational Consumer)                                      ↑
        |                                             |                                                   |                                                 |
        ├→ Hardware Change Analyzer ───────────────→  ├→ Hardware Change Visualization Service            |                                                 |
        |  (machineLayout, machineMoldPair)           |  (Visualizations: PNG/TXT)                        |                                                 |
        |                                             |                                                   |                                                 |
        ├→ Multi-Level Performance Analyzer ───────→  ├→ Multi-Level Performance Visualization Service    |                                                 |
        |  (day/month/year analytics)                 |  (Visualizations: PNG/TXT/XLSX)                   |                                                 |
        |                                             |                                                   |                                                 |
        |                                             └→ Dynamic Dashboard UI (Web) 📝                    |                                                 |
        |                                                                                                 |                                                 |
        ├→ Cross-Level Performance Analyzer 📝 ─────────────────────────────────────────────────────────→ └→ Operational Coordinators 📝                   |
        |  (advanced predictive analytics)                                                              (resin, maintenance, quality, yield)                |
        |                                                                                                                                                   |
        └───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                                  (Future: Cross-Level insights for planning)
```