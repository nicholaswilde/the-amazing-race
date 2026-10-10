"""Tests for automated scheduled ingestion workflow script."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from scripts.schedule_ingest import (
    check_wikipedia_season_exists,
    create_pr_or_commit,
    get_highest_ingested_season,
    main,
    post_issue_comment,
    run_cmd,
    run_pipeline,
)


def test_run_cmd() -> None:
    output = run_cmd(["echo", "hello world"])
    assert output == "hello world"

    output_str = run_cmd("echo 'single string cmd'")
    assert output_str == "single string cmd"


def test_get_highest_ingested_season_from_csv(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    csv_file = processed_dir / "seasons.csv"
    csv_file.write_text(
        "season,version,year\n1,US,2001\n2,US,2002\n35,US,2023\n36,US,2024\n1,CAN,2013\n",
        encoding="utf-8",
    )

    highest_us = get_highest_ingested_season(
        raw_dir=raw_dir, processed_dir=processed_dir, version="US"
    )
    assert highest_us == 36

    highest_can = get_highest_ingested_season(
        raw_dir=raw_dir, processed_dir=processed_dir, version="CAN"
    )
    assert highest_can == 1


def test_get_highest_ingested_season_from_raw_fallback(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    (raw_dir / "season_us_10.json").write_text("{}", encoding="utf-8")
    (raw_dir / "season_us_25.json").write_text("{}", encoding="utf-8")
    (raw_dir / "season_can_5.json").write_text("{}", encoding="utf-8")

    highest_us = get_highest_ingested_season(
        raw_dir=raw_dir, processed_dir=processed_dir, version="US"
    )
    assert highest_us == 25

    highest_can = get_highest_ingested_season(
        raw_dir=raw_dir, processed_dir=processed_dir, version="CAN"
    )
    assert highest_can == 5


def test_get_highest_ingested_season_default(tmp_path: Path) -> None:
    processed_dir = tmp_path / "empty_processed"
    processed_dir.mkdir(parents=True)
    raw_dir = tmp_path / "empty_raw"
    raw_dir.mkdir(parents=True)

    # Empty dirs should fallback to 36
    assert (
        get_highest_ingested_season(
            raw_dir=raw_dir, processed_dir=processed_dir, version="US"
        )
        == 36
    )


@patch("tar_dataset.scrapers.wikipedia.WikipediaScraper.fetch_page_html")
@patch("tar_dataset.scrapers.wikipedia.WikipediaScraper.get_page_title")
def test_check_wikipedia_season_exists(
    mock_title: MagicMock, mock_fetch: MagicMock
) -> None:
    mock_title.return_value = "The_Amazing_Race_37"

    # Valid article
    mock_fetch.return_value = (
        "<html><body>" + ("contestant info " * 500) + "</body></html>"
    )
    assert check_wikipedia_season_exists(37, version="US") is True

    # Too short / empty stub
    mock_fetch.return_value = "<html><body>contestant</body></html>"
    assert check_wikipedia_season_exists(37, version="US") is False

    # None or network failure
    mock_fetch.return_value = None
    assert check_wikipedia_season_exists(37, version="US") is False

    # Exception thrown
    mock_fetch.side_effect = RuntimeError("Network error")
    assert check_wikipedia_season_exists(37, version="US") is False


@patch("shutil.which")
@patch("scripts.schedule_ingest.run_cmd")
def test_post_issue_comment(mock_run_cmd: MagicMock, mock_which: MagicMock) -> None:
    mock_which.return_value = "/usr/bin/gh"

    # Successful call
    success = post_issue_comment(37, version="US", issue_num=4)
    assert success is True
    mock_run_cmd.assert_called_with(
        'rtk gh issue comment 4 --body "Imported Season 37 (US)" | cat', check=True
    )

    # Missing gh
    mock_which.return_value = None
    assert post_issue_comment(37, version="US", issue_num=4) is False


@patch("scripts.schedule_ingest.run_cmd")
def test_create_pr_or_commit_no_changes(mock_run_cmd: MagicMock) -> None:
    mock_run_cmd.return_value = ""  # git status --porcelain is empty
    result = create_pr_or_commit(37, version="US", open_pr=True)
    assert result is False


@patch("scripts.schedule_ingest.run_cmd")
def test_create_pr_or_commit_with_pr(mock_run_cmd: MagicMock) -> None:
    def fake_run_cmd(cmd: object, *args: object, **kwargs: object) -> str:
        if isinstance(cmd, str) and "status" in cmd:
            return "M data/processed/seasons.csv"
        return ""

    mock_run_cmd.side_effect = fake_run_cmd
    result = create_pr_or_commit(37, version="US", open_pr=True)
    assert result is True


@patch("scripts.schedule_ingest.run_cmd")
def test_create_pr_or_commit_direct_push(mock_run_cmd: MagicMock) -> None:
    def fake_run_cmd(cmd: object, *args: object, **kwargs: object) -> str:
        if isinstance(cmd, str) and "status" in cmd:
            return "M data/processed/seasons.csv"
        return ""

    mock_run_cmd.side_effect = fake_run_cmd
    result = create_pr_or_commit(37, version="US", open_pr=False)
    assert result is True


@patch("shutil.which")
@patch("subprocess.run")
def test_run_pipeline_task(mock_subproc: MagicMock, mock_which: MagicMock) -> None:
    mock_which.return_value = "/usr/bin/task"
    mock_subproc.return_value = MagicMock(returncode=0)
    assert run_pipeline() is True
    mock_subproc.assert_called_with(["/usr/bin/task", "pipeline"], check=False)


@patch("sys.argv", ["schedule_ingest.py", "--check-only"])
@patch("scripts.schedule_ingest.check_wikipedia_season_exists")
@patch("scripts.schedule_ingest.get_highest_ingested_season")
def test_main_check_only(
    mock_get_highest: MagicMock,
    mock_check_exists: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mock_get_highest.return_value = 36
    mock_check_exists.return_value = True

    ret = main()
    assert ret == 0
    captured = capsys.readouterr()
    assert "NEW_SEASON_AVAILABLE=37" in captured.out


@patch("sys.argv", ["schedule_ingest.py"])
@patch("scripts.schedule_ingest.check_wikipedia_season_exists")
@patch("scripts.schedule_ingest.get_highest_ingested_season")
def test_main_not_available(
    mock_get_highest: MagicMock,
    mock_check_exists: MagicMock,
) -> None:
    mock_get_highest.return_value = 36
    mock_check_exists.return_value = False

    ret = main()
    assert ret == 0


@patch(
    "sys.argv", ["schedule_ingest.py", "--season", "37", "--post-comment", "--open-pr"]
)
@patch("tar_dataset.processors.predictor.SeasonPredictor.update_predictions_docs")
@patch("scripts.schedule_ingest.create_pr_or_commit")
@patch("scripts.schedule_ingest.post_issue_comment")
@patch("scripts.schedule_ingest.run_pipeline")
@patch("tar_dataset.scrapers.fandom.FandomScraper.scrape_season")
@patch("tar_dataset.scrapers.wikipedia.WikipediaScraper.scrape_season")
@patch("scripts.schedule_ingest.check_wikipedia_season_exists")
def test_main_full_ingest_flow(
    mock_check_exists: MagicMock,
    mock_wiki_scrape: MagicMock,
    mock_fandom_scrape: MagicMock,
    mock_run_pipeline: MagicMock,
    mock_post_comment: MagicMock,
    mock_create_pr: MagicMock,
    mock_update_docs: MagicMock,
) -> None:
    mock_check_exists.return_value = True
    mock_run_pipeline.return_value = True
    mock_post_comment.return_value = True
    mock_create_pr.return_value = True

    ret = main()
    assert ret == 0
    mock_wiki_scrape.assert_called_once_with(37, version="US", save=True)
    mock_fandom_scrape.assert_called_once_with(37, version="US")
    mock_run_pipeline.assert_called_once()
    mock_update_docs.assert_called_once_with(season=37)
    mock_post_comment.assert_called_once_with(37, version="US", issue_num=4)
    mock_create_pr.assert_called_once_with(37, version="US", open_pr=True)
