from agents.dataPipelineOrchestrator.utils import dataframes_equal_fast
from configs.shared.agent_report_format import update_change_log

from datetime import datetime
from loguru import logger
from typing import Dict, Any
from pathlib import Path
import json
import shutil
import pandas as pd
import os

def save_collected_data(input_dict: Dict) -> Dict:
    
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
        collected_data = result.get('collected_data', {})
        path_annotation = result.get('path_annotation', {})
        processing_details = result.get('log_str', '')

        # Export change data to Excel with versioning support
        logger.info("Start parquet file exporting...")
        export_log = save_databases(output_dir, collected_data,
                                    path_annotation, change_log_path)
        logger.info("Results exported successfully!")

        # Generate validation summary
        from configs.shared.dict_based_report_generator import DictBasedReportGenerator
        reporter = DictBasedReportGenerator(use_colors=False)
        collecting_summary = "\n".join(reporter.export_report(collected_data))

        # Aggregate export information for upstream orchestration/logging
        metadata['export_log'] = export_log
        metadata['summary'] = collecting_summary
        metadata['status'] = 'success'

    except Exception as e:
        error_msg = f"Failed to save tracking data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        metadata['export_log'] = error_msg
        metadata['summary'] = ''
        metadata['status'] = 'failed'

    return metadata

def save_databases(
    database_dir: Path | str,
    collected_data: Dict[str, Any],
    path_annotation: Dict[str, Any],
    annotations_path: Path | str) -> str:

    """
    Save databases with versioning based on annotations.
    
    Args:
        database_dir: Directory to store databases
        collected_data: Dict of {db_type: {db_name: DataFrame}}
        path_annotation: Dict mapping db_name to file paths (already loaded from pipeline)
        annotations_path: Path to save the annotations JSON file
        
    Returns:
        Log string of operations performed
    """
    
    database_dir = Path(database_dir)
    database_dir.mkdir(parents=True, exist_ok=True)
    annotations_path = Path(annotations_path)
    
    # Create parent directory for annotations file if it doesn't exist
    annotations_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp_now = datetime.now()
    timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M%S")

    log_entries = [f"[{timestamp_str}] Saving new version..."]

    newest_dir = database_dir / "newest"
    newest_dir.mkdir(parents=True, exist_ok=True)
    historical_dir = database_dir / "historical_db"
    historical_dir.mkdir(parents=True, exist_ok=True)

    # Check if this is first time initialization
    is_first_run = (path_annotation == {})
    
    if is_first_run:
        log_entries.append("\n🆕 First run detected - saving all databases without comparison")
    else:
        log_entries.append("\n🔄 Existing annotations found - comparing and updating changed databases")

    # Process each database
    for db_type, db_info in collected_data.items():
        log_entries.append(f"\nProcessing {db_type}:")
        
        for db_name, db_df in db_info.items():
            log_entries.append(f"\n  📊 {db_name}:")
            
            if is_first_run:
                # First run: save everything without comparison
                log_entries.append(f"  ⤷ First run - saving without comparison")
                
                # Save new dataframe
                new_filename = f"{timestamp_file}_{db_name}.parquet"
                new_path = newest_dir / new_filename
                db_df.to_parquet(new_path, engine='pyarrow', compression='snappy', index=False)

                # Update path annotation
                path_annotation[db_name] = str(new_path)
                log_entries.append(f"  ⤷ Saved: {new_filename}")
                logger.info("Saved new file: {}", new_path)
                
            else:
                # Not first run: compare with existing data
                existed_df_path = path_annotation.get(db_name)
                
                if existed_df_path and os.path.exists(existed_df_path):
                    log_entries.append(f"  ⤷ Loading existing data from: {Path(existed_df_path).name}")
                    existed_db_df = pd.read_parquet(existed_df_path)
                else:
                    log_entries.append(f"  ⤷ No existing data found (new database)")
                    existed_db_df = pd.DataFrame()
                
                # Compare dataframes
                log_entries.append(f"  ⤷ Comparing current vs existing data...")
                are_equal = dataframes_equal_fast(db_df, existed_db_df)

                if are_equal:
                    log_entries.append(f"  ⤷ ✓ No changes detected - data is up to date")
                else:
                    log_entries.append(f"  ⤷ ✓ Data has changed - saving new version")
                    
                    # Move old file to historical if exists
                    if existed_df_path and os.path.exists(existed_df_path):
                        old_filename = Path(existed_df_path).name
                        historical_path = historical_dir / old_filename
                        shutil.move(str(existed_df_path), str(historical_path))
                        log_entries.append(f"  ⤷ Archived: {old_filename} → historical_db/")
                        logger.info("Moved old file {} → {}", existed_df_path, historical_path)

                    # Save new dataframe
                    new_filename = f"{timestamp_file}_{db_name}.parquet"
                    new_path = newest_dir / new_filename
                    db_df.to_parquet(new_path, engine='pyarrow', compression='snappy', index=False)

                    # Update path annotation
                    path_annotation[db_name] = str(new_path)
                    log_entries.append(f"  ⤷ Saved: {new_filename}")
                    logger.info("Saved new file: {}", new_path)

    # Save updated path annotations (works for both first run and updates)
    try:
        with open(annotations_path, "w", encoding="utf-8") as f:
            json.dump(path_annotation, f, ensure_ascii=False, indent=4)
        logger.info("Updated path annotations at {}", annotations_path)
        log_entries.append(f"\n✅ Updated annotations: {annotations_path}")
    except Exception as e:
        logger.error("Failed to update path annotations {}: {}", annotations_path, e)
        raise OSError(f"Failed to update annotation file {annotations_path}: {e}")

    return "\n".join(log_entries)