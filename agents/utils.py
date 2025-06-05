from pathlib import Path
import shutil
from datetime import datetime
import pandas as pd
from loguru import logger
from pyxlsb import open_workbook

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
                raise TypeError(f"Failed to move file {f.name}: {e}")

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
        raise TypeError(f"Failed to save file {new_filename}: {e}")

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.writelines(log_entries)
        logger.info("Updated change log {}", log_path)
    except Exception as e:
        logger.error("Failed to update change log {}: {}", log_path, e)
        raise TypeError(f"Failed to update change log {log_path}: {e}")

def get_sheets_xlsb(path):
    with open_workbook(path) as wb:
        return wb.sheets
                
def load_latest_file_from_folder(
    folder_path: str | Path,
    sheet_name=None,  # None or str or list[str]
    allowed_extensions=['.xlsx', '.xls', '.xlsb', '.csv']
) -> dict[str, pd.DataFrame] | None:
    
    folder_path = Path(folder_path)
    if not folder_path.is_dir():
        raise NotADirectoryError(f"{folder_path} is not a valid directory")

    valid_files = [f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() in allowed_extensions]
    if not valid_files:
        logger.warning(f"No valid files found in {folder_path}")
        return None

    latest_file = max(valid_files, key=lambda f: f.stat().st_mtime)
    logger.info("Loading latest file: {}", latest_file.name)

    try:
        suffix = latest_file.suffix.lower()
        if suffix == '.csv':
            df = pd.read_csv(latest_file)
            return {"csv": df}
        
        elif suffix == '.xlsb':
                        
            sheets_in_file = get_sheets_xlsb(latest_file)

            if sheet_name is None:
                sheets_to_load = sheets_in_file
            elif isinstance(sheet_name, str):
                sheets_to_load = [sheet_name]
            else:
                sheets_to_load = sheet_name

            valid_sheets = [sheet for sheet in sheets_to_load if sheet in sheets_in_file] or sheets_in_file

            data = {sheet: pd.read_excel(latest_file, sheet_name=sheet, engine='pyxlsb') for sheet in valid_sheets}

            return data

        else:
            xls = pd.ExcelFile(latest_file)
            sheets_in_file = xls.sheet_names

            if sheet_name is None:
                # Load all sheets
                data = {sheet: xls.parse(sheet) for sheet in sheets_in_file}
            else:
                # Convert sheet name(s) into list
                if isinstance(sheet_name, str):
                    sheet_name = [sheet_name]

                # Valid sheets
                valid_sheets = [sheet for sheet in sheet_name if sheet in sheets_in_file]

                if not valid_sheets:
                    logger.warning("No requested sheets found in file. Loading all sheets instead.")
                    data = {sheet: xls.parse(sheet) for sheet in sheets_in_file}
                else:
                    data = {sheet: xls.parse(sheet) for sheet in valid_sheets}

            return data
    except Exception as e:
        logger.error("Failed to load {}: {}", latest_file.name, e)
        raise TypeError(f"Failed to load {latest_file.name}: {e}")