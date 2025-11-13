# 3. Shared Database

**Location:** `agents/shared_db/`

## Directory Structure

```plaintext
agents/shared_db/
│
# ═══════════════════════════════════════════════════════════
# DATA PIPELINE & VALIDATION
# ═══════════════════════════════════════════════════════════
├── DataPipelineOrchestrator/newest/        # Pipeline execution logs (3 files)
│   ├── *_DataCollector_[success/failed]_report.txt
│   ├── *_DataLoaderAgent_[success/failed]_report.txt
│   └── *_DataPipelineOrchestrator_final_report.txt
│
├── DataLoaderAgent/newest/                 # Main Shared Database (9 files)
│   ├── [Dynamic DB] (2 files)              # *_productRecords.parquet, *_purchaseOrders.parquet
│   ├── [Static DB] (6 files)               # *_itemInfo, *_machineInfo, *_moldInfo, etc.
│   └── path_annotations.json               # Database path metadata
│
├── ValidationOrchestrator/newest/          # Data validation reports (1 file)
│   └── *_validation_orchestrator.xlsx
│
├── OrderProgressTracker/newest/            # Production & order status tracking (1 file)
│   └── *_auto_status.xlsx                  # Cross-references validation if available
│
# ═══════════════════════════════════════════════════════════
# PRODUCTION OPTIMIZATION
# ═══════════════════════════════════════════════════════════
├── MoldMachineFeatureWeightCalculator/     # Mold-machine compatibility scoring
│   ├── newest/                             # *_confidence_report.txt
│   └── weights_hist.xlsx                   # Historical calculations
│
├── MoldStabilityIndexCalculator/newest/    # Mold performance stability (1 file)
│   └── *_mold_stability_index.xlsx         # → Feeds ProducingProcessor
│
├── ProducingProcessor/newest/              # Active production analysis (1 file)
│   └── *_producing_processor.xlsx          # Uses: OrderProgress + HybridSuggest outputs
│
├── PendingProcessor/newest/                # Production planning suggestions (1 file)
│   └── *_pending_processor.xlsx            # Builds on ProducingProcessor output
│
# ═══════════════════════════════════════════════════════════
# HISTORICAL ANALYTICS
# ═══════════════════════════════════════════════════════════
├── UpdateHistMachineLayout/newest/         # Machine layout change analysis (4 files)
│   ├── *_Machine_change_layout_timeline.png
│   ├── *_Machine_level_change_layout_details.png
│   ├── *_Machine_level_change_layout_pivot.xlsx
│   └── *_Top_machine_change_layout.png
│
├── UpdateHistMoldOverview/newest/          # Mold usage & performance history (11 files)
│   ├── *_Bottom_molds_tonnage.png
│   ├── ... (9 more visualization files)
│   └── *_Top_molds_tonnage.png
│
# ═══════════════════════════════════════════════════════════
# MULTI-LEVEL PERFORMANCE DASHBOARDS
# ═══════════════════════════════════════════════════════════
├── DayLevelDataProcessor/newest/           # Daily data preparation
├── DayLevelDataPlotter/newest/             # Daily dashboards (9 files)
│
├── MonthLevelDataProcessor/newest/         # Monthly data aggregation
├── MonthLevelDataPlotter/newest/           # Monthly dashboards (6 files)
│
├── YearLevelDataProcessor/newest/          # Annual data consolidation
└── YearLevelPlotter/newest/                # Annual dashboards (11 files)
```

### Notes on Directory Structure:

**Orchestrators vs Output Folders:**
- Some folders represent **output locations** (e.g., `DayLevelDataPlotter`)
- The actual **orchestrator/agent names** may differ (e.g., `DashboardBuilder` coordinates multiple plotter folders)
- See "System Reports" section below for full orchestrator → output mapping

**Folder Naming:**
- `newest/` = symbolic link to latest timestamped output
- `*_` prefix = timestamp format YYYYMMDD_HHMM_

