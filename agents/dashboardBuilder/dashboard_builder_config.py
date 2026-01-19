from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from configs.shared.shared_source_config import SharedSourceConfig
from agents.analyticsOrchestrator.analytics_orchestrator_config import LevelConfig, ComponentConfig, AnalyticsOrchestratorConfig
from agents.dashboardBuilder.visualizationServices.configs.change_visualization_service_config import ChangeVisualizationConfig
from agents.dashboardBuilder.visualizationServices.configs.performance_visualization_service_config import PerformanceVisualizationConfig

@dataclass
class DashboardBuilderConfig:
    """Two-layer orchestration configuration
    
    Layer 1 (AnalyticsOrchestrator): Data processing
        - Trackers/Processors run with save_result=False
        - Results kept in-memory for visualization layer
    
    Layer 2 (DashboardBuilder): Visualization 
        - Visualization services run with user-defined save_result
        - Final artifacts saved to disk if save_result=True
    
    Config Flow:
        User defines: day_level_visualization_service (save_result=True)
                ↓
        Auto-creates: day_level_processor (save_result=False)
                ↓
        Orchestrator runs processor → in-memory result
                ↓
        Builder extracts result → runs visualization → saves to disk
    
    Workflow 1 - Hardware Change Visualization:
        - machine_layout_visualization_service
        - mold_machine_pair_visualization_service
    
    Workflow 2 - Multi-Level Performance Visualization:
        - day_level_visualization_service
        - month_level_visualization_service
        - year_level_visualization_service
    """
    
    # ===== User-facing API =====
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)
    
    # Workflow 1: Hardware visualization services
    machine_layout_visualization_service: ComponentConfig = field(default_factory=ComponentConfig)
    mold_machine_pair_visualization_service: ComponentConfig = field(default_factory=ComponentConfig)
    
    # Workflow 2: Performance visualization services
    day_level_visualization_service: ComponentConfig = field(default_factory=ComponentConfig)
    month_level_visualization_service: ComponentConfig = field(default_factory=ComponentConfig)
    year_level_visualization_service: ComponentConfig = field(default_factory=ComponentConfig)

    # Top-level logging
    save_builder_log: Optional[bool] = None
    
    # ===== Internal configs (private - built automatically) =====
    _analytics_orchestrator_config: Optional[AnalyticsOrchestratorConfig] = field(default=None, init=False, repr=False)
    _change_visualization_config: Optional[ChangeVisualizationConfig] = field(default=None, init=False, repr=False)
    _performance_visualization_config: Optional[PerformanceVisualizationConfig] = field(default=None, init=False, repr=False)

    # ===== Defaults =====
    DEFAULT_ENABLE_MACHINE_LAYOUT_VISUALIZATION_SERVICE = False
    DEFAULT_SAVE_MACHINE_LAYOUT_RESULT = False
    DEFAULT_ENABLE_MOLD_MACHINE_PAIR_VISUALIZATION_SERVICE = False
    DEFAULT_SAVE_MOLD_MACHINE_PAIR_RESULT = False
    DEFAULT_ENABLE_DAY_LEVEL_VISUALIZATION_SERVICE = False
    DEFAULT_SAVE_DAY_RESULT = True
    DEFAULT_ENABLE_MONTH_LEVEL_VISUALIZATION_SERVICE = False
    DEFAULT_SAVE_MONTH_YEAR_RESULT = True
    DEFAULT_ENABLE_YEAR_LEVEL_VISUALIZATION_SERVICE = False
    
    def __post_init__(self):
        """Apply defaults, validate, and build internal configs"""
        self._apply_defaults()
        self.validate()
        self._build_internal_configs()
    
    def _apply_defaults(self):
        """Apply default values for all components"""
        # Hardware visualization services
        self._apply_component_defaults(
            self.machine_layout_visualization_service,
            self.DEFAULT_ENABLE_MACHINE_LAYOUT_VISUALIZATION_SERVICE,
            self.DEFAULT_SAVE_MACHINE_LAYOUT_RESULT
        )
        self._apply_component_defaults(
            self.mold_machine_pair_visualization_service,
            self.DEFAULT_ENABLE_MOLD_MACHINE_PAIR_VISUALIZATION_SERVICE,
            self.DEFAULT_SAVE_MOLD_MACHINE_PAIR_RESULT
        )

        # Performance visualization services
        self._apply_visualization_service_defaults(
            self.day_level_visualization_service,
            self.DEFAULT_ENABLE_DAY_LEVEL_VISUALIZATION_SERVICE,
            self.DEFAULT_SAVE_DAY_RESULT,
            require_timestamp=False
        )
        self._apply_visualization_service_defaults(
            self.month_level_visualization_service,
            self.DEFAULT_ENABLE_MONTH_LEVEL_VISUALIZATION_SERVICE,
            self.DEFAULT_SAVE_MONTH_YEAR_RESULT,
            require_timestamp=True
        )
        self._apply_visualization_service_defaults(
            self.year_level_visualization_service,
            self.DEFAULT_ENABLE_YEAR_LEVEL_VISUALIZATION_SERVICE,
            self.DEFAULT_SAVE_MONTH_YEAR_RESULT,
            require_timestamp=True
        )
        
        # Orchestrator logging
        if self.save_builder_log is None:
            self.save_builder_log = self.enable_analytics_orchestrator

    def _apply_component_defaults(self, 
                                  component: ComponentConfig, 
                                  default_enabled: bool, 
                                  default_save: bool):
        """Apply defaults for a simple component (visualization service)"""
        if component.enabled is None:
            component.enabled = default_enabled
        if component.save_result is None:
            component.save_result = default_save

    def _apply_visualization_service_defaults(self, 
                                              visualization_service: ComponentConfig,
                                              default_enabled: bool, 
                                              default_save: bool,
                                              require_timestamp: bool):
        """Apply defaults for a time-based visualization service"""
        if visualization_service.enabled is None:
            visualization_service.enabled = default_enabled

        if visualization_service.enabled and visualization_service.save_result is None:
            if require_timestamp:
                has_timestamp = visualization_service.requested_timestamp is not None
                visualization_service.save_result = default_save if has_timestamp else False
            else:
                visualization_service.save_result = default_save

    def validate(self):
        """Validate configuration consistency"""
        if self.month_level_visualization_service.enabled:
            if self.month_level_visualization_service.requested_timestamp is None:
                raise ValueError(
                    "Month level visualization service requires requested_timestamp to be set"
                )

        if self.year_level_visualization_service.enabled:
            if self.year_level_visualization_service.requested_timestamp is None:
                raise ValueError(
                    "Year level visualization service requires requested_timestamp to be set"
                )
    
    def _to_processor_config(self, viz_config: ComponentConfig) -> ComponentConfig:
        """Convert visualization config to processor config (no save)
        
        This ensures intermediate data from AnalyticsOrchestrator is never saved,
        only final visualization outputs are persisted.
        """
        return ComponentConfig(
            enabled = viz_config.enabled,
            save_result = False,  # Always False at processor level
            requested_timestamp = viz_config.requested_timestamp,
            analysis_date = viz_config.analysis_date
        )

    def _build_internal_configs(self):
        """Build internal analyzer configs from ComponentConfigs"""
        # Build analytics orchestrator config
        if self.enable_analytics_orchestrator:
            self._analytics_orchestrator_config = AnalyticsOrchestratorConfig(
                shared_source_config = self.shared_source_config,

                # Workflow 1: Hardware trackers
                machine_layout_tracker = self._to_processor_config(
                    self.machine_layout_visualization_service
                ),
                mold_machine_pair_tracker = self._to_processor_config(
                    self.mold_machine_pair_visualization_service
                ),

                # Workflow 2: Performance processors
                day_level_processor = self._to_processor_config(
                    self.day_level_visualization_service
                ),
                month_level_processor = self._to_processor_config(
                    self.month_level_visualization_service
                ),
                year_level_processor = self._to_processor_config(
                    self.year_level_visualization_service
                ),

                # Top-level logging
                save_orchestrator_log = False  # Handled at outer level
            )

        # Build change visualization config
        if self.enable_change_visualization_service:
            self._change_visualization_config = ChangeVisualizationConfig(
                shared_source_config=self.shared_source_config,
                enable_machine_layout_visualization=self.machine_layout_visualization_service.enabled,
                save_machine_layout_result=self.machine_layout_visualization_service.save_result,
                enable_mold_machine_pair_visualization=self.mold_machine_pair_visualization_service.enabled,
                save_mold_machine_pair_result=self.mold_machine_pair_visualization_service.save_result,
                save_hardware_change_visualization_log=(
                    self.machine_layout_visualization_service.save_result or
                    self.mold_machine_pair_visualization_service.save_result
                )
            )

        # Build performance visualization config
        if self.enable_performance_visualization_service:
            self._performance_visualization_config = PerformanceVisualizationConfig(
                shared_source_config=self.shared_source_config,
                
                enable_day_level_visualization=self.day_level_visualization_service.enabled,
                day_level_visualization_params=LevelConfig(
                    requested_timestamp=self.day_level_visualization_service.requested_timestamp,
                    analysis_date=self.day_level_visualization_service.analysis_date,
                    save_result=self.day_level_visualization_service.save_result
                ),
                
                enable_month_level_visualization=self.month_level_visualization_service.enabled,
                month_level_visualization_params=LevelConfig(
                    requested_timestamp=self.month_level_visualization_service.requested_timestamp,
                    analysis_date=self.month_level_visualization_service.analysis_date,
                    save_result=self.month_level_visualization_service.save_result
                ),

                enable_year_level_visualization=self.year_level_visualization_service.enabled,
                year_level_visualization_params=LevelConfig(
                    requested_timestamp=self.year_level_visualization_service.requested_timestamp,
                    analysis_date=self.year_level_visualization_service.analysis_date,
                    save_result=self.year_level_visualization_service.save_result
                ),

                save_multi_level_performance_visualization_log=(
                    self.day_level_visualization_service.save_result or
                    self.month_level_visualization_service.save_result or
                    self.year_level_visualization_service.save_result
                )
            )

    # ===== Properties for workflow detection =====
    @property
    def enable_analytics_orchestrator(self) -> bool:
        """Check if analytics orchestrator workflow is enabled"""
        return (
            self.machine_layout_visualization_service.enabled or 
            self.mold_machine_pair_visualization_service.enabled or 
            self.day_level_visualization_service.enabled or 
            self.month_level_visualization_service.enabled or 
            self.year_level_visualization_service.enabled
        )
    
    @property
    def enable_change_visualization_service(self) -> bool:
        """Check if hardware change visualization services workflow is enabled"""
        return (
            self.machine_layout_visualization_service.enabled or 
            self.mold_machine_pair_visualization_service.enabled
        )
    
    @property
    def enable_performance_visualization_service(self) -> bool:
        """Check if performance visualization services workflow is enabled"""
        return (
            self.day_level_visualization_service.enabled or
            self.month_level_visualization_service.enabled or
            self.year_level_visualization_service.enabled
        )

    # ===== Internal config getters (for agent use) =====
    def get_analytics_orchestrator_config(self) -> Optional[AnalyticsOrchestratorConfig]:
        """Get internal config for AnalyticsOrchestrator agent
        
        Returns:
            AnalyticsOrchestratorConfig if workflow is enabled, None otherwise
        """
        return self._analytics_orchestrator_config
    
    def get_change_visualization_config(self) -> Optional[ChangeVisualizationConfig]:
        """Get internal config for ChangeVisualizationService
        
        Returns:
            ChangeVisualizationConfig if workflow is enabled, None otherwise
        """
        return self._change_visualization_config
    
    def get_performance_visualization_config(self) -> Optional[PerformanceVisualizationConfig]:
        """Get internal config for PerformanceVisualizationService
        
        Returns:
            PerformanceVisualizationConfig if workflow is enabled, None otherwise
        """
        return self._performance_visualization_config

    # ===== Helper methods for component management =====
    def _get_enabled_components(self) -> List[Tuple[str, ComponentConfig]]:
        """Get list of all enabled visualization services with their names"""
        components = [
            ("MACHINE_LAYOUT", self.machine_layout_visualization_service),
            ("MOLD_MACHINE_PAIR", self.mold_machine_pair_visualization_service),
            ("DAY", self.day_level_visualization_service),
            ("MONTH", self.month_level_visualization_service),
            ("YEAR", self.year_level_visualization_service)
        ]
        return [(name, config) for name, config in components if config.enabled]

    # ===== Utility methods =====
    def get_summary(self) -> dict:
        """Get readable configuration summary
        
        Returns:
            Dictionary containing builder logging state and enabled workflows
        """
        summary = {
            "builder_logging": self.save_builder_log,
            "workflows": {}
        }

        # Get all enabled components once
        enabled_components = self._get_enabled_components()
        
        if not enabled_components:
            return summary

        # Analytics orchestrator (includes all components)
        if self.enable_analytics_orchestrator:
            summary["workflows"]["analytics_orchestrator"] = {
                "enabled": True,
                "analytic_services": [name for name, _ in enabled_components]
            }

        # Hardware change visualization (subset)
        if self.enable_change_visualization_service:
            hardware_components = [
                name for name, _ in enabled_components 
                if name in ("MACHINE_LAYOUT", "MOLD_MACHINE_PAIR")
            ]
            summary["workflows"]["hardware_change_visualization"] = {
                "enabled": True,
                "visualization_services": hardware_components
            }

        # Performance visualization (subset)
        if self.enable_performance_visualization_service:
            performance_components = [
                name for name, _ in enabled_components 
                if name in ("DAY", "MONTH", "YEAR")
            ]
            summary["workflows"]["performance_visualization"] = {
                "enabled": True,
                "visualization_services": performance_components
            }
        
        return summary
    
    def __repr__(self) -> str:
        """Readable representation showing only enabled user-facing components"""
        enabled = []
        
        if self.enable_analytics_orchestrator:
            enabled.append("analytics_orchestrator")
        
        # Add individual services
        for name, config in self._get_enabled_components():
            service_name = f"{name.lower()}_visualization_service"
            enabled.append(service_name)
        
        return f"DashboardBuilderConfig(enabled={enabled})"