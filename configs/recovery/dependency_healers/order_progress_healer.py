# configs/recovery/dependency_healers/order_progress_healer.py
from typing import Dict, Any
from configs.recovery.dependency_healers.base import BaseHealingAgent

class OrderProgressTrackerHealer(BaseHealingAgent):
    """Healing agent for OrderProgressTracker with lazy import"""
    
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.tracker = None
    
    def heal(self) -> Dict[str, Any]:
        try:
            self.logger.info("Starting order progress tracker healing...")
            
            # Lazy import
            if self.tracker is None:
                from agents.orderProgressTracker.order_progress_tracker import OrderProgressTracker
                self.tracker = OrderProgressTracker(self.config)
            
            results, log_str = self.tracker.pro_status()
            
            self.logger.info("Order progress tracker healing completed")
            
            return {
                'status': 'SUCCESS',
                'message': 'Order progress tracker completed',
                'results': results,
                'log': log_str
            }
            
        except Exception as e:
            self.logger.error(f"Healing failed: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'message': str(e)
            }