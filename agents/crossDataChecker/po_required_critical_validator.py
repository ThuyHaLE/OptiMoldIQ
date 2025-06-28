from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import os

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
})
class PORequiredCriticalValidator:
    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        self.logger = logger.bind(class_="PORequiredCriticalValidator")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent, 
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path, 
                                                    annotation_name)

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
        
        # Process productRecords DataFrame more efficiently
        self.rm_null_productRecords_df = self._process_product_records()
        
        self.filename_prefix = "po_required_critical_validator"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "PORequiredCriticalValidator"

    def _process_product_records(self, **kwargs):
        # Remove null values more efficiently
        rm_null_productRecords_df = self.productRecords_df.rename(columns={'poNote': 'poNo'}).dropna(subset=['poNo'])
        self.logger.info('Removed null values, from {} rows to {} rows', 
                         len(self.productRecords_df), len(rm_null_productRecords_df))
        return rm_null_productRecords_df
    
    def run_validations(self, **kwargs):
        # Find overlapping fields using set intersection
        overlap_field_list = list(set(self.rm_null_productRecords_df.columns) & 
                                  set(self.purchaseOrders_df.columns))

        # Get valid and invalid PO numbers
        productRecords_poNo_set = set(self.rm_null_productRecords_df['poNo'])
        purchaseOrders_poNo_set = set(self.purchaseOrders_df['poNo'])

        invalid_poNo_list = list(productRecords_poNo_set - purchaseOrders_poNo_set)
        invalid_productRecords = self.rm_null_productRecords_df[
            self.rm_null_productRecords_df['poNo'].isin(invalid_poNo_list)
            ].copy()
        self.logger.info("Invalid PO list: {}", invalid_poNo_list)

        valid_poNo_list = list(productRecords_poNo_set & purchaseOrders_poNo_set)
        # Filter dataframes using isin with valid PO list
        productRecords_df_filtered = self.rm_null_productRecords_df[
            self.rm_null_productRecords_df['poNo'].isin(valid_poNo_list)
        ].copy()
        purchaseOrders_df_filtered = self.purchaseOrders_df[
            self.purchaseOrders_df['poNo'].isin(valid_poNo_list)
        ].copy()

        # Merge dataframes
        merged = pd.merge(
            productRecords_df_filtered[overlap_field_list+['recordDate', 'workingShift', 'machineNo']], 
            purchaseOrders_df_filtered[overlap_field_list], 
            on='poNo', 
            suffixes=('_productRecords', '_purchaseOrders')
        )

        # Vectorized comparison for all fields at once
        comparison_cols = [c for c in overlap_field_list if c != 'poNo']

        # Create comparison columns using vectorized operations
        for col in comparison_cols:
            col_pr = f'{col}_productRecords'
            col_po = f'{col}_purchaseOrders'
            
            # Vectorized comparison that handles NaN values correctly
            merged[f'{col}_match'] = (
                (merged[col_pr].isna() & merged[col_po].isna()) | 
                (merged[col_pr] == merged[col_po])
            )

        # Calculate final match using vectorized all
        field_match_columns = [f'{col}_match' for col in comparison_cols]
        merged['final_match'] = merged[field_match_columns].all(axis=1)

        self.logger.debug("Merged data with match results: {} - {}", merged.shape, merged.columns)

        # Process warnings for merged data - only invalid records
        invalid_field_warnings = PORequiredCriticalValidator._process_warnings(merged, comparison_cols)
        
        # Process invalid PO warnings if any exist
        invalid_po_warnings = []
        if invalid_poNo_list:
            invalid_po_warnings = PORequiredCriticalValidator._process_invalid_po_warnings(invalid_productRecords)

        # Combine only invalid warnings
        all_invalid_warnings = invalid_field_warnings + invalid_po_warnings

        # Calculate summary statistics
        total_processed = len(merged) + len(invalid_poNo_list)
        total_valid = len(merged) - len(invalid_field_warnings)
        total_invalid = len(all_invalid_warnings)

        self.logger.info("Summary: Total processed POs: {} - Valid POs: {} - Invalid POs: {} (Field mismatches: {}, Non-existent orders: {})",
                        total_processed, 
                        total_valid,
                        total_invalid,
                        len(invalid_field_warnings),
                        len(invalid_po_warnings))

        return pd.DataFrame(all_invalid_warnings) if all_invalid_warnings else pd.DataFrame(columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])

    def run_validations_and_save_results(self, **kwargs):
        self.data = {}
        final_results = self.run_validations()
        self.data[f"Sheet1"] = final_results
        
        self.logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    @staticmethod
    def _process_warnings(merged_df, comparison_cols):
        results = []
        
        for _, row in merged_df.iterrows():
            poNo = row['poNo']
            recordDate = row['recordDate'].strftime('%Y-%m-%d')
            workingShift = row['workingShift']
            machineNo = row['machineNo']
            
            if not row['final_match']:  # Only process invalid records
                # Find mismatched columns
                mismatched_cols = []
                for col in comparison_cols:
                    if not row[f'{col}_match']:
                        mismatched_cols.append(col)
                
                mismatch_type = ', '.join(mismatched_cols)
                required_action = f"please check the poNo, there is not matching in {mismatch_type}"
                
                # Create message with mismatch details
                mismatch_details = []
                for col in mismatched_cols:
                    pr_val = row[f'{col}_productRecords']
                    po_val = row[f'{col}_purchaseOrders']
                    mismatch_details.append(f"{col}: {pr_val} vs {po_val}")
                
                context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}"
                message = f"({context_info}, {', '.join(mismatch_details)}) mismatch: {mismatch_type} - required action: {required_action}"
                
                entry = {
                    'poNo': poNo,
                    'warningType': 'invalid',
                    'mismatchType': mismatch_type,
                    'requiredAction': required_action,
                    'message': message
                }
                
                results.append(entry)

        return results

    @staticmethod
    def _process_invalid_po_warnings(invalid_productRecords):
        invalid_results = []
        
        for _, row in invalid_productRecords.iterrows():
            poNo = row['poNo']
            recordDate = row['recordDate'].strftime('%Y-%m-%d')
            workingShift = row['workingShift']
            machineNo = row['machineNo']

            mismatch_type = 'This order does not exist.'
            required_action = 'Stop progressing or double check poNo'

            context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}"
            message = f"({context_info}, This order does not exist.) mismatch: {mismatch_type} - required action: {required_action}"
            
            entry = {
                'poNo': poNo,
                'warningType': 'invalid',
                'mismatchType': mismatch_type,
                'requiredAction': required_action,
                'message': message
            }
                
            invalid_results.append(entry)          
        
        return invalid_results