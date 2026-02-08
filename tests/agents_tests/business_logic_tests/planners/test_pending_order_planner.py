# tests/agents_tests/business_logic_tests/planners/test_pending_order_planner.py

"""
Simple, direct tests for PendingOrderPlanner
Focus on testing actual logic, minimal mocking
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock

from agents.autoPlanner.phases.initialPlanner.pending_order_planner import (
    PendingOrderPlanner, PendingPlannerResult)
from agents.autoPlanner.tools.machine_processing import check_newest_machine_layout

# ============================================================================
# BONUS: Test check_newest_machine_layout (pure function, no mock needed)
# ============================================================================

class TestCheckNewestMachineLayout:
    """Test the machine layout filter - pure function"""
    
    def test_filters_null_end_date(self):
        """Should keep only rows where layoutEndDate is null"""
        df = pd.DataFrame({
            'machineNo': ['M1', 'M2', 'M3'],
            'machineCode': ['MC1', 'MC2', 'MC3'],
            'layoutEndDate': [None, '2024-01-01', None]
        })
        
        result = check_newest_machine_layout(df)
        
        assert len(result) == 2
        assert 'M1' in result['machineNo'].values
        assert 'M3' in result['machineNo'].values
        assert 'M2' not in result['machineNo'].values
    
    def test_returns_empty_if_input_empty(self):
        """Should return empty df if input is empty"""
        df = pd.DataFrame()
        result = check_newest_machine_layout(df)
        assert result.empty
    
    def test_filters_only_available_fields(self):
        """Should only return machine info fields that exist"""
        df = pd.DataFrame({
            'machineNo': ['M1'],
            'machineCode': ['MC1'],
            'extraField': ['extra'],  # Should be filtered out
            'layoutEndDate': [None]
        })
        
        result = check_newest_machine_layout(df)
        
        assert 'machineNo' in result.columns
        assert 'machineCode' in result.columns
        assert 'extraField' not in result.columns
    
    def test_works_without_layoutEndDate_column(self):
        """Should work even if layoutEndDate doesn't exist"""
        df = pd.DataFrame({
            'machineNo': ['M1', 'M2'],
            'machineCode': ['MC1', 'MC2']
        })
        
        result = check_newest_machine_layout(df)
        
        # Should return all rows
        assert len(result) == 2


# ============================================================================
# SIMPLE FIXTURES - Just real data
# ============================================================================

@pytest.fixture
def schemas():
    """Schemas matching actual data structure after check_newest_machine_layout"""
    return {
        'databaseSchemas': {
            'staticDB': {
                'machineInfo': {
                    'dtypes': {
                        'machineNo': 'object',
                        'machineCode': 'object',
                        'machineName': 'object',
                        'manufacturerName': 'object',
                        'machineTonnage': 'int64',
                        'tonnage': 'int64',
                        'maxLoad': 'int64',
                        'status': 'object',
                        'layoutEndDate': 'object'
                    }
                },
                'moldInfo': {
                    'dtypes': {
                        'moldNo': 'object', 
                        'tonnage': 'int64',
                        'cavity': 'int64'
                    }
                }
            }
        },
        'sharedSchemas': {
            'machine_info': {
                'dtypes': {
                    # check_newest_machine_layout filters to these fields
                    'machineNo': 'object',
                    'machineCode': 'object', 
                    'machineName': 'object',
                    'manufacturerName': 'object',
                    'machineTonnage': 'int64'
                }
            },
            'mold_estimated_capacity': {
                'dtypes': {
                    'moldNo': 'object', 
                    'itemCode': 'object',
                    'estimatedCapacity': 'float64'
                }
            },
            'producing_data': {
                'dtypes': {
                    'machineCode': 'object', 
                    'moldNo': 'object',
                    'itemCode': 'object',
                    'quantity': 'int64'
                }
            },
            'pending_data': {
                'dtypes': {
                    'itemCode': 'object', 
                    'quantity': 'int64',
                    'priority': 'int64'
                }
            }
        }
    }


