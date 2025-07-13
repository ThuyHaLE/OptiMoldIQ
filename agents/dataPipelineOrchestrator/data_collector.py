import pandas as pd
import os
from pathlib import Path
from loguru import logger
import tempfile
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List,  Any

# Import healing system constants
from agents.dataPipelineOrchestrator.data_collector_healing_rules import check_local_backup_and_update_status
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ErrorType, AgentType, AgentExecutionInfo, RecoveryAction, get_agent_config)


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

        self.config = get_agent_config(AgentType.DATA_COLLECTOR)

    def process_all_data(self) -> Dict[str, Any]:
        """Main processing method with structured response"""

        results = []
        overall_status = ProcessingStatus.SUCCESS

        # Process productRecords
        product_result = self._process_data_type(
            folder_path=self.source_dir / 'monthlyReports_history',
            summary_file_path=self.output_dir / 'productRecords.parquet',
            name_start='monthlyReports_',
            file_extension='.xlsb',
            sheet_name='Sheet1',
            data_type='productRecords'
        )
        results.append(product_result)

        # Process purchaseOrders
        purchase_result = self._process_data_type(
            folder_path=self.source_dir / 'purchaseOrders_history',
            summary_file_path=self.output_dir / 'purchaseOrders.parquet',
            name_start='purchaseOrder_',
            file_extension='.xlsx',
            sheet_name='poList',
            data_type='purchaseOrders'
        )
        results.append(purchase_result)

        # Determine overall status
        if any(r['status'] == ProcessingStatus.ERROR.value for r in results):
            overall_status = ProcessingStatus.ERROR
        elif any(r['status'] == ProcessingStatus.WARNING.value for r in results):
            overall_status = ProcessingStatus.WARNING
        elif any(r['status'] == ProcessingStatus.PARTIAL_SUCCESS.value for r in results):
            overall_status = ProcessingStatus.PARTIAL_SUCCESS

        execution_info = AgentExecutionInfo(agent_id=AgentType.DATA_COLLECTOR.value,
                                            status=overall_status.value,
                                            summary={
                                                "total_datasets": len(results),
                                                "successful": len([r for r in results if r['status'] == ProcessingStatus.SUCCESS.value]),
                                                "failed": len([r for r in results if r['status'] == ProcessingStatus.ERROR.value]),
                                                "warnings": len([r for r in results if r['status'] == ProcessingStatus.WARNING.value])
                                            },
                                            details=results,
                                            healing_actions=self._get_healing_actions(results),
                                            trigger_agents=self._get_trigger_agents(results),
                                            metadata={
                                                "processing_duration": None,
                                                "disk_usage": self._get_disk_usage()
                                            }
                                        )

        return execution_info

    def _process_data_type(self, folder_path, summary_file_path, name_start,
                          file_extension, sheet_name, data_type) -> Dict[str, Any]:
        """Process single data type with detailed error handling"""

        try:
            # Check if source folder exists
            if not os.path.exists(folder_path):

                #local healing - rollback to backup
                recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Source folder {folder_path} does not exist",
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0
                }

            # Get required fields
            required_fields = self._get_required_fields()
            if name_start not in required_fields:

                #local healing - rollback to backup
                recovery_actions = self.config.recovery_actions.get(ErrorType.UNSUPPORTED_DATA_TYPE, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.UNSUPPORTED_DATA_TYPE.value,
                    "error_message": f"Unsupported data type: {name_start}",
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0
                }
            # Load existing data
            existing_df = self._load_existing_data(summary_file_path)

            # Get and process files
            files_result = self._get_source_files(folder_path, name_start, file_extension)
            if files_result['status'] != ProcessingStatus.SUCCESS.value:
                return files_result

            # Process each file
            merged_dfs = []
            failed_files = []

            for file_name in files_result['files']:
                file_path = os.path.join(folder_path, file_name)
                file_result = self._process_single_file(
                    file_path, file_name, sheet_name, file_extension,
                    required_fields[name_start]
                )

                if file_result['status'] == ProcessingStatus.SUCCESS.value:
                    merged_dfs.append(file_result['data'])
                else:
                    failed_files.append({
                        "file": file_name,
                        "error": file_result['error_message']
                    })

            # Handle no successful files
            if not merged_dfs:

                #local healing - rollback to backup
                recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_READ_ERROR.value,
                    "error_message": "No files could be processed successfully",
                    "failed_files": failed_files,
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0
                }

            # Merge and process data
            merge_result = self._merge_and_process_data(
                merged_dfs, summary_file_path, existing_df
            )

            # Determine final status
            final_status = ProcessingStatus.SUCCESS
            if failed_files:
                final_status = ProcessingStatus.PARTIAL_SUCCESS

            #local healing - rollback to backup
            recovery_actions = self.config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "data_type": data_type,
                "status": final_status.value,
                "files_processed": len(files_result['files']),
                "files_successful": len(merged_dfs),
                "files_failed": len(failed_files),
                "failed_files": failed_files,
                "records_processed": merge_result.get('records_processed', 0),
                "output_file": str(summary_file_path),
                "file_size_mb": merge_result.get('file_size_mb', 0),
                "data_updated": merge_result.get('data_updated', False),
                "error_type": ErrorType.DATA_PROCESSING_ERROR.value,
                "recovery_actions": updated_recovery_actions if failed_files else [],
                "warnings": merge_result.get('warnings', [])
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in {data_type}: {e}")

            #local healing - rollback to backup
            recovery_actions = self.config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "data_type": data_type,
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_PROCESSING_ERROR.value,
                "error_message": str(e),
                "recovery_actions": updated_recovery_actions,
                "files_processed": 0,
                "records_processed": 0
            }

    def _process_single_file(self, file_path, file_name, sheet_name,
                           file_extension, required_fields) -> Dict[str, Any]:
        """Process single file with error handling"""

        try:
            self.logger.info(f"Reading file: {file_name}")

            if file_extension == '.xlsb':
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='pyxlsb')
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Check missing fields
            missing_fields = [col for col in required_fields if col not in df.columns]
            if missing_fields:
                
                #local healing - rollback to backup
                recovery_actions = self.config.recovery_actions.get(ErrorType.MISSING_FIELDS, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                return {
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.MISSING_FIELDS.value,
                    "error_message": f"Missing required fields: {missing_fields}",
                    "recovery_actions": updated_recovery_actions,
                    "missing_fields": missing_fields
                }

            # Filter to required columns
            df_filtered = df[required_fields].copy()

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "data": df_filtered,
                "records_count": len(df_filtered)
            }

        except Exception as e:

            #local healing - rollback to backup
            recovery_actions = self.config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read file {file_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _merge_and_process_data(self, merged_dfs, summary_file_path, existing_df) -> Dict[str, Any]:
        """Merge dataframes and save with error handling"""

        try:
            # Merge dataframes
            merged_df = pd.concat(merged_dfs, ignore_index=True)
            initial_rows = len(merged_df)

            # Remove duplicates
            merged_df = merged_df.drop_duplicates()
            duplicates_removed = initial_rows - len(merged_df)

            # Process data
            merged_df = self._data_prosesssing(merged_df, summary_file_path)

            # Check if data changed
            data_updated = True
            if not existing_df.empty:
                if self._dataframes_equal_fast(merged_df, existing_df):
                    data_updated = False
                    self.logger.info("No changes detected in data")

            # Save data if updated
            file_size_mb = 0
            if data_updated:
                save_result = self._save_parquet_file(merged_df, summary_file_path)
                if save_result['status'] != ProcessingStatus.SUCCESS.value:
                    return save_result
                file_size_mb = save_result['file_size_mb']

            warnings = []
            if duplicates_removed > 0:
                warnings.append(f"Removed {duplicates_removed} duplicate rows")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "records_processed": len(merged_df),
                "data_updated": data_updated,
                "file_size_mb": file_size_mb,
                "duplicates_removed": duplicates_removed,
                "warnings": warnings
            }

        except Exception as e:

            #local healing - rollback to backup
            recovery_actions = self.config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_PROCESSING_ERROR.value,
                "error_message": f"Failed to merge and process data: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _save_parquet_file(self, df, summary_file_path) -> Dict[str, Any]:
        """Save parquet file with error handling"""

        try:
            # Convert object columns to string
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)

            # Save to temporary file first
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                temp_path = tmp.name
                df.to_parquet(
                    temp_path,
                    engine='pyarrow',
                    compression='snappy',
                    index=False
                )

            # Move to final location
            shutil.move(temp_path, summary_file_path)

            file_size_mb = os.path.getsize(summary_file_path) / 1024 / 1024

            self.logger.info(f"✅ Parquet file saved: {summary_file_path} "
                           f"({len(df)} rows, {file_size_mb:.2f}MB)")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "file_size_mb": file_size_mb
            }

        except Exception as e:
            # Clean up temp file if exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

            #local healing - rollback to backup
            recovery_actions = self.config.recovery_actions.get(ErrorType.PARQUET_SAVE_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.PARQUET_SAVE_ERROR.value,
                "error_message": f"Failed to save parquet file: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _get_healing_actions(self, results) -> List[str]:
        """Determine healing actions based on results"""

        healing_actions = set()

        for result in results:
            if result['status'] == ProcessingStatus.ERROR.value:
                healing_actions.update(result.get('recovery_actions', []))
            elif result['status'] == ProcessingStatus.PARTIAL_SUCCESS.value:
                healing_actions.add(RecoveryAction.RETRY_PROCESSING.value)

        return list(healing_actions)

    def _get_trigger_agents(self, results) -> List[str]:
        """Determine which agents to trigger based on results"""

        trigger_agents = []

        for result in results:
            if result['status'] == ProcessingStatus.SUCCESS.value:
                # Trigger data loader agents when data is successfully processed
                trigger_list = self.config.trigger_on_status.get(ProcessingStatus.SUCCESS, [])
                trigger_agents.extend([agent.value for agent in trigger_list])
            elif result['status'] == ProcessingStatus.ERROR.value:
                # Trigger admin notification
                trigger_list = self.config.trigger_on_status.get(ProcessingStatus.ERROR, [])
                trigger_agents.extend([agent.value for agent in trigger_list])

        return list(set(trigger_agents))  # Remove duplicates

    def _get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage information"""

        try:
            output_size = sum(
                os.path.getsize(os.path.join(self.output_dir, f))
                for f in os.listdir(self.output_dir)
                if f.endswith('.parquet')
            ) / 1024 / 1024  # MB

            return {
                "output_directory_mb": output_size,
                "available_space_mb": shutil.disk_usage(self.output_dir).free / 1024 / 1024
            }
        except:
            return {}

    # Keep existing helper methods
    def _get_source_files(self, folder_path, name_start, file_extension):
        """Get and validate source files"""

        files = [f for f in os.listdir(folder_path)
                if f.startswith(name_start) and f.endswith(file_extension)]

        if not files:
            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_NOT_FOUND.value,
                "error_message": f"No files found matching pattern {name_start}*{file_extension}",
                "files": []
            }

        files_sorted = sorted(files, key=lambda x: int(x.split('_')[1][:6]))

        return {
            "status": ProcessingStatus.SUCCESS.value,
            "files": files_sorted
        }

    def _load_existing_data(self, summary_file_path):
        """Load existing parquet file"""

        if os.path.exists(summary_file_path):
            try:
                return pd.read_parquet(summary_file_path)
            except Exception as e:
                self.logger.warning(f"Error reading existing parquet file: {e}")

        return pd.DataFrame()

    # Keep all existing static methods unchanged
    @staticmethod
    def _dataframes_equal_fast(df1, df2):
        """Fast comparison of dataframes using hash"""
        if df1.shape != df2.shape:
            return False

        try:
            hash1 = hashlib.md5(pd.util.hash_pandas_object(df1, index=False).values).hexdigest()
            hash2 = hashlib.md5(pd.util.hash_pandas_object(df2, index=False).values).hexdigest()
            return hash1 == hash2
        except:
            return df1.equals(df2)

    @staticmethod
    def _get_required_fields():
        """Get required fields for different data types"""

        return {
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

    @staticmethod
    def _data_prosesssing(df, summary_file_path):
        """Keep existing data processing logic unchanged"""

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

        # Handle special cases
        for c in spec_cases:
            if c in df.columns:
                df[c] = df[c].map(safe_convert)

        df = df.astype(schema_data[db_name]['dtypes'])
        if db_name == "productRecords":
            df['workingShift'] = df['workingShift'].str.upper()

        # Fill null with same format pd.NA
        df.replace(check_null_str(df), pd.NA, inplace=True)
        df.fillna(pd.NA, inplace=True)

        return df