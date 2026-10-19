"""Unit tests for Fast Forward timing optimization, prize capture, and championship conversion."""

from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.fastforward_analysis import (
    FastForwardAnalyzer,
    FastForwardMetrics,
    classify_ff_era,
    classify_ff_timing,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_classify_era_and_timing():
    """Verify era and timing tier classification helpers."""
    assert classify_ff_era("US", 1) == "Classic (S1-S4)"
    assert classify_ff_era("US", 4) == "Classic (S1-S4)"
    assert classify_ff_era("US", 5) == "Modern Scarce (S5+)"
    assert classify_ff_era("US", 37) == "Modern Scarce (S5+)"
    assert classify_ff_era("CAN", 1) == "Modern Scarce (S5+)"

    assert classify_ff_timing(1) == "Early (Legs 1-4)"
    assert classify_ff_timing(4) == "Early (Legs 1-4)"
    assert classify_ff_timing(5) == "Mid (Legs 5-6)"
    assert classify_ff_timing(6) == "Mid (Legs 5-6)"
    assert classify_ff_timing(7) == "Late (Legs 7+)"
    assert classify_ff_timing(11) == "Late (Legs 7+)"


def test_fastforward_analyzer_us_metrics():
    """Verify empirical metrics for 54 US Fast Forward instances."""
    analyzer = FastForwardAnalyzer()
    metrics = analyzer.analyze(version="US")

    assert isinstance(metrics, FastForwardMetrics)
    assert metrics.version == "US"
    assert metrics.total_instances == 54

    # Immediate leg outcomes
    assert metrics.leg_win_count == 47
    assert metrics.leg_win_rate == pytest.approx(0.8704, abs=0.01)
    assert metrics.leg_podium_count == 50
    assert metrics.leg_podium_rate == pytest.approx(0.9259, abs=0.01)
    assert metrics.eliminated_on_leg_count == 2
    assert metrics.eliminated_on_leg_rate == pytest.approx(0.037, abs=0.01)
    assert metrics.mean_placement == pytest.approx(1.44, abs=0.05)
    assert metrics.median_placement == 1.0

    # Post-FF survival & final conversion
    assert metrics.mean_survival_lag == pytest.approx(4.30, abs=0.05)
    assert metrics.median_survival_lag == 4.0
    assert metrics.podium_count == 29
    assert metrics.podium_rate == pytest.approx(0.537, abs=0.01)
    assert metrics.winner_count == 14
    assert metrics.winner_rate == pytest.approx(0.2593, abs=0.01)

    # Timing breakdown
    assert metrics.early_count == 16
    assert metrics.early_leg_win_rate == pytest.approx(0.875, abs=0.01)
    assert metrics.early_podium_rate == pytest.approx(0.25, abs=0.01)
    assert metrics.early_winner_rate == pytest.approx(0.0625, abs=0.01)

    assert metrics.mid_count == 13
    assert metrics.mid_leg_win_rate == pytest.approx(0.9231, abs=0.01)
    assert metrics.mid_podium_rate == pytest.approx(0.5385, abs=0.01)
    assert metrics.mid_winner_rate == pytest.approx(0.3077, abs=0.01)

    assert metrics.late_count == 25
    assert metrics.late_leg_win_rate == pytest.approx(0.84, abs=0.01)
    assert metrics.late_podium_rate == pytest.approx(0.72, abs=0.01)
    assert metrics.late_winner_rate == pytest.approx(0.36, abs=0.01)

    # Era breakdown
    assert metrics.classic_era_count == 24
    assert metrics.classic_era_leg_win_rate == pytest.approx(0.875, abs=0.01)
    assert metrics.classic_era_podium_rate == pytest.approx(0.4583, abs=0.01)
    assert metrics.classic_era_winner_rate == pytest.approx(0.1667, abs=0.01)

    assert metrics.modern_era_count == 30
    assert metrics.modern_era_leg_win_rate == pytest.approx(0.8667, abs=0.01)
    assert metrics.modern_era_podium_rate == pytest.approx(0.60, abs=0.01)
    assert metrics.modern_era_winner_rate == pytest.approx(0.3333, abs=0.01)


def test_fastforward_champions_and_eliminations():
    """Verify the 14 US championship winners and 2 eliminated Fast Forward teams."""
    analyzer = FastForwardAnalyzer()
    instances = analyzer.extract_instances(version="US")

    winners = [(i.season, i.team_name) for i in instances if i.is_winner]
    assert len(winners) == 14
    assert (1, "Rob & Brennan") in winners
    assert (7, "Uchenna & Joyce") in winners
    assert (15, "Meghan & Cheyne") in winners
    assert (20, "Rachel & Dave") in winners
    assert (37, "Carson & Jack") in winners

    elims = [
        (i.season, i.leg_number, i.team_name) for i in instances if i.eliminated_on_leg
    ]
    assert elims == [
        (3, 3, "Dennis & Andrew"),
        (20, 10, "Bopper & Mark"),
    ]


def test_fastforward_international_and_dataframe_export():
    """Verify extraction across Canada, Australia, ALL, and DataFrame/dict serialization."""
    analyzer = FastForwardAnalyzer()

    can_metrics = analyzer.analyze(version="CAN")
    assert can_metrics.total_instances == 4
    assert can_metrics.leg_win_count == 3

    aus_metrics = analyzer.analyze(version="AUS")
    assert aus_metrics.total_instances == 6
    assert aus_metrics.leg_win_count == 4

    all_metrics = analyzer.analyze(version="ALL")
    assert all_metrics.total_instances == 64
    assert all_metrics.leg_win_count == 54

    df = analyzer.to_dataframe(version="US")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 54
    for col in [
        "version",
        "season",
        "leg_number",
        "team_name",
        "era",
        "timing_bucket",
        "placement",
        "won_leg",
        "is_leg_podium",
        "eliminated_on_leg",
        "is_podium",
        "is_winner",
    ]:
        assert col in df.columns

    summary = analyzer.summary_dict(version="US")
    assert summary["total_instances"] == 54
    assert "instances" not in summary


def test_fastforward_empty_tables(tmp_path):
    """Verify analyzer handles empty tables without division by zero."""
    for name, cols in [
        (
            "leg_results",
            [
                "version",
                "season",
                "leg_number",
                "team_name",
                "fast_forward",
                "placement",
            ],
        ),
        ("tasks", ["version", "season", "leg_number", "task_type", "description"]),
        ("teams", ["version", "season", "team_name", "result"]),
    ]:
        pd.DataFrame(columns=cols).to_parquet(tmp_path / f"{name}.parquet")

    empty_analyzer = FastForwardAnalyzer(data_dir=tmp_path)
    metrics = empty_analyzer.analyze(version="US")
    assert metrics.total_instances == 0
    assert metrics.leg_win_rate == 0.0
    assert metrics.instances == []
    assert empty_analyzer.to_dataframe(version="US").empty


def test_fastforward_cli(cli_runner: CliRunner):
    """Verify `tar-dataset fastforward` CLI sub-command execution."""
    res_us = cli_runner.invoke(app, ["fastforward", "--version", "US"])
    assert res_us.exit_code == 0
    assert (
        "Fast Forward Timing, Prize Capture & Championship Conversion (US)"
        in res_us.output
    )
    assert "Total Fast Forward Plays: 54" in res_us.output
    assert "Leg Win Rate (1st Place): 47 (87.0%)" in res_us.output

    res_full = cli_runner.invoke(app, ["fastforward", "--instances"])
    assert res_full.exit_code == 0
    assert "All Fast Forward Instances (US)" in res_full.output

    res_none = cli_runner.invoke(app, ["fastforward", "--version", "NONEXISTENT"])
    assert res_none.exit_code == 0
    assert "No Fast Forward instances found" in res_none.output
