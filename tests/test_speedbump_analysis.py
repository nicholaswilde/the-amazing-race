"""Unit tests for Speed Bump penalty efficacy and post-NEL survival lag analysis."""

from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.speedbump_analysis import (
    SpeedBumpAnalyzer,
    SpeedBumpMetrics,
    match_team_from_description,
    normalize_text,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_normalize_text_and_team_matching():
    """Verify text normalization and robust team name resolution."""
    raw = "For their Speed Bump, Tim Sr. & Tim Jr. had to build a tent!"
    norm = normalize_text(raw)
    assert "tim sr and tim jr" in norm

    candidates = ["Tim Sr. & Tim Jr.", "Jody & Cory", "Vanessa & Celina"]
    matched = match_team_from_description(raw, candidates)
    assert matched == "Tim Sr. & Tim Jr."

    # Substring boundary check
    raw_jordan = "For their Speed Bump, Jordan & Jeff had to reinforce a trench wall with branches"
    cand_jordan = ["Dan & Jordan", "Jordan & Jeff", "Brent & Caite"]
    assert match_team_from_description(raw_jordan, cand_jordan) == "Jordan & Jeff"


def test_speedbump_analyzer_us_metrics():
    """Verify empirical metrics for 44 US Speed Bump penalty instances."""
    analyzer = SpeedBumpAnalyzer()
    metrics = analyzer.analyze(version="US")

    assert isinstance(metrics, SpeedBumpMetrics)
    assert metrics.version == "US"
    assert metrics.total_instances == 44

    # Elimination vs Survival on penalty leg
    assert metrics.eliminated_on_leg_count == 18
    assert metrics.eliminated_on_leg_rate == pytest.approx(0.409, abs=0.01)
    assert metrics.survived_leg_count == 26
    assert metrics.survived_leg_rate == pytest.approx(0.591, abs=0.01)

    # Leg placement dynamics
    assert metrics.mean_placement == pytest.approx(4.95, abs=0.05)
    assert metrics.median_placement == 5.0
    assert metrics.placement_counts[1] == 3
    assert metrics.placement_counts[6] == 10

    # Post-penalty survival horizon
    assert metrics.mean_survival_lag == pytest.approx(1.98, abs=0.05)
    assert metrics.median_survival_lag == 1.0
    assert metrics.survival_lag_distribution[0] == 18
    assert metrics.survival_lag_distribution[1] == 7

    # Conversion to Finale & Podium
    assert metrics.podium_count == 15
    assert metrics.podium_rate == pytest.approx(0.341, abs=0.01)
    assert metrics.winner_count == 2
    assert metrics.winner_rate == pytest.approx(0.045, abs=0.01)
    assert metrics.finale_count == 16
    assert metrics.finale_rate == pytest.approx(0.364, abs=0.01)


def test_speedbump_champions_identified():
    """Verify that the two winning teams overcoming Speed Bumps are correctly matched."""
    analyzer = SpeedBumpAnalyzer()
    instances = analyzer.extract_instances(version="US")

    winners = [i for i in instances if i.is_winner]
    assert len(winners) == 2

    winner_tuples = [(w.season, w.team_name) for w in winners]
    assert (12, "TK & Rachel") in winner_tuples
    assert (21, "Josh & Brent") in winner_tuples


def test_speedbump_dataframe_and_summary_dict():
    """Verify dataframe export and summary dictionary serialization."""
    analyzer = SpeedBumpAnalyzer()
    df = analyzer.to_dataframe(version="US")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 44
    expected_cols = [
        "version",
        "season",
        "leg_number",
        "team_name",
        "placement",
        "eliminated_on_leg",
        "legs_survived_after",
        "is_winner",
        "is_podium",
        "reached_finale",
    ]
    for col in expected_cols:
        assert col in df.columns

    summary = analyzer.summary_dict(version="US")
    assert isinstance(summary, dict)
    assert summary["total_instances"] == 44
    assert summary["eliminated_on_leg_count"] == 18
    assert "instances" not in summary  # Excluded from concise summary


def test_speedbump_international_versions():
    """Verify extraction works across Canada and Australia datasets."""
    analyzer = SpeedBumpAnalyzer()

    can_metrics = analyzer.analyze(version="CAN")
    assert can_metrics.total_instances == 16
    assert can_metrics.eliminated_on_leg_count == 3

    all_metrics = analyzer.analyze(version="ALL")
    assert all_metrics.total_instances >= 65


def test_speedbump_synthetic_empty_data(tmp_path):
    """Verify analyzer handles empty tables gracefully without division by zero."""
    for table_name in ["tasks", "leg_results", "teams"]:
        df = pd.DataFrame(
            columns=["version", "season", "leg_number", "task_type", "description"]
        )
        df.to_parquet(tmp_path / f"{table_name}.parquet")

    empty_analyzer = SpeedBumpAnalyzer(data_dir=tmp_path)
    metrics = empty_analyzer.analyze(version="US")

    assert metrics.total_instances == 0
    assert metrics.eliminated_on_leg_count == 0
    assert metrics.eliminated_on_leg_rate == 0.0
    assert metrics.mean_placement == 0.0
    assert metrics.instances == []


def test_speedbump_cli(cli_runner: CliRunner):
    """Verify `tar-dataset speedbump` CLI sub-command execution."""
    res_us = cli_runner.invoke(app, ["speedbump", "--version", "US"])
    assert res_us.exit_code == 0
    assert "Speed Bump Penalty Efficacy & Post-NEL Survival (US)" in res_us.output
    assert "Total Recorded Speed Bumps: 44" in res_us.output
    assert "Eliminated on Penalty Leg: 18 (40.9%)" in res_us.output

    res_inst = cli_runner.invoke(app, ["speedbump", "--instances"])
    assert res_inst.exit_code == 0
    assert "All Speed Bump Instances (US)" in res_inst.output

    res_none = cli_runner.invoke(app, ["speedbump", "--version", "NONEXISTENT"])
    assert res_none.exit_code == 0
    assert "No Speed Bump instances found" in res_none.output
