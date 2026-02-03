import pytest

from agents.analyticsOrchestrator.analyzers.configs.performance_analyzer_config import (
    PerformanceAnalyzerConfig,
    LevelConfig,
)

# =========================
# __post_init__ defaults
# =========================

def test_defaults_when_all_none(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config
    )

    assert config.enable_day_level_processor is False
    assert config.enable_month_level_processor is False
    assert config.enable_year_level_processor is False
    assert config.save_multi_level_performance_analyzer_log is False


def test_logging_enabled_when_any_level_enabled(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_day_level_processor=True,
    )

    assert config.save_multi_level_performance_analyzer_log is True


# =========================
# Day level defaults
# =========================

def test_day_level_default_save_result_applied(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_day_level_processor=True,
        day_level_processor_params=LevelConfig(save_result=None),
    )

    assert config.day_level_processor_params.save_result is True


# =========================
# Month level defaults
# =========================

def test_month_level_save_result_true_when_timestamp_provided(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_month_level_processor=True,
        month_level_processor_params=LevelConfig(
            requested_timestamp="2024-01"
        ),
    )

    assert config.month_level_processor_params.save_result is True


def test_month_level_save_result_false_when_no_timestamp(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_month_level_processor=True,
        month_level_processor_params=LevelConfig(),
    )

    assert config.month_level_processor_params.save_result is False


# =========================
# Year level defaults
# =========================

def test_year_level_save_result_true_when_timestamp_provided(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_year_level_processor=True,
        year_level_processor_params=LevelConfig(
            requested_timestamp="2024"
        ),
    )

    assert config.year_level_processor_params.save_result is True


def test_year_level_save_result_false_when_no_timestamp(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_year_level_processor=True,
        year_level_processor_params=LevelConfig(),
    )

    assert config.year_level_processor_params.save_result is False


# =========================
# Validation
# =========================

def test_validate_raises_for_month_without_timestamp(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_month_level_processor=True,
        month_level_processor_params=LevelConfig(),
    )

    with pytest.raises(ValueError):
        config.validate()


def test_validate_raises_for_year_without_timestamp(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_year_level_processor=True,
        year_level_processor_params=LevelConfig(),
    )

    with pytest.raises(ValueError):
        config.validate()


def test_validate_passes_when_required_timestamps_present(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_month_level_processor=True,
        enable_year_level_processor=True,
        month_level_processor_params=LevelConfig(requested_timestamp="2024-01"),
        year_level_processor_params=LevelConfig(requested_timestamp="2024"),
    )

    config.validate()  # should not raise


# =========================
# get_enabled_levels
# =========================

def test_get_enabled_levels_multiple(mock_shared_source_config):
    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_day_level_processor=True,
        enable_year_level_processor=True,
    )

    assert set(config.get_enabled_levels()) == {"DAY", "YEAR"}


# =========================
# get_level_params
# =========================

def test_get_level_params_returns_only_enabled_levels(mock_shared_source_config):
    day_params = LevelConfig()
    month_params = LevelConfig(requested_timestamp="2024-01")

    config = PerformanceAnalyzerConfig(
        shared_source_config=mock_shared_source_config,
        enable_day_level_processor=True,
        enable_month_level_processor=True,
        day_level_processor_params=day_params,
        month_level_processor_params=month_params,
    )

    params = config.get_level_params()

    assert params["DAY"] is day_params
    assert params["MONTH"] is month_params
    assert "YEAR" not in params
