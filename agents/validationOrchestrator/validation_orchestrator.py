from loguru import logger
from agents.utils import save_output_with_versioning, ConfigReportMixin
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import time
import multiprocessing as mp
import psutil

from agents.validationOrchestrator.dynamic_cross_data_validator import DynamicCrossDataValidator
from agents.validationOrchestrator.static_cross_data_checker import StaticCrossDataChecker
from agents.validationOrchestrator.po_required_critical_validator import PORequiredCriticalValidator

from agents.autoPlanner.reportFormatters.dict_based_report_generator import DictBasedReportGenerator

from agents.utils import ConfigReportMixin
from configs.shared.shared_source_config import SharedSourceConfig


class ValidationOrchestrator(ConfigReportMixin):
    """
    Main orchestrator class that coordinates multiple validation processes for manufacturing data.
    
    This class manages the validation of product records, purchase orders, and related 
    manufacturing data by running three types of validations:
    1. Static cross-data validation
    2. Purchase order required field validation  
    3. Dynamic cross-data validation
    
    Supports both sequential and parallel execution with auto-detection of optimal configuration.
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
        """
        Initialize the ValidationOrchestrator.
        
        Args:
            shared_source_config: SharedSourceConfig containing processing parameters
            enable_parallel: Whether to enable parallel processing (default: True, auto-detected)
            max_workers: Maximum number of workers for parallel processing (None = auto-detect)
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="ValidationOrchestrator")

        # Validate required configs
        is_valid, errors = shared_source_config.validate_requirements(self.REQUIRED_FIELDS['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")

        # Store configuration and parallel settings
        self.config = shared_source_config
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers

        # Set up output configuration for saving validation results
        self.filename_prefix = "validation_orchestrator"
        self.output_dir = Path(self.config.validation_dir)
        
        # Initialize report collection for tracking all validation reports
        self.report_collection = {}
        
        # Setup parallel processing configuration
        self._setup_parallel_config()

    def _setup_parallel_config(self) -> None:
        """
        Setup parallel processing configuration based on system resources.
        
        Auto-detects optimal worker count and determines if parallel processing
        is beneficial for the current system.
        """
        try:
            # Get system information
            cpu_count = mp.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)

            self.logger.info("System specs: {} CPU cores, {:.1f}GB RAM", cpu_count, memory_gb)

            # Determine optimal worker count if not specified
            if self.max_workers is None:
                if cpu_count == 1:
                    # Single core - no parallel benefit
                    self.max_workers = 1
                    self.enable_parallel = False
                elif cpu_count == 2:
                    # Dual core (like Colab) - can still benefit from 2 workers if enough RAM
                    if memory_gb >= 8:
                        self.max_workers = 2  # Use both cores
                        self.logger.info("Colab-style environment detected. Using both cores.")
                    else:
                        self.max_workers = 1
                        self.enable_parallel = False
                        self.logger.warning("Limited RAM with dual core. Using sequential processing.")
                else:
                    # Multi-core systems
                    if memory_gb < 4:
                        self.max_workers = max(1, min(2, cpu_count // 2))
                        self.logger.warning("Limited RAM detected. Limiting workers to {}", self.max_workers)
                    elif memory_gb < 8:
                        self.max_workers = max(2, min(3, cpu_count // 2))
                    else:
                        # Use 75% of cores for validation tasks
                        self.max_workers = max(2, int(cpu_count * 0.75))

            # We have 3 validators - no need for more workers than that
            num_validators = 3
            if self.max_workers > num_validators:
                self.max_workers = num_validators
                self.logger.info("Limiting workers to {} (number of validators)", num_validators)

            # Final check - disable if explicitly disabled or only 1 worker
            if not self.enable_parallel or self.max_workers <= 1:
                self.enable_parallel = False
                self.max_workers = 1
                self.logger.info("⏭️  Parallel processing disabled. Workers: {}", self.max_workers)
            else:
                self.logger.info("⚡ Parallel processing enabled. Workers: {} (optimized for validation)", 
                               self.max_workers)

        except Exception as e:
            self.logger.warning("Failed to detect system specs: {}. Using sequential processing.", e)
            self.enable_parallel = False
            self.max_workers = 1

    def run_validations(self, **kwargs) -> tuple[Dict[str, Any], str]:
        """
        Execute all validation processes and return consolidated results.
        
        This method runs three types of validations either sequentially or in parallel
        based on the enable_parallel setting and system resources.
        
        Args:
            **kwargs: Additional parameters passed to individual validators
            
        Returns:
            tuple: (final_report, validation_log_str)
                - final_report: Dict with standardized structure containing Agent ID, Timestamp, and Content
                - validation_log_str: String containing full validation log
        """

        agent_id = "ValidationOrchestrator"
        execution_mode = "PARALLEL" if self.enable_parallel else "SEQUENTIAL"
        self.logger.info("🚀 Starting {} in {} mode...", agent_id, execution_mode)

        # Generate config header using mixin
        start_time = datetime.now()
        timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # Initialize validation log entries for entire processing run
        validation_log_entries = [config_header]
        validation_log_entries.append(f"--Processing Summary--\n")
        validation_log_entries.append(f"⤷ {self.__class__.__name__} results (Mode: {execution_mode}):\n")

        try:
            # Run validations based on mode
            if self.enable_parallel:
                validation_results_dict = self._execute_validations_parallel()
            else:
                validation_results_dict = self._execute_validations_sequential()

            # Append all logs
            for result in validation_results_dict.values():
                validation_log_entries.append(result['log'])

            # Combine all validation results
            validation_results = self._combine_validation_results(
                validation_results_dict['static']['data'],
                validation_results_dict['po']['data'],
                validation_results_dict['dynamic']['data']
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            validation_log_entries.append(f"\n⏱️  Total execution time: {execution_time:.2f}s\n")

            # Combine log entries into a single string
            validation_log_str = "\n".join(validation_log_entries)
            self.logger.info("✅ {} completed in {:.2f}s!", agent_id, execution_time)

            # Create standardized final report
            final_report = {
                'Agent ID': agent_id,
                'Timestamp': self._get_timestamp(),
                'Execution Mode': execution_mode,
                'Execution Time': f"{execution_time:.2f}s",
                'Workers Used': self.max_workers,
                'Content': validation_results
            }
            
            # Store in report collection
            self.report_collection[agent_id] = {'final_report': final_report}

            return final_report, validation_log_str

        except Exception as e:
            self.logger.error("❌ {} failed: {}", agent_id, str(e))
            raise

    def _execute_validations_sequential(self) -> Dict[str, Dict[str, Any]]:
        """
        Execute all validations sequentially (fallback method).
        
        Returns:
            Dict containing results from all three validators
        """
        self.logger.info("🔄 Running validations sequentially...")
        start_time = time.time()
        
        results = {
            'static': self._run_static_validation(),
            'po': self._run_po_validation(),
            'dynamic': self._run_dynamic_validation()
        }
        
        total_time = time.time() - start_time
        self.logger.info("Sequential validation completed in {:.1f}s", total_time)
        
        return results

    def _execute_validations_parallel(self) -> Dict[str, Dict[str, Any]]:
        """
        Execute all validations in parallel using ThreadPoolExecutor.
        
        Note: Uses ThreadPoolExecutor instead of ProcessPoolExecutor because:
        - Validators likely do I/O operations (reading files)
        - Thread overhead is lower for I/O-bound tasks
        - Easier to share config objects across threads
        
        For CPU-intensive validations, consider ProcessPoolExecutor.
        
        Returns:
            Dict containing results from all three validators
        """
        self.logger.info("⚡ Starting parallel validation with {} workers", self.max_workers)
        start_time = time.time()
        
        results = {}
        
        # Define validation tasks
        tasks = {
            'static': self._run_static_validation,
            'po': self._run_po_validation,
            'dynamic': self._run_dynamic_validation
        }
        
        # Execute in parallel with ThreadPoolExecutor (better for I/O-bound tasks)
        # Use ProcessPoolExecutor if validators are CPU-intensive
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_name = {
                executor.submit(func): name 
                for name, func in tasks.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    results[name] = result
                    self.logger.info("✅ {} validation completed ({:.1f}s)", 
                                   name.upper(), result['time'])
                except Exception as e:
                    error_msg = f"Validation failed for {name.upper()}: {str(e)}"
                    self.logger.error("❌ {}", error_msg)
                    # Re-raise to fail fast
                    raise RuntimeError(error_msg) from e
        
        total_time = time.time() - start_time
        self.logger.info("Parallel validation completed in {:.1f}s. Success: {}/3", 
                        total_time, len(results))
        
        return results

    def run_validations_and_save_results(self, **kwargs) -> tuple[Dict[str, Any], str]:
        """
        Execute validation processes and save results to Excel files.
        
        This method runs all validations and exports the combined results to Excel files
        with automatic versioning to prevent overwrites.
        
        Args:
            **kwargs: Additional parameters passed to validation methods
            
        Returns:
            tuple: (final_report, validation_log_str)
            
        Raises:
            Exception: If validation execution or file saving fails
        """

        try:
            # Execute validations
            final_report, validation_log_str = self.run_validations(**kwargs)
            
            # Extract validation results for exporting
            validation_results = final_report['Content']

            # Generate validation summary
            reporter = DictBasedReportGenerator(use_colors=False)
            validation_summary = "\n".join(reporter.export_report(validation_results))

            # Export results to Excel files with versioning
            self.logger.info("📤 Exporting results to Excel...")
            output_exporting_log = save_output_with_versioning(
                data=validation_results['combined_all'],
                output_dir=self.output_dir,
                filename_prefix=self.filename_prefix,
                report_text=validation_summary
            )
            self.logger.info("✅ Results exported successfully!")
            
            # Append export log to validation log
            validation_log_str = "\n".join([validation_log_str, output_exporting_log])

            # Save change log
            self._save_change_log(validation_log_str)
            
            return final_report, validation_log_str

        except Exception as e:
            self.logger.error("❌ Failed to save results: {}", str(e))
            raise

    def _run_static_validation(self) -> Dict[str, Any]:
        """
        Execute static cross-data validation.
        
        Returns:
            Dict containing 'data', 'log', and 'time' keys
        """
        start = time.time()
        self.logger.info("📋 Running StaticCrossDataChecker...")
        
        checker = StaticCrossDataChecker(self.config)
        validation_data, validation_log = checker.run_validations()
        
        elapsed = time.time() - start
        self.logger.info("✓ StaticCrossDataChecker completed in {:.2f}s", elapsed)
        
        return {
            'data': validation_data,
            'log': validation_log,
            'time': elapsed
        }

    def _run_po_validation(self) -> Dict[str, Any]:
        """
        Execute purchase order required field validation.
        
        Returns:
            Dict containing 'data', 'log', and 'time' keys
        """
        start = time.time()
        self.logger.info("📋 Running PORequiredCriticalValidator...")
        
        validator = PORequiredCriticalValidator(self.config)
        validation_data, validation_log = validator.run_validations()
        
        elapsed = time.time() - start
        self.logger.info("✓ PORequiredCriticalValidator completed in {:.2f}s", elapsed)
        
        return {
            'data': validation_data,
            'log': validation_log,
            'time': elapsed
        }

    def _run_dynamic_validation(self) -> Dict[str, Any]:
        """
        Execute dynamic cross-data validation.
        
        Returns:
            Dict containing 'data', 'log', and 'time' keys
        """
        start = time.time()
        self.logger.info("📋 Running DynamicCrossDataValidator...")
        
        validator = DynamicCrossDataValidator(self.config)
        validation_data, validation_log = validator.run_validations()
        
        elapsed = time.time() - start
        self.logger.info("✓ DynamicCrossDataValidator completed in {:.2f}s", elapsed)
        
        return {
            'data': validation_data,
            'log': validation_log,
            'time': elapsed
        }

    def _combine_validation_results(
        self,
        static_data: Dict[str, Any],
        po_data: Any,
        dynamic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine results from all validation processes.
        
        Args:
            static_data: Results from static validation
            po_data: Results from PO validation
            dynamic_data: Results from dynamic validation
            
        Returns:
            Dict containing combined validation results organized by type
        """
        # Extract static validation warnings by dataset
        static_mismatch_warnings_purchase = static_data['purchaseOrders']
        static_mismatch_warnings_product = static_data['productRecords']

        # Copy PO validation results
        po_required_mismatch_warnings = po_data.copy()

        # Extract dynamic validation results
        dynamic_invalid_warnings = dynamic_data['invalid_warnings']
        dynamic_mismatch_warnings = dynamic_data['mismatch_warnings']

        # Combine all mismatch warnings into a single DataFrame
        final_df = pd.concat([
            dynamic_mismatch_warnings,
            static_mismatch_warnings_purchase,
            static_mismatch_warnings_product,
            po_required_mismatch_warnings
        ], ignore_index=True)

        return {
            # Static validation results (reference data mismatches)
            'static_mismatch': {
                'purchaseOrders': static_mismatch_warnings_purchase,
                'productRecords': static_mismatch_warnings_product
            },
            # Purchase order required field validation results
            'po_required_mismatch': po_required_mismatch_warnings,
            # Dynamic validation results (cross-dataset inconsistencies)
            'dynamic_mismatch': {
                'invalid_items': dynamic_invalid_warnings,
                'info_mismatches': dynamic_mismatch_warnings
            },
            # Combined results for reporting
            'combined_all': {
                'item_invalid_warnings': dynamic_invalid_warnings,
                'po_mismatch_warnings': final_df
            }
        }

    def _save_change_log(self, log_content: str) -> None:
        """
        Save change log to file.
        
        Args:
            log_content: Log content to save
        """
        try:
            log_path = self.output_dir / "change_log.txt"
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_content)
            self.logger.info("✓ Updated and saved change log: {}", log_path)
        except Exception as e:
            self.logger.error("✗ Failed to save change log {}: {}", log_path, e)

    def _get_timestamp(self) -> str:
        """
        Get current timestamp in standardized format.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")