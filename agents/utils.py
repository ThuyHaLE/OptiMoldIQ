from pathlib import Path
import shutil
from datetime import datetime
import pandas as pd
from loguru import logger
import os
import json 


def save_output_with_versioning(
    data: dict[str, pd.DataFrame],
    output_dir: str | Path,
    filename_prefix: str = "output",
    file_format: str = 'xlsx',
):  
    if not isinstance(data, dict):
        logger.error("❌ Expected data to be a dict[str, pd.DataFrame] but got: {}", type(data))
        raise TypeError(f"Expected data to be a dict[str, pd.DataFrame] but got: {type(data)}")

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, pd.DataFrame):
            logger.error("❌ Invalid dict contents: key type {}, value type {}", type(k), type(v))
            raise TypeError(f"Expected dict keys to be str and values to be pd.DataFrame, but got key: {type(k)}, value: {type(v)}")

    output_dir = Path(output_dir)
    log_path = output_dir / "change_log.txt"
    timestamp_now = datetime.now()
    timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
    log_entries = [f"[{timestamp_str}] Saving new version...\n"]

    newest_dir = output_dir / "newest"
    newest_dir.mkdir(parents=True, exist_ok=True)
    historical_dir = output_dir / "historical_db"
    historical_dir.mkdir(parents=True, exist_ok=True)

    # Move old files to historical_db
    for f in newest_dir.iterdir():
        if f.is_file():
            try:
                dest = historical_dir / f.name
                shutil.move(str(f), dest)
                log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
            except Exception as e:
                logger.error("Failed to move file {}: {}", f.name, e)
                raise OSError(f"Failed to move file {f.name}: {e}")

    timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
    new_filename = f"{timestamp_file}_{filename_prefix}.{file_format}"
    new_path = newest_dir / new_filename

    try:
        with pd.ExcelWriter(new_path, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        log_entries.append(f"  ⤷ Saved new file: newest/{new_filename}\n")
        logger.info("Saved new file: newest/{}", new_filename)
    except Exception as e:
        logger.error("Failed to save file {}: {}", new_filename, e)
        raise OSError(f"Failed to save file {new_filename}: {e}")

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.writelines(log_entries)
        logger.info("Updated change log {}", log_path)
    except Exception as e:
        logger.error("Failed to update change log {}: {}", log_path, e)
        raise OSError(f"Failed to update change log {log_path}: {e}")

def load_annotation_path(source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                         annotation_name: str = "path_annotations.json"):
  annotation_path = Path(source_path) / annotation_name

  #Load existing path annotations
  if os.path.exists(annotation_path):
      with open(annotation_path, "r", encoding="utf-8") as f:
        path_annotation = json.load(f)
      logger.debug("Loaded existing annotation file: {}", path_annotation)
      return path_annotation
  else:
      logger.error("No existing annotation - please call dataLoader first...")
      raise FileNotFoundError(f"No existing annotation - please call dataLoader first: {annotation_path}")