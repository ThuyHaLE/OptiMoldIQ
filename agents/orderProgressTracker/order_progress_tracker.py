from pathlib import Path
from loguru import logger

import os
import pandas as pd
from typing import Dict, Any, NoReturn, List
from configs.shared.config_report_format import ConfigReportMixin
from agents.utils import load_annotation_path, read_change_log
from configs.shared.shared_source_config import SharedSourceConfig
from agents.orderProgressTracker.save_output_formatter import save_tracking_data

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    print_execution_summary,
    save_result)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: SharedSourceConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DataLoading")
        self.config = config
        self.data_container = data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load database schema for productRecords_df
        try:
            pro_status_schema = load_annotation_path(
                Path(self.config.progress_tracker_constant_config_path).parent,
                Path(self.config.progress_tracker_constant_config_path).name)
        except Exception as e:
            raise FileNotFoundError(f"Failed to database schema for productRecords_df: {e}")
        
        # Load database schemas
        try:
            databaseSchemas_data = load_annotation_path(
                Path(self.config.databaseSchemas_path).parent,
                Path(self.config.databaseSchemas_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load databaseSchemas: {e}")
        
        # Load path annotations
        try:
            path_annotation = load_annotation_path(
                Path(self.config.annotation_path).parent,
                Path(self.config.annotation_path).name
            )
        except Exception as e:
            raise FileNotFoundError(f"Failed to load path_annotation: {e}")
        
        logger.info("📊 Loading DataFrames from parquet files...")
        
        # Define dataframes to load
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('purchaseOrders', 'purchaseOrders_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df')
        ]
        
        loaded_dfs = {}
        missing_files = []
        failed_loads = []
        
        for path_key, attr_name in dataframes_to_load:
            path = path_annotation.get(path_key)
            
            if not path:
                missing_files.append(f"{path_key}: path not found in annotation")
                continue
            
            if not os.path.exists(path):
                missing_files.append(f"{path_key}: file not found at {path}")
                continue
            
            try:
                df = pd.read_parquet(path)
                loaded_dfs[attr_name] = df
                logger.debug("{}: {} - {}", path_key, df.shape, list(df.columns))
            except Exception as e:
                failed_loads.append(f"{path_key}: {str(e)}")
        
        # Check if we have critical failures
        if missing_files or failed_loads:
            error_msg = []
            if missing_files:
                error_msg.append("Missing files:\n  - " + "\n  - ".join(missing_files))
            if failed_loads:
                error_msg.append("Failed to load:\n  - " + "\n  - ".join(failed_loads))
            
            raise FileNotFoundError("\n".join(error_msg))
        
        self.data_container.update({
            'pro_status_schema': pro_status_schema,
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })

        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'pro_status_schema': pro_status_schema,
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        }
    
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for data loading.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("DataLoading cannot fallback - missing data files")
        
        raise FileNotFoundError(
            "Cannot proceed without required data files. "
            "Please check paths in configuration."
        )

