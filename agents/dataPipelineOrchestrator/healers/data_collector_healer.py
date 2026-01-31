# agents/dataPipelineOrchestrator/healers/data_collector_healer.py

from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction, RecoveryDecision, ErrorType)
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport
from agents.dataPipelineOrchestrator.utils import load_existing_data

from datetime import datetime
from typing import List, Tuple
from pathlib import Path
from loguru import logger
import copy
import json

class DataCollectorHealer:
    """
    Handles schema validation errors by attempting recovery from backup files.
    """
    
    ANNOTATION_PATH = "schema_backups/path_annotations.json"
    
    def __init__(self, 
                 collector_result: DataProcessingReport,
                 recovery_actions: List[RecoveryDecision]):
        
        self.logger = logger.bind(class_name="DataCollectorHealer")

        self.collector_result = collector_result

        self.annotation_path = Path(self.ANNOTATION_PATH)
        self.recovery_actions = recovery_actions
        
        self.logger.info(f"Initialized DataCollectorHealer")
        self.logger.info(f"  Annotation: {self.annotation_path}")
    
    def heal(self) -> Tuple[List[RecoveryDecision], 
                                             DataProcessingReport]:
        """
        Process recovery actions and load backup database if available.
        
        Returns:
            Tuple of (updated_recovery_actions, final_collector_result)
        """
        final_collector_result = self.collector_result
        healing_queues = self._process_healing_queues()
        
        decisions_to_healing = [
            decision for trigger, decision in healing_queues.values() 
            if trigger
        ]
        
        # Early return if nothing to heal
        if not decisions_to_healing:
            return [decision for _, decision in healing_queues.values()], final_collector_result
        
        # Check backup availability with error handling
        try:
            has_backup_annotation = self.annotation_path.exists()
        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot access backup annotation: {e}")
            has_backup_annotation = False

        # Process healing
        if not has_backup_annotation:
            self.logger.warning("No backup annotation file found for rollback")
            for decision in decisions_to_healing:
                decision.status = ProcessingStatus.ERROR
        else:
            # Load backup databases ONCE
            try:
                self.logger.info("Loading backup annotation path...")
                start_time = datetime.now()

                # Load annotation file
                with open(self.annotation_path, "r") as f:
                    annotation_dict = json.load(f)

                # Load all databases (load_existing_data handles all errors internally)
                databases = {}
                successful_loads = []
                failed_loads = []
                
                for db_name, db_path in annotation_dict.items():
                    db_result = load_existing_data(db_path)
                    databases[db_name] = db_result
                    
                    if db_result.status == ProcessingStatus.SUCCESS:
                        successful_loads.append(db_name)
                    else:
                        failed_loads.append((db_name, db_result.error_message))
                        self.logger.warning(f"Failed to load {db_name}: {db_result.error_message}")

                end_time = datetime.now()

                # Determine overall status
                total_dbs = len(annotation_dict)
                
                # ONLY update when final_collector_result has status SUCCESS
                if successful_loads and not failed_loads:
                    loading_status = ProcessingStatus.SUCCESS
                    self.logger.info(f"Backup database loading successful: {total_dbs} database(s)")
                    
                    final_collector_result = DataProcessingReport(
                        status=loading_status,
                        data=databases,
                        error_type=ErrorType.NONE,
                        error_message="",
                        metadata={
                            "total_database": total_dbs,
                            "successful": len(successful_loads),
                            "failed": 0,
                            "databases": successful_loads,
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "processing_duration": f"{(end_time - start_time).total_seconds():.2f}s",
                            "log": "Backup database loading successful"
                        }
                    )
                else:
                    # If there is any failed → DO NOT update final_collector_result
                    loading_status = ProcessingStatus.ERROR
                    error_messages = [f"{name}: {msg}" for name, msg in failed_loads]
                    self.logger.error(
                        f"Backup loading failed: {len(successful_loads)}/{total_dbs} successful. "
                        f"Errors: {'; '.join(error_messages)}"
                    )
                
                # Update ALL decisions with same result
                for decision in decisions_to_healing:
                    decision.status = loading_status

            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in annotation file: {e}")
                for decision in decisions_to_healing:
                    decision.status = ProcessingStatus.ERROR
                    
            except Exception as e:
                self.logger.error(f"Error during healing process: {e}")
                for decision in decisions_to_healing:
                    decision.status = ProcessingStatus.ERROR
        
        return [decision for _, decision in healing_queues.values()], final_collector_result
    
    def _process_healing_queues(self):
        """
        Process recovery actions and organize them into healing queues.
        
        Creates a dictionary mapping recovery action indices to tuples containing:
        - Boolean flag: True if the action requires immediate healing
        (LOCAL scale + ROLLBACK_TO_BACKUP + PENDING status)
        - RecoveryDecision object: containing detailed recovery action information
        
        Conditions for flag = True (requires immediate healing):
        - scale must be LOCAL (not affect entire system)
        - action must be ROLLBACK_TO_BACKUP
        - status must be PENDING (not yet processed)
        
        Returns:
            Dict[int, Tuple[bool, RecoveryDecision]]: Dictionary where:
                - key: index of recovery action in self.recovery_actions
                - value: tuple (needs_healing, recovery_decision_copy)
        
        Example:
            {
                0: (True, RecoveryDecision(...)),   # LOCAL ROLLBACK_TO_BACKUP, needs healing
                1: (False, RecoveryDecision(...))   # GLOBAL manual review, no healing
            }
        """
        healing_queues = {}  # Đổi tên cho đúng

        for idx, decision in enumerate(self.recovery_actions):
            healing_queues[idx] = (
                (
                    decision.scale == ProcessingScale.LOCAL
                    and decision.action == RecoveryAction.ROLLBACK_TO_BACKUP
                    and decision.status == ProcessingStatus.PENDING
                ),
                copy.copy(decision))

        return healing_queues