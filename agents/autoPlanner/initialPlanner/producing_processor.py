import pandas as pd
import numpy as np
import os
from typing import Tuple

from agents.decorators import validate_init_dataframes, validate_dataframe
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, read_change_log, save_output_with_versioning
from agents.core_helpers import check_newest_machine_layout
from datetime import datetime
from agents.autoPlanner.initialPlanner.hybrid_suggest_optimizer import HybridSuggestOptimizer

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
})

class RequiredColumns:
    # Select available columns
    PRODUCING_BASE_COLS = ['poNo', 'itemCode', 'itemName', 'poETA', 'moldNo',
                           'itemQuantity', 'itemRemain', 'machineNo', 'startedDate']
    PENDING_BASE_COLS = ['poNo', 'itemCode', 'itemName', 'poETA', 'itemRemain']

class ProducingProcessor:

    """
    A comprehensive class for processing manufacturing/molding/producing data including mold capacity,
    production planning, and plastic usage calculations.
    """

    def __init__(self,
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 sharedDatabaseSchemas_path: str = 'database/sharedDatabaseSchemas.json',
                 folder_path: str = 'agents/shared_db/OrderProgressTracker',
                 target_name: str = "change_log.txt",
                 default_dir: str = "agents/shared_db/AutoPlanner/InitialPlanner",
                 mold_stability_index_folder = "agents/shared_db/HistoricalInsights/MoldStabilityIndexCalculator/mold_stability_index",
                 mold_stability_index_target_name = "change_log.txt",
                 mold_machine_weights_hist_path = "agents/shared_db/HistoricalInsights/MoldMachineFeatureWeightCalculator/weights_hist.xlsx",
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

        self.databaseSchemas_path = databaseSchemas_path
        self.sharedDatabaseSchemas_path = sharedDatabaseSchemas_path

        # Load path annotations that map logical names to actual file paths
        self.path_annotation = load_annotation_path(source_path, annotation_name)

        # Set up output configuration
        self.filename_prefix = "producing_processor"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "ProducingProcessor"

        # Load production report
        proStatus_path = read_change_log(folder_path, target_name)
        self.proStatus_df = pd.read_excel(proStatus_path)

        # Load all required DataFrames from parquet files
        self._setup_schemas()
        self._load_dataframes()

        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        self.optimizer = HybridSuggestOptimizer(  
            self.databaseSchemas_data,
            self.sharedDatabaseSchemas_data,
            source_path,
            annotation_name,
            self.default_dir,
            folder_path,
            target_name,
            mold_stability_index_folder,
            mold_stability_index_target_name,
            mold_machine_weights_hist_path,
            self.efficiency,
            self.loss)

    def _setup_schemas(self) -> None:
        """Load database schema configuration for column validation."""
        try:
            self.databaseSchemas_data = load_annotation_path(
                Path(self.databaseSchemas_path).parent,
                Path(self.databaseSchemas_path).name
            )
            self.logger.debug("Database schemas loaded successfully")

            self.sharedDatabaseSchemas_data = load_annotation_path(
                Path(self.sharedDatabaseSchemas_path).parent,
                Path(self.sharedDatabaseSchemas_path).name
            )
            self.logger.debug("Shared database schemas loaded successfully")

        except Exception as e:
            self.logger.error("Failed to load database schemas: {}", str(e))
            raise

    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - machineInfo_df: Machine specifications and tonnage information
        - itemCompositionSummary_df: Item composition details (resin, masterbatch, etc.)
        """

        # Define the mapping between path annotation keys and DataFrame attribute names
        dataframes_to_load = [
            ('machineInfo', 'machineInfo_df'),
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

    def execute_hybrid_suggest_optimization(self):
        
        # Validate configuration before processing
        if self.optimizer.validate_configuration():
            logger.info("Configuration is valid. Starting optimization...")

            # Run optimization
            result = self.optimizer.process()
            logger.info("Optimization completed successfully!")
            logger.info("Invalid molds: {}", len(result.estimated_capacity_invalid_molds + result.priority_matrix_invalid_molds))
            logger.info("Capacity data shape: {}", result.mold_estimated_capacity_df.shape)
            logger.info("Priority matrix shape: {}", result.mold_machine_priority_matrix.shape)

        else:
            logger.info("Configuration validation failed. Please check the logs.")

        # Process results for production planning
        optimization_results = {
            'estimated_capacity_invalid_molds': result.estimated_capacity_invalid_molds,
            'priority_matrix_invalid_molds': result.priority_matrix_invalid_molds,
            'capacity_data': result.mold_estimated_capacity_df,
            'priority_matrix': result.mold_machine_priority_matrix,
            'timestamp': datetime.now()
        }

        return optimization_results

    @staticmethod
    def _split_producing_and_pending_orders(proStatus_df, 
                                            producing_base_cols,
                                            pending_base_cols):

        if proStatus_df.empty:
            logger.error('Error processing data: Empty proStatus_df')

        # Get producing data
        producing_status_data = proStatus_df[
            (proStatus_df['itemRemain'] > 0) & (proStatus_df['proStatus'] == 'MOLDING')
            ][producing_base_cols].copy().sort_values(by='machineNo')

        # Get paused POs
        paused = proStatus_df[
            (proStatus_df['itemRemain'] > 0) & (proStatus_df['proStatus'] == 'PAUSED')
        ][pending_base_cols].copy()
        paused.rename(columns={'itemRemain': 'itemQuantity'}, inplace=True)

        # Get pending POs
        pending = proStatus_df[
            (proStatus_df['itemRemain'] > 0) & (proStatus_df['proStatus'] == 'PENDING')
        ][pending_base_cols].copy()
        pending.rename(columns={'itemRemain': 'itemQuantity'}, inplace=True)

        # Combine paused and pending POs as pending data
        pending_status_data = pd.concat([paused, pending], ignore_index=True)
        
        return producing_status_data, pending_status_data

    def process(self):
        
        try:
            optimization_results = self.execute_hybrid_suggest_optimization()
        except Exception as e:
            logger.error("Hybrid suggest optimizer failed")
            raise
        
        try:
            mold_estimated_capacity_df = optimization_results['capacity_data']
            cols = list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys())
            logger.info('Validation for mold_estimated_capacity...')
            validate_dataframe(mold_estimated_capacity_df, cols)
        except Exception as e:
            logger.error("Validation failed for mold_estimated_capacity (expected cols: %s): %s", cols, e)
            raise

        # Process the data
        try:
            (pending_status_data,
            producing_status_data,
            pro_plan,
            mold_plan,
            plastic_plan) = self._process_production_data(self.proStatus_df,
                                                          mold_estimated_capacity_df)
            self.logger.info("Manufacturing data processing completed successfully!")
            return optimization_results, pending_status_data, producing_status_data, pro_plan, mold_plan, plastic_plan

        except FileNotFoundError as e:
            self.logger.debug("File not found: {}. \nPlease ensure all required data files are available.", e)
        except Exception as e:
            self.logger.debug("Error processing data: {}. \nPlease check your data files and try again.", e)

    def process_and_save_results(self, **kwargs):
        
        def priority_matrix_process(priority_matrix):
            priority_matrix.columns.name = None
            return priority_matrix.reset_index()

        self.data = {}
        (optimization_results, 
         pending_status_data, 
         producing_status_data, 
         pro_plan, mold_plan, plastic_plan) = self.process()
        
        estimated_capacity_invalid_molds = optimization_results['estimated_capacity_invalid_molds']
        priority_matrix_invalid_molds = optimization_results['priority_matrix_invalid_molds']
        mold_machine_priority_matrix = optimization_results['priority_matrix']
        mold_estimated_capacity_df = optimization_results['capacity_data']

        # Prepare data for saving (matching PORequiredCriticalValidator format)
        self.data["producing_status_data"] = producing_status_data
        self.data["producing_pro_plan"] = pro_plan 
        self.data["producing_mold_plan"] = mold_plan
        self.data["producing_plastic_plan"] = plastic_plan

        self.data["pending_status_data"] = pending_status_data

        self.data["mold_machine_priority_matrix"] = priority_matrix_process(mold_machine_priority_matrix)
        self.data["mold_estimated_capacity_df"] = mold_estimated_capacity_df

         # Create a proper DataFrame structure for invalid molds
        max_len = max(len(estimated_capacity_invalid_molds), len(priority_matrix_invalid_molds))
        # Pad shorter lists with None values
        estimated_padded = estimated_capacity_invalid_molds + [""] * (max_len - len(estimated_capacity_invalid_molds))
        priority_padded = priority_matrix_invalid_molds + [""] * (max_len - len(priority_matrix_invalid_molds))
        
        self.data["invalid_molds"] = pd.DataFrame({
            "estimated_capacity_invalid_molds": estimated_padded,
            "priority_matrix_invalid_molds": priority_padded
        })

        self.logger.info("Start excel file exporting...")
        save_output_with_versioning(
            self.data,
            self.output_dir,
            self.filename_prefix,
        )

        return self.data

    def _process_production_data(self,
                                 proStatus_df: pd.DataFrame,
                                 mold_estimated_capacity_df: pd.DataFrame) -> Tuple[pd.DataFrame, ...]:

        """
        Process production data to generate production, mold, and plastic plans.

        Args:
            proStatus_df: DataFrame with production status information
            mold_estimated_capacity_df: DataFrame with mold information
            machine_info_df: DataFrame with machine information
            itemCompositionSummary_df: DataFrame with item composition data

        Returns:
            Tuple of (producing_data, pro_plan, mold_plan, plastic_plan)
        """

        # Rename columns for consistency
        proStatus_df.rename(columns={'lastestMachineNo': 'machineNo',
                                     'lastestMoldNo': 'moldNo'}, inplace=True)
        
        # Filter producing data
        producing_status_data, pending_status_data = ProducingProcessor._split_producing_and_pending_orders(proStatus_df,
                                                                                                            RequiredColumns.PRODUCING_BASE_COLS,
                                                                                                            RequiredColumns.PENDING_BASE_COLS)

        if producing_status_data.empty:

            def empty_df_from_schema(schema_dict, key):
                return pd.DataFrame(columns=list(schema_dict[key]['dtypes'].keys()))
        
            producing_status_data = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_data")
            producing_pro_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_pro_plan")
            producing_mold_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_mold_plan")
            producing_plastic_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_plastic_plan")
            
            return pending_status_data, producing_status_data, producing_pro_plan, producing_mold_plan, producing_plastic_plan

        # Merge with mold info
        if not mold_estimated_capacity_df.empty:
            mold_merge_cols = ['itemCode', 'moldNo', 'moldName',
                              'theoreticalMoldHourCapacity', 'balancedMoldHourCapacity']
            available_mold_cols = [col for col in mold_merge_cols if col in mold_estimated_capacity_df.columns]

            producing_status_data = producing_status_data.merge(
                mold_estimated_capacity_df[available_mold_cols],
                how='left', on=['itemCode', 'moldNo']
            )

        # Merge with machine info
        if not self.machine_info_df.empty:
            machine_merge_cols = ['machineNo', 'machineCode', 'machineName', 'machineTonnage']
            available_machine_cols = [col for col in machine_merge_cols if col in self.machine_info_df.columns]

            producing_status_data = producing_status_data.merge(
                self.machine_info_df[available_machine_cols],
                how='left', on=['machineNo']
            )

        # Calculate time-related columns
        producing_status_data = self._calculate_time_metrics(producing_status_data)

        # Create output plans
        output_plan_format = pd.DataFrame({
            'machineNo': self.machine_info_df['machineNo'].unique() if not self.machine_info_df.empty else []
        })

        machine_info_subset = self.machine_info_df[
            [col for col in ['machineCode', 'machineName', 'machineTonnage', 'machineNo']
             if col in self.machine_info_df.columns]
        ] if not self.machine_info_df.empty else pd.DataFrame()

        # Create plans
        producing_pro_plan = self._create_production_plan(output_plan_format, machine_info_subset, producing_status_data)
        producing_mold_plan = self._create_mold_plan(output_plan_format, machine_info_subset, producing_status_data)
        producing_plastic_plan = self._create_plastic_plan(output_plan_format, machine_info_subset, producing_status_data)

        return pending_status_data, producing_status_data, producing_pro_plan, producing_mold_plan, producing_plastic_plan

    def _calculate_time_metrics(self, 
                                producing_data: pd.DataFrame) -> pd.DataFrame:

        """Calculate time-related metrics for production data."""

        if 'balancedMoldHourCapacity' in producing_data.columns:
            # Avoid division by zero
            producing_data['balancedMoldHourCapacity'] = producing_data['balancedMoldHourCapacity'].replace(0, np.nan)

            producing_data['leadTime'] = pd.to_timedelta(
                producing_data['itemQuantity'] / producing_data['balancedMoldHourCapacity'],
                unit='hours', errors='coerce'
            )

            producing_data['remainTime'] = pd.to_timedelta(
                producing_data['itemRemain'] / producing_data['balancedMoldHourCapacity'],
                unit='hours', errors='coerce'
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
    
    ############################
    #  Create production plan  #
    ############################

    def _create_production_plan(self, 
                                output_plan_format: pd.DataFrame,
                                machine_info: pd.DataFrame,
                                producing_data: pd.DataFrame) -> pd.DataFrame:

        """Create production plan."""

        if output_plan_format.empty:
            return pd.DataFrame()

        pro_plan = output_plan_format.copy()

        if not machine_info.empty:
            pro_plan = pro_plan.merge(machine_info, how='left', on=['machineNo'])

        if not producing_data.empty and 'itemName_poNo' in producing_data.columns:
            merge_cols = ['machineNo', 'itemName_poNo']
            if 'remainTime' in producing_data.columns:
                merge_cols.append('remainTime')

            pro_plan = pro_plan.merge(
                producing_data[merge_cols],
                how='left', on=['machineNo']
            )

        return pro_plan
    
    #########################
    #    Create mold plan   #
    #########################

    def _create_mold_plan(self, 
                          output_plan_format: pd.DataFrame,
                          machine_info: pd.DataFrame,
                          producing_data: pd.DataFrame) -> pd.DataFrame:

        """Create mold plan."""

        if output_plan_format.empty:
            return pd.DataFrame()

        mold_plan = output_plan_format.copy()

        if not machine_info.empty:
            mold_plan = mold_plan.merge(machine_info, how='left', on=['machineNo'])

        if not producing_data.empty and 'moldName' in producing_data.columns:
            merge_cols = ['machineNo', 'moldName']
            if 'remainTime' in producing_data.columns:
                merge_cols.append('remainTime')

            mold_plan = mold_plan.merge(
                producing_data[merge_cols],
                how='left', on=['machineNo']
            )

        return mold_plan

    #########################
    #  Create plastic plan  #
    #########################

    def _create_plastic_plan(self, 
                             output_plan_format: pd.DataFrame,
                             machine_info: pd.DataFrame,
                             producing_data: pd.DataFrame) -> pd.DataFrame:

        """Create plastic plan with composition data."""

        if output_plan_format.empty:
            return pd.DataFrame()

        plastic_plan = output_plan_format.copy()

        if not machine_info.empty:
            plastic_plan = plastic_plan.merge(machine_info, how='left', on=['machineNo'])

        if producing_data.empty or self.itemCompositionSummary_df.empty:
            return plastic_plan

        # Process plastic data
        plastic_data = self._process_plastic_data(producing_data)

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

    def _process_plastic_data(self, 
                              producing_data: pd.DataFrame) -> pd.DataFrame:

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
                                      if col in self.itemCompositionSummary_df.columns]

        if len(available_composition_cols) < 2:  # Need at least itemCode and one composition
            return plastic_data

        plastic_data = plastic_data.merge(
            self.itemCompositionSummary_df[available_composition_cols],
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

    def _calculate_material_quantities(self, 
                                       plastic_data: pd.DataFrame) -> None:

        """Calculate estimated material quantities (KG)."""

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