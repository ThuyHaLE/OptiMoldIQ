from typing import Dict, Optional, Any
from datetime import datetime
from agents.analyticsOrchestrator.hardwareChangeAnalyzer.hardware_change_analyzer import ChangeAnalyticflowConfig

def build_hardware_change_analyzer_log(config: ChangeAnalyticflowConfig, 
                                       results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for HardwareChangeAnalyzer run.
    Does NOT log; just returns string.
    """

    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] HardwareChangeAnalyzer Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")
    log_lines.append(f"⤷ Database Annotation: {config.source_path}/{config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.databaseSchemas_path}")

    log_lines.append(f"⤷ Save hardware change analyzer log: {config.save_hardware_change_analyzer_log}")
    if config.save_hardware_change_analyzer_log:
        log_lines.append(f"   ⤷ Output Directory: {config.hardware_change_analyzer_dir}")
    log_lines.append("")

    # ---------- Machine layout tracker ----------
    if getattr(config, "enable_machine_layout_tracker", False):
        log_lines.append("⤷ Machine layout tracker: Enable")
        log_lines.append("--MachineLayoutTracker Configuration--")
        log_lines.append(f"   ⤷ Output Directory: {config.machine_layout_tracker_dir}")
        log_lines.append(f"   ⤷ Change Log Name: {config.machine_layout_tracker_change_log_name}")
    else:
        log_lines.append("⤷ Machine layout tracker: Disable")

    # ---------- Machine mold pair tracker ----------
    if getattr(config, "enable_machine_mold_pair_tracker", False):
        log_lines.append("⤷ Machine mold pair tracker: Enable")
        log_lines.append("--MachineMoldPairTracker Configuration--")
        log_lines.append(f"   ⤷ Output Directory: {config.machine_mold_pair_tracker_dir}")
        log_lines.append(f"   ⤷ Change Log Name: {config.machine_mold_pair_tracker_change_log_name}")
    else:
        log_lines.append("⤷ Machine mold pair tracker: Disable")
    log_lines.append("")

    # ---------- Processing Summary ----------
    summary_dict = build_hardware_analyzer_processing_summary(results)

    log_lines.append("--Processing Summary--")
    skipped = summary_dict.get('Processing Summary', {}).get('Skipped')
    if skipped:
        log_lines.append(f"⤷ Skipped: {skipped}")
    completed = summary_dict.get('Processing Summary', {}).get('Completed')
    if completed:
        log_lines.append(f"⤷ Completed: {completed}")
    log_lines.append("")

    # ---------- Details ----------
    details = summary_dict.get('Details')
    if details:
        log_lines.append("--Details--")
        for level_name, level_result in details.items():
            log_lines.append(f"⤷ {level_name}:")
            if isinstance(level_result, dict):
                for sub_name, sub_val in level_result.items():
                    log_lines.append(f"   ⤷ {sub_name}: {str(sub_val)}")
            else:
                log_lines.append(f"   ⤷ {str(level_result)}")
        log_lines.append("")

    return "\n".join(log_lines)


def build_hardware_analyzer_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build structured processing summary for HardwareChangeAnalyzer.
    Does NOT log; returns a dict suitable for formatting.
    """
    summary = {'Processing Summary': {}, 'Details': {}}

    skipped = [k for k, v in results.items() if v is None]
    if skipped:
        summary['Processing Summary']['Skipped'] = ", ".join(skipped)

    completed = [k for k, v in results.items() if v is not None]
    summary['Processing Summary']['Completed'] = ", ".join(completed) if completed else "None"

    for lv in completed:
        level_data = results[lv]
        if level_data and "log_entries" in level_data:
            summary['Details'][lv] = level_data["log_entries"] or "No new changes detected."
        else:
            summary['Details'][lv] = "No new changes detected."

    return summary
