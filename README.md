🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Intelligent Plastic Molding Planner

OptiMoldIQ is a smart production system designed to streamline and optimize the plastic molding process. It integrates multi-agent architecture to automate production scheduling, track resources, and provide actionable insights to improve efficiency and quality.

---

## Table of Contents
- [Current Phase](#current-phase)
- [Business Problem](#business-problem)
- [Key Goals](#key-goals)
- [Planned Solution](#planned-solution)
- [Dataset Overview](#dataset-overview)
- [Data Overview](#data-overview)
- [Folder Structure](#folder-structure)
- [Roadmap](#roadmap)
- [Current Status Summary](#current-status-summary)
- [Milestones](#milestones)
- [Quickstart](#quickstart-coming-soon)
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
| **AutoPlanner** | Generates and refines production schedules: <br>• `InitialPlanner`: Creates the first plan based on static info. <br>• `PlanRefiner`: Refines plans based on tracking and validation. |
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
                   ┌────────────────────────────────┐
                   │       External Inputs          │
                   │ DynamicDB (purchaseOrders,     │
                   │    productRecords) + StaticDB  │
                   └────────────┬───────────────────┘
                                │
                                ▼                                                          ┌────────────────────────────┐ 
                 ┌────────────────────────────┐                                            │    ValidationOrchestrator  │ 
                 │  DataPipelineOrchestrator  │                   ┌──────────────────────► │(Check consistency between  │ 
                 └────────────┬───────────────┘                   │                        │  Static & Dynamic Data)    │
                              │                                   │                        └────────────┬───────────────┘ 
        ┌────────────────────┴────────────────────┐               │         ┌───────────────────────┬───┴────────────────────┐                     
        ▼                                         ▼               │         ▼                       ▼                        ▼
┌────────────────────┐                 ┌─────────────────────┐    │    ┌────────────┐  ┌─────────────────────────┐ ┌────────────────────┐  
│    DataCollector   │                 │   DataLoaderAgent   │    │    │StaticCross │  │DynamicCrossDataValidator│ │ PORequiredCritical │       
│ (monthly dynamic DB│                 │ (load & unify static│    │    │DataChecker │  └────────────┬────────────┘ │ Validator          │
│   .xlsx → .parquet)│                 │   data → .parquet)  │    │    └─────┬──────┘               │              └───────────┬────────┘
└─────────┬──────────┘                 └─────────┬───────────┘    │          ▼                      ▼                          ▼
          ▼                                      ▼                │     ┌────────────────────────────────────────────────────────┐
    ┌──────────────────────────────────────────────────┐          │     │                    PO Mistmatch information            │
    │           ✅ Shared Database (.parquet)         │          │     └────────────────────────────────────────────────────────┘
    │     (static + dynamic for all other agents)      │──────────┘                                │
    └──────────────────────────────────────────────────┘                                           │
                          │                                                                        │
                          ▼                                                                        ▼
                   ┌──────────────────────────────────────────────────────────────────────────────────────┐
                   │                                  OrderProgressTracker                                │
                   │ (Group product records by PO, flag mismatch note from Validation agent (if any))     │
                   └──────────────────────────────────────────┬───────────────────────────────────────────┘
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

## Milestones
- ✅ **Milestone 01**: Core Data Pipeline Agents  
  Completed July 2025 — Includes `dataPipelineOrchestrator`, `validationOrchestrator`, and `orderProgressTracker`.  
  ➤ [View Details](docs/milestones/OptiMoldIQ-milestone_01.md)
  ➤ [View orderProgressTracker Demo](docs/agents_output_overviews/orderProgressTracker_output_overviews.md)
  
- 🔄 **Upcoming**: AnalyticsOrchestrator + DashBoardBuilder

---

## Quickstart (Coming Soon)
- Set up the Python environment
- Run initial agents on sample data
- Visualize results via the dashboard

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
