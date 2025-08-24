from agents.autoPlanner.initialPlanner.pending_processor import PendingProcessor, ProcessingConfig
from agents.autoPlanner.initialPlanner.compatibility_based_mold_machine_optimizer import PriorityOrder
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

def test_pending_processor():
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
        default_dir = "tests/shared_db",
        producing_processor_folder_path='tests/shared_db/ProducingProcessor',
        producing_processor_target_name="change_log.txt",
        config=config
    )

    results = pending_processor.run_and_save_results()

    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))

    assert True