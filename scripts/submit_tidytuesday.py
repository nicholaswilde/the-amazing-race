#!/usr/bin/env python3
"""Automated helper script for validating and submitting The Amazing Race dataset to R4DS TidyTuesday."""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("submit_tidytuesday")

REQUIRED_FILES = [
    Path("tidytuesday/readme.md"),
    Path("tidytuesday/cleaning.R"),
    Path("tidytuesday/exploration.R"),
    Path("tidytuesday/submission_issue.md"),
    Path("data/processed/seasons.csv"),
    Path("data/processed/episodes.csv"),
    Path("data/processed/contestants.csv"),
    Path("data/processed/teams.csv"),
    Path("data/processed/legs.csv"),
    Path("data/processed/leg_results.csv"),
    Path("data/processed/tasks.csv"),
]

TARGET_REPO = "rfordatascience/tidytuesday"
ISSUE_TITLE = "The Amazing Race (US Seasons 1–38)"


def validate_intake_package() -> bool:
    """Ensure all required files and submission assets are present."""
    missing = [f for f in REQUIRED_FILES if not f.exists()]
    if missing:
        logger.error("Missing required intake package files:")
        for m in missing:
            logger.error("  - %s", m)
        return False
    logger.info("✓ All required TidyTuesday intake package files verified.")
    return True


def check_gh_cli() -> bool:
    """Verify gh CLI is installed and authenticated."""
    gh_bin = shutil.which("gh")
    if not gh_bin:
        logger.error("GitHub CLI ('gh') is not installed or not in PATH.")
        return False

    res = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True, check=False
    )
    if res.returncode != 0:
        logger.error("GitHub CLI is not authenticated. Run 'gh auth login'.")
        return False

    logger.info("✓ GitHub CLI is authenticated.")
    return True


def submit_issue(dry_run: bool = True) -> int:
    """Submit the dataset issue to rfordatascience/tidytuesday or print dry run."""
    issue_body_file = Path("tidytuesday/submission_issue.md")
    if not issue_body_file.exists():
        logger.error("Issue template file not found: %s", issue_body_file)
        return 1

    if dry_run:
        logger.info("[DRY RUN] Would execute:")
        logger.info(
            "gh issue create -R %s --title '%s' --label dataset --body-file %s",
            TARGET_REPO,
            ISSUE_TITLE,
            issue_body_file,
        )
        logger.info("\nFirst 20 lines of body:")
        for line in issue_body_file.read_text(encoding="utf-8").splitlines()[:20]:
            print(f"  {line}")
        logger.info("To actually submit the issue to GitHub, pass '--submit'.")
        return 0

    cmd = [
        "gh",
        "issue",
        "create",
        "-R",
        TARGET_REPO,
        "--title",
        ISSUE_TITLE,
        "--label",
        "dataset",
        "--body-file",
        str(issue_body_file),
    ]
    logger.info("Submitting issue to %s...", TARGET_REPO)
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        logger.error("Failed to submit issue: %s", res.stderr.strip())
        if "Resource not accessible by personal access token" in res.stderr:
            logger.warning(
                "\nNote: Your GitHub CLI token is a fine-grained PAT without write permissions on external repo '%s'.",
                TARGET_REPO,
            )
            logger.info(
                "You can:\n"
                "  1. Submit directly via browser at:\n"
                "     https://github.com/%s/issues/new?template=dataset_template.md\n"
                "     (Title: '%s'; paste content from %s)\n\n"
                "  2. Or refresh GitHub CLI credentials with public repo scope:\n"
                "     gh auth refresh -s public_repo\n",
                TARGET_REPO,
                ISSUE_TITLE,
                issue_body_file,
            )
        return res.returncode

    issue_url = res.stdout.strip()
    logger.info("✓ Successfully created TidyTuesday issue: %s", issue_url)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and submit The Amazing Race dataset to R4DS TidyTuesday."
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Actually submit the issue to rfordatascience/tidytuesday (default is dry-run).",
    )
    args = parser.parse_args()

    if not validate_intake_package():
        return 1

    if not check_gh_cli():
        return 1

    return submit_issue(dry_run=not args.submit)


if __name__ == "__main__":
    sys.exit(main())
