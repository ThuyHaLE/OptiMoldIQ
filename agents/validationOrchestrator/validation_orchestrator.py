from agents.decorators import validate_init_dataframes
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning, ConfigReportMixin
from pathlib import Path
import os
import pandas as pd
from typing import Dict, Any
from datetime import datetime

from agents.validationOrchestrator.dynamic_cross_data_validator import DynamicCrossDataValidator
from agents.validationOrchestrator.static_cross_data_checker import StaticCrossDataChecker
from agents.validationOrchestrator.po_required_critical_validator import PORequiredCriticalValidator
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "itemInfo_df": list(self.databaseSchemas_data['staticDB']['itemInfo']['dtypes'].keys()),
    "resinInfo_df": list(self.databaseSchemas_data['staticDB']['resinInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

class ValidationOrchestrator(ConfigReportMixin):

    """
    Main orchestrator class that coordinates multiple validation processes for manufacturing data.
    
    This class manages the validation of product records, purchase orders, and related 
    manufacturing data by running three types of validations:
    1. Static cross-data validation
    2. Purchase order required field validation  
    3. Dynamic cross-data validation
    """

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        """
        Initialize the ValidationOrchestrator with data paths and load required dataframes.

        Args:
            source_path: Path to the data source directory containing the latest data files
            annotation_name: Name of the JSON file containing path annotations for data files
            databaseSchemas_path: Path to database schemas JSON file defining data structure
            default_dir: Default directory for saving output validation results
        """

        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ValidationOrchestrator")

        # Define which DataFrames need to be validated (dynamic data that changes frequently)
        self.checking_df_name = ['productRecords', 'purchaseOrders']

        # Store initialization parameters
        self.source_path = source_path
        self.annotation_name = annotation_name
        self.databaseSchemas_path = databaseSchemas_path

        # Load database schema definitions and file path annotations
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )
        self.path_annotation = load_annotation_path(self.source_path, self.annotation_name)

        # Load all required DataFrames from parquet files
        self._load_dataframes()

        # Set up output configuration for saving validation results
        self.filename_prefix = "validation_orchestrator"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "ValidationOrchestrator"

    def _load_dataframes(self) -> None:
        
        """
        Load all required DataFrames from parquet files with consistent error handling.
        
        This method loads both dynamic data (productRecords, purchaseOrders) and 
        static reference data (itemInfo, resinInfo, machineInfo, etc.) needed for validation.
        """

        # Define mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),                    # Dynamic: Production records
            ('purchaseOrders', 'purchaseOrders_df'),                    # Dynamic: Purchase order data
            ('itemInfo', 'itemInfo_df'),                                # Static: Item master data
            ('resinInfo', 'resinInfo_df'),                              # Static: Resin specifications
            ('machineInfo', 'machineInfo_df'),                          # Static: Machine specifications
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),# Static: Mold pecifications
            ('moldInfo', 'moldInfo_df'),                                # Static: Mold information
            ('itemCompositionSummary', 'itemCompositionSummary_df')     # Static: Item composition
        ]

        # Load each DataFrame with error handling
        for path_key, attr_name in dataframes_to_load:

            # Get file path from annotations
            path = self.path_annotation.get(path_key)

            # Validate path exists
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                df = pd.read_parquet(path)
                # Set as instance attribute
                setattr(self, attr_name, df)
                # Log successful load with shape and column info
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def run_validations(self, **kwargs) -> Dict[str, Any]:
      
        """
        Execute all validation processes and return consolidated results.
        
        This method runs three types of validations:
        1. StaticCrossDataChecker: Validates data consistency against static reference data
        2. PORequiredCriticalValidator: Validates required fields in purchase orders
        3. DynamicCrossDataValidator: Validates cross-references between dynamic datasets
        
        Args:
            **kwargs: Additional parameters passed to individual validators
            
        Returns:
            Dict containing validation results organized by validation type and severity
        """
      
        # 1. Run static cross-data validation
        StaticCrossDataChecker_data = StaticCrossDataChecker(self.checking_df_name,
                                                            self.source_path,
                                                            self.annotation_name,
                                                            self.databaseSchemas_path,
                                                            self.default_dir).run_validations()

        # Extract static validation warnings by dataset
        static_mismatch_warnings_purchase = StaticCrossDataChecker_data['purchaseOrders']
        static_mismatch_warnings_product = StaticCrossDataChecker_data['productRecords']

        # 2. Run purchase order required field validation
        PORequiredCriticalValidator_data = PORequiredCriticalValidator(self.source_path,
                                                                        self.annotation_name,
                                                                        self.databaseSchemas_path,
                                                                        self.default_dir).run_validations()

        # Copy PO validation results
        po_required_mismatch_warnings = PORequiredCriticalValidator_data.copy()

        # 3. Run dynamic cross-data validation
        DynamicCrossDataValidator_data = DynamicCrossDataValidator(self.source_path,
                                                                    self.annotation_name,
                                                                    self.databaseSchemas_path,
                                                                    self.default_dir).run_validations()

        # Extract dynamic validation results
        dynamic_invalid_warnings = DynamicCrossDataValidator_data['invalid_warnings']
        dynamic_mismatch_warnings = DynamicCrossDataValidator_data['mismatch_warnings']

        # Combine all mismatch warnings into a single DataFrame for consolidated reporting
        final_df = pd.concat([dynamic_mismatch_warnings,
                                static_mismatch_warnings_purchase,
                                static_mismatch_warnings_product,
                                po_required_mismatch_warnings], ignore_index=True)

        # Return structured validation results
        return {
            # Static validation results (reference data mismatches)
            'static_mismatch': {
                'purchaseOrders': static_mismatch_warnings_purchase,
                'productRecords': static_mismatch_warnings_product
                },
            # Purchase order required field validation results
            'po_required_mismatch': po_required_mismatch_warnings,
            # Dynamic validation results (cross-dataset inconsistencies)
            'dynamic_mismatch': {
                'invalid_items': dynamic_invalid_warnings,
                'info_mismatches': dynamic_mismatch_warnings
                },
            # Combined results for reporting
            'combined_all': {
                'item_invalid_warnings': dynamic_invalid_warnings,
                'po_mismatch_warnings': final_df}
            }

    def run_validations_and_save_results(self, **kwargs) -> None:
        
        """
        Execute validation processes and save results to Excel files.
        
        This method runs all validations and exports the combined results to Excel files
        with automatic versioning to prevent overwrites.
        
        Args:
            **kwargs: Additional parameters passed to validation methods
            
        Raises:
            Exception: If validation execution or file saving fails
        """

        try:
            # Execute validations
            final_results = self.run_validations(**kwargs)

            # Generate validation summary
            reporter = DictBasedReportGenerator(use_colors=False)
            validation_summary = "\n".join(reporter.export_report(final_results))

            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str)

            validation_log_lines = [config_header]
            validation_log_lines.append(f"--Processing Summary--\n")
            validation_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")

            # Export results to Excel files with versioning
            self.logger.info("Exporting results to Excel...")
            output_exporting_log = save_output_with_versioning(
                data = final_results['combined_all'],
                output_dir = self.output_dir,
                filename_prefix = self.filename_prefix,
                report_text = validation_summary
            )
            self.logger.info("Results exported successfully!")
            validation_log_lines.append(f"{output_exporting_log}")

            validation_log_str = "\n".join(validation_log_lines)

            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(validation_log_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)
            
            return final_results, validation_log_str

        except Exception as e:
            self.logger.error("Failed to save results: {}", str(e))
            raise