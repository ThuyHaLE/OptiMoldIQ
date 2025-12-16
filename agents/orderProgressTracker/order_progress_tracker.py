from pathlib import Path
from loguru import logger

from agents.utils import load_annotation_path, read_change_log, save_output_with_versioning
from configs.shared.shared_source_config import SharedSourceConfig
import pandas as pd
from datetime import datetime
import os
from typing import Dict, Any
from configs.shared.config_report_format import ConfigReportMixin

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    PhaseSeverity,
    ExecutionStatus,
    print_execution_tree,
    analyze_execution)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!
    
    DEFAUTL_SCHEMA_PATH = "agents/orderProgressTracker/pro_status_schema.json"

    def __init__(self, config: SharedSourceConfig):
        super().__init__("DataLoading")
        self.config = config
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load database schema for productRecords_df
        try:
            pro_status_schema = load_annotation_path(
                Path(self.DEFAUTL_SCHEMA_PATH).parent,
                Path(self.DEFAUTL_SCHEMA_PATH).name)
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
        
        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'pro_status_schema': pro_status_schema,
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        }
    
    def _fallback(self) -> Dict[str, Any]:
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
    
    def __init__(self, config: SharedSourceConfig):
        super().__init__("DependencyDataLoading")
        self.config = config
    
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
                 loaded_data: Dict[str, Any], 
                 dependency_data: Dict[str, Any]):
        super().__init__("ProgressTracking")
        self.loaded_data = loaded_data
        self.dependency_data = dependency_data
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Run progress tracking logic"""
        logger.info("🔄 Running progress tracking...")
        
        # Import ProgressTracker (your existing class)
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
        
        return tracker_result
    
    def _fallback(self) -> Dict[str, Any]:
        """
        No valid fallback for progress tracking.
        Raise to ensure CRITICAL severity is applied.
        """
        logger.error("ProgressTracking cannot fallback - error processing tracker")
        
        raise RuntimeError(
            "Error processing tracker."
            "ProgressTracking cannot fallback."
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
        'progress_tracker_dir': str
    }
    
    def __init__(self, config: SharedSourceConfig):
        """Initialize the OrderProgressTracker agent"""
        
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

        # NOTE: Data loading is now handled by DataLoadingPhase and DependencyDataLoadingPhase
        # These will be populated during execution
        self.loaded_data = {}
        self.dependency_data = {}
        
        # Set up output configuration
        self.filename_prefix = "auto_status"
        self.output_dir = Path(self.config.progress_tracker_dir)
    
    def run_tracking(self, **kwargs) -> ExecutionResult:
        """
        Main execution method using agent report format
        
        Returns:
            ExecutionResult: Hierarchical execution report
        """

        self.logger.info("Starting OrderProgressTracker ...")

        # Create data loading phase
        data_phase = DataLoadingPhase(self.config)
        
        # Execute data loading first
        self.logger.info("📂 Step 1: Loading data...")
        data_result = data_phase.execute()
        
        # Check if data loading succeeded
        if data_result.status != "success":
            self.logger.error("❌ Data loading failed, cannot proceed with validations")
            
            # Return early with failed result
            return ExecutionResult(
                name="OrderProgressTracker",
                type="agent",
                status="failed",
                duration=data_result.duration,
                severity=data_result.severity,
                sub_results=[data_result],
                total_sub_executions=1,
                error="Data loading failed"
            )

        self.loaded_data = data_result.data.get('result', {})
        self.logger.info("✓ Data loaded successfully")

        self.logger.info("📂 Step 2: Loading dependency data...")
        dependency_data_phase = DependencyDataLoadingPhase(self.config)
        dependency_data_result = dependency_data_phase.execute()
        self.dependency_data = dependency_data_result.data.get('result', {})

        self.logger.info("✓ Dependency data loaded successfully")

        self.logger.info("🔍 Step 3: Running tracking...")
        tracking_phase = ProgressTrackingPhase(self.loaded_data, self.dependency_data)
        tracking_result = tracking_phase.execute()

        # Check if data loading succeeded
        if tracking_result.status != "success":
            self.logger.error("❌ Progress tracking failed")
            
            # Return early with failed result
            return ExecutionResult(
                name="OrderProgressTracker",
                type="agent",
                status="failed",
                duration=tracking_result.duration,
                severity=tracking_result.severity,
                sub_results=[data_result, dependency_data_result, tracking_result],
                total_sub_executions=3,
                error="Error processing OrderProgressTracker"
            )

        # Combine data loading + validations into final result
        total_duration = data_result.duration + dependency_data_result.duration + tracking_result.duration
        
        final_result = ExecutionResult(
            name="OrderProgressTracker",
            type="agent",
            status=tracking_result.status,
            duration=total_duration,
            severity=tracking_result.severity,
            sub_results=[data_result, dependency_data_result, tracking_result],
            total_sub_executions= 3,
            warnings=tracking_result.warnings
        )
        
        # Log completion
        self.logger.info("✅ OrderProgressTracker completed in {:.2f}s!", final_result.duration)
        
        # Print execution tree for visibility
        print("\n" + "="*60)
        print("VALIDATION EXECUTION TREE")
        print("="*60)
        print_execution_tree(final_result)
        print("="*60 + "\n")
        
        # Print analysis
        analysis = analyze_execution(final_result)
        print("EXECUTION ANALYSIS:")
        print(f"  Status: {analysis['status']}")
        print(f"  Duration: {analysis['duration']:.2f}s")
        print(f"  Complete: {analysis['complete']}")
        print(f"  All Successful: {analysis['all_successful']}")
        print(f"  Statistics: {analysis['statistics']}")
        if analysis['failed_paths']:
            print(f"  Failed Paths: {analysis['failed_paths']}")
        print("="*60 + "\n")
        
        return final_result
    
    def _extract_tracking_data(self, result: ExecutionResult) -> Dict[str, Any]:
        """Extract tracking data from ExecutionResult hierarchy."""
        
        # Skip first sub_results (DataLoading and DependencyDataLoading phase) 
        tracking_result = [r for r in result.sub_results if r.name not in ["DataLoading", "DependencyDataLoading"]]
        tracking_data = tracking_result[0].data.get(
            'result', {}) if tracking_result and tracking_result[0].status == "success" else {}

        if not isinstance(tracking_data, dict):
            return {}

        if not {"result", "tracking_summary"}.issubset(tracking_data):
            return {}
    
        return tracking_data
                
    def run_tracking_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute tracking and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """

        try:
            # Execute tracking
            result = self.run_tracking(**kwargs)
            
            # Check if tracking succeeded
            if result.has_critical_errors():
                self.logger.error("❌ Validations failed with critical errors, skipping save")
                return result

            # Extract tracking data
            tracker_result = self._extract_tracking_data(result)
            if not tracker_result:
                self.logger.error("❌ Validations failed: empty or invalid tracking result, skipping save")
                return result
            
            # Export Excel file with versioning
            logger.info("Start excel file exporting...")
            export_log = save_output_with_versioning(
                data = tracker_result['result'],
                output_dir = self.output_dir,
                filename_prefix = self.filename_prefix,
                report_text = tracker_result['tracking_summary']
            )
            self.logger.info("Results exported successfully!")

            # Add export info to result metadata
            result.metadata['export_log'] = export_log
            result.metadata['tracking_summary'] = tracker_result['tracking_summary']
            
            # Save change log
            self._save_change_log(result, tracker_result['tracking_summary'], export_log)
            
            return result

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise

    def _save_change_log(
        self, 
        result: ExecutionResult,
        tracking_summary: str,
        export_log: str
    ) -> None:
        """Save change log to file."""
        try:
            log_path = self.output_dir / "change_log.txt"
            
            # Generate config header using mixin
            start_time = datetime.now()
            timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str, required_only=True)
            
            # Initialize validation log entries for entire processing run
            log_content = ["="*60]
            log_content.append(config_header)
            log_content.append(f"--Processing Summary--\n")
            log_content.append(f"⤷ {self.__class__.__name__} results:\n")
            log_content.append("EXECUTION TREE:")
            
            # Add execution tree (capture print output)
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            print_execution_tree(result)
            sys.stdout = old_stdout
            log_content.append(buffer.getvalue())
            
            log_content.extend([
                "",
                "ANALYSIS:",
                str(analyze_execution(result)),
                "",
                "TRACKING SUMMARY:",
                tracking_summary,
                "",
                "EXPORT LOG:",
                export_log,
                "",
                "="*60,
                ""
            ])
            
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write("\n".join(log_content))
            
            self.logger.info("✓ Updated and saved change log: {}", log_path)

        except Exception as e:
            self.logger.error("✗ Failed to save change log: {}", e)