from agents.dashboardBuilder.plotters.day_level_data_plotter import DayLevelDataPlotter

def test_day_level_data_plotter():
    plotter = DayLevelDataPlotter(
        selected_date="2018-11-01",
        source_path='tests/shared_db/DataLoaderAgent/newest',
        annotation_name="path_annotations.json",
        databaseSchemas_path='tests/mock_database/databaseSchemas.json',
        default_dir="tests/shared_db"
    )
    plotter.plot_all()

    # Nếu không có exception thì pass
    assert True