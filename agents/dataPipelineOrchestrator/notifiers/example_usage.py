# Example Usage: ManualReviewNotifier

"""
This example demonstrates how to use ManualReviewNotifier in the data pipeline orchestrator.
"""
from agents.dataPipelineOrchestrator.configs.output_formats import (
    AgentType,
    ErrorType,
    ProcessingStatus,
    DataProcessingReport,
    get_recovery_actions_for_agent_error,
)
from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import ManualReviewNotifier

# ============================================================================
# Example 1: Basic Usage
# ============================================================================

def example_basic_usage():
    """Basic example of using ManualReviewNotifier."""
    
    # Simulate a validation error
    validation_result = DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="Database schema does not match expected structure",
        metadata={
            "expected_columns": ["id", "name", "timestamp"],
            "actual_columns": ["id", "name"],
            "missing_columns": ["timestamp"],
        },
    )

    # Get recovery actions for this error
    recovery_actions = get_recovery_actions_for_agent_error(
        agent_type=AgentType.SCHEMA_VALIDATOR,
        error_type=ErrorType.SCHEMA_MISMATCH,
    )

    print(f"Initial recovery actions: {len(recovery_actions)}")
    for action in recovery_actions:
        print(f"  - {action.action.value} ({action.scale.value}) - {action.status.value}")

    # Initialize notifier
    notifier = ManualReviewNotifier(
        validation_result=validation_result,
        recovery_actions=recovery_actions,
    )

    # Get summary before sending
    summary = notifier.get_notification_summary()
    print(f"\nNotification Summary:")
    print(f"  Total actions: {summary['total_recovery_actions']}")
    print(f"  Pending notifications: {summary['pending_notifications']}")
    print(f"  Error: {summary['error_type']}")
    print(f"  Highest priority: {summary['highest_priority']}")

    # Send notifications
    print("\nSending notifications...")
    updated_actions = notifier.notify()

    # Check results
    print(f"\nUpdated recovery actions:")
    for action in updated_actions:
        print(f"  - {action.action.value} ({action.scale.value}) - {action.status.value}")


# ============================================================================
# Example 2: With Custom Configuration
# ============================================================================

def example_with_config():
    """Example with custom notification configuration."""
    
    validation_result = DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
        error_message="Schema structure is invalid - missing required keys",
        metadata={
            "file_path": "/data/schemas/database_schema.json",
            "validation_errors": ["Missing 'version' field", "Invalid 'tables' structure"],
        },
    )

    recovery_actions = get_recovery_actions_for_agent_error(
        agent_type=AgentType.SCHEMA_VALIDATOR,
        error_type=ErrorType.INVALID_SCHEMA_STRUCTURE,
    )

    # Custom notification configuration
    notification_config = {
        "log_path": "logs/critical_notifications.log",
        "email_recipients": ["admin@company.com", "data-team@company.com"],
        "slack_channel": "#data-pipeline-alerts",
        "webhook_url": "https://monitoring.company.com/webhooks/alerts",
    }

    notifier = ManualReviewNotifier(
        validation_result=validation_result,
        recovery_actions=recovery_actions,
        notification_config=notification_config,
    )

    updated_actions = notifier.notify()
    
    return updated_actions


# ============================================================================
# Example 3: Integration with SchemaErrorHealer
# ============================================================================

