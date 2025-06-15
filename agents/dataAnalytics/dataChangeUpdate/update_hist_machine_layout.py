from agents.dashboardBuilder.visualize_data.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
from agents.utils import load_latest_file_from_folder
from datetime import datetime
from loguru import logger
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import shutil
import math
import os

# Decorator to validate the required columns in input DataFrame
@validate_init_dataframes({"productRecords_df": [
    'machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity',
    'recordDate', 'workingShift', 'moldNo', 'moldShot'
]})
class UpdateHistMachineLayout():
    def __init__(self, data_source: str,
                 default_dir="agents/shared_db"):

        self.logger = logger.bind(class_="UpdateHistMachineLayout")

        # Load the most recent Excel file from the folder
        self.data = load_latest_file_from_folder(data_source)

        # Extract productRecords DataFrame
        self.productRecords_df = self.data.get('productRecords')
        if self.productRecords_df is None:
            self.logger.error("❌ Sheet 'productRecords' not found.")
            raise ValueError("Sheet 'productRecords' not found.")

        # Setup output directory and file prefix
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "UpdateHistMachineLayout"
        self.filename_prefix = "update_hist_machine_layout_record"

        # Detect layout changes over time
        self.layout_changes = self._record_hist_layout_changes(self.productRecords_df)
        logger.debug("Layout changes updated: {}", self.layout_changes)
        # Start update process
        self.hist_machine_layout_record = self.update_layout_changes()
        self.plot_all()

    def update_layout_changes(self, **kwargs):
        hist_machine_layout_record = pd.DataFrame()

        # Iterate through each layout change and update historical layout record
        for hist_name, change_info in self.layout_changes.items():
            layout_change_df = self._machine_layout_record(self.productRecords_df,
                                                           change_info['recordDate'],
                                                           change_info['workingShift'])
            if hist_machine_layout_record.empty:
                hist_machine_layout_record = layout_change_df.copy()
                logger.debug("This is the first updated layout")
            else:
                logger.debug("Historical machine layouts updating...")
                hist_machine_layout_record = self._update_hist_machine_layout_record(
                    hist_machine_layout_record, layout_change_df
                )

        logger.debug("Hitorical Machine Layouts Updated: {} - {}",
                     hist_machine_layout_record.shape, hist_machine_layout_record.columns)

        return hist_machine_layout_record

    @staticmethod
    def _machine_layout_record(df, recordDate, workingShift):
        # Filter data for given date and shift, remove duplicates
        df['workingShift'] = df['workingShift'].apply(lambda x: f'{x}')
        df = df[(df['recordDate'] == recordDate) & (df['workingShift'] == workingShift)].drop_duplicates()

        # Convert recordDate to datetime
        df['recordDate'] = pd.to_datetime(df['recordDate'])

        # Take the first record per machineCode
        df_first = df.groupby('machineCode').first().reset_index()

        # Extract machineName from machineCode using regex
        df_first['machineName'] = df_first['machineCode'].str.extract(r'([A-Z]+[0-9]*)')

        # Convert date to string format for column naming
        df_first['date_str'] = df_first['recordDate'].dt.strftime('%Y-%m-%d')

        # Pivot table: machineCode as rows, each date as a column
        pivot = df_first.pivot(index='machineCode', columns='date_str', values='machineNo').reset_index()

        # Add machineName back
        pivot['machineName'] = df_first.set_index('machineCode').loc[pivot['machineCode']]['machineName'].values

        # Reorder columns
        cols = [col for col in pivot.columns if col not in ['machineCode', 'machineName']]
        return pivot[cols + ['machineName', 'machineCode']].reset_index(drop=True)

    @staticmethod
    def _update_hist_machine_layout_record(df_old, df_new):
        # Identify date columns (excluding machine metadata)
        date_cols = sorted(set(df_old.columns).union(df_new.columns) - {'machineName', 'machineCode'})

        # Merge the two layout records
        merged = pd.merge(df_old, df_new, on='machineCode', how='outer', suffixes=('_old', '_new'))

        # Update layout for each date
        for date in date_cols:
            old_col = f"{date}_old" if date in df_old.columns else None
            new_col = f"{date}_new" if date in df_new.columns else None

            if date in df_old.columns:
                merged.rename(columns={date: old_col}, inplace=True)
            else:
                merged[old_col] = None

            if date in df_new.columns:
                merged.rename(columns={date: new_col}, inplace=True)
            else:
                merged[new_col] = None

            # Prefer new data over old
            merged[date] = merged[new_col].combine_first(merged[old_col])

        # Update machineName (prefer new name)
        merged['machineName'] = merged['machineName_new'].combine_first(merged['machineName_old'])

        # Return final table with updated layout info
        final = merged[date_cols + ['machineName', 'machineCode']].copy().reset_index(drop=True)

        return final

    @staticmethod
    def _record_hist_layout_changes(df):

        # Convert dates and extract machineName from machineCode
        df['machineName'] = df['machineCode'].str.extract(r'([A-Z]+[0-9]*)')

        # Keep relevant columns, drop duplicates
        df = df[['recordDate', 'workingShift', 'machineNo', 'machineName', 'machineCode']].drop_duplicates()

        # Create a unique shift key like 'YYYY-MM-DD-S1'
        df['date_str'] = df['recordDate'].dt.strftime('%Y-%m-%d')

        df['shift_key'] = df['date_str'] + '-S' + df['workingShift'].astype(str)

        layout_dict = {}       # Stores layout string per shift
        layout_changes = {}    # Stores shifts where layout changes happened

        # Generate layout strings per shift
        for shift_key in sorted(df['shift_key'].unique()):
            shift_df = df[df['shift_key'] == shift_key]

            layout_string = '|'.join(
                shift_df[['machineCode', 'machineNo', 'machineName']]
                .drop_duplicates()
                .sort_values(by='machineCode')
                .apply(lambda row: f"{row['machineCode']}-{row['machineNo']}-{row['machineName']}", axis=1)
                .tolist()
            )

            layout_dict[shift_key] = layout_string

        # Detect changes between shifts by comparing layout strings
        prev_layout = None
        change_index = 1

        for shift_key, current_layout in layout_dict.items():
            if current_layout != prev_layout:
                layout_changes[f'layout_change_{change_index}'] = {
                    'recordDate': shift_key.split("-S")[0],
                    'workingShift': shift_key.split("-S")[1]
                }
                change_index += 1
            prev_layout = current_layout

        return layout_changes

    def plot_all(self, **kwargs):
      # Preprocessing data
      date_columns = [col for col in self.hist_machine_layout_record.columns if col not in ['machineCode', 'machineName']]
      logger.debug("Layout change dates: {}", date_columns)

      # Convert into long format
      df_melted = self.hist_machine_layout_record.melt(id_vars=['machineCode', 'machineName'],
                                                       value_vars=date_columns,
                                                       var_name='changedDate',
                                                       value_name='machineNo')
      df_melted = df_melted.dropna(subset=['machineNo'])
      df_melted['changedDate'] = pd.to_datetime(df_melted['changedDate'])
      df_melted['machineNo_numeric'] = df_melted['machineNo'].str.replace('NO.', '').astype(int)

      # Calculate change_stats
      unique_machines = df_melted['machineCode'].unique()
      n_unique = len(unique_machines)
      logger.debug("Total machines: {}", n_unique)
      colors = generate_color_palette(n_unique)
      machine_colors = dict(zip(unique_machines, colors))

      logger.info("Start charting...")
      plots_args = [
          ((df_melted, unique_machines, n_unique, machine_colors), 
           "Machine_change_layout_timeline.png", self._plot_machine_timeline),
          ((df_melted, unique_machines, colors), 
           "Top_machine_change_layout.png", self._plot_top_changes),
          ((df_melted, unique_machines, n_unique, machine_colors), 
           "Machine_level_change_layout_details.png", self._plot_individual_machines),
          (self.hist_machine_layout_record, "Machine_level_change_layout_pivot.xlsx", "Excel")
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
                  raise TypeError(f"Failed to move file {f.name}: {e}")
  
      timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
      for data, name, func in plots_args:
          path = os.path.join(newest_dir, f'{timestamp_file}_{name}')
          logger.debug('File path: {}', path)
          try:
              if isinstance(data, tuple) and func != 'Excel':
                  func(*data, path)
              elif not isinstance(data, tuple) and func != 'Excel':
                  func(data, path)
              else:
                  logger.info("Start excel file exporting...")
                  self.hist_machine_layout_record.to_excel(path, index=False)      
              log_entries.append(f"  ⤷ Saved new file: newest/{path}\n")
              logger.info("✅ Created plot: {}", path)
          except Exception as e:
              logger.error("❌ Failed to create file '{}'. Error: {}", name, str(e))
              raise TypeError(f"Failed to create file '{name}': {str(e)}")
      try:
          with open(log_path, "a", encoding="utf-8") as log_file:
              log_file.writelines(log_entries)
          logger.info("Updated change log {}", log_path)
      except Exception as e:
          logger.error("Failed to update change log {}: {}", log_path, e)
          raise TypeError(f"Failed to update change log {log_path}: {e}")

    @staticmethod
    def _plot_machine_timeline(df_melted,
                               unique_machines, n_unique,
                               machine_colors, file_path):
        fig, ax = plt.subplots(1, 1, figsize=(16, 10))

        # Plot timeline with optimized style
        for machine_code in unique_machines:
            machine_data = df_melted[df_melted['machineCode'] == machine_code].sort_values('changedDate')
            color = machine_colors[machine_code]

            # Plot line if there is more than 1 point
            if len(machine_data) > 1:
                ax.plot(machine_data['changedDate'], machine_data['machineNo_numeric'],
                      color=color, linewidth=2, alpha=0.7, marker='o', markersize=6)
            else:
                # Plot scatter if there is only 1 point
                ax.scatter(machine_data['changedDate'], machine_data['machineNo_numeric'],
                          color=color, s=80, alpha=0.8, edgecolors='white', linewidth=1)

        ax.set_title('Layout Change Timeline For All Machines', fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Timeline', fontsize=14, fontweight='bold')
        ax.set_ylabel('Machine No', fontsize=14, fontweight='bold')

        # Show all machineNo values in Y axis
        all_machine_numbers = sorted(df_melted['machineNo_numeric'].unique())
        ax.set_yticks(all_machine_numbers)
        ax.set_yticklabels([f'NO.{num:02d}' for num in all_machine_numbers])

        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(axis='x', rotation=45, labelsize=12)
        ax.tick_params(axis='y', labelsize=10)  # Scale down font size for Y axis because there are too much labels

        # Optimize legend in case too many machines
        if n_unique <= 20:
            # Default legend (if less machines)
            legend_elements = [plt.Line2D([0], [0], color=color, lw=3, label=code)
                              for code, color in machine_colors.items()]
            ax.legend(handles=legend_elements, title='Machine Code',
                    bbox_to_anchor=(1.05, 1), loc='upper left',
                    fontsize=10, title_fontsize=12)
        else:
            # Split legend into many columns if too many machines
            legend_elements = [plt.Line2D([0], [0], color=color, lw=3, label=code)
                              for code, color in machine_colors.items()]
            ncol = min(3, (n_unique + 15) // 16)  # Auto split columns
            ax.legend(handles=legend_elements, title='Machine Code',
                    bbox_to_anchor=(1.05, 1), loc='upper left',
                    fontsize=9, title_fontsize=11, ncol=ncol)

        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    @staticmethod
    def _plot_top_changes(df_melted, unique_machines, colors, file_path, top_n=15):
        # Create DataFrame for top_n changes
        change_stats = {}
        for machine_code in unique_machines:
            machine_data = df_melted[df_melted['machineCode'] == machine_code].sort_values('changedDate')
            machine_data['layoutChange'] = machine_data['machineNo_numeric'] != machine_data['machineNo_numeric'].shift()
            layout_changes = machine_data['layoutChange'].sum()
            change_stats[machine_code] = layout_changes
        logger.debug('Layout change info: {}', change_stats)
        machine_change_df = pd.DataFrame(list(change_stats.items()),
                                        columns=['machineCode', 'n_changes']).sort_values('n_changes',
                                                                                          ascending=False).head(top_n)

        fig, ax = plt.subplots(1, 1, figsize=(14, 8))
        color_list = colors[:len(machine_change_df)]
        bars = ax.bar(range(len(machine_change_df)), machine_change_df['n_changes'],
                      color=color_list, alpha=0.8, edgecolor='darkred', linewidth=1)

        ax.set_title(f'Top {top_n} machines with the most layout changes',
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('MachineCode', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of layout changes', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(machine_change_df)))
        ax.set_xticklabels(machine_change_df['machineCode'], rotation=45, ha='right')

        # Styling
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=12)

        # Add stats
        total_changes = sum(change_stats.values())
        avg_changes = total_changes / len(unique_machines)
        ax.text(0.85, 0.92, f'Total changes: {total_changes}\nAvg: {avg_changes:.1f} times/machine',
                transform=ax.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    @staticmethod
    def _plot_individual_machines(df_melted, unique_machines, n_unique, machine_colors, file_path, max_change_thershold=5):

        # Optimized layout - fewer columns for larger charts
        n_cols = min(2, n_unique) if n_unique > 4 else min(1, n_unique)
        n_rows = math.ceil(n_unique / n_cols)

        # Increase figure size for easier viewing
        fig_width = n_cols * 16
        fig_height = n_rows * 8

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))

        # Handle if there is only 1 subplot
        if n_unique == 1:
            axes = [axes]
        elif n_unique <= n_cols:
            axes = [axes] if n_cols == 1 else list(axes)
        else:
            axes = axes.flatten()

        # Get all machine numbers to set Y axis
        all_machine_numbers = sorted(df_melted['machineNo_numeric'].unique())

        # Data processing
        for idx, machine_code in enumerate(unique_machines):
            ax = axes[idx]
            process_data = df_melted[df_melted['machineCode'] == machine_code].sort_values('changedDate')
            process_data['layoutChange'] = process_data['machineNo_numeric'] != process_data['machineNo_numeric'].shift()
            machine_data = process_data[process_data['layoutChange'] == True]
            color = machine_colors[machine_code]

            # Plot line and scatter with clearly style
            if len(machine_data) > 1:
                # Plot a connection line
                ax.plot(machine_data['changedDate'], machine_data['machineNo_numeric'],
                      color=color, linewidth=2, alpha=0.7, zorder=1)
                # Plot scatters
                ax.scatter(machine_data['changedDate'], machine_data['machineNo_numeric'],
                          color=color, s=120, alpha=0.9, edgecolors='white',
                          linewidth=2.5, zorder=2)
            else: #only scatter if there is 1 point
                ax.scatter(machine_data['changedDate'], machine_data['machineNo_numeric'],
                          color=color, s=150, alpha=0.9, edgecolors='white',
                          linewidth=2, zorder=2)

            # All labels
            for _, row in machine_data.iterrows():
                # Add text position
                y_pos = row['machineNo_numeric']
                y_offset = 0.7 if y_pos < (max(all_machine_numbers) + min(all_machine_numbers)) / 2 else -0.7

                # Handle in case machineNo can be string or number
                machine_no_str = str(row['machineNo']).zfill(2) if str(row['machineNo']).isdigit() else str(row['machineNo'])

                # Add annotations
                ax.annotate(f"{machine_no_str}",
                            xy=(row['changedDate'], y_pos),
                            xytext=(0, y_offset), textcoords='offset points',
                            fontsize=11, fontweight='bold', ha='center',
                            va='bottom' if y_offset > 0 else 'top',
                            rotation=45,
                            zorder=2)

            # Styling
            changes_count = len(machine_data)
            ax.set_title(f'{machine_code}\n({changes_count} change times)',
                        fontsize=14, fontweight='bold', pad=25,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.3))

            # Grid
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8)
            ax.set_axisbelow(True)

            # Tick styling
            ax.tick_params(axis='x', rotation=45, labelsize=11, pad=5)

            # Set limits with padding
            if len(machine_data) > 0:
                # X axis padding
                time_range = machine_data['changedDate'].max() - machine_data['changedDate'].min()
                if time_range.total_seconds() > 0:
                    padding = time_range * 0.05
                    ax.set_xlim(machine_data['changedDate'].min() - padding,
                              machine_data['changedDate'].max() + padding)

            # Highlight the machines with highest changes (using thershold)
            max_changes = max(len(machine_data[machine_data['machineCode'] == mc])
                            for mc in unique_machines)
            if changes_count == max_changes and max_changes >= max_change_thershold:
                # Highlight with red border
                for spine in ax.spines.values():
                    spine.set_color('red')
                    spine.set_linewidth(2)

                # Add text indicator
                ax.text(0.07, 0.98, 'Most Changed', transform=ax.transAxes,
                      fontsize=10, fontweight='bold', color='red',
                      va='top', ha='left',
                      bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

        # Hide redundant subplots
        for j in range(n_unique, len(axes)):
            fig.delaxes(axes[j])

        # Add title and labels
        fig.suptitle('MACHINE LEVEL CHANGE TIMELINE\n(Red border = The most changed machine)',
                    fontsize=18, fontweight='bold', y=0.06)

        # Improve layout
        plt.tight_layout(rect=[0.04, 0.06, 1, 0.92])

        # Add general information
        total_changes = len(df_melted)
        avg_changes = total_changes / n_unique

        fig.text(0.9, 0.06, f'Total: {total_changes} change times | Avg: {avg_changes:.1f}/machine',
                ha='right', va='bottom', fontsize=12,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))

        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)