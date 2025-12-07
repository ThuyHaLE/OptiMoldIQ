import pandas as pd
from loguru import logger
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
import os
from typing import Dict, List, Any

from agents.utils import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig

# Import healing system constants for error handling and recovery
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ErrorType, AgentType, AgentExecutionInfo, RecoveryAction, get_agent_config)
from agents.dataPipelineOrchestrator.data_loader_healing_rules import check_annotation_paths_and_update_status

class DataLoaderAgent(ConfigReportMixin):

    """
    Data Loader Agent responsible for loading, processing, and managing database files.
    
    This agent handles both static and dynamic databases, detects changes in data,
    and provides comprehensive error handling with recovery mechanisms.
    """

    # Define requirements
    REQUIRED_FIELDS = {
        'databaseSchemas_path': str,
        'annotation_path': str,
        'data_pipeline_dir': str
    }

    def __init__(self, config: SharedSourceConfig):
        
        """
        Initialize the DataLoaderAgent.
        
        Args:
            config: SharedSourceConfig containing processing parameters
            Including:
                - databaseSchemas_path: Path to database schema configuration file
                - annotation_path: Path to file storing database path annotations
                - data_pipeline_dir: Default directory for shared database files
        """
        self._capture_init_args()
        
        # Initialize logger for this class
        self.logger = logger.bind(class_="DataLoaderAgent")
        
        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
    
        self.config = config

        # Load database schema configuration
        if os.path.exists(self.config.databaseSchemas_path):
            with open(self.config.databaseSchemas_path, "r", encoding="utf-8") as f:
                self.databaseSchemas_data = json.load(f)
  
        # Load existing path annotations if available, otherwise create empty dict
        if os.path.exists(self.config.annotation_path):
            with open(self.config.annotation_path, "r", encoding="utf-8") as f:
                self.path_annotation = json.load(f)
            logger.debug("Loaded existing annotation file: {}", self.path_annotation)
        else:
            self.path_annotation = {}
            logger.info("First time for initial - creating new annotation file...")

        # Set up directory paths
        self.output_dir = Path(self.config.data_pipeline_dir) / "DataLoaderAgent"
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load healing configuration for this agent
        self.healing_config = get_agent_config(AgentType.DATA_LOADER)

    def process_all_data(self) -> Dict[str, Any]:
        """
        Main processing method that handles all databases and returns structured response.
        
        Returns:
            Dict containing execution information including status, results, and metadata
        """
        
        self.logger.info("Starting DataLoaderAgent ...")

        start_time = datetime.now()
        results = []
        overall_status = ProcessingStatus.SUCCESS

        # Generate config header using mixin
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, 
                                                     required_only=True)

        # Initialize combined log entries for entire processing run
        combined_log_entries = [config_header]
        combined_log_entries.append(f"--Processing Summary--\n")
        combined_log_entries.append(f"⤷ {self.__class__.__name__} results:\n")

        # Dictionary to store files that have changed and need to be saved
        self.have_changed_files = {}
        
        # Count databases to process
        total_databases = sum(len(dbs) for dbs in self.databaseSchemas_data.values())
        combined_log_entries.append(f"Total databases to process: {total_databases}\n\n")

        # Process each database type and database name
        db_counter = 0
        for db_type in self.databaseSchemas_data.keys():
            for db_name in self.databaseSchemas_data[db_type].keys():
                db_counter += 1
                combined_log_entries.append(f"--- Database {db_counter}/{total_databases} ---\n")
                
                db_result = self._process_database(db_name, db_type)
                results.append(db_result)
                
                # Collect log entries from individual database processing
                if 'log_entries' in db_result:
                    combined_log_entries.append(db_result['log_entries'])
                
                combined_log_entries.append("\n")  # Add spacing between databases

                # Collect changed files for saving
                if db_result['status'] == ProcessingStatus.SUCCESS.value and db_result.get('data_updated', False):
                    self.have_changed_files[db_name] = db_result.get('dataframe')

        # Save changed files if any were detected
        combined_log_entries.append(f"\n{'='*80}\n")
        combined_log_entries.append("FILE SAVE OPERATION\n")
        combined_log_entries.append(f"{'='*80}\n\n")
        
        save_result = None
        if self.have_changed_files:
            combined_log_entries.append(f"Files requiring save: {list(self.have_changed_files.keys())}\n\n")
            save_result = self._save_changed_files()
            results.append(save_result)
            
            # Add save operation log entries
            if 'log_entries' in save_result:
                combined_log_entries.append(save_result['log_entries'])
        else:
            no_changes_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            combined_log_entries.append(f"[{no_changes_timestamp}] No file changes detected - skipping save operation\n")

        # Determine overall processing status based on individual results
        if any(r['status'] == ProcessingStatus.ERROR.value for r in results):
            overall_status = ProcessingStatus.ERROR
        elif any(r['status'] == ProcessingStatus.WARNING.value for r in results):
            overall_status = ProcessingStatus.WARNING
        elif any(r['status'] == ProcessingStatus.PARTIAL_SUCCESS.value for r in results):
            overall_status = ProcessingStatus.PARTIAL_SUCCESS

        # Calculate processing duration
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        db_results = [r for r in results if r.get('database_name')]
        successful_count = len([r for r in db_results if r['status'] == ProcessingStatus.SUCCESS.value])
        failed_count = len([r for r in db_results if r['status'] == ProcessingStatus.ERROR.value])
        warning_count = len([r for r in db_results if r['status'] == ProcessingStatus.WARNING.value])
        
        # Add completion log
        combined_log_entries.append(f"\n{'='*80}\n")
        end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        combined_log_entries.append(f"[{end_timestamp}] DATA PROCESSING COMPLETED\n")
        combined_log_entries.append(f"{'='*80}\n\n")
        combined_log_entries.append(f"SUMMARY:\n")
        combined_log_entries.append(f"  ⤷ Overall Status: {overall_status.value}\n")
        combined_log_entries.append(f"  ⤷ Duration: {processing_duration:.2f}s\n")
        combined_log_entries.append(f"  ⤷ Total Databases: {len(db_results)}\n")
        combined_log_entries.append(f"  ⤷ Successful: {successful_count}\n")
        combined_log_entries.append(f"  ⤷ Failed: {failed_count}\n")
        combined_log_entries.append(f"  ⤷ Warnings: {warning_count}\n")
        combined_log_entries.append(f"  ⤷ Files Changed: {len(self.have_changed_files)}\n")
        combined_log_entries.append(f"  ⤷ Files Saved: {1 if save_result and save_result['status'] == ProcessingStatus.SUCCESS.value else 0}\n")
        combined_log_entries.append(f"\n{'='*80}\n")
        
        # Combine all log entries
        full_log = "".join(combined_log_entries)
        self._write_log_to_file(full_log, "data_loader_master_log.txt")

        # Create comprehensive execution information
        execution_info = AgentExecutionInfo(
            agent_id=AgentType.DATA_LOADER.value,
            status=overall_status.value,
            summary={
                "total_databases": len(db_results),
                "successful": successful_count,
                "failed": failed_count,
                "warnings": warning_count,
                "changed_files": len(self.have_changed_files),
                "files_saved": 1 if save_result and save_result['status'] == ProcessingStatus.SUCCESS.value else 0
            },
            details=results,
            healing_actions=self._get_healing_actions(results),
            trigger_agents=self._get_trigger_agents(results),
            metadata={
                "processing_duration_seconds": processing_duration,
                "processing_start_time": start_time.isoformat(),
                "processing_end_time": end_time.isoformat(),
                "memory_usage": self._get_memory_usage(),
                "disk_usage": self._get_disk_usage(),
                "log_entries": full_log,
                "log_entry_count": len(combined_log_entries)
            }
        )

        self.logger.info("✅ Process finished!!!")

        return execution_info

    def _process_database(self, db_name: str, db_type: str) -> Dict[str, Any]:
        """
        Process a single database with comprehensive error handling and logging.
        
        Args:
            db_name: Name of the database to process
            db_type: Type of database (static or dynamic)
            
        Returns:
            Dict containing processing results, status information, and log entries
        """
        
        # Initialize log entries for this database processing
        log_entries = []
        start_timestamp = datetime.now()
        timestamp_str = start_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        log_entries.append(f"[{timestamp_str}] Processing database: {db_name} (type: {db_type})\n")

        try:
            # Get existing path from annotations
            db_existing_path = self.path_annotation.get(db_name, "")
            if db_existing_path:
                log_entries.append(f"  ⤷ Found existing path: {db_existing_path}\n")
            else:
                log_entries.append(f"  ⤷ No existing path found - treating as new database\n")

            # Load current data based on database type
            load_start = datetime.now()
            if db_type == 'dynamicDB':
                log_entries.append(f"  ⤷ Loading dynamic database data...\n")
                current_result = self._load_dynamic_db(db_name, db_type)
            else:
                log_entries.append(f"  ⤷ Loading static database data...\n")
                current_result = self._load_static_db(db_name, db_type)
            
            load_duration = (datetime.now() - load_start).total_seconds()
            log_entries.append(f"  ⤷ Load completed in {load_duration:.2f}s\n")

            # Check if current data loading was successful
            if current_result['status'] != ProcessingStatus.SUCCESS.value:
                log_entries.append(f"  ⤷ ❌ Failed to load current data: {current_result.get('error_message', 'Unknown error')}\n")
                current_result['log_entries'] = "".join(log_entries)
                return current_result

            current_df = current_result['dataframe']
            log_entries.append(f"  ⤷ ✓ Loaded {len(current_df)} records from current source\n")

            # Load existing data for comparison
            log_entries.append(f"  ⤷ Loading existing data for comparison...\n")
            existing_result = self._load_existing_df(db_existing_path)
            
            if existing_result['status'] != ProcessingStatus.SUCCESS.value:
                # If can't load existing, treat as new data
                existing_df = pd.DataFrame()
                warnings = [existing_result['error_message']]
                log_entries.append(f"  ⤷ ⚠ Could not load existing data: {existing_result['error_message']}\n")
                log_entries.append(f"  ⤷ Treating as new database with no existing data\n")
            else:
                existing_df = existing_result['dataframe']
                warnings = []
                log_entries.append(f"  ⤷ ✓ Loaded {len(existing_df)} records from existing file\n")

            # Compare current and existing dataframes to detect changes
            log_entries.append(f"  ⤷ Comparing current vs existing data...\n")
            comparison_result = self._compare_dataframes(current_df, existing_df)
            
            if comparison_result['status'] != ProcessingStatus.SUCCESS.value:
                log_entries.append(f"  ⤷ ❌ Comparison failed: {comparison_result['error_message']}\n")
                
                # Local healing - attempt rollback to backup
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.HASH_COMPARISON_ERROR, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)
                
                log_entries.append(f"  ⤷ Initiated {len(updated_recovery_actions)} recovery action(s)\n")

                return {
                    "database_name": db_name,
                    "database_type": db_type,
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.HASH_COMPARISON_ERROR.value,
                    "error_message": comparison_result['error_message'],
                    "recovery_actions": updated_recovery_actions,
                    "records_processed": 0,
                    "data_updated": False,
                    "log_entries": "".join(log_entries)
                }

            # Determine if data has been updated
            data_updated = not comparison_result['dataframes_equal']
            
            if data_updated:
                log_entries.append(f"  ⤷ ✓ Data has changed - flagged for saving\n")
            else:
                log_entries.append(f"  ⤷ ✓ No changes detected - data is up to date\n")
            
            # Calculate processing duration
            processing_duration = (datetime.now() - start_timestamp).total_seconds()
            end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entries.append(f"[{end_timestamp}] Completed processing {db_name} in {processing_duration:.2f}s\n")

            # Return successful processing result
            return {
                "database_name": db_name,
                "database_type": db_type,
                "status": ProcessingStatus.SUCCESS.value,
                "records_processed": len(current_df),
                "data_updated": data_updated,
                "dataframe": current_df,
                "existing_path": db_existing_path,
                "warnings": warnings,
                "recovery_actions": [],
                "log_entries": "".join(log_entries)
            }

        except Exception as e:
            # Handle unexpected errors during processing
            error_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entries.append(f"[{error_timestamp}] ❌ UNEXPECTED ERROR in {db_name}: {str(e)}\n")
            
            self.logger.error(f"Unexpected error processing {db_name}: {e}")

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.DATA_CORRUPTION, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)
            
            log_entries.append(f"  ⤷ Initiated {len(updated_recovery_actions)} recovery action(s)\n")

            return {
                "database_name": db_name,
                "database_type": db_type,
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.DATA_CORRUPTION.value,
                "error_message": str(e),
                "recovery_actions": updated_recovery_actions,
                "records_processed": 0,
                "data_updated": False,
                "log_entries": "".join(log_entries)
            }

    def _load_dynamic_db(self, db_name: str, db_type: str) -> Dict[str, Any]:
        
        """
        Load dynamic database file (parquet format).
        
        Args:
            db_name: Name of the database
            db_type: Type of database
            
        Returns:
            Dict containing loading results or error information
        """

        try:
            # Get the current path for the dynamic database
            db_current_path = self.databaseSchemas_data[db_type][db_name]['path']

            # Check if file exists
            if not os.path.exists(db_current_path):

                # Local healing - attempt rollback to backup
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

                return {
                    "status": ProcessingStatus.ERROR.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Dynamic DB file not found: {db_current_path}",
                    "recovery_actions": updated_recovery_actions,
                }

            # Load parquet file
            df = pd.read_parquet(db_current_path)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df,
                "file_path": db_current_path
            }

        except Exception as e:

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read dynamic DB {db_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _load_static_db(self, db_name: str, db_type: str) -> Dict[str, Any]:
        
        """
        Load and process static database file (Excel format).
        
        Args:
            db_name: Name of the database
            db_type: Type of database
            
        Returns:
            Dict containing loading results or error information
        """

        try:
            # Process static database using the static method
            df = self._process_data(db_name, db_type, self.databaseSchemas_data)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df
            }

        except Exception as e:

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.SCHEMA_MISMATCH, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.SCHEMA_MISMATCH.value,
                "error_message": f"Failed to process static DB {db_name}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _load_existing_df(self, file_path: str) -> Dict[str, Any]:
        
        """
        Load existing dataframe from file for comparison purposes.
        
        Args:
            file_path: Path to the existing dataframe file
            
        Returns:
            Dict containing the loaded dataframe or error information
        """

        try:
            # Check if file path exists
            if not file_path or not os.path.exists(file_path):

                # Local healing - attempt rollback to backup
                recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_NOT_FOUND, [])
                updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

                return {
                    "status": ProcessingStatus.WARNING.value,
                    "error_type": ErrorType.FILE_NOT_FOUND.value,
                    "error_message": f"Existing file not found: {file_path}",
                    "recovery_actions": updated_recovery_actions,
                    "dataframe": pd.DataFrame()
                }

            # Load existing parquet file
            df = pd.read_parquet(file_path)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframe": df
            }

        except Exception as e:

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.FILE_READ_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

            return {
                "status": ProcessingStatus.WARNING.value,
                "error_type": ErrorType.FILE_READ_ERROR.value,
                "error_message": f"Failed to read existing file {file_path}: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "dataframe": pd.DataFrame()
            }

    def _compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
        
        """
        Compare two dataframes to detect changes.
        
        Args:
            df1: First dataframe (current data)
            df2: Second dataframe (existing data)
            
        Returns:
            Dict containing comparison results
        """

        try:
            # Use fast hash-based comparison
            are_equal = self._dataframes_equal_fast(df1, df2)

            return {
                "status": ProcessingStatus.SUCCESS.value,
                "dataframes_equal": are_equal
            }

        except Exception as e:

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.HASH_COMPARISON_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)

            return {
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.HASH_COMPARISON_ERROR.value,
                "error_message": f"Failed to compare dataframes: {str(e)}",
                "recovery_actions": updated_recovery_actions,
            }

    def _save_changed_files(self) -> Dict[str, Any]:
        """
        Save files that have changed with versioning support.
        
        Returns:
            Dict containing save operation results with detailed log entries
        """
        
        # Initialize log entries list
        log_entries = []
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Check if there are any changes to save
            if not self.have_changed_files:
                log_entries.append(f"[{timestamp_str}] No changes detected - skipping save operation\n")
                
                return {
                    "operation": "file_save",
                    "status": ProcessingStatus.SUCCESS.value,
                    "message": "No changes detected - no files to save",
                    "files_saved": 0,
                    "log_entries": "".join(log_entries)
                }

            # Log detected changes
            log_entries.append(f"[{timestamp_str}] Starting file save operation\n")
            log_entries.append(f"  ⤷ Detected changes in {len(self.have_changed_files)} file(s): {list(self.have_changed_files.keys())}\n")
            
            self.logger.debug("Detect changes: {}", [(k, v.columns) for k, v in self.have_changed_files.items()])

            # Save files using the existing versioning method
            output_exporting_log = self.save_output_with_versioning(
                self.have_changed_files,
                self.path_annotation,
                self.output_dir
            )
            
            # Combine log entries
            log_entries.append(output_exporting_log)
            log_entries.append(f"[{timestamp_str}] File save operation completed successfully\n")
            
            combined_log = "".join(log_entries)

            return {
                "operation": "file_save",
                "status": ProcessingStatus.SUCCESS.value,
                "files_saved": len(self.have_changed_files),
                "saved_files": list(self.have_changed_files.keys()),
                "output_directory": str(self.output_dir),
                "log_entries": combined_log
            }

        except Exception as e:
            # Handle save errors
            error_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entries.append(f"[{error_timestamp}] ❌ ERROR: Failed to save changed files: {str(e)}\n")
            
            self.logger.error(f"Failed to save changed files: {e}")

            # Local healing - attempt rollback to backup
            recovery_actions = self.healing_config.recovery_actions.get(ErrorType.PARQUET_SAVE_ERROR, [])
            updated_recovery_actions = check_annotation_paths_and_update_status(recovery_actions, self.config.annotation_path)
            
            log_entries.append(f"  ⤷ Initiated recovery actions: {len(updated_recovery_actions)} action(s)\n")

            return {
                "operation": "file_save",
                "status": ProcessingStatus.ERROR.value,
                "error_type": ErrorType.PARQUET_SAVE_ERROR.value,
                "error_message": f"Failed to save files: {str(e)}",
                "recovery_actions": updated_recovery_actions,
                "files_saved": 0,
                "log_entries": "".join(log_entries)
            }

    def _get_healing_actions(self, results: List[Dict[str, Any]]) -> List[str]:
        
        """
        Determine healing actions based on processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            List of healing actions to be taken
        """

        healing_actions = set()

        for result in results:
            if result['status'] == ProcessingStatus.ERROR.value:
                # Add recovery actions for errors
                healing_actions.update(result.get('recovery_actions', []))
            elif result['status'] == ProcessingStatus.PARTIAL_SUCCESS.value:
                # Retry processing for partial success
                healing_actions.add(RecoveryAction.RETRY_PROCESSING.value)
            elif result['status'] == ProcessingStatus.WARNING.value:
                # Trigger manual review for warnings
                healing_actions.add(RecoveryAction.TRIGGER_MANUAL_REVIEW.value)

        return list(healing_actions)

    def _get_trigger_agents(self, results: List[Dict[str, Any]]) -> List[str]:
        
        """
        Determine which downstream agents to trigger based on processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            List of agent IDs to trigger
        """

        trigger_agents = []

        for result in results:
            if result['status'] == ProcessingStatus.SUCCESS.value and result.get('data_updated'):
                # Trigger downstream agents when data is updated
                trigger_list = self.healing_config.trigger_on_status.get(ProcessingStatus.SUCCESS, [])
                trigger_agents.extend([agent.value for agent in trigger_list])
            elif result['status'] == ProcessingStatus.ERROR.value:
                # Trigger admin notification
                trigger_list = self.healing_config.trigger_on_status.get(ProcessingStatus.ERROR, [])
                trigger_agents.extend([agent.value for agent in trigger_list])

        return list(set(trigger_agents))  # Remove duplicates

    def _get_memory_usage(self) -> Dict[str, Any]:
        
        """
        Get current memory usage information.
        
        Returns:
            Dict containing memory usage statistics
        """

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
        
        """
        Get disk usage information for the output directory.
        
        Returns:
            Dict containing disk usage statistics
        """

        try:
            # Calculate total size of output directory
            output_size = 0
            if self.output_dir.exists():
                for file_path in self.output_dir.rglob("*.parquet"):
                    output_size += file_path.stat().st_size

            # Convert to MB
            output_size_mb = output_size / 1024 / 1024
            available_space_mb = shutil.disk_usage(self.output_dir).free / 1024 / 1024

            return {
                "output_directory_mb": output_size_mb,
                "available_space_mb": available_space_mb
            }
        except:
            return {"output_directory_mb": 0, "available_space_mb": 0}

    # Static methods for data processing and comparison
    @staticmethod
    def _dataframes_equal_fast(df1, df2):
        
        """
        Fast comparison of dataframes using hash-based approach.
        
        Args:
            df1: First dataframe
            df2: Second dataframe
            
        Returns:
            Boolean indicating whether dataframes are equal
        """

        # Quick shape comparison
        if df1.shape != df2.shape:
            return False

        # Hash-based comparison for performance
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
        
        """
        Save dataframes with versioning support and file management.
        
        Args:
            data: Dictionary mapping database names to dataframes
            path_annotation: Dictionary tracking file paths
            output_dir: Output directory path
            file_format: File format for saving (default: parquet)
        """

        # Validate input data structure
        if not isinstance(data, dict):
            logger.error("❌ Expected data to be a dict[str, pd.DataFrame] but got: {}", type(data))
            raise TypeError(f"Expected data to be a dict[str, pd.DataFrame] but got: {type(data)}")

        # Validate dictionary contents
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
                logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
                raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")

        # Set up directory structure
        output_dir = Path(output_dir)
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        # Create necessary directories
        newest_dir = output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = output_dir / "historical_db"
        historical_dir.mkdir(parents=True, exist_ok=True)
        annotations_path = newest_dir / "path_annotations.json"

        # Move old files to historical directory
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

        # Save new files with timestamp
        try:
            for db_name, df in data.items():
                timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
                new_filename = f"{timestamp_file}_{db_name}.{file_format}"
                new_path = newest_dir / new_filename

                # Save dataframe as parquet
                df.to_parquet(new_path,
                              engine='pyarrow',
                              compression='snappy',
                              index=False)
                
                # Update path annotation
                path_annotation[db_name] = str(new_path)
                log_entries.append(f"  ⤷ Saved new file: {new_path}\n")
                logger.info("Saved new file: {}", new_path)
        except Exception as e:
            logger.error("Failed to save file {}: {}", new_path, e)
            raise OSError(f"Failed to save file {new_path}: {e}")

        # Update path annotations file
        try:
            with open(annotations_path, "w", encoding="utf-8") as f:
                json.dump(path_annotation, f, ensure_ascii=False, indent=4)
            logger.info("Updated path annotations {} with {}", annotations_path, path_annotation)
        except Exception as e:
            logger.error("Failed to update path annotations {}: {}", annotations_path, e)
            raise OSError(f"Failed to update annotation file {annotations_path}: {e}")
        
        return "".join(log_entries)

    @staticmethod
    def _process_data(db_name, db_type, databaseSchemas_data):

        """
        Process static database data with data cleaning and type conversion.
        
        Args:
            db_name: Name of the database
            db_type: Type of database
            databaseSchemas_data: Database schema configuration
            
        Returns:
            Processed pandas DataFrame
        """

        def check_null_str(df):

            """
            Check for string values that should be treated as null/NaN.
            
            Args:
                df: Input dataframe
                
            Returns:
                List of suspect values found in the dataframe
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
            Safely convert values to string format, handling NaN values.
            
            Args:
                x: Value to convert
                
            Returns:
                Converted string value or original NaN
            """

            if pd.isna(x):
                return x
            if isinstance(x, (int, float)) and not pd.isna(x):
                return str(int(x))
            return str(x)

        # Special cases that need string conversion
        spec_cases = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']

        # Load Excel file
        db_path = databaseSchemas_data[db_type][db_name]['path']
        try:
            df = pd.read_excel(db_path)
        except Exception as e:
            logger.error("❌ Failed to read Excel at {}: {}", db_path, e)
            raise OSError(f"❌ Failed to read Excel at {db_path}: {e}")

        # Handle special cases with safe conversion
        for c in spec_cases:
            try:
                df[c] = df[c].map(safe_convert)
            except:
                pass
        
        # Apply data types from schema
        df = df.astype(databaseSchemas_data[db_type][db_name]['dtypes'])

        # Clean null-like string values
        df.replace(check_null_str(df), pd.NA, inplace=True)
        df.fillna(pd.NA, inplace=True)
        
        return df
    
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