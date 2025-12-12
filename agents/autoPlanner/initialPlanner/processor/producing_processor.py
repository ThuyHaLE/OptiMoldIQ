import pandas as pd
import numpy as np
import os
from typing import Tuple
from dataclasses import dataclass

from agents.decorators import validate_init_dataframes, validate_dataframe
from pathlib import Path
from loguru import logger
from agents.utils import load_annotation_path, save_output_with_versioning, ConfigReportMixin
from agents.core_helpers import check_newest_machine_layout
from datetime import datetime
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.initialPlanner.optimizer.hybrid_optimizer.hybrid_suggest_optimizer import OptimizationResult, HybridSuggestConfig, HybridSuggestOptimizer
from agents.autoPlanner.initialPlanner.processor.configs.producing_processor_config import RequiredColumns, ProducingProcessorConfig

@dataclass
class ProductionProcessingResult:
    """Container for production processing results."""
    optimization_results: OptimizationResult
    pending_status_data: pd.DataFrame
    producing_status_data: pd.DataFrame
    pro_plan: pd.DataFrame
    mold_plan: pd.DataFrame
    plastic_plan: pd.DataFrame
    log: str = ""

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "itemCompositionSummary_df": list(self.databaseSchemas_data['staticDB']['itemCompositionSummary']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "proStatus_df": list(self.sharedDatabaseSchemas_data["pro_status"]['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
})

class ProducingProcessor(ConfigReportMixin):

    """
    A comprehensive class for processing manufacturing/molding/producing data including mold capacity,
    production planning, and plastic usage calculations.
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'progress_tracker_change_log_path': str,
                'mold_machine_weights_hist_path': str,
                'mold_stability_index_change_log_path': str,
                'producing_processor_dir': str
                },
            'efficiency': float,
            'loss': float
            }
        }

    def __init__(self,
                 config: ProducingProcessorConfig):
        
        """
        Initialize ProducingProcessor with configuration.
        
        Args:
            config: ProducingProcessorConfig containing processing parameters
            including:
                - shared_source_config: 
                    - annotation_path: Path to the JSON file containing path annotations
                    - databaseSchemas_path: Path to database schemas JSON file for validation
                    - sharedDatabaseSchemas_path: Path to shared database schemas JSON file for validation
                    - progress_tracker_change_log_path: Path to the OrderProgressTracker change log
                    - mold_machine_weights_hist_path: Path to mold-machine feature weights (from MoldMachineFeatureWeightCalculator)
                    - mold_stability_index_change_log_path: Path to the MoldStabilityIndexCalculator change log
                    - producing_processor_dir: Directory for ProducingProcessor outputs
                - efficiency: Production efficiency factor (0.0 to 1.0)
                - loss: Production loss factor (0.0 to 1.0)
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="ProducingProcessor")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        # Load database schema configuration for column validation
        self.load_schema_and_annotations()
        self._load_dataframes()
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        # Set up output configuration
        self.filename_prefix = "producing_processor"
        self.output_dir = Path(self.config.shared_source_config.producing_processor_dir)

        # Initialize optimizer
        self.optimizer = HybridSuggestOptimizer(
            config = HybridSuggestConfig(
                shared_source_config = self.config.shared_source_config,
                efficiency = self.config.efficiency,
                loss = self.config.loss
                )
            )
    
    def load_schema_and_annotations(self):
        """Load database schemas and path annotations from configuration files."""
        self.databaseSchemas_data = self._load_annotation_from_config(
            self.config.shared_source_config.databaseSchemas_path
        )
        self.sharedDatabaseSchemas_data = self._load_annotation_from_config(
            self.config.shared_source_config.sharedDatabaseSchemas_path
        )
        self.path_annotation = self._load_annotation_from_config(
            self.config.shared_source_config.annotation_path
        )

    def _load_annotation_from_config(self, config_path):
        """Helper function to load annotation from a config path."""
        return load_annotation_path(
            Path(config_path).parent,
            Path(config_path).name
        )
    
    def _load_dataframes(self) -> None:

        """
        Load all required DataFrames from parquet files with consistent error handling.

        This method loads the following DataFrames:
        - productRecords_df: Production records with item, mold, machine data
        - machineInfo_df: Machine specifications and tonnage information
        - moldSpecificationSummary_df: Mold specifications and compatible items
        - moldInfo_df: Detailed mold information including tonnage requirements
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

    def process(self):
        """Execute the complete processing workflow."""
        self.logger.info("Starting ProducingProcessor ...")

        # Generate config header using mixin
        timestamp_start = datetime.now()
        timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)

        processor_log_lines = [config_header]
        processor_log_lines.append("--Processing Summary--")
        processor_log_lines.append(f"⤷ {self.__class__.__name__} results:")

        try:
            processor_log_lines.append("=" * 30)
            processor_log_lines.append("Starting hybrid suggest optimization...")
            processor_log_lines.append("=" * 30)

            # Execute optimization
            optimization_results = self.optimizer.process()

            # Log optimization summary
            processor_log_lines.append(f"✓ Optimization status: {optimization_results.status}")
            processor_log_lines.append(
                f"⤷ Invalid molds: {len(optimization_results.estimated_capacity_invalid_molds + optimization_results.priority_matrix_invalid_molds)}")
            processor_log_lines.append(
                f"⤷ Capacity data: {optimization_results.mold_estimated_capacity_df.shape}")
            processor_log_lines.append(
                f"⤷ Priority matrix: {optimization_results.mold_machine_priority_matrix.shape}")
            
            # Append detailed optimization log
            processor_log_lines.append("⤷ Details: ")
            processor_log_lines.append(optimization_results.log)

            # Validate optimization status and handle accordingly
            if optimization_results.status == "PHASE_1_FAILED":
                # Critical failure - cannot proceed
                self.logger.error("Critical failure - Phase 1 failed, no data available")
                processor_log_lines.append("\n❌ CRITICAL FAILURE: Phase 1 optimization failed")
                processor_log_lines.append("⤷ Cannot proceed with production data processing")
                processor_log_lines.append(f"⤷ See optimization log for details")
                
                processor_log_str = "\n".join(processor_log_lines)
                self.logger.error("Process terminated due to Phase 1 failure")
                
                return ProductionProcessingResult(
                    optimization_results=optimization_results,
                    pending_status_data=None,
                    producing_status_data=None,
                    pro_plan=None,
                    mold_plan=None,
                    plastic_plan=None,
                    log=processor_log_str
                )
            
            elif optimization_results.status == "PHASE_2_FAILED":
                # Partial success - proceed with Phase 1 data only
                self.logger.warning("Phase 2 failed, proceeding with partial results from Phase 1")
                processor_log_lines.append("\n⚠️ WARNING: Phase 2 optimization failed")
                processor_log_lines.append("⤷ Proceeding with Phase 1 data only: mold_estimated_capacity_df")
                processor_log_lines.append("⤷ Priority matrix will not be available")
            
            elif optimization_results.status == "SUCCESS":
                # Full success
                self.logger.info("Both optimization phases completed successfully")
                processor_log_lines.append("\n✓ SUCCESS: Both optimization phases completed")
                processor_log_lines.append("⤷ Using both results: mold_estimated_capacity_df and mold_machine_priority_matrix")

            else:
                # Unexpected status
                self.logger.warning(f"Unexpected optimization status: {optimization_results.status}")
                processor_log_lines.append(f"\n⚠️ Unexpected optimization status: {optimization_results.status}")

        except Exception as e:
            logger.error("Optimization failed: {}", e)
            raise
            
        try:
            cols = list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys())
            validate_dataframe(optimization_results.mold_estimated_capacity_df, cols)
            processor_log_lines.append("\n✓ Validation for mold_estimated_capacity: PASSED!")
        except Exception as e:
            self.logger.error("Validation for mold_estimated_capacity: FAILED! (expected cols: {}): {}", cols, e)
            raise

        # Process the data (only if optimization was at least partially successful)
        try:
            (pending_status_data,
            producing_status_data,
            pro_plan,
            mold_plan,
            plastic_plan) = self._process_production_data(optimization_results.proStatus_df,
                                                          optimization_results.mold_estimated_capacity_df)
            
            # Calculate processing time
            timestamp_end = datetime.now()
            processing_time = (timestamp_end - timestamp_start).total_seconds()
            
            processor_log_lines.append("\n✓ Manufacturing data processing completed!")
            processor_log_lines.append(f"⤷ Processing time: {processing_time:.2f}s")
            processor_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")

            processor_log_str = "\n".join(processor_log_lines)
            
            self.logger.info("✅ Process finished!!!")

            return ProductionProcessingResult(
                optimization_results=optimization_results,
                pending_status_data=pending_status_data,
                producing_status_data=producing_status_data,
                pro_plan=pro_plan,
                mold_plan=mold_plan,
                plastic_plan=plastic_plan,
                log=processor_log_str
            )

        except FileNotFoundError as e:
            self.logger.debug("File not found: {}. \nPlease ensure all required data files are available.", e)
            raise
        except Exception as e:
            self.logger.debug("Error processing data: {}. \nPlease check your data files and try again.", e)
            raise

    def process_and_save_results(self, **kwargs):
        
        def priority_matrix_process(priority_matrix):
            if priority_matrix is None:
                self.logger.warning("Priority matrix is None - Phase 2 optimization may have failed")
                return pd.DataFrame()
            priority_matrix.columns.name = None
            return priority_matrix.reset_index()

        producing_processor_result = self.process()

        # Extract optimization results for cleaner access
        opt_results = producing_processor_result.optimization_results

        # Prepare export data
        final_results = {
            "producing_status_data": producing_processor_result.producing_status_data,
            "producing_pro_plan": producing_processor_result.pro_plan,
            "producing_mold_plan": producing_processor_result.mold_plan,
            "producing_plastic_plan": producing_processor_result.plastic_plan,
            "pending_status_data": producing_processor_result.pending_status_data,
            "mold_machine_priority_matrix": priority_matrix_process(opt_results.mold_machine_priority_matrix),
            "mold_estimated_capacity_df": opt_results.mold_estimated_capacity_df,
        }

        # Create invalid molds DataFrame
        estimated_invalid = opt_results.estimated_capacity_invalid_molds
        priority_invalid = opt_results.priority_matrix_invalid_molds
        max_len = max(len(estimated_invalid), len(priority_invalid))
        
        final_results["invalid_molds"] = pd.DataFrame({
            "estimated_capacity_invalid_molds": estimated_invalid + [""] * (max_len - len(estimated_invalid)),
            "priority_matrix_invalid_molds": priority_invalid + [""] * (max_len - len(priority_invalid))
        })

        # Generate validation summary
        reporter = DictBasedReportGenerator(use_colors=False)
        processor_summary = "\n".join(reporter.export_report(final_results))

        # Log data summary
        export_log_lines = []
        export_log_lines.append("DATA EXPORT SUMMARY")
        export_log_lines.append(f"⤷ Producing records: {len(final_results['producing_status_data'])}")
        export_log_lines.append(f"⤷ Pending records: {len(final_results['pending_status_data'])}")
        export_log_lines.append(f"⤷ Production plan: {len(final_results['producing_pro_plan'])}")
        export_log_lines.append(f"⤷ Mold plan: {len(final_results['producing_mold_plan'])}")
        export_log_lines.append(f"⤷ Plastic plan: {len(final_results['producing_plastic_plan'])}")
        export_log_lines.append(f"⤷ Priority matrix: {final_results['mold_machine_priority_matrix'].shape}")
        export_log_lines.append(f"⤷ Invalid molds: {len(estimated_invalid) + len(priority_invalid)} total")

        # Export results to Excel files with versioning
        self.logger.info("Start excel file exporting...")
        try:
            output_exporting_log = save_output_with_versioning(
                data = final_results,
                output_dir = self.output_dir,
                filename_prefix = self.filename_prefix,
                report_text = processor_summary
            )
            export_log_lines.append("✓ Results exported successfully!")
            export_log_lines.append(output_exporting_log)
            self.logger.info("✓ Results exported successfully!")
        except Exception as e:
            self.logger.error("✗ Excel export failed: {}", e)
            raise

        # Combine all logs
        master_log_lines = [producing_processor_result.log, "\n".join(export_log_lines)]
        master_log_str = "\n".join(master_log_lines)

        try:
            log_path = self.output_dir / "change_log.txt"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(master_log_str)
            self.logger.info("✓ Updated and saved change log: {}", log_path)
        except Exception as e:
            self.logger.error("✗ Failed to save change log {}: {}", log_path, e)
        
        return producing_processor_result, master_log_str

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

        # Filter producing data
        (producing_status_data, 
         pending_status_data) = ProducingProcessor._split_producing_and_pending_orders(proStatus_df,
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