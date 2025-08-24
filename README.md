🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

OptiMoldIQ is a smart production system designed to streamline and optimize the plastic molding process. It integrates multi-agent architecture to automate production scheduling, track resources, and provide actionable insights to improve efficiency and quality.

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
  - [🚀 Interactive System Dashboard](#-interactive-system-dashboard)
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

## Business Problem
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

## Key Goals
- **Integrated Planning and Monitoring**: Automate production scheduling and resource tracking.
- **Quality and Yield Insights**: Optimize cycle times while maintaining quality.
- **Proactive Maintenance and Restocking**: Prevent downtime and material shortages.
- **Visualization and Decision Support**: Build a centralized dashboard for actionable insights.

👉 [Read full context](docs/OptiMoldIQ-business-problem.md)

---

## Planned Solution
The OptiMoldIQ System uses a multi-agent architecture to tackle these challenges:
| Agent                        | Description                                                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **DataPipelineOrchestrator** | **Collector**: Collects distributed monthly data → consolidates → **Loader**: loads into shared DB. Handles both dynamic & static data.|
| **ValidationOrchestrator**   | Performs cross-checks: <br>1. **PORequiredCriticalValidator**: `productRecords` ↔ `purchaseOrders` <br>2. **StaticCrossDataChecker**: Both ↔ static fields <br>3. **DynamicCrossDataValidator**: Both ↔ dynamic fields |
| **OrderProgressTracker**     | Aggregates production per machine/shift → Maps back to PO → Flags any mismatches via validation results.                   |
| **AutoPlanner** | Generates and refines production schedules: <br>• `InitialPlanner`: Creates the first plan based on **historical insights** when sufficient data records are available for trend analysis, and **compatibility specifications** using technical specifications to maximize machine utilization. <br>• `Plan Refinery`: Refines plans based on tracking and validation from related sources, including real-time plastic storage, historical usage, and maintenance status of the machines and molds. |
| **AnalyticsOrchestrator**     | Performs:<br>1. **DataChangeAnalyzer**: Tracks and updates historical changes (e.g., machine layout, mold usage)<br>2. **MultiLevelDataAnalytics**: Analyzes product-related information across multiple levels (year, month, day, shift) for deeper insights.|
| **TaskOrchestrator**     | Performs: <br>1. **ResinCoordinator**: Monitors resin stock and consumption. <br>2. **MoldCoordinator**: Tracks mold usage, maintenance. <br>3. **MachineCoordinator**: Tracks machine usage, machine availability and lead times. <br>4. **ProductQualityCoordinator**: Tracks yield and NG rates. <br>5. **MaintenanceCoordinator**: Predictive maintenance scheduling to reduce downtime for mold and machine. <br>6. **YieldOptimizator**: Tracks the relationship between cycle time, yield, and NG rates to optimize overall production yield. It also analyzes resin usage patterns to recommend more efficient material requirements.|
| **DashBoardBuilder** |Creates an interactive dashboard for real-time monitoring and decision support. |

🔗 For agent architecture details, see [OptiMoldIQ-agentsBreakDown](docs/OptiMoldIQ-agentsBreakDown.md)

---

## System Architecture Diagram

The following diagram shows how the data flows from external sources into the system and how various agents interact in the pipeline.

🔗 For full  diagram details, see [OptiMoldIQ-systemDiagram-ASCII](docs/OptiMoldIQ-systemDiagram-ASCII.md)

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

## Dataset Overview

This project leverages a 27-month dataset collected from a plastic injection molding production facility. It consists of over **61,000 production records** and **6,200 internal orders**, reflecting the complexity of real-world manufacturing operations.

### Key Entities
- **Items** – 694 plastic products
- **Molds** – 251 unique molds
- **Machines** – 49 molding machines
- **Materials** – 445 materials (resins, masterbatches, additives)
- **Orders** – 6,234 scheduled production orders
- **Production Records** – 61,185 logs of manufacturing outcomes

🔗 For full schema and statistical details, see [OptiMoldIQ-dataset](docs/OptiMoldIQ-dataset.md)

---

## Data Overview

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

🔗 See [OptiMoldIQ-dbSchema](docs/OptiMoldIQ-dbSchema.md) for full field details and formats.

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

## Roadmap

| Phase | Description |
|-------|-------------|
| **Phase 1** | ✅ Define static & dynamic databases |
| **Phase 2** | ✅ Build & integrate core preprocessing agents |
| **Phase 3** | 🔄 Integrate RL-based optimization <br> • Define reward function <br> • Train on historical data |
| **Phase 4** | 🔄 Build dashboard <br> • UI wireframes <br> • API integration |

---

## Current Status Summary

| Component | Status |
|-----------|--------|
| Static Databases (mold/machine/resin) | ✅ Defined |
| Dynamic Data Pipeline | ✅ Implemented |
| Shared Database | ✅ First version generated |
| Validation System | ✅ Functional |
| Production Tracker | ✅ Mapping by PO & shift |
| AnalyticsOrchestrator | 🔄 Upcoming |
| DashBoardBuilder | 🔄 Upcoming |
| AutoPlanner | 🔄 Upcoming |
| TaskOrchestrator | 🔄 Upcoming |

---

## 🚀 Interactive System Dashboard

Experience OptiMoldIQ's architecture through our interactive dashboard:

➤ [🔗 View Live Dashboard](https://thuyhale.github.io/OptiMoldIQ/)

---

## Milestones

### ✅ **Milestone 01**: Core Data Pipeline Agents  
  
Completed July 2025 — Includes:

- `dataPipelineOrchestrator`
- `validationOrchestrator`
- `orderProgressTracker` 

➤ [View Details](docs/milestones/OptiMoldIQ-milestone_01.md) 

➤ [View orderProgressTracker Live Demo](docs/agents_output_overviews/orderProgressTracker_output_overviews.md)

### ✅ **Milestone 02**: Initial Production Planning System
  
Completed August 2025 — Includes:

- Upgrated `dataPipelineOrchestrator`, `validationOrchestrator`, and `orderProgressTracker`
  
- `initialPlanner` includes:

  - 1. Generated **historical insights** from historical production records: 

    - `MoldStabilityIndexCalculator` generate **comprehensive stability assessments** for manufacturing molds. It evaluates mold reliability through multi-dimensional analysis of cavity utilization and cycle time performance, providing critical input for production capacity planning and mold maintenance optimization.

    - `MoldMachineFeatureWeightCalculator` against **efficiency thresholds** to generate confidence-weighted feature importance scores. It analyzes good vs bad production performance patterns using statistical methods to determine optimal weights for production planning priority matrices.

  - 2. Tracked and created comprehensive manufacturing/producing plans using `ProducingProcessor` integrates production status data with optimization results from `HybridSuggestOptimizer`. 
  
    - `HybridSuggestOptimizer` combines multiple optimization strategies to suggest optimal production configurations based on historical records. It integrates: 
      - `ItemMoldCapacityOptimizer` to estimate mold capacity used `MoldStabilityIndexCalculator` results
        
      - `MoldMachinePriorityMatrixCalculator` calculate mold-machine priority matrix used `MoldMachineFeatureWeightCalculator` results.

    The system helps manufacturing operations make intelligent decisions about mold selection, machine allocation, and production scheduling.

  - 3. Optimizated and generated comprehensive pending assignments using `PendingProcessor` with two-tier optimization system using two-phase greedy algorithms:
    - `HistBasedMoldMachineOptimizer` based on `priority matrices` and `estimated capacity based lead time` constraints.
    - `CompatibilityBasedMoldMachineOptimizer` based on `technical compatibility matrices` and `estimated capacity based lead time` constraints.

➤ [View Details](docs/milestones/OptiMoldIQ-milestone_02.md) 

➤ [View optiMoldIQWorkflow Live Demo](docs/agents_output_overviews/optiMoldIQWorkflow_output_overview.md)
  
### 🔄 **In Progress**: AnalyticsOrchestrator + DashBoardBuilder

---

## Quickstart

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
