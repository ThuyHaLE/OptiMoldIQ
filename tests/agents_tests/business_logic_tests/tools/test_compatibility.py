import pandas as pd
import pytest

from agents.autoPlanner.tools.compatibility import (
    create_mold_machine_compatibility_matrix
)

# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def machine_df():
    return pd.DataFrame({
        "machineCode": ["M1", "M2", "M3"],
        "machineTonnage": ["100", "200", "300"]
    })


@pytest.fixture
def mold_df():
    return pd.DataFrame({
        "moldNo": ["MO1", "MO2"],
        "machineTonnage": ["100/200", "300"]
    })


# --------------------------------------------------
# Tests
# --------------------------------------------------

def test_create_compatibility_matrix_happy_path(
    machine_df,
    mold_df,
    monkeypatch
):
    """
    Mold & machine match by tonnage
    """

    # mock check_newest_machine_layout → return input as-is
    monkeypatch.setattr(
        "agents.autoPlanner.tools.compatibility.check_newest_machine_layout",
        lambda df: df
    )

    result = create_mold_machine_compatibility_matrix(
        machine_df,
        mold_df
    )

    # expected index & columns
    assert set(result.index) == {"MO1", "MO2"}
    assert set(result.columns) == {"M1", "M2", "M3"}

    # MO1 compatible with 100, 200
    assert result.loc["MO1", "M1"] == 1
    assert result.loc["MO1", "M2"] == 1
    assert result.loc["MO1", "M3"] == 0

    # MO2 compatible with 300 only
    assert result.loc["MO2", "M3"] == 1
    assert result.loc["MO2", "M1"] == 0


def test_no_compatible_mold_machine_returns_empty_df(
    machine_df,
    monkeypatch
):
    """
    No mold tonnage matches machine tonnage
    """
    mold_df = pd.DataFrame({
        "moldNo": ["MO1"],
        "machineTonnage": ["999"]
    })

    monkeypatch.setattr(
        "agents.autoPlanner.tools.compatibility.check_newest_machine_layout",
        lambda df: df
    )

    result = create_mold_machine_compatibility_matrix(
        machine_df,
        mold_df
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_empty_machine_data_raises_runtime_error(mold_df, monkeypatch):
    machine_df = pd.DataFrame(columns=["machineCode", "machineTonnage"])

    monkeypatch.setattr(
        "agents.autoPlanner.tools.compatibility.check_newest_machine_layout",
        lambda df: df
    )

    with pytest.raises(RuntimeError) as exc:
        create_mold_machine_compatibility_matrix(
            machine_df,
            mold_df,
            validate_data=True
        )

    assert "Machine data is empty" in str(exc.value)


def test_empty_mold_data_raises_runtime_error(machine_df, monkeypatch):
    mold_df = pd.DataFrame(columns=["moldNo", "machineTonnage"])

    monkeypatch.setattr(
        "agents.autoPlanner.tools.compatibility.check_newest_machine_layout",
        lambda df: df
    )

    with pytest.raises(RuntimeError) as exc:
        create_mold_machine_compatibility_matrix(
            machine_df,
            mold_df,
            validate_data=True
        )

    assert "Mold data is empty" in str(exc.value)
