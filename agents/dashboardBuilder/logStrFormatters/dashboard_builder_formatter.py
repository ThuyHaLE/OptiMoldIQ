from typing import Dict, Optional, Any
from datetime import datetime
from agents.dashboardBuilder.dashboardBuilderConfigs.dashboard_builder_config import DashboardBuilderConfig


def build_dashboard_builder_log(config: DashboardBuilderConfig, 
                                results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for DashboardBuilder run.
    Does NOT log; just returns string.
    """
    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] DashboardBuilder Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")
    log_lines.append(f"⤷ Database Annotation: {config.source_path}/{config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.databaseSchemas_path}")
    log_lines.append(f"⤷ Save dashboard builder log: {config.save_dashboard_builder_log}")
    if getattr(config, "save_dashboard_builder_log", False):
        log_lines.append(f"   ⤷ Output Directory: {config.dashboard_builder_dir}")

    # Processing optimization
    log_lines.append(f"⤷ Parallel Processing: {config.enable_parallel}")
    if config.enable_parallel:
        log_lines.append(f"   ⤷ Max Workers: {config.max_workers if config.max_workers else 'Auto-detect'}")

    # ---------- Hardware Change Plotter ----------
    if getattr(config, "enable_hardware_change_plotter", False):
        log_lines.append("⤷ Hardware Change Plotter: Enable")
        log_lines.append(f"   ⤷ Save hardware change plotter log: {config.save_hardware_change_plotter_log}")
        if getattr(config, "save_hardware_change_plotter_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.hardware_change_plotter_dir}")

        log_lines.append("--HardwareChangePlotter Configuration--")
        # Machine layout plotter
        if getattr(config, "enable_machine_layout_plotter", False):
            log_lines.append("   ⤷ Machine layout plotter: Enable")
            log_lines.append(f"       ⤷ Result Directory: {config.machine_layout_plotter_result_dir}")
            log_lines.append(f"       ⤷ Visualization Config: {config.machine_layout_visualization_config_path or 'Default'}")
        else:
            log_lines.append("   ⤷ Machine layout plotter: Disable")
        
        # Machine mold pair plotter
        if getattr(config, "enable_machine_mold_pair_plotter", False):
            log_lines.append("   ⤷ Machine mold pair plotter: Enable")
            log_lines.append(f"       ⤷ Result Directory: {config.machine_mold_pair_plotter_result_dir}")
            log_lines.append(f"       ⤷ Visualization Config: {config.machine_mold_pair_visualization_config_path or 'Default'}")
        else:
            log_lines.append("   ⤷ Machine mold pair plotter: Disable")

        # AnalyticsOrchestrator - HardwareChangeAnalyzer
        log_lines.append("--HardwareChangeAnalyzer Configuration--")
        log_lines.append(f"   ⤷ Save hardware change analyzer log: {config.save_hardware_change_analyzer_log}")
        if getattr(config, "save_hardware_change_analyzer_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.hardware_change_analyzer_dir}")
        log_lines.append(f"   ⤷ Machine layout tracker directory: {config.machine_layout_tracker_result_dir}")
        log_lines.append(f"   ⤷ Machine mold pair tracker directory: {config.machine_mold_pair_tracker_result_dir}")
    else:
        log_lines.append("⤷ Hardware Change Plotter: Disable")

    # ---------- Multi-Level Performance Plotter ----------
    if getattr(config, "enable_multi_level_plotter", False):
        log_lines.append("⤷ Multi-level Performance Plotter: Enable")
        log_lines.append(f"   ⤷ Save multi-level performance plotter log: {config.save_multi_level_performance_plotter_log}")
        if getattr(config, "save_multi_level_performance_plotter_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.multi_level_performance_plotter_dir}")

        log_lines.append("--MultiLevelPerformancePlotter Configuration--")
        # Day level
        if getattr(config, "record_date", None):
            log_lines.append("   ⤷ Day level")
            log_lines.append(f"       ⤷ Record Date: {config.record_date}")
            log_lines.append(f"       ⤷ Visualization Config: {config.day_level_visualization_config_path or 'Default'}")
        else:
            log_lines.append("   ⤷ Day level: Disable")
        
        # Month level
        if getattr(config, "record_month", None):
            log_lines.append("   ⤷ Month level")
            log_lines.append(f"       ⤷ Record Month: {config.record_month}")
            log_lines.append(f"       ⤷ Analysis Date: {getattr(config, 'month_analysis_date', 'Not set')}")
            log_lines.append(f"       ⤷ Visualization Config: {config.month_level_visualization_config_path or 'Default'}")
        else:
            log_lines.append("   ⤷ Month level: Disable")
        
        # Year level
        if getattr(config, "record_year", None):
            log_lines.append("   ⤷ Year level")
            log_lines.append(f"       ⤷ Record Year: {config.record_year}")
            log_lines.append(f"       ⤷ Analysis Date: {getattr(config, 'year_analysis_date', 'Not set')}")
            log_lines.append(f"       ⤷ Visualization Config: {config.year_level_visualization_config_path or 'Default'}")
        else:
            log_lines.append("   ⤷ Year level: Disable")

        # AnalyticsOrchestrator - MultiLevelPerformanceAnalyzer
        log_lines.append("--MultiLevelPerformanceAnalyzer Configuration--")
        log_lines.append(f"   ⤷ Save multi-level performance analyzer log: {config.save_multi_level_performance_analyzer_log}")
        if getattr(config, "save_multi_level_performance_analyzer_log", False):
            log_lines.append(f"       ⤷ Output Directory: {config.multi_level_performance_analyzer_dir}")
    else:
        log_lines.append("⤷ Multi-level Performance Plotter: Disable")

    log_lines.append("")

    # ---------- Processing Summary ----------
    summary = build_dashboard_builder_processing_summary(results)
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
                log_lines.append("   ⤷ No visualizations generated.")
        log_lines.append("")

    return "\n".join(log_lines)


def build_dashboard_builder_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build structured processing summary for DashboardBuilder.
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
        summary['Details'][comp] = level_data.get("log_entries_str") or "No visualizations generated."

    return summary