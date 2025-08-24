```plaintext
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               [ OptiMoldIQWorkflow ]                                            │
│                    Main orchestrator coordinating all manufacturing workflow phases              │
└──────────────┬──────────────────────────────────────────────────────────────────────────────────┘
               ▼ PHASE 1: DATA COLLECTION                                           
        ┌──────────────────────┐                                            ┌──────────────────────┐
        │ DataPipelineOrch.    │                                            │   Update Detection   │
        │ (Collect & Process)  │────── Process Pipeline ──────────────────⯈│ (Analyze Changes)    │
        └──────────────────────┘                                            └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    📊 Execute Data Collection                                             🔍 Detect Database Updates
    • Run DataPipelineOrchestrator                                         • Check collector results
    • Process dynamic databases                                            • Check loader results  
    • Generate pipeline report                                             • Identify changed databases
    • Handle collection errors                                             • Return trigger flag & details

               ▼ PHASE 2: SHARED DB BUILDING (Conditional)
        ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
        │ ValidationOrch.      │      │ OrderProgressTracker │      │ Historical insight   │      │ ProducingProcessor   │
        │ (Data Validation)    │────⯈│ (Progress Monitoring)│────⯈ │ adding phase         │────⯈│ (Production Analysis)│
        └──────────────────────┘      └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
               │                              │                              │                                │
               ▼                              ▼                              ▼                                ▼
    ✅ Validate Data Quality          📈 Track Order Status       📈 Generate Historical Insights   🏭 Process Production Data
    • Run validation checks            • Monitor order progress     • Calculate:                      • Analyze production metrics
    • Generate mismatch reports        • Track milestones           1. mold stability index           • Calculate efficiency & loss
    • Ensure data integrity            • Update progress logs       2. mold machine feature weight    • Generate production reports
    • Save validation results          • Generate progress reports                                    • Process stability indices

               ▼ PHASE 3: INITIAL PLANNING (Conditional)
        ┌──────────────────────┐                                             ┌──────────────────────┐
        │   Purchase Order     │                                             │   PendingProcessor   │
        │   Change Detection   │────── If PO Changes Detected ─────────────⯈│ (Order Processing)   │
        └──────────────────────┘                                             └──────────────────────┘
               │                                                                        │
               ▼                                                                        ▼
    🛒 Check Purchase Orders                                            ⚡ Process Pending Orders
    • Analyze updated databases                                          • Apply priority ordering
    • Look for 'purchaseOrders' changes                                  • Respect load thresholds
    • Determine if planning needed                                       • Optimize processing schedule
    • Trigger or skip processing                                         • Generate planning reports

        ┌─────────────────────────────────────────────────────────────────────────────────────┐
        │                                📋 REPORTING SYSTEM                                  │
        │  • Generate comprehensive workflow reports                                          │
        │  • Include data collection, validation, progress, and planning results              │
        │  • Save timestamped reports with UTF-8 encoding                                     │
        │  • Provide audit trails and operational summaries                                   │
        └──────────────────────────────────────┬──────────────────────────────────────────────┘
                                               ▼
                                      🛠️  To Be Continued...

```
