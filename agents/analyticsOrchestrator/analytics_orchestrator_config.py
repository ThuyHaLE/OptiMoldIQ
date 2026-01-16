from dataclasses import dataclass, field
from typing import Optional
from configs.shared.shared_source_config import SharedSourceConfig
from agents.analyticsOrchestrator.analyzers.configs.change_analyzer_config import ChangeAnalyzerConfig
from agents.analyticsOrchestrator.analyzers.configs.performance_analyzer_config import LevelConfig, PerformanceAnalyzerConfig

@dataclass
class ComponentConfig:
    """User-facing configuration for a single component
    
    This is the ONLY config structure users need to know.
    Internal sub-configs are built automatically from these.
    """
    enabled: Optional[bool] = None
    save_result: Optional[bool] = None
    requested_timestamp: Optional[str] = None  # For time-based processors
    analysis_date: Optional[str] = None  # For time-based processors

@dataclass
class AnalyticsOrchestratorConfig:
    """User-facing orchestrator configuration
    
    Users define components via ComponentConfig.
    Internal analyzer configs are built automatically.
    
    Workflow 1 - Hardware Change Analysis:
        - machine_layout_tracker
        - mold_machine_pair_tracker
    
    Workflow 2 - Multi-Level Performance Analysis:
        - day_level_processor
        - month_level_processor
        - year_level_processor
    """
    
    # ===== User-facing API =====
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)
    
    # Workflow 1: Hardware trackers
    machine_layout_tracker: ComponentConfig = field(default_factory=ComponentConfig)
    mold_machine_pair_tracker: ComponentConfig = field(default_factory=ComponentConfig)
    
    # Workflow 2: Performance processors
    day_level_processor: ComponentConfig = field(default_factory=ComponentConfig)
    month_level_processor: ComponentConfig = field(default_factory=ComponentConfig)
    year_level_processor: ComponentConfig = field(default_factory=ComponentConfig)
    
    # Top-level logging
    save_orchestrator_log: Optional[bool] = None
    
    # ===== Internal configs (private - built automatically) =====
    _change_analyzer_config: Optional[ChangeAnalyzerConfig] = field(default=None, init=False, repr=False)
    _performance_analyzer_config: Optional[PerformanceAnalyzerConfig] = field(default=None, init=False, repr=False)
    
    # ===== Defaults =====
    DEFAULT_ENABLE_MACHINE_LAYOUT_TRACKER = False
    DEFAULT_SAVE_MACHINE_LAYOUT_RESULT = False
    DEFAULT_ENABLE_MOLD_MACHINE_PAIR_TRACKER = False
    DEFAULT_SAVE_MOLD_MACHINE_PAIR_RESULT = False
    DEFAULT_ENABLE_DAY_LEVEL_PROCESSOR = False
    DEFAULT_SAVE_DAY_RESULT = True
    DEFAULT_ENABLE_MONTH_LEVEL_PROCESSOR = False
    DEFAULT_SAVE_MONTH_YEAR_RESULT = True
    DEFAULT_ENABLE_YEAR_LEVEL_PROCESSOR = False
    
    def __post_init__(self):
        """Apply defaults, validate, and build internal configs"""
        self._apply_defaults()
        self.validate()
        self._build_internal_configs()
    
    def _apply_defaults(self):
        """Apply default values for all components"""
        # Hardware trackers
        self._apply_component_defaults(
            self.machine_layout_tracker,
            self.DEFAULT_ENABLE_MACHINE_LAYOUT_TRACKER,
            self.DEFAULT_SAVE_MACHINE_LAYOUT_RESULT
        )
        self._apply_component_defaults(
            self.mold_machine_pair_tracker,
            self.DEFAULT_ENABLE_MOLD_MACHINE_PAIR_TRACKER,
            self.DEFAULT_SAVE_MOLD_MACHINE_PAIR_RESULT
        )
        
        # Performance processors
        self._apply_processor_defaults(
            self.day_level_processor,
            self.DEFAULT_ENABLE_DAY_LEVEL_PROCESSOR,
            self.DEFAULT_SAVE_DAY_RESULT,
            require_timestamp=False
        )
        self._apply_processor_defaults(
            self.month_level_processor,
            self.DEFAULT_ENABLE_MONTH_LEVEL_PROCESSOR,
            self.DEFAULT_SAVE_MONTH_YEAR_RESULT,
            require_timestamp=True
        )
        self._apply_processor_defaults(
            self.year_level_processor,
            self.DEFAULT_ENABLE_YEAR_LEVEL_PROCESSOR,
            self.DEFAULT_SAVE_MONTH_YEAR_RESULT,
            require_timestamp=True
        )
        
        # Orchestrator logging
        if self.save_orchestrator_log is None:
            self.save_orchestrator_log = (
                self.enable_change_analysis or 
                self.enable_performance_analysis
            )

    def _apply_component_defaults(self, component: ComponentConfig, 
                                default_enabled: bool, default_save: bool):
        """Apply defaults for a simple component (tracker)"""
        if component.enabled is None:
            component.enabled = default_enabled
        if component.save_result is None:
            component.save_result = default_save

    def _apply_processor_defaults(self, processor: ComponentConfig,
                                default_enabled: bool, default_save: bool,
                                require_timestamp: bool):
        """Apply defaults for a time-based processor"""
        if processor.enabled is None:
            processor.enabled = default_enabled
        
        if processor.enabled and processor.save_result is None:
            if require_timestamp:
                has_timestamp = processor.requested_timestamp is not None
                processor.save_result = default_save if has_timestamp else False
            else:
                processor.save_result = default_save
    
    def validate(self):
        """Validate configuration consistency"""
        if self.month_level_processor.enabled:
            if self.month_level_processor.requested_timestamp is None:
                raise ValueError(
                    "Month level processor requires requested_timestamp to be set"
                )
        
        if self.year_level_processor.enabled:
            if self.year_level_processor.requested_timestamp is None:
                raise ValueError(
                    "Year level processor requires requested_timestamp to be set"
                )
    
    def _build_internal_configs(self):
        """Build internal analyzer configs from ComponentConfigs"""
        # Build change analyzer config
        if self.enable_change_analysis:
            self._change_analyzer_config = ChangeAnalyzerConfig(
                shared_source_config=self.shared_source_config,
                enable_machine_layout_tracker=self.machine_layout_tracker.enabled,
                save_machine_layout_result=self.machine_layout_tracker.save_result,
                enable_mold_machine_pair_tracker=self.mold_machine_pair_tracker.enabled,
                save_mold_machine_pair_result=self.mold_machine_pair_tracker.save_result,
                save_hardware_change_analyzer_log=self.enable_change_analysis
            )
        
        # Build performance analyzer config
        if self.enable_performance_analysis:
            self._performance_analyzer_config = PerformanceAnalyzerConfig(
                shared_source_config=self.shared_source_config,
                enable_day_level_processor=self.day_level_processor.enabled,
                day_level_processor_params=LevelConfig(
                    requested_timestamp=self.day_level_processor.requested_timestamp,
                    analysis_date=self.day_level_processor.analysis_date,
                    save_result=self.day_level_processor.save_result
                ),
                enable_month_level_processor=self.month_level_processor.enabled,
                month_level_processor_params=LevelConfig(
                    requested_timestamp=self.month_level_processor.requested_timestamp,
                    analysis_date=self.month_level_processor.analysis_date,
                    save_result=self.month_level_processor.save_result
                ),
                enable_year_level_processor=self.year_level_processor.enabled,
                year_level_processor_params=LevelConfig(
                    requested_timestamp=self.year_level_processor.requested_timestamp,
                    analysis_date=self.year_level_processor.analysis_date,
                    save_result=self.year_level_processor.save_result
                ),
                save_multi_level_performance_analyzer_log=self.enable_performance_analysis
            )
    
    # ===== Properties for workflow detection =====
    @property
    def enable_change_analysis(self) -> bool:
        """Check if hardware change analysis workflow is enabled"""
        return (self.machine_layout_tracker.enabled or 
                self.mold_machine_pair_tracker.enabled)
    
    @property
    def enable_performance_analysis(self) -> bool:
        """Check if performance analysis workflow is enabled"""
        return (self.day_level_processor.enabled or
                self.month_level_processor.enabled or
                self.year_level_processor.enabled)
    
    # ===== Internal config getters (for agent use) =====
    def get_change_analyzer_config(self) -> Optional[ChangeAnalyzerConfig]:
        """Get internal config for ChangeAnalyzer agent
        
        Returns:
            ChangeAnalyzerConfig if workflow is enabled, None otherwise
        """
        return self._change_analyzer_config
    
    def get_performance_analyzer_config(self) -> Optional[PerformanceAnalyzerConfig]:
        """Get internal config for PerformanceAnalyzer agent
        
        Returns:
            PerformanceAnalyzerConfig if workflow is enabled, None otherwise
        """
        return self._performance_analyzer_config
    
    # ===== Utility methods =====
    def get_summary(self) -> dict:
        """Get readable configuration summary"""
        summary = {
            "orchestrator_logging": self.save_orchestrator_log,
            "workflows": {}
        }
        
        if self.enable_change_analysis:
            trackers = []
            if self.machine_layout_tracker.enabled:
                trackers.append("MACHINE_LAYOUT")
            if self.mold_machine_pair_tracker.enabled:
                trackers.append("MOLD_MACHINE_PAIR")
            
            summary["workflows"]["hardware_change_analysis"] = {
                "enabled": True,
                "trackers": trackers
            }
        
        if self.enable_performance_analysis:
            levels = []
            if self.day_level_processor.enabled:
                levels.append("DAY")
            if self.month_level_processor.enabled:
                levels.append("MONTH")
            if self.year_level_processor.enabled:
                levels.append("YEAR")
            
            summary["workflows"]["performance_analysis"] = {
                "enabled": True,
                "levels": levels
            }
        
        return summary
    
    def __repr__(self) -> str:
        """Readable representation showing only user-facing config"""
        components = []
        if self.machine_layout_tracker.enabled:
            components.append("machine_layout_tracker")
        if self.mold_machine_pair_tracker.enabled:
            components.append("mold_machine_pair_tracker")
        if self.day_level_processor.enabled:
            components.append("day_level_processor")
        if self.month_level_processor.enabled:
            components.append("month_level_processor")
        if self.year_level_processor.enabled:
            components.append("year_level_processor")
        
        return f"AnalyticsOrchestratorConfig(enabled={components})"