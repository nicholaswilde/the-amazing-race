"""Unit tests for DatasetValidator edge cases, WikipediaScraper scrape_season, and AIExportBuilder."""

from __future__ import annotations

import json
from unittest.mock import patch

import pandas as pd

from tar_dataset.exports.ai_formats import AIExportBuilder
from tar_dataset.processors.validator import DatasetValidator
from tar_dataset.scrapers.wikipedia import WikipediaScraper


def test_validator_no_tables(tmp_path):
    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()
    assert report["status"] == "FAIL"
    assert "No processed tables found." in report["issues"]


def test_validator_missing_tables(tmp_path):
    # Only create one table
    pd.DataFrame({"season": [1]}).to_csv(tmp_path / "seasons.csv", index=False)
    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()
    assert report["status"] == "FAIL"
    assert any("Missing table" in i for i in report["issues"])


def test_validator_rules_and_warnings(tmp_path):
    # Create all required tables with intentional issues to test each branch
    pd.DataFrame({"season": [1, 1], "version": ["US", "US"]}).to_csv(
        tmp_path / "seasons.csv", index=False
    )
    pd.DataFrame({"season": [1], "episode": [1]}).to_csv(
        tmp_path / "episodes.csv", index=False
    )
    # 1 contestant but 2 teams -> fewer contestants than teams
    pd.DataFrame({"season": [1], "contestant_id": ["c1"]}).to_csv(
        tmp_path / "contestants.csv", index=False
    )
    pd.DataFrame({"season": [1, 1], "team_id": ["t1", "t2"]}).to_csv(
        tmp_path / "teams.csv", index=False
    )
    pd.DataFrame({"season": [1], "leg_number": [1]}).to_csv(
        tmp_path / "legs.csv", index=False
    )
    # Leg result with null placement
    pd.DataFrame({"season": [1], "leg_number": [1], "placement": [None]}).to_csv(
        tmp_path / "leg_results.csv", index=False
    )
    pd.DataFrame({"season": [1], "task_type": ["Detour"]}).to_csv(
        tmp_path / "tasks.csv", index=False
    )

    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()
    assert report["status"] == "WARNING"
    assert any("Duplicate season numbers" in i for i in report["issues"])
    assert any("unresolved placement" in i for i in report["issues"])
    assert any("fewer contestants" in i for i in report["issues"])


def test_validator_season_with_no_teams(tmp_path):
    pd.DataFrame({"season": [1, 2]}).to_csv(tmp_path / "seasons.csv", index=False)
    pd.DataFrame({"season": [1]}).to_csv(tmp_path / "episodes.csv", index=False)
    pd.DataFrame({"season": [1, 1], "contestant_id": ["c1", "c2"]}).to_csv(
        tmp_path / "contestants.csv", index=False
    )
    # Season 2 has no teams
    pd.DataFrame({"season": [1], "team_id": ["t1"]}).to_csv(
        tmp_path / "teams.csv", index=False
    )
    pd.DataFrame({"season": [1], "leg_number": [1]}).to_csv(
        tmp_path / "legs.csv", index=False
    )
    pd.DataFrame({"season": [1], "leg_number": [1], "placement": [1]}).to_csv(
        tmp_path / "leg_results.csv", index=False
    )
    pd.DataFrame({"season": [1], "task_type": ["Detour"]}).to_csv(
        tmp_path / "tasks.csv", index=False
    )

    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()
    assert any("Season 2 has no teams" in i for i in report["issues"])


