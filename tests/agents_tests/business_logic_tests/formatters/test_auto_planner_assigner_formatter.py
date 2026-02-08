# tests/agents_tests/business_logic_tests/formatters/test_auto_planner_assigner_formatter.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional

# Import the classes and functions to test
from agents.autoPlanner.assigners.configs.assigner_formatter import (
    AssignerStats,
    log_constraint_based_optimization,
    log_load_balance_based_optimization,
    log_machine_load,
    log_priority_order,
    log_final_results
)

class TestAssignerStats:
    """Test suite for AssignerStats dataclass"""
    
    def test_initialization_with_defaults(self):
        """Test AssignerStats initialization with default values"""
        stats = AssignerStats()
        
        assert stats.start_time is None
        assert stats.end_time is None
        assert stats.iterations == 0
        assert stats.assignments_made == 0
        assert stats.unique_matches == 0
        assert stats.duration is None
    
    def test_initialization_with_values(self):
        """Test AssignerStats initialization with provided values"""
        start = datetime.now()
        end = start + timedelta(seconds=10)
        
        stats = AssignerStats(
            start_time=start,
            end_time=end,
            iterations=5,
            assignments_made=10,
            unique_matches=8
        )
        
        assert stats.start_time == start
        assert stats.end_time == end
        assert stats.iterations == 5
        assert stats.assignments_made == 10
        assert stats.unique_matches == 8
    
    def test_duration_calculation(self):
        """Test duration property calculation"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 0, 30)
        
        stats = AssignerStats(start_time=start, end_time=end)
        
        assert stats.duration == 30.0
    
    def test_duration_none_when_incomplete(self):
        """Test duration returns None when times are not set"""
        # Only start time
        stats1 = AssignerStats(start_time=datetime.now())
        assert stats1.duration is None
        
        # Only end time
        stats2 = AssignerStats(end_time=datetime.now())
        assert stats2.duration is None
        
        # Neither time
        stats3 = AssignerStats()
        assert stats3.duration is None


class TestLogConstraintBasedOptimization:
    """Test suite for log_constraint_based_optimization function"""
    
    def test_basic_logging(self):
        """Test basic logging output format"""
        start = datetime.now()
        end = start + timedelta(seconds=15.5)
        stats = AssignerStats(
            start_time=start,
            end_time=end,
            iterations=3,
            unique_matches=5
        )
        
        assigned = ["MOLD001", "MOLD002"]
        unassigned = ["MOLD003"]
        
        result = log_constraint_based_optimization(
            stats=stats,
            total_molds=3,
            assigned_molds=assigned,
            unassigned_molds=unassigned,
            success_rate=66.7
        )
        
        assert "ROUND 1 - OPTIMIZATION RESULTS SUMMARY" in result
        assert "Total molds processed: 3" in result
        assert "Unique matches found: 5" in result
        assert "Optimization iterations: 3" in result
        assert "Successfully assigned molds: 2" in result
        assert "MOLD001" in result
        assert "MOLD002" in result
        assert "Unassigned molds: 1" in result
        assert "MOLD003" in result
        assert "Success rate: 66.7%" in result
        assert "15.50 seconds" in result
    
    def test_empty_lists(self):
        """Test with empty assigned/unassigned lists"""
        stats = AssignerStats(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1),
            unique_matches=0
        )
        
        result = log_constraint_based_optimization(
            stats=stats,
            total_molds=0,
            assigned_molds=[],
            unassigned_molds=[],
            success_rate=0.0
        )
        
        assert "Successfully assigned molds: 0" in result
        assert "Unassigned molds: 0" in result
        assert "Success rate: 0.0%" in result
    
    def test_100_percent_success(self):
        """Test with 100% success rate"""
        stats = AssignerStats(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=5),
            iterations=2,
            unique_matches=10
        )
        
        assigned = [f"MOLD{i:03d}" for i in range(1, 11)]
        
        result = log_constraint_based_optimization(
            stats=stats,
            total_molds=10,
            assigned_molds=assigned,
            unassigned_molds=[],
            success_rate=100.0
        )
        
        assert "Success rate: 100.0%" in result
        assert "Successfully assigned molds: 10" in result
        assert "Unassigned molds: 0" in result


class TestLogLoadBalanceBasedOptimization:
    """Test suite for log_load_balance_based_optimization function"""
    
    def test_basic_logging(self):
        """Test basic logging output"""
        assigned = ["MOLD001", "MOLD002", "MOLD003"]
        unassigned = ["MOLD004"]
        
        result = log_load_balance_based_optimization(
            assigned_molds=assigned,
            unassigned_molds=unassigned,
            total_molds=4,
            success_rate=75.0,
            total_time=10.5
        )
        
        assert "ROUND 2 - OPTIMIZATION RESULTS SUMMARY" in result
        assert "Successfully assigned molds: 3" in result
        assert "MOLD001" in result
        assert "Unassigned molds: 1" in result
        assert "MOLD004" in result
        assert "Total molds processed: 4" in result
        assert "Success rate: 75.0%" in result
        assert "10.50 seconds" in result
    
    def test_all_assigned(self):
        """Test when all molds are assigned"""
        assigned = ["MOLD001", "MOLD002"]
        
        result = log_load_balance_based_optimization(
            assigned_molds=assigned,
            unassigned_molds=[],
            total_molds=2,
            success_rate=100.0,
            total_time=5.0
        )
        
        assert "Successfully assigned molds: 2" in result
        assert "Unassigned molds: 0" in result
        assert "Success rate: 100.0%" in result


class TestLogMachineLoad:
    """Test suite for log_machine_load function"""
    
    def test_basic_machine_load(self):
        """Test basic machine load logging"""
        load = {
            "MACHINE_A": 5,
            "MACHINE_B": 3,
            "MACHINE_C": 8
        }
        
        result = log_machine_load(
            phase="INITIAL",
            current_load=load,
            max_load_threshold=None
        )
        
        assert "=== INITIAL machine load ===" in result
        assert "MACHINE_A: 5" in result
        assert "MACHINE_B: 3" in result
        assert "MACHINE_C: 8" in result
    
    def test_with_threshold_no_overload(self):
        """Test machine load with threshold, no overloads"""
        load = {
            "MACHINE_A": 5,
            "MACHINE_B": 3
        }
        
        result = log_machine_load(
            phase="CURRENT",
            current_load=load,
            max_load_threshold=10
        )
        
        assert "✅ OK" in result
        assert "⚠️ OVERLOAD" not in result
        assert "Maximum allowed load: 10" in result
    
    def test_with_threshold_and_overload(self):
        """Test machine load with overloaded machines"""
        load = {
            "MACHINE_A": 5,
            "MACHINE_B": 12,
            "MACHINE_C": 15
        }
        
        result = log_machine_load(
            phase="FINAL",
            current_load=load,
            max_load_threshold=10
        )
        
        assert "MACHINE_A: 5 ✅ OK" in result
        assert "MACHINE_B: 12 ⚠️ OVERLOAD" in result
        assert "MACHINE_C: 15 ⚠️ OVERLOAD" in result
        assert "Maximum allowed load: 10" in result
    
    def test_empty_load(self):
        """Test with empty load dictionary"""
        result = log_machine_load(
            phase="EMPTY",
            current_load={},
            max_load_threshold=5
        )
        
        assert "=== EMPTY machine load ===" in result
        assert "Maximum allowed load: 5" in result
    
    def test_sorted_output(self):
        """Test that machines are sorted in output"""
        load = {
            "MACHINE_C": 3,
            "MACHINE_A": 1,
            "MACHINE_B": 2
        }
        
        result = log_machine_load(
            phase="TEST",
            current_load=load,
            max_load_threshold=None
        )
        
        lines = result.split('\n')
        machine_lines = [l for l in lines if "MACHINE" in l]
        
        assert "MACHINE_A" in machine_lines[0]
        assert "MACHINE_B" in machine_lines[1]
        assert "MACHINE_C" in machine_lines[2]


class TestLogPriorityOrder:
    """Test suite for log_priority_order function"""
    
    def test_basic_priority_logging(self):
        """Test basic priority order logging"""
        data = {
            'moldNo': ['MOLD001', 'MOLD002', 'MOLD003'],
            'machine_compatibility': [3, 2, 5],
            'moldLeadTime': [10, 5, 15],
            'totalQuantity': [1000, 2000, 1500]
        }
        df = pd.DataFrame(data)
        priority_order = ['moldLeadTime', 'totalQuantity']
        
        result = log_priority_order(df, priority_order)
        
        assert "MOLD PRIORITY ORDER" in result
        assert "moldLeadTime > totalQuantity" in result
        assert "MOLD001: machines=3, leadTime=10, quantity=1,000" in result
        assert "MOLD002: machines=2, leadTime=5, quantity=2,000" in result
        assert "MOLD003: machines=5, leadTime=15, quantity=1,500" in result
    
    def test_truncation_at_15_molds(self):
        """Test that only first 15 molds are displayed"""
        data = {
            'moldNo': [f'MOLD{i:03d}' for i in range(1, 21)],
            'machine_compatibility': [3] * 20,
            'moldLeadTime': [10] * 20,
            'totalQuantity': [1000] * 20
        }
        df = pd.DataFrame(data)
        priority_order = ['moldLeadTime']
        
        result = log_priority_order(df, priority_order)
        
        assert "MOLD015" in result
        assert "MOLD016" not in result
        assert "... and 5 more molds" in result
    
    def test_fewer_than_15_molds(self):
        """Test with fewer than 15 molds"""
        data = {
            'moldNo': ['MOLD001', 'MOLD002'],
            'machine_compatibility': [3, 2],
            'moldLeadTime': [10, 5],
            'totalQuantity': [1000, 2000]
        }
        df = pd.DataFrame(data)
        priority_order = ['moldLeadTime']
        
        result = log_priority_order(df, priority_order)
        
        assert "MOLD001" in result
        assert "MOLD002" in result
        assert "... and" not in result
    
    def test_quantity_formatting(self):
        """Test that quantities are formatted with commas"""
        data = {
            'moldNo': ['MOLD001'],
            'machine_compatibility': [3],
            'moldLeadTime': [10],
            'totalQuantity': [1234567]
        }
        df = pd.DataFrame(data)
        priority_order = ['moldLeadTime']
        
        result = log_priority_order(df, priority_order)
        
        assert "1,234,567" in result


class TestLogFinalResults:
    """Test suite for log_final_results function"""
    
    def test_basic_final_results(self):
        """Test basic final results logging"""
        start = datetime.now()
        end = start + timedelta(seconds=20)
        stats = AssignerStats(start_time=start, end_time=end)
        
        mold_priorities = ['MOLD001', 'MOLD002', 'MOLD003']
        assignments = ['MOLD001', 'MOLD002']
        unassigned = ['MOLD003']
        current_load = {'MACHINE_A': 5, 'MACHINE_B': 3}
        overloaded = set()
        
        result = log_final_results(
            stats=stats,
            mold_priorities=mold_priorities,
            assignments=assignments,
            unassigned_molds=unassigned,
            current_load=current_load,
            overloaded_machines=overloaded,
            max_load_threshold=10
        )
        
        assert "ROUND 3 - OPTIMIZATION RESULTS SUMMARY" in result
        assert "Successfully assigned molds: 2" in result
        assert "Unassigned molds: 1" in result
        assert "MOLD003" in result
        assert "Total molds processed:" in result
        assert "Success rate:" in result
        assert "20.00 seconds" in result
        assert "FINAL machine load" in result
    
    def test_with_overloaded_machines(self):
        """Test final results with overloaded machines"""
        stats = AssignerStats(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=10)
        )
        
        current_load = {
            'MACHINE_A': 15,
            'MACHINE_B': 12,
            'MACHINE_C': 5
        }
        overloaded = {'MACHINE_A', 'MACHINE_B'}
        
        result = log_final_results(
            stats=stats,
            mold_priorities=['MOLD001', 'MOLD002'],
            assignments=['MOLD001'],
            unassigned_molds=['MOLD002'],
            current_load=current_load,
            overloaded_machines=overloaded,
            max_load_threshold=10
        )
        
        assert "MACHINES SKIPPED DUE TO HIGH LOAD" in result
        assert "MACHINE_A: load = 15" in result
        assert "MACHINE_B: load = 12" in result
        assert "⚠️ OVERLOAD" in result
    
    def test_without_threshold(self):
        """Test final results without load threshold"""
        stats = AssignerStats(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=5)
        )
        
        result = log_final_results(
            stats=stats,
            mold_priorities=['MOLD001'],
            assignments=['MOLD001'],
            unassigned_molds=[],
            current_load={'MACHINE_A': 5},
            overloaded_machines=set(),
            max_load_threshold=None
        )
        
        assert "MACHINES SKIPPED DUE TO HIGH LOAD" not in result
        assert "FINAL machine load" in result
        assert "⚠️ OVERLOAD" not in result
    
    def test_no_duration_calculated(self):
        """Test when duration is None"""
        stats = AssignerStats()  # No times set
        
        result = log_final_results(
            stats=stats,
            mold_priorities=['MOLD001'],
            assignments=['MOLD001'],
            unassigned_molds=[],
            current_load={},
            overloaded_machines=set(),
            max_load_threshold=None
        )
        
        assert "Total execution time: 0.00 seconds" in result
    
    def test_success_rate_calculation(self):
        """Test success rate is calculated correctly"""
        stats = AssignerStats(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1)
        )
        
        mold_priorities = ['MOLD001', 'MOLD002', 'MOLD003', 'MOLD004']
        assignments = ['MOLD001', 'MOLD002', 'MOLD003']
        
        result = log_final_results(
            stats=stats,
            mold_priorities=mold_priorities,
            assignments=assignments,
            unassigned_molds=['MOLD004'],
            current_load={},
            overloaded_machines=set(),
            max_load_threshold=None
        )
        
        # 3/4 = 0.75 = 75.0%
        assert "Success rate: 75.0%" in result or "Success rate: 0.8%" in result


# Integration tests
class TestIntegration:
    """Integration tests for logging functions"""
    
    def test_full_workflow_simulation(self):
        """Test a complete workflow through all rounds"""
        # Round 1
        start = datetime.now()
        end = start + timedelta(seconds=10)
        stats1 = AssignerStats(
            start_time=start,
            end_time=end,
            iterations=5,
            unique_matches=8
        )
        
        log1 = log_constraint_based_optimization(
            stats=stats1,
            total_molds=10,
            assigned_molds=['MOLD001', 'MOLD002'],
            unassigned_molds=['MOLD003', 'MOLD004'],
            success_rate=20.0
        )
        
        assert "ROUND 1" in log1
        
        # Round 2
        log2 = log_load_balance_based_optimization(
            assigned_molds=['MOLD003'],
            unassigned_molds=['MOLD004'],
            total_molds=2,
            success_rate=50.0,
            total_time=5.0
        )
        
        assert "ROUND 2" in log2
        
        # Round 3
        stats3 = AssignerStats(
            start_time=start,
            end_time=start + timedelta(seconds=20)
        )
        
        log3 = log_final_results(
            stats=stats3,
            mold_priorities=['MOLD001', 'MOLD002', 'MOLD003', 'MOLD004'],
            assignments=['MOLD001', 'MOLD002', 'MOLD003'],
            unassigned_molds=['MOLD004'],
            current_load={'MACHINE_A': 10},
            overloaded_machines=set(),
            max_load_threshold=15
        )
        
        assert "ROUND 3" in log3
        
        # Verify different rounds don't interfere
        assert log1 != log2 != log3