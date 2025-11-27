from typing import Dict, Optional, Any
from datetime import datetime
from agents.analyticsOrchestrator.analyticsConfigs.performance_analyticflow_config import PerformanceAnalyticflowConfig

def build_multi_level_performance_analyzer_log(config: PerformanceAnalyticflowConfig, 
                                               results: Dict[str, Optional[Dict[str, Any]]]) -> str:
    """
    Build formatted log string for MultiLevelPerformanceAnalyzer run.
    Does NOT log; just returns string.
    """
    if not isinstance(results, dict):
        raise TypeError("results must be a dict")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp_str}] MultiLevelPerformanceAnalyzer Run", ""]

    # ---------- Configuration ----------
    log_lines.append("--Configuration--")
    log_lines.append(f"⤷ Database Annotation: {config.source_path}/{config.annotation_name}")
    log_lines.append(f"⤷ Database Schemas: {config.databaseSchemas_path}")
    log_lines.append(f"⤷ Save multi-level performance analyzer log: {config.save_multi_level_performance_analyzer_log}")
    if config.save_multi_level_performance_analyzer_log:
        log_lines.append(f"   ⤷ Output Directory: {config.multi_level_performance_analyzer_dir}")

    # ---------- Levels ----------
    if getattr(config, "record_date", None):
        log_lines.append("Day Level:")
        log_lines.append(f"⤷ Record Date: {config.record_date}")
        log_lines.append(f"⤷ Save output: {config.day_save_output}")

    if getattr(config, "record_month", None):
        log_lines.append("Month Level:")
        log_lines.append(f"⤷ Record Month: {config.record_month}")
        log_lines.append(f"⤷ Analysis Date: {config.month_analysis_date or 'Not set'}")
        log_lines.append(f"⤷ Save output: {config.month_save_output}")

    if getattr(config, "record_year", None):
        log_lines.append("Year Level:")
        log_lines.append(f"⤷ Record Year: {config.record_year or 'Not set'}")
        log_lines.append(f"⤷ Analysis Date: {config.year_analysis_date or 'Not set'}")
        log_lines.append(f"⤷ Save output: {config.year_save_output}")

    log_lines.append("")

    # ---------- Processing Summary ----------
    summary_dict = build_multi_level_performance_processing_summary(results)

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
            if isinstance(level_result, list):
                log_lines.extend([str(entry) for entry in level_result])
            else:
                log_lines.append(str(level_result))
        log_lines.append("")

    return "\n".join(log_lines)

def build_multi_level_performance_processing_summary(results: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Build structured processing summary for MultiLevelPerformanceAnalyzer.
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
        if level_data and "log_entries" in level_data and level_data["log_entries"] is not None:
            summary['Details'][lv] = level_data["log_entries"]
        else:
            # Default: combine message and analysis_summary
            analysis_summary = level_data.get('analysis_summary') if level_data else "No data."
            summary['Details'][lv] = [
                f"Only process the data without saving any results.\n-{lv}_summary:\n",
                analysis_summary
            ]

    return summary
