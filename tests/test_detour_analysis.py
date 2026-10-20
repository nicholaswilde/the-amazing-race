"""Tests for Detour branch switching, task archetype, and sunk-cost analysis."""

from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.detour_analysis import (
    DetourAnalyzer,
    classify_detour_branch,
)

runner = CliRunner()


def test_classify_detour_branch() -> None:
    """Verify keyword classification across all six Detour branch archetypes."""
    assert (
        classify_detour_branch("Quick Jump: take a tandem bungee jump off a cliff")
        == "Thrill / Heights"
    )
    assert (
        classify_detour_branch("Perform a traditional tango dance routine for a judge")
        == "Judge / Performance"
    )
    assert (
        classify_detour_branch("Search through a giant haystack to find a hidden pin")
        == "Searching / Needle"
    )
    assert (
        classify_detour_branch("Assemble an exact replica puzzle and count the blocks")
        == "Attention to Detail / Puzzle"
    )
    assert (
        classify_detour_branch("Paddle a kayak and steer a camel around floating buoys")
        == "Skill / Coordination"
    )
    assert (
        classify_detour_branch("Carry heavy sacks of coal up 200 stone stairs")
        == "Physical / Brute Force"
    )


def test_detour_analyzer_synthetic(tmp_path: Path) -> None:
    """Verify DetourAnalyzer on controlled synthetic tasks and leg_results data."""
    tasks_df = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 2,
                "task_type": "Detour",
                "description": (
                    "This leg's Detour was a choice between Jump or Hike. "
                    "In Jump, teams had to bungee jump off a canyon bridge. "
                    "In Hike, teams would have had to hike down a long trail to the bottom."
                ),
                "performed_by": None,
            },
            {
                "version": "US",
                "season": 1,
                "leg_number": 3,
                "task_type": "Detour",
                "description": (
                    "This leg's Blind Detour was a choice between Search or Dance. "
                    "In Search, teams had to dig and search for a hidden token. "
                    "In Dance, teams had to perform a salsa dance for the judges."
                ),
                "performed_by": None,
            },
        ]
    )
    tasks_df.to_parquet(tmp_path / "tasks.parquet", index=False)

    rows = [
        # Leg 1 baseline placements
        {
            "version": "US",
            "season": 1,
            "leg_number": 1,
            "team_name": "Team A",
            "placement": 1,
            "raw_cell": "1st",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 1,
            "team_name": "Team B",
            "placement": 2,
            "raw_cell": "2nd",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 1,
            "team_name": "Team C",
            "placement": 3,
            "raw_cell": "3rd",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 1,
            "team_name": "Team D",
            "placement": 4,
            "raw_cell": "4th",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 1,
            "team_name": "Team E",
            "placement": 5,
            "raw_cell": "5th",
        },
        # Leg 2 (Detour): Team A drops from 1st to 5th (delta=+4, eliminated), Team B U-Turned (2nd->4th)
        {
            "version": "US",
            "season": 1,
            "leg_number": 2,
            "team_name": "Team C",
            "placement": 1,
            "raw_cell": "1st",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 2,
            "team_name": "Team D",
            "placement": 2,
            "raw_cell": "2nd⊃",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 2,
            "team_name": "Team E",
            "placement": 3,
            "raw_cell": "3rd",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 2,
            "team_name": "Team B",
            "placement": 4,
            "raw_cell": "4th⊂",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 2,
            "team_name": "Team A",
            "placement": 5,
            "raw_cell": "5th",
        },
        # Leg 3 (Finale): remaining 4 teams
        {
            "version": "US",
            "season": 1,
            "leg_number": 3,
            "team_name": "Team C",
            "placement": 1,
            "raw_cell": "1st",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 3,
            "team_name": "Team D",
            "placement": 2,
            "raw_cell": "2nd",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 3,
            "team_name": "Team E",
            "placement": 3,
            "raw_cell": "3rd",
        },
        {
            "version": "US",
            "season": 1,
            "leg_number": 3,
            "team_name": "Team B",
            "placement": 4,
            "raw_cell": "4th",
        },
    ]
    pd.DataFrame(rows).to_parquet(tmp_path / "leg_results.parquet", index=False)

    analyzer = DetourAnalyzer(data_dir=tmp_path)
    metrics = analyzer.analyze(version="US")

    assert metrics.total_detours == 2
    assert metrics.total_branches == 4
    assert metrics.unchosen_branch_count == 1
    assert metrics.blind_detour_count == 1
    assert metrics.total_team_legs == 5
    assert metrics.clean_single_count == 3
    assert metrics.voluntary_switch_count == 1
    assert metrics.voluntary_switch_elim_rate == 1.0
    assert metrics.forced_dual_count == 1
    assert metrics.forced_dual_elim_rate == 0.0
    assert len(metrics.switch_events) == 2

    payload = metrics.to_dict()
    assert payload["version"] == "US"
    assert payload["total_branches"] == 4


def test_detour_analyzer_empty(tmp_path: Path) -> None:
    """Verify graceful empty handling when tables are missing."""
    analyzer = DetourAnalyzer(data_dir=tmp_path)
    metrics = analyzer.analyze(version="US")
    assert metrics.total_detours == 0
    assert metrics.total_team_legs == 0


def test_detour_analyzer_real_dataset() -> None:
    """Verify DetourAnalyzer against real processed dataset."""
    analyzer = DetourAnalyzer()
    us_metrics = analyzer.analyze(version="US")
    assert us_metrics.total_detours == 379
    assert us_metrics.total_branches == 758
    assert us_metrics.unchosen_branch_count == 46
    assert us_metrics.total_team_legs == 2499
    assert us_metrics.clean_single_count == 2076
    assert us_metrics.voluntary_switch_count == 363
    assert us_metrics.forced_dual_count == 60
    assert abs(us_metrics.clean_single_elim_rate - 0.0742) < 0.005
    assert abs(us_metrics.voluntary_switch_elim_rate - 0.2369) < 0.005
    assert abs(us_metrics.forced_dual_elim_rate - 0.4833) < 0.005

    all_metrics = analyzer.analyze(version="ALL")
    assert all_metrics.total_detours == 555
    assert all_metrics.total_branches == 1110
    assert all_metrics.unchosen_branch_count == 48
    assert all_metrics.total_team_legs == 3563


def test_cli_detour_command() -> None:
    """Verify CLI `detour` command output."""
    result = runner.invoke(app, ["detour", "--version", "US", "--events"])
    assert result.exit_code == 0
    assert "Detour Branch Switching & Sunk-Cost Analysis (US)" in result.stdout
    assert "Detour Task Archetype Distribution (US)" in result.stdout
    assert "Sunk-Cost Survival Threshold Curve for Contenders (US)" in result.stdout
