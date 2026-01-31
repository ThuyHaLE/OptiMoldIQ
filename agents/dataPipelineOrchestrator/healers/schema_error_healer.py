# agents/dataPipelineOrchestrator/healers/schema_error_healer.py

from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction, RecoveryDecision)
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport
from agents.dataPipelineOrchestrator.validators.schema_validator import SchemaValidator

from typing import List, Tuple
from pathlib import Path
from loguru import logger
import copy

class SchemaErrorHealer:
    """
    Handles schema validation errors by attempting recovery from backup files.
    """
    
    BACKUP_SCHEMA_PATH = "schema_backups/databaseSchemas.json"
    
    def __init__(self, 
                 validation_result: DataProcessingReport,
                 recovery_actions: List[RecoveryDecision]):
        
        self.logger = logger.bind(class_name="SchemaErrorHealer")

        self.validation_result = validation_result

        self.schema_path = Path(self.BACKUP_SCHEMA_PATH)
        self.recovery_actions = recovery_actions
        
        self.logger.info(f"Initialized SchemaErrorHealer")
        self.logger.info(f"  Schema: {self.schema_path}")
    
    def heal(self) -> Tuple[List[RecoveryDecision], 
                                     DataProcessingReport]:
        """
        Process recovery actions and validate backup schema if available.
        
        Returns:
            Tuple of (updated_recovery_actions, final_validation_result)
        """
        final_validation_result = self.validation_result
        healing_queues = self._process_healing_queues()
        
        decisions_to_healing = [
            decision for trigger, decision in healing_queues.values() 
            if trigger
        ]
        
        # Early return if nothing to heal
        if not decisions_to_healing:
            return [decision for _, decision in healing_queues.values()], final_validation_result
        
        # Check backup availability with error handling
        try:
            has_backup_data = self.schema_path.exists()
        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot access backup path: {e}")
            has_backup_data = False
        
        # Process healing
        if not has_backup_data:
            self.logger.warning("No backup file found for rollback")
            for decision in decisions_to_healing:
                decision.status = ProcessingStatus.ERROR
        else:
            # Validate backup schema ONCE
            try:
                self.logger.info("Validating backup schema...")
                backup_validator = SchemaValidator(str(self.schema_path))
                backup_validation = backup_validator.validate()
                
                # Update ALL decisions with same result
                for decision in decisions_to_healing:
                    decision.status = backup_validation.status
                
                # Update final result only if backup validation succeeded
                if backup_validation.status == ProcessingStatus.SUCCESS:
                    self.logger.info("Backup schema validation successful")
                    final_validation_result = backup_validation
                else:
                    self.logger.warning(
                        f"Backup validation failed with status: {backup_validation.status}"
                    )
                        
            except Exception as e:
                self.logger.error(f"Error during healing process: {e}")
                # Set all decisions to ERROR
                for decision in decisions_to_healing:
                    decision.status = ProcessingStatus.ERROR
        
        return [decision for _, decision in healing_queues.values()], final_validation_result


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