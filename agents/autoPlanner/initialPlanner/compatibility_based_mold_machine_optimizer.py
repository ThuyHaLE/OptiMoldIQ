import pandas as pd
from loguru import logger
from typing import List, Dict, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class PriorityOrder(Enum):
    """Enumeration for priority orders"""
    PRIORITY_1 = "priority_order_1"
    PRIORITY_2 = "priority_order_2"
    PRIORITY_3 = "priority_order_3"

@dataclass
class OptimizationStats:
    """Statistics tracking for optimization process"""
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
class OptimizationResult:
    """Container for optimization results"""
    assigned_matrix: pd.DataFrame
    assignments: List[str]
    unassigned_molds: List[str]
    stats: OptimizationStats
    overloaded_machines: set

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

class CompatibilityBasedMoldMachineOptimizer:

    def __init__(self, log_progress_interval: int = 10):
        self.logger = logger.bind(class_="CompatibilityBasedMoldMachineOptimizer")
        self.log_progress_interval = log_progress_interval
        
    def run_optimization(self,
                         mold_machine_assigned_matrix: pd.DataFrame,
                         unassigned_mold_lead_times: Union[Dict[str, int], pd.DataFrame],
                         compatibility_matrix: pd.DataFrame,
                         priority_order: Union[str, PriorityOrder] = "priority_order_1",
                         max_load_threshold: Optional[int] = 30,
                         verbose: bool = True) -> OptimizationResult:
        
        """
        Assign molds using optimized algorithm with optional load constraint

        Parameters:
        -----------
        mold_machine_assigned_matrix : pd.DataFrame
            Current machine assignment matrix
        unassigned_mold_lead_times : Union[Dict[str, int], pd.DataFrame]
            Mold lead times data
        compatibility_matrix : pd.DataFrame
            Mold-machine compatibility matrix
        priority_order : Union[str, PriorityOrder]
            Priority ordering strategy
        max_load_threshold : Optional[int], default=30
            Maximum allowed load threshold. If None, no load constraint is applied
        verbose : bool, default=True
            Enable verbose logging

        Returns:
        --------
        OptimizationResult
            Complete optimization results
        """

        stats = OptimizationStats(start_time=datetime.now())
        
        try:
            # Input validation and preprocessing
            mold_lead_times_df = self._preprocess_mold_data(unassigned_mold_lead_times)
            priority_criteria = PriorityOrdersConfig.get_priority_order(priority_order)
            
            # Initialize tracking variables
            assignments = []
            unassigned_molds = []
            overloaded_machines = set()
            
            # Calculate mold priorities
            mold_priorities = self._calculate_mold_priorities_flexible(
                mold_lead_times_df, compatibility_matrix, priority_criteria, verbose=verbose)
            
            if verbose:
                self.logger.info('Processing {} molds in priority order', len(mold_priorities))

            # Convert lead time data to dictionary for faster lookup
            mold_lead_times_dict = dict(zip(mold_lead_times_df['moldNo'], 
                                          mold_lead_times_df['moldLeadTime']))

            # Calculate initial machine load
            machine_df = mold_machine_assigned_matrix.copy()
            current_load = self._calculate_machine_load(machine_df)
            
            if verbose:
                self._log_machine_load("INITIAL", current_load, max_load_threshold)

            # Initialize result matrix
            assigned_matrix = pd.DataFrame(columns=machine_df.columns)

            # Process molds by priority order
            for i, mold_id in enumerate(mold_priorities):
                stats.iterations += 1
                
                if verbose and i % self.log_progress_interval == 0:
                    self.logger.info("Processing mold {}/{}: {}", 
                                    i+1, len(mold_priorities), mold_id)

                # Process individual mold assignment
                result = self._process_mold_assignment(
                    mold_id, i, compatibility_matrix, current_load, 
                    mold_lead_times_dict, max_load_threshold, verbose)
                
                if result['assigned']:
                    best_machine = result['machine']
                    mold_lead_time = result['lead_time']
                    
                    # Record assignment
                    assignments.append(mold_id)
                    current_load[best_machine] += mold_lead_time
                    stats.assignments_made += 1

                    # Update matrices
                    machine_df = self._update_machine_dataframe_optimized(
                        machine_df, best_machine, mold_id, mold_lead_time)
                    
                    assigned_matrix = self._update_machine_dataframe_optimized(
                        assigned_matrix, best_machine, mold_id, mold_lead_time)
                else:
                    unassigned_molds.append(mold_id)
                    if result['overloaded_machines']:
                        overloaded_machines.update(result['overloaded_machines'])

            # Finalize results
            assigned_matrix.index.name = "moldNo"
            stats.end_time = datetime.now()
            stats.unique_matches = len(assignments)

            if verbose:
                self._log_final_results(stats, mold_priorities, assignments, 
                                      unassigned_molds, current_load, 
                                      overloaded_machines, max_load_threshold)

            return OptimizationResult(assigned_matrix=assigned_matrix,
                                      assignments=assignments,
                                      unassigned_molds=unassigned_molds,
                                      stats=stats,
                                      overloaded_machines=overloaded_machines)
            
        except Exception as e:
            self.logger.error("Optimization failed: {}", str(e))
            raise

    def _preprocess_mold_data(self, 
                              mold_data: Union[Dict[str, int], pd.DataFrame]) -> pd.DataFrame:
        
        """Convert mold data to standardized DataFrame format"""

        if isinstance(mold_data, dict):
            # Convert dictionary to DataFrame
            df = pd.DataFrame([
                {'moldNo': k, 'moldLeadTime': v, 'totalQuantity': 1} 
                for k, v in mold_data.items()
            ])

        elif isinstance(mold_data, pd.DataFrame):
            df = mold_data.copy()
            # Ensure required columns exist
            required_cols = ['moldNo', 'moldLeadTime']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Add totalQuantity if not present
            if 'totalQuantity' not in df.columns:
                df['totalQuantity'] = 1

        else:
            raise TypeError("mold_data must be either Dict or DataFrame")
        
        return df

    def _process_mold_assignment(self, 
                                 mold_id: str, 
                                 iteration: int, 
                                 compatibility_matrix: pd.DataFrame,
                                 current_load: Dict[str, int],
                                 mold_lead_times_dict: Dict[str, int],
                                 max_load_threshold: Optional[int],
                                 verbose: bool) -> Dict:
        
        """Process assignment for a single mold"""
        
        # Check compatibility
        if mold_id not in compatibility_matrix.index:
            if verbose and iteration < 5:
                self.logger.info("❌ {} not found in compatibility matrix", mold_id)
            return {'assigned': False, 'overloaded_machines': set()}

        # Get compatible machines
        compatible_machines = compatibility_matrix.loc[mold_id]
        suitable_machines = compatible_machines[compatible_machines == 1].index.tolist()

        if not suitable_machines:
            if verbose and iteration < 5:
                self.logger.info("❌ {} has no compatible machines", mold_id)
            return {'assigned': False, 'overloaded_machines': set()}

        # Find best machine
        best_machine = self._find_best_machine(suitable_machines, current_load, max_load_threshold)

        if best_machine is None:
            overloaded = set()
            if max_load_threshold is not None:
                overloaded = {m for m in suitable_machines 
                            if current_load.get(m, 0) > max_load_threshold}
                
                if verbose and iteration < 10:
                    self.logger.info("⚠️ {} cannot be assigned - all compatible machines overloaded", mold_id)
                    for machine in overloaded:
                        self.logger.info("- {}: load = {} > {}", 
                                       machine, current_load.get(machine, 0), max_load_threshold)
            
            return {'assigned': False, 'overloaded_machines': overloaded}

        # Successful assignment
        mold_lead_time = mold_lead_times_dict.get(mold_id, 1)
        return {
            'assigned': True, 
            'machine': best_machine, 
            'lead_time': mold_lead_time,
            'overloaded_machines': set()
            }

    def _calculate_mold_priorities_flexible(self, 
                                            mold_lead_times_df: pd.DataFrame,
                                            compatibility_matrix: pd.DataFrame,
                                            priority_order: List[str],
                                            verbose: bool = False) -> List[str]:
        
        """Calculate mold priorities based on flexible priority order"""

        priority_data = []

        for _, row in mold_lead_times_df.iterrows():
            mold_id = row['moldNo']

            # Calculate compatibility score
            if mold_id in compatibility_matrix.index:
                compatible_count = compatibility_matrix.loc[mold_id].sum()
            else:
                compatible_count = 0  # No compatibility = highest priority

            priority_data.append({
                'moldNo': mold_id,
                'machine_compatibility': compatible_count,
                'moldLeadTime': row['moldLeadTime'],
                'totalQuantity': row['totalQuantity']
            })

        # Convert to DataFrame and sort
        priority_df = pd.DataFrame(priority_data)
        
        # Create sorting configuration
        sort_keys = []
        ascending_flags = []

        for criterion in priority_order:
            sort_keys.append(criterion)
            
            if criterion == 'machine_compatibility':
                ascending_flags.append(True)  # Fewer machines = higher priority
            elif criterion == 'moldLeadTime':
                ascending_flags.append(False)  # Longer lead time = higher priority
            elif criterion == 'totalQuantity':
                ascending_flags.append(True)  # Smaller quantity = higher priority

        # Sort by priority
        priority_df_sorted = priority_df.sort_values(
            by=sort_keys, ascending=ascending_flags
        ).reset_index(drop=True)

        if verbose:
            self._log_priority_order(priority_df_sorted, priority_order)

        return priority_df_sorted['moldNo'].tolist()

    def _log_priority_order(self, 
                            priority_df: pd.DataFrame, 
                            priority_order: List[str]) -> None:
        
        """Log mold priority order"""

        self.logger.info("=== MOLD PRIORITY ORDER (by {}) ===", ' > '.join(priority_order))
        
        display_count = min(15, len(priority_df))
        for i in range(display_count):
            row = priority_df.iloc[i]
            self.logger.info("{:2d}. {}: machines={}, leadTime={}, quantity={:,}",
                           i+1, row['moldNo'], row['machine_compatibility'], 
                           row['moldLeadTime'], row['totalQuantity'])

        if len(priority_df) > display_count:
            self.logger.info("    ... and {} more molds", len(priority_df) - display_count)

    def _log_machine_load(self, 
                          phase: str, 
                          current_load: Dict[str, int], 
                          max_load_threshold: Optional[int]) -> None:
        
        """Log machine load information"""

        self.logger.info("=== {} MACHINE LOAD ===", phase)
        
        for machine, load in sorted(current_load.items()):
            if max_load_threshold is not None:
                status = "⚠️ OVERLOAD" if load > max_load_threshold else "✅ OK"
                self.logger.info("{}: {} {}", machine, load, status)
            else:
                self.logger.info("{}: {}", machine, load)

        if max_load_threshold is not None:
            self.logger.info("Maximum allowed load: {}", max_load_threshold)

    def _log_final_results(self, 
                           stats: OptimizationStats, 
                           mold_priorities: List[str],
                           assignments: List[str], 
                           unassigned_molds: List[str],
                           current_load: Dict[str, int], 
                           overloaded_machines: set,
                           max_load_threshold: Optional[int]) -> None:
        
        """Log final optimization results"""

        self.logger.info("=" * 50)
        self.logger.info("ROUND 3 - OPTIMIZATION RESULTS SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info("Successfully assigned molds: {}. \nDetails: {}", len(assignments), assignments)
        self.logger.info("Unassigned molds: {}. \nDetail: {}", len(unassigned_molds), unassigned_molds)
        self.logger.info("Total molds processed: {}", mold_priorities)
        self.logger.info("Success rate: {:.1f}%", len(assignments)/len(mold_priorities))
        self.logger.info("Total execution time: {:.2f} seconds", stats.duration or 0)
        self.logger.info("=" * 50)

        if max_load_threshold is not None and overloaded_machines:
            self.logger.info("=== MACHINES SKIPPED DUE TO HIGH LOAD ===")
            for machine in sorted(overloaded_machines):
                self.logger.info("{}: load = {}", machine, current_load.get(machine, 0))

        self._log_machine_load("FINAL", current_load, max_load_threshold)

    @staticmethod
    def _calculate_machine_load(machine_df: pd.DataFrame) -> Dict[str, int]:
        """Calculate total current load for each machine"""
        return machine_df.sum().to_dict()
    
    @staticmethod
    def _find_best_machine(suitable_machines: List[str],
                           current_load: Dict[str, int],
                           max_load_threshold: Optional[int] = None) -> Optional[str]:
        
        """Find the best machine based on load constraints and optimization criteria"""
        
        machine_scores = []

        for machine in suitable_machines:
            load = current_load.get(machine, 0)

            # Apply load constraint if specified
            if max_load_threshold is not None and load > max_load_threshold:
                continue

            # Score based on current load (lower load = higher score)
            score = -load
            machine_scores.append((machine, score, load))

        if not machine_scores:
            return None

        # Return machine with highest score (lowest load)
        machine_scores.sort(key=lambda x: x[1], reverse=True)
        return machine_scores[0][0]
    
    @staticmethod
    def _update_machine_dataframe_optimized(machine_df: pd.DataFrame,
                                            machine_code: str,
                                            mold_id: str,
                                            lead_time: int) -> pd.DataFrame:
        
        """Update machine DataFrame with new assignment (optimized version)"""
        
        df = machine_df.copy()
        
        # Create new row efficiently
        new_row_data = {col: 0 for col in df.columns}
        new_row_data[machine_code] = lead_time
        
        new_row_df = pd.DataFrame([new_row_data], index=[mold_id])
        
        # Concatenate efficiently
        df = pd.concat([df, new_row_df], ignore_index=False)
        
        return df