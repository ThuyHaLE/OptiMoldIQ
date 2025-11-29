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
              │                             │                             │                             │
              │ ✅ Validate Data           │ 📈 Track Order Status       │ 📈 Generate Historical      │ ⚖️ Calculate Features
              │ • Run validation checks     │ • Monitor order progress    │    Insights                 │ • Process stability data
              │ • Generate mismatch reports │ • Track milestones          │ • Mold stability index      │ • Calculate confidence
              │ • Ensure data integrity     │ • Update progress logs      │ • Machine feature weights   │ • Generate weight reports
              │ • Save validation results   │ • Generate progress reports │                             │
              │                             │                             │                             │
              ▼                             ▼                             ▼                             ▼
         📊 validation_          📈 auto_status.xlsx            🎯 mold_stability_         ⚖️ confidence_report.txt
         orchestrator.xlsx       (newest + historical)               index.xlsx                 + weights_hist.xlsx
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
      ┌───────────────────────┐
      │   Purchase Order      │
      │   Change Detection    │
      └───────────┬───────────┘
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
   ┌──────────────────────────┐
   |     DashboardBuilder     |
   |     (Entry Point)        |
   └──────────────┬───────────┘
                  │ • Receives pre-built config from OptiMoldIQWorkflow
                  │ • No validation logic (trusts parent config)
                  │ • Coordinates visualization workflows
                  │ • Supports parallel processing (optional)
                  │
                  │
                  │ ⚙️ Auto-Configuration Flow:
                  │ • Parent enables → Child configs enabled
                  │ • Logging settings propagated
                  │ • See logs for propagation details
                  |       
                  ├───────────────────────────────────────────────────────────────────────────────┐
                  ▼                                                                               ▼
         ┌───────────────────────────────┐                                           ┌─────────────────────────┐
         │ MultiLevelPerformancePlotter  │                                           │ HardwareChangePlotter   │
         │                               │                                           │                         │
         │ [Visualization Layer]         │                                           │ [Visualization Layer]   │
         └────────┬──────────────────────┘                                           └────────────┬────────────┘
                  │ Trigger Analysis                                                              │ Trigger Analysis
                  ▼                                                                               ▼
            ┌────────────────────────────────────────────────────────────────────────────────────────────┐
            │                            AnalyticsOrchestrator (Shared Component)                        │
            │  • Called by both plotters                                                                 │
            │  • Coordinates analysis workflows                                                          │
            │  • Auto-configuration propagation                                                          │
            │  • Manages analyzer lifecycles                                                             │
            └─────┬──────────────────────────────────────────────────────────────────────────────────┬───┘
                  ▼                                                                                  ▼
         ┌───────────────────────────────┐                                             ┌─────────────────────────┐
         │ MultiLevelPerformanceAnalyzer │                                             │ HardwareChangeAnalyzer  │
         │                               │                                             │                         │
         │ [Data Processing Layer]       │                                             │ [Change Detection]      │
         └────────┬──────────────────────┘                                             └─────────────┬───────────┘
                  ├──────────────────┬──────────────────────┐                        ┌───────────────┴──────────────┐
                  ▼                  ▼                      ▼                        ▼                              ▼  
      ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐       ┌──────────────────────┐    ┌──────────────────────┐        
      │ DayLevelData    │  │ MonthLevelData   │  │ YearLevelData  │       │ MachineLayout        │    │ MachineMoldPair      │            
      │ Processor       │  │ Processor        │  │ Processor      │       │ Tracker              │    │ Tracker              │            
      └──────────┬──────┘  └──────────┬───────┘  └──────────┬─────┘       └──────────┬───────────┘    └──────────┬───────────┘            
                 │                    │                     │                        ▼                           ▼               
                 │                    │                     │             ┌──────────────────────┐    ┌──────────────────────┐             
                 │                    │                     │             │ Layout History       │    │ Mold History         │            
                 │                    │                     │             │ • Timeline           │    │ • First run pairs    │ 
                 │                    │                     │             │ • Change details     │    │ • Tonnage dist       │ 
                 │                    │                     │             │ • Pivot tables       │    │ • Machine molds JSON │ 
                 │                    │                     │             └──────────┬───────────┘    └───────────┬──────────┘ 
                 ▼                    ▼                     ▼                        ▼                            ▼  
    ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │                                               Return to Plotters for Visualization                                         │
    └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                 │                    │                     │                        │                            │
                 ▼                    ▼                     ▼                        ▼                            ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
