from pathlib import Path
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction)

def check_local_backup_and_update_status(recovery_actions, backup_dir: Path):

    """
    Check if required local backup files exist, and update the status of recovery actions accordingly.

    Args:
        recovery_actions (list of tuples): Each tuple contains 
            (priority, scale, action, status).
        backup_dir (Path): Directory where backup files are expected to exist.

    Returns:
        list: Updated list of recovery actions with potentially modified statuses.
    """

    # Define the list of required backup files
    required_files = [
        backup_dir / "productRecords.parquet",
        backup_dir / "purchaseOrders.parquet"
    ]

    # Check if all required backup files are present
    has_backup_data = all(file.exists() for file in required_files)

    updated_recovery_actions = []

    # Iterate through all recovery actions and update the status if conditions are met
    for (priority, scale, action, status) in recovery_actions:
        # Only process actions that are:
        # 1. Local scale
        # 2. Require rollback to backup
        if scale == ProcessingScale.LOCAL and action == RecoveryAction.ROLLBACK_TO_BACKUP:
            # If the status is pending, update it based on whether backup files exist
            if status == ProcessingStatus.PENDING:
                new_status = ProcessingStatus.SUCCESS if has_backup_data else ProcessingStatus.ERROR
                updated_recovery_actions.append((priority, scale, action, new_status))
            else:
                # If not pending, retain the original status
                updated_recovery_actions.append((priority, scale, action, status))
        else:
            # For other types of actions or scales, keep them unchanged
            updated_recovery_actions.append((priority, scale, action, status))

    return updated_recovery_actions