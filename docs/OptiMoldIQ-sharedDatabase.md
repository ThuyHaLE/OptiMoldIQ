# Shared Database

**Location:** `agents/shared_db/`

## Directory Structure

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

### Key Integration Points:

**Orchestrators vs Output Folders:**
- Some folders represent **output locations** (e.g., `UpdateHistMachineLayout`, `UpdateHistMoldOverview`)
- The actual **orchestrator/agent names** may differ (e.g., `DataChangeAnalyzer` coordinates multiple plotter folders)
- See section below for full orchestrator → output mapping

```
**Orchestrators vs Output Folders:**

    Orchestrator/Agent Name    → Output Folder(s)
    ───────────────────────────────────────────────────
    DataPipelineOrchestrator   → DataPipelineOrchestrator/newest/
                               → DataLoaderAgent/newest/

    DataChangeAnalyzer         → UpdateHistMachineLayout/newest/
                               → UpdateHistMoldOverview/newest/

    ProducingProcessor         → ProducingProcessor/newest/
      ↳ invokes: HybridSuggestOptimizer (internal)

    PendingProcessor         → PendingProcessor/newest/
      ↳ invokes: HistBasedMoldMachineOptimizer (internal)
      ↳ invokes: CompatibilityBasedMoldMachineOptimizer (internal)
      ↳ invokes: MachineAssignmentProcessor (internal)

    HardwareChangePlotter         → HardwareChangePlotter/newest/
      ↳ invokes: AnalyticsOrchestrator (internal)

    MultiLevelPerformancePlotter  → MultiLevelPerformancePlotter/newest/
      ↳ invokes: AnalyticsOrchestrator (internal) 

Note: Other modules output directly to their own folders
(e.g., ValidationOrchestrator → ValidationOrchestrator/newest/)
```

**Folder Naming:**
- `newest/` = symbolic link to latest timestamped output
- `*_` prefix = timestamp format YYYYMMDD_HHMM_

**Data Sources:**
- **Data Loader** feeds from Data Collection to create Main Shared Database (9 files)

**Cross-Module Dependencies:**
- **Validation** → Order Progress Tracking (optional cross-reference)
- **Data Insights Generator** → Production Processing (required inputs)
- **Order Progress** → Production Processing (required inputs)
- **Producing Processor** → Pending Processor (sequential pipeline)

**Data Consumers:**
- **ValidationOrchestrator** reads Main Shared Database
- **OrderProgressTracker** reads Main Shared Database + Validation results
- **Data Insights Generator** reads Main Shared Database
- **DataChangeAnalyzer** reads Main Shared Database for historical change analysis
- **DashboardBuilder** reads Main Shared Database for performance analysis and visualization
  
---

## Database Files

### Main Shared Database

#### **Dynamic DB Collection** (2 files)
Updated regularly with new production data:
- `*_productRecords.parquet` - Historical product records
- `*_purchaseOrders.parquet` - Historical purchase orders

#### **Static DB Collection** (6 files)
Reference data with infrequent updates:
- `*_itemCompositionSummary.parquet` - Item composition details
- `*_itemInfo.parquet` - Product item specifications
- `*_machineInfo.parquet` - Machine specifications
- `*_moldInfo.parquet` - Mold specifications
- `*_moldSpecificationSummary.parquet` - Mold specification summaries
- `*_resinInfo.parquet` - Resin material information

#### **Metadata File** (1 file)
Database configuration and path references:
- `path_annotations.json` - Contains all paths of main shared database

> **Naming Convention:** `*_` prefix represents timestamp in format YYYYMMDD_HHMM_ (e.g., 20241113_1430_itemInfo.parquet)

---

## 📋 System Reports & Visualizations

### 1. Data Pipeline Reports

#### **DataPipelineOrchestrator** (2 folders, 11 files)
Coordinates Data Collection and DataLoaderAgent to produce the main shared database, then saves execution logs:

- **Main Shared Database** (9 files, located in `DataLoaderAgent/newest/`):
  - Static DB Collection (6 files) - Reference data
  - Dynamic DB Collection (2 files)  - Production data
  - `path_annotations.json` (1 file) - Path metadata
  