| DayLevel               | | MonthLevel             | | YearLevel              | | MachineLayout          | | MachineMoldPair        |
├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤
| 📊 PROCESSOR OUTPUTS   | | 📊 PROCESSOR OUTPUTS   | | 📊 PROCESSOR OUTPUTS  | | 📊 TRACKER OUTPUTS     | | 📊 TRACKER OUTPUTS    |
| DayLevelDataProcessor/ | | MonthLevelDataProc../  | | YearLevelDataProc../   | | MachineLayoutTracker/  | | MachineMoldPairTrack./ |
| └─ newest/             | | └─ newest/             | | └─ newest/             | | └─ newest/             | | └─ newest/             |
|   ├─ *_day_level       | |   ├─ *_day_level       | |   ├─ *_year_level      | |   ├─ *_machine_layout  | |   ├─ *_mold_machine    |
|   │  _insights         | |   │  _insights         | |   │  _insights         | |   │  _changes          | |   │  _pairing          |
|   │  _YYYY-MM-DD.xlsx  | |   │  _YYYY-MM.xlsx     | |   │  _YYYY.xlsx        | |   │  _YYYY-MM-DD.json  | |   │  _YYYY-MM-DD.xlsx  |
|   └─ *_day_level       | |   └─ *_day_level       | |   └─ *_year_level      | |   └─ *_machine_layout  | |   ├─ *_mold_machine    |
|      _summary          | |      _summary          | |      _summary          | |      _changes          | |   │  _pairing_summary  |
|      _YYYY-MM-DD.txt   | |      _YYYY-MM.txt      | |      _YYYY.txt         | |      _YYYY-MM-DD.xlsx  | |   │  _YYYY-MM-DD.txt   |
├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤ |   └─ pair_changes/     |
| 📊 PLOTTER OUTPUTS     | | 📊 PLOTTER OUTPUTS    | | 📊 PLOTTER OUTPUTS     | | 📊 PLOTTER OUTPUTS    | |     └─ YYYY-MM-DD_     |
| DayLevelDataPlotter/   | | MonthLevelDataPlotter/ | | YearLevelPlotter/      | | MachineLayoutPlotter/  | |        *_pairing       |
| └─ newest/             | | └─ newest/             | | └─ newest/             | | └─ newest/             | |        _YYYY-MM-DD.json|
|   ├─ *_item_based      | |   ├─ *_month           | |   ├─ *_year            | |   ├─ *_Machine_layout  | ├────────────────────────┤
|   │  _overview         | |   │  _performance      | |   │  _performance      | |   │  _change           | | 📊 PLOTTER OUTPUTS     |
|   │  _dashboard        | |   │  _dashboard        | |   │  _dashboard        | |   │  _dashboard.png    | | MachineMoldPairPlotter/|
|   │  _YYYY-MM-DD.png   | |   │  _YYYY-MM.png      | |   │  _YYYY.png         | |   └─ *_Individual      | | └─ newest/             |
|   ├─ *_mold_based      | |   ├─ *_machine_based   | |   ├─ *_monthly         | |      _machine_layout   | |   ├─ *_Mold_machine    |
|   │  _overview         | |   │  _dashboard        | |   │  _performance      | |      _change_times     | |   │  _first_pairing    |
|   │  _dashboard        | |   │  _YYYY-MM.png      | |   │  _dashboard        | |      _dashboard.png    | |   │  _dashboard.png    |
|   │  _YYYY-MM-DD.png   | |   ├─ *_mold_based      | |   │  _YYYY.png         | └────────────────────────┘ |   ├─ *_Mold            |
|   ├─ *_shift_level     | |   │  _dashboard        | |   ├─ *_machine_based   |                            |   │  _utilization      |
|   │  _yield_efficiency | |   │  _YYYY-MM.png      | |   │  _year_view        |                            |   │  _dashboard.png    |
|   │  _chart            | |   ├─ *_early_warning   | |   │  _dashboard        |                            |   └─ *_Machine_tonage  |
|   │  _YYYY-MM-DD.png   | |   │  _report           | |   │  _YYYY.png         |                            |      _based_mold       |
|   ├─ *_shift_level     | |   │  _YYYY-MM.txt      | |   ├─ *_mold_based      |                            |      _utilization      |
|   │  _mold_efficiency  | |   ├─ *_final_summary   | |   │  _year_view        |                            |      _dashboard.png    |
|   │  _chart            | |   │  _YYYY-MM.txt      | |   │  _dashboard        |                            └────────────────────────┘
|   │  _YYYY-MM-DD.png   | |   └─ *_extracted       | |   │  _YYYY.png         |
|   ├─ *_shift_level     | |      _records          | |   ├─ *_machine_po_item |
|   │  _detailed_yield   | |      _YYYY-MM.xlsx     | |   │  _dashboard        |
|   │  _efficiency_chart | └────────────────────────┘ |   │  _YYYY_page1-2.png |
|   │  _YYYY-MM-DD.png   |                            |   ├─ *_machine_quantity|
|   ├─ *_machine_level   |                            |   │  _dashboard        |
|   │  _yield_efficiency |                            |   │  _YYYY_page1-2.png |
|   │  _chart            |                            |   ├─ *_machine_working |
|   │  _YYYY-MM-DD.png   |                            |   │  _days_dashboard   |
|   ├─ *_machine_level   |                            |   │  _YYYY_page1-2.png |
|   │  _mold_analysis    |                            |   ├─ *_mold_quantity   |
|   │  _chart            |                            |   │  _dashboard        |
|   │  _YYYY-MM-DD.png   |                            |   │  _YYYY_page1-4.png |
|   └─ *_change_times    |                            |   ├─ *_mold_shots      |
|      _all_types_fig    |                            |   │  _dashboard        |
|      _YYYY-MM-DD.png   |                            |   │  _YYYY_page1-4.png |
└────────────────────────┘                            |   ├─ *_final_summary   |
                                                      |   │  _YYYY.txt         |
                                                      |   └─ *_extracted       |
                                                      |      _records          |
                                                      |      _YYYY.xlsx        |
                                                      └────────────────────────┘
                                                      
        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                          📋 CENTRALIZED REPORTING SYSTEM                            │
        │                                                                                     │
        │  All modules output to: agents/shared_db/{ModuleName}/                              │
        │  ├── newest/              ← Current outputs                                         │
        │  ├── historical_db/       ← Archived outputs with timestamps                        │
        │  └── change_log.txt       ← Track all changes and updates                           │
        │                                                                                     │
        │  Storage Features:                                                                  │
        │  • UTF-8 encoding for all text reports                                              │
        │  • Timestamped outputs (*_YYYY-MM-DD or *_YYYYMM format)                            │
        │  • Historical versioning with automatic archival                                    │
        │  • Change tracking across all phases                                                │
        │  • Comprehensive audit trails                                                       │
        │                                                                                     │
        │  Workflow Reports Include:                                                          │
        │  • Data collection, validation, progress tracking results                           │
        │  • Planning, visualizations and analysis outputs                                    │
        │  • Operational summaries and audit trails                                           │
        └─────────────────────────────────────────────────────────────────────────────────────┘
                                               ▼
                                      ✅ Workflow Complete
                                      • All phases executed based on triggers
                                      • Data validated and processed
                                      • Reports and visualizations generated
                                      • Historical data archived with timestamps
                                      • System ready for next cycle
```