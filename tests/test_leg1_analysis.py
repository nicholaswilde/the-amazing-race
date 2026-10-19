"""Unit tests for First Leg Winner trajectory and Episode 1 curse analysis."""

from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.leg1_analysis import (
    Leg1Analyzer,
    Leg1Metrics,
    classify_final_tier,
    classify_leg1_tier,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_classify_leg1_and_final_tiers():
    """Verify Leg 1 and Final placement tier classification helpers."""
    assert classify_leg1_tier(1) == "1st (Leg 1 Winner)"
    assert classify_leg1_tier(2) == "2nd-3rd (Leg 1 Podium)"
    assert classify_leg1_tier(3) == "2nd-3rd (Leg 1 Podium)"
    assert classify_leg1_tier(4) == "4th-7th (Mid-Pack)"
    assert classify_leg1_tier(7) == "4th-7th (Mid-Pack)"
    assert classify_leg1_tier(8) == "8th+ (Back-Pack)"
    assert classify_leg1_tier(11) == "8th+ (Back-Pack)"

    assert classify_final_tier(1) == "1st (Champion)"
    assert classify_final_tier(2) == "2nd-3rd (Finalist)"
    assert classify_final_tier(3) == "2nd-3rd (Finalist)"
    assert classify_final_tier(4) == "4th-7th (Mid-Race Exit)"
    assert classify_final_tier(7) == "4th-7th (Mid-Race Exit)"
    assert classify_final_tier(8) == "8th+ (Early Exit)"
    assert classify_final_tier(11) == "8th+ (Early Exit)"


def test_leg1_analyzer_us_metrics():
    """Verify empirical metrics for 41 US Leg 1 winners and 431 completed teams."""
    analyzer = Leg1Analyzer()
    metrics = analyzer.analyze(version="US")

    assert isinstance(metrics, Leg1Metrics)
    assert metrics.version == "US"
    assert metrics.total_completed_teams == 431
    assert metrics.pearson_r == pytest.approx(0.4102, abs=0.01)
    assert metrics.ols_slope == pytest.approx(0.4149, abs=0.01)
    assert metrics.ols_intercept == pytest.approx(3.6772, abs=0.05)

    assert metrics.total_leg1_winners == 41
    assert metrics.champion_count == 10
    assert metrics.champion_rate == pytest.approx(0.2439, abs=0.01)
    assert metrics.podium_count == 23
    assert metrics.podium_rate == pytest.approx(0.561, abs=0.01)
    assert metrics.final_four_count == 26
    assert metrics.final_four_rate == pytest.approx(0.6341, abs=0.01)

    assert metrics.collapse_count == 18
    assert metrics.collapse_rate == pytest.approx(0.439, abs=0.01)
    assert metrics.mid_collapse_count == 9
    assert metrics.mid_collapse_rate == pytest.approx(0.2195, abs=0.01)
    assert metrics.early_flameout_count == 9
    assert metrics.early_flameout_rate == pytest.approx(0.2195, abs=0.01)

    assert metrics.mean_final_result == pytest.approx(4.22, abs=0.05)
    assert metrics.median_final_result == 3.0

    # U-Turn targeting hazard on Leg 1 winners
    assert metrics.uturned_winner_count == 6
    assert metrics.uturned_winner_elim_count == 4
    assert metrics.uturned_winner_elim_rate == pytest.approx(0.6667, abs=0.01)

    # Transition matrix verification
    w1_row = metrics.transition_matrix["1st (Leg 1 Winner)"]
    assert w1_row == {
        "1st (Champion)": 10,
        "2nd-3rd (Finalist)": 13,
        "4th-7th (Mid-Race Exit)": 9,
        "8th+ (Early Exit)": 9,
    }


def test_leg1_champions_and_uturned_collapses():
    """Verify the 10 US wire-to-wire champions and 4 U-Turned Leg 1 winner eliminations."""
    analyzer = Leg1Analyzer()
    instances = analyzer.extract_winner_instances(version="US")

    winners = [(i.season, i.team_name) for i in instances if i.is_winner]
    assert len(winners) == 10
    assert (1, "Rob & Brennan") in winners
    assert (10, "Tyler & James") in winners
    assert (15, "Meghan & Cheyne") in winners
    assert (20, "Rachel & Dave") in winners
    assert (34, "Derek & Claire") in winners
    assert (37, "Carson & Jack") in winners
    assert (38, "Jas & Jag") in winners

    ut_elims = [(i.season, i.team_name) for i in instances if i.eliminated_by_uturn]
    assert ut_elims == [
        (21, "Abbie & Ryan"),
        (24, "Jet & Cord"),
        (27, "Tanner & Josh"),
        (29, "Seth & Olive"),
    ]


def test_leg1_international_and_dataframe_export():
    """Verify extraction across Canada, Australia, ALL, and DataFrame/dict serialization."""
    analyzer = Leg1Analyzer()

    can_metrics = analyzer.analyze(version="CAN")
    assert can_metrics.total_completed_teams == 103
    assert can_metrics.total_leg1_winners == 10
    assert can_metrics.champion_count == 2
    assert can_metrics.podium_count == 5
    assert can_metrics.pearson_r == pytest.approx(0.4959, abs=0.01)

    aus_metrics = analyzer.analyze(version="AUS")
    assert aus_metrics.total_completed_teams == 89
    assert aus_metrics.total_leg1_winners == 8
    assert aus_metrics.champion_count == 1
    assert aus_metrics.podium_count == 4
    assert aus_metrics.pearson_r == pytest.approx(0.3147, abs=0.01)

    all_metrics = analyzer.analyze(version="ALL")
    assert all_metrics.total_completed_teams == 623
    assert all_metrics.total_leg1_winners == 59
    assert all_metrics.champion_count == 13
    assert all_metrics.podium_count == 32
    assert all_metrics.pearson_r == pytest.approx(0.4055, abs=0.01)

    df = analyzer.to_dataframe(version="US")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 41
    for col in [
        "version",
        "season",
        "team_name",
        "leg1_placement",
        "final_result",
        "final_tier",
        "elimination_leg",
        "is_winner",
        "is_podium",
        "is_mid_collapse",
        "is_early_flameout",
        "was_uturned",
        "eliminated_by_uturn",
    ]:
        assert col in df.columns

    summary = analyzer.summary_dict(version="US")
    assert summary["total_leg1_winners"] == 41
    assert "instances" not in summary


def test_leg1_empty_tables(tmp_path):
    """Verify analyzer handles empty tables without division by zero."""
    for name, cols in [
        (
            "leg_results",
            ["version", "season", "leg_number", "team_name", "placement", "raw_cell"],
        ),
        (
            "teams",
            [
                "version",
                "season",
                "team_name",
                "result",
                "legs_completed",
                "racing_average",
            ],
        ),
    ]:
        pd.DataFrame(columns=cols).to_parquet(tmp_path / f"{name}.parquet")

    empty_analyzer = Leg1Analyzer(data_dir=tmp_path)
    metrics = empty_analyzer.analyze(version="US")
    assert metrics.total_leg1_winners == 0
    assert metrics.pearson_r == 0.0
    assert metrics.instances == []
    assert empty_analyzer.to_dataframe(version="US").empty


def test_leg1_cli(cli_runner: CliRunner):
    """Verify `tar-dataset leg1` CLI sub-command execution."""
    res_us = cli_runner.invoke(app, ["leg1", "--version", "US"])
    assert res_us.exit_code == 0
    assert (
        "First Leg Winner Trajectory & Episode 1 Curse Analysis (US)" in res_us.output
    )
    assert "Total Leg 1 Winners: 41" in res_us.output
    assert "Championship Winners (1st): 10 (24.4%)" in res_us.output

    res_full = cli_runner.invoke(app, ["leg1", "--instances"])
    assert res_full.exit_code == 0
    assert "All Leg 1 Winning Teams (US)" in res_full.output

    res_none = cli_runner.invoke(app, ["leg1", "--version", "NONEXISTENT"])
    assert res_none.exit_code == 0
    assert "No Leg 1 winner instances found" in res_none.output
