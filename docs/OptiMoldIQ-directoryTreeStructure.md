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
├── DataPipelineOrchestrator/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_DataCollector_success/failed_report.txt
│       ├── *_DataLoaderAgent_success/failed_report.txt
│       └── *_DataPipelineOrchestrator_final_report.txt
├── DayLevelDataPlotter/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_change_times_all_types_fig_YYYY-MM-DD.png
│       ├── *_extracted_records_YYYY-MM-DD.xlsx
│       ├── *_item_based_overview_dashboard_YYYY-MM-DD.png
│       ├── *_machine_level_mold_analysis_chart_YYYY-MM-DD.png
│       ├── *_machine_level_yield_efficiency_chart_YYYY-MM-DD.png
│       ├── *_mold_based_overview_dashboard_YYYY-MM-DD.png
│       ├── *_shift_level_detailed_yield_efficiency_chart_YYYY-MM-DD.png
│       ├── *_shift_level_mold_efficiency_chart_YYYY-MM-DD.png
│       └── *_shift_level_yield_efficiency_chart_YYYY-MM-DD.png
├── MoldMachineFeatureWeightCalculator/
│   ├── change_log.txt
│   ├── historical_db/
│   ├── newest/
│   │   └── *_confidence_report.txt
│   └── weights_hist.xlsx
├── MoldStabilityIndexCalculator/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       └── *_mold_stability_index.xlsx
├── MonthLevelDataPlotter/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_early_warning_report_YYYY-MM.txt
│       ├── *_extracted_records_YYYY-MM.xlsx
│       ├── *_final_summary_YYYY-MM.txt
│       ├── *_machine_based_dashboard_YYYY-MM.png
│       ├── *_mold_based_dashboard_YYYY-MM.png
│       └── *_month_performance_dashboard_YYYY-MM.png
├── OrderProgressTracker/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       └── *_auto_status.xlsx
├── PendingProcessor/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       └── *_pending_processor.xlsx
├── ProducingProcessor/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       └── *_producing_processor.xlsx
├── UpdateHistMachineLayout/
│   ├── change_log.txt
│   ├── historical_db/
│   ├── layout_changes.json
│   └── newest/
│       ├── *_Machine_change_layout_timeline.png
│       ├── *_Machine_level_change_layout_details.png
│       ├── *_Machine_level_change_layout_pivot.xlsx
│       └── *_Top_machine_change_layout.png
├── UpdateHistMoldOverview/
│   ├── change_log.txt
│   ├── historical_db/
│   ├── machine_molds/
│   │   ├── change_log.txt
│   │   ├── historical_db/
│   │   └── newest/
│   │       ├── ...
│   │       └── *_machine_molds.json
│   └── newest/
│       ├── *_Bottom_molds_tonnage.png
│       ├── *_Comparison_of_acquisition_and_first_use.png
│       ├── *_Machine_mold_first_run_pair.xlsx
│       ├── *_Mold_machine_first_run_pair.xlsx
│       ├── *_Number_of_molds_first_run_on_each_machine.png
│       ├── *_Time_Gap_of_acquisition_and_first_use.png
│       ├── *_Tonage_machine_mold_not_matched.xlsx
│       ├── *_Tonnage_distribution.png
│       ├── *_Tonnage_proportion.png
│       ├── *_Top_Bottom_molds_gap_time_analysis.png
│       └── *_Top_molds_tonnage.png
├── ValidationOrchestrator/
│   ├── change_log.txt
│   └── newest/
│       └── *_validation_orchestrator.xlsx
├── YearLevelPlotter/
│   ├── change_log.txt
│   ├── historical_db/
│   └── newest/
│       ├── *_extracted_records_YYYY.xlsx
│       ├── *_final_summary_YYYY.txt
│       ├── *_machine_based_year_view_dashboard_YYYY.png
│       ├── *_machine_po_item_dashboard_YYYY_page(x).png
│       ├── *_machine_quantity_dashboard_YYYY_page(x).png
│       ├── *_machine_working_days_dashboard_YYYY_page(x).png
│       ├── *_mold_based_year_view_dashboard_YYYY.png
│       ├── *_mold_quantity_dashboard_YYYY_page(x).png
│       ├── *_mold_shots_dashboard_YYYY_page(x).png
│       ├── *_monthly_performance_dashboard_YYYY.png
│       └── *_year_performance_dashboard_YYYY.png
└── dynamicDatabase/
    ├── productRecords.parquet
    └── purchaseOrders.parquet
```