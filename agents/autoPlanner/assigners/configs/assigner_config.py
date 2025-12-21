import pandas as pd
from typing import List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class PriorityOrder(Enum):
    """Enumeration for priority orders"""
    PRIORITY_1 = "priority_order_1"
    PRIORITY_2 = "priority_order_2"
    PRIORITY_3 = "priority_order_3"

class PriorityOrdersConfig:
    """Configuration for priority orders"""
    
    PRIORITY_ORDERS = {
        "priority_order_1": ['machine_compatibility', 'moldLeadTime', 'totalQuantity'], 
        "priority_order_2": ['totalQuantity', 'machine_compatibility', 'moldLeadTime'],
        "priority_order_3": ['moldLeadTime', 'totalQuantity', 'machine_compatibility']
    }
    
    @classmethod
    def get_priority_order(cls, order: Union[str, PriorityOrder]) -> List[str]:
        """Get priority order by enum or string"""
        if isinstance(order, PriorityOrder):
            order = order.value
        
        if order not in cls.PRIORITY_ORDERS:
            raise ValueError(f"Invalid priority order: {order}. Available: {list(cls.PRIORITY_ORDERS.keys())}")
        
        return cls.PRIORITY_ORDERS[order]
    
@dataclass
class AssignerStats:
    """Statistics tracking for assignment process"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    iterations: int = 0
    assignments_made: int = 0
    unique_matches: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

@dataclass
class AssignerResult:
    """Container for assigner results"""
    assigned_matrix: pd.DataFrame
    assignments: List[str]
    unassigned_molds: List[str]
    stats: AssignerStats
    overloaded_machines: set = None
    log: str = ""