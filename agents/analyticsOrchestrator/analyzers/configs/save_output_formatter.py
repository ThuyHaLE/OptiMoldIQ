from agents.utils import save_output_with_versioning, camel_to_snake
from configs.shared.agent_report_format import update_change_log
from datetime import datetime
from loguru import logger
from typing import Dict, Tuple
from pathlib import Path
import pandas as pd
import json

def save_analyzer_reports(input_dict: Dict) -> Dict:

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
        excel_data = result.get('processed_data', {})

        # Normalize value: dict → DataFrame
        for k, v in excel_data.items():
            v = ensure_dataframe(v)
            excel_data[k] = v

            if not isinstance(k, str):
                raise TypeError(f"Invalid key type: {type(k)}")

        analysis_summary = result.get('analysis_summary', '')
        processing_details = result.get('log', '')

        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data=excel_data,
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=analysis_summary
        )
        logger.info("Results exported successfully!")

        # Persist execution record into centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            processing_details,
            export_log,
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, message])
        metadata['summary'] = analysis_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save processed data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata

def ensure_dataframe(v):
    if isinstance(v, pd.DataFrame):
        return v
    if isinstance(v, dict):
        if all(isinstance(x, dict) for x in v.values()):
            return pd.DataFrame.from_dict(v, orient="index")
        return pd.DataFrame(v)
    raise TypeError(f"Cannot convert {type(v)} to DataFrame")

def save_machine_layout(input_dict: Dict) -> Dict:
    """
    Save machine layout change results.

    This function handles the persistence layer for machine layout change detection:
    - Early exit if no change is detected (NO_OP case)
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

    # NO_OP branch: no detected layout changes → skip all saving logic
    if not result.get('has_change', False):
        logger.info("No new layout changes detected.")
        return {
            'status': 'skipped_no_changes',  # ✨ More specific
            'export_log': "No new layout changes detected. Skipping save.",
            'summary': '',
            'reason': 'no_changes'  # ✨ Explicit reason
            }

    metadata = {
        'status': 'unknown',
        'export_log': '',
        'summary': ''
    }

    try:
        # Extract change data with safe defaults
        logger.info("New layout changes detected.")

        machine_layout_hist_change = result.get(
            'changes_data', {}
        ).get('machine_layout_hist_change', pd.DataFrame())

        tracking_summary = result.get('tracker_summary', '')
        processing_details = result.get('log', '')

        # Export change data to Excel with versioning support
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data={"machineLayoutChange": machine_layout_hist_change},
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=tracking_summary
        )
        logger.info("Results exported successfully!")

        # Persist first-pair change history as JSON snapshots
        layout_changes_dict = result.get('changes_dict', {})
        save_log = save_layout_change(
            layout_changes_dict=layout_changes_dict,
            output_dir=Path(output_dir),
            filename_prefix=f"{camel_to_snake(agent_id)}_{result.get('record_date')}"
        )

        # Persist execution record into centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            processing_details,
            "\n".join([export_log, save_log]),
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, save_log, message])
        metadata['summary'] = tracking_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata

def save_mold_machine_pair(input_dict: Dict) -> Dict:
    """
    Save machine–mold pairing change results.

    Responsibilities:
    - Early exit on NO_OP case
    - Export analytical Excel reports (pivot tables, unmatched tonnage)
    - Persist first-pair change history as JSON snapshots
    - Update centralized change log
    - Return standardized metadata

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

    # NO_OP branch: no detected pairing changes
    if not result.get('has_change', False):
        logger.info("No new machine-mold pair changes detected.")
        return {
            'status': 'skipped_no_changes',  # ✨ More specific
            'export_log': 'No new machine-mold pair changes detected. Skipping save.',
            'summary': '',
            'reason': 'no_changes'  # ✨ Explicit reason
        }

    metadata = {
        'status': 'unknown',
        'export_log': '',
        'summary': ''
    }
    
    try:
        # Extract change datasets
        logger.info("New machine-mold pair changes detected.")
        mold_machine_df = result.get('changes_data', {}).get(
            'mold_machine_df', pd.DataFrame()
        )
        first_paired_mold_machine = result.get('changes_data', {}).get(
            'first_paired_mold_machine', pd.DataFrame()
        )

        # Prepare pivot tables for reporting
        pivot_machine_mold, pivot_mold_machine = prepare_privot(
            first_paired_mold_machine
        )

        # Compose Excel export payload
        excel_data = {
            "moldTonageUnmatched": mold_machine_df[
                mold_machine_df['tonnageMatched'] == False
            ],
            "machineMoldFirstRunPair": pivot_machine_mold,
            "moldMachineFirstRunPair": pivot_mold_machine
        }

        tracking_summary = result.get('tracker_summary', '')
        metadata['summary'] = tracking_summary

        # Export analytical results to Excel with versioning
        logger.info("Start excel file exporting...")
        export_log = save_output_with_versioning(
            data=excel_data,
            output_dir=Path(output_dir),
            filename_prefix=camel_to_snake(agent_id),
            report_text=tracking_summary
        )
        logger.info("Results exported successfully!")

        # Persist first-pair change history as JSON snapshots
        change_hist_dict = result.get('changes_dict', {})
        save_log = save_change_hist(
            change_hist_dict=change_hist_dict,
            output_dir=Path(output_dir),
            filename_prefix=f"{camel_to_snake(agent_id)}_{result.get('record_date')}"
        )
        
        # Update centralized change log
        message = update_change_log(
            agent_id,
            change_log_header,
            execution_summary,
            result.get('log', ''),
            "\n".join([export_log, save_log]),
            Path(change_log_path)
        )

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = "\n".join([export_log, save_log, message])
        metadata['summary'] = tracking_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'
        metadata['error'] = str(e)

    return metadata

def save_layout_change(
        layout_changes_dict: Dict[str, dict],
        output_dir: str | Path,
        filename_prefix: str
        ) -> str:
    """
    Persist machine layout change history as JSON files.

    Each entry in the change history is saved as an individual JSON snapshot,
    allowing chronological inspection and auditability.

    Args:
        layout_changes_dict (Dict[str, dict]): Time-indexed change records
        output_dir (str | Path): Base output directory
        filename_prefix (str): Prefix used for saved filenames

    Returns:
        str: Human-readable log summary of saved files
    """
    try:
        # Save layout changes
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M")
        json_filepath = Path(output_dir) / "newest" / f"{timestamp_file}_{filename_prefix}.json"
    
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(layout_changes_dict, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Layout changes saved to {json_filepath}")
        return f"  ⤷ Saved new json file: {json_filepath}"
    
    except Exception as e:
        logger.error("Failed to analyze layout changes: {}", e)
        raise OSError(f"Failed to analyze layout changes: {e}")
    
def save_change_hist(
    change_hist_dict: Dict[str, dict],
    output_dir: str | Path,
    filename_prefix: str
    ) -> str:
    """
    Persist machine–mold first-pair change history as JSON files.

    Each entry in the change history is saved as an individual JSON snapshot,
    allowing chronological inspection and auditability.

    Args:
        change_hist_dict (Dict[str, dict]): Time-indexed change records
        output_dir (str | Path): Base output directory
        filename_prefix (str): Prefix used for saved filenames

    Returns:
        str: Human-readable log summary of saved files
    """

    pair_change_dir = Path(output_dir) / "newest" / "pair_changes"
    pair_change_dir.mkdir(parents=True, exist_ok=True)

    log_entries = []

    try:
        for time_str in change_hist_dict.keys():
            timestamp = datetime.fromisoformat(time_str).strftime("%Y-%m-%d")
            json_filepath = pair_change_dir / f"{timestamp}_{filename_prefix}.json"

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(
                    change_hist_dict[time_str],
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            log_entries.append(f"  ⤷ Saved new json file: {json_filepath}")

        logger.info(
            f"Machine-mold pair changes saved to {pair_change_dir}, "
            f"total {len(change_hist_dict)} files"
        )
        return "\n".join(log_entries)

    except Exception as e:
        logger.error("Failed to analyze machine-mold pair changes: {}", e)
        raise OSError(f"Failed to analyze machine-mold pair changes: {e}")


def prepare_privot(
    first_paired_mold_machine: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate pivot tables for machine–mold first pairing analysis.

    Returns two complementary pivot views:
    - Machine → Mold
    - Mold → Machine

    Args:
        first_paired_mold_machine (pd.DataFrame): Raw first-pair dataset

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Pivoted DataFrames
    """

    pivot_machine_mold = first_paired_mold_machine.pivot(
        index='machineCode',
        columns='moldNo',
        values='firstDate'
    )

    pivot_mold_machine = first_paired_mold_machine.pivot(
        index='moldNo',
        columns='machineCode',
        values='firstDate'
    )

    return pivot_machine_mold, pivot_mold_machine