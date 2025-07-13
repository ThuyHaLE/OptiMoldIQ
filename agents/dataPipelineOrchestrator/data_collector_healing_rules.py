from pathlib import Path
from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction)

def check_local_backup_and_update_status(recovery_actions, backup_dir: Path):

    required_files = [
        backup_dir / "productRecords.parquet",
        backup_dir / "purchaseOrders.parquet"
    ]

    has_backup_data = all(file.exists() for file in required_files)

    updated_recovery_actions = []

    for (priority, scale, action, status) in recovery_actions:
        if scale == ProcessingScale.LOCAL and action == RecoveryAction.ROLLBACK_TO_BACKUP:
            if status == ProcessingStatus.PENDING:
                new_status = ProcessingStatus.SUCCESS if has_backup_data else ProcessingStatus.ERROR
                updated_recovery_actions.append((priority, scale, action, new_status))
            else:
                updated_recovery_actions.append((priority, scale, action, status))
        else:
            updated_recovery_actions.append((priority, scale, action, status))

    return updated_recovery_actions