> Introduced in v2
> Purpose: Act as a centralized shared database and backbone data layer connecting data ingestion, validation, analytics, production planning, and dashboard visualization.

---

## Shared Database

**Location:** `agents/shared_db/`

The Shared Database is the **single source of truth** for all data exchanged between agents. It defines **where data lives, how it is versioned, and who can read or write it**, without encoding module-specific business logic. It is designed to remain stable across milestones and serve as the primary integration surface for future framework layers.

---

## Design Principles

* Centralized, agent-agnostic data layer
* Explicit producer → consumer boundaries
* Append-only, timestamped outputs
* Read-only access for downstream agents
* No agent owns filesystem topology or data lifecycle

> **Important:** Shared Database documents *data contracts*, not *algorithmic behavior*. Detailed module logic and output schemas are defined in the framework documentation.

---

## Directory Structure (High-level)

```plaintext
agents/shared_db/
│
├── DataPipelineOrchestrator/newest/        # Pipeline execution logs
├── DataLoaderAgent/newest/                 # Main Shared Database (canonical datasets)
├── ValidationOrchestrator/newest/          # Validation reports
│
├── OrderProgressTracker/newest/            # Production & order status snapshots
│
├── HistoricalInsights/                     # Derived historical insights
│   ├── MoldMachineFeatureWeightCalculator/
│   └── MoldStabilityIndexCalculator/
│
├── AutoPlanner/InitialPlanner/              # Production planning outputs
│   ├── ProducingProcessor/newest/
│   └── PendingProcessor/newest/
│
├── AnalyticsOrchestrator/                   # Analytics outputs
│   ├── HardwareChangeAnalyzer/newest/
│   └── MultiLevelPerformanceAnalyzer/newest/
│
└── DashboardBuilder/                        # Analytics & visualization outputs
    ├── MultiLevelPerformanceVisualizationService/
    └── HardwareChangeVisualizationService/
```

---

## Versioning & Naming Conventions

* `newest/` is a symbolic pointer to the latest timestamped execution output
* Timestamp prefix format: `YYYYMMDD_HHMM_*`
* Historical outputs are preserved for traceability and auditing

---

## Main Shared Database

Located at: `DataLoaderAgent/newest/`

This folder contains the **canonical datasets** consumed by all downstream agents.

### Dynamic Datasets (frequently updated)

* `*_productRecords.parquet`
* `*_purchaseOrders.parquet`

### Static Reference Datasets (infrequently updated)

* `*_itemInfo.parquet`
* `*_machineInfo.parquet`
* `*_moldInfo.parquet`
* `*_resinInfo.parquet`
* `*_itemCompositionSummary.parquet`
* `*_moldSpecificationSummary.parquet`

### Metadata

* `path_annotations.json` — authoritative path registry for shared database assets

---

## Agent Read / Write Responsibilities

| Agent / Component             | Reads From                                         | Writes To                           |
| ----------------------------- | -------------------------------------------------- | ----------------------------------- |
| DataPipelineOrchestrator      | Raw data sources                                   | Execution logs                      |
| DataLoaderAgent               | Raw data sources                                   | Main Shared Database                |
| ValidationOrchestrator        | Main Shared Database                               | Validation reports                  |
| OrderProgressTracker          | Main Shared Database (+ Validation)                | Order progress snapshots            |
| HistoricalInsights generators | Main Shared Database                               | HistoricalInsights outputs          |
| ProducingProcessor            | Main Shared Database + HistoricalInsights          | ProducingProcessor outputs          |
| PendingProcessor              | Main Shared Database + ProducingProcessor outputs  | PendingProcessor outputs            |
| AnalyticsOrchestrator         | Main Shared Database                               | Analytics outputs                   |
| DashboardBuilder              | Main Shared Database                               | Visualization & analytics artifacts |

> No agent writes to another agent’s output directory.

## Special Note: AnalyticsOrchestrator

`AnalyticsOrchestrator` acts as a **central analytics facade** rather than a single-purpose analytics agent.

It supports two execution modes:

1. **Standalone analytics execution**
   - Triggered directly by workflow or user configuration
   - Persists analytics outputs into its own namespace under `AnalyticsOrchestrator/`
   - Behaves like a standard downstream consumer of the Shared Database

2. **Shared analytics backend service**
   - Invoked by visualization and operational layers (e.g., `DashboardBuilder`)
   - Provides analytics results as intermediate artifacts for downstream visualization
   - Does not alter or re-route Shared Database contents

In both modes:
- `AnalyticsOrchestrator` remains **read-only** with respect to the Main Shared Database
- All persisted outputs are explicitly versioned and isolated within its own output directories

---

## Data Flow Summary

```plaintext
    Data Collection → Data Loader → Shared Database (9 files)
                                          ↓
        ┌─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┐
        |                                 |                                                                             |
        ↓                                 ↓                                                                             ↓
ValidationOrchestrator      MoldMachineFeatureWeightCalculator                                                    DashboardBuilder
        ↓                     + MoldStabilityIndexCalculator                                                            ↓ (reads Shared DB)
  Validation Report            (Data Insights Generator)                                                 AnalyticsOrchestrator (Shared)
        | (cross-ref                      |                                                ┌────────────────────────────┴───────────────────────────┐
        |  if exists)                     ↓                                                ↓                                                        ↓
        └──> OrderProgress ─────→ ProducingProcessor                            HardwareChangeAnalyzer                                 MultiLevelPerformanceAnalyzer
          (reads Shared DB)               ↓                                                ↓ (reads Shared DB)                                      ↓ (reads Shared DB)
                   ↓               PendingProcessor                      HardwareChangeVisualizationService                       MultiLevelPerformanceVisualizationService
             Status Reports               ↓                                                                             ↓
            (with validation       Production Plans                                            Hardware Change & Multi-Level Performance Dashboards
             flags)                (Initial Plan)                           
```

---

## What This Document Intentionally Excludes

The following are **out of scope** for the Shared Database specification and are documented in the framework/module layer:

* Algorithmic strategies and optimizers
* Internal execution graphs within agents
* Output file schemas (sheets, columns, metrics)
* Dashboard layout, pagination, and visualization details
* Auto-configuration propagation rules

> See: `OptiMoldIQ-framework.md` for module contracts and execution semantics.

---

## Role in Milestone 03

The Shared Database finalizes **data contracts and execution boundaries**, enabling:

* Stable agent interfaces
* Deterministic execution
* Safe framework formalization in Milestone 04

Milestone 03 is considered complete once this contract is stable and validated across agents.
