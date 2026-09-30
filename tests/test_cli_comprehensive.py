"""Comprehensive tests for the Typer CLI commands in tar_dataset.cli."""

from __future__ import annotations

import pathlib
from unittest.mock import patch

import pandas as pd
from typer.testing import CliRunner

from tar_dataset.cli import app

runner = CliRunner()


def test_cli_scrape_wiki():
    with patch("tar_dataset.cli.WikipediaScraper") as mock_scraper_cls:
        mock_instance = mock_scraper_cls.return_value
        mock_instance.scrape_season.return_value = {"season": 1}
        mock_instance.scrape_all_seasons.return_value = [{"season": 1}, {"season": 2}]

        # Single season scrape
        res = runner.invoke(app, ["scrape-wiki", "--season", "1"])
        assert res.exit_code == 0
        assert "Successfully scraped and cached Season 1" in res.stdout

        # Failed single season scrape
        mock_instance.scrape_season.return_value = {}
        res = runner.invoke(app, ["scrape-wiki", "--season", "99"])
        assert res.exit_code == 0
        assert "Failed to scrape Season 99" in res.stdout

        # Range scrape
        res = runner.invoke(app, ["scrape-wiki", "--start", "1", "--end", "2"])
        assert res.exit_code == 0
        assert "Successfully scraped 2 seasons" in res.stdout


def test_cli_scrape_fandom():
    with patch("tar_dataset.cli.FandomScraper") as mock_scraper_cls:
        mock_instance = mock_scraper_cls.return_value
        mock_instance.scrape_season.return_value = {"season": 1}
        mock_instance.scrape_all.return_value = [{"season": 1}]

        # Single season scrape
        res = runner.invoke(app, ["scrape-fandom", "--season", "1"])
        assert res.exit_code == 0
        assert "Successfully scraped and cached Fandom data" in res.stdout

        # Failed single season scrape
        mock_instance.scrape_season.return_value = {}
        res = runner.invoke(app, ["scrape-fandom", "--season", "99"])
        assert res.exit_code == 0
        assert "Failed to scrape Fandom data" in res.stdout

        # Range scrape
        res = runner.invoke(app, ["scrape-fandom", "--start", "1", "--end", "2"])
        assert res.exit_code == 0
        assert "Successfully scraped 1 Fandom season pages" in res.stdout


def test_cli_scrape_reddit():
    with patch("tar_dataset.cli.RedditScraper") as mock_scraper_cls:
        mock_instance = mock_scraper_cls.return_value
        mock_instance.scrape_discussions.return_value = [{"id": "p1"}]
        mock_instance.scrape_all_categories.return_value = {
            "episode_discussion": [{"id": "p1"}],
            "live_discussion": [],
        }

        # Query scrape
        res = runner.invoke(app, ["scrape-reddit", "--query", "Test", "--limit", "5"])
        assert res.exit_code == 0
        assert "Successfully scraped and cached 1 Reddit discussions" in res.stdout

        # Batch scrape
        res = runner.invoke(app, ["scrape-reddit", "--batch"])
        assert res.exit_code == 0
        assert "Batch scraping all TAR discussion categories" in res.stdout


def test_cli_import_sheet(tmp_path):
    local_csv = tmp_path / "test.csv"
    local_csv.write_text("a,b\n1,2\n", encoding="utf-8")

    with patch("tar_dataset.cli.SheetsImporter") as mock_importer_cls:
        mock_instance = mock_importer_cls.return_value
        mock_instance.import_public_sheet_csv.return_value = pd.DataFrame({"a": [1]})
        mock_instance.import_local_csv.return_value = pd.DataFrame({"a": [1]})

        # Test Sheet ID import
        res = runner.invoke(
            app,
            ["import-sheet", "--sheet-id", "12345", "--name", "sheet1"],
        )
        assert res.exit_code == 0
        assert "Imported 1 rows" in res.stdout

        # Test CSV import
        res = runner.invoke(
            app,
            ["import-sheet", "--csv", str(local_csv), "--name", "sheet2"],
        )
        assert res.exit_code == 0
        assert "Imported 1 rows" in res.stdout

        # Missing both arguments error
        res = runner.invoke(app, ["import-sheet"])
        assert res.exit_code == 1


