🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner
**OptiMoldIQ** is a multi-agent intelligent manufacturing system designed to optimize injection molding operations through automated data pipelines, validation, production planning, analytics, and real-time decision support.
It centralizes operational intelligence by coordinating data, machines, molds, and scheduling under a unified architecture.  

---

Legend: ✅ Complete | 🔄  In Progress | 📝 Planned

---

## Table of Contents
- [OptiMoldIQ: Intelligent Plastic Molding Planner](#optimoldiq-intelligent-plastic-molding-planner)
  - [Table of Contents](#table-of-contents)
  - [Current Phase](#current-phase)
  - [Business Problem](#business-problem)
    - [Background](#background)
    - [Challenges](#challenges)
    - [Problem Statement](#problem-statement)
  - [Key Goals](#key-goals)
  - [Planned Solution](#planned-solution)
  - [System Architecture Diagram](#system-architecture-diagram)
  - [Dataset Overview](#dataset-overview)
    - [Key Entities](#key-entities)
  - [Data Overview](#data-overview)
    - [Dynamic Datasets](#dynamic-datasets)
    - [Static Datasets](#static-datasets)
  - [Folder Structure](#folder-structure)
  - [Roadmap](#roadmap)
  - [Current Status Summary](#current-status-summary)
  - [Interactive System Dashboard](#-interactive-system-dashboard)
  - [Milestones](#milestones)
    - [✅ **Milestone 01**: Core Data Pipeline Agents](#-milestone-01-core-data-pipeline-agents)
    - [✅ **Milestone 02**: Initial Production Planning System](#-milestone-02-initial-production-planning-system)
    - [🔄 **In Progress**: AnalyticsOrchestrator + DashBoardBuilder](#-in-progress-analyticsorchestrator--dashboardbuilder)
  - [Quickstart](#quickstart)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

---

## Current Phase
OptiMoldIQ is in the **system design phase**, focusing on defining database structures, agent workflows, and system architecture.

---

## Business Problem 📝
### Background 📝
In plastic molding production, achieving optimal efficiency while maintaining high product quality is challenging due to the complexity of interconnected factors like:
- Mold utilization and machine maintenance.
- Resin inventory management.
- Production scheduling and yield optimization.

### Challenges 📝
Poor management or lack of integration between components can lead to:
- Increased production downtime.
- Material waste or stock shortages.
- Unbalanced machine and mold utilization.
- Inconsistent product quality or high NG (non-good) rates.
- Reduced production yield and efficiency.

### Problem Statement 📝
Current systems are:
- Manual or static, lacking real-time insights.
- Prone to inefficiencies in scheduling, resource tracking, and quality management.

> 👉 [Full context](docs/OptiMoldIQ-business-problem.md)

--- 

## Key Goals 🔄
- **1. Data Operations Orchestration** 
  - Daily Data Ingestion Pipeline: Automated collection and loading of production and operational data. ✅
  - Multi-Layer Validation: Static, dynamic, and required-field checks to ensure data integrity. ✅
  - Real-Time Production Tracking: Monitor production progress and operational KPIs as they happen. ✅
- **2. Production Planning Orchestration** 
  - *Multi-Stage Mold–Machine Planning*:
    - Initial planning leveraging historical patterns and compatibility analysis. ✅
    - Plan refinement using insights from analytics orchestration and operational task orchestration, including resin inventory and mold/machine maintenance. 📝
- **3. High-Level Orchestration**
  - *Analytics Orchestration*: 
    - Auto-detect mold/machine layout changes and generate static reports. ✅
    - Multi-level analytics with day, month, and year views for operational insights. ✅
  - *Reporting Orchestration*: 
    - Centralized dashboard generation for actionable insights. ✅
    - Visualization across multiple time resolutions (day/month/year) for decision support. ✅
  - *Operational Task Orchestration*:
    - Proactive maintenance of molds and machines; resin restocking to prevent downtime and material shortages. 📝
    - Quality and yield optimization: 📝
      - Improve cycle times while maintaining product quality.
      - Enhance production yield through actionable insights.

---

## Planned Solution 🔄
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
  ├─ dashboardBuilder (child)
  └─ taskOrchestrator (child)
      ├─ resourceCoordinator (resin, inventory)
      ├─ assetCoordinator (mold + machine tracking)
      ├─ maintenanceCoordinator (predictive maintenance)
      └─ qualityOptimizer (yield + quality + cycle time)
  ```
### 1. optiMoldMaster (Mother-Agent) 🔄
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

### 2. Core Components (Child Agents) 🔄
- 2.1 dataPipelineOrchestrator ✅
  - Manages a robust 2-phase ETL pipeline:
    - Collect → Load
    - Full error–recovery workflow
    - Automated alerts & self-healing mechanisms
  - Ensures stable, reproducible manufacturing data ingestion.
- 2.2 validationOrchestrator ✅
  - Coordinates and enforces multi-level data validation:
    - Static validation (schema, datatype, integrity)
    - Dynamic validation (anomaly detection, cross-table checks)
    - Required-field validation
    - Version-controlled validation reports
  - Maintains consistency across all manufacturing datasets.
- 2.3 orderProgressTracker ✅
  - Real-time operational visibility:
    - Tracks production progress of all manufacturing orders
    - Monitors status transitions, cycle completion, and schedule adherence
    - Integrates validated data to produce consolidated production analytics
- 2.4 autoPlanner 🔄
- Advanced production planning tailored for mold manufacturing.
  - 2.4.1 initialPlanner ✅
    - Multi-stage pipeline for transforming raw data → optimized production plan
    - Integrates production status analysis + advanced optimization algorithms
    - Robust error-handling and plan-quality validation
    - Two-tier optimization for mold–machine assignment based on:
      - Historical machine performance
      - Technical compatibility
      - Load balancing
      - Quality and efficiency constraints
  - 2.4.2 planRefiner 
    - Performs refinement & adjustment of initialPlanner’s output
    - Adds secondary analysis layers (capacity shifts, conflicts, real-time updates)
- 2.5 analyticsOrchestrator 🔄
  - Central hub that:
    - Coordinates analytic modules
    - Processes manufacturing data into structured insights
    - Updates historical analytics records
    - Supplies data for dashboards, planning, and progress tracking
- 2.6 dashboardBuilder ✅
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
- 2.7 taskOrchestrator 📝
  - Coordinates cross-dependent operational tasks, including:
  - Resin inventory management
  - Mold maintenance planning
  - Machine maintenance scheduling
  - Escalation handling for related operational constraints

### 3. Agent Descriptions 🔄

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
| dataChangeAnalyzer | Sub-component | Tracks mold/machine layout changes and history |
| multiLevelDataAnalytics | Sub-component | Multi-resolution analytics engine (day/month/year) |
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

- Central analytics hub that processes manufacturing data into structured insights  
- Coordinates all analytic modules  
- Updates historical analytics records  
- Supplies data for dashboards, planning, and progress tracking  
- Auto-detects operational changes (mold/machine layout updates)

- **Sub-components**:  
  - **dataChangeAnalyzer**: Monitors machine/mold layout changes and generates reports  
  - **multiLevelDataAnalytics**: Provides daily/monthly/yearly analytics and KPIs

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

> 👉 [Agent architecture](docs/OptiMoldIQ-agentsBreakDown.md)

---

## System Architecture Diagram 🔄

The following diagram shows how the data flows from external sources into the system and how various agents interact in the pipeline.

> 👉 [ASCII diagram](docs/OptiMoldIQ-systemDiagram-ASCII.md)

<details> <summary> Or click to expand system architecture diagram</summary>

```plaintext
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               [ OptiMoldIQWorkflow ]                                            │
│                    Main orchestrator coordinating all manufacturing workflow phases              │
└──────────────┬──────────────────────────────────────────────────────────────────────────────────┘
               ▼ PHASE 1: DATA COLLECTION                                           
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │ DataPipelineOrch.    │                                            │   Update Detection   │
        │ (Collect & Process)  │────── Process Pipeline ──────────────────⯈│ (Analyze Changes)    │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Execute Data Collection                                             🔍 Detect Database Updates
    • Run DataPipelineOrchestrator                                         • Check collector results
    • Process dynamic databases                                            • Check loader results  
    • Generate pipeline report                                             • Identify changed databases
    • Handle collection errors                                             • Return trigger flag & details

               ▼ PHASE 2: SHARED DB BUILDING (Conditional)
        ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
        │ ValidationOrch.      │      │ OrderProgressTracker │      │ Historical insight   │      │ ProducingProcessor   │
        │ (Data Validation)    │────⯈│ (Progress Monitoring)│────⯈ │ adding phase         │────⯈│ (Production Analysis)│
        └──────────────────────┘      └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
               │                              │                              │                                │
               ▼                              ▼                              ▼                                ▼
    ✅ Validate Data Quality          📈 Track Order Status       📈 Generate Historical Insights   🏭 Process Production Data
    • Run validation checks            • Monitor order progress     • Calculate:                      • Analyze production metrics
    • Generate mismatch reports        • Track milestones           1. mold stability index           • Calculate efficiency & loss
    • Ensure data integrity            • Update progress logs       2. mold machine feature weight    • Generate production reports
    • Save validation results          • Generate progress reports                                    • Process stability indices

               ▼ PHASE 3: INITIAL PLANNING (Conditional)
        ┌──────────────────────┐                                             ┌──────────────────────┐
        │   Purchase Order     │                                             │   PendingProcessor   │
        │   Change Detection   │────── If PO Changes Detected ─────────────⯈│ (Order Processing)   │
        └──────────────────────┘                                             └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    🛒 Check Purchase Orders                                            ⚡ Process Pending Orders
    • Analyze updated databases                                          • Apply priority ordering
    • Look for 'purchaseOrders' changes                                  • Respect load thresholds
    • Determine if planning needed                                       • Optimize processing schedule
    • Trigger or skip processing                                         • Generate planning reports

        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                                📋 REPORTING SYSTEM                                  │
        │  • Generate comprehensive workflow reports                                          │
        │  • Include data collection, validation, progress, and planning results              │
        │  • Save timestamped reports with UTF-8 encoding                                     │
        │  • Provide audit trails and operational summaries                                   │
        └──────────────────────────────────────┬──────────────────────────────────────────────┘
                                               ▼
                                      🛠️  To Be Continued...
```
</details>



---

## Dataset Overview ✅

This project leverages a 27-month dataset collected from a plastic injection molding production facility. It consists of over **61,000 production records** and **6,200 internal orders**, reflecting the complexity of real-world manufacturing operations.

### Key Entities
- **Items** – 694 plastic products
- **Molds** – 251 unique molds
- **Machines** – 49 molding machines
- **Materials** – 445 materials (resins, masterbatches, additives)
- **Orders** – 6,234 scheduled production orders
- **Production Records** – 61,185 logs of manufacturing outcomes

> 👉 [Full schema & stats](docs/OptiMoldIQ-dataset.md)

---

## Data Overview ✅

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

> 👉 [Database schema](docs/OptiMoldIQ-dbSchema.md)

---

## Folder Structure ✅

```bash
.
├── agents/                # Agent logic (AutoStatusAgent, InitialSchedAgent, etc.)
├── database/              # Static and shared JSON schemas
├── logs/                  # Auto-generated logs for status/errors
├── docs/                  # Documentation (business_problem.md, agent_specifications.md, etc.)
└── README.md              # This file
```

---

## Roadmap 🔄

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

## Current Status Summary 🔄

| Component                             | Status & Notes                                                                               |
| ------------------------------------- | -------------------------------------------------------------------------------------------- |
| Static Databases (mold/machine/resin) | ✅ Defined                                                                                    |
| Dynamic Data Pipeline                 | ✅ Implemented                                                                                |
| Shared Database                       | ✅ First version generated                                                                    |
| Validation System                     | ✅ Functional                                                                                 |
| Production Tracker                    | ✅ Mapping by PO & shift                                                                      |
| AnalyticsOrchestrator                 | 📝 In Progress (Layout Changes Detection 📝, Multi-Level Analytics ✅, other modules ongoing) |
| DashBoardBuilder                      | 📝 Upgrading (offline static ✅ → dynamic interactive UI/UX 📝)                               |
| AutoPlanner                           | 📝 In Progress (initialPlanner ✅, planRefiner 📝)                                            |
| TaskOrchestrator                      | 📝 In Progress (maintenance, resin, quality/yield tasks ongoing)                             |

---

## 🚀 Interactive System Dashboard

Experience OptiMoldIQ's architecture through our interactive dashboard:

> 👉 [Live Dashboard](https://thuyhale.github.io/OptiMoldIQ/)

---

## Milestones 🔄

### ✅ **Milestone 01**: Core Data Pipeline Agents  
  
Completed July 2025 — Includes:

- `dataPipelineOrchestrator`
- `validationOrchestrator`
- `orderProgressTracker` 

> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_01.md) 

> 👉 [orderProgressTracker Live Demo](docs/agents_output_overviews/orderProgressTracker_output_overviews.md)

### ✅ **Milestone 02**: Initial Production Planning System
  
Completed August 2025 — Includes:

- Upgrated `dataPipelineOrchestrator`, `validationOrchestrator`, and `orderProgressTracker`
  
- `initialPlanner` includes:

  - Generated **historical insights** from historical production records: 

    - `MoldStabilityIndexCalculator` generate **comprehensive stability assessments** for manufacturing molds. It evaluates mold reliability through multi-dimensional analysis of cavity utilization and cycle time performance, providing critical input for production capacity planning and mold maintenance optimization.

    - `MoldMachineFeatureWeightCalculator` against **efficiency thresholds** to generate confidence-weighted feature importance scores. It analyzes good vs bad production performance patterns using statistical methods to determine optimal weights for production planning priority matrices.

  - Tracked and created comprehensive manufacturing/producing plans using `ProducingProcessor` integrates production status data with optimization results from `HybridSuggestOptimizer`. 
  
    - `HybridSuggestOptimizer` combines multiple optimization strategies to suggest optimal production configurations based on historical records. It integrates: 
      - `ItemMoldCapacityOptimizer` to estimate mold capacity used `MoldStabilityIndexCalculator` results
        
      - `MoldMachinePriorityMatrixCalculator` calculate mold-machine priority matrix used `MoldMachineFeatureWeightCalculator` results.

    The system helps manufacturing operations make intelligent decisions about mold selection, machine allocation, and production scheduling.

  - Optimizated and generated comprehensive pending assignments using `PendingProcessor` with two-tier optimization system using two-phase greedy algorithms:
    - `HistBasedMoldMachineOptimizer` based on `priority matrices` and `estimated capacity based lead time` constraints.
    - `CompatibilityBasedMoldMachineOptimizer` based on `technical compatibility matrices` and `estimated capacity based lead time` constraints.

> 👉 [Details](docs/milestones/OptiMoldIQ-milestone_02.md) 

> 👉 [optiMoldIQWorkflow Live Demo](docs/agents_output_overviews/optiMoldIQWorkflow_output_overviews.md)
  
### 🔄 **In Progress**: AnalyticsOrchestrator + DashBoardBuilder

---

## Quickstart 🔄

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

*This README will be updated regularly as the OptiMoldIQ system evolves through development.*