- **Execution logs** (3 files, located in `DataPipelineOrchestrator/newest/`):
  - `*_DataCollector_success_report.txt` or `*_DataCollector_failed_report.txt`
  - `*_DataLoaderAgent_success_report.txt` or `*_DataLoaderAgent_failed_report.txt`
  - `*_DataPipelineOrchestrator_final_report.txt`

#### **ValidationOrchestrator** (1 file)
Performs validation checks directly on the **Main Shared Database** (located in `DataLoaderAgent/newest/`) and outputs:

- `*_validation_orchestrator.xlsx` → Validation results


#### **OrderProgressTracker** (1 file)
Tracks production and order status based on the **Main Shared Database** (from `DataLoaderAgent/newest/`), 
Note: If **Validation results** (from `ValidationOrchestrator/newest/`) exist, they will be cross-referenced to flag potential issues.

- `*_auto_status.xlsx` → Order status report with validation flags (if applicable)

### 2. Production Planning Reports

#### Historical Data Insights
Generates data insights from historical records, including:

**MoldMachineFeatureWeightCalculator** (2 files)  
Generates compatibility scoring between molds and machines:
- `newest/*_confidence_report.txt` → Confidence metrics  
- `weights_hist.xlsx` → Historical weight calculations  
    
**MoldStabilityIndexCalculator** (1 file)  
Calculates mold performance stability:
- `*_mold_stability_index.xlsx`

#### Initial Production Plan

**ProducingProcessor** (1 file)  

Invokes `HybridSuggestOptimizer` using outputs from `Data Insights Generator` to:  
  1. Estimate mold capacity based on the computed `mold stability index`
  2. Calculate the `mold–machine priority matrix` by combining:
     - the `estimated mold capacity`, and
     - the `mold–machine feature weight`

Then combines results from `OrderProgressTracker` with `estimated mold capacity` from `HybridSuggestOptimizer` to generate production planning for active POs (e.g., estimate lead time, coordinate material requirements).

Finally, produces a unified report set that serves as input for the next planning stage handled by `PendingProcessor` (for pending POs).

**Output:**
- `*_producing_processor.xlsx` → Multi-sheet active production report

**Sheet breakdown:**
- **Historical insights** (from HybridSuggestOptimizer):
  - `mold_machine_priority_matrix` → Mold-machine compatibility matrix
  - `mold_estimated_capacity_df` → Estimated mold production capacity

- **Production planning for active POs:**
  - `producing_status_data` → Current production status
  - `producing_pro_plan` → Production schedule plan
  - `producing_mold_plan` → Mold allocation plan
  - `producing_plastic_plan` → Material requirements plan
  - `pending_status_data` → Pending order status

- **Validation:**
  - `invalid_molds` → Mold validation issues

---

**PendingProcessor** (1 file)  

Invokes `MachineAssignmentProcessor` to generate initial production plan suggestions for both producing and pending POs using two-tier optimization strategy:
  1. **Primary optimization** (history-based): `HistBasedMoldMachineOptimizer` optimizes mold–machine assignments based on historical insights and active production planning from `ProducingProcessor`
  2. **Fallback optimization** (compatibility-based): `CompatibilityBasedMoldMachineOptimizer` handles unassigned molds using compatibility scoring

**Optimization workflow:**
```
Historical insights + Active production planning → HistBasedMoldMachineOptimizer ─────┐                             
                                                                                      ├──→ MachineAssignmentProcessor ─→ PendingProcessor
Compatibility scoring (for unassigned molds) → CompatibilityBasedMoldMachineOptimizer ┘
```

**Output:**
- `*_pending_processor.xlsx` → Suggested production plan

**Sheet breakdown:**
- **Historical insights** (from ProducingProcessor via HybridSuggestOptimizer):
  - `mold_machine_priority_matrix` → Mold-machine compatibility matrix
  - `mold_estimated_capacity_df` → Estimated mold production capacity

- **Initial planning for all POs:**
  - `initialPlan` → Unified production plan for active + pending orders

- **Validation:**
  - `invalid_molds` → Mold validation issues

---

**Overall Flow:**
```
Data Insights Generator (`mold–machine feature weight` + `mold stability index`)────┐
                                                                                    ├──→ ProducingProcessor
OrderProgressTracker (`production status`)──────────────────────────────────────────┘            ↓ 
                                                                                        (active production analysis)
                                                                                                  ↓
                                                                                           PendingProcessor
                                                                                                  ↓ 
                                                                                        (production plan suggestion)
                                                                                                  ↓
                                                                                     Initial production plan suggestion
```

