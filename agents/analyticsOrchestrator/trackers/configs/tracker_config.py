from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class TrackerResult:
    """Container for tracker results"""
    record_date: str
    has_change: bool
    changes_dict: Dict = field(default_factory=dict)
    changes_data: Dict = field(default_factory=dict)
    tracker_summary: str = ""
    log: str = ""

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)