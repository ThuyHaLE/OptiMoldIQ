from agents.decorators import validate_init_dataframes
from agents.dashboardBuilder.visualize_data.utils import generate_color_palette, save_plot
from agents.utils import load_annotation_path
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from datetime import datetime
import shutil
import os

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
})

class UpdateHistMoldOverview():
    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):

        self.logger = logger.bind(class_="UpdateHistMoldOverview")

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent, 
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path, 
                                                    annotation_name)

        # Extract productRecords DataFrame
        productRecords_path = self.path_annotation.get('productRecords')
        if not productRecords_path or not os.path.exists(productRecords_path):
            self.logger.error("❌ Path to 'productRecords' not found or does not exist.")
            raise FileNotFoundError("Path to 'productRecords' not found or does not exist.")
        self.productRecords_df = pd.read_parquet(productRecords_path)

        
        # Extract moldInfo DataFrame
        moldInfo_path = self.path_annotation.get('moldInfo')
        if not moldInfo_path or not os.path.exists(moldInfo_path):
            self.logger.error("❌ Path to 'moldInfo' not found or does not exist.")
            raise FileNotFoundError("Path to 'moldInfo' not found or does not exist.")
        self.moldInfo_df = pd.read_parquet(moldInfo_path)


        # Extract machineInfo DataFrame
        machineInfo_path = self.path_annotation.get('machineInfo')
        if not machineInfo_path or not os.path.exists(machineInfo_path):
            self.logger.error("❌ Path to 'machineInfo' not found or does not exist.")
            raise FileNotFoundError("Path to 'machineInfo' not found or does not exist.")
        self.machineInfo_df = pd.read_parquet(machineInfo_path)

        # Setup output directory and file prefix
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "UpdateHistMoldOverview"
        self.filename_prefix = "update_hist_mold_overview"

    def process_data(self, **kwargs):
        mold_machine_df = pd.merge(pd.merge(self.productRecords_df[['recordDate', 'machineCode', 'moldNo']],
                                          self.moldInfo_df[['moldNo', 'machineTonnage',	'acquisitionDate']],
                                          on='moldNo'),
                                          self.machineInfo_df[['machineCode', 'machineName']].drop_duplicates().reset_index(drop=True),
                                          on= 'machineCode'
                                          )
        mold_machine_df.columns = ['recordDate',	'machineCode',	'moldNo',
                                          'suitedMachineTonnages',	'acquisitionDate',	'machineType']
        mold_machine_df['acquisitionDate'] = pd.to_datetime(mold_machine_df['acquisitionDate'])

        def _check_match(machineCode, suitedMachineTonnages):
          try:
            ton_list = suitedMachineTonnages.split('/')
          except:
            ton_list = [str(suitedMachineTonnages)]
          return any(ton in str(machineCode) for ton in ton_list)

        #Check if mold tonage matches machine tonage
        mold_machine_df['tonnageMatched'] = mold_machine_df.apply(lambda row: _check_match(row['machineCode'],
                                                                                                        row['suitedMachineTonnages']),
                                                                                axis=1)
        
        #Create a summary of the number of tonnage types used for each mold.
        def create_mold_tonnage_summary(mold_machine_df):
            return (mold_machine_df.groupby('moldNo', as_index=False)
                    .agg(usedMachineTonnage=('machineType', lambda x: x.unique().tolist()),
                        usedTonnageCount=('machineType', 'nunique')))
        used_mold_machine_df = create_mold_tonnage_summary(mold_machine_df)

        # Create statistics
        used_mold_machine_stats = {
            'Total Molds': len(used_mold_machine_df),
            'Average Tonnage Types per Mold': used_mold_machine_df['usedTonnageCount'].mean(),
            'Max Tonnage Types': used_mold_machine_df['usedTonnageCount'].max(),
            'Min Tonnage Types': used_mold_machine_df['usedTonnageCount'].min(),
            'Median Tonnage Types': used_mold_machine_df['usedTonnageCount'].median(),
            'Standard Deviation': used_mold_machine_df['usedTonnageCount'].std()
        }
        logger.info("\n📈 Summary statistics:")
        for key, value in used_mold_machine_stats.items():
            if isinstance(value, float):
                logger.info(f"  • {key}: {value:.2f}")
            else:
                logger.info(f"  • {key}: {value}")
        
        # Get first day of each moldNo
        first_use_mold_df = mold_machine_df.groupby(['moldNo', 'acquisitionDate'])['recordDate'].min().reset_index(name='firstDate')
        # Calculate the time gap between acquisition and first use
        first_use_mold_df['daysDifference'] = (first_use_mold_df['firstDate'] - first_use_mold_df['acquisitionDate']).dt.days
        first_use_mold_stats = {
            'Total molds analyzed': len(first_use_mold_df),
            'Average days between acquisition and first use': first_use_mold_df['daysDifference'].mean(),
            'Median days between acquisition and first use': first_use_mold_df['daysDifference'].median(),
            'Standard deviation': first_use_mold_df['daysDifference'].std(),
            'Min gap (days)': first_use_mold_df['daysDifference'].min(),
            'Max gap (days)': first_use_mold_df['daysDifference'].max()
            }
        logger.info("\n📈 Summary statistics:")
        for key, value in first_use_mold_stats.items():
            if isinstance(value, float):
                logger.info(f"  • {key}: {value:.2f}")
            else:
                logger.info(f"  • {key}: {value}")

        # Molds with negative gap (use before buy?)
        negative_gap = first_use_mold_df[first_use_mold_df['daysDifference'] < 0]
        if len(negative_gap) > 0:
            logger.debug("\nWarning: {} molds have negative gap (used before acquisition). \nThese molds might have data quality issues:",
                        len(negative_gap),
                        negative_gap[['moldNo', 'acquisitionDate', 'firstDate', 'daysDifference']].head())
    
        # Get first day of each pair (machineCode, moldNo)
        paired_mold_machine_df = mold_machine_df.groupby(['machineCode', 'moldNo', 
                                                          'acquisitionDate'])['recordDate'].min().reset_index(name='firstDate')
        paired_mold_machine_df = paired_mold_machine_df[['firstDate', 'machineCode', 
                                                         'moldNo', 'acquisitionDate']].sort_values('machineCode').reset_index(drop=True)

        # Create pivot: machineCode is rows, moldNo is columns
        pivot_machine_mold = paired_mold_machine_df.pivot(index='machineCode', 
                                                          columns='moldNo', values='firstDate')

        # Create pivot: moldNo is rows, machineCode is columns
        pivot_mold_machine = paired_mold_machine_df.pivot(index='moldNo', 
                                                          columns='machineCode', values='firstDate')
            
        return mold_machine_df, first_use_mold_df, paired_mold_machine_df, used_mold_machine_df, pivot_machine_mold, pivot_mold_machine

    def update_and_plot(self, **kwargs):

        #Process data
        logger.info("Data processing...")
        (self.mold_machine_df, 
         self.first_use_mold_df, self.paired_mold_machine_df, 
         self. used_mold_machine_df, 
         self.pivot_machine_mold, self.pivot_mold_machine) = self.process_data()
        
        #Plot data
        logger.info("Start charting...")
        plots_args = [
            (self.mold_machine_df[self.mold_machine_df['tonnageMatched'] == False], "Tonage_machine_mold_not_matched.xlsx", "Excel"),
            (self.pivot_machine_mold, "Machine_mold_first_run_pair.xlsx", "Excel"),
            (self.pivot_mold_machine, "Mold_machine_first_run_pair.xlsx", "Excel"),
            
            (self.first_use_mold_df, "Comparison_of_acquisition_and_first_use.png", self.compare_acquisition_firstuse),
            (self.first_use_mold_df, "Time_Gap_of_acquisition_and_first_use.png", self.timegap_acquisition_firstuse),
            (self.first_use_mold_df, "Top_Bottom_molds_gap_time_analysis.png", self.top_bot_mold_gaptime_analysis),

            (self.paired_mold_machine_df, "Number_of_molds_first_run_on_each_machine.png", self.machine_level_mold_count),
            
            (self.used_mold_machine_df, "Top_molds_tonnage.png", self.plot_top_molds_tonnage),
            (self.used_mold_machine_df, "Bottom_molds_tonnage.png", self.plot_bottom_molds_tonnage),
            (self.used_mold_machine_df, "Tonnage_distribution.png", self.plot_tonnage_distribution),
            (self.used_mold_machine_df, "Tonnage_proportion.png", self.plot_tonnage_proportion_pie),
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
            path = os.path.join(newest_dir, f'{timestamp_file}_{name}')
            logger.debug('File path: {}', path)
            try:
                if isinstance(data, tuple) and func != 'Excel':
                    func(*data, path)
                elif not isinstance(data, tuple) and func != 'Excel':
                    func(data, path)
                else:
                    logger.info("Start excel file exporting...")
                    data.to_excel(path, index=False)      
                log_entries.append(f"  ⤷ Saved new file: newest/{path}\n")
                logger.info("✅ Created plot: {}", path)
            except Exception as e:
                logger.error("❌ Failed to create file '{}'. Error: {}", name, str(e))
                raise OSError(f"Failed to create file '{name}': {str(e)}")
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_entries)
            logger.info("Updated change log {}", log_path)
        except Exception as e:
            logger.error("Failed to update change log {}: {}", log_path, e)
            raise OSError(f"Failed to update change log {log_path}: {e}")

    #Plot the top N molds with the most machine tonnage types.
    @staticmethod
    def plot_top_molds_tonnage(used_mold_machine_df, 
                              file_path, top_n=20, figsize=(14, 6)):
        top_molds = used_mold_machine_df.nlargest(top_n, 'usedTonnageCount')
        colors = generate_color_palette(len(top_molds))

        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.bar(range(len(top_molds)), 
                      top_molds['usedTonnageCount'], 
                      color=colors
                      )

        # Optimize labels
        ax.set_xticks(range(len(top_molds)))
        ax.set_xticklabels(top_molds['moldNo'], rotation=45, ha='right')

        # Add values on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)

        ax.set_xlabel('Mold No', fontweight='bold')
        ax.set_ylabel('Number of Used Tonnages', fontweight='bold')
        ax.set_title(f'Top {top_n} Molds with Most Machine Tonnage Types Used',
                    fontweight='bold', fontsize=14)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    #Plot the top N molds with the fewest machine tonnage types.
    @staticmethod
    def plot_bottom_molds_tonnage(used_mold_machine_df, 
                                  file_path, bottom_n=20, figsize=(14, 6)):
        bottom_molds = used_mold_machine_df.nsmallest(bottom_n, 'usedTonnageCount')
        colors = generate_color_palette(len(bottom_molds))

        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.bar(range(len(bottom_molds)), 
                      bottom_molds['usedTonnageCount'],
                      color=colors)

        # Optimize labels
        ax.set_xticks(range(len(bottom_molds)))
        ax.set_xticklabels(bottom_molds['moldNo'], rotation=45, ha='right')

        ax.set_xlabel('Mold No', fontweight='bold')
        ax.set_ylabel('Number of Used Tonnages', fontweight='bold')
        ax.set_title(f'Bottom {bottom_n} Molds with Least Machine Tonnage Types Used',
                    fontweight='bold', fontsize=14)
        ax.grid(True, alpha=0.3)

        # Highlight molds only match 1 tonnage type
        single_tonnage_molds = bottom_molds[bottom_molds['usedTonnageCount'] == 1]
        if len(single_tonnage_molds) > 0:
            ax.axhline(y=1, color='red', linestyle='--', alpha=0.7,
                      label=f'{len(single_tonnage_molds)} molds only match 1 tonnage type')
            ax.legend()

        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    #Plot a histogram of the distribution of tonnage types per mold.
    @staticmethod
    def plot_tonnage_distribution(used_mold_machine_df, 
                                  file_path, 
                                  figsize=(8, 5)):

        max_count = used_mold_machine_df['usedTonnageCount'].max()
        bins = np.arange(0.5, max_count + 1.5, 1)

        fig, ax = plt.subplots(figsize=figsize)
        n, bins_used, patches = ax.hist(used_mold_machine_df['usedTonnageCount'],
                                      bins=bins, edgecolor='black', alpha=0.7,
                                      color='skyblue')

        # Add values on bars
        for i, (patch, count) in enumerate(zip(patches, n)):
            if count > 0:
                ax.text(patch.get_x() + patch.get_width()/2., count + max(n)*0.01,
                      f'{int(count)}', ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('Number of Machine Tonnages Used', fontweight='bold')
        ax.set_ylabel('Number of Molds', fontweight='bold')
        ax.set_title('Distribution of Tonnage Variety per Mold',
                    fontweight='bold', fontsize=14)
        ax.set_xticks(range(1, max_count + 1))
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    #Plot a pie chart of mold proportions according to the number of tonnage types.
    @staticmethod
    def plot_tonnage_proportion_pie(used_mold_machine_df, 
                                    file_path, 
                                    figsize=(8, 8)):

        count_dist = used_mold_machine_df['usedTonnageCount'].value_counts().sort_index()
        colors = generate_color_palette(len(count_dist))

        fig, ax = plt.subplots(figsize=figsize)
        wedges, texts, autotexts = ax.pie(count_dist.values,
                                        labels=[f'{k} types\n({v} molds)' for k, v in count_dist.items()],
                                        autopct='%1.1f%%',
                                        startangle=140,
                                        colors=colors,
                                        explode=[0.05] * len(count_dist))

        # Improve appearance
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        for text in texts:
            text.set_fontsize(9)
            text.set_fontweight('bold')

        ax.set_title('Proportion of Molds by Number of Tonnage Types Used',
                    fontweight='bold', fontsize=14, pad=20)

        plt.tight_layout()

        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)

    #Comparison of Acquisition Date and First Use Date
    @staticmethod
    def compare_acquisition_firstuse(first_use_mold_df, 
                                    file_path, figsize=(15, 8)):

      first_use_mold_df['moldIndex'] = range(len(first_use_mold_df))
      
      fig, ax = plt.subplots(figsize=figsize)
      plt.scatter(first_use_mold_df['moldIndex'], first_use_mold_df['acquisitionDate'],
                  label='Acquisition Date', alpha=0.6, s=20)
      plt.scatter(first_use_mold_df['moldIndex'], first_use_mold_df['firstDate'],
                  label='First Use Date', alpha=0.6, s=20)

      plt.xticks([], [])  #Remove label only
      #plt.gca().get_xaxis().set_visible(False)  #Hide X axis

      #plt.xlabel('Mold Index')
      plt.ylabel('Date')
      plt.title('Comparison of Acquisition Date and First Use Date')

      plt.legend()
      plt.tight_layout()
      plt.grid(True, alpha=0.3)
      plt.show()

      logger.debug("Saving plot...")
      save_plot(fig, file_path, dpi=300)

    #Distribution of Time Gap between Acquisition and First Use
    @staticmethod
    def timegap_acquisition_firstuse(first_use_mold_df, 
                                    file_path, figsize=(12, 6)):

      # Calculate the time gap between acquisition and first use
      first_use_mold_df['daysDifference'] = (first_use_mold_df['firstDate'] - first_use_mold_df['acquisitionDate']).dt.days

      fig, ax = plt.subplots(figsize=figsize)
      plt.hist(first_use_mold_df['daysDifference'], bins=30, alpha=0.7, edgecolor='black')
      plt.xlabel('Days between Acquisition and First Use')
      plt.ylabel('Number of Molds')
      plt.title('Distribution of Time Gap between Acquisition and First Use')
      plt.grid(True, alpha=0.3)

      # Add statistic
      mean_days = first_use_mold_df['daysDifference'].mean()
      median_days = first_use_mold_df['daysDifference'].median()
      plt.axvline(mean_days, color='red', linestyle='--', label=f'Mean: {mean_days:.1f} days')
      plt.axvline(median_days, color='orange', linestyle='--', label=f'Median: {median_days:.1f} days')
      plt.legend()
      plt.tight_layout()
      plt.show()

      logger.debug("Saving plot...")
      save_plot(fig, file_path, dpi=300)

    #Top/Bottom molds gap time analysis
    @staticmethod
    def top_bot_mold_gaptime_analysis(first_use_mold_df, file_path, 
                                      top_n = 20, bot_n = 20, figsize=(15, 12)):

      sorted_df = first_use_mold_df.sort_values('daysDifference')
      top_20 = sorted_df.tail(top_n)
      bottom_20 = sorted_df.head(bot_n)

      fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

      # Top 20 molds with the largest gap
      ax1.barh(range(len(top_20)), top_20['daysDifference'], color='red', alpha=0.7)
      ax1.set_yticks(range(len(top_20)))
      ax1.set_yticklabels(top_20['moldNo'])
      ax1.set_xlabel('Days between Acquisition and First Use')
      ax1.set_title('Top 20 Molds with Longest Gap')
      ax1.grid(True, alpha=0.3)

      # Bottom 20 molds with minimum gap
      ax2.barh(range(len(bottom_20)), bottom_20['daysDifference'], color='green', alpha=0.7)
      ax2.set_yticks(range(len(bottom_20)))
      ax2.set_yticklabels(bottom_20['moldNo'])
      ax2.set_xlabel('Days between Acquisition and First Use')
      ax2.set_title('Top 20 Molds with Shortest Gap')
      ax2.grid(True, alpha=0.3)

      plt.tight_layout()
      plt.show()

      logger.debug("Saving plot...")
      save_plot(fig, file_path, dpi=300)

    #Number of Molds First Run on Each Machine
    @staticmethod
    def machine_level_mold_count(paired_mold_machine_df, 
                                file_path, figsize=(12, 6)):
        
        # More efficient mold counting
        count_mold_per_machine = (paired_mold_machine_df.groupby('machineCode')['moldNo']
                                .nunique()
                                .sort_values(ascending=False))
        colors = generate_color_palette(len(count_mold_per_machine))
        
        fig, ax = plt.subplots(figsize=figsize)
        bars = plt.bar(range(len(count_mold_per_machine)), 
                      count_mold_per_machine.values,
                      color=colors)
        
        plt.axhline(10, color='red', linestyle='--', linewidth=2, 
                    label='Machines running only 10 molds')
        
        plt.xticks(range(len(count_mold_per_machine)), 
                  count_mold_per_machine.index, rotation=45, ha='right')
        plt.title('Number of Molds First Run on Each Machine')
        plt.xlabel('Machine Code')
        plt.ylabel('Number of Molds')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        logger.debug("Saving plot...")
        save_plot(fig, file_path, dpi=300)