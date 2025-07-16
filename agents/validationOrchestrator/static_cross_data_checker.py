from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
from typing import List
import os

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "itemInfo_df": list(self.databaseSchemas_data['staticDB']['itemInfo']['dtypes'].keys()),
    "resinInfo_df": list(self.databaseSchemas_data['staticDB']['resinInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

class StaticCrossDataChecker:
    
    """
    A class for cross-referencing and validating data consistency between 
    dynamic data (productRecords, purchaseOrders) and static reference data 
    (itemInfo, resinInfo, itemCompositionSummary).
    
    This checker validates that:
    1. Item codes and names exist in the itemInfo reference table
    2. Resin codes and names exist in the resinInfo reference table  
    3. Item compositions match the itemCompositionSummary reference table
    """

    def __init__(self, 
                 checking_df_name: List[str],
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        """
        Initialize the StaticCrossDataChecker with configuration and data loading.
        
        Args:
            checking_df_name: List of dataframe names to validate ("productRecords", "purchaseOrders")
            source_path: Path to the directory containing data files
            annotation_name: Name of the JSON file containing path annotations
            databaseSchemas_path: Path to the database schema definition file
            default_dir: Default directory for output files
        """

        self.logger = logger.bind(class_="StaticCrossDataChecker")

        # Validate that only allowed dataframe names are provided
        allowed_names = ["productRecords", "purchaseOrders"]
        invalid_names = [name for name in checking_df_name if name not in allowed_names]
        if invalid_names:
            self.logger.error("Invalid checking_df_name values: {}. Must be within {}.",
                              invalid_names, allowed_names)
            raise ValueError(f"Invalid checking_df_name values: {invalid_names}. Must be within {allowed_names}")
        self.checking_df_name = checking_df_name

        # Load database schema configuration and file path annotations
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent, 
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path, 
                                                    annotation_name)

        # Load all required DataFrames from parquet files
        self._load_dataframes()
        
        # Set up output configuration
        self.filename_prefix = "static_cross_checker"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "StaticCrossDataChecker"

    def _load_dataframes(self):
        
        """
        Load all required DataFrames with consistent error handling.
        
        This method loads both static reference data (itemInfo, resinInfo, itemCompositionSummary)
        and dynamic data (productRecords, purchaseOrders) from parquet files.
        """

        # Define mapping of path annotation keys to DataFrame attribute names
        dataframes_to_load = [
            ('itemInfo', 'itemInfo_df'),                              # Static reference: item master data
            ('resinInfo', 'resinInfo_df'),                            # Static reference: resin master data
            ('itemCompositionSummary', 'itemCompositionSummary_df'),  # Static reference: item composition data
            ('productRecords', 'productRecords_df'),                  # Dynamic data: production records
            ('purchaseOrders', 'purchaseOrders_df')                   # Dynamic data: purchase orders
        ]
        
        # Load each dataframe and set as instance attribute
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)
            if not path or not os.path.exists(path):
                self.logger.error("❌ Path to '{}' not found or does not exist.", path_key)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist.")
            
            df = pd.read_parquet(path)
            setattr(self, attr_name, df)
            self.logger.debug("{}: {} - {}", path_key, df.shape, df.columns)

    def _process_checking_data(self, checking_df_name):
        
        """
        Process and prepare checking data based on the dataframe type.
        
        Args:
            checking_df_name: Name of the dataframe to process ("productRecords" or "purchaseOrders")
            
        Returns:
            pd.DataFrame: Processed dataframe ready for validation
        """

        if checking_df_name == "productRecords":
            checking_df = self.productRecords_df.copy()
            # Remove records with null poNote and rename column to poNo for consistency
            checking_df = checking_df[checking_df['poNote'].notna()].copy()
            checking_df = checking_df.rename(columns={"poNote": "poNo"})
            self.logger.info('Processed productRecords: removed null poNote, {} rows remaining', len(checking_df))
        elif checking_df_name == "purchaseOrders":
            checking_df = self.purchaseOrders_df.copy()
            self.logger.info('Processed purchaseOrders: {} rows', len(checking_df))
        else:
            raise ValueError(f"Unknown checking_df_name: {checking_df_name}")
        return checking_df

    def run_validations(self, **kwargs):
        
        """
        Run all validation checks following PORequiredCriticalValidator pattern.
        
        This method performs three types of validation:
        1. Item info validation (itemCode + itemName matches)
        2. Resin info validation (resinCode + resinName matches)
        3. Composition validation (full item composition matches)
        
        Returns:
            dict: Dictionary containing validation results for each dataframe
        """

        self.logger.info("Starting static cross data validation...")
        
        final_results = {}

        # Process each dataframe specified in checking_df_name
        for df_name in self.checking_df_name:
            self.logger.info("Processing validations for: {}", df_name)
            checking_df = self._process_checking_data(df_name)
            
            # Run all three validation checks
            item_warnings = self._check_item_info_matches(df_name, checking_df)
            resin_warnings = self._check_resin_info_matches(df_name, checking_df)
            composition_warnings = self._check_composition_matches(df_name, checking_df)
            
            # Combine all warnings following PORequiredCriticalValidator pattern
            all_warnings = item_warnings + resin_warnings + composition_warnings
            
            # Calculate summary statistics for reporting
            total_warnings = len(all_warnings)
            
            self.logger.info("Summary for {}: Total warnings: {} (Item: {}, Resin: {}, Composition: {})",
                            df_name, total_warnings, len(item_warnings), 
                            len(resin_warnings), len(composition_warnings))
            
            # Store results as DataFrame with standardized column structure
            final_results[df_name] = pd.DataFrame(all_warnings) if all_warnings else pd.DataFrame(
                columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])

        return final_results

    def run_validations_and_save_results(self, **kwargs):
        
        """
        Run validations and save results to Excel file following PORequiredCriticalValidator pattern.
        
        This method executes all validations and exports the results to a versioned Excel file.
        """

        self.data = {}
        final_results = self.run_validations()
        
        # Prepare data for saving (matching PORequiredCriticalValidator format)
        for df_name, results_df in final_results.items():
            self.data[f"{df_name}"] = results_df
        
        self.logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    def _check_item_info_matches(self, df_name, checking_df):
        
        """
        Check for itemCode + itemName matches in itemInfo reference table.
        
        This validation ensures that all item codes and names in the checking data
        exist as valid combinations in the itemInfo reference table.
        
        Args:
            df_name: Name of the dataframe being checked
            checking_df: DataFrame to validate
            
        Returns:
            list: List of warning dictionaries for mismatched items
        """

        self.logger.debug("Checking item info matches for {}", df_name)
        
        # Define required fields based on dataframe type
        if df_name == "productRecords":
          subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo', 'itemCode', 'itemName']
        elif df_name == "purchaseOrders":
          subset_fields = ['poNo', 'itemCode', 'itemName']
        else:
          logger.error("Unknown df_name: {}", df_name)
          raise ValueError(f"Unknown df_name: {df_name}")

        # Extract relevant data and remove records with missing item info
        po_subset = checking_df[subset_fields].dropna(subset=['itemCode', 'itemName']).copy()
        
        if po_subset.empty:
            return []
        
        # Create reference lookup from itemInfo table
        item_pairs = self.itemInfo_df[['itemCode', 'itemName']].drop_duplicates()
        
        # Find mismatches using left join with indicator
        merged = po_subset.merge(item_pairs, on=['itemCode', 'itemName'], how='left', indicator=True)
        mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        if mismatches.empty:
            return []
        
        # Process and format warnings
        return self._process_item_warnings(mismatches, df_name)

    def _check_resin_info_matches(self, df_name, checking_df):
        
        """
        Check for resinCode + resinName matches in resinInfo reference table.
        
        This validation checks three types of resin information:
        1. Plastic resin (plasticResinCode + plasticResin)
        2. Color masterbatch (colorMasterbatchCode + colorMasterbatch)
        3. Additive masterbatch (additiveMasterbatchCode + additiveMasterbatch)
        
        Args:
            df_name: Name of the dataframe being checked
            checking_df: DataFrame to validate
            
        Returns:
            list: List of warning dictionaries for mismatched resin info
        """

        self.logger.debug("Checking resin info matches for {}", df_name)
        
        # Define resin field configurations for validation
        resin_configs = [
            ('plasticResinCode', 'plasticResin'),
            ('colorMasterbatchCode', 'colorMasterbatch'),
            ('additiveMasterbatchCode', 'additiveMasterbatch')
        ]
        
        all_resin_warnings = []
        
        # Check each type of resin information
        for code_field, name_field in resin_configs:
            
            # Skip if fields don't exist in the dataframe
            if code_field not in checking_df.columns or name_field not in checking_df.columns:
                continue
                
            # Define required fields based on dataframe type
            if df_name == "productRecords":
              subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo']
            elif df_name == "purchaseOrders":
              subset_fields = ['poNo']
            else:
              logger.error("Unknown df_name: {}", df_name)
              raise ValueError(f"Unknown df_name: {df_name}")

            # Extract and clean resin data
            resin_subset = checking_df[subset_fields + [code_field, name_field]].copy()
            resin_subset = resin_subset.dropna(subset=[code_field, name_field], how='all')
            resin_subset = resin_subset.rename(columns={code_field: 'resinCode', name_field: 'resinName'})
            
            if resin_subset.empty:
                continue
            
            # Create reference lookup from resinInfo table
            resin_pairs = self.resinInfo_df[['resinCode', 'resinName']].drop_duplicates()
            
            # Find mismatches using left join
            merged = resin_subset.merge(resin_pairs, on=['resinCode', 'resinName'], how='left', indicator=True)
            mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
            
            if not mismatches.empty:
                # Add plastic type context for clearer error messages
                mismatches['plasticType'] = name_field
                warnings = self._process_resin_warnings(mismatches, df_name)
                all_resin_warnings.extend(warnings)
        
        return all_resin_warnings

    def _check_composition_matches(self, df_name, checking_df):
        
        """
        Check for complete item composition matches in itemCompositionSummary reference table.
        
        This validation ensures that the complete combination of item and resin information
        exists as a valid composition in the reference table.
        
        Args:
            df_name: Name of the dataframe being checked
            checking_df: DataFrame to validate
            
        Returns:
            list: List of warning dictionaries for mismatched compositions
        """

        self.logger.debug("Checking composition matches for {}", df_name)
        
        # Define all composition fields that must match together
        composition_cols = [
            'itemCode', 'itemName', 'plasticResinCode', 'plasticResin',
            'colorMasterbatchCode', 'colorMasterbatch', 
            'additiveMasterbatchCode', 'additiveMasterbatch'
        ]

        # Define required fields based on dataframe type
        if df_name == "productRecords":
          subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo']
        elif df_name == "purchaseOrders":
          subset_fields = ['poNo']
        else:
          logger.error("Unknown df_name: {}", df_name)
          raise ValueError(f"Unknown df_name: {df_name}")
          
        # Extract composition data, excluding records with all null composition fields
        po_subset = checking_df[subset_fields + composition_cols].dropna(subset=composition_cols, how='all').copy()
        
        if po_subset.empty:
            return []
        
        # Create reference lookup from itemCompositionSummary table
        composition_pairs = self.itemCompositionSummary_df[composition_cols].drop_duplicates()
        
        # Find mismatches using left join
        merged = po_subset.merge(composition_pairs, on=composition_cols, how='left', indicator=True)
        mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        if mismatches.empty:
            return []
        
        # Process and format composition warnings
        return self._process_composition_warnings(mismatches, df_name, composition_cols)

    @staticmethod
    def _process_item_warnings(mismatches_df, df_name):
        
        """
        Process item info warnings following PORequiredCriticalValidator pattern.
        
        Converts item mismatch data into standardized warning format with
        contextual information and recommended actions.
        
        Args:
            mismatches_df: DataFrame containing mismatched item records
            df_name: Name of the source dataframe
            
        Returns:
            list: List of formatted warning dictionaries
        """

        results = []
        
        for _, row in mismatches_df.iterrows():
            # Build context information based on dataframe type
            if df_name == "productRecords":
              poNo = row['poNo']
              recordDate = row['recordDate'].strftime('%Y-%m-%d')
              workingShift = row['workingShift']
              machineNo = row['machineNo']
              itemCode = row['itemCode']
              itemName = row['itemName']
              context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}, {itemCode}, {itemName}"
            elif df_name == "purchaseOrders":
              poNo = row['poNo']
              itemCode = row['itemCode']
              itemName = row['itemName']
              context_info = f"{poNo}, {itemCode}, {itemName}"
            else:
              logger.error("Unknown df_name: {}", df_name)
              raise ValueError(f"Unknown df_name: {df_name}")
            
            # Define mismatch type and required action
            mismatch_type = f'{itemCode}_and_{itemName}_not_matched'
            required_action = f'update_itemInfo_or_double_check_{df_name}'
            
            # Create comprehensive warning message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"
            
            # Create standardized warning entry
            entry = {
                'poNo': poNo,
                'warningType': 'item_info_warnings',
                'mismatchType': 'item_code_and_name_not_matched',
                'requiredAction': required_action,
                'message': message
            }
            
            results.append(entry)
        
        return results

    @staticmethod
    def _process_resin_warnings(mismatches_df, df_name):
        
        """
        Process resin info warnings following PORequiredCriticalValidator pattern.
        
        Converts resin mismatch data into standardized warning format with
        contextual information and recommended actions.
        
        Args:
            mismatches_df: DataFrame containing mismatched resin records
            df_name: Name of the source dataframe
            
        Returns:
            list: List of formatted warning dictionaries
        """

        results = []
        
        for _, row in mismatches_df.iterrows():
            # Build context information based on dataframe type
            if df_name == "productRecords":
              poNo = row['poNo']
              recordDate = row['recordDate'].strftime('%Y-%m-%d')
              workingShift = row['workingShift']
              machineNo = row['machineNo']
              resinCode = row['resinCode']
              resinName = row['resinName']
              context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}, {resinCode}, {resinName}"
            elif df_name == "purchaseOrders":
              poNo = row['poNo']
              resinCode = row['resinCode']
              resinName = row['resinName']
              context_info = f"{poNo}, {resinCode}, {resinName}"
            else:
              logger.error("Unknown df_name: {}", df_name)
              raise ValueError(f"Unknown df_name: {df_name}")
            
            # Define mismatch type and required action
            mismatch_type = f'{resinCode}_and_{resinName}_not_matched'
            required_action = f'update_resinInfo_or_double_check_{df_name}'
            
            # Create comprehensive warning message
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"
            
            # Create standardized warning entry
            entry = {
                'poNo': poNo,
                'warningType': 'resin_info_warnings',
                'mismatchType': 'resin_code_and_name_not_matched',
                'requiredAction': required_action,
                'message': message
            }
            
            results.append(entry)
        
        return results

    @staticmethod
    def _process_composition_warnings(mismatches_df, df_name, composition_fields):
        
        """
        Process composition warnings following PORequiredCriticalValidator pattern.
        
        Converts composition mismatch data into standardized warning format with
        contextual information and recommended actions.
        
        Args:
            mismatches_df: DataFrame containing mismatched composition records
            df_name: Name of the source dataframe
            composition_fields: List of fields that make up the composition
            
        Returns:
            list: List of formatted warning dictionaries
        """

        results = []
        for _, row in mismatches_df.iterrows():
            # Build context information based on dataframe type
            if df_name == "productRecords":
              poNo = row['poNo']
              recordDate = row['recordDate'].strftime('%Y-%m-%d')
              workingShift = row['workingShift']
              machineNo = row['machineNo']
              context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}"
              detail_info = ", ".join([row[field] if pd.notna(row[field]) else '' for field in composition_fields])
              
            elif df_name == "purchaseOrders":
              poNo = row['poNo']
              context_info = f"{poNo}"
              detail_info = ", ".join([row[field] if pd.notna(row[field]) else '' for field in composition_fields])
              
            else:
              logger.error("Unknown df_name: {}", df_name)
              raise ValueError(f"Unknown df_name: {df_name}")
            
            # Define mismatch type and required action
            mismatch_type = f'{detail_info}_not_matched'
            required_action = f'update_itemCompositionSummary_or_double_check_{df_name}'
            
            # Create comprehensive warning message
            message = f"({context_info}) - Mismatch: {mismatch_type} - Please: {required_action}"
            
            # Create standardized warning entry
            entry = {
                'poNo': poNo,
                'warningType': 'composition_warnings',
                'mismatchType': 'item_composition_not_matched',
                'requiredAction': required_action,
                'message': message
            }
            
            results.append(entry)
        
        return results