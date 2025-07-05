import pandas as pd
import os
from pathlib import Path
from loguru import logger
import tempfile
import shutil
import hashlib
from datetime import datetime, timedelta


class DataCollector:
    def __init__(self,
                 source_dir: str = "database/dynamicDatabase",
                 default_dir: str = "agents/shared_db"
                 ):

        self.source_dir = Path(source_dir)
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "dynamicDatabase"
        os.makedirs(self.output_dir, exist_ok=True)

        self.logger = logger.bind(class_="DataCollector")

        # Update productRecords - chuyển sang parquet
        self._merge_monthly_reports_if_updated(
            folder_path=self.source_dir / 'monthlyReports_history',
            summary_file_path=self.output_dir / 'productRecords.parquet',
            name_start='monthlyReports_',
            file_extension='.xlsb',
            sheet_name='Sheet1'
        )

        # Update purchaseOrders - chuyển sang parquet
        self._merge_monthly_reports_if_updated(
            folder_path=self.source_dir / 'purchaseOrders_history',
            summary_file_path=self.output_dir / 'purchaseOrders.parquet',
            name_start='purchaseOrder_',
            file_extension='.xlsx',
            sheet_name='poList'
        )

    @staticmethod
    def _merge_monthly_reports_if_updated(folder_path,
                                          summary_file_path,
                                          name_start,
                                          file_extension,
                                          sheet_name='Sheet1'):
        
        if not os.path.exists(folder_path):
            logger.warning("❗ Folder path {} does not exist. Skipping.", folder_path)
            return

        required_fields = {
            'monthlyReports_': ['recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
                                'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
                                'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
                                'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
                                'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
                                'itemStain', 'otherNG', 'plasticResine', 'plasticResineCode',
                                'plasticResineLot', 'colorMasterbatch', 'colorMasterbatchCode',
                                'additiveMasterbatch', 'additiveMasterbatchCode'],
            "purchaseOrder_": ['poReceivedDate', 'poNo', 'poETA', 'itemCode', 'itemName',
                               'itemQuantity', 'plasticResinCode', 'plasticResin',
                               'plasticResinQuantity', 'colorMasterbatchCode', 'colorMasterbatch',
                               'colorMasterbatchQuantity', 'additiveMasterbatchCode',
                               'additiveMasterbatch', 'additiveMasterbatchQuantity']
        }

        if name_start not in required_fields.keys():
            logger.error("❌ Only support files with name start in {}", list(required_fields.keys()))
            raise ValueError(f"❌ Only support files with name start in {list(required_fields.keys())}")

        # Read existing summary file (parquet format)
        if os.path.exists(summary_file_path):
            try:
                existing_df = pd.read_parquet(summary_file_path)
                logger.debug("Loaded existing parquet file: {} rows", len(existing_df))
            except Exception as e:
                logger.warning("❗ Error reading existing parquet file {}: {}. Creating new one.", 
                              summary_file_path, e)
                existing_df = pd.DataFrame()
        else:
            existing_df = pd.DataFrame()
            logger.info("First time for DataCollector - creating new parquet file...")

        # Get source files and check for updates
        files = [f for f in os.listdir(folder_path)
                if f.startswith(name_start) and f.endswith(file_extension)]
        files_sorted = sorted(files, key=lambda x: int(x.split('_')[1][:6]))

        if not files_sorted:
            logger.info("No source files found matching pattern {}*{}", name_start, file_extension)
            return

        # Collect and merge data
        merged_dfs = []
        for f in files_sorted:
            file_path = os.path.join(folder_path, f)
            try:
                logger.info("Reading...: {}", f)
                if file_extension == '.xlsb':
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='pyxlsb')
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Check missing fields
                missing = [col for col in required_fields[name_start] if col not in df.columns]
                if missing:
                    logger.debug('Missing fields: {}', missing)
                    raise ValueError(f"❌ Missing fields: {missing}")
                
                df_filtered = df[required_fields[name_start]].copy()
                
                merged_dfs.append(df_filtered)
                
            except Exception as e:
                logger.error("❌ Failed to read file {}: {}", f, e)
                raise OSError(f"Failed to read file {f}: {e}")

        if not merged_dfs:
            logger.info("No data to merge.")
            return

        logger.info("Merging {} dataframes...", len(merged_dfs))
        merged_df = pd.concat(merged_dfs, ignore_index=True)
        
        # Remove duplicates if any (based on all columns)
        initial_rows = len(merged_df)
        merged_df = merged_df.drop_duplicates()
        if len(merged_df) < initial_rows:
            logger.info("Removed {} duplicate rows", initial_rows - len(merged_df))

        merged_df = DataCollector._data_prosesssing(merged_df, summary_file_path)

        logger.debug("Merged {} dataframes into new dataframe shape: {}", 
                     len(merged_dfs), merged_df.shape)

        # Compare with existing data using hash for efficiency
        if not existing_df.empty:
            if DataCollector._dataframes_equal_fast(merged_df, existing_df):
                logger.info("No changes detected in data. Skipping write.")
                return

        # Save as parquet with minimal processing
        try:
            # Convert all object columns to string to avoid pyarrow inference issues
            for col in merged_df.columns:
                if merged_df[col].dtype == 'object':
                    merged_df[col] = merged_df[col].astype(str)
            
            # Write to temporary file first for atomic operation
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                temp_path = tmp.name
                merged_df.to_parquet(
                    temp_path,
                    engine='pyarrow',
                    compression='snappy',
                    index=False
                )
            
            # Move to final location
            shutil.move(temp_path, summary_file_path)
            
            logger.info("✅ New parquet file saved: {} ({} rows, {:.2f}MB)", 
                       summary_file_path, len(merged_df), 
                       os.path.getsize(summary_file_path) / 1024 / 1024)
                       
        except Exception as e:
            logger.error("❌ Error saving parquet file: {}", e)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    @staticmethod
    def _dataframes_equal_fast(df1, df2):
        """Fast comparison of dataframes using hash"""
        if df1.shape != df2.shape:
            return False
            
        # Quick hash comparison
        try:
            hash1 = hashlib.md5(pd.util.hash_pandas_object(df1, index=False).values).hexdigest()
            hash2 = hashlib.md5(pd.util.hash_pandas_object(df2, index=False).values).hexdigest()
            return hash1 == hash2
        except:
            # Fallback to regular comparison if hashing fails
            return df1.equals(df2)

    @staticmethod
    def _data_prosesssing(df, summary_file_path):

      def check_null_str(df):
        suspect_values = ['nan', "null", "none", "", "n/a", "na"]
        nan_values = []
        for col in df.columns:
            for uniq in df[col].unique(): 
              if str(uniq).lower() in suspect_values:
                nan_values.append(uniq)
        return list(set(nan_values))

      def safe_convert(x):
        if pd.isna(x):
            return x
        if isinstance(x, (int, float)) and not pd.isna(x):
            return str(int(x))
        return str(x)

      spec_cases = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

      schema_data = {
          'productRecords': {
              'dtypes': {'workingShift': "string", 
                        'machineNo': "string", 'machineCode': "string", 
                        'itemCode': "string", 'itemName': "string", 
                        'colorChanged': "string", 'moldChanged': "string", 'machineChanged': "string", 
                        'poNote': "string", 'moldNo': "string", 'moldShot': "Int64", 'moldCavity': "Int64", 
                        'itemTotalQuantity': "Int64", 'itemGoodQuantity': "Int64", 
                        'plasticResinCode': 'string', 'colorMasterbatchCode': 'string', 'additiveMasterbatchCode': 'string',
                        'plasticResin': 'string', 'colorMasterbatch': 'string', "additiveMasterbatch": 'string', 'plasticResinLot': 'string',
                        'itemBlackSpot': "Int64", 'itemOilDeposit': "Int64", 'itemScratch': "Int64", 'itemCrack': "Int64", 'itemSinkMark': "Int64", 
                        'itemShort': "Int64", 'itemBurst': "Int64", 'itemBend': "Int64", 'itemStain': "Int64", 'otherNG': "Int64",
                         }
              },
          'purchaseOrders': {
              'dtypes': {'poNo': "string", 'itemCode': "string", 'itemName': "string", 
                         'plasticResin': 'string', 'colorMasterbatch': 'string', "additiveMasterbatch": 'string',
                         'plasticResinCode': 'string', 'colorMasterbatchCode': 'string', 'additiveMasterbatchCode': 'string',
                         'plasticResinQuantity': "Float64", 
                         'colorMasterbatchQuantity': "Float64", 
                         'additiveMasterbatchQuantity': "Float64"},
              }
      }

      db_name = Path(summary_file_path).name.replace('.parquet', '')
      if db_name == "productRecords":
        df.rename(columns={
                            "plasticResine": "plasticResin",
                            "plasticResineCode": "plasticResinCode",
                            'plasticResineLot': 'plasticResinLot'
                        }, inplace=True)
        df['recordDate'] = df['recordDate'].apply(lambda x: timedelta(days=x) + datetime(1899,12,30))
      if db_name == "purchaseOrders":
        df[['poReceivedDate', 'poETA']] = df[['poReceivedDate', 
                                              'poETA']].apply(lambda col: pd.to_datetime(col, errors='coerce'))

      #Handle with specical cases
      for c in spec_cases:
        df[c] = df[c].map(safe_convert)

      df = df.astype(schema_data[db_name]['dtypes'])
      if db_name == "productRecords": #working shifts with 1, 2, 3 and HC or hc
          df['workingShift'] = df['workingShift'].str.upper()
    
      # fill null with same format pd.NA
      df.replace(check_null_str(df), pd.NA, inplace=True)
      df.fillna(pd.NA, inplace=True)

      return df