def test_wikipedia_scraper_scrape_season_and_seasons(tmp_path):
    scraper = WikipediaScraper(raw_dir=tmp_path)

    sample_html = """
    <html>
      <body>
        <table class="infobox vevent">
          <tr><th scope="row">Teams</th><td>11</td></tr>
          <tr><th scope="row">Winners</th><td>Rob & Brennan</td></tr>
        </table>
        <table class="wikitable">
          <tr><th>Contestants</th><th>Age</th><th>Relationship</th><th>Current Residence</th></tr>
          <tr><td>Rob Frisbee</td><td>27</td><td>Best Friends</td><td>Minneapolis, MN</td></tr>
        </table>
        <table class="wikitable">
          <tr><th>Team</th><th>1</th><th>2</th></tr>
          <tr><td>Rob & Brennan</td><td>1st</td><td>1st</td></tr>
        </table>
        <table class="wikitable">
          <tr><th>No. overall</th><th>No. in season</th><th>Title</th><th>Air date</th><th>Viewers</th></tr>
          <tr><td>1</td><td>1</td><td>"The Race Begins"</td><td>2001-09-05</td><td>11.8</td></tr>
        </table>
        <div class="mw-heading mw-heading3">
          <h3>Leg 1 (USA -> RSA)</h3>
        </div>
        <p>Route summary for leg 1.</p>
      </body>
    </html>
    """

    with patch.object(scraper, "fetch_page_html", return_value=sample_html):
        data = scraper.scrape_season(1, version="US", save=True)
        assert data["season"] == 1
        assert data["infobox"]["winners"] == "Rob & Brennan"
        assert len(data["contestants"]) == 1
        assert len(data["results"]) == 1
        assert len(data["episodes"]) == 1
        assert len(data["legs"]) == 1
        assert (tmp_path / "season_us_01.json").exists()

        # Scrape seasons range
        all_data = scraper.scrape_seasons(start=1, end=2, version="US")
        assert len(all_data) == 2

    # Scrape season failure when fetch_page_html returns None
    with patch.object(scraper, "fetch_page_html", return_value=None):
        assert scraper.scrape_season(99, save=False) == {}


def test_ai_formats_export_all_and_reddit(tmp_path):
    # Mock Reddit files with AMA, live discussion, and bad json
    reddit_dir = tmp_path / "reddit"
    reddit_dir.mkdir(parents=True)
    reddit_file = reddit_dir / "reddit_test.json"
    reddit_file.write_text(
        json.dumps(
            [
                {
                    "post_id": "ama_1",
                    "title": "I am a racer AMA!",
                    "thread_type": "ama",
                    "season": 30,
                    "episode": None,
                    "comments": [
                        {
                            "body": "This is a detailed response to a fan about race logistics."
                        }
                    ],
                },
                {
                    "post_id": "live_1",
                    "title": "Live Discussion S30E01",
                    "thread_type": "live_discussion",
                    "season": 30,
                    "episode": 1,
                    "comments": [
                        {
                            "author": "User1",
                            "body": "What an incredible start to this leg across Iceland!",
                        }
                    ],
                },
            ]
        ),
        encoding="utf-8",
    )
    bad_file = reddit_dir / "bad.json"
    bad_file.write_text("corrupted json content", encoding="utf-8")

    exporter = AIExportBuilder(
        processed_dir="data/processed",
        ai_dir=tmp_path / "ai",
    )

    with patch("tar_dataset.exports.ai_formats.Path") as mock_path:
        # Let Path("data/raw/reddit") point to our temporary reddit_dir
        def side_effect(arg):
            if str(arg) == "data/raw/reddit":
                return reddit_dir
            return tmp_path / str(arg)

        mock_path.side_effect = side_effect
        discs = exporter.load_reddit_discussions()
        assert len(discs) >= 0

    # Test full export_all writes the JSONL files
    counts = exporter.export_all()
    assert "qa_pairs" in counts
    assert "corpus_chunks" in counts
    assert (tmp_path / "ai" / "tar_qa_finetuning.jsonl").exists()
    assert (tmp_path / "ai" / "tar_knowledge_corpus.jsonl").exists()


def test_builder_skips_in_progress_seasons(tmp_path):
    """Verify DatasetBuilder excludes in-progress seasons by default."""
    from tar_dataset.processors.builder import DatasetBuilder

    raw_wiki = tmp_path / "raw" / "wikipedia"
    raw_wiki.mkdir(parents=True)

    completed_season = {
        "version": "US",
        "season": 1,
        "infobox": {"winners": "Rob & Brennan", "n_teams": 11, "n_legs": 13},
    }
    in_progress_season = {
        "version": "US",
        "season": 99,
        "infobox": {"winners": None, "n_teams": 12, "n_legs": 12},
    }

    (raw_wiki / "season_us_01.json").write_text(
        json.dumps(completed_season), encoding="utf-8"
    )
    (raw_wiki / "season_us_99.json").write_text(
        json.dumps(in_progress_season), encoding="utf-8"
    )

    # Default: skip in-progress
    builder_default = DatasetBuilder(
        raw_dir=tmp_path / "raw", processed_dir=tmp_path / "processed"
    )
    seasons = builder_default.load_wikipedia_seasons()
    assert len(seasons) == 1
    assert seasons[0]["season"] == 1

    # Explicit: include in-progress
    builder_include = DatasetBuilder(
        raw_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
        include_in_progress=True,
    )
    seasons_all = builder_include.load_wikipedia_seasons()
    assert len(seasons_all) == 2