def example_full_recovery_pipeline():
    """Example showing full recovery pipeline with both healer and notifier."""
    
    from agents.dataPipelineOrchestrator.healers.schema_error_healer import (
        SchemaErrorHealer,
    )

    # Step 1: Validation fails
    validation_result = DataProcessingReport(
        status=ProcessingStatus.ERROR,
        data=None,
        error_type=ErrorType.SCHEMA_MISMATCH,
        error_message="Schema validation failed",
        metadata={"schema_file": "databaseSchemas.json"},
    )

    # Step 2: Get recovery actions
    recovery_actions = get_recovery_actions_for_agent_error(
        agent_type=AgentType.SCHEMA_VALIDATOR,
        error_type=ErrorType.SCHEMA_MISMATCH,
    )

    print("=" * 80)
    print("RECOVERY PIPELINE")
    print("=" * 80)
    
    print(f"\nInitial Status:")
    print(f"  Validation: {validation_result.status.value}")
    print(f"  Error: {validation_result.error_type.value}")
    print(f"  Recovery Actions: {len(recovery_actions)}")

    # Step 3: Try local healing (backup rollback)
    print(f"\n{'─' * 80}")
    print("STEP 1: Attempting Local Recovery (Backup Rollback)")
    print(f"{'─' * 80}")
    
    healer = SchemaErrorHealer(
        validation_result=validation_result,
        recovery_actions=recovery_actions,
    )

    healed_actions, healed_result = healer.heal_schema_error()

    print(f"\nLocal Recovery Results:")
    for action in healed_actions:
        if action.scale.value == "local":
            print(f"  {action.action.value}: {action.status.value}")
    print(f"  Healed validation status: {healed_result.status.value}")

    # Step 4: Send global notifications if needed
    print(f"\n{'─' * 80}")
    print("STEP 2: Triggering Global Notifications")
    print(f"{'─' * 80}")
    
    notifier = ManualReviewNotifier(
        validation_result=healed_result,
        recovery_actions=healed_actions,
    )

    final_actions = notifier.notify()

    print(f"\nGlobal Notification Results:")
    for action in final_actions:
        if action.scale.value == "global":
            print(f"  {action.action.value}: {action.status.value}")

    # Step 5: Summary
    print(f"\n{'=' * 80}")
    print("FINAL RECOVERY STATUS")
    print(f"{'=' * 80}")
    
    all_successful = all(
        action.status == ProcessingStatus.SUCCESS for action in final_actions
    )
    
    print(f"\nAll recovery actions completed: {all_successful}")
    print(f"\nFinal Action Statuses:")
    for action in final_actions:
        status_icon = "✓" if action.status == ProcessingStatus.SUCCESS else "✗"
        print(
            f"  {status_icon} [{action.scale.value.upper()}] "
            f"{action.action.value}: {action.status.value}"
        )

    return final_actions


# ============================================================================
# Example 4: Handling Multiple Error Types
# ============================================================================

def example_multiple_errors():
    """Example handling different error types with different notifications."""
    
    error_scenarios = [
        (ErrorType.FILE_NOT_FOUND, "Critical file missing from system"),
        (ErrorType.DATA_CORRUPTION, "Data integrity check failed"),
        (ErrorType.INVALID_JSON, "Configuration file contains invalid JSON"),
    ]

    for error_type, error_msg in error_scenarios:
        print(f"\n{'=' * 80}")
        print(f"Processing: {error_type.value}")
        print(f"{'=' * 80}")

        validation_result = DataProcessingReport(
            status=ProcessingStatus.ERROR,
            data=None,
            error_type=error_type,
            error_message=error_msg,
        )

        recovery_actions = get_recovery_actions_for_agent_error(
            agent_type=AgentType.SCHEMA_VALIDATOR,
            error_type=error_type,
        )

        notifier = ManualReviewNotifier(
            validation_result=validation_result,
            recovery_actions=recovery_actions,
        )

        summary = notifier.get_notification_summary()
        print(f"  Notifications to send: {summary['pending_notifications']}")
        print(f"  Priority level: {summary['highest_priority']}")

        updated_actions = notifier.notify()
        
        success_count = sum(
            1
            for action in updated_actions
            if action.status == ProcessingStatus.SUCCESS
        )
        print(f"  Successful notifications: {success_count}/{len(updated_actions)}")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80)
    example_basic_usage()

    print("\n\n")
    print("EXAMPLE 3: Full Recovery Pipeline")
    print("=" * 80)
    example_full_recovery_pipeline()

    print("\n\n")
    print("EXAMPLE 4: Multiple Error Types")
    print("=" * 80)
    example_multiple_errors()