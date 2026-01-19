from dataclasses import dataclass, field
from typing import Optional

from configs.shared.shared_source_config import SharedSourceConfig

@dataclass
class ChangeVisualizationConfig:
    """Configuration class for hardware change visualization service.
    
    This class manages configuration for machine layout and mold-machine pair visualization services.
    Each level can be independently enabled/disabled and configured with save settings.
    """
    
    # Shared source configs
    shared_source_config: SharedSourceConfig = field(default_factory=SharedSourceConfig)

    # Enable AnalyticsOrchestrator components
    enable_machine_layout_visualization: Optional[bool] = None
    save_machine_layout_result: Optional[bool] = None
    enable_mold_machine_pair_visualization: Optional[bool] = None
    save_mold_machine_pair_result: Optional[bool] = None

    # Save HardwareChangeAnalyzer change log
    save_hardware_change_visualization_log: Optional[bool] = None

    ENABLE_LAYOUT_VISUALIZATION = False
    SAVE_MACHINE_LAYOUT_RESULT = False
    ENABLE_PAIR_VISUALIZATION = False
    SAVE_MOLD_MACHINE_PAIR_RESULT = False

    def __post_init__(self):
        """Apply default values for None fields"""
        self.enable_machine_layout_visualization = self._get_default(self.enable_machine_layout_visualization, 
                                                               self.ENABLE_LAYOUT_VISUALIZATION)
        self.save_machine_layout_result = self._get_default(self.save_machine_layout_result,
                                                            self.SAVE_MACHINE_LAYOUT_RESULT)
        self.enable_mold_machine_pair_visualization = self._get_default(self.enable_mold_machine_pair_visualization, 
                                                                  self.ENABLE_PAIR_VISUALIZATION)
        self.save_mold_machine_pair_result = self._get_default(self.save_mold_machine_pair_result,
                                                               self.SAVE_MOLD_MACHINE_PAIR_RESULT)
        
        self.save_hardware_change_visualization_log = self._get_default(
            self.save_hardware_change_visualization_log,
            (
                (self.enable_machine_layout_visualization and self.save_machine_layout_result) or
                (self.enable_mold_machine_pair_visualization and self.save_mold_machine_pair_result)
            )
        )

    @staticmethod
    def _get_default(value, default):
        """Return default if value is None"""
        return default if value is None else value