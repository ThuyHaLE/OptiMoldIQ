  🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

*AI-driven orchestration system for end-to-end manufacturing optimization.*

---

## Table of Contents
- [OptiMoldIQ: Intelligent Plastic Molding Planner](#optimoldiq-intelligent-plastic-molding-planner)
  - [Table of Contents](#table-of-contents)
  - [Project Status](#project-status)
  - [Overview](#overview)
  - [Business Problem](#-business-problem)
  - [Problem–Driven Solution Overview](#-problemdriven-solution-overview)
    - [Strategic Alignment](#strategic-alignment)
    - [Goals and Planned Solution](#goals-and-planned-solution)
  - [System Architecture Overview](#system-architecture-overview)
  - [Agent Descriptions](#agent-descriptions)
    - [OptiMoldMaster (Mother Agent)](#optimoldmaster-mother-agent-)
    - [Core Components (Child Agents)](#core-components-child-agents-)
    - [System Connectivity Summary](#system-connectivity-summary)
    - [Execution Flow](#execution-flow)
  - [System Architecture Diagram](#system-architecture-diagram)
  - [Databases Overview](#databases-overview)
    - [Raw Database](#raw-database)
    - [Shared Database (Processed for Multi-Agent System)](#shared-database-processed-for-multi-agent-system)
  - [Folder Structure](#folder-structure)
  - [Milestones](#milestones)
    - [Milestone 01: Core Data Pipeline Agents (Completed July 2025)](#milestone-01-core-data-pipeline-agents-completed-july-2025)
    - [Milestone 02: Initial Production Planning System (Completed August 2025)](#milestone-02-initial-production-planning-system-completed-august-2025)
    - [Milestone 03: Analytics Orchestration & Multi-Level Dashboard Agents (Completed November 2025)](#milestone-03-analytics-orchestration--multi-level-dashboard-agents-completed-november-2025)
    - [In Progress: AnalyticsOrchestrator & TaskOrchestrator](#in-progress-analyticsorchestrator--taskorchestrator)
  - [Quickstart](#quickstart)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

---

## Project Status

Current Phase: finalizing documentation for Milestone 03, covering analytics orchestration, dashboard building, multi-resolution dashboards, and change detection workflows.

Legend: ✅ Complete | 🔄  In Progress | 📝 Planned

---

## Overview

**OptiMoldIQ** is a multi-agent intelligent manufacturing system designed to optimize injection molding operations through automated data pipelines, validation, production planning, analytics, and real-time decision support.

It centralizes operational intelligence by coordinating data, machines, molds, and scheduling under a unified architecture.  

---

<!-- 🌐 Interactive Lite Version Box -->
<div align="center" style="border:2px solid #4CAF50; padding:20px; border-radius:12px; background:#f0fff0; margin-bottom:20px; max-width:600px;">
  <h2 style="margin:0; color:#2E7D32;">🌐 Explore OptiMoldIQ Lite</h2>
  <p style="margin:10px 0 15px 0; color:#333; font-size:16px;">
    Visualize the injection molding workflow and dashboards interactively.
  </p>
  <a href="https://thuyhale.github.io/OptiMoldIQ/" target="_blank" 
     style="text-decoration:none; background:#4CAF50; color:white; padding:10px 20px; border-radius:8px; font-weight:bold; font-size:16px;">
    🚀 Open Lite Dashboard
  </a>
  <p style="margin-top:10px; font-size:14px; color:#555;">
    Click the button above to explore without scrolling through the full README.
  </p>
</div>

---

## 📝 Business Problem 
> 👉 [Full context](docs/OptiMoldIQ-business-problem.md)

### Background
In plastic molding production, achieving optimal efficiency while maintaining high product quality is challenging due to the complexity of interconnected factors like:
- Mold utilization and machine maintenance.
- Resin inventory management.
- Production scheduling and yield optimization.

### Challenges 
Poor management or lack of integration between components can lead to:
- Increased production downtime.
- Material waste or stock shortages.
- Unbalanced machine and mold utilization.
- Inconsistent product quality or high NG (non-good) rates.
- Reduced production yield and efficiency.

### Problem Statement
Current systems are:
- Manual or static, lacking real-time insights.
- Prone to inefficiencies in scheduling, resource tracking, and quality management.

---

## 🔄 Problem–Driven Solution Overview

### Strategic Alignment

OptiMoldIQ directly addresses each business challenge through a set of orchestrated, data-driven systems:

| **Business Challenge** | **Strategic Goal / Orchestration Focus** |
| ---------------------- | ---------------------------------------- |
| Lack of real-time data and fragmented sources | **Data Operations Orchestration** → Automate data ingestion, validation, and real-time production tracking. |
| Inefficient or manual production planning | **Production Planning Orchestration** → Optimize mold–machine assignments through initial planning and refine plans using analytics insights and operational data. |
| Limited visibility into performance and trends | **Data Insight Analytics Orchestration** → Enable multi-level data analytics, historical change analysis, and auto-detection of layout or performance trends. |
| Poor coordination between production, maintenance, and materials | **Operational Task Orchestration** → Predictive maintenance, resin restocking, asset coordination, and yield optimization to prevent downtime. |
| Static and isolated reporting systems | **Reporting & Visualization Orchestration** → Generate multi-level dashboards and evolve from static reports to dynamic, interactive visualizations. |

### Goals and Planned Solution

In response to the production challenges outlined above, the **OptiMoldIQ System** was built as a **multi-agent orchestration framework** that transforms fragmented manufacturing operations into a unified, data-driven ecosystem. These orchestration layers collectively form the operational backbone of OptiMoldIQ, enabling synchronized workflows from raw data collection to intelligent decision-making.

#### Data Operations Orchestration
- **Daily Data Ingestion Pipeline**: Automated collection and loading of production and operational data. ✅
- **Multi-Layer Validation**: Static, dynamic, and required-field checks to ensure data integrity. ✅
- **Real-Time Production Tracking**: Monitor production progress and operational KPIs as they happen. ✅

#### Production Planning Orchestration
- **Data Insights Generating** based on historical data. ✅
- **Multi-Stage Mold–Machine Planning**:
  - Initial planning leveraging historical patterns and compatibility analysis. ✅
  - Plan refinement using insights from analytics orchestration and operational task orchestration, including resin inventory and mold/machine maintenance. 📝 

#### High-Level Orchestrations

- **Data Insight Analytics**: 
  - Historical Analytics (**dataChangeAnalyzer**) ✅ : coordinates and executes historical change analyses for both machines and molds. Visualize and generate analytical reports through two modules:
    - *UpdateHistMachineLayout*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
    - *UpdateHistMoldOverview*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
  - Multi-level insight analytics ✅ : currently process and extract data insights by multi-level (including **DayLevelDataProcessor**, **MonthLevelDataProcessor**, and **YearLevelDataProcessor** for day, month, and year views) to serve in the multi-level dashboard building phase.
  - Data insight analytics support **Operational Task Orchestration**. 📝
  - Data insight analytics support **Production Planning Orchestration** (Plan refinement phase). 📝

- **Production Insight Reporting and Visualization**: 
  - Multi-level performance reports and static dashboards generation ✅: including **DayLevelDataPlotter**, **MonthLevelDataPlotter** and **YearLevelDataPlotter** to support various requests, each plotter invokes **DayLevelDataProcessor**, **MonthLevelDataProcessor** and **YearLevelDataProcessor** corresponding to:
    - Centralized dashboard generation for multi-level production data extract with processed insights (from **DayLevelDataProcessor**, **MonthLevelDataProcessor**, and **YearLevelDataProcessor** corresponding). ✅
    - Visualization across multiple time resolutions (day/month/year) for decision support. And generate performance alerts and executive reports alongside visualization dashboards ✅
    - Upgrade from static report to dynamic UI/UX 📝

- **Operational Task Coordination**:
  - Proactive maintenance of molds and machines; resin restocking to prevent downtime and material shortages. 📝
  - Quality and yield optimization: 📝
    - Improve cycle times while maintaining product quality.
    - Enhance production yield through actionable insights.

--- 

## System Architecture Overview

OptiMoldIQ uses a **multi-agent architecture** to operationalize these orchestration layers:

```
optiMoldMaster (Mother Agent)
│
├─ Data Operations
│  ├─ dataPipelineOrchestrator ✅        # ETL: collect & load data
│  ├─ validationOrchestrator ✅          # Multi-layer data validation
│  └─ orderProgressTracker ✅            # Real-time production tracking
│
├─ Production Planning
│  └─ autoPlanner 📝
│     ├─ initialPlanner ✅               # Generate optimal plans
│     └─ planRefiner 📝                  # Refine with real-time data
│
├─ Analytics & Reporting
│  ├─ analyticsOrchestrator 📝
│  │  ├─ dataChangeAnalyzer ✅           # Track layout changes
│  │  ├─ Multi-level Analytics Service (multiLevelDataAnalytics namespace)
│  │  │  ├─ dayLevelDataProcessor ✅     # Day insight analytics
│  │  │  ├─ monthLevelDataProcessor ✅   # Month insight analytics
│  │  │  └─ yearLevelDataProcessor ✅    # Year insight analytics
│  │  └─ dataInsightAnalytics 📝         # Advanced data analytics
│  │
│  └─ Reporting & Visualization Layer (dashboardBuilder namespace)
│     ├─ dayLevelDataPlotter ✅          # Day insight reports & visualizations  
│     ├─ monthLevelDataPlotter ✅        # Month insight reports & visualizations
│     └─ yearLevelDataPlotter ✅         # Year insight reports & visualizations
│
└─ taskOrchestrator 📝
   ├─ resinCoordinator 📝                # Resin inventory
   ├─ moldCoordinator 📝                 # Mold tracking and maintenance
   ├─ machineCoordinator 📝              # Machine tracking and maintenance
   ├─ maintenanceCoordinator 📝          # Predictive mold-machine maintenance scheduling
   ├─ productQualityCoordinator 📝       # Quality optimization
   └─ yieldOptimizer 📝                  # Yield optimization
```

> *Note:* `optiMoldMaster` functions as the **mother-agent**, orchestrating all child agents below. Each child agent operates autonomously but synchronizes through shared data and event channels.

> **Service-Consumer Architecture:** The `multiLevelDataAnalytics` namespace (Analytics Service Layer) provides processed insights to the `dashboardBuilder` namespace (Visualization Consumer Layer) through a 1-to-1 processor-to-plotter mapping: `dayLevelDataProcessor` → `dayLevelDataPlotter`, `monthLevelDataProcessor` → `monthLevelDataPlotter`, `yearLevelDataProcessor` → `yearLevelDataPlotter`.

---

## Agent Descriptions
> 👉 [Details](docs/OptiMoldIQ-agentsBreakDown.md)

| Agent | Type | Summary | Status |
|-------|------|----------|--------|
| optiMoldMaster | Mother Agent | Central coordinator managing all manufacturing operations | ✅ |
| dataPipelineOrchestrator | Child Agent | 2-phase ETL pipeline for data collection and loading | ✅ |
| validationOrchestrator | Child Agent | Multi-layer data validation | ✅ |
| orderProgressTracker | Child Agent | Real-time production tracking | ✅ |
| autoPlanner | Child Agent | Advanced production planning engine | 📝 |
| initialPlanner | Sub-component | Generates initial production plan | ✅ |
| planRefiner | Sub-component | Refines and adjusts initial production plans | 📝 |
| analyticsOrchestrator | Child Agent | Central analytics hub for structured insights | 📝 |
| dataChangeAnalyzer | Sub-component | Tracks mold/machine layout changes | ✅ |
| dayLevelDataProcessor | Sub-component | Daily insight analytics | ✅ |
| monthLevelDataProcessor | Sub-component | Monthly insight analytics | ✅ |
| yearLevelDataProcessor | Sub-component | Yearly insight analytics | ✅ |
| dataInsightAnalytics | Sub-component | Advanced data analytics service | 📝 |
| dayLevelDataPlotter | Child Agent | Daily dashboard visualization | ✅ |
| monthLevelDataPlotter | Child Agent | Monthly dashboard visualization | ✅ |
| yearLevelDataPlotter | Child Agent | Yearly dashboard visualization | ✅ |
| taskOrchestrator | Child Agent | Coordinates operational tasks | 📝 |
| resinCoordinator | Sub-component | Manages resin inventory and consumption | 📝 |
| moldCoordinator | Sub-component | Tracks mold usage and maintenance requirements | 📝 |
| machineCoordinator | Sub-component | Monitors machine utilization and maintenance requirements | 📝 |
| maintenanceCoordinator | Sub-component | Predictive mold-machine maintenance scheduling | 📝 |
| productQualityCoordinator | Sub-component | Tracks yield and defects | 📝 |
| yieldOptimizer | Sub-component | Optimizes cycle time and yield | 📝 |

---

### OptiMoldMaster (Mother Agent) ✅

`optiMoldMaster` acts as the **central coordinator**, managing the entire OptiMoldIQ manufacturing operations system.  
It orchestrates all child agents to ensure seamless workflow across data processing, planning, analytics, reporting, and operational tasks.

**Responsibilities**
- End-to-end data processing:  
  - `dataPipelineOrchestrator` (data ingestion)  
  - `validationOrchestrator` (data integrity)  
  - `orderProgressTracker` (production tracking)
- Multi-stage production planning via `autoPlanner`
- Centralized analytics and reporting via `analyticsOrchestrator` + visualization agents
- Task-level optimization and coordination via `analyticsOrchestrator` + `taskOrchestrator`

---

### Core Components (Child Agents) 🔄

<details>
<summary>2.1 dataPipelineOrchestrator ✅</summary>

**Role:**  
Manages the **two-phase ETL pipeline** for both static and dynamic manufacturing data.

**Functions**
- **Collect Phase:** Gathers distributed monthly data from multiple sources.  
- **Load Phase:** Consolidates and loads into the shared manufacturing database.  
- Supports both **static (master data)** and **dynamic (production records)**.  
- Includes **error-recovery workflows** and **automated alerting** mechanisms.

**Purpose:**  
Ensures stable, reproducible, and traceable manufacturing data ingestion.
</details>

<details>
<summary>2.2 validationOrchestrator ✅</summary>

**Role:**  
Enforces multi-layer validation across all incoming manufacturing data streams.

**Validation Layers**
- **Static Validation:** Schema, datatype, integrity checks.  
- **Dynamic Validation:** Anomaly detection, cross-table consistency validation.  
- **Required-Field Validation:** Ensures critical data completeness.  
- Maintains **version-controlled validation reports** for traceability and audits.

**Purpose:**  
Guarantees high data integrity and reliability across all downstream processes.
</details>

<details>
<summary>2.3 orderProgressTracker ✅</summary>

**Role:**  
Provides **real-time operational visibility** across production orders.

**Functions**
- Tracks production progress and order lifecycle.  
- Monitors **status transitions**, **cycle completion**, and **schedule adherence**.  
- Aggregates per-machine and per-shift data.  
- Maps production records back to purchase orders and flags discrepancies.

**Output:**  
Consolidated production analytics and performance indicators.
</details>

<details>
<summary>2.4 autoPlanner 📝</summary>

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
</details>

<details>
<summary>2.5 analyticsOrchestrator 📝</summary>

**Role:**  
Central analytics hub coordinating multiple complementary analytics functions.

**Subcomponents**

1. **dataChangeAnalyzer ✅ (Standalone Function)**
- Monitors **machine and mold layout changes** over time.  
- Generates **static reports** capturing configuration deltas.  
- Operates independently — does **not** directly serve other agents.  
- **Modules:**
  - *UpdateHistMachineLayout*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
  - *UpdateHistMoldOverview*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
- **Output:** Historical change logs and configuration reports.

2. **multiLevelDataAnalytics 🔄 (Analytics Service Layer)**

*Note:* `multiLevelDataAnalytics` is a logical namespace (folder structure) grouping multi-level analytics processors that serve as the **Analytics Service Layer**.

- Processes validated manufacturing data into structured insights at multiple resolutions:  
  - `dayLevelDataProcessor` ✅: Extracts daily-level KPIs and trends
  - `monthLevelDataProcessor` ✅: Aggregates monthly performance metrics
  - `yearLevelDataProcessor` ✅: Generates yearly operational insights
- Updates **historical analytics records** with derived KPIs and trend metrics.  
- **Service-Consumer Relationship:**
  - `dayLevelDataProcessor` → `dayLevelDataPlotter` ✅
  - `monthLevelDataProcessor` → `monthLevelDataPlotter` ✅
  - `yearLevelDataProcessor` → `yearLevelDataPlotter` ✅
- **Planned consumers:** `planRefiner`, `taskOrchestrator` 📝  
- **Purpose:** Acts as a **shared service layer** ensuring consistent analytics results across all consuming agents.

3. **dataInsightAnalytics 📝 (Advanced Analytics)**
- Provides advanced data analytics capabilities for operational task orchestration and production planning refinement.
- Supports cross-functional insights for decision-making optimization.

**Output:**  
Structured KPIs, operational trends, and cross-period performance insights.
</details>

<details>
<summary>2.6 Visualization Agents (dashboardBuilder namespace) ✅</summary>

**Note:** `dashboardBuilder` is a logical namespace (folder structure) grouping three independent visualization agents that form the **Visualization Consumer Layer**. Each plotter consumes processed insights from its corresponding processor in the Analytics Service Layer.

*Architecture Pattern: Processor → Plotter (1-to-1 mapping)*

```
Analytics Service Layer          Visualization Consumer Layer
(multiLevelDataAnalytics)        (dashboardBuilder)
        ↓                                  ↓
dayLevelDataProcessor      →    dayLevelDataPlotter
monthLevelDataProcessor    →    monthLevelDataPlotter  
yearLevelDataProcessor     →    yearLevelDataPlotter
```
**Purpose:**  
Transform analytics outputs into actionable visual insights for managers and engineers across multiple time resolutions. This separation of concerns ensures that data processing logic remains independent from visualization logic, enabling flexible dashboard design without affecting underlying analytics.

1. **dayLevelDataPlotter ✅**

    **Role:**  
    Daily dashboard generation and visualization.

    **Functions**
    - Generates dashboards at **daily** resolutions.  
    - End-to-end workflow: Data extraction → Validation → Aggregation → Visualization  
    - Consumes processed insights from `dayLevelDataProcessor` to ensure consistency.  
    - Outputs **static or dynamic dashboards** for operational decision-making.

2. **2 monthLevelDataPlotter ✅**

    **Role:**  
    Monthly dashboard generation and visualization.

    **Functions**
    - Generates dashboards at **monthly** resolutions.  
    - End-to-end workflow: Data extraction → Validation → Aggregation → Visualization  
    - Consumes processed insights from `monthLevelDataProcessor` to ensure consistency.  
    - Outputs **static or dynamic dashboards** for operational decision-making.

3. **yearLevelDataPlotter ✅**

    **Role:**  
    Yearly dashboard generation and visualization.

    **Functions**
    - Generates dashboards at **yearly** resolutions.  
    - End-to-end workflow: Data extraction → Validation → Aggregation → Visualization  
    - Consumes processed insights from `yearLevelDataProcessor` to ensure consistency.  
    - Outputs **static or dynamic dashboards** for operational decision-making.

</details>

<details>
<summary>2.7 taskOrchestrator 📝</summary>

**Role:**  
Coordinates cross-dependent operational activities to prevent downtime and optimize production efficiency.

**Functions**
- Manages resource availability and production constraints.  
- Feeds critical operational data to `planRefiner` for real-time plan optimization.  
- Implements **proactive task management**, **maintenance scheduling**, and **escalation handling**.

**Subcomponents**

- **resinCoordinator:** Tracks resin stock, consumption, and forecasts material needs.  
- **moldCoordinator:** Manages mold lifecycle, usage, and maintenance requirements.  
- **machineCoordinator:** Monitors machine utilization and maintenance requirements.  
- **maintenanceCoordinator:** Handles predictive mold-machine maintenance scheduling, working alongside `moldCoordinator` and `machineCoordinator`.
- **productQualityCoordinator:** Monitors yield, NG rates, and defect analysis.  
- **yieldOptimizer:** Evaluates cycle times and resin efficiency; recommends performance improvements.

**Purpose:**  
Maintains stable, optimized operations across all production assets.
</details>

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
            DATA OPERATIONS → VALIDATION ────┐
                    |                        ├──→ TRACKING ─→ PLANNING
                    ├────────────────────────┘                   ↓
                    ↓                                    ┌───────────────┐          
        ┌────────────────────┐                           ↓               ↓           
        ↓                    ↓                     INITIAL PLAN    REFINER PLAN
    ANALYTICS --------→ DASHBOARDS                                       ↑
        | (Service)      (Consumer)                                      |
        | Optimize                                                       |
        ├────────────────────────────────────────────────────────────────┘
        ↓ 
 OPERATIONAL TASK

```

---

## System Architecture Diagram

The following diagram illustrates how **OptiMoldIQWorkflow** orchestrates data flow and agent interactions across multiple phases — from raw data ingestion to analytics and visualization. It reflects the modular multi-phase execution of agents and how data flows between orchestration layers.

For a more technical explanation, see

> 👉 [ASCII diagram](docs/OptiMoldIQ-systemDiagram-ASCII.md)

> 👉 [Directory Tree Structure](docs/OptiMoldIQ-directoryTreeStructure.md)

<details> <summary>Click to expand simplified workflow diagram</summary>

```plaintext
┌───────────────────────────────────────────────────────────────────────┐
│                         OptiMoldIQWorkflow                            │
│         (Multi-Phase Manufacturing & Analytics Orchestrator)          │
└───────────────────────────────────────────────────────────────────────┘

DATA SOURCES
    • databaseSchemas.json
    • dynamicDatabase/{monthlyReports_history, purchaseOrders_history}

──────────────────────────────────────────────────────────────────────────
PHASE 1 — DATA COLLECTION
    DataPipelineOrchestrator
        ├─ DataCollector → *_collector_report.txt
        ├─ DataLoaderAgent → *_loader_report.txt
        └─ Final pipeline report
    OUTPUT: shared_db/DataLoaderAgent/newest/*.parquet + annotations.json
    TRIGGER OUT: updateDetectionFlag

──────────────────────────────────────────────────────────────────────────
PHASE 2 — SHARED DB BUILDING (If updatesDetected)
    • Validate Data: ValidationOrchestrator
    • Track Order Status: OrderProgressTracker
    • Generate Historical Insights:
        - MoldStabilityIndexCalculator → mold stability index
        - MoldMachineFeatureWeightCalculator → machine/mold feature weights
    • Support Production & Material Coordination: ProducingProcessor

──────────────────────────────────────────────────────────────────────────
PHASE 3 — INITIAL PLANNING (If purchaseOrders changed)
    • Detect Purchase Order Changes: PurchaseOrderChangeDetection
    • Generate Planning for New Orders: PendingProcessor

──────────────────────────────────────────────────────────────────────────
PHASE 4 — ANALYTICS & VISUALIZATION
    • TriggerDetection → checks for new or changed data
    • Dashboard Builders
        - DayLevelPlotter → daily dashboards
        - MonthLevelPlotter → monthly dashboards
        - YearLevelPlotter → yearly dashboards
    • Historical Analysis Modules
        - MoldOverview → first-run machine/mold pair history extraction
        - MachineLayout → layout change history

──────────────────────────────────────────────────────────────────────────
CENTRALIZED REPORTING
    agents/shared_db/{ModuleName}/
        ├─ newest/
        ├─ historical_db/
        └─ change_log.txt

WORKFLOW UPDATING...

```
</details>

---

## Databases Overview
OptiMoldIQ leverages a **27-month production dataset** from a plastic injection molding facility, containing over **61,000 production records** and **6,200 orders**. This dataset underpins the system's planning, validation, and analytics workflows. 

In OptiMoldIQ, the raw database is loaded, collected, and processed into a shared database in a multi-agent system.

### Raw Database

**Location:** `agents/database/` 

```plaintext
agents/database/
├── databaseSchemas.json              # Database schema definitions
├── staticDatabase/                   # Static reference data (8 files)
└── dynamicDatabase/                  # Time-series data
    ├── monthlyReports_history/       # Monthly production reports
    └── purchaseOrders_history/       # Monthly purchase orders
```

> Full raw database details: [Raw Database Details](docs/OptiMoldIQ-rawDatabase.md).

#### Key Entities
| Entity                 | Count | Key Info                                              |
| ---------------------- | ------| ----------------------------------------------------- |
| **Items**              | 694   | Plastic products with code, name, type                |
| **Molds**              | 251   | Molds with cavities, cycle time, status               |
| **Machines**           | 49    | Machine code (scaled from 9→49), tonnage, manufacturer|
| **Materials**          | 445   | Base resin, color masterbatch, additives              |
| **Production Orders**  | 6,234 | Order dates, item, quantity, ETA                      |
| **Production Records** | 61,185| Daily production quantities, defects, cycle times     |

####  Relationships
- Items → Molds: 1 item ~ 1.33 molds (range: 1-3)
- Molds → Machines: 1 mold ~ 1.83 machine types (range: 1-4)
- Items → Materials: Base resin + color masterbatch + additives
  
> Full ERD and schema details: [Entity-Relationship Diagram](docs/images/OptiMoldIQ-entityRelationshipDiagram(ERD).png) & [DatabaseSchema](docs/OptiMoldIQ-dbSchema.md).

#### Quality Metrics
- 10 defect types: BlackSpot, Scratch, Crack, Short, Burst, etc.
- Lead time: Average 9.25 days
- Order cycles: Beginning and mid-month

#### Limitations
- 27-month timespan (insufficient for long-term seasonal trends)
- Missing external factors (demand forecasts, material delays)
- Single-facility data (may not generalize to other operations)

### Shared Database (Processed for Multi-Agent System)

The raw database is processed through **DataPipelineOrchestrator** (DataCollector → DataLoader) into a unified shared database that serves all agents in the OptiMoldIQ system.

**Location:** `agents/shared_db/`

```plaintext
agents/shared_db/
│
# ══════════════════════════════════════════════════════════════════
# DATA PIPELINE & VALIDATION
# ══════════════════════════════════════════════════════════════════
├── DataPipelineOrchestrator/newest/        # Pipeline execution logs (3 files)
│   ├── *_DataCollector_[success/failed]_report.txt
│   ├── *_DataLoaderAgent_[success/failed]_report.txt
│   └── *_DataPipelineOrchestrator_final_report.txt
│
├── DataLoaderAgent/newest/                 # Main Shared Database including Dynamic (2) + Static (6) + Metadata (1) = 9 files.
│   ├── [Dynamic DB] (2 files)              # *_productRecords.parquet, *_purchaseOrders.parquet
│   ├── [Static DB] (6 files)               # *_itemInfo, *_machineInfo, *_moldInfo, etc.
│   └── path_annotations.json               # Database path metadata
│
├── ValidationOrchestrator/newest/          # Data validation reports (1 file)
│   └── *_validation_orchestrator.xlsx
│
# ══════════════════════════════════════════════════════════════════
# PRODUCTION PROGRESS TRACKER
# ══════════════════════════════════════════════════════════════════
├── OrderProgressTracker/newest/            # Production & order status tracking (1 file)
│   └── *_auto_status.xlsx                  # Cross-references validation if available
│
# ══════════════════════════════════════════════════════════════════
# DATA INSIGHTS GENERATOR
# ══════════════════════════════════════════════════════════════════
├── MoldMachineFeatureWeightCalculator/     # Mold-machine compatibility scoring
│   ├── newest/                             # *_confidence_report.txt
│   └── weights_hist.xlsx                   # Historical calculations
│
├── MoldStabilityIndexCalculator/newest/    # Mold performance stability (1 file)
│   └── *_mold_stability_index.xlsx         # → Feeds ProducingProcessor
|
# ══════════════════════════════════════════════════════════════════
# PRODUCTION OPTIMIZATION
# ══════════════════════════════════════════════════════════════════
├── ProducingProcessor/newest/              # Active production analysis (1 file)
│   └── *_producing_processor.xlsx          # Uses: OrderProgress + MoldMachineFeatureWeightCalculator +  MoldStabilityIndexCalculator outputs
│
├── PendingProcessor/newest/                # Production planning suggestions (1 file)
│   └── *_pending_processor.xlsx            # Builds on ProducingProcessor output
│
# ══════════════════════════════════════════════════════════════════
# HISTORICAL ANALYTICS
# ══════════════════════════════════════════════════════════════════
├── UpdateHistMachineLayout/newest/         # Machine layout change analysis (4 files)
│   ├── *_Machine_change_layout_timeline.png
│   ├── *_Machine_level_change_layout_details.png
│   ├── *_Machine_level_change_layout_pivot.xlsx
│   └── *_Top_machine_change_layout.png
│
├── UpdateHistMoldOverview/newest/          # Mold usage & performance history (11 files)
│   ├── *_Bottom_molds_tonnage.png
│   ├── ... (9 more visualization files)
│   └── *_Top_molds_tonnage.png
│
# ══════════════════════════════════════════════════════════════════
# MULTI-LEVEL PERFORMANCE DASHBOARDS
# ══════════════════════════════════════════════════════════════════
├── DayLevelDataPlotter/newest/             # Daily dashboards (9 files)
├── MonthLevelDataPlotter/newest/           # Monthly dashboards (6 files)
└── YearLevelPlotter/newest/                # Annual dashboards (11 files)
```

> Full shared database details: [Shared Database Details](docs/OptiMoldIQ-sharedDatabase.md).

#### Main Shared Database

**Dynamic DB Collection** (2 files)

- `*_productRecords.parquet` - Historical product records
- `*_purchaseOrders.parquet` - Historical purchase orders

**Static DB Collection** (6 files)

- `*_itemCompositionSummary.parquet` - Item composition details
- `*_itemInfo.parquet` - Product item specifications
- `*_machineInfo.parquet` - Machine specifications
- `*_moldInfo.parquet` - Mold specifications
- `*_moldSpecificationSummary.parquet` - Mold specification summaries
- `*_resinInfo.parquet` - Resin material information

**Metadata File** (1 file)

- `path_annotations.json` - Contains all paths of the main shared database

#### Key Features
- **Timestamped versioning:** All files prefixed with `YYYYMMDD_HHMM_` format (e.g., `20241113_1430_itemInfo.parquet`)
- **Centralized access:** Single source of truth for all agents
- **Multi-level analytics:** Day/month/year aggregations with 50+ visualization outputs
- **Automated tracking:** Pipeline reports, validation checks, and order status monitoring

#### Data Flow Summary

```

    Data Collection → Data Loader → Shared Database (9 files)
                                          ↓
        ┌─────────────────────────────────┼──────────────────────────────────┬───────────────────────────────────────────┐
        |                                 |                                  |                                           |
        ↓                                 ↓                                  ↓                                           ↓
    ValidationOrch            MoldMachineFeatureWeightCalculator     DataChangeAnalyzer                  Multi-Level Performance Analysis
        ↓                     + MoldStabilityIndexCalculator      (Change History Analysis)              ┌──────────────┼───────────────┐
    Validation Report            (Data Insights Generator)         ├─ UpdateHistMachine                  ↓              ↓               ↓
        | (cross-ref                      |                        └─ UpdateHistMold                 DayLevel       MonthLevel      YearLevel
        |  if exists)                     ↓                                  ↓                       Plotter        Plotter         Plotter
        └──> OrderProgress ─────→ ProducingProcessor                  Change Detection                                  ↓
           (reads Shared DB)              ↓                                  ↓                           Multi-Level Performance Dashboards
                   ↓               PendingProcessor                    Change Analysis                   
             Status Reports               ↓                          Change Visualization          
            (with validation      Production Plans                               
             flags)                (Initial Plan)           

```

---

## Folder Structure

```bash
.
├── agents/                # Agent logic (AutoStatusAgent, InitialSchedAgent, etc.)
├── database/              # Static and shared JSON schemas
├── logs/                  # Auto-generated logs for status/errors
├── docs/                  # Documentation (business_problem.md, agent_specifications.md, etc.)
└── README.md              # This file
```

---

## Milestones

### Milestone 01: Core Data Pipeline Agents (Completed July 2025)
> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_01.md)

#### Scope & Objectives
- Establish the foundational data pipeline to:
  - Collect and consolidate monthly dynamic data into the shared database.
  - Enforce multi-layer data integrity validation across static and dynamic sources.
  - Transform machine/shift production logs into PO-level progress and flag inconsistencies.

#### Completed Agents
| Agent                        | Core Responsibilities                                                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **DataPipelineOrchestrator** | Coordinates the end-to-end pipeline for data collecting, cleaning, and loading into shared databases.                  |
| **ValidationOrchestrator**   | Manages validation workflow using key validators (PO-required check, static cross-reference, dynamic logic validation). |
| **OrderProgressTracker**     | Converts raw production logs into PO progress data and highlights mismatches for downstream review.                     |

#### High-Level Workflow
- `Data Collection` → `Data Loading` (via `DataCollector` & `DataLoaderAgent`).
- Validation Layer executes core rule checks through the `validationOrchestrator`.
- Production Progress Reconstruction outputs PO-level timelines and discrepancy flags through the `orderProgressTracker`.
> 👉 [orderProgressTracker Output Overview](docs/agents_output_overviews/orderProgressTracker_output_overviews.md)

#### Two-Tier Healing System
- `Local Healing`: each sub-agent performs autonomous recovery (rollback, retry, schema validation).
- `Global Healing`: orchestrator handles cross-agent failures, multi-stage rollback, or escalates for manual intervention.

### Milestone 02: Initial Production Planning System (Completed August 2025)
> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_02.md)

- Depends on: Milestone 01 (Core Data Pipeline Agents)

#### Scope & Objectives
- Deliver an intelligent workflow-based production planning system that:
  - Orchestrates daily operations through the OptiMoldIQWorkflow.
  - Performs conditional, resource-efficient processing based on detected data changes.
  - Generates historical insights when enough data is accumulated.
  - Produces unified operational and planning reports with auditability.

#### Core System Components
- **OptiMoldIQWorkflow (Main Orchestrator)**
> 👉 [optiMoldIQWorkflow Live Demo](docs/agents_output_overviews/optiMoldIQWorkflow_output_overviews.md)

- Manages the entire daily pipeline with:
  - Smart change detection and phase-based execution.
  - Automatic resource optimization (skip unnecessary phases).
  - Central activity monitoring and reporting.
  - Unified error-handling with safe isolated execution.  

#### Three-Phase Conditional Architecture
| Phase                               | Trigger             | What Runs                                                            | Purpose                                        |
| ----------------------------------- | ------------------- | -------------------------------------------------------------------- | ---------------------------------------------- |
| **1. Data Pipeline**                | Always              | `DataPipelineOrchestrator`                                           | Collect & detect changes in dynamic data.      |
| **2. Shared DB Build & Validation** | When data changes   | `ValidationOrchestrator`, `OrderProgressTracker`                     | Refresh validated shared DB.                   |
| **2.5. Historical Insights**        | When enough records | `MoldStabilityIndexCalculator`, `MoldMachineFeatureWeightCalculator` | Generate stability and machine–mold analytics. |
| **3. Production Planning**          | When PO changes     | `ProducingProcessor`, `PendingProcessor`                             | Optimize schedules & resource allocation.      |

- **Historical Insight Engines (Phase 2.5)**
  - *MoldStabilityIndexCalculator*: cavity stability, cycle consistency, trend detection.
  - *MoldMachineFeatureWeightCalculator*: bootstrap-based feature weights for mold–machine optimization.
 
- **Production Planning Processors (Phase 3)**
  - *ProducingProcessor*: analyzes active production, integrates stability metrics, and generates performance reports.
  - *PendingProcessor*: priority scheduling, load balancing, and assignment optimization using historical insights.

#### Configuration Management
- Centralized workflow settings (WorkflowConfig) controlling:
  - Path management.
  - Efficiency & loss targets.
  - Historical insight thresholds.
  - Load limits and priority orders.
  - Stability/analytics thresholds and confidence parameters.
 
#### Smart Processing & Change Detection
- Conditional triggers ensure:
  - Phase 2 → on dynamic data updates.
  - Phase 2.5 → on historical thresholds.
  - Phase 3 → on purchase order changes.
- *Benefits*: reduced processing time, lower compute cost, scalable performance.

#### Error Handling & Recovery
- The workflow wraps each operation with:
  - Safe isolated execution (_safe_execute).
  - Contextual logging for each agent.
  - Graceful degradation when individual components fail.

#### Reporting System
- Generates multi-level reports for:
  - Data collection
  - Validation
  - Progress tracking
  - Production planning
  - Historical analysis
- With automatic timestamping, archiving, and audit trail support.

#### Impact & Performance Gains
- 60–80% reduction in unnecessary processing via conditional execution.
- High reliability through centralized error handling.
- Improved planning accuracy and visibility across operations.
- Consistent historical insights improve decision-making.

### Milestone 03: Analytics Orchestration + Multi-Level Dashboard Agents (Completed November 2025)
> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_03.md) 🔄 

- Depends on: Milestone 01 (Core Data Pipeline Agents)

#### Scope & Objectives

Build a multi-tier analytics system with two complementary functions:

**1. Standalone Change Detection**:

  - Auto-detect layout & machine–mold relationship changes
  - Generate independent historical change reports

**2. Shared Analytics Service**:

  - Run day/month/year-level analytical processing at scale
  - Serve as a shared analytics layer for multiple consumers
  - Currently powers [Day/Month/Year]LevelDataPlotter
  - Designed to extend to planRefiner and taskOrchestrator

**Deliverables**:

  - 20+ production dashboards with versioned historical archives
  - Centralized static reports for operational visibility
  - Structured analytics outputs for multi-agent consumption

#### Completed Agents
| Agent                       | Service Model | Core Responsibilities                                                                                      |
| --------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------- |
| **DataChangeAnalyzer**      | Standalone    | Detects machine layout changes & first-run machine–mold pairings; generates independent historical reports.  |
| **DayLevelDataProcessor**   | Shared Service | Performs day-level aggregations; **currently serves** dayLevelDataPlotter. |
| **MonthLevelDataProcessor** | Shared Service | Performs month-level aggregations; **currently serves** monthLevelDataPlotter. |
| **YearLevelDataProcessor**  | Shared Service | Performs year-level aggregations; **currently serves** yearLevelDataPlotter. |
| **DayLevelDataPlotter**     | Consumer | Consumes dayLevelDataProcessor outputs to generate day-level production dashboards (PNG, Excel, JSON logs). |
| **MonthLevelDataPlotter**   | Consumer | Consumes monthLevelDataProcessor outputs to generate month-level production dashboards (PNG, Excel, JSON logs). |
| **YearLevelDataPlotter**    | Consumer | Consumes yearLevelDataProcessor outputs to generate year-level production dashboards (PNG, Excel, JSON logs). |

#### High-Level Workflow

**Parallel Independent Tracks**:

1. **Standalone Change Detection** (DataChangeAnalyzer):
   - Detects machine layout changes & first-run machine–mold pairings
   - Generates independent historical reports and change logs
   - Does NOT trigger other analytics processes
   > 👉 [dataChangeAnalyzer Output Overview](docs/agents_output_overviews/dataChangeAnalyzer)

2. **Shared Analytics Pipeline** ([Day/Month/Year]LevelDataProcessor → [Day/Month/Year]LevelDataPlotter):
   - [Day/Month/Year]LevelDataProcessor executes day → month → year processors (conditional on data availability)
   - Produces structured analytics outputs (KPIs, trends, metrics)
   - [Day/Month/Year]LevelDataPlotter consumes these outputs to generate:
     - Production dashboards (PNG format)
     - Excel summaries
     - Timestamped archives with JSON logs
   > 👉 [dashboardBuilder Output Overview](docs/agents_output_overviews/dashboardBuilder)

*Current State*: [Day/Month/Year]LevelDataProcessor serves [Day/Month/Year]LevelDataPlotter only

*Planned*: Will extend to serve planRefiner and taskOrchestrator

#### Performance & Reliability Features
- Parallel Processing Engine: 40–60% faster execution via smart worker allocation.
- Multi-Resolution Analytics: 8 day-level, 3 month-level, 9+ year-level dashboards.
- Versioned Output System: Auto-archived historical PNG/Excel/TXT summaries.
- Error Isolation Layer: Per-module fault isolation with fallback execution paths.

### In Progress: AnalyticsOrchestrator + TaskOrchestrator

---

## Quickstart

Clone the repo and run this Python script to run initial agents on sample data

```python

!git clone https://github.com/ThuyHaLE/OptiMoldIQ.git
%cd ./OptiMoldIQ
%pwd
!pip -q install -r requirements.txt

# sample data
mock_db_dir = 'tests/mock_database'
mock_dynamic_db_dir = 'tests/mock_database/dynamicDatabase'
shared_db_dir = 'tests/shared_db'

#!rm -rf {shared_db_dir} 

from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.initialPlanner.compatibility_based_mold_machine_optimizer import PriorityOrder
from agents.optiMoldMaster.optimold_master import WorkflowConfig, OptiMoldIQWorkflow

def daily_workflow():
    """
    Configure a scheduler to automatically execute the task daily at 8:00 AM.
    """

    # Configuration - these should be moved to a config file or environment variables

    config = WorkflowConfig(
        db_dir = mock_db_dir,
        dynamic_db_dir = mock_dynamic_db_dir,
        shared_db_dir = shared_db_dir,
        efficiency = 0.85,
        loss = 0.03,

        historical_insight_threshold = 30, #15

        # PendingProcessor
        max_load_threshold = 30,
        priority_order = PriorityOrder.PRIORITY_1,
        verbose=True,
        use_sample_data=False,

        # MoldStabilityIndexCalculator
        cavity_stability_threshold = 0.6,
        cycle_stability_threshold = 0.4,
        total_records_threshold = 30,

        # MoldMachineFeatureWeightCalculator
        scaling = 'absolute',
        confidence_weight = 0.3,
        n_bootstrap = 500,
        confidence_level = 0.95,
        min_sample_size = 10,
        feature_weights = None,
        targets = {'shiftNGRate': 'minimize',
                   'shiftCavityRate': 1.0,
                   'shiftCycleTimeRate': 1.0,
                   'shiftCapacityRate': 1.0}
        )

    workflow = OptiMoldIQWorkflow(config)
    return workflow.run_workflow()

if __name__ == "__main__":
    # Example usage
    results = daily_workflow()
    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))
```

--- 

## Contributing
Contributions are welcome! To contribute:
- Fork the repository.
- Create a branch for your feature.
- Submit a pull request for review.

---

## License
This project is licensed under the MIT License. See [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) for details.

---

## Contact
For questions or collaboration, reach out via:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*OptiMoldIQ is under continuous development — documentation and capabilities will expand with each milestone.*
