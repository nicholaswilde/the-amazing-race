# Agent Guidelines: The Amazing Race Dataset

This repository creates a comprehensive tidy dataset and AI training corpus for the television series **The Amazing Race** (**TAR**). Note that throughout this repository, CLI commands (`tar-dataset`), issue tracking, and agent interactions, the acronym **TAR** refers exclusively to **The Amazing Race** (not the Unix `tar` archive utility).

## Environment & Dependency Management
- **Tooling**: Use [`uv`](https://docs.astral.sh/uv/) and [`go-task`](https://taskfile.dev/) (`task`) to manage dependencies, run pipeline workflows, and execute commands.
  - Run tasks: `task <command>` (e.g., `task test`, `task check`, `task spellcheck`, `task spellcheck-file FILE=path/to/file`, `task build`, `task package`, `task sync`)
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
- `tar-predict`: Predicts race outcomes, finale contenders, and elimination risks using multi-factor empirical modeling.
- `tar-ingest`: Automates broadcast season checking, Wikipedia revision detection, pipeline build, and Issue #4 progress tracking.
- `tar-tidytuesday`: Packages, validates, and manages R4DS TidyTuesday intake bundles and submission issues.
- `tar-gap-audit`: Audits dataset completeness, null rates, and guides viewership/rating backfilling.
- `release`: Automates versioning, validation (`task check`), tagging, and atomic push to trigger GitHub release workflow (`./scripts/release.sh`).
- `release-summary`: Generates categorized release notes from git logs and updates GitHub draft release (`./scripts/release_summary.py`).


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

## Viewership & Ratings Auditing
- When auditing or backfilling broadcast viewership (`viewers_millions`) or ratings where Wikipedia or Fandom tables list `TBD` or pending data, cross-reference industry television ratings databases such as **The TV Ratings Guide** (`thetvratingsguide.com`) and **USTVDB** (`ustvdb.com`).

## Release Guidelines
- When performing the release skill (`release`), **always ensure to bump the git version tag** (incrementing patch, minor, or major according to SemVer) and create a distinct new git tag, never re-tagging, force-moving, or reusing an existing release tag.

## Reference Repositories
- **`doehm/alone`**: When inspecting or searching the reference `doehm/alone` repository for schema patterns, tidy data structures, or package conventions, **always look locally first** at `/home/nicholas/git/doehm/alone` before searching the web or GitHub.

## Serena Semantic Code Navigation & LSP
This project uses Serena for semantic Python development, AST manipulation, and LSP diagnostics.
- **Mandatory Activation**: Before analyzing or editing Python code, agents MUST activate the project using `activate_project(project="the-amazing-race")` or `initial_instructions`.
- **Project Memories**: Always read the `critical_info` memory using `read_memory(memory_name="critical_info")` to load essential project constraints.
- **Rules Reference**: See [`.agents/rules/serena-rules.md`](.agents/rules/serena-rules.md) for tool mappings, refactoring protocols, and CodeGraph boundaries.

Serena (`serena-agent`) provides symbol-level semantic code navigation, refactoring, and AST indexing via LSP (Pyright).
- **Project Configuration**: Stored in `.serena/project.yml`.
- **Health Check**: Run `serena project health-check` to verify language server connectivity and symbol lookup.
- **Index Codebase**: Run `serena project index` to rebuild the symbol cache.
- **MCP Server Registration**:
  - Registered in `~/.gemini/config/mcp_config.json` (for Antigravity):
    ```json
    "serena": {
      "command": "serena",
      "args": [
        "start-mcp-server",
        "--context=antigravity",
        "--project-from-cwd",
        "--open-web-dashboard",
        "false"
      ]
    }
    ```
  - Registered in `~/.claude.json` (for Claude Code):
    ```json
    "serena": {
      "command": "serena",
      "args": [
        "start-mcp-server",
        "--context=claude-code",
        "--project-from-cwd",
        "--open-web-dashboard",
        "false"
      ]
    }
    ```
- **New Workspace Setup**:
  1. Ensure `serena-agent` is installed: `uv tool install -p 3.13 serena-agent`
  2. Initialize project configuration: `serena project create . --ls python`
  3. Index symbols: `serena project index .`
  4. Verify setup: `serena project health-check .`
- **Troubleshooting**:
  - **MCP Reload Warning (`signal: terminated`)**:
    - *Symptom*: `Failed to reload MCP config: failed to stop existing instances for reload: failed to stop mcp instance: serena: signal: terminated`.
    - *Cause*: `agy` terminates running MCP instances with `SIGTERM` when reloading. Serena exits cleanly on signal 15, but Go's `cmd.Wait()` treats signal termination as an error string (`signal: terminated`), causing `agy` to report a reload error.
    - *Resolution*: Benign. Serena restarts immediately on the next tool invocation or post-reload cycle. Verify status via `serena project health-check .` or by calling any Serena MCP tool.

