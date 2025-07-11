from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import os
from typing import Dict, Tuple, Any, List

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

class DynamicCrossDataValidator:
    """
    A validator class for cross-referencing production records with standard reference data.

    This class validates that production records (items, molds, machines, compositions)
    match against standard reference data and generates detailed warnings for mismatches.
    """

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
        self.logger = logger.bind(class_="DynamicCrossDataValidator")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Load all required DataFrames
        self._load_dataframes()

        self.filename_prefix = "dynamic_cross_validator"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DynamicCrossDataValidator"

    def _load_dataframes(self) -> None:
        """Load all required DataFrames with consistent error handling"""
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
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
        """
        Run all validation checks and return comprehensive results.

        Returns:
            Dict containing validation results, warnings, and statistics
        """
        self.logger.info("Starting dynamic cross data validation...")

        try:
            # Prepare data
            self.logger.info("Preparing production data...")
            production_df = self._prepare_production_data(
                self.productRecords_df,
                self.machineInfo_df
            )

            self.logger.info("Preparing standard reference data...")
            standard_df, total_invalids = self._prepare_standard_data(
                self.moldSpecificationSummary_df,
                self.moldInfo_df,
                self.itemCompositionSummary_df
            )

            # Analyze mismatches
            self.logger.info("Analyzing mismatches...")
            results = self._analyze_mismatches(production_df, standard_df)

            # Generate warnings
            self.logger.info("Generating warnings...")
            mismatch_warnings = self._generate_warnings(results)
            invalid_warnings = self._process_invalid_item_warnings(total_invalids)

            # Add warnings to results
            results['mismatch_warnings'] = mismatch_warnings
            results['invalid_warnings'] = invalid_warnings

            return DynamicCrossDataValidator._convert_results(results)

        except Exception as e:
            self.logger.error("❌ Validation failed: {}", str(e))
            raise

    @staticmethod
    def _convert_results(results):
      final_results = {}
      # Handle invalid warnings với proper column structure
      if results['invalid_warnings']['invalid_item']:
          final_results['invalid_warnings'] = pd.DataFrame(results['invalid_warnings']['invalid_item'])
      else:
          final_results['invalid_warnings'] = DynamicCrossDataValidator._create_empty_warning_dataframe('invalid')

      # Handle mismatch warnings với proper column structure
      all_mismatch_warnings = []
      for warning_type, warnings in results['mismatch_warnings'].items():
          all_mismatch_warnings.extend(warnings)

      if all_mismatch_warnings:
          final_results['mismatch_warnings'] = pd.DataFrame(all_mismatch_warnings)
      else:
          final_results['mismatch_warnings'] = DynamicCrossDataValidator._create_empty_warning_dataframe('mismatch')

      return final_results

    def run_validations_and_save_results(self, **kwargs) -> None:
        """Run validations and save results to Excel files - Improved version"""
        try:
            self.data = self.run_validations(**kwargs)

            # Log summary thông tin
            self.logger.info("Validation Summary:")
            self.logger.info("- Invalid warnings: {} items", len(self.data['invalid_warnings']))
            self.logger.info("- Mismatch warnings: {} items", len(self.data['mismatch_warnings']))

            self.logger.info("Exporting results to Excel...")
            save_output_with_versioning(
                self.data,
                self.output_dir,
                self.filename_prefix,
            )
            self.logger.info("Results exported successfully!")

        except Exception as e:
            self.logger.error("Failed to save results: {}", str(e))
            raise

    @staticmethod
    def _check_invalid(df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Check for invalid (null) values in critical columns.

        Args:
            df: DataFrame to check

        Returns:
            Dictionary with lists of invalid item codes and names
        """
        invalid_rows = df[df.isnull().any(axis=1)].copy()
        invalid_details = {'itemCode': [], 'itemName': []}

        for r in invalid_rows.index:
            for c in df.columns:
                if pd.isnull(df.at[r, c]):
                    logger.debug(f"Null value found at row {r}, column '{c}'")

                    item_code = df.at[r, 'itemCode']
                    item_name = df.at[r, 'itemName']

                    if item_code not in invalid_details['itemCode']:
                        invalid_details['itemCode'].append(item_code)
                    if item_name not in invalid_details['itemName']:
                        invalid_details['itemName'].append(item_name)

        return invalid_details

    @staticmethod
    def _build_component_string(row: pd.Series) -> str:
        """
        Build component string from plastic resin, color masterbatch, and additive masterbatch.

        Args:
            row: DataFrame row containing component information

        Returns:
            Formatted component string or pd.NA if required fields are missing
        """
        parts = []

        # Plastic Resin (Required)
        if pd.notna(row.get('plasticResin')) and pd.notna(row.get('plasticResinCode')):
            parts.append(f"{row['plasticResinCode']}_{row['plasticResin']}")
        else:
            return pd.NA

        # Color Masterbatch (optional)
        if pd.notna(row.get('colorMasterbatch')) and pd.notna(row.get('colorMasterbatchCode')):
            parts.append(f"{row['colorMasterbatchCode']}_{row['colorMasterbatch']}")

        # Additive Masterbatch (optional)
        if pd.notna(row.get('additiveMasterbatch')) and pd.notna(row.get('additiveMasterbatchCode')):
            parts.append(f"{row['additiveMasterbatchCode']}_{row['additiveMasterbatch']}")

        return " | ".join(parts)

    def _prepare_production_data(self, productRecords_df: pd.DataFrame,
                               machineInfo_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare production data for matching by merging product records with machine info.

        Args:
            productRecords_df: Product records DataFrame
            machineInfo_df: Machine information DataFrame

        Returns:
            Prepared production DataFrame
        """
        # Load and filter product records
        product_df = productRecords_df.copy()
        product_df = product_df[product_df['poNote'].notna()].reset_index(drop=True)

        self.logger.debug("Filtered product records: {:,} rows", len(product_df))

        # Build item composition
        product_df['item_composition'] = product_df.apply(
            self._build_component_string, axis=1
        )

        # Select only needed columns to reduce memory usage
        product_cols = [
            'recordDate', 'workingShift', 'poNote', 'itemCode', 'itemName',
            'machineNo', 'machineCode', 'moldNo', 'item_composition'
        ]
        machine_cols = ['machineCode', 'machineTonnage']

        # Merge with machine information
        machine_df = machineInfo_df.copy()
        result_df = pd.merge(
            product_df[product_cols],
            machine_df[machine_cols],
            on='machineCode',
            how='left'
        )

        # Convert machineTonnage to string for consistent matching
        result_df['machineTonnage'] = result_df['machineTonnage'].astype(str)

        self.logger.debug("Production data prepared: {:,} rows", len(result_df))
        return result_df

    @staticmethod
    def _process_invalid_item_warnings(invalid_details: Dict[str, Dict[str, List[str]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process invalid item warnings from null value checks.

        Args:
            invalid_details: Dictionary containing invalid item details by database

        Returns:
            Dictionary with processed invalid item warnings
        """
        # Initialize với empty list thay vì để trống
        invalid_results = {"invalid_item": []}

        for df_name, invalid_data in invalid_details.items():
            if not invalid_data['itemCode'] and not invalid_data['itemName']:
                continue

            # Create combinations of invalid codes and names
            invalid_items = set()
            for code in invalid_data['itemCode']:
                for name in invalid_data['itemName']:
                    invalid_items.add((code, name))

            for item_code, item_name in invalid_items:
                context_info = [item_code, item_name]
                mismatch_type = f"{'_and_'.join(context_info)}_does_not_exist_in_{df_name}"
                required_action = f"update_{df_name}_or_double_check_related_databases"

                message = f"({', '.join(context_info)}) - Mismatch: {mismatch_type}. Please {required_action}"

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
        Prepare standard reference data by processing and merging mold specs, mold info, and item compositions.

        Args:
            moldSpecificationSummary_df: Mold specification summary DataFrame
            moldInfo_df: Mold information DataFrame
            itemCompositionSummary_df: Item composition summary DataFrame

        Returns:
            Tuple of (standard_df, total_invalids)
        """
        total_invalids = {}

        # Process mold specifications
        mold_spec_df = moldSpecificationSummary_df.copy()
        mold_spec_df = mold_spec_df.rename(columns={"moldList": "moldNo"})
        mold_spec_df['moldNo'] = mold_spec_df['moldNo'].str.split('/')

        # Explode mold numbers and merge with mold info
        mold_exploded = mold_spec_df.explode('moldNo')[['itemCode', 'itemName', 'moldNo']]
        mold_info_df = moldInfo_df.copy()
        mold_machine_df = pd.merge(
            mold_exploded,
            mold_info_df[['moldNo', 'moldName', 'machineTonnage']],
            on='moldNo',
            how='left'
        )

        # Check for invalid combinations
        invalids = self._check_invalid(mold_machine_df)
        if invalids['itemCode'] or invalids['itemName']:
            self.logger.warning(
                'Invalid items found in mold specifications: codes={}, names={}',
                invalids['itemCode'], invalids['itemName']
            )
        total_invalids['moldSpecificationSummary_and_moldInfo'] = invalids

        # Process machine tonnage
        mold_machine_df = mold_machine_df.dropna()
        mold_machine_df['machineTonnage'] = mold_machine_df['machineTonnage'].str.split('/')
        mold_machine_final = mold_machine_df.explode('machineTonnage')

        # Process item compositions
        item_comp_df = itemCompositionSummary_df.copy()
        item_comp_df['item_composition'] = item_comp_df.apply(
            self._build_component_string, axis=1
        )

        # Group compositions by item
        item_comp_grouped = (
            item_comp_df
            .groupby(['itemCode', 'itemName'])['item_composition']
            .agg(lambda x: x.dropna().unique())
            .reset_index()
        )

        # Final merge and explode compositions
        standard_df = pd.merge(
            mold_machine_final[['itemCode', 'itemName', 'moldNo', 'machineTonnage']],
            item_comp_grouped,
            on=['itemCode', 'itemName'],
            how='left'
        )

        # Check for invalid combinations in final merge
        second_invalids = self._check_invalid(standard_df)
        if second_invalids['itemCode'] or second_invalids['itemName']:
            self.logger.warning(
                'Invalid items found in item compositions: codes={}, names={}',
                second_invalids['itemCode'], second_invalids['itemName']
            )
        total_invalids['itemCompositionSummary'] = second_invalids

        standard_df = standard_df.dropna()
        standard_df = standard_df.explode('item_composition')

        self.logger.debug("Standard data prepared: {:,} rows", len(standard_df))
        return standard_df[['itemCode', 'itemName', 'moldNo', 'machineTonnage', 'item_composition']], total_invalids

    @staticmethod
    def _analyze_mismatches(production_df: pd.DataFrame, standard_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze mismatches between production and standard data at multiple levels.

        Args:
            production_df: Production data DataFrame
            standard_df: Standard reference data DataFrame

        Returns:
            Dictionary containing mismatch analysis results
        """
        # Define matching columns for different levels
        match_levels = {
            'items': ['itemCode', 'itemName'],
            'molds': ['itemCode', 'itemName', 'moldNo'],
            'machines': ['itemCode', 'itemName', 'moldNo', 'machineTonnage'],
            'compositions': ['itemCode', 'itemName', 'item_composition'],
            'full': ['itemCode', 'itemName', 'moldNo', 'machineTonnage', 'item_composition']
        }

        results = {}

        # Analyze each level of mismatch
        for level, cols in match_levels.items():
            prod_subset = production_df[cols].drop_duplicates()
            std_subset = standard_df[cols].drop_duplicates()

            # Find mismatches using merge indicator
            mismatches = prod_subset.merge(
                std_subset,
                on=cols,
                how='left',
                indicator=True
            )

            not_matched = mismatches[mismatches['_merge'] == 'left_only'][cols]
            results[f'not_matched_{level}'] = not_matched

            logger.debug(f"Level {level}: {len(not_matched)} mismatches found")

        # Find detailed records that don't match
        detailed_mismatches = production_df.merge(
            standard_df,
            on=match_levels['full'],
            how='left',
            indicator=True
        )

        not_matched_records = detailed_mismatches[detailed_mismatches['_merge'] == 'left_only']
        not_matched_records = not_matched_records.drop('_merge', axis=1)

        results['not_matched_records'] = not_matched_records
        results['total_records'] = len(production_df)
        results['total_not_matched'] = len(not_matched_records)

        return results

    @staticmethod
    def _process_item_warnings(mismatches_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process item information warnings"""
        results = []

        for _, row in mismatches_df.iterrows():
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}"

            mismatch_type = f'({item_code}, {item_name})_not_matched'
            required_action = 'update_itemInfo_or_double_check_productRecords'

            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

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
        """Process mold warnings"""
        results = []

        for _, row in mismatches_df.iterrows():
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            mold_no = row.get('moldNo', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {mold_no}"

            mismatch_type = f'{mold_no}_and_({item_code},{item_name})_not_matched'
            required_action = 'update_moldInfo_or_double_check_productRecords'

            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

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
        """Process machine tonnage warnings"""
        results = []

        for _, row in mismatches_df.iterrows():
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            mold_no = row.get('moldNo', 'N/A')
            machine_tonnage = row.get('machineTonnage', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {mold_no}, {machine_tonnage}"

            mismatch_type = f'{machine_tonnage}_and_{mold_no}_not_matched'
            required_action = 'update_moldSpecificationSummary_or_double_check_productRecords'

            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

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
        """Process item composition warnings"""
        results = []

        for _, row in mismatches_df.iterrows():
            po_no = row.get('poNote', 'N/A')
            record_date = row['recordDate'].strftime('%Y-%m-%d') if pd.notna(row['recordDate']) else 'N/A'
            working_shift = row.get('workingShift', 'N/A')
            machine_no = row.get('machineNo', 'N/A')
            item_code = row.get('itemCode', 'N/A')
            item_name = row.get('itemName', 'N/A')
            item_composition = row.get('item_composition', 'N/A')
            context_info = f"{po_no}, {record_date}, {working_shift}, {machine_no}, {item_code}, {item_name}, {item_composition}"

            mismatch_type = f'({item_code},{item_name})_and_{item_composition}_not_matched'
            required_action = 'update_itemCompositionSummary_or_double_check_productRecords'

            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"

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
        Generate warnings for all mismatch types.

        Args:
            results: Dictionary containing mismatch analysis results

        Returns:
            Dictionary with categorized warnings
        """
        # Initialize với empty lists thay vì để trống
        warnings = {
            'item_warnings': [],
            'mold_warnings': [],
            'machine_warnings': [],
            'composition_warnings': [],
        }

        not_matched_records = results['not_matched_records']

        if len(not_matched_records) == 0:
            logger.info("No mismatches found - all records validated successfully!")
            return warnings  # Trả về dict với empty lists, không phải dict rỗng

        # Generate warnings for each category
        warning_configs = [
            ('item_warnings', 'not_matched_items', DynamicCrossDataValidator._process_item_warnings),
            ('item_mold_warnings', 'not_matched_molds', DynamicCrossDataValidator._process_mold_warnings),
            ('mold_machine_tonnage_warnings', 'not_matched_machines', DynamicCrossDataValidator._process_machine_warnings),
            ('item_composition_warnings', 'not_matched_compositions', DynamicCrossDataValidator._process_composition_warnings)
        ]

        total_warnings = 0
        for warning_key, result_key, processor_func in warning_configs:
            # Find records that match this specific mismatch type
            if result_key in results and not results[result_key].empty:
                category_records = not_matched_records.merge(
                    results[result_key],
                    on=results[result_key].columns.tolist(),
                    how='inner'
                )

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
        Create empty DataFrame with proper column structure for warnings.

        Args:
            warning_type: Type of warning ('invalid' or 'mismatch')

        Returns:
            Empty DataFrame with appropriate columns
        """
        if warning_type == 'invalid':
            columns = ['itemInfo', 'warningType', 'mismatchType', 'requiredAction', 'message']
        elif warning_type == 'mismatch':
            columns = ['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message']
        else:
            raise ValueError(f"Unknown warning type: {warning_type}")

        return pd.DataFrame(columns=columns)