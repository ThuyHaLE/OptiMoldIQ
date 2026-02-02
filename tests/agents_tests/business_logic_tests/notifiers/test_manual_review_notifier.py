# tests/agents_tests/business_logic/notifiers/test_manual_review_notifier.py

import pytest
from pathlib import Path
import json
from datetime import datetime

from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    Priority,
    ErrorType,
)
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
)
from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import (
    ManualReviewNotifier,
)


class TestManualReviewNotifier:
    """Test suite for ManualReviewNotifier class."""

    # ============================================
    # FIXTURES
    # ============================================

    @pytest.fixture
    def sample_error_result(self):
        """Create a sample error result for testing."""
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=ErrorType.SCHEMA_MISMATCH,
            error_message="Schema validation failed - missing required fields",
            metadata={"expected_fields": ["id", "name"], "missing": ["name"]},
        )

    @pytest.fixture
    def sample_success_result(self):
        return DataProcessingReport(
            status=ProcessingStatus.SUCCESS,
            data={"test": "data"},
            error_type=ErrorType.NONE,
            error_message="",
            metadata={},
        )

    @pytest.fixture
    def global_manual_review_action(self):
        """GLOBAL + TRIGGER_MANUAL_REVIEW + PENDING action (should trigger notification)."""
        return RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

    @pytest.fixture
    def local_manual_review_action(self):
        """LOCAL + TRIGGER_MANUAL_REVIEW + PENDING action (should NOT trigger)."""
        return RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.LOCAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

    @pytest.fixture
    def global_rollback_action(self):
        """GLOBAL + ROLLBACK + PENDING action (should NOT trigger)."""
        return RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.ROLLBACK_TO_BACKUP,
            status=ProcessingStatus.PENDING,
        )

    @pytest.fixture
    def global_manual_review_success(self):
        """GLOBAL + TRIGGER_MANUAL_REVIEW + SUCCESS action (already processed)."""
        return RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.SUCCESS,
        )

    @pytest.fixture
    def temp_notification_log(self, tmp_path):
        """Create a temporary notification log path."""
        return tmp_path / "test_notifications.log"

    @pytest.fixture
    def notification_config(self, temp_notification_log):
        """Create notification config with temp log path."""
        return {"log_path": str(temp_notification_log)}

    # ============================================
    # INITIALIZATION TESTS
    # ============================================

    def test_initialization_basic(
        self, sample_error_result, global_manual_review_action
    ):
        """Test basic initialization without config."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        assert notifier.data_processing_result == sample_error_result
        assert len(notifier.recovery_actions) == 1
        assert notifier.notification_config == {}
        assert notifier.notification_log_path == Path(
            "logs/manual_review_notifications.log"
        )

    def test_initialization_with_config(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        temp_notification_log,
    ):
        """Test initialization with custom config."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        assert notifier.notification_config == notification_config
        assert notifier.notification_log_path == temp_notification_log

    def test_initialization_creates_log_directory(
        self, sample_error_result, global_manual_review_action, tmp_path
    ):
        """Test that initialization creates parent directories for log file."""
        nested_log = tmp_path / "nested" / "dir" / "test.log"
        config = {"log_path": str(nested_log)}

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=config,
        )

        assert nested_log.parent.exists()

    # ============================================
    # NOTIFICATION QUEUE TESTS
    # ============================================

    def test_process_notification_queues_global_manual_review_pending(
        self, sample_error_result, global_manual_review_action
    ):
        """Test that GLOBAL + MANUAL_REVIEW + PENDING triggers notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        queues = notifier._process_notification_queues()

        assert len(queues) == 1
        trigger, decision = queues[0]
        assert trigger is True
        assert decision.scale == ProcessingScale.GLOBAL
        assert decision.action == RecoveryAction.TRIGGER_MANUAL_REVIEW
        assert decision.status == ProcessingStatus.PENDING

    def test_process_notification_queues_local_does_not_trigger(
        self, sample_error_result, local_manual_review_action
    ):
        """Test that LOCAL scale does NOT trigger notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[local_manual_review_action],
        )

        queues = notifier._process_notification_queues()

        trigger, decision = queues[0]
        assert trigger is False
        assert decision.scale == ProcessingScale.LOCAL

    def test_process_notification_queues_wrong_action_does_not_trigger(
        self, sample_error_result, global_rollback_action
    ):
        """Test that non-MANUAL_REVIEW action does NOT trigger notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_rollback_action],
        )

        queues = notifier._process_notification_queues()

        trigger, decision = queues[0]
        assert trigger is False
        assert decision.action == RecoveryAction.ROLLBACK_TO_BACKUP

    def test_process_notification_queues_already_processed_does_not_trigger(
        self, sample_error_result, global_manual_review_success
    ):
        """Test that already processed action does NOT trigger notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_success],
        )

        queues = notifier._process_notification_queues()

        trigger, decision = queues[0]
        assert trigger is False
        assert decision.status == ProcessingStatus.SUCCESS

    def test_process_notification_queues_multiple_actions(
        self,
        sample_error_result,
        global_manual_review_action,
        local_manual_review_action,
        global_rollback_action,
    ):
        """Test queue processing with multiple mixed actions."""
        actions = [
            global_manual_review_action,  # Should trigger
            local_manual_review_action,  # Should NOT trigger
            global_rollback_action,  # Should NOT trigger
        ]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result, recovery_actions=actions
        )

        queues = notifier._process_notification_queues()

        assert len(queues) == 3

        # First action should trigger
        trigger0, _ = queues[0]
        assert trigger0 is True

        # Second and third should not trigger
        trigger1, _ = queues[1]
        assert trigger1 is False

        trigger2, _ = queues[2]
        assert trigger2 is False

    def test_process_notification_queues_creates_copies(
        self, sample_error_result, global_manual_review_action
    ):
        """Test that queue processing creates copies of decisions."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        queues = notifier._process_notification_queues()
        _, decision_copy = queues[0]

        # Modify copy
        decision_copy.status = ProcessingStatus.SUCCESS

        # Original should remain unchanged
        assert global_manual_review_action.status == ProcessingStatus.PENDING

    # ============================================
    # BUILD NOTIFICATION DATA TESTS
    # ============================================

    def test_build_notification_data_structure(
        self, sample_error_result, global_manual_review_action
    ):
        """Test notification data has required fields."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        notification_data = notifier._build_notification_data(
            global_manual_review_action
        )

        # Check required fields
        assert "timestamp" in notification_data
        assert "priority" in notification_data
        assert "scale" in notification_data
        assert "action" in notification_data
        assert "error_type" in notification_data
        assert "error_message" in notification_data
        assert "validation_status" in notification_data
        assert "metadata" in notification_data
        assert "requires_immediate_attention" in notification_data

    def test_build_notification_data_values(
        self, sample_error_result, global_manual_review_action
    ):
        """Test notification data contains correct values."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        notification_data = notifier._build_notification_data(
            global_manual_review_action
        )

        assert notification_data["priority"] == "HIGH"
        assert notification_data["scale"] == "global"
        assert notification_data["action"] == "trigger_manual_review"
        assert notification_data["error_type"] == "schema_mismatch"
        assert (
            notification_data["error_message"]
            == "Schema validation failed - missing required fields"
        )
        assert notification_data["validation_status"] == "error"
        assert notification_data["metadata"] == {
            "expected_fields": ["id", "name"],
            "missing": ["name"],
        }

    def test_build_notification_data_high_priority_requires_attention(
        self, sample_error_result
    ):
        """Test that HIGH priority requires immediate attention."""
        action = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result, recovery_actions=[action]
        )

        notification_data = notifier._build_notification_data(action)
        assert notification_data["requires_immediate_attention"] is True

    def test_build_notification_data_critical_priority_requires_attention(
        self, sample_error_result
    ):
        """Test that CRITICAL priority requires immediate attention."""
        action = RecoveryDecision(
            priority=Priority.CRITICAL,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result, recovery_actions=[action]
        )

        notification_data = notifier._build_notification_data(action)
        assert notification_data["requires_immediate_attention"] is True

    def test_build_notification_data_low_priority_no_immediate_attention(
        self, sample_error_result
    ):
        """Test that LOW priority does NOT require immediate attention."""
        action = RecoveryDecision(
            priority=Priority.LOW,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result, recovery_actions=[action]
        )

        notification_data = notifier._build_notification_data(action)
        assert notification_data["requires_immediate_attention"] is False

    def test_build_notification_data_medium_priority_no_immediate_attention(
        self, sample_error_result
    ):
        """Test that MEDIUM priority does NOT require immediate attention."""
        action = RecoveryDecision(
            priority=Priority.MEDIUM,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result, recovery_actions=[action]
        )

        notification_data = notifier._build_notification_data(action)
        assert notification_data["requires_immediate_attention"] is False

    def test_build_notification_data_timestamp_format(
        self, sample_error_result, global_manual_review_action
    ):
        """Test that timestamp is in ISO format."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        notification_data = notifier._build_notification_data(
            global_manual_review_action
        )

        # Verify timestamp can be parsed as ISO format
        timestamp = notification_data["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_build_notification_data_includes_catalog_info(
        self, sample_error_result, global_manual_review_action
    ):
        """Test that notification includes error and action catalog information."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
        )

        notification_data = notifier._build_notification_data(
            global_manual_review_action
        )

        # Should include catalog details if available
        # (This test assumes ERROR_CATALOG and RECOVERY_ACTION_CATALOG are defined)
        if "error_details" in notification_data:
            assert isinstance(notification_data["error_details"], dict)

        if "action_details" in notification_data:
            assert isinstance(notification_data["action_details"], dict)

    # ============================================
    # LOG NOTIFICATION TESTS
    # ============================================

    def test_log_notification_creates_file(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        temp_notification_log,
    ):
        """Test that logging creates notification file."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        notification_data = {
            "global": notifier._build_notification_data(global_manual_review_action)
        }

        result = notifier._log_notification(notification_data)

        assert result is True
        assert temp_notification_log.exists()

    def test_log_notification_content(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        temp_notification_log,
    ):
        """Test that logged notification contains expected content."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        notification_data = {
            "global": notifier._build_notification_data(global_manual_review_action)
        }

        notifier._log_notification(notification_data)

        content = temp_notification_log.read_text(encoding="utf-8")

        # Check that key information is in the log
        assert "schema_mismatch" in content
        assert "HIGH" in content
        assert "global" in content

    def test_log_notification_handles_invalid_data(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        monkeypatch,
    ):
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        # Mock DictBasedReportGenerator to raise
        class DummyReporter:
            def __init__(self, *args, **kwargs): ...
            def export_report(self, *_):
                raise ValueError("invalid data")

        monkeypatch.setattr(
            "configs.shared.dict_based_report_generator.DictBasedReportGenerator",
            DummyReporter,
            raising=False,
        )

        result = notifier._log_notification(None)
        assert result is False

    # ============================================
    # SEND NOTIFICATION TESTS
    # ============================================

    def test_send_notification_calls_log(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        temp_notification_log,
    ):
        """Test that send_notification calls log notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        result = notifier._send_notification()

        assert result is True
        assert temp_notification_log.exists()

    def test_send_notification_builds_data_for_all_actions(
        self,
        sample_error_result,
        global_manual_review_action,
        local_manual_review_action,
        notification_config,
        temp_notification_log,
    ):
        """Test that send_notification builds data for ALL recovery actions."""
        actions = [global_manual_review_action, local_manual_review_action]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=actions,
            notification_config=notification_config,
        )

        result = notifier._send_notification()

        assert result is True

        # Check log contains both GLOBAL and LOCAL data
        content = temp_notification_log.read_text(encoding="utf-8")
        assert "global" in content
        assert "local" in content

    # ============================================
    # NOTIFY METHOD TESTS (Main workflow)
    # ============================================

    def test_notify_updates_status_to_success(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
    ):
        """Test that notify() updates status from PENDING to SUCCESS."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.SUCCESS

    def test_notify_skips_non_matching_actions(
        self,
        sample_error_result,
        global_manual_review_action,
        local_manual_review_action,
        notification_config,
    ):
        """Test that notify() only processes matching actions."""
        actions = [
            local_manual_review_action,  # LOCAL - should remain PENDING
            global_manual_review_action,  # GLOBAL - should become SUCCESS
        ]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=actions,
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        # First action (LOCAL) should remain PENDING
        assert updated_actions[0].status == ProcessingStatus.PENDING

        # Second action (GLOBAL) should be SUCCESS
        assert updated_actions[1].status == ProcessingStatus.SUCCESS

    def test_notify_preserves_all_actions(
        self,
        sample_error_result,
        global_manual_review_action,
        local_manual_review_action,
        global_rollback_action,
        notification_config,
    ):
        """Test that notify() returns ALL actions, not just processed ones."""
        actions = [
            global_manual_review_action,
            local_manual_review_action,
            global_rollback_action,
        ]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=actions,
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        assert len(updated_actions) == 3

    def test_notify_with_no_matching_actions(
        self, sample_error_result, local_manual_review_action, notification_config
    ):
        """Test notify() when no actions require notification."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[local_manual_review_action],
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        # Action should remain unchanged
        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.PENDING

    def test_notify_handles_multiple_global_actions(
        self, sample_error_result, notification_config
    ):
        """Test notify() with multiple GLOBAL MANUAL_REVIEW actions."""
        actions = [
            RecoveryDecision(
                priority=Priority.CRITICAL,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.HIGH,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.MEDIUM,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
        ]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=actions,
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        # All should be updated to SUCCESS
        assert all(
            action.status == ProcessingStatus.SUCCESS for action in updated_actions
        )
        assert len(updated_actions) == 3

    def test_notify_handles_notification_failure(
        self,
        sample_error_result,
        global_manual_review_action,
        notification_config,
        monkeypatch,
    ):
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        monkeypatch.setattr(notifier, "_send_notification", lambda: False)

        updated_actions = notifier.notify()

        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.ERROR

    # ============================================
    # EDGE CASES & ERROR HANDLING
    # ============================================

    def test_empty_recovery_actions(self, sample_error_result, notification_config):
        """Test behavior with empty recovery actions list."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[],
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()
        assert len(updated_actions) == 0

    def test_all_actions_already_processed(
        self, sample_error_result, global_manual_review_success, notification_config
    ):
        """Test when all actions are already SUCCESS."""
        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=[global_manual_review_success],
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        # Should remain SUCCESS, no notification sent
        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.SUCCESS

    def test_mixed_priorities(self, sample_error_result, notification_config):
        """Test notify() with mixed priority levels."""
        actions = [
            RecoveryDecision(
                priority=Priority.LOW,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.CRITICAL,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
        ]

        notifier = ManualReviewNotifier(
            data_processing_result=sample_error_result,
            recovery_actions=actions,
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        # Both should be processed regardless of priority
        assert all(
            action.status == ProcessingStatus.SUCCESS for action in updated_actions
        )

    def test_notification_with_success_result(
        self, sample_success_result, global_manual_review_action, notification_config
    ):
        """Test notification can be sent even with SUCCESS validation result."""
        # Edge case: manual review triggered despite success
        # (e.g., warning that requires human verification)
        notifier = ManualReviewNotifier(
            data_processing_result=sample_success_result,
            recovery_actions=[global_manual_review_action],
            notification_config=notification_config,
        )

        updated_actions = notifier.notify()

        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.SUCCESS


# ============================================
# INTEGRATION-LIKE TESTS
# ============================================


class TestManualReviewNotifierIntegration:
    """Integration-style tests for complete notification workflows."""

    def test_complete_notification_workflow(self, tmp_path):
        """Test complete notification workflow from creation to file output."""
        log_path = tmp_path / "notifications" / "test.log"
        config = {"log_path": str(log_path)}

        # Create error result
        error_result = DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=ErrorType.SCHEMA_MISMATCH,
            error_message="Critical schema validation failure",
            metadata={"table": "production_orders", "missing_columns": ["po_number"]},
        )

        # Create multiple recovery actions
        actions = [
            RecoveryDecision(
                priority=Priority.CRITICAL,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.HIGH,
                scale=ProcessingScale.LOCAL,
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.MEDIUM,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                status=ProcessingStatus.PENDING,
            ),
        ]

        # Create notifier and notify
        notifier = ManualReviewNotifier(
            data_processing_result=error_result,
            recovery_actions=actions,
            notification_config=config,
        )

        updated_actions = notifier.notify()

        # Verify results
        assert len(updated_actions) == 3

        # First action (GLOBAL MANUAL_REVIEW) should be SUCCESS
        assert updated_actions[0].status == ProcessingStatus.SUCCESS

        # Second action (LOCAL) should remain PENDING
        assert updated_actions[1].status == ProcessingStatus.PENDING

        # Third action (ROLLBACK) should remain PENDING
        assert updated_actions[2].status == ProcessingStatus.PENDING

        # Verify log file created
        assert log_path.exists()

        # Verify log content
        content = log_path.read_text(encoding="utf-8")
        assert "schema_mismatch" in content.lower()
        assert any(level in content for level in ["CRITICAL", "HIGH", "MEDIUM"])

    def test_notification_preserves_original_actions(self, tmp_path):
        """Test that original recovery actions are not modified."""
        config = {"log_path": str(tmp_path / "test.log")}

        error_result = DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=ErrorType.SCHEMA_MISMATCH,
            error_message="Test error",
            metadata={},
        )

        original_action = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            data_processing_result=error_result,
            recovery_actions=[original_action],
            notification_config=config,
        )

        # Store original status
        original_status = original_action.status

        # Notify (should update returned copy, not original)
        updated_actions = notifier.notify()

        # Original should remain unchanged
        assert original_action.status == original_status

        # Returned copy should be updated
        assert updated_actions[0].status == ProcessingStatus.SUCCESS