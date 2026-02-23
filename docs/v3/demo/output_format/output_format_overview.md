
demo/output_format/
|
├── DataPipelineOrchestrator/
│   ├── itemCompositionSummary.parquet
│   ├── itemInfo.parquet
│   ├── machineInfo.parquet
│   ├── moldInfo.parquet
│   ├── moldSpecificationSummary.parquet
│   ├── productRecords.parquet
│   ├── purchaseOrders.parquet
│   └── resinInfo.parquet
|
├── AnalyticsOrchestrator
|   ├── machine_layout_tracker_result.xlsx
|   ├── mold_machine_pair_tracker_result.xlsx
|   ├── day_level_data_processor_result.xlsx
|   ├── month_level_data_processor_result.xlsx
|   └── year_level_data_processor_result.xlsx
|
├── AutoPlanner
|   ├── pending_order_planner_result.xlsx
|   ├── producing_order_planner_result.xlsx
|   ├── mold_stability_index_calculator_result.xlsx
|   └── weights_hist.xlsx
|
├── OrderProgressTracker
|   └── progress_tracker_result.xlsx
|
├── ValidationOrchestrator
|   └── validation_orchestrator_result.xlsx
|
└── DashboardBuilder
    ├── MachineLayoutVisualizationPipeline/
    │   ├── machine_layout_visualization_pipeline_result.xlsx
    │   └── visualized_results/
    │       ├── Individual_machine_layout_change_times_dashboard.png
    │       └── Machine_layout_change_dashboard.png
    ├── MoldMachinePairVisualizationPipeline/
    |       ├── mold_machine_pair_visualization_pipeline_result.xlsx
    |       └── visualized_results/
    |           ├── Machine_tonage_based_mold_utilization_dashboard.png
    |           ├── Mold_machine_first_pairing_dashboard.png
    |           └── Mold_utilization_dashboard.png
    ├── DayLevelVisualizationPipeline/
    │   ├── day_level_visualization_pipeline_result.xlsx
    │   └── visualized_results/
    │       ├── change_times_all_types_fig_2018-11-06.png
    │       ├── item_based_overview_dashboard_2018-11-06.png
    │       ├── machine_level_mold_analysis_chart_2018-11-06.png
    │       ├── machine_level_yield_efficiency_chart_2018-11-06.png
    │       ├── mold_based_overview_dashboard_2018-11-06.png
    │       ├── shift_level_detailed_yield_efficiency_chart_2018-11-06.png
    │       ├── shift_level_mold_efficiency_chart_2018-11-06.png
    │       └── shift_level_yield_efficiency_chart_2018-11-06.png
    ├── MonthLevelVisualizationPipeline/
    │   ├── month_level_visualization_pipeline_result.xlsx
    |   └── visualized_results/
    │       ├── machine_based_dashboard_2019-01.png
    │       ├── mold_based_dashboard_2019-01.png
    │       └── month_performance_dashboard_2019-01.png
    └── YearLevelVisualizationPipeline/
        ├── visualized_results/
        |   ├── machine_based_year_view_dashboard_2019.png
        |   ├── machine_po_item_dashboard_2019_page1.png
        |   ├── machine_po_item_dashboard_2019_page2.png
        |   ├── machine_quantity_dashboard_2019_page1.png
        |   ├── machine_quantity_dashboard_2019_page2.png
        |   ├── machine_working_days_dashboard_2019_page1.png
        |   ├── machine_working_days_dashboard_2019_page2.png
        |   ├── mold_based_year_view_dashboard_2019.png
        |   ├── mold_quantity_dashboard_2019_page1.png
        |   ├── mold_quantity_dashboard_2019_page2.png
        |   ├── mold_quantity_dashboard_2019_page3.png
        |   ├── mold_quantity_dashboard_2019_page4.png
        |   ├── mold_shots_dashboard_2019_page1.png
        |   ├── mold_shots_dashboard_2019_page2.png
        |   ├── mold_shots_dashboard_2019_page3.png
        |   ├── mold_shots_dashboard_2019_page4.png
        |   ├── monthly_performance_dashboard_2019.png
        |   └── year_performance_dashboard_2019.png
        └── year_level_visualization_pipeline_result.xlsx