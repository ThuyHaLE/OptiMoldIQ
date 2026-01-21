> Status: Normalized from v1  
> Changes:
> -Updated system ASCII diagram to align with standardized agent format.
> -Added new architectural branches to reflect newly introduced features.
> -No changes to existing business logic; updates are structural and representational only.

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
         ┌────────────────────────────────────────────┐                              ┌──────────────────────────────────────┐
         │ MultiLevelPerformanceVisualizationService  │                              │ HardwareChangeVisualizationService   │
         │                                            │                              │                                      │
         │ [Visualization Layer]                      │                              │ [Visualization Layer]                │
         └────────┬───────────────────────────────────┘                              └────────────┬─────────────────────────┘
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
    │                                  Return to VisualizationPipelines for Visualization                                        │
    └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                 │                    │                     │                        │                            │
                 ▼                    ▼                     ▼                        ▼                            ▼
    ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │              Summary + visualized data collection + service-specific reports (if supported) + Visualizations               │
    └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                      
        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                          📋 CENTRALIZED REPORTING SYSTEM                            │
        │                                                                                     │
        │  All modules output to: agents/shared_db/{ModuleName}/                              │
        │  ├── newest/              ← Current outputs                                         │
        │  ├── historical_db/       ← Archived outputs with timestamps                        │
        │  ├── (specific folder)/   ← Optional output folders depending on module design      │
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

> Note: Output directory conventions may vary by agent. The `newest/` and `historical_db/` structure represents the default pattern, while certain agents (e.g., visualization services) may employ module-specific, timestamp-based storage strategies.