### 3. Hardware Change & Multi-level performance Reports and Static Dashboards

#### Dashboard Builder

The `Dashboard Builder` acts as a coordinating pipeline that provides comprehensive analytics and visualization capabilities through two main plotters:
- **HardwareChangePlotter**: Tracks and visualizes hardware changes over time
- **MultiLevelPerformancePlotter**: Analyzes and visualizes production performance at multiple time granularities
Both plotters share the **AnalyticsOrchestrator** component for coordinated analysis workflows.

**1. HardwareChangePlotter**: coordinates hardware change analysis and visualization. It can invoke one or both subordinate modules—`MachineLayoutPlotter` and `MachineMoldPairPlotter`—depending on configuration. Trigger **AnalyticsOrchestrator** to analyzes machine layout evolution over time to identify layout changes and activity patterns (**MachineLayoutTracker**) and machine-mold relationships, first-run history, and pairing patterns (**MachineMoldPairTracker**). Then visualizes layout change patterns and machine activity (**MachineLayoutPlotter**) and mold-machine relationships, tonnage distribution, and utilization patterns (**MachineMoldPairTracker**).

**Key capabilities:**
- **Invocation flexibility**: Users can run layout tracking only, mold pairing only, or both simultaneously
- **Data orchestration**: Coordinates with `AnalyticsOrchestrator` → `HardwareChangeAnalyzer` → specific Trackers
- **Historical tracking**: Maintains change history in JSON format for timeline analysis

**Output:**

**MachineLayoutTracker outputs** (in `MachineLayoutTracker/newest/`): (2 files)
- `*_machine_layout_changes_YYYY-MM-DD.json` → Structured change records
- `*_machine_layout_changes_YYYY-MM-DD.xlsx` → Human-readable change log

**MachineLayoutPlotter outputs** (in `MachineLayoutPlotter/newest/`): (2 files)
- `*_Machine_layout_change_dashboard.png` → Overall layout change timeline
- `*_Individual_machine_layout_change_times_dashboard.png` → Per-machine change frequency

**MachineMoldPairTracker outputs** (in `MachineMoldPairTracker/newest/`): (3 files)
- `*_mold_machine_pairing_YYYY-MM-DD.xlsx` → Complete pairing history
- `*_mold_machine_pairing_summary_YYYY-MM-DD.txt` → Executive summary
- `pair_changes/YYYY-MM-DD_mold_machine_pairing_YYYY-MM-DD.json` → Daily tracking snapshots

**MachineMoldPairPlotter outputs** (in `MachineMoldPairPlotter/newest/`): (3 files)
- `*_Mold_machine_first_pairing_dashboard.png` → First-run pairing analysis
- `*_Mold_utilization_dashboard.png` → Mold usage patterns
- `*_Machine_tonage_based_mold_utilization_dashboard.png` → Tonnage-based analysis

**2. MultiLevelPerformancePlotter**: coordinates multi-level performance analysis. It can invoke one, two, or all three subordinate modules—`DayLevelPlotter`, `MonthLevelPlotter`, and `YearLevelPlotter`—depending on the analysis scope. Trigger **AnalyticsOrchestrator** to processes daily production data for the specified date and extracts key metrics (**DayLevelDataProcessor**), monthly production data and aggregates performance metrics (**MonthLevelDataProcessor**) and yearly production data and consolidates annual insights (**YearLevelDataProcessor**). Then visualizes daily production performance across multiple dimensions (**DayLevelDataPlotter**), generates monthly performance dashboards, alerts, and executive summaries (**MonthLevelDataPlotter**) and generates comprehensive annual dashboards with multi-page detailed breakdowns (**YearLevelDataPlotter**).

**Key capabilities:**
- **Invocation flexibility**: Users can run daily, monthly, yearly analysis independently or in combination
- **Data orchestration**: Coordinates with `AnalyticsOrchestrator` → `MultiLevelPerformanceAnalyzer` → specific Processors
- **Consistent metrics**: Ensures uniform KPIs across all time granularities

