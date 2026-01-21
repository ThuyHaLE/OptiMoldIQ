> Status: Introduced in v2  
> Purpose: Illustrate example project directory layout (non-normative)

The following structure is an illustrative snapshot. 

Only top-level agent namespaces and Shared Database contracts are considered stable.

```plaintext

# DATA SOURCES

agents/database
├── databaseSchemas.json                                     # Source directory (Data Loader)
└── dynamicDatabase/                                         # Source directory (Data Collection)
    ├── monthlyReports_history/                              # Product records source (Data Collection)
    │   └── monthlyReports_YYYYMM.xlsb
    └── purchaseOrders_history/                              # Purchase orders source (Data Collection)
        └── purchaseOrder_YYYYMM.xlsx

# REPORTING SYSTEM

agents/shared_db
├── DataLoaderAgent/
├── DataPipelineOrchestrator/
├── ValidationOrchestrator/
├── OrderProgressTracker/
├── HistoricalInsights
|   ├── MoldMachineFeatureWeightCalculator/
|   └── MoldStabilityIndexCalculator/
├── AutoPlanner/InitialPlanner/
|   ├── ProducingProcessor/
|   └── PendingProcessor/
├── dynamicDatabase/
|    ├── productRecords.parquet
|    └── purchaseOrders.parquet
├── AnalyticsOrchestrator/
|   ├── HardwareChangeAnalyzer/
|   └── MultiLevelPerformanceAnalyzer/
└── DashboardBuilder/
    ├── HardwareChangeVisualizationService/
    │   ├── MachineLayoutVisualizationPipeline/
    │   └── MachineMoldPairVisualizationPipeline/
    └── MultiLevelPerformanceVisualizationService/
        ├── DayLevelDataVisualizationPipeline/
        ├── MonthLevelDataVisualizationPipeline/
        └── YearLevelDataVisualizationPipeline/
```