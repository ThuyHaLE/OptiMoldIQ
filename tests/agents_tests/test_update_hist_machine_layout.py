from agents.dataAnalytics.dataChangeUpdate.update_hist_machine_layout import UpdateHistMachineLayout

def test_update_hist_mold_overview():
    updator = UpdateHistMachineLayout(source_path = 'tests/shared_db/DataLoaderAgent/newest',
                        annotation_name = "path_annotations.json",
                        databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                        default_dir="tests/shared_db")
    
    updator.update_and_plot()

    # Nếu không có exception thì pass
    assert True


