"""Unit tests for U-Turn lethality, retaliation dynamics, and defensive burn analysis."""

from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.uturn_analysis import (
    UTurnAnalyzer,
    UTurnMetrics,
    match_teams_in_order,
    normalize_text,
    resolve_user_for_victim,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_normalize_and_user_resolution():
    """Verify text normalization, ordered team matching, and user-to-victim resolution."""
    narrative = (
        "This leg featured a Double U-Turn. "
        "Nat & Kat chose to use the U-Turn on Chad & Stephanie, "
        "while Jill & Thomas chose to use the U-Turn on Brook & Claire."
    )
    assert "nat and kat" in normalize_text(narrative)

    ordered = match_teams_in_order(
        narrative, ["Brook & Claire", "Nat & Kat", "Jill & Thomas", "Chad & Stephanie"]
    )
    assert ordered == [
        "Nat & Kat",
        "Chad & Stephanie",
        "Jill & Thomas",
        "Brook & Claire",
    ]

    users = ["Nat & Kat", "Jill & Thomas"]
    assert resolve_user_for_victim("Chad & Stephanie", users, narrative) == "Nat & Kat"
    assert (
        resolve_user_for_victim("Brook & Claire", users, narrative) == "Jill & Thomas"
    )
    assert resolve_user_for_victim("Steve & Anna Leigh", [], narrative) == "Live Vote"


def test_uturn_analyzer_us_metrics():
    """Verify empirical metrics for 61 US U-Turn victim instances."""
    analyzer = UTurnAnalyzer()
    metrics = analyzer.analyze(version="US")

    assert isinstance(metrics, UTurnMetrics)
    assert metrics.version == "US"
    assert metrics.total_victims == 61

    # Immediate lethality & survival
    assert metrics.eliminated_on_leg_count == 30
    assert metrics.eliminated_on_leg_rate == pytest.approx(0.4918, abs=0.01)
    assert metrics.survived_leg_count == 31
    assert metrics.survived_leg_rate == pytest.approx(0.5082, abs=0.01)

    # Placement recovery on leg
    assert metrics.leg_podium_count == 4
    assert metrics.leg_podium_rate == pytest.approx(0.0656, abs=0.01)
    assert metrics.mean_placement == pytest.approx(5.92, abs=0.05)
    assert metrics.median_placement == 6.0

    # Post-U-Turn survival lag & final conversion
    assert metrics.mean_survival_lag == pytest.approx(2.08, abs=0.05)
    assert metrics.survivor_mean_survival_lag == pytest.approx(4.10, abs=0.05)
    assert metrics.podium_count == 15
    assert metrics.podium_rate == pytest.approx(0.2459, abs=0.01)
    assert metrics.winner_count == 4
    assert metrics.winner_rate == pytest.approx(0.0656, abs=0.01)

    # Double U-Turn Chain vs Defensive Burns
    assert metrics.chain_uturn_count == 9
    assert metrics.chain_uturn_survived_count == 7
    assert metrics.chain_uturn_survival_rate == pytest.approx(0.7778, abs=0.01)
    assert metrics.wasted_uturn_count == 11
    assert metrics.double_board_burn_count == 8
    assert metrics.double_board_burn_elim_rate == pytest.approx(0.875, abs=0.01)
    assert metrics.intentional_defensive_burn_count == 5
    assert metrics.intentional_defensive_burn_elim_rate == pytest.approx(1.0, abs=0.01)

    # Blind vs Public vs Vote dynamics
    assert metrics.total_users == 53
    assert metrics.blind_users_count == 9
    assert metrics.public_users_count == 44
    assert metrics.blind_user_retaliation_rate == pytest.approx(0.1111, abs=0.01)
    assert metrics.public_user_retaliation_rate == pytest.approx(0.1818, abs=0.01)
    assert metrics.blind_victim_elim_rate == pytest.approx(0.6667, abs=0.01)
    assert metrics.public_victim_elim_rate == pytest.approx(0.4773, abs=0.01)
    assert metrics.vote_victim_elim_rate == pytest.approx(0.375, abs=0.01)


def test_uturn_champions_and_defensive_burns():
    """Verify the 4 US championship winners and 5 intentional defensive burns."""
    analyzer = UTurnAnalyzer()
    instances = analyzer.extract_instances(version="US")
    winners = [(i.season, i.team_name) for i in instances if i.is_winner]
    assert len(winners) == 4
    assert (24, "Dave & Connor") in winners
    assert (30, "Cody & Jessica") in winners
    assert (31, "Colin & Christie") in winners
    assert (38, "Jas & Jag") in winners

    burns = analyzer.extract_burn_events(version="US")
    def_burns = [b for b in burns if b.is_intentional_defensive]
    assert len(def_burns) == 5
    assert all(b.primary_victim_eliminated for b in def_burns)
    def_seasons = [b.season for b in def_burns]
    assert def_seasons == [21, 24, 28, 29, 32]


def test_uturn_international_and_dataframe_export():
    """Verify extraction across Canada, Australia, ALL, and DataFrame/dict serialization."""
    analyzer = UTurnAnalyzer()

    can_metrics = analyzer.analyze(version="CAN")
    assert can_metrics.total_victims == 21
    assert can_metrics.eliminated_on_leg_count == 6

    aus_metrics = analyzer.analyze(version="AUS")
    assert aus_metrics.total_victims == 9
    assert aus_metrics.eliminated_on_leg_count == 3

    all_metrics = analyzer.analyze(version="ALL")
    assert all_metrics.total_victims == 91
    assert all_metrics.eliminated_on_leg_count == 39

    df = analyzer.to_dataframe(version="US")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 61
    for col in [
        "version",
        "season",
        "leg_number",
        "team_name",
        "user_team",
        "board_type",
        "is_blind",
        "is_chain_uturn",
        "second_slot_burned",
        "eliminated_on_leg",
        "is_leg_podium",
        "is_winner",
    ]:
        assert col in df.columns

    summary = analyzer.summary_dict(version="US")
    assert summary["total_victims"] == 61
    assert "instances" not in summary
    assert "burn_events" not in summary


def test_uturn_empty_tables(tmp_path):
    """Verify analyzer handles empty tables without division by zero."""
    for name, cols in [
        ("leg_results", ["version", "season", "leg_number", "team_name", "raw_cell"]),
        ("legs", ["version", "season", "leg_number", "narrative"]),
        ("teams", ["version", "season", "team_name", "result"]),
    ]:
        pd.DataFrame(columns=cols).to_parquet(tmp_path / f"{name}.parquet")

    empty_analyzer = UTurnAnalyzer(data_dir=tmp_path)
    metrics = empty_analyzer.analyze(version="US")
    assert metrics.total_victims == 0
    assert metrics.eliminated_on_leg_rate == 0.0
    assert metrics.instances == []
    assert metrics.burn_events == []
    assert empty_analyzer.to_dataframe(version="US").empty


def test_uturn_cli(cli_runner: CliRunner):
    """Verify `tar-dataset uturn` CLI sub-command execution."""
    res_us = cli_runner.invoke(app, ["uturn", "--version", "US"])
    assert res_us.exit_code == 0
    assert (
        "U-Turn Lethality, Retaliation & Defensive Burn Analysis (US)" in res_us.output
    )
    assert "Total U-Turn Victims: 61" in res_us.output
    assert "Eliminated on U-Turn Leg: 30 (49.2%)" in res_us.output

    res_full = cli_runner.invoke(app, ["uturn", "--instances", "--burns"])
    assert res_full.exit_code == 0
    assert "Burned & Wasted U-Turn Attempts (US)" in res_full.output
    assert "All U-Turn Victim Instances (US)" in res_full.output

    res_none = cli_runner.invoke(app, ["uturn", "--version", "NONEXISTENT"])
    assert res_none.exit_code == 0
    assert "No U-Turn instances found" in res_none.output
