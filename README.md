🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner
**OptiMoldIQ** is a multi-agent intelligent manufacturing system designed to optimize injection molding operations through automated data pipelines, validation, production planning, analytics, and real-time decision support.
It centralizes operational intelligence by coordinating data, machines, molds, and scheduling under a unified architecture.  

---

Legend: ✅ Complete | 🔄  In Progress | 📝 Planned

---

## Table of Contents
- [Current Phase](#current-phase)
- [Business Problem](#-business-problem)
- [Key Goals](#-key-goals)
- [Planned Solution](#-planned-solution)
- [System Architecture Diagram](#-system-architecture-diagram)
- [Dataset Overview](#-dataset-overview)
- [Databases Overview](#-databases-overview)
- [Folder Structure](#-folder-structure)
- [Roadmap](#-roadmap)
- [Current Status Summary](#-current-status-summary)
- [Interactive System Dashboard](#-interactive-system-dashboard)
- [Milestones](#-milestones)
  - [Milestone 01: Core Data Pipeline Agents (Completed July 2025)](#-milestone-01-core-data-pipeline-agents-completed-july-2025)
  - [Milestone 02: Initial Production Planning System (Completed August 2025)](#-milestone-02-initial-production-planning-system-completed-august-2025)
  - [Milestone 03: Analytics Orchestration & Multi-Level Dashboard Agents (Completed November 2025)](#-milestone-03-analytics-orchestration--multi-level-dashboard-agents-completed-november-2025)
  - [In Progress: AnalyticsOrchestrator & TaskOrchestrator](#-in-progress-analyticsorchestrator--taskorchestrator)
- [Quickstart](#-quickstart)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## Current Phase
OptiMoldIQ is currently finalizing documentation for Milestone 03, covering analytics orchestration, dashboard building, multi-resolution dashboards, and change detection workflows.

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

--- 

## 🔄 Key Goals
<details>
<summary>Data Operations Orchestration</summary>

- Daily Data Ingestion Pipeline: Automated collection and loading of production and operational data. ✅

- Multi-Layer Validation: Static, dynamic, and required-field checks to ensure data integrity. ✅
 
- Real-Time Production Tracking: Monitor production progress and operational KPIs as they happen. ✅

</details>

<details>
<summary>Production Planning Orchestration</summary>
  
*Multi-Stage Mold–Machine Planning*:
  
- Initial planning leveraging historical patterns and compatibility analysis. ✅
  
- Plan refinement using insights from analytics orchestration and operational task orchestration, including resin inventory and mold/machine maintenance. 📝 

</details>
   
<details>
<summary>High-Level Orchestration</summary>
  
*Analytics Orchestration*: 
  
- Auto-detect mold/machine layout changes and generate static reports (dataChangeAnalyzer). ✅
  
- Multi-level analytics with day, month, and year views for operational insights (multiLevelDataAnalytics). ✅

- Multi-level analytics currently serves dashboardBuilder. ✅

- Support Operational Task Orchestration via shared analytics. 📝

- Support Production Planning Orchestration (Plan refinement phase) via shared analytics. 📝

*Reporting Orchestration*: 

- Centralized dashboard generation for actionable insights. ✅

- Visualization across multiple time resolutions (day/month/year) for decision support. ✅

- Upgrade from static report to dynamic UI/UX 📝

*Operational Task Orchestration*:

- Proactive maintenance of molds and machines; resin restocking to prevent downtime and material shortages. 📝

- Quality and yield optimization: 📝

  - Improve cycle times while maintaining product quality.

  - Enhance production yield through actionable insights.

</details>

---

## 🔄 Planned Solution

The OptiMoldIQ System uses a multi-agent architecture to tackle these challenges:

  ```
  agents
  ├─ dataPipelineOrchestrator (child)
  ├─ validationOrchestrator (child)
  ├─ orderProgressTracker (child)
  ├─ optiMoldMaster (mother)
  ├─ autoPlanner (child)
  │   ├─ initialPlanner
  │   └─ planRefiner
  ├─ analyticsOrchestrator (child)
  |   ├─ dataChangeAnalyzer         # Standalone: layout change tracking
  |   └─ multiLevelDataAnalytics    # Shared Service: multi-agent analytics
  |      ├─ dayLevelDataProcessor
  |      ├─ monthLevelDataProcessor
  |      └─ yearLevelDataProcessor
  ├─ dashboardBuilder (child)
  |   ├─ dayLevelDataPlotter
  |   ├─ monthLevelDataPlotter
  |   └─ yearLevelDataPlotter
  └─ taskOrchestrator (child)
      ├─ resourceCoordinator (resin, inventory)
      ├─ assetCoordinator (mold + machine tracking)
      ├─ maintenanceCoordinator (predictive maintenance)
      └─ qualityOptimizer (yield + quality + cycle time)
  ```

### 🔄 1. optiMoldMaster (Mother-Agent) 
The central coordinating agent responsible for manufacturing operations management.
- It automates:
  - Daily data processing pipeline
    - Collection & loading (dataPipelineOrchestrator)
    - Multi-layer validation (validationOrchestrator)
    - Real-time production tracking (orderProgressTracker)
  - Automated production planning
    - Multi-stage mold–machine planning workflow (autoPlanner)
  - Analytics orchestration
    - Consolidates and triggers all analytics modules (analyticsOrchestrator)
  - High-level orchestration
    - Generates multi-resolution dashboards (daily → monthly → yearly) via dashboardBuilder
    - Coordinates dependent operational tasks (taskOrchestrator)

### 🔄 2. Core Components (Child Agents)

<details>
<summary>2.1 dataPipelineOrchestrator ✅</summary>

- Manages a robust 2-phase ETL pipeline:

  - Collect → Load

  - Full error–recovery workflow

  - Automated alerts & self-healing mechanisms

- Ensures stable, reproducible manufacturing data ingestion.
</details>

<details>
<summary>2.2 validationOrchestrator ✅</summary>

- Coordinates and enforces multi-level data validation:

  - Static validation (schema, datatype, integrity)

  - Dynamic validation (anomaly detection, cross-table checks)

  - Required-field validation

  - Version-controlled validation reports

- Maintains consistency across all manufacturing datasets.
</details>

<details>
<summary>2.3 orderProgressTracker ✅</summary>

- Real-time operational visibility:
    
  - Tracks production progress of all manufacturing orders
  
  - Monitors status transitions, cycle completion, and schedule adherence
  
  - Integrates validated data to produce consolidated production analytics
</details>

<details>
<summary>2.4 autoPlanner 🔄</summary>

Advanced production planning tailored for mold manufacturing.
  
- 2.4.1 initialPlanner ✅

  - Multi-stage pipeline for transforming raw data → optimized production plan

  - Integrates production status analysis + advanced optimization algorithms

  - Robust error-handling and plan-quality validation

  - Two-tier optimization for mold–machine assignment based on:

    - Historical machine performance

    - Technical compatibility

    - Load balancing

    - Quality and efficiency constraints

- 2.4.2 planRefiner 📝

  - Performs refinement & adjustment of initialPlanner’s output

  - Adds secondary analysis layers (capacity shifts, conflicts, real-time updates)
</details>

<details>
<summary>2.5 analyticsOrchestrator 🔄</summary>

- Central analytics hub coordinating two distinct analytics functions:

  - **dataChangeAnalyzer**: Standalone monitoring of mold/machine layout changes ✅

  - **multiLevelDataAnalytics**: Shared analytics service providing multi-resolution insights 🔄

- **multiLevelDataAnalytics as Shared Service**:

  - Processes manufacturing data into structured insights (day/month/year)

  - Updates historical analytics records

  - **Currently serves**: dashboardBuilder ✅

  - **Planned to serve**: planRefiner, taskOrchestrator, and other agents 📝

  - Ensures consistent data processing across consuming agents
</details>

<details>
<summary>2.6 dashboardBuilder ✅</summary>
  
- A multi-level analytics + visualization pipeline that produces production intelligence dashboards at:
  
  - Daily

  - Monthly

  - Yearly

- It performs:

  - Data extraction

  - Validation

  - Aggregation

  - Multi-perspective visualization (machine, mold, item, PO)

- Outputs are fully structured and standardized for reporting.
</details>

<details>
<summary>2.7 taskOrchestrator 📝</summary>

- Coordinates cross-dependent operational tasks, including:

- Resin inventory management

- Mold maintenance planning

- Machine maintenance scheduling

- Escalation handling for related operational constraints
</details>

### 🔄 3. Agent Descriptions
> 👉 [Details](docs/OptiMoldIQ-agentsBreakDown.md)

| Agent | Type | Summary |
|-------|------|---------|
| optiMoldMaster | Mother Agent | Central coordinator managing the entire manufacturing operations system |
| dataPipelineOrchestrator | Child Agent | 2-phase ETL pipeline for collecting and loading production data |
| validationOrchestrator | Child Agent | Multi-layer data validation across all datasets |
| orderProgressTracker | Child Agent | Real-time production progress tracking |
| autoPlanner | Child Agent | Advanced production planning system |
| initialPlanner | Sub-component | Generates initial production plan |
| planRefiner | Sub-component | Refines and adjusts initial production plans |
| analyticsOrchestrator | Child Agent | Central hub for analytics and structured insights |
| dataChangeAnalyzer | Sub-component (Standalone) | Tracks mold/machine layout changes and history |
| multiLevelDataAnalytics | Sub-component (Shared Service) | Multi-resolution analytics engine (day/month/year) |
| dashboardBuilder | Child Agent | Generates multi-level dashboards (daily/monthly/yearly) |
| taskOrchestrator | Child Agent | Coordinates operational tasks (resin, molds, machines, quality) |
| resinCoordinator | Sub-component | Manages resin inventory and consumption |
| moldCoordinator | Sub-component | Tracks mold usage, availability, and maintenance |
| machineCoordinator | Sub-component | Monitors machine utilization and readiness |
| maintenanceCoordinator | Sub-component | Predictive maintenance scheduling and tracking |
| productQualityCoordinator | Sub-component | Tracks production yield, NG rates, and defects |
| yieldOptimizer | Sub-component | Optimizes cycle time, yield, and resin usage |

---

<details>
<summary>optiMoldMaster Details</summary>

- Central coordinator managing the entire manufacturing operations system  
- Orchestrates all child agents  
- Ensures seamless workflow across data processing, planning, analytics, and operational tasks

</details>

<details>
<summary>dataPipelineOrchestrator Details</summary>

- **Collect Phase**: Gathers distributed monthly data from multiple sources  
- **Load Phase**: Consolidates and loads into shared database  
- Handles both static (master data) and dynamic (production records) data  
- Implements error-recovery workflow and automated alerts

</details>

<details>
<summary>validationOrchestrator Details</summary>

- **Static Validation**: Schema, datatype, integrity checks  
- **Dynamic Validation**: Anomaly detection, cross-table validation  
- **Required-Field Validation**: Ensures critical fields are populated  
- Maintains version-controlled validation reports for audit trails

</details>

<details>
<summary>orderProgressTracker Details</summary>

- Tracks production progress of all manufacturing orders  
- Monitors status transitions, cycle completion, and schedule adherence  
- Aggregates production data per machine/shift  
- Maps production back to purchase orders and flags discrepancies

</details>

<details>
<summary>autoPlanner Details</summary>

- Advanced production planning system with two-stage optimization:  
  - **initialPlanner**: Generates initial production plan using historical patterns & compatibility analysis  
  - **planRefiner**: Refines initial plan using analytics & operational tasks, including real-time updates

</details>

<details>
<summary>analyticsOrchestrator Details</summary>

*Role*: Central analytics hub coordinating two independent analytics functions

*Sub-components*:

1. **dataChangeAnalyzer** ✅ (Standalone Function)
   - Monitors machine/mold layout changes over time
   - Generates static reports on operational configuration changes
   - Operates independently - does NOT serve other agents
   - Output: Historical change logs and configuration reports

2. **multiLevelDataAnalytics** 🔄 (Shared Analytics Service)
   - Processes manufacturing data into structured insights at multiple resolutions:
     - dayLevelDataProcessor
     - monthLevelDataProcessor  
     - yearLevelDataProcessor
   - Updates historical analytics records
   - **Current consumers**: dashboardBuilder ✅
   - **Planned consumers**: planRefiner 📝, taskOrchestrator 📝
   - **Design purpose**: Shared service layer ensuring consistent analytics across all consuming agents
   - Output: Structured KPIs, trends, and operational metrics

</details>

<details>
<summary>dashboardBuilder Details</summary>

- Multi-level visualization and reporting pipeline:  
  - Generates dashboards at daily, monthly, yearly resolutions  
  - End-to-end processing: data extraction → validation → aggregation → visualization  
  - Multi-perspective views: machine, mold, item, purchase order  
  - Outputs structured and standardized reports for decision support

</details>

<details>
<summary>taskOrchestrator Details</summary>

- Coordinates cross-dependent operational tasks to prevent downtime and optimize production:  
  - Resource availability & scheduling constraints  
  - Feeds critical data to planRefiner for optimization  
  - Implements proactive task management and escalation handling

- **Sub-components**:  
  - **resinCoordinator**: Monitors resin stock, consumption, and forecasts material needs  
  - **moldCoordinator**: Tracks mold lifecycle, usage, maintenance, and availability  
  - **machineCoordinator**: Tracks machine utilization and performance  
  - **maintenanceCoordinator**: Predictive maintenance scheduling  
  - **productQualityCoordinator**: Tracks production yield, NG rates, defects  
  - **yieldOptimizer**: Analyzes cycle time, yield, and resin efficiency; recommends improvements

</details>

---

## 🔄 System Architecture Diagram

The following diagram shows how the data flows from external sources into the system and how various agents interact in the pipeline.

> 👉 [ASCII diagram](docs/OptiMoldIQ-systemDiagram-ASCII.md)

> 👉 [Directory Tree Structure](docs/OptiMoldIQ-directoryTreeStructure.md)

<details> <summary> Or click to expand system architecture diagram (simple version) </summary>

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

## ✅ Dataset Overview
> 👉 [Details](docs/OptiMoldIQ-dataset.md)

This project leverages a 27-month dataset collected from a plastic injection molding production facility. It consists of over **61,000 production records** and **6,200 internal orders**, reflecting the complexity of real-world manufacturing operations.

### Key Entities
- **Items** – 694 plastic products
- **Molds** – 251 unique molds
- **Machines** – 49 molding machines
- **Materials** – 445 materials (resins, masterbatches, additives)
- **Orders** – 6,234 scheduled production orders
- **Production Records** – 61,185 logs of manufacturing outcomes

---

## ✅ Databases Overview
> 👉 [Details](docs/OptiMoldIQ-dbSchema.md)

OptiMoldIQ uses a shared database with both dynamic and static datasets:

### Dynamic Datasets
- `productRecords`: Real-time production log per machine and shift.
- `purchaseOrders`: Orders to be fulfilled, with resin and material requirements.

### Static Datasets
- `itemCompositionSummary`: Material composition for each item.
- `itemInfo`: Metadata about items.
- `machineInfo`: Machine details and layout history.
- `moldInfo`: Mold technical specs and lifecycle data.
- `moldSpecificationSummary`: Mold-to-item mapping and counts.
- `resinInfo`: Resin codes, names, and classification.

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

*This README will be updated regularly as the OptiMoldIQ system evolves through development.*
