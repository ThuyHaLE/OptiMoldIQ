# configs/recovery/dependency_healers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from loguru import logger

class BaseHealingAgent(ABC):
    """Base class for healing agents"""
    
    def __init__(self, shared_source_config):
        self.shared_source_config = shared_source_config
        self.logger = logger.bind(class_=self.__class__.__name__)
    
    @abstractmethod
    def heal(self) -> Dict[str, Any]:
        """Execute healing logic. Returns dict with 'status' key."""
        pass
    
    def __call__(self):
        """Make healing agent callable"""
        result = self.heal()
        if result.get('status') != 'SUCCESS':
            raise ValueError(f"Healing failed: {result.get('message', 'Unknown error')}")
        return result