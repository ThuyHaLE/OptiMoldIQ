from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import os
from typing import Dict, Tuple, Any, List

from datetime import datetime
from agents.utils import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

class DynamicCrossDataValidator(ConfigReportMixin):
    
    """
    A validator class for cross-referencing production records with standard reference data.

    This class validates that production records (items, molds, machines, compositions)
    match against standard reference data and generates detailed warnings for mismatches.
    
    The validation process includes:
    - Loading production records and reference data
    - Cross-referencing items, molds, machines, and compositions
    - Identifying mismatches and generating actionable warnings
    - Exporting results to Excel files for review
    """

    # Define requirements
    REQUIRED_FIELDS = {
        'databaseSchemas_path': str,
        'annotation_path': str,
        'validation_dir': str
    }

    def __init__(self, config: SharedSourceConfig):
        
        """
        Initialize the DynamicCrossDataValidator.
        
        Args:
            config: SharedSourceConfig containing processing parameters
            Including:
                - annotation_path: Path to the JSON file containing path annotations
                - databaseSchemas_path: Path to database schemas JSON file for validation
                - validation_dir: Default directory for saving output files
        """

        self._capture_init_args()

        # Initialize logger for this class
        self.logger = logger.bind(class_="DynamicCrossDataValidator")

        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
    
        self.config = config

        # Load database schema configuration for column validation
        self.databaseSchemas_data = load_annotation_path(
            Path(self.config.databaseSchemas_path).parent,
            Path(self.config.databaseSchemas_path).name
        )
        # Load path annotations that map logical names to actual file paths
        self.path_annotation = load_annotation_path(
            Path(self.config.annotation_path).parent, 
            Path(self.config.annotation_path).name
        )

        # Load all required DataFrames from parquet files
        self._load_dataframes()

        # Set up output configuration
        self.filename_prefix = "dynamic_cross_validator"
        self.output_dir = Path(self.config.validation_dir) / "DynamicCrossDataValidator"

    def _load_dataframes(self) -> None:
        
        """
        Load all required DataFrames from parquet files with consistent error handling.
        
        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
        - itemCompositionSummary_df: Item composition details (resin, masterbatch, etc.)
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df')
        ]
        
        # Load each DataFrame with error handling
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)

            # Validate path exists
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                df = pd.read_parquet(path)
                setattr(self, attr_name, df)
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def run_validations(self, 
                        save_results: bool = False,
                        **kwargs) -> Dict[str, Any]:

        """
        Run all validation checks and return comprehensive results.
        
        This is the main validation pipeline that:
        1. Prepares production data by merging records with machine info
        2. Prepares standard reference data from multiple sources
        3. Analyzes mismatches between production and standard data
        4. Generates detailed warnings for each type of mismatch

        Returns:
            Dict containing:
            - mismatch_warnings: DataFrame with production record mismatches
            - invalid_warnings: DataFrame with invalid/missing reference data
        """

        self.logger.info("Starting DynamicCrossDataValidator ...")

        start_time = datetime.now()
        # Generate config header using mixin
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, 
                                                     required_only=True)
        
        # Initialize validation log entries for entire processing run
        validation_log_entries = [config_header]
        validation_log_entries.append(f"--Processing Summary--\n")
        validation_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

        try:
            # Step 1: Prepare production data by merging product records with machine info
            self.logger.info("Preparing production data...")
            production_df = self._prepare_production_data(
                self.productRecords_df,
                self.machineInfo_df
            )

            # Step 2: Prepare standard reference data from multiple sources
            self.logger.info("Preparing standard reference data...")
            standard_df, total_invalids = self._prepare_standard_data(
                self.moldSpecificationSummary_df,
                self.moldInfo_df,
                self.itemCompositionSummary_df
            )

            # Step 3: Analyze mismatches between production and standard data
            self.logger.info("Analyzing mismatches...")
            results = self._analyze_mismatches(production_df, standard_df)

            # Step 4: Generate detailed warnings for each mismatch type
            self.logger.info("Generating warnings...")
            mismatch_warnings = self._generate_warnings(results)
            invalid_warnings = self._process_invalid_item_warnings(total_invalids)

            # Combine all warnings into final results
            results['mismatch_warnings'] = mismatch_warnings
            results['invalid_warnings'] = invalid_warnings

            final_result = DynamicCrossDataValidator._convert_results(results)

            # Log summary information for user review
            validation_log_entries.append("Validation Summary:")
            validation_log_entries.append(f"- Invalid warnings: {len(final_result['invalid_warnings'])} items")
            validation_log_entries.append(f"- Mismatch warnings: {len(final_result['mismatch_warnings'])} items")
            
            reporter = DictBasedReportGenerator(use_colors=False)
            validation_summary = "\n".join(reporter.export_report(final_result))
            validation_log_entries.append(f"{validation_summary}")

            if save_results:
                try:
                    # Export results to Excel with versioning
                    self.logger.info("Exporting results to Excel...")
                    output_exporting_log = save_output_with_versioning(
                        data = final_result,
                        output_dir = self.output_dir,
                        filename_prefix = self.filename_prefix,
                        report_text = validation_summary
                    )
                    self.logger.info("Results exported successfully!")
                    validation_log_entries.append(f"{output_exporting_log}")

                except Exception as e:
                    self.logger.error("Failed to save results: {}", str(e))
                    raise
            
            validation_log_str = "\n".join(validation_log_entries)
            self.logger.info("✅ Process finished!!!")

            return final_result, validation_log_str
        
        except Exception as e:
            self.logger.error("❌ Validation failed: {}", str(e))
            raise

    @staticmethod
    def _convert_results(results):
      
        """
        Convert validation results into properly structured DataFrames.
        
        This method ensures consistent DataFrame structure for both warning types:
        - invalid_warnings: Items that don't exist in reference data
        - mismatch_warnings: Production records that don't match reference data
        
        Args:
            results: Raw validation results dictionary
            
        Returns:
            Dict with properly structured DataFrames
        """
       
        final_results = {}

        # Process invalid warnings with proper column structure
        if results['invalid_warnings']['invalid_item']:
            final_results['invalid_warnings'] = pd.DataFrame(results['invalid_warnings']['invalid_item'])
        else:
            final_results['invalid_warnings'] = DynamicCrossDataValidator._create_empty_warning_dataframe('invalid')

        # Process mismatch warnings by combining all warning types
        all_mismatch_warnings = []
        for warning_type, warnings in results['mismatch_warnings'].items():
            all_mismatch_warnings.extend(warnings)

        if all_mismatch_warnings:
            final_results['mismatch_warnings'] = pd.DataFrame(all_mismatch_warnings)
        else:
            final_results['mismatch_warnings'] = DynamicCrossDataValidator._create_empty_warning_dataframe('mismatch')

        return final_results

    @staticmethod
    def _check_invalid(df: pd.DataFrame) -> Dict[str, List[str]]:
        
        """
        Check for invalid (null) values in critical columns and collect affected items.
        
        This method identifies rows with null values in any column, which indicates
        incomplete or invalid data that needs to be addressed.

        Args:
            df: DataFrame to check for null values

        Returns:
            Dictionary with lists of invalid item codes and names
        """

        # Find all rows that have null values in any column
        invalid_rows = df[df.isnull().any(axis=1)].copy()
        invalid_details = {'itemCode': [], 'itemName': []}

        # Process each invalid row to collect item information
        for r in invalid_rows.index:
            for c in df.columns:
                if pd.isnull(df.at[r, c]):
                    logger.debug(f"Null value found at row {r}, column '{c}'")

                    # Extract item identification information
                    item_code = df.at[r, 'itemCode']
                    item_name = df.at[r, 'itemName']
                    
                    # Add to invalid details if not already present
                    if item_code not in invalid_details['itemCode']:
                        invalid_details['itemCode'].append(item_code)
                    if item_name not in invalid_details['itemName']:
                        invalid_details['itemName'].append(item_name)

        return invalid_details

    @staticmethod
    def _build_component_string(row: pd.Series) -> str:
        
        """
        Build a standardized component string from material composition data.
        
        This method creates a consistent format for item compositions by combining:
        - Plastic Resin (required): code_name format
        - Color Masterbatch (optional): code_name format
        - Additive Masterbatch (optional): code_name format
        
        Components are separated by " | " for easy parsing.

        Args:
            row: DataFrame row containing component information

        Returns:
            Formatted component string (e.g., "PR001_PET | CM002_Blue | AM003_UV")
            Returns pd.NA if required plastic resin fields are missing
        """

        parts = []

        # Plastic Resin is required - return pd.NA if missing
        if pd.notna(row.get('plasticResin')) and pd.notna(row.get('plasticResinCode')):
            parts.append(f"{row['plasticResinCode']}_{row['plasticResin']}")
        else:
            return pd.NA

        # Color Masterbatch is optional - add if present
        if pd.notna(row.get('colorMasterbatch')) and pd.notna(row.get('colorMasterbatchCode')):
            parts.append(f"{row['colorMasterbatchCode']}_{row['colorMasterbatch']}")

        # Additive Masterbatch is optional - add if present
        if pd.notna(row.get('additiveMasterbatch')) and pd.notna(row.get('additiveMasterbatchCode')):
            parts.append(f"{row['additiveMasterbatchCode']}_{row['additiveMasterbatch']}")

        return " | ".join(parts)

    def _prepare_production_data(self, productRecords_df: pd.DataFrame,
                               machineInfo_df: pd.DataFrame) -> pd.DataFrame:
        
        """
        Prepare production data for validation by merging product records with machine info.
        
        This method:
        1. Filters product records to include only those with valid PO notes
        2. Builds standardized item composition strings
        3. Merges with machine information to get tonnage data
        4. Ensures consistent data types for matching

        Args:
            productRecords_df: Raw product records from production
            machineInfo_df: Machine specifications including tonnage

        Returns:
            Prepared production DataFrame ready for validation
        """

        # Create working copy and filter for valid records
        product_df = productRecords_df.copy()
        product_df = product_df[product_df['poNote'].notna()].reset_index(drop=True)

        self.logger.debug("Filtered product records: {:,} rows", len(product_df))

        # Build standardized item composition strings
        product_df['item_composition'] = product_df.apply(
            self._build_component_string, axis=1
        )

        # Select only columns needed for validation to reduce memory usage
        product_cols = [
            'recordDate', 'workingShift', 'poNote', 'itemCode', 'itemName',
            'machineNo', 'machineCode', 'moldNo', 'item_composition'
        ]
        machine_cols = ['machineCode', 'machineTonnage']

        # Merge production records with machine information
        machine_df = machineInfo_df.copy()
        result_df = pd.merge(
            product_df[product_cols],
            machine_df[machine_cols],
            on='machineCode',
            how='left'
        )

        # Convert machine tonnage to string for consistent matching with reference data
        result_df['machineTonnage'] = result_df['machineTonnage'].astype(str)

        self.logger.debug("Production data prepared: {:,} rows", len(result_df))
        return result_df

    @staticmethod
    def _process_invalid_item_warnings(invalid_details: Dict[str, Dict[str, List[str]]]) -> Dict[str, List[Dict[str, Any]]]:
        
        """
        Process invalid item warnings from null value checks in reference data.
        
        This method creates structured warnings for items that are missing or invalid
        in the reference databases, helping users identify data quality issues.

        Args:
            invalid_details: Dictionary containing invalid item details by database

        Returns:
            Dictionary with processed invalid item warnings
        """

        # Initialize with empty list to ensure consistent structure
        invalid_results = {"invalid_item": []}

        # Process each database's invalid items
        for df_name, invalid_data in invalid_details.items():

            # Skip if no invalid items found
            if not invalid_data['itemCode'] and not invalid_data['itemName']:
                continue

            # Create combinations of invalid codes and names to avoid duplicates
            invalid_items = set()
            for code in invalid_data['itemCode']:
                for name in invalid_data['itemName']:
                    invalid_items.add((code, name))

            # Generate warning entry for each invalid item
            for item_code, item_name in invalid_items:
                context_info = [item_code, item_name]
                mismatch_type = f"{'_and_'.join(context_info)}_does_not_exist_in_{df_name}"
                required_action = f"update_{df_name}_or_double_check_related_databases"

                # Create human-readable message
                message = f"({', '.join(context_info)}) - Mismatch: {mismatch_type}. Please {required_action}"

                # Create structured warning entry
                entry = {
                    'itemInfo': ', '.join(context_info),
                    'warningType': f'item_invalid_in_{df_name}',
                    'mismatchType': f"item_does_not_exist_in_{df_name}",
                    'requiredAction': required_action,
                    'message': message
                }

                invalid_results["invalid_item"].append(entry)

        return invalid_results

    def _prepare_standard_data(self, moldSpecificationSummary_df: pd.DataFrame,
                             moldInfo_df: pd.DataFrame,
                             itemCompositionSummary_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, List[str]]]]:
        
        """
        Prepare standard reference data by processing and merging multiple data sources.
        
        This method creates a comprehensive reference dataset by:
        1. Processing mold specifications and expanding multiple mold lists
        2. Merging with mold information to get machine tonnage requirements
        3. Processing item compositions and grouping by item
        4. Creating final reference data with all valid combinations
        
        Args:
            moldSpecificationSummary_df: Mold specifications with item-mold mappings
            moldInfo_df: Detailed mold information including tonnage
            itemCompositionSummary_df: Item composition details

        Returns:
            Tuple of (standard_df, total_invalids) where:
            - standard_df: Complete reference data for validation
            - total_invalids: Dictionary of invalid items found in each source
        """

        total_invalids = {}

        # Step 1: Process mold specifications
        mold_spec_df = moldSpecificationSummary_df.copy()
        mold_spec_df = mold_spec_df.rename(columns={"moldList": "moldNo"})

        # Split mold lists (e.g., "MOLD1/MOLD2/MOLD3" -> ["MOLD1", "MOLD2", "MOLD3"])
        mold_spec_df['moldNo'] = mold_spec_df['moldNo'].str.split('/')

        # Expand mold lists to individual rows and merge with mold info
        mold_exploded = mold_spec_df.explode('moldNo')[['itemCode', 'itemName', 'moldNo']]
        mold_info_df = moldInfo_df.copy()
        mold_machine_df = pd.merge(
            mold_exploded,
            mold_info_df[['moldNo', 'moldName', 'machineTonnage']],
            on='moldNo',
            how='left'
        )

        # Step 2: Check for invalid combinations in mold data
        invalids = self._check_invalid(mold_machine_df)
        if invalids['itemCode'] or invalids['itemName']:
            self.logger.warning(
                'Invalid items found in mold specifications: codes={}, names={}',
                invalids['itemCode'], invalids['itemName']
            )
        total_invalids['moldSpecificationSummary_and_moldInfo'] = invalids

        # Step 3: Process machine tonnage data
        mold_machine_df = mold_machine_df.dropna()

        # Split machine tonnage lists (e.g., "100T/200T" -> ["100T", "200T"])
        mold_machine_df['machineTonnage'] = mold_machine_df['machineTonnage'].str.split('/')
        mold_machine_final = mold_machine_df.explode('machineTonnage')

        # Step 4: Process item compositions
        item_comp_df = itemCompositionSummary_df.copy()
        item_comp_df['item_composition'] = item_comp_df.apply(
            self._build_component_string, axis=1
        )

        # Group compositions by item to handle multiple compositions per item
        item_comp_grouped = (
            item_comp_df
            .groupby(['itemCode', 'itemName'])['item_composition']
            .agg(lambda x: x.dropna().unique())
            .reset_index()
        )

        # Step 5: Create final reference data by merging all sources
        standard_df = pd.merge(
            mold_machine_final[['itemCode', 'itemName', 'moldNo', 'machineTonnage']],
            item_comp_grouped,
            on=['itemCode', 'itemName'],
            how='left'
        )

        # Step 6: Check for invalid combinations in final merge
        second_invalids = self._check_invalid(standard_df)
        if second_invalids['itemCode'] or second_invalids['itemName']:
            self.logger.warning(
                'Invalid items found in item compositions: codes={}, names={}',
                second_invalids['itemCode'], second_invalids['itemName']
            )
        total_invalids['itemCompositionSummary'] = second_invalids

        # Step 7: Clean up and expand compositions
        standard_df = standard_df.dropna()
        standard_df = standard_df.explode('item_composition')

        self.logger.debug("Standard data prepared: {:,} rows", len(standard_df))
        return standard_df[['itemCode', 'itemName', 'moldNo', 'machineTonnage', 'item_composition']], total_invalids

    @staticmethod
    def _analyze_mismatches(production_df: pd.DataFrame, standard_df: pd.DataFrame) -> Dict[str, Any]:
        
        """
        Analyze mismatches between production and standard data at multiple levels.
        
        This method performs hierarchical mismatch analysis:
        1. Items level: Check if items exist in reference data
        2. Molds level: Check if item-mold combinations are valid
        3. Machines level: Check if item-mold-machine combinations are valid
        4. Compositions level: Check if item-composition combinations are valid
        5. Full level: Check complete production records against reference data

        Args:
            production_df: Production data to validate
            standard_df: Reference data for validation

        Returns:
            Dictionary containing mismatch analysis results for each level
        """

        # Define matching columns for different validation levels
        match_levels = {
            'items': ['itemCode', 'itemName'],
            'molds': ['itemCode', 'itemName', 'moldNo'],
            'machines': ['itemCode', 'itemName', 'moldNo', 'machineTonnage'],
            'compositions': ['itemCode', 'itemName', 'item_composition'],
            'full': ['itemCode', 'itemName', 'moldNo', 'machineTonnage', 'item_composition']
        }

        results = {}

        # Analyze each level of mismatch using merge indicator
        for level, cols in match_levels.items():
            # Get unique combinations for this level
            prod_subset = production_df[cols].drop_duplicates()
            std_subset = standard_df[cols].drop_duplicates()

            # Find mismatches using merge indicator
            mismatches = prod_subset.merge(
                std_subset,
                on=cols,
                how='left',
                indicator=True
            )
            
            # Extract records that don't match (left_only)
            not_matched = mismatches[mismatches['_merge'] == 'left_only'][cols]
            results[f'not_matched_{level}'] = not_matched

            logger.debug(f"Level {level}: {len(not_matched)} mismatches found")

        # Find detailed production records that don't match reference data
        detailed_mismatches = production_df.merge(
            standard_df,
            on=match_levels['full'],
            how='left',
            indicator=True
        )

        # Extract unmatched records with full context
        not_matched_records = detailed_mismatches[detailed_mismatches['_merge'] == 'left_only']
        not_matched_records = not_matched_records.drop('_merge', axis=1)

        # Add summary statistics
        results['not_matched_records'] = not_matched_records
        results['total_records'] = len(production_df)
        results['total_not_matched'] = len(not_matched_records)

        return results

    @staticmethod
    def _process_item_warnings(mismatches_df: pd.DataFrame) -> List[Dict[str, Any]]:
        
        """
        Process item information warnings for production records with invalid items.
        
        This method generates warnings for production records where the item
        (itemCode, itemName) combination doesn't exist in the reference data.
        """

        results = []

        for _, row in mismatches_df.iterrows():
            # Extract production context information
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}"

            # Generate warning details
            mismatch_type = f'({item_code}, {item_name})_not_matched'
            required_action = 'update_itemInfo_or_double_check_productRecords'

            # Create human-readable message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

            # Create structured warning entry
            entry = {
                'poNo': po_no,
                'warningType': 'item_warnings',
                'mismatchType': 'item_info_not_matched',
                'requiredAction': required_action,
                'message': message
            }

            results.append(entry)

        return results

    @staticmethod
    def _process_mold_warnings(mismatches_df: pd.DataFrame) -> List[Dict[str, Any]]:
        
        """
        Process mold warnings for production records with invalid item-mold combinations.
        
        This method generates warnings for production records where the item-mold
        combination is not valid according to the reference data.
        """

        results = []

        for _, row in mismatches_df.iterrows():
            # Extract production context information
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            mold_no = row.get('moldNo', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {mold_no}"

            # Generate warning details
            mismatch_type = f'{mold_no}_and_({item_code},{item_name})_not_matched'
            required_action = 'update_moldInfo_or_double_check_productRecords'

            # Create human-readable message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

            # Create structured warning entry
            entry = {
                'poNo': po_no,
                'warningType': 'item_mold_warnings',
                'mismatchType': 'item_and_mold_not_matched',
                'requiredAction': required_action,
                'message': message
            }

            results.append(entry)

        return results

    @staticmethod
    def _process_machine_warnings(mismatches_df: pd.DataFrame) -> List[Dict[str, Any]]:
        
        """
        Process machine tonnage warnings for invalid mold-machine combinations.
        
        This method generates warnings for production records where the mold-machine
        tonnage combination is not valid according to the reference data.
        """

        results = []

        for _, row in mismatches_df.iterrows():
            # Extract production context information
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            mold_no = row.get('moldNo', 'N/A')
            machine_tonnage = row.get('machineTonnage', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {mold_no}, {machine_tonnage}"

            # Generate warning details
            mismatch_type = f'{machine_tonnage}_and_{mold_no}_not_matched'
            required_action = 'update_moldSpecificationSummary_or_double_check_productRecords'

            # Create human-readable message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

            # Create structured warning entry
            entry = {
                'poNo': po_no,
                'warningType': 'mold_machine_tonnage_warnings',
                'mismatchType': 'mold_and_machine_tonnage_not_matched',
                'requiredAction': required_action,
                'message': message
            }

            results.append(entry)

        return results

    @staticmethod
    def _process_composition_warnings(mismatches_df: pd.DataFrame) -> List[Dict[str, Any]]:
        
        """
        Process item composition warnings for invalid item-composition combinations.
        
        This method generates warnings for production records where the item-composition
        combination is not valid according to the reference data.
        """

        results = []

        for _, row in mismatches_df.iterrows():
            # Extract production context information
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            item_composition = row.get('item_composition', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {item_composition}"

            # Generate warning details
            mismatch_type = f'({item_code},{item_name})_and_{item_composition}_not_matched'
            required_action = 'update_itemCompositionSummary_or_double_check_productRecords'

            # Create human-readable message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

            # Create structured warning entry
            entry = {
                'poNo': po_no,
                'warningType': 'item_composition_warnings',
                'mismatchType': 'item_and_item_composition_not_matched',
                'requiredAction': required_action,
                'message': message
            }

            results.append(entry)

        return results

    @staticmethod
    def _generate_warnings(results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:

        """
        Generate warnings for all mismatch types found during validation.

        This method processes validation results and creates categorized warnings
        for different types of mismatches (items, molds, machines, compositions).

        Args:
            results: Dictionary containing mismatch analysis results from validation

        Returns:
            Dictionary with categorized warnings organized by warning type
        """

        # Initialize warning dictionary with empty lists for each category
        warnings = {
            'item_warnings': [],          # Warnings for item-related mismatches
            'mold_warnings': [],          # Warnings for mold-related mismatches
            'machine_warnings': [],       # Warnings for machine-related mismatches
            'composition_warnings': [],   # Warnings for composition-related mismatches
        }

        # Extract records that didn't match validation criteria
        not_matched_records = results['not_matched_records']

        # Early return if no mismatches were found
        if len(not_matched_records) == 0:
            logger.info("No mismatches found - all records validated successfully!")
            return warnings

        # Configuration for processing different warning types
        # Format: (warning_dict_key, results_key, processor_function)
        warning_configs = [
            ('item_warnings', 'not_matched_items', DynamicCrossDataValidator._process_item_warnings),
            ('item_mold_warnings', 'not_matched_molds', DynamicCrossDataValidator._process_mold_warnings),
            ('mold_machine_tonnage_warnings', 'not_matched_machines', DynamicCrossDataValidator._process_machine_warnings),
            ('item_composition_warnings', 'not_matched_compositions', DynamicCrossDataValidator._process_composition_warnings)
        ]

        total_warnings = 0
        # Process each warning category
        for warning_key, result_key, processor_func in warning_configs:
            # Check if this mismatch type exists in results and has data
            if result_key in results and not results[result_key].empty:
                # Find records that match this specific mismatch type by merging dataframes
                category_records = not_matched_records.merge(
                    results[result_key],
                    on=results[result_key].columns.tolist(), # Join on all columns
                    how='inner' # Only keep matching records
                )

                # Generate warnings if matching records exist
                if len(category_records) > 0:
                    category_warnings = processor_func(category_records)
                    warnings[warning_key] = category_warnings
                    total_warnings += len(category_warnings)
                    logger.debug(f"Generated {len(category_warnings)} {warning_key}")

        logger.info(f"Total warnings generated: {total_warnings}")
        return warnings


    @staticmethod
    def _create_empty_warning_dataframe(warning_type: str) -> pd.DataFrame:

        """
        Create an empty DataFrame with proper column structure for different warning types.

        This method ensures consistent DataFrame structure for warning data,
        preventing column mismatch errors during data processing.

        Args:
            warning_type: Type of warning to create structure for
                        - 'invalid': For invalid data warnings
                        - 'mismatch': For data mismatch warnings

        Returns:
            Empty DataFrame with appropriate columns based on warning type

        Raises:
            ValueError: If warning_type is not 'invalid' or 'mismatch'
        """

        # Define column structure based on warning type
        if warning_type == 'invalid':
            # Columns for invalid data warnings (item-focused)
            columns = ['itemInfo', 'warningType', 'mismatchType', 'requiredAction', 'message']
        elif warning_type == 'mismatch':
            # Columns for mismatch warnings (PO-focused)
            columns = ['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message']
        else:
            # Handle unexpected warning types
            raise ValueError(f"Unknown warning type: {warning_type}")
        
        # Create and return empty DataFrame with specified columns
        return pd.DataFrame(columns=columns)