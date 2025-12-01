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
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_itemCompositionSummary.parquet
│       ├── *_itemInfo.parquet
│       ├── *_machineInfo.parquet
│       ├── *_moldInfo.parquet
│       ├── *_moldSpecificationSummary.parquet
│       ├── *_productRecords.parquet
│       ├── *_purchaseOrders.parquet
│       ├── *_resinInfo.parquet
│       └── path_annotations.json
|
├── DataPipelineOrchestrator/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_DataCollector_success/failed_report.txt
│       ├── *_DataLoaderAgent_success/failed_report.txt
│       └── *_DataPipelineOrchestrator_final_report.txt
|
├── ValidationOrchestrator/
│   ├── change_log.txt
│   └── newest/
│       └── *_validation_orchestrator.xlsx
|
├── OrderProgressTracker/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       └── *_auto_status.xlsx
|
├── HistoricalInsights
|   ├── MoldMachineFeatureWeightCalculator/
|   │   ├── change_log.txt
|   │   ├── historical_db/
|   │   ├── newest/
|   │   │   └── *_confidence_report.txt
|   │   └── weights_hist.xlsx
|   └── MoldStabilityIndexCalculator/
|       ├── change_log.txt
|       ├── historical_db/
|       └── newest/
|           └── *_mold_stability_index.xlsx
|
├── AutoPlanner/InitialPlanner/
|   ├── ProducingProcessor/
|   │   ├── change_log.txt
|   │   ├── historical_db/
|   │   └── newest/
|   │       └── *_producing_processor.xlsx
|   └── PendingProcessor/
|       ├── change_log.txt
|       ├── historical_db/
|       └── newest/
|           └── *_pending_processor.xlsx
|
├── dynamicDatabase/
|    ├── productRecords.parquet
|    └── purchaseOrders.parquet
|
└── DashboardBuilder/
    ├── HardwareChangePlotter/
    │   ├── MachineLayoutPlotter/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_Individual_machine_layout_change_times_dashboard.png
    │   │       └── *_Machine_layout_change_dashboard.png
    │   ├── MachineLayoutTracker/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_machine_layout_changes_YYYY-MM-DD.json
    │   │       └── *_machine_layout_changes_YYYY-MM-DD.xlsx
    │   ├── MachineMoldPairPlotter/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_Machine_tonage_based_mold_utilization_dashboard.png
    │   │       ├── *_Mold_machine_first_pairing_dashboard.png
    │   │       └── *_Mold_utilization_dashboard.png
    │   ├── MachineMoldPairTracker/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   │   └── pair_changes/
    │   │   └── newest/
    │   │       ├── *_mold_machine_pairing_YYYY-MM-DD.xlsx
    │   │       ├── *_mold_machine_pairing_summary_YYYY-MM-DD.txt
    │   │       └── pair_changes/
    │   │           ├── ...
    │   │           └── *_mold_machine_pairing_YYYY-MM-DD.json
    │   └── change_log.txt
    ├── MultiLevelPerformancePlotter/
    │   ├── DayLevelDataPlotter/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_change_times_all_types_fig_YYYY-MM-DD.png
    │   │       ├── *_item_based_overview_dashboard_YYYY-MM-DD.png
    │   │       ├── *_machine_level_mold_analysis_chart_YYYY-MM-DD.png
    │   │       ├── *_machine_level_yield_efficiency_chart_YYYY-MM-DD.png
    │   │       ├── *_mold_based_overview_dashboard_YYYY-MM-DD.png
    │   │       ├── *_shift_level_detailed_yield_efficiency_chart_YYYY-MM-DD.png
    │   │       ├── *_shift_level_mold_efficiency_chart_YYYY-MM-DD.png
    │   │       └── *_shift_level_yield_efficiency_chart_YYYY-MM-DD.png
    │   ├── DayLevelDataProcessor/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_day_level_insights_YYYY-MM-DD.xlsx
    │   │       └── *_day_level_summary_YYYY-MM-DD.txt
    │   ├── MonthLevelDataPlotter/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_early_warning_report_YYYY-MM.txt
    │   │       ├── *_extracted_records_YYYY-MM.xlsx
    │   │       ├── *_final_summary_YYYY-MM.txt
    │   │       ├── *_machine_based_dashboard_YYYY-MM.png
    │   │       ├── *_mold_based_dashboard_YYYY-MM.png
    │   │       └── *_month_performance_dashboard_YYYY-MM.png
    │   ├── MonthLevelDataProcessor/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_day_level_insights_YYYY-MM.xlsx
    │   │       └── *_day_level_summary_YYYY-MM.txt
    │   ├── YearLevelDataProcessor/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_year_level_insights_YYYY.xlsx
    │   │       └── *_year_level_summary_YYYY.txt
    │   ├── YearLevelDataPlotter/
    │   │   ├── change_log.txt
    │   │   ├── historical_db/
    │   │   └── newest/
    │   │       ├── *_extracted_records_YYYY.xlsx
    │   │       ├── *_final_summary_YYYY.txt
    │   │       ├── *_machine_based_year_view_dashboard_YYYY.png
    │   │       ├── *_machine_po_item_dashboard_YYYY_page(x).png
    │   │       ├── *_machine_quantity_dashboard_YYYY_page(x).png
    │   │       ├── *_machine_working_days_dashboard_YYYY_page(x).png
    │   │       ├── *_mold_based_year_view_dashboard_YYYY.png
    │   │       ├── *_mold_quantity_dashboard_YYYY_page(x).png
    │   │       ├── *_mold_shots_dashboard_YYYY_page(x).png
    │   │       ├── *_monthly_performance_dashboard_YYYY.png
    │   │       └── *_year_performance_dashboard_YYYY.png
    │   └── change_log.txt
    └── change_log.txt
```