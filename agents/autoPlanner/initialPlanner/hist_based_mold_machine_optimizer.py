import pandas as pd
import numpy as np
from loguru import logger
from typing import Tuple, List, Dict
import time

class HistBasedMoldMachineOptimizer:

    """
    Optimized mold-machine assignment algorithm with improved performance and logging.

    This class implements a greedy optimization approach for assigning molds to machines
    based on priority matrices and lead times, prioritizing constrained resources.
    """

    def __init__(self,
                 mold_machine_priority_matrix: pd.DataFrame,
                 mold_lead_times_df: pd.DataFrame,
                 producing_data: pd.DataFrame,
                 machine_info_df: pd.DataFrame,
                 max_load_threshold: int = 30):

        self.logger = logger.bind(class_="HistBasedMoldMachineOptimizer")

        self.mold_machine_priority_matrix = mold_machine_priority_matrix
        self.mold_lead_times_df = mold_lead_times_df
        self.producing_data = producing_data
        self.machine_info_df = machine_info_df
        self.max_load_threshold = max_load_threshold

        self.stats = {
            'start_time': None,
            'iterations': 0,
            'assignments_made': 0,
            'unique_matches': 0
        }

    def run_optimization(self) -> Tuple[pd.DataFrame, List[str], List[str]]:

        """
        Main wrapper function to run the complete optimization process.

        Args:
            mold_machine_priority_matrix: Input priority matrix
            mold_lead_times_df: DataFrame with lead time information
            producing_data: Current production data
            machine_info_df: Machine information DataFrame
            max_load_threshold: Maximum load threshold for round 2

        Returns:
            Tuple of (final_results, all_assigned_molds, final_unassigned_molds)
        """

        self.logger.info("=" * 50)
        self.logger.info("Starting Mold-Machine Optimization Process")
        self.logger.info("=" * 50)

        # Round 1
        round_one_start_time = time.time()

        (round_one_assigned_matrix,
         non_unique_match_priority_matrix,
         unique_match_priority_matrix,
         round_one_assigned_molds,
         round_one_unassigned_molds) = self.constraint_based_optimized()

        # Calculate and log final statistics
        round_one_total_molds = len(non_unique_match_priority_matrix) + len(unique_match_priority_matrix)
        round_one_success_rate = (len(round_one_assigned_molds) / round_one_total_molds * 100) if round_one_total_molds > 0 else 0
        round_one_total_time = time.time() - round_one_start_time

        self.logger.info("=" * 50)
        self.logger.info("ROUND 1 - OPTIMIZATION RESULTS SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info("Total molds processed: {}", round_one_total_molds)
        self.logger.info("Unique matches found: {}", self.stats['unique_matches'])
        self.logger.info("Optimization iterations: {}", self.stats['iterations'])
        self.logger.info("Successfully assigned molds: {}. \nDetails: {}", len(round_one_assigned_molds), round_one_assigned_molds)
        self.logger.info("Unassigned molds: {}. \nDetail: {}", len(round_one_unassigned_molds), round_one_unassigned_molds)
        self.logger.info("Success rate: {:.1f}%", round_one_success_rate)
        self.logger.info("Total execution time: {:.2f} seconds", round_one_total_time)
        self.logger.info("=" * 50)

        # Round 2 (if any unassigned molds remain)
        if len(round_one_unassigned_molds) == 0:
            self.logger.info("Optimization completed")
            round_one_assigned_matrix.index.name = 'moldNo'
            return round_one_assigned_matrix, round_one_assigned_molds, round_one_unassigned_molds
        else:
            round_two_start_time = time.time()
            self.logger.info("Starting optimization process round 2")

            (round_two_assigned_matrix,
             round_two_assigned_molds,
             round_two_unassigned_molds) = self.load_balance_based_optimized(round_one_unassigned_molds,
                                                                             round_one_assigned_matrix)

            # Combine results from both rounds
            final_assigned_matrix = pd.concat([round_one_assigned_matrix, round_two_assigned_matrix], axis=0)
            final_assigned_matrix.index.name = 'moldNo'
            all_assigned_molds = round_one_assigned_molds + round_two_assigned_molds

            round_two_total_molds = len(round_two_assigned_molds) + len(round_two_unassigned_molds)
            round_two_success_rate = (len(round_two_assigned_molds) / round_two_total_molds * 100) if round_two_total_molds > 0 else 0
            round_two_total_time = time.time() - round_two_start_time

            self.logger.info("=" * 50)
            self.logger.info("ROUND 2 - OPTIMIZATION RESULTS SUMMARY")
            self.logger.info("=" * 50)
            self.logger.info("Successfully assigned molds: {}. \nDetails: {}", len(round_two_assigned_molds), round_two_assigned_molds)
            self.logger.info("Unassigned molds: {}. \nDetail: {}", len(round_two_unassigned_molds), round_two_unassigned_molds)
            self.logger.info("Total molds processed: {}", round_two_total_molds)
            self.logger.info("Success rate: {:.1f}%", round_two_success_rate)
            self.logger.info("Total execution time: {:.2f} seconds", round_two_total_time)
            self.logger.info("=" * 50)

            return final_assigned_matrix, all_assigned_molds, round_two_unassigned_molds
        
    
    ###############################################
    # Round 1: Constraint-Based Greedy Assignment #
    ###############################################
    
    def constraint_based_optimized(self):

        """
        Round 1: Constraint-Based Greedy Assignment

        This function performs the first phase of mold-to-machine optimization using
        a greedy strategy that prioritizes constrained resources.

        - Unique Match Processing: Identifies molds with only one compatible machine
        - Constrained Resource Prioritization: Focuses on machines with minimal assignment options
        - Iterative Assignment: Repeatedly assigns molds and updates matrices to reflect progress

        Args:
            mold_lead_time_df (pd.DataFrame): DataFrame containing lead time info (moldNo, moldLeadTime)
            mold_machine_priority_matrix (pd.DataFrame): Mold-machine compatibility matrix

        Returns:
            round_one_results (pd.DataFrame): Assignment matrix after round 1
            non_unique_match_priority_matrix (pd.DataFrame): Remaining priority matrix after unique matches removed
            unique_match_priority_matrix (pd.DataFrame): Priority matrix of molds with only one matching machine
            round_one_assigned_molds (List[str]): List of assigned molds in round 1
            round_one_unassigned_molds (List[str]): Molds not assigned in round 1
        """

        # Phase 1: Handle molds with exactly one matching machine

        self.logger.info("Phase 1: Processing unique matches")

        (unique_match_list,
        unique_match_priority_matrix,
        non_unique_match_priority_matrix) = self.find_unique_matches(self.mold_lead_times_df, 
                                                                     self.mold_machine_priority_matrix)

        # Phase 2: Perform greedy assignment for remaining molds,
        # prioritizing machines with few compatible options

        self.logger.info("Phase 2: Optimizing remaining assignments")

        results, round_one_assigned_molds, round_one_unassigned_molds, final_matrix = self.optimize_mold_machine_matching(
            non_unique_match_priority_matrix, self.mold_lead_times_df
        )

        # Include uniquely matched molds into the assigned list
        round_one_assigned_molds.extend(unique_match_list)

        # Merge results from unique matches and greedy optimization
        if not unique_match_priority_matrix.empty:
            # Convert unique matches to leadtime format and combine
            unique_match_leadtime_matrix = self.create_leadtime_matrix(
                self.create_binary_priority_matrix(unique_match_priority_matrix),
                self.mold_lead_times_df
            )
            results = pd.concat([results, unique_match_leadtime_matrix], axis=0)

        round_one_assigned_matrix = results[~(results == 0).all(axis=1)]

        return round_one_assigned_matrix, non_unique_match_priority_matrix, unique_match_priority_matrix, round_one_assigned_molds, round_one_unassigned_molds
    
    def find_unique_matches(self,
                            mold_lead_time_df: pd.DataFrame,
                            mold_machine_priority_matrix: pd.DataFrame) -> Tuple[List[str], pd.DataFrame, pd.DataFrame]:

        """
        Identify and separate molds that have unique machine matches.

        Args:
            mold_lead_time_df: DataFrame with lead time information
            mold_machine_priority_matrix: Priority matrix

        Returns:
            Tuple of (unique_match_list, unique_matrix, non_unique_matrix)
        """

        self.logger.debug("Finding unique matches")

        unique_matched_list = []

        # Filter for valid molds only
        valid_mold_nos = set(mold_lead_time_df['moldNo'])
        filtered_priority_matrix = mold_machine_priority_matrix[mold_machine_priority_matrix.index.isin(valid_mold_nos)].copy()

        # Pre-compute lead time mapping
        mold_leadtime_mapping = dict(zip(mold_lead_time_df['moldNo'], mold_lead_time_df['moldLeadTime']))

        # Calculate total compatible machines per mold efficiently
        machine_count = (filtered_priority_matrix != 0).sum(axis=1)
        unique_molds = machine_count[machine_count == 1].index

        # Process unique matches
        for mold_no in unique_molds:
            # Find the single compatible machine
            compatible_machine = filtered_priority_matrix.loc[mold_no][filtered_priority_matrix.loc[mold_no] != 0].index[0]
            leadtime = mold_leadtime_mapping.get(mold_no)
            if leadtime is not None:
                unique_matched_list.append(mold_no)

        # Split matrices
        unique_matched_priority_matrix = filtered_priority_matrix.loc[unique_matched_list] if unique_matched_list else pd.DataFrame()
        non_unique_matched_priority_matrix = filtered_priority_matrix.drop(index=unique_matched_list)

        self.stats['unique_matches'] = len(unique_matched_list)
        self.logger.info("Found {} unique matches", len(unique_matched_list))

        return unique_matched_list, unique_matched_priority_matrix, non_unique_matched_priority_matrix
    
    def optimize_mold_machine_matching(self, 
                                       mold_machine_priority_matrix: pd.DataFrame,
                                       mold_lead_time_df: pd.DataFrame) -> Tuple[pd.DataFrame,
                                                                            List[str], List[str],
                                                                            pd.DataFrame]:

        """
        Main optimization algorithm with improved performance and logging.

        Args:
            mold_machine_priority_matrix: Initial priority matrix
            mold_lead_time_df: DataFrame with lead time information

        Returns:
            Tuple of (assigned_matrix, assigned_molds, unassigned_molds, final_leadtime_matrix)
        """

        self.logger.info("Starting mold-machine optimization")
        self.stats['start_time'] = time.time()

        # Step 1: Create binary priority matrix
        binary_priority_matrix = self.create_binary_priority_matrix(mold_machine_priority_matrix)

        # Step 2: Create lead time matrix
        mold_leadtime_matrix = self.create_leadtime_matrix(binary_priority_matrix, mold_lead_time_df)

        # Step 3: Initialize assigned matrix with optimal dtype
        assigned_matrix = pd.DataFrame(
            data=0,
            index=mold_machine_priority_matrix.index,
            columns=mold_machine_priority_matrix.columns,
            dtype='int32'
        )

        # Pre-compute lead time mapping for efficiency
        mold_leadtime_mapping = dict(zip(mold_lead_time_df['moldNo'], mold_lead_time_df['moldLeadTime']))

        all_assigned_pairs = []
        max_iterations = min(len(mold_machine_priority_matrix) * 2, 1000)  # Reasonable limit

        self.logger.info("Starting optimization loop with max {} iterations", max_iterations)

        # Main optimization loop - prioritize constrained machines
        while self.stats['iterations'] < max_iterations:

            # Find valid pairs with machines having exactly 1 suitable mold
            valid_pairs = self.find_valid_pairs(mold_leadtime_matrix, mold_leadtime_mapping, target_suitable_count=1)

            if not valid_pairs:
                self.logger.debug("No more valid pairs found, terminating optimization")
                break

            # Assign molds to machines
            valid_pairs, assigned_matrix, mold_leadtime_matrix = self.assign_molds_to_machines(
                valid_pairs, assigned_matrix, mold_leadtime_matrix
            )

            all_assigned_pairs.extend(valid_pairs)
            self.stats['iterations'] += 1

            if self.stats['iterations'] % 10 == 0:
                self.logger.debug("Completed {} iterations, {} assignments made",
                                  self.stats['iterations'], len(all_assigned_pairs))

        # Classify results
        assigned_molds = list(set([mold for mold, _, _ in all_assigned_pairs]))
        remaining_molds = mold_leadtime_matrix[mold_leadtime_matrix.sum(axis=1) > 0].index.tolist()

        elapsed_time = time.time() - self.stats['start_time']

        self.logger.info("Optimization completed in {:.2f}s, {} iterations", elapsed_time, self.stats['iterations'])
        self.logger.info("Assigned {} molds, {} remain unassigned", len(assigned_molds), len(remaining_molds))

        return assigned_matrix, assigned_molds, remaining_molds, mold_leadtime_matrix

    def find_valid_pairs(self,
                         mold_leadtime_matrix: pd.DataFrame,
                         mold_leadtime_mapping: Dict[str, int],
                         target_suitable_count: int = 1) -> List[Tuple[str, str, int]]:

        """
        Find valid (mold, machine) pairs based on machine constraints.

        Args:
            mold_leadtime_matrix: Current lead time matrix
            mold_leadtime_mapping: Pre-computed mapping of mold to lead time
            target_suitable_count: Target number of suitable molds per machine

        Returns:
            List of valid (moldNo, machineCode, leadTime) tuples
        """

        # Calculate statistics efficiently
        suitable_count, _ = self.calculate_machine_statistics(mold_leadtime_matrix)

        # Find machines with target suitable count
        target_machines = suitable_count[suitable_count == target_suitable_count].index

        if len(target_machines) == 0:
            return []

        valid_pairs = []

        # Only iterate through target machines for efficiency
        for machine in target_machines:
            # Find the single compatible mold for this machine
            compatible_molds = mold_leadtime_matrix[mold_leadtime_matrix[machine] > 0].index

            for mold in compatible_molds:
                leadtime = mold_leadtime_mapping.get(mold)
                if leadtime is not None:
                    valid_pairs.append((mold, machine, int(leadtime)))

        self.logger.debug("Found {} valid pairs with target count {}",
                          len(valid_pairs), target_suitable_count)

        return valid_pairs
    
    def assign_molds_to_machines(self,
                                 valid_mold_machine_pairs: List[Tuple[str, str, int]],
                                 assigned_matrix: pd.DataFrame,
                                 mold_leadtime_matrix: pd.DataFrame) -> Tuple[List[Tuple[str, str, int]],
                                                                         pd.DataFrame, pd.DataFrame]:

        """
        Assign molds to machines and update matrices efficiently.

        Args:
            valid_mold_machine_pairs: List of valid assignments
            assigned_matrix: Mold-machine matrix to update
            mold_leadtime_matrix: Lead time matrix to modify

        Returns:
            Tuple of (valid_pairs, updated_assigned_matrix, updated_leadtime_matrix)
        """

        if not valid_mold_machine_pairs:
            return valid_mold_machine_pairs, assigned_matrix, mold_leadtime_matrix

        # Batch update assigned matrix
        for mold, machine, leadtime in valid_mold_machine_pairs:
            if mold in assigned_matrix.index and machine in assigned_matrix.columns:
                assigned_matrix.loc[mold, machine] = leadtime

        # Efficiently remove assigned molds using vectorized operation
        assigned_molds = [mold for mold, _, _ in valid_mold_machine_pairs]
        if assigned_molds:
            mold_leadtime_matrix.loc[assigned_molds] = 0

        self.stats['assignments_made'] += len(valid_mold_machine_pairs)
        self.logger.debug("Assigned {} molds to machines", len(valid_mold_machine_pairs))

        return valid_mold_machine_pairs, assigned_matrix, mold_leadtime_matrix
    
    def create_leadtime_matrix(self,
                               mold_machine_binary_priority: pd.DataFrame,
                               mold_lead_time_df: pd.DataFrame) -> pd.DataFrame:

        """
        Create lead time matrix by multiplying binary priority with corresponding lead times.

        Args:
            binary_priority: Binary compatibility matrix
            mold_lead_time_df: DataFrame containing moldNo and moldLeadTime columns

        Returns:
            Lead mold time matrix with adjusted values
        """

        self.logger.debug("Creating lead time matrix")

        # Create efficient mapping using dictionary for O(1) lookup
        mold_leadtime_mapping = dict(zip(mold_lead_time_df['moldNo'], mold_lead_time_df['moldLeadTime']))

        # Use vectorized operations for better performance
        mold_leadtime_series = pd.Series([mold_leadtime_mapping.get(idx, 0) for idx in mold_machine_binary_priority.index],
                                    index=mold_machine_binary_priority.index, dtype='int32')

        # Multiply each row by corresponding lead time using broadcasting
        mold_leadtime_matrix = mold_machine_binary_priority.mul(mold_leadtime_series, axis=0).astype('int32')

        self.logger.debug("Lead time matrix created with {} non-zero entries", 
                          (mold_leadtime_matrix > 0).sum().sum())

        return mold_leadtime_matrix
    
    @staticmethod
    def create_binary_priority_matrix(mold_machine_priority_matrix: pd.DataFrame) -> pd.DataFrame:

        """
        Convert priority matrix to binary format (0 and 1 only).

        Args:
            priority_matrix: Input priority matrix with various values

        Returns:
            Binary matrix where 1 indicates compatibility, 0 indicates incompatibility
        """

        logger.debug("Converting priority matrix of shape {} to binary", mold_machine_priority_matrix.shape)

        return (mold_machine_priority_matrix == 1).astype(np.int8)  # Use int8 for memory efficiency
    
    @staticmethod
    def calculate_machine_statistics(mold_leadtime_matrix: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:

        """
        Calculate statistics for each machine efficiently without copying the entire matrix.

        Args:
            mold_leadtime_matrix: Matrix containing lead times

        Returns:
            Tuple of (suitable_count, total_leadtime) series
        """

        # Use vectorized operations for better performance
        suitable_count = (mold_leadtime_matrix > 0).sum(axis=0)
        total_leadtime = mold_leadtime_matrix.sum(axis=0)

        logger.debug("Calculated statistics for {} machines", len(suitable_count))

        return suitable_count, total_leadtime


    ###############################################
    #      Round 2: Load-Balanced Assignment      #
    ###############################################

    def load_balance_based_optimized(self,
                                     round_one_unassigned_molds: List,
                                     round_one_assigned_matrix: pd.DataFrame):

        """
        Round 2: Load-Balanced Assignment

        Assign moldNo to machineCode with real-time updates of candidateMachineLoad
        and a maximum machine load constraint.

        - Machine Load Calculation: Combines current production + pending assignments
        - Threshold-Based Selection: Respects maximum load constraints (default: 30 days)
        - Real-Time Updates: Continuously recalculates machine loads during assignment

        Args:
            round_one_unassigned_molds: List of mold numbers that need to be assigned.
            mold_lead_times_df: DataFrame containing lead time for molds.
            producing_data: DataFrame of ongoing or past production info.
            machine_info_df: DataFrame containing static machine information.
            round_one_assigned_matrix: DataFrame containing prior assignment results.
            priority_matrix: Matrix indicating machine suitability/priority for each mold.
            max_load_threshold: Maximum allowed load per machine (default: 30 days).

        Returns:
            assigned_df: DataFrame with optimized mold-to-machine assignments.
            assigned_molds: List of molds that were successfully assigned.
            unassigned_molds: List of molds that couldn't be assigned under the threshold.
        """

        assigned_molds = []
        unassigned_molds = []

        # Step 1: Compute current machine load
        total_machine_load_df = HistBasedMoldMachineOptimizer._update_total_machine_load(self.producing_data,
                                                                                         round_one_assigned_matrix,
                                                                                         self.machine_info_df)

        # Step 2: Create lead time matrix for unassigned molds and candidate machines
        candidate_lead_time_matrix = HistBasedMoldMachineOptimizer._create_candidate_lead_time_matrix(self.mold_machine_priority_matrix,
                                                                                                      round_one_unassigned_molds,
                                                                                                      self.mold_lead_times_df)
        
        # Combine into working result_df
        round_two_info_df = pd.concat([total_machine_load_df, candidate_lead_time_matrix], axis=0)
        result_df = round_two_info_df.copy()
        result_df.loc['candidateMachineLoad'] = result_df.sum(numeric_only=True)

        # Extract components from result_df
        machine_load_df = result_df.loc[['machineLoad']]
        leadtime_df = result_df.drop(index=['machineLoad', 'candidateMachineLoad'])
        current_candidate_load = result_df.loc[['candidateMachineLoad']].copy()
        assigned_df = leadtime_df.copy()

        self.logger.info("Starting mold assignment with real-time load updates...")
        self.logger.info("Max load threshold: {} days", self.max_load_threshold)
        self.logger.info("Initial Candidate Machine Load:\n{}\n",
                         current_candidate_load.loc['candidateMachineLoad'].to_dict())

        # Iterate over each moldNo to assign
        for moldNo in leadtime_df.index:
            row = leadtime_df.loc[moldNo]

            # Filter machines with valid leadtime > 0
            available_machines = row[row > 0].index.tolist()

            if not available_machines:
                unassigned_molds.append(moldNo)
                self.logger.warning("No available machine for {}", moldNo)
                continue

            # Only include machines that exist in both available_machines and current_candidate_load.columns
            valid_machines = [m for m in available_machines if m in current_candidate_load.columns]
            
            if not valid_machines:
                unassigned_molds.append(moldNo)
                self.logger.warning("No valid machine in candidate load for {}", moldNo)
                continue

            # Load values of available machines
            available_loads = current_candidate_load[available_machines].loc['candidateMachineLoad']
            sorted_machines = available_loads.sort_values().index.tolist()

            self.logger.debug("{}:", moldNo)
            self.logger.debug("- Available machines (sorted by load): {}", sorted_machines)
            self.logger.debug("- Corresponding loads: {}", [available_loads[m] for m in sorted_machines])

            selected_machine = None
            selected_load = None

            # Try assigning to the best available machine under threshold
            for machine in sorted_machines:
                machine_load = available_loads[machine]
                mold_leadtime = row[machine]
                projected_load = machine_load + mold_leadtime

                self.logger.debug("- Trying machine {}: current load = {}, leadtime = {}",
                                  machine, machine_load, mold_leadtime)
                self.logger.debug("→ Projected load after assignment = {}", projected_load)

                if projected_load <= self.max_load_threshold:
                    selected_machine = machine
                    selected_load = machine_load
                    self.logger.debug("✓ Selected machine {} - {} days (projected load: {} ≤ {})",
                                      selected_machine, selected_load, projected_load, self.max_load_threshold)
                    break
                else:
                    self.logger.debug("✗ Skipped machine {} (projected load: {} > {})",
                                      machine, projected_load, self.max_load_threshold)

            # If no machine meets threshold, assign to the one with the lowest load
            if selected_machine is None:
                selected_machine = sorted_machines[0]
                selected_load = available_loads[selected_machine]
                self.logger.debug("⚠ No machine ≤ {} days, choosing best option: {} - {} days",
                                  self.max_load_threshold, selected_machine, selected_load)

            # Update assigned_df: keep only selected machine's leadtime, others set to 0
            assigned_molds.append(moldNo)
            mold_leadtime = assigned_df.loc[moldNo, selected_machine]
            for col in leadtime_df.columns:
                if col != selected_machine:
                    assigned_df.at[moldNo, col] = 0

            self.logger.debug("- Leadtime kept for {} on {}: {}\nDetails: {}\n",
                              moldNo, selected_machine, mold_leadtime, assigned_df.loc[moldNo].to_dict())

            # Update candidateMachineLoad in real-time
            current_candidate_load.loc['candidateMachineLoad'] = (
                machine_load_df.loc['machineLoad'] + assigned_df.sum(numeric_only=True)
            )

            self.logger.debug("- Updated Candidate Load:\n{}\n",
                              current_candidate_load.loc['candidateMachineLoad'].to_dict())

        # Combine final result
        final_result = pd.concat([machine_load_df, assigned_df], axis=0)
        final_result.loc['candidateMachineLoad'] = current_candidate_load.loc['candidateMachineLoad']

        self.logger.info("=== FINAL RESULT ===")
        self.logger.info("Final Candidate Machine Load:\n{}\n",
                         final_result.loc['candidateMachineLoad'].to_dict())

        return assigned_df, assigned_molds, unassigned_molds
    
    @staticmethod
    def _calculate_machine_load(df: pd.DataFrame):

        """Calculate machine load from DataFrame."""

        machine_load = df.sum(numeric_only=True).to_frame().T
        machine_load.index = ['machineLoad']

        return machine_load
    
    @staticmethod
    def _update_total_machine_load(producing_df: pd.DataFrame,
                                   pending_leadtime_df: pd.DataFrame,
                                   machine_info_df: pd.DataFrame):

        """Update total machine load with producing and pending data."""

        producing_machine_load_df = HistBasedMoldMachineOptimizer._create_producing_machine_load(producing_df, machine_info_df)
        pending_machine_load_df = HistBasedMoldMachineOptimizer._calculate_machine_load(pending_leadtime_df)

        return producing_machine_load_df + pending_machine_load_df
    
    @staticmethod
    def _create_producing_machine_load(producing_df: pd.DataFrame,
                                       machine_info_df: pd.DataFrame):

        """Create machine load matrix from producing data."""

        machine_list = machine_info_df['machineCode'].unique().tolist()
        data = HistBasedMoldMachineOptimizer._convert_producing_leadtime(producing_df)

        unique_moldNo = sorted({row[0] for row in data})
        df = pd.DataFrame(0, index=unique_moldNo, columns=machine_list)

        for moldNo, machineCode, leadtime in data:
            df.loc[moldNo, machineCode] = leadtime

        return HistBasedMoldMachineOptimizer._calculate_machine_load(df)
    
    @staticmethod
    def _convert_producing_leadtime(df: pd.DataFrame):

        """Convert producing data to leadtime format."""

        df = df.copy()
        df['remainTime'] = (df['remainTime'].dt.total_seconds() / 86400).round().astype('int')  # Convert to days
        return list(df[['itemCode', 'machineCode', 'remainTime']].itertuples(index=False, name=None))

    @staticmethod
    def _create_candidate_lead_time_matrix(mold_machine_priority_matrix: pd.DataFrame,
                                           unassigned_molds: List,
                                           mold_lead_times_df: pd.DataFrame):

        """Create candidate lead time matrix for unassigned molds."""

        updated_priority_matrix = mold_machine_priority_matrix[mold_machine_priority_matrix.index.isin(unassigned_molds)].copy()

        binary_priority = (updated_priority_matrix > 0).astype(int)

        best_leadtime_map = mold_lead_times_df.set_index('moldNo')['moldLeadTime']
        best_leadtime_matrix = binary_priority.multiply(best_leadtime_map, axis=0).fillna(0).astype('Int64')

        candidate_lead_time_matrix = best_leadtime_matrix[~(best_leadtime_matrix == 0).all(axis=1)]
         
        return candidate_lead_time_matrix