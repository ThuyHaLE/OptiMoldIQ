import pandas as pd
from loguru import logger
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os
from pathlib import Path
from datetime import datetime

from agents.decorators import validate_init_dataframes, validate_dataframe
from agents.core_helpers import check_newest_machine_layout, mold_item_plan_a_matching, create_mold_machine_compatibility_matrix
from agents.utils import read_change_log, load_annotation_path, save_output_with_versioning, ConfigReportMixin
from agents.autoPlanner.initialPlanner.processor.configs.pending_processor_config import PendingProcessorConfig, ExcelSheetMapping
from agents.autoPlanner.initialPlanner.optimizer.hist_based_mold_machine_optimizer import HistBasedMoldMachineOptimizer
from agents.autoPlanner.initialPlanner.optimizer.compatibility_based_mold_machine_optimizer import CompatibilityBasedMoldMachineOptimizer
from agents.autoPlanner.initialPlanner.processor.machine_assignment_processor import MachineAssignmentProcessor
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.initialPlanner.optimizer.compatibility_based_mold_machine_optimizer import PriorityOrder

@dataclass
class ProcessingResult:
    """Result from PendingProcessor"""
    used_producing_report_name: str
    final_assignment_summary: pd.DataFrame
    invalid_molds_dict: Dict[str, List]
    hist_based_assigned_molds: List
    hist_based_unassigned_molds: List
    compatibility_based_assigned_molds: Optional[List] = None
    compatibility_based_unassigned_molds: Optional[List] = None
    not_matched_pending: Optional[pd.DataFrame] = None
    log: str = ""

class DataValidationError(Exception):
    """Raised when data validation fails"""
    pass

# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
})

@validate_init_dataframes(lambda self: {
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
})

