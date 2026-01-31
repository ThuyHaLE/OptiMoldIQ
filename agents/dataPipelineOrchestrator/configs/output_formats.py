# agents/dataPipelineOrchestrator/configs/output_formats.py

from agents.dataPipelineOrchestrator.configs.healing_configs import ProcessingStatus, ErrorType

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class DataProcessingReport:
    """Generic output for utils functions"""
    status: ProcessingStatus
    data: Any
    error_type: ErrorType = ErrorType.NONE
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        return self.status == ProcessingStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        return self.status == ProcessingStatus.ERROR
    
    @property
    def is_warning(self) -> bool:
        return self.status == ProcessingStatus.WARNING
    
    @property
    def ok(self) -> bool:
        return self.status in {
            ProcessingStatus.SUCCESS,
            ProcessingStatus.PARTIAL_SUCCESS,
            ProcessingStatus.WARNING,
        }