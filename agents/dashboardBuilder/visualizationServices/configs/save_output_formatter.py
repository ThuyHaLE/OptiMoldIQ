from agents.utils import save_output_with_versioning, camel_to_snake, write_text_report
from configs.shared.agent_report_format import update_change_log
from loguru import logger
from typing import Dict
from pathlib import Path
import pandas as pd

def save_reports(input_dict: Dict) -> Dict:

    """
    Save analyzer reports.

    This function handles the persistence layer for multi-level performance analyzing:
    - Export change data to versioned Excel files
    - Update centralized change log
    - Return standardized metadata for orchestrator consumption

    Args:
        input_dict (Dict): Aggregated execution context from agent/orchestrator

    Returns:
        Dict: Metadata including export logs and execution summary
    """

    # Extract execution context
    agent_id = input_dict.get("name")
    result = input_dict.get("result")
    execution_summary = input_dict.get("execution_summary")
    output_dir = input_dict.get("output_dir")
    change_log_path = input_dict.get("change_log_path")
    change_log_header = input_dict.get("change_log_header")

    metadata = {
        'status': 'unknown',
        'export_log': '',
        'summary': ''
    }

    try:
        # Extract processed data with safe defaults
        visualized_data = result.get('visualized_data', {})

        pipeline_summary = result.get('pipeline_summary', '')
        pipeline_report = result.get('pipeline_report', '')
        processing_details = result.get('log', '')
 
        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data=visualized_data,
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=pipeline_summary
        )
        logger.info("Results exported successfully!")

        write_report_log = ""
        if pipeline_report and pipeline_report.strip():
            # Save early warning report
            report_path = Path(output_dir) / "newest" / f"{camel_to_snake(agent_id)}_early_warning_report.txt"
            write_report_log = write_text_report(report_path, pipeline_report)
            logger.info("Early warning report exported successfully!") 

        # Persist execution record into centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            processing_details,
            "\n".join([export_log, write_report_log]),
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, write_report_log,message])
        metadata['summary'] = pipeline_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save processed data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata