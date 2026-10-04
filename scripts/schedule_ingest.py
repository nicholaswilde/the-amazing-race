#!/usr/bin/env -S uv run python
"""Automated scheduled ingestion and season tracking workflow script.

Periodically checks for new broadcast episodes and seasons of The Amazing Race,
ingests new data from Wikipedia/Fandom, executes the data pipeline, and
updates GitHub Issue #4.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("schedule_ingest")


def run_cmd(cmd: list[str] | str, check: bool = True, capture: bool = True) -> str:
    """Run shell command and return decoded stdout."""
    if isinstance(cmd, str):
        res = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture,
            text=True,
        )
    else:
        res = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
        )
    return res.stdout.strip() if capture else ""


def get_highest_ingested_season(
    raw_dir: Path = Path("data/raw/wikipedia"),
    processed_dir: Path = Path("data/processed"),
    version: str = "US",
) -> int:
    """Determine highest season number currently ingested."""
    seasons_csv = processed_dir / "seasons.csv"
    if seasons_csv.exists():
        try:
            import pandas as pd

            df = pd.read_csv(seasons_csv)
            if not df.empty and "season" in df.columns:
                v_df = (
                    df[df.get("version", "US").str.upper() == version.upper()]
                    if "version" in df.columns
                    else df
                )
                if not v_df.empty:
                    return int(v_df["season"].max())
        except Exception as e:
            logger.warning("Error reading seasons.csv: %s", e)

    # Fallback to scanning raw directory
    pattern = re.compile(rf"season_{version.lower()}_(\d+)\.json")
    highest = 0
    if raw_dir.exists():
        for f in raw_dir.glob("*.json"):
            m = pattern.match(f.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest or 36


def check_wikipedia_season_exists(season: int, version: str = "US") -> bool:
    """Check if Wikipedia has a valid article with content for given season."""
    try:
        from tar_dataset.scrapers.wikipedia import WikipediaScraper

        scraper = WikipediaScraper()
        rev = scraper.get_latest_revision(season, version=version)
        if not rev:
            return False

        title = scraper.get_page_title(season, version=version)
        html = scraper.fetch_page_html(title)
        if not html:
            return False
        # Verify page is not a redirect to main franchise or empty stub
        return ("infobox" in html.lower() or "contestant" in html.lower()) and len(
            html
        ) > 5000
    except Exception as e:
        logger.error("Error checking Wikipedia for Season %d: %s", season, e)
        return False


def run_pipeline() -> bool:
    """Execute the data processing and export pipeline."""
    task_bin = shutil.which("task")
    if task_bin:
        logger.info("Executing `task pipeline`...")
        res = subprocess.run([task_bin, "pipeline"], check=False)
        return res.returncode == 0

    # Fallback to python modules
    logger.info("Task not found; running pipeline via python modules...")
    try:
        from tar_dataset.exports.ai_formats import AIExportBuilder
        from tar_dataset.exports.arrow_export import export_arrow_and_hf
        from tar_dataset.exports.r_export import export_to_r
        from tar_dataset.exports.sqlite_export import export_to_sqlite
        from tar_dataset.processors.builder import DatasetBuilder
        from tar_dataset.processors.validator import DatasetValidator

        builder = DatasetBuilder()
        builder.build_all()

        validator = DatasetValidator()
        report = validator.validate()
        if report.get("status") != "PASS":
            logger.warning("Validation warnings detected: %s", report.get("issues"))

        AIExportBuilder().export_all()
        export_arrow_and_hf()
        export_to_r()
        export_to_sqlite()
        from tar_dataset.exports.geojson_export import export_to_geojson

        export_to_geojson()
        return True
    except Exception as e:
        logger.error("Error running pipeline: %s", e)
        return False


def post_issue_comment(season: int, version: str = "US", issue_num: int = 4) -> bool:
    """Post ingestion progress update comment to GitHub Issue #4."""
    gh_bin = shutil.which("gh")
    if not gh_bin:
        logger.warning("GitHub CLI (`gh`) not found; skipping issue comment.")
        return False

    body = f"Imported Season {season} ({version})"
    logger.info("Posting comment to Issue #%d: '%s'", issue_num, body)
    try:
        run_cmd(f'rtk gh issue comment {issue_num} --body "{body}" | cat', check=True)
        logger.info("Successfully commented on Issue #%d", issue_num)
        return True
    except Exception as e:
        logger.warning("Failed to post comment via rtk gh, trying raw gh: %s", e)
        try:
            run_cmd(
                ["gh", "issue", "comment", str(issue_num), "--body", body], check=True
            )
            return True
        except Exception as e2:
            logger.error("Failed to post issue comment: %s", e2)
            return False


