```plaintext
                   ┌────────────────────────────────┐
                   │       External Inputs          │
                   │ DynamicDB (purchaseOrders,     │
                   │    productRecords) + StaticDB  │
                   └────────────┬───────────────────┘
                                │
                                ▼                                                          ┌────────────────────────────┐ 
                 ┌────────────────────────────┐                                            │    ValidationOrchestrator  │ 
                 │  DataPipelineOrchestrator  │                   ┌──────────────────────► │(Check consistency between  │ 
                 └────────────┬───────────────┘                   │                        │  Static & Dynamic Data)    │
                              │                                   │                        └────────────┬───────────────┘ 
        ┌────────────────────┴────────────────────┐               │         ┌───────────────────────┬───┴────────────────────┐                     
        ▼                                         ▼               │         ▼                       ▼                        ▼
┌────────────────────┐                 ┌─────────────────────┐    │    ┌────────────┐  ┌─────────────────────────┐ ┌────────────────────┐  
│    DataCollector   │                 │   DataLoaderAgent   │    │    │StaticCross │  │DynamicCrossDataValidator│ │ PORequiredCritical │       
│ (monthly dynamic DB│                 │ (load & unify static│    │    │DataChecker │  └────────────┬────────────┘ │ Validator          │
│   .xlsx → .parquet)│                 │   data → .parquet)  │    │    └─────┬──────┘               │              └───────────┬────────┘
└─────────┬──────────┘                 └─────────┬───────────┘    │          ▼                      ▼                          ▼
          ▼                                      ▼                │     ┌────────────────────────────────────────────────────────┐
    ┌──────────────────────────────────────────────────┐          │     │                    PO Mistmatch information            │
    │           ✅ Shared Database (.parquet)          │          │     └────────────────────────────────────────────────────────┘
    │     (static + dynamic for all other agents)      │──────────┘                                │
    └──────────────────────────────────────────────────┘                                           │
                          │                                                                        │
                          ▼                                                                        ▼
                   ┌──────────────────────────────────────────────────────────────────────────────────────┐
                   │                                  OrderProgressTracker                                │
                   │ (Group product records by PO, flag mismatch note from Validation agent (if any))     │
                   └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                                              ▼
                                                    🛠️  To Be Continued...
