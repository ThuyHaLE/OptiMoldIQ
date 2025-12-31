from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class AnalyzerResult:
    """Container for analyzer results"""
    analyzer_result: Dict = field(default_factory=dict)
    analyzer_summary: str = ""
    log: str = ""

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)