import pandas as pd
import os
from pathlib import Path
from loguru import logger
import tempfile
import shutil

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

      #update productRecords
      self._merge_monthly_reports_if_updated(folder_path = self.source_dir / 'monthlyReports_history',
                                             summary_file_path = self.output_dir / 'productRecords.xlsx',
                                             name_start = 'monthlyReports_',
                                             file_extension = '.xlsb',
                                             sheet_name='Sheet1')

      #update purchaseOrders
      self._merge_monthly_reports_if_updated(folder_path = self.source_dir / 'purchaseOrders_history',
                                             summary_file_path = self.output_dir / 'purchaseOrders.xlsx',
                                             name_start = 'purchaseOrder_',
                                             file_extension = '.xlsx',
                                             sheet_name='poList')

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

        # Read existing summary file (if any)
        if os.path.exists(summary_file_path):
            existing_df = pd.read_excel(summary_file_path)
        else:
            existing_df = pd.DataFrame()
            logger.info("First time for DataColector...")

        # Merge all files start with name_start and end with file_extension (name_start)_yyyymm.(file_extension)
        files = [f for f in os.listdir(folder_path)
                if f.startswith(name_start) and f.endswith(file_extension)]
        files_sorted = sorted(files, key=lambda x: int(x.split('_')[1][:6]))

        # Collect merged list
        merged_dfs = []
        for f in files_sorted:
            file_path = os.path.join(folder_path, f)
            try:
                logger.info(f"Reading...: {f}")
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
                logger.error("❌ Error: {}: {}", f, e)
                raise TypeError(f"Error: {f}: {e}")

        # Merge
        if not merged_dfs:
          logger.info("There is no data to merge.")
          return
        logger.info("Merging... {} dataframes", len(merged_dfs))
        merged_df = pd.concat(merged_dfs, ignore_index=True)
        logger.debug("Merged... {} dataframes into new dataframe {}: {}", 
                      len(merged_dfs), merged_df.shape, merged_df.columns)

        # Compare new merged file with existing summary file (if any)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_path = tmp.name
            merged_df.to_excel(temp_path, index=False)
        reloaded_merged_df = pd.read_excel(temp_path)
        if reloaded_merged_df.equals(existing_df):
            os.remove(temp_path)
            logger.info("{}: No changes to the summary file. Temp file deleted.", summary_file_path)
        else:
            shutil.move(temp_path, summary_file_path)
            logger.info("New summary file saved at: {}", summary_file_path)