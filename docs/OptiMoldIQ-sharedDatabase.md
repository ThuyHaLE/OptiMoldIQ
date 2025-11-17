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
# HISTORICAL ANALYTICS
# ══════════════════════════════════════════════════════════════════
├── DataChangeAnalyzer/
|   ├── UpdateHistMachineLayout/newest/         # Machine layout change analysis (4 files)
│   │   ├── *_Machine_change_layout_timeline.png
│   │   ├── *_Machine_level_change_layout_details.png
│   │   ├── *_Machine_level_change_layout_pivot.xlsx
│   │   └── *_Top_machine_change_layout.png
│   └── UpdateHistMoldOverview/newest/          # Mold usage & performance history (11 files)
│       ├── *_Bottom_molds_tonnage.png
│       ├── ... (9 more visualization files)
│       └── *_Top_molds_tonnage.png
│
# ══════════════════════════════════════════════════════════════════
# MULTI-LEVEL PERFORMANCE DASHBOARDS
# ══════════════════════════════════════════════════════════════════
└── MultiLevelDataPlotter
    ├── DayLevelDataPlotter/newest/             # Daily dashboards & reports (9 files)
    ├── MonthLevelDataPlotter/newest/           # Monthly dashboards & reports (6 files)
    └── YearLevelPlotter/newest/                # Annual dashboards & reports (11 files)

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

    DayLevelDataPlotter        → DayLevelDataPlotter/newest/
      ↳ invokes: DayLevelDataProcessor (internal)

    MonthLevelDataPlotter      → MonthLevelDataPlotter/newest/
      ↳ invokes: MonthLevelDataProcessor (internal)

    YearLevelPlotter           → YearLevelPlotter/newest/
      ↳ invokes: YearLevelDataProcessor (internal)

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
- **DayLevelPlotter**/**MonthLevelPlotter**/**YearLevelPlotter** reads Main Shared Database for performance visualization
  
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

### 3. Historical Machine Layout Change Reports & Machine-Mold First-Run History Reports

#### **DataChangeAnalyzer** (2 folders, total 15 files)
Coordinates and executes historical change analyses using `UpdateHistMachineLayout` and `UpdateHistMoldOverview` for both machines and molds. It processes data from the **Main Shared Database** and outputs visualizations and analytical reports through two modules:

- *UpdateHistMachineLayout* (4 files): Analyzes machine layout evolution over time to identify layout changes and activity patterns:
  - `*_Machine_change_layout_timeline.png` → Machine layout change timeline
  - `*_Machine_level_change_layout_details.png` → Detailed layout change breakdown
  - `*_Machine_level_change_layout_pivot.xlsx` → Pivot analysis of layout changes
  - `*_Top_machine_change_layout.png` → Machines with most frequent layout updates

- *UpdateHistMoldOverview* (11 files): Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends:
  - `*_Bottom_molds_tonnage.png` → Low-tonnage mold analysis  
  - `*_Comparison_of_acquisition_and_first_use.png` → Mold acquisition vs. first-use timeline  
  - `*_Machine_mold_first_run_pair.xlsx` → Machine–mold pairing history  
  - `*_Mold_machine_first_run_pair.xlsx` → Mold–machine pairing history  
  - `*_Number_of_molds_first_run_on_each_machine.png` → First-run distribution by machine  
  - `*_Time_Gap_of_acquisition_and_first_use.png` → Time gap analysis between acquisition and first use  
  - `*_Tonnage_machine_mold_not_matched.xlsx` → Mismatched tonnage records  
  - `*_Tonnage_distribution.png` → Tonnage distribution overview  
  - `*_Tonnage_proportion.png` → Tonnage proportion breakdown  
  - `*_Top_Bottom_molds_gap_time_analysis.png` → Gap time comparison (top vs. bottom molds)  
  - `*_Top_molds_tonnage.png` → High-tonnage mold analysis

### 4. Multi-Level Performance Reports and Static Dashboards

#### MultiLevelDataPlotter (Pipeline Overview)

The `MultiLevelDataPlotter` acts as a coordinating pipeline that can invoke one or all of the subordinate modules—`DayLevelDataPlotter`, `MonthLevelDataPlotter`, and `YearLevelDataPlotter`—depending on the analysis scope. It manages the end-to-end flow from data extraction through analytics to dashboard and report generation, ensuring consistency across daily, monthly, and yearly insights.
- **Invocation flexibility**: Users can run only the daily, monthly, or yearly module, or all of them in sequence.
- **Data orchestration**: Coordinates with `MultiLevelDataAnalytics` pipeline and the corresponding processors (`DayLevelDataProcessor`, `MonthLevelDataProcessor`, `YearLevelDataProcessor`) for structured extraction and visualization.

#### **DayLevelDataPlotter** (9 files)
Analyzes daily production data and visualizes key efficiency metrics. Internally, it configures and invokes `MultiLevelDataAnalytics`, which in turn runs the `DayLevelDataProcessor` for the selected date.