class PendingProcessor(ConfigReportMixin):
    
    """
    Processor for handling pending production assignments using two-tier optimization:
    1. History-based optimization (primary)
    2. Compatibility-based optimization (fallback for unassigned molds)
    """

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'producing_processor_change_log_path': str,
                'pending_processor_dir': str
                },
            'priority_order': PriorityOrder,
            'max_load_threshold': int,
            'log_progress_interval': int,
            'use_sample_data': bool,
            'efficiency': float,
            'loss': float
            }
        }

    def __init__(self, 
                 sheet_mapping: ExcelSheetMapping,
                 config: PendingProcessorConfig
                 ):
        
        """
        Initialize PendingProcessor with configuration.
        
        Args:
            sheet_mapping: ExcelSheetMapping containing Excel sheet name mappings for loading
            config: PendingProcessorConfig containing processing parameters
            including:
                - shared_source_config: 
                    - annotation_path: Path to the JSON file containing path annotations
                    - databaseSchemas_path: Path to database schemas JSON file for validation
                    - sharedDatabaseSchemas_path: Path to shared database schemas JSON file for validation
                    - producing_processor_change_log_path: Path to the ProducingProcessor change log
                    - pending_processor_dir: Directory for PendingProcessor outputs
                - priority_order: Priority ordering strategy
                - max_load_threshold: Maximum allowed load threshold. If None, no load constraint is applied (default=30)
                - log_progress_interval: Interval for logging progress during optimization (default=10)
                - use_sample_data: Whether to use sample data for testing or development purposes (default=False)
                - efficiency: Production efficiency factor (0.0 to 1.0)
                - loss: Production loss factor (0.0 to 1.0)
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="PendingProcessor")

        # Store configuration
        self.sheet_mapping = sheet_mapping
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

        # Check for the newest machine layout
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)
        
        # Set up output configuration
        self.filename_prefix = "pending_processor"
        self.output_dir = Path(self.config.shared_source_config.pending_processor_dir)

        # Initialize data containers
        self._initialize_data_containers()

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
            ('moldInfo', 'moldInfo_df')
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
    
    def _initialize_data_containers(self) -> None:
        """Initialize all data containers to None"""
        self.invalid_molds_dict = {}
        self.mold_lead_times = None
        self.not_matched_pending = None

    def process(self) -> ProcessingResult:
        """
        Run the complete pending processing workflow
        
        Returns:
            ProcessingResult: Complete results from processing
        """

        self.logger.info("Starting PendingProcessor ...")

        # Generate config header using mixin
        timestamp_start = datetime.now()
        timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        processor_log_lines = [config_header]
        processor_log_lines.append("--Processing Summary--")
        processor_log_lines.append(f"⤷ {self.__class__.__name__} results:")

        try:
            # Phase 1: Load and validate data
            self._load_and_validate_data()

            processor_log_lines.append("=" * 30)
            processor_log_lines.append("Data is loaded and valid. Starting optimization phases...")
            processor_log_lines.append("=" * 30)

            # Uncomment below to test retry logic
            #self.mold_machine_priority_matrix = pd.DataFrame()
            
            # Check if mold_machine_priority_matrix empty
            if self.mold_machine_priority_matrix.empty:
                self.logger.warning("Retry HybridSuggestOptimizer failed: Mold-Machine priority matrix is still empty.")
                self.logger.info("Starting compatibility optimization ...")

                unassigned_molds = self.mold_lead_times['moldNo'].to_list()
                assigned_matrix = pd.DataFrame(columns=self.machine_info_df['machineCode'])
                assigned_matrix.columns.name = None
                assigned_matrix.index.name = 'moldNo'
                
                processor_log_lines.append("Mold-Machine priority matrix is empty.")
                processor_log_lines.append("History-based optimization phase skipped.")
                processor_log_lines.append(f"Starting compatibility optimization for {len(unassigned_molds)} unassigned molds")

                (comp_assignment_summary, 
                comp_assigned_molds, 
                comp_unassigned_molds) = self._process_compatibility_based_phase(
                    assigned_matrix, 
                    unassigned_molds
                )

                processor_log_lines.append("Compatibility-based optimization phase completed successfully!")
                processor_log_str = "\n".join(processor_log_lines)
                self.logger.info("✅ Process finished!!!")

                return ProcessingResult(
                    used_producing_report_name=os.path.basename(self.report_path),
                    final_assignment_summary=comp_assignment_summary,
                    invalid_molds_dict=self.invalid_molds_dict,
                    hist_based_assigned_molds=assigned_matrix,
                    hist_based_unassigned_molds=unassigned_molds,
                    compatibility_based_assigned_molds=comp_assigned_molds,
                    compatibility_based_unassigned_molds=comp_unassigned_molds,
                    not_matched_pending=self.not_matched_pending,
                    log=processor_log_str
                )
            
            # Phase 2: Execute optimization phases
            (final_summary, 
             hist_assigned_molds, 
             hist_unassigned_molds, 
             comp_assigned_molds, 
             comp_unassigned_molds,
             phase_log) = self._execute_optimization_phases()
            
            processor_log_lines.append("Optimization phase completed successfully!")
            processor_log_lines.append(phase_log)

            # Calculate processing time
            timestamp_end = datetime.now()
            processing_time = (timestamp_end - timestamp_start).total_seconds()
            
            processor_log_lines.append("\n✓ Manufacturing data processing completed!")
            processor_log_lines.append(f"⤷ Processing time: {processing_time:.2f}s")
            processor_log_lines.append(f"⤷ End time: {timestamp_end.strftime('%Y-%m-%d %H:%M:%S')}")

            processor_log_str = "\n".join(processor_log_lines)
            
            self.logger.info("✅ Process finished!!!")
            
            # Phase 3: Create and return results
            return ProcessingResult(
                used_producing_report_name=os.path.basename(self.report_path),
                final_assignment_summary=final_summary,
                invalid_molds_dict=self.invalid_molds_dict,
                hist_based_assigned_molds=hist_assigned_molds,
                hist_based_unassigned_molds=hist_unassigned_molds,
                compatibility_based_assigned_molds=comp_assigned_molds,
                compatibility_based_unassigned_molds=comp_unassigned_molds,
                not_matched_pending=self.not_matched_pending,
                log=processor_log_str
            )
            
        except Exception as e:
            self.logger.error("Processing pipeline failed: {}", str(e))
            raise

    def process_and_save_results(self):
        try:

            pending_processor_result = self.process()
            
            # Prepare export data
            final_results = {
                'initialPlan': pending_processor_result.final_assignment_summary,
                'invalid_molds': pd.DataFrame([
                    {"category": k, "mold": v} 
                    for k, values in pending_processor_result.invalid_molds_dict.items() for v in values])
                    }
            
            # Generate validation summary
            reporter = DictBasedReportGenerator(use_colors=False)
            processor_summary = "\n".join(reporter.export_report(final_results))

            # Log data summary
            export_log_lines = []
            export_log_lines.append("DATA EXPORT SUMMARY")
            export_log_lines.append(f"⤷ Producing records: {len(final_results['initialPlan'])}")
            export_log_lines.append(f"⤷ Pending records: {len(final_results['invalid_molds'])}")

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
            master_log_lines = [pending_processor_result.log, "\n".join(export_log_lines)]
            master_log_str = "\n".join(master_log_lines)

            try:
                log_path = self.output_dir / "change_log.txt"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(master_log_str)
                self.logger.info("✓ Updated and saved change log: {}", log_path)
            except Exception as e:
                self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

            return final_results, master_log_str

        except Exception as e:
            self.logger.error("Processing pipeline failed: {}", str(e))
            raise
    
    #---------------------------------#
    # PHASE 1: LOAD AND VALIDATE DATA #
    #---------------------------------#
    def _load_and_validate_data(self) -> None:
        """Phase 1: Load and validate all required data"""
        # Load producing processor report
        self._load_producing_processor_report()
        
        # Validate dataframes
        self._validate_loaded_dataframes()
        
        # Prepare mold lead times
        self._prepare_mold_lead_times()

        # Retry HybridSuggestOptimizer if needed
        # Uncomment below to test retry logic
        #self.mold_machine_priority_matrix = pd.DataFrame()
        self.retry_hybrid_phase_if_needed()
    
    #--------------------------------------------#
    # PHASE 1-1: LOAD PRODUCING PROCESSOR REPORT #
    #--------------------------------------------#
    def _load_producing_processor_report(self) -> None:
        """Load all required data from producing processor report"""
        self.logger.info("Loading producing processor report...")
        
        try:
            if not os.path.isfile(self.config.shared_source_config.producing_processor_change_log_path):
                self.logger.warning("Producing processor report not found at: {}",
                                    self.config.shared_source_config.producing_processor_change_log_path)
                self.logger.info("Retrying ProducingProcessor to execute the report...")
                self.retry_producing_processor_if_needed()

            # Get report path
            self.report_path = self._get_report_path()

            # Validate sheets
            self._validate_excel_sheets(self.report_path)
            
            # Load all sheets
            sheet_mappings = self.sheet_mapping.get_sheet_mappings()
            for sheet_name, attr_name in sheet_mappings.items():
                self._load_excel_sheet(self.report_path, sheet_name, attr_name)
            
            # Process invalid molds
            self._process_invalid_molds()
            
        except Exception as e:
            self.logger.error("Failed to load producing processor report: {}", str(e))
            raise
    
    def _get_report_path(self) -> str:
        """Get the report path from change log"""
        return read_change_log(
            Path(self.config.shared_source_config.producing_processor_change_log_path).parent, 
            Path(self.config.shared_source_config.producing_processor_change_log_path).name
        )
    
    def retry_producing_processor_if_needed(self) -> None:
        """Retry ProducingProcessor if producing report is missing"""
        from agents.autoPlanner.initialPlanner.processor.producing_processor import ProducingProcessorConfig, ProducingProcessor
        processor = ProducingProcessor(
            config = ProducingProcessorConfig(
                shared_source_config = self.config.shared_source_config,
                efficiency = self.config.efficiency,
                loss = self.config.loss
                ))
        processor_result, processor_log_str  = processor.process_and_save_results()
        if processor_result.status != "SUCCESS":
            self.logger.error("ProducingProcessor did not complete successfully")
            raise ValueError("ProducingProcessor did not complete successfully")   

    def _validate_excel_sheets(self, report_path: str) -> List[str]:
        """Validate that all required sheets exist in the Excel file"""
        available_sheets = pd.ExcelFile(report_path).sheet_names
        self.logger.info("Available sheets: {}", available_sheets)
        
        sheet_mappings = self.sheet_mapping.get_sheet_mappings()
        missing_sheets = [sheet for sheet in sheet_mappings.keys() if sheet not in available_sheets]
        
        if missing_sheets:
            raise DataValidationError(f"Missing required sheets: {missing_sheets}")
        
        return available_sheets

    def _load_excel_sheet(self, report_path: str, sheet_name: str, attr_name: str) -> None:
        """Load a single Excel sheet and set it as an attribute"""
        df = pd.read_excel(report_path, sheet_name=sheet_name)
        
        # Apply special processing if needed
        if sheet_name in self.sheet_mapping.get_sheets_requiring_index():
            df = self._apply_sheet_specific_processing(df, sheet_name)
        
        setattr(self, attr_name, df)
        self.logger.debug("Loaded {}: {} rows", attr_name, len(df))
    
    def _apply_sheet_specific_processing(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Apply sheet-specific processing (e.g., setting index)"""
        if sheet_name == self.sheet_mapping.mold_machine_priority_matrix:
            return df.set_index('moldNo')
        return df

    def _process_invalid_molds(self) -> None:
        """Process invalid molds data into dictionary format"""
        self.invalid_molds_dict = {
            col: self.invalid_molds[col].dropna().tolist() 
            for col in self.invalid_molds.columns
        }
        self.logger.info("Invalid molds categories: {}", list(self.invalid_molds_dict.keys()))

    #---------------------------------------#
    # PHASE 1-2: VALIDATE LOADED DATAFRAMES #
    #---------------------------------------#
    def _validate_loaded_dataframes(self) -> None:
        """Validate all loaded dataframes against expected schemas"""
        validation_mappings = {
            'producing_data': self.producing_status_data,
            'pending_data': self.pending_status_data,
            'mold_estimated_capacity': self.mold_estimated_capacity_df
        }
        
        for schema_name, dataframe in validation_mappings.items():
            self._validate_single_dataframe(schema_name, dataframe)
    
    def _validate_single_dataframe(self, 
                                   schema_name: str, 
                                   dataframe: pd.DataFrame) -> None:
        """Validate a single dataframe against its schema"""
        try:
            expected_cols = list(self.sharedDatabaseSchemas_data[schema_name]['dtypes'].keys())
            self.logger.info('Validation for {}...', schema_name)
            validate_dataframe(dataframe, expected_cols)
        except Exception as e:
            self.logger.error(
                "Validation failed for {} (expected cols: {}): {}", 
                schema_name, expected_cols, str(e)
            )
            raise
    
    #------------------------------------#
    # PHASE 1-3: PREPARE MOLD LEAD TIMES #
    #------------------------------------#
    def _prepare_mold_lead_times(self) -> None:
        """Match molds with items and calculate lead times"""
        self.logger.info("Preparing mold lead times...")
        
        try:
            self.mold_lead_times, self.not_matched_pending = mold_item_plan_a_matching(
                self.pending_status_data, 
                self.mold_estimated_capacity_df
            )
            self.logger.info("Cannot match item-mold: {}", 
                           len(self.not_matched_pending) if self.not_matched_pending is not None else 0)
        except Exception as e:
            self.logger.error("Failed to prepare mold lead times: {}", str(e))
            raise
    
    #-------------------------------------------#
    # PHASE 1-4: RETRY HYBRID SUGGEST OPTIMIZER #
    #-------------------------------------------#    
    def retry_hybrid_phase_if_needed(self) -> None:
        if self.mold_machine_priority_matrix.empty:
            self.logger.warning("Mold-Machine priority matrix is not loaded or empty.")
            self.logger.info("Retrying HybridSuggestOptimizer to generate the priority matrix...")
            self.retry_hybrid_optimizer()
    
    def retry_hybrid_optimizer(self) -> None:
        """Retry HybridSuggestOptimizer"""
        from agents.autoPlanner.initialPlanner.optimizer.hybrid_optimizer.hybrid_suggest_optimizer import (
            HybridSuggestConfig, HybridSuggestOptimizer)

        # Initialize optimizer
        self.optimizer = HybridSuggestOptimizer(
            config = HybridSuggestConfig(
                shared_source_config = self.config.shared_source_config,
                efficiency = self.config.efficiency,
                loss = self.config.loss
                )
            )
        optimization_results = self.optimizer.process()

        self.mold_estimated_capacity_df = optimization_results.mold_estimated_capacity_df
        self.mold_machine_priority_matrix = optimization_results.mold_machine_priority_matrix
        self.logger.info("Retry HybridSuggestOptimizer completed.")

    #--------------------------------------# 
    # PHASE 2: EXECUTE OPTIMIZATION PHASES #
    #--------------------------------------#     
    def _execute_optimization_phases(self) -> Tuple[pd.DataFrame, List, List, Optional[List], Optional[List]]:
        """Execute both optimization phases and return results"""

        self.logger.info("Starting optimization phases ...")
        phase_log_lines = []

        # Phase 1: History-based optimization
        (hist_assigned_matrix, 
         hist_assignment_summary, 
         hist_assigned_molds, 
         hist_unassigned_molds,
         phase_log) = self._process_history_based_phase()
        
        phase_log_lines.append("History-based optimization phase completed successfully!")
        phase_log_lines.append(phase_log)

        # Phase 2: Handle unassigned molds
        comp_assigned_molds = None
        comp_unassigned_molds = None
        
        if self._should_run_compatibility_optimization(hist_unassigned_molds):
            
            self.logger.info("Starting compatibility optimization ...")
            phase_log_lines.append(f"Starting compatibility-based optimization for {len(hist_unassigned_molds)} unassigned molds")
            (comp_assignment_summary, 
             comp_assigned_molds, 
             comp_unassigned_molds) = self._process_compatibility_based_phase(
                hist_assigned_matrix, 
                hist_unassigned_molds
            )
            phase_log_lines.append("Compatibility-based optimization phase completed successfully!")

            # Combine results
            final_summary = self._combine_assignments(
                hist_assignment_summary, 
                comp_assignment_summary
            )
        else:
            # All molds assigned by history-based optimization
            final_summary = hist_assignment_summary.copy()
            final_summary['Note'] = 'histBased'

        phase_log_lines.append("Assignment refinement completed successfully!")
        self.logger.info("All molds assigned by history-based optimization")
        
        phase_log_str = "\n".join(phase_log_lines)

        self.logger.info("✅ Process finished!!!")

        return (final_summary, hist_assigned_molds, hist_unassigned_molds, 
                comp_assigned_molds, comp_unassigned_molds, phase_log_str)
    
    def _process_assignments(self, 
                             assigned_matrix: pd.DataFrame, 
                             mold_lead_times: pd.DataFrame,
                             pending_data: pd.DataFrame) -> pd.DataFrame:
        """Process assignments and generate summary"""
        try:
            producing_mold_list = self.producing_status_data['moldNo'].unique().tolist()
            producing_info_list = self.producing_status_data[['machineCode', 'moldNo']].drop_duplicates().values.tolist()
            
            processor = MachineAssignmentProcessor(
                assigned_matrix,
                mold_lead_times,
                pending_data,
                self.machine_info_df,
                producing_mold_list,
                producing_info_list
            )
            
            return processor.process_all()
            
        except Exception as e:
            self.logger.error("Assignment processing failed: {}", str(e))
            raise

    #---------------------------------------#
    # PHASE 2-1: HISTORY-BASED OPTIMIZATION #
    #---------------------------------------#
    def _process_history_based_phase(self) -> Tuple[pd.DataFrame, pd.DataFrame, List, List]:
        """Process the history-based optimization phase"""

        self.logger.info("Starting history-based optimization phase ...")

        phase_log_lines = []
        
        # Run history-based optimization
        (assigned_matrix, 
         assigned_molds, 
         unassigned_molds,
         optimizer_log) = self._run_history_based_optimization()
        phase_log_lines.append("History-based optimization completed successfully!")
        phase_log_lines.append(optimizer_log)
        
        # Process assignments
        assignment_summary = self._process_assignments(
            assigned_matrix, 
            self.mold_lead_times, 
            self.pending_status_data
        )
        phase_log_lines.append("Assignment summarization completed successfully!")

        phase_log_str = "\n".join(phase_log_lines)

        self.logger.info("✅ Process finished!!!")

        return assigned_matrix, assignment_summary, assigned_molds, unassigned_molds, phase_log_str
    
    def _run_history_based_optimization(self) -> Tuple[pd.DataFrame, List, List]:
        """Run history-based optimization (first tier)"""
        
        self.logger.info("Starting history-based optimization (first tier) ...")
        
        try:
            optimizer = HistBasedMoldMachineOptimizer(
                self.mold_machine_priority_matrix,
                self.mold_lead_times,
                self.producing_status_data,
                self.machine_info_df,
                max_load_threshold=self.config.max_load_threshold
            )
            
            results = optimizer.run_optimization()
            
            self.logger.info(
                "\nHistory-based - Assigned: {} molds, Unassigned: {} molds", 
                len(results.assignments), 
                len(results.unassigned_molds)
            )
            
            return results.assigned_matrix, results.assignments, results.unassigned_molds, results.log
            
        except Exception as e:
            self.logger.error("History-based optimization failed: {}", str(e))
            raise

    #----------------------------------------------#
    # PHASE 2-2: COMPATIBILITY-BASED OPTIMIZATION  #
    #----------------------------------------------#
    def _should_run_compatibility_optimization(self, 
                                               unassigned_molds: List) -> bool:
        """Determine if compatibility-based optimization should run"""
        unassigned_count = len(unassigned_molds)
        
        # Force compatibility optimization for sample data testing
        if self.config.use_sample_data:
            return True
            
        return unassigned_count > 0

    def _process_compatibility_based_phase(self, 
                                           hist_assigned_matrix: pd.DataFrame,
                                           hist_unassigned_molds: List) -> Tuple[pd.DataFrame, List, List]:
        """Process the compatibility-based optimization phase"""
        # Prepare unassigned data
        (unassigned_mold_lead_times, 
         unassigned_pending_data) = self._prepare_unassigned_data(hist_unassigned_molds)
        
        # Run compatibility-based optimization
        (comp_assigned_matrix, 
         comp_assigned_molds, 
         comp_unassigned_molds) = self._run_compatibility_based_optimization(
            hist_assigned_matrix, 
            unassigned_mold_lead_times
        )
        
        # Process compatibility-based assignments
        comp_assignment_summary = self._process_assignments(
            comp_assigned_matrix,
            unassigned_mold_lead_times,
            unassigned_pending_data
        )
        
        return comp_assignment_summary, comp_assigned_molds, comp_unassigned_molds
    
    def _prepare_unassigned_data(self, unassigned_molds: List) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for unassigned molds"""
        if self.config.use_sample_data:
            return self._create_sample_data()
        
        unassigned_items = self.mold_lead_times.loc[
            self.mold_lead_times["moldNo"].isin(unassigned_molds), 
            "itemCode"
        ].tolist()
        
        unassigned_mold_lead_times = self.mold_lead_times[
            self.mold_lead_times["moldNo"].isin(unassigned_molds)
        ]
        
        unassigned_pending_data = self.pending_status_data[
            self.pending_status_data["itemCode"].isin(unassigned_items)
        ]
        
        return unassigned_mold_lead_times, unassigned_pending_data

    def _run_compatibility_based_optimization(self, 
                                            assigned_matrix: pd.DataFrame,
                                            unassigned_mold_lead_times: pd.DataFrame
                                            ) -> Tuple[pd.DataFrame, List, List]:
        """Run compatibility-based optimization (second tier)"""
        self.logger.info("Running compatibility-based optimization...")
        
        try:
            # Create compatibility matrix
            compatibility_matrix = create_mold_machine_compatibility_matrix(
                self.machineInfo_df, 
                self.moldInfo_df, 
                validate_data=True
            )
            
            # Run optimization
            optimizer = CompatibilityBasedMoldMachineOptimizer(
                log_progress_interval=self.config.log_progress_interval
            )
            
            results = optimizer.run_optimization(
                mold_machine_assigned_matrix=assigned_matrix,
                unassigned_mold_lead_times=unassigned_mold_lead_times,
                compatibility_matrix=compatibility_matrix,
                priority_order=self.config.priority_order,
                max_load_threshold=self.config.max_load_threshold
            )
            
            self.logger.info(
                "\nCompatibility-based - Assigned: {} molds, Unassigned: {} molds", 
                len(results.assignments), 
                len(results.unassigned_molds)
            )
            
            # Update invalid molds
            self.invalid_molds_dict['mold_machine_optimizer'] = results.unassigned_molds
            
            return results.assigned_matrix, results.assignments, results.unassigned_molds
            
        except Exception as e:
            self.logger.error("Compatibility-based optimization failed: {}", str(e))
            raise
    
    def _combine_assignments(self, 
                             hist_based_df: pd.DataFrame, 
                             compatibility_based_df: pd.DataFrame) -> pd.DataFrame:
        """Combine history-based and compatibility-based assignments"""
        try:
            # Add notes to distinguish assignment types
            hist_based_df = hist_based_df.copy()
            compatibility_based_df = compatibility_based_df.copy()
            
            hist_based_df['Note'] = 'histBased'
            compatibility_based_df['Note'] = 'compatibilityBased'
            
            # Validate required columns
            required_cols = ['Machine No.', 'Priority in Machine', 'Machine Code', 'PO Quantity']
            self._validate_assignment_dataframes(hist_based_df, compatibility_based_df, required_cols)
            
            # Calculate priority adjustments
            max_priority_by_machine = hist_based_df.groupby('Machine No.')['Priority in Machine'].max().to_dict()
            compatibility_based_df['Priority in Machine'] += (
                compatibility_based_df['Machine No.'].map(max_priority_by_machine).fillna(0)
            )
            
            # Combine and sort
            combined_df = (
                pd.concat([hist_based_df, compatibility_based_df], ignore_index=True)
                .sort_values(['Machine No.', 'Priority in Machine'])
                .reset_index(drop=True)
            )
            
            # Remove duplicates with zero quantity
            mask_multi = combined_df.groupby('Machine Code')['Machine Code'].transform('count') > 1
            filtered_df = combined_df[~((mask_multi) & (combined_df['PO Quantity'] == 0))]
            
            return filtered_df
            
        except Exception as e:
            self.logger.error("Failed to combine assignments: {}", str(e))
            raise
    
    def _validate_assignment_dataframes(self, 
                                        hist_df: pd.DataFrame, 
                                        comp_df: pd.DataFrame, 
                                        required_cols: List[str]) -> None:
        """Validate assignment DataFrames have required structure"""
        for name, df in [('history-based', hist_df), ('compatibility-based', comp_df)]:
            # Check required columns
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise DataValidationError(f"{name} DataFrame missing columns: {missing_cols}")
            
            # Check for duplicate priorities within machines
            duplicates = df.duplicated(subset=['Machine No.', 'Priority in Machine'])
            if duplicates.any():
                raise DataValidationError(f"{name} DataFrame has duplicate priorities within machines")

    @staticmethod
    def _create_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create sample data for testing purposes (Round 3)"""
        unassigned_mold_lead_times = pd.DataFrame({
            'itemCode': ['10136M', '10441M', '10142M', '10250M', '24724309M',
                         '24721319M', '24725323M', '24724326M', '24721327M'],
            'moldNo': ['15300CBS-M-001', 'PSSC-M-001', '12002CBS-M-001', 'PGXSR-M-001',
                       'PSPH2-M-001', '14102CAJ-M-003', 'PXNLG5-M-001', '12000CBG-M-001', '16200CBG-M-001'],
            'totalQuantity': [100000, 10000, 15000, 44000, 2516, 180000, 155000, 340000, 175000],
            'balancedMoldHourCapacity': [345.52, 544.58, 544.58, 636.68, 689.82, 534.3, 395.97, 1065.84, 1108.43],
            'moldLeadTime': [10, 5, 1, 2, 1, 14, 16, 13, 7]
        })
        
        unassigned_pending_data = pd.DataFrame({
            'poNo': ['IM2812004', 'IM2901020', 'IM2902001', 'IM2902002', 'IM2902047', 
                     'IM2902116', 'IM2902118', 'IM2902119', 'IM2902120'],
            'itemCode': ['10136M', '10441M', '10142M', '10250M', '24724309M',
                         '24721319M', '24725323M', '24724326M', '24721327M'],
            'itemName': ['CT-YA-PRINTER-HEAD-4.2MM', 'ABC-TP-BODY', 'ABC-TP-LARGE-CAP-027-BG', 
                         'ABC-TP-LARGE-CAP-055-YW', 'ABC-TP-SMALL-CAP-062-YW',
                         'CTT-CAX-UPPER-CASE-PINK', 'CTT-CAX-LOWER-CASE-PINK', 
                         'CTT-CAX-CARTRIDGE-BASE', 'CTT-CAX-BASE-COVER'],
            'poETA': ['2019-02-20'] * 9,
            'itemQuantity': [100000, 10000, 15000, 44000, 2516, 180000, 155000, 340000, 175000]
        })
        
        return unassigned_mold_lead_times, unassigned_pending_data