import pandas as pd
import numpy as np
from typing import Tuple, Dict
from loguru import logger
from datetime import datetime
import copy

from agents.decorators import validate_init_dataframes, validate_dataframe
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout

from dataclasses import dataclass, asdict

@dataclass
class ProducingPlannerResult:
    producing_status_data: pd.DataFrame
    producing_pro_plan: pd.DataFrame
    producing_mold_plan: pd.DataFrame
    producing_plastic_plan: pd.DataFrame
    pending_status_data: pd.DataFrame
    planner_summary: str
    log_str: str
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)

@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys())
})
class ProducingOrderPlanner(ConfigReportMixin):

    """
    A comprehensive class for processing manufacturing/molding/producing data including mold capacity,
    production planning, and plastic usage calculations.
    """

    PRODUCING_BASE_COLS = [
        'poNo', 'itemCode', 'itemName', 'poETA', 'moldNo',
        'itemQuantity', 'itemRemain', 'machineNo', 'startedDate']
    
    PENDING_BASE_COLS = [
        'poNo', 'itemCode', 'itemName', 'poETA', 'itemRemain']

    PROGRESS_DECIMAL_PRECISION = 2

    CAPACITY_MERGE_COLS = [
        'itemCode', 'moldNo', 'moldName',
        'theoreticalMoldHourCapacity', 'balancedMoldHourCapacity']
    
    MACHINE_MERGE_COLS = [
        'machineCode', 'machineName', 'machineTonnage', 'machineNo']

    PLASTIC_BASE_COLS = [
        'poNo', 'itemName_poNo', 'itemName', 'machineNo', 
        'itemCode', 'itemRemain', 'theoreticalMoldHourCapacity']
    
    COMPOSITION_REQUIRED_COLS = [
        'itemCode', 'plasticResin', 'plasticResinQuantity',
        'colorMasterbatch', 'colorMasterbatchQuantity',
        'additiveMasterbatch', 'additiveMasterbatchQuantity']
    
    PLASITC_REQUIRED_COLS = [
        'itemName_poNo', 'estimatedOutputQuantity', 'plasticResin',
        'estimatedPlasticResinQuantity', 'colorMasterbatch',
        'estimatedColorMasterbatchQuantity', 'additiveMasterbatch',
        'estimatedAdditiveMasterbatchQuantity']
    
    MATERIAL_REQUIRED_COLS = [
        'plasticResin', 'colorMasterbatch', 'additiveMasterbatch']

    QUANTITY_MATERIAL_REQUIRED_COLS = [
        'estimatedPlasticResinQuantity', 'estimatedColorMasterbatchQuantity',
        'estimatedAdditiveMasterbatchQuantity']
    
    def __init__(self,
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict,
                 machineInfo_df: pd.DataFrame,
                 itemCompositionSummary_df: pd.DataFrame,
                 proStatus_df: pd.DataFrame,
                 mold_estimated_capacity: pd.DataFrame,
                 planner_constant_config: Dict | None = None):
        
        """
        Initialize ProducingOrderPlanner with configuration.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - sharedDatabaseSchemas_data: Shared database schemas for validation
            - machineInfo_df: Machine specifications and tonnage information
            - itemCompositionSummary_df: Item composition details (resin, masterbatch, etc.)
            - proStatus_df: Detailed order production progress.
            - mold_estimated_capacity: Detailed priority molds for each item code with the highest estimated capacity
            - planner_constant_config: Constant config for producing order planner
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="ProducingOrderPlanner")

        self.databaseSchemas_data = databaseSchemas_data
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data

        self.machineInfo_df = machineInfo_df
        self.machine_info_df = check_newest_machine_layout(machineInfo_df)

        self.itemCompositionSummary_df = itemCompositionSummary_df

        self.proStatus_df = proStatus_df
        self.mold_estimated_capacity_df = mold_estimated_capacity

        if not planner_constant_config:
            self.planner_constant_config = {}
            self.logger.debug("ProducingOrderPlanner constant config not found.")
        else:
            self.planner_constant_config = copy.deepcopy(planner_constant_config)

    def process_planning(self) -> ProducingPlannerResult:
        """
        Process production data to generate production, mold, and plastic plans.
        """

        self.logger.info("Starting ProducingOrderPlanner ...")

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)
        
        # Initialize validation log entries for entire processing run
        planner_log_lines = [config_header]
        planner_log_lines.append(f"--Processing Summary--\n")
        planner_log_lines.append(f"⤷ {self.__class__.__name__} results:\n")

        try:
            # Step 1: Split production status data into producing and pending orders
            producing_status_data, pending_status_data = self._split_producing_and_pending_orders()

            if producing_status_data.empty:

                def empty_df_from_schema(schema_dict, key):
                    return pd.DataFrame(columns=list(schema_dict[key]['dtypes'].keys()))
            
                producing_status_data = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_data")
                pro_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_pro_plan")
                mold_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_mold_plan")
                plastic_plan = empty_df_from_schema(self.sharedDatabaseSchemas_data, "producing_plastic_plan")
                
                return pending_status_data, producing_status_data, pro_plan, mold_plan, plastic_plan

            # Step 2: estimate producing time metrics (production time, remaining duration, and progress)
            producing_status_data = self._estimate_producing_time_metrics(producing_status_data)

            # Step 3: Create plans for orders currently in production, 
            # including production plan, mold plan, and plastic plan
            pro_plan, mold_plan, plastic_plan = self._create_plans(producing_status_data)
            
            # Log data summary
            planner_log_lines.append("DATA EXPORT SUMMARY")
            planner_log_lines.append(f"⤷ Producing records: {len(producing_status_data)}")
            planner_log_lines.append(f"⤷ Pending records: {len(pending_status_data)}")
            planner_log_lines.append(f"⤷ Production plan: {len(pro_plan)}")
            planner_log_lines.append(f"⤷ Mold plan: {len(mold_plan)}")
            planner_log_lines.append(f"⤷ Plastic plan: {len(plastic_plan)}")

            # Generate planner summary
            reporter = DictBasedReportGenerator(use_colors=False)
            planner_summary = "\n".join(reporter.export_report({"producing_status_data": producing_status_data,
                                                                "producing_pro_plan": pro_plan,
                                                                "producing_mold_plan": mold_plan,
                                                                "producing_plastic_plan": plastic_plan,
                                                                "pending_status_data": pending_status_data
                                                                }))
            planner_log_lines.append(f"{planner_summary}")

            self.logger.info("✅ Process finished!!!")

            return ProducingPlannerResult(
                producing_status_data = producing_status_data,
                producing_pro_plan = pro_plan,
                producing_mold_plan = mold_plan,
                producing_plastic_plan = plastic_plan,
                pending_status_data = pending_status_data,
                planner_summary = planner_summary,
                log_str = "\n".join(planner_log_lines))

        except Exception as e:
            self.logger.error("Failed to process ProducingOrderPlanner: {}", str(e))
            raise RuntimeError(f"ProducingOrderPlanner processing failed: {str(e)}") from e
    
    #----------------------------------------------------------------------#
    # STEP 1: SPLIT PRODUCTION STATUS DATA INTO PRODUCING & PENDING ORDERS #
    #----------------------------------------------------------------------#
    def _split_producing_and_pending_orders(self) -> tuple[pd.DataFrame, pd.DataFrame]:

        """
        Split production status data into producing and pending orders.

        This method filters the input production status DataFrame into:
        - Producing orders: orders currently in MOLDING status
        - Pending orders: orders in PAUSED or PENDING status

        Args:
            proStatus_df (pd.DataFrame):
                Input DataFrame containing production order status information.
            producing_base_cols (list[str]):
                List of column names to keep for producing orders.
            pending_base_cols (list[str]):
                List of column names to keep for pending orders.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]:
        """

        # Validate input
        if self.proStatus_df.empty:
            logger.error('Error processing data: Empty proStatus_df')
            raise ValueError("Error processing data: proStatus_df is empty")

        #--------------------------------------------------------------------#
        # Get producing data
        #--------------------------------------------------------------------#    
        producing_base_cols = self.planner_constant_config.get(
            "PRODUCING_BASE_COLS", self.PRODUCING_BASE_COLS)
        validate_dataframe(self.proStatus_df, producing_base_cols)
        
        producing_status_data = self.proStatus_df[
            (self.proStatus_df['itemRemain'] > 0) 
            & (self.proStatus_df['proStatus'] == 'MOLDING')
            ][producing_base_cols].copy().sort_values(by='machineNo')

        #--------------------------------------------------------------------#
        # Get pending POs
        #--------------------------------------------------------------------#
        pending_base_cols = self.planner_constant_config.get(
                "PENDING_BASE_COLS", self.PENDING_BASE_COLS)
        validate_dataframe(self.proStatus_df, pending_base_cols)

        # Get paused POs
        paused = self.proStatus_df[
            (self.proStatus_df['itemRemain'] > 0) 
            & (self.proStatus_df['proStatus'] == 'PAUSED')
            ][pending_base_cols].copy()
        paused.rename(columns={'itemRemain': 'itemQuantity'}, inplace=True)

        # Get pending POs
        pending = self.proStatus_df[
            (self.proStatus_df['itemRemain'] > 0) 
            & (self.proStatus_df['proStatus'] == 'PENDING')
            ][pending_base_cols].copy()
        pending.rename(columns={'itemRemain': 'itemQuantity'}, inplace=True)

        # Combine paused and pending POs as pending data
        pending_status_data = pd.concat(
            [paused, pending], ignore_index=True)
        
        return producing_status_data, pending_status_data

    #---------------------------------------------------------------#
    # STEP 2: ESTIMATE PRODUCING TIME METRICS
    #---------------------------------------------------------------#
    def _estimate_producing_time_metrics(self, 
                                         producing_data: pd.DataFrame) -> pd.DataFrame:

        """
        Estimate production time, remaining duration, and progress for orders currently in production.
        - Computed metrics include:
            - Lead time (`leadTime`):
                Estimated total production duration, calculated as: itemQuantity / balancedMoldHourCapacity
            - Remaining time (`remainTime`):
                Estimated remaining production duration, calculated as: itemRemain / balancedMoldHourCapacity
            - Finished estimated date (`finishedEstimatedDate`):
                Estimated completion datetime, calculated as: startedDate + leadTime
            - Production progress (`proProgressing`):
                Production completion percentage, calculated as: (itemQuantity - itemRemain) / itemQuantity * 100
            - Combined item and PO label (`itemName_poNo`):
                Concatenation of item name and PO number for display purposes.

        Args:
            producing_data (pd.DataFrame):
                DataFrame containing producing order information.

        Returns:
            pd.DataFrame:
                The input DataFrame enriched with calculated time and progress metrics. 
                The original DataFrame is modified in-place and returned.        
        """

        # Enrich producing orders with mold capacity and machine reference data
        producing_data = self._merge_producing_with_mold_and_machine_info(producing_data)

        if 'balancedMoldHourCapacity' in producing_data.columns:
            # Avoid division by zero
            producing_data['balancedMoldHourCapacity'] = producing_data[
                'balancedMoldHourCapacity'].replace(0, np.nan)

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
                producing_data['itemQuantity'], 
                self.planner_constant_config.get(
                    "PROGRESS_DECIMAL_PRECISION", self.PROGRESS_DECIMAL_PRECISION)
                )

        if all(col in producing_data.columns for col in ['itemName', 'poNo']):
            producing_data['itemName_poNo'] = (
                producing_data['itemName'] + ' (' + producing_data['poNo'] + ')'
                )

        return producing_data
    
    def _merge_producing_with_mold_and_machine_info(self, 
                                                    producing_data: pd.DataFrame
                                                    ) -> pd.DataFrame:
        
        """
        Enrich producing orders with mold capacity and machine reference data.

        This method conditionally merges mold and machine information
        into the producing orders DataFrame to provide contextual capacity and resource details.
        """
        
        producing_status_data = producing_data.copy()

        # Merge with mold info
        if not self.mold_estimated_capacity_df.empty:
            capacity_cols = self.planner_constant_config.get(
                "CAPACITY_MERGE_COLS", self.CAPACITY_MERGE_COLS)
            validate_dataframe(self.mold_estimated_capacity_df, capacity_cols)

            producing_status_data = producing_status_data.merge(
                self.mold_estimated_capacity_df[capacity_cols],
                how='left', on=['itemCode', 'moldNo']
            )

        # Merge with machine info
        if not self.machine_info_df.empty:
            machine_cols = self.planner_constant_config.get(
                "MACHINE_MERGE_COLS", self.MACHINE_MERGE_COLS)
            validate_dataframe(self.machine_info_df, machine_cols)

            producing_status_data = producing_status_data.merge(
                self.machine_info_df[machine_cols],
                how='left', on=['machineNo']
            )

        return producing_status_data

    #---------------------------------------------------------------#
    # STEP 3: CREATE PLANS FOR ORDERS CURRENTLY IN PRODUCTION
    #---------------------------------------------------------------#
    def _create_plans(self, 
                      producing_data: pd.DataFrame) -> Tuple[pd.DataFrame, 
                                                             pd.DataFrame,
                                                             pd.DataFrame]:

        # Create output plans
        output_plan_format = pd.DataFrame({
            'machineNo': self.machine_info_df['machineNo'].unique() if not self.machine_info_df.empty else []
        })

        machine_cols = self.planner_constant_config.get(
            "MACHINE_MERGE_COLS", self.MACHINE_MERGE_COLS)
        validate_dataframe(self.machine_info_df, machine_cols)
        
        machine_info_subset = self.machine_info_df[machine_cols] if not self.machine_info_df.empty else pd.DataFrame()

        # Create plans
        pro_plan = self._create_production_plan(output_plan_format, machine_info_subset, producing_data)
        mold_plan = self._create_mold_plan(output_plan_format, machine_info_subset, producing_data)
        plastic_plan = self._create_plastic_plan(output_plan_format, machine_info_subset, producing_data)

        return pro_plan, mold_plan, plastic_plan

    #---------------------------------------------------------------#
    # STEP 3-1: CREATE PRODUCTION PLAN
    #---------------------------------------------------------------#
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
    
    #---------------------------------------------------------------#
    # STEP 3-2: CREATE MOLD PLAN
    #---------------------------------------------------------------#
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

    #---------------------------------------------------------------#
    # STEP 3-3: CREATE PLASTIC PLAN
    #---------------------------------------------------------------#
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

        # Map available columns
        plastic_cols = self.planner_constant_config.get(
            "PLASITC_REQUIRED_COLS", self.PLASITC_REQUIRED_COLS)
        validate_dataframe(plastic_data, plastic_cols)

        for col in plastic_cols:
            if col in plastic_mapping.columns:
                plastic_plan[col] = plastic_plan['machineNo'].map(plastic_mapping[col])

        # Fill NaN values
        for col in self.planner_constant_config.get(
            "MATERIAL_REQUIRED_COLS", self.MATERIAL_REQUIRED_COLS):
            if col in plastic_plan.columns:
                plastic_plan[col] = plastic_plan[col].fillna('NONE')

        for col in self.planner_constant_config.get(
            "QUANTITY_MATERIAL_REQUIRED_COLS", self.QUANTITY_MATERIAL_REQUIRED_COLS):
            if col in plastic_plan.columns:
                plastic_plan[col] = plastic_plan[col].fillna(0).astype('Float64')

        return plastic_plan

    def _process_plastic_data(self, 
                              producing_data: pd.DataFrame) -> pd.DataFrame:

        """Process plastic composition data."""

        composition_cols = self.planner_constant_config.get(
            "COMPOSITION_REQUIRED_COLS", self.COMPOSITION_REQUIRED_COLS)
        validate_dataframe(self.itemCompositionSummary_df, composition_cols)

        plastic_cols = self.planner_constant_config.get(
            "PLASTIC_BASE_COLS", self.PLASTIC_BASE_COLS) 
        validate_dataframe(producing_data, plastic_cols)

        # Merge with composition data
        plastic_data = producing_data[plastic_cols].copy()
        plastic_data = plastic_data.merge(
            self.itemCompositionSummary_df[composition_cols],
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