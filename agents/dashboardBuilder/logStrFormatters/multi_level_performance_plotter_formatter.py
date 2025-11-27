from typing import Dict, Optional, Any
from datetime import datetime
from agents.dashboardBuilder.dashboardBuilderConfigs.performance_plotflow_config import PerformancePlotflowConfig

def build_multi_level_performance_plotter_log(config: PerformancePlotflowConfig, 
                                results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for MultiLevelPerformancePlotter run.
    Does NOT log; just returns string.
    """

    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] MultiLevelPerformancePlotter Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")

    log_lines.append("⤷ Analyzer Configuration")
    log_lines.append(f"⤷ Database Annotation: {config.analytics_orchestrator_config.source_path}/{config.analytics_orchestrator_config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.analytics_orchestrator_config.databaseSchemas_path}")
    log_lines.append(f"   ⤷ Save analytics orchestrator log: {config.analytics_orchestrator_config.save_analytics_orchestrator_log}")
    if config.analytics_orchestrator_config.save_analytics_orchestrator_log:
        log_lines.append(f"       ⤷ Output Directory: {config.analytics_orchestrator_config.analytics_orchestrator_dir}")

    log_lines.append(f"   ⤷ Save multi level performance analyzer log: {config.analytics_orchestrator_config.save_multi_level_performance_analyzer_log}")
    if config.analytics_orchestrator_config.save_multi_level_performance_analyzer_log:
        log_lines.append(f"       ⤷ Output Directory: {config.analytics_orchestrator_config.multi_level_performance_analyzer_dir}")

    log_lines.append("⤷ Plotter Configuration")
    log_lines.append(f"   ⤷ Save multi level performance plotter log: {config.save_multi_level_performance_plotter_log}")
    if config.save_multi_level_performance_plotter_log:
        log_lines.append(f"       ⤷ Output Directory: {config.multi_level_performance_plotter_dir}")

    log_lines.append(f"⤷ Parallel Enabled: {config.enable_parallel}")
    log_lines.append(f"⤷ Max Workers: {config.max_workers or 'Auto'}")

    # ---------- Day-level ----------
    if config.analytics_orchestrator_config.record_date:
        log_lines.append("⤷ Day-level performance plotter: Enable")
        log_lines.append("--DayLevelDataPlotter Configuration--")
        log_lines.append(f"   ⤷ Plotter for: {config.analytics_orchestrator_config.record_date}")
        log_lines.append(f"   ⤷ Used plotter config: {config.day_level_visualization_config_path}")
    else:
        log_lines.append("⤷ Day-level performance plotter: Disable")

    # ---------- Month-level ----------
    if config.analytics_orchestrator_config.record_month:
        log_lines.append("⤷ Month-level performance plotter: Enable")
        log_lines.append("--MonthLevelDataPlotter Configuration--")
        log_lines.append(f"   ⤷ Plotter for: {config.analytics_orchestrator_config.record_month}")
        log_lines.append(f"   ⤷ Analysis date: {config.analytics_orchestrator_config.month_analysis_date}")
        log_lines.append(f"   ⤷ Used plotter config: {config.month_level_visualization_config_path or 'Default'}")
    else:
        log_lines.append("⤷ Month-level performance plotter: Disable")

    # ---------- Year-level ----------
    if config.analytics_orchestrator_config.record_year:
        log_lines.append("⤷ Year-level performance plotter: Enable")
        log_lines.append("--YearLevelDataPlotter Configuration--")
        log_lines.append(f"   ⤷ Plotter for: {config.analytics_orchestrator_config.record_year}")
        log_lines.append(f"   ⤷ Analysis date: {config.analytics_orchestrator_config.year_analysis_date}")
        log_lines.append(f"   ⤷ Used plotter config: {config.year_level_visualization_config_path or 'Default'}")
    else:
        log_lines.append("⤷ Year-level performance plotter: Disable")

    log_lines.append("")

    # ---------- Processing Summary ----------
    summary_dict = build_processing_summary(results)

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
            for sub_name, sub_result in level_result.items():
                log_lines.append(f"   ⤷ {sub_name}:")
                log_lines.append(str(sub_result) if sub_result is not None else "None")
        log_lines.append("")

    return "\n".join(log_lines)

def build_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build processing summary from results dict.
    Does NOT log; just returns a dict.
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