import pandas as pd
from typing import Tuple, List
from dataclasses import dataclass
from loguru import logger
from agents.autoPlanner.tools.item_mold_capacity_estimator import ItemMoldCapacityEstimator
from agents.autoPlanner.optimizer.hybrid_optimizer.mold_machine_priority_matrix_calculator import MoldMachinePriorityMatrixCalculator
from datetime import datetime
from agents.utils import ConfigReportMixin
from agents.autoPlanner.optimizer.hybrid_optimizer.config.hybrid_suggest_config import HybridSuggestConfig

# class PriorityMatrixCalculator(ConfigReportMixin): # MoldMachinePriorityMatrixCalculator
# Agent that calculates priority matrix based on mold-machine feature weights and estimated mold capacities.

@dataclass
class PriorityBuilderResult:
    """Container for optimization results."""
    proStatus_df: pd.DataFrame | None
    estimated_capacity_invalid_molds: List[str]
    priority_matrix_invalid_molds: List[str]
    mold_estimated_capacity_df: pd.DataFrame | None
    mold_machine_priority_matrix: pd.DataFrame | None
    log: str = ""
    status: str = "UNKNOWN"

class HistoryBasedPriorityBuilder(ConfigReportMixin): #HybridSuggestOptimizer
    
    """
    A hybrid optimization system that combines historical data analysis with mold-machine
    compatibility matching to suggest optimal production configurations.

    This class integrates multiple optimization strategies:
    1. Historical-based mold capacity estimation
    2. Feature weight and production efficiency-based mold-machine priority matrix

    The optimizer helps manufacturing systems make data-driven decisions about
    mold selection, machine allocation, and production planning.
    """
    REQUIRED_FIELDS = {
        'config': {
            'shared_source_config': {
                'annotation_path': str,
                'databaseSchemas_path': str,
                'sharedDatabaseSchemas_path': str,
                'progress_tracker_change_log_path': str,
                'mold_machine_weights_hist_path': str,
                'mold_stability_index_change_log_path': str
                },
            'efficiency': float,
            'loss': float
            }
        }

    def __init__(self,
                 config: HybridSuggestConfig):

        """
        Initialize HybridSuggestOptimizer with configuration.
        
        Args:
            config: HybridSuggestConfig containing processing parameters
            including:
                - shared_source_config: 
                    - annotation_path: Path to the JSON file containing path annotations
                    - databaseSchemas_path: Path to database schemas JSON file for validation
                    - sharedDatabaseSchemas_path: Path to shared database schemas JSON file for validation
                    - progress_tracker_change_log_path: Path to the OrderProgressTracker change log
                    - mold_machine_weights_hist_path: Path to mold-machine feature weights (from MoldMachineFeatureWeightCalculator)
                    - mold_stability_index_change_log_path: Path to the MoldStabilityIndexCalculator change log
                - efficiency: Production efficiency factor (0.0 to 1.0)
                - loss: Production loss factor (0.0 to 1.0)
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="HybridSuggestOptimizer")

        # Store configuration
        self.config = config

        # Validate required configs
        is_valid, errors = self.config.shared_source_config.validate_requirements(self.REQUIRED_FIELDS['config']['shared_source_config'])
        if not is_valid:
            raise ValueError(
                f"{self.__class__.__name__} config validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )
        self.logger.info("✓ Validation for shared_source_config requirements: PASSED!")
        
        #Validate production efficiency factor and loss factor 
        self.validate_configuration()
        self.logger.info("✓ Validation for production efficiency factor and loss factor: PASSED!")

    def validate_configuration(self) -> bool:
        """
        Validate that all required configurations are accessible.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        validation_results = []
        
        # Validate configuration parameters
        if not (0 < self.config.efficiency <= 1):
            self.logger.error("Efficiency must be between 0 and 1, got: {}", self.config.efficiency)
            validation_results.append(False)
        else:
            validation_results.append(True)
            
        if not (0 <= self.config.loss < 1):
            self.logger.error("Loss must be between 0 and 1, got: {}", self.config.loss)
            validation_results.append(False)
        else:
            validation_results.append(True)
        
        is_valid = all(validation_results)
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error("Configuration validation failed")
            
        return is_valid
    
    # ------------------------------------------------------ #
    # HYBRID SUGGEST OPTIMIZER:                              #
    # - ESTIMATE MOLD CAPACITY USING HISTORICAL DATA USING : #
    #     + MOLD MOLD STABILITY INDEX DATA                   #
    # - CALCULATE MOLD MACHINE PRIORITY MATRIX USING :       #
    #     + MOLD ESTIMATED CAPACITY                          #
    #     + MOLD-MACHINE FEATURE WEIGHTS                     #
    # ------------------------------------------------------ #

    def process(self) -> OptimizationResult:
        """Execute the complete hybrid optimization process."""
        
        self.logger.info("Starting HybridSuggestOptimizer ...")
        
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str, required_only=True)
        
        optimization_log_lines = [config_header, "--Processing Summary--"]
        
        # Phase 1: CRITICAL - Must succeed
        try:
            optimization_log_lines.append("Starting Phase 1: ItemMoldCapacityEstimator...")
            (estimated_capacity_invalid_molds, mold_estimated_capacity_df,
            estimation_log) = self._estimate_mold_capacities()
            optimization_log_lines.append("⤷ ItemMoldCapacityEstimator results:")
            optimization_log_lines.append(f"{estimation_log}")
            optimization_log_lines.append("✅ Phase 1 completed")
            
        except Exception as e:
            error_msg = f"❌ Phase 1 failed: {str(e)}"
            self.logger.error(error_msg)
            optimization_log_lines.append(error_msg)
            optimization_log_lines.append("⚠️ Cannot proceed without capacity data")
            
            # Return early with failure state
            return OptimizationResult(
                proStatus_df=None,
                estimated_capacity_invalid_molds=[],
                priority_matrix_invalid_molds=[],
                mold_estimated_capacity_df=None,
                mold_machine_priority_matrix=None,
                log="\n".join(optimization_log_lines),
                status="PHASE_1_FAILED"  # if you have status field
            )
        
        # Phase 2: Dependent on Phase 1
        try:
            optimization_log_lines.append("Starting Phase 2: MoldMachinePriorityMatrixCalculator...")
            (proStatus_df, mold_machine_priority_matrix, priority_matrix_invalid_molds,
            calculator_log) = self._calculate_priority_matrix(mold_estimated_capacity_df)
            optimization_log_lines.append("⤷ MoldMachinePriorityMatrixCalculator results:")
            optimization_log_lines.append(f"{calculator_log}")
            optimization_log_lines.append("✅ Phase 2 completed")
            
        except Exception as e:
            error_msg = f"❌ Phase 2 failed: {str(e)}"
            self.logger.error(error_msg)
            optimization_log_lines.append(error_msg)
            
            # Return partial results (Phase 1 OK, Phase 2 failed)
            return OptimizationResult(
                proStatus_df=None,
                estimated_capacity_invalid_molds=estimated_capacity_invalid_molds,
                priority_matrix_invalid_molds=[],
                mold_estimated_capacity_df=mold_estimated_capacity_df,
                mold_machine_priority_matrix=None,
                log="\n".join(optimization_log_lines),
                status="PHASE_2_FAILED"
            )
        
        # Both phases succeeded
        self.logger.info("✅ Process finished successfully!")
        return OptimizationResult(
            proStatus_df=proStatus_df,
            estimated_capacity_invalid_molds=estimated_capacity_invalid_molds,
            priority_matrix_invalid_molds=priority_matrix_invalid_molds,
            mold_estimated_capacity_df=mold_estimated_capacity_df,
            mold_machine_priority_matrix=mold_machine_priority_matrix,
            log="\n".join(optimization_log_lines),
            status="SUCCESS"
        )
    
    def _estimate_mold_capacities(self) -> Tuple[List[str], pd.DataFrame, str]:
        """Estimate mold capacities using ItemMoldCapacityEstimator."""   
        try:
            self.logger.debug("Initializing ItemMoldCapacityEstimator...")
            optimizer = ItemMoldCapacityEstimator(
                shared_source_config=self.config.shared_source_config,
                efficiency=self.config.efficiency,
                loss=self.config.loss
            )
            self.logger.debug("ItemMoldCapacityEstimator initialized successfully")
            return optimizer.process()
        except Exception as e:
            self.logger.error("Failed to initialize/run ItemMoldCapacityEstimator: {}", str(e))
            raise

    def _calculate_priority_matrix(self,
                                mold_estimated_capacity: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], str]:
        """Calculate mold-machine priority matrix."""
        try:
            self.logger.debug("Initializing MoldMachinePriorityMatrixCalculator...")
            calculator = MoldMachinePriorityMatrixCalculator(
                shared_source_config=self.config.shared_source_config,
                mold_estimated_capacity=mold_estimated_capacity,
                efficiency=self.config.efficiency,
                loss=self.config.loss
            )
            self.logger.debug("MoldMachinePriorityMatrixCalculator initialized successfully")
            return calculator.process()
        except Exception as e:
            self.logger.error("Failed to initialize/run MoldMachinePriorityMatrixCalculator: {}", str(e))
            raise