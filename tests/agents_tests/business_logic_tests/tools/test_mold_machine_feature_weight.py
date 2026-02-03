import pandas as pd
import pytest

from agents.autoPlanner.tools.mold_machine_feature_weight import (
    suggest_weights_standard_based
)

# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def good_df():
    return pd.DataFrame({
        "f1": [10, 12],
        "f2": [5, 5],
        "f3": [1, 1]
    })


@pytest.fixture
def bad_df():
    return pd.DataFrame({
        "f1": [20, 18],
        "f2": [10, 10],
        "f3": [1, 1]
    })


# --------------------------------------------------
# Validation errors
# --------------------------------------------------

def test_empty_features_raises():
    with pytest.raises(ValueError, match="Features list cannot be empty"):
        suggest_weights_standard_based(
            good_hist_df=pd.DataFrame(),
            bad_hist_df=pd.DataFrame(),
            targets={}
        )


def test_invalid_scaling_raises(good_df, bad_df):
    with pytest.raises(ValueError, match="Scaling must be"):
        suggest_weights_standard_based(
            good_hist_df=good_df,
            bad_hist_df=bad_df,
            targets={"f1": 10},
            scaling="invalid"
        )


# --------------------------------------------------
# Feature missing in dataframe
# --------------------------------------------------

def test_feature_not_in_dataframe_sets_weight_zero(good_df, bad_df):
    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={
            "f1": 10,
            "missing_feature": 5
        }
    )

    assert result["missing_feature"] == 0
    assert result["f1"] > 0
    assert abs(sum(result.values()) - 1.0) < 1e-6


# --------------------------------------------------
# Mean NaN / empty dataframe handling
# --------------------------------------------------

def test_nan_means_handled_as_zero():
    good_df = pd.DataFrame({"f1": [None, None]})
    bad_df = pd.DataFrame({"f1": [None, None]})

    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={"f1": 10}
    )

    # total == 0 → equal weights
    assert result == {"f1": 1.0}


def test_empty_good_or_bad_df():
    good_df = pd.DataFrame(columns=["f1"])
    bad_df = pd.DataFrame({"f1": [5, 5]})

    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={"f1": 0}
    )

    assert result["f1"] == 1.0


# --------------------------------------------------
# Scaling logic
# --------------------------------------------------

def test_relative_scaling_with_target(good_df, bad_df):
    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={"f1": 10, "f2": 5},
        scaling="relative"
    )

    assert abs(sum(result.values()) - 1.0) < 1e-6
    assert all(v >= 0 for v in result.values())


def test_relative_scaling_with_minimize(good_df, bad_df):
    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={"f3": "minimize"},
        scaling="relative"
    )

    assert result == {"f3": 1.0}


# --------------------------------------------------
# total == 0 branch
# --------------------------------------------------

def test_all_scores_zero_returns_equal_weights():
    good_df = pd.DataFrame({"f1": [1], "f2": [1]})
    bad_df = pd.DataFrame({"f1": [1], "f2": [1]})

    result = suggest_weights_standard_based(
        good_hist_df=good_df,
        bad_hist_df=bad_df,
        targets={"f1": 1, "f2": 1}
    )

    assert result == {"f1": 0.5, "f2": 0.5}