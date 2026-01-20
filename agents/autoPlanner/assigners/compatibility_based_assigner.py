import pandas as pd
from loguru import logger
from typing import List, Dict, Optional, Union
from datetime import datetime
from configs.shared.config_report_format import ConfigReportMixin
from agents.autoPlanner.assigners.configs.assigner_config import (
    PriorityOrder, AssignerStats, AssignerResult, PriorityOrdersConfig)
from agents.autoPlanner.assigners.configs.assigner_formatter import (
    log_machine_load, log_priority_order, log_final_results)
from agents.autoPlanner.tools.machine_assignment import find_best_machine, update_machine_dataframe_optimized

class CompatibilityBasedAssigner(ConfigReportMixin): #CompatibilityBasedMoldMachineOptimizer

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

    Returns:
    --------
    AssignerResult
        Complete assignment results
    """
    
    def __init__(self,
                 mold_machine_assigned_matrix: pd.DataFrame,
                 unassigned_mold_lead_times: Union[Dict[str, int], pd.DataFrame],
                 compatibility_matrix: pd.DataFrame,
                 priority_order: Union[str, PriorityOrder] = "priority_order_1",
                 max_load_threshold: Optional[int] = 30, 
                 log_progress_interval: int = 10):

        self._capture_init_args()

        # Initialize logger with class name for better tracking
        self.logger = logger.bind(class_="CompatibilityBasedAssigner")

        self.mold_machine_assigned_matrix = mold_machine_assigned_matrix
        self.unassigned_mold_lead_times = unassigned_mold_lead_times
        self.compatibility_matrix = compatibility_matrix
        self.priority_order = priority_order
        self.max_load_threshold = max_load_threshold
        self.log_progress_interval = log_progress_interval
        
    def run_assign(self) -> AssignerResult:

        self.logger.info("Starting CompatibilityBasedAssigner ...")
        self.stats = AssignerStats(start_time=datetime.now())

        self.assignments = []
        self.unassigned_molds = []
        self.overloaded_machines = set()
        
        try:
            # Generate config header using mixin
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_header = self._generate_config_report(timestamp_str)

            assignment_log_lines = [config_header, 
                                    f"--Processing Summary--", 
                                    f"⤷ {self.__class__.__name__} results:"]

            # Input validation and preprocessing
            mold_lead_times_df = self._preprocess_mold_data()
            priority_criteria = PriorityOrdersConfig.get_priority_order(self.priority_order)
            
            # Convert lead time data to dictionary for faster lookup
            mold_lead_times_dict = dict(zip(mold_lead_times_df['moldNo'], 
                                            mold_lead_times_df['moldLeadTime']))

            # Calculate mold priorities
            mold_priorities, calculator_log = self._calculate_mold_priorities_flexible(mold_lead_times_df, 
                                                                                       priority_criteria)
            assignment_log_lines.append(f"{calculator_log}")

            # Process molds by priority order
            assigned_matrix, assignment_log_str = self._assign_by_priority_order(mold_priorities,
                                                                                 mold_lead_times_dict)
            assignment_log_lines.append(f"{assignment_log_str}")

            self.logger.info("✅ Process finished!!!")

            return AssignerResult(
                assigned_matrix=assigned_matrix,
                assignments=self.assignments,
                unassigned_molds=self.unassigned_molds,
                stats=self.stats,
                overloaded_machines=self.overloaded_machines,
                log="\n".join(assignment_log_lines))

        except Exception as e:
            self.logger.error("Assignment failed: {}", str(e))
            raise

    #------------------------------------#
    # Input validation and preprocessing #
    #------------------------------------#
    def _preprocess_mold_data(self) -> pd.DataFrame:
        
        """Convert mold data to standardized DataFrame format"""

        if isinstance(self.unassigned_mold_lead_times, dict):
            # Convert dictionary to DataFrame
            df = pd.DataFrame([
                {'moldNo': k, 'moldLeadTime': v, 'totalQuantity': 1} 
                for k, v in self.unassigned_mold_lead_times.items()
            ])

        elif isinstance(self.unassigned_mold_lead_times, pd.DataFrame):
            df = self.unassigned_mold_lead_times.copy()
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

    #---------------------------#
    # Calculate mold priorities #
    #---------------------------#
    def _calculate_mold_priorities_flexible(self, 
                                            mold_lead_times_df: pd.DataFrame,
                                            priority_order: List[str]) -> List[str]:
        
        """Calculate mold priorities based on flexible priority order"""

        priority_data = []

        for _, row in mold_lead_times_df.iterrows():
            mold_id = row['moldNo']

            # Calculate compatibility score
            if mold_id in self.compatibility_matrix.index:
                compatible_count = self.compatibility_matrix.loc[mold_id].sum()
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
                ascending_flags.append(True)   # Fewer machines = higher priority
            elif criterion == 'moldLeadTime':
                ascending_flags.append(False)  # Longer lead time = higher priority
            elif criterion == 'totalQuantity':
                ascending_flags.append(True)   # Smaller quantity = higher priority

        # Sort by priority
        priority_df_sorted = priority_df.sort_values(
            by=sort_keys, 
            ascending=ascending_flags).reset_index(drop=True)

        calculator_log = log_priority_order(priority_df_sorted, 
                                            priority_order)

        mold_priorities = priority_df_sorted['moldNo'].tolist()
        
        self.logger.info('Total molds to process: {}', len(mold_priorities))
        calculator_log.append(f"Total molds to process: {len(mold_priorities)}")
        
        return mold_priorities, calculator_log
    
    #--------------------------------#
    # Assign molds by priority order #
    #--------------------------------#
    def _assign_by_priority_order(self,
                                  mold_priorities: List[str],
                                  mold_lead_times_dict: Dict[str, int]
                                  ) -> str:

        # Initial machine load and result matrix
        machine_df = self.mold_machine_assigned_matrix.copy()
        assigned_matrix = pd.DataFrame(columns=machine_df.columns)

        # Calculate initial machine load
        current_load = machine_df.sum().to_dict()
        machine_load_log_str = log_machine_load(
            "INITIAL", 
            current_load, 
            self.max_load_threshold)
        
        # Process molds by priority order
        for i, mold_id in enumerate(mold_priorities):
            self.stats.iterations += 1
            
            if i % self.log_progress_interval == 0:
                self.logger.info("Processing mold {}/{}: {}", i+1, len(mold_priorities), mold_id)

            # Process individual mold assignment
            result = self._process_mold_assignment(
                mold_id, i, 
                self.compatibility_matrix, 
                current_load, 
                mold_lead_times_dict, 
                self.max_load_threshold)
            
            if result['assigned']:
                best_machine = result['machine']
                mold_lead_time = result['lead_time']
                
                # Record assignment
                self.assignments.append(mold_id)
                current_load[best_machine] += mold_lead_time
                self.stats.assignments_made += 1

                # Update matrices
                machine_df = update_machine_dataframe_optimized(
                    machine_df, best_machine, 
                    mold_id, mold_lead_time)
                
                assigned_matrix = update_machine_dataframe_optimized(
                    assigned_matrix, best_machine, 
                    mold_id, mold_lead_time)
            else:
                self.unassigned_molds.append(mold_id)
                if result['overloaded_machines']:
                    self.overloaded_machines.update(result['overloaded_machines'])

        # Finalize results
        assigned_matrix.index.name = "moldNo"
        self.stats.end_time = datetime.now()
        self.stats.unique_matches = len(self.assignments)

        assignment_log = log_final_results(
            self.stats, 
            mold_priorities, 
            self.assignments, 
            self.unassigned_molds, 
            current_load, 
            self.overloaded_machines, 
            self.max_load_threshold)
        self.logger.info("{}", assignment_log)

        assignment_log_str = "\n".join([machine_load_log_str, assignment_log])
        self.logger.info("✅ Process finished!!!")

        return assigned_matrix, assignment_log_str
    
    def _process_mold_assignment(self, 
                                 mold_id: str, 
                                 iteration: int, 
                                 compatibility_matrix: pd.DataFrame,
                                 current_load: Dict[str, int],
                                 mold_lead_times_dict: Dict[str, int],
                                 max_load_threshold: Optional[int]) -> Dict:
        
        """Process assignment for a single mold"""
        
        # Check compatibility
        if mold_id not in compatibility_matrix.index:
            if iteration < 5:
                self.logger.info("❌ {} not found in compatibility matrix", mold_id)
            return {'assigned': False, 'overloaded_machines': set()}

        # Get compatible machines
        compatible_machines = compatibility_matrix.loc[mold_id]
        suitable_machines = compatible_machines[compatible_machines == 1].index.tolist()

        if not suitable_machines:
            if iteration < 5:
                self.logger.info("❌ {} has no compatible machines", mold_id)
            return {'assigned': False, 'overloaded_machines': set()}

        # Find best machine
        best_machine = find_best_machine(suitable_machines, 
                                         current_load, 
                                         max_load_threshold)

        if best_machine is None:
            overloaded = set()
            if max_load_threshold is not None:
                overloaded = {m for m in suitable_machines if current_load.get(m, 0) > max_load_threshold}
                
                if iteration < 10:
                    self.logger.info("⚠️ {} cannot be assigned - all compatible machines overloaded", mold_id)
                    for machine in overloaded:
                        self.logger.info("- {}: load = {} > {}", 
                                         machine, 
                                         current_load.get(machine, 0), 
                                         max_load_threshold)
            
            return {'assigned': False, 'overloaded_machines': overloaded}

        # Successful assignment
        mold_lead_time = mold_lead_times_dict.get(mold_id, 1)
        return {
            'assigned': True, 
            'machine': best_machine, 
            'lead_time': mold_lead_time,
            'overloaded_machines': set()
            }