@pytest.fixture
def simple_data():
    """Real data with ALL required columns for validation"""
    # machineInfo_df needs these columns for staticDB validation
    # machine_info_df (after check_newest_machine_layout) needs these for shared validation
    machines = pd.DataFrame({
        'machineNo': ['M1', 'M2', 'M3'],
        'machineCode': ['M1', 'M2', 'M3'],
        'machineName': ['Machine 1', 'Machine 2', 'Machine 3'],
        'manufacturerName': ['Maker A', 'Maker B', 'Maker C'],
        'machineTonnage': [100, 150, 200],
        'tonnage': [100, 150, 200],
        'maxLoad': [30, 30, 30],
        'status': ['active', 'active', 'active'],
        'layoutEndDate': [None, None, None]  # For check_newest_machine_layout
    })
    
    molds = pd.DataFrame({
        'moldNo': ['MOLD1', 'MOLD2', 'MOLD3'],
        'tonnage': [90, 140, 190],
        'cavity': [4, 8, 12]
    })
    
    producing = pd.DataFrame({
        'machineCode': ['M1'],
        'moldNo': ['MOLD1'],
        'itemCode': ['ITEM1'],
        'quantity': [1000]
    })
    
    pending = pd.DataFrame({
        'itemCode': ['ITEM2', 'ITEM3'],
        'quantity': [2000, 3000],
        'priority': [1, 2]
    })
    
    capacity = pd.DataFrame({
        'moldNo': ['MOLD2', 'MOLD3'],
        'itemCode': ['ITEM2', 'ITEM3'],
        'estimatedCapacity': [100.0, 120.0]
    })
    
    priority_matrix = pd.DataFrame(
        [[0.9, 0.7, 0.5], [0.8, 0.9, 0.6]],
        index=['MOLD2', 'MOLD3'],
        columns=['M1', 'M2', 'M3']
    )
    priority_matrix.index.name = 'moldNo'
    
    return {
        'machines': machines,
        'molds': molds,
        'producing': producing,
        'pending': pending,
        'capacity': capacity,
        'priority_matrix': priority_matrix
    }


# ============================================================================
# TEST BASIC FUNCTIONALITY - No heavy mocking
# ============================================================================

class TestBasics:
    """Test basic functionality without excessive mocking"""
    
    def test_init_extracts_producing_lists(self, schemas, simple_data):
        """Test that init correctly extracts producing mold lists"""
        # No mock needed! Just pass real data
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        # Direct assertions on actual data
        assert planner.producing_mold_list == ['MOLD1']
        assert len(planner.producing_info_list) == 1
        assert planner.producing_info_list[0] == ['M1', 'MOLD1']
    
    def test_empty_producing_gives_empty_lists(self, schemas, simple_data):
        """Test empty producing data"""
        empty_producing = pd.DataFrame(columns=['machineCode', 'moldNo', 'itemCode', 'quantity'])
        
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=empty_producing,
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        assert planner.producing_mold_list == []
        assert planner.producing_info_list == []


class TestPrepareUnassignedData:
    """Test _prepare_unassigned_data - pure logic, no mocking needed"""
    
    def test_filters_correct_molds(self, schemas, simple_data):
        """Test that unassigned data is filtered correctly"""
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        # Setup test data
        planner.mold_lead_times = pd.DataFrame({
            'moldNo': ['MOLD2', 'MOLD3'],
            'itemCode': ['ITEM2', 'ITEM3'],
            'leadTime': [24.0, 20.0]
        })
        
        # Test the actual method
        unassigned_lead, unassigned_pending = planner._prepare_unassigned_data(['MOLD2'])
        
        # Direct assertions
        assert len(unassigned_lead) == 1
        assert unassigned_lead['moldNo'].iloc[0] == 'MOLD2'
        assert 'ITEM2' in unassigned_pending['itemCode'].values


class TestCombineAssignments:
    """Test _combine_assignments - pure pandas logic"""
    
    def test_combines_and_adjusts_priority(self, schemas, simple_data):
        """Test assignment combination logic"""
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        hist = pd.DataFrame({
            'Machine No.': ['M1', 'M1'],
            'Priority in Machine': [1, 2],
            'Machine Code': ['M1', 'M1'],
            'PO Quantity': [1000, 1500]
        })
        
        comp = pd.DataFrame({
            'Machine No.': ['M1'],
            'Priority in Machine': [1],
            'Machine Code': ['M1'],
            'PO Quantity': [2000]
        })
        
        result = planner._combine_assignments(hist, comp)
        
        # Test actual logic
        assert 'Note' in result.columns
        assert 'histBased' in result['Note'].values
        assert 'compatibilityBased' in result['Note'].values
        # Compatibility priority should be adjusted
        comp_row = result[result['Note'] == 'compatibilityBased']
        assert comp_row['Priority in Machine'].iloc[0] > 2  # Should be after hist max (2)
    
    def test_filters_zero_quantity_duplicates(self, schemas, simple_data):
        """Test zero quantity filtering"""
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        hist = pd.DataFrame({
            'Machine No.': ['M1'],
            'Priority in Machine': [1],
            'Machine Code': ['M1'],
            'PO Quantity': [0]
        })
        
        comp = pd.DataFrame({
            'Machine No.': ['M1'],
            'Priority in Machine': [2],
            'Machine Code': ['M1'],
            'PO Quantity': [0]
        })
        
        result = planner._combine_assignments(hist, comp)
        
        # Should keep at most one zero quantity per machine
        zero_rows = result[result['PO Quantity'] == 0]
        assert len(zero_rows) <= 1


