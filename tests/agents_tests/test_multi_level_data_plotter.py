from agents.dashboardBuilder.plotters.multi_level_data_plotter import PlotflowConfig, MultiLevelDataPlotter

def test_multi_level_data_plotter(): 
    plotter = MultiLevelDataPlotter(
        PlotflowConfig(
            # Day level
            record_date = '2018-11-06',
            day_visualization_config_path = None, 
            # agents/dashboardBuilder/visualize_data/day_level/visualization_config.json

            # Month level
            record_month = "2019-01",
            month_analysis_date = "2019-01-15",
            month_visualization_config_path = None, 
            # agents.dashboardBuilder.visualize_data.month_level.visualization_config.json

            # Year level
            record_year = "2019",
            year_analysis_date = "2019-12-31",
            year_visualization_config_path = None, 
            # agents.dashboardBuilder.visualize_data.year_level.visualization_config.json

            # Shared paths
            source_path = 'tests/shared_db/DataLoaderAgent/newest',
            annotation_name = 'path_annotations.json',
            databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
            default_dir= 'tests/shared_db',

            # Optimal Processing
            enable_parallel = True,  # Enable parallel processing
            max_workers = None  # Auto-detect optimal worker count
        )
    )

    results = plotter.data_process()

    # Nếu không có exception thì pass
    assert True