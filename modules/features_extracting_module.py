# modules/validation_module.py

from pathlib import Path
from typing import Dict, List, Optional
from modules.base_module import BaseModule, ModuleResult
from loguru import logger
from dataclasses import asdict
from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.auto_planner import FeatureExtractorParams, AutoPlanner, AutoPlannerConfig

class FeaturesExtractingModule(BaseModule):
    """
    Module wrapper for FeaturesExtractingModule.
    
    Handles validation pipeline.
    """
    
    DEFAULT_CONFIG_PATH = 'configs/modules/features_extracting.yaml'

    def __init__(self, config_path: Optional[str] = None):
        # Load YAML as dict (via BaseModule)
        super().__init__(config_path)
        
        # Extract values from YAML structure
        self.project_root = Path(self.config.get('project_root', '.'))
        self.extracting_config = self.config.get('features_extracting', {})
        if not self.extracting_config:
            self.logger.debug("FeaturesExtractingModule config not found in loaded YAML dict")

        # Convert dict to AutoPlannerConfig
        self.extractor_config = self._build_auto_planner_config()

    def _build_auto_planner_config(self) -> AutoPlannerConfig:
        return AutoPlannerConfig(
            shared_source_config = self._build_shared_config(),
            efficiency = self.extracting_config.get('efficiency', None),
            loss = self.extracting_config.get('loss', None),
            feature_extractor = self._build_feature_extractor_params(),
            save_planner_log = self.extracting_config.get('save_planner_log', None),)

    def _build_feature_extractor_params(self) -> FeatureExtractorParams:
        """Build FeatureExtractorParams from YAML config"""
        config = self.extracting_config.get('feature_extractor', {})
        if not config:
            self.logger.debug("Using default FeatureExtractorParams")
        return FeatureExtractorParams(**config)

    def _build_shared_config(self) -> SharedSourceConfig:
        """Build SharedSourceConfig from loaded YAML dict"""
        shared_source_config = self.extracting_config.get('shared_source_config', {})
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
        return "FeaturesExtractingModule"
    
    @property
    def dependencies(self) -> Dict[str, str]:
        """Three dependencies - this is the four module"""
        return {
            'DataPipelineModule': self.extractor_config.shared_source_config.annotation_path, 
            'ValidationModule': self.extractor_config.shared_source_config.validation_change_log_path, 
            'ProgressTrackingModule': self.extractor_config.shared_source_config.progress_tracker_change_log_path
            }
    
    @property
    def context_outputs(self) -> List[str]:
        """Keys that this module writes to context"""
        return [
            'extraction_result',
            'configs'
        ]

    def execute(self, context, dependency_policy) -> ModuleResult:
        
        """
        Execute FeaturesExtractingModule.
        
        Args:
            Configuration containing:
                - project_root: Project root directory
                - shared_source_config: 
                    - annotation_path (str): Path to the JSON file containing path annotations.
                    - databaseSchemas_path (str): Path to database schema for validation.
                    - sharedDatabaseSchemas_path (str): Path to shared database schema for validation.
                    - progress_tracker_change_log_path (str): Path to the OrderProgressTracker change log.
                    - auto_planner_dir (str): Default directory for output and temporary files.
                    - auto_planner_change_log_path (str): Path to the AutoPlanner change log.
                    - features_extractor_dir (str): Base directory for storing reports.
                    - features_extractor_change_log_path (str): Path to the HistoricalFeaturesExtractor change log.
                    - features_extractor_constant_config_path (str): Path to the HistoricalFeaturesExtractor constant config.
                    - mold_stability_index_dir (str): Default directory for output and temporary files.
                    - mold_stability_index_change_log_path (str): Path to the MoldStabilityIndexCalculator change log.
                    - mold_machine_weights_dir (str): Base directory for storing reports.
                    - mold_machine_weights_hist_path (str): Path to the MoldMachineFeatureWeightCalculator weight hist.
                    - mold_machine_weights_change_log_path (str): Path to the MoldMachineFeatureWeightCalculator change log.     
                - efficiency (float): Efficiency threshold [0-1] to classify good/bad records.
                - loss (float): Allowable production loss threshold [0-1].
                - feature_extractor (FeatureExtractorParams): HistoricalFeatureExtractor params
                    - cavity_stability_threshold (float): Threshold for cavity stability.
                    - cycle_stability_threshold (float): Threshold for cycle stability.
                    - total_records_threshold (int): Minimum number of valid production records required
                    (at least 30 records per day).
                    - scaling (str): Method to scale feature impacts ('absolute' or 'relative').
                    - confidence_weight (float): Weight assigned to confidence scores in final weight calculation.
                    - n_bootstrap (int): Number of bootstrap samples for confidence interval estimation.
                    - confidence_level (float): Desired confidence level for statistical tests.
                    - min_sample_size (int): Minimum sample size required for reliable estimation.
                    - feature_weights (dict): Optional preset weights for features.
                    - targets (dict): Target metrics and optimization directions or goals.   
        Returns:
            ModuleResult with pipeline execution results
        """
        
        self.logger = logger.bind(class_="FeaturesExtractingModule")

        try:
            # Create extractor
            extractor = AutoPlanner(config = self.extractor_config)

            # Run extracting
            self.logger.info("Running extracting...")
            extractor_result = extractor.run_scheduled_components()

            self.logger.info("Features extraction execution completed!")

            # ✅ CHECK if it has critical errors in sub-results
            if extractor_result.has_critical_errors():
                failed_paths = extractor_result.get_failed_paths()
                return ModuleResult(
                    status='failed',
                    data={'extraction_result': extractor_result},
                    message=f'Features extraction has critical errors in: {failed_paths}',
                    errors=failed_paths
                )
            
            # ✅ CHECK STATUS from ExecutionResult
            if extractor_result.status == 'failed':
                return ModuleResult(
                    status='failed',
                    data={'extraction_result': extractor_result},
                    message=f'Features extraction failed: {extractor_result.error}',
                    errors=[extractor_result.error] if extractor_result.error else []
                )
 
            # ✅ SUCCESS case
            return ModuleResult(
                status='success',
                data={
                    'extraction_result': extractor_result,
                },
                message='Features extraction completed successfully',
                context_updates={
                    'extraction_result': extractor_result,
                    'configs': asdict(self.extractor_config)
                }
            )

        except Exception as e:
            # ❌ Only catch NOT expected exception (agent crash)
            self.logger.error(f"Features extraction failed: {e}", exc_info=True)
            return ModuleResult(
                status='failed',
                data=None,
                message=f"Features extraction execution failed: {str(e)}",
                errors=[str(e)]
            )