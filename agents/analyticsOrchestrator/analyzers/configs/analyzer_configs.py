from dataclasses import dataclass, field
from typing import Dict

@dataclass
class AnalyzerResult:
    """Container for analyzer results"""
    analyzer_result: Dict = field(default_factory=dict)
    analyzer_summary: str = ""
    log: str = ""