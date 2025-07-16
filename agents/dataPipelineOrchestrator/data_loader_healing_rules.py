from pathlib import Path
import json

from configs.recovery.dataPipelineOrchestrator.data_pipeline_orchestrator_configs import (
    ProcessingStatus, ProcessingScale, RecoveryAction, Priority)


def check_annotation_paths_and_update_status(recovery_actions, annotation_path):

    """
    Check whether all file paths specified in the annotation JSON exist,
    and update the status of local rollback-to-backup recovery actions accordingly.

    Args:
        recovery_actions (list of tuples): List of recovery actions in the format 
            (priority, scale, action, status).
        annotation_path (str or Path): Path to a JSON file that maps keys to file paths.

    Returns:
        list: Updated recovery_actions list with modified statuses based on annotation path existence.
    """

    updated_recovery_actions = []
    all_exist = False  # Default to False in case of error or missing files

    try:
        # Open and parse the annotation file
        with open(Path(annotation_path), "r") as f:
            annotation_dict = json.load(f)

            # Resolve all paths listed in the annotation values
            resolved_paths = [Path(p) for p in annotation_dict.values()]

            # Check if all the paths exist
            all_exist = all(p.exists() for p in resolved_paths)
    except Exception:
        # If any error occurs (e.g., file not found or JSON error), treat as failure
        all_exist = False

    # Iterate through the recovery actions and update those that match specific criteria
    for (priority, scale, action, status) in recovery_actions:
        if scale == ProcessingScale.LOCAL and action == RecoveryAction.ROLLBACK_TO_BACKUP:
            # If annotation files exist, mark as SUCCESS; otherwise, mark as ERROR
            new_status = ProcessingStatus.SUCCESS if all_exist else ProcessingStatus.ERROR
            updated_recovery_actions.append((priority, scale, action, new_status))
        else:
            # Leave all other actions unchanged
            updated_recovery_actions.append((priority, scale, action, status))

    return updated_recovery_actions