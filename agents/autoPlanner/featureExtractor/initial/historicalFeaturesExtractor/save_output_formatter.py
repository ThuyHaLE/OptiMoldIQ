import pandas as pd
from loguru import logger
from typing import Dict
from pathlib import Path
from configs.shared.agent_report_format import update_change_log
from agents.utils import save_output_with_versioning, camel_to_snake
from agents.utils import camel_to_snake, save_output_with_versioning, update_weight_and_save_confidence_report

def save_mold_stability_index(input_dict: Dict) -> Dict:

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
        mold_stability_index = result.get('mold_stability_index', pd.DataFrame())
        index_calculation_summary = result.get('index_calculation_summary', '')
        processing_details = result.get('log_str', '')

        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data={"moldStabilityIndex": mold_stability_index},
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=index_calculation_summary
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
        metadata['summary'] = index_calculation_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata

def save_mold_machine_weights(input_dict: Dict) -> Dict:

    agent_id = input_dict.get("name")
    result = input_dict.get("result")
    execution_summary = input_dict.get("execution_summary")
    output_dir = input_dict.get("output_dir")
    change_log_paths = input_dict.get("change_log_path")
    change_log_path = change_log_paths["mold_machine_weights_change_log_path"]
    weights_hist_path = change_log_paths["mold_machine_weights_hist_path"]
    change_log_header = input_dict.get("change_log_header")

    metadata = {
        'status': 'unknown',
        'export_log': '',
        'summary': ''
    }

    try:
        # Extract change data with safe defaults
        enhanced_weights = result.get('enhanced_weights', {})
        confidence_report_text = result.get('confidence_report_text', '')
        processing_details = result.get('log_str', '')
                    
        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = update_weight_and_save_confidence_report(
            report_text = confidence_report_text,
            output_dir = Path(output_dir),
            filename_prefix = camel_to_snake(agent_id),
            enhanced_weights = enhanced_weights,
            weights_hist_path = weights_hist_path)
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
        metadata['summary'] = confidence_report_text
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata