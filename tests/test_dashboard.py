"""Tests for the interactive web dashboard and its CLI integration."""

from __future__ import annotations

import re
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.dashboard.data import _get_data_dir, load_all_datasets, load_table
from tar_dataset.dashboard.views.challenge_browser import render_challenge_browser
from tar_dataset.dashboard.views.predictor_view import (
    _render_custom_team_simulator,
    _render_season_forecast,
    render_predictor_view,
)
from tar_dataset.dashboard.views.season_explorer import render_season_explorer

runner = CliRunner()


def _clean_ansi(text: str) -> str:
    """Remove ANSI escape sequences from terminal output."""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def test_dashboard_data_loading(tmp_path):
    """Test loading tables from parquet or csv."""
    # Test fallback to empty dataframe when table does not exist
    df_empty = load_table("nonexistent_table", data_dir=tmp_path)
    assert df_empty.empty

    # Test loading existing parquet
    sample_df = pd.DataFrame([{"season": 1, "n_teams": 11}])
    parquet_path = tmp_path / "seasons.parquet"
    sample_df.to_parquet(parquet_path)

    loaded = load_table("seasons", data_dir=tmp_path)
    assert not loaded.empty
    assert len(loaded) == 1
    assert loaded["season"].iloc[0] == 1

    # Test loading csv fallback
    csv_df = pd.DataFrame([{"season": 2, "n_teams": 11}])
    csv_path = tmp_path / "teams.csv"
    csv_df.to_csv(csv_path, index=False)

    loaded_csv = load_table("teams", data_dir=tmp_path)
    assert not loaded_csv.empty
    assert loaded_csv["season"].iloc[0] == 2

    # Test load_all_datasets with tmp_path
    all_dfs = load_all_datasets(data_dir=str(tmp_path))
    assert "seasons" in all_dfs
    assert "teams" in all_dfs


def test_get_data_dir_resolution():
    """Verify data directory resolution finds data/processed."""
    d = _get_data_dir()
    assert d.exists()


def test_season_explorer_render():
    """Test Season Explorer view rendering with sample datasets."""
    datasets = {
        "seasons": pd.DataFrame(
            [
                {
                    "season": 1,
                    "n_teams": 11,
                    "n_legs": 13,
                    "winners": "Rob & Brennan",
                    "distance_miles": 35000,
                }
            ]
        ),
        "episodes": pd.DataFrame(
            [
                {
                    "season": 1,
                    "episode": 1,
                    "title": "Premiere",
                    "air_date": "2001-09-05",
                    "viewers_millions": 10.5,
                }
            ]
        ),
        "teams": pd.DataFrame(
            [
                {
                    "season": 1,
                    "team_name": "Rob & Brennan",
                    "relationship": "Lawyers",
                    "result": "1st",
                    "legs_won": 5,
                    "legs_completed": 13,
                    "racing_average": 2.4,
                    "podium_rate": 0.8,
                    "roadblock_split": "5-7",
                    "roadblock_equity_score": 0.83,
                }
            ]
        ),
        "contestants": pd.DataFrame(
            [
                {
                    "season": 1,
                    "name": "Rob Frisbee",
                    "relationship": "Lawyers",
                    "age": 27,
                    "roadblocks_completed": 5,
                    "hometown": "Minneapolis, MN",
                    "status": "Winner",
                }
            ]
        ),
        "legs": pd.DataFrame(
            [
                {
                    "season": 1,
                    "leg_number": 1,
                    "origin_country": "United States",
                    "destination_country": "Zambia",
                    "destination_city": "Livingstone",
                    "destination_lat": -17.85,
                    "destination_lon": 25.85,
                    "tasks_count": 3,
                    "itinerary_stops": "Livingstone Victoria Falls",
                    "narrative": "Teams fly to Zambia.",
                }
            ]
        ),
        "leg_results": pd.DataFrame(
            [
                {
                    "season": 1,
                    "leg_number": 1,
                    "team_name": "Rob & Brennan",
                    "placement": 1,
                    "raw_cell": "1st",
                    "roadblock_performer": "Rob",
                }
            ]
        ),
        "tasks": pd.DataFrame(),
    }

    with (
        patch("streamlit.selectbox", return_value=1),
        patch("streamlit.tabs") as mock_tabs,
    ):
        # Create mock tab contexts
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = mock_tab
        mock_tabs.return_value = [mock_tab, mock_tab, mock_tab, mock_tab]

        render_season_explorer(datasets)


def test_season_explorer_empty():
    """Verify season explorer handles empty dataset gracefully."""
    with patch("streamlit.warning") as mock_warning:
        render_season_explorer({})
        mock_warning.assert_called_once()


def test_challenge_browser_render():
    """Test Challenge Browser view rendering."""
    datasets = {
        "tasks": pd.DataFrame(
            [
                {
                    "season": 1,
                    "leg_number": 1,
                    "task_type": "Roadblock",
                    "performed_by": "Rob",
                    "description": "Bungee jump over gorge",
                },
                {
                    "season": 1,
                    "leg_number": 1,
                    "task_type": "Detour",
                    "performed_by": None,
                    "description": "Choice between Air or Water",
                },
                {
                    "season": 1,
                    "leg_number": 2,
                    "task_type": "Fast Forward",
                    "performed_by": None,
                    "description": "Find the key",
                },
                {
                    "season": 1,
                    "leg_number": 3,
                    "task_type": "Speed Bump",
                    "performed_by": None,
                    "description": "Wash an elephant",
                },
            ]
        ),
        "contestants": pd.DataFrame(
            [
                {
                    "season": 1,
                    "name": "Rob",
                    "relationship": "Friends",
                    "roadblocks_completed": 5,
                }
            ]
        ),
    }

    with (
        patch("streamlit.selectbox", side_effect=["All", "All"]),
        patch("streamlit.text_input", return_value="bungee"),
        patch("streamlit.tabs") as mock_tabs,
    ):
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = mock_tab
        mock_tabs.return_value = [mock_tab, mock_tab]

        render_challenge_browser(datasets)


def test_challenge_browser_empty():
    """Verify challenge browser handles empty tasks gracefully."""
    with patch("streamlit.warning") as mock_warning:
        render_challenge_browser({})
        mock_warning.assert_called_once()


def test_predictor_view_render():
    """Test Predictor view render modes."""
    datasets = {
        "seasons": pd.DataFrame([{"season": 38}]),
    }

    # Test season forecast mode
    with (
        patch("streamlit.radio", return_value="🏁 Season Forecast"),
        patch(
            "tar_dataset.dashboard.views.predictor_view._render_season_forecast"
        ) as mock_forecast,
    ):
        render_predictor_view(datasets)
        mock_forecast.assert_called_once()

    # Test custom team simulator mode
    with (
        patch("streamlit.radio", return_value="🧪 Custom Team 'What-If' Simulator"),
        patch(
            "tar_dataset.dashboard.views.predictor_view._render_custom_team_simulator"
        ) as mock_sim,
    ):
        render_predictor_view(datasets)
        mock_sim.assert_called_once()


def test_predictor_forecast_execution():
    """Test _render_season_forecast execution with mocked SeasonPredictor."""
    datasets = {"seasons": pd.DataFrame([{"season": 38}])}
    mock_prediction = {
        "season": 38,
        "total_teams": 2,
        "active_teams_count": 1,
        "eliminated_teams_count": 1,
        "current_leg": 1,
        "rankings": [
            {
                "team_name": "Team A",
                "relationship": "Brothers",
                "archetype": "siblings",
                "avg_age": 28.0,
                "avg_placement": 2.0,
                "express_pass_status": "None",
                "win_probability": 60.0,
                "top3_probability": 90.0,
                "is_eliminated": False,
                "strengths": ["Strong momentum"],
                "risks": [],
            },
            {
                "team_name": "Team B",
                "relationship": "Friends",
                "archetype": "friends",
                "avg_age": 35.0,
                "avg_placement": 8.0,
                "express_pass_status": "None",
                "win_probability": 0.0,
                "top3_probability": 0.0,
                "is_eliminated": True,
                "strengths": [],
                "risks": ["Eliminated"],
            },
        ],
    }

    with (
        patch(
            "tar_dataset.dashboard.views.predictor_view.SeasonPredictor"
        ) as mock_pred_cls,
        patch("streamlit.selectbox", side_effect=[38, "Team A"]),
    ):
        mock_instance = mock_pred_cls.return_value
        mock_instance.predict_season.return_value = mock_prediction

        _render_season_forecast(datasets)
        mock_instance.predict_season.assert_called_once_with(season=38)


def test_custom_team_simulator():
    """Test custom team evaluator simulator."""
    with (
        patch("streamlit.text_input", return_value="Custom Racers"),
        patch("streamlit.selectbox", return_value="Siblings"),
        patch("streamlit.slider", side_effect=[28, 29, 2.5]),
        patch("streamlit.checkbox", side_effect=[False, False]),
        patch("streamlit.number_input", return_value=1),
    ):
        _render_custom_team_simulator()


def test_app_main_navigation():
    """Test main entrypoint sidebar navigation."""
    from tar_dataset.dashboard.app import main

    with (
        patch("streamlit.set_page_config"),
        patch(
            "tar_dataset.dashboard.app.load_all_datasets",
            return_value={"seasons": pd.DataFrame([{"season": 1}])},
        ),
        patch("streamlit.sidebar.radio", return_value="🗺️ Season Explorer"),
        patch("tar_dataset.dashboard.app.render_season_explorer") as mock_explorer,
    ):
        main()
        mock_explorer.assert_called_once()


def test_cli_dashboard_help():
    """Test tar-dataset dashboard --help."""
    res = runner.invoke(app, ["dashboard", "--help"])
    assert res.exit_code == 0
    clean_stdout = _clean_ansi(res.stdout)
    assert "Launch interactive web dashboard" in clean_stdout
    assert "--port" in clean_stdout
    assert "--host" in clean_stdout
    assert "--browser" in clean_stdout


