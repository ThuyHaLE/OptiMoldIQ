import pandas as pd
from loguru import logger

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set, Union

from agents.decorators import validate_init_dataframes

from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout
from agents.autoPlanner.tools.plan_matching import mold_item_plan_a_matching
from agents.autoPlanner.tools.compatibility import create_mold_machine_compatibility_matrix

from configs.shared.config_report_format import ConfigReportMixin
from configs.shared.dict_based_report_generator import DictBasedReportGenerator
from agents.autoPlanner.assigners.configs.assigner_config import PriorityOrder, AssignerResult
from dataclasses import dataclass, asdict

@dataclass
class PendingPlannerResult:
    initial_plan: pd.DataFrame
    assigned_molds: List
    unassigned_molds: List
    overloaded_machines: Set
    not_matched_pending: pd.DataFrame
    log_str: str
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary for serialization/logging."""
        return asdict(self)
    
# Decorator to validate DataFrames are initialized with the correct schema
@validate_init_dataframes(lambda self: {
    "machineInfo_df": list(self.databaseSchemas_data['staticDB']['machineInfo']['dtypes'].keys()),
    "moldInfo_df": list(self.databaseSchemas_data['staticDB']['moldInfo']['dtypes'].keys()),
    "machine_info_df": list(self.sharedDatabaseSchemas_data["machine_info"]['dtypes'].keys()),
    "mold_estimated_capacity_df": list(self.sharedDatabaseSchemas_data["mold_estimated_capacity"]['dtypes'].keys()),
    "producing_status_data": list(self.sharedDatabaseSchemas_data["producing_data"]['dtypes'].keys()),
    "pending_status_data": list(self.sharedDatabaseSchemas_data["pending_data"]['dtypes'].keys())
})
class PendingOrderPlanner(ConfigReportMixin):
    
    """
    Processor for handling pending production assignments using two-tier optimization:
    1. History-based optimization (primary)
    2. Compatibility-based optimization (fallback for unassigned molds)
    """

    def __init__(self, 
                 databaseSchemas_data: Dict,
                 sharedDatabaseSchemas_data: Dict,
                 generator_constant_config: Dict,
                 moldInfo_df: pd.DataFrame,
                 machineInfo_df: pd.DataFrame,
                 producing_status_data: pd.DataFrame,
                 pending_status_data: pd.DataFrame,
                 mold_estimated_capacity: pd.DataFrame,
                 mold_machine_priority_matrix: pd.DataFrame,
                 priority_order: Union[str, PriorityOrder] = "priority_order_1",
                 max_load_threshold: int = 30,
                 log_progress_interval: int = 5
                 ):
        
        """
        Initialize PendingOrderPlanner with configuration.
        
        Args:
            - databaseSchemas_data: Database schemas for validation
            - sharedDatabaseSchemas_data: Shared database schemas for validation
            - generator_constant_config: Constant config for production schedule generator
            - moldInfo_df: Detailed mold information including tonnage requirements
            - machineInfo_df: Machine specifications and tonnage information
            - producing_status_data: Input DataFrame containing production orders currently in MOLDING status
            - pending_status_data: Input DataFrame containing production orders in PAUSED or PENDING status
            - mold_estimated_capacity: Detailed priority molds for each item code with the highest estimated capacity
            - mold_machine_priority_matrix: Ranked mold-machine pairs based on historical weight and actual efficiency
            - priority_order: Priority ordering strategy
            - max_load_threshold: Maximum allowed load threshold. If None, no load constraint is applied (default=30)
            - log_progress_interval: Interval for logging progress during optimization (default=10)
        """

        self._capture_init_args()

        # Initialize logger with class context for better debugging and monitoring
        self.logger = logger.bind(class_="PendingOrderPlanner")

        self.databaseSchemas_data = databaseSchemas_data
        self.sharedDatabaseSchemas_data = sharedDatabaseSchemas_data 

        self.generator_constant_config = generator_constant_config 

        # Check for the newest machine layout
        self.moldInfo_df = moldInfo_df
        self.machineInfo_df = machineInfo_df
        self.machine_info_df = check_newest_machine_layout(self.machineInfo_df)

        self.producing_status_data = producing_status_data
        self.pending_status_data = pending_status_data
        self.mold_machine_priority_matrix = mold_machine_priority_matrix
        self.mold_estimated_capacity_df = mold_estimated_capacity

        self.producing_mold_list = self.producing_status_data['moldNo'].unique().tolist()
        self.producing_info_list = self.producing_status_data[['machineCode', 'moldNo']].drop_duplicates().values.tolist()

        self.priority_order = priority_order
        self.max_load_threshold = max_load_threshold
        self.log_progress_interval = log_progress_interval

        """Initialize all data containers to None"""
        self.mold_lead_times = None
        self.not_matched_pending = None

    def process_planning(self) -> PendingPlannerResult:
        """
        Generate production assignments for pending orders
        """

        self.logger.info("Starting PendingOrderPlanner ...")

        # Generate config header using mixin
        timestamp_start = datetime.now()
        timestamp_str = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
        config_header = self._generate_config_report(timestamp_str)

        planner_log_lines = [config_header]
        planner_log_lines.append("--Processing Summary--")
        planner_log_lines.append(f"⤷ {self.__class__.__name__} results:")

        try:
            # Step 1: Match molds and calculate lead times for pending items 
            (self.mold_lead_times, 
             self.not_matched_pending) = self._prepare_mold_lead_times(self.pending_status_data, 
                                                                       self.mold_estimated_capacity_df)

            # Phase 2: Execute optimization phases
            self.mold_machine_priority_matrix.set_index('moldNo')
            initial_plan, final_assignments, log_str = self._execute_planning_phases(
                self.mold_machine_priority_matrix,
                self.mold_lead_times)
            planner_log_lines.append(f"{log_str}")

            assigned_molds = final_assignments.assignments
            unassigned_molds = final_assignments.unassigned_molds
            overloaded_machines = final_assignments.overloaded_machine
            
            # Log data summary
            planner_log_lines.append("DATA EXPORT SUMMARY")
            planner_log_lines.append(f"⤷ Initial plan: {len(initial_plan)}")
            planner_log_lines.append(f"⤷ Assigned molds: {len(assigned_molds)}")
            planner_log_lines.append(f"⤷ Unassigned molds: {len(unassigned_molds)}")
            planner_log_lines.append(f"⤷ Overloaded machines: {len(overloaded_machines)}")
            planner_log_lines.append(f"⤷ Not matched in pending data: {len(self.not_matched_pending)}")

            # Generate planner summary
            reporter = DictBasedReportGenerator(use_colors=False)
            planner_summary = "\n".join(reporter.export_report({"initial_plan": initial_plan,
                                                                "assigned_molds": assigned_molds,
                                                                "unassigned_molds": unassigned_molds,
                                                                "overloaded_machines": overloaded_machines,
                                                                "not_matched_pending": self.not_matched_pending
                                                                }))
            planner_log_lines.append(f"{planner_summary}")

            self.logger.info("✅ Process finished!!!")

            return PendingPlannerResult(
                initial_plan = initial_plan,
                assigned_molds = assigned_molds,
                unassigned_molds = unassigned_molds,
                overloaded_machines = overloaded_machines,
                not_matched_pending = self.not_matched_pending,
                log_str = "\n".join(planner_log_lines)
                )
            
        except Exception as e:
            self.logger.error("Processing pipeline failed: {}", str(e))
            raise

    #----------------------------------------------------------------#
    # STEP 1: MATCH MOLDS AND CALCULATE LEAD TIMES FOR PENDING ITEMS #
    #----------------------------------------------------------------#
    def _prepare_mold_lead_times(self, 
                                 pending_data: pd.DataFrame,
                                 mold_estimated_capacity: pd.DataFrame
                                 ) -> Tuple[pd.DataFrame, pd.DataFrame]:

        """Match molds with items and calculate lead times"""

        self.logger.info("Preparing mold lead times...")
        
        try:
            mold_lead_times, not_matched_pending = mold_item_plan_a_matching(pending_data, 
                                                                             mold_estimated_capacity)
            self.logger.info("Cannot match item-mold: {}", 
                             len(not_matched_pending) if not_matched_pending is not None else 0)
            
            return mold_lead_times, not_matched_pending
        
        except Exception as e:
            self.logger.error("Failed to prepare mold lead times: {}", str(e))
            raise

    #----------------------------------------------------------------#
    # STEP 2: EXECUTE OPTIMIZATION PHASES                            #
    #----------------------------------------------------------------# 
    def _execute_planning_phases(
            self,
            mold_machine_priority_matrix: pd.DataFrame,
            mold_lead_times: pd.DataFrame
            ) -> Tuple[pd.DataFrame, Any, str]:
        
        """Execute both planning phases and return results"""
        
        self.logger.info("Starting planning phases ...")
        phase_log_lines = []
        
        # Initialize default values
        history_result = None
        compatibility_result = None
        
        # === PHASE 1: History-based (if data available) ===
        if not mold_machine_priority_matrix.empty:
            history_result = self._process_history_based_phase(
                mold_machine_priority_matrix,
                mold_lead_times
            )
            phase_log_lines.append("History-based optimization phase completed successfully!")
            phase_log_lines.append(history_result["phase_log"])
        else:
            phase_log_lines.append("Mold-Machine priority matrix is empty.")
            phase_log_lines.append("History-based optimization phase skipped.")
        
        # === PHASE 2: Compatibility-based (if needed) ===
        should_run_compatibility = (
            history_result is None or  # No history data
            self._should_run_compatibility_optimization(history_result)  # Has unassigned molds
        )
        
        if should_run_compatibility:
            # Prepare inputs for compatibility phase
            if history_result is None:
                # No history → start from scratch
                assigned_matrix = pd.DataFrame(columns=self.machine_info_df['machineCode'])
                assigned_matrix.columns.name = None
                assigned_matrix.index.name = 'moldNo'
                unassigned_molds = self.mold_lead_times['moldNo'].to_list()
                phase_log_lines.append(f"Starting compatibility optimization for {len(unassigned_molds)} unassigned molds")
            else:
                # Has history → continue with unassigned molds
                assigned_matrix = history_result["assigner_result"].assigned_matrix
                unassigned_molds = history_result["assigner_result"].unassigned_molds
            
            self.logger.info("Starting compatibility optimization ...")
            compatibility_result = self._process_compatibility_based_phase(
                assigned_matrix,
                unassigned_molds
            )
            phase_log_lines.append("Compatibility-based optimization phase completed successfully!")
            phase_log_lines.append(compatibility_result["phase_log"])
        
        # === COMPILE FINAL RESULTS ===
        final_summary, final_assignments = self._compile_final_results(
            history_result,
            compatibility_result
        )
        
        self.logger.info("✅ Process finished!!!")
        
        return final_summary, final_assignments, "\n".join(phase_log_lines)

    def _compile_final_results(self,
                               history_result: Optional[Dict],
                               compatibility_result: Optional[Dict]
                               ) -> Tuple[pd.DataFrame, Any]:
        
        """Compile final results from history and compatibility phases"""

        # Case 1: Only compatibility (no history)
        if history_result is None:
            summary = compatibility_result["assignment_summary"].copy()
            summary['Note'] = 'compatibilityBased'
            return summary, compatibility_result["assigner_result"]
        
        # Case 2: Only history (all molds assigned)
        if compatibility_result is None:
            summary = history_result["assignment_summary"].copy()
            summary['Note'] = 'histBased'
            return summary, history_result["assigner_result"]
        
        # Case 3: Both phases (combine results)
        combined_summary = self._combine_assignments(
            history_result["assignment_summary"],
            compatibility_result["assignment_summary"]
        )
        return combined_summary, compatibility_result["assigner_result"]
    
    def _generate_production_schedule(self, 
                                      assigned_matrix: pd.DataFrame, 
                                      mold_lead_times: pd.DataFrame,
                                      pending_data: pd.DataFrame) -> Dict[str, Any]:
        
        """Process assignments and generate summary (human-readable version)"""

        try:

            from agents.autoPlanner.generators.production_schedule_generator import ProductionScheduleGenerator

            generator = ProductionScheduleGenerator(
                assigned_matrix,
                mold_lead_times,
                pending_data,
                self.machine_info_df,
                self.producing_mold_list,
                self.producing_info_list,
                self.generator_constant_config
            )

            return generator.process_generating()

        except Exception as e:
            self.logger.error("Assignment processing failed: {}", str(e))
            raise

    #----------------------------------------------------------------#
    # STEP 2-1: HISTORY-BASED OPTIMIZATION                           #
    #----------------------------------------------------------------#
    def _process_history_based_phase(self, 
                                     mold_machine_priority_matrix: pd.DataFrame,
                                     mold_lead_times: pd.DataFrame
                                     ) -> Dict[str, Any]:
        """Process the history-based optimization phase"""

        self.logger.info("Starting history-based optimization phase ...")
        
        # Run HistoryBasedAssigner
        assigner_result = self._run_history_based_assigner(mold_machine_priority_matrix,
                                                           mold_lead_times)
        
        # Run ProductionScheduleGenerator
        generator_result = self._generate_production_schedule(
            assigner_result.assigned_matrix, 
            self.mold_lead_times, 
            self.pending_status_data
        )

        # Compile phase log
        phase_log_lines = [
            "History-based optimization completed successfully!",
            assigner_result.log,
            "Assignment summarization completed successfully!",
            generator_result["log_str"]]

        self.logger.info("✅ Process finished!!!")

        return {
            "assigner_result": assigner_result,
            "assignment_summary": generator_result["result"],
            "phase_log": "\n".join(phase_log_lines)
            }
    
    def _run_history_based_assigner(self, 
                                    mold_machine_priority_matrix: pd.DataFrame,
                                    mold_lead_times: pd.DataFrame) -> AssignerResult:
        """Run history-based assigner (first tier)"""
        
        self.logger.info("Starting history-based assigner (first tier) ...")
        
        try:
            from agents.autoPlanner.assigners.history_based_assigner import HistoryBasedAssigner
        
            assigner = HistoryBasedAssigner(
                mold_machine_priority_matrix,
                mold_lead_times,
                self.producing_status_data,
                self.machine_info_df,
                self.max_load_threshold
            )

            # Run HistoryBasedAssigner
            results = assigner.run_assign()
            
            self.logger.info(
                "\nHistory-based - Assigned: {} molds, Unassigned: {} molds", 
                len(results.assignments), 
                len(results.unassigned_molds)
            )
            
            return results
            
        except Exception as e:
            self.logger.error("History-based optimization failed: {}", str(e))
            raise

    #----------------------------------------------------------------#
    # STEP 2-2: COMPATIBILITY-BASED OPTIMIZATION                     #
    #----------------------------------------------------------------#
    def _should_run_compatibility_optimization(self, 
                                               history_based_phase_result: Dict[str, Any]) -> bool:
        
        """Determine if compatibility-based optimization should run"""

        unassigned_molds = history_based_phase_result["assigner_result"].unassigned_molds
        unassigned_count = len(unassigned_molds)
            
        return unassigned_count > 0

    def _process_compatibility_based_phase(self, 
                                           hist_assigned_matrix: pd.DataFrame,
                                           hist_unassigned_molds: List) -> Dict[str, Any]:
        
        """Process the compatibility-based optimization phase"""
        
        # Prepare unassigned data
        (unassigned_mold_lead_times, 
         unassigned_pending_data) = self._prepare_unassigned_data(hist_unassigned_molds)
        
        # Run CompatibilityBasedAssigner
        assigner_result = self._run_compatibility_based_assigner(hist_assigned_matrix, 
                                                                 unassigned_mold_lead_times
                                                                 )
    
        # Run ProductionScheduleGenerator
        generator_result = self._generate_production_schedule(
            assigner_result.assigned_matrix,
            unassigned_mold_lead_times,
            unassigned_pending_data
        )

        # Compile phase log
        phase_log_lines = [
            "History-based optimization completed successfully!",
            assigner_result.log,
            "Assignment summarization completed successfully!",
            generator_result["log_str"]]

        self.logger.info("✅ Process finished!!!")
        
        return {
            "assigner_result": assigner_result,
            "assignment_summary": generator_result["result"],
            "phase_log": "\n".join(phase_log_lines)
            }
    
    def _prepare_unassigned_data(self, unassigned_molds: List) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for unassigned molds"""
        unassigned_items = self.mold_lead_times.loc[
            self.mold_lead_times["moldNo"].isin(unassigned_molds), 
            "itemCode"
            ].tolist()
        
        unassigned_mold_lead_times = self.mold_lead_times[
            self.mold_lead_times["moldNo"].isin(unassigned_molds)
            ]
        
        unassigned_pending_data = self.pending_status_data[
            self.pending_status_data["itemCode"].isin(unassigned_items)
            ]
        
        return unassigned_mold_lead_times, unassigned_pending_data

    def _run_compatibility_based_assigner(self, 
                                          assigned_matrix: pd.DataFrame,
                                          unassigned_mold_lead_times: pd.DataFrame
                                          )  -> AssignerResult:
        
        """Run compatibility-based assigner (second tier)"""

        self.logger.info("Running compatibility-based assigner...")
        
        try:
            # Create compatibility matrix
            compatibility_matrix = create_mold_machine_compatibility_matrix(
                self.machineInfo_df, 
                self.moldInfo_df, 
                validate_data=True
            )
            
            from agents.autoPlanner.assigners.compatibility_based_assigner import CompatibilityBasedAssigner

            assigner = CompatibilityBasedAssigner(
                assigned_matrix,
                unassigned_mold_lead_times,
                compatibility_matrix,
                self.priority_order,
                self.max_load_threshold, 
                self.log_progress_interval
            )

            # Run CompatibilityBasedAssigner
            results = assigner.run_assign()
            
            self.logger.info(
                "\nHistory-based - Assigned: {} molds, Unassigned: {} molds", 
                len(results.assignments), 
                len(results.unassigned_molds)
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Compatibility-based optimization failed: {}", str(e))
            raise
    
    def _combine_assignments(self, 
                             hist_based_df: pd.DataFrame, 
                             compatibility_based_df: pd.DataFrame) -> pd.DataFrame:
        """Combine history-based and compatibility-based assignments"""
        try:
            # Add notes to distinguish assignment types
            hist_based_df = hist_based_df.copy()
            compatibility_based_df = compatibility_based_df.copy()
            
            hist_based_df['Note'] = 'histBased'
            compatibility_based_df['Note'] = 'compatibilityBased'
            
            # Validate required columns
            required_cols = ['Machine No.', 'Priority in Machine', 'Machine Code', 'PO Quantity']
            self._validate_assignment_dataframes(hist_based_df, 
                                                 compatibility_based_df, 
                                                 required_cols)
            
            # Calculate priority adjustments
            max_priority_by_machine = hist_based_df.groupby('Machine No.')['Priority in Machine'].max().to_dict()
            compatibility_based_df['Priority in Machine'] += (
                compatibility_based_df['Machine No.'].map(max_priority_by_machine).fillna(0)
            )
            
            # Combine and sort
            combined_df = (
                pd.concat([hist_based_df, compatibility_based_df], ignore_index=True)
                .sort_values(['Machine No.', 'Priority in Machine'])
                .reset_index(drop=True)
            )
            
            # Remove duplicates with zero quantity
            mask_multi = combined_df.groupby('Machine Code')['Machine Code'].transform('count') > 1
            filtered_df = combined_df[~((mask_multi) & (combined_df['PO Quantity'] == 0))]
            
            return filtered_df
            
        except Exception as e:
            self.logger.error("Failed to combine assignments: {}", str(e))
            raise
    
    def _validate_assignment_dataframes(self, 
                                        hist_df: pd.DataFrame, 
                                        comp_df: pd.DataFrame, 
                                        required_cols: List[str]) -> None:
        """Validate assignment DataFrames have required structure"""
        for name, df in [('history-based', hist_df), ('compatibility-based', comp_df)]:
            # Check required columns
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise Exception(f"{name} DataFrame missing columns: {missing_cols}")
            
            # Check for duplicate priorities within machines
            duplicates = df.duplicated(subset=['Machine No.', 'Priority in Machine'])
            if duplicates.any():
                raise Exception(f"{name} DataFrame has duplicate priorities within machines")