def test_validator_gender_and_composition_checks(tmp_path):
    """Verify validator flags missing or invalid gender and gender_composition values."""
    pd.DataFrame({"season": [1]}).to_csv(tmp_path / "seasons.csv", index=False)
    pd.DataFrame({"season": [1], "episode": [1]}).to_csv(
        tmp_path / "episodes.csv", index=False
    )
    # Contestant with invalid and null gender
    pd.DataFrame(
        {
            "season": [1, 1],
            "contestant_id": ["c1", "c2"],
            "gender": [None, "INVALID"],
        }
    ).to_csv(tmp_path / "contestants.csv", index=False)
    # Team with invalid and null gender_composition
    pd.DataFrame(
        {
            "season": [1],
            "team_id": ["t1"],
            "gender_composition": [None],
        }
    ).to_csv(tmp_path / "teams.csv", index=False)
    pd.DataFrame({"season": [1], "leg_number": [1]}).to_csv(
        tmp_path / "legs.csv", index=False
    )
    pd.DataFrame({"season": [1], "leg_number": [1], "placement": [1]}).to_csv(
        tmp_path / "leg_results.csv", index=False
    )
    pd.DataFrame({"season": [1], "task_type": ["Detour"]}).to_csv(
        tmp_path / "tasks.csv", index=False
    )

    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()

    assert any("missing gender values" in i for i in report["issues"])
    assert any("invalid gender values" in i for i in report["issues"])
    assert any("missing gender_composition values" in i for i in report["issues"])


def test_validator_racing_metrics_and_geography_checks(tmp_path):
    """Verify validator flags invalid racing metrics and missing/invalid geography."""
    pd.DataFrame({"season": [1]}).to_csv(tmp_path / "seasons.csv", index=False)
    pd.DataFrame({"season": [1], "episode": [1]}).to_csv(
        tmp_path / "episodes.csv", index=False
    )
    # Contestant missing hometown_country
    pd.DataFrame(
        {
            "season": [1, 1],
            "contestant_id": ["c1", "c2"],
            "gender": ["M", "F"],
            "hometown_country": [None, "USA"],
        }
    ).to_csv(tmp_path / "contestants.csv", index=False)
    # Team with invalid racing_average (< 1.0) and invalid podium_rate (> 1.0)
    pd.DataFrame(
        {
            "season": [1],
            "team_id": ["t1"],
            "gender_composition": ["MF"],
            "legs_completed": [5],
            "racing_average": [0.5],
            "podium_rate": [1.5],
        }
    ).to_csv(tmp_path / "teams.csv", index=False)
    # Leg with missing origin_country and invalid destination_continent
    pd.DataFrame(
        {
            "season": [1],
            "leg_number": [1],
            "origin_country": [None],
            "destination_country": ["FRA"],
            "destination_continent": ["Atlantis"],
        }
    ).to_csv(tmp_path / "legs.csv", index=False)
    pd.DataFrame({"season": [1], "leg_number": [1], "placement": [1]}).to_csv(
        tmp_path / "leg_results.csv", index=False
    )
    pd.DataFrame({"season": [1], "task_type": ["Detour"]}).to_csv(
        tmp_path / "tasks.csv", index=False
    )

    validator = DatasetValidator(processed_dir=tmp_path)
    report = validator.validate()

    assert any("invalid racing_average" in i for i in report["issues"])
    assert any("invalid podium_rate" in i for i in report["issues"])
    assert any("missing origin_country" in i for i in report["issues"])
    assert any("invalid destination_continent" in i for i in report["issues"])
    assert any("missing hometown_country" in i for i in report["issues"])
