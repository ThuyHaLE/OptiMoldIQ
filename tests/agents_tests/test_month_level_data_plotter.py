from agents.dashboardBuilder.plotters.month_level_data_plotter import MonthLevelDataPlotter

def test_month_level_data_plotter():

    plotter = MonthLevelDataPlotter(
        record_month = "2019-01",
        analysis_date = "2019-01-15",
        source_path='tests/shared_db/DataLoaderAgent/newest',
        annotation_name="path_annotations.json",
        databaseSchemas_path='tests/mock_database/databaseSchemas.json',
        default_dir="tests/shared_db",
        enable_parallel=True,  # Enable parallel processing
        max_workers=None  # Auto-detect optimal worker count
        )
    plotter.plot_all()

    # Nếu không có exception thì pass
    assert True