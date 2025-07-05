from agents.decorators import validate_init_dataframes
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
from pathlib import Path
import os
import pandas as pd
from typing import Dict, Any

from agents.validationOrchestrator.dynamic_cross_data_validator import DynamicCrossDataValidator
from agents.validationOrchestrator.static_cross_data_checker import StaticCrossDataChecker
from agents.validationOrchestrator.po_required_critical_validator import PORequiredCriticalValidator


@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "itemInfo_df": list(self.databaseSchemas_data['statisticDB']['itemInfo']['dtypes'].keys()),
    "resinInfo_df": list(self.databaseSchemas_data['statisticDB']['resinInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['statisticDB']['itemCompositionSummary']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['statisticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['statisticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['statisticDB']['moldInfo']['dtypes'].keys()),
})

class ValidationOrchestrator:
    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        """
        Initialize the validator with data paths and load required dataframes.

        Args:
            source_path: Path to the data source directory
            annotation_name: Name of the path annotations file
            databaseSchemas_path: Path to database schemas JSON file
            default_dir: Default directory for output files
        """
        self.logger = logger.bind(class_="ValidationOrchestrator")

        self.checking_df_name = ['productRecords', 'purchaseOrders']
        self.source_path = source_path
        self.annotation_name = annotation_name
        self.databaseSchemas_path = databaseSchemas_path

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )
        self.path_annotation = load_annotation_path(self.source_path, self.annotation_name)

        # Load all required DataFrames
        self._load_dataframes()

        self.filename_prefix = "validation_orchestrator"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "ValidationOrchestrator"

    def _load_dataframes(self) -> None:
        """Load all required DataFrames with consistent error handling"""
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('purchaseOrders', 'purchaseOrders_df'),
            ('itemInfo', 'itemInfo_df'),
            ('resinInfo', 'resinInfo_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df')
        ]

        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                df = pd.read_parquet(path)
                setattr(self, attr_name, df)
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def run_validations(self, **kwargs) -> Dict[str, Any]:
      StaticCrossDataChecker_data = StaticCrossDataChecker(self.checking_df_name,
                                                           self.source_path,
                                                           self.annotation_name,
                                                           self.databaseSchemas_path,
                                                           self.default_dir).run_validations()

      static_mismatch_warnings_purchase = StaticCrossDataChecker_data['purchaseOrders']
      static_mismatch_warnings_product = StaticCrossDataChecker_data['productRecords']

      PORequiredCriticalValidator_data = PORequiredCriticalValidator(self.source_path,
                                                                     self.annotation_name,
                                                                     self.databaseSchemas_path,
                                                                     self.default_dir).run_validations()

      po_required_mismatch_warnings = PORequiredCriticalValidator_data.copy()

      DynamicCrossDataValidator_data = DynamicCrossDataValidator(self.source_path,
                                                                 self.annotation_name,
                                                                 self.databaseSchemas_path,
                                                                 self.default_dir).run_validations()

      dynamic_invalid_warnings = DynamicCrossDataValidator_data['invalid_warnings']
      dynamic_mismatch_warnings = DynamicCrossDataValidator_data['mismatch_warnings']

      final_df = pd.concat([dynamic_mismatch_warnings,
                            static_mismatch_warnings_purchase,
                            static_mismatch_warnings_product,
                            po_required_mismatch_warnings], ignore_index=True)

      return {'static_mismatch': {
                  'purchaseOrders': static_mismatch_warnings_purchase,
                  'productRecords': static_mismatch_warnings_product
              },
              'po_required_mismatch': po_required_mismatch_warnings,
              'dynamic_mismatch': {
                  'invalid_items': dynamic_invalid_warnings,
                  'info_mismatches': dynamic_mismatch_warnings
              },
              'combined_all': {
                  'item_invalid_warnings': dynamic_invalid_warnings,
                  'po_mismatch_warnings': final_df}
          }

    def run_validations_and_save_results(self, **kwargs) -> None:
        """Run validations and save results to Excel files"""
        try:
            final_results = self.run_validations(**kwargs)

            self.logger.info("Exporting results to Excel...")
            save_output_with_versioning(
                final_results['combined_all'],
                self.output_dir,
                self.filename_prefix,
            )
            self.logger.info("Results exported successfully!")

        except Exception as e:
            self.logger.error("Failed to save results: {}", str(e))
            raise