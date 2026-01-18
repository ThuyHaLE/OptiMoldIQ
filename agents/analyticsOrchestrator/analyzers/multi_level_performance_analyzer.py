from loguru import logger
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, NoReturn
from configs.shared.config_report_format import ConfigReportMixin
from agents.utils import load_annotation_path
from agents.analyticsOrchestrator.analyzers.configs.performance_analyzer_config import LevelConfig, PerformanceAnalyzerConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.analyticsOrchestrator.analyzers.configs.save_output_formatter import save_analyzer_reports

# Import agent report format components
from configs.shared.agent_report_format import (
    Executable,
    ExecutionResult,
    AtomicPhase,
    CompositeAgent,
    save_result,
    print_execution_summary,
    format_execution_tree,
    update_change_log,
    format_export_logs)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: PerformanceAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DataLoading")
        self.config = config.shared_source_config
        self.data_container = data_container
    
    def _load_annotation(self, path: str, name: str) -> Dict:

        """Helper to load annotation with consistent error handling"""

        try:
            return load_annotation_path(Path(path).parent, Path(path).name)
        
        except Exception as e:
            raise FileNotFoundError(f"Failed to load {name}: {e}")
        
    def _load_constant_configs(self, 
                               constant_configs: Dict) -> Dict[str, Any]:
        
        # Define configs to load
        configs_to_load = [
            ('DayLevelDataProcessor', 'day_constant_config'),
        ]
        
        loaded_configs = {}
        missing_configs = []
        
        for config_key, config_name in configs_to_load:
            config = constant_configs.get(config_key)
            
            if config is None:
                missing_configs.append(f"{config_key}: not found in constant_configs")
                continue
                
            if not isinstance(config, dict):
                missing_configs.append(f"{config_key}: must be a dict, got {type(config)}")
                continue
            
            loaded_configs[config_name] = config
            logger.debug("Loaded constant config '{}': {} keys", config_key, len(config))
        
        if missing_configs:
            raise KeyError("Missing or invalid constant configs:\n  - " + "\n  - ".join(missing_configs))
        
        return loaded_configs
    
    def _load_dataframes(self,
                         path_annotation: Dict) -> Dict[str, Any]:
        
        # Define dataframes to load
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
            ('purchaseOrders', 'purchaseOrders_df'),
            ('moldSpecificationSummary', 'moldSpecificationSummary_df'),
            ('moldInfo', 'moldInfo_df')
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
        
        return loaded_dfs

    def _execute_impl(self) -> Dict[str, Any]:
        """Load all required data"""
        logger.info("📂 Loading database schemas and path annotations...")
        
        # Load constant configurations
        constant_config = self._load_annotation(
            self.config.performance_analyzer_constant_config_path, 
            "constant config"
        )
        if not constant_config:
            logger.debug("Constant config not found in loaded YAML dict")
        
        # Load specific constant configs for each component
        logger.info("⚙️ Loading component constant configurations...")
        loaded_configs = self._load_constant_configs(constant_config)
        logger.info("✓ All constant configs loaded successfully ({} configs)", len(loaded_configs))

        # Load schemas
        databaseSchemas_data = self._load_annotation(
            self.config.databaseSchemas_path, "databaseSchemas"
        )
        path_annotation = self._load_annotation(
            self.config.annotation_path, "path_annotation"
        )
        
        logger.info("📊 Loading DataFrames from parquet files...")
        loaded_dfs = self._load_dataframes(path_annotation)

        self.data_container.update({
            'constant_config': constant_config,
            'component_configs': loaded_configs,
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })

        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
            'constant_config': constant_config,
            'component_configs': loaded_configs,
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
# PHASE: DAY LEVEL PROCESSING
# ============================================
class  DayLevelProcessingPhase(AtomicPhase):
    """Phase for running the actual day-level data processor logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("DayLevelDataProcessor")

        self.config = config
        self.loaded_data = data_container
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run day-level data processor logic"""
        logger.info("🔄 Running day-level data processor...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]
        purchaseOrders_df = self.loaded_data['dataframes']["purchaseOrders_df"]
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']

        constant_configs = self.loaded_data.get('component_configs', {})
        record_date = self.config.day_level_processor_params.requested_timestamp

        # Initialize day-level data processor
        from agents.analyticsOrchestrator.processor.day_level_data_processor import DayLevelDataProcessor
        processor = DayLevelDataProcessor(
            productRecords_df,
            purchaseOrders_df,
            databaseSchemas_data,
            constant_configs.get('day_constant_config', {}), 
            record_date)
        
        processor_result = processor.process_records()

        return {
            "payload": processor_result.get_temporal_context(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty processing results"""
        logger.warning("Using fallback for DayLevelProcessingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: MONTH LEVEL PROCESSING
# ============================================
class  MonthLevelProcessingPhase(AtomicPhase):
    """Phase for running the actual month-level data processor logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("MonthLevelDataProcessor")

        self.config = config
        self.loaded_data = data_container
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run month-level data processor logic"""
        logger.info("🔄 Running month-level data processor...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]
        purchaseOrders_df = self.loaded_data['dataframes']["purchaseOrders_df"]
        moldInfo_df = self.loaded_data['dataframes']["moldInfo_df"]
        moldSpecificationSummary_df = self.loaded_data['dataframes']["moldSpecificationSummary_df"]
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']

        record_month = self.config.month_level_processor_params.requested_timestamp
        analysis_date = self.config.month_level_processor_params.analysis_date

        # Initialize month-level data processor
        from agents.analyticsOrchestrator.processor.month_level_data_processor import MonthLevelDataProcessor

        processor = MonthLevelDataProcessor(
            productRecords_df,
            purchaseOrders_df,
            moldInfo_df,
            moldSpecificationSummary_df,
            databaseSchemas_data,
            record_month,
            analysis_date)
        
        processor_result = processor.process_records()

        return {
            "payload": processor_result.get_temporal_context(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty processing results"""
        logger.warning("Using fallback for MonthLevelProcessingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: YEAR LEVEL PROCESSING
# ============================================
class  YearLevelProcessingPhase(AtomicPhase):
    """Phase for running the actual year-level data processor logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceAnalyzerConfig,
                 data_container: Dict[str, Any]):
        super().__init__("YearLevelDataProcessor")

        self.config = config
        self.loaded_data = data_container
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run year-level data processor logic"""
        logger.info("🔄 Running year-level data processor...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]
        purchaseOrders_df = self.loaded_data['dataframes']["purchaseOrders_df"]
        moldInfo_df = self.loaded_data['dataframes']["moldInfo_df"]
        moldSpecificationSummary_df = self.loaded_data['dataframes']["moldSpecificationSummary_df"]
        databaseSchemas_data = self.loaded_data['databaseSchemas_data']

        record_year = self.config.year_level_processor_params.requested_timestamp
        analysis_date = self.config.year_level_processor_params.analysis_date

        # Initialize year-level data processor
        from agents.analyticsOrchestrator.processor.year_level_data_processor import YearLevelDataProcessor

        processor = YearLevelDataProcessor(
            productRecords_df,
            purchaseOrders_df,
            moldInfo_df,
            moldSpecificationSummary_df,
            databaseSchemas_data,
            record_year,
            analysis_date)

        processor_result = processor.process_records()

        return {
            "payload": processor_result.get_temporal_context(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty processing results"""
        logger.warning("Using fallback for YearLevelProcessingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }
    
class MultiLevelPerformanceAnalyzer(ConfigReportMixin):

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'day_level_processor_dir': str,
                'day_level_processor_log_path': str,
                'month_level_processor_dir': str,
                'month_level_processor_log_path': str,
                'year_level_processor_dir': str,
                'year_level_processor_log_path': str,
                'multi_level_performance_analyzer_log_path': str,
                'performance_analyzer_constant_config_path': str
                },
            'enable_day_level_processor': Optional[bool],
            'day_level_processor_params': {
                'requested_timestamp': Optional[str],
                'save_result': Optional[bool]
                },
            'enable_month_level_processor': Optional[bool],
            'month_level_processor_params': {
                'requested_timestamp': Optional[str],
                'analysis_date': Optional[str],
                'save_result': Optional[bool]
                },
            'enable_year_level_processor': Optional[bool],
            'year_level_processor_params': {
                'requested_timestamp': Optional[str],
                'analysis_date': Optional[str],
                'save_result': Optional[bool]
                },
            'save_multi_level_performance_analyzer_log': Optional[bool]
            }
        }
    
    def __init__(self, 
                 config: PerformanceAnalyzerConfig):
        
        """
        Initialize MultiLevelPerformanceAnalyzer with configuration.
        
        Args:        
            config: PerformanceAnalyzerConfig containing processing parameters, including:
                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - day_level_processor_dir (str): Base directory for storing reports.
                    - day_level_processor_log_path (str): Path to the DayLevelDataProcessor change log.
                    - month_level_processor_dir (str): Base directory for storing reports.
                    - month_level_processor_log_path (str): Path to the MonthLevelDataProcessor change log.
                    - year_level_processor_dir (str): Base directory for storing reports.
                    - year_level_processor_log_path (str): Path to the YearLevelDataProcessor change log.
                    - multi_level_performance_analyzer_log_path (str): Path to the MultiLevelPerformanceAnalyzer change log.
                - enable_day_level_processor (bool): Enable DayLevelDataProcessor
                - day_level_processor_params (dict): Parameters to process DayLevelDataProcessor
                - enable_month_level_processor (bool): Enable MonthLevelDataProcessor
                - month_level_processor_params (dict): Parameters to process MonthLevelDataProcessor
                - enable_year_level_processor (bool): Enable YearLevelDataProcessor
                - year_level_processor_params (dict): Parameters to process YearLevelDataProcessor
                - save_multi_level_performance_analyzer_log (bool): Save MultiLevelPerformanceAnalyzer change log
                - performance_analyzer_constant_config_path (str): Path to the MultiLevelPerformanceAnalyzer constant config.
        """
        
        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="MultiLevelPerformanceAnalyzer")

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

        self.save_routing = {
            "DayLevelDataProcessor": {
                "enabled": self.config.enable_day_level_processor and self.config.day_level_processor_params.save_result,
                "save_fn": save_analyzer_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.day_level_processor_dir,
                    "change_log_path": self.config.shared_source_config.day_level_processor_log_path
                }
            },
            "MonthLevelDataProcessor": {
                "enabled": self.config.enable_month_level_processor and self.config.month_level_processor_params.save_result,
                "save_fn": save_analyzer_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.month_level_processor_dir,
                    "change_log_path": self.config.shared_source_config.month_level_processor_log_path
                }
            },
            "YearLevelDataProcessor": {
                "enabled": self.config.enable_year_level_processor and self.config.year_level_processor_params.save_result,
                "save_fn": save_analyzer_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.year_level_processor_dir,
                    "change_log_path": self.config.shared_source_config.year_level_processor_log_path
                }
            }
        }

    def run_analyzing(self) -> ExecutionResult:
        """Execute the complete hardware change analyzer pipeline."""
        
        self.logger.info("Starting HardwareChangeAnalyzer ...")

        agent_id = self.__class__.__name__

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        # ============================================
        # ✨ CREATE SHARED CONTAINER
        # ============================================
        shared_data = {}  # This will be populated by DataLoadingPhase
        
        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []
        
        # Phase 1: Data Loading (always required)
        phases.append(DataLoadingPhase(self.config, shared_data))
        
        # Phase 2: Day Level Processing (optional)
        if self.config.enable_day_level_processor:
            self.save_routing["DayLevelDataProcessor"].update({
                "change_log_header": config_header
                })
            phases.append(DayLevelProcessingPhase(self.config, shared_data))

        # Phase 3: Month Level Processing (optional)
        if self.config.enable_month_level_processor:
            self.save_routing["MonthLevelDataProcessor"].update({
                "change_log_header": config_header
                })
            phases.append(MonthLevelProcessingPhase(self.config, shared_data))

        # Phase 4: Year Level Processing (optional)
        if self.config.enable_year_level_processor:
            self.save_routing["YearLevelDataProcessor"].update({
                "change_log_header": config_header
                })
            phases.append(YearLevelProcessingPhase(self.config, shared_data))
        
        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("MultiLevelPerformanceAnalyzer", phases)
        result = agent.execute()
    
        # Process save routing and collect metadata
        save_routing, export_metadata = save_result(self.save_routing, result)
        
        # Update result metadata
        result.metadata.update({
            'save_routing': save_routing,
            'export_metadata': export_metadata
        })

        # ============================================
        # SAVE PIPELINE LOG IF REQUESTED
        # ============================================
        if self.config.save_multi_level_performance_analyzer_log:

            # Generate summary report
            reporter = DictBasedReportGenerator(use_colors=False)
            summary = "\n".join(reporter.export_report(save_routing))
            
            # Save pipeline change log
            message = update_change_log(
                agent_id, 
                config_header, 
                format_execution_tree(result), 
                summary, 
                "\n".join(format_export_logs(export_metadata)), 
                Path(self.config.shared_source_config.multi_level_performance_analyzer_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ HardwareChangeAnalyzer completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result