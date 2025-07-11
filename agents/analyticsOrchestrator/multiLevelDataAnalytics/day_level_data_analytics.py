from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning
import pandas as pd
import os

@validate_init_dataframes(lambda self: {
    "productRecords_df": list(self.databaseSchemas_data['dynamicDB']['productRecords']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

class DayLevelDataAnalytics:
    def __init__(self, 
                 selected_date: str,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest', 
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 default_dir: str = "agents/shared_db"):
        
        self.logger = logger.bind(class_="DayLevelDataAnalytics")

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
        logger.debug("productRecords: {} - {}", self.productRecords_df.shape, self.productRecords_df.columns)

        
        # Extract moldInfo DataFrame
        moldInfo_path = self.path_annotation.get('moldInfo')
        if not moldInfo_path or not os.path.exists(moldInfo_path):
            self.logger.error("❌ Path to 'moldInfo' not found or does not exist.")
            raise FileNotFoundError("Path to 'moldInfo' not found or does not exist.")
        self.moldInfo_df = pd.read_parquet(moldInfo_path)

        self.selected_date = selected_date
        self.filename_prefix= "workingshift_level_analysis"

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DayLevelDataAnalytics"

    def prepare_data(self, **kwargs):
        df = self.productRecords_df.copy()
        filtered = df[df['recordDate'] == self.selected_date]
        if filtered.empty:
            self.logger.error("❌ No records found for date: {}.", self.selected_date)
            raise TypeError(f"No records found for date: {self.selected_date}.")
        logger.debug("productRecords_date_filtered shape={}, columns={}", filtered.shape, filtered.columns)

        summary = filtered.groupby(['machineNo', 'itemName'])[
            ['itemTotalQuantity', 'itemGoodQuantity']].sum().reset_index()
        logger.debug("productRecords_summary shape={}, columns={}", summary.shape, summary.columns)

        shift_summary = filtered.groupby(['machineNo', 'workingShift', 'itemName'])[
            ['itemTotalQuantity', 'itemGoodQuantity']].sum().reset_index()
        logger.debug("productRecords_shiftsummary shape={}, columns={}", shift_summary.shape, shift_summary.columns)

        merged = pd.merge(
            filtered[['workingShift', 'machineNo', 'itemName', 'itemTotalQuantity',
                      'itemGoodQuantity', 'moldNo', 'moldShot', 'moldCavity']],
            self.moldInfo_df[['moldNo', 'moldCavityStandard', 'moldSettingCycle']],
            on='moldNo', how='left'
        )
        logger.debug("moldInfo_merged shape={}, columns={}", merged.shape, merged.columns)

        mold_count = merged.groupby(['workingShift', 'machineNo'])['moldNo'].nunique().reset_index(name='moldCount')
        logger.debug("mold_per_shift_machine shape={}, columns={}", mold_count.shape, mold_count.columns)

        merged_count = pd.merge(
            merged, mold_count, on=['workingShift', 'machineNo'], how='left'
        )
        logger.debug("moldInfo_moldCount_merged shape={}, columns={}", merged_count.shape, merged_count.columns)

        mold_shots = merged_count.groupby(['workingShift', 'machineNo'])['moldShot'].sum().reset_index()
        logger.debug("moldShot_per_shift_machine shape={}, columns={}", mold_shots.shape, mold_shots.columns)

        single_mold_df = merged_count[
            (merged_count['moldCount'] == 1) & (merged_count['moldShot'] > 0)
        ].copy()
        single_mold_df['moldCycle'] = (8 * 3600) / single_mold_df['moldShot']
        single_mold_df['moldCavityUtilizationRate'] = (
            single_mold_df['moldCavity'] / single_mold_df['moldCavityStandard']
        ) * 100
        single_mold_df['moldCavityGap'] = single_mold_df['moldCavity'] - single_mold_df['moldCavityStandard']
        single_mold_df['moldCycleEfficiency'] = (
            single_mold_df['moldSettingCycle'] / single_mold_df['moldCycle']
        ) * 100
        single_mold_df['moldCycleDeviation'] = (
            single_mold_df['moldSettingCycle'] - single_mold_df['moldCycle']
        )
        single_mold_df['overallProductionEfficiency'] = (
            single_mold_df['moldCavityUtilizationRate'] + single_mold_df['moldCycleEfficiency']
        ) / 2
        single_mold_df['expected_total_quantity'] = (
            ((8 * 3600) / single_mold_df['moldSettingCycle']) * single_mold_df['moldCavityStandard']
        )
        single_mold_df['expectedYieldEfficiency'] = (
            single_mold_df['itemTotalQuantity'] / single_mold_df['expected_total_quantity']
        ) * 100
        logger.debug("single_mold_df shape={}, columns={}", single_mold_df.shape, single_mold_df.columns)

        return (
            filtered[['machineNo', 'workingShift', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity']],
            summary,
            shift_summary,
            merged_count,
            mold_shots,
            single_mold_df
        )

    def report_dayworkingshift_level(self, **kwargs) -> None:
        (
        self.filtered,
        self.summary,
        self.shift_summary,
        self.merged_count,
        self.mold_shots,
        self.single_mold_df
        ) = self.prepare_data()

        self.data = {
                    "selectedDateFilter": self.filtered,
                    "yieldByMachine": self.summary, 
                    "yieldByShift": self.shift_summary,
                    "usedMoldTrack": self.merged_count,
                    "moldShotPerShift": self.mold_shots,
                    "singleMoldEfficiency": self.single_mold_df
                    }
        
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )