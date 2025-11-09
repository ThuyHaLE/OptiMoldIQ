# DashboardBuilder

## 1. Overview
- The `dashboardBuilder` module is a multi-level analytics and visualization system designed to generate production intelligence dashboards at daily, monthly, and yearly resolutions. It provides a unified pipeline that extracts, validates, aggregates, and visualizes factory production records (machine, mold, item, and PO-based data) into structured analytical outputs.
- This module is optimized for large-scale automated reporting, parallel plotting, and historical tracking, enabling real-time monitoring and long-term performance analysis.

## 2. System Purpose
`dashboardBuilder` provides automated end-to-end generation of production dashboards with three complementary analytical scopes:
- Daily insight → Operational troubleshooting & short-term performance check
- Monthly tracking → PO progress monitoring, risk alerts, efficiency evaluation
- Yearly trends → Historical patterns, seasonal behaviors, and long-term capacity planning
Each level contains its own processing logic, visualization set, and reporting structure, but all share a unified data pipeline and configuration model.

## 3. Core Responsibilities of dashboardBuilder
Across all three plotters, the system provides:

### 3.1 Unified Data Processing Pipeline
- Load raw production or PO data from DataLoaderAgent outputs
- Apply schema validation and safe type handling
- Normalize time-based fields (day, month, year)
- Create aggregated machine-, mold-, and item-level datasets
- Compute efficiency, completion, and utilization metrics

### 3.2 Automatic Dashboard Generation
Depending on level (day/month/year), the engine generates from 3 to 9+ dashboard types, including:
- Yield and scrap overviews
- Machine efficiency and status analysis
- Mold performance and shot-count distribution
- Item-level QC and production metrics
- Monthly trend lines, backlog evolution, and PO completion
- Annual aggregates and long-term patterns

### 3.3 Parallel Visualization Execution
- Optional multiprocessing for handling heavy workloads
- Auto selection of worker count based on system hardware
- Graceful fallback to sequential execution

### 3.4 Output Management & File Tracking
- Auto-generated filenames with timestamp versioning
- Historical file archiving (historical_db/)
- Comprehensive change log tracking:
  - created files
  - overridden versions
  - update timestamps
- Excel exports with multi-sheet structured outputs
- Text-based summary reports (for month/year analytics)

## 4. Components Overview
### 4.1 Day-Level Integration

#### Overview

- *Flow*:`DayLevelDataProcessor` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_dayLevelDataProcessor_overview.md)) → `DayLevelDataPlotter` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_dayLevelDataPlotter_overview.md))   

- `DayLevelDataProcessor`
  - *Scope*: Daily production record analysis
  - *Use case*: Real-time machine/mold/item operations and shift-level performance.
  - *Key Functions*
    - Filter records by the selected date (or auto-detect latest available)
    - Merge production records with purchase orders
    - Build composite fields (machineInfo, itemInfo, itemComponent)
    - Compute key metrics:
      - output quantities
      - defect rates
      - job counts
      - late/on-time delivery checks
    - Classify production change events
    - Generate:
      - mold-based aggregated datasets
      - item-based aggregated datasets
      - daily operation summary statistics

- `DayLevelDataPlotter`
  - *Scope*: Single-day production analysis
  - *Use case*: Real-time operational monitoring, troubleshooting anomalies, validating per-shift or per-machine performance.
  - *Key Functions*
    - 8 visualizations (yield, change time, mold overview, item overview, etc.)
    - Generate machine-, mold-, and item-based datasets
    - Export 4-sheet Excel (raw & processed daily records)
    - Parallel plotting with check for system capability

#### Processor Responsibilities
- Load daily production records
- Filter or auto-detect valid record date
- Merge production records with purchase orders
- Generate enriched fields (machineInfo, itemInfo, itemComponent)
- Compute metrics: output quantity, scrap, shift performance
- Classify change events (mold change, color change, idle)
- Produce:
  - merged_df
  - mold_based_record_df
  - item_based_record_df
  - daily summary statistics

#### Plotter Consumption
`DayLevelDataPlotter` uses the processed datasets to generate 8 visualization types, including:
- Mold-based & item-based dashboards
- Machine-level performance
- Yield, scrap, change-time charts
- Daily overview dashboards

It also exports:
- 4-sheet Excel (daily processed records)
- PNG dashboards
- Change logs + historical archive

#### Integration Summary
The `DayLevelDataProcessor` prepares everything needed for visualization—clean, aggregated, and validated per-day analytics—while the `DayLevelDataPlotter` focuses solely on rendering visual reports and structuring export files.

### 4.2 Month-Level Integration
#### Overview

- *Flow*:`MonthLevelDataProcessor` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_monthLevelDataProcessor_overview.md)) → `MonthLevelDataPlotter` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_monthLevelDataPlotter_overview.md)) 

- `MonthLevelDataProcessor`
  - *Scope*: Monthly PO and production fulfillment analysis
  - *Use case*: Monitoring monthly workload, backlog, ETA risk, and capacity constraints.
  - *Key Functions*
    - Load & validate product records, purchase orders, mold info, and technical specs
    - Validate analysis date and record month (auto-adjust if needed)
    - Identify backlog POs from previous months
    - Compute fulfillment status (finished / in-progress / not-started)
    - Calculate remaining quantities and progress for unfinished orders
    - Estimate production capacity using:
      - cavity count
      - cycle time
      - mold availability
    - Detect overcapacity risk and potential late orders
    - Generate:
      - finished and unfinished PO datasets
      - adjusted month metadata
      - consolidated monthly summary

- `MonthLevelDataPlotter`
  - *Scope*: Monthly Purchase Order (PO) performance analysis
  - *Use case*: Production control, delivery risk management, backlog monitoring.
  - *Key Functions*
    - 3 main dashboards (month performance, machine-based, mold-based)
    - Finished vs unfinished PO tracking
    - Early warning system (capacity alerts, ETA risk detection)
    - 5-sheet Excel output (finished, unfinished, progress, etc.)
    - Text summary + early warning TXT report
    - Historical archiving & file version control

#### Processor Responsibilities
- Validate analysis date and target record month
- Identify backlog orders from previous months
- Merge PO + production records
- Compute:
  - finished / unfinished / not-started orders
  - on-time vs late delivery
  - progress % and remaining quantities
- Perform capacity estimation using mold technical specs
- Detect mold overloading and delivery risk
- Output:
  - validated timestamps
  - finished_df
  - unfinished_df (with risk flags + capacity metrics)
  - short- and full summaries

#### Plotter Consumption
- MonthLevelDataPlotter uses the processor outputs to generate:
- Month performance dashboard (PO-based)
- Machine-based monthly dashboard
- Mold-based monthly dashboard
- Early warning reports
- Excel with 5 structured sheets
- Historical file versioning

#### Integration Summary
The `MonthLevelDataProcessor` handles business logic, capacity modeling, and risk detection, while the `MonthLevelDataPlotter` converts those insights into visual form and distribution-ready reports.

### 4.3 Year-Level Integration
#### Overview

- *Flow*:`YearLevelDataProcessor` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/analyticsOrchestrator/multiLevelDataAnalytics/OptiMoldIQ_yearLevelDataProcessor_overview.md)) → `YearLevelDataPlotter` ([→ see detail](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/docs/documentations/dashboardBuilder/OptiMoldIQ_yearLevelDataPlotter_overview.md)) 

- `YearLevelDataProcessor`
  - *Scope*: Annual PO processing, backlog tracking, and capacity analysis
  - *Use case*: Year-round strategic planning and performance review.
  - *Key Functions*
    - Validate record year and analysis date
    - Load production/PO datasets + mold technical information
    - Detect carry-over backlog from previous years
    - Track year-wide completion and delay patterns
    - Compute production progress, remaining quantities, and delay risk
    - Estimate year-capacity and mold utilization pressure
    - Generate:
      - finished PO dataset
      - unfinished PO dataset with capacity risk evaluation
      - validated year parameters
      - annual summary report

- `YearLevelDataPlotter`
  - *Scope*: Year-wide PO performance, trends, and historical analysis
  - *Use case*: Capacity planning, annual review, management reporting.
  - *Key Functions*
    - 9+ dashboards (monthly trends, year performance, machine/mold year view, month-view deep dives)
    - Seasonal pattern detection & long-term backlog evolution
    - Machine/mold year-view analytics across 12 months
    - Multi-page plots for detailed month-view fields
    - 5-sheet Excel + annual summary TXT report
    - Optimized parallel execution for heavy visualization workload

#### Processor Responsibilities
- Validate year and cutoff analysis date
- Identify backlog orders from previous years
- Merge annual PO + production records
- Compute:
  - annual completion trends
  - late vs on-time performance
  - unfinished orders and remaining quantities
- Estimate annual capacity (cycle time, cavity count, mold limits)
- Generate:
  - finished_df
  - unfinished_df (risk + capacity analysis)
  - validated year fields
  - annual summary

#### Plotter Consumption
`YearLevelDataPlotter` builds 9+ dashboards including:
- month trends
- year performance
- machine-based year view
- mold-based year view
- detailed month-view multi-page dashboards

It exports:
- 5-sheet annual Excel
- TXT summary
- Large dashboard set (multi-page)
- Archived historical outputs

#### Integration Summary

The `YearLevelDataProcessor` prepares long-range, aggregated annual datasets, while the `YearLevelDataPlotter` focuses on producing trend dashboards and multi-page analytical visuals for management-level review.

## 5. Integration Summary Table
| Level     | DataProcessor                                                             | DataPlotter                                                      | Relationship                                                         |
| --------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Day**   | Prepares daily production metrics, classifications, and aggregated tables | Creates daily dashboards (8 plots), Excel, logs                  | Plotter requires all processed DataFrames from Processor             |
| **Month** | Computes PO progress, backlog, capacity risks, finished/unfinished status | Generates monthly dashboards (3 plots), early warning TXT, Excel | Plotter fully depends on Processor’s PO logic & risk detection       |
| **Year**  | Performs annual aggregation, backlog, capacity estimation, trend analysis | Produces annual dashboards (9+ plots), summary TXT, Excel        | Plotter visualizes long-term patterns from Processor’s annual models |

## 6. System Architecture
    ```
                           ┌───────────────────────────────────────────────┐
                           │                Raw Data Sources               │
                           │  (Production Records, Purchase Orders,        │
                           │         Mold Info, Additional Inputs)         │
                           └───────────────────────────────────────────────┘
                                            │
               ┌────────────────────────────┼───────────────────────────────┐
               │                            │                               │
               ▼                            ▼                               ▼
     DayLevelDataProcessor      MonthLevelDataProcessor         YearLevelDataProcessor
               │                            │                               │
               │                            │                               │
               ▼                            ▼                               ▼
     DayLevelDataPlotter        MonthLevelDataPlotter           YearLevelDataPlotter
               │                            │                               │
               ▼                            ▼                               ▼
     Daily Dashboards &         Monthly Dashboards,               Yearly Dashboards,
           Reports             Early Warnings, Reports          Multi-page Reports

    ─────  : Data flows from one step to the next
    ▼      : Transformation or processing stage
    │      : Hierarchical/vertical dependency

    ```

## 7. High-level Summary
Each Processor–Plotter pair forms a complete reporting pipeline:
- DataProcessor = “Analysis Engine”
  - Performs validation, merging, enrichment, capacity modeling, classification, aggregation.
- DataPlotter = “Visualization Layer”
  - Converts processed data into dashboards, Excel reports, warning summaries, and archives.

Together, they form the end-to-end automated reporting system for daily, monthly, and yearly production intelligence.