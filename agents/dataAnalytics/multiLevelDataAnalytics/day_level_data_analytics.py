from agents.utils import load_latest_file_from_folder, save_output_with_versioning
from agents.dashboardBuilder.visualize_data.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
import pandas as pd

@validate_init_dataframes({
    "productRecords_df": [
            'machineNo', 'itemName', 'itemTotalQuantity', 'itemGoodQuantity',
            'recordDate', 'workingShift', 'moldNo', 'moldShot'
        ],
    "moldInfo_df": ['moldNo', 'moldCavityStandard', 'moldSettingCycle']
})
class DayLevelDataAnalytics:
    def __init__(self, 
                 data_source: str, 
                 selected_date: str,
                 default_dir="agents/shared_db"):
        
        self.data = load_latest_file_from_folder(data_source)
        self.moldInfo_df = self.data.get('moldInfo')
        if self.moldInfo_df is None:
            self.logger.error("❌ Sheet 'moldInfo' not found.")
            raise ValueError("Sheet 'moldInfo' not found.")

        self.productRecords_df = self.data.get('productRecords')
        if self.productRecords_df is None:
            self.logger.error("❌ Sheet 'productRecords' not found.")
            raise ValueError("Sheet 'productRecords' not found.")

        self.moldInfo_df = self.data['moldInfo']
        self.productRecords_df = self.data['productRecords']

        self.selected_date = pd.to_datetime(selected_date).date() #make sure it is datetime type (date)
        self.filename_prefix= "workingshift_level_analysis"

        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "DayLevelDataAnalytics"

        self.logger = logger.bind(class_="DayLevelDataAnalytics")

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

        self.dayworkingshift_level_analysis()

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

    def dayworkingshift_level_analysis(self, **kwargs) -> None:
        logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )