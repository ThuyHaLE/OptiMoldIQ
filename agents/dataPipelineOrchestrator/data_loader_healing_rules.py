from pathlib import Path
import json

from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction, Priority)


def check_annotation_paths_and_update_status(recovery_actions, annotation_path):
    updated_recovery_actions = []
    all_exist = False  # default value

    try:
        with open(Path(annotation_path), "r") as f:
            annotation_dict = json.load(f)
            resolved_paths = [Path(p) for p in annotation_dict.values()]
            all_exist = all(p.exists() for p in resolved_paths)
    except Exception:
        all_exist = False

    for (priority, scale, action, status) in recovery_actions:
        if scale == ProcessingScale.LOCAL and action == RecoveryAction.ROLLBACK_TO_BACKUP:
            new_status = ProcessingStatus.SUCCESS if all_exist else ProcessingStatus.ERROR
            updated_recovery_actions.append((priority, scale, action, new_status))
        else:
            updated_recovery_actions.append((priority, scale, action, status))

    return updated_recovery_actions