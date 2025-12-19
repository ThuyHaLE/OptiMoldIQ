from agents.decorators import validate_init_dataframes
from loguru import logger
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
import pandas as pd
from pandas.api.types import is_object_dtype
from datetime import datetime, timedelta
import ast
import re
from typing import Dict, List, Any, Tuple
from configs.shared.config_report_format import ConfigReportMixin

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
})
class ProgressTracker(ConfigReportMixin):

    """
    Class to track order production progress
    Main functions:
    - Track production status of orders
    - Calculate completion progress
    - Analyze production data by shift, machine, mold
    """

    def __init__(self, 
                 pro_status_schema: Dict,
                 databaseSchemas_data: Dict, 
                 productRecords_df: pd.DataFrame,
                 purchaseOrders_df: pd.DataFrame,
                 moldSpecificationSummary_df: pd.DataFrame,
                 validation_data: Dict = None):
        
        """
        Initialize the ProgressTracker.
        
        Args:
            - pro_status_schema: Schema to process productRecords
            - databaseSchemas_data: Database schemas for validation
            - productRecords_df: Production records with item, mold, machine data
            - purchaseOrders_df: Purchase order records
            - moldSpecificationSummary_df: Mold specifications and compatible items
            - validation_data: Validation data from ValidationOrchestrator (if any)
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ProgressTracker")

        self.pro_status_schema = pro_status_schema
        self.databaseSchemas_data = databaseSchemas_data

        self.validation_data = validation_data

        self.productRecords_df = productRecords_df
        self.purchaseOrders_df = purchaseOrders_df
        self.moldSpecificationSummary_df = moldSpecificationSummary_df

    def run_tracking(self) -> Dict[str, Any]:

        """
        Main function to process and generate production status report

        Process:
        1. Merge order data with mold information
        2. Extract and summarize production data
        3. Process production status
        4. Add warning information
        """

        self.logger.info("Starting ProgressTracker ...")

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        # Initialize validation log entries for entire processing run
        tracking_log_lines = [config_header]
        tracking_log_lines.append(f"--Processing Summary--\n")
        tracking_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")

        try:
            # Step 1: Merge purchase orders with mold specification summary
            ordersInfo_df = self._merge_purchase_mold_specification()

            # Step 2: Extract and aggregate product record information. 
            # Including: 
            # - Aggregated production data by poNote, 
            # - List of POs currently in production, 
            # - DataFrame of records without production
            agg_df, producing_po_list, notWorking_productRecords_df = self._extract_product_records(
                self.productRecords_df, 
                self.pro_status_schema['shift_start_map'])

            # Step 3: Generate production status report
            # Process production status information and handle data type conversions.
            pro_status_df = self._pro_status_processing(
                pd.merge(
                    ordersInfo_df, 
                    agg_df, 
                    on='poNo', 
                    how='left'
                    ),
                self.pro_status_schema['pro_status_fields'],
                producing_po_list,
                self.pro_status_schema['pro_status_dtypes']
                )
            
            # Mark pending POs as paused if they haven't been updated in the latest shift
            pro_status_df = self._mark_paused_pending_pos(
                self.productRecords_df,
                pro_status_df,
                self.pro_status_schema['shift_start_map']
                )

            # Get the latest machine information for each machine based on working shift timestamp.
            # Includes machines that were not working (poNote is null) in the most recent shift.
            lastest_info_df = self._get_latest_po_info(
                self.productRecords_df,
                self.pro_status_schema['shift_start_map'],
                keys=['machineNo', 'moldNo']
                )
            
            # Merge latest machine information into production status DataFrame
            updated_lastest_info_df = pro_status_df.merge(lastest_info_df, 
                                                          how='left', 
                                                          on='poNo')

            # Step 4: Extract warning information from validationOrchestrator's output
            warning_merge_dict, total_warnings = self._extract_validation_data(self.validation_data)
            updated_pro_status_df = self._add_warning_notes_column(updated_lastest_info_df, 
                                                                   warning_merge_dict)

            # Step 5: Prepare final output data structure
            final_result = {
                        "productionStatus": updated_pro_status_df,

                        'materialComponentMap': self._pro_status_fattening(updated_pro_status_df,
                                                                           field_name = 'materialComponentMap'),

                        'moldShotMap': self._pro_status_fattening(updated_pro_status_df,
                                                                  field_name = 'moldShotMap'),

                        'machineQuantityMap': self._pro_status_fattening(updated_pro_status_df,
                                                                         field_name = 'machineQuantityMap'),
                        
                        'dayQuantityMap': self._pro_status_fattening(updated_pro_status_df,
                                                                     field_name = 'dayQuantityMap'),
                        
                        "notWorkingStatus": notWorking_productRecords_df,
                        }

            # Add total warnings if available
            if total_warnings:
                final_result.update(total_warnings)

            # Generate validation summary
            reporter = DictBasedReportGenerator(use_colors=False)
            tracking_summary = "\n".join(reporter.export_report(final_result))
            tracking_log_lines.append(f"{tracking_summary}")
            
            # Compile tracking log
            tracking_log_str = "\n".join(tracking_log_lines)
            self.logger.info("✅ Process finished!!!")

            return {
                "result": final_result, 
                "tracking_summary": tracking_summary,
                "log_str": tracking_log_str}
        
        except Exception as e:
            self.logger.error("Failed to process ProgressTracker: {}", str(e))
            raise RuntimeError(f"ProgressTracker processing failed: {str(e)}") from e
    
    #---------------------------------------------------------------#
    # STEP 1: MERGE PURCHASE ORDERS WITH MOLD SPECIFICATION SUMMARY #
    #---------------------------------------------------------------#
    def _merge_purchase_mold_specification(self) -> pd.DataFrame:
        """Merge purchase orders with mold specification summary."""
        return pd.merge(
                self.purchaseOrders_df[['poNo', 'poReceivedDate', 'poETA', 'itemCode',	'itemName', 'itemQuantity']],
                self.moldSpecificationSummary_df[['itemCode', 'itemType', 'moldList']],
                on='itemCode',
                how='left')
    
    #---------------------------------------------------------------#
    # STEP 2: EXTRACT AND AGGREGATE PRODUCT RECORD INFORMATION      #
    #---------------------------------------------------------------#
    def _extract_product_records(self, 
                                 productRecords_df: pd.DataFrame,
                                 shift_start_map: Dict
                                 ) -> Tuple[pd.DataFrame, List, pd.DataFrame]:

        """
        Extract and aggregate product record information.

        Args:
            productRecords_df: DataFrame containing production records
            shift_start_map: Dictionary mapping shift codes to start times

        Returns:
            pd.DataFrame: Aggregated production data by poNote
            List: List of POs currently in production
            pd.DataFrame: DataFrame of records without production
        """

        # Input validation
        if productRecords_df.empty:
            self.logger.error("Empty productRecords_df provided")
            raise ValueError("Empty productRecords_df provided.")

        # Create derived columns
        productRecords_df = productRecords_df.copy()

        # Combine date and shift into a string identifier
        productRecords_df['dateShiftCombined'] = (productRecords_df['recordDate'].dt.strftime('%Y-%m-%d') + 
                                                  '_shift_' + productRecords_df['workingShift']
                                                  )

        # Create a unique machine history identifier
        productRecords_df['machineHist'] = productRecords_df['machineNo'] + '_' + productRecords_df['machineCode']
        self.logger.debug("Total records => {}: {}", 
                     productRecords_df.shape, productRecords_df.columns.to_list()
                     )

        # Split records into those with no production and those with actual production
        not_working_mask = (productRecords_df['itemTotalQuantity'].isna() | 
                            (productRecords_df['itemTotalQuantity'] == 0)
                            )

        # DataFrame for records without production
        notWorking_productRecords_df = productRecords_df[not_working_mask].copy()
        notWorking_productRecords_df['recordDate'] = notWorking_productRecords_df['recordDate'].dt.strftime('%Y-%m-%d')

        # DataFrame for records with production
        haveWorking_productRecords_df = productRecords_df[~not_working_mask].copy()

        self.logger.debug("Not working => {}: {}", 
                     notWorking_productRecords_df.shape, notWorking_productRecords_df.columns.to_list()
                     )
        self.logger.debug("Have working => {}: {}", 
                     haveWorking_productRecords_df.shape, haveWorking_productRecords_df.columns.to_list()
                     )

        if haveWorking_productRecords_df.empty:
            self.logger.error("No working production records found")
            raise ValueError("No working production records found.")

        # Determine the latest production time based on working shift start times
        time_to_shift = {datetime.strptime(v, "%H:%M").time(): k for k, v in shift_start_map.items()}

        # Calculate shift start time for each record
        shift_starts = haveWorking_productRecords_df.apply(
            lambda row: ProgressTracker._get_shift_start(row, shift_start_map), axis=1)
        latest_shift_start = shift_starts.max()

        if pd.isna(latest_shift_start):
            logger.error("Could not determine latest shift start")
            raise ValueError("Could not determine latest shift start.")

        else:
            # Determine the latest date and shift
            latest_date = latest_shift_start.date().strftime("%Y-%m-%d")
            latest_shift = time_to_shift.get(latest_shift_start.time())
            logger.debug("Latest date: {}, Latest shift: {}", latest_date, latest_shift)

        # Get POs still being produced in the latest shift
        latest_shift_mask = (
            (haveWorking_productRecords_df['recordDate'] == latest_date) &
            (haveWorking_productRecords_df['workingShift'] == str(latest_shift))
            )

        # Get a list of poNotes that are still being produced in the latest shift
        producing_po_list = haveWorking_productRecords_df[latest_shift_mask]['poNote'].tolist()
        logger.debug(f"Producing PO list: {producing_po_list}")

        # Extract material codes
        resin_code_map = ProgressTracker._extract_material_codes(haveWorking_productRecords_df)

        # Aggregate multiple production metrics by poNote
        agg_df = haveWorking_productRecords_df.groupby('poNote').agg(

            moldedQuantity=('itemGoodQuantity', 'sum'),
            totalMoldShot=('moldShot', 'sum'),
            startedDate=('recordDate', 'min'),
            endDate=('recordDate', 'max'),
            totalDay=('recordDate', 'nunique'),
            totalShift=('dateShiftCombined', 'count'),
            machineHist=('machineHist', lambda x: x.dropna().unique().tolist()),
            moldHist=('moldNo', lambda x: x.dropna().unique().tolist()),
            moldCavity=('moldCavity', lambda x: x.dropna().unique().tolist()),
            plasticResinCode=('plasticResinCode', lambda x: x.dropna().unique().tolist()),
            colorMasterbatchCode=('colorMasterbatchCode', lambda x: x.dropna().unique().tolist()),
            additiveMasterbatchCode=('additiveMasterbatchCode', lambda x: x.dropna().unique().tolist()),

            ).reset_index()

        # Create aggregation maps
        maps = ProgressTracker._create_aggregation_maps(haveWorking_productRecords_df)

        # Add mapping columns
        agg_df['moldShotMap'] = agg_df['poNote'].map(maps['mold_map'])
        agg_df['machineQuantityMap'] = agg_df['poNote'].map(maps['machine_map'])
        agg_df['dayQuantityMap'] = agg_df['poNote'].map(maps['date_map'])
        agg_df['shiftQuantityMap'] = agg_df['poNote'].map(maps['shift_map'])
        agg_df['materialComponentMap'] = agg_df['poNote'].map(resin_code_map)

        # Rename poNote to poNo for consistency
        agg_df = agg_df.rename(columns={'poNote': 'poNo'})

        return agg_df, producing_po_list, notWorking_productRecords_df
    
    @staticmethod
    def _get_shift_start(row: pd.Series, 
                         shift_start_map: Dict,
                         date_field_name: str ='recordDate',
                         shift_field_name: str ='workingShift') -> pd.Timestamp:

        """
        Calculate the shift start datetime for a given row.

        Args:
            row: DataFrame row containing date and shift information
            shift_start_map: Dictionary mapping shift codes to start times (HH:MM format)
            date_field_name: Name of the date field in the row
            shift_field_name: Name of the shift field in the row

        Returns:
            pd.Timestamp: Shift start datetime or pd.NaT if invalid
        """

        try:
            # Convert date to datetime format
            date = pd.to_datetime(row[date_field_name])
            shift = str(row[shift_field_name])
            start_time_str = shift_start_map.get(shift)

            # Check if the shift code is valid
            if not start_time_str:
                logger.warning(f"Invalid shift code: {shift}")
                return pd.NaT

            # Extract hours and minutes from string
            hour, minute = map(int, start_time_str.split(":"))

            # Create datetime combining shift start date and time
            start_datetime = datetime.combine(
                date.date(), 
                datetime.min.time()) + timedelta(hours=hour, minutes=minute)

            return pd.Timestamp(start_datetime)

        except Exception as e:
            logger.error(f"Error calculating shift start for row: {e}")
            return pd.NaT

    @staticmethod
    def _extract_material_codes(df: pd.DataFrame) -> Dict:
        """
        Extract material component combinations for each poNote.

        Args:
            df: DataFrame with production records

        Returns:
            dict: Dictionary mapping poNote to list of material component combinations
        """

        def extract_material_combinations(group: pd.DataFrame) -> List:
            """
            Extract list of material component combinations from a group
            """
            combinations = []

            for _, row in group.iterrows():

                combination = {
                    'plasticResinCode': row.get('plasticResinCode') if pd.notna(row.get('plasticResinCode')) else None,
                    'colorMasterbatchCode': row.get('colorMasterbatchCode') if pd.notna(row.get('colorMasterbatchCode')) else None,
                    'additiveMasterbatchCode': row.get('additiveMasterbatchCode') if pd.notna(row.get('additiveMasterbatchCode')) else None
                }

                # Validation
                if combination['plasticResinCode'] == None:
                    logger.error("The material combination is required to include at least one component of plasticResinCode")
                    raise ValueError("The material combination is required to include at least one component of plasticResinCode")

                if combination not in combinations:
                    combinations.append(combination)

            return combinations

        return (
            df.groupby('poNote')
            .apply(extract_material_combinations, include_groups=False)
            .to_dict()
        )
    
    @staticmethod
    def _create_aggregation_maps(df: pd.DataFrame) -> Dict:

        """
        Create aggregation maps for molds, machines, dates, and shifts.

        Args:
            df: DataFrame with production records

        Returns:
            dict: Dictionary containing various aggregation maps
        """

        maps = {}

        # Map summarizes the number of mold shots by mold for each PO
        maps['mold_map'] = (
            df.groupby(['poNote', 'moldNo'])['moldShot']
            .sum()
            .reset_index()
            .groupby('poNote')[['moldNo', 'moldShot']]
            .apply(lambda x: {k: int(v) for k, v in zip(x['moldNo'], x['moldShot'])})
            .to_dict()
        )

        # Map good quantity summary by machine for each PO
        maps['machine_map'] = (
            df.groupby(['poNote', 'machineHist'])['itemGoodQuantity']
            .sum()
            .reset_index()
            .groupby('poNote')[['machineHist', 'itemGoodQuantity']]
            .apply(lambda x: {k: int(v) for k, v in zip(x['machineHist'], x['itemGoodQuantity'])})
            .to_dict()
        )

        # Map sums up good quantity by day for each PO
        maps['date_map'] = (
            df.groupby(['poNote', 'recordDate'])['itemGoodQuantity']
            .sum()
            .reset_index()
            .groupby('poNote')[['recordDate', 'itemGoodQuantity']]
            .apply(lambda x: {
                k.strftime('%Y-%m-%d'): int(v)
                for k, v in zip(x['recordDate'], x['itemGoodQuantity'])
            })
            .to_dict()
        )

        # Map sums up good quantity by shift+day for each PO
        maps['shift_map'] = (
            df.groupby(['poNote', 'dateShiftCombined'])['itemGoodQuantity']
            .sum()
            .reset_index()
            .groupby('poNote')[['dateShiftCombined', 'itemGoodQuantity']]
            .apply(lambda x: {
                k: int(v)
                for k, v in zip(x['dateShiftCombined'], x['itemGoodQuantity'])
            })
            .to_dict()
        )

        return maps

    #---------------------------------------------------------------#
    # STEP 3: GENERATE PRODUCTION STATUS REPORT                     #
    #---------------------------------------------------------------#
    def _pro_status_processing(self, 
                               pro_status_df: pd.DataFrame, 
                               pro_status_fields: List,
                               producing_po_list: List, 
                               pro_status_dtypes: Dict) -> pd.DataFrame:

        """
        Process production status information and handle data type conversions.

        Args:
            pro_status_df: DataFrame with production status data
            pro_status_fields: List of fields to include in output
            producing_po_list: List of POs currently in production
            pro_status_dtypes: Dictionary of data types for columns

        Returns:
            pd.DataFrame: Processed production status DataFrame
        """

        # Input validation
        if pro_status_df.empty:
            self.logger.error("Empty pro_status_df provided")
            raise ValueError("Empty pro_status_df provided.")

        # Work on a copy to avoid modifying original DataFrame
        pro_status_df = pro_status_df.copy()

        # Calculate remaining items to be produced
        pro_status_df['itemRemain'] = pro_status_df['itemQuantity'] - pro_status_df['moldedQuantity'].fillna(0)

        # Determine production status
        pro_status_df['proStatus'] = 'PENDING'  # Default status

        # Mark completed orders
        molded_mask = pro_status_df['itemRemain'] == 0
        pro_status_df.loc[molded_mask, 'proStatus'] = 'MOLDED'
        pro_status_df.loc[molded_mask, 'actualFinishedDate'] = pro_status_df.loc[molded_mask, 'endDate']

        # Check for missing actualFinishedDate in completed orders
        missing_actual_finish = molded_mask & pro_status_df['actualFinishedDate'].isna()
        # Log warning if any completed orders are missing actualFinishedDate
        if missing_actual_finish.any():
            self.logger.warning("Some completed orders are missing actualFinishedDate:\n{}",
                            pro_status_df.loc[missing_actual_finish, ['poNo', 'endDate']])

        # Mark orders currently in production
        molding_mask = (pro_status_df['poNo'].isin(producing_po_list)) & (pro_status_df['itemRemain'] != 0)
        pro_status_df.loc[molding_mask, 'proStatus'] = 'MOLDING'

        # Determine status compared to ETA (Expected Time of Arrival)
        pro_status_df['etaStatus'] = 'PENDING' # Default: PENDING

        # ONTIME: Finish on or before ETA
        on_time_mask = (
            pro_status_df['actualFinishedDate'].notnull() &
            (pro_status_df['itemRemain'] == 0) &
            (pro_status_df['actualFinishedDate'] <= pro_status_df['poETA'])
        )
        pro_status_df.loc[on_time_mask, 'etaStatus'] = 'ONTIME'

        # LATE: Finish later than ETA
        late_mask = (
            pro_status_df['actualFinishedDate'].notnull() &
            (pro_status_df['itemRemain'] == 0) &
            (pro_status_df['actualFinishedDate'] > pro_status_df['poETA'])
        )
        pro_status_df.loc[late_mask, 'etaStatus'] = 'LATE'

        # Apply data types
        try:
            pro_status_df = pro_status_df.astype(pro_status_dtypes)
        except Exception as e:
            self.logger.error("Error applying data types: {}", e)
            raise ValueError(f"Failed to apply data types: {e}")

        # Handle datetime columns and NaT values
        for col in pro_status_df.select_dtypes(include='datetime'):
            # Create a mask for NaT values
            nat_mask = pro_status_df[col].isna()
            # Convert datetime values into '%Y-%m-%d'
            formatted_dates = pro_status_df.loc[~nat_mask, col].dt.strftime('%Y-%m-%d')
            # Convert entire column to object
            pro_status_df[col] = pro_status_df[col].astype("object")
            # Replace only the NaT positions (now None) with pd.NA
            pro_status_df.loc[nat_mask, col] = pd.NA
            # Replace datetime values with '%Y-%m-%d'
            pro_status_df.loc[~nat_mask, col] = formatted_dates

        # Fill remaining NaN values
        pro_status_df.fillna(pd.NA, inplace=True)

        # Debugging: Log NaN, null, and pd.NA counts for object dtype columns
        for col in pro_status_df.columns:
            if is_object_dtype(pro_status_df[col]):
                series = pro_status_df[col]
                nas = series.isna().sum()
                nulls = series.isnull().sum()
                # Use .apply to deal with (pd.NA == pd.NA) return pd.NA
                pdna = series.apply(lambda x: x is pd.NA).sum()
                self.logger.debug(f"{col}: isna = {nas}, isnull = {nulls}, pd.NA (by identity) = {pdna}")
        # Ensure all expected fields are present in the final DataFrame
        assert set(pro_status_fields).issubset(pro_status_df.columns), \
            f"Missing expected fields in final dataframe: {set(pro_status_fields) - set(pro_status_df.columns)}"

        return pro_status_df[pro_status_fields]

    @staticmethod
    def _mark_paused_pending_pos(df: pd.DataFrame, 
                                 proStatus_df: pd.DataFrame, 
                                 shift_start_map: Dict) -> pd.DataFrame:
        """Mark pending POs as paused if they haven't been updated in the latest shift."""
        # Filter only production records with item quantity > 0
        df_work = df[df['itemTotalQuantity'] > 0].copy()

        # Ensure workingShift is a string and map it to shift start time
        df_work['workingShift'] = df_work['workingShift'].astype(str)
        df_work['shift_time'] = df_work['workingShift'].map(shift_start_map).fillna("00:00")

        # Create a full datetime column by combining recordDate and shift start time
        df_work['shiftStartTimestamp'] = pd.to_datetime(
            df_work['recordDate'].astype(str) + ' ' + df_work['shift_time'],
            format='%Y-%m-%d %H:%M',
            errors='coerce'
        )

        # Extract list of pending POs from proStatus_df where itemRemain > 0 and status is 'PENDING'
        pending_list = proStatus_df[
            (proStatus_df['itemRemain'] > 0) &
            (proStatus_df['proStatus'] == 'PENDING')
        ]['poNo'].tolist()

        # Filter records of those pending POs
        df_pending = df_work[df_work['poNote'].isin(pending_list)]

        # Get the most recent production timestamp for each pending PO
        pending_latest_shift = df_pending.groupby('poNote')['shiftStartTimestamp'].max().reset_index()

        # Get the most recent production timestamp for all POs
        total_latest_shift = df_work.groupby('poNote')['shiftStartTimestamp'].max().reset_index()
        latest_shift_start = total_latest_shift['shiftStartTimestamp'].max()

        # Identify pending POs that have not been updated until the most recent production timestamp
        paused_mask = pending_latest_shift['shiftStartTimestamp'] < latest_shift_start
        paused_po_list = pending_latest_shift[paused_mask]['poNote'].tolist()

        # Mark those POs as 'PAUSED' in proStatus_df
        proStatus_df.loc[proStatus_df['poNo'].isin(paused_po_list), 'proStatus'] = 'PAUSED'

        return proStatus_df

    @staticmethod
    def _get_latest_po_info(df: pd.DataFrame, 
                            shift_start_map: Dict, 
                            keys: List =['machineNo', 'moldNo']) -> pd.DataFrame:

        """
        Get the latest machine information for each machine based on working shift timestamp.
        Includes machines that were not working (poNote is null) in the most recent shift.

        Args:
            df: DataFrame containing product record data
            shift_start_map: Dictionary mapping working shift codes to start times
            keys: List of additional columns to include in the output

        Returns:
            DataFrame with the latest machine information per machine (poNo may be null)
        """

        df_work = df.copy()

        # Create shift timestamp (vectorized)
        df_work['workingShift'] = df_work['workingShift'].astype(str)
        df_work['shift_time'] = df_work['workingShift'].map(shift_start_map).fillna("00:00")

        # Combine date and time into timestamp
        df_work['shiftStartTimestamp'] = pd.to_datetime(
            df_work['recordDate'].astype(str) + ' ' + df_work['shift_time'],
            format='%Y-%m-%d %H:%M',
            errors='coerce'
        )

        # Get the most recent record for each machine (including idle machines)
        latest_indices = df_work.groupby('poNote')['shiftStartTimestamp'].max().reset_index()
        latest_per_po = df_work.merge(latest_indices, on=['poNote', 'shiftStartTimestamp'], how='inner')

        # Select and rename columns
        result_columns = ['poNote', 'shiftStartTimestamp'] + keys
        result = latest_per_po[result_columns].copy()

        # Rename columns (avoid duplicate column names)
        new_column_names = ['poNo', 'lastestRecordTime', 'lastestMachineNo', 'lastestMoldNo']
        result.columns = new_column_names

        return result[result['poNo'].notna()].reset_index(drop=True)

    #---------------------------------------------------------------#
    # STEP 4: EXTRACT WARNING INFORMATION FROM VALIDATION DATA      #
    #---------------------------------------------------------------#  
    def _extract_validation_data(self, 
                                 total_warnings: Dict) -> Tuple[Dict, Dict]:

        """
        Process summarize mismatch warnings.

        Returns:
            - warning_merge_dict: dict of grouped mismatch warnings by PO
            - total_warnings: all sheets collected from the Excel file
        """

        try:
            if not total_warnings:
                self.logger.info("No warnings found in change log")
                return {}, {}

            if 'po_mismatch_warnings' in total_warnings:
                po_mismatch_df = total_warnings['po_mismatch_warnings']

                # Validate the DataFrame before processing
                if po_mismatch_df.empty:
                    self.logger.warning("po_mismatch_warnings DataFrame is empty")
                    return {}, total_warnings

                # Check required columns exist
                required_columns = ['poNo', 'mismatchType']
                missing_cols = set(required_columns) - set(po_mismatch_df.columns)
                if missing_cols:
                    self.logger.error("Missing required columns in po_mismatch_warnings: {}", missing_cols)
                    return {}, total_warnings

                # Aggregate mismatch counts by PO
                warning_merge_dict = ProgressTracker._aggregate_po_mismatches(po_mismatch_df)
                return warning_merge_dict, total_warnings
            else:
                self.logger.info("No po_mismatch_warnings found in change log")
                return {}, total_warnings

        except Exception as e:
            self.logger.error("Error processing change log: {}", str(e))
            return {}, {}

    @staticmethod
    def _aggregate_po_mismatches(df: pd.DataFrame) -> Dict:

        """
        Group mismatch warnings by PO and mismatch type, then count the occurrences of each type.
        Also logs the mismatch ratio for each type within each PO.
        """

        grouped = df.groupby(['poNo', 'mismatchType']).size().reset_index(name='count')

        result = {}
        for _, row in grouped.iterrows():
            po_no = row['poNo']
            mismatch_type = row['mismatchType']
            count = row['count']

            if po_no not in result:
                result[po_no] = {}
            result[po_no][mismatch_type] = count

        # Log mismatch ratio for each PO
        for po_no, mismatches in result.items():
            total_issues = sum(mismatches.values())
            for mismatch_type, count in mismatches.items():
                logger.info("{} - Mismatch: {} - Ratio: {}/{}", po_no, mismatch_type, count, total_issues)

        return result

    @staticmethod
    def _add_warning_notes_column(df: pd.DataFrame, 
                                  warning_dict: Dict) -> pd.DataFrame:

        """
        Add a 'warningNotes' column to the DataFrame based on the warning dictionary.
        Each row will contain a semicolon-separated list of mismatch types for its PO.
        """

        df = df.copy()

        if warning_dict:
            def get_warning_notes(po):
                if po in warning_dict:
                    return "; ".join(warning_dict[po].keys())
                else:
                    return ""

            df["warningNotes"] = df["poNo"].apply(get_warning_notes)

        else:
            df["warningNotes"] = ""

        return df

    #---------------------------------------------------------------#
    # STEP 5: PREPARE FINAL OUTPUT DATA STRUCTURE                   #
    #---------------------------------------------------------------#   
    def _pro_status_fattening(self,
                              df: pd.DataFrame,
                              field_name: str = 'moldShotMap') -> pd.DataFrame:

        """
        Optimize and flatten data from mapping fields in a DataFrame.

        Args:
            df: Input DataFrame
            field_name: The name of the field to process

        Returns:
            Flattened DataFrame

        Raises:
            ValueError: If the field_name is not supported
        """

        # Constants - defined once
        SUPPORTED_FIELDS = frozenset(['moldShotMap', 'machineQuantityMap', 'dayQuantityMap', 'materialComponentMap'])
        COLUMNS_TO_KEEP = ['poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
                          'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate']
        NAME_MAPPING = {
            'mold': 'moldNo',
            'shot': 'shotCount',
            'machine': 'machineCode',
            'quantity': 'moldedQuantity',
            'day': 'workingDay'
        }

        # Validation
        if field_name not in SUPPORTED_FIELDS:
            raise ValueError(f"Field '{field_name}' not supported. Must be one of: {SUPPORTED_FIELDS}")

        # Filter data once
        filtered_df = df.dropna(subset=['startedDate']).copy()

        if filtered_df.empty:
            return pd.DataFrame()

        # Split the field name once
        field_parts = self._split_field_name(field_name)
        if len(field_parts) != 2:
            raise ValueError(f"Invalid field name format: {field_name}")

        first_element, second_element = field_parts

        # Special case: materialComponentMap
        if field_name == 'materialComponentMap':
            return self._process_material_components(filtered_df, COLUMNS_TO_KEEP)

        # Process other map fields
        return self._process_map_fields(filtered_df, field_name, first_element, second_element,
                                                        NAME_MAPPING, COLUMNS_TO_KEEP)

    @staticmethod
    def _split_field_name(field_name: str) -> List[str]:

        """Split field name into parts."""

        clean_name = field_name.replace("Map", "")
        match = re.match(r'^([a-z]+)([A-Z].*)$', clean_name)

        if match:
            return [match.group(1), match.group(2).lower()]
        return [clean_name]

    @staticmethod
    def _safe_literal_eval(data: Any) -> Any:

        """Safely parse a string into a Python object."""

        if not isinstance(data, str):
            return data

        try:
            return ast.literal_eval(data)
        except (ValueError, SyntaxError):
            return None
        
    @staticmethod
    def _process_material_components(filtered_df: pd.DataFrame,
                                     columns_to_keep: List[str]) -> pd.DataFrame:

        """Process materialComponentMap field."""

        def extract_material_info(material_data: Any) -> Dict[str, Any]:
            """Extract material information from data."""
            default_result = {
                'plasticResinCode': None,
                'colorMasterbatchCode': None,
                'additiveMasterbatchCode': None,
                'numOfMaterialComponent': 0
            }

            # Parse string if needed
            parsed_data = ProgressTracker._safe_literal_eval(material_data)

            # Validate as non-empty list
            if not isinstance(parsed_data, list) or not parsed_data:
                return default_result

            # Get the first item
            first_item = parsed_data[0] if isinstance(parsed_data[0], dict) else {}

            return {
                'plasticResinCode': first_item.get('plasticResinCode'),
                'colorMasterbatchCode': first_item.get('colorMasterbatchCode'),
                'additiveMasterbatchCode': first_item.get('additiveMasterbatchCode'),
                'numOfMaterialComponent': len(parsed_data)
            }

        # Vectorized operation - faster than apply
        material_info = filtered_df['materialComponentMap'].apply(extract_material_info)
        components_df = pd.DataFrame(material_info.tolist())

        # Optimize data types
        components_df['numOfMaterialComponent'] = components_df['numOfMaterialComponent'].astype('Int64')

        # Concatenate once
        result = pd.concat([filtered_df[columns_to_keep].reset_index(drop=True),
                            components_df.reset_index(drop=True)], axis=1)

        return result

    @staticmethod
    def _process_map_fields(filtered_df: pd.DataFrame, 
                            field_name: str, 
                            first_element: str,
                            second_element: str, 
                            name_mapping: Dict[str, str],
                            columns_to_keep: List[str]) -> pd.DataFrame:

        """Process map fields (moldShotMap, machineQuantityMap, etc.)."""

        # Pre-compute column names
        first_col = name_mapping[first_element]
        second_col = name_mapping[second_element]
        count_col = f'numOf{first_element.capitalize()}'

        rows = []

        for _, row in filtered_df.iterrows():
            info_data = ProgressTracker._safe_literal_eval(row[field_name])

            # Skip if not a dict or is empty
            if not isinstance(info_data, dict) or not info_data:
                continue

            num_of_info = len(info_data)
            base_row = {col: row[col] for col in columns_to_keep}  # Create base row once

            # Create rows for each item in the dict
            for first_info, second_info in info_data.items():
                new_row = base_row.copy()
                new_row.update({
                    first_col: first_info,
                    second_col: second_info,
                    count_col: num_of_info
                })
                rows.append(new_row)

        return pd.DataFrame(rows) if rows else pd.DataFrame()