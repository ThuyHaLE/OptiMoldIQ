import pandas as pd
import os
from pathlib import Path
from loguru import logger
import tempfile
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List,  Any

from agents.utils import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig

# Import healing system constants for error handling and recovery
from agents.dataPipelineOrchestrator.data_collector_healing_rules import check_local_backup_and_update_status
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ErrorType, AgentType, AgentExecutionInfo, RecoveryAction, get_agent_config)

class DataCollector(ConfigReportMixin):

    """
    A class responsible for collecting and processing data from various sources.
    Handles product records and purchase orders from Excel files and converts them to Parquet format.
    """
    # Define requirements
    REQUIRED_FIELDS = {
        'dynamic_db_dir': str,
        'data_pipeline_dir': str
    }

    def __init__(self, config: SharedSourceConfig):
        
        """
        Initialize the DataCollector.
        
        Args:
            config: SharedSourceConfig containing processing parameters
            Including:
                - dynamic_db_dir: Directory containing the source Excel files
                - data_pipeline_dir: Base directory for output files
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger for this class
        self.logger = logger.bind(class_="DataCollector")

        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
        
        # Store config
        self.config = config

        # Setup output dir
        self.output_dir = Path(self.config.data_pipeline_dir) / "dynamicDatabase"
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Load healing configuration for this agent
        self.healing_config = get_agent_config(AgentType.DATA_COLLECTOR)

    def process_all_data(self) -> Dict[str, Any]:

        """
        Main processing method that handles all data types.
        Processes both product records and purchase orders.
        
        Returns:
            Dict containing execution information with status, summary, details, and log entries
        """
        
        self.logger.info("Starting DataCollector ...")

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, 
                                                     required_only=True)

        # Initialize log entries
        log_entries = [config_header]
        log_entries.append(f"--Processing Summary--\n")
        log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

        # Initialize results list and overall status
        results = []
        overall_status = ProcessingStatus.SUCCESS

        # Process product records from monthly reports
        log_entries.append(f">>> Processing Product Records <<<\n")
        product_result = self._process_data_type(
            folder_path=Path(self.config.dynamic_db_dir) / 'monthlyReports_history',
            summary_file_path=self.output_dir / 'productRecords.parquet',
            name_start='monthlyReports_',
            file_extension='.xlsb',
            sheet_name='Sheet1',
            data_type='productRecords'
        )
        results.append(product_result)
        log_entries.append(product_result.get('log_entries', ''))
        log_entries.append(f"\n")

        # Process purchase orders from purchase order files
        log_entries.append(f">>> Processing Purchase Orders <<<\n")
        purchase_result = self._process_data_type(
            folder_path=Path(self.config.dynamic_db_dir) / 'purchaseOrders_history',
            summary_file_path=self.output_dir / 'purchaseOrders.parquet',
            name_start='purchaseOrder_',
            file_extension='.xlsx',
            sheet_name='poList',
            data_type='purchaseOrders'
        )
        results.append(purchase_result)
        log_entries.append(purchase_result.get('log_entries', ''))
        log_entries.append(f"\n")

        # Determine overall processing status based on individual results
        if any(r['status'] == ProcessingStatus.ERROR.value for r in results):
            overall_status = ProcessingStatus.ERROR
            log_entries.append(f"⚠️  Overall Status: ERROR\n")
        elif any(r['status'] == ProcessingStatus.WARNING.value for r in results):
            overall_status = ProcessingStatus.WARNING
            log_entries.append(f"⚠️  Overall Status: WARNING\n")
        elif any(r['status'] == ProcessingStatus.PARTIAL_SUCCESS.value for r in results):
            overall_status = ProcessingStatus.PARTIAL_SUCCESS
            log_entries.append(f"⚠️  Overall Status: PARTIAL SUCCESS\n")
        else:
            log_entries.append(f"✅ Overall Status: SUCCESS\n")

        # Calculate processing duration
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        # Get disk usage
        disk_usage = self._get_disk_usage()
        
        # Summary statistics
        successful_count = len([r for r in results if r['status'] == ProcessingStatus.SUCCESS.value])
        failed_count = len([r for r in results if r['status'] == ProcessingStatus.ERROR.value])
        warning_count = len([r for r in results if r['status'] == ProcessingStatus.WARNING.value])
        
        # Append summary to log entries
        log_entries.append(f"\n{'='*80}\n")
        log_entries.append(f"SUMMARY\n")
        log_entries.append(f"{'='*80}\n")
        log_entries.append(f"Total Datasets: {len(results)}\n")
        log_entries.append(f"  ✅ Successful: {successful_count}\n")
        log_entries.append(f"  ❌ Failed: {failed_count}\n")
        log_entries.append(f"  ⚠️  Warnings: {warning_count}\n")
        log_entries.append(f"Processing Duration: {processing_duration:.2f}s\n")
        log_entries.append(f"Disk Usage: {disk_usage.get('used_percent', 'N/A')}%\n")
        log_entries.append(f"{'='*80}\n")
        log_entries.append(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] Data collection completed\n")
        log_entries.append(f"{'='*80}\n")

        # Write complete log to master file
        self._write_log_to_file(log_entries, "data_collection_master_log.txt")

        # Create execution information object with comprehensive details
        execution_info = AgentExecutionInfo(
            agent_id=AgentType.DATA_COLLECTOR.value,
            status=overall_status.value,
            summary={
                "total_datasets": len(results),
                "successful": successful_count,
                "failed": failed_count,
                "warnings": warning_count
            },
            details=results,
            healing_actions=self._get_healing_actions(results),
            trigger_agents=self._get_trigger_agents(results),
            metadata={
                "processing_duration": processing_duration,
                "processing_duration_formatted": f"{processing_duration:.2f}s",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "disk_usage": disk_usage,
                "log_entries": "".join(log_entries),
                "log_summary": {
                    "total_files_processed": sum(r.get('files_processed', 0) for r in results),
                    "total_records_processed": sum(r.get('records_processed', 0) for r in results),
                    "total_files_failed": sum(r.get('files_failed', 0) for r in results),
                }
            }
        )

        self.logger.info("✅ Process finished!!!")

        return execution_info

    def _process_data_type(self, 
                           folder_path, 
                           summary_file_path, 
                           name_start,
                           file_extension, 
                           sheet_name, 
                           data_type) -> Dict[str, Any]:
    
        """
        Process a specific data type (product records or purchase orders).
        
        Args:
            folder_path: Path to the folder containing source files
            summary_file_path: Path where the output parquet file will be saved
            name_start: Prefix pattern for file names to process
            file_extension: File extension to look for (.xlsb or .xlsx)
            sheet_name: Name of the Excel sheet to read
            data_type: Type of data being processed (for logging/reporting)
            
        Returns:
            Dict containing processing results, status, error information, and log entries
        """
        
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp_str}] Processing {data_type}...\n"]

        try:
            # Check if the source folder exists
            if not os.path.exists(folder_path):
                log_entries.append(f"  ❌ Source folder not found: {folder_path}\n")
                
                # Local healing - attempt rollback to backup
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                # Write error log
                self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Source folder {folder_path} does not exist",
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0,
                    "log_entries": "".join(log_entries)
                }

            log_entries.append(f"  ⤷ Source folder verified: {folder_path}\n")

            # Get required fields for validation
            required_fields = self._get_required_fields()
            if name_start not in required_fields:
                log_entries.append(f"  ❌ Unsupported data type: {name_start}\n")
                
                # Local healing - attempt rollback to backup for unsupported data type
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.UNSUPPORTED_DATA_TYPE, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                # Write error log
                self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.UNSUPPORTED_DATA_TYPE.value,
                    "error_message": f"Unsupported data type: {name_start}",
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0,
                    "log_entries": "".join(log_entries)
                }
            
            log_entries.append(f"  ⤷ Data type validated: {name_start}\n")
            
            # Load existing data from parquet file (if exists)
            existing_df = self._load_existing_data(summary_file_path)
            if not existing_df.empty:
                log_entries.append(f"  ⤷ Loaded existing data: {len(existing_df)} rows\n")
            else:
                log_entries.append(f"  ⤷ No existing data found - creating new file\n")

            # Get list of source files to process
            files_result = self._get_source_files(folder_path, name_start, file_extension)
            if files_result['status'] != ProcessingStatus.SUCCESS.value:
                log_entries.append(f"  ❌ Failed to get source files\n")
                log_entries.append(files_result.get('log_entries', ''))
                
                # Write error log
                self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")
                
                return {
                    **files_result,
                    "log_entries": "".join(log_entries)
                }

            log_entries.append(f"  ⤷ Found {len(files_result['files'])} files to process\n")

            # Process each file individually
            merged_dfs = [] # Successfully processed dataframes
            failed_files = [] # Files that failed processing

            for idx, file_name in enumerate(files_result['files'], 1):
                file_path = os.path.join(folder_path, file_name)
                log_entries.append(f"    [{idx}/{len(files_result['files'])}] Processing: {file_name}\n")
                
                file_result = self._process_single_file(
                    file_path, file_name, sheet_name, file_extension,
                    required_fields[name_start]
                )

                # Append single file logs
                log_entries.append(file_result.get('log_entries', ''))

                if file_result['status'] == ProcessingStatus.SUCCESS.value:
                    merged_dfs.append(file_result['data'])
                    log_entries.append(f"      ✅ Success: {len(file_result['data'])} rows\n")
                else:
                    failed_files.append({
                        "file": file_name,
                        "error": file_result['error_message']
                    })
                    log_entries.append(f"      ❌ Failed: {file_result['error_message']}\n")

            # Summary of file processing
            log_entries.append(f"  ⤷ Files processed: {len(merged_dfs)}/{len(files_result['files'])} successful\n")

            # Handle case where no files were processed successfully
            if not merged_dfs:
                log_entries.append(f"  ❌ No files could be processed successfully\n")
                
                # Local healing - attempt rollback to backup
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                # Write error log
                self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")

                return {
                    "data_type": data_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_READ_ERROR.value,
                    "error_message": "No files could be processed successfully",
                    "failed_files": failed_files,
                    "recovery_actions": updated_recovery_actions,
                    "files_processed": 0,
                    "records_processed": 0,
                    "log_entries": "".join(log_entries)
                }

            # Merge successfully processed dataframes and save to parquet
            log_entries.append(f"  ⤷ Merging {len(merged_dfs)} dataframes...\n")
            merge_result = self._merge_and_process_data(
                merged_dfs, summary_file_path, existing_df
            )
            
            # Append merge logs
            log_entries.append(merge_result.get('log_entries', ''))

            # Determine final status based on processing results
            final_status = ProcessingStatus.SUCCESS
            if failed_files:
                final_status = ProcessingStatus.PARTIAL_SUCCESS
                log_entries.append(f"  ⚠️  Partial success: {len(failed_files)} files failed\n")
            else:
                log_entries.append(f"  ✅ All files processed successfully\n")

            # Prepare recovery actions for potential data processing errors
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            # Final summary
            log_entries.append(f"  ⤷ Total records: {merge_result.get('records_processed', 0)}\n")
            log_entries.append(f"  ⤷ Output file: {summary_file_path}\n")
            if merge_result.get('data_updated', False):
                log_entries.append(f"  ⤷ File size: {merge_result.get('file_size_mb', 0):.2f}MB\n")
            
            log_entries.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {data_type} processing completed\n")

            # Write successful log
            self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")

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
                "warnings": merge_result.get('warnings', []),
                "log_entries": "".join(log_entries)
            }

        except Exception as e:
            # Handle unexpected errors during processing
            log_entries.append(f"  ❌ Unexpected error: {str(e)}\n")
            self.logger.error(f"Unexpected error in {data_type}: {e}")

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            # Write error log
            self._write_log_to_file(log_entries, f"{data_type}_processing_log.txt")

            return {
                "data_type": data_type,
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_PROCESSING_ERROR.value,
                "error_message": str(e),
                "recovery_actions": updated_recovery_actions,
                "files_processed": 0,
                "records_processed": 0,
                "log_entries": "".join(log_entries)
            }

    def _process_single_file(self, 
                             file_path, 
                             file_name, 
                             sheet_name,
                             file_extension, 
                             required_fields) -> Dict[str, Any]:
        """
        Process a single Excel file and validate its structure.
        
        Args:
            file_path: Full path to the Excel file
            file_name: Name of the file (for logging)
            sheet_name: Name of the sheet to read from
            file_extension: File extension (.xlsb or .xlsx)
            required_fields: List of required column names
            
        Returns:
            Dict containing processing status, data (if successful), and log entries
        """
        log_entries = []

        try:
            self.logger.info(f"Reading file: {file_name}")
            log_entries.append(f"        ⤷ Reading sheet: {sheet_name}\n")

            # Read Excel file based on extension
            if file_extension == '.xlsb':
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='pyxlsb')
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

            log_entries.append(f"        ⤷ Loaded {len(df)} rows, {len(df.columns)} columns\n")

            # Validate that all required fields are present
            missing_fields = [col for col in required_fields if col not in df.columns]
            if missing_fields:
                log_entries.append(f"        ❌ Missing fields: {', '.join(missing_fields)}\n")
                
                # Local healing - attempt rollback to backup for missing fields
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.MISSING_FIELDS, [])
                updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

                return {
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.MISSING_FIELDS.value,
                    "error_message": f"Missing required fields: {missing_fields}",
                    "recovery_actions": updated_recovery_actions,
                    "missing_fields": missing_fields,
                    "log_entries": "".join(log_entries)
                }

            # Filter dataframe to only include required columns
            df_filtered = df[required_fields].copy()
            log_entries.append(f"        ⤷ Filtered to {len(required_fields)} required columns\n")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "data": df_filtered,
                "records_count": len(df_filtered),
                "log_entries": "".join(log_entries)
            }

        except Exception as e:
            log_entries.append(f"        ❌ Read error: {str(e)}\n")
            
            # Handle file reading errors
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read file {file_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "log_entries": "".join(log_entries)
            }

    def _merge_and_process_data(self, 
                                merged_dfs, 
                                summary_file_path, 
                                existing_df) -> Dict[str, Any]:
        """
        Merge multiple dataframes, process the data, and save to parquet format.
        
        Args:
            merged_dfs: List of dataframes to merge
            summary_file_path: Path where the parquet file will be saved
            existing_df: Previously saved dataframe (if any)
            
        Returns:
            Dict containing merge results, statistics, and log entries
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp_str}] Merging and processing data...\n"]

        try:
            # Concatenate all dataframes into one
            merged_df = pd.concat(merged_dfs, ignore_index=True)
            initial_rows = len(merged_df)
            log_entries.append(f"  ⤷ Concatenated {len(merged_dfs)} dataframes: {initial_rows} rows\n")

            # Remove duplicate rows
            merged_df = merged_df.drop_duplicates()
            duplicates_removed = initial_rows - len(merged_df)
            if duplicates_removed > 0:
                log_entries.append(f"  ⤷ Removed {duplicates_removed} duplicate rows\n")
            else:
                log_entries.append(f"  ⤷ No duplicates found\n")

            # Apply data processing and type conversion
            merged_df = self._data_prosesssing(merged_df, summary_file_path)
            log_entries.append(f"  ⤷ Applied data processing and type conversion\n")

            # Check if the data has actually changed compared to existing data
            data_updated = True
            if not existing_df.empty:
                if self._dataframes_equal_fast(merged_df, existing_df):
                    data_updated = False
                    log_entries.append(f"  ⤷ No changes detected - data matches existing file\n")
                    self.logger.info("No changes detected in data")
                else:
                    log_entries.append(f"  ⤷ Data changes detected - will save new version\n")
            else:
                log_entries.append(f"  ⤷ No existing data - creating new file\n")

            # Save data only if it has been updated
            file_size_mb = 0
            if data_updated:
                save_result = self._save_parquet_file(merged_df, summary_file_path)
                if save_result['status'] != ProcessingStatus.SUCCESS.value:
                    # Append save error logs
                    log_entries.append(save_result.get('log_entries', ''))
                    return {
                        **save_result,
                        "log_entries": "".join(log_entries)
                    }
                file_size_mb = save_result['file_size_mb']
                # Append successful save logs
                log_entries.append(save_result.get('log_entries', ''))
            else:
                log_entries.append(f"  ⤷ Skipped saving - no changes detected\n")

            # Collect warnings about data processing
            warnings = []
            if duplicates_removed > 0:
                warnings.append(f"Removed {duplicates_removed} duplicate rows")

            log_entries.append(f"  ✅ Processing completed: {len(merged_df)} records\n")

            # Optional: Write to log file
            self._write_log_to_file(log_entries, "merge_process_log.txt")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "records_processed": len(merged_df),
                "data_updated": data_updated,
                "file_size_mb": file_size_mb,
                "duplicates_removed": duplicates_removed,
                "warnings": warnings,
                "log_entries": "".join(log_entries)
            }

        except Exception as e:
            log_entries.append(f"  ❌ Error during merge/process: {str(e)}\n")
            
            # Handle errors during data merging and processing
            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.DATA_PROCESSING_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            # Write error log
            self._write_log_to_file(log_entries, "merge_process_log.txt")

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_PROCESSING_ERROR.value,
                "error_message": f"Failed to merge and process data: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "log_entries": "".join(log_entries)
            }

    def _save_parquet_file(self, df, 
                           summary_file_path) -> Dict[str, Any]:
        """
        Save dataframe to parquet format with error handling.
        Uses atomic write (temporary file + move) to prevent corruption.
        
        Args:
            df: Dataframe to save
            summary_file_path: Target path for the parquet file
            
        Returns:
            Dict containing save results, file size, and log entries
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"    [{timestamp_str}] Saving parquet file...\n"]

        try:
            # Convert object columns to string for better parquet compatibility
            object_cols = [col for col in df.columns if df[col].dtype == 'object']
            for col in object_cols:
                df[col] = df[col].astype(str)
            
            if object_cols:
                log_entries.append(f"      ⤷ Converted {len(object_cols)} object columns to string\n")

            # Save to temporary file first (atomic write pattern)
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                temp_path = tmp.name
                df.to_parquet(
                    temp_path,
                    engine='pyarrow',
                    compression='snappy',
                    index=False
                )
            
            log_entries.append(f"      ⤷ Created temporary file: {temp_path}\n")

            # Move temporary file to final location
            shutil.move(temp_path, summary_file_path)
            log_entries.append(f"      ⤷ Moved to: {summary_file_path}\n")
            
            # Calculate file size in MB
            file_size_mb = os.path.getsize(summary_file_path) / 1024 / 1024
            log_entries.append(f"      ⤷ Saved {len(df)} rows, {file_size_mb:.2f}MB\n")

            self.logger.info(f"✅ Parquet file saved: {summary_file_path} "
                        f"({len(df)} rows, {file_size_mb:.2f}MB)")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "file_size_mb": file_size_mb,
                "log_entries": "".join(log_entries)
            }

        except Exception as e:
            # Clean up temporary file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
                log_entries.append(f"      ⤷ Cleaned up temporary file\n")

            log_entries.append(f"      ❌ Save error: {str(e)}\n")

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.PARQUET_SAVE_ERROR, [])
            updated_recovery_actions = check_local_backup_and_update_status(recovery_actions, self.output_dir)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.PARQUET_SAVE_ERROR.value,
                "error_message": f"Failed to save parquet file: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "log_entries": "".join(log_entries)
            }

    def _write_log_to_file(self, log_entries: list, log_filename: str):
        """
        Helper method to write log entries to a file.
        
        Args:
            log_entries: List of log entry strings
            log_filename: Name of the log file
        """
        try:
            log_path = Path(self.output_dir) / log_filename
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            self.logger.info(f"Updated log file: {log_path}")
        except Exception as e:
            self.logger.warning(f"Failed to write to log file {log_filename}: {e}")

    def _get_healing_actions(self, results) -> List[str]:
        
        """
        Determine what healing actions should be taken based on processing results.
        
        Args:
            results: List of processing results from different data types
            
        Returns:
            List of healing actions to be performed
        """

        healing_actions = set()

        for result in results:
            if result['status'] == ProcessingStatus.ERROR.value:
                # Add recovery actions for errors
                healing_actions.update(result.get('recovery_actions', []))
            elif result['status'] == ProcessingStatus.PARTIAL_SUCCESS.value:
                # Add retry action for partial successes
                healing_actions.add(RecoveryAction.RETRY_PROCESSING.value)

        return list(healing_actions)

    def _get_trigger_agents(self, results) -> List[str]:
        
        """
        Determine which downstream agents should be triggered based on processing results.
        
        Args:
            results: List of processing results from different data types
            
        Returns:
            List of agent types that should be triggered
        """

        trigger_agents = []

        for result in results:
            if result['status'] == ProcessingStatus.SUCCESS.value:
                # Trigger data loader agents when data is successfully processed
                trigger_list = self.healing_config.trigger_on_status.get(ProcessingStatus.SUCCESS, [])
                trigger_agents.extend([agent.value for agent in trigger_list])
            elif result['status'] == ProcessingStatus.ERROR.value:
                # Trigger admin notification agents for errors
                trigger_list = self.healing_config.trigger_on_status.get(ProcessingStatus.ERROR, [])
                trigger_agents.extend([agent.value for agent in trigger_list])

        return list(set(trigger_agents))  # Remove duplicates

    def _get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage information for monitoring purposes.
        
        Returns:
            Dict containing disk usage statistics
        """
        try:
            # Get disk usage for the output directory
            disk_stat = shutil.disk_usage(self.output_dir)
            total_gb = disk_stat.total / (1024 ** 3)
            used_gb = disk_stat.used / (1024 ** 3)
            free_gb = disk_stat.free / (1024 ** 3)
            used_percent = (disk_stat.used / disk_stat.total) * 100

            # Calculate total size of parquet files in output directory
            parquet_size_mb = 0
            try:
                parquet_size_mb = sum(
                    os.path.getsize(os.path.join(self.output_dir, f))
                    for f in os.listdir(self.output_dir)
                    if f.endswith('.parquet')
                ) / (1024 ** 2)
            except:
                pass

            return {
                "total": f"{total_gb:.2f}GB",
                "used": f"{used_gb:.2f}GB",
                "free": f"{free_gb:.2f}GB",
                "used_percent": round(used_percent, 2),
                "parquet_files_size_mb": round(parquet_size_mb, 2)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get disk usage: {e}")
            return {
                "total": "N/A",
                "used": "N/A",
                "free": "N/A",
                "used_percent": "N/A",
                "parquet_files_size_mb": 0
            }

    # Helper methods for file and data processing
    def _get_source_files(self, folder_path, name_start, file_extension):
        """
        Get and validate source files from the specified folder.
        
        Args:
            folder_path: Path to search for files
            name_start: Prefix pattern for file names
            file_extension: Required file extension
            
        Returns:
            Dict containing file list, status, and log entries
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"  [{timestamp_str}] Searching for source files...\n"]

        try:
            # Find files matching the pattern
            files = [f for f in os.listdir(folder_path)
                    if f.startswith(name_start) and f.endswith(file_extension)]

            if not files:
                log_entries.append(f"    ❌ No files found matching pattern: {name_start}*{file_extension}\n")
                return {
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"No files found matching pattern {name_start}*{file_extension}",
                    "files": [],
                    "log_entries": "".join(log_entries)
                }

            # Sort files by date (extracted from filename)
            files_sorted = sorted(files, key=lambda x: int(x.split('_')[1][:6]))
            log_entries.append(f"    ✅ Found {len(files_sorted)} files matching pattern\n")

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "files": files_sorted,
                "log_entries": "".join(log_entries)
            }
        except Exception as e:
            log_entries.append(f"    ❌ Error searching files: {str(e)}\n")
            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_NOT_FOUND.value,
                "error_message": f"Error searching files: {str(e)}",
                "files": [],
                "log_entries": "".join(log_entries)
            }

    def _load_existing_data(self, summary_file_path):
        
        """
        Load existing parquet file if it exists.
        
        Args:
            summary_file_path: Path to the parquet file
            
        Returns:
            DataFrame containing existing data, or empty DataFrame if file doesn't exist
        """

        if os.path.exists(summary_file_path):
            try:
                return pd.read_parquet(summary_file_path)
            except Exception as e:
                self.logger.warning(f"Error reading existing parquet file: {e}")

        return pd.DataFrame()

    # Static methods for data processing and validation
    @staticmethod
    def _dataframes_equal_fast(df1, df2):
        
        """
        Fast comparison of dataframes using hash-based comparison.
        
        Args:
            df1, df2: DataFrames to compare
            
        Returns:
            Boolean indicating if dataframes are equal
        """

        # Quick shape comparison first
        if df1.shape != df2.shape:
            return False

        try:
            # Use hash-based comparison for speed
            hash1 = hashlib.md5(pd.util.hash_pandas_object(df1, index=False).values).hexdigest()
            hash2 = hashlib.md5(pd.util.hash_pandas_object(df2, index=False).values).hexdigest()
            return hash1 == hash2
        except:
            # Fallback to standard equals method
            return df1.equals(df2)

    @staticmethod
    def _get_required_fields():
        
        """
        Get required field definitions for different data types.
        
        Returns:
            Dict mapping data type prefixes to their required field lists
        """

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
        
        """
        Process and clean the dataframe according to business rules.
        Handles data type conversions, null value standardization, and schema validation.
        
        Args:
            df: DataFrame to process
            summary_file_path: Path to output file (used to determine data type)
            
        Returns:
            Processed DataFrame with proper data types and cleaned values
        """

        def check_null_str(df):

            """
            Identify string values that should be treated as null/NaN.
            
            Returns:
                List of values found in the dataframe that should be converted to NaN
            """

            suspect_values = ['nan', "null", "none", "", "n/a", "na"]
            nan_values = []
            for col in df.columns:
                for uniq in df[col].unique():
                    if str(uniq).lower() in suspect_values:
                        nan_values.append(uniq)
            return list(set(nan_values))

        def safe_convert(x):

            """
            Safely convert values to string, handling numeric and null values.
            
            Args:
                x: Value to convert
                
            Returns:
                String representation of the value, or original value if null
            """

            if pd.isna(x):
                return x
            if isinstance(x, (int, float)) and not pd.isna(x):
                return str(int(x))
            return str(x)

        # Special handling for material code columns
        spec_cases = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

        # Define data schemas for different data types
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

        # Determine data type from output file name
        db_name = Path(summary_file_path).name.replace('.parquet', '')

        # Apply data type specific transformations
        if db_name == "productRecords":
            # Standardize column names
            df.rename(columns={
                                "plasticResine": "plasticResin",
                                "plasticResineCode": "plasticResinCode",
                                'plasticResineLot': 'plasticResinLot'
                            }, inplace=True)
            # Convert Excel serial date to datetime
            df['recordDate'] = df['recordDate'].apply(lambda x: timedelta(days=x) + datetime(1899,12,30))
        
        if db_name == "purchaseOrders":
            # Convert date columns to datetime
            df[['poReceivedDate', 'poETA']] = df[['poReceivedDate',
                                                  'poETA']].apply(lambda col: pd.to_datetime(col, errors='coerce'))

        # Handle special cases for material code columns
        for c in spec_cases:
            if c in df.columns:
                df[c] = df[c].map(safe_convert)

        # Apply data type schema
        df = df.astype(schema_data[db_name]['dtypes'])

        # Standardize working shift values to uppercase
        if db_name == "productRecords":
            df['workingShift'] = df['workingShift'].str.upper()

        # Replace various null-like string values with pandas NA
        df.replace(check_null_str(df), pd.NA, inplace=True)
        df.fillna(pd.NA, inplace=True)

        return df