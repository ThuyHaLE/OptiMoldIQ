from agents.decorators import validate_init_dataframes
from loguru import logger
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
})
class PORequiredCriticalValidator(ConfigReportMixin):

    """
    A validator class that checks Purchase Order (PO) data consistency between 
    product records and purchase orders databases.
    
    This class validates that:
    1. Product records have valid PO numbers that exist in purchase orders
    2. Product record data matches corresponding purchase order data
    3. Generates warnings for any mismatches or invalid records
    """

    def __init__(self,
                 databaseSchemas_data: Dict, 
                 productRecords_df: pd.DataFrame, 
                 purchaseOrders_df: pd.DataFrame,
                 ):
        
        """
        Initialize the PORequiredCriticalValidator.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - productRecords_df: Production records with item, mold, machine data
            - purchaseOrders_df: Purchase order records
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()
        
        # Initialize logger for this class
        self.logger = logger.bind(class_="PORequiredCriticalValidator")

        # Database schema for validation
        self.databaseSchemas_data = databaseSchemas_data

        # Store config to validate in __init__
        self.productRecords_df = productRecords_df
        self.purchaseOrders_df = purchaseOrders_df
    
    def run_validations(self) -> Dict[str, Any]:

        """
        Run comprehensive PO validation checks.
        
        This method performs the following validations:
        1. Identifies overlapping fields between product records and purchase orders
        2. Finds invalid PO numbers (exist in product records but not in purchase orders)
        3. Validates data consistency for valid PO numbers
        4. Generates detailed warnings for all validation failures
        
        Returns:
            Dict containing:
            - result
                - DataFrame with detailed warnings for all validation failures
            - log_str
                - validation log entries for entire processing run
        """

        self.logger.info("Starting PORequiredCriticalValidator ...")
        
        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        # Initialize validation log entries for entire processing run
        validation_log_entries = [config_header]
        validation_log_entries.append(f"--Processing Summary--\n")
        validation_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

        try:
            # Preprocess product records to remove null PO numbers
            rm_null_productRecords_df = self._process_product_records()

            # Identify overlapping fields between both DataFrames for comparison
            overlap_field_list = list(set(rm_null_productRecords_df.columns) & set(self.purchaseOrders_df.columns))

            # Extract sets of PO numbers from both DataFrames
            productRecords_poNo_set = set(rm_null_productRecords_df['poNo'])
            purchaseOrders_poNo_set = set(self.purchaseOrders_df['poNo'])

            # Find PO numbers that exist in product records but not in purchase orders (invalid POs)
            invalid_poNo_list = list(productRecords_poNo_set - purchaseOrders_poNo_set)
            invalid_productRecords = rm_null_productRecords_df[
                rm_null_productRecords_df['poNo'].isin(invalid_poNo_list)
                ].copy()
            self.logger.info("Invalid PO list: {}", invalid_poNo_list)

            # Find valid PO numbers that exist in both DataFrames
            valid_poNo_list = list(productRecords_poNo_set & purchaseOrders_poNo_set)
            
            # Filter DataFrames to only include valid PO numbers for comparison
            productRecords_df_filtered = rm_null_productRecords_df[
                rm_null_productRecords_df['poNo'].isin(valid_poNo_list)
            ].copy()
            purchaseOrders_df_filtered = self.purchaseOrders_df[
                self.purchaseOrders_df['poNo'].isin(valid_poNo_list)
            ].copy()

            # Merge DataFrames on 'poNo' to align records for comparison
            # Suffixes are added to distinguish columns from each DataFrame
            merged = pd.merge(
                productRecords_df_filtered[overlap_field_list+['recordDate', 'workingShift', 'machineNo']], 
                purchaseOrders_df_filtered[overlap_field_list], 
                on='poNo', 
                suffixes=('_productRecords', '_purchaseOrders')
            )

            # Identify columns to compare (excluding 'poNo')
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

            # Determine overall match status across all fields
            field_match_columns = [f'{col}_match' for col in comparison_cols]
            merged['final_match'] = merged[field_match_columns].all(axis=1)
            self.logger.debug("Merged data with match results: {} - {}", 
                              merged.shape, merged.columns)

            # Generate warnings for field mismatches in valid PO numbers
            invalid_field_warnings = PORequiredCriticalValidator._process_warnings(
                merged, comparison_cols)
            
            # Generate warnings for invalid PO numbers
            invalid_po_warnings = (
                [] if not invalid_poNo_list
                else PORequiredCriticalValidator._process_invalid_po_warnings(invalid_productRecords)
            )

            # Combine all warnings into a single list
            all_invalid_warnings = invalid_field_warnings + invalid_po_warnings

            # Calculate summary statistics
            total_processed = len(merged) + len(invalid_poNo_list)
            total_valid = len(merged) - len(invalid_field_warnings)
            total_invalid = len(all_invalid_warnings)

            # Prepare final result DataFrame
            final_result = (
                pd.DataFrame(all_invalid_warnings) if all_invalid_warnings 
                else pd.DataFrame(columns=['poNo', 'warningType', 'mismatchType', 'requiredAction', 'message'])
            )

            # Log summary information for user review
            validation_log_entries.append("Validation Summary:")
            validation_log_entries.append(f"⤷ Total processed POs: {total_processed}")
            validation_log_entries.append(f"⤷ Valid POs: {total_valid}")
            validation_log_entries.append(f"⤷ Invalid POs: {total_invalid} (Field mismatches: {len(invalid_field_warnings)}, Non-existent orders: {len(invalid_po_warnings)})")

            # Generate detailed validation report
            reporter = DictBasedReportGenerator(use_colors=False)
            validation_summary = "\n".join(reporter.export_report({'Warning details': final_result}))
            validation_log_entries.append(f"{validation_summary}") 
            
            # Compile final validation log
            validation_log_str = "\n".join(validation_log_entries)
            self.logger.info("✅ Process finished!!!")

            return {
                    "result": final_result, 
                    "log_str": validation_log_str
                    }

        except Exception as e:
            self.logger.error("❌ Validation failed: {}", str(e))
            raise
    
    def _process_product_records(self, **kwargs) -> pd.DataFrame:
        
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
    
    @staticmethod
    def _process_warnings(merged_df: pd.DataFrame, 
                          comparison_cols: List) -> List:

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
    def _process_invalid_po_warnings(invalid_productRecords: pd.DataFrame) -> List:

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