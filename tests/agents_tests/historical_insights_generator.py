from agents.autoPlanner.initialPlanner.historyBasedProcessor.mold_machine_feature_weight_calculator import MoldMachineFeatureWeightCalculator
from agents.autoPlanner.initialPlanner.historyBasedProcessor.mold_stability_index_calculator import MoldStabilityIndexCalculator

def test_historical_insights_generator():
    stability_index_calculator = MoldStabilityIndexCalculator(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        default_dir = "tests/shared_db",
        efficiency = 0.85,
        loss = 0.03
    )
    stability_index_calculator.process_and_save_result(
        cavity_stability_threshold = 0.6,
        cycle_stability_threshold = 0.4,
        total_records_threshold = 30)
    
    feature_weight_calculator = MoldMachineFeatureWeightCalculator(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'tests/mock_database/sharedDatabaseSchemas.json',
        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = 'change_log.txt',
        default_dir = "tests/shared_db",
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
        mold_stability_index_folder='tests/shared_db/MoldStabilityIndexCalculator',
        mold_stability_index_target_name='change_log.txt'
        )

    # Nếu không có exception thì pass
    assert True