def test_cli_dashboard_missing_streamlit():
    """Test CLI behavior when streamlit is not installed."""
    with patch.dict(sys.modules, {"streamlit": None}):
        res = runner.invoke(app, ["dashboard"])
        # Should catch ImportError and print guidance
        assert res.exit_code == 1
        clean_stdout = _clean_ansi(res.stdout)
        assert "Streamlit is not installed" in clean_stdout
        assert "uv sync --extra dashboard" in clean_stdout


def test_cli_dashboard_launch():
    """Test CLI launches streamlit subprocess successfully."""
    with (
        patch("subprocess.run") as mock_run,
        patch.dict(sys.modules, {"streamlit": MagicMock()}),
    ):
        res = runner.invoke(
            app, ["dashboard", "--port", "9000", "--host", "127.0.0.1", "--no-browser"]
        )
        assert res.exit_code == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "streamlit" in cmd
        assert "run" in cmd
        assert "--server.port" in cmd
        assert "9000" in cmd
        assert "--server.headless" in cmd
        assert "true" in cmd


def test_app_main_navigation_other_views():
    """Test main entrypoint sidebar navigation for predictor and challenge views."""
    from tar_dataset.dashboard.app import main

    with (
        patch("streamlit.set_page_config"),
        patch(
            "tar_dataset.dashboard.app.load_all_datasets",
            return_value={"seasons": pd.DataFrame([{"season": 1}])},
        ),
        patch("streamlit.sidebar.radio", return_value="🔮 Interactive Predictor"),
        patch("tar_dataset.dashboard.app.render_predictor_view") as mock_pred,
    ):
        main()
        mock_pred.assert_called_once()

    with (
        patch("streamlit.set_page_config"),
        patch(
            "tar_dataset.dashboard.app.load_all_datasets",
            return_value={"seasons": pd.DataFrame([{"season": 1}])},
        ),
        patch("streamlit.sidebar.radio", return_value="🧩 Challenge Browser"),
        patch("tar_dataset.dashboard.app.render_challenge_browser") as mock_browser,
    ):
        main()
        mock_browser.assert_called_once()


def test_predictor_forecast_error_and_empty():
    """Test predictor error and empty handling."""
    datasets = {"seasons": pd.DataFrame([{"season": 38}])}

    # Exception case
    with (
        patch("streamlit.selectbox", return_value=38),
        patch(
            "tar_dataset.dashboard.views.predictor_view.SeasonPredictor"
        ) as mock_pred_cls,
        patch("streamlit.error") as mock_error,
    ):
        mock_instance = mock_pred_cls.return_value
        mock_instance.predict_season.side_effect = RuntimeError("Scraping failed")

        _render_season_forecast(datasets)
        mock_error.assert_called_once()

    # Empty rankings case
    with (
        patch("streamlit.selectbox", return_value=38),
        patch(
            "tar_dataset.dashboard.views.predictor_view.SeasonPredictor"
        ) as mock_pred_cls,
        patch("streamlit.warning") as mock_warn,
    ):
        mock_instance = mock_pred_cls.return_value
        mock_instance.predict_season.return_value = {"rankings": []}

        _render_season_forecast(datasets)
        mock_warn.assert_called_once()


def test_cli_dashboard_keyboard_interrupt():
    """Test CLI handles KeyboardInterrupt cleanly."""
    with (
        patch("subprocess.run", side_effect=KeyboardInterrupt),
        patch.dict(sys.modules, {"streamlit": MagicMock()}),
    ):
        res = runner.invoke(app, ["dashboard"])
        assert res.exit_code == 0
        clean_stdout = _clean_ansi(res.stdout)
        assert "Dashboard stopped" in clean_stdout


def test_dashboard_in_progress_loading(tmp_path):
    """Test detecting and appending in-progress raw season files."""
    import json

    proc_dir = tmp_path / "processed"
    raw_dir = tmp_path / "raw"
    wiki_dir = raw_dir / "wikipedia"
    proc_dir.mkdir(parents=True)
    wiki_dir.mkdir(parents=True)

    # Base processed tables has Season 1
    base_seasons = pd.DataFrame(
        [{"season": 1, "n_teams": 11, "winners": "Rob & Brennan"}]
    )
    base_seasons.to_parquet(proc_dir / "seasons.parquet")

    # Raw Wikipedia has in-progress Season 39 (winners pending)
    s39_raw = {
        "season": 39,
        "version": "US",
        "infobox": {"winners": "TBD"},
        "contestants": [
            {
                "name": "Racer A",
                "age": 28,
                "relationship": "Brothers",
                "status": "Active",
            },
            {
                "name": "Racer B",
                "age": 26,
                "relationship": "Brothers",
                "status": "Active",
            },
        ],
        "results": [],
        "legs": [],
        "episodes": [],
    }
    (wiki_dir / "season_us_39.json").write_text(json.dumps(s39_raw), encoding="utf-8")

    loaded = load_all_datasets(
        data_dir=str(proc_dir), raw_dir=str(raw_dir), include_in_progress=True
    )
    assert 39 in loaded["seasons"]["season"].values
    assert 1 in loaded["seasons"]["season"].values
    assert len(loaded["contestants"][loaded["contestants"]["season"] == 39]) == 2
