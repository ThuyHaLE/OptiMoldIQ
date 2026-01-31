# tests/test_manual_review_notifier.py

import pytest
from pathlib import Path
import json
from datetime import datetime

from agents.dataPipelineOrchestrator.configs.output_formats import (
    ProcessingStatus,
    DataProcessingReport,
    ProcessingScale,
    RecoveryAction,
    RecoveryDecision,
    ErrorType,
    Priority,
)
from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import (
    ManualReviewNotifier,
)


class TestManualReviewNotifier:
    """Test suite for ManualReviewNotifier class."""

    @pytest.fixture
    def sample_validation_result(self):
        """Create a sample validation result for testing."""
        return DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=ErrorType.SCHEMA_MISMATCH,
            error_message="Schema validation failed - missing required fields",
            metadata={"expected_fields": ["id", "name"], "missing": ["name"]},
        )

    @pytest.fixture
    def sample_recovery_actions(self):
        """Create sample recovery actions for testing."""
        return [
            RecoveryDecision(
                priority=Priority.CRITICAL,
                scale=ProcessingScale.LOCAL,
                action=RecoveryAction.ROLLBACK_TO_BACKUP,
                status=ProcessingStatus.PENDING,
            ),
            RecoveryDecision(
                priority=Priority.HIGH,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.PENDING,
            ),
        ]

    @pytest.fixture
    def temp_notification_log(self, tmp_path):
        """Create a temporary notification log path."""
        return tmp_path / "test_notifications.log"

    def test_initialization(self, sample_validation_result, sample_recovery_actions):
        """Test ManualReviewNotifier initialization."""
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=sample_recovery_actions,
        )

        assert notifier.validation_result == sample_validation_result
        assert notifier.recovery_actions == sample_recovery_actions
        assert notifier.notification_config == {}

    def test_initialization_with_config(
        self, sample_validation_result, sample_recovery_actions, temp_notification_log
    ):
        """Test initialization with custom configuration."""
        config = {"log_path": str(temp_notification_log)}

        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=sample_recovery_actions,
            notification_config=config,
        )

        assert notifier.notification_config == config
        assert notifier.notification_log_path == temp_notification_log

    def test_should_trigger_notification_true(self):
        """Test that GLOBAL TRIGGER_MANUAL_REVIEW PENDING actions trigger notifications."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            validation_result=DataProcessingReport(
                status=ProcessingStatus.ERROR, data=None
            ),
            recovery_actions=[decision],
        )

        assert notifier._should_trigger_notification(decision) is True

    def test_should_trigger_notification_false_local_scale(self):
        """Test that LOCAL scale actions don't trigger notifications."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.LOCAL,  # Not GLOBAL
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            validation_result=DataProcessingReport(
                status=ProcessingStatus.ERROR, data=None
            ),
            recovery_actions=[decision],
        )

        assert notifier._should_trigger_notification(decision) is False

    def test_should_trigger_notification_false_wrong_action(self):
        """Test that non-TRIGGER_MANUAL_REVIEW actions don't trigger notifications."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.ROLLBACK_TO_BACKUP,  # Wrong action
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            validation_result=DataProcessingReport(
                status=ProcessingStatus.ERROR, data=None
            ),
            recovery_actions=[decision],
        )

        assert notifier._should_trigger_notification(decision) is False

    def test_should_trigger_notification_false_not_pending(self):
        """Test that non-PENDING actions don't trigger notifications."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.SUCCESS,  # Not PENDING
        )

        notifier = ManualReviewNotifier(
            validation_result=DataProcessingReport(
                status=ProcessingStatus.ERROR, data=None
            ),
            recovery_actions=[decision],
        )

        assert notifier._should_trigger_notification(decision) is False

    def test_build_notification_data(self, sample_validation_result):
        """Test notification data building."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result, recovery_actions=[decision]
        )

        notification_data = notifier._build_notification_data(decision)

        assert "timestamp" in notification_data
        assert notification_data["priority"] == "HIGH"
        assert notification_data["scale"] == "global"
        assert notification_data["action"] == "trigger_manual_review"
        assert notification_data["error_type"] == "schema_mismatch"
        assert notification_data["error_message"] == sample_validation_result.error_message
        assert notification_data["requires_immediate_attention"] is True

    def test_build_notification_data_low_priority(self, sample_validation_result):
        """Test that low priority doesn't require immediate attention."""
        decision = RecoveryDecision(
            priority=Priority.LOW,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result, recovery_actions=[decision]
        )

        notification_data = notifier._build_notification_data(decision)
        assert notification_data["requires_immediate_attention"] is False

    def test_log_notification(
        self, sample_validation_result, temp_notification_log
    ):
        """Test notification logging to file."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        config = {"log_path": str(temp_notification_log)}
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=[decision],
            notification_config=config,
        )

        notification_data = notifier._build_notification_data(decision)
        result = notifier._log_notification(notification_data)

        assert result is True
        assert temp_notification_log.exists()

        # Verify content
        with open(temp_notification_log, "r") as f:
            content = f.read()
            assert "schema_mismatch" in content
            assert "HIGH" in content

    def test_notify_updates_status_to_success(
        self, sample_validation_result, temp_notification_log
    ):
        """Test that notify() updates status from PENDING to SUCCESS."""
        decision = RecoveryDecision(
            priority=Priority.HIGH,
            scale=ProcessingScale.GLOBAL,
            action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
            status=ProcessingStatus.PENDING,
        )

        config = {"log_path": str(temp_notification_log)}
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=[decision],
            notification_config=config,
        )

        updated_actions = notifier.notify()

        assert len(updated_actions) == 1
        assert updated_actions[0].status == ProcessingStatus.SUCCESS

    def test_notify_skips_non_matching_actions(
        self, sample_validation_result, sample_recovery_actions
    ):
        """Test that notify() only processes matching actions."""
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=sample_recovery_actions,
        )

        updated_actions = notifier.notify()

        # First action is LOCAL ROLLBACK - should remain PENDING
        assert updated_actions[0].status == ProcessingStatus.PENDING
        # Second action is GLOBAL TRIGGER_MANUAL_REVIEW - should be SUCCESS
        assert updated_actions[1].status == ProcessingStatus.SUCCESS

    def test_notify_preserves_all_actions(
        self, sample_validation_result, sample_recovery_actions
    ):
        """Test that notify() returns all actions, not just processed ones."""
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=sample_recovery_actions,
        )

        updated_actions = notifier.notify()

        assert len(updated_actions) == len(sample_recovery_actions)

    def test_get_notification_summary(
        self, sample_validation_result, sample_recovery_actions
    ):
        """Test notification summary generation."""
        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result,
            recovery_actions=sample_recovery_actions,
        )

        summary = notifier.get_notification_summary()

        assert summary["total_recovery_actions"] == 2
        assert summary["pending_notifications"] == 1  # Only GLOBAL TRIGGER_MANUAL_REVIEW
        assert summary["error_type"] == "schema_mismatch"
        assert summary["highest_priority"] == "HIGH"

    def test_get_notification_summary_no_pending(self, sample_validation_result):
        """Test summary when no notifications are pending."""
        # All actions already processed
        actions = [
            RecoveryDecision(
                priority=Priority.HIGH,
                scale=ProcessingScale.GLOBAL,
                action=RecoveryAction.TRIGGER_MANUAL_REVIEW,
                status=ProcessingStatus.SUCCESS,  # Already processed
            )
        ]

        notifier = ManualReviewNotifier(
            validation_result=sample_validation_result, recovery_actions=actions
        )

        summary = notifier.get_notification_summary()

        assert summary["pending_notifications"] == 0
        assert summary["highest_priority"] == "NONE"

    def test_multiple_notifications(self, sample_validation_result):
        """Test handling multiple pending notifications."""
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
            validation_result=sample_validation_result, recovery_actions=actions
        )

        updated_actions = notifier.notify()

        # All should be updated to SUCCESS
        assert all(action.status == ProcessingStatus.SUCCESS for action in updated_actions)
        assert len(updated_actions) == 3