class TestValidation:
    """Test validation methods - pure logic"""
    
    def test_validate_missing_columns_raises_error(self, schemas, simple_data):
        """Test validation catches missing columns"""
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        bad_df = pd.DataFrame({'Machine No.': [1]})  # Missing columns
        good_df = pd.DataFrame({
            'Machine No.': [1],
            'Priority in Machine': [1],
            'Machine Code': ['M1'],
            'PO Quantity': [1000]
        })
        
        required = ['Machine No.', 'Priority in Machine', 'Machine Code', 'PO Quantity']
        
        with pytest.raises(Exception, match="missing columns"):
            planner._validate_assignment_dataframes(bad_df, good_df, required)
    
    def test_validate_duplicate_priorities_raises_error(self, schemas, simple_data):
        """Test validation catches duplicate priorities"""
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        dup_df = pd.DataFrame({
            'Machine No.': ['M1', 'M1'],
            'Priority in Machine': [1, 1],  # Duplicate!
            'Machine Code': ['M1', 'M1'],
            'PO Quantity': [1000, 2000]
        })
        
        good_df = pd.DataFrame({
            'Machine No.': ['M2'],
            'Priority in Machine': [1],
            'Machine Code': ['M2'],
            'PO Quantity': [1000]
        })
        
        required = ['Machine No.', 'Priority in Machine', 'Machine Code', 'PO Quantity']
        
        with pytest.raises(Exception, match="duplicate priorities"):
            planner._validate_assignment_dataframes(dup_df, good_df, required)


class TestShouldRunCompatibility:
    """Test decision logic for running compatibility phase"""
    
    def test_should_run_when_has_unassigned(self, schemas, simple_data):
        """Should run compatibility when there are unassigned molds"""
        from dataclasses import dataclass
        
        @dataclass
        class Stats:
            total: int = 0
        
        @dataclass
        class Result:
            assignments: list
            unassigned_molds: list
            assigned_matrix: pd.DataFrame = None
            stats: Stats = None
            overloaded_machines: set = None
            log: str = ""
        
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        # Has unassigned molds
        history_result = {
            'assigner_result': Result(
                assignments=[],
                unassigned_molds=['MOLD1', 'MOLD2']
            )
        }
        
        assert planner._should_run_compatibility_optimization(history_result) is True
    
    def test_should_not_run_when_all_assigned(self, schemas, simple_data):
        """Should NOT run compatibility when all molds assigned"""
        from dataclasses import dataclass
        
        @dataclass
        class Stats:
            total: int = 0
        
        @dataclass
        class Result:
            assignments: list
            unassigned_molds: list
            assigned_matrix: pd.DataFrame = None
            stats: Stats = None
            overloaded_machines: set = None
            log: str = ""
        
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        # No unassigned molds
        history_result = {
            'assigner_result': Result(
                assignments=[('MOLD1', 'M1'), ('MOLD2', 'M2')],
                unassigned_molds=[]
            )
        }
        
        assert planner._should_run_compatibility_optimization(history_result) is False


class TestCompileFinalResults:
    """Test result compilation - simple if/else logic"""
    
    def test_compile_only_history(self, schemas, simple_data):
        """Case: Only history phase ran"""
        from dataclasses import dataclass
        
        @dataclass
        class Stats:
            total: int = 0
        
        @dataclass
        class Result:
            assignments: list
            unassigned_molds: list
            assigned_matrix: pd.DataFrame = None
            stats: Stats = None
            overloaded_machines: set = None
            log: str = ""
        
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        hist = {
            'assigner_result': Result([], []),
            'assignment_summary': pd.DataFrame({'col': [1]})
        }
        
        summary, result = planner._compile_final_results(hist, None)
        
        assert summary['Note'].iloc[0] == 'histBased'
        assert result == hist['assigner_result']
    
    def test_compile_only_compatibility(self, schemas, simple_data):
        """Case: Only compatibility phase ran"""
        from dataclasses import dataclass
        
        @dataclass
        class Stats:
            total: int = 0
        
        @dataclass
        class Result:
            assignments: list
            unassigned_molds: list
            assigned_matrix: pd.DataFrame = None
            stats: Stats = None
            overloaded_machines: set = None
            log: str = ""
        
        planner = PendingOrderPlanner(
            databaseSchemas_data=schemas['databaseSchemas'],
            sharedDatabaseSchemas_data=schemas['sharedSchemas'],
            generator_constant_config={},
            moldInfo_df=simple_data['molds'],
            machineInfo_df=simple_data['machines'],
            producing_status_data=simple_data['producing'],
            pending_status_data=simple_data['pending'],
            mold_estimated_capacity=simple_data['capacity'],
            mold_machine_priority_matrix=simple_data['priority_matrix']
        )
        
        comp = {
            'assigner_result': Result([], []),
            'assignment_summary': pd.DataFrame({'col': [1]})
        }
        
        summary, result = planner._compile_final_results(None, comp)
        
        assert summary['Note'].iloc[0] == 'compatibilityBased'
        assert result == comp['assigner_result']