from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
from agents.autoPlanner.initialPlanner.producing_processor import ProducingProcessor
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.initialPlanner.pending_processor import PendingProcessor, ProcessingConfig
from agents.autoPlanner.initialPlanner.compatibility_based_mold_machine_optimizer import PriorityOrder
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

def test_initial_planer():

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

    # ProducingProcessor
    producing_processor = ProducingProcessor(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'tests/mock_database/sharedDatabaseSchemas.json',
        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = 'change_log.txt',
        mold_stability_index_folder='tests/shared_db/HistoricalInsights/MoldStabilityIndexCalculator',
        mold_stability_index_target_name='change_log.txt',
        mold_machine_weights_hist_path='tests/shared_db/HistoricalInsights/MoldMachineFeatureWeightCalculator/weights_hist.xlsx',
        default_dir = "tests/shared_db/AutoPlanner/InitialPlanner",
        efficiency = 0.85,
        loss = 0.03,
    )

    results = producing_processor.process_and_save_results()

    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))
    
    # PendingProcessor
    config = ProcessingConfig(
        max_load_threshold = 30,
        priority_order = PriorityOrder.PRIORITY_1,
        verbose = True,
        use_sample_data = False
        )

    pending_processor = PendingProcessor(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'tests/mock_database/sharedDatabaseSchemas.json',
        default_dir = "tests/shared_db/AutoPlanner/InitialPlanner",
        producing_processor_folder_path='tests/shared_db/AutoPlanner/InitialPlanner/ProducingProcessor',
        producing_processor_target_name="change_log.txt",
        config=config
    )

    results = pending_processor.run_and_save_results()

    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))
    

    # Nếu không có exception thì pass
    assert True