# ============================================
# DEPENDENCY DATA/REPORT LOADING PHASE
# ============================================
class DependencyDataLoadingPhase(AtomicPhase):
    """Phase for loading validation data from dependency (ValidationOrchestrator)"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False  # Not critical - can continue without validation data
    
    def __init__(self, 
                 config: SharedSourceConfig,
                 dependency_data_container: Dict[str, Any]):
        super().__init__("DependencyDataLoading")
        self.config = config
        self.dependency_data_container = dependency_data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load validation data from dependency"""
        logger.info("📂 Loading log file from dependency ValidationOrchestrator...")
        
        # Process the log file
        excel_file_path = read_change_log(
            Path(self.config.validation_change_log_path).parent,
            Path(self.config.validation_change_log_path).name
        )
        
        if excel_file_path is None:
            logger.info("No change log file found")
            raise FileNotFoundError("No validation change log found")
        
        # Read all sheets from the Excel file
        validation_data = self._collect_validation_data(excel_file_path)

        self.dependency_data_container.update({"validation_data": validation_data})

        logger.info(f"✓ Loaded validation data ({len(validation_data)} sheets)")
        
        return {"validation_data": validation_data}
    
    def _collect_validation_data(self, excel_file_path: str) -> Dict[str, pd.DataFrame]:
        """Read all sheets from the Excel file"""
        try:
            result = {}
            xls = pd.ExcelFile(excel_file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                result[sheet_name] = df
            return result
        except Exception as e:
            logger.error(f"Error processing validation report: {e}")
            raise FileNotFoundError(f"Error processing validation report: {e}")
    
    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty validation results"""
        logger.warning("Using fallback for DependencyDataLoadingPhase - returning empty results")

        self.dependency_data_container.update({"validation_data": {}})

        return {"validation_data": {}}

# ============================================
# PHASE 3: PROGRESS TRACKING
# ============================================
class ProgressTrackingPhase(AtomicPhase):
    """Phase for running the actual progress tracking logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # Can return partial results
    
    def __init__(self, 
                 data_container: Dict[str, Any], 
                 dependency_data_container: Dict[str, Any]):
        super().__init__("ProgressTracker")
        self.loaded_data = data_container
        self.dependency_data = dependency_data_container
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Run progress tracking logic"""
        logger.info("🔄 Running progress tracking...")
        
        # Import ProgressTracker
        from agents.orderProgressTracker.tracker_utils import ProgressTracker
        
        # Extract data from loaded_data
        pro_status_schema = self.loaded_data['pro_status_schema']
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']
        dataframes = self.loaded_data['dataframes']
        validation_data = self.dependency_data.get('validation_data', {})
        
        # Initialize and run tracker
        tracker = ProgressTracker(
            pro_status_schema,
            databaseSchemas_data,
            dataframes['productRecords_df'],
            dataframes['purchaseOrders_df'],
            dataframes['moldSpecificationSummary_df'],
            validation_data
        )
        
        tracker_result = tracker.run_tracking()
        logger.info("✓ Progress tracking completed")
        
        return {
                "payload": tracker_result,
                "savable": True
            }
        
    def _fallback(self) -> NoReturn:
        """
        No valid fallback for progress tracking.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("ProgressTracker cannot fallback - error processing tracker")
        
        raise RuntimeError(
            "Error processing tracker."
            "ProgressTracker cannot fallback."
        )

# ============================================
# MAIN AGENT: ORDER PROGRESS TRACKER
# ============================================

class OrderProgressTracker(ConfigReportMixin):
    """
    Order Progress Tracker Agent
    
    Orchestrates the complete order progress tracking workflow using
    the standardized agent report format.
    """
    
    REQUIRED_FIELDS = {
        'annotation_path': str,
        'databaseSchemas_path': str,
        'validation_change_log_path': str,
        'progress_tracker_dir': str,
        'progress_tracker_change_log_path': str,
        'progress_tracker_constant_config_path': str
    }
    
    def __init__(self, config: SharedSourceConfig):
        """
        Initialize the OrderProgressTracker agent
        
        Args:        
            config: SharedSourceConfig containing processing parameters, including:
                - annotation_path (str): Path to the JSON file containing path annotations.
                - databaseSchemas_path (str): Path to database schema for validation.
                - validation_change_log_path (str): Path to the ValidationOrchestrator change log.
                - progress_tracker_dir (str): Default directory for output and temporary files.
                - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                - progress_tracker_constant_config_path (str): Path to the OrderProgressTracker constant config.
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()
        
        # Initialize logger
        self.logger = logger.bind(class_="OrderProgressTracker")
        
        # Validate required configs
        is_valid, errors = config.validate_requirements(self.REQUIRED_FIELDS)
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for config requirements: PASSED!")
        
        # Store config
        self.config = config

        self.save_routing = {
            "ProgressTracker": {
                "enabled": True,
                "save_fn": save_tracking_data,
                "save_paths": {
                    "output_dir": self.config.progress_tracker_dir,
                    "change_log_path": self.config.progress_tracker_change_log_path
                }
            }
        }

    def run_tracking(self, **kwargs) -> ExecutionResult:
        """
        Main execution method using agent report format
        
        Returns:
            ExecutionResult: Hierarchical execution report
        """

        self.logger.info("Starting OrderProgressTracker ...")

        # ============================================
        # ✨ CREATE SHARED CONTAINER
        # ============================================
        shared_data = {}  # This will be populated by DataLoadingPhase
        dependency_data = {} # This will be populated by DependencyDataLoadingPhase
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Data Loading (always required)
        phases.append(DataLoadingPhase(self.config, shared_data))

        # Phase 2: Dependency data Loading (always required)
        phases.append(DependencyDataLoadingPhase(self.config, dependency_data))

        # Phase 3: Progress Tracking
        phases.append(ProgressTrackingPhase(shared_data, dependency_data))

        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("OrderProgressTracker", phases)
        result = agent.execute()
        
        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ OrderProgressTracker completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result
                
    def run_tracking_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute tracking and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        try:
            # Execute tracking
            result = self.run_tracking(**kwargs)

            # Process save routing and collect metadata
            save_routing, export_metadata = save_result(self.save_routing, result)

            # Log any export failures (optional, doesn't affect execution status)
            for phase_name, phase_export in export_metadata.items():
                if phase_export and phase_export.get('metadata'):
                    phase_metadata = phase_export['metadata']
                    if phase_metadata.get('status') == 'failed':
                        self.logger.warning(
                            "⤷ Phase {}: ⚠️ Excel export failed: {}",
                            phase_name,
                            phase_metadata.get('export_log')
                        )

            # Update result metadata
            result.metadata.update({
                'save_routing': save_routing,
                'export_metadata': export_metadata
            })
            
            self.logger.info("✅ OrderProgressTracker completed")

            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise