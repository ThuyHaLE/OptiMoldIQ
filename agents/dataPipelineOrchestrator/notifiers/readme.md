# ManualReviewNotifier

## Overview

`ManualReviewNotifier` là component chịu trách nhiệm gửi thông báo đến administrators khi có lỗi nghiêm trọng cần can thiệp thủ công (manual review). Component này xử lý các recovery actions với:

- **Scale**: `ProcessingScale.GLOBAL`
- **Action**: `RecoveryAction.TRIGGER_MANUAL_REVIEW`
- **Status**: `ProcessingStatus.PENDING` → `ProcessingStatus.SUCCESS`

## Features

✅ Xử lý thông báo cho GLOBAL manual review actions  
✅ Log notifications ra file  
✅ Hỗ trợ multiple notification channels (email, Slack, webhook) - ready to implement  
✅ Tự động update status từ PENDING → SUCCESS  
✅ Priority-aware notifications  
✅ Detailed notification data với metadata  

## Installation

```python
from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import (
    ManualReviewNotifier,
)
from agents.dataPipelineOrchestrator.configs.output_formats import (
    DataProcessingReport,
    get_recovery_actions_for_agent_error,
    AgentType,
    ErrorType,
)
```

## Basic Usage

```python
# 1. Có một validation result với error
validation_result = DataProcessingReport(
    status=ProcessingStatus.ERROR,
    data=None,
    error_type=ErrorType.SCHEMA_MISMATCH,
    error_message="Schema validation failed",
    metadata={"missing_fields": ["timestamp", "user_id"]}
)

# 2. Get recovery actions cho error này
recovery_actions = get_recovery_actions_for_agent_error(
    agent_type=AgentType.SCHEMA_VALIDATOR,
    error_type=ErrorType.SCHEMA_MISMATCH
)

# 3. Initialize notifier
notifier = ManualReviewNotifier(
    validation_result=validation_result,
    recovery_actions=recovery_actions
)

# 4. Send notifications
updated_actions = notifier.notify()

# 5. Check results
for action in updated_actions:
    if action.scale == ProcessingScale.GLOBAL:
        print(f"{action.action}: {action.status}")
        # Output: trigger_manual_review: success
```

## Configuration

### Default Configuration

```python
notifier = ManualReviewNotifier(
    validation_result=validation_result,
    recovery_actions=recovery_actions
)
# Logs to: logs/manual_review_notifications.log
```

### Custom Configuration

```python
config = {
    "log_path": "custom/path/notifications.log",
    "email_recipients": ["admin@company.com"],
    "slack_channel": "#alerts",
    "webhook_url": "https://api.monitoring.com/webhooks"
}

notifier = ManualReviewNotifier(
    validation_result=validation_result,
    recovery_actions=recovery_actions,
    notification_config=config
)
```

## Integration with Recovery Pipeline

### Full Recovery Flow

```python
from agents.dataPipelineOrchestrator.healers.schema_error_healer import SchemaErrorHealer
from agents.dataPipelineOrchestrator.notifiers.manual_review_notifier import ManualReviewNotifier

# Step 1: Validation fails
validation_result = validator.validate()

# Step 2: Get recovery actions
recovery_actions = get_recovery_actions_for_agent_error(
    agent_type=AgentType.SCHEMA_VALIDATOR,
    error_type=validation_result.error_type
)

# Step 3: Try LOCAL recovery (backup rollback)
healer = SchemaErrorHealer(
    validation_result=validation_result,
    recovery_actions=recovery_actions
)
healed_actions, healed_result = healer.heal_schema_error()

# Step 4: Send GLOBAL notifications if needed
notifier = ManualReviewNotifier(
    validation_result=healed_result,
    recovery_actions=healed_actions
)
final_actions = notifier.notify()

# Step 5: Check if all recovery completed
all_successful = all(
    action.status == ProcessingStatus.SUCCESS 
    for action in final_actions
)
```

## How It Works

### Processing Logic

```
For each recovery_action in recovery_actions:
    ├─ Is it GLOBAL + TRIGGER_MANUAL_REVIEW + PENDING?
    │  ├─ YES → Send notification
    │  │         └─ Update status to SUCCESS
    │  └─ NO  → Keep original status
    └─ Add to updated_actions list
```

### Notification Data Structure

```json
{
  "timestamp": "2025-01-29T10:30:00",
  "priority": "HIGH",
  "scale": "global",
  "action": "trigger_manual_review",
  "error_type": "schema_mismatch",
  "error_message": "Schema validation failed",
  "validation_status": "error",
  "metadata": {
    "expected_fields": ["id", "name"],
    "missing_fields": ["name"]
  },
  "requires_immediate_attention": true
}
```

