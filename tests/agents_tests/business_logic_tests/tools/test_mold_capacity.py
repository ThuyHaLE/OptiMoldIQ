# tests/agents_tests/business_logic_tests/tools/test_mold_capacity.py

import pandas as pd
import pytest
from loguru import logger
import sys

from agents.autoPlanner.tools.mold_capacity import (
    calculate_mold_lead_times,
    split_pending_by_mold_availability
)

# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def pending_df():
    return pd.DataFrame({
        "itemCode": ["I1", "I1", "I2"],
        "itemQuantity": [240, 120, 100]
    })


@pytest.fixture
def mold_capacity_df():
    return pd.DataFrame({
        "itemCode": ["I1", "I2"],
        "moldNo": ["MOLD1", "MOLD2"],
        "moldName": ["Mold A", "Mold B"],
        "moldCavityStandard": [2, 4],
        "moldSettingCycle": [30, 20],
        "balancedMoldHourCapacity": [10, 5]
    })


@pytest.fixture
def loguru_caplog():
    """Fixture to capture loguru logs in tests."""
    class LoguruCapture:
        def __init__(self):
            self.records = []
        
        def write(self, message):
            self.records.append(message)
    
    capture = LoguruCapture()
    handler_id = logger.add(capture.write, format="{message}")
    yield capture
    logger.remove(handler_id)


# --------------------------------------------------
# calculate_mold_lead_times
# --------------------------------------------------

def test_calculate_mold_lead_times_happy_path(
    pending_df,
    mold_capacity_df
):
    result = calculate_mold_lead_times(
        pending_df,
        mold_capacity_df
    )

    assert set(result.columns) >= {
        "itemCode",
        "moldNo",
        "totalQuantity",
        "balancedMoldHourCapacity",
        "moldLeadTime"
    }

    # I1: totalQuantity = 360, capacity = 10
    # lead time = (360 / 10) / 24 = 1.5 → round = 2
    row_i1 = result[result["itemCode"] == "I1"].iloc[0]
    assert row_i1["moldLeadTime"] == 2

    # I2: (100 / 5) / 24 = 0.83 → round = 1 → replace(0,1)
    row_i2 = result[result["itemCode"] == "I2"].iloc[0]
    assert row_i2["moldLeadTime"] == 1


def test_calculate_mold_lead_times_empty_pending_raises():
    with pytest.raises(ValueError, match="Pending DataFrame is empty"):
        calculate_mold_lead_times(
            pd.DataFrame(),
            pd.DataFrame({"itemCode": ["I1"]})
        )


def test_calculate_mold_lead_times_empty_mold_df_raises(pending_df):
    with pytest.raises(ValueError, match="Mold info DataFrame is empty"):
        calculate_mold_lead_times(
            pending_df,
            pd.DataFrame()
        )


def test_calculate_mold_lead_times_warns_on_non_positive_quantity(
    mold_capacity_df,
    loguru_caplog
):
    pending_df = pd.DataFrame({
        "itemCode": ["I1"],
        "itemQuantity": [0]
    })

    calculate_mold_lead_times(
        pending_df,
        mold_capacity_df
    )

    assert any(
        "non-positive quantities" in record
        for record in loguru_caplog.records
    )


# --------------------------------------------------
# split_pending_by_mold_availability
# --------------------------------------------------

def test_split_pending_by_mold_availability_happy_path(
    pending_df,
    mold_capacity_df
):
    with_mold, without_mold = split_pending_by_mold_availability(
        pending_df,
        mold_capacity_df
    )

    assert set(with_mold["itemCode"]) == {"I1", "I2"}
    assert without_mold.empty


def test_split_pending_with_missing_items_warns(
    mold_capacity_df,
    loguru_caplog
):
    pending_df = pd.DataFrame({
        "itemCode": ["I1", "I3"],
        "itemQuantity": [10, 20]
    })

    with_mold, without_mold = split_pending_by_mold_availability(
        pending_df,
        mold_capacity_df
    )

    assert set(without_mold["itemCode"]) == {"I3"}
    assert set(with_mold["itemCode"]) == {"I1"}

    assert any(
        "No suitable molds found for items" in record
        for record in loguru_caplog.records
    )


def test_split_pending_empty_pending_raises(mold_capacity_df):
    with pytest.raises(ValueError, match="Pending DataFrame is empty"):
        split_pending_by_mold_availability(
            pd.DataFrame(),
            mold_capacity_df
        )


def test_split_pending_empty_mold_df_raises(pending_df):
    with pytest.raises(ValueError, match="Mold info DataFrame is empty"):
        split_pending_by_mold_availability(
            pending_df,
            pd.DataFrame()
        )