**Key Relationships:**
- `DataLoaderAgent` = single source of truth (Main Shared Database)
- All analytics/reports read from this shared database
- `ProducingProcessor` depends on: OrderProgressTracker + MoldMachine + MoldStability outputs
  
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

## 📋 System Reports

### Data Pipeline Reports

#### **DataPipelineOrchestrator** (12 files total involved)
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

---

### Production Optimization Reports

#### **HybridSuggestOptimizer**
Provides optimization metrics to support **ProducingProcessor** modules.

**MoldMachineFeatureWeightCalculator** (2 files)  
Generates compatibility scoring between molds and machines:
- `newest/*_confidence_report.txt` → Confidence metrics  
- `weights_hist.xlsx` → Historical weight calculations  
    
**MoldStabilityIndexCalculator** (1 file)  
Calculates mold performance stability:
- `*_mold_stability_index.xlsx`

---

#### **AutoPlanner / InitialPlanner**

**ProducingProcessor** (1 file)  
Uses results from **HybridSuggestOptimizer** and  **OrderProgressTracker** to perform active production analysis and generate initial production planning data:  
- `*_producing_processor.xlsx` → Active production report

**PendingProcessor** (1 file)  
Builds upon the outputs from **ProducingProcessor** to generate and suggest final production plans via **OptiMoldIQ**:  
- `*_pending_processor.xlsx` → Suggested production plan

**Flow**
OrderProgressTracker (production status) ────────────────────────────┐
                                                                     ├──→ ProducingProcessor
HybridSuggestOptimizer (compatibility weights + stability index) ────┘          |
                                                                                ↓ (active production analysis)
                                                                            PendingProcessor
                                                                                ↓ (final production plan suggestion)

---

## 📈 Analytics & Visualizations

### Detect and Visualize Machine/Mold-Based Historical Changes

#### **AnalyticsOrchestrator / DataChangeAnalyzer** (15 files)
Coordinates and executes historical change analyses for both machines and molds.  
It processes data from the **Main Shared Database** and outputs visualizations and analytical reports through two modules:

---

#### **UpdateHistMachineLayout** (4 files)
Analyzes machine layout evolution over time to identify layout changes and activity patterns:
- `*_Machine_change_layout_timeline.png` → Machine layout change timeline
- `*_Machine_level_change_layout_details.png` → Detailed layout change breakdown
- `*_Machine_level_change_layout_pivot.xlsx` → Pivot analysis of layout changes
- `*_Top_machine_change_layout.png` → Machines with most frequent layout updates

---

#### **UpdateHistMoldOverview** (11 files)
Analyzes mold-machine relationships, first-run history, and mold utilization to identify operational trends:
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


---

### Multi-Level Performance Dashboards

#### **DashboardBuilder**
Collaborates with **AnalyticsOrchestrator / MultiLevelDataAnalytics** to process and visualize production performance across three levels — Day, Month, and Year.  
Each level consists of a **DataProcessor** (for data preparation and aggregation) and a **DataPlotter** (for visualization and reporting).  
All modules operate based on requests and pull data from the **Main Shared Database**.

---

#### **DayLevelDataProcessor + DayLevelDataPlotter** (9 files)
Generates **daily operational insights** by processing production and performance data for each day, then visualizing key efficiency metrics:
- `*_change_times_all_types_fig_YYYY-MM-DD.png` → All changeover types  
- `*_extracted_records_YYYY-MM-DD.xlsx` → Daily data extract  
- `*_item_based_overview_dashboard_YYYY-MM-DD.png` → Item-level performance  
- `*_machine_level_mold_analysis_chart_YYYY-MM-DD.png` → Machine–mold analysis  
- `*_machine_level_yield_efficiency_chart_YYYY-MM-DD.png` → Machine yield efficiency  
- `*_mold_based_overview_dashboard_YYYY-MM-DD.png` → Mold-level performance  
- `*_shift_level_detailed_yield_efficiency_chart_YYYY-MM-DD.png` → Shift-level detailed efficiency  
- `*_shift_level_mold_efficiency_chart_YYYY-MM-DD.png` → Shift-level mold efficiency  
- `*_shift_level_yield_efficiency_chart_YYYY-MM-DD.png` → Shift-level yield efficiency  

