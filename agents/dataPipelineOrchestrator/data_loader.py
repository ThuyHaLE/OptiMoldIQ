import pandas as pd
from loguru import logger
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
import os

class DataLoaderAgent:
    def __init__(self, 
                 databaseSchemas_path: str = "database/databaseSchemas.json",
                 annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
                 default_dir: str = "agents/shared_db"
                 ):
      
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DataLoaderAgent"
        self.logger = logger.bind(class_="DataLoaderAgent")

        #Load database schema
        with open(databaseSchemas_path, "r", encoding="utf-8") as f:
          self.databaseSchemas_data = json.load(f)

        #Load existing path annotations
        if os.path.exists(annotation_path):
            with open(annotation_path, "r", encoding="utf-8") as f:
              self.path_annotation = json.load(f)
            logger.debug("Loaded existing annotation file: {}", self.path_annotation)
        else:
            self.path_annotation = {}
            logger.info("First time for initial - creating new annotation file...")

        #Process to load and check if there is any change in files
        self.have_changed_files = {}
        for db_type in self.databaseSchemas_data.keys():
          for db_name in self.databaseSchemas_data[db_type].keys():
            db_existing_path = self.path_annotation.get(db_name, "")
            if db_type == 'dynamicDB':
              db_current_path = self.databaseSchemas_data[db_type][db_name]['path']
              current_df = self._load_existing_df(db_current_path)
              existing_df = self._load_existing_df(db_existing_path)
            else:
              current_df = self._process_data(db_name, db_type, self.databaseSchemas_data)
              existing_df = self._load_existing_df(db_existing_path)
            if not self._dataframes_equal_fast(current_df, existing_df):
              self.have_changed_files[db_name] = current_df
        
        if not self.have_changed_files:
          logger.info("No changes detected in data. Skipping write.")
        else:
          logger.debug("Detect changes: {}", [(k, v.columns) for k, v in self.have_changed_files.items()])
          #Only save if there is any change in files
          self.save_output_with_versioning(self.have_changed_files, 
                                          self.path_annotation,
                                          self.output_dir)

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
    def _load_existing_df(file_path):
      # Read existing file (parquet format)
      try:
          existing_df = pd.read_parquet(file_path)
      except Exception as e:
          logger.warning("Failed to read existing parquet {}: {}", file_path, e)
          existing_df = pd.DataFrame()
      return existing_df

    @staticmethod
    def save_output_with_versioning(data: dict[str, pd.DataFrame],
                                    path_annotation: dict[str, str],
                                    output_dir: str | Path,
                                    file_format: str = 'parquet'
                                    ):  
        if not isinstance(data, dict):
            logger.error("❌ Expected data to be a dict[str, pd.DataFrame] but got: {}", type(data))
            raise TypeError(f"Expected data to be a dict[str, pd.DataFrame] but got: {type(data)}")

        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
                logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
                raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")

        output_dir = Path(output_dir)
        log_path = output_dir / "change_log.txt"
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)
        annotations_path = newest_dir / "path_annotations.json"

        # Move old files to historical_db
        for f in newest_dir.iterdir():
            if f.is_file() and f.name.split('_', 2)[-1].split('.')[0] in data.keys():
                try:
                    dest = historical_dir / f.name
                    shutil.move(str(f), dest)
                    log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                    logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                except Exception as e:
                    logger.error("Failed to move file {}: {}", f.name, e)
                    raise OSError(f"Failed to move file {f.name}: {e}")

        try:
            for db_name, df in data.items():
                timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
                new_filename = f"{timestamp_file}_{db_name}.{file_format}"
                new_path = newest_dir / new_filename
                df.to_parquet(new_path,
                              engine='pyarrow',
                              compression='snappy',
                              index=False)
                path_annotation[db_name] = str(new_path)
                log_entries.append(f"  ⤷ Saved new file: newest/{new_filename}\n")
                logger.info("Saved new file: newest/{}", new_filename)
        except Exception as e:
            logger.error("Failed to save file {}: {}", new_filename, e)
            raise OSError(f"Failed to save file {new_filename}: {e}")

        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            logger.info("Updated change log {}", log_path)
        except Exception as e:
            logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")

        try:
            with open(annotations_path, "w", encoding="utf-8") as f:
                json.dump(path_annotation, f, ensure_ascii=False, indent=4)
            logger.info("Updated path annotations {} with {}", annotations_path, path_annotation)
        except Exception as e:
            logger.error("Failed to update path annotations {}: {}", annotations_path, e)
            raise OSError(f"Failed to update annotation file {annotations_path}: {e}")

    @staticmethod
    def _process_data(db_name, db_type, databaseSchemas_data):
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

      db_path = databaseSchemas_data[db_type][db_name]['path']
      try:
          df = pd.read_excel(db_path)
      except Exception as e:
          logger.error("❌ Failed to read Excel at {}: {}", db_path, e)
          raise OSError(f"❌ Failed to read Excel at {db_path}: {e}")

      #Handle with specical cases
      for c in spec_cases:
        try:
          df[c] = df[c].map(safe_convert)
        except:
          pass

      df = df.astype(databaseSchemas_data[db_type][db_name]['dtypes'])
      df.replace(check_null_str(df), pd.NA, inplace=True)
      df.fillna(pd.NA, inplace=True)
      return df