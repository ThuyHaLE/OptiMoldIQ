from agents.autoPlanner.initialPlanner.historyBasedProcessor.mold_machine_feature_weight_calculator import MoldMachineFeatureWeightCalculator
from agents.autoPlanner.initialPlanner.historyBasedProcessor.mold_stability_index_calculator import MoldStabilityIndexCalculator
from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator

def test_historical_insights_generator():
    # MoldStabilityIndexCalculator
    stability_index_calculator = MoldStabilityIndexCalculator(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        default_dir = "tests/shared_db/HistoricalInsights",
        efficiency = 0.85,
        loss = 0.03
    )
    stability_index_calculator.process_and_save_result(
        cavity_stability_threshold = 0.6,
        cycle_stability_threshold = 0.4,
        total_records_threshold = 30)
    
    # ValidationOrchestrator
    validation_orchestrator = ValidationOrchestrator(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                    annotation_name = "path_annotations.json",
                                                    databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                    default_dir = "tests/shared_db")

    results = validation_orchestrator.run_validations_and_save_results()

    # OrderProgressTracker
    order_progress_tracker = OrderProgressTracker(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                  annotation_name = "path_annotations.json",
                                                  databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                  folder_path = "tests/shared_db/ValidationOrchestrator",
                                                  target_name = "change_log.txt",
                                                  default_dir = "tests/shared_db")

    results = order_progress_tracker.pro_status()
    
    # MoldMachineFeatureWeightCalculator
    feature_weight_calculator = MoldMachineFeatureWeightCalculator(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'tests/mock_database/sharedDatabaseSchemas.json',
        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = 'change_log.txt',
        default_dir = "tests/shared_db/HistoricalInsights",
        efficiency = 0.85,
        loss = 0.03,
        scaling = 'absolute',
        confidence_weight = 0.3,
        n_bootstrap = 500,
        confidence_level = 0.95,
        min_sample_size = 10,
        feature_weights = None,
        targets = {'shiftNGRate': 'minimize',
                    'shiftCavityRate': 1.0,
                    'shiftCycleTimeRate': 1.0,
                    'shiftCapacityRate': 1.0}
                    )

    feature_weight_calculator.calculate_and_save_report(
        mold_stability_index_folder='tests/shared_db/HistoricalInsights/MoldStabilityIndexCalculator',
        mold_stability_index_target_name='change_log.txt'
        )

    # Nếu không có exception thì pass
    assert True