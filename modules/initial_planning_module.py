# modules/validation_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from dataclasses import asdict

from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.assigners.configs.assigner_config import PriorityOrder
from agents.autoPlanner.phases.initialPlanner.initial_planner import InitialPlannerConfig, InitialPlanner

class InitialPlanningModule(BaseModule):
    """
    Module wrapper for InitialPlanningModule.
    
    Handles planning pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/initial_planning.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Extract values from YAML structure
        self.project_root = Path(self.config.get('project_root', '.'))
        self.planning_config = self.config.get('initial_planning', {})
        if not self.planning_config:
            self.logger.debug("InitialPlanningModule config not found in loaded YAML dict")

        # Convert dict to InitialPlannerConfig
        self.planner_config = self._build_planner_config()

    def _build_planner_config(self) -> InitialPlannerConfig:
        return InitialPlannerConfig(
            shared_source_config = self._build_shared_config(),
            priority_order = self.planning_config.get('priority_order', PriorityOrder.PRIORITY_1),
            max_load_threshold = self.planning_config.get('max_load_threshold', None),
            log_progress_interval = self.planning_config.get('log_progress_interval', None),
            efficiency = self.planning_config.get('efficiency', None),
            loss = self.planning_config.get('loss', None),
            )

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        shared_source_config = self.planning_config.get('shared_source_config', {})
        if not shared_source_config:
            self.logger.debug("Using default SharedSourceConfig")
        resolved_config = self._resolve_paths(shared_source_config)
        return SharedSourceConfig(**resolved_config)

    def _resolve_paths(self, config: dict) -> dict:
        """Resolve relative paths with project_root"""
        resolved = {}
        for key, value in config.items():
            if value and isinstance(value, str) and ('_dir' in key or '_path' in key):
                resolved[key] = str(self.project_root / value)
            else:
                resolved[key] = value
        return resolved

    @property
    def module_name(self) -> str:
        """Unique module name"""
        return "InitialPlanningModule"
    
    @property
    def dependencies(self) -> List[str]:
        """Two dependencies - this is the third module"""
        return ['DataPipelineModule', 'ValidationModule', "ProgressTrackingModule", "FeaturesExtractingModule"]
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'planning_result',
            'configs'
        ]

    def execute(self, context: Dict) -> ModuleResult:
        """
        Execute InitialPlanningModule.
        
        Args:
            context: Shared context (empty for first module)
            self.config: Configuration containing:

                - project_root: Project root directory
                - shared_source_config: 
                    - annotation_path (str): Path to the JSON file containing path annotations
                    - databaseSchemas_path (str): Path to database schemas JSON file for validation
                    - sharedDatabaseSchemas_path (str): Path to shared database schemas JSON file for validation
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log
                    - mold_machine_weights_hist_path (str): Path to mold-machine feature weights (from MoldMachineFeatureWeightCalculator)
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log
                    - initial_planner_dir (str): Base directory for storing reports
                    - initial_planner_change_log_path (str): Path to the InitialPlanner change log
                    - initial_planner_constant_config_path (str): Path to the InitialPlanner constant config.
                    - pending_processor_dir (str): Base directory for storing reports
                    - pending_processor_change_log_path (str): Path to the ProducingOrderPlanner change log
                    - producing_processor_dir (str): Base directory for storing reports
                    - producing_processor_change_log_path (str): Path to the PendingOrderPlanner change log
                - priority_order (str): Priority ordering strategy
                - max_load_threshold (int): Maximum allowed load threshold. If None, no load constraint is applied
                - log_progress_interval (int): Interval at which progress logs are emitted during processing.
                - efficiency (float): Production efficiency factor (0.0 to 1.0)
                - loss (float): Production loss factor (0.0 to 1.0)
            dependencies: Empty dict (no dependencies)
            
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="InitialPlanningModule")

        try:
            # Create planner
            initial_planner = InitialPlanner(config = self.planner_config)

            # Run planning
            self.logger.info("Running planning...")
            planner_result = initial_planner.run_planning_and_save_results()

            self.logger.info("Initial planner execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if planner_result.has_critical_errors():
                failed_paths = planner_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'planning_result': planner_result},
                    message=f'Initial planner has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if planner_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'planning_result': planner_result},
                    message=f'Initial planner failed: {planner_result.error}',
                    errors=[planner_result.error] if planner_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'planning_result': planner_result,
                },
                message='Initial planner completed successfully',
                context_updates={
                    'planning_result': planner_result,
                    'configs': asdict(self.planner_config)
                }
            )

        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Initial planner failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Initial planner execution failed: {str(e)}",
                errors=[str(e)]
            )