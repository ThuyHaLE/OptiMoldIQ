from pathlib import Path
from typing import Dict, Any
from loguru import logger
from datetime import datetime
from dataclasses import dataclass, field
import os
import json

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig

from agents.dataPipelineOrchestrator.collectors.data_collector import DataCollector
from agents.dataPipelineOrchestrator.validators.schema_validator import SchemaValidator

from agents.dataPipelineOrchestrator.healers.schema_error_healer import SchemaErrorHealer
from agents.dataPipelineOrchestrator.healers.data_collector_healer import DataCollectorHealer

from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    get_recovery_actions_for_agent_error,
    ProcessingStatus, 
    ProcessingScale, 
    RecoveryAction, 
    RecoveryDecision, 
    AgentType,
    ErrorType, 
    )

@dataclass
class DataPipelineResults:
    """Generic output for DataPipelineProcessor"""
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_type: ErrorType = ErrorType.NONE
    error_message: str = ""
    recovery_actions: Dict[str, Any] = field(default_factory=dict)
    schema_data: Any = None
    schema_validation_result: Any = None
    path_annotation: Any = None
    collected_data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
         
class DataPipelineProcessor(ConfigReportMixin):

    """
    Main processor class that coordinates the entire data pipeline process.
    
    This class manages a data pipeline: 
    Collects raw data (Excel) from various sources. 
    Then processes and loads data into the target system

    The processor includes error handling, rollback mechanisms, and notification systems
    to ensure pipeline reliability and proper error reporting.
    """

    # Define requirements
    REQUIRED_FIELDS = {
        'databaseSchemas_path': str,
        'annotation_path': str,
        'manual_review_notifications_dir': str
    }
    
    def __init__(self, config: SharedSourceConfig):
        
        """
        Initialize the DataPipelineProcessor.
        
        Args:
            config: SharedSourceConfig containing processing parameters
            Including:
                - databaseSchemas_path: Path to the database schemas JSON file
                - annotation_path: Path to the data annotations file
                - manual_review_notifications_dir: Default directory for storing healing notifications (if any)
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class-specific binding for better log tracking
        self.logger = logger.bind(class_="DataPipelineProcessor")

        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
        self.config = config

        # Initialize result tracking
        self.pipeline_result = DataPipelineResults()

        # Set up directory paths
        self.manual_review_notifications_dir = Path(self.config.manual_review_notifications_dir)
        os.makedirs(self.manual_review_notifications_dir, exist_ok=True)

    def _process_healing_mechanism(self, 
                                   result_name: AgentType, 
                                   result_data: DataProcessingReport, 
                                   notification_path: str,
                                   local_healer) -> tuple[bool, DataProcessingReport]:
        """
        Execute healing mechanism for failed processing steps.
        
        Implements a two-tier recovery strategy:
        1. Local healing: Attempt automatic recovery (e.g., backup rollback)
        2. Global notification: Alert for manual review if local healing fails
        
        Args:
            result_name: Type of agent that failed (SCHEMA_VALIDATOR or DATA_COLLECTOR)
            result_data: Processing result containing error information
            notification_path: Path to save manual review notification
            local_healer: Healer class to use for local recovery
            
        Returns:
            tuple: (healing_succeeded: bool, recovery_result: DataProcessingReport)
        """

        # Get available recovery actions for this error type
        recovery_actions = get_recovery_actions_for_agent_error(
            result_name,
            result_data.error_type
        )

        recovery_action_results = []

        # Log available recovery actions
        self.log_entries.append(f"Recovery actions available: {len(recovery_actions)}")
        for action in recovery_actions:
            self.log_entries.append(
                f"  - [{action.scale.value.upper()}] {action.action.value} (Priority: {action.priority.name})")
        
        # ==========================================
        # STEP 1: LOCAL HEALING (Automatic Recovery)
        # ==========================================
        # Attempt to recover using backup rollback or other local strategies
        error_healer = local_healer(result_data, recovery_actions)
        local_recovery_actions, recovery_result = error_healer.heal()
        
        # Store recovery actions in pipeline results
        self.pipeline_result.recovery_actions[result_name.value] = local_recovery_actions

        # Log local recovery results
        for action in local_recovery_actions:
            if action.scale == ProcessingScale.LOCAL:
                status_icon = "✓" if action.status == ProcessingStatus.SUCCESS else "✗"
                act_msg = f"  {status_icon} {action.action.value}: {action.status.value}"
                recovery_action_results.append(act_msg)
                self.log_entries.append(act_msg)

        # Check if local healing succeeded
        if recovery_result.status == ProcessingStatus.SUCCESS:
            self.pipeline_result.status = ProcessingStatus.SUCCESS
            self.log_entries.append(f"✓ Local recovery successful for {result_name.value} - using Backup Rollback")
            return True, recovery_result
            
        else:
            # ==========================================
            # STEP 2: GLOBAL NOTIFICATION (Manual Review)
            # ==========================================
            # Local healing failed - create notification for manual intervention
            self.log_entries.append("✗ Local recovery failed - Backup Rollback unavailable or invalid")
        
            from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import ManualReviewNotifier
            notifier = ManualReviewNotifier(
                data_processing_result=recovery_result,
                recovery_actions=local_recovery_actions,
                notification_config={"log_path": notification_path})
            global_recovery_actions = notifier.notify()

            # Update recovery actions with global notification results
            self.pipeline_result.recovery_actions[result_name.value] = global_recovery_actions

            # Log notification results
            for action in global_recovery_actions:
                if action.scale == ProcessingScale.GLOBAL:
                    status_icon = "✓" if action.status == ProcessingStatus.SUCCESS else "✗"
                    act_msg = f"  {status_icon} {action.action.value}: {action.status.value}"
                    recovery_action_results.append(act_msg)
                    self.log_entries.append(act_msg)

            # Update pipeline status - cannot continue without successful healing
            self.pipeline_result.status = ProcessingStatus.ERROR
            self.pipeline_result.error_type = recovery_result.error_type
            recovery_summary = '\n'.join(recovery_action_results)
            self.pipeline_result.error_message = (
                f"Local healing for {result_name.value} failed: {recovery_result.error_message}. "
                f"Recovery action results for {result_name.value}: {recovery_summary}"
            )

            self.log_entries.append(f"⤷ Local healing FAILED for {result_name.value} - Manual review required")
            self.log_entries.append(f"⤷ Notification log for {result_name.value}: {notification_path}")

            return False, recovery_result
        
    def run_pipeline(self) -> DataPipelineResults:
        
        """
        Execute the complete data pipeline with proper error handling and notifications.
        
        Pipeline Phases:
        1. Schema Validation: Validate database schema file
        2. Annotation Validation: Load/create path annotations
        3. Data Collection: Collect data for ALL database types (all-or-nothing)
        
        Returns:
            DataPipelineResults: Complete pipeline execution results
        """

        class_id = "DataPipelineProcessor"
        self.logger.info(f"{class_id} ...")  

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = start_time.strftime("%Y%m%d_%H%M")
        config_header = self._generate_config_report(timestamp_str, 
                                                     required_only=True)
        
        # Initialize log entries
        self.log_entries = [
            config_header,
            f"--Processing Summary--",
            f"⤷ {class_id} results:"
            ]

        # ==========================================
        # PHASE 1: SCHEMA VALIDATION
        # ==========================================
        # Validate the database schema file structure and content
        # This is a single-file validation - if it fails, entire pipeline stops

        # Initialize SchemaValidator
        validator = SchemaValidator(self.config.databaseSchemas_path)

        # Run validate schema
        validation_result = validator.validate()

        # Update validation result into pipeline results
        self.pipeline_result.schema_validation_result = validation_result

        # Log validation results
        self.log_entries.append(f"Validation Status: {validation_result.status.value}")
        if validation_result.error_type:
            self.log_entries.append(f"Error Type: {validation_result.error_type.value}")
            self.log_entries.append(f"Error Message: {validation_result.error_message}")

        # Handle validation result
        if validation_result.status == ProcessingStatus.SUCCESS:
            # Schema is valid - proceed to next phase
            self.pipeline_result.status = ProcessingStatus.SUCCESS
            self.pipeline_result.schema_data = validation_result.data
            self.log_entries.append("⤷ Schema validation: SUCCESS")
        
        else:
            # Schema validation failed - attempt healing
            healing_success, recovery_result = self._process_healing_mechanism(
                result_name=AgentType.SCHEMA_VALIDATOR, 
                result_data=validation_result, 
                notification_path=(
                    f"{self.manual_review_notifications_dir}/{timestamp_file}_"
                    f"{AgentType.SCHEMA_VALIDATOR.value}_manual_review_notification.txt"
                ),
                local_healer=SchemaErrorHealer
            )
            
            if healing_success:
                # Healing succeeded - use recovered schema data
                self.log_entries.append("⤷ Schema validation: HEALING SUCCESS")
                self.pipeline_result.schema_data = recovery_result.data
            else:
                # Healing failed - cannot proceed without valid schema
                self.log_entries.append("⤷ Schema validation: HEALING FAILED")
                self.pipeline_result.metadata['log'] = "\n".join(self.log_entries)
                self.logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {class_id} completed.")
                return self.pipeline_result
        
        self.logger.info("✓ Schema validation successful")

        # ==========================================
        # PHASE 2: DATABASE ANNOTATION VALIDATION
        # ==========================================
        # Load or create path annotations for database files

        # Load existing path annotations if available, otherwise create empty dict
        if os.path.exists(self.config.annotation_path):
            with open(self.config.annotation_path, "r", encoding="utf-8") as f:
                path_annotation = json.load(f)
            self.log_entries.append(f"Loaded existing annotation file: {path_annotation}")
        else:
            path_annotation = {}
            self.log_entries.append("First time for initial - creating new annotation file...")

        # Update databases annotation into pipeline results
        self.pipeline_result.path_annotation = path_annotation
        self.logger.info("✓ Databases annotation validation successful")

        # ==========================================
        # PHASE 3: DATABASE COLLECTION (ALL-OR-NOTHING)
        # ==========================================
        # Collect data from ALL database types (e.g., dynamic_DB, staticDB)
        # CRITICAL: All database types must succeed - if ANY type fails, entire phase fails
        # This is different from schema validation which is single-file

        schema_data = self.pipeline_result.schema_data
        
        # Initialize collected data if None
        if self.pipeline_result.collected_data is None:
            self.pipeline_result.collected_data = {}

        # Track overall success - ALL types must succeed
        all_db_types_succeeded = True
        failed_db_types = []  # Track which types failed for debugging

        # Process each database type independently
        for db_type in schema_data:
            # Initialize DataCollector for this specific database type
            collector = DataCollector(db_type, schema_data.get(db_type, {}))

            self.log_entries.append(f"Data collecting for {db_type}...")
            collector_result = collector.process_data()
            
            # Check if this type needs healing
            needs_healing = collector_result.status != ProcessingStatus.SUCCESS

            if not needs_healing:
                # Collection succeeded for this type
                self.pipeline_result.collected_data[db_type] = collector_result.data
                self.log_entries.append(f"⤷ Data collection ({db_type}): SUCCESS")
            else:
                # Collection failed for this type - attempt healing
                self.log_entries.append(f"⤷ Data collection ({db_type}): FAILED")

                healing_success, recovery_result = self._process_healing_mechanism(
                    result_name=AgentType.DATA_COLLECTOR, 
                    result_data=collector_result, 
                    notification_path=(
                        f"{self.manual_review_notifications_dir}/{timestamp_file}_"
                        f"{AgentType.DATA_COLLECTOR.value}_{db_type}_manual_review_notification.txt"
                    ),
                    local_healer=DataCollectorHealer
                )

                if healing_success:
                    # Healing succeeded for this type
                    self.log_entries.append(f"⤷ Data collection ({db_type}): HEALING SUCCESS")
                    self.pipeline_result.collected_data[db_type] = recovery_result.data
                else:
                    # Healing failed for this type - mark overall failure
                    self.log_entries.append(f"⤷ Data collection ({db_type}): HEALING FAILED")
                    all_db_types_succeeded = False
                    failed_db_types.append(db_type)
        
        # Check if ALL database types succeeded
        if not all_db_types_succeeded:
            # At least one database type failed - entire collection phase fails
            self.pipeline_result.status = ProcessingStatus.ERROR
            self.pipeline_result.error_type = ErrorType.DATA_PROCESSING_ERROR
            self.pipeline_result.error_message = (
                f"Data collection failed for {len(failed_db_types)} database type(s): "
                f"{', '.join(failed_db_types)}"
            )
            
            self.log_entries.append("⤷ Databases collection: HEALING FAILED")
            self.log_entries.append(f"⤷ Failed types: {', '.join(failed_db_types)}")
            
            self.pipeline_result.metadata['failed_db_types'] = failed_db_types
            self.pipeline_result.metadata['log'] = "\n".join(self.log_entries)

            self.logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {class_id} completed.")
            return self.pipeline_result

        self.logger.info("✓ Data collection successful")

        # ==========================================
        # PIPELINE COMPLETION
        # ==========================================
        # Log recovery actions if any were executed
        if self.pipeline_result.recovery_actions:
            self.log_entries.append(f"Recovery actions executed for: {len(self.pipeline_result.recovery_actions)} phases")
        
        self.pipeline_result.metadata['log'] = "\n".join(self.log_entries)

        self.logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {class_id} completed.")
        return self.pipeline_result