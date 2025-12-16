from loguru import logger
from agents.utils import save_output_with_versioning
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import multiprocessing as mp
import psutil
import os
import traceback

from agents.utils import load_annotation_path
from agents.validationOrchestrator.dynamic_cross_data_validator import DynamicCrossDataValidator
from agents.validationOrchestrator.static_cross_data_checker import StaticCrossDataChecker
from agents.validationOrchestrator.po_required_critical_validator import PORequiredCriticalValidator
from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator
from configs.shared.shared_source_config import SharedSourceConfig
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
    
    def __init__(self, config: SharedSourceConfig):
        super().__init__("DataLoading")
        self.config = config
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
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
            ('moldInfo', 'moldInfo_df'),
            ('machineInfo', 'machineInfo_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('itemCompositionSummary', 'itemCompositionSummary_df'),
            ('purchaseOrders', 'purchaseOrders_df'),
            ('itemInfo', 'itemInfo_df'),
            ('resinInfo', 'resinInfo_df'),
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
# VALIDATION PHASES (AtomicPhase implementations)
# ============================================
class StaticValidationPhase(AtomicPhase):
    """Phase for static cross-data validation"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    
    def __init__(
        self, 
        config,
        databaseSchemas_data,
        productRecords_df,
        purchaseOrders_df,
        itemInfo_df,
        resinInfo_df,
        itemCompositionSummary_df
    ):
        super().__init__("StaticCrossDataValidation")
        self.config = config
        self.databaseSchemas_data = databaseSchemas_data
        self.productRecords_df = productRecords_df
        self.purchaseOrders_df = purchaseOrders_df
        self.itemInfo_df = itemInfo_df
        self.resinInfo_df = resinInfo_df
        self.itemCompositionSummary_df = itemCompositionSummary_df
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Execute static validation"""
        logger.info("📋 Running StaticCrossDataChecker...")
        
        checker = StaticCrossDataChecker(
            self.config.validation_df_name,
            self.databaseSchemas_data,
            self.productRecords_df,
            self.purchaseOrders_df,
            self.itemInfo_df,
            self.resinInfo_df,
            self.itemCompositionSummary_df
        )
        result = checker.run_validations()
        
        logger.info("✓ StaticCrossDataChecker completed")
        return result
    
    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty validation results"""
        logger.warning("Using fallback for StaticCrossDataChecker - returning empty results")
        return {
            "result": pd.DataFrame(),
            "log_str": "Fallback: static cross validation skipped due to error\n"
            }
    
class POValidationPhase(AtomicPhase):
    """Phase for purchase order required field validation"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    
    def __init__(self, databaseSchemas_data, productRecords_df, purchaseOrders_df):
        super().__init__("PORequiredFieldValidation")
        self.databaseSchemas_data = databaseSchemas_data
        self.productRecords_df = productRecords_df
        self.purchaseOrders_df = purchaseOrders_df
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Execute PO validation"""
        logger.info("📋 Running PORequiredCriticalValidator...")
        
        validator = PORequiredCriticalValidator(
            self.databaseSchemas_data,
            self.productRecords_df,
            self.purchaseOrders_df
        )
        result = validator.run_validations()
        
        logger.info("✓ PORequiredCriticalValidator completed")
        return result
    
    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty validation results"""
        logger.warning("Using fallback for PORequiredFieldValidation - returning empty results")
        return {
            "result": pd.DataFrame(),
            "log_str": "Fallback: PO validation skipped due to error\n"
            }
    

class DynamicValidationPhase(AtomicPhase):
    """Phase for dynamic cross-data validation"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    
    def __init__(
        self,
        databaseSchemas_data,
        productRecords_df,
        machineInfo_df,
        moldSpecificationSummary_df,
        moldInfo_df,
        itemCompositionSummary_df
    ):
        super().__init__("DynamicCrossDataValidation")
        self.databaseSchemas_data = databaseSchemas_data
        self.productRecords_df = productRecords_df
        self.machineInfo_df = machineInfo_df
        self.moldSpecificationSummary_df = moldSpecificationSummary_df
        self.moldInfo_df = moldInfo_df
        self.itemCompositionSummary_df = itemCompositionSummary_df
    
    def _execute_impl(self) -> Dict[str, Any]:
        """Execute dynamic validation"""
        logger.info("📋 Running DynamicCrossDataValidator...")
        
        validator = DynamicCrossDataValidator(
            self.databaseSchemas_data,
            self.productRecords_df,
            self.machineInfo_df,
            self.moldSpecificationSummary_df,
            self.moldInfo_df,
            self.itemCompositionSummary_df
        )
        result = validator.run_validations()
        
        logger.info("✓ DynamicCrossDataValidator completed")
        return result
    
    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty validation results"""
        logger.warning("Using fallback for DynamicCrossDataValidation - returning empty results")
        return {
            "result": {
                'mismatch_warnings': {},
                'invalid_warnings': {}
                }, 
            "log_str": "Fallback: Dynamic cross validation skipped due to error\n"
            }
    
# ============================================
# MAIN VALIDATION ORCHESTRATOR
# ============================================
class ValidationOrchestrator(ConfigReportMixin):
    """
    Main orchestrator class that coordinates multiple validation processes.
    
    Now implements the agent_report_format pattern with ExecutionResult hierarchy.
    """

    REQUIRED_FIELDS = {
        'shared_source_config': {
            'validation_df_name': List[str],
            'databaseSchemas_path': str,
            'annotation_path': str,
            'validation_dir': str,
        },
        'enable_parallel': bool,
        'max_workers': Optional[int]
    }

    def __init__(
        self,
        shared_source_config: SharedSourceConfig,
        enable_parallel: bool = False,
        max_workers: Optional[int] = None
    ):
        """Initialize the ValidationOrchestrator."""
        
        # Capture initialization arguments for reporting
        self._capture_init_args()
        
        # Initialize logger
        self.logger = logger.bind(class_="ValidationOrchestrator")
        
        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['shared_source_config']
        )
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")
        
        # Store configuration
        self.config = shared_source_config
        
        # NOTE: Data loading is now handled by DataLoadingPhase
        # These will be populated during execution
        self.databaseSchemas_data = None
        self.path_annotation = None
        self.loaded_dataframes = {}
        
        # Set up output configuration
        self.filename_prefix = "validation_orchestrator"
        self.output_dir = Path(self.config.validation_dir)
        
        # Store parallel settings
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        
        # Setup parallel processing configuration
        self._setup_parallel_config()

    def _setup_parallel_config(self) -> None:
        """Setup parallel processing configuration based on system resources."""
        try:
            cpu_count = mp.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            self.logger.info("System specs: {} CPU cores, {:.1f}GB RAM", cpu_count, memory_gb)
            
            if self.max_workers is None:
                if cpu_count == 1:
                    self.max_workers = 1
                    self.enable_parallel = False
                elif cpu_count == 2:
                    if memory_gb >= 8:
                        self.max_workers = 2
                        self.logger.info("Colab-style environment detected. Using both cores.")
                    else:
                        self.max_workers = 1
                        self.enable_parallel = False
                else:
                    if memory_gb < 4:
                        self.max_workers = max(1, min(2, cpu_count // 2))
                    elif memory_gb < 8:
                        self.max_workers = max(2, min(3, cpu_count // 2))
                    else:
                        self.max_workers = max(2, int(cpu_count * 0.75))
            
            # Limit to number of validators (3 validation phases)
            num_validators = 3
            if self.max_workers > num_validators:
                self.max_workers = num_validators
            
            if not self.enable_parallel or self.max_workers <= 1:
                self.enable_parallel = False
                self.max_workers = 1
                self.logger.info("⏭️  Parallel processing disabled. Workers: {}", self.max_workers)
            else:
                self.logger.info("⚡ Parallel processing enabled. Workers: {}", self.max_workers)
                
        except Exception as e:
            self.logger.warning("Failed to detect system specs: {}. Using sequential.", e)
            self.enable_parallel = False
            self.max_workers = 1

    def _create_validation_phases(self) -> List[AtomicPhase]:
        """Create all validation phases using loaded data."""
        
        # Get dataframes from loaded_dataframes
        dfs = self.loaded_dataframes
        
        return [
            StaticValidationPhase(
                self.config,
                self.databaseSchemas_data,
                dfs.get('productRecords_df', pd.DataFrame()),
                dfs.get('purchaseOrders_df', pd.DataFrame()),
                dfs.get('itemInfo_df', pd.DataFrame()),
                dfs.get('resinInfo_df', pd.DataFrame()),
                dfs.get('itemCompositionSummary_df', pd.DataFrame())
            ),
            POValidationPhase(
                self.databaseSchemas_data,
                dfs.get('productRecords_df', pd.DataFrame()),
                dfs.get('purchaseOrders_df', pd.DataFrame())
            ),
            DynamicValidationPhase(
                self.databaseSchemas_data,
                dfs.get('productRecords_df', pd.DataFrame()),
                dfs.get('machineInfo_df', pd.DataFrame()),
                dfs.get('moldSpecificationSummary_df', pd.DataFrame()),
                dfs.get('moldInfo_df', pd.DataFrame()),
                dfs.get('itemCompositionSummary_df', pd.DataFrame())
            )
        ]

    def _execute_phases_sequential(self, phases: List[AtomicPhase]) -> ExecutionResult:
        """Execute phases sequentially."""
        self.logger.info("🔄 Running validations sequentially...")
        
        agent = CompositeAgent("ValidationOrchestrator", phases)
        return agent.execute()

    def _execute_phases_parallel(self, phases: List[AtomicPhase]) -> ExecutionResult:
        """Execute phases in parallel using ThreadPoolExecutor."""
        self.logger.info("⚡ Starting parallel validation with {} workers", self.max_workers)
        start_time = time.time()
        
        sub_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_phase = {
                executor.submit(phase.execute): phase
                for phase in phases
            }
            
            for future in as_completed(future_to_phase):
                phase = future_to_phase[future]
                try:
                    result = future.result()
                    sub_results.append(result)
                    self.logger.info("✅ {} completed ({:.1f}s)",
                                   result.name, result.duration)
                except Exception as e:
                    error_msg = f"Unexpected error in {phase.name}: {str(e)}"
                    self.logger.error("❌ {}", error_msg)
                    
                    # Create failed result
                    sub_results.append(ExecutionResult(
                        name=phase.name,
                        type="phase",
                        status="failed",
                        duration=0.0,
                        severity=PhaseSeverity.CRITICAL.value,
                        error=error_msg,
                        traceback=traceback.format_exc()
                    ))
        
        duration = time.time() - start_time
        
        # Determine overall status
        if any(r.has_critical_errors() for r in sub_results):
            status = ExecutionStatus.FAILED.value
            severity = PhaseSeverity.CRITICAL.value
        elif not all(r.status == "success" for r in sub_results):
            status = ExecutionStatus.PARTIAL.value
            severity = PhaseSeverity.ERROR.value
        else:
            status = ExecutionStatus.SUCCESS.value
            severity = PhaseSeverity.INFO.value
        
        return ExecutionResult(
            name="ValidationOrchestrator",
            type="agent",
            status=status,
            duration=duration,
            severity=severity,
            sub_results=sub_results,
            total_sub_executions=len(phases),
            metadata={
                "execution_mode": "parallel",
                "workers": self.max_workers
            }
        )

    def run_validations(self, **kwargs) -> ExecutionResult:
        """
        Execute all validation processes and return ExecutionResult.
        
        Returns:
            ExecutionResult: Hierarchical execution result
        """
        execution_mode = "PARALLEL" if self.enable_parallel else "SEQUENTIAL"
        self.logger.info("🚀 Starting ValidationOrchestrator in {} mode...", execution_mode)
        
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
                name="ValidationOrchestrator",
                type="agent",
                status="failed",
                duration=data_result.duration,
                severity=data_result.severity,
                sub_results=[data_result],
                total_sub_executions=1,
                error="Data loading failed"
            )
        
        # Extract loaded data
        loaded_data = data_result.data.get('result', {})
        self.databaseSchemas_data = loaded_data.get('databaseSchemas_data', {})
        self.path_annotation = loaded_data.get('path_annotation', {})
        self.loaded_dataframes = loaded_data.get('dataframes', {})
        
        self.logger.info("✓ Data loaded successfully")
        self.logger.info("🔍 Step 2: Running validations...")
        
        # Create validation phases
        validation_phases = self._create_validation_phases()
        
        # Execute validations based on mode
        if self.enable_parallel:
            validation_result = self._execute_phases_parallel(validation_phases)
        else:
            validation_result = self._execute_phases_sequential(validation_phases)
        
        # Combine data loading + validations into final result
        total_duration = data_result.duration + validation_result.duration
        
        final_result = ExecutionResult(
            name="ValidationOrchestrator",
            type="agent",
            status=validation_result.status,
            duration=total_duration,
            severity=validation_result.severity,
            sub_results=[data_result] + validation_result.sub_results,
            total_sub_executions=1 + len(validation_phases),
            warnings=validation_result.warnings,
            metadata={
                "execution_mode": execution_mode,
                "workers": self.max_workers if self.enable_parallel else 1
            }
        )
        
        # Log completion
        self.logger.info("✅ ValidationOrchestrator completed in {:.2f}s!", final_result.duration)
        
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

    def _extract_validation_data(self, result: ExecutionResult) -> Dict[str, Any]:
        """Extract validation data from ExecutionResult hierarchy."""
        
        # Skip first sub_result (DataLoading phase)
        validation_results = [r for r in result.sub_results if r.name != "DataLoading"]
        
        # Find results by phase name
        static_result = next((r for r in validation_results 
                            if r.name == "StaticCrossDataValidation"), None)
        po_result = next((r for r in validation_results 
                         if r.name == "PORequiredFieldValidation"), None)
        dynamic_result = next((r for r in validation_results 
                             if r.name == "DynamicCrossDataValidation"), None)
        
        # Extract data from successful results
        static_data = static_result.data.get(
            'result', {}).get(
                'result', {}) if static_result and static_result.status == "success" else {}
        
        po_data = po_result.data.get(
            'result', {}).get(
                'result', pd.DataFrame()) if po_result and po_result.status == "success" else pd.DataFrame()
        
        dynamic_data = dynamic_result.data.get(
            'result', {}).get(
                'result', {}) if dynamic_result and dynamic_result.status == "success" else {}
        
        # Combine results
        return self._combine_validation_results(static_data, po_data, dynamic_data)

    def _combine_validation_results(self,
                                    static_data: Dict[str, Any],
                                    po_data: Any,
                                    dynamic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from all validation processes."""
        
        static_mismatch_warnings_purchase = static_data.get('purchaseOrders', pd.DataFrame())
        static_mismatch_warnings_product = static_data.get('productRecords', pd.DataFrame())
        po_required_mismatch_warnings = po_data if isinstance(po_data, pd.DataFrame) else pd.DataFrame()
        dynamic_invalid_warnings = dynamic_data.get('invalid_warnings', pd.DataFrame())
        dynamic_mismatch_warnings = dynamic_data.get('mismatch_warnings', pd.DataFrame())
        
        final_df = pd.concat([
            dynamic_mismatch_warnings,
            static_mismatch_warnings_purchase,
            static_mismatch_warnings_product,
            po_required_mismatch_warnings
        ], ignore_index=True)
        
        return {
            'static_mismatch': {
                'purchaseOrders': static_mismatch_warnings_purchase,
                'productRecords': static_mismatch_warnings_product
            },
            'po_required_mismatch': po_required_mismatch_warnings,
            'dynamic_mismatch': {
                'invalid_items': dynamic_invalid_warnings,
                'info_mismatches': dynamic_mismatch_warnings
            },
            'combined_all': {
                'po_mismatch_warnings': final_df,
                'item_invalid_warnings': dynamic_invalid_warnings
            }
        }

    def run_validations_and_save_results(self, **kwargs) -> ExecutionResult:
        """
        Execute validation processes and save results to Excel files.
        
        Returns:
            ExecutionResult: Hierarchical execution result with saved data
        """
        try:
            # Execute validations
            result = self.run_validations(**kwargs)
            
            # Check if validations succeeded
            if result.has_critical_errors():
                self.logger.error("❌ Validations failed with critical errors, skipping save")
                return result
            
            # Extract validation data
            validation_data = self._extract_validation_data(result)

            if (
                validation_data['combined_all']['po_mismatch_warnings'].empty
                and validation_data['combined_all']['item_invalid_warnings'].empty
                ):
                self.logger.warning("No mismatches were found during validation, skipping save")
                return result
            
            # Generate validation summary
            reporter = DictBasedReportGenerator(use_colors=False)
            validation_summary = "\n".join(reporter.export_report(validation_data))
            
            # Export results to Excel
            self.logger.info("📤 Exporting results to Excel...")
            export_log = save_output_with_versioning(
                data=validation_data['combined_all'],
                output_dir=self.output_dir,
                filename_prefix=self.filename_prefix,
                report_text=validation_summary
            )
            self.logger.info("✅ Results exported successfully!")
            
            # Add export info to result metadata
            result.metadata['export_log'] = export_log
            result.metadata['validation_summary'] = validation_summary
            
            # Save change log
            self._save_change_log(result, validation_summary, export_log)
            
            return result
            
        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise

    def _save_change_log(
        self, 
        result: ExecutionResult,
        validation_summary: str,
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
                "VALIDATION SUMMARY:",
                validation_summary,
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