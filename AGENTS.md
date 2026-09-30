# Agent Guidelines: The Amazing Race Dataset

This repository creates a comprehensive tidy dataset and AI training corpus for the television series **The Amazing Race** (**TAR**). Note that throughout this repository, CLI commands (`tar-dataset`), issue tracking, and agent interactions, the acronym **TAR** refers exclusively to **The Amazing Race** (not the Unix `tar` archive utility).

## Environment & Dependency Management
- **Tooling**: Use [`uv`](https://docs.astral.sh/uv/) and [`go-task`](https://taskfile.dev/) (`task`) to manage dependencies, run pipeline workflows, and execute commands.
  - Run tasks: `task <command>` (e.g., `task test`, `task check`, `task build`, `task package`, `task sync`)
  - Run scripts and CLI: `uv run tar-dataset <command>`
  - Run tests: `task test` or `uv run --extra dev pytest`
  - Manage packages: `uv add <package>`, `uv lock`, or `task sync`
  - Never run raw `pip install` or direct `python` without `uv run`.

## Directory Structure
- `src/tar_dataset/`: Python source code
  - `schemas.py`: Pydantic models for Season, Episode, Contestant, Team, Leg, LegResult, Task.
  - `scrapers/`: Wikipedia, Fandom, and Reddit scrapers.
  - `importers/`: Google Sheets and CSV importers.
  - `processors/`: Dataset builder (`builder.py`) and validator (`validator.py`).
  - `exports/`: Exporters for AI training corpora, SQLite, Arrow, R, and release packaging (`packaging.py`).
  - `cli.py`: Typer command-line application (`uv run tar-dataset`).
- `data/`:
  - `data/raw/`: Cached raw scraped data (`wikipedia/`, `fandom/`, `reddit/`, `sheets/`).
  - `data/processed/`: Clean, relational tidy tables in both CSV and Apache Parquet formats.
  - `data/ai/`: JSONL datasets for LLM fine-tuning, RAG, and knowledge retrieval.
- `tests/`: Pytest unit and integration test suite.

## Available Workspace Skills
Agents can invoke the following skills located in `.agents/skills/`:
- `tar-scrape-wiki`: Scrapes Wikipedia and Fandom for seasons, results matrices, and leg challenges.
- `tar-scrape-reddit`: Extracts discussion threads and comments from r/TheAmazingRace.
- `tar-import-sheets`: Imports community Google Sheets and CSVs.
- `tar-dataset-builder`: Compiles raw data into tidy tables (`alone` format) and exports AI training JSONL.

## RTK Command Guidelines
- **Git Operations**: Prefix `git` commands with `rtk` (e.g., `rtk git status`, `rtk git diff`, `rtk git log`, `rtk git commit`, `rtk git push`).
- **GitHub CLI**: Prefix `gh` commands with `rtk` and always pipe to `cat` to bypass interactive prompts and terminal pagers (e.g., `rtk gh issue list | cat`, `rtk gh pr status | cat`).
- **File & Directory Inspection**: Use `rtk ls`, `rtk tree`, `rtk find`, or `rtk read` when listing or reading files to get token-optimized output.
- **Searching**: Use `rtk rg` (ripgrep) as the primary pattern and text search utility. Avoid raw `grep` or `find | xargs`. Leverage `-t py`, `-l`, and path scoping to conserve tokens.
- **Build & Test Outputs**: Use `rtk err` or `rtk test` when running build/test commands to filter output to errors/failures only (e.g. `rtk test pio test -e native`).

## What To Do Next
- When asked "what to do next" (or similar), **always check the remote repository issues first** using `gh`:
  ```bash
  rtk gh issue list | cat
  ```

## Issue Creation
- When asked to create an issue, use your best guess to determine if it is a new feature or a bug fix.
- Prefix the issue title with `[feat]: <description>` or `[bug]: <description>`.
- Add the `enhancement` or `bug` label to the issue accordingly using the `--label` flag with the `gh` command.

## Season Ingestion Tracking
- When importing or scraping a TAR season (or batch of seasons), **always update GitHub Issue #4** to track ingestion progress:
  ```bash
  rtk gh issue comment 4 --body "Imported Season <N> (<version>)" | cat
  ```

## Reference Repositories
- **`doehm/alone`**: When inspecting or searching the reference `doehm/alone` repository for schema patterns, tidy data structures, or package conventions, **always look locally first** at `/home/nicholas/git/doehm/alone` before searching the web or GitHub.

