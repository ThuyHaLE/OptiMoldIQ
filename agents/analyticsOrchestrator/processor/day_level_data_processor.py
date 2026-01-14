import numpy as np
import pandas as pd
from typing import Optional, Dict
from loguru import logger
from datetime import datetime
from configs.shared.config_report_format import ConfigReportMixin
from agents.decorators import validate_init_dataframes
from agents.analyticsOrchestrator.processor.configs.processor_config import ProcessorLevel, ProcessorResult

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "purchaseOrders_df": list(self.databaseSchemas_data['dynamicDB']['purchaseOrders']['dtypes'].keys()),
})
class DayLevelDataProcessor(ConfigReportMixin):

    # Class constants
    GROUP_COLS = [
        'machineInfo', 'workingShift']
    COMPONENT_COLS = [
        'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode']
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
                 productRecords_df: pd.DataFrame,
                 purchaseOrders_df: pd.DataFrame,
                 databaseSchemas_data: Dict,
                 day_constant_config: Dict = {},
                 record_date: Optional[str] = None):

        self._capture_init_args()
        self.logger = logger.bind(class_="DayLevelDataProcessor")

        self.record_date = record_date

        self.databaseSchemas_data = databaseSchemas_data

        self.productRecords_df = productRecords_df
        self.purchaseOrders_df = purchaseOrders_df

        self.day_constant_config = day_constant_config
        if not self.day_constant_config:
            self.logger.debug("DayLevelDataProcessor constant config not found.")

    def process_records(self) -> ProcessorResult:
        """
        Process product records and merge with purchase orders data.

        Args:
            productRecords_df: Product records data
            purchaseOrders_df: Purchase orders data
            record_date: Specific date to filter (YYYY-MM-DD). If None, uses latest date

        Returns:
            ProcessorResult
        """

        self.logger.info("Starting DayLevelDataProcessor ...")

        # Generate config header
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        processor_log_entries = [
            config_header,
            "--Processing Summary--\n",
            f"⤷ {self.__class__.__name__} results:\n"
            ]

        try:
            # Input validation
            self._validate_product_records()

            adjusted_record_date = self._validate_analysis_parameters()

            self.logger.info("Initial day level data processing at {}", adjusted_record_date.isoformat())
            processor_log_entries.append(f"Initial day level data processing at {adjusted_record_date.isoformat()}")

            # Filter data for the selected date
            filtered_df = self.productRecords_df[self.productRecords_df['recordDate'] == adjusted_record_date].copy()

            if filtered_df.empty:
                self.logger.warning("No data found for date {}", adjusted_record_date)
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
            merged_df = self._create_info_fields(merged_df)
            merged_df = self._calculate_counts(merged_df)
            merged_df = self._calculate_job_metrics(merged_df)

            # Apply change classification
            merged_df['changeType'] = merged_df.apply(self._classify_change, axis=1)

            # Generate summary statistics
            summary_stats = self.generate_summary_stats(merged_df, adjusted_record_date)

            # Process mold based data
            required_configs = self.day_constant_config.get(
                "REQUIRED_CONFIGS", self.REQUIRED_CONFIGS)
            
            mold_based_record_df = self._mold_based_processing(
                merged_df, required_configs.get('mold', self.REQUIRED_CONFIGS['mold']))

            # Process item based data
            item_based_record_df = self._item_based_processing(
                merged_df, required_configs.get('item', self.REQUIRED_CONFIGS['item']))
            
            processed_data = {
                        "selectedDateFilter": merged_df,
                        "moldBasedRecords": mold_based_record_df,
                        "itemBasedRecords": item_based_record_df,
                        "summaryStatics": summary_stats
                    }

            was_adjusted = (pd.Timestamp(self.record_date) != adjusted_record_date)

            # adjusted_record_date, processed_data, analysis_summary
            return ProcessorResult(
                processor_level = ProcessorLevel.DAY,
                record_date = self.record_date, 
                analysis_date = self.analysis_date,
                adjusted_record_date = adjusted_record_date, 
                was_adjusted = was_adjusted, 
                processed_data = processed_data,
                log = '\n'.join(processor_log_entries)
                )
            
        except Exception as e:
            self.logger.error("❌ Processor failed: {}", str(e))
            raise

    def _validate_product_records(self) -> None: 
        if self.productRecords_df.empty:
            self.logger.error("productRecords_df is empty")
            raise ValueError("productRecords_df is empty")
        if 'recordDate' not in self.productRecords_df.columns:
            self.logger.error("recordDate column not found in productRecords_df")
            raise ValueError("recordDate column not found in productRecords_df")
    
    def _validate_analysis_parameters(self) -> pd.Timestamp:
        """
        Validate and determine the record date to use for analysis.
        
        Returns:
            pd.Timestamp: The validated record date
        """
        
        if self.record_date is None:
            latest_record_date = self.productRecords_df['recordDate'].max()
            self.logger.info("No record_date provided. Using latest available date: {}", latest_record_date.date())
        else:
            try:
                # Convert string input to Timestamp to match DataFrame dtype
                requested_date = pd.Timestamp(self.record_date).normalize()
            except Exception as e:
                self.logger.error("Invalid record_date format '{}'. Expected 'YYYY-MM-DD'. Error: {}", self.record_date, e)
                raise ValueError(f"Invalid record_date format '{self.record_date}'. Expected 'YYYY-MM-DD'. Error: {e}")
            
            available_dates = self.productRecords_df['recordDate'].unique()
            
            if requested_date not in available_dates:
                self.logger.warning("Requested date {} not found in database.", requested_date.date())
                self.logger.info("Available dates: {}", sorted([d.date() for d in available_dates]))
                
                latest_record_date = self.productRecords_df['recordDate'].max()
                self.logger.info("Falling back to latest available date: {}", latest_record_date.date())
            else:
                latest_record_date = requested_date
                self.logger.info("Using requested record date: {}", latest_record_date.date())
        
        return latest_record_date
    
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
        component_cols = DayLevelDataProcessor.day_constant_config.get(
            "COMPONENT_COLS", DayLevelDataProcessor.COMPONENT_COLS)
        
        components_mask = df[component_cols].notna().any(axis=1)
        df['itemComponent'] = df.apply(lambda row: tuple(row[col] if pd.notna(row[col]) else None for col in component_cols)
                                       if components_mask.loc[row.name] else pd.NA, axis=1)

        return df
    
    @staticmethod
    def _calculate_counts(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate various count metrics by machine and shift."""
        df = df.copy()

        group_cols = DayLevelDataProcessor.day_constant_config.get(
            "GROUP_COLS", DayLevelDataProcessor.GROUP_COLS)
        
        # Create grouper once
        grouper = df.groupby(group_cols)

        # Count configurations
        count_configs = DayLevelDataProcessor.day_constant_config.get(
            "COUNT_CONFIGS", DayLevelDataProcessor.COUNT_CONFIGS)

        # Calculate counts using groupby transform
        for new_col, src_col in count_configs.items():
            df[new_col] = grouper[src_col].transform('nunique')

        return df
    
    @staticmethod
    def _calculate_job_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate job count and late status metrics."""
        df = df.copy()

        group_cols = DayLevelDataProcessor.day_constant_config.get(
            "GROUP_COLS", DayLevelDataProcessor.GROUP_COLS)

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