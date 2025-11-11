```plaintext
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               [ OptiMoldIQWorkflow ]                                            │
│                    Main orchestrator coordinating all manufacturing workflow phases             │
└──────────────┬──────────────────────────────────────────────────────────────────────────────────┘
               │
               ▼ DATA SOURCES
    📂 agents/database/
    ├── databaseSchemas.json ────────────────────────────┐
    └── dynamicDatabase/                                 │
        ├── monthlyReports_history/*.xlsb                │
        └── purchaseOrders_history/*.xlsx                │
                                                         │
               ▼ PHASE 1: DATA COLLECTION                │
        ┌──────────────────────┐                         │
        │ DataPipelineOrch.    │◀───────────────────────┘
        │ (Collect & Process)  │
        └──────────┬───────────┘
                   │
                   │ 📊 Execute Data Collection
                   │ • Run DataPipelineOrchestrator
                   │ • Process dynamic databases
                   │ • Generate pipeline report
                   │ • Handle collection errors
                   │
                   ├──⯈ DataCollector ──────────⯈ 📄 *_DataCollector_success/failed_report.txt
                   ├──⯈ DataLoaderAgent ────────⯈ 📄 *_DataLoaderAgent_success/failed_report.txt
                   └──⯈ Pipeline Orchestrator ──⯈ 📄 *_DataPipelineOrchestrator_final_report.txt
                   │
                   ▼ OUTPUT: shared_db/DataLoaderAgent/newest/
                   • itemCompositionSummary.parquet
                   • itemInfo.parquet, machineInfo.parquet, moldInfo.parquet
                   • moldSpecificationSummary.parquet
                   • productRecords.parquet, purchaseOrders.parquet
                   • resinInfo.parquet, path_annotations.json
                   │
                   ▼
        ┌──────────────────────┐
        │   Update Detection   │
        │ (Analyze Changes)    │
        └──────────┬───────────┘
                   │ 🔍 Detect Database Updates
                   │ • Check collector results
                   │ • Check loader results  
                   │ • Identify changed databases
                   │ • Return trigger flag & details
                   │
                   ▼ PHASE 2: SHARED DB BUILDING (Conditional - If Updates Detected)
       ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
       │ ValidationOrch.      │      │ OrderProgressTracker │      │ MoldStabilityIndex   │      │ MoldMachineFeature   │
       │ (Data Validation)    │────⯈│ (Progress Monitor)   │────⯈│ Calculator            │────⯈│ WeightCalculator     │
       └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
              │                             │                              │                              │
              │ ✅ Validate Data            │ 📈 Track Order Status       │ 📈 Generate Historical      │ ⚖️ Calculate Features
              │ • Run validation checks     │ • Monitor order progress    │    Insights                 │ • Process stability data
              │ • Generate mismatch reports │ • Track milestones          │ • Mold stability index      │ • Calculate confidence
              │ • Ensure data integrity     │ • Update progress logs      │ • Machine feature weights   │ • Generate weight reports
              │ • Save validation results   │ • Generate progress reports │                             │
              │                             │                              │                              │
              ▼                             ▼                              ▼                              ▼
       📊 validation_          📈 auto_status.xlsx      🎯 mold_stability_      ⚖️ confidence_report.txt
       orchestrator.xlsx       (newest + historical)     index.xlsx             + weights_hist.xlsx
              │                             │                              │                              │
              └─────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
                                                          │
                   ┌──────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ ProducingProcessor   │──⯈ 📊 producing_processor.xlsx
        │ (Production Analysis)│
        └──────────────────────┘
                   │
                   │ 🏭 Process Production Data
                   │ • Analyze production metrics
                   │ • Calculate efficiency & loss
                   │ • Generate production reports
                   │ • Process stability indices
                   │
                   ▼ PHASE 3: INITIAL PLANNING (Conditional)
        ┌──────────────────────┐
        │   Purchase Order     │
        │   Change Detection   │
        └──────────┬───────────┘
                   │
                   │ 🛒 Check Purchase Orders
                   │ • Analyze updated databases
                   │ • Look for 'purchaseOrders' changes
                   │ • Determine if planning needed
                   │ • Trigger or skip processing
                   │
                   ▼ If PO Changes Detected
        ┌──────────────────────┐
        │   PendingProcessor   │──⯈ 📋 pending_processor.xlsx
        │ (Order Processing)   │
        └──────────────────────┘
                   │
                   │ ⚡ Process Pending Orders
                   │ • Apply priority ordering
                   │ • Respect load thresholds
                   │ • Optimize processing schedule
                   │ • Generate planning reports
                   │
                   ▼ PHASE 4: ANALYTICS & VISUALIZATION
        ┌──────────────────────┐
        │   Trigger Detection  │
        │ (Request Validation) │
        └──────────┬───────────┘
                   │
                   │ 🔍 Validate Visualization Request
                   │ • Receive viz/change detection request
                   │ • Check newest excels in history
                   │ • Run new analysis vs latest version
                   │ • Compare and detect changes
                   │ • Return trigger flag & details
                   │
                   ├──────────────────────────┬──────────────────────────┬──────────────────────────┐
                   ▼                          ▼                          ▼                          ▼
        ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
        │   DayLevelPlotter    │  │  MonthLevelPlotter   │  │   YearLevelPlotter   │  │  UpdateHist Modules  │
        └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
                   │                         │                         │                         │
                   ▼ Daily Analysis          ▼ Monthly Analysis        ▼ Yearly Analysis         ▼ Historical
    📊 Per Date (e.g. 2018-11-06)   📈 Per Month (e.g. 2019-01)   📅 Per Year (2019)        📜 Timeline Analysis
    ├─ item_based_overview          ├─ month_performance          ├─ year_performance        ┌─────────────────┐
    │  _dashboard.png                │  _dashboard.png             │  _dashboard.png         │ MoldOverview    │
    ├─ mold_based_overview          ├─ machine_based              ├─ monthly_performance     └────┬────────────┘
    │  _dashboard.png                │  _dashboard.png             │  _dashboard.png              │
    ├─ shift_level_yield            ├─ mold_based                 ├─ machine_based_year           ▼ Mold History
    │  _efficiency_chart.png         │  _dashboard.png             │  _view_dashboard.png    • Machine_mold_
    ├─ shift_level_mold             ├─ early_warning              ├─ mold_based_year           first_run_pair.xlsx
    │  _efficiency_chart.png         │  _report.txt                │  _view_dashboard.png    • Tonnage_distribution
    ├─ shift_level_detailed         ├─ final_summary.txt          ├─ machine_po_item           .png
    │  _yield_efficiency.png         └─ extracted_records          │  _dashboard_page1-2     • machine_molds/
    ├─ machine_level_yield             .xlsx                       ├─ machine_quantity          ├─ *_machine_molds
    │  _efficiency_chart.png                                       │  _dashboard_page1-2         .json (historical)
    ├─ machine_level_mold                                          ├─ machine_working_days   • First run pairs
    │  _analysis_chart.png                                         │  _dashboard_page1-2      • Tonnage matching
    ├─ change_times_all                                            ├─ mold_quantity          
    │  _types_fig.png                                              │  _dashboard_page1-4      ┌─────────────────┐
    └─ extracted_records                                           ├─ mold_shots              │ MachineLayout   │
       .xlsx                                                       │  _dashboard_page1-4      └────┬────────────┘
                                                                   ├─ final_summary.txt            │
                                                                   └─ extracted_records            ▼ Layout History
                                                                      .xlsx                   • Machine_change
                                                                                                 _layout_timeline
                                                                                              • Machine_level
                                                                                                 _change_layout
                                                                                                 _details.png
                                                                                              • layout_changes
                                                                                                 .json
                                                                                              • Pivot tables

        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                          📋 CENTRALIZED REPORTING SYSTEM                            │
        │                                                                                     │
        │  All modules output to: agents/shared_db/{ModuleName}/                             │
        │  ├── newest/              ← Current outputs                                        │
        │  ├── historical_db/       ← Archived outputs with timestamps                       │
        │  └── change_log.txt       ← Track all changes and updates                          │
        │                                                                                     │
        │  Storage Features:                                                                  │
        │  • UTF-8 encoding for all text reports                                             │
        │  • Timestamped outputs (*_YYYY-MM-DD or *_YYYYMM format)                           │
        │  • Historical versioning with automatic archival                                   │
        │  • Change tracking across all phases                                               │
        │  • Comprehensive audit trails                                                      │
        │                                                                                     │
        │  Workflow Reports Include:                                                          │
        │  • Data collection, validation, progress tracking results                          │
        │  • Planning, visualizations and analysis outputs                                   │
        │  • Operational summaries and audit trails                                          │
        └─────────────────────────────────────────────────────────────────────────────────────┘
                                               ▼
                                      ✅ Workflow Complete
                                      • All phases executed based on triggers
                                      • Data validated and processed
                                      • Reports and visualizations generated
                                      • Historical data archived with timestamps
                                      • System ready for next cycle
```