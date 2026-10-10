"""Unit and integration tests for SeasonPredictor and predictive CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.predictor import SeasonPredictor, categorize_relationship

runner = CliRunner()


def test_categorize_relationship():
    assert categorize_relationship("Brothers") == "siblings"
    assert categorize_relationship("Sisters & Best Friends") == "siblings"
    assert categorize_relationship("Married Entrepreneurs") == "married"
    assert categorize_relationship("Dating Reality Stars") == "dating"
    assert categorize_relationship("Childhood Friends") == "friends"
    assert categorize_relationship("Mother & Daughter") == "parent_child"
    assert categorize_relationship("Father & Son") == "parent_child"
    assert categorize_relationship("Grandfather & Grandson") == "grandparent_grandchild"
    assert categorize_relationship("Strangers") == "strangers"
    assert categorize_relationship("Astronauts") == "other"


def test_season_predictor_baselines(tmp_path: Path):
    predictor = SeasonPredictor(processed_dir=tmp_path)
    assert "winner_mean_age" in predictor.baselines
    assert predictor.baselines["winner_mean_age"] > 20
    assert 1 in predictor.baselines["leg1_finish_win_rates"]


def test_score_team_eliminated():
    predictor = SeasonPredictor()
    res = predictor.score_team(
        team_name="Zach & Nate",
        relationship="Brothers",
        racers=[{"name": "Zach", "age": 30}, {"name": "Nate", "age": 27}],
        placements=[{"placement": 13}],
        is_eliminated=True,
    )
    assert res["is_eliminated"] is True
    assert res["win_probability"] == 0.0
    assert res["top3_probability"] == 0.0


def test_score_team_active():
    predictor = SeasonPredictor()
    res = predictor.score_team(
        team_name="Conner & Garrett",
        relationship="Childhood Friends",
        racers=[{"name": "Conner", "age": 27}, {"name": "Garrett", "age": 27}],
        placements=[{"placement": 2}],
        has_express_pass=True,
        used_express_pass=False,
        is_eliminated=False,
    )
    assert res["is_eliminated"] is False
    assert res["avg_age"] == 27.0
    assert res["avg_placement"] == 2.0
    assert res["express_pass_status"] == "Active / Intact"
    assert res["raw_score"] > -10.0


def test_predict_season_mock():
    predictor = SeasonPredictor()
    mock_data = {
        "contestants": [
            {
                "name": "Alice Smith",
                "age": 28,
                "relationship": "Sisters",
                "status": "Participating",
            },
            {
                "name": "Bobbie Smith",
                "age": 26,
                "relationship": "Sisters",
                "status": "Participating",
            },
            {
                "name": "Charlie Brown",
                "age": 50,
                "relationship": "Father & Son",
                "status": "Participating",
            },
            {
                "name": "David Brown",
                "age": 20,
                "relationship": "Father & Son",
                "status": "Participating",
            },
            {
                "name": "Evan Green",
                "age": 30,
                "relationship": "Dating",
                "status": "Eliminated 1st",
            },
            {
                "name": "Fiona Green",
                "age": 29,
                "relationship": "Dating",
                "status": "Eliminated 1st",
            },
        ],
        "results": [
            {
                "team_name": "Alice & Bobbie",
                "placements": [{"placement": 1, "raw_cell": "1st"}],
            },
            {
                "team_name": "Charlie & David",
                "placements": [{"placement": 2, "raw_cell": "2nd"}],
            },
            {
                "team_name": "Evan & Fiona",
                "placements": [{"placement": 3, "raw_cell": "3rd †"}],
            },
        ],
    }

    with (
        patch.object(predictor, "predict_season", wraps=predictor.predict_season),
        patch("pathlib.Path.exists", return_value=False),
        patch(
            "tar_dataset.scrapers.wikipedia.WikipediaScraper.scrape_season",
            return_value=mock_data,
        ),
    ):
        predictions = predictor.predict_season(season=99)
        assert predictions["season"] == 99
        assert predictions["total_teams"] == 3
        assert predictions["active_teams_count"] == 2
        assert predictions["eliminated_teams_count"] == 1

        # Check probabilities sum to ~100%
        active = [t for t in predictions["rankings"] if not t["is_eliminated"]]
        total_prob = sum(t["win_probability"] for t in active)
        assert 99.0 <= total_prob <= 101.0

        # Sibling pair in prime age with 1st place should outrank Father & Son with large age gap
        assert active[0]["team_name"] == "Alice & Bobbie"


def test_cli_predict(tmp_path: Path):
    output_file = tmp_path / "predictions.json"
    result = runner.invoke(
        app,
        [
            "predict",
            "--season",
            "39",
            "--top",
            "3",
            "--detail",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "Running TAR predictive engine for Season 39" in result.stdout
    assert "Contender Rankings" in result.stdout
    assert "Detailed Team Diagnostics" in result.stdout
    assert output_file.exists()

    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["season"] == 39
    assert len(data["rankings"]) >= 10


def test_update_predictions_docs(tmp_path: Path):
    readme_path = tmp_path / "README.md"
    docs_path = tmp_path / "docs" / "predictions.md"
    data_dir = tmp_path / "data" / "predictions"
    readme_path.write_text(
        "## :package: Release Asset Packages\nDetails\n", encoding="utf-8"
    )

    predictor = SeasonPredictor()
    res = predictor.update_predictions_docs(
        season=39,
        readme_path=readme_path,
        docs_path=docs_path,
        data_dir=data_dir,
    )
    assert res["season"] == 39
    assert docs_path.exists()
    assert (data_dir / "season_39" / f"leg_{res['current_leg']}.json").exists()

    docs_text = docs_path.read_text(encoding="utf-8")
    assert "The Amazing Race Season 39 Empirical Predictions" in docs_text
    assert "Weekly Win Probability Trajectory" in docs_text
    assert "Prediction Accuracy vs Actual Leg Outcomes" in docs_text

    readme_text = readme_path.read_text(encoding="utf-8")
    assert "Live Empirical Predictions (Season 39" in readme_text
    assert "docs/predictions.md" in readme_text


def test_cli_predict_update_docs(tmp_path: Path):
    mock_readme = tmp_path / "README.md"
    mock_docs = tmp_path / "docs" / "predictions.md"
    mock_data = tmp_path / "data" / "predictions"
    mock_readme.write_text("## :package: Release Asset Packages\n", encoding="utf-8")

    with patch.object(
        SeasonPredictor,
        "update_predictions_docs",
        return_value={
            "docs_file": str(mock_docs),
            "readme_file": str(mock_readme),
            "snapshot_file": str(mock_data / "season_39" / "leg_3.json"),
        },
    ) as mock_update:
        result = runner.invoke(
            app,
            [
                "predict",
                "--season",
                "39",
                "--update-docs",
            ],
        )
        assert result.exit_code == 0
        assert "Updated prediction documentation" in result.stdout
        mock_update.assert_called_once_with(season=39)


def test_score_team_roadblock_equity():
    """Verify that roadblock equity score affects predictor scoring, strengths, and risks."""
    predictor = SeasonPredictor()
    racers = [{"name": "Rob", "age": 28}, {"name": "Brennan", "age": 28}]
    placements = [{"placement": 2}]

    # Neutral baseline
    base = predictor.score_team(
        team_name="Rob & Brennan",
        relationship="Lawyers",
        racers=racers,
        placements=placements,
    )
    assert base["roadblock_equity_score"] is None

    # Balanced team (equity >= 0.85)
    balanced = predictor.score_team(
        team_name="Rob & Brennan",
        relationship="Lawyers",
        racers=racers,
        placements=placements,
        roadblock_equity_score=0.92,
    )
    assert balanced["roadblock_equity_score"] == 0.92
    assert balanced["raw_score"] > base["raw_score"]
    assert any("Balanced Roadblock distribution" in s for s in balanced["strengths"])

    # Imbalanced team (equity < 0.60)
    imbalanced = predictor.score_team(
        team_name="Rob & Brennan",
        relationship="Lawyers",
        racers=racers,
        placements=placements,
        roadblock_equity_score=0.45,
    )
    assert imbalanced["roadblock_equity_score"] == 0.45
    assert imbalanced["raw_score"] < base["raw_score"]
    assert any("Severe Roadblock imbalance" in r for r in imbalanced["risks"])

    # Eliminated team
    elim = predictor.score_team(
        team_name="Rob & Brennan",
        relationship="Lawyers",
        racers=racers,
        placements=placements,
        is_eliminated=True,
        roadblock_equity_score=0.50,
    )
    assert elim["is_eliminated"] is True
    assert elim["roadblock_equity_score"] == 0.50
