from loguru import logger
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.dashboardBuilder.visualizationServices.configs.change_visualization_service_config import ChangeVisualizationConfig
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
# PHASE: MACHINE LAYOUT VISUALIZATION
# ============================================
class  MachineLayoutVisualizationPhase(AtomicPhase):
    """Phase for running the actual machine layout visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: ChangeVisualizationConfig,
                 data: ExecutionResult,
                 visualization_results_dir: Path | str):
        super().__init__("MachineLayoutVisualizationPipeline")

        self.config = config
        self.data = data
        self.visualization_results_dir = visualization_results_dir

    def _execute_impl(self) -> Dict[str, Any]:
        """Run machine layout visualization logic"""
        logger.info("🔄 Running machine layout visualization...")

        layout_tracker_results = self.data.get_path_data(
            "MachineLayoutTracker",
            'result', 'payload'
        )
        machine_level_results = layout_tracker_results['changes_data']

        from agents.dashboardBuilder.visualizationPipelines.machine_layout_visualization import MachineLayoutVisualizationPipeline
        
        visualization_pipeline = MachineLayoutVisualizationPipeline(
            machine_level_results = machine_level_results,
            default_dir = self.visualization_results_dir,
            visualization_config_path = None,
            enable_parallel = True,
            max_workers = None
            )

        machine_level_visualization_results = visualization_pipeline.run_pipeline()
        
        return {
            "payload": machine_level_visualization_results.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for MachineLayoutVisualizationPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }

# ============================================
# PHASE: MOLD MACHINE PAIR VISUALIZATION
# ============================================
class  MoldMachinePairVisualizationPhase(AtomicPhase):
    """Phase for running the actual mold machine pair visualization logic"""
    
    RECOVERABLE_ERRORS = (KeyError, ValueError, pd.errors.MergeError)
    CRITICAL_ERRORS = (MemoryError, KeyboardInterrupt)
    FALLBACK_FAILURE_IS_CRITICAL = False
    
    def __init__(self, 
                 config: ChangeVisualizationConfig,
                 data: ExecutionResult,
                 visualization_results_dir: Path | str):
        super().__init__("MoldMachinePairVisualizationPipeline")

        self.config = config
        self.data = data
        self.visualization_results_dir = visualization_results_dir
        
    def _execute_impl(self) -> Dict[str, Any]:
        """Run mold machine pair visualization logic"""
        logger.info("🔄 Running mold machine pair visualization...")

        pair_tracker_results = self.data.get_path_data(
            "MoldMachinePairTracker",
            'result', 'payload'
        )
        mold_level_results = pair_tracker_results['changes_data']

        from agents.dashboardBuilder.visualizationPipelines.mold_machine_pair_visualization import MoldMachinePairVisualizationPipeline
        visualization_pipeline = MoldMachinePairVisualizationPipeline(
            mold_level_results = mold_level_results,
            default_dir = self.visualization_results_dir,
            visualization_config_path = None,
            enable_parallel = True,
            max_workers = None
            )

        mold_level_visualization_results = visualization_pipeline.run_pipeline()
        
        return {
            "payload": mold_level_visualization_results.to_dict(),
            "savable": True
        }

    def _fallback(self) -> Dict[str, Any]:
        """Fallback: return empty visualization results"""
        logger.warning("Using fallback for MoldMachinePairVisualizationPhase - returning empty results")
        return {
            "payload": None,
            "savable": False
        }
    
class HardwareChangeVisualizationService(ConfigReportMixin):

    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'hardware_change_visualization_service_dir': str,
                'hardware_change_visualization_service_log_path': str,
                'machine_layout_visualization_pipeline_dir': str,
                'machine_layout_visualization_pipeline_change_log_path': str,
                'mold_machine_pair_visualization_pipeline_dir': str,
                'mold_machine_pair_visualization_pipeline_change_log_path': str,
                },
            'enable_machine_layout_visualization': Optional[bool],
            'save_machine_layout_result': Optional[bool],
            'enable_mold_machine_pair_visualization': Optional[bool],
            'save_mold_machine_pair_result': Optional[bool],
            'save_hardware_change_visualization_log': Optional[bool]
            }
        }
    
    def __init__(self, 
                 config: ChangeVisualizationConfig, 
                 data: ExecutionResult):

        """
        Initialize HardwareChangeVisualizationService with configuration.
        
        Args:        
            config: ChangeVisualizationConfig containing processing parameters, including:
                - shared_source_config:
                    - hardware_change_visualization_service_dir (str): Base directory for storing reports/visualizations.
                    - hardware_change_visualization_service_log_path (str): Path to the HardwareChangeVisualizationService change log.
                    - machine_layout_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - machine_layout_visualization_pipeline_change_log_path (str): Path to the MachineLayoutVisualizationPipeline change log.
                    - mold_machine_pair_visualization_pipeline_dir (str): Base directory for storing reports/visualizations.
                    - mold_machine_pair_visualization_pipeline_change_log_path (str): Path to the MoldMachinePairVisualizationPipeline change log.
                - enable_machine_layout_visualization (bool): Enable MachineLayoutVisualizationPipeline
                - save_machine_layout_result (bool): Save MachineLayoutVisualizationPipeline result
                - enable_mold_machine_pair_visualization (bool): Enable MoldMachinePairVisualizationPipeline
                - save_mold_machine_pair_result (bool): Save MoldMachinePairVisualizationPipeline result
                - save_hardware_change_visualization_log (bool): Save HardwareChangeVisualizationService change log
        """

        # Capture initialization arguments for reporting
        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="HardwareChangeAnalyzer")

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
            "MachineLayoutVisualizationPipeline": {
                "enabled": self.config.enable_machine_layout_visualization and self.config.save_machine_layout_result,
                "save_fn": save_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.machine_layout_visualization_pipeline_dir,
                    "change_log_path": self.config.shared_source_config.machine_layout_visualization_pipeline_change_log_path
                }
            },
            "MoldMachinePairVisualizationPipeline": {
                "enabled": self.config.enable_mold_machine_pair_visualization and self.config.save_mold_machine_pair_result,
                "save_fn": save_reports,
                "save_paths": {
                    "output_dir": self.config.shared_source_config.mold_machine_pair_visualization_pipeline_dir,
                    "change_log_path": self.config.shared_source_config.mold_machine_pair_visualization_pipeline_change_log_path
                }
            },
        }

    def run_visualizing(self):

        """Execute the complete hardware change visualization pipeline."""

        self.logger.info("Starting HardwareChangeVisualizationService ...")

        agent_id = self.__class__.__name__

        timestamp_now = datetime.now()
        timestamp_str = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        dir_name = f"visualized_results/{timestamp_now.strftime('%Y%m%d_%H%M')}"

        # ============================================
        # BUILD PHASE LIST WITH SHARED CONTAINER
        # ============================================
        phases: List[Executable] = []

        # Phase 1: Machine Layout Visualization (optional)
        if self.config.enable_machine_layout_visualization:
            self.save_routing["MachineLayoutVisualizationPipeline"].update({
                "change_log_header": config_header
                })
            visualization_results_dir=f"{self.config.shared_source_config.machine_layout_visualization_pipeline_dir}/{dir_name}"
            phases.append(MachineLayoutVisualizationPhase(self.config, self.data, visualization_results_dir))

        # Phase 2: Mold-Machine Pair Visualization (optional)
        if self.config.enable_mold_machine_pair_visualization:
            self.save_routing["MoldMachinePairVisualizationPipeline"].update({
                "change_log_header": config_header
                })
            visualization_results_dir=f"{self.config.shared_source_config.mold_machine_pair_visualization_pipeline_dir}/{dir_name}"
            phases.append(MoldMachinePairVisualizationPhase(self.config, self.data, visualization_results_dir))

        # ============================================
        # EXECUTE USING COMPOSITE AGENT
        # ============================================
        agent = CompositeAgent("HardwareChangeVisualizationService", phases)
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
        if self.config.save_hardware_change_visualization_log:

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
                Path(self.config.shared_source_config.hardware_change_visualization_service_log_path)
            )
            
            self.logger.info(f"Pipeline log saved: {message}")

        # ============================================
        # PRINT EXECUTION TREE & ANALYSIS
        # ============================================
        self.logger.info("✅ HardwareChangeVisualizationService completed in {:.2f}s!", result.duration)
        
        # Print execution tree for visibility
        print_execution_summary(result)
        
        return result