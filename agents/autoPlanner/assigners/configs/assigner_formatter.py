import pandas as pd
from typing import List, Dict, Optional
from agents.autoPlanner.assigners.configs.assigner_config import AssignerStats

# HistoryBasedAssigner logging functions
def log_constraint_based_optimization(
        stats: AssignerStats,
        total_molds: int,
        assigned_molds: List[str], 
        unassigned_molds: List[str],
        success_rate: float) -> str:
    
    """Log constraint-based optimization results"""

    log_lines = [
        "=" * 30,
        "ROUND 1 - OPTIMIZATION RESULTS SUMMARY",
        "=" * 30,
        f"Total molds processed: {total_molds}",
        f"Unique matches found: {stats.unique_matches}",
        f"Optimization iterations: {stats.iterations}",
        f"Successfully assigned molds: {len(assigned_molds)}. \nDetails: {assigned_molds}",
        f"Unassigned molds: {len(unassigned_molds)}. \nDetail: {unassigned_molds}",
        f"Success rate: {success_rate:.1f}%",
        f"Total execution time: {stats.duration:.2f} seconds",
        "=" * 30
        ]
    
    return "\n".join(log_lines)

def log_load_balance_based_optimization(
        assigned_molds: List[str],
        unassigned_molds: List[str],
        total_molds: int,
        success_rate: float,
        total_time: float) -> str:
    
    """Log load-balance based optimization results"""

    log_lines = [
        "=" * 30,
        "ROUND 2 - OPTIMIZATION RESULTS SUMMARY",
        "=" * 30,
        f"Successfully assigned molds: {len(assigned_molds)}. \nDetails: {assigned_molds}",
        f"Unassigned molds: {len(unassigned_molds)}. \nDetail: {unassigned_molds}",
        f"Total molds processed: {total_molds}",
        f"Success rate: {success_rate:.1f}%",
        f"Total execution time: {total_time:.2f} seconds",
        "=" * 30
    ]

    return "\n".join(log_lines)

# CompatibilityBasedAssigner logging functions
def log_machine_load(phase: str, 
                     current_load: Dict[str, int], 
                     max_load_threshold: Optional[int]) -> str:
    
    """Log machine load information"""

    log_entries = [f"=== {phase} machine load ==="]

    for machine, load in sorted(current_load.items()):
        if max_load_threshold is not None:
            status = "⚠️ OVERLOAD" if load > max_load_threshold else "✅ OK"
            log_entries.append(f"{machine}: {load} {status}")  
        else:
            log_entries.append(f"{machine}: {load}")

    if max_load_threshold is not None:
        log_entries.append(f"Maximum allowed load: {max_load_threshold}")
        
    return "\n".join(log_entries)

def log_priority_order(priority_df: pd.DataFrame, 
                       priority_order: List[str]) -> str:      
    
    """Log mold priority order"""

    log_lines = ["=== MOLD PRIORITY ORDER ===",
                 f"(by {' > '.join(priority_order)})"]      
    
    display_count = min(15, len(priority_df))

    for i in range(display_count):
        row = priority_df.iloc[i]
        no = row['moldNo']
        machines = row['machine_compatibility']
        lead_time = row['moldLeadTime']
        quantity = row['totalQuantity']
        log_lines.append(
            f"{i+1:2d}. {no}: machines={machines}, leadTime={lead_time}, quantity={quantity:,}"
            )
        
    if len(priority_df) > display_count:
        log_lines.append(f"    ... and {len(priority_df) - display_count} more molds")

    return "\n".join(log_lines)

def log_final_results(stats: AssignerStats, 
                      mold_priorities: List[str],
                      assignments: List[str], 
                      unassigned_molds: List[str],
                      current_load: Dict[str, int], 
                      overloaded_machines: set,
                      max_load_threshold: Optional[int]) -> str:
        
        """Log final optimization results"""

        log_lines = [
            "=" * 50,
            "ROUND 3 - OPTIMIZATION RESULTS SUMMARY",
            "=" * 50,
            f"Successfully assigned molds: {len(assignments)}. \nDetails: {assignments}",
            f"Unassigned molds: {len(unassigned_molds)}. \nDetail: {unassigned_molds}",
            f"Total molds processed: {mold_priorities}",
            f"Success rate: {len(assignments)/len(mold_priorities):.1f}%",
            f"Total execution time: {stats.duration or 0:.2f} seconds",
            "=" * 50
            ]

        if max_load_threshold is not None and overloaded_machines:
            log_lines.append("=== MACHINES SKIPPED DUE TO HIGH LOAD ===")
            for machine in sorted(overloaded_machines):
                log_lines.append(f"{machine}: load = {current_load.get(machine, 0)}")

        machine_load_log_str = log_machine_load("FINAL", 
                                                current_load, 
                                                max_load_threshold)
        log_lines.append(f"{machine_load_log_str}")

        return "\n".join(log_lines)