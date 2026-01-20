from loguru import logger
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, NoReturn
from configs.shared.config_report_format import ConfigReportMixin
from agents.utils import load_annotation_path

from agents.dashboardBuilder.visualizationServices.configs.performance_visualization_service_config import PerformanceVisualizationConfig
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.visualizationServices.configs.save_output_formatter import save_reports

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
    format_export_logs,
    extract_export_metadata)

# ============================================
# DATA LOADING PHASE
# ============================================
class DataLoadingPhase(AtomicPhase):
    """Phase for loading all required data files"""
    
    RECOVERABLE_ERRORS = (FileNotFoundError, pd.errors.EmptyDataError, KeyError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = True  # ⭐ Data loading is critical!

    def __init__(self, 
                 config: PerformanceVisualizationConfig,
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
    
    def _load_dataframes(self,
                         path_annotation: Dict) -> Dict[str, Any]:
        
        # Define dataframes to load
        dataframes_to_load = [
            ('productRecords', 'productRecords_df'),
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
            'databaseSchemas_data': databaseSchemas_data,
            'path_annotation': path_annotation,
            'dataframes': loaded_dfs
        })

        logger.info("✓ All data loaded successfully ({} DataFrames)", len(loaded_dfs))
        
        return {
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
# PHASE: DAY LEVEL VISUALIZATION
# ============================================
class  DayLevelVisualizationPhase(AtomicPhase):
    """Phase for running the actual day-level data visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceVisualizationConfig,
                 data_container: Dict[str, Any],
                 visualization_data: ExecutionResult,
                 visualization_results_dir: Path | str):
        super().__init__("DayLevelVisualizationPipeline")

        self.config = config
        self.loaded_data = data_container
        self.visualization_data = visualization_data
        self.visualization_results_dir = visualization_results_dir

    def _execute_impl(self) -> Dict[str, Any]:
        """Run day-level data processor logic"""
        logger.info("🔄 Running day-level data processor...")

        moldInfo_df = self.loaded_data['dataframes']["moldInfo_df"]

        day_processor_results = self.visualization_data.get_path_data(
            "DayLevelDataProcessor",
            'result', 'payload'
        )

        requested_timestamp = day_processor_results['adjusted']['date']
        day_level_results = day_processor_results['processed_data']

        from agents.dashboardBuilder.visualizationPipelines.day_level_visualization import DayLevelVisualizationPipeline
        visualization_pipeline = DayLevelVisualizationPipeline(
            day_level_results = day_level_results,
            requested_timestamp = requested_timestamp,
            moldInfo_df = moldInfo_df,
            default_dir = self.visualization_results_dir,
            visualization_config_path = None,
            enable_parallel = True,
            max_workers = None
        )

        day_level_visualization_results = visualization_pipeline.run_pipeline()

        return {
            "payload": day_level_visualization_results.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for DayLevelProcessingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: MONTH LEVEL VISUALIZATION
# ============================================
class  MonthLevelVisualizationPhase(AtomicPhase):
    """Phase for running the actual month-level data visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceVisualizationConfig,
                 data_container: Dict[str, Any],
                 visualization_data: ExecutionResult,
                 visualization_results_dir: Path | str):
        super().__init__("MonthLevelVisualizationPipeline")

        self.config = config
        self.loaded_data = data_container
        self.visualization_data = visualization_data
        self.visualization_results_dir = visualization_results_dir
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run month-level data processor logic"""
        logger.info("🔄 Running month-level data processor...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]

        month_processor_results = self.visualization_data.get_path_data(
            "MonthLevelDataProcessor",
            'result', 'payload'
        )

        analysis_date = month_processor_results['adjusted']['analysis_timestamp']
        requested_timestamp = month_processor_results['adjusted']['month']

        month_level_results = month_processor_results['processed_data']

        from agents.dashboardBuilder.visualizationPipelines.month_level_visualization import MonthLevelVisualizationPipeline
        visualization_pipeline = MonthLevelVisualizationPipeline(
            month_level_results = month_level_results,
            requested_timestamp = requested_timestamp,
            analysis_date = analysis_date,
            productRecords_df = productRecords_df,
            default_dir = self.visualization_results_dir,
            visualization_config_path = None,
            enable_parallel = True,
            max_workers = None
        )

        month_level_visualization_results = visualization_pipeline.run_pipeline()

        return {
            "payload": month_level_visualization_results.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for MonthLevelProcessingPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: YEAR LEVEL VISUALIZATION
# ============================================
class YearLevelVisualizationPhase(AtomicPhase):
    """Phase for running the actual year-level data visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: PerformanceVisualizationConfig,
                 data_container: Dict[str, Any],
                 visualization_data: ExecutionResult,
                 visualization_results_dir: Path | str):
        super().__init__("YearLevelVisualizationPipeline")

        self.config = config
        self.loaded_data = data_container
        self.visualization_data = visualization_data
        self.visualization_results_dir = visualization_results_dir
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run year-level data processor logic"""
        logger.info("🔄 Running year-level data processor...")

        productRecords_df = self.loaded_data['dataframes']["productRecords_df"]

        year_processor_results = self.visualization_data.get_path_data(
            "YearLevelDataProcessor",
            'result', 'payload'
        )

        analysis_date = year_processor_results['adjusted']['analysis_timestamp']
        requested_timestamp = year_processor_results['adjusted']['year']

        year_level_results = year_processor_results['processed_data']

        from agents.dashboardBuilder.visualizationPipelines.year_level_visualization import YearLevelVisualizationPipeline
        visualization_pipeline = YearLevelVisualizationPipeline(
            year_level_results = year_level_results,
            requested_timestamp = requested_timestamp,
            analysis_date = analysis_date,
            productRecords_df = productRecords_df,
            default_dir = self.visualization_results_dir,
            visualization_config_path = None,
            enable_parallel = True,
            max_workers = None
        )

        year_level_visualization_results = visualization_pipeline.run_pipeline()

        return {
            "payload": year_level_visualization_results.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for YearLevelVisualizationPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

class MultiLevelPerformanceVisualizationService(ConfigReportMixin):

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'multi_level_performance_visualization_service_dir': str,
                'multi_level_performance_visualization_service_log_path': str,
                'day_level_visualization_pipeline_dir': str,
                'day_level_visualization_pipeline_log_path': str,
                'month_level_visualization_pipeline_dir': str,
                'month_level_visualization_pipeline_log_path': str,
                'year_level_visualization_pipeline_dir': str,
                'year_level_visualization_pipeline_log_path': str,
                },
            'enable_day_level_visualization': Optional[bool],
            'day_level_visualization_params': {
                'requested_timestamp': Optional[str],
                'save_result': Optional[bool]
                },
            'enable_month_level_visualization': Optional[bool],
            'month_level_visualization_params': {
                'requested_timestamp': Optional[str],
                'analysis_date': Optional[str],
                'save_result': Optional[bool]
                },
            'enable_year_level_visualization': Optional[bool],
            'year_level_visualization_params': {
                'requested_timestamp': Optional[str],
                'analysis_date': Optional[str],
                'save_result': Optional[bool]
                },
            'save_multi_level_performance_visualization_log': Optional[bool]
            }
        }
    
    def __init__(self, 
                 config: PerformanceVisualizationConfig, 
                 data: ExecutionResult):

        """
        Initialize MultiLevelPerformanceAnalyzer with configuration.
        
        Args:        
            config: PerformanceVisualizationConfig containing processing parameters, including:
                - shared_source_config:
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - day_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - day_level_visualization_pipeline_log_path (str): Path to the DayLevelVisualizationPipeline change log.
                    - month_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - month_level_visualization_pipeline_log_path (str): Path to the MonthLevelVisualizationPipeline change log.
                    - year_level_visualization_pipeline_dir (str): Base directory for storing reports.
                    - year_level_visualization_pipeline_log_path (str): Path to the YearLevelVisualizationPipeline change log.
                    - multi_level_performance_visualization_service_log_path (str): Path to the MultiLevelPerformanceVisualizationService change log.

                - enable_day_level_visualization (bool): Enable DayLevelVisualizationPipeline
                - day_level_visualization_params (dict): Parameters to process DayLevelVisualizationPipeline
                - enable_month_level_visualization (bool): Enable MonthLevelVisualizationPipeline
                - month_level_visualization_params (dict): Parameters to process MonthLevelVisualizationPipeline
                - enable_year_level_visualization (bool): Enable YearLevelVisualizationPipeline
                - year_level_visualization_params (dict): Parameters to process YearLevelVisualizationPipeline
                - save_multi_level_performance_visualization_log (bool): Save MultiLevelPerformanceVisualizationService change log
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="MultiLevelPerformanceAnalyzer")

        # Store configuration
        self.config = config
        self.data = data

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(
            self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        self.save_routing = {
            "DayLevelVisualizationPipeline": {
                "enabled": self.config.enable_day_level_visualization and self.config.day_level_visualization_params.save_result,
                "save_fn": save_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.day_level_visualization_pipeline_dir,
                    "change_log_path": self.config.shared_source_config.day_level_visualization_pipeline_log_path
                }
            },
            "MonthLevelVisualizationPipeline": {
                "enabled": self.config.enable_month_level_visualization and self.config.month_level_visualization_params.save_result,
                "save_fn": save_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.month_level_visualization_pipeline_dir,
                    "change_log_path": self.config.shared_source_config.month_level_visualization_pipeline_log_path
                }
            },
            "YearLevelVisualizationPipeline": {
                "enabled": self.config.enable_year_level_visualization and self.config.year_level_visualization_params.save_result,
                "save_fn": save_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.year_level_visualization_pipeline_dir,
                    "change_log_path": self.config.shared_source_config.year_level_visualization_pipeline_log_path
                }
            }
        }

    def run_visualizing(self):

        """Execute the complete hardware change analyzer pipeline."""
        
        self.logger.info("Starting HardwareChangeAnalyzer ...")

        agent_id = self.__class__.__name__

        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        dir_name = f"visualized_results/{timestamp_now.strftime('%Y%m%d_%H%M')}"
        
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
        
        # Phase 2: Day Level Visualization (optional)
        if self.config.enable_day_level_visualization:
            self.save_routing["DayLevelVisualizationPipeline"].update({
                "change_log_header": config_header
                })
            visualization_results_dir=f"{self.config.shared_source_config.day_level_visualization_pipeline_dir}/{dir_name}"
            phases.append(DayLevelVisualizationPhase(self.config, shared_data, self.data, visualization_results_dir))

        # Phase 3: Month Level Visualization (optional)
        if self.config.enable_month_level_visualization:
            self.save_routing["MonthLevelVisualizationPipeline"].update({
                "change_log_header": config_header
                })
            visualization_results_dir=f"{self.config.shared_source_config.month_level_visualization_pipeline_dir}/{dir_name}"
            phases.append(MonthLevelVisualizationPhase(self.config, shared_data, self.data, visualization_results_dir))

        # Phase 4: Year Level Visualization (optional)
        if self.config.enable_year_level_visualization:
            self.save_routing["YearLevelVisualizationPipeline"].update({
                "change_log_header": config_header
                })
            visualization_results_dir=f"{self.config.shared_source_config.year_level_visualization_pipeline_dir}/{dir_name}"
            phases.append(YearLevelVisualizationPhase(self.config, shared_data, self.data, visualization_results_dir))

        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("MultiLevelPerformanceVisualizationService", phases)
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
        if self.config.save_multi_level_performance_visualization_log:
            
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
                Path(self.config.shared_source_config.multi_level_performance_visualization_service_log_path)
            )

            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ MultiLevelPerformanceVisualizationService completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result