from agents.autoPlanner.initialPlanner.producing_processor import ProducingProcessor
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

def test_producing_processor():
    processor = ProducingProcessor(
        source_path = 'tests/shared_db/DataLoaderAgent/newest',
        annotation_name = "path_annotations.json",
        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
        sharedDatabaseSchemas_path = 'tests/mock_database/sharedDatabaseSchemas.json',
        folder_path = 'tests/shared_db/OrderProgressTracker',
        target_name = 'change_log.txt',
        mold_stability_index_folder='tests/shared_db/MoldStabilityIndexCalculator',
        mold_stability_index_target_name='change_log.txt',
        mold_machine_weights_hist_path='tests/shared_db/MoldMachineFeatureWeightCalculator/weights_hist.xlsx',
        default_dir = "tests/shared_db",
        efficiency = 0.85,
        loss = 0.03,
    )

    results = processor.process_and_save_results()

    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))

    assert True