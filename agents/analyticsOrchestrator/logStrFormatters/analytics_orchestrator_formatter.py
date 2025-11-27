from typing import Dict, Optional, Any
from datetime import datetime
from agents.analyticsOrchestrator.analytics_orchestrator import AnalyticsOrchestratorConfig

def build_analytics_orchestrator_log(config: AnalyticsOrchestratorConfig, 
                                     results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for AnalyticsOrchestrator run.
    Does NOT log; just returns string.
    """
    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] AnalyticsOrchestrator Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")
    log_lines.append(f"⤷ Database Annotation: {config.source_path}/{config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.databaseSchemas_path}")
    log_lines.append(f"⤷ Save analytics orchestrator log: {config.save_analytics_orchestrator_log}")
    if getattr(config, "save_analytics_orchestrator_log", False):
        log_lines.append(f"   ⤷ Output Directory: {config.analytics_orchestrator_dir}")

    # ---------- Change Analysis ----------
    if getattr(config, "enable_hardware_change_analysis", False):
        log_lines.append("⤷ Change Analysis: Enable")
        log_lines.append(f"   ⤷ Save hardware change analyzer log: {config.save_hardware_change_analyzer_log}")
        if getattr(config, "save_hardware_change_analyzer_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.hardware_change_analyzer_dir}")

        log_lines.append("--HardwareChangeAnalyzer Configuration--")
        # Machine layout tracker
        if getattr(config, "enable_machine_layout_tracker", False):
            log_lines.append("   ⤷ Machine layout tracker: Enable")
            log_lines.append(f"       ⤷ Output Directory: {config.machine_layout_tracker_dir}")
            log_lines.append(f"       ⤷ Change Log Name: {config.machine_layout_tracker_change_log_name}")
        else:
            log_lines.append("   ⤷ Machine layout tracker: Disable")
        # Machine mold pair tracker
        if getattr(config, "enable_machine_mold_pair_tracker", False):
            log_lines.append("   ⤷ Machine mold pair tracker: Enable")
            log_lines.append(f"       ⤷ Output Directory: {config.machine_mold_pair_tracker_dir}")
            log_lines.append(f"       ⤷ Change Log Name: {config.machine_mold_pair_tracker_change_log_name}")
        else:
            log_lines.append("   ⤷ Machine mold pair tracker: Disable")
    else:
        log_lines.append("⤷ Change Analysis: Disable")

    # ---------- Multi-Level Analysis ----------
    if getattr(config, "enable_multi_level_analysis", False):
        log_lines.append("⤷ Multi-level Analysis: Enable")
        log_lines.append(f"   ⤷ Save multi-level performance analyzer log: {config.save_multi_level_performance_analyzer_log}")
        if getattr(config, "save_multi_level_performance_analyzer_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.multi_level_performance_analyzer_dir}")

        log_lines.append("--MultiLevelPerformanceAnalyzer Configuration--")
        # Day level
        if getattr(config, "record_date", None):
            log_lines.append("   ⤷ Day level")
            log_lines.append(f"       ⤷ Record Date: {config.record_date}")
            log_lines.append(f"       ⤷ Save Output: {config.day_save_output}")
        else:
            log_lines.append("   ⤷ Day level: Disable")
        # Month level
        if getattr(config, "record_month", None):
            log_lines.append("   ⤷ Month level")
            log_lines.append(f"       ⤷ Record Month: {config.record_month}")
            log_lines.append(f"       ⤷ Analysis Date: {getattr(config, 'month_analysis_date', 'Not set')}")
            log_lines.append(f"       ⤷ Save Output: {config.month_save_output}")
        else:
            log_lines.append("   ⤷ Month level: Disable")
        # Year level
        if getattr(config, "record_year", None):
            log_lines.append("   ⤷ Year level")
            log_lines.append(f"       ⤷ Record Year: {config.record_year}")
            log_lines.append(f"       ⤷ Analysis Date: {getattr(config, 'year_analysis_date', 'Not set')}")
            log_lines.append(f"       ⤷ Save Output: {config.year_save_output}")
        else:
            log_lines.append("   ⤷ Year level: Disable")
    else:
        log_lines.append("⤷ Multi-level Analysis: Disable")

    log_lines.append("")

    # ---------- Processing Summary ----------
    summary = build_analytics_orchestrator_processing_summary(results)
    skipped = summary.get('Processing Summary', {}).get('Skipped')
    completed = summary.get('Processing Summary', {}).get('Completed')

    log_lines.append("--Processing Summary--")
    if skipped:
        log_lines.append(f"⤷ Skipped: {skipped}")
    if completed:
        log_lines.append(f"⤷ Completed: {completed}")
    log_lines.append("")

    # ---------- Component Details ----------
    details = summary.get('Details')
    if details:
        log_lines.append("--Component Details--")
        for component, detail in details.items():
            log_lines.append(f"⤷ {component}")
            if detail:
                log_lines.append(f"   ⤷ Log Entries:\n{detail}")
            else:
                log_lines.append("   ⤷ No new changes detected.")
        log_lines.append("")

    return "\n".join(log_lines)


def build_analytics_orchestrator_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build structured processing summary for AnalyticsOrchestrator.
    Returns a dict suitable for formatting.
    """
    summary = {'Processing Summary': {}, 'Details': {}}

    skipped = [k for k, v in results.items() if v is None]
    if skipped:
        summary['Processing Summary']['Skipped'] = ", ".join(skipped)

    completed = [k for k, v in results.items() if v is not None]
    summary['Processing Summary']['Completed'] = ", ".join(completed) if completed else "None"

    for comp in completed:
        level_data = results.get(comp, {})
        summary['Details'][comp] = level_data.get("log_entries_str") or "No new changes detected."

    return summary
