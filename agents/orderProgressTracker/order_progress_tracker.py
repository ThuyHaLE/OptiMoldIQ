from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
from pandas.api.types import is_object_dtype
from datetime import datetime, timedelta
from typing import Optional
import os
import re

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['statisticDB']['moldSpecificationSummary']['dtypes'].keys()),
})

class OrderProgressTracker:
    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 folder_path: str = 'agents/shared_db/ValidationOrchestrator', 
                 target_name: str = "change_log.txt",
                 default_dir: str = "agents/shared_db"):
        
        self.logger = logger.bind(class_="OrderProgressTracker")

        self.shift_start_map = {"1": "06:00",
                                "2": "14:00",
                                "3": "22:00",
                                "HC": "08:00"}

        self.pro_status_dtypes = {'poReceivedDate': "datetime64[ns]", 'poNo': "string", 'itemCode': "string", 'itemName': "string", 'itemType': "string", 
                                  'poETA': "datetime64[ns]", 'itemQuantity': "Int64", 'itemRemain': "Int64", 
                                  'startedDate': "datetime64[ns]", 'actualFinishedDate': "datetime64[ns]", 
                                  'proStatus': "string", 'etaStatus': 'string',
                                  'machineHist': 'object', 'moldList': 'object', 'moldHist': 'object', 'moldCavity': 'object', 
                                  'plasticResinCode': 'object', 'colorMasterbatchCode': 'object', 'additiveMasterbatchCode': 'object',
                                  'totalMoldShot': "Int64", 'totalDay': "Int64", 'totalShift': "Int64",
                                  'moldShotMap': 'object', 'machineQuantityMap': 'object', 
                                  'dayQuantityMap': 'object', 'shiftQuantityMap': 'object', 'materialComponentMap': 'object'}

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
        
        # Extract productRecords DataFrame
        productRecords_path = self.path_annotation.get('productRecords')
        if not productRecords_path or not os.path.exists(productRecords_path):
            self.logger.error("❌ Path to 'productRecords' not found or does not exist.")
            raise FileNotFoundError("Path to 'productRecords' not found or does not exist.")
        self.productRecords_df = pd.read_parquet(productRecords_path)
        logger.debug("productRecords: {} - {}", self.productRecords_df.shape, self.productRecords_df.columns)

        # Extract purchaseOrders DataFrame
        purchaseOrders_path = self.path_annotation.get('purchaseOrders')
        if not purchaseOrders_path or not os.path.exists(purchaseOrders_path):
            self.logger.error("❌ Path to 'purchaseOrders' not found or does not exist.")
            raise FileNotFoundError("Path to 'purchaseOrders' not found or does not exist.")
        self.purchaseOrders_df = pd.read_parquet(purchaseOrders_path)
        logger.debug("purchaseOrders: {} - {}", self.purchaseOrders_df.shape, self.purchaseOrders_df.columns)

        # Extract moldSpecificationSummary DataFrame
        moldSpecificationSummary_path = self.path_annotation.get('moldSpecificationSummary')
        if not moldSpecificationSummary_path or not os.path.exists(moldSpecificationSummary_path):
            self.logger.error("❌ Path to 'moldSpecificationSummary' not found or does not exist.")
            raise FileNotFoundError("Path to 'moldSpecificationSummary' not found or does not exist.")
        self.moldSpecificationSummary_df = pd.read_parquet(moldSpecificationSummary_path)
        logger.debug("moldSpecificationSummary: {} - {}", self.moldSpecificationSummary_df.shape, self.moldSpecificationSummary_df.columns)

        self.folder_path = folder_path
        self.target_name = target_name

        self.filename_prefix= "auto_status"

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "OrderProgressTracker"


    def pro_status(self, **kwargs) -> None:
        ordersInfo_df = pd.merge(self.purchaseOrders_df[['poNo', 'poReceivedDate', 'poETA', 'itemCode',	'itemName', 'itemQuantity']], 
                                 self.moldSpecificationSummary_df[['itemCode', 'itemType', 'moldList']], 
                                 on='itemCode', how='left')
        
        agg_df, producing_po_list, notWorking_productRecords_df = OrderProgressTracker._extract_product_records(self.productRecords_df, self.shift_start_map)

        pro_status_df = OrderProgressTracker._pro_status_processing(pd.merge(ordersInfo_df,
                                                      agg_df, 
                                                      on='poNo', how='left'),
                                              self.pro_status_fields, 
                                              producing_po_list, 
                                              self.pro_status_dtypes)
        
        warning_merge_dict, total_warnings = OrderProgressTracker._get_change(self.folder_path, self.target_name)
        updated_pro_status_df = OrderProgressTracker._add_warning_notes_column(pro_status_df, warning_merge_dict)

        self.data = {
                    "productionStatus": updated_pro_status_df,
                    "notWorkingStatus": notWorking_productRecords_df, 
                    }
        if total_warnings:
            self.data.update(total_warnings)
        
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

    @staticmethod
    # Helper function to calculate the shift's start datetime based on the date and shift code
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
            date = pd.to_datetime(row[date_field_name])
            shift = str(row[shift_field_name])
            start_time_str = shift_start_map.get(shift)

            if not start_time_str:
                logger.warning(f"Invalid shift code: {shift}")
                return pd.NaT

            hour, minute = map(int, start_time_str.split(":"))
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
        
        # Aggregate mold shot data per mold per PO
        maps['mold_map'] = (
            df.groupby(['poNote', 'moldNo'])['moldShot']
            .sum()
            .reset_index()
            .groupby('poNote')[['moldNo', 'moldShot']]
            .apply(lambda x: {k: int(v) for k, v in zip(x['moldNo'], x['moldShot'])})
            .to_dict()
        )

        # Aggregate good quantity per machine per PO
        maps['machine_map'] = (
            df.groupby(['poNote', 'machineHist'])['itemGoodQuantity']
            .sum()
            .reset_index()
            .groupby('poNote')[['machineHist', 'itemGoodQuantity']]
            .apply(lambda x: {k: int(v) for k, v in zip(x['machineHist'], x['itemGoodQuantity'])})
            .to_dict()
        )

        # Aggregate good quantity per date per PO
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

        # Aggregate good quantity per date+shift per PO
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
            dict: Dictionary mapping poNote to material codes
        """
        def extract_code_set(group):
            result = {}
            material_columns = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']
            
            for col in material_columns:
                if col in group.columns:
                    values = group[col].dropna().unique().tolist()
                    if values:
                        result[col] = values
            return result
        
        return (
            df.groupby('poNote')
            .apply(extract_code_set, include_groups=False)
            .to_dict()
        )

    @staticmethod
    # Main function to extract and aggregate product record information
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

      notWorking_productRecords_df = productRecords_df[not_working_mask].copy()
      notWorking_productRecords_df['recordDate'] = notWorking_productRecords_df['recordDate'].dt.strftime('%Y-%m-%d')

      haveWorking_productRecords_df = productRecords_df[~not_working_mask].copy()

      logger.debug("Not working => {}: {}", notWorking_productRecords_df.shape, notWorking_productRecords_df.columns.to_list())
      logger.debug("Have working => {}: {}", haveWorking_productRecords_df.shape, haveWorking_productRecords_df.columns.to_list())

      if haveWorking_productRecords_df.empty:
        logger.error("No working production records found")
        raise ValueError("No working production records found.")

      # Determine the latest production time based on working shift start times
      time_to_shift = {datetime.strptime(v, "%H:%M").time(): k for k, v in shift_start_map.items()}

      shift_starts = haveWorking_productRecords_df.apply(lambda row: OrderProgressTracker._get_shift_start(row, shift_start_map), axis=1)
      latest_shift_start = shift_starts.max()

      if pd.isna(latest_shift_start):
        logger.error("Could not determine latest shift start")
        raise ValueError("Could not determine latest shift start.")
      
      else:
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

      missing_actual_finish = molded_mask & pro_status_df['actualFinishedDate'].isna()
      if missing_actual_finish.any():
          logger.warning("Some completed orders are missing actualFinishedDate:\n{}", 
                        pro_status_df.loc[missing_actual_finish, ['poNo', 'endDate']])

      # Mark currently producing orders
      molding_mask = (pro_status_df['poNo'].isin(producing_po_list)) & (pro_status_df['itemRemain'] != 0)
      pro_status_df.loc[molding_mask, 'proStatus'] = 'MOLDING'

      # Mark late and on time orders
      # Default: PENDING
      pro_status_df['etaStatus'] = 'PENDING'

      # ONTIME
      on_time_mask = (
          pro_status_df['actualFinishedDate'].notnull() &
          (pro_status_df['itemRemain'] == 0) &
          (pro_status_df['actualFinishedDate'] <= pro_status_df['poETA'])
      )
      pro_status_df.loc[on_time_mask, 'etaStatus'] = 'ONTIME'

      # LATE
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
      result = {}
      xls = pd.ExcelFile(excel_file)

      for f_name in xls.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=f_name)
        result[f_name] = df

      return result
    
    @staticmethod
    def _aggregate_po_mismatches(df):

        grouped = df.groupby(['poNo', 'mismatchType']).size().reset_index(name='count')
        
        result = {}
        for _, row in grouped.iterrows():
            po_no = row['poNo']
            mismatch_type = row['mismatchType']
            count = row['count']
            
            if po_no not in result:
                result[po_no] = {}
            result[po_no][mismatch_type] = count
        
        for po_no, mismatches in result.items():
            total_issues = sum(mismatches.values())
            for mismatch_type, count in mismatches.items():
                logger.info("{} - Mismatch: {} - Ratio: {}/{}", po_no, mismatch_type, count, total_issues)
                
        return result

    @staticmethod
    def _extract_latest_saved_file(log_text: str) -> Optional[str]:

        if not log_text.strip():
            return None
        
        # Pattern to match timestamp and content blocks
        pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\](.*?)(?=\n\[|$)'
        matches = re.findall(pattern, log_text, flags=re.DOTALL)

        if not matches:
            return None

        log_blocks = {}
        for ts_str, content in matches:
            log_blocks[ts_str] = content.strip()

        # Find the latest timestamp
        latest_ts_str = max(log_blocks, key=lambda ts: datetime.strptime(ts, '%Y-%m-%d %H:%M:%S'))
        latest_block = log_blocks[latest_ts_str]

        # Look for saved file pattern
        saved_file_match = re.search(r'⤷ Saved new file: (.+)', latest_block)
        if saved_file_match:
            return saved_file_match.group(1).strip()
        
        return None

    @staticmethod
    def _read_change_log(folder_path, target_name):

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

        df = df.copy()

        if warning_dict:
            def get_warning_notes(po):
                if po in warning_dict:
                    return "; ".join(warning_dict[po].keys())
                else:
                    return ""

            df["warningNotes"] = df["poNo"].apply(get_warning_notes)

        return df