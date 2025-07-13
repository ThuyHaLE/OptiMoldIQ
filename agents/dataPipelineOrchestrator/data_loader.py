import pandas as pd
from loguru import logger
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
import os
from typing import Dict, List, Any

# Import healing system constants
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ErrorType, AgentType, AgentExecutionInfo, RecoveryAction, get_agent_config)
from agents.dataPipelineOrchestrator.data_loader_healing_rules import check_annotation_paths_and_update_status

class DataLoaderAgent:
    def __init__(self,
                 databaseSchemas_path: str = "database/databaseSchemas.json",
                 annotation_path: str = 'agents/shared_db/DataLoaderAgent/newest/path_annotations.json',
                 default_dir: str = "agents/shared_db"
                 ):

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DataLoaderAgent"
        self.logger = logger.bind(class_="DataLoaderAgent")

        self.annotation_path = annotation_path
        self.config = get_agent_config(AgentType.DATA_LOADER)

        # Load database schema
        with open(databaseSchemas_path, "r", encoding="utf-8") as f:
            self.databaseSchemas_data = json.load(f)

        # Load existing path annotations
        if os.path.exists(self.annotation_path):
            with open(self.annotation_path, "r", encoding="utf-8") as f:
                self.path_annotation = json.load(f)
            logger.debug("Loaded existing annotation file: {}", self.path_annotation)
        else:
            self.path_annotation = {}
            logger.info("First time for initial - creating new annotation file...")

    def process_all_data(self) -> Dict[str, Any]:
        """Main processing method with structured response"""

        start_time = datetime.now()
        results = []
        overall_status = ProcessingStatus.SUCCESS

        # Process to load and check if there is any change in files
        self.have_changed_files = {}

        for db_type in self.databaseSchemas_data.keys():
            for db_name in self.databaseSchemas_data[db_type].keys():
                db_result = self._process_database(db_name, db_type)
                results.append(db_result)

                # Collect changed files
                if db_result['status'] == ProcessingStatus.SUCCESS.value and db_result.get('data_updated', False):
                    self.have_changed_files[db_name] = db_result.get('dataframe')

        # Save changed files if any
        save_result = None
        if self.have_changed_files:
            save_result = self._save_changed_files()
            results.append(save_result)

        # Determine overall status
        if any(r['status'] == ProcessingStatus.ERROR.value for r in results):
            overall_status = ProcessingStatus.ERROR
        elif any(r['status'] == ProcessingStatus.WARNING.value for r in results):
            overall_status = ProcessingStatus.WARNING
        elif any(r['status'] == ProcessingStatus.PARTIAL_SUCCESS.value for r in results):
            overall_status = ProcessingStatus.PARTIAL_SUCCESS

        processing_duration = (datetime.now() - start_time).total_seconds()

        execution_info = AgentExecutionInfo(agent_id=AgentType.DATA_LOADER.value,
                                            status=overall_status.value,
                                            summary={
                                                "total_databases": len([r for r in results if r.get('database_name')]),
                                                "successful": len([r for r in results if r['status'] == ProcessingStatus.SUCCESS.value and r.get('database_name')]),
                                                "failed": len([r for r in results if r['status'] == ProcessingStatus.ERROR.value and r.get('database_name')]),
                                                "warnings": len([r for r in results if r['status'] == ProcessingStatus.WARNING.value and r.get('database_name')]),
                                                "changed_files": len(self.have_changed_files),
                                                "files_saved": 1 if save_result and save_result['status'] == ProcessingStatus.SUCCESS.value else 0
                                            },
                                            details=results,
                                            healing_actions=self._get_healing_actions(results),
                                            trigger_agents=self._get_trigger_agents(results),
                                            metadata={
                                                "processing_duration_seconds": processing_duration,
                                                "memory_usage": self._get_memory_usage(),
                                                "disk_usage": self._get_disk_usage()
                                            }
                                        )

        return execution_info

    def _process_database(self, db_name: str, db_type: str) -> Dict[str, Any]:
        """Process single database with detailed error handling"""

        try:
            # Get existing path
            db_existing_path = self.path_annotation.get(db_name, "")

            # Load current data
            if db_type == 'dynamicDB':
                current_result = self._load_dynamic_db(db_name, db_type)
            else:
                current_result = self._load_static_db(db_name, db_type)

            if current_result['status'] != ProcessingStatus.SUCCESS.value:
                return current_result

            current_df = current_result['dataframe']

            # Load existing data
            existing_result = self._load_existing_df(db_existing_path)
            if existing_result['status'] != ProcessingStatus.SUCCESS.value:
                # If can't load existing, treat as new data
                existing_df = pd.DataFrame()
                warnings = [existing_result['error_message']]
            else:
                existing_df = existing_result['dataframe']
                warnings = []

            # Compare dataframes
            comparison_result = self._compare_dataframes(current_df, existing_df)
            if comparison_result['status'] != ProcessingStatus.SUCCESS.value:
                
                #local healing
                recovery_actions = self.config.recovery_actions.get(ErrorType.HASH_COMPARISON_ERROR, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

                return {
                    "database_name": db_name,
                    "database_type": db_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.HASH_COMPARISON_ERROR.value,
                    "error_message": comparison_result['error_message'],
                    "recovery_actions": updated_recovery_actions,
                    "records_processed": 0,
                    "data_updated": False
                }

            data_updated = not comparison_result['dataframes_equal']

            return {
                "database_name": db_name,
                "database_type": db_type,
                "status": ProcessingStatus.SUCCESS.value,
                "records_processed": len(current_df),
                "data_updated": data_updated,
                "dataframe": current_df,
                "existing_path": db_existing_path,
                "warnings": warnings,
                "recovery_actions": []
            }

        except Exception as e:
            self.logger.error(f"Unexpected error processing {db_name}: {e}")

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.DATA_CORRUPTION, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "database_name": db_name,
                "database_type": db_type,
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_CORRUPTION.value,
                "error_message": str(e),
                "recovery_actions": updated_recovery_actions,
                "records_processed": 0,
                "data_updated": False
            }

    def _load_dynamic_db(self, db_name: str, db_type: str) -> Dict[str, Any]:
        """Load dynamic database file"""

        try:
            db_current_path = self.databaseSchemas_data[db_type][db_name]['path']

            if not os.path.exists(db_current_path):

                #local healing
                recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

                return {
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Dynamic DB file not found: {db_current_path}",
                    "recovery_actions": updated_recovery_actions,
                }

            df = pd.read_parquet(db_current_path)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df,
                "file_path": db_current_path
            }

        except Exception as e:

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read dynamic DB {db_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _load_static_db(self, db_name: str, db_type: str) -> Dict[str, Any]:
        """Load and process static database file"""

        try:
            df = self._process_data(db_name, db_type, self.databaseSchemas_data)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df
            }

        except Exception as e:

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.SCHEMA_MISMATCH, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.SCHEMA_MISMATCH.value,
                "error_message": f"Failed to process static DB {db_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _load_existing_df(self, file_path: str) -> Dict[str, Any]:
        """Load existing dataframe from file"""

        try:
            if not file_path or not os.path.exists(file_path):

                #local healing
                recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

                return {
                    "status": ProcessingStatus.WARNING.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Existing file not found: {file_path}",
                    "recovery_actions": updated_recovery_actions,
                    "dataframe": pd.DataFrame()
                }

            df = pd.read_parquet(file_path)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df
            }

        except Exception as e:

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "status": ProcessingStatus.WARNING.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read existing file {file_path}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "dataframe": pd.DataFrame()
            }

    def _compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
        """Compare two dataframes"""

        try:
            are_equal = self._dataframes_equal_fast(df1, df2)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframes_equal": are_equal
            }

        except Exception as e:

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.HASH_COMPARISON_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.HASH_COMPARISON_ERROR.value,
                "error_message": f"Failed to compare dataframes: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _save_changed_files(self) -> Dict[str, Any]:
        """Save changed files with versioning"""

        try:
            if not self.have_changed_files:
                return {
                    "operation": "file_save",
                    "status": ProcessingStatus.SUCCESS.value,
                    "message": "No changes detected - no files to save",
                    "files_saved": 0
                }

            self.logger.debug("Detect changes: {}", [(k, v.columns) for k, v in self.have_changed_files.items()])

            # Call the existing save method
            self.save_output_with_versioning(
                self.have_changed_files,
                self.path_annotation,
                self.output_dir
            )

            return {
                "operation": "file_save",
                "status": ProcessingStatus.SUCCESS.value,
                "files_saved": len(self.have_changed_files),
                "saved_files": list(self.have_changed_files.keys()),
                "output_directory": str(self.output_dir)
            }

        except Exception as e:
            self.logger.error(f"Failed to save changed files: {e}")

            #local healing
            recovery_actions = self.config.recovery_actions.get(ErrorType.PARQUET_SAVE_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.annotation_path)

            return {
                "operation": "file_save",
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.PARQUET_SAVE_ERROR.value,
                "error_message": f"Failed to save files: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "files_saved": 0
            }

    def _get_healing_actions(self, results: List[Dict[str, Any]]) -> List[str]:
        """Determine healing actions based on results"""

        healing_actions = set()

        for result in results:
            if result['status'] == ProcessingStatus.ERROR.value:
                healing_actions.update(result.get('recovery_actions', []))
            elif result['status'] == ProcessingStatus.PARTIAL_SUCCESS.value:
                healing_actions.add(RecoveryAction.RETRY_PROCESSING.value)
            elif result['status'] == ProcessingStatus.WARNING.value:
                healing_actions.add(RecoveryAction.TRIGGER_MANUAL_REVIEW.value)

        return list(healing_actions)

    def _get_trigger_agents(self, results: List[Dict[str, Any]]) -> List[str]:
        """Determine which agents to trigger based on results"""

        trigger_agents = []

        for result in results:
            if result['status'] == ProcessingStatus.SUCCESS.value and result.get('data_updated'):
                # Trigger downstream agents when data is updated
                trigger_list = self.config.trigger_on_status.get(ProcessingStatus.SUCCESS, [])
                trigger_agents.extend([agent.value for agent in trigger_list])
            elif result['status'] == ProcessingStatus.ERROR.value:
                # Trigger admin notification
                trigger_list = self.config.trigger_on_status.get(ProcessingStatus.ERROR, [])
                trigger_agents.extend([agent.value for agent in trigger_list])

        return list(set(trigger_agents))  # Remove duplicates

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""

        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent()
            }
        except:
            return {"memory_mb": None, "memory_percent": None}

    def _get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage information"""

        try:
            output_size = 0
            if self.output_dir.exists():
                for file_path in self.output_dir.rglob("*.parquet"):
                    output_size += file_path.stat().st_size

            output_size_mb = output_size / 1024 / 1024
            available_space_mb = shutil.disk_usage(self.output_dir).free / 1024 / 1024

            return {
                "output_directory_mb": output_size_mb,
                "available_space_mb": available_space_mb
            }
        except:
            return {"output_directory_mb": 0, "available_space_mb": 0}

    # Keep all existing static methods
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

        # Handle with special cases
        for c in spec_cases:
            try:
                df[c] = df[c].map(safe_convert)
            except:
                pass

        df = df.astype(databaseSchemas_data[db_type][db_name]['dtypes'])
        df.replace(check_null_str(df), pd.NA, inplace=True)
        df.fillna(pd.NA, inplace=True)
        return df