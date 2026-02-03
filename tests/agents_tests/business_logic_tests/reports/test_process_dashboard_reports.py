import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from agents.orderProgressTracker.process_dashboard_reports import ProcessDashboardReports


# ======================================================
# Fixtures
# ======================================================

@pytest.fixture
def fake_excel_file(tmp_path):
    path = tmp_path / "fake.xlsx"
    path.write_text("fake excel")
    return str(path)


@pytest.fixture
def mock_excel_file(monkeypatch):
    mock = MagicMock()
    mock.sheet_names = [
        "productionStatus",
        "materialComponentMap",
        "moldShotMap",
        "machineQuantityMap",
        "dayQuantityMap",
    ]
    monkeypatch.setattr(pd, "ExcelFile", lambda *_: mock)
    return mock


def mock_read_excel_factory(sheet_data_map):
    def _mock_read_excel(*_, sheet_name=None, **__):
        return sheet_data_map[sheet_name].copy()
    return _mock_read_excel


# ======================================================
# __init__
# ======================================================

def test_init_success(fake_excel_file, mock_excel_file):
    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    assert len(report.sheet_names) > 0


def test_init_file_not_found(monkeypatch):
    monkeypatch.setattr(pd, "ExcelFile", lambda *_: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(FileNotFoundError):
        ProcessDashboardReports(excel_file_path="missing.xlsx")


# ======================================================
# _safe_read_excel
# ======================================================

def test_safe_read_excel_success(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({"a": [1, 2]})
    monkeypatch.setattr(pd, "read_excel", lambda *_, **__: df)

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    out = report._safe_read_excel("productionStatus")

    assert isinstance(out, pd.DataFrame)
    assert len(out) == 2


def test_safe_read_excel_missing_sheet(fake_excel_file, mock_excel_file):
    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    with pytest.raises(ValueError):
        report._safe_read_excel("unknownSheet")


# ======================================================
# _apply_limit_range
# ======================================================

def test_apply_limit_range_dataframe(fake_excel_file, mock_excel_file):
    report = ProcessDashboardReports(
        excel_file_path=fake_excel_file,
        limit_range=(0, 1)
    )
    df = pd.DataFrame({"a": [1, 2, 3]})
    out = report._apply_limit_range(df)

    assert len(out) == 1


# ======================================================
# process_machine_quantity_map
# ======================================================

def test_process_machine_quantity_map_success(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({
        "poNo": ["PO1"],
        "itemCode": ["IT1"],
        "itemName": ["Item"],
        "machineCode": ["NO.01_ABC"],
        "moldedQuantity": [100]
    })

    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"machineQuantityMap": df})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.process_machine_quantity_map()

    assert isinstance(result, list)
    assert result[0]["machineNo"] == "NO.01"
    assert len(result[0]["items"]) == 1


def test_process_machine_quantity_map_missing_columns(fake_excel_file, mock_excel_file, monkeypatch):
    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"machineQuantityMap": pd.DataFrame({"a": [1]})})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    assert report.process_machine_quantity_map() == []


# ======================================================
# process_mold_shot_map
# ======================================================

def test_process_mold_shot_map_success(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({
        "poNo": ["PO1"],
        "itemCode": ["IT1"],
        "itemName": ["Item"],
        "moldNo": ["123-M001"],
        "shotCount": [10]
    })

    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"moldShotMap": df})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.process_mold_shot_map()

    assert result[0]["moldNo"] == "123"
    assert "items" in result[0]


# ======================================================
# process_day_quantity_map
# ======================================================

def test_process_day_quantity_map_success(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({
        "poNo": ["PO1"],
        "itemCode": ["IT1"],
        "itemName": ["Item"],
        "workingDay": ["2024-01-01"],
        "moldedQuantity": [5]
    })

    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"dayQuantityMap": df})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.process_day_quantity_map()

    assert result[0]["workingDay"] == "2024-01-01"


# ======================================================
# process_production_status
# ======================================================

def test_process_production_status_basic(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({
        "poNo": ["PO1"],
        "itemCode": ["IT1"],
        "itemName": ["Item"],
        "poReceivedDate": ["2024-01-01"]
    })

    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"productionStatus": df})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.process_production_status()

    assert isinstance(result, list)
    assert "poNo" in result[0]


# ======================================================
# process_material_component_map
# ======================================================

def test_process_material_component_map_success(fake_excel_file, mock_excel_file, monkeypatch):
    df = pd.DataFrame({
        "poNo": ["PO1"],
        "itemCode": ["IT1"],
        "itemName": ["Item"],
        "plasticResinCode": ["PR"],
        "colorMasterbatchCode": ["CM"],
        "additiveMasterbatchCode": ["AD"]
    })

    monkeypatch.setattr(
        pd,
        "read_excel",
        mock_read_excel_factory({"materialComponentMap": df})
    )

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.process_material_component_map()

    assert result[0]["details"][0]["materialComponentInfo"] == "PR | CM | AD"


# ======================================================
# generate_all_reports
# ======================================================

def test_generate_all_reports(fake_excel_file, mock_excel_file, monkeypatch):
    monkeypatch.setattr(pd, "read_excel", lambda *_, **__: pd.DataFrame())

    report = ProcessDashboardReports(excel_file_path=fake_excel_file)
    result = report.generate_all_reports()

    assert "sheet_summary" in result
    assert "machine_quantity_map" in result