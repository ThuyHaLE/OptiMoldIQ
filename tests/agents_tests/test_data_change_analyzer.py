from agents.analyticsOrchestrator.dataChangeAnalyzer.data_change_analyzer import DataChangeAnalyzer

def test_data_change_analyzer():
    analyzer = DataChangeAnalyzer(
      source_path = 'tests/shared_db/DataLoaderAgent/newest', 
      annotation_name = "path_annotations.json",
      databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
      machine_layout_output_dir = "tests/shared_db/UpdateHistMachineLayout",
      mold_overview_output_dir = "tests/shared_db/UpdateHistMoldOverview",
      min_workers=3,           # Require at least 3 workers
      max_workers=6,           # Don't exceed 6 workers
      parallel_mode="thread"   # Use thread-based parallelism
      )
    
    # Force parallel execution (=True) even if resources are limited
    analyzer.analyze_changes(force_parallel=False)
    
    # Print summary
    print(analyzer.get_analysis_summary())

    # Nếu không có exception thì pass
    assert True

