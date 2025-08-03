import pandas as pd
import numpy as np
import os
from typing import Tuple

from agents.decorators import validate_init_dataframes
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, read_change_log
from agents.core_helpers import check_newest_machine_layout

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldSpecificationSummary_df": list(self.databaseSchemas_data['staticDB']['moldSpecificationSummary']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

@validate_init_dataframes({"proStatus_df": [
    'poReceivedDate', 'poNo', 'itemCode', 'itemName', 'poETA',
    'itemQuantity', 'itemRemain', 'startedDate', 'actualFinishedDate',
    'proStatus', 'etaStatus', 'machineHist', 'itemType', 'moldList',
    'moldHist', 'moldCavity', 'totalMoldShot', 'totalDay', 'totalShift',
    'plasticResinCode', 'colorMasterbatchCode', 'additiveMasterbatchCode',
    'moldShotMap', 'machineQuantityMap', 'dayQuantityMap',
    'shiftQuantityMap', 'materialComponentMap', 'lastestRecordTime',
    'machineNo', 'moldNo', 'warningNotes']})

class ProducingProcessor:

    """
    A comprehensive class for processing manufacturing/molding/producing data including mold capacity,
    production planning, and plastic usage calculations.
    """

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 folder_path: str = 'agents/shared_db/OrderProgressTracker',
                 target_name: str = "change_log.txt",
                 default_dir: str = "agents/shared_db",
                 efficiency: float = 0.85,
                 loss: float = 0.03):

        """
        Initialize the processor with default efficiency and loss parameters.

        Args:
            efficiency: Machine efficiency rate (default 85%)
            loss: Expected production loss (default 3%)
        """

        self.logger = logger.bind(class_="ProducingProcessor")

        self.efficiency = efficiency
        self.loss = loss

        # Load database schema configuration for column validation
        self.databaseSchemas_data = load_annotation_path(
            Path(databaseSchemas_path).parent,
            Path(databaseSchemas_path).name
        )
        # Load path annotations that map logical names to actual file paths
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Set up output configuration
        self.filename_prefix = "producing_processor"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "ProducingProcessor"

        # Load production report
        proStatus_path = read_change_log(folder_path, target_name)
        self.proStatus_df = pd.read_excel(proStatus_path)

        # Rename columns for consistency
        self.proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                          'lastestMoldNo': 'moldNo'
                                          }, inplace=True)

        # Load all required DataFrames from parquet files
        self._load_dataframes()

    def process(self, capacity_mold_info_df):
      try:
        # Process the data

        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        (producing_data,
         pro_plan,
         mold_plan,
         plastic_plan) = self._process_production_data(self.proStatus_df,
                                                       capacity_mold_info_df,
                                                       self.machine_info_df,
                                                       self.itemCompositionSummary_df)

        self.logger.info("Manufacturing data processing completed successfully!")

        return producing_data, pro_plan, mold_plan, plastic_plan

      except FileNotFoundError as e:
          self.logger.debug("File not found: {}. \nPlease ensure all required data files are available.", e)
      except Exception as e:
          self.logger.debug("Error processing data: {}. \nPlease check your data files and try again.", e)

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
        - itemCompositionSummary_df: Item composition details (resin, masterbatch, etc.)
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('machineInfo', 'machineInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df')
        ]

        # Load each DataFrame with error handling
        for path_key, attr_name in dataframes_to_load:
            path = self.path_annotation.get(path_key)

            # Validate path exists
            if not path or not os.path.exists(path):
                self.logger.error("Path to '{}' not found or does not exist: {}", path_key, path)
                raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")

            try:
                # Load DataFrame from parquet file
                df = pd.read_parquet(path)
                setattr(self, attr_name, df)
                self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                self.logger.error("Failed to load {}: {}", path_key, str(e))
                raise

    def _process_production_data(self,
                                 proStatus_df: pd.DataFrame,
                                 mold_info_df: pd.DataFrame,
                                 machine_info_df: pd.DataFrame,
                                 itemCompositionSummary_df: pd.DataFrame) -> Tuple[pd.DataFrame, ...]:

        """
        Process production data to generate production, mold, and plastic plans.

        Args:
            proStatus_df: DataFrame with production status information
            mold_info_df: DataFrame with mold information
            machine_info_df: DataFrame with machine information
            itemCompositionSummary_df: DataFrame with item composition data

        Returns:
            Tuple of (producing_data, pro_plan, mold_plan, plastic_plan)
        """

        if proStatus_df.empty:
            return tuple(pd.DataFrame() for _ in range(4))

        # Filter producing data
        producing_data = proStatus_df[
            (proStatus_df['itemRemain'] > 0) &
            (proStatus_df['proStatus'] == 'MOLDING')
        ].copy()

        if producing_data.empty:
            return tuple(pd.DataFrame() for _ in range(4))

        # Select available columns
        base_cols = ['poNo', 'itemCode', 'itemName', 'poETA', 'moldNo',
                    'itemQuantity', 'itemRemain', 'machineNo', 'startedDate']
        available_cols = [col for col in base_cols if col in producing_data.columns]

        producing_data = producing_data[available_cols].sort_values(by='machineNo')

        # Merge with mold info
        if not mold_info_df.empty:
            mold_merge_cols = ['itemCode', 'moldNo', 'moldName',
                              'theoreticalMoldHourCapacity', 'balancedMoldHourCapacity']
            available_mold_cols = [col for col in mold_merge_cols if col in mold_info_df.columns]

            producing_data = producing_data.merge(
                mold_info_df[available_mold_cols],
                how='left', on=['itemCode', 'moldNo']
            )

        # Merge with machine info
        if not machine_info_df.empty:
            machine_merge_cols = ['machineNo', 'machineCode', 'machineName', 'machineTonnage']
            available_machine_cols = [col for col in machine_merge_cols if col in machine_info_df.columns]

            producing_data = producing_data.merge(
                machine_info_df[available_machine_cols],
                how='left', on=['machineNo']
            )

        # Calculate time-related columns
        producing_data = self._calculate_time_metrics(producing_data)

        # Create output plans
        output_plan = pd.DataFrame({
            'machineNo': machine_info_df['machineNo'].unique() if not machine_info_df.empty else []
        })

        machine_info_subset = machine_info_df[
            [col for col in ['machineCode', 'machineName', 'machineTonnage', 'machineNo']
             if col in machine_info_df.columns]
        ] if not machine_info_df.empty else pd.DataFrame()

        # Create plans
        pro_plan = self._create_production_plan(output_plan, machine_info_subset, producing_data)
        mold_plan = self._create_mold_plan(output_plan, machine_info_subset, producing_data)
        plastic_plan = self._create_plastic_plan(output_plan, machine_info_subset,
                                                producing_data, itemCompositionSummary_df)

        return producing_data, pro_plan, mold_plan, plastic_plan

    def _calculate_time_metrics(self, producing_data: pd.DataFrame) -> pd.DataFrame:

        """Calculate time-related metrics for production data."""

        if 'balancedMoldHourCapacity' in producing_data.columns:
            # Avoid division by zero
            producing_data['balancedMoldHourCapacity'] = producing_data['balancedMoldHourCapacity'].replace(0, np.nan)

            producing_data['leadTime'] = pd.to_timedelta(
                producing_data['itemQuantity'] / producing_data['balancedMoldHourCapacity'],
                unit='hours'
            )

            producing_data['remainTime'] = pd.to_timedelta(
                producing_data['itemRemain'] / producing_data['balancedMoldHourCapacity'],
                unit='hours'
            )

        if 'startedDate' in producing_data.columns:
            producing_data['startedDate'] = pd.to_datetime(
                producing_data['startedDate'], errors='coerce'
            )

            if 'leadTime' in producing_data.columns:
                producing_data['finishedEstimatedDate'] = (
                    producing_data['startedDate'] + producing_data['leadTime']
                ).dt.strftime('%Y-%m-%d %H:%M:%S')

        if all(col in producing_data.columns for col in ['itemQuantity', 'itemRemain']):
            producing_data['proProgressing'] = round(
                (producing_data['itemQuantity'] - producing_data['itemRemain']) * 100 /
                producing_data['itemQuantity'], 2
            )

        if all(col in producing_data.columns for col in ['itemName', 'poNo']):
            producing_data['itemName_poNo'] = (
                producing_data['itemName'] + ' (' + producing_data['poNo'] + ')'
            )

        return producing_data

    def _create_production_plan(self, output_plan: pd.DataFrame,
                              machine_info_subset: pd.DataFrame,
                              producing_data: pd.DataFrame) -> pd.DataFrame:

        """Create production plan."""

        if output_plan.empty:
            return pd.DataFrame()

        pro_plan = output_plan.copy()

        if not machine_info_subset.empty:
            pro_plan = pro_plan.merge(machine_info_subset, how='left', on=['machineNo'])

        if not producing_data.empty and 'itemName_poNo' in producing_data.columns:
            merge_cols = ['machineNo', 'itemName_poNo']
            if 'remainTime' in producing_data.columns:
                merge_cols.append('remainTime')

            pro_plan = pro_plan.merge(
                producing_data[merge_cols],
                how='left', on=['machineNo']
            )

        return pro_plan

    def _create_mold_plan(self, output_plan: pd.DataFrame,
                         machine_info_subset: pd.DataFrame,
                         producing_data: pd.DataFrame) -> pd.DataFrame:

        """Create mold plan."""

        if output_plan.empty:
            return pd.DataFrame()

        mold_plan = output_plan.copy()

        if not machine_info_subset.empty:
            mold_plan = mold_plan.merge(machine_info_subset, how='left', on=['machineNo'])

        if not producing_data.empty and 'moldName' in producing_data.columns:
            merge_cols = ['machineNo', 'moldName']
            if 'remainTime' in producing_data.columns:
                merge_cols.append('remainTime')

            mold_plan = mold_plan.merge(
                producing_data[merge_cols],
                how='left', on=['machineNo']
            )

        return mold_plan

    def _create_plastic_plan(self, output_plan: pd.DataFrame,
                           machine_info_subset: pd.DataFrame,
                           producing_data: pd.DataFrame,
                           itemCompositionSummary_df: pd.DataFrame) -> pd.DataFrame:

        """Create plastic plan with composition data."""

        if output_plan.empty:
            return pd.DataFrame()

        plastic_plan = output_plan.copy()

        if not machine_info_subset.empty:
            plastic_plan = plastic_plan.merge(machine_info_subset, how='left', on=['machineNo'])

        if producing_data.empty or itemCompositionSummary_df.empty:
            return plastic_plan

        # Process plastic data
        plastic_data = self._process_plastic_data(producing_data, itemCompositionSummary_df)

        if plastic_data.empty:
            return plastic_plan

        # Create mapping for plastic data
        plastic_mapping = plastic_data.set_index('machineNo')

        plastic_columns = [
            'itemName_poNo', 'estimatedOutputQuantity', 'plasticResin',
            'estimatedPlasticResinQuantity', 'colorMasterbatch',
            'estimatedColorMasterbatchQuantity', 'additiveMasterbatch',
            'estimatedAdditiveMasterbatchQuantity'
        ]

        # Map available columns
        available_plastic_cols = [col for col in plastic_columns if col in plastic_data.columns]

        for col in available_plastic_cols:
            if col in plastic_mapping.columns:
                plastic_plan[col] = plastic_plan['machineNo'].map(plastic_mapping[col])

        # Fill NaN values
        material_cols = ['plasticResin', 'colorMasterbatch', 'additiveMasterbatch']
        quantity_cols = ['estimatedPlasticResinQuantity', 'estimatedColorMasterbatchQuantity',
                        'estimatedAdditiveMasterbatchQuantity']

        for col in material_cols:
            if col in plastic_plan.columns:
                plastic_plan[col] = plastic_plan[col].fillna('NONE')

        for col in quantity_cols:
            if col in plastic_plan.columns:
                plastic_plan[col] = plastic_plan[col].fillna(0).astype('Float64')

        return plastic_plan

    def _process_plastic_data(self, producing_data: pd.DataFrame,
                            itemCompositionSummary_df: pd.DataFrame) -> pd.DataFrame:

        """Process plastic composition data."""

        required_cols = ['machineNo', 'itemCode', 'itemRemain', 'theoreticalMoldHourCapacity']
        available_cols = [col for col in required_cols if col in producing_data.columns]

        if len(available_cols) < 2:  # Need at least machineNo and itemCode
            return pd.DataFrame()

        plastic_data = producing_data[available_cols].copy()

        # Add optional columns if available
        optional_cols = ['poNo', 'itemName_poNo', 'itemName']
        for col in optional_cols:
            if col in producing_data.columns:
                plastic_data[col] = producing_data[col]

        # Merge with composition data
        composition_cols = ['itemCode', 'plasticResin', 'plasticResinQuantity',
                           'colorMasterbatch', 'colorMasterbatchQuantity',
                           'additiveMasterbatch', 'additiveMasterbatchQuantity']

        available_composition_cols = [col for col in composition_cols
                                    if col in itemCompositionSummary_df.columns]

        if len(available_composition_cols) < 2:  # Need at least itemCode and one composition
            return plastic_data

        plastic_data = plastic_data.merge(
            itemCompositionSummary_df[available_composition_cols],
            how='left', on=['itemCode']
        )

        # Calculate estimated quantities
        if all(col in plastic_data.columns for col in ['itemRemain', 'theoreticalMoldHourCapacity']):
            max_daily_capacity = plastic_data['theoreticalMoldHourCapacity'] * 24
            plastic_data['estimatedOutputQuantity'] = np.minimum(
                plastic_data['itemRemain'],
                max_daily_capacity
            ).astype('Int64')

            # Calculate material quantities
            self._calculate_material_quantities(plastic_data)

        return plastic_data

    def _calculate_material_quantities(self, plastic_data: pd.DataFrame) -> None:

        """Calculate estimated material quantities."""

        if 'estimatedOutputQuantity' not in plastic_data.columns:
            return

        # Plastic resin
        if 'plasticResinQuantity' in plastic_data.columns:
            plastic_data['estimatedPlasticResinQuantity'] = (
                plastic_data['plasticResinQuantity'] / 10000 *
                plastic_data['estimatedOutputQuantity']
            )

        # Color masterbatch
        if 'colorMasterbatchQuantity' in plastic_data.columns:
            plastic_data['estimatedColorMasterbatchQuantity'] = (
                plastic_data['colorMasterbatchQuantity'] * 1000 / 10000 *
                plastic_data['estimatedOutputQuantity']
            )

        # Additive masterbatch
        if 'additiveMasterbatchQuantity' in plastic_data.columns:
            plastic_data['estimatedAdditiveMasterbatchQuantity'] = (
                plastic_data['additiveMasterbatchQuantity'] * 1000 / 10000 *
                plastic_data['estimatedOutputQuantity']
            )