from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import numpy as np
from typing import List
import os

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "itemInfo_df": list(self.databaseSchemas_data['statisticDB']['itemInfo']['dtypes'].keys()),
    "resinInfo_df": list(self.databaseSchemas_data['statisticDB']['resinInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['statisticDB']['itemCompositionSummary']['dtypes'].keys()),
})

class StaticCrossDataChecker:
    def __init__(self, 
                 checking_df_name: List[str],
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        self.logger = logger.bind(class_="StaticCrossDataChecker")

        allowed_names = ["productRecords", "purchaseOrders"]
        invalid_names = [name for name in checking_df_name if name not in allowed_names]
        if invalid_names:
            self.logger.error("Invalid checking_df_name values: {}. Must be within {}.",
                              invalid_names, allowed_names)
            raise ValueError(f"Invalid checking_df_name values: {invalid_names}. Must be within {allowed_names}")
        self.checking_df_name = checking_df_name

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent, 
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path, 
                                                    annotation_name)
        
        # Extract itemInfo DataFrame
        itemInfo_path = self.path_annotation.get('itemInfo')
        if not itemInfo_path or not os.path.exists(itemInfo_path):
            self.logger.error("❌ Path to 'itemInfo' not found or does not exist.")
            raise FileNotFoundError("Path to 'itemInfo' not found or does not exist.")
        self.itemInfo_df = pd.read_parquet(itemInfo_path)
        self.logger.debug("itemInfo: {} - {}", self.itemInfo_df.shape, self.itemInfo_df.columns)

        # Extract resinInfo DataFrame
        resinInfo_path = self.path_annotation.get('resinInfo')
        if not resinInfo_path or not os.path.exists(resinInfo_path):
            self.logger.error("❌ Path to 'resinInfo' not found or does not exist.")
            raise FileNotFoundError("Path to 'resinInfo' not found or does not exist.")
        self.resinInfo_df = pd.read_parquet(resinInfo_path)
        self.logger.debug("resinInfo: {} - {}", self.resinInfo_df.shape, self.resinInfo_df.columns)

        # Extract itemCompositionSummary DataFrame
        itemCompositionSummary_path = self.path_annotation.get('itemCompositionSummary')
        if not itemCompositionSummary_path or not os.path.exists(itemCompositionSummary_path):
            self.logger.error("❌ Path to 'itemCompositionSummary' not found or does not exist.")
            raise FileNotFoundError("Path to 'itemCompositionSummary' not found or does not exist.")
        self.itemCompositionSummary_df = pd.read_parquet(itemCompositionSummary_path)
        self.logger.debug("itemCompositionSummary: {} - {}", self.itemCompositionSummary_df.shape, self.itemCompositionSummary_df.columns)

        # Extract productRecords DataFrame
        productRecords_path = self.path_annotation.get('productRecords')
        if not productRecords_path or not os.path.exists(productRecords_path):
            self.logger.error("❌ Path to 'productRecords' not found or does not exist.")
            raise FileNotFoundError("Path to 'productRecords' not found or does not exist.")
        self.productRecords_df = pd.read_parquet(productRecords_path)
        self.logger.debug("productRecords: {} - {}", self.productRecords_df.shape, self.productRecords_df.columns)

        # Extract purchaseOrders DataFrame
        purchaseOrders_path = self.path_annotation.get('purchaseOrders')
        if not purchaseOrders_path or not os.path.exists(purchaseOrders_path):
            self.logger.error("❌ Path to 'purchaseOrders' not found or does not exist.")
            raise FileNotFoundError("Path to 'purchaseOrders' not found or does not exist.")
        self.purchaseOrders_df = pd.read_parquet(purchaseOrders_path)
        self.logger.debug("purchaseOrders: {} - {}", self.purchaseOrders_df.shape, self.purchaseOrders_df.columns)
        
        # Initialize ignored_pos set
        self.ignored_pos = set()
        
        self.filename_prefix = "static_cross_checker"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "StaticCrossDataChecker"

    def load_checking_data(self, checking_df_name):
        if checking_df_name == "productRecords":
            checking_df = self.productRecords_df.copy()
            checking_df = checking_df[checking_df['poNote'].notna()]
            checking_df = checking_df.rename(columns={"poNote": "poNo"})
        elif checking_df_name == "purchaseOrders":
            checking_df = self.purchaseOrders_df.copy()
        else:
            raise ValueError(f"Unknown checking_df_name: {checking_df_name}")
        return checking_df
    
    def run_static_validations(self, **kwargs):
        """Run all validation checks with optimized flow"""

        self.logger.info("Running optimized validation checks...")

        final_results = {}

        for df_name in self.checking_df_name:
          checking_df = self.load_checking_data(df_name)
          
          # Check 1: Item Info validation
          item_warnings = self.check_item_info_matches(checking_df)
          self.logger.info("Found {} item info mismatches", len(item_warnings))
          
          # Check 2: Resin Info validation (ignore POs with item issues)
          resin_warnings = self.check_resin_info_matches(checking_df)
          self.logger.info("Found {} resin info mismatches", len(resin_warnings))
          
          # Check 3: Item Composition validation (ignore POs with item or resin issues)
          composition_warnings = self.check_composition_matches(checking_df)
          self.logger.info("Found {} composition mismatches", len(composition_warnings))
          
          # Calculate total ignored POs
          ignored_pos_all = self.ignored_pos
          
          # Summary
          results = {
              'item_info_warnings': item_warnings,
              'resin_info_warnings': resin_warnings,
              'composition_warnings': composition_warnings
          }
          
          self.logger.info("DONE: \n{}", results)
          self.logger.info("\nSummary: \nItem Info mismatches: {} \nResin Info mismatches: {} \nComposition mismatches: {} \nTotal ignored POs: {}",
                      len(item_warnings), len(resin_warnings), len(composition_warnings), len(ignored_pos_all))
          
          final_results[df_name] = results

        return final_results

    def run_static_validations_and_save_results(self, **kwargs):
        self.data = {}
        final_results = self.run_static_validations()

        for df_name, results in final_results.items():
            self.data[f"{df_name}"] = StaticCrossDataChecker._convert_dict_to_df(results)
        
        self.logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    def check_item_info_matches(self, checking_df, **kwargs):
        """Optimized check for itemCode + itemName matches in itemInfo"""
        self.logger.info("Checking item info matches...")
        
        (item_codes_set, item_names_set, 
         item_pairs_set, item_pair_unique) = StaticCrossDataChecker._create_lookup_sets(
            self.itemInfo_df, 'itemCode', 'itemName')

        po_subset = checking_df[['poNo', 'itemCode', 'itemName']].copy()
        
        # Single merge operation with indicator
        merged = po_subset.merge(
            item_pair_unique,
            on=['itemCode', 'itemName'],
            how='left',
            indicator=True
        )
        
        # Filter mismatches
        mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        if mismatches.empty:
            return []
        
        # Vectorized mismatch type determination
        code_exists = mismatches['itemCode'].isin(item_codes_set)
        name_exists = mismatches['itemName'].isin(item_names_set)
        
        # Determine mismatch types
        conditions = [
            ~code_exists & ~name_exists,
            code_exists | name_exists
        ]
        choices = ['new_item_to_add', 'code_name_mismatch']
        actions = [f'update_itemInfo_or_double_check_{self.checking_df_name}', f'double_check_{self.checking_df_name}']
        
        mismatches['mismatchType'] = np.select(conditions, choices, default='')
        mismatches['requiredAction'] = np.select(conditions, actions, default='')
        
        # Create messages - Fixed string concatenation
        mismatches['message'] = (
            "(" + mismatches['poNo'].astype(str) + ", " + 
            mismatches['itemCode'].astype(str) + ", " + 
            mismatches['itemName'].astype(str) + ") mismatch: " + 
            mismatches['mismatchType'].astype(str) + " - required action: " + 
            mismatches['requiredAction'].astype(str)
        )

        item_warnings = mismatches.to_dict('records')

        # Update ignored POs
        self.ignored_pos.update(warning["poNo"] for warning in item_warnings)
        
        return item_warnings

    def check_resin_info_matches(self, checking_df, **kwargs):
        """Optimized check for resin code + resin name matches"""
        self.logger.info("Checking resin info matches...")

        (resin_codes_set, resin_names_set, 
         resin_pairs_set, resin_pair_unique) = StaticCrossDataChecker._create_lookup_sets(
            self.resinInfo_df, 'resinCode', 'resinName')
        
        # Filter out ignored POs
        filtered_po = checking_df[~checking_df['poNo'].isin(self.ignored_pos)].copy()
        
        if filtered_po.empty:
            return []
        
        all_mismatches = []
        
        # Define resin types with their columns
        resin_configs = [
            ('plasticResinCode', 'plasticResin'),
            ('colorMasterbatchCode', 'colorMasterbatch'),
            ('additiveMasterbatchCode', 'additiveMasterbatch')
        ]
        
        for code_col, name_col in resin_configs:
            # Skip if columns don't exist
            if code_col not in filtered_po.columns or name_col not in filtered_po.columns:
                continue
            
            # Only check rows with both code and name (non-empty)
            mask = (
                (filtered_po[code_col] != '') & 
                (filtered_po[name_col] != '') &
                filtered_po[code_col].notna() & 
                filtered_po[name_col].notna()
            )
            po_subset = filtered_po[mask][['poNo', code_col, name_col]].copy()
            
            if po_subset.empty:
                continue
            
            # Check matches using vectorized operations
            po_subset['code_exists'] = po_subset[code_col].isin(resin_codes_set)
            po_subset['name_exists'] = po_subset[name_col].isin(resin_names_set)
            
            # More efficient pair checking using apply
            po_subset['pair_exists'] = po_subset.apply(
                lambda row: (row[code_col], row[name_col]) in resin_pairs_set, 
                axis=1
            )
            
            # Filter mismatches
            mismatches = po_subset[~po_subset['pair_exists']].copy()
            
            if mismatches.empty:
                continue
            
            # Determine mismatch types
            conditions = [
                ~mismatches['code_exists'] & ~mismatches['name_exists'],
                mismatches['code_exists'] | mismatches['name_exists']
            ]
            choices = ['new_resin_to_add', 'code_name_mismatch']
            actions = [f'update_resinInfo_or_double_check_{self.checking_df_name}', f'double_check_{self.checking_df_name}'] 
            
            mismatches['mismatchType'] = np.select(conditions, choices, default='')
            mismatches['requiredAction'] = np.select(conditions, actions, default='')
            
            # Create messages - Fixed string concatenation
            mismatches['message'] = (
                "(" + mismatches['poNo'].astype(str) + ", " + 
                mismatches[code_col].astype(str) + ", " + 
                mismatches[name_col].astype(str) + ") mismatch: " + 
                mismatches['mismatchType'].astype(str) + " - required action: " + 
                mismatches['requiredAction'].astype(str)
            )
            
            # Standardize column names for output
            result_data = mismatches.rename(columns={
                code_col: 'resinCode',
                name_col: 'resinName'
            })[['poNo', 'resinCode', 'resinName', 'mismatchType', 'requiredAction', 'message']]
            
            all_mismatches.extend(result_data.to_dict('records'))

        # Update ignored POs based on resin warnings
        if all_mismatches:
            ignored_pos_resin = {warning["poNo"] for warning in all_mismatches}
            self.ignored_pos.update(ignored_pos_resin)
        
        return all_mismatches

    def check_composition_matches(self, checking_df, **kwargs):
        """Optimized check for item composition matches"""
        self.logger.info("Checking composition matches...")
        
        # Filter out ignored POs
        filtered_po = checking_df[~checking_df['poNo'].isin(self.ignored_pos)].copy()
        
        if filtered_po.empty:
            return []
        
        # Define columns to check for composition
        composition_cols = [
            'itemCode', 'itemName', 'plasticResinCode', 'plasticResin',
            'colorMasterbatchCode', 'colorMasterbatch', 
            'additiveMasterbatchCode', 'additiveMasterbatch'
        ]
        
        # Filter columns that exist in both dataframes
        available_cols = [
            col for col in composition_cols 
            if col in filtered_po.columns and col in self.itemCompositionSummary_df.columns
        ]
        
        if not available_cols:
            return []
        
        # Use merge for efficient matching
        merged = filtered_po[['poNo'] + available_cols].merge(
            self.itemCompositionSummary_df[available_cols].drop_duplicates(),
            on=available_cols,
            how='left',
            indicator=True
        )
        
        # Filter mismatches
        mismatches = merged[merged['_merge'] == 'left_only'].copy()
        
        if mismatches.empty:
            return []
        
        # Check for partial matches to determine mismatch type
        has_any_match = pd.Series([False] * len(mismatches))
        
        for col in available_cols:
            comp_values = set(self.itemCompositionSummary_df[col].unique())
            has_any_match |= mismatches[col].isin(comp_values)
        
        # Determine mismatch types
        conditions = [
            ~has_any_match,
            has_any_match
        ]
        choices = ['new_item_composition_to_add', 'code_name_mismatch']
        actions = [f'update_itemCompositionSummary_or_double_check_{self.checking_df_name}', f'double_check_{self.checking_df_name}'] 
        
        mismatches['mismatchType'] = np.select(conditions, choices, default='')
        mismatches['requiredAction'] = np.select(conditions, actions, default='')
        
        # Create messages - Fixed string concatenation
        mismatches['message'] = (
            "(" + mismatches['poNo'].astype(str) + ", " + 
            mismatches['itemCode'].astype(str) + ", " + 
            mismatches['itemName'].astype(str) + ") mismatch: " + 
            mismatches['mismatchType'].astype(str) + " - required action: " + 
            mismatches['requiredAction'].astype(str)
        )
        
        return mismatches[['poNo', 'itemCode', 'itemName', 'mismatchType', 'requiredAction', 'message']].to_dict('records')

    @staticmethod
    def _create_lookup_sets(df, field_name_1, field_name_2):
        """Create lookup sets for O(1) validation"""
        # Validate data
        for field_name in [field_name_1, field_name_2]:
            if field_name not in df.columns:
                self.logger.error("Field '{}' does not exist in DataFrame.", field_name)
                raise KeyError(f"Field '{field_name}' does not exist in DataFrame.")
                
        # Create lookup sets
        field_name_1_set = set(df[field_name_1].dropna())
        field_name_2_set = set(df[field_name_2].dropna())
        pairs_set = set(zip(df[field_name_1], df[field_name_2]))
        
        # Pre-deduplicated dataframes for merging
        pair_unique = df[[field_name_1, field_name_2]].drop_duplicates()

        return field_name_1_set, field_name_2_set, pairs_set, pair_unique

    @staticmethod
    def _convert_dict_to_df(warning_dict):
        """Convert warning dictionary to DataFrame"""
        rows = []
        for warning_type, warnings in warning_dict.items():
            for entry in warnings:
                rows.append({
                    'poNo': entry.get('poNo', ''),
                    'warningType': warning_type,
                    'mismatchType': entry.get('mismatchType', ''),
                    'requiredAction': entry.get('requiredAction', ''),
                    'message': entry.get('message', '')
                })
        warnings_df = pd.DataFrame(rows)

        if not rows:
            return pd.DataFrame(columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])

        return warnings_df