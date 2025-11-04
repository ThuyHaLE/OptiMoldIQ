from agents.dashboardBuilder.plotters.year_level_data_plotter import YearLevelPlotter

def test_month_level_data_plotter():

    plotter = YearLevelPlotter(
        record_year = "2019",
        analysis_date = "2019-12-31",
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

