from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
from pandas.api.types import is_object_dtype
from datetime import datetime, timedelta
import os
import ast
import re
from typing import Dict, List, Any, Optional

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
})

class OrderProgressTracker:

    """
    Class to track order production progress

    Main functions:
    - Track production status of orders
    - Calculate completion progress
    - Analyze production data by shift, machine, mold
    - Export Excel report
    """

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 folder_path: str = 'agents/shared_db/ValidationOrchestrator',
                 target_name: str = "change_log.txt",
                 default_dir: str = "agents/shared_db"):

        """
        Initialize OrderProgressTracker

        Args:
        source_path: Path to the directory containing the source data
        annotation_name: Name of the annotation file containing the paths of the data files
        databaseSchemas_path: Path to the database schema file
        folder_path: Path to the directory containing the change log
        target_name: Name of the change log file
        default_dir: Default directory to save the output
        """

        self.logger = logger.bind(class_="OrderProgressTracker")

        # Mapping shift start times
        self.shift_start_map = {"1": "06:00", # Shift 1: 6:00 AM
                                "2": "14:00", # Shift 2: 2:00 PM
                                "3": "22:00", # Shift 3: 10:00 PM
                                "HC": "08:00"} # Administrative shift: 8:00 AM

        # Define data types for columns in the production status table
        self.pro_status_dtypes = {
            'poReceivedDate': "datetime64[ns]",        # Date the PO was received
            'poNo': "string",                          # Purchase Order number
            'itemCode': "string",                      # Product code
            'itemName': "string",                      # Product name
            'itemType': "string",                      # Product type
            'poETA': "datetime64[ns]",                 # Estimated delivery date
            'itemQuantity': "Int64",                   # Ordered quantity
            'itemRemain': "Int64",                     # Remaining quantity to be produced
            'startedDate': "datetime64[ns]",           # Production start date
            'actualFinishedDate': "datetime64[ns]",    # Actual production completion date
            'proStatus': "string",                     # Production status
            'etaStatus': 'string',                     # Status compared to ETA
            'machineHist': 'object',                   # Production machine history
            'moldList': 'object',                      # List of molds used
            'moldHist': 'object',                      # Mold usage history
            'moldCavity': 'object',                    # Mold cavity count
            'plasticResinCode': 'object',              # Raw plastic resin code
            'colorMasterbatchCode': 'object',          # Color masterbatch code
            'additiveMasterbatchCode': 'object',       # Additive masterbatch code
            'totalMoldShot': "Int64",                  # Total mold shots
            'totalDay': "Int64",                       # Total production days
            'totalShift': "Int64",                     # Total production shifts
            'moldShotMap': 'object',                   # Mapping of mold shots by mold
            'machineQuantityMap': 'object',            # Quantity mapping by machine
            'dayQuantityMap': 'object',                # Quantity mapping by day
            'shiftQuantityMap': 'object',              # Quantity mapping by shift
            'materialComponentMap': 'object'           # Mapping of material components
        }

        # List of fields to output the final result
        self.pro_status_fields = ['poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA', 'itemQuantity',
                                  'itemRemain', 'startedDate', 'actualFinishedDate','proStatus', 'etaStatus',
                                  'machineHist', 'itemType', 'moldList', 'moldHist', 'moldCavity', 'totalMoldShot' , 'totalDay', 'totalShift',
                                  'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
                                  'moldShotMap', 'machineQuantityMap', 'dayQuantityMap', 'shiftQuantityMap','materialComponentMap']

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path,
                                                    annotation_name)

        # ===== Load productRecords DataFrame =====
        productRecords_path = self.path_annotation.get('productRecords')
        if not productRecords_path or not os.path.exists(productRecords_path):
            self.logger.error("❌ Path to 'productRecords' not found or does not exist.")
            raise FileNotFoundError("Path to 'productRecords' not found or does not exist.")
        self.productRecords_df = pd.read_parquet(productRecords_path)
        logger.debug("productRecords: {} - {}", self.productRecords_df.shape, self.productRecords_df.columns)

        # ===== Load purchaseOrders DataFrame =====
        purchaseOrders_path = self.path_annotation.get('purchaseOrders')
        if not purchaseOrders_path or not os.path.exists(purchaseOrders_path):
            self.logger.error("❌ Path to 'purchaseOrders' not found or does not exist.")
            raise FileNotFoundError("Path to 'purchaseOrders' not found or does not exist.")
        self.purchaseOrders_df = pd.read_parquet(purchaseOrders_path)
        logger.debug("purchaseOrders: {} - {}", self.purchaseOrders_df.shape, self.purchaseOrders_df.columns)

        # ===== Load moldSpecificationSummary DataFrame =====
        moldSpecificationSummary_path = self.path_annotation.get('moldSpecificationSummary')
        if not moldSpecificationSummary_path or not os.path.exists(moldSpecificationSummary_path):
            self.logger.error("❌ Path to 'moldSpecificationSummary' not found or does not exist.")
            raise FileNotFoundError("Path to 'moldSpecificationSummary' not found or does not exist.")
        self.moldSpecificationSummary_df = pd.read_parquet(moldSpecificationSummary_path)
        logger.debug("moldSpecificationSummary: {} - {}", self.moldSpecificationSummary_df.shape, self.moldSpecificationSummary_df.columns)

        # Set output file paths and names
        self.folder_path = folder_path
        self.target_name = target_name
        self.filename_prefix= "auto_status"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "OrderProgressTracker"


    def pro_status(self, **kwargs) -> None:

        """
        Main function to process and generate production status report

        Process:
        1. Merge order data with mold information
        2. Extract and summarize production data
        3. Process production status
        4. Add warning information
        5. Export Excel file
        """

        # Step 1: Merge order data with mold information
        ordersInfo_df = pd.merge(self.purchaseOrders_df[['poNo', 'poReceivedDate', 'poETA', 'itemCode',	'itemName', 'itemQuantity']],
                                 self.moldSpecificationSummary_df[['itemCode', 'itemType', 'moldList']],
                                 on='itemCode', how='left')

        # Step 2: Extract and summarize production data
        agg_df, producing_po_list, notWorking_productRecords_df = OrderProgressTracker._extract_product_records(self.productRecords_df, self.shift_start_map)

        # Step 3: Process production status
        pro_status_df = OrderProgressTracker._pro_status_processing(pd.merge(ordersInfo_df,
                                                                             agg_df,
                                                                             on='poNo', how='left'),
                                              self.pro_status_fields,
                                              producing_po_list,
                                              self.pro_status_dtypes)
        pro_status_df = OrderProgressTracker._mark_paused_pending_pos(self.productRecords_df,
                                                                      pro_status_df,
                                                                      self.shift_start_map)

        # Get the latest machine information for each po on working shift timestamp
        lastest_info_df = OrderProgressTracker._get_latest_po_info(self.productRecords_df,
                                                                    self.shift_start_map,
                                                                    keys=['machineNo', 'moldNo'])
        updated_lastest_info_df = pro_status_df.merge(lastest_info_df, how='left', on='poNo')

        # Step 4: Get and add warning information from validationOrchestrator's output
        warning_merge_dict, total_warnings = OrderProgressTracker._get_change(self.folder_path, self.target_name)
        updated_pro_status_df = OrderProgressTracker._add_warning_notes_column(updated_lastest_info_df, warning_merge_dict)

        # Step 5: Prepare output data
        self.data = {
                    "productionStatus": updated_pro_status_df,
                    'materialComponentMap': OrderProgressTracker._pro_status_fattening(updated_pro_status_df,
                                                                                       field_name = 'materialComponentMap'),
                    'moldShotMap': OrderProgressTracker._pro_status_fattening(updated_pro_status_df,
                                                                              field_name = 'moldShotMap'),
                    'machineQuantityMap': OrderProgressTracker._pro_status_fattening(updated_pro_status_df,
                                                                                     field_name = 'machineQuantityMap'),
                    'dayQuantityMap': OrderProgressTracker._pro_status_fattening(updated_pro_status_df,
                                                                                 field_name = 'dayQuantityMap'),
                    "notWorkingStatus": notWorking_productRecords_df,
                    }

        # Add warning information into output data if any
        if total_warnings:
            self.data.update(total_warnings)

        # Step 6: Export Excel file
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    @staticmethod
    def _get_shift_start(row, shift_start_map,
                         date_field_name='recordDate',
                         shift_field_name='workingShift'):

        """
        Calculate the shift's start datetime based on the date and shift code.

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
            start_datetime = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute)

            return pd.Timestamp(start_datetime)

        except Exception as e:
            logger.error(f"Error calculating shift start for row: {e}")
            return pd.NaT

    @staticmethod
    def _create_aggregation_maps(df):

        """
        Create various aggregation maps for production data.

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

    @staticmethod
    def _extract_material_codes(df):
        """
        Extract material component codes and drop NaNs.

        Args:
            df: DataFrame with production records

        Returns:
            dict: Dictionary mapping poNote to list of material component combinations
        """

        def extract_material_combinations(group):
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
    def _extract_product_records(productRecords_df,
                                 shift_start_map):

        """
        Main function to extract and aggregate product record information.

        Args:
            productRecords_df: DataFrame containing production records
            shift_start_map: Dictionary mapping shift codes to start times

        Returns:
            tuple: (aggregated_df, producing_po_list, not_working_records_df)
        """

        # Input validation
        if productRecords_df.empty:
            logger.error("Empty productRecords_df provided")
            raise ValueError("Empty productRecords_df provided.")

        # Create derived columns
        productRecords_df = productRecords_df.copy()

        # Combine date and shift into a string identifier
        productRecords_df['dateShiftCombined'] = productRecords_df['recordDate'].dt.strftime('%Y-%m-%d') + '_shift_' + productRecords_df['workingShift']

        # Create a unique machine history identifier
        productRecords_df['machineHist'] = productRecords_df['machineNo'] + '_' + productRecords_df['machineCode']
        logger.debug("Total records => {}: {}", productRecords_df.shape, productRecords_df.columns.to_list())

        # Split records into those with no production and those with actual production
        not_working_mask = (productRecords_df['itemTotalQuantity'].isna() | (productRecords_df['itemTotalQuantity'] == 0))

        # DataFrame for records without production
        notWorking_productRecords_df = productRecords_df[not_working_mask].copy()
        notWorking_productRecords_df['recordDate'] = notWorking_productRecords_df['recordDate'].dt.strftime('%Y-%m-%d')

        # DataFrame for records with production
        haveWorking_productRecords_df = productRecords_df[~not_working_mask].copy()

        logger.debug("Not working => {}: {}", notWorking_productRecords_df.shape, notWorking_productRecords_df.columns.to_list())
        logger.debug("Have working => {}: {}", haveWorking_productRecords_df.shape, haveWorking_productRecords_df.columns.to_list())

        if haveWorking_productRecords_df.empty:
            logger.error("No working production records found")
            raise ValueError("No working production records found.")

        # Determine the latest production time based on working shift start times
        time_to_shift = {datetime.strptime(v, "%H:%M").time(): k for k, v in shift_start_map.items()}

        # Calculate shift start time for each record
        shift_starts = haveWorking_productRecords_df.apply(lambda row: OrderProgressTracker._get_shift_start(row, shift_start_map), axis=1)
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
        resin_code_map = OrderProgressTracker._extract_material_codes(haveWorking_productRecords_df)

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
        maps = OrderProgressTracker._create_aggregation_maps(haveWorking_productRecords_df)

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
    def _pro_status_processing(pro_status_df, pro_status_fields,
                               producing_po_list, pro_status_dtypes):

        """
        Process production status and handle data type conversions.

        Args:
            pro_status_df: DataFrame with production status data
            pro_status_fields: List of fields to include in output
            producing_po_list: List of POs currently in production
            pro_status_dtypes: Dictionary of data types for columns

        Returns:
            pd.DataFrame: Processed dataframe with status information
        """

        if pro_status_df.empty:
            logger.error("Empty pro_status_df provided")
            raise ValueError("Empty pro_status_df provided.")

        pro_status_df = pro_status_df.copy()

        # Calculate remaining items
        pro_status_df['itemRemain'] = pro_status_df['itemQuantity'] - pro_status_df['moldedQuantity'].fillna(0)

        # Determine production status
        pro_status_df['proStatus'] = 'PENDING'  # Default status

        # Mark completed orders
        molded_mask = pro_status_df['itemRemain'] == 0
        pro_status_df.loc[molded_mask, 'proStatus'] = 'MOLDED'
        pro_status_df.loc[molded_mask, 'actualFinishedDate'] = pro_status_df.loc[molded_mask, 'endDate']

        # Check and alert on completed orders with missing end date
        missing_actual_finish = molded_mask & pro_status_df['actualFinishedDate'].isna()
        if missing_actual_finish.any():
            logger.warning("Some completed orders are missing actualFinishedDate:\n{}",
                            pro_status_df.loc[missing_actual_finish, ['poNo', 'endDate']])

        # Mark currently producing orders
        molding_mask = (pro_status_df['poNo'].isin(producing_po_list)) & (pro_status_df['itemRemain'] != 0)
        pro_status_df.loc[molding_mask, 'proStatus'] = 'MOLDING'

        # Determine status compared to ETA (Expected Time of Arrival)
        pro_status_df['etaStatus'] = 'PENDING' # Default: PENDING

        # ONTIME: Complete on time or ahead of schedule
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
            logger.error("Error applying data types: {}", e)
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

        # Debug logging for object columns
        for col in pro_status_df.columns:
            if is_object_dtype(pro_status_df[col]):
                series = pro_status_df[col]
                nas = series.isna().sum()
                nulls = series.isnull().sum()
                # Use .apply to deal with (pd.NA == pd.NA) return pd.NA
                pdna = series.apply(lambda x: x is pd.NA).sum()
                logger.debug(f"{col}: isna = {nas}, isnull = {nulls}, pd.NA (by identity) = {pdna}")

        assert set(pro_status_fields).issubset(pro_status_df.columns), \
            f"Missing expected fields in final dataframe: {set(pro_status_fields) - set(pro_status_df.columns)}"

        return pro_status_df[pro_status_fields]

    def _data_collecting(excel_file):

        """
        Read all sheets from the Excel file and store them in a dictionary using sheet names as keys.
        """

        result = {}
        xls = pd.ExcelFile(excel_file)

        for f_name in xls.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=f_name)
            result[f_name] = df

        return result

    @staticmethod
    def _aggregate_po_mismatches(df):

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
    def _extract_latest_saved_file(log_text: str) -> Optional[str]:

        """
        Extract the most recently saved file name from log text.
        Assumes log format includes: "[timestamp] ⤷ Saved new file: ..."
        """

        if not log_text.strip():
            return None

        # Match all log blocks by timestamp
        pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\](.*?)(?=\n\[|$)'
        matches = re.findall(pattern, log_text, flags=re.DOTALL)

        if not matches:
            return None

        log_blocks = {}
        for ts_str, content in matches:
            log_blocks[ts_str] = content.strip()

        # Get the latest block based on timestamp
        latest_ts_str = max(log_blocks, key=lambda ts: datetime.strptime(ts, '%Y-%m-%d %H:%M:%S'))
        latest_block = log_blocks[latest_ts_str]

        # Extract saved file name from the latest block
        saved_file_match = re.search(r'⤷ Saved new file: (.+)', latest_block)
        if saved_file_match:
            return saved_file_match.group(1).strip()

        return None

    @staticmethod
    def _read_change_log(folder_path, target_name):

        """
        Read a log file in the given folder and extract the path to the latest saved Excel file.
        """

        # Check if folder exists
        if not os.path.isdir(folder_path):
            logger.warning("Directory does not exist: {}", folder_path)
            return None

        file_path = os.path.join(folder_path, target_name)

        # Check if file exists
        if not os.path.isfile(file_path):
            logger.warning("Could not find '{}' in folder {}", target_name, folder_path)
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                log_text = f.read()
                newest_file_name = OrderProgressTracker._extract_latest_saved_file(log_text)

                if newest_file_name:
                    return os.path.join(folder_path, newest_file_name)
                else:
                    logger.warning("No file information found saved in '{}'", target_name)
                    return None

        except Exception as e:
            logger.error("Error reading file '{}': {}", target_name, str(e))
            raise

    @staticmethod
    def _get_change(folder_path, target_name):

        """
        Process the log file and summarize mismatch warnings if available.

        Returns:
            - warning_merge_dict: dict of grouped mismatch warnings by PO
            - total_warnings: all sheets collected from the Excel file
        """

        try:
            excel_file = OrderProgressTracker._read_change_log(folder_path, target_name)

            if excel_file is None:
                logger.info("No change log file found, returning empty warnings")
                return {}, {}

            total_warnings = OrderProgressTracker._data_collecting(excel_file)

            if not total_warnings:
                logger.info("No warnings found in change log")
                return {}, {}

            if 'po_mismatch_warnings' in total_warnings:
                po_mismatch_df = total_warnings['po_mismatch_warnings']

                # Validate the DataFrame before processing
                if po_mismatch_df.empty:
                    logger.warning("po_mismatch_warnings DataFrame is empty")
                    return {}, total_warnings

                # Check required columns exist
                required_columns = ['poNo', 'mismatchType']
                missing_cols = set(required_columns) - set(po_mismatch_df.columns)
                if missing_cols:
                    logger.error("Missing required columns in po_mismatch_warnings: {}", missing_cols)
                    return {}, total_warnings

                # Aggregate mismatch counts by PO
                warning_merge_dict = OrderProgressTracker._aggregate_po_mismatches(po_mismatch_df)
                return warning_merge_dict, total_warnings
            else:
                logger.info("No po_mismatch_warnings found in change log")
                return {}, total_warnings

        except Exception as e:
            logger.error("Error processing change log: {}", str(e))
            return {}, {}

    @staticmethod
    def _add_warning_notes_column(df, warning_dict):

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

        return df

    @staticmethod
    def _get_latest_po_info(df, shift_start_map, keys=['machineNo', 'moldNo']):

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

    @staticmethod
    def _mark_paused_pending_pos(df, proStatus_df, shift_start_map):
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
    def _pro_status_fattening(df: pd.DataFrame,
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
        field_parts = OrderProgressTracker._split_field_name(field_name)
        if len(field_parts) != 2:
            raise ValueError(f"Invalid field name format: {field_name}")

        first_element, second_element = field_parts

        # Special case: materialComponentMap
        if field_name == 'materialComponentMap':
            return OrderProgressTracker._process_material_components(filtered_df, COLUMNS_TO_KEEP)

        # Process other map fields
        return OrderProgressTracker._process_map_fields(filtered_df, field_name, first_element, second_element,
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
    def _process_map_fields(filtered_df: pd.DataFrame, field_name: str, first_element: str,
                          second_element: str, name_mapping: Dict[str, str],
                          columns_to_keep: List[str]) -> pd.DataFrame:

        """Process map fields (moldShotMap, machineQuantityMap, etc.)."""

        # Pre-compute column names
        first_col = name_mapping[first_element]
        second_col = name_mapping[second_element]
        count_col = f'numOf{first_element.capitalize()}'

        rows = []

        for _, row in filtered_df.iterrows():
            info_data = OrderProgressTracker._safe_literal_eval(row[field_name])

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
            parsed_data = OrderProgressTracker._safe_literal_eval(material_data)

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