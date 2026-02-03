# tests/agents_tests/tools/test_plan_matching.py

import pandas as pd
import pytest

from agents.autoPlanner.tools.plan_matching import mold_item_plan_a_matching

# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def pending_df():
    return pd.DataFrame({
        "itemCode": ["I1", "I2"],
        "itemQuantity": [100, 50]
    })


@pytest.fixture
def mold_capacity_df():
    return pd.DataFrame({
        "itemCode": ["I1", "I2"],
        "moldNo": ["M1", "M2"],
        "moldName": ["Mold 1", "Mold 2"],
        "balancedMoldHourCapacity": [10, 5],
        "isPriority": [True, True]
    })


# --------------------------------------------------
# Validation errors
# --------------------------------------------------

def test_empty_pending_raises(mold_capacity_df):
    with pytest.raises(ValueError, match="Pending DataFrame is empty"):
        mold_item_plan_a_matching(
            pd.DataFrame(),
            mold_capacity_df
        )


def test_empty_mold_df_raises(pending_df):
    with pytest.raises(ValueError, match="Mold info DataFrame is empty"):
        mold_item_plan_a_matching(
            pending_df,
            pd.DataFrame()
        )


def test_no_priority_mold_raises(pending_df):
    mold_df = pd.DataFrame({
        "itemCode": ["I1"],
        "isPriority": [False]
    })

    with pytest.raises(ValueError, match="No priority molds found"):
        mold_item_plan_a_matching(
            pending_df,
            mold_df
        )


# --------------------------------------------------
# Warning branches
# --------------------------------------------------

def test_warns_on_non_positive_quantity(mold_capacity_df, caplog):
    pending_df = pd.DataFrame({
        "itemCode": ["I1"],
        "itemQuantity": [0]
    })

    mold_item_plan_a_matching(
        pending_df,
        mold_capacity_df
    )

    assert any(
        "non-positive quantities" in record.message
        for record in caplog.records
    )


def test_priority_mold_exists_but_no_matching_items_returns_empty(
    pending_df,
    caplog
):
    mold_df = pd.DataFrame({
        "itemCode": ["I3"],  # không match item nào
        "moldNo": ["M3"],
        "balancedMoldHourCapacity": [10],
        "isPriority": [True]
    })

    lead_time_df, pending_without = mold_item_plan_a_matching(
        pending_df,
        mold_df
    )

    assert lead_time_df.empty
    assert set(pending_without["itemCode"]) == {"I1", "I2"}

    assert any(
        "No pending items can be matched" in record.message
        for record in caplog.records
    )


# --------------------------------------------------
# Happy path (integration level)
# --------------------------------------------------

def test_happy_path_returns_lead_time_and_pending_without(
    pending_df,
    mold_capacity_df
):
    lead_time_df, pending_without = mold_item_plan_a_matching(
        pending_df,
        mold_capacity_df
    )

    assert not lead_time_df.empty
    assert pending_without.empty

    assert set(lead_time_df.columns) >= {
        "itemCode",
        "moldNo",
        "moldLeadTime"
    }