**Important architecture note:** Each level consists of TWO components:
1. **DataProcessor**: Extracts and analyzes data, outputs structured insights (XLSX + TXT)
2. **DataPlotter**: Visualizes processed data, generates dashboards (PNG)

**Output:**

**DayLevelDataProcessor outputs** (in `DayLevelDataProcessor/newest/`): (2 files)
- `*_day_level_insights_YYYY-MM-DD.xlsx` → Structured daily metrics
- `*_day_level_summary_YYYY-MM-DD.txt` → Executive daily summary

**DayLevelDataPlotter outputs** (in `DayLevelDataPlotter/newest/`): (8 files)
- `*_item_based_overview_dashboard_YYYY-MM-DD.png` → Item-level performance overview
- `*_mold_based_overview_dashboard_YYYY-MM-DD.png` → Mold-level performance overview
- `*_shift_level_yield_efficiency_chart_YYYY-MM-DD.png` → Shift-level yield efficiency
- `*_shift_level_mold_efficiency_chart_YYYY-MM-DD.png` → Shift-level mold efficiency
- `*_shift_level_detailed_yield_efficiency_chart_YYYY-MM-DD.png` → Detailed shift efficiency breakdown
- `*_machine_level_yield_efficiency_chart_YYYY-MM-DD.png` → Machine yield efficiency
- `*_machine_level_mold_analysis_chart_YYYY-MM-DD.png` → Machine-mold performance analysis
- `*_change_times_all_types_fig_YYYY-MM-DD.png` → All changeover types analysis

**MonthLevelDataProcessor outputs** (in `MonthLevelDataProcessor/newest/`): (2 files)
- `*_day_level_insights_YYYY-MM.xlsx` → Daily metrics aggregated by month
- `*_day_level_summary_YYYY-MM.txt` → Monthly summary with daily breakdowns

**MonthLevelDataPlotter outputs** (in `MonthLevelDataPlotter/newest/`): (6 files)
- `*_early_warning_report_YYYY-MM.txt` → Performance alerts and anomalies
- `*_final_summary_YYYY-MM.txt` → Executive monthly summary
- `*_extracted_records_YYYY-MM.xlsx` → Detailed monthly records extract
- `*_month_performance_dashboard_YYYY-MM.png` → Overall monthly performance
- `*_machine_based_dashboard_YYYY-MM.png` → Machine-level performance
- `*_mold_based_dashboard_YYYY-MM.png` → Mold-level performance

**YearLevelDataProcessor outputs** (in `YearLevelDataProcessor/newest/`): (2 files)
- `*_year_level_insights_YYYY.xlsx` → Structured yearly metrics
- `*_year_level_summary_YYYY.txt` → Executive yearly summary

**YearLevelPlotter** 
Generates comprehensive annual dashboards with multi-page detailed breakdowns.

**YearLevelDataPlotter outputs** (in `YearLevelDataPlotter/newest/`): (11 files)
- `*_final_summary_YYYY.txt` → Annual executive summary
- `*_extracted_records_YYYY.xlsx` → Complete yearly records extract
- `*_year_performance_dashboard_YYYY.png` → Annual overview
- `*_monthly_performance_dashboard_YYYY.png` → Month-by-month trends
- `*_machine_based_year_view_dashboard_YYYY.png` → Machine annual view
- `*_mold_based_year_view_dashboard_YYYY.png` → Mold annual view
- `*_machine_po_item_dashboard_YYYY_page1.png` → Machine PO/item breakdown (page 1)
- `*_machine_po_item_dashboard_YYYY_page2.png` → Machine PO/item breakdown (page 2)
- `*_machine_quantity_dashboard_YYYY_page1.png` → Machine quantity analysis (page 1)
- `*_machine_quantity_dashboard_YYYY_page2.png` → Machine quantity analysis (page 2)
- `*_machine_working_days_dashboard_YYYY_page1.png` → Machine utilization (page 1)
- `*_machine_working_days_dashboard_YYYY_page2.png` → Machine utilization (page 2)
- `*_mold_quantity_dashboard_YYYY_page1-4.png` → Mold quantity analysis (4 pages)
- `*_mold_shots_dashboard_YYYY_page1-4.png` → Mold shot count analysis (4 pages)