---

#### **MonthLevelDataProcessor + MonthLevelDataPlotter** (6 files)
Produces **monthly performance summaries** with alerts, executive insights, and comparative dashboards:
- `*_early_warning_report_YYYY-MM.txt` → Performance alerts  
- `*_extracted_records_YYYY-MM.xlsx` → Monthly data extract  
- `*_final_summary_YYYY-MM.txt` → Executive summary  
- `*_machine_based_dashboard_YYYY-MM.png` → Machine performance  
- `*_mold_based_dashboard_YYYY-MM.png` → Mold performance  
- `*_month_performance_dashboard_YYYY-MM.png` → Overall monthly performance  

---

#### **YearLevelDataProcessor + YearLevelPlotter** (11 files)
Provides **annual performance analytics** consolidating machine, mold, and monthly data into high-level visualizations and reports:
- `*_extracted_records_YYYY.xlsx` → Yearly data extract  
- `*_final_summary_YYYY.txt` → Annual executive summary  
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

---

## Data Flow Summary

```
Data Flow:

    Data Collection → Data Loader → Shared Database (9 files)
                                            ↓
        ┌───────────────────────────────────┼───────────────────────────┬─────────────────────────┐
        |                                   |                           |                         |
        ↓                                   ↓                           ↓                         ↓
    ValidationOrch              HybridSuggestOptimizer       AnalyticsOrchestrator       DashboardBuilder
        ↓                       ├─ MoldMachine               (Historical Analysis)      + MultiLevelDataAnalytics
    Validation Report           └─ MoldStability             ├─ UpdateHistMachine              ↓
        | (cross-ref                   |                     └─ UpdateHistMold          ├─ Day Level
        |  if exists)                  |                             ↓                  ├─ Month Level
        |                              ↓                      Change Detection          └─ Year Level
        └──> OrderProgress ─────→ ProducingProc                      ↓                        ↓
             (reads Shared DB)         ↓                      Change Analysis            Performance
                    ↓            PendingProcessor            Change Visualization        Dashboards
               Status Reports          ↓
              (with validation   Production Plans
                  flags)          (Initial Plan)
```

### Key Integration Points:

**Data Sources:**
- **Data Loader** feeds from Data Collection to create Main Shared Database (9 files)

**Cross-Module Dependencies:**
- **Validation** → Order Progress Tracking (optional cross-reference)
- **Order Progress + HybridSuggest** → Production Processing (required inputs)
- **Producing Processor** → Pending Processor (sequential pipeline)

**Data Consumers:**
- **ValidationOrchestrator** reads Main Shared Database
- **OrderProgressTracker** reads Main Shared Database + Validation results
- **AnalyticsOrchestrator** reads Main Shared Database for historical analysis
- **DashboardBuilder** reads Main Shared Database for performance visualization

### Quick Reference: Output File Counts

| Module | Output Files | Key Files |
|--------|--------------|-----------|
| DataPipelineOrchestrator | 12 total | DB (9) + Logs (3) |
| ValidationOrchestrator | 1 | validation_orchestrator.xlsx |
| OrderProgressTracker | 1 | auto_status.xlsx |
| HybridSuggestOptimizer | 3 | confidence_report, weights_hist, stability_index |
| ProducingProcessor | 1 | producing_processor.xlsx |
| PendingProcessor | 1 | pending_processor.xlsx |
| UpdateHistMachineLayout | 4 | 3 PNG + 1 XLSX |
| UpdateHistMoldOverview | 11 | 10 PNG + 1 XLSX |
| DayLevel (Processor + Plotter) | 9 | 8 PNG + 1 XLSX |
| MonthLevel (Processor + Plotter) | 6 | 3 PNG + 3 TXT/XLSX |
| YearLevel (Processor + Plotter) | 11 | 10 PNG + 1 XLSX |