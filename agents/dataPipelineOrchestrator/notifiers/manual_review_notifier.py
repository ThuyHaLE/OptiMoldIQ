# agents/dataPipelineOrchestrator/notifiers/manual_review_notifier.py

from agents.dataPipelineOrchestrator.configs.healing_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction, RecoveryDecision, Priority,
    ERROR_CATALOG, RECOVERY_ACTION_CATALOG)
from agents.dataPipelineOrchestrator.configs.output_formats import DataProcessingReport

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict
from loguru import logger
import copy

class ManualReviewNotifier:
    """
    Handles manual review notifications for GLOBAL scale recovery actions.
    
    Sends notifications to administrators when critical errors require manual intervention.
    Processes TRIGGER_MANUAL_REVIEW actions and updates their status upon successful notification.
    """

    def __init__(
            self,
            data_processing_result: DataProcessingReport,
            recovery_actions: List[RecoveryDecision],
            notification_config: Optional[Dict[str, Any]] = None,
        ):
        """
        Initialize Manual Review Notifier.

        Args:
            data_processing_result: The data processing result that triggered the recovery actions
            recovery_actions: List of recovery decisions to process
            notification_config: Optional configuration for notification system
                                (e.g., email settings, webhook URLs, Slack channels)
        """
        self.logger = logger.bind(class_name="ManualReviewNotifier")

        self.data_processing_result = data_processing_result
        self.recovery_actions = recovery_actions
        self.notification_config = notification_config or {}

        # Default notification settings
        self.notification_log_path = Path(
            self.notification_config.get(
                "log_path", "logs/manual_review_notifications.log"
            )
        )
        self.notification_log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("Initialized ManualReviewNotifier")
        self.logger.info(f"  Validation Status: {data_processing_result.status}")
        self.logger.info(f"  Error Type: {data_processing_result.error_type}")
        self.logger.info(f"  Recovery Actions: {len(recovery_actions)}")

    def notify(self) -> List[RecoveryDecision]:
        """
        Process all GLOBAL TRIGGER_MANUAL_REVIEW actions and send notifications.
        
        Iterates through recovery actions, identifies those requiring manual review notifications,
        sends the notifications, and updates their status based on success/failure.
        
        Workflow:
        1. Build notification queues from recovery actions
        2. For each action flagged for notification (GLOBAL + TRIGGER_MANUAL_REVIEW + PENDING):
        - Send notification to administrators
        - Update status to SUCCESS if notification sent successfully
        - Update status to ERROR if notification failed
        3. Return all recovery actions with updated statuses
        
        Returns:
            List[RecoveryDecision]: Updated recovery actions with modified statuses.
                Actions that were successfully notified have status = SUCCESS.
                Actions that failed notification have status = ERROR.
                Other actions remain unchanged.
        """

        notification_queues = self._process_notification_queues()

        decisions_to_notify = [
            decision for trigger, decision in notification_queues.values() 
            if trigger
        ]

        if decisions_to_notify:
            try:
                self.logger.info(f"Processing manual review notification for {len(decisions_to_notify)} action(s)")
                notification_success = self._send_notification()
                if notification_success:
                    self.logger.info(f"Manual review notification sent successfully")
                else:
                    self.logger.error("Failed to send manual review notification")

                # Update status cho ALL decisions are notified
                status = ProcessingStatus.SUCCESS if notification_success else ProcessingStatus.ERROR
                for decision in decisions_to_notify:
                    decision.status = status
                        
            except Exception as e:
                self.logger.error(f"Error during notification process: {e}")
                for decision in decisions_to_notify:
                    decision.status = ProcessingStatus.ERROR

        return [decision for _, decision in notification_queues.values()]

    def _process_notification_queues(self):
        """
        Process recovery actions and organize them into notification queues.
        
        Creates a dictionary mapping recovery action indices to tuples containing:
        - Boolean flag: True if the action requires immediate notification
        (GLOBAL scale + TRIGGER_MANUAL_REVIEW + PENDING status)
        - RecoveryDecision object: containing detailed recovery action information
        
        Conditions for flag = True (requires immediate notification):
        - scale must be GLOBAL (affects entire system)
        - action must be TRIGGER_MANUAL_REVIEW (requires admin intervention)
        - status must be PENDING (not yet processed)
        
        Returns:
            Dict[int, Tuple[bool, RecoveryDecision]]: Dictionary where:
                - key: index of recovery action in self.recovery_actions
                - value: tuple (needs_immediate_notification, recovery_decision)
        
        Example:
            {
                0: (False, RecoveryDecision(...)),  # LOCAL action, no immediate notification
                1: (True, RecoveryDecision(...))    # GLOBAL manual review, needs immediate notification
            }
        """
        notification_queues = {}

        for idx, decision in enumerate(self.recovery_actions):
            notification_queues[idx] = (
                (
                    decision.scale == ProcessingScale.GLOBAL
                    and decision.action == RecoveryAction.TRIGGER_MANUAL_REVIEW
                    and decision.status == ProcessingStatus.PENDING
                ),
                copy.copy(decision))

        return notification_queues

    def _send_notification(self) -> bool:
        """
        Send notification to administrators about errors requiring manual review.
        
        Builds notification data for all recovery decisions (both LOCAL and GLOBAL),
        then sends through available notification channels. Currently only logs to file,
        but designed to support multiple channels (email, Slack, webhooks).
        
        Process:
        1. Build notification data for each recovery decision (organized by scale)
        2. Log notification to file (primary channel)
        3. TODO: Send via additional channels (email, Slack, webhooks)
        
        Returns:
            bool: True if notification was sent successfully through at least one channel,
                False if all channels failed or no channels are configured.
        
        Note:
            Currently returns True only if file logging succeeds. When additional
            channels are implemented, this should return True if ANY channel succeeds.
        """
        notification_data = {}

        for decision in self.recovery_actions:
            notification_data[decision.scale.value] = self._build_notification_data(decision)

        # Log the notification
        log_success = self._log_notification(notification_data)

        # TODO: Implement additional notification channels
        # email_success = self._send_email_notification(notification_data)
        # slack_success = self._send_slack_notification(notification_data)
        # webhook_success = self._send_webhook_notification(notification_data)

        return log_success

    def _build_notification_data(self, decision: RecoveryDecision) -> Dict[str, Any]:
        """
        Build notification data from validation result and recovery decision.

        Args:
            decision: Recovery decision being processed

        Returns:
            Dictionary containing all notification details with catalog information
        """
        notification_data = {
            "timestamp": datetime.now().isoformat(),
            "priority": decision.priority.name,
            "scale": decision.scale.value,
            "action": decision.action.value,
            "error_type": self.data_processing_result.error_type.value,
            "error_message": self.data_processing_result.error_message,
            "validation_status": self.data_processing_result.status.value,
            "metadata": self.data_processing_result.metadata,
            "requires_immediate_attention": decision.priority in [Priority.HIGH, Priority.CRITICAL],
        }
        
        # Add error catalog information
        error_info = ERROR_CATALOG.get(self.data_processing_result.error_type)
        if error_info:
            notification_data["error_details"] = asdict(error_info)
            # Convert enum to string for JSON serialization
            notification_data["error_details"]["severity"] = error_info.severity.name
            notification_data["error_details"]["error_type"] = error_info.error_type.value
        
        # Add recovery action catalog information
        action_info = RECOVERY_ACTION_CATALOG.get(decision.action)
        if action_info:
            notification_data["action_details"] = asdict(action_info)
            # Convert enum to string for JSON serialization
            notification_data["action_details"]["action"] = action_info.action.value
            notification_data["action_details"]["priority"] = action_info.priority.name
        
        return notification_data

    def _log_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Log notification details to a file for audit trail and debugging.
        
        Converts the notification data dictionary into a human-readable text format
        using DictBasedReportGenerator, then writes it to the configured log file.
        This serves as both a notification record and fallback when other channels fail.
        
        Args:
            notification_data: Dictionary containing notification information, organized
                            by scale (LOCAL/GLOBAL) with error details, action details,
                            timestamps, and priority information.
        
        Returns:
            bool: True if notification was successfully written to log file,
                False if writing failed or data validation failed.
        
        Side Effects:
            - Creates parent directories if they don't exist
            - Overwrites existing log file at self.notification_log_path
            - Logs success/failure messages via self.logger
        
        Raises:
            Exception: Catches and logs any exceptions during file writing,
                    returns False instead of propagating.
        """
        
        try:
            # Generate notification
            from configs.shared.dict_based_report_generator import DictBasedReportGenerator
            reporter = DictBasedReportGenerator(use_colors=False)
            notification_text = "\n".join(reporter.export_report(notification_data))

            # Validate excel data, it must be string
            if not isinstance(notification_text, str):
                self.logger.error("❌ Expected str but got: {}", type(notification_text))
                return False
            
            with open(Path(self.notification_log_path), "w", encoding="utf-8") as notification_file:
                notification_file.write(notification_text)    
            self.logger.info("✓ Saved notification: {}", self.notification_log_path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to log notification: {e}")
            return False

    def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send email notification to administrators (placeholder for future implementation).
        
        Will use SMTP or email service API (e.g., SendGrid, AWS SES) to send
        formatted notification emails to configured recipients.
        
        Args:
            notification_data: Notification information to include in email body
        
        Returns:
            bool: Currently returns False (not implemented).
                Will return True when email is sent successfully.
        
        TODO:
            - Configure SMTP server or email service credentials
            - Format notification_data into HTML/text email template
            - Add recipient list from notification_config
            - Implement retry logic for transient failures
            - Add email rate limiting
        """

        # TODO: Implement email notification
        # This would use SMTP or email service API
        self.logger.warning("Email notification not implemented yet")
        return False

    def _send_slack_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send Slack notification to designated channel (placeholder for future implementation).
        
        Will use Slack Webhook or Slack API to post formatted notifications
        to configured Slack channels or direct messages.
        
        Args:
            notification_data: Notification information to format as Slack message
        
        Returns:
            bool: Currently returns False (not implemented).
                Will return True when Slack message is delivered successfully.
        
        TODO:
            - Configure Slack webhook URL or bot token
            - Format notification_data into Slack message blocks
            - Add channel/user configuration from notification_config
            - Implement message threading for related notifications
            - Add @mention support for high-priority notifications
        """
        
        # TODO: Implement Slack notification
        # This would use Slack Webhook or API
        self.logger.warning("Slack notification not implemented yet")
        return False

    def _send_webhook_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        Send webhook notification to external system (placeholder for future implementation).
        
        Will POST notification data to configured webhook URLs, allowing integration
        with external monitoring, ticketing, or alerting systems.
        
        Args:
            notification_data: Notification information to send as JSON payload
        
        Returns:
            bool: Currently returns False (not implemented).
                Will return True when webhook is delivered successfully (2xx response).
        
        TODO:
            - Configure webhook URLs from notification_config
            - Add authentication headers (API keys, HMAC signatures)
            - Implement retry logic with exponential backoff
            - Add webhook timeout configuration
            - Log webhook response for debugging
            - Support multiple webhook endpoints
        """
        
        # TODO: Implement webhook notification
        # This would POST to configured webhook URL
        self.logger.warning("Webhook notification not implemented yet")
        return False