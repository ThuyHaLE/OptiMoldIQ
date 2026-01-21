OptiMoldIQ
├── agents/
│   ├── __init__.py
│   ├── analyticsOrchestrator/
│   ├── autoPlanner/
│   ├── core_helpers.py
│   ├── dashboardBuilder/
│   ├── dataPipelineOrchestrator/
│   ├── decorators.py
│   ├── optiMoldMaster/
│   ├── orderProgressTracker/
│   ├── taskOrchestrator/
│   ├── utils.py
│   └── validationOrchestrator/
├── configs/
|   ├── module_registry.yaml
│   └── modules/
|       ├── analytics.yaml
|       ├── dashboard.yaml
|       ├── data_pipeline.yaml
│       └── validation.yaml
├── modules/
|   ├── __init__.py
|   ├── analytics_module.py
|   ├── base_module.py
|   ├── dashboard_module.py
|   ├── data_pipeline_module.py
│   └── validation_module.py
└── tests/
    ├── agents_tests/
    │   ├── __init__.py
    │   ├── test_analytics_orchestrator.py
    │   ├── test_daily_workflow.py
    │   ├── test_dashboard_builder.py
    │   ├── test_data_pipeline_orchestrator.py
    │   ├── test_historical_insights_generator.py
    │   ├── test_initial_planer.py
    │   ├── test_order_progress_tracker.py
    │   └── test_validation_orchestrator.py
    ├── mock_database/
    └── set_up_shared_db/
        ├── __init__.py
        └── setup_shared_db.py