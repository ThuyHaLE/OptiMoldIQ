from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import os

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
})
class PORequiredCriticalValidator:

    """
    A validator class that checks Purchase Order (PO) data consistency between 
    product records and purchase orders databases.
    
    This class validates that:
    1. Product records have valid PO numbers that exist in purchase orders
    2. Product record data matches corresponding purchase order data
    3. Generates warnings for any mismatches or invalid records
    """

    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        """
        Initialize the PO validator with database paths and schemas.
        
        Args:
            source_path: Path to the directory containing data file annotations
            annotation_name: Name of the JSON file containing data file paths
            databaseSchemas_path: Path to the database schema configuration file
            default_dir: Default directory for output files
        """
        
        self.logger = logger.bind(class_="PORequiredCriticalValidator")

        # Load database schema configuration to understand data structure
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent, 
                                                         Path(databaseSchemas_path).name)
        
        # Load path annotations that contain actual file paths to data
        self.path_annotation = load_annotation_path(source_path, 
                                                    annotation_name)

        # Load and validate productRecords DataFrame
        productRecords_path = self.path_annotation.get('productRecords')
        if not productRecords_path or not os.path.exists(productRecords_path):
            self.logger.error("❌ Path to 'productRecords' not found or does not exist.")
            raise FileNotFoundError("Path to 'productRecords' not found or does not exist.")
        self.productRecords_df = pd.read_parquet(productRecords_path)
        self.logger.debug("productRecords: {} - {}", self.productRecords_df.shape, self.productRecords_df.columns)

        # Load and validate purchaseOrders DataFrame
        purchaseOrders_path = self.path_annotation.get('purchaseOrders')
        if not purchaseOrders_path or not os.path.exists(purchaseOrders_path):
            self.logger.error("❌ Path to 'purchaseOrders' not found or does not exist.")
            raise FileNotFoundError("Path to 'purchaseOrders' not found or does not exist.")
        self.purchaseOrders_df = pd.read_parquet(purchaseOrders_path)
        self.logger.debug("purchaseOrders: {} - {}", self.purchaseOrders_df.shape, self.purchaseOrders_df.columns)
        
        # Clean and preprocess productRecords DataFrame for validation
        self.rm_null_productRecords_df = self._process_product_records()
        
        # Set up output configuration for saving results
        self.filename_prefix = "po_required_critical_validator"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "PORequiredCriticalValidator"

    def _process_product_records(self, **kwargs):
        
        """
        Clean and preprocess the product records DataFrame.
        
        This method:
        1. Renames 'poNote' column to 'poNo' for consistency
        2. Removes records with null PO numbers (invalid records)
        
        Returns:
            pd.DataFrame: Cleaned product records with valid PO numbers
        """

        # Rename column for consistency and remove null PO numbers
        rm_null_productRecords_df = self.productRecords_df.rename(columns={'poNote': 'poNo'}).dropna(subset=['poNo'])
        self.logger.info('Removed null values, from {} rows to {} rows', 
                         len(self.productRecords_df), len(rm_null_productRecords_df))
        return rm_null_productRecords_df
    
    def run_validations(self, **kwargs):

        """
        Run comprehensive PO validation checks.
        
        This method performs the following validations:
        1. Identifies overlapping fields between product records and purchase orders
        2. Finds invalid PO numbers (exist in product records but not in purchase orders)
        3. Validates data consistency for valid PO numbers
        4. Generates detailed warnings for all validation failures
        
        Returns:
            pd.DataFrame: DataFrame containing all validation warnings and errors
        """

        # Find common columns between both DataFrames for comparison
        overlap_field_list = list(set(self.rm_null_productRecords_df.columns) & 
                                  set(self.purchaseOrders_df.columns))

        # Get unique PO numbers from both datasets for comparison
        productRecords_poNo_set = set(self.rm_null_productRecords_df['poNo'])
        purchaseOrders_poNo_set = set(self.purchaseOrders_df['poNo'])

        # Find PO numbers that exist in product records but not in purchase orders (invalid)
        invalid_poNo_list = list(productRecords_poNo_set - purchaseOrders_poNo_set)
        invalid_productRecords = self.rm_null_productRecords_df[
            self.rm_null_productRecords_df['poNo'].isin(invalid_poNo_list)
            ].copy()
        self.logger.info("Invalid PO list: {}", invalid_poNo_list)

        # Find PO numbers that exist in both datasets (valid for further validation)
        valid_poNo_list = list(productRecords_poNo_set & purchaseOrders_poNo_set)
        
        # Filter both DataFrames to include only valid PO numbers
        productRecords_df_filtered = self.rm_null_productRecords_df[
            self.rm_null_productRecords_df['poNo'].isin(valid_poNo_list)
        ].copy()
        purchaseOrders_df_filtered = self.purchaseOrders_df[
            self.purchaseOrders_df['poNo'].isin(valid_poNo_list)
        ].copy()

        # Merge DataFrames on PO number to compare field values
        # Include additional context fields from product records for reporting
        merged = pd.merge(
            productRecords_df_filtered[overlap_field_list+['recordDate', 'workingShift', 'machineNo']], 
            purchaseOrders_df_filtered[overlap_field_list], 
            on='poNo', 
            suffixes=('_productRecords', '_purchaseOrders')
        )

        # Get list of fields to compare (excluding 'poNo' which is the join key)
        comparison_cols = [c for c in overlap_field_list if c != 'poNo']

        # Perform vectorized comparison for all fields
        # Create boolean columns indicating whether each field matches
        for col in comparison_cols:
            col_pr = f'{col}_productRecords' # Column name from product records
            col_po = f'{col}_purchaseOrders' # Column name from purchase orders
            
            # Vectorized comparison that properly handles NaN values
            # Two values match if both are NaN OR both are equal
            merged[f'{col}_match'] = (
                (merged[col_pr].isna() & merged[col_po].isna()) | 
                (merged[col_pr] == merged[col_po])
            )

        # Calculate final match status: all fields must match for a record to be valid
        field_match_columns = [f'{col}_match' for col in comparison_cols]
        merged['final_match'] = merged[field_match_columns].all(axis=1)

        self.logger.debug("Merged data with match results: {} - {}", merged.shape, merged.columns)

        # Generate warnings for field mismatches in valid PO numbers
        invalid_field_warnings = PORequiredCriticalValidator._process_warnings(merged, comparison_cols)
        
        # Generate warnings for invalid PO numbers (if any exist)
        invalid_po_warnings = []
        if invalid_poNo_list:
            invalid_po_warnings = PORequiredCriticalValidator._process_invalid_po_warnings(invalid_productRecords)

        # Combine all warnings into a single list
        all_invalid_warnings = invalid_field_warnings + invalid_po_warnings

        # Calculate and log summary statistics
        total_processed = len(merged) + len(invalid_poNo_list)
        total_valid = len(merged) - len(invalid_field_warnings)
        total_invalid = len(all_invalid_warnings)

        self.logger.info("Summary: Total processed POs: {} - Valid POs: {} - Invalid POs: {} (Field mismatches: {}, Non-existent orders: {})",
                        total_processed, 
                        total_valid,
                        total_invalid,
                        len(invalid_field_warnings),
                        len(invalid_po_warnings))

        # Return warnings as DataFrame, or empty DataFrame with expected columns if no warnings
        return pd.DataFrame(all_invalid_warnings) if all_invalid_warnings else pd.DataFrame(columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])

    def run_validations_and_save_results(self, **kwargs):

        """
        Run validations and save results to Excel file.
        
        This method:
        1. Executes all validation checks
        2. Formats results for Excel export
        3. Saves results with versioning to prevent overwrites
        """

        self.data = {}

        # Run all validations and get results
        final_results = self.run_validations()
        self.data[f"Sheet1"] = final_results
        
        # Export results to Excel file with versioning
        self.logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    @staticmethod
    def _process_warnings(merged_df, comparison_cols):

        """
        Process field mismatch warnings for valid PO numbers.
        
        This method identifies records where PO numbers exist in both datasets
        but have mismatched field values, and generates detailed warning messages.
        
        Args:
            merged_df: DataFrame with merged data and match results
            comparison_cols: List of columns to check for mismatches
            
        Returns:
            list: List of dictionaries containing warning details
        """

        results = []
        
        # Process each record in the merged DataFrame
        for _, row in merged_df.iterrows():
            # Extract context information for the warning message
            poNo = row['poNo']
            recordDate = row['recordDate'].strftime('%Y-%m-%d')
            workingShift = row['workingShift']
            machineNo = row['machineNo']

            # Only process records that have field mismatches
            if not row['final_match']:
                # Identify which specific columns have mismatches
                mismatched_cols = []
                for col in comparison_cols:
                    if not row[f'{col}_match']:
                        mismatched_cols.append(col)
                
                # Create detailed mismatch information showing actual vs expected values
                mismatch_details = []
                for col in mismatched_cols:
                    pr_val = row[f'{col}_productRecords']
                    po_val = row[f'{col}_purchaseOrders']
                    mismatch_details.append(f"{col}: {pr_val} vs {po_val}")
                
                # Generate descriptive mismatch type and required action
                mismatch_type = f"PO was produced incorrectly with purchaseOrders. Details: {('_'.join(mismatched_cols)) + '_not_matched'}"
                required_action = 'stop progressing or double check productRecords'

                # Create context string for the warning message
                context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}"
                message = f"({context_info}) - Mismatch: {', '.join(mismatch_details)}. Please {required_action}"
                
                # Create structured warning entry
                entry = {
                    'poNo': poNo,
                    'warningType': 'product_info_not_matched',
                    'mismatchType': mismatch_type,
                    'requiredAction': required_action,
                    'message': message
                }
                
                results.append(entry)

        return results

    @staticmethod
    def _process_invalid_po_warnings(invalid_productRecords):

        """
        Process warnings for invalid PO numbers.
        
        This method generates warnings for product records that reference
        PO numbers that don't exist in the purchase orders database.
        
        Args:
            invalid_productRecords: DataFrame containing product records with invalid PO numbers
            
        Returns:
            list: List of dictionaries containing warning details for invalid POs
        """

        invalid_results = []
        
        # Process each invalid product record
        for _, row in invalid_productRecords.iterrows():
            # Extract context information for the warning message
            poNo = row['poNo']
            recordDate = row['recordDate'].strftime('%Y-%m-%d')
            workingShift = row['workingShift']
            machineNo = row['machineNo']

            # Define the mismatch type and required action for invalid PO
            mismatch_type = f'{poNo} does not exist in purchaseOrders.'
            required_action = 'stop progressing or double check productRecords'

            # Create context string and warning message
            context_info = f"{poNo}, {recordDate}, {workingShift}, {machineNo}"
            message = f"({context_info}) - Mismatch: {mismatch_type} . Please {required_action}"
            
            # Create structured warning entry for invalid PO
            entry = {
                'poNo': poNo,
                'warningType': 'PO_invalid',
                'mismatchType': 'PO does not exist in purchaseOrders.',
                'requiredAction': required_action,
                'message': message
            }
                
            invalid_results.append(entry)          
        
        return invalid_results