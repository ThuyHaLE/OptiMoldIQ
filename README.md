  🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

*AI-driven orchestration system for end-to-end manufacturing optimization.*

---

## Table of Contents
- [OptiMoldIQ: Intelligent Plastic Molding Planner](#optimoldiq-intelligent-plastic-molding-planner)
  - [Table of Contents](#table-of-contents)
  - [Project Status](#project-status)
  - [Overview](#overview)
  - [📝 Business Problem](#-business-problem)
    - [Background](#background)
    - [Challenges](#challenges)
    - [Problem Statement](#problem-statement)
  - [🔄 Problem–Driven Solution Overview](#-problemdriven-solution-overview)
    - [Strategic Alignment](#strategic-alignment)
    - [Goals and Planned Solution](#goals-and-planned-solution)
      - [Data Operations Orchestration](#data-operations-orchestration)
      - [Production Planning Orchestration](#production-planning-orchestration)
      - [High-Level Orchestrations](#high-level-orchestrations)
  - [System Architecture Overview](#system-architecture-overview)
  - [Agent Descriptions](#agent-descriptions)
    - [OptiMoldMaster (Mother Agent) ✅](#optimoldmaster-mother-agent-)
    - [Core Components (Child Agents) 🔄](#core-components-child-agents-)
      - [2.1 dataPipelineOrchestrator ✅](#21-datapipelineorchestrator-)
      - [2.2 validationOrchestrator ✅](#22-validationorchestrator-)
      - [2.3 orderProgressTracker ✅](#23-orderprogresstracker-)
      - [2.4 autoPlanner 📝](#24-autoplanner-)
      - [2.5 analyticsOrchestrator 📝](#25-analyticsorchestrator-)
      - [2.6 dashboardBuilder 📝](#26-dashboardbuilder-)
      - [2.7 taskOrchestrator 📝](#27-taskorchestrator-)
    - [System Connectivity Summary](#system-connectivity-summary)
    - [Execution Flow](#execution-flow)
  - [System Architecture Diagram](#system-architecture-diagram)
  - [Databases Overview](#databases-overview)
    - [Raw Database](#raw-database)
      - [Key Entities](#key-entities)
      - [Relationships](#relationships)
      - [Quality Metrics](#quality-metrics)
      - [Limitations](#limitations)
    - [Shared Database (Processed for Multi-Agent System)](#shared-database-processed-for-multi-agent-system)
      - [Main Shared Database](#main-shared-database)
      - [Key Features](#key-features)
      - [Data Flow Summary](#data-flow-summary)
  - [Folder Structure](#folder-structure)
  - [Milestones](#milestones)
    - [Milestone 01: Core Data Pipeline Agents (Completed July 2025)](#milestone-01-core-data-pipeline-agents-completed-july-2025)
      - [Scope \& Objectives](#scope--objectives)
      - [Completed Agents](#completed-agents)
      - [High-Level Workflow](#high-level-workflow)
      - [Two-Tier Healing System](#two-tier-healing-system)
    - [Milestone 02: Initial Production Planning System (Completed August 2025)](#milestone-02-initial-production-planning-system-completed-august-2025)
      - [Scope \& Objectives](#scope--objectives-1)
      - [Core System Components](#core-system-components)
      - [Three-Phase Conditional Architecture](#three-phase-conditional-architecture)
      - [Configuration Management](#configuration-management)
      - [Smart Processing \& Change Detection](#smart-processing--change-detection)
      - [Error Handling \& Recovery](#error-handling--recovery)
      - [Reporting System](#reporting-system)
      - [Impact \& Performance Gains](#impact--performance-gains)
    - [Milestone 03: Enhanced Production Planning with Analytics and Dashboard System (Completed November 2025)](#milestone-03-enhanced-production-planning-with-analytics-and-dashboard-system-completed-november-2025)
      - [Overview](#overview-1)
      - [System Evolution](#system-evolution)
      - [What's Preserved from M02](#whats-preserved-from-m02)
      - [What's Added in M03](#whats-added-in-m03)
        - [A. analyticsOrchestrator (Backend Service)](#a-analyticsorchestrator-backend-service)
        - [B. dashboardBuilder (Visualization Layer)](#b-dashboardbuilder-visualization-layer)
        - [Service-Consumer Architecture](#service-consumer-architecture)
      - [Enhanced Workflow Architecture](#enhanced-workflow-architecture)
    - [Milestone 04: Enhanced Production Planning with Analytics and Task Orchestrator System (In Progress)](#milestone-04-enhanced-production-planning-with-analytics-and-task-orchestrator-system-in-progress)
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

1. **Data Insight Analytics**: 

- **Analytics Orchestrator** (**analyticsOrchestrator**) 📝: Central analytics facade providing unified interface for coordinating multiple complementary analytics functions. It orchestrates comprehensive data insights for decision-making and downstream system components. **Operates in two modes: (1) Standalone analytics execution with direct output persistence, (2) Shared backend service for visualization layers.**

  **Functional Groups:**
  - **Historical Analytics** (**hardwareChangeAnalyzer**) ✅: Coordinates and executes historical change analyses for both machines and molds through two modules:
    - *MachineLayoutTracker*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
    - *MachineMoldPairTracker*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
  
  - **Multi-Level Analytics** (**multiLevelPerformanceAnalyzer**) ✅: Orchestrates and executes comprehensive data processing pipeline across multiple time granularities through three hierarchical modules:
    - *DayLevelDataProcessor*: Processes daily production data with mold-based and item-based aggregations, generating real-time operational metrics and summary statistics
    - *MonthLevelDataProcessor*: Analyzes monthly production patterns, distinguishing finished and unfinished orders to track completion rates and identify trends
    - *YearLevelDataProcessor*: Performs annual production analysis, providing long-term insights into finished/unfinished orders and yearly performance summaries

  **Optional Groups:** (planning...)
  - **Advanced Analytics** (**crossLevelPerformanceAnalyzer**) 📝: Provides advanced data analytics capabilities supporting operational task orchestration and production planning refinement with cross-functional insights for decision-making optimization

2. **Visualization & Report Generating Layer**:

- **Dashboard Builder** (**dashboardBuilder**) 📝: Unified visualization facade providing both static reporting and interactive dashboard capabilities. It transforms analytics outputs into actionable visual insights **by orchestrating Analytics Orchestrator as a shared backend service (Mode 2)**.
  
  **Functional Groups:**
  - **Static Report Generator** (**multiLevelPerformancePlotter**) ✅: Generates static dashboards, plots, and reports (PNG, TXT, XLSX) through three hierarchical modules:
    - *DayLevelDataPlotter*: Generates daily operational dashboards with real-time metrics visualization, production summaries, and mold performance reports
    - *MonthLevelDataPlotter*: Creates monthly trend dashboards tracking completion rates, production patterns, and month-to-date performance analysis
    - *YearLevelDataPlotter*: Produces annual strategic dashboards with long-term trends, yearly summaries, and performance comparisons
  
  - **Hardware Change Visualization** (**hardwareChangePlotter**) ✅: Visualizes hardware change detection and history tracking through two modules:
    - *MachineLayoutPlotter*: Generates machine layout evolution visualizations and change reports
    - *MachineMoldPairPlotter*: Creates mold-machine relationship visualizations and utilization reports

  **Optional Groups:** (planning...)
  - **Interactive Dashboard Platform** (**dynamicDashboardUI**) 📝: Web-based interactive dashboard with real-time data updates, advanced filtering, drill-down capabilities, and responsive visualizations

3. **Operational Task Coordinating Layer**: (planing...)

- Task Orchestrator (**taskOrchestrator**) 📝: The central coordination layer responsible for distributing, monitoring, and optimizing workflows across all operational coordinators:
  - Resin Coordinator (**resinCoordinator**) 📝: Manages resin inventory, tracks consumption levels, forecasts material demand, and optimizes raw material supply.
  - Maintenance Coordinator (**maintenanceCoordinator**) 📝: Oversees predictive maintenance for both molds and machines, automatically scheduling tasks to reduce downtime and extend equipment lifespan through 2 modules:
    - *MoldTracker* 📝: Tracks mold status, lifecycle, production and maintenance history.
    - *MachineTracker* 📝: Monitors machine conditions, performance metrics, activity schedules and maintenance history.
  - Product Quality Coordinator (**productQualityCoordinator**) 📝: Optimizes product quality through defect data analysis, operational parameter adjustments, and real-time quality monitoring.
  - Yield Optimizer (**yieldOptimizer**) 📝: Enhances production yield using performance analytics, scrap reduction strategies, and intelligent load balancing across resources.

--- 

## System Architecture Overview

OptiMoldIQ uses a **multi-agent architecture** to operationalize these orchestration layers:
```
optiMoldMaster (Mother Agent)
│
├─ Data Operations Layer
│  ├─ dataPipelineOrchestrator ✅        # ETL: collect & load data
│  ├─ validationOrchestrator ✅          # Multi-layer data validation
│  └─ orderProgressTracker ✅            # Real-time production tracking
│
├─ Production Planning Layer
│  └─ autoPlanner 📝
│     ├─ initialPlanner ✅               # Generate optimal plans
│     └─ planRefiner 📝                  # Refine with real-time data
│
├─ Insight Analytics Layer
│  └─ analyticsOrchestrator 📝                    # Dual-mode: Standalone or backend service
│     ├─ hardwareChangeAnalyzer ✅                # Machine & mold change tracking
│     ├─ multiLevelPerformanceAnalyzer ✅         # Day/Month/Year performance analytics
│     └─ crossLevelPerformanceAnalyzer 📝         # Advanced cross-functional analytics
│
├─ Visualization & Report Generating Layer
│  └─ dashboardBuilder 📝                         # Consumes Analytics Orchestrator
│     ├─ multiLevelPerformancePlotter ✅         # Day/Month/Year static visualizations
│     ├─ hardwareChangePlotter ✅                # Hardware change visualizations
│     └─ dynamicDashboardUI 📝                   # Interactive web dashboards
│
└─ Operational Task Coordinating Layer            # Consumes Analytics Orchestrator
    └─ taskOrchestrator 📝
       ├─ resinCoordinator 📝            # Resin inventory management
       ├─ maintenanceCoordinator 📝      # Predictive mold-machine maintenance
       ├─ productQualityCoordinator 📝   # Quality optimization
       └─ yieldOptimizer 📝              # Yield optimization
```

> **Note:** `optiMoldMaster` functions as the **mother-agent**, orchestrating all child agents. Each child agent operates autonomously but synchronizes through shared data and event channels.
> ---
> 
> **Analytics Orchestrator - Dual Architecture Modes:**
> 
> - **Standalone Mode**: 
>   ```
>   analyticsOrchestrator.run_analytics() → Direct outputs (TXT, JSON, XLSX)
>   ```
> 
> - **Integrated Mode** (Config Injection Pipeline):
>   ```
>   Consumer Agent → [Component]Config → Auto-Config 
>   → AnalyticsOrchestrator.run_analytics() → Analytics Results 
>   → Consumer Processing → Outputs
>   ```
> ---
> 
> **Config-Driven Orchestration Pattern:**
> 
> Consumer agents embed `AnalyticsOrchestratorConfig` to trigger specific analyzers, then consume results:
> 
> - **dashboardBuilder**:
>   - `multiLevelPerformancePlotter` → `multiLevelPerformanceAnalyzer` → day/month/year visualizations
>   - `hardwareChangePlotter` → `hardwareChangeAnalyzer` → machineLayout/machineMoldPair visualizations
> 
> - **taskOrchestrator** (planning):
>   - `resinCoordinator` → relevant analyzers → inventory actions
>   - `maintenanceCoordinator` → relevant analyzers → maintenance scheduling
>   - *[similar pattern for other coordinators]*

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
| analyticsOrchestrator | Child Agent | Central analytics facade (dual-mode: standalone/backend service) | 📝 |
| hardwareChangeAnalyzer | Sub-component | Tracks machine/mold layout and pairing changes | ✅ |
| multiLevelPerformanceAnalyzer | Sub-component | Day/Month/Year hierarchical performance analytics | ✅ |
| crossLevelPerformanceAnalyzer | Sub-component | Advanced cross-functional analytics service | 📝 |
| dashboardBuilder | Child Agent | Visualization facade consuming Analytics Orchestrator | 📝 |
| multiLevelPerformancePlotter | Sub-component | Day/Month/Year static reports & visualizations | ✅ |
| hardwareChangePlotter | Sub-component | Machine/mold change visualizations | ✅ |
| dynamicDashboardUI | Sub-component | Interactive web-based dashboards | 📝 |
| taskOrchestrator | Child Agent | Coordinates operational tasks | 📝 |
| resinCoordinator | Sub-component | Manages resin inventory and consumption | 📝 |
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
- Centralized analytics and reporting via `analyticsOrchestrator` + `dashboardBuilder`
- Task-level optimization and coordination via `analyticsOrchestrator` + `taskOrchestrator`

---

### Core Components (Child Agents) 🔄

#### 2.1 dataPipelineOrchestrator ✅

**Role:**  
Manages the **two-phase ETL pipeline** for both static and dynamic manufacturing data.

**Functions**
- **Collect Phase:** Gathers distributed monthly data from multiple sources.  
- **Load Phase:** Consolidates and loads into the shared manufacturing database.  
- Supports both **static (master data)** and **dynamic (production records)**.  
- Includes **error-recovery workflows** and **automated alerting** mechanisms.

**Purpose:**  
Ensures stable, reproducible, and traceable manufacturing data ingestion.

#### 2.2 validationOrchestrator ✅

**Role:**  
Enforces multi-layer validation across all incoming manufacturing data streams.

**Validation Layers**
- **Static Validation:** Schema, datatype, integrity checks.  
- **Dynamic Validation:** Anomaly detection, cross-table consistency validation.  
- **Required-Field Validation:** Ensures critical data completeness.  
- Maintains **version-controlled validation reports** for traceability and audits.

**Purpose:**  
Guarantees high data integrity and reliability across all downstream processes.

#### 2.3 orderProgressTracker ✅

**Role:**  
Provides **real-time operational visibility** across production orders.

**Functions**
- Tracks production progress and order lifecycle.  
- Monitors **status transitions**, **cycle completion**, and **schedule adherence**.  
- Aggregates per-machine and per-shift data.  
- Maps production records back to purchase orders and flags discrepancies.

**Output:**  
Consolidated production analytics and performance indicators.

#### 2.4 autoPlanner 📝

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

#### 2.5 analyticsOrchestrator 📝

**Role:**  
Central analytics facade orchestrating multiple complementary analytics functions through a dual-mode architecture: (1) standalone analytics execution with direct output persistence, (2) shared backend service for visualization and operational layers. Provides comprehensive, multi-faceted data insights supporting dashboard generation, task coordination, and production planning refinement.

**Subcomponents**

1. **hardwareChangeAnalyzer ✅**
- Coordinates and executes **historical change analyses** for both machines and molds over time.  
- Generates **change tracking reports** capturing configuration evolution and operational patterns.  
- Operates in dual modes: standalone analytics or backend service for `hardwareChangePlotter`.
- **Modules:**
  - *MachineLayoutTracker*: Analyzes machine layout evolution over time to identify layout changes and activity patterns
  - *MachineMoldPairTracker*: Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends
- **Output:** Historical change logs, configuration reports (TXT, JSON, XLSX).
- **Service-Consumer Relationship:**
  - `machineLayoutTracker` → `machineLayoutPlotter` ✅
  - `machineMoldPairTracker` → `machineMoldPairPlotter` ✅

2. **multiLevelPerformanceAnalyzer ✅**
- Orchestrates and executes **comprehensive data processing pipeline** across multiple time granularities (day/month/year).
- Generates **structured analytics outputs** for consumption by dashboard builders and downstream agents (planRefiner, taskOrchestrator).
- Operates in dual modes: standalone analytics or backend service for `multiLevelPerformancePlotter`.
- **Modules:**
  - *DayLevelDataProcessor*: Processes daily production data with mold-based and item-based aggregations, generating real-time operational metrics and summary statistics
  - *MonthLevelDataProcessor*: Analyzes monthly production patterns, distinguishing finished and unfinished orders to track completion rates and identify trends
  - *YearLevelDataProcessor*: Performs annual production analysis, providing long-term insights into finished/unfinished orders and yearly performance summaries
- **Output:** Multi-level processed DataFrames with aggregated records and statistical summaries (TXT, JSON, XLSX).
- **Service-Consumer Relationship:**
  - `dayLevelDataProcessor` → `dayLevelDataPlotter` ✅
  - `monthLevelDataProcessor` → `monthLevelDataPlotter` ✅
  - `yearLevelDataProcessor` → `yearLevelDataPlotter` ✅
  - Future consumers: `planRefiner`, `taskOrchestrator`, `dynamicDashboardUI` 📝

3. **crossLevelPerformanceAnalyzer 📝 (Advanced Analytics)**
- Provides **advanced data analytics capabilities** for operational decision-making and strategic planning. 📝
- Generates **cross-functional insights** for decision-making optimization across operations and planning. 📝 
- Operates as an **advanced service layer** — delivers predictive analytics and actionable insights to downstream orchestrators. 📝

**Architecture Modes:**
- **Standalone**: `analyticsOrchestrator.run_analytics()` → Direct analytics outputs (TXT, JSON, XLSX)
- **Integrated**: Consumer agents orchestrate via config injection pipeline:
```
  [Component]Config → Auto-Config → AnalyticsOrchestrator.run_analytics() 
  → Analytics Results → Consumer Processing → Outputs
```

---

#### 2.6 dashboardBuilder 📝

**Role:**
Unified visualization facade providing dual-mode dashboard capabilities through config-driven orchestration: (1) static report generation for scheduled distribution and archival, (2) interactive web platform for real-time data exploration. Orchestrates `analyticsOrchestrator` as a shared backend service via config injection.

**Subcomponents**

1. **multiLevelPerformancePlotter ✅ (Static Report Generator)**
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
  - *DayLevelDataPlotter*: Generates daily operational dashboards with real-time metrics visualization, production summaries, and mold performance reports
  - *MonthLevelDataPlotter*: Creates monthly trend dashboards tracking completion rates, production patterns, and month-to-date performance analysis
  - *YearLevelDataPlotter*: Produces annual strategic dashboards with long-term trends, yearly summaries, and performance comparisons

**Output:** 
  - Static PNG images for visual dashboards
  - TXT reports for quick summaries
  - XLSX spreadsheets for detailed data tables
  - Saved to configured directories for email distribution and archival

**Orchestration Flow:**
```
  PerformancePlotflowConfig → Auto-Config → AnalyticsOrchestrator.multiLevelPerformanceAnalyzer
  → [day/month/year]LevelDataProcessor → Analytics Results 
  → [day/month/year]LevelDataPlotter → Visualizations (PNG/TXT/XLSX)
```

2. **hardwareChangePlotter ✅ (Hardware Change Visualization)**
- Coordinates **hardware change visualizations** for machine layouts and machine-mold pairs.
- Manages **execution flow** with flexible configuration, auto-configuration, and error isolation.
- Operates as a **batch processing layer** — generates change reports and visualizations.
- **Config Injection:** Embeds `AnalyticsOrchestratorConfig` to trigger `hardwareChangeAnalyzer`, then consumes analytics results for visualization.

**Configuration (`HardwareChangePlotflowConfig`):**
  - Shared paths: `source_path`, `annotation_name`, `databaseSchemas_path`
  - Performance: `enable_parallel`, `max_workers` (optional parallel processing)
  - Embedded: `analytics_orchestrator_config` (auto-configured)

**Modules:**
  - *MachineLayoutPlotter*: Generates machine layout evolution visualizations and change reports
  - *MachineMoldPairPlotter*: Creates mold-machine relationship visualizations and utilization reports

**Output:**
  - Static PNG images for change visualizations
  - TXT reports for change summaries
  - Saved to configured directories for distribution and archival

**Orchestration Flow:**
```
  HardwareChangePlotflowConfig → Auto-Config → AnalyticsOrchestrator.hardwareChangeAnalyzer
  → [machineLayout/machineMoldPair]Tracker → Analytics Results 
  → [machineLayout/machineMoldPair]Plotter → Visualizations (PNG/TXT)
```

3. **dynamicDashboardUI 📝 (Interactive Dashboard Platform)**
- Provides **web-based interactive dashboards** with real-time data exploration. 📝
- Manages **live data streaming** and user interactions for dynamic analysis. 📝
- Operates as a **real-time service layer** — enables on-demand data visualization and drill-down analysis. 📝

**Service Layer Architecture:**
```
Analytics Orchestrator (Backend Service)          Dashboard Builder (Visualization Consumer)
        ↓                                                      ↓
┌─────────────────────────────────┐           ┌──────────────────────────────────────┐
│ multiLevelPerformanceAnalyzer   │           │ multiLevelPerformancePlotter         │
│  ├─ dayLevelDataProcessor    ───┼──────────→│  ├─ dayLevelDataPlotter (PNG/TXT/XLS)│
│  ├─ monthLevelDataProcessor  ───┼──────────→│  ├─ monthLevelDataPlotter            │
│  └─ yearLevelDataProcessor   ───┼──────────→│  └─ yearLevelDataPlotter             │
└─────────────────────────────────┘           └──────────────────────────────────────┘

┌─────────────────────────────────┐           ┌──────────────────────────────────────┐
│ hardwareChangeAnalyzer          │           │ hardwareChangePlotter                │
│  ├─ machineLayoutTracker     ───┼──────────→│  ├─ machineLayoutPlotter (PNG/TXT)   │
│  └─ machineMoldPairTracker   ───┼──────────→│  └─ machineMoldPairPlotter           │
└─────────────────────────────────┘           └──────────────────────────────────────┘

                                              ┌──────────────────────────────────────┐
                                              │ dynamicDashboardUI 📝                 │
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
                                              DATA OPERATIONS → VALIDATION ────┐
                                                      |                        ├──────────────────────────→ TRACKING ─→ PLANNING
                                                      ├────────────────────────┘                                            ↓
                                                      ↓                                                              ┌────────────────┐          
        ┌─────────────────────────────────────────────┼──────────────────────────────────────┐                       ↓                ↓           
        ↓                                             ↓                                      ↓                 INITIAL PLAN     REFINER PLAN 📝
    ANALYTICS ORCHESTRATOR                    DASHBOARD BUILDER                    TASK ORCHESTRATOR                              (Consumer)   
   (Dual-Mode: Standalone/Backend)         (Visualization Consumer)              (Operational Consumer)                                ↑
        |                                             |                                      |                                         |
        ├→ Hardware Change Analyzer ───────────────→  ├→ Hardware Change Plotter             |                                         |
        |  (machineLayout, machineMoldPair)           |  (Visualizations: PNG/TXT)           |                                         |
        |                                             |                                      |                                         |
        ├→ Multi-Level Performance Analyzer ───────→  ├→ Multi-Level Performance Plotter     |                                         |
        |  (day/month/year analytics)                 |  (Visualizations: PNG/TXT/XLSX)      |                                         |
        |                                             |                                      |                                         |
        |                                             └→ Dynamic Dashboard UI (Web) 📝      |                                         |
        |                                                                                    |                                         |
        ├→ Cross-Level Performance Analyzer 📝 ───────────────────────────────────────────→ └→ Operational Coordinators 📝            |
        |  (advanced predictive analytics)                                                      (resin, maintenance, quality, yield)   |
        |                                                                                                                              |
        └──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                            (Future: Cross-Level insights for planning)
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
        
──────────────────────────────────────────────────────────────────────────
PHASE 3 — INITIAL PLANNING
    • Support Production & Material Coordination (active POs): ProducingProcessor
    • Detect Purchase Order Changes: PurchaseOrderChangeDetection
    • Generate Initial Planning for (active POs + pending POs): PendingProcessor

──────────────────────────────────────────────────────────────────────────
PHASE 4 — ANALYTICS & VISUALIZATION
    • TriggerDetection → checks for new or changed data
    • DashboardBuilder
      - HardwareChangePlotter
        - MachineLayoutTracker → machine layout change history
        - MachineLayoutPlotter → machine layout change dashboard
        
        - MachineMoldPairTracker → first-run machine/mold pair history extraction
        - MachineMoldPairPlotter → first-run machine/mold pair history dashboard
      
      - MultiLevelPerformancePlotter
        - DayLevelDataPlotter → daily production records with mold/item aggregations
        - DayLevelDataProcessor → daily production static dashboard

        - MonthLevelDataProcessor → monthly finished/unfinished order analysis
        - MonthLevelDataPlotter → monthly production static dashboard

        - YearLevelDataProcessor → annual production trends and completion statistics
        - YearLevelPlotter → annual production static dashboard
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
├── HistoricalInsights/
|   ├── MoldMachineFeatureWeightCalculator/     # Mold-machine compatibility scoring
|   │   ├── newest/                             # *_confidence_report.txt
|   │   └── weights_hist.xlsx                   # Historical calculations
|   │
|   └── MoldStabilityIndexCalculator/newest/    # Mold performance stability (1 file)
|       └── *_mold_stability_index.xlsx         # → Feeds ProducingProcessor
|
# ══════════════════════════════════════════════════════════════════
# PRODUCTION OPTIMIZATION
# ══════════════════════════════════════════════════════════════════
├── AutoPlanner/InitialPlanner/
|   |
|   ├── ProducingProcessor/newest/       # Active production analysis (1 file)
|   │   └── *_producing_processor.xlsx   # Uses: OrderProgress + MoldMachineFeatureWeightCalculator +  MoldStabilityIndexCalculator outputs
|   │
|   └── PendingProcessor/newest/         # Production planning suggestions (1 file)
|        └── *_pending_processor.xlsx    # Builds on ProducingProcessor output
│
# ══════════════════════════════════════════════════════════════════
# DASHBOARD BUILDER
# ══════════════════════════════════════════════════════════════════
└── DashboardBuilder/
    │ 
    # ══════════════════════════════════════════════════════════════════
    # HARDWARE CHANGE DASHBOARDS
    # ══════════════════════════════════════════════════════════════════
    ├── HardwareChangePlotter/
    |   ├─ MachineLayoutTracker/newest/ + MachineLayoutPlotter/newest/
    |   └─ MachineMoldPairTracker/newest/ + MachineMoldPairPlotter/newest/
    # ══════════════════════════════════════════════════════════════════
    # MULTI-LEVEL PERFORMANCE DASHBOARDS
    # ══════════════════════════════════════════════════════════════════
    └── MultiLevelPerformancePlotter/
        ├── DayLevelDataProcessor/newest/ + DayLevelDataPlotter/newest/
        ├── MonthLevelDataProcessor/newest/ + MonthLevelDataPlotter/newest/ 
        └── YearLevelDataProcessor/newest/ + YearLevelPlotter/newest/
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
                                               DataPipelineOrchestrator
                                                         ↓
                                                  DashboardBuilder
                            ┌────────────────────────────┴───────────────────────────┐
                            ↓                                                        ↓
              enable_hardware_change_plotter                             enable_multi_level_plotter
                            ↓                                                        ↓
                HardwareChangePlotter                                   MultiLevelPerformancePlotter
                            ↓                                                        ↓
                AnalyticsOrchestrator                                      AnalyticsOrchestrator
                            ↓                                                        ↓
                HardwareChangeAnalyzer                                  MultiLevelPerformanceAnalyzer
                  ├─ Machine Layout change dashboards                    ├─ Daily dashboards
                  │  MachineLayoutTracker → MachineLayoutPlotter         |  DayLevelDataProcessor  → DayLevelDataPlotter
                  │       (analysis)          (visualization)            │       (analysis)            (visualization)
                  │                                                      │
                  └─ Mold pairing dashboards                             ├─ Monthly dashboards 
                     MachineMoldPairTracker → MachineMoldPairPlotter     |  MonthLevelDataProcessor → MonthLevelDataPlotter
                          (analysis)          (visualization)            │       (analysis)            (visualization)
                                                                         │
                                                                         └─ Yearly dashboards
                                                                            YearLevelDataProcessor  → YearLevelPlotter
                                                                                 (analysis)            (visualization)
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

### Milestone 03: Enhanced Production Planning with Analytics and Dashboard System (Completed November 2025)
> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_03.md)

- **Depends on:** Milestone 02 (Initial Production Planning System)
- **Nature of Update:** Upgrade & Extension to OptiMoldIQWorkflow

#### Overview

Milestone 03 upgrades the OptiMoldIQWorkflow from a pure production planning engine into a comprehensive **planning + analytics + visualization system**.

**Key Principle:** **Extends without replacing** — all M02 functionality remains intact while adding optional analytics and dashboard capabilities.

#### System Evolution

```
M01: Data Pipeline
  ↓
M02: Production Planning Workflow
  ↓
M03: + Analytics & Dashboards ← YOU ARE HERE
  ↓
M04: + Plan Refinement (consumes M03 analytics)
  ↓
M05: + Task Orchestration (consumes M03 analytics)
```

#### What's Preserved from M02

All phases remain **unchanged and fully operational**:

1. **Phase 1:** Data Pipeline
2. **Phase 2:** Shared DB Build & Validation
3. **Phase 2.5:** Historical Insights
4. **Phase 3:** Production Planning

> Plus: Conditional execution, smart change detection, WorkflowConfig settings, error handling.

#### What's Added in M03

Phase 4: Analytics & Dashboards (Optional) with two independent components connected via service-consumer pattern:

##### A. analyticsOrchestrator (Backend Service)

**1. hardwareChangeAnalyzer ✅**
- **MachineLayoutTracker:** Layout evolution, change detection, activity patterns
- **MachineMoldPairTracker:** Mold-machine relationships, first-run history, utilization
- **Output:** TXT, JSON, XLSX reports

**2. multiLevelPerformanceAnalyzer ✅**
- **DayLevelDataProcessor:** Daily production metrics, real-time operations
- **MonthLevelDataProcessor:** Monthly patterns, completion rates, trends
- **YearLevelDataProcessor:** Annual insights, long-term performance
- **Output:** Multi-level DataFrames (TXT, JSON, XLSX)

**3. crossLevelPerformanceAnalyzer 📝** (Future: advanced predictive analytics)

##### B. dashboardBuilder (Visualization Layer)

**1. multiLevelPerformancePlotter ✅**
- **DayLevelDataPlotter:** Daily operational dashboards
- **MonthLevelDataPlotter:** Monthly trend analysis
- **YearLevelDataPlotter:** Annual strategic dashboards
- **Output:** PNG, TXT, XLSX

**2. hardwareChangePlotter ✅**
- **MachineLayoutPlotter:** Layout evolution visualizations
- **MachineMoldPairPlotter:** Relationship and utilization reports
- **Output:** PNG, TXT

**3. dynamicDashboardUI 📝** (Future: interactive web platform)

##### Service-Consumer Architecture

```
analyticsOrchestrator (Backend)       dashboardBuilder (Consumer)
        ↓                                     ↓
┌──────────────────────────────┐    ┌─────────────────────────────┐
│ multiLevelPerformanceAnalyzer│    │ multiLevelPerformancePlotter│
│  ├─ dayLevelDataProcessor ───┼───→│  ├─ dayLevelDataPlotter     │
│  ├─ monthLevelDataProcessor──┼───→│  ├─ monthLevelDataPlotter   │
│  └─ yearLevelDataProcessor───┼───→│  └─ yearLevelDataPlotter    │
└──────────────────────────────┘    └─────────────────────────────┘

┌─────────────────────────────┐    ┌────────────────────────────┐
│ hardwareChangeAnalyzer      │    │ hardwareChangePlotter      │
│  ├─ machineLayoutTracker ───┼───→│  ├─ machineLayoutPlotter   │
│  └─ machineMoldPairTracker──┼───→│  └─ machineMoldPairPlotter │
└─────────────────────────────┘    └────────────────────────────┘

Future: → planRefiner, taskOrchestrator, dynamicDashboardUI
```

**Config Injection Pattern:**
```
[Plotter]Config → Embeds AnalyticsOrchestratorConfig → Auto-triggers Analytics
→ Results → Visualization → PNG/TXT/XLSX
```

#### Enhanced Workflow Architecture

| Phase | Trigger | Components | Status |
|-------|---------|------------|--------|
| **1. Data Pipeline** | Always | DataPipelineOrchestrator | M02 |
| **2. DB Build & Validation** | Data changes | ValidationOrchestrator | M02 |
| **2.5. Historical Insights** | Enough records | MoldStabilityCalculator | M02 |
| **3. Production Planning** | PO changes | Producing/PendingProcessor | M02 |
| **4A. Analytics** | Optional | analyticsOrchestrator | **NEW** |
| **4B. Dashboards** | Optional | dashboardBuilder | **NEW** |

### Milestone 04: Enhanced Production Planning with Analytics and Task Orchestrator System (In Progress)

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