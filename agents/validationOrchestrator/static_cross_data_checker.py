from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
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

        # Validate checking_df_name
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

        # Load all required DataFrames
        self._load_dataframes()
        
        self.filename_prefix = "static_cross_checker"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "StaticCrossDataChecker"

    def _load_dataframes(self):
        """Load all required DataFrames with consistent error handling"""
        dataframes_to_load = [
            ('itemInfo', 'itemInfo_df'),
            ('resinInfo', 'resinInfo_df'), 
            ('itemCompositionSummary', 'itemCompositionSummary_df'),
            ('productRecords', 'productRecords_df'),
            ('purchaseOrders', 'purchaseOrders_df')
        ]
        
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)
            if not path or not os.path.exists(path):
                self.logger.error("❌ Path to '{}' not found or does not exist.", path_key)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist.")
            
            df = pd.read_parquet(path)
            setattr(self, attr_name, df)
            self.logger.debug("{}: {} - {}", path_key, df.shape, df.columns)

    def _process_checking_data(self, checking_df_name):
        """Process checking data with consistent logic"""
        if checking_df_name == "productRecords":
            checking_df = self.productRecords_df.copy()
            # Remove null poNote and rename to poNo
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
        """Run all validation checks following PORequiredCriticalValidator pattern"""
        self.logger.info("Starting static cross data validation...")
        
        final_results = {}

        for df_name in self.checking_df_name:
            self.logger.info("Processing validations for: {}", df_name)
            checking_df = self._process_checking_data(df_name)
            
            # Run all validation checks
            item_warnings = self._check_item_info_matches(df_name, checking_df)
            resin_warnings = self._check_resin_info_matches(df_name, checking_df)
            composition_warnings = self._check_composition_matches(df_name, checking_df)
            
            # Combine all warnings following PORequiredCriticalValidator pattern
            all_warnings = item_warnings + resin_warnings + composition_warnings
            
            # Calculate summary statistics
            total_warnings = len(all_warnings)
            
            self.logger.info("Summary for {}: Total warnings: {} (Item: {}, Resin: {}, Composition: {})",
                            df_name, total_warnings, len(item_warnings), 
                            len(resin_warnings), len(composition_warnings))
            
            # Store results as DataFrame (similar to PORequiredCriticalValidator)
            final_results[df_name] = pd.DataFrame(all_warnings) if all_warnings else pd.DataFrame(
                columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])

        return final_results

    def run_validations_and_save_results(self, **kwargs):
        """Run validations and save results following PORequiredCriticalValidator pattern"""
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
        """Check for itemCode + itemName matches in itemInfo"""
        self.logger.debug("Checking item info matches for {}", df_name)
        
        # Extract required fields
        if df_name == "productRecords":
          subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo', 'itemCode', 'itemName']
        elif df_name == "purchaseOrders":
          subset_fields = ['poNo', 'itemCode', 'itemName']
        else:
          logger.error("Unknown df_name: {}", df_name)
          raise ValueError(f"Unknown df_name: {df_name}")

        po_subset = checking_df[subset_fields].dropna(subset=['itemCode', 'itemName']).copy()
        
        if po_subset.empty:
            return []
        
        # Create reference lookup
        item_pairs = self.itemInfo_df[['itemCode', 'itemName']].drop_duplicates()
        
        # Find mismatches using merge
        merged = po_subset.merge(item_pairs, on=['itemCode', 'itemName'], how='left', indicator=True)
        mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        if mismatches.empty:
            return []
        
        # Process warnings using static method
        return self._process_item_warnings(mismatches, df_name)

    def _check_resin_info_matches(self, df_name, checking_df):
        """Check for resinCode + resinName matches in resinInfo"""
        self.logger.debug("Checking resin info matches for {}", df_name)
        
        resin_configs = [
            ('plasticResinCode', 'plasticResin'),
            ('colorMasterbatchCode', 'colorMasterbatch'),
            ('additiveMasterbatchCode', 'additiveMasterbatch')
        ]
        
        all_resin_warnings = []
        
        for code_field, name_field in resin_configs:
            if code_field not in checking_df.columns or name_field not in checking_df.columns:
                continue
                
            # Extract required fields
            if df_name == "productRecords":
              subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo']
            elif df_name == "purchaseOrders":
              subset_fields = ['poNo']
            else:
              logger.error("Unknown df_name: {}", df_name)
              raise ValueError(f"Unknown df_name: {df_name}")

            # Extract and clean data
            resin_subset = checking_df[subset_fields + [code_field, name_field]].copy()
            resin_subset = resin_subset.dropna(subset=[code_field, name_field], how='all')
            resin_subset = resin_subset.rename(columns={code_field: 'resinCode', name_field: 'resinName'})
            
            if resin_subset.empty:
                continue
            
            # Create reference lookup
            resin_pairs = self.resinInfo_df[['resinCode', 'resinName']].drop_duplicates()
            
            # Find mismatches
            merged = resin_subset.merge(resin_pairs, on=['resinCode', 'resinName'], how='left', indicator=True)
            mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
            
            if not mismatches.empty:
                # Add plastic type context
                mismatches['plasticType'] = name_field
                warnings = self._process_resin_warnings(mismatches, df_name)
                all_resin_warnings.extend(warnings)
        
        return all_resin_warnings

    def _check_composition_matches(self, df_name, checking_df):
        """Check for item composition matches"""
        self.logger.debug("Checking composition matches for {}", df_name)
        
        composition_cols = [
            'itemCode', 'itemName', 'plasticResinCode', 'plasticResin',
            'colorMasterbatchCode', 'colorMasterbatch', 
            'additiveMasterbatchCode', 'additiveMasterbatch'
        ]

        # Extract required fields
        if df_name == "productRecords":
          subset_fields = ['poNo', 'recordDate', 'workingShift', 'machineNo']
        elif df_name == "purchaseOrders":
          subset_fields = ['poNo']
        else:
          logger.error("Unknown df_name: {}", df_name)
          raise ValueError(f"Unknown df_name: {df_name}")
          
        # Extract composition data
        po_subset = checking_df[subset_fields + composition_cols].dropna(subset=composition_cols, how='all').copy()
        
        if po_subset.empty:
            return []
        
        # Create reference lookup
        composition_pairs = self.itemCompositionSummary_df[composition_cols].drop_duplicates()
        
        # Find mismatches
        merged = po_subset.merge(composition_pairs, on=composition_cols, how='left', indicator=True)
        mismatches = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        if mismatches.empty:
            return []
        
        return self._process_composition_warnings(mismatches, df_name, composition_cols)

    @staticmethod
    def _process_item_warnings(mismatches_df, df_name):
        """Process item info warnings following PORequiredCriticalValidator pattern"""
        results = []
        
        for _, row in mismatches_df.iterrows():
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
            
            # Determine mismatch type (simplified logic)
            mismatch_type = f'{itemCode}_and_{itemName}_not_matched'
            required_action = f'update_itemInfo_or_double_check_{df_name}'
            
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"
            
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
        """Process resin info warnings following PORequiredCriticalValidator pattern"""
        results = []
        
        for _, row in mismatches_df.iterrows():
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
              
            mismatch_type = f'{resinCode}_and_{resinName}_not_matched'
            required_action = f'update_resinInfo_or_double_check_{df_name}'
            
            message = f"({context_info}) - Mismatch: {mismatch_type}. Please {required_action}"
            
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
        """Process composition warnings following PORequiredCriticalValidator pattern"""
        results = []
        for _, row in mismatches_df.iterrows():
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
            
            mismatch_type = f'{detail_info}_not_matched'
            required_action = f'update_itemCompositionSummary_or_double_check_{df_name}'
            
            message = f"({context_info}) - Mismatch: {mismatch_type} - Please: {required_action}"
            
            entry = {
                'poNo': poNo,
                'warningType': 'composition_warnings',
                'mismatchType': 'item_composition_not_matched',
                'requiredAction': required_action,
                'message': message
            }
            
            results.append(entry)
        
        return results