## API Reference

### `ManualReviewNotifier`

#### `__init__(validation_result, recovery_actions, notification_config=None)`

Initialize notifier.

**Parameters:**
- `validation_result` (DataProcessingReport): Validation result that triggered recovery
- `recovery_actions` (List[RecoveryDecision]): Recovery decisions to process
- `notification_config` (Optional[Dict]): Notification configuration

#### `notify() -> List[RecoveryDecision]`

Process all pending GLOBAL manual review notifications.

**Returns:**
- List of updated recovery actions with SUCCESS status for processed notifications

#### `get_notification_summary() -> Dict[str, Any]`

Get summary of pending notifications.

**Returns:**
```python
{
    "total_recovery_actions": 2,
    "pending_notifications": 1,
    "error_type": "schema_mismatch",
    "error_message": "...",
    "highest_priority": "HIGH"
}
```

## Error Handling

```python
try:
    notifier = ManualReviewNotifier(
        validation_result=validation_result,
        recovery_actions=recovery_actions
    )
    updated_actions = notifier.notify()
    
    # Check for failed notifications
    failed = [
        action for action in updated_actions
        if action.action == RecoveryAction.TRIGGER_MANUAL_REVIEW
        and action.status == ProcessingStatus.ERROR
    ]
    
    if failed:
        print(f"Warning: {len(failed)} notifications failed to send")
        
except Exception as e:
    print(f"Notification system error: {e}")
```

## Testing

Run tests:

```bash
pytest tests/test_manual_review_notifier.py -v
```

Key test cases:
- ✓ Status update from PENDING to SUCCESS
- ✓ Only processes GLOBAL + TRIGGER_MANUAL_REVIEW + PENDING
- ✓ Preserves non-matching actions
- ✓ Logs notifications correctly
- ✓ Handles multiple notifications
- ✓ Priority-based filtering

## Future Enhancements

### Planned Features

1. **Email Notifications**
   ```python
   def _send_email_notification(self, notification_data):
       # Send via SMTP or email API
       pass
   ```

2. **Slack Integration**
   ```python
   def _send_slack_notification(self, notification_data):
       # Post to Slack webhook
       pass
   ```

3. **Webhook Support**
   ```python
   def _send_webhook_notification(self, notification_data):
       # POST to monitoring system
       pass
   ```

4. **Retry Logic**
   - Automatic retry on failed notifications
   - Exponential backoff
   - Dead letter queue for persistent failures

5. **Notification Templates**
   - Customizable message templates
   - Different templates per error type
   - Markdown/HTML formatting

## Examples

See `example_usage_manual_review_notifier.py` for:
- Basic usage
- Custom configuration
- Full recovery pipeline integration
- Multiple error types handling

## Logging

Default log format:

```
2025-01-29 10:30:00 | INFO | ManualReviewNotifier | Initialized ManualReviewNotifier
2025-01-29 10:30:00 | INFO | ManualReviewNotifier |   Validation Status: error
2025-01-29 10:30:00 | INFO | ManualReviewNotifier |   Error Type: schema_mismatch
2025-01-29 10:30:00 | INFO | ManualReviewNotifier | Processing manual review notification...
2025-01-29 10:30:00 | INFO | ManualReviewNotifier | Notification logged to logs/manual_review_notifications.log
2025-01-29 10:30:00 | INFO | ManualReviewNotifier | Manual review notification sent successfully (Priority: HIGH)
```

## Best Practices

1. **Always check notification summary before sending**
   ```python
   summary = notifier.get_notification_summary()
   if summary['pending_notifications'] > 0:
       print(f"Will send {summary['pending_notifications']} notifications")
       updated_actions = notifier.notify()
   ```

2. **Configure appropriate log paths for production**
   ```python
   config = {
       "log_path": "/var/log/data-pipeline/notifications.log"
   }
   ```

3. **Monitor notification success rates**
   ```python
   success_count = sum(
       1 for action in updated_actions
       if action.status == ProcessingStatus.SUCCESS
   )
   success_rate = success_count / len(updated_actions)
   ```

4. **Handle notification failures gracefully**
   ```python
   if any(action.status == ProcessingStatus.ERROR for action in updated_actions):
       # Fallback: log to system logger
       logger.critical("Some notifications failed to send")
   ```

## License

Internal use only - Data Pipeline Orchestrator System