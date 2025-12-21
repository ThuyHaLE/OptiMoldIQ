from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

# CompatibilityBasedAssigner helper functions
def find_best_machine(suitable_machines: List[str],
                      current_load: Dict[str, int],
                      max_load_threshold: Optional[int] = None
                      ) -> Optional[str]:
    
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
    
def update_machine_dataframe_optimized(machine_df: pd.DataFrame,
                                       machine_code: str,
                                       mold_id: str,
                                       lead_time: int
                                       ) -> pd.DataFrame:
    
    """Update machine DataFrame with new assignment (optimized version)"""
    
    df = machine_df.copy()
    
    # Create new row efficiently
    new_row_data = {col: 0 for col in df.columns}
    new_row_data[machine_code] = lead_time
    
    new_row_df = pd.DataFrame([new_row_data], index=[mold_id])
    
    # Concatenate efficiently
    df = pd.concat([df, new_row_df], ignore_index=False)
    
    return df

# HistoryBasedAssigner helper functions
def create_binary_priority_matrix(
        mold_machine_priority_matrix: pd.DataFrame) -> pd.DataFrame:

    """Convert priority matrix to binary format (0 and 1 only)."""

    return (mold_machine_priority_matrix == 1).astype(np.int8)  # Use int8 for memory efficiency

def calculate_machine_statistics(mold_leadtime_matrix: pd.DataFrame
                                 ) -> Tuple[pd.Series, pd.Series]:
    
    """Calculate statistics for each machine efficiently without copying the entire matrix."""

    # Use vectorized operations for better performance
    suitable_count = (mold_leadtime_matrix > 0).sum(axis=0)
    total_leadtime = mold_leadtime_matrix.sum(axis=0)

    return suitable_count, total_leadtime

def calculate_machine_load(df: pd.DataFrame) -> pd.DataFrame:

    """Calculate machine load from DataFrame."""

    machine_load = df.sum(numeric_only=True).to_frame().T
    machine_load.index = ['machineLoad']

    return machine_load

def create_producing_machine_load(producing_df: pd.DataFrame,
                                  machine_info_df: pd.DataFrame
                                  ) -> pd.DataFrame:

    """Create machine load matrix from producing data."""

    machine_list = machine_info_df['machineCode'].unique().tolist()
    data = convert_producing_leadtime(producing_df)

    unique_moldNo = sorted({row[0] for row in data})
    df = pd.DataFrame(0, index=unique_moldNo, columns=machine_list)

    for moldNo, machineCode, leadtime in data:
        df.loc[moldNo, machineCode] = leadtime

    return calculate_machine_load(df)

def update_total_machine_load(producing_df: pd.DataFrame,
                              pending_leadtime_df: pd.DataFrame,
                              machine_info_df: pd.DataFrame
                              ) -> pd.DataFrame:

    """Update total machine load with producing and pending data."""

    producing_machine_load_df = create_producing_machine_load(producing_df, machine_info_df)
    pending_machine_load_df = calculate_machine_load(pending_leadtime_df)

    return producing_machine_load_df + pending_machine_load_df

def convert_producing_leadtime(df: pd.DataFrame
                               ) -> List[Tuple[str, str, int]]:

    """Convert producing data to leadtime format."""

    df = df.copy()

    df['remainTime'] = pd.to_timedelta(df['remainTime'], unit='hours', errors='coerce')
    df['remainTime'] = (df['remainTime'].dt.total_seconds() / 86400).round().astype('int')  # Convert to days

    return list(df[['itemCode', 'machineCode', 'remainTime']].itertuples(index=False, name=None))

def create_candidate_lead_time_matrix(mold_machine_priority_matrix: pd.DataFrame,
                                      unassigned_molds: List,
                                      mold_lead_times_df: pd.DataFrame
                                      ) -> pd.DataFrame:

    """Create candidate lead time matrix for unassigned molds."""

    updated_priority_matrix = mold_machine_priority_matrix[
        mold_machine_priority_matrix.index.isin(unassigned_molds)].copy()
    
    binary_priority = (updated_priority_matrix > 0).astype(int)

    best_leadtime_map = mold_lead_times_df.set_index('moldNo')['moldLeadTime']

    best_leadtime_matrix = binary_priority.multiply(best_leadtime_map, axis=0).fillna(0).astype('Int64')

    candidate_lead_time_matrix = best_leadtime_matrix[~(best_leadtime_matrix == 0).all(axis=1)]

    return candidate_lead_time_matrix