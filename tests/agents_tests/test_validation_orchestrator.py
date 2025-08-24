from agents.validationOrchestrator.validation_orchestrator import ValidationOrchestrator
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

def test_validation_orchestrator():
    validation_orchestrator = ValidationOrchestrator(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                 annotation_name = "path_annotations.json",
                                                 databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                 default_dir = "tests/shared_db")

    results = validation_orchestrator.run_validations_and_save_results()

    colored_reporter = DictBasedReportGenerator(use_colors=True)
    print("\n".join(colored_reporter.export_report(results)))

    # Nếu không có exception thì pass
    assert True