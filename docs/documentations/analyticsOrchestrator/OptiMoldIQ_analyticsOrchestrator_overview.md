# AnalyticsOrchestrator

## 1. Agent Info
- **Name**: AnalyticsOrchestrator
- **Purpose**: 
The AnalyticsOrchestrator module coordinates multiple analytics submodules for manufacturing data processing, tracking, and historical updates.
- **Owner**: 
- **Status**: Active
- **Location**: `agents/analyticsOrchestrator/`

---

## 2. What it does
  
- It mainly consists of two functional groups:
    - `dataChangeAnalyzer` – focuses on change detection and history tracking.
    - `multiLevelDataAnalytics` – handles time-level (day/month/year) data summarization and aggregation.
- Integration Flow:
```
┌──────────────────────────────────┐
│ `dataChangeAnalyzer`             │
│  ├─ `MachineLayoutTracker`       |
│  ├─ `MachineMoldPairTracker`     |
│  ├─ `UpdateHistMachineLayout`    |
│  └─ `UpdateHistMoldOverview`     |
└─────────────┬────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│ `multiLevelDataAnalytics`        │
│  ├─ `DayLevelDataProcessor`      |
│  ├─ `MonthLevelDataProcessor`    |
│  └─ `YearLevelDataProcessor`     |
└──────────────────────────────────┘
```
---
## 3. Functional groups details
- ([dataChangeAnalyzer](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/dataChangeAnalyzer/OptiMoldIQ_dataChangeAnalyzer_overview.md)):

    - Orchestrate and coordinate the detection of data changes in production records, specifically tracking machine layout changes and machine-mold pair relationships over time.
    - Provide intelligent parallel or sequential processing based on system resource availability.
    - Serve as the main entry point for change analysis workflows.

- **multiLevelDataAnalytics**:
  
  - Handles three time-level including `DayLevelDataProcessor`, `MonthLevelDataProcessor`, and `YearLevelDataProcessor` for data summarization and aggregation.

    - ([DayLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_dayLevelDataProcessor_overview.md)):

      - Process and analyze daily production records to generate comprehensive reports on manufacturing operations.
      - Aggregate production data by mold and item to track performance metrics.
      - Classify production changes (mold changes, color changes, machine idle states).
      - Calculate defect rates and efficiency metrics across machines, shifts, and products.

    - ([MonthLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_monthLevelDataProcessor_overview.md)):

      - Analyze monthly manufacturing operations and purchase order fulfillment status.
      - Track backlog orders from previous months and assess their impact on current production.
      - Estimate production capacity based on mold specifications and historical usage.
      - Detect capacity constraints and identify orders at risk of delay.
      - Classify order status (finished, in-progress, not-started) and timeliness (ontime, late).

    - ([YearLevelDataProcessor](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_yearLevelDataProcessor_overview.md)):

      - Analyze yearly manufacturing operations and purchase order fulfillment status.
      - Track backlog orders from previous years and assess their impact on current production.
      - Estimate production capacity based on mold specifications and historical usage.
      - Detect capacity constraints and identify orders at risk of delay.
      - Classify order status (finished, in-progress, not-started) and timeliness (ontime, late).
