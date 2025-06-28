from agents.crossDataChecker.po_required_critical_validator import PORequiredCriticalValidator

def test_po_required_critical_validator():
    required_critical_validator = PORequiredCriticalValidator(checking_df_name = ['productRecords', 'purchaseOrders'],
                                                              source_path = 'tests/shared_db/DataLoaderAgent/newest',
                                                              annotation_name = "path_annotations.json",
                                                              databaseSchemas_path = 'tests/mock_database/databaseSchemas.json',
                                                              default_dir = "tests/shared_db")
    required_critical_validator.run_validations_and_save_results()

    # Nếu không có exception thì pass
    assert True