from loguru import logger
from typing import Dict
from pathlib import Path
from configs.shared.agent_report_format import update_change_log
from agents.utils import save_output_with_versioning, camel_to_snake
from agents.utils import camel_to_snake, save_output_with_versioning

def save_producing_plan(input_dict: Dict) -> Dict:

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
        # Extract change data with safe defaults
        producing_planner_data = result.get('result', {})
        producing_planner_summary = result.get('planner_summary', '')
        processing_details = result.get('log_str', '')

        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data=producing_planner_data,
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=producing_planner_summary
        )
        logger.info("Results exported successfully!")

        # Persist execution record into centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            processing_details,
            "\n".join([export_log]),
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, message])
        metadata['summary'] = producing_planner_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata

def save_pending_plan(input_dict: Dict) -> Dict:

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
        # Extract change data with safe defaults
        pending_planner_data = result.get('result', {})
        pending_planner_summary = result.get('planner_summary', '')
        processing_details = result.get('log_str', '')

        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data=pending_planner_data,
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=pending_planner_summary
        )
        logger.info("Results exported successfully!")

        # Persist execution record into centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            processing_details,
            "\n".join([export_log]),
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, message])
        metadata['summary'] = pending_planner_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata