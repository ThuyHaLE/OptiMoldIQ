# configs/recovery/dependency_healers/order_progress_healer.py
from typing import Dict, Any
from configs.recovery.dependency_healers.base import BaseHealingAgent

class MoldStabilityIndexCalculatorHealer(BaseHealingAgent):
    """Healing agent for MoldStabilityIndexCalculator with lazy import"""
    
    def __init__(self, 
                 shared_source_config, 
                 mold_stability_config):
        super().__init__(shared_source_config, 
                         mold_stability_config)
        self.shared_source_config = shared_source_config
        self.mold_stability_config = mold_stability_config
        self.calculator = None
    
    def heal(self) -> Dict[str, Any]:
        try:
            self.logger.info("Starting mold stability index calculator healing...")
            
            # Lazy import
            if self.calculator is None:
                from agents.autoPlanner.featureExtractor.initial.historicalFeaturesExtractor.mold_stability_index_calculator import (
                     MoldStabilityIndexCalculator)
                
                self.calculator = MoldStabilityIndexCalculator(
                    self.shared_source_config, 
                    self.mold_stability_config)
            
            results, log_str = self.calculator.process(save_results = True)
            
            self.logger.info("Mold stability index calculator healing completed")
            
            return {
                'status': 'SUCCESS',
                'message': 'Mold stability index calculator healing completed',
                'results': results,
                'log': log_str
            }
            
        except Exception as e:
            self.logger.error(f"Healing failed: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'message': str(e)
            }