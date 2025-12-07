from agents.autoPlanner.initialPlanner.processor.producing_processor import (
    ProducingProcessor, ProducingProcessorConfig)

from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.feature_weight_config import FeatureWeightConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.configs.mold_stability_config import MoldStabilityConfig

from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.historical_features_extractor import (
    HistoricalFeaturesExtractor, FeaturesExtractorConfig)

from agents.autoPlanner.initialPlanner.processor.pending_processor import (
    ExcelSheetMapping, PendingProcessorConfig, PendingProcessor)
from agents.autoPlanner.initialPlanner.optimizer.compatibility_based_mold_machine_optimizer import PriorityOrder

def test_initial_planner():
    
    # ----------------------------- #
    # HISTORICAL FEATURES EXTRACTOR
    # ----------------------------- #

    # MoldStabilityConfig
    mold_stability_config = MoldStabilityConfig(
        source_path = 'tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',
        default_dir = "tests/shared_db/HistoricalFeaturesExtractor",
        efficiency = 0.85,
        loss = 0.03,
        cavity_stability_threshold  = 0.6,
        cycle_stability_threshold  = 0.4,
        total_records_threshold = 30)

    # FeatureWeightConfig
    feature_weight_config = FeatureWeightConfig(
        source_path = 'tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'database/sharedDatabaseSchemas.json',

        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = "change_log.txt",

        default_dir = "tests/shared_db/HistoricalFeaturesExtractor",

        mold_stability_index_folder = 'tests/shared_db/HistoricalFeaturesExtractor/MoldStabilityIndexCalculator',
        mold_stability_index_target_name = "change_log.txt",

        efficiency = 0.85,
        loss = 0.03,

        scaling = 'absolute',
        confidence_weight = 0.3,
        n_bootstrap = 500,
        confidence_level = 0.95,
        min_sample_size = 10,
        feature_weights = None,

        targets = {
                'shiftNGRate': 'minimize',
                'shiftCavityRate': 1.0,
                'shiftCycleTimeRate': 1.0,
                'shiftCapacityRate': 1.0,
            }
    )

    # FeaturesExtractorConfig
    features_extractor_config = FeaturesExtractorConfig(
        # Phase 1 - MoldStabilityIndexCalculator configs
        mold_stability_config = mold_stability_config,

        # Phase 2 - OrderProgressTracker configs
        source_path = 'tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',

        folder_path = "tests/shared_db/ValidationOrchestrator",
        target_name = "change_log.txt",
        default_dir = "tests/shared_db",
        
        # Phase 3 - MoldMachineFeatureWeightCalculator configs
        feature_weight_config = feature_weight_config
        )


    extractor = HistoricalFeaturesExtractor(config = features_extractor_config)
    result, log_str = extractor.run_extraction()

    # ------------------- #
    # PRODUCING PROCESSOR
    # ------------------- #

    config = ProducingProcessorConfig(
        source_path = 'tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'database/sharedDatabaseSchemas.json',
        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = "change_log.txt",
        default_dir = "tests/shared_db/AutoPlanner/InitialPlanner",
        mold_stability_index_folder = "tests/shared_db/HistoricalFeaturesExtractor/MoldStabilityIndexCalculator",
        mold_stability_index_target_name = "change_log.txt",
        mold_machine_weights_hist_path = "tests/shared_db/HistoricalFeaturesExtractor/MoldMachineFeatureWeightCalculator/weights_hist.xlsx",
        efficiency = 0.85,
        loss = 0.03
    )
    processor = ProducingProcessor(config = config)
    results, log_str = processor.process_and_save_results()

    # ----------------- #
    # PENDING PROCESSOR
    # ----------------- #

    config = PendingProcessorConfig(
        source_path = 'tests/shared_db/DataPipelineOrchestrator/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'database/sharedDatabaseSchemas.json',

        default_dir = "tests/shared_db/AutoPlanner/InitialPlanner",

        producing_processor_folder_path = 'tests/shared_db/AutoPlanner/InitialPlanner/ProducingProcessor',
        producing_processor_target_name = "change_log.txt",

        max_load_threshold = 30,
        priority_order = PriorityOrder.PRIORITY_1,
        log_progress_interval = 5,
        verbose = True,
        use_sample_data = False
    )

    processor = PendingProcessor(
        config = config,
        sheet_mapping = ExcelSheetMapping())

    results, log_str = processor.process_and_save_results()

    assert True