**Data processing output:**
- `*_extracted_records_YYYY-MM-DD.xlsx` → Daily data extract with processed insights (from DayLevelDataProcessor)

**Performance visualizations:**
- `*_change_times_all_types_fig_YYYY-MM-DD.png` → All changeover types  
- `*_item_based_overview_dashboard_YYYY-MM-DD.png` → Item-level performance  
- `*_machine_level_mold_analysis_chart_YYYY-MM-DD.png` → Machine–mold analysis  
- `*_machine_level_yield_efficiency_chart_YYYY-MM-DD.png` → Machine yield efficiency  
- `*_mold_based_overview_dashboard_YYYY-MM-DD.png` → Mold-level performance  
- `*_shift_level_detailed_yield_efficiency_chart_YYYY-MM-DD.png` → Shift-level detailed efficiency  
- `*_shift_level_mold_efficiency_chart_YYYY-MM-DD.png` → Shift-level mold efficiency  
- `*_shift_level_yield_efficiency_chart_YYYY-MM-DD.png` → Shift-level yield efficiency
  
#### **MonthLevelDataPlotter** (6 files)
Analyzes monthly production data and generates performance alerts, executive summaries, and dashboards. It configures `MultiLevelDataAnalytics` to invoke the `MonthLevelDataProcessor` for the target month.

**Data processing output:**
- `*_extracted_records_YYYY-MM.xlsx` → Monthly data extract with processed insights (from MonthLevelDataProcessor)

**Executive reports:**
- `*_early_warning_report_YYYY-MM.txt` → Performance alerts  
- `*_final_summary_YYYY-MM.txt` → Executive summary  

**Performance visualizations:**
- `*_machine_based_dashboard_YYYY-MM.png` → Machine performance  
- `*_mold_based_dashboard_YYYY-MM.png` → Mold performance  
- `*_month_performance_dashboard_YYYY-MM.png` → Overall monthly performance

#### **YearLevelDataPlotter** (11 files)
Analyzes yearly production data and generates high-level visualizations and executive reports. Internally, it configures and invokes `MultiLevelDataAnalytics`, which automatically selects the `YearLevelDataProcessor` and consolidates machine, mold, and monthly insights into aggregated outputs.

**Data processing output:**
- `*_extracted_records_YYYY.xlsx` → Yearly data extract with processed insights (from YearLevelDataProcessor)

**Executive report:**
- `*_final_summary_YYYY.txt` → Annual executive summary  
  
**Performance visualizations:**
- `*_machine_based_year_view_dashboard_YYYY.png` → Machine annual view  
- `*_machine_po_item_dashboard_YYYY_page(x).png` → Machine PO/item breakdown*  
- `*_machine_quantity_dashboard_YYYY_page(x).png` → Machine quantity analysis*  
- `*_machine_working_days_dashboard_YYYY_page(x).png` → Machine utilization*  
- `*_mold_based_year_view_dashboard_YYYY.png` → Mold annual view  
- `*_mold_quantity_dashboard_YYYY_page(x).png` → Mold quantity analysis*  
- `*_mold_shots_dashboard_YYYY_page(x).png` → Mold shot count analysis*  
- `*_monthly_performance_dashboard_YYYY.png` → Month-by-month trends  
- `*_year_performance_dashboard_YYYY.png` → Annual overview  

> *Multi-page outputs: Files marked with `page(x)` contain multiple visualizations for detailed breakdowns.

#### Summary of all three levels for consistency check:

| Level | Total Files | Processing | Reports | Visualizations |
|-------|-------------|------------|---------|----------------|
| Day   | 9           | 1          | 0       | 8              |
| Month | 6           | 1          | 2       | 3              |
| Year  | 11          | 1          | 1       | 9              |


---

## Data Flow Summary

```
    Data Collection → Data Loader → Shared Database (9 files)
                                          ↓
        ┌─────────────────────────────────┼──────────────────────────────────┬───────────────────────────────────────────┐
        |                                 |                                  |                                           |
        ↓                                 ↓                                  ↓                                           ↓
    ValidationOrch            MoldMachineFeatureWeightCalculator     DataChangeAnalyzer                  Multi-Level Performance Analysis
        ↓                     + MoldStabilityIndexCalculator      (Change History Analysis)                              ↓
    Validation Report            (Data Insights Generator)         ├─ UpdateHistMachine                         MultiLevelDataPlotter
        | (cross-ref                      |                        └─ UpdateHistMold                      ┌──────────────┼───────────────┐
        |  if exists)                     ↓                                  ↓                            ↓              ↓               ↓
        └──> OrderProgress ─────→ ProducingProcessor                  Change Detection                DayLevel       MonthLevel      YearLevel
           (reads Shared DB)              ↓                                  ↓                        Plotter        Plotter         Plotter
                   ↓               PendingProcessor                    Change Analysis                                   ↓
             Status Reports               ↓                          Change Visualization                 Multi-Level Performance Dashboards
            (with validation       Production Plans                               
             flags)                (Initial Plan)           
```