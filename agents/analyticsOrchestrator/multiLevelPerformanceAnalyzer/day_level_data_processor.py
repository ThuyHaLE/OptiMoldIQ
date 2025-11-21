import numpy as np
import pandas as pd
from typing import Optional, Tuple
from loguru import logger
from pathlib import Path
import os
from agents.decorators import validate_init_dataframes
from agents.utils import load_annotation_path
from datetime import datetime
import shutil

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
})

class DayLevelDataProcessor:

    # Class constants
    GROUP_COLS = ['machineInfo', 'workingShift']
    COMPONENT_COLS = ['plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']
    COUNT_CONFIGS = {
        'itemCount': 'itemInfo',
        'moldCount': 'moldNo',
        'itemComponentCount': 'itemComponent'
    }
    REQUIRED_CONFIGS = {
        'mold': ['machineInfo', 'workingShift', 'moldNo', 'moldShot',
                 'moldCavity', 'itemTotalQuantity', 'itemGoodQuantity', 'changeType'],
        'item': ['machineInfo', 'workingShift', 'itemInfo',
                 'moldNo', 'moldShot', 'moldCavity',
                 'itemTotalQuantity', 'itemGoodQuantity', 'itemComponent']
    }

    def __init__(self,
                 record_date: Optional[str] = None,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db/MultiLevelDataAnalytics"):

        self.logger = logger.bind(class_="DayLevelDataProcessor")

        self.record_date = record_date

        # Load database schema and database paths annotation
        self.databaseSchemas_data = load_annotation_path(Path(databaseSchemas_path).parent,
                                                         Path(databaseSchemas_path).name)
        self.path_annotation = load_annotation_path(source_path,
                                                    annotation_name)

        # Load DataFrames
        self.productRecords_df = self._load_dataframe('productRecords')
        self.purchaseOrders_df = self._load_dataframe('purchaseOrders')

        self.filename_prefix = "day_level"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DayLevelDataProcessor"

    def _load_dataframe(self, df_name: str) -> pd.DataFrame:
        """Load a specific DataFrame with error handling."""
        df_path = self.path_annotation.get(df_name)

        if not df_path:
            error_msg = f"Path to '{df_name}' not found in annotations."
            self.logger.error("❌ {}", error_msg)
            raise KeyError(error_msg)

        if not os.path.exists(df_path):
            error_msg = f"Path to '{df_name}' does not exist: {df_path}"
            self.logger.error("❌ {}", error_msg)
            raise FileNotFoundError(error_msg)

        try:
            df = pd.read_parquet(df_path)
            self.logger.info("✅ Successfully loaded {}: {} records", df_name, len(df))
            return df
        except Exception as e:
            error_msg = f"Failed to read parquet file for '{df_name}': {e}"
            self.logger.error("❌ {}", error_msg)
            raise

    def data_process(self, 
                     save_output = False):
        
        self.logger.info("Start processing...")
        (merged_df, mold_based_record_df, 
            item_based_record_df, summary_stats, analysis_summary) = self.product_record_processing()
    
        if save_output: 
            # Setup directories and timestamps
            timestamp_now = datetime.now()
            timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
            timestamp_file = timestamp_now.strftime("%Y%m%d_%H%M")
            
            newest_dir = self.output_dir / "newest"
            newest_dir.mkdir(parents=True, exist_ok=True)
            historical_dir = self.output_dir / "historical_db"
            historical_dir.mkdir(parents=True, exist_ok=True)
            
            log_entries = [f"[{timestamp_str}] Saving new version...\n"]
            
            # Move old files to historical_db
            for f in newest_dir.iterdir():
                if f.is_file():
                    try:
                        dest = historical_dir / f.name
                        shutil.move(str(f), dest)
                        log_entries.append(f"  ⤷ Moved old file: {f.name} → historical_db/{f.name}\n")
                        self.logger.info("Moved old file {} to historical_db as {}", f.name, dest.name)
                    except Exception as e:
                        self.logger.error("Failed to move file {}: {}", f.name, e)
                        raise OSError(f"Failed to move file {f.name}: {e}")
            
            # Save day level extracted records
            try:
                excel_file_name = f"{timestamp_file}_{self.filename_prefix}_insights_{self.record_date}.xlsx"
                excel_file_path = newest_dir / excel_file_name

                excel_data = {
                    "selectedDateFilter": merged_df,
                    "moldBasedRecords": mold_based_record_df,
                    "itemBasedRecords": item_based_record_df,
                    "summaryStatics": summary_stats
                }
                with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
                    for sheet_name, df in excel_data.items():
                        if not isinstance(df, pd.DataFrame):
                            df = pd.DataFrame([df])
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                log_entries.append(f"  ⤷ Saved data analysis results: {excel_file_path}\n")
                logger.info("✅ Saved data analysis results: {}", excel_file_path)
            except Exception as e:
                logger.error("❌ Failed to save file {}: {}", excel_file_name, e)
                raise OSError(f"Failed to save file {excel_file_name}: {e}")
            
            # Save analysis summary
            try:
                analysis_summary_name = f"{timestamp_file}_{self.filename_prefix}_summary_{self.record_date}.txt"
                analysis_summary_path = newest_dir / analysis_summary_name
                with open(analysis_summary_path, "w", encoding="utf-8") as log_file:
                    log_file.writelines(analysis_summary)
                log_entries.append(f"  ⤷ Saved analysis summary: {analysis_summary_path}\n")
                self.logger.info("Updated analysis summary {}", analysis_summary_path)
            except Exception as e:
                self.logger.error("Failed to update analysis summary {}: {}", analysis_summary_path, e)
                raise OSError(f"Failed to update analysis summary {analysis_summary_path}: {e}")

            # Update change log
            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.writelines(log_entries)
                self.logger.info("Updated change log {}", log_path)
            except Exception as e:
                self.logger.error("Failed to update change log {}: {}", log_path, e)
                raise OSError(f"Failed to update change log {log_path}: {e}")
            
            return merged_df, mold_based_record_df, item_based_record_df, summary_stats, analysis_summary, log_entries
        
        else:
            return merged_df, mold_based_record_df, item_based_record_df, summary_stats, analysis_summary, None

    def product_record_processing(self) -> Tuple[pd.DataFrame, dict]:
        """
        Process product records and merge with purchase orders data.

        Args:
            productRecords_df: Product records data
            purchaseOrders_df: Purchase orders data
            record_date: Specific date to filter (YYYY-MM-DD). If None, uses latest date

        Returns:
            Tuple of (processed dataframe, summary statistics)
        """

        # Input validation
        if self.productRecords_df.empty:
            self.logger.error("productRecords_df is empty")
            raise ValueError("productRecords_df is empty")
        if 'recordDate' not in self.productRecords_df.columns:
            self.logger.error("recordDate column not found in productRecords_df")
            raise ValueError("recordDate column not found in productRecords_df")

        # Determine the record date to use
        if self.record_date is None:
            latest_record_date = self.productRecords_df['recordDate'].max()
            self.logger.info("Using the latest available date: {}", latest_record_date)
        else:
            latest_record_date = self.record_date
            available_dates = self.productRecords_df['recordDate'].unique()
            if latest_record_date not in available_dates:
                self.logger.warning("Requested date {} not found in database.", latest_record_date)
                self.logger.info("Available dates: {}", sorted(available_dates))
                latest_record_date = self.productRecords_df['recordDate'].max()
                self.logger.info("Falling back to latest available date: {}", latest_record_date)

        # Filter data for the selected date
        filtered_df = self.productRecords_df[
            self.productRecords_df['recordDate'] == latest_record_date
        ].copy()

        if filtered_df.empty:
            self.logger.warning("No data found for date {}", latest_record_date)
            return filtered_df, {}

        # Standardize column names
        if 'poNote' in filtered_df.columns and 'poNo' not in filtered_df.columns:
            filtered_df = filtered_df.rename(columns={'poNote': 'poNo'})

        # Merge with purchase orders data
        if not self.purchaseOrders_df.empty and 'poNo' in filtered_df.columns:
            merge_columns = ['poNo', 'itemQuantity', 'poETA']
            available_po_columns = [col for col in merge_columns if col in self.purchaseOrders_df.columns]

            if available_po_columns:
                merged_df = filtered_df.merge(
                    self.purchaseOrders_df[available_po_columns],
                    on='poNo',
                    how='left'
                )
                self.logger.info("Merged with {} columns from purchase orders", len(available_po_columns))
            else:
                self.logger.warning("No matching columns available for merging from purchaseOrders_df")
                merged_df = filtered_df
        else:
            merged_df = filtered_df
            self.logger.warning("Skipping purchase orders merge - data unavailable or missing poNo column")

        # Process the data step by step
        merged_df = DayLevelDataProcessor._create_info_fields(merged_df)
        merged_df = DayLevelDataProcessor._calculate_counts(merged_df)
        merged_df = DayLevelDataProcessor._calculate_job_metrics(merged_df)

        # Apply change classification
        merged_df['changeType'] = merged_df.apply(DayLevelDataProcessor._classify_change, axis=1)

        # Process mold based data
        mold_based_record_df = DayLevelDataProcessor._mold_based_processing(
            merged_df, DayLevelDataProcessor.REQUIRED_CONFIGS['mold'])

        # Process item based data
        item_based_record_df = DayLevelDataProcessor._item_based_processing(
            merged_df, DayLevelDataProcessor.REQUIRED_CONFIGS['item'])

        # Generate summary statistics
        summary_stats = self.generate_summary_stats(merged_df, latest_record_date)

        analysis_summary = self._log_analysis_summary(summary_stats)

        return merged_df, mold_based_record_df, item_based_record_df, summary_stats, analysis_summary

    def _log_analysis_summary(self, stats: dict) -> str:

        """
        Convert summary statistics dictionary into formatted text block.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DATA SUMMARY REPORT")
        lines.append("=" * 60)

        # Basic info
        lines.append(f"Record date: {stats.get('record_date')}")
        lines.append(f"Total records: {stats.get('total_records', 0)}")
        lines.append(f"Active jobs: {stats.get('active_jobs', 0)}")

        # Optional: Only show detailed stats if active_jobs > 0
        if stats.get('active_jobs', 0) > 0:

            # Working shifts & machines
            if 'working_shifts' in stats:
                lines.append(f"Working shifts: {stats['working_shifts']}")

            if 'machines' in stats:
                lines.append(f"Machines: {stats['machines']}")

            if 'purchase_orders' in stats:
                lines.append(f"Purchase orders: {stats['purchase_orders']}")

            # Products
            if 'products' in stats:
                lines.append(f"Products: {stats['products']}")

            # Molds
            if 'molds' in stats:
                lines.append(f"Molds: {stats['molds']}")

            # Late status report
            if 'late_pos' in stats and 'total_pos_with_eta' in stats:
                late = stats['late_pos']
                total = stats['total_pos_with_eta']
                lines.append(f"POs delayed vs ETA: {late}/{total}")

            # Change type distribution
            if 'change_type_distribution' in stats:
                lines.append("Change type distribution:")
                for change_type, count in stats['change_type_distribution'].items():
                    lines.append(f"  └─ {change_type}: {count}")
        else:
            lines.append("No active job data found!")

        lines.append("=" * 60)
        return "\n".join(lines)

    def generate_summary_stats(self, merged_df: pd.DataFrame, record_date: str) -> dict:
        """Generate summary statistics and return as dictionary."""

        # Filter for active jobs
        job_df = merged_df[
            (merged_df['itemTotalQuantity'] > 0) &
            (merged_df['poNo'].notna())
        ].copy() if 'itemTotalQuantity' in merged_df.columns else pd.DataFrame()

        stats = {
            'record_date': record_date,
            'total_records': len(merged_df),
            'active_jobs': len(job_df)
        }

        self.logger.info("=== DATA SUMMARY FOR {} ===", record_date)
        self.logger.info("Total records: {}", stats['total_records'])
        self.logger.info("Active jobs: {}", stats['active_jobs'])

        if len(job_df) > 0:
            stats.update({
                'working_shifts': job_df['workingShift'].nunique() if 'workingShift' in job_df.columns else 0,
                'machines': job_df['machineNo'].nunique() if 'machineNo' in job_df.columns else 0,
                'purchase_orders': job_df['poNo'].nunique(),
            })

            self.logger.info("Working shifts: {}", stats['working_shifts'])
            self.logger.info("Machines: {}", stats['machines'])
            self.logger.info("Purchase orders: {}", stats['purchase_orders'])

            # Products and molds stats
            if 'itemCode' in job_df.columns:
                products_with_code = job_df[job_df['itemCode'].notna()]
                if len(products_with_code) > 0:
                    stats['products'] = products_with_code['itemCode'].nunique()
                    self.logger.info("Products: {}", stats['products'])

            if 'moldNo' in job_df.columns:
                molds_with_no = job_df[job_df['moldNo'].notna()]
                if len(molds_with_no) > 0:
                    stats['molds'] = molds_with_no['moldNo'].nunique()
                    self.logger.info("Molds: {}", stats['molds'])

            # Late status summary
            if 'lateStatus' in job_df.columns:
                po_late_summary = job_df[['poNo', 'lateStatus']].drop_duplicates()
                late_count = po_late_summary['lateStatus'].sum()
                total_count = len(po_late_summary)
                stats['late_pos'] = late_count
                stats['total_pos_with_eta'] = total_count
                self.logger.info("POs delayed vs ETA: {}/{}", late_count, total_count)

            # Change type distribution
            if 'changeType' in merged_df.columns:
                change_dist = merged_df['changeType'].value_counts().to_dict()
                stats['change_type_distribution'] = change_dist
                self.logger.info("Change type distribution:")
                for change_type, count in change_dist.items():
                    self.logger.info("  {}: {}", change_type, count)
        else:
            self.logger.warning("No active job data found!")
        return stats

    @staticmethod
    def _classify_change(row) -> str:
        """Classify the type of change based on moldChanged and colorChanged columns."""
        if pd.notna(row.get('moldChanged')) and pd.notna(row.get('colorChanged')):
            return 'mold&color_change'
        elif pd.notna(row.get('moldChanged')):
            return 'mold_change'
        elif pd.notna(row.get('colorChanged')):
            return 'color_change'
        elif row.get('jobCount', 0) == 0:
            return 'machine_idle'
        else:
            return 'no_change'

    @staticmethod
    def _create_info_fields(df: pd.DataFrame) -> pd.DataFrame:
        """Create composite information fields from existing columns."""
        if not any(col in df.columns for col in ['machineInfo', 'itemInfo', 'itemComponent']):
            df = df.copy()

        # Machine info
        df['machineInfo'] = (df['machineNo'].astype(str) + ' (' + df['machineCode'].astype(str) + ')')

        # Item info - only create if both itemCode and itemName exist
        item_mask = df[['itemCode', 'itemName']].notna().all(axis=1)
        df['itemInfo'] = df.apply(lambda row: f"{row['itemCode']} ({row['itemName']})"
                                  if item_mask.loc[row.name] else pd.NA, axis=1)

        # Item components - create tuple of component codes
        component_cols = DayLevelDataProcessor.COMPONENT_COLS
        components_mask = df[component_cols].notna().any(axis=1)
        df['itemComponent'] = df.apply(lambda row: tuple(row[col] if pd.notna(row[col]) else None for col in component_cols)
                                       if components_mask.loc[row.name] else pd.NA, axis=1)

        return df

    @staticmethod
    def _calculate_counts(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate various count metrics by machine and shift."""
        df = df.copy()

        group_cols = DayLevelDataProcessor.GROUP_COLS

        # Create grouper once
        grouper = df.groupby(group_cols)

        # Count configurations
        count_configs = DayLevelDataProcessor.COUNT_CONFIGS

        # Calculate counts using groupby transform
        for new_col, src_col in count_configs.items():
            df[new_col] = grouper[src_col].transform('nunique')

        return df

    @staticmethod
    def _calculate_job_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate job count and late status metrics."""
        df = df.copy()

        group_cols = DayLevelDataProcessor.GROUP_COLS

        # Check if any group has positive quantities
        group_has_positive = (df.groupby(group_cols)['itemTotalQuantity'].transform(lambda x: (x > 0).any()))

        # Count jobs per group
        group_job_count = df.groupby(group_cols)['moldNo'].transform('count')
        df['jobCount'] = np.where(group_has_positive, group_job_count, 0)

        # Calculate late status (if poETA column exists)
        if 'poETA' in df.columns:
            try:
                df['lateStatus'] = np.where(group_has_positive,
                                            pd.to_datetime(df['recordDate']) >= pd.to_datetime(df['poETA']), False)
            except Exception as e:
                logger.warning(f"Error calculating late status: {e}. Defaulting to False.")
                df['lateStatus'] = False
        else:
            df['lateStatus'] = False
            logger.warning("Missing column 'poETA'. Defaulting lateStatus to False.")

        return df

    @staticmethod
    def _mold_based_processing(record_df, required_fields) -> pd.DataFrame:
        # Create a copy with selected fields
        df_copy = record_df[required_fields].copy()

        # Separate records by change type
        df_no_changes = df_copy[df_copy['changeType'] == 'no_change'].copy()
        df_mold = df_copy[df_copy['changeType'] == 'mold_change'].copy()
        df_no_working = df_copy[df_copy['changeType'] == 'machine_idle'].copy()

        # Process color change records with aggregation
        df_color = df_copy[df_copy['changeType'] == 'color_change'].copy()

        if not df_color.empty:
            df_color_agg = df_color.groupby([
                'machineInfo', 'workingShift', 'moldNo', 'changeType'
            ], dropna=False).agg({
                'itemTotalQuantity': 'sum',
                'itemGoodQuantity': 'sum',
                'moldShot': 'mean',
                'moldCavity': 'mean'
            }).reset_index()
        else:
            df_color_agg = pd.DataFrame()

        # Combine all dataframes
        dfs_to_concat = [df for df in [df_no_changes, df_color_agg, df_mold, df_no_working] if not df.empty]

        if dfs_to_concat:
            df_final = pd.concat(dfs_to_concat, ignore_index=True, sort=False)
            df_final = df_final.sort_values(by=['machineInfo', 'workingShift']).reset_index(drop=True)

            # Handle missing values
            df_final[['itemTotalQuantity', 'itemGoodQuantity']] = df_final[['itemTotalQuantity', 'itemGoodQuantity']].fillna(0)
            # Calculate defect and its rate
            df_final['defectQuantity'] = df_final['itemTotalQuantity'] - df_final['itemGoodQuantity']
            df_final['defectRate'] = np.where(
                df_final['itemTotalQuantity'] > 0,
                (df_final['defectQuantity'] / df_final['itemTotalQuantity'] * 100),
                0
            )
            # Filter null or 0
            df_clean = df_final.dropna(subset=['moldNo'])

            return df_clean
        else:
            return pd.DataFrame()

    @staticmethod
    def _item_based_processing(record_df, required_fields) -> pd.DataFrame:
        # Create a copy with selected fields
        df_copy = record_df[required_fields].copy()

        if not df_copy.empty:
            df_agg = df_copy.groupby('itemInfo', dropna=False).agg(
                itemTotalQuantity=('itemTotalQuantity', 'sum'),
                itemGoodQuantity=('itemGoodQuantity', 'sum'),
                usedMachineNums=('machineInfo', 'nunique'),
                totalShifts=('workingShift', 'count'),
                usedMoldNums=('moldNo', 'nunique'),
                moldTotalShots=('moldShot', 'sum'),
                avgCavity=('moldCavity', 'mean'),
                usedComponentNums=('itemComponent', 'nunique')
                ).reset_index()

        else:
            df_agg = pd.DataFrame()

        if not df_agg.empty:
            df_final = df_agg.sort_values(by=['itemInfo']).reset_index(drop=True)

            # Handle missing values
            df_final[['itemTotalQuantity', 'itemGoodQuantity']] = df_final[['itemTotalQuantity', 'itemGoodQuantity']].fillna(0)
            # Calculate defect and its rate
            df_final['defectQuantity'] = df_final['itemTotalQuantity'] - df_final['itemGoodQuantity']
            df_final['defectRate'] = np.where(
                df_final['itemTotalQuantity'] > 0,
                (df_final['defectQuantity'] / df_final['itemTotalQuantity'] * 100),
                0
            )
            # Filter null or 0
            df_clean = df_final.dropna(subset=['itemInfo'])

            return df_clean
        else:
            return pd.DataFrame()