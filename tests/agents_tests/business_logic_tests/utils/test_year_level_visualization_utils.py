# tests/agents_tests/business_logic_tests/utils/test_year_level_visualization_utils.py

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agents.dashboardBuilder.plotters.year_level.utils import (
    generate_coords,
    find_best_ncols,
    process_mold_based_data,
    process_machine_based_data,
    add_new_features,
    detect_not_progress,
    detect_process_status,
    process_not_progress_records,
    calculate_aggregations,
    merge_by_fields
)

# ==================== FIXTURES ====================

@pytest.fixture
def base_dataframe():
    """Create base DataFrame with all required columns"""
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    
    data = {
        'recordDate': dates,
        'workingShift': ['1', '2', '3', 'HC'] * 5,
        'machineNo': ['M001', 'M002'] * 10,
        'machineCode': ['MC01', 'MC02'] * 10,
        'itemCode': ['ITEM001', 'ITEM002'] * 10,
        'itemName': ['Item A', 'Item B'] * 10,
        'colorChanged': [False] * 20,
        'moldChanged': [False] * 20,
        'machineChanged': [False] * 20,
        'poNote': ['PO001', 'PO002'] * 10,
        'moldNo': ['MOLD001', 'MOLD002'] * 10,
        'moldShot': [100, 150] * 10,
        'moldCavity': [4, 8] * 10,
        'itemTotalQuantity': [1000, 1500] * 10,
        'itemGoodQuantity': [950, 1425] * 10,
        'itemBlackSpot': [10, 15] * 10,
        'itemOilDeposit': [5, 10] * 10,
        'itemScratch': [15, 20] * 10,
        'itemCrack': [5, 8] * 10,
        'itemSinkMark': [3, 5] * 10,
        'itemShort': [2, 4] * 10,
        'itemBurst': [1, 2] * 10,
        'itemBend': [4, 6] * 10,
        'itemStain': [5, 5] * 10,
        'otherNG': [0, 0] * 10,
        'plasticResin': ['Resin A', 'Resin B'] * 10,
        'plasticResinCode': ['R001', 'R002'] * 10,
        'plasticResinLot': ['L001', 'L002'] * 10,
        'colorMasterbatch': ['Color A', 'Color B'] * 10,
        'colorMasterbatchCode': ['C001', 'C002'] * 10,
        'additiveMasterbatch': ['Add A', 'Add B'] * 10,
        'additiveMasterbatchCode': ['A001', 'A002'] * 10,
        'recordMonth': ['2024-01'] * 20
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def dataframe_with_missing_data(base_dataframe):
    """DataFrame with some missing/zero values for not-progress testing"""
    df = base_dataframe.copy()
    
    # Add some problematic records
    df.loc[0:2, 'poNote'] = np.nan
    df.loc[3:5, 'itemTotalQuantity'] = 0
    df.loc[6:8, 'itemTotalQuantity'] = np.nan
    
    return df

@pytest.fixture
def processed_dataframe(base_dataframe):
    """DataFrame with derived features already added"""
    return add_new_features(base_dataframe)

# ==================== TEST GENERATE_COORDS ====================

class TestGenerateCoords:
    """Test coordinate generation for subplot layouts"""
    
    def test_generates_correct_number_of_coords(self):
        """Should generate n_rows * n_cols coordinates"""
        coords = generate_coords(3, 4)
        assert len(coords) == 12
    
    def test_coords_format(self):
        """Each coordinate should be a tuple of (row, col)"""
        coords = generate_coords(2, 3)
        
        for coord in coords:
            assert isinstance(coord, tuple)
            assert len(coord) == 2
            assert isinstance(coord[0], int)
            assert isinstance(coord[1], int)
    
    def test_coords_range(self):
        """Coordinates should be within valid range"""
        n_rows, n_cols = 3, 4
        coords = generate_coords(n_rows, n_cols)
        
        for row, col in coords:
            assert 0 <= row < n_rows
            assert 0 <= col < n_cols
    
    def test_coords_order(self):
        """Coordinates should be in row-major order"""
        coords = generate_coords(2, 2)
        expected = [(0, 0), (0, 1), (1, 0), (1, 1)]
        assert coords == expected
    
    @pytest.mark.parametrize("n_rows,n_cols,expected_len", [
        (1, 1, 1),
        (2, 3, 6),
        (4, 5, 20),
        (10, 1, 10),
        (1, 10, 10),
    ])
    def test_various_dimensions(self, n_rows, n_cols, expected_len):
        """Test various grid dimensions"""
        coords = generate_coords(n_rows, n_cols)
        assert len(coords) == expected_len
    
    def test_zero_rows_or_cols(self):
        """Should handle zero dimensions"""
        assert generate_coords(0, 5) == []
        assert generate_coords(5, 0) == []
        assert generate_coords(0, 0) == []
    
    def test_negative_dimensions(self):
        """Should handle negative dimensions"""
        assert generate_coords(-1, 5) == []
        assert generate_coords(5, -1) == []

# ==================== TEST FIND_BEST_NCOLS ====================

class TestFindBestNcols:
    """Test optimal column calculation for subplot layouts"""
    
    @pytest.mark.parametrize("num_metrics,expected", [
        (4, 2),   # 4 % 2 == 0
        (6, 2),   # 6 % 2 == 0
        (8, 2),   # 8 % 2 == 0
        (9, 3),   # 9 % 3 == 0
        (12, 2),  # 12 % 2 == 0 (finds smallest)
    ])
    def test_finds_even_divisor(self, num_metrics, expected):
        """Should find the smallest even divisor"""
        result = find_best_ncols(num_metrics)
        assert result == expected
        assert num_metrics % result == 0
    
    @pytest.mark.parametrize("num_metrics,expected", [
        (5, 4),   # No divisor in range, return max_cols
        (7, 4),   # No divisor in range, return max_cols
        (11, 4),  # No divisor in range, return max_cols
    ])
    def test_falls_back_to_max(self, num_metrics, expected):
        """Should fall back to max_cols when no divisor found"""
        result = find_best_ncols(num_metrics)
        assert result == expected
    
    def test_custom_min_max_cols(self):
        """Should respect custom min/max column limits"""
        result = find_best_ncols(10, min_cols=3, max_cols=5)
        assert result == 5  # 10 % 5 == 0
        
        result = find_best_ncols(9, min_cols=3, max_cols=5)
        assert result == 3  # 9 % 3 == 0
    
    def test_single_metric(self):
        """Should handle single metric"""
        result = find_best_ncols(1, min_cols=2, max_cols=4)
        assert result == 4  # Falls back to max
    
    def test_prefers_smaller_divisor(self):
        """Should prefer smaller divisor when multiple exist"""
        result = find_best_ncols(12, min_cols=2, max_cols=4)
        assert result == 2  # 12 divisible by 2, 3, 4 -> choose 2
    
    @pytest.mark.parametrize("num_metrics", [0, -1, -5])
    def test_handles_invalid_metrics(self, num_metrics):
        """Should handle zero or negative metrics"""
        result = find_best_ncols(num_metrics)
        assert result == 4  # Falls back to max_cols

# ==================== TEST ADD_NEW_FEATURES ====================

class TestAddNewFeatures:
    """Test derived feature creation"""
    
    def test_adds_item_component(self, base_dataframe):
        """Should create itemComponent from resin, color, additive"""
        result = add_new_features(base_dataframe)
        
        assert 'itemComponent' in result.columns
        assert result['itemComponent'].notna().all()
        
        # Check format: resin_color_additive
        expected = 'Resin A_Color A_Add A'
        assert result.loc[0, 'itemComponent'] == expected
    
    def test_adds_record_info(self, base_dataframe):
        """Should create recordInfo from date and shift"""
        result = add_new_features(base_dataframe)
        
        assert 'recordInfo' in result.columns
        assert result['recordInfo'].notna().all()
        
        # Check format: YYYY-MM-DD_Shift
        expected = '2024-01-01_1'
        assert result.loc[0, 'recordInfo'] == expected
    
    def test_adds_record_month(self, base_dataframe):
        """Should create recordMonth in YYYY-MM format"""
        result = add_new_features(base_dataframe)
        
        assert 'recordMonth' in result.columns
        assert result.loc[0, 'recordMonth'] == '2024-01'
    
    def test_handles_missing_component_values(self, base_dataframe):
        """Should handle NaN in component fields"""
        df = base_dataframe.copy()
        df.loc[0:2, 'plasticResin'] = np.nan
        df.loc[3:5, 'colorMasterbatch'] = np.nan
        df.loc[6:8, 'additiveMasterbatch'] = np.nan
        
        result = add_new_features(df)
        
        # Should convert NaN to empty string
        assert result['itemComponent'].notna().all()
        assert 'nan' not in result.loc[0, 'itemComponent'].lower()
    
    def test_preserves_original_columns(self, base_dataframe):
        """Should keep all original columns"""
        original_cols = set(base_dataframe.columns)
        result = add_new_features(base_dataframe)
        
        assert original_cols.issubset(set(result.columns))
    
    def test_raises_on_missing_required_columns(self):
        """Should raise error if required columns missing"""
        df = pd.DataFrame({'dummy': [1, 2, 3]})
        
        with pytest.raises(ValueError):
            add_new_features(df)

# ==================== TEST DETECT_NOT_PROGRESS ====================

class TestDetectNotProgress:
    """Test non-productive period detection"""
    
    def test_detects_missing_po(self, processed_dataframe):
        """Should flag shifts with missing PO"""
        df = processed_dataframe.copy()
        df.loc[0:2, 'poNote'] = np.nan
        
        shift_level, day_level = detect_not_progress(df)
        
        assert shift_level.loc[0, 'is_shift_not_progress'] == True
        assert shift_level.loc[1, 'is_shift_not_progress'] == True
    
    def test_detects_zero_quantity(self, processed_dataframe):
        """Should flag shifts with zero total quantity"""
        df = processed_dataframe.copy()
        df.loc[0:2, 'itemTotalQuantity'] = 0
        
        shift_level, day_level = detect_not_progress(df)
        
        assert shift_level.loc[0, 'is_shift_not_progress'] == True
    
    def test_detects_missing_quantity(self, processed_dataframe):
        """Should flag shifts with NaN quantity"""
        df = processed_dataframe.copy()
        df.loc[0:2, 'itemTotalQuantity'] = np.nan
        
        shift_level, day_level = detect_not_progress(df)
        
        assert shift_level.loc[0, 'is_shift_not_progress'] == True
    
    def test_day_level_requires_3_shifts(self, processed_dataframe):
        """Day should be flagged only if >=3 shifts are non-productive"""
        df = processed_dataframe.copy()
        
        # Same date, same machine, different shifts (using the actual shift values from fixture)
        # The base fixture uses ['1', '2', '3', 'HC'] * 5 pattern
        df.loc[0:5, 'recordDate'] = pd.Timestamp('2024-01-01')
        df.loc[0:5, 'machineCode'] = 'MC01'  # Same machine
        df.loc[0:5, 'workingShift'] = ['1', '2', '3', 'HC', '1', '2']  # 6 different shifts
        
        # Mark first 3 shifts as non-productive by setting itemTotalQuantity to 0
        # (just setting poNote to NaN is not enough - need zero quantity too)
        df.loc[0:2, 'poNote'] = np.nan
        df.loc[0:2, 'itemTotalQuantity'] = 0  # This is critical!
        
        shift_level, day_level = detect_not_progress(df)
        
        # Day should be flagged (3 shifts are non-productive)
        day_records = day_level[day_level['recordDate'] == '2024-01-01']
        assert len(day_records) > 0
        assert day_records.iloc[0]['is_day_not_progress'] == True

    # Test the boundary conditions more explicitly
    def test_day_level_requires_exactly_3_shifts(self, processed_dataframe):
        """Test boundary: exactly 3 non-productive shifts flags the day"""
        df = processed_dataframe.copy()
        
        # Setup: 4 shifts on same date, same machine
        df.loc[0:3, 'recordDate'] = pd.Timestamp('2024-01-01')
        df.loc[0:3, 'machineCode'] = 'MC01'
        df.loc[0:3, 'workingShift'] = ['1', '2', '3', 'HC']
        
        # Mark exactly 3 as non-productive
        df.loc[0:2, 'itemTotalQuantity'] = 0
        
        shift_level, day_level = detect_not_progress(df)
        
        # Should be flagged (3 >= 3)
        day_records = day_level[day_level['recordDate'] == '2024-01-01']
        assert len(day_records) > 0
        assert day_records.iloc[0]['is_day_not_progress'] == True


    def test_day_level_not_flagged_with_2_shifts(self, processed_dataframe):
        """Test boundary: only 2 non-productive shifts does NOT flag the day"""
        df = processed_dataframe.copy()
        
        # Setup: 4 shifts on same date, same machine
        df.loc[0:3, 'recordDate'] = pd.Timestamp('2024-01-01')
        df.loc[0:3, 'machineCode'] = 'MC01'
        df.loc[0:3, 'workingShift'] = ['1', '2', '3', 'HC']
        
        # Mark only 2 as non-productive
        df.loc[0:1, 'itemTotalQuantity'] = 0
        
        shift_level, day_level = detect_not_progress(df)
        
        # Should NOT be flagged (2 < 3)
        day_records = day_level[day_level['recordDate'] == '2024-01-01']
        assert len(day_records) == 0  # No day should be flagged

    # Most comprehensive version with detailed comments
    def test_day_level_requires_3_shifts_comprehensive(self, processed_dataframe):
        """
        Day should be flagged only if >=3 shifts are non-productive.
        
        Non-productive criteria (from detect_not_progress):
        - Missing PO (poNote is NaN) OR
        - Missing quantity (itemTotalQuantity is NaN) OR  
        - Zero quantity (itemTotalQuantity == 0)
        """
        df = processed_dataframe.copy()
        
        # Create a clear scenario: 6 shifts on 2024-01-01 for machine MC01
        test_date = pd.Timestamp('2024-01-01')
        
        df.loc[0:5, 'recordDate'] = test_date
        df.loc[0:5, 'machineCode'] = 'MC01'
        
        # Use actual shift values from the fixture pattern: '1', '2', '3', 'HC'
        # We need 6 distinct recordInfo values (date_shift combinations)
        df.loc[0, 'workingShift'] = '1'
        df.loc[1, 'workingShift'] = '2' 
        df.loc[2, 'workingShift'] = '3'
        df.loc[3, 'workingShift'] = 'HC'
        df.loc[4, 'workingShift'] = '1'  # Different from row 0 due to different machineCode originally
        df.loc[5, 'workingShift'] = '2'
        
        # Make shifts 0, 1, 2 non-productive (3 shifts total)
        # Strategy: Set itemTotalQuantity to 0 (clearest signal)
        df.loc[0:2, 'itemTotalQuantity'] = 0
        df.loc[0:2, 'itemGoodQuantity'] = 0
        
        # Ensure shifts 3, 4, 5 are productive (have valid data)
        df.loc[3:5, 'poNote'] = 'PO001'
        df.loc[3:5, 'itemTotalQuantity'] = 1000
        df.loc[3:5, 'itemGoodQuantity'] = 950
        
        shift_level, day_level = detect_not_progress(df)
        
        # Verify shift-level detection
        assert shift_level.loc[0, 'is_shift_not_progress'] == True
        assert shift_level.loc[1, 'is_shift_not_progress'] == True
        assert shift_level.loc[2, 'is_shift_not_progress'] == True
        assert shift_level.loc[3, 'is_shift_not_progress'] == False
        assert shift_level.loc[4, 'is_shift_not_progress'] == False
        assert shift_level.loc[5, 'is_shift_not_progress'] == False
        
        # Day should be flagged (offShifts = 3, which is >= 3)
        day_records = day_level[day_level['recordDate'] == test_date]
        assert len(day_records) > 0, "Expected at least one day record to be flagged"
        assert day_records.iloc[0]['is_day_not_progress'] == True
        assert day_records.iloc[0]['offShifts'] == 3
        assert day_records.iloc[0]['machineCode'] == 'MC01'
    
    def test_returns_correct_columns(self, processed_dataframe):
        """Should return expected columns"""
        shift_level, day_level = detect_not_progress(processed_dataframe)
        
        expected_shift_cols = {'machineCode', 'recordDate', 'workingShift', 
                              'recordInfo', 'is_shift_not_progress'}
        assert expected_shift_cols.issubset(set(shift_level.columns))
        
        expected_day_cols = {'machineCode', 'recordDate', 'is_day_not_progress'}
        assert expected_day_cols.issubset(set(day_level.columns))
    
    def test_empty_dataframe(self, processed_dataframe):
        """Should handle empty DataFrame"""
        empty_df = processed_dataframe.iloc[0:0].copy()
        
        shift_level, day_level = detect_not_progress(empty_df)
        
        assert len(shift_level) == 0
        assert len(day_level) == 0

# ==================== TEST PROCESS_MACHINE_BASED_DATA ====================

class TestProcessMachineBasedData:
    """Test machine-based data processing pipeline"""
    
    def test_handles_all_productive_data(self, base_dataframe):
       """Should handle data with no non-productive records"""
       # All records are valid - no missing PO, no zero quantities
       result = process_machine_based_data(base_dataframe, group_by_month=False)
       
       # Should complete successfully and return valid summary
       assert len(result) > 0
       assert (result['notProgressDays'] == 0).all()
       assert (result['notProgressShifts'] == 0).all()

    def test_returns_correct_structure(self, base_dataframe):
        """Should return summary DataFrame with expected columns"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        expected_cols = {'poNums', 'itemNums', 'moldNums', 'itemComponentNums',
                        'totalMoldShot', 'totalQuantity', 'goodQuantity',
                        'workingDays', 'workingShifts', 'avgNGRate',
                        'notProgressDays', 'notProgressShifts'}
        
        assert expected_cols.issubset(set(result.columns))
    
    def test_groups_by_machine_code(self, base_dataframe):
        """Should group results by machineCode"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        assert 'machineCode' in result.index.names
        assert len(result) > 0
    
    def test_groups_by_month_and_machine(self, base_dataframe):
        """Should group by month when requested"""
        result = process_machine_based_data(base_dataframe, group_by_month=True)
        
        assert 'recordMonth' in result.index.names
        assert 'machineCode' in result.index.names
    
    def test_excludes_non_productive_records(self, dataframe_with_missing_data):
        """Should exclude records with missing PO or zero quantity"""
        result = process_machine_based_data(dataframe_with_missing_data, group_by_month=False)
        
        # Total quantity should not include non-productive records
        assert result['totalQuantity'].sum() < dataframe_with_missing_data['itemTotalQuantity'].sum()
    
    def test_calculates_ng_rate_correctly(self, base_dataframe):
        """Should calculate NG rate as percentage"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        assert 'avgNGRate' in result.columns
        assert (result['avgNGRate'] >= 0).all()
        assert (result['avgNGRate'] <= 100).all()
    
    def test_counts_unique_items_correctly(self, base_dataframe):
        """Should count unique POs, items, molds"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        assert 'poNums' in result.columns
        assert 'itemNums' in result.columns
        assert 'moldNums' in result.columns
        assert (result['poNums'] > 0).any()
    
    def test_working_days_and_shifts(self, base_dataframe):
        """Should count working days and shifts"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        assert 'workingDays' in result.columns
        assert 'workingShifts' in result.columns
        assert (result['workingDays'] > 0).any()
        assert (result['workingShifts'] >= result['workingDays']).all()
    
    def test_handles_all_non_productive_data(self, base_dataframe):
        """Should handle case where all data is non-productive"""
        df = base_dataframe.copy()
        df['poNote'] = np.nan  # Make all non-productive
        
        result = process_machine_based_data(df, group_by_month=False)
        
        # Should still return structure but with zeros
        assert len(result) > 0
        assert (result['totalQuantity'] == 0).all()
    
    def test_preserves_machine_codes(self, base_dataframe):
        """Should include all machine codes from input"""
        unique_machines = base_dataframe['machineCode'].unique()
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        result_machines = result.index.get_level_values('machineCode').unique()
        assert set(unique_machines).issubset(set(result_machines))

# ==================== TEST PROCESS_MOLD_BASED_DATA ====================

class TestProcessMoldBasedData:
    """Test mold-based data processing"""
    
    def test_returns_correct_structure(self, base_dataframe):
        """Should return summary with expected columns"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        expected_cols = {'moldNo', 'totalShots', 'cavityNums', 'avgCavity',
                        'cavityList', 'machineNums', 'machineList',
                        'totalQuantity', 'goodQuantity', 'totalNG', 'totalNGRate'}
        
        assert expected_cols.issubset(set(result.columns))
    
    def test_groups_by_mold_number(self, base_dataframe):
        """Should group by moldNo"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        assert 'moldNo' in result.columns
        unique_molds = base_dataframe['moldNo'].unique()
        assert len(result) <= len(unique_molds)
    
    def test_groups_by_month_and_mold(self, base_dataframe):
        """Should group by month when requested"""
        result = process_mold_based_data(base_dataframe, group_by_month=True)
        
        assert 'recordMonth' in result.columns
        assert 'moldNo' in result.columns
    
    def test_calculates_total_shots(self, base_dataframe):
        """Should sum all shots for each mold"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        assert 'totalShots' in result.columns
        assert (result['totalShots'] > 0).all()
    
    def test_tracks_cavity_information(self, base_dataframe):
        """Should track cavity counts and lists"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        assert 'cavityNums' in result.columns
        assert 'avgCavity' in result.columns
        assert 'cavityList' in result.columns
        
        # Average should be reasonable
        assert (result['avgCavity'] > 0).all()
    
    def test_tracks_machine_usage(self, base_dataframe):
        """Should track which machines used each mold"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        assert 'machineNums' in result.columns
        assert 'machineList' in result.columns
        assert (result['machineNums'] > 0).all()
    
    def test_calculates_ng_metrics(self, base_dataframe):
        """Should calculate NG quantity and rate"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        assert 'totalNG' in result.columns
        assert 'totalNGRate' in result.columns
        
        # NG should equal total - good
        expected_ng = result['totalQuantity'] - result['goodQuantity']
        assert (result['totalNG'] == expected_ng).all()
        
        # NG rate should be percentage
        assert (result['totalNGRate'] >= 0).all()
        assert (result['totalNGRate'] <= 100).all()
    
    def test_sorts_by_total_shots(self, base_dataframe):
        """Should sort results by total shots descending"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        # Check if sorted descending
        shots = result['totalShots'].values
        assert all(shots[i] >= shots[i+1] for i in range(len(shots)-1))
    
    def test_excludes_zero_quantity_records(self, base_dataframe):
        """Should filter out records with zero quantity"""
        df = base_dataframe.copy()
        df.loc[0:5, 'itemTotalQuantity'] = 0
        
        result = process_mold_based_data(df, group_by_month=False)
        
        # Result should not include those records
        assert result['totalQuantity'].sum() < df['itemTotalQuantity'].sum()
    
    def test_handles_single_mold(self, base_dataframe):
        """Should handle data with single mold"""
        df = base_dataframe.copy()
        df['moldNo'] = 'MOLD001'  # All same mold
        
        result = process_mold_based_data(df, group_by_month=False)
        
        assert len(result) == 1
        assert result.loc[0, 'moldNo'] == 'MOLD001'
    
    def test_cavity_list_is_array(self, base_dataframe):
        """cavityList should contain array of unique cavities"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        for cavity_list in result['cavityList']:
            assert isinstance(cavity_list, np.ndarray)
            
# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests combining multiple functions"""
    
    def test_full_machine_pipeline(self, base_dataframe):
        """Test complete machine processing pipeline"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        
        # Should have data for both machines
        assert len(result) >= 2
        
        # All metrics should be positive
        assert (result['totalQuantity'] > 0).all()
        assert (result['goodQuantity'] > 0).all()
        assert (result['workingDays'] > 0).all()
    
    def test_full_mold_pipeline(self, base_dataframe):
        """Test complete mold processing pipeline"""
        result = process_mold_based_data(base_dataframe, group_by_month=False)
        
        # Should have data for both molds
        assert len(result) >= 2
        
        # All molds should have shots
        assert (result['totalShots'] > 0).all()
    
    def test_month_grouping_consistency(self, base_dataframe):
        """Month grouping should be consistent across functions"""
        machine_result = process_machine_based_data(base_dataframe, group_by_month=True)
        mold_result = process_mold_based_data(base_dataframe, group_by_month=True)
        
        # Both should have recordMonth
        assert 'recordMonth' in machine_result.index.names or 'recordMonth' in machine_result.columns
        assert 'recordMonth' in mold_result.columns
    
    def test_coords_with_metrics(self, base_dataframe):
        """Test coord generation matches actual metric count"""
        result = process_machine_based_data(base_dataframe, group_by_month=False)
        num_metrics = 10  # Example: 10 KPIs to plot
        
        n_cols = find_best_ncols(num_metrics)
        n_rows = (num_metrics + n_cols - 1) // n_cols
        coords = generate_coords(n_rows, n_cols)
        
        # Should have enough coords for all metrics
        assert len(coords) >= num_metrics

# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_dataframe_machine(self):
        """Should handle empty DataFrame for machine processing"""
        empty_df = pd.DataFrame(columns=[
            'recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
            'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
            'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
            'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
            'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
            'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
            'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
            'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth'
        ])
        
        result = process_machine_based_data(empty_df, group_by_month=False)
        assert len(result) == 0
    
    def test_empty_dataframe_mold(self):
        """Should handle empty DataFrame for mold processing"""
        empty_df = pd.DataFrame(columns=[
            'recordDate', 'workingShift', 'machineNo', 'machineCode', 'itemCode',
            'itemName', 'colorChanged', 'moldChanged', 'machineChanged', 'poNote',
            'moldNo', 'moldShot', 'moldCavity', 'itemTotalQuantity',
            'itemGoodQuantity', 'itemBlackSpot', 'itemOilDeposit', 'itemScratch',
            'itemCrack', 'itemSinkMark', 'itemShort', 'itemBurst', 'itemBend',
            'itemStain', 'otherNG', 'plasticResin', 'plasticResinCode',
            'plasticResinLot', 'colorMasterbatch', 'colorMasterbatchCode',
            'additiveMasterbatch', 'additiveMasterbatchCode', 'recordMonth'
        ])
        
        result = process_mold_based_data(empty_df, group_by_month=False)
        assert len(result) == 0
    
    def test_all_null_quantities(self, base_dataframe):
        """Should handle all null quantities"""
        df = base_dataframe.copy()
        df['itemTotalQuantity'] = np.nan
        
        result = process_machine_based_data(df, group_by_month=False)
        assert (result['totalQuantity'] == 0).all()
    
    def test_single_record(self, base_dataframe):
        """Should handle single record"""
        single_row = base_dataframe.iloc[[0]].copy()
        
        result_machine = process_machine_based_data(single_row, group_by_month=False)
        result_mold = process_mold_based_data(single_row, group_by_month=False)
        
        assert len(result_machine) == 1
        assert len(result_mold) == 1
    
    def test_extreme_coordinates(self):
        """Test extreme coordinate generation"""
        # Very large grid
        coords = generate_coords(100, 100)
        assert len(coords) == 10000
        
        # Very small grid
        coords = generate_coords(1, 1)
        assert len(coords) == 1
        assert coords[0] == (0, 0)
    
    def test_extreme_ncols_values(self):
        """Test extreme values for ncols calculation"""
        assert find_best_ncols(1000) in range(2, 5)
        assert find_best_ncols(1) == 4