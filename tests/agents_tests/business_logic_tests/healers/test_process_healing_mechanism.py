# tests/agents_tests/business_logic_tests/healers/test_process_healing_mechanism.py

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
from dataclasses import dataclass

from agents.dataPipelineOrchestrator.processors.data_pipeline_processor import (
    DataPipelineProcessor,
    DataPipelineResults
)
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport
from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    AgentType,
    ErrorType,
    Priority,
)


class TestProcessHealingMechanism:
    """Test suite for _process_healing_mechanism method"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock SharedSourceConfig"""
        config = Mock()
        config.databaseSchemas_path = "/path/to/schemas.json"
        config.annotation_path = "/path/to/annotations.json"
        config.manual_review_notifications_dir = "/tmp/notifications"
        config.validate_requirements = Mock(return_value=(True, []))
        return config
    
    @pytest.fixture
    def processor(self, mock_config):
        """Create DataPipelineProcessor instance"""
        with patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.os.makedirs'):
            proc = DataPipelineProcessor(mock_config)
            proc.log_entries = []  # Initialize log entries
            return proc
    
    @pytest.fixture
    def failed_result(self):
        """Create a failed DataProcessingReport"""
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=ErrorType.SCHEMA_MISMATCH,
            error_message="Schema validation failed"
        )
    
    @pytest.fixture
    def recovery_actions(self):
        """Create sample recovery actions"""
        return [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.PENDING
            )
        ]
    
    # ==========================================
    # Test Case 1: Successful Local Healing
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_successful_local_healing(self, mock_get_actions, processor, failed_result, recovery_actions):
        """
        Test successful local healing scenario
        
        Expected behavior:
        - Local healer succeeds
        - Returns (True, success_result)
        - Pipeline status updated to SUCCESS
        - No global notification needed
        """
        # Arrange
        mock_get_actions.return_value = recovery_actions
        
        # Mock local healer
        mock_healer = Mock()
        success_result = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"recovered": "data"}
        )
        local_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_healer.return_value.heal.return_value = (local_recovery_actions, success_result)
        
        notification_path = "/tmp/notification.json"
        
        # Act
        healing_succeeded, result = processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path=notification_path,
            local_healer=mock_healer
        )
        
        # Assert
        assert healing_succeeded is True
        assert result.status == ProcessingStatus.SUCCESS
        assert processor.pipeline_result.status == ProcessingStatus.SUCCESS
        assert AgentType.SCHEMA_VALIDATOR.value in processor.pipeline_result.recovery_actions
        
        # Verify log entries
        log_text = '\n'.join(processor.log_entries)
        assert "Local recovery successful" in log_text
        assert "Backup Rollback" in log_text or "BACKUP_ROLLBACK" in log_text
        
        # Verify healer was called correctly
        mock_healer.assert_called_once_with(failed_result, recovery_actions)
    
    # ==========================================
    # Test Case 2: Failed Local Healing -> Global Notification
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier')
    def test_failed_local_healing_with_notification(
        self, 
        mock_notifier_class, 
        mock_get_actions, 
        processor, 
        failed_result, 
        recovery_actions
    ):
        """
        Test failed local healing triggering global notification
        
        Expected behavior:
        - Local healer fails
        - Global notification is created
        - Returns (False, failed_result)
        - Pipeline status updated to ERROR
        """
        # Arrange
        mock_get_actions.return_value = recovery_actions
        
        # Mock local healer - fails
        mock_healer = Mock()
        local_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.ERROR
            )
        ]
        mock_healer.return_value.heal.return_value = (local_recovery_actions, failed_result)
        
        # Mock global notifier
        global_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_notifier = Mock()
        mock_notifier.notify.return_value = global_recovery_actions
        mock_notifier_class.return_value = mock_notifier
        
        notification_path = "/tmp/notification.json"
        
        # Act
        healing_succeeded, result = processor._process_healing_mechanism(
            result_name=AgentType.DATA_COLLECTOR,
            result_data=failed_result,
            notification_path=notification_path,
            local_healer=mock_healer
        )
        
        # Assert
        assert healing_succeeded is False
        assert result.status == ProcessingStatus.ERROR
        assert processor.pipeline_result.status == ProcessingStatus.ERROR
        assert processor.pipeline_result.error_type == ErrorType.SCHEMA_MISMATCH
        
        # Verify notification was created
        mock_notifier_class.assert_called_once()
        call_kwargs = mock_notifier_class.call_args[1]
        assert call_kwargs['data_processing_result'] == failed_result
        assert call_kwargs['recovery_actions'] == local_recovery_actions
        assert call_kwargs['notification_config']['log_path'] == notification_path
        
        # Verify log entries
        log_text = '\n'.join(processor.log_entries)
        assert "Local recovery failed" in log_text or "Local healing FAILED" in log_text
        assert "Manual review" in log_text.lower()
        assert notification_path in log_text
    
    # ==========================================
    # Test Case 3: Recovery Actions Logging
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_recovery_actions_are_logged(self, mock_get_actions, processor, failed_result, recovery_actions):
        """
        Test that all recovery actions are properly logged
        
        Expected behavior:
        - Available actions are logged at start
        - Each action execution is logged with status icon
        - Priority and scale information is included
        """
        # Arrange
        mock_get_actions.return_value = recovery_actions
        
        mock_healer = Mock()
        local_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                status=ProcessingStatus.SUCCESS,
                priority=Priority.CRITICAL
            )
        ]
        success_result = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"recovered": "data"}
        )
        mock_healer.return_value.heal.return_value = (local_recovery_actions, success_result)
        
        # Act
        processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert - Check log entries contain expected information
        log_text = '\n'.join(processor.log_entries)
        
        # Available actions should be logged
        assert "Recovery actions available: 2" in log_text
        assert "BACKUP_ROLLBACK" in log_text or "ROLLBACK_TO_BACKUP" in log_text
        assert "MANUAL_REVIEW" in log_text or "TRIGGER_MANUAL_REVIEW" in log_text
        assert "LOCAL" in log_text
        assert "GLOBAL" in log_text
        
        # Success icon should be present
        assert "✓" in log_text
        
        # Priority should be logged
        assert "Priority:" in log_text or "priority" in log_text.lower()
    
    # ==========================================
    # Test Case 4: Multiple Recovery Actions
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier')
    def test_multiple_recovery_actions(
        self, 
        mock_notifier_class, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test handling of multiple local and global recovery actions
        
        Expected behavior:
        - All local actions are attempted
        - All global actions are logged
        - Recovery actions are stored separately by scale
        """
        # Arrange
        recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP, 
                scale=ProcessingScale.LOCAL, 
                priority=Priority.CRITICAL,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.RETRY_PROCESSING, 
                scale=ProcessingScale.LOCAL, 
                priority=Priority.HIGH,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW, 
                scale=ProcessingScale.GLOBAL, 
                priority=Priority.MEDIUM,
                status=ProcessingStatus.PENDING
            ),
        ]
        mock_get_actions.return_value = recovery_actions
        
        # Multiple local actions - both fail
        local_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.ERROR
            ),
            RecoveryDecision(
                action=RecoveryAction.RETRY_PROCESSING,
                scale=ProcessingScale.LOCAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.ERROR
            ),
        ]
        
        mock_healer = Mock()
        mock_healer.return_value.heal.return_value = (local_recovery_actions, failed_result)
        
        global_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.MEDIUM,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_notifier = Mock()
        mock_notifier.notify.return_value = global_recovery_actions
        mock_notifier_class.return_value = mock_notifier
        
        # Act
        processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        log_text = '\n'.join(processor.log_entries)
        
        # Check that both local actions are in logs
        assert "BACKUP_ROLLBACK" in log_text or "ROLLBACK_TO_BACKUP" in log_text
        assert "RETRY_PROCESSING" in log_text
        assert "MANUAL_REVIEW" in log_text or "TRIGGER_MANUAL_REVIEW" in log_text
        
        # Verify error icons for failed actions
        assert "✗" in log_text
    
    # ==========================================
    # Test Case 5: Pipeline Result Updates
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier')
    def test_pipeline_result_updates(
        self, 
        mock_notifier_class, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test that pipeline_result is properly updated throughout healing process
        
        Expected behavior:
        - recovery_actions dictionary is updated
        - status is updated based on outcome
        - error_type and error_message are set on failure
        """
        # Arrange
        mock_get_actions.return_value = []
        
        mock_healer = Mock()
        local_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.ERROR
            )
        ]
        mock_healer.return_value.heal.return_value = (local_actions, failed_result)
        
        global_actions = [
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_notifier = Mock()
        mock_notifier.notify.return_value = global_actions
        mock_notifier_class.return_value = mock_notifier
        
        # Act
        processor._process_healing_mechanism(
            result_name=AgentType.DATA_COLLECTOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        # Check recovery_actions are stored
        assert AgentType.DATA_COLLECTOR.value in processor.pipeline_result.recovery_actions
        assert processor.pipeline_result.recovery_actions[AgentType.DATA_COLLECTOR.value] == global_actions
        
        # Check error information
        assert processor.pipeline_result.status == ProcessingStatus.ERROR
        assert processor.pipeline_result.error_type == ErrorType.SCHEMA_MISMATCH
        assert "Local healing for DATA_COLLECTOR failed" in processor.pipeline_result.error_message
        assert "Recovery action results" in processor.pipeline_result.error_message
    
    # ==========================================
    # Test Case 6: Different Agent Types
    # ==========================================
    @pytest.mark.parametrize("agent_type", [
        AgentType.SCHEMA_VALIDATOR,
        AgentType.DATA_COLLECTOR,
    ])
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_different_agent_types(
        self, 
        mock_get_actions, 
        processor, 
        failed_result, 
        agent_type
    ):
        """
        Test healing mechanism works for different agent types
        
        Expected behavior:
        - Each agent type is handled correctly
        - Recovery actions are fetched for specific agent
        - Results are stored with correct agent key
        """
        # Arrange
        mock_get_actions.return_value = []
        
        mock_healer = Mock()
        local_actions = []
        success_result = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"recovered": "data"}
        )
        mock_healer.return_value.heal.return_value = (local_actions, success_result)
        
        # Act
        processor._process_healing_mechanism(
            result_name=agent_type,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        mock_get_actions.assert_called_once_with(agent_type, ErrorType.SCHEMA_MISMATCH)
        assert agent_type.value in processor.pipeline_result.recovery_actions
    
    # ==========================================
    # Test Case 7: Error Message Construction
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier')
    def test_error_message_includes_recovery_summary(
        self, 
        mock_notifier_class, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test that error message includes detailed recovery action summary
        
        Expected behavior:
        - Error message contains original error
        - Error message contains recovery action results
        - Both success and failure actions are included
        """
        # Arrange
        mock_get_actions.return_value = []
        
        mock_healer = Mock()
        local_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.ERROR
            )
        ]
        mock_healer.return_value.heal.return_value = (local_actions, failed_result)
        
        global_actions = [
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_notifier = Mock()
        mock_notifier.notify.return_value = global_actions
        mock_notifier_class.return_value = mock_notifier
        
        # Act
        processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        error_msg = processor.pipeline_result.error_message
        assert "Local healing for SCHEMA_VALIDATOR failed" in error_msg
        assert "Schema validation failed" in error_msg  # Original error
        assert "Recovery action results" in error_msg
        assert "MANUAL_REVIEW" in error_msg or "TRIGGER_MANUAL_REVIEW" in error_msg
    
    # ==========================================
    # Test Case 8: Different Error Types
    # ==========================================
    @pytest.mark.parametrize("error_type,agent_type", [
        (ErrorType.FILE_NOT_VALID, AgentType.SCHEMA_VALIDATOR),
        (ErrorType.FILE_NOT_FOUND, AgentType.SCHEMA_VALIDATOR),
        (ErrorType.INVALID_JSON, AgentType.SCHEMA_VALIDATOR),
        (ErrorType.SCHEMA_MISMATCH, AgentType.SCHEMA_VALIDATOR),
        (ErrorType.UNSUPPORTED_DATA_TYPE, AgentType.DATA_COLLECTOR),
        (ErrorType.DATA_PROCESSING_ERROR, AgentType.DATA_COLLECTOR),
    ])
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_different_error_types(
        self, 
        mock_get_actions, 
        processor, 
        error_type,
        agent_type
    ):
        """
        Test healing mechanism handles different error types correctly
        
        Expected behavior:
        - Each error type triggers appropriate recovery actions
        - get_recovery_actions_for_agent_error is called with correct error_type
        """
        # Arrange
        failed_result = DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=error_type,
            error_message=f"{error_type.value} occurred"
        )
        
        mock_recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.PENDING
            )
        ]
        mock_get_actions.return_value = mock_recovery_actions
        
        mock_healer = Mock()
        success_result = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"recovered": "data"}
        )
        # Return actions with updated status
        completed_actions = [
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.SUCCESS
            )
        ]
        mock_healer.return_value.heal.return_value = (completed_actions, success_result)
        
        # Act
        processor._process_healing_mechanism(
            result_name=agent_type,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        mock_get_actions.assert_called_once_with(agent_type, error_type)
    
    # ==========================================
    # Test Case 9: RecoveryDecision Priority Levels
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_recovery_decision_priority_logging(
        self, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test that recovery decisions with different priority levels are logged
        
        Expected behavior:
        - All priority levels (LOW, MEDIUM, HIGH, CRITICAL) are logged
        - Priority information appears in log entries
        """
        # Arrange
        recovery_actions = [
            RecoveryDecision(
                action=RecoveryAction.RETRY_PROCESSING,
                scale=ProcessingScale.LOCAL,
                priority=Priority.LOW,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                scale=ProcessingScale.LOCAL,
                priority=Priority.CRITICAL,
                status=ProcessingStatus.PENDING
            ),
            RecoveryDecision(
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                scale=ProcessingScale.GLOBAL,
                priority=Priority.HIGH,
                status=ProcessingStatus.PENDING
            ),
        ]
        mock_get_actions.return_value = recovery_actions
        
        mock_healer = Mock()
        success_result = DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"recovered": "data"}
        )
        mock_healer.return_value.heal.return_value = ([], success_result)
        
        # Act
        processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        log_text = '\n'.join(processor.log_entries)
        
        # Check that priority information is logged
        assert "Priority:" in log_text or "priority" in log_text.lower()
        
        # At least one of the priorities should be mentioned
        priority_found = any(p in log_text for p in ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        assert priority_found, f"No priority level found in logs:\n{log_text}"
    
    # ==========================================
    # Test Case 10: Empty Recovery Actions
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.ManualReviewNotifier')
    def test_empty_recovery_actions(
        self, 
        mock_notifier_class, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test behavior when no recovery actions are available
        
        Expected behavior:
        - Should still attempt healing
        - Should handle gracefully without actions
        - Notification should still be created on failure
        """
        # Arrange
        mock_get_actions.return_value = []  # No recovery actions available
        
        mock_healer = Mock()
        mock_healer.return_value.heal.return_value = ([], failed_result)
        
        global_recovery_actions = []
        mock_notifier = Mock()
        mock_notifier.notify.return_value = global_recovery_actions
        mock_notifier_class.return_value = mock_notifier
        
        # Act
        healing_succeeded, result = processor._process_healing_mechanism(
            result_name=AgentType.SCHEMA_VALIDATOR,
            result_data=failed_result,
            notification_path="/tmp/test.json",
            local_healer=mock_healer
        )
        
        # Assert
        assert healing_succeeded is False
        assert processor.pipeline_result.status == ProcessingStatus.ERROR
        
        # Verify notification was still attempted
        mock_notifier_class.assert_called_once()
        
        # Check log mentions zero actions
        log_text = '\n'.join(processor.log_entries)
        assert "Recovery actions available: 0" in log_text
    
    # ==========================================
    # BONUS: Test Case 11 - Exception Handling
    # ==========================================
    @patch('agents.dataPipelineOrchestrator.processors.data_pipeline_processor.get_recovery_actions_for_agent_error')
    def test_healer_exception_is_propagated(
        self, 
        mock_get_actions, 
        processor, 
        failed_result
    ):
        """
        Test that exceptions from healer are properly propagated
        
        Expected behavior:
        - If healer raises exception, it should propagate up
        - Or be caught and logged appropriately
        """
        # Arrange
        mock_get_actions.return_value = []
        
        mock_healer = Mock()
        mock_healer.return_value.heal.side_effect = Exception("Healer internal error")
        
        # Act & Assert
        # If implementation doesn't catch exceptions, they should propagate
        with pytest.raises(Exception, match="Healer internal error"):
            processor._process_healing_mechanism(
                result_name=AgentType.SCHEMA_VALIDATOR,
                result_data=failed_result,
                notification_path="/tmp/test.json",
                local_healer=mock_healer
            )