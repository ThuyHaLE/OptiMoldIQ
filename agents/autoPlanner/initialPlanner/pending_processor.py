import pandas as pd
from loguru import logger
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import os
from pathlib import Path

from agents.core_helpers import (
    check_newest_machine_layout, mold_item_plan_a_matching, create_mold_machine_compatibility_matrix)

from agents.decorators import validate_init_dataframes, validate_dataframe

from agents.utils import read_change_log, load_annotation_path, save_output_with_versioning
from agents.autoPlanner.initialPlanner.hist_based_mold_machine_optimizer import HistBasedMoldMachineOptimizer
from agents.autoPlanner.initialPlanner.compatibility_based_mold_machine_optimizer import (
    CompatibilityBasedMoldMachineOptimizer, PriorityOrder)
from agents.autoPlanner.initialPlanner.machine_assignment_processor import MachineAssignmentProcessor


@dataclass
class ProcessingConfig:
    """Configuration for PendingProcessor"""
    max_load_threshold: int = 30
    priority_order: PriorityOrder = PriorityOrder.PRIORITY_1
    log_progress_interval: int = 5
    verbose: bool = True
    use_sample_data: bool = False


@dataclass
class ExcelSheetMapping:
    """Configuration for Excel sheet loading"""
    producing_status_data: str = 'producing_status_data'
    pending_status_data: str = 'pending_status_data'
    mold_machine_priority_matrix: str = 'mold_machine_priority_matrix'
    mold_estimated_capacity_df: str = 'mold_estimated_capacity_df'
    invalid_molds: str = 'invalid_molds'
    
    def get_sheet_mappings(self) -> Dict[str, str]:
        """Get dictionary mapping of sheet names to attribute names"""
        return {
            self.producing_status_data: 'producing_status_data',
            self.pending_status_data: 'pending_status_data', 
            self.mold_machine_priority_matrix: 'mold_machine_priority_matrix',
            self.mold_estimated_capacity_df: 'mold_estimated_capacity_df',
            self.invalid_molds: 'invalid_molds'
        }
    
    def get_sheets_requiring_index(self) -> List[str]:
        """Get list of sheets that need special index processing"""
        return [self.mold_machine_priority_matrix]

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

class PendingProcessor:
    
    """
    Processor for handling pending production assignments using two-tier optimization:
    1. History-based optimization (primary)
    2. Compatibility-based optimization (fallback for unassigned molds)
    """
    
    def __init__(self, 
                 source_path: str = 'agents/shared_db/DataLoaderAgent/newest',
                 annotation_name: str = "path_annotations.json",
                 databaseSchemas_path: str = 'database/databaseSchemas.json',
                 sharedDatabaseSchemas_path: str = 'database/sharedDatabaseSchemas.json',
                 default_dir: str = "agents/shared_db/AutoPlanner/InitialPlanner",
                 producing_processor_folder_path: str = 'agents/shared_db/AutoPlanner/InitialPlanner/ProducingProcessor',
                 producing_processor_target_name: str = "change_log.txt", 
                 config: ProcessingConfig = None,
                 sheet_mapping: ExcelSheetMapping = None):
        
        """Initialize PendingProcessor"""
        self.logger = logger.bind(class_="PendingProcessor")

        # Set up output configuration
        self.filename_prefix = "pending_processor"
        self.default_dir = Path(default_dir)
        self.output_dir = self.default_dir / "PendingProcessor"
        
        # Configuration
        self.config = config or ProcessingConfig()
        self.sheet_mapping = sheet_mapping or ExcelSheetMapping()
        self.producing_processor_folder_path = producing_processor_folder_path
        self.producing_processor_target_name = producing_processor_target_name

        self.databaseSchemas_path = databaseSchemas_path
        self.sharedDatabaseSchemas_path = sharedDatabaseSchemas_path
        
        # Load path annotations and base data
        self.path_annotation = load_annotation_path(source_path, annotation_name)
        self._load_base_dataframes()
        self._setup_schemas()
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)
        
        # Initialize data containers
        self._initialize_data_containers()

    def _initialize_data_containers(self) -> None:
        """Initialize all data containers to None"""
        self.producing_status_data = None
        self.pending_status_data = None
        self.mold_machine_priority_matrix = None
        self.mold_estimated_capacity_df = None
        self.invalid_molds = None
        self.invalid_molds_dict = {}
        self.mold_lead_times = None
        self.not_matched_pending = None

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

    def _load_base_dataframes(self) -> None:
        """Load base DataFrames required for processing"""
        dataframes_to_load = [
            ('machineInfo', 'machineInfo_df'),
            ('moldInfo', 'moldInfo_df')
        ]
        
        for path_key, attr_name in dataframes_to_load:
            self._load_single_dataframe(path_key, attr_name)

    def _load_single_dataframe(self, path_key: str, attr_name: str) -> None:
        """Load a single DataFrame with error handling"""
        path = self.path_annotation.get(path_key)
        
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"Path to '{path_key}' not found or does not exist: {path}")
        
        try:
            df = pd.read_parquet(path)
            setattr(self, attr_name, df)
            self.logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
        except Exception as e:
            self.logger.error("Failed to load {}: {}", path_key, str(e))
            raise

    def _get_report_path(self) -> str:
        """Get the report path from change log"""
        return read_change_log(
            self.producing_processor_folder_path, 
            self.producing_processor_target_name
        )
    
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
    
    def _load_producing_processor_report(self) -> None:
        """Load all required data from producing processor report"""
        self.logger.info("Loading producing processor report...")
        
        try:
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

    def _run_history_based_optimization(self) -> Tuple[pd.DataFrame, List, List]:
        """Run history-based optimization (first tier)"""
        self.logger.info("Running history-based optimization...")
        
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
            
            return results.assigned_matrix, results.assignments, results.unassigned_molds
            
        except Exception as e:
            self.logger.error("History-based optimization failed: {}", str(e))
            raise

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
                max_load_threshold=self.config.max_load_threshold,
                verbose=self.config.verbose
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

    def _process_history_based_phase(self) -> Tuple[pd.DataFrame, pd.DataFrame, List, List]:
        """Process the history-based optimization phase"""
        # Run history-based optimization
        (assigned_matrix, 
         assigned_molds, 
         unassigned_molds) = self._run_history_based_optimization()
        
        # Process assignments
        assignment_summary = self._process_assignments(
            assigned_matrix, 
            self.mold_lead_times, 
            self.pending_status_data
        )
        
        return assigned_matrix, assignment_summary, assigned_molds, unassigned_molds

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

    def _load_and_validate_data(self) -> None:
        """Phase 1: Load and validate all required data"""
        # Load production data
        self._load_producing_processor_report()
        
        # Validate dataframes
        self._validate_loaded_dataframes()
        
        # Prepare mold lead times
        self._prepare_mold_lead_times()
    
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
    
    def _execute_optimization_phases(self) -> Tuple[pd.DataFrame, List, List, Optional[List], Optional[List]]:
        """Execute both optimization phases and return results"""
        # Phase 1: History-based optimization
        (hist_assigned_matrix, 
         hist_assignment_summary, 
         hist_assigned_molds, 
         hist_unassigned_molds) = self._process_history_based_phase()
        
        # Phase 2: Handle unassigned molds
        comp_assigned_molds = None
        comp_unassigned_molds = None
        
        if self._should_run_compatibility_optimization(hist_unassigned_molds):
            self.logger.info(
                "Running compatibility-based optimization for {} unassigned molds", 
                len(hist_unassigned_molds)
            )
            
            (comp_assignment_summary, 
             comp_assigned_molds, 
             comp_unassigned_molds) = self._process_compatibility_based_phase(
                hist_assigned_matrix, 
                hist_unassigned_molds
            )
            
            # Combine results
            final_summary = self._combine_assignments(
                hist_assignment_summary, 
                comp_assignment_summary
            )
        else:
            # All molds assigned by history-based optimization
            final_summary = hist_assignment_summary.copy()
            final_summary['Note'] = 'histBased'
            self.logger.info("All molds assigned by history-based optimization")
        
        return (final_summary, hist_assigned_molds, hist_unassigned_molds, 
                comp_assigned_molds, comp_unassigned_molds)
    
    def _should_run_compatibility_optimization(self, 
                                               unassigned_molds: List) -> bool:
        """Determine if compatibility-based optimization should run"""
        unassigned_count = len(unassigned_molds)
        
        # Force compatibility optimization for sample data testing
        if self.config.use_sample_data:
            return True
            
        return unassigned_count > 0
    
    def _create_processing_result(self, 
                                  final_summary: pd.DataFrame,
                                  hist_assigned_molds: List,
                                  hist_unassigned_molds: List,
                                  comp_assigned_molds: Optional[List],
                                  comp_unassigned_molds: Optional[List]) -> ProcessingResult:
        """Create the final processing result"""
        return ProcessingResult(
            used_producing_report_name=os.path.basename(self.report_path),
            final_assignment_summary=final_summary,
            invalid_molds_dict=self.invalid_molds_dict,
            hist_based_assigned_molds=hist_assigned_molds,
            hist_based_unassigned_molds=hist_unassigned_molds,
            compatibility_based_assigned_molds=comp_assigned_molds,
            compatibility_based_unassigned_molds=comp_unassigned_molds,
            not_matched_pending=self.not_matched_pending
        )

    def run(self) -> ProcessingResult:
        """
        Run the complete pending processing workflow
        
        Returns:
            ProcessingResult: Complete results from processing
        """
        try:
            # Phase 1: Load and validate data
            self._load_and_validate_data()
            
            # Phase 2: Execute optimization phases
            (final_summary, 
             hist_assigned_molds, 
             hist_unassigned_molds, 
             comp_assigned_molds, 
             comp_unassigned_molds) = self._execute_optimization_phases()
            
            # Phase 3: Create and return results
            return self._create_processing_result(
                final_summary,
                hist_assigned_molds,
                hist_unassigned_molds,
                comp_assigned_molds,
                comp_unassigned_molds
            )
            
        except Exception as e:
            self.logger.error("Processing pipeline failed: {}", str(e))
            raise

    def run_and_save_results(self):
        try:
            # Phase 1: Load and validate data
            self._load_and_validate_data()
            
            # Phase 2: Execute optimization phases
            (final_summary, _, _, _, _) = self._execute_optimization_phases()
            
            self.data = {
                'initialPlan': final_summary,
                'invalid_molds': pd.DataFrame([{"category": k, "mold": v} 
                                               for k, values in self.invalid_molds_dict.items() for v in values])
                         }

            self.logger.info("Start excel file exporting...")
            save_output_with_versioning(
                self.data,
                self.output_dir,
                self.filename_prefix,
        )
            
            return self.data
        
        except Exception as e:
            self.logger.error("Processing pipeline failed: {}", str(e))
            raise