def test_cli_build_and_validate():
    sample_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    with (
        patch("tar_dataset.cli.DatasetBuilder") as mock_builder_cls,
        patch("tar_dataset.cli.export_to_sqlite", return_value="data/processed/tar.db"),
        patch("tar_dataset.cli.DatasetValidator") as mock_validator_cls,
    ):
        mock_builder = mock_builder_cls.return_value
        mock_builder.build_all.return_value = {
            "seasons": sample_df,
            "episodes": sample_df,
        }

        res = runner.invoke(app, ["build"])
        assert res.exit_code == 0
        assert "Generated Tidy Datasets" in res.stdout

        # Empty build result branch
        mock_builder.build_all.return_value = {}
        res = runner.invoke(app, ["build"])
        assert res.exit_code == 0
        assert "No data built" in res.stdout

        mock_validator = mock_validator_cls.return_value
        mock_validator.validate.return_value = {
            "status": "PASS",
            "row_counts": {"seasons": 36},
            "issues": [],
        }

        res = runner.invoke(app, ["validate"])
        assert res.exit_code == 0
        assert "Validation Status: PASS" in res.stdout

        # Validation with warnings
        mock_validator.validate.return_value = {
            "status": "WARNING",
            "row_counts": {"seasons": 36},
            "issues": ["Warning: missing value"],
        }
        res = runner.invoke(app, ["validate"])
        assert res.exit_code == 0
        assert "Validation Status: WARNING" in res.stdout


def test_cli_stats_and_gaps(tmp_path):
    res = runner.invoke(app, ["stats"])
    assert res.exit_code == 0
    assert "The Amazing Race Dataset" in res.stdout

    res = runner.invoke(app, ["gaps"])
    assert res.exit_code == 0
    assert "Completeness" in res.stdout

    res = runner.invoke(app, ["gaps", "--season", "1", "--detail"])
    assert res.exit_code == 0

    gap_report = tmp_path / "gaps.md"
    res = runner.invoke(app, ["gaps", "--export-md", str(gap_report)])
    assert res.exit_code == 0
    assert gap_report.exists()


def test_cli_exports_and_eval():
    with (
        patch("tar_dataset.cli.export_to_sqlite") as mock_sqlite,
        patch("tar_dataset.cli.export_arrow_and_hf") as mock_arrow,
        patch("tar_dataset.cli.AIExportBuilder") as mock_ai,
        patch("tar_dataset.cli.BenchmarkSuite") as mock_eval,
    ):
        mock_sqlite.return_value = pathlib.Path("data/processed/tar.db")
        mock_arrow.return_value = {
            "arrow_tables": {"seasons": pathlib.Path("s.arrow")},
            "hf_datasets": {"qa_pairs": pathlib.Path("hf/")},
        }
        mock_ai.return_value.export_all.return_value = {
            "qa_pairs": 10,
            "corpus_chunks": 5,
        }
        mock_eval.return_value.evaluate_benchmark.return_value = {}

        res = runner.invoke(app, ["export-sqlite"])
        assert res.exit_code == 0
        assert "Successfully exported SQLite bundle" in res.stdout

        res = runner.invoke(app, ["export-arrow"])
        assert res.exit_code == 0
        assert "Exported 1 tables to Apache Arrow IPC" in res.stdout

        res = runner.invoke(app, ["export-ai"])
        assert res.exit_code == 0
        assert "Generating AI training datasets" in res.stdout

        res = runner.invoke(app, ["eval-benchmark"])
        assert res.exit_code == 0
        assert "Running The Amazing Race AI Benchmark" in res.stdout


def test_cli_show_commands():
    # Season show
    res = runner.invoke(app, ["show", "season", "1"])
    assert res.exit_code == 0
    assert "Season 1" in res.stdout

    res = runner.invoke(app, ["show", "season", "999"])
    assert res.exit_code == 1
    assert "not found" in res.stdout

    # Team show
    res = runner.invoke(app, ["show", "team", "Rob & Brennan"])
    assert res.exit_code == 0

    res = runner.invoke(app, ["show", "team", "NonExistentTeamXYZ"])
    assert res.exit_code == 1
    assert "No teams found" in res.stdout

    # Racer show
    res = runner.invoke(app, ["show", "racer", "Rob"])
    assert res.exit_code == 0

    res = runner.invoke(app, ["show", "racer", "NonExistentRacerXYZ"])
    assert res.exit_code == 1
    assert "No contestants found" in res.stdout

    # Leg show
    res = runner.invoke(app, ["show", "leg", "1", "--season", "1"])
    assert res.exit_code == 0

    res = runner.invoke(app, ["show", "leg", "999", "--season", "1"])
    assert res.exit_code == 1
    assert "not found" in res.stdout