def create_pr_or_commit(season: int, version: str = "US", open_pr: bool = True) -> bool:
    """Commit changes and optionally open a Pull Request."""
    status = run_cmd("git status --porcelain data/ docs/", check=False)
    if not status:
        logger.info("No git changes detected in data/ or docs/; skipping commit/PR.")
        return False

    branch_name = f"data/ingest-{version.lower()}-s{season:02d}"
    commit_msg = (
        f"data(ingest): import {version} Season {season} and update data pipeline"
    )

    logger.info("Creating git commit for Season %d ingestion...", season)
    try:
        run_cmd("git config user.name 'github-actions[bot]' || true", check=False)
        run_cmd(
            "git config user.email 'github-actions[bot]@users.noreply.github.com' || true",
            check=False,
        )

        if open_pr:
            run_cmd(f"git checkout -b {branch_name}", check=True)
            run_cmd("git add data/ docs/", check=True)
            run_cmd(["git", "commit", "-m", commit_msg], check=True)
            run_cmd(f"git push -u origin {branch_name}", check=True)

            pr_title = f"data(ingest): import {version} Season {season}"
            pr_body = (
                f"## Automated Season Ingestion\n\n"
                f"- Scraped and ingested **{version} Season {season}** from Wikipedia and Fandom.\n"
                f"- Rebuilt tidy datasets, Parquet, SQLite, Arrow, and AI training corpora.\n"
                f"- Updates tracking issue #4.\n"
            )
            run_cmd(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    pr_title,
                    "--body",
                    pr_body,
                    "--base",
                    "main",
                ],
                check=True,
            )
            logger.info("Opened Pull Request for %s", branch_name)
        else:
            run_cmd("git add data/ docs/", check=True)
            run_cmd(["git", "commit", "-m", commit_msg], check=True)
            run_cmd("git push origin HEAD", check=True)
            logger.info("Pushed commit directly to current branch.")
        return True
    except Exception as e:
        logger.error("Error creating PR/commit: %s", e)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check and ingest new seasons/episodes of The Amazing Race."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help="Specific season number to ingest (defaults to auto-detecting next season)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="US",
        help="Franchise version code (US, CAN, AUS)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if new season data is available without scraping or building",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post update comment to Issue #4 upon successful ingestion",
    )
    parser.add_argument(
        "--issue-num",
        type=int,
        default=4,
        help="GitHub issue number to comment on (default: 4)",
    )
    parser.add_argument(
        "--open-pr",
        action="store_true",
        help="Create branch and open Pull Request for new data",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scraping and rebuilding even if season already exists",
    )

    args = parser.parse_args()

    highest = get_highest_ingested_season(version=args.version)
    logger.info(
        "Current highest ingested season for %s: Season %d", args.version, highest
    )

    target_season = args.season or (highest + 1)
    logger.info(
        "Checking availability for %s Season %d...", args.version, target_season
    )

    exists = check_wikipedia_season_exists(target_season, version=args.version)

    if not exists and not args.force:
        logger.info(
            "Season %d does not have active Wikipedia/Fandom broadcast data yet. Dataset is current.",
            target_season,
        )
        return 0

    logger.info("✓ Found available data for %s Season %d!", args.version, target_season)

    if args.check_only:
        print(f"NEW_SEASON_AVAILABLE={target_season}")
        return 0

    # Ingest from Wikipedia
    from tar_dataset.scrapers.wikipedia import WikipediaScraper

    logger.info("Scraping Wikipedia for Season %d...", target_season)
    wiki_scraper = WikipediaScraper()
    wiki_scraper.scrape_season(target_season, version=args.version, save=True)

    # Ingest from Fandom
    try:
        from tar_dataset.scrapers.fandom import FandomScraper

        logger.info("Scraping Fandom for Season %d...", target_season)
        fandom_scraper = FandomScraper(version=args.version)
        fandom_scraper.scrape_season(target_season, version=args.version)
    except Exception as e:
        logger.warning("Fandom scraping encountered error: %s", e)

    # Re-run pipeline to compile all tables and AI corpora
    success = run_pipeline()
    if not success:
        logger.error("Pipeline execution failed during ingestion.")
        return 1

    logger.info("✓ Pipeline re-built successfully with Season %d data!", target_season)

    # Post comment to Issue #4
    if args.post_comment:
        post_issue_comment(
            target_season, version=args.version, issue_num=args.issue_num
        )

    # Open PR or commit
    if args.open_pr:
        create_pr_or_commit(target_season, version=args.version, open_pr=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
