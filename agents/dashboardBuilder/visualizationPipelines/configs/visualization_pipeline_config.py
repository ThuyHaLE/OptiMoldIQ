from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class VisualizationPipelineResult:
    """Container for pipeline results"""
    raw_data: Dict = field(default_factory=dict)
    visualized_data: Dict = field(default_factory=dict)
    pipeline_name: str = ""
    pipeline_summary: str = ""
    pipeline_report: str = "" #early_warning_report (month-level only)
    log: str = ""

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)