> **Note:** Multi-page outputs contain multiple visualizations for comprehensive breakdowns. Page numbers are appended to filenames (e.g., `_page1.png`, `_page2.png`).

**Auto-Configuration Propagation**

```
DashboardBuilder (parent config)
    │
    ├─ enable_hardware_change_plotter = True
    │     ↓ (auto-propagates)
    │  HardwareChangePlotflowConfig.enable_machine_layout_plotter = True
    │  HardwareChangePlotflowConfig.enable_machine_mold_pair_plotter = True
    │     ↓ (auto-propagates)
    │  AnalyticsOrchestratorConfig.enable_hardware_change_analysis = True
    │     ↓ (auto-propagates)
    │  ChangeAnalyticflowConfig.enable_machine_layout_tracker = True
    │  ChangeAnalyticflowConfig.enable_machine_mold_pair_tracker = True
    │
    └─ enable_multi_level_plotter = True
          ↓ (auto-propagates)
       PerformancePlotflowConfig.enable_day_level_plotter = True
       PerformancePlotflowConfig.enable_month_level_plotter = True
       PerformancePlotflowConfig.enable_year_level_plotter = True
          ↓ (auto-propagates)
       AnalyticsOrchestratorConfig.enable_multi_level_analysis = True
          ↓ (auto-propagates)
       PerformanceAnalyticflowConfig.enable_day_level_processor = True
       PerformanceAnalyticflowConfig.enable_month_level_processor = True
       PerformanceAnalyticflowConfig.enable_year_level_processor = True
```

> **Note:** Manual config settings are overridden by auto-configuration. Check logs for propagation details.

**Overall Flow:**
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

#### Summary of all five levels for consistency check:

| Level  | Total Files | Processing | Reports | Visualizations |
|--------|-------------|------------|---------|----------------|
| Machine| 4           | 2          | 2       | 2              |
| Mold   | 6           | 2          | 3       | 3              |
| Day    | 11          | 2          | 2       | 8              |
| Month  | 8           | 2          | 2+3     | 3              |
| Year   | 12+         | 2          | 2+2     | 8+             |

---

## Data Flow Summary

```
    Data Collection → Data Loader → Shared Database (9 files)
                                          ↓
        ┌─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┐
        |                                 |                                                                             |
        ↓                                 ↓                                                                             ↓
    ValidationOrch            MoldMachineFeatureWeightCalculator                                                DashboardBuilder
        ↓                     + MoldStabilityIndexCalculator                               ┌────────────────────────────┴───────────────────────────┐
    Validation Report            (Data Insights Generator)                                 ↓                                                        ↓
        | (cross-ref                      |                                     HardwareChangePlotter                                 MultiLevelPerformancePlotter
        |  if exists)                     ↓                                                ↓                                                        ↓
        └──> OrderProgress ─────→ ProducingProcessor                        AnalyticsOrchestrator (Shared)                           AnalyticsOrchestrator (Shared)
           (reads Shared DB)              ↓                                                ↓                                                        ↓
                   ↓               PendingProcessor                            HardwareChangeAnalyzer                                 MultiLevelPerformanceAnalyzer
             Status Reports               ↓                                         ┌──────┴──────┐                                      ┌──────────┼──────────┐
            (with validation       Production Plans                                 ↓             ↓                                      ↓          ↓          ↓
             flags)                (Initial Plan)                             MachineLayout  MachineMoldPair                          DayLevel    MonthLevel  YearLevel
                                                                              Tracker        Tracker                                  Processor   Processor   Processor
                                                                                    ↓             ↓                                      ↓          ↓          ↓
                                                                              Returns to     Returns to                               Returns to  Returns to  Returns to
                                                                              Plotter        Plotter                                  Plotter     Plotter     Plotter
                                                                                    ↓             ↓                                      ↓          ↓          ↓
                                                                              MachineLayout  MachineMoldPair                          DayLevel    MonthLevel  YearLevel
                                                                              Plotter        Plotter                                  Plotter     Plotter     Plotter
                                                                                    ↓             ↓                                      ↓          ↓          ↓
                                                                              Layout         Mold Pairing                             Daily       Monthly     Yearly
                                                                              Visualizations Visualizations                           Dashboards  Dashboards  Dashboards
                                                                                                                          ↓
                                                                                                Hardware Change & Multi-Level Performance Dashboards
```