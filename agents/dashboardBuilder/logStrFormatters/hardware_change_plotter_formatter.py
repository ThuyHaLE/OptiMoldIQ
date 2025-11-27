from typing import Dict, Optional, Any
from datetime import datetime
from agents.dashboardBuilder.dashboardBuilderConfigs.hardware_change_plotflow_config import HardwareChangePlotflowConfig

def build_hardware_change_plotter_log(config: HardwareChangePlotflowConfig, 
                                    results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for HardwareChangePlotter run.
    Does NOT log; just returns string.
    """

    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] HardwareChangePlotter Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")

    log_lines.append("⤷ Analyzer Configuration")
    log_lines.append(f"⤷ Database Annotation: {config.analytics_orchestrator_config.source_path}/{config.analytics_orchestrator_config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.analytics_orchestrator_config.databaseSchemas_path}")
    log_lines.append(f"   ⤷ Save analytics orchestrator log: {config.analytics_orchestrator_config.save_analytics_orchestrator_log}")
    if config.analytics_orchestrator_config.save_analytics_orchestrator_log:
        log_lines.append(f"       ⤷ Output Directory: {config.analytics_orchestrator_config.analytics_orchestrator_dir}")

    log_lines.append(f"   ⤷ Save hardware change analyzer log: {config.analytics_orchestrator_config.save_hardware_change_analyzer_log}")
    if config.analytics_orchestrator_config.save_hardware_change_analyzer_log:
        log_lines.append(f"       ⤷ Output Directory: {config.analytics_orchestrator_config.hardware_change_analyzer_dir}")

    log_lines.append("⤷ Plotter Configuration")
    log_lines.append(f"   ⤷ Save hardware change plotter log: {config.save_hardware_change_plotter_log}")
    if config.save_hardware_change_plotter_log:
        log_lines.append(f"       ⤷ Output Directory: {config.hardware_change_plotter_dir}")

    log_lines.append(f"⤷ Parallel Enabled: {config.enable_parallel}")
    log_lines.append(f"⤷ Max Workers: {config.max_workers or 'Auto'}")

    # ---------- Machine layout plotter ----------
    if getattr(config, "enable_machine_layout_plotter", False):
        log_lines.append("⤷ Machine layout plotter: Enable")
        log_lines.append("--MachineLayoutPlotter Configuration--")
        log_lines.append(f"   ⤷ Tracker Output Dir: {config.analytics_orchestrator_config.machine_layout_tracker_dir}")
        log_lines.append(f"   ⤷ Change Log Name: {config.analytics_orchestrator_config.machine_layout_tracker_change_log_name}")
        log_lines.append(f"   ⤷ Plotter Output Dir: {config.machine_layout_plotter_result_dir}")
        log_lines.append(f"   ⤷ Viz Config: {config.machine_layout_visualization_config_path}")
    else:
        log_lines.append("⤷ Machine layout plotter: Disable")

    # ---------- Machine mold pair plotter ----------
    if getattr(config, "enable_machine_mold_pair_plotter", False):
        log_lines.append("⤷ Machine mold pair plotter: Enable")
        log_lines.append("--MachineMoldPairPlotter Configuration--")
        log_lines.append(f"   ⤷ Tracker Output Dir: {config.analytics_orchestrator_config.machine_mold_pair_tracker_dir}")
        log_lines.append(f"   ⤷ Change Log Name: {config.analytics_orchestrator_config.machine_mold_pair_tracker_change_log_name}")
        log_lines.append(f"   ⤷ Plotter Output Dir: {config.machine_mold_pair_plotter_result_dir}")
        log_lines.append(f"   ⤷ Viz Config: {config.machine_mold_pair_visualization_config_path}")
    else:
        log_lines.append("⤷ Machine mold pair plotter: Disable")

    log_lines.append("")

    # ---------- Processing Summary ----------
    summary_dict = build_hardware_processing_summary(results)

    log_lines.append("--Processing Summary--")
    skipped = summary_dict.get('Processing Summary', {}).get('Skipped')
    if skipped:
        log_lines.append(f"⤷ Skipped: {skipped}")
    completed = summary_dict.get('Processing Summary', {}).get('Completed')
    if completed:
        log_lines.append(f"⤷ Completed: {completed}")
    log_lines.append("")

    # ---------- Detailed Results ----------
    details = summary_dict.get('Details')
    if details:
        log_lines.append("--Details--")
        for level_name, level_result in details.items():
            log_lines.append(f"⤷ {level_name}:")
            for sub_name, sub_result in level_result.items():
                log_lines.append(f"   ⤷ {sub_name}:")
                log_lines.append(str(sub_result) if sub_result is not None else "None")
        log_lines.append("")

    return "\n".join(log_lines)

def build_hardware_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build processing summary dict from results.
    Does NOT log; just returns structured dict.
    """
    summary = {'Processing Summary': {}, 'Details': {}}

    skipped = [k for k, v in results.items() if v is None]
    if skipped:
        summary['Processing Summary']['Skipped'] = ", ".join(skipped)

    completed = [k for k, v in results.items() if v is not None]
    summary['Processing Summary']['Completed'] = ", ".join(completed) if completed else "None"

    for lv in completed:
        summary['Details'][lv] = {}
        result_dict = results[lv]
        if result_dict and 'result' in result_dict:
            for sub_name, sub_val in result_dict['result'].items():
                summary['Details'][lv][sub_name] = sub_val

    return summary