from dataclasses import dataclass, field
from typing import Optional, Literal, Dict

from configs.shared.shared_source_config import SharedSourceConfig
from agents.autoPlanner.calculators.configs.feature_weight_config import FeatureWeightConfig
from agents.autoPlanner.calculators.configs.mold_stability_config import MoldStabilityConfig
from agents.autoPlanner.assigners.configs.assigner_config import PriorityOrder
from agents.autoPlanner.phases.initialPlanner.configs.initial_planner_config import InitialPlannerConfig
from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.features_extractor_config import (
    FeaturesExtractorConfig)    

@dataclass
class FeatureExtractorParams:
    """User-facing parameters for Historical Features Extractor
    
    Combines parameters for:
    - MoldStabilityIndexCalculator
    - MoldMachineFeatureWeightCalculator
    """
    enabled: Optional[bool] = None
    save_result: Optional[bool] = None

    # MoldStabilityIndexCalculator params
    cavity_stability_threshold: Optional[float] = None
    cycle_stability_threshold: Optional[float] = None
    total_records_threshold: Optional[int] = None
    
    # MoldMachineFeatureWeightCalculator params
    scaling: Optional[Literal['absolute', 'relative']] = None
    confidence_weight: Optional[float] = None
    n_bootstrap: Optional[int] = None
    confidence_level: Optional[float] = None
    min_sample_size: Optional[int] = None
    sample_size_threshold: Optional[int] = None
    feature_weights: Optional[Dict[str, float]] = None
    targets: Optional[Dict[str, float]] = None

@dataclass
class InitialPlannerParams:
    """User-facing parameters for Initial Planner"""
    enabled: Optional[bool] = None
    save_result: Optional[bool] = None
    
    priority_order: Optional[PriorityOrder] = None
    max_load_threshold: Optional[int] = None
    log_progress_interval: Optional[int] = None

@dataclass
class AutoPlannerConfig:
    """User-facing orchestrator configuration
    
    AutoPlanner orchestrates:
    1. HistoricalFeaturesExtractor - Extract insights from historical data
    2. InitialPlanner - Plan orders using insights
    
    Global params (efficiency, loss) are applied to both components.
    Component-specific params can be customized via FeatureExtractorParams and InitialPlannerParams.
    
    Example:
        # Minimal config with defaults
        config = AutoPlannerConfig(
            feature_extractor=FeatureExtractorParams(enabled=True),
            initial_planner=InitialPlannerParams(enabled=True)
        )
        
        # Custom config
        config = AutoPlannerConfig(
            efficiency=0.90,  # Global - auto-applied to sub-components
            loss=0.02,
            feature_extractor=FeatureExtractorParams(
                enabled=True,
                cavity_stability_threshold=0.7,
                n_bootstrap=1000
            ),
            initial_planner=InitialPlannerParams(
                enabled=True,
                priority_order=PriorityOrder.PRIORITY_2
            )
        )
    """

    # ===== User-facing API =====
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)
    
    # Global parameters (applied to both components)
    efficiency: Optional[float] = None
    loss: Optional[float] = None

    # Component-specific parameters
    feature_extractor: FeatureExtractorParams = field(default_factory=FeatureExtractorParams)
    initial_planner: InitialPlannerParams = field(default_factory=InitialPlannerParams)

    # Top-level logging
    save_planner_log: Optional[bool] = None
    
    # ===== Defaults =====
    DEFAULT_EFFICIENCY = 0.85
    DEFAULT_LOSS = 0.03

    DEFAULT_ENABLE_FEATURE_EXTRACTOR = False
    DEFAULT_SAVE_FEATURE_EXTRACTOR_RESULT = False
    
    DEFAULT_ENABLE_INITIAL_PLANNER = False
    DEFAULT_SAVE_INITIAL_PLANNER_RESULT = False

    # ===== Internal configs (private - built automatically) =====
    _feature_extractor_config: Optional[FeaturesExtractorConfig] = field(
        default=None, init=False, repr=False
    )
    _initial_planner_config: Optional[InitialPlannerConfig] = field(
        default=None, init=False, repr=False
    )

    def __post_init__(self):
        """Apply defaults and build internal configs"""
        self._apply_defaults()
        self._build_internal_configs()

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value

    def _apply_defaults(self):
        """Apply default values for all components"""
        # Global params
        self.efficiency = self._get_default(self.efficiency, self.DEFAULT_EFFICIENCY)
        self.loss = self._get_default(self.loss, self.DEFAULT_LOSS)  

        # Feature extractor
        if self.feature_extractor.enabled is None:
            self.feature_extractor.enabled = self.DEFAULT_ENABLE_FEATURE_EXTRACTOR
        if self.feature_extractor.save_result is None:
            self.feature_extractor.save_result = self.DEFAULT_SAVE_FEATURE_EXTRACTOR_RESULT
        
        # Initial planner
        if self.initial_planner.enabled is None:
            self.initial_planner.enabled = self.DEFAULT_ENABLE_INITIAL_PLANNER
        if self.initial_planner.save_result is None:
            self.initial_planner.save_result = self.DEFAULT_SAVE_INITIAL_PLANNER_RESULT
        
        # Apply default priority_order if None
        if self.initial_planner.priority_order is None:
            self.initial_planner.priority_order = PriorityOrder.PRIORITY_1

        # Orchestrator logging
        if self.save_planner_log is None:
            self.save_planner_log = (
                (self.should_run_feature_extractor and
                self.should_save_feature_extractor)
                or
                (self.should_run_initial_planner and
                self.should_save_initial_planner)
            )
    
    def _build_internal_configs(self):
        """Build internal configs from user-facing params"""
        # Build FeaturesExtractorConfig
        if self.should_run_feature_extractor:
            self._feature_extractor_config = FeaturesExtractorConfig(
                efficiency=self.efficiency,
                loss=self.loss,
                shared_source_config=self.shared_source_config,
                # Nested configs - NO need to pass efficiency/loss
                # FeaturesExtractorConfig.__post_init__ handles propagation
                mold_stability_config=MoldStabilityConfig(
                    cavity_stability_threshold=self.feature_extractor.cavity_stability_threshold,
                    cycle_stability_threshold=self.feature_extractor.cycle_stability_threshold,
                    total_records_threshold=self.feature_extractor.total_records_threshold
                ),
                feature_weight_config=FeatureWeightConfig(
                    scaling=self.feature_extractor.scaling,
                    confidence_weight=self.feature_extractor.confidence_weight,
                    n_bootstrap=self.feature_extractor.n_bootstrap,
                    confidence_level=self.feature_extractor.confidence_level,
                    min_sample_size=self.feature_extractor.min_sample_size,
                    sample_size_threshold=self.feature_extractor.sample_size_threshold,
                    feature_weights=self.feature_extractor.feature_weights,
                    targets=self.feature_extractor.targets
                )
            )

        # Build InitialPlannerConfig
        if self.should_run_initial_planner:
            self._initial_planner_config = InitialPlannerConfig(
                shared_source_config=self.shared_source_config,
                priority_order=self.initial_planner.priority_order,
                max_load_threshold=self.initial_planner.max_load_threshold,
                log_progress_interval=self.initial_planner.log_progress_interval,
                efficiency=self.efficiency,
                loss=self.loss
            )
    
    # ===== Properties for workflow detection =====
    @property
    def should_run_feature_extractor(self) -> bool:
        """Check if feature extractor should run"""
        return self.feature_extractor.enabled
    
    @property
    def should_save_feature_extractor(self) -> bool:
        """Check if feature extractor should save"""
        return self.feature_extractor.save_result
    
    @property
    def should_run_initial_planner(self) -> bool:
        """Check if initial planner should run"""
        return self.initial_planner.enabled
    
    @property
    def should_save_initial_planner(self) -> bool:
        """Check if initial planner should save"""
        return self.initial_planner.save_result
     
    # ===== Internal config getters (for orchestrator use) =====
    def get_feature_extractor_config(self) -> Optional[FeaturesExtractorConfig]:
        """Get internal config for HistoricalFeaturesExtractor
        
        Returns:
            FeaturesExtractorConfig if enabled, None otherwise
        """
        return self._feature_extractor_config
    
    def get_initial_planner_config(self) -> Optional[InitialPlannerConfig]:
        """Get internal config for InitialPlanner
        
        Returns:
            InitialPlannerConfig if enabled, None otherwise
        """
        return self._initial_planner_config
    
    # ===== Utility methods =====
    def get_summary(self) -> dict:
        """Get readable configuration summary"""
        summary = {
            "global_params": {
                "efficiency": self.efficiency,
                "loss": self.loss
            },
            "orchestrator_logging": self.save_planner_log,
            "components": {}
        }
        
        if self.should_run_feature_extractor:
            summary["components"]["feature_extractor"] = {
                "enabled": True,
                "save_result": self.feature_extractor.save_result,
                "mold_stability": {
                    k: v for k, v in {
                        "cavity_threshold": self.feature_extractor.cavity_stability_threshold,
                        "cycle_threshold": self.feature_extractor.cycle_stability_threshold,
                        "total_records": self.feature_extractor.total_records_threshold
                    }.items() if v is not None
                },
                "feature_weight": {
                    k: v for k, v in {
                        "scaling": self.feature_extractor.scaling,
                        "n_bootstrap": self.feature_extractor.n_bootstrap,
                        "confidence_level": self.feature_extractor.confidence_level,
                        "confidence_weight": self.feature_extractor.confidence_weight
                    }.items() if v is not None
                }
            }
        
        if self.should_run_initial_planner:
            summary["components"]["initial_planner"] = {
                "enabled": True,
                "save_result": self.initial_planner.save_result,
                "priority_order": self.initial_planner.priority_order.name if self.initial_planner.priority_order else None,
                "max_load_threshold": self.initial_planner.max_load_threshold,
                "log_progress_interval": self.initial_planner.log_progress_interval
            }
        
        return summary
    
    def __repr__(self) -> str:
        """Readable representation showing enabled components"""
        components = []
        if self.should_run_feature_extractor:
            components.append("feature_extractor")
        if self.should_run_initial_planner:
            components.append("initial_planner")
        
        return f"AutoPlannerConfig(enabled={components}, efficiency={self.efficiency}, loss={self.loss})"