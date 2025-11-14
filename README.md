  🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

*An AI-driven orchestration system for end-to-end manufacturing optimization.*

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

## Table of Contents
- [OptiMoldIQ: Intelligent Plastic Molding Planner](#optimoldiq-intelligent-plastic-molding-planner)
  - [Table of Contents](#table-of-contents)
  - [Current Phase](#current-phase)
  - [📝 Business Problem](#-business-problem)
    - [📝 Background](#-background)
    - [📝 Challenges](#-challenges)
    - [📝 Problem Statement](#-problem-statement)
    - [🔄 Problem–Goal Alignment](#-problemgoal-alignment)
  - [🔄 Goals + Planned Solution](#-goals--planned-solution)
    - [1. 🔄   Orchestration Layers Overview](#1----orchestration-layers-overview)
    - [2. 🔄 System Architecture Overview](#2--system-architecture-overview)
    - [3. 🔄 Agent Descriptions](#3--agent-descriptions)
      - [🔄 1. optiMoldMaster (Mother-Agent)](#-1-optimoldmaster-mother-agent)
      - [🔄 2. Core Components (Child Agents)](#-2-core-components-child-agents)
      - [Subcomponents](#subcomponents)
      - [Subcomponents](#subcomponents-1)
    - [3. 🔄 System Connectivity Summary](#3--system-connectivity-summary)
  - [🔄 System Architecture Diagram](#-system-architecture-diagram)
  - [✅ Databases Overview](#-databases-overview)
    - [Raw Database](#raw-database)
      - [Key Entities](#key-entities)
      - [Relationships](#relationships)
      - [Quality Metrics](#quality-metrics)
      - [Limitations](#limitations)
    - [Shared Database (Processed for Multi-Agent System)](#shared-database-processed-for-multi-agent-system)
    - [Main Shared Database](#main-shared-database)
      - [Key Features](#key-features)
      - [Data Flow Summary](#data-flow-summary)
  - [✅ Folder Structure](#-folder-structure)
  - [🔄 Roadmap](#-roadmap)
  - [🔄 Current Status Summary](#-current-status-summary)
  - [🚀 Interactive System Dashboard](#-interactive-system-dashboard)
  - [🔄 Milestones](#-milestones)
    - [✅ Milestone 01: Core Data Pipeline Agents (Completed July 2025)](#-milestone-01-core-data-pipeline-agents-completed-july-2025)
      - [Scope \& Objectives](#scope--objectives)
      - [Completed Agents](#completed-agents)
      - [High-Level Workflow](#high-level-workflow)
      - [Two-Tier Healing System](#two-tier-healing-system)
    - [✅ Milestone 02: Initial Production Planning System (Completed August 2025)](#-milestone-02-initial-production-planning-system-completed-august-2025)
      - [Scope \& Objectives](#scope--objectives-1)
      - [Core System Components](#core-system-components)
      - [Three-Phase Conditional Architecture](#three-phase-conditional-architecture)
      - [Configuration Management](#configuration-management)
      - [Smart Processing \& Change Detection](#smart-processing--change-detection)
      - [Error Handling \& Recovery](#error-handling--recovery)
      - [Reporting System](#reporting-system)
      - [Impact \& Performance Gains](#impact--performance-gains)
    - [🔄 Milestone 03: Analytics Orchestration + Multi-Level Dashboard Agents (Completed November 2025)](#-milestone-03-analytics-orchestration--multi-level-dashboard-agents-completed-november-2025)
      - [Scope \& Objectives](#scope--objectives-2)
      - [Completed Agents](#completed-agents-1)
      - [High-Level Workflow](#high-level-workflow-1)
      - [Performance \& Reliability Features](#performance--reliability-features)
    - [📝 In Progress: AnalyticsOrchestrator + TaskOrchestrator](#-in-progress-analyticsorchestrator--taskorchestrator)
  - [🔄 Quickstart](#-quickstart)
  - [🔄 Contributing](#-contributing)
  - [🔄 License](#-license)
  - [🔄 Contact](#-contact)

---

## Current Phase
OptiMoldIQ is currently finalizing documentation for Milestone 03, covering analytics orchestration, dashboard building, multi-resolution dashboards, and change detection workflows.

---

Legend: ✅ Complete | 🔄  In Progress | 📝 Planned

---

## 📝 Business Problem 
> 👉 [Full context](docs/OptiMoldIQ-business-problem.md)

### 📝 Background
In plastic molding production, achieving optimal efficiency while maintaining high product quality is challenging due to the complexity of interconnected factors like:
- Mold utilization and machine maintenance.
- Resin inventory management.
- Production scheduling and yield optimization.

### 📝 Challenges 
Poor management or lack of integration between components can lead to:
- Increased production downtime.
- Material waste or stock shortages.
- Unbalanced machine and mold utilization.
- Inconsistent product quality or high NG (non-good) rates.
- Reduced production yield and efficiency.

### 📝 Problem Statement
Current systems are:
- Manual or static, lacking real-time insights.
- Prone to inefficiencies in scheduling, resource tracking, and quality management.

### 🔄 Problem–Goal Alignment
OptiMoldIQ directly addresses each business challenge through a set of orchestrated, data-driven systems:

| **Business Challenge**                                           | **Strategic Goal / Orchestration Focus**                                                                                   |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Lack of real-time data and fragmented sources                    | **Data Operations Orchestration** → Automate data ingestion, validation, and real-time production tracking.                |
| Inefficient or manual production planning                        | **Production Planning Orchestration** → Optimize mold–machine assignments and refine plans using analytics insights.       |
| Limited visibility into performance and trends                   | **High-Level Analytics Orchestration** → Enable multi-level reporting and auto-detection of layout or performance changes. |
| Poor coordination between production, maintenance, and materials | **Operational Task Orchestration** → Predictive maintenance, resin restocking, and yield optimization to prevent downtime. |
| Static and isolated reporting systems                            | **Reporting Orchestration** → Centralize dashboards and evolve from static reports to dynamic, interactive visualizations. |

--- 

## 🔄 Goals + Planned Solution

In response to the production challenges outlined above, the **OptiMoldIQ System** was built as a **multi-agent orchestration framework** that transforms fragmented manufacturing operations into a unified, data-driven ecosystem.

--- 

### 1. 🔄   Orchestration Layers Overview

These orchestration layers collectively form the operational backbone of OptiMoldIQ, enabling synchronized workflows from raw data collection to intelligent decision-making.

<details>
<summary>Data Operations Orchestration</summary>

- **Daily Data Ingestion Pipeline**: Automated collection and loading of production and operational data. ✅

- **Multi-Layer Validation**: Static, dynamic, and required-field checks to ensure data integrity. ✅
 
- **Real-Time Production Tracking**: Monitor production progress and operational KPIs as they happen. ✅

</details>

<details>
<summary>Production Planning Orchestration</summary>
  
- **Multi-Stage Mold–Machine Planning**:
  
  - Initial planning leveraging historical patterns and compatibility analysis. ✅
    
  - Plan refinement using insights from analytics orchestration and operational task orchestration, including resin inventory and mold/machine maintenance. 📝 

</details>
   
<details>
<summary>High-Level Orchestration</summary>
  
- **Analytics Orchestration**: 
  
  - Auto-detect mold/machine layout changes and generate static reports (dataChangeAnalyzer). ✅
    
  - Multi-level analytics with day, month, and year views for operational insights (multiLevelDataAnalytics). ✅
  
  - Multi-level analytics currently serves dashboardBuilder. ✅
  
  - Support Operational Task Orchestration via shared analytics. 📝
  
  - Support Production Planning Orchestration (Plan refinement phase) via shared analytics. 📝

- **Reporting Orchestration**: 

  - Centralized dashboard generation for actionable insights. ✅
  
  - Visualization across multiple time resolutions (day/month/year) for decision support. ✅
  
  - Upgrade from static report to dynamic UI/UX 📝

- **Operational Task Orchestration**:

  - Proactive maintenance of molds and machines; resin restocking to prevent downtime and material shortages. 📝
  
  - Quality and yield optimization: 📝
  
    - Improve cycle times while maintaining product quality.
  
    - Enhance production yield through actionable insights.

</details>

---

### 2. 🔄 System Architecture Overview

OptiMoldIQ uses a **multi-agent architecture** to operationalize these orchestration layers:

  ```
optiMoldMaster (Mother Agent)
├─ Data Operations
│  ├─ dataPipelineOrchestrator ✅     # ETL: collect & load data
│  ├─ validationOrchestrator ✅       # Multi-layer data validation
│  └─ orderProgressTracker ✅         # Real-time production tracking
│
├─ Production Planning
│  └─ autoPlanner 🔄
│     ├─ initialPlanner ✅            # Generate optimal plans
│     └─ planRefiner 📝               # Refine with real-time data
│
├─ Analytics & Reporting
│  ├─ analyticsOrchestrator 🔄
│  │  ├─ dataChangeAnalyzer ✅        # Track layout changes
│  │  └─ multiLevelDataAnalytics 🔄   # Day/month/year analytics
│  └─ dashboardBuilder ✅             # Multi-level visualizations
│
└─ Operational Tasks
   └─ taskOrchestrator 📝
      ├─ resourceCoordinator          # Resin inventory
      ├─ assetCoordinator             # Mold/machine tracking
      ├─ maintenanceCoordinator       # Predictive maintenance
      └─ qualityOptimizer             # Yield & quality optimization

  ```

Execution Flow: 
```
RAW DATA → DATA OPERATIONS → PLANNING → ANALYTICS → DASHBOARDS
                    ↓             ↓          ↓
                VALIDATION → TRACKING → OPTIMIZATION
```

> *Note:*  `optiMoldMaster` functions as the **mother-agent**, orchestrating all child agents below. Each child agent operates autonomously but synchronizes through shared data and event channels.

### 3. 🔄 Agent Descriptions
> 👉 [Details](docs/OptiMoldIQ-agentsBreakDown.md)

| Agent | Type | Summary | Status |
|-------|------|----------|--------|
| optiMoldMaster | Mother Agent | Central coordinator managing all manufacturing operations | ✅ |
| dataPipelineOrchestrator | Child Agent | 2-phase ETL pipeline for data collection and loading | ✅ |
| validationOrchestrator | Child Agent | Multi-layer data validation | ✅ |
| orderProgressTracker | Child Agent | Real-time production tracking | ✅ |
| autoPlanner | Child Agent | Advanced production planning engine | 🔄 |
| initialPlanner | Sub-component | Generates initial production plan | ✅ |
| planRefiner | Sub-component | Refines and adjusts initial production plans | 📝 |
| analyticsOrchestrator | Child Agent | Central analytics hub for structured insights | 🔄 |
| dataChangeAnalyzer | Sub-component | Tracks mold/machine layout changes | ✅ |
| multiLevelDataAnalytics | Sub-component | Multi-resolution analytics engine | 🔄 |
| dashboardBuilder | Child Agent | Generates multi-level dashboards | ✅ |
| taskOrchestrator | Child Agent | Coordinates operational tasks | 📝 |
| resinCoordinator | Sub-component | Manages resin inventory and consumption | 📝 |
| moldCoordinator | Sub-component | Tracks mold usage and maintenance | 📝 |
| machineCoordinator | Sub-component | Monitors machine utilization | 📝 |
| maintenanceCoordinator | Sub-component | Predictive maintenance scheduling | 📝 |
| productQualityCoordinator | Sub-component | Tracks yield and defects | 📝 |
| yieldOptimizer | Sub-component | Optimizes cycle time and yield | 📝 |

#### 🔄 1. optiMoldMaster (Mother-Agent)

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

#### 🔄 2. Core Components (Child Agents)

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
<summary>2.4 autoPlanner 🔄</summary>

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
<summary>2.5 analyticsOrchestrator 🔄</summary>

**Role:**  
Central analytics hub coordinating two independent yet complementary analytics functions.

#### Subcomponents

1. **dataChangeAnalyzer ✅ (Standalone Function)**
   - Monitors **machine and mold layout changes** over time.  
   - Generates **static reports** capturing configuration deltas.  
   - Operates independently — does **not** directly serve other agents.  
   - **Output:** Historical change logs and configuration reports.

2. **multiLevelDataAnalytics 🔄 (Shared Analytics Service)**
   - Processes validated manufacturing data into structured insights at multiple resolutions:  
     - `dayLevelDataProcessor`  
     - `monthLevelDataProcessor`  
     - `yearLevelDataProcessor`  
   - Updates **historical analytics records** with derived KPIs and trend metrics.  
   - **Current consumers:** `dashboardBuilder` ✅  
   - **Planned consumers:** `planRefiner`, `taskOrchestrator` 📝  
   - **Purpose:** Acts as a **shared service layer** ensuring consistent analytics results across all consuming agents.

**Output:**  
Structured KPIs, operational trends, and cross-period performance insights.
</details>

<details>
<summary>2.6 dashboardBuilder ✅</summary>

**Role:**  
Centralized visualization engine producing structured, standardized reports.

**Functions**
- Generates dashboards at **daily**, **monthly**, and **yearly** resolutions.  
- End-to-end workflow:  
  - Data extraction → Validation → Aggregation → Visualization  
- Provides **multi-perspective views**: by machine, mold, item, or purchase order.  
- Feeds from `multiLevelDataAnalytics` to ensure consistency.  
- Outputs **static or dynamic dashboards** for operational decision-making.

**Purpose:**  
Transforms analytics outputs into actionable visual insights for managers and engineers.
</details>

<details>
<summary>2.7 taskOrchestrator 📝</summary>

**Role:**  
Coordinates cross-dependent operational activities to prevent downtime and optimize production efficiency.

**Functions**
- Manages resource availability and production constraints.  
- Feeds critical operational data to `planRefiner` for real-time plan optimization.  
- Implements **proactive task management**, **maintenance scheduling**, and **escalation handling**.

#### Subcomponents
- **resinCoordinator:** Tracks resin stock, consumption, and forecasts material needs.  
- **moldCoordinator:** Manages mold lifecycle, usage, and availability.  
- **machineCoordinator:** Monitors machine utilization and performance.  
- **maintenanceCoordinator:** Handles predictive maintenance and scheduling.  
- **productQualityCoordinator:** Monitors yield, NG rates, and defect analysis.  
- **yieldOptimizer:** Evaluates cycle times and resin efficiency; recommends performance improvements.

**Purpose:**  
Maintains stable, optimized operations across all production assets.
</details>

### 3. 🔄 System Connectivity Summary
- **Data Layer** → powers → `Planning`, `Analytics`, and `Task` orchestration layers.  
- **Planning Layer** ↔ **Task Layer** → continuously refine and optimize schedules.  
- **Analytics Layer** → feeds both `Reporting` and `Planning` systems.  
- **Reporting Layer** → provides insights to human decision-makers.  

Together, these layers form a **closed feedback loop** where data → planning → execution → analytics → continuous improvement.

---

## 🔄 System Architecture Diagram

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

## ✅ Databases Overview
OptiMoldIQ leverages a **27-month production dataset** from a plastic injection molding facility, containing over **61,000 production records** and **6,200 orders**. This dataset underpins the system's planning, validation, and analytics workflows. 

In OptiMoldIQ, the raw database is loaded, collected and processed into a shared database in multi-agents system.

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

### Main Shared Database

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

- `path_annotations.json` - Contains all paths of main shared database

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

## ✅ Folder Structure

```bash
.
├── agents/                # Agent logic (AutoStatusAgent, InitialSchedAgent, etc.)
├── database/              # Static and shared JSON schemas
├── logs/                  # Auto-generated logs for status/errors
├── docs/                  # Documentation (business_problem.md, agent_specifications.md, etc.)
└── README.md              # This file
```

---

## 🔄 Roadmap

| Phase / Key Goal                         | Task                                                     | Status         | Responsible Agent                                                                     |
| ---------------------------------------- | -------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------- |
| **1. Data Operations Orchestration**     | Daily Data Ingestion Pipeline                            | ✅ Done         | dataPipelineOrchestrator                                                              |
|                                          | Multi-Layer Validation                                   | ✅ Done         | validationOrchestrator                                                                |
|                                          | Real-Time Production Tracking                            | ✅ Done         | orderProgressTracker                                                                  |
| **2. Production Planning Orchestration** | Initial Multi-Stage Mold–Machine Planning                | ✅ Done         | autoPlanner → initialPlanner                                                          |
|                                          | Plan Refinement & Real-Time Adjustments                  | 📝 In Progress | analyticsOrchestrator + taskOrchestrator + autoPlanner → planRefiner                  |
| **3. High-Level Orchestration**          | Auto-Detect Mold/Machine Layout Changes & Static Reports | ✅ Done         | analyticsOrchestrator → dataChangeAnalyzer                                            |
|                                          | Multi-Level Analytics (Day/Month/Year Views)             | ✅ Done         | analyticsOrchestrator → multiLevelDataAnalytics                                       |
|                                          | Centralized Dashboard Generation                         | ✅ Done         | dashboardBuilder                                                                      |
|                                          | Multi-Resolution Visualization (Day/Month/Year)          | 📝 Upgrading   | dashboardBuilder (offline static ✅ → dynamic UI/UX 📝)                                |
|                                          | Proactive Maintenance & Resin Restocking                 | 📝 In Progress | analyticsOrchestrator + taskOrchestrator → maintenanceCoordinator / resinCoordinator  |
|                                          | Quality & Yield Optimization                             | 📝 In Progress | analyticsOrchestrator + taskOrchestrator → yieldOptimizer / productQualityCoordinator |

---

## 🔄 Current Status Summary

| Component                             | Status & Notes                                                                               |
| ------------------------------------- | -------------------------------------------------------------------------------------------- |
| Static Databases (mold/machine/resin) | ✅ Defined                                                                                    |
| Dynamic Data Pipeline                 | ✅ Implemented                                                                                |
| Shared Database                       | ✅ First version generated                                                                    |
| Validation System                     | ✅ Functional                                                                                 |
| Production Tracker                    | ✅ Mapping by PO & shift                                                                      |
| AnalyticsOrchestrator                 | 📝 In Progress (DataChangeAnalyzer ✅, Multi-LevelAnalytics ✅, other modules ongoing 📝)    |
| DashBoardBuilder                      | 📝 Upgrading (offline static ✅ → dynamic interactive UI/UX 📝)                              |
| AutoPlanner                           | 📝 In Progress (initialPlanner ✅, planRefiner 📝)                                           |
| TaskOrchestrator                      | 📝 In Progress (maintenance, resin, quality/yield tasks ongoing 📝)                          |

---

## 🚀 Interactive System Dashboard

Experience OptiMoldIQ's architecture through our interactive dashboard:

> 👉 [Live Dashboard](https://thuyhale.github.io/OptiMoldIQ/)

---

## 🔄 Milestones

### ✅ Milestone 01: Core Data Pipeline Agents (Completed July 2025)
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

### ✅ Milestone 02: Initial Production Planning System (Completed August 2025)
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
  - *ProducingProcessor*: analyzes active production, integrates stability metrics, generates performance reports.
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
- Consistent historical insights improving decision-making.

### 🔄 Milestone 03: Analytics Orchestration + Multi-Level Dashboard Agents (Completed November 2025)
> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_03.md) 🔄 

- Depends on: Milestone 01 (Core Data Pipeline Agents)

#### Scope & Objectives

Build a multi-tier analytics system with two complementary functions:

**1. Standalone Change Detection**:

  - Auto-detect layout & machine–mold relationship changes
  - Generate independent historical change reports

**2. Shared Analytics Service**:

  - Run day/month/year-level analytical processing at scale
  - Serve as shared analytics layer for multiple consumers
  - Currently powers dashboardBuilder ✅
  - Designed to extend to planRefiner and taskOrchestrator 📝

**Deliverables**:

  - 20+ production dashboards with versioned historical archives
  - Centralized static reports for operational visibility
  - Structured analytics outputs for multi-agent consumption

#### Completed Agents
| Agent                       | Service Model | Core Responsibilities                                                                                      |
| --------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------- |
| **AnalyticsOrchestrator**   | Coordinator | Coordinates two independent analytics functions: standalone change detection and shared analytics service. |
| └─**DataChangeAnalyzer**      | Standalone | Detects machine layout changes & first-run machine–mold pairings; generates independent historical reports.  |
| └─**MultiLevelDataAnalytics** | Shared Service | Performs day/month/year-level aggregations; **currently serves** dashboardBuilder. |
| **DashboardBuilder**        | Consumer | Consumes multiLevelDataAnalytics outputs to generate production dashboards (PNG, Excel, JSON logs). |

#### High-Level Workflow

**Parallel Independent Tracks**:

1. **Standalone Change Detection** (DataChangeAnalyzer):
   - Detects machine layout changes & first-run machine–mold pairings
   - Generates independent historical reports and change logs
   - Does NOT trigger other analytics processes
   > 👉 [dataChangeAnalyzer Output Overview](docs/agents_output_overviews/dataChangeAnalyzer)

2. **Shared Analytics Pipeline** (MultiLevelDataAnalytics → DashboardBuilder):
   - `MultiLevelDataAnalytics` executes day → month → year processors (conditional on data availability)
   - Produces structured analytics outputs (KPIs, trends, metrics)
   - `DashboardBuilder` consumes these outputs to generate:
     - Production dashboards (PNG format)
     - Excel summaries
     - Timestamped archives with JSON logs
   > 👉 [dashboardBuilder Output Overview](docs/agents_output_overviews/dashboardBuilder)

*Current State*: MultiLevelDataAnalytics serves dashboardBuilder only ✅  

*Planned*: Will extend to serve planRefiner and taskOrchestrator 📝

#### Performance & Reliability Features
- Parallel Processing Engine: 40–60% faster execution via smart worker allocation.
- Multi-Resolution Analytics: 8 day-level, 3 month-level, 9+ year-level dashboards.
- Versioned Output System: Auto-archived historical PNG/Excel/TXT summaries.
- Error Isolation Layer: Per-module fault isolation with fallback execution paths.

### 📝 In Progress: AnalyticsOrchestrator + TaskOrchestrator

---

## 🔄 Quickstart

Clone repo and run this python script to run initial agents on sample data

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

## 🔄 Contributing
Contributions are welcome! To contribute:
- Fork the repository.
- Create a branch for your feature.
- Submit a pull request for review.

---

## 🔄 License
This project is licensed under the MIT License. See [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) for details.

---

## 🔄 Contact
For questions or collaboration, reach out via:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*OptiMoldIQ is under continuous development — documentation and capabilities will expand with each milestone.*
