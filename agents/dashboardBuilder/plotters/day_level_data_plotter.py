from agents.dashboardBuilder.visualize_data.machine_level_yield_efficiency import create_machine_level_yield_efficiency_chart
from agents.dashboardBuilder.visualize_data.shift_level_yield_analysis import create_shift_level_yield_chart
from agents.dashboardBuilder.visualize_data.adapted_shift_level_yield_analysis import create_adapted_shift_level_yield_chart
from agents.dashboardBuilder.visualize_data.machine_level_mold_analysis import create_machine_level_mold_analysis_chart
from agents.dashboardBuilder.visualize_data.shift_level_mold_efficiency_analysis import create_shift_level_mold_efficiency_chart
from agents.dataAnalytics.multiLevelDataAnalytics.day_level_data_analytics import DayLevelDataAnalytics
from loguru import logger
from pathlib import Path
from datetime import datetime
import shutil
import os

class DayLevelDataPlotter:
    def __init__(self, 
                 selected_date: str,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):

        self.logger = logger.bind(class_="DayLevelDataPlotter")

        self.selected_date = selected_date
        
        self.day_level_data_analytics = DayLevelDataAnalytics(self.selected_date,
                                                              source_path, 
                                                              annotation_name,
                                                              databaseSchemas_path,
                                                              default_dir)

        (self.filtered, self.summary, self.shift_summary, 
         self.merged_count, self.mold_shots, self.single_mold_df) = self.day_level_data_analytics.prepare_data()

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DayLevelDataPlotter"

    def plot_all(self, **kwargs):

        logger.info("Start charting...")
        plots_args = [
            (self.summary, "Machine_level_yield_efficiency_chart", create_machine_level_yield_efficiency_chart),
            (self.shift_summary, "Shift_level_yield_chart", create_shift_level_yield_chart),
            (self.filtered, "Detailed_shift_level_yield_chart", create_adapted_shift_level_yield_chart),
            ((self.merged_count, self.mold_shots), "Mold_analysis_by_machine", create_machine_level_mold_analysis_chart),
            (self.single_mold_df, "Mold_efficient_by_machine_and_working_shift", create_shift_level_mold_efficiency_chart)
        ]

        log_path = self.output_dir / "change_log.txt"
        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        log_entries = [f"[{timestamp_str}] Saving new version...\n"]

        newest_dir = self.output_dir / "newest"
        newest_dir.mkdir(parents=True, exist_ok=True)
        historical_dir = self.output_dir / "historical_db"
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
        for data, name, func in plots_args:
          path = os.path.join(newest_dir, f'{timestamp_file}_{self.selected_date}_{name}.png')
          try:
              if isinstance(data, tuple):
                  func(*data, path)
              else:
                  func(data, path)
              log_entries.append(f"  ⤷ Saved new file: newest/{path}\n")
              logger.info("✅ Created plot: {}", path)
          except Exception as e:
              logger.error("❌ Failed to create plot '{}'. Error: {}", name, str(e))
              raise OSError(f"Failed to create plot '{name}': {str(e)}")
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            logger.info("Updated change log {}", log_path)
        except Exception as e:
            logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")