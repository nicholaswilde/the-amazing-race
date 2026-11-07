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


<!-- rtk-begin -->
## RTK Command Guidelines
- **Git Operations**: Prefix `git` commands with `rtk` (e.g., `rtk git status`, `rtk git diff`, `rtk git log`, `rtk git commit`, `rtk git push`).
- **GitHub CLI**: Prefix `gh` commands with `rtk` and always pipe to `cat` to bypass interactive prompts and terminal pagers (e.g., `rtk gh issue list | cat`, `rtk gh pr status | cat`).
- **File & Directory Inspection**: Use `rtk ls`, `rtk tree`, `rtk find`, or `rtk read` when listing or reading files to get token-optimized output.
- **Searching**: Use `rtk rg` (ripgrep) as the primary pattern and text search utility. Avoid raw `grep` or `find | xargs`. Leverage `-t py`, `-l`, and path scoping to conserve tokens.
- **Ripwire**: Prefix `ripwire` commands with `rtk` (e.g., `rtk ripwire . --doctor`, `rtk ripwire . --report`, `rtk ripwire . --for="<task>"`).
- **Build & Test Outputs**: Use `rtk err` or `rtk test` when running build/test commands to filter output to errors/failures only (e.g. `rtk test uv run pytest`).
- **Exceptions**: Inside `ctx_execute` / `ctx_batch_execute` sandbox code, skip `rtk` (only printed output enters context). Drop `rtk` when exact raw bytes or patch required (`git diff` patch).
<!-- rtk-end -->

<!-- context-mode-begin -->
## Context-Mode Routing Guidelines
- **Derive, Do Not Dump**: Do NOT use `ctx_execute_file` or `ctx_execute` to dump whole file or full config. Print only specific value, matches, count, or known line range needed.
- **Tool Call Surface**: When using MCP wrappers, call `call_mcp_tool` with `ServerName: "context-mode_context-mode"` (or `"context-mode"`) and `ToolName: "ctx_execute"`, `"ctx_execute_file"`, `"ctx_batch_execute"`, `"ctx_fetch_and_index"`, `"ctx_search"`, or `"ctx_index"`.
- **Mandatory Routing**:
  - For analyze/count/filter/compare/search/parse/transform tasks, write code with `ctx_execute` and print only final answer.
  - For analyzing/exploring inside file, use `ctx_execute_file`. Use native `read_file` only when editing requires exact bytes or small known range.
  - Use `ctx_batch_execute` for multi-command repository reconnaissance.
  - Use `ctx_execute` for shell commands whose output may exceed short fixed answer.
  - Use `ctx_fetch_and_index` for web content, then `ctx_search` to query it.
  - Return only derived answers, concise summaries, selected snippets, or file paths.
<!-- context-mode-end -->

<!-- ponytail-begin -->
## Ponytail (Lazy Senior Dev Mode) Guidelines
- **Stop at first rung that holds**:
  1. Need to build at all? (YAGNI)
  2. Already in codebase? Reuse existing helpers/utils/patterns.
  3. Stdlib does it? Use it.
  4. Native platform feature covers it? Use it.
  5. Installed dependency solves it? Use it.
  6. Can be one line? One line.
  7. Only then: write minimum working code.
- **Bug fix = root cause, not symptom**: Fix shared function/path rather than individual callers.
- **Rules**:
  - No unrequested abstractions, boilerplate, or avoidable dependencies.
  - Deletion over addition. Boring over clever. Fewest files possible.
  - Shortest working diff wins once problem understood.
  - Mark deliberate simplifications cutting real corner with `ponytail:` comment naming ceiling and upgrade path.
  - Ensure logic leaves behind ONE runnable check (assert-based demo/self-check or small test file). Trivial one-liners need none.
<!-- ponytail-end -->

<!-- caveman-begin -->
## Caveman Guidelines
Respond terse like smart caveman. All technical substance stay. Only fluff die.

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging.
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused. Resume after.

Boundaries: code/commits/PRs written normal.
<!-- caveman-end -->

<!-- codegraph-begin -->
## CodeGraph

In repositories indexed by CodeGraph (`.codegraph/` directory exists at repo root), reach for it BEFORE grep/find or reading files when exploring code:

- **MCP tool**: `codegraph_explore` answers source + call path + blast radius in one call. Dynamic-dispatch hops included. Name file or symbol in query to read current line-numbered source.
- **Shell**: `codegraph explore "<symbol names or question>"`.

If no `.codegraph/` directory exists, skip CodeGraph entirely.
<!-- codegraph-end -->

<!-- serena-begin -->
## Serena Semantic Navigation & LSP Integration
Use Serena (`serena`) MCP tools for semantic navigation, AST symbol inspection, LSP diagnostics, and project memories:
1. **Map first**: Call `get_symbols_overview` on target file instead of reading entire file.
2. **Read target symbol only**: Call `find_symbol` with `include_body: true` for target function/class/method.
3. **Check callers**: Call `find_referencing_symbols` or `find_implementations` before signature or behavior changes.
4. **Edit by symbol**: Use `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, or `rename_symbol`. Use standard edit for small tweaks or non-code files.
5. **Verify diagnostics**: Call `get_diagnostics_for_file` after edits to catch LSP errors before full test run.
<!-- serena-end -->

<!-- headroom-begin -->
## Headroom MCP (Context Window Compression)
Use Headroom (`headroom`) MCP tools to manage context window consumption on large payloads:
- `headroom_compress`: Shrink large tool outputs or raw data.
- `headroom_retrieve`: Retrieve original content by hash if specific details needed.
- `headroom_stats`: Monitor headroom cache usage.
<!-- headroom-end -->

<!-- ripwire-begin -->
## Ripwire CLI Codebase Navigation & Analysis
Use `ripwire` CLI binary (prefixed with `rtk ripwire`) for AST codebase mapping, call graphs, blast radius, and structural queries:
- **Architecture summary**: `rtk ripwire . --report`
- **Task bundle**: `rtk ripwire . --pack-task="<task>" --legend=compact`
- **Blast radius**: `rtk ripwire . --impact=SYM --legend=compact`
- **Callers / Callees**: `rtk ripwire . --callers=SYM --legend=compact` / `rtk ripwire . --callees=SYM --legend=compact`
- **Symbol edit**: `rtk ripwire . --replace-symbol-body=SYM --edit-payload=FILE|-`
<!-- ripwire-end -->

<!-- ripgrep-guidelines-begin -->
## Ripgrep Guidelines
- **Pattern Searching**: Always use `rg` (ripgrep) or `rtk rg` instead of standard `grep` to search text inside files quickly and save token output.
- **Scope**: Use `-t py` for Python files, `-l` for file listing, keep context small (`-C 1`).
<!-- ripgrep-guidelines-end -->

<!-- taplo-rules-begin -->
## Taplo TOML Rules
- **Format**: Run `taplo fmt` to format TOML files in-place (`pyproject.toml`).
- **Validation**: Run `taplo lint` to validate TOML syntax and schema.
<!-- taplo-rules-end -->

<!-- uv-rules-begin -->
## Python Tooling & Execution with `uv`
Always use `uv` to manage Python dependencies, run workflows, execute scripts, and invoke CLI tools:
- Prefix all Python commands and scripts with `uv run` or `rtk uv run` (e.g., `rtk uv run pytest`, `rtk uv run tar-dataset <cmd>`). Never run bare `python`, `pip`, or bare `uv`.
- Always keep `uv.lock` and `pyproject.toml` up-to-date and in sync whenever project dependencies or configurations change. Run `uv lock` or `uv sync` after modifying dependencies.
<!-- uv-rules-end -->

<!-- issue-management-begin -->
## GitHub Issue Management
When creating or updating GitHub issues, adhere to naming and labeling scheme:
- **Features**: Prefix title with `[feat]: ` and apply `enhancement` label.
- **Bugs**: Prefix title with `[bug]: ` and apply `bug` label.
- **Commit Closing**: GitHub issues only close automatically when commits containing `Fixes #<number>` are pushed to remote repository.
<!-- issue-management-end -->

<!-- sensitive-information-protection-begin -->
## Sensitive Information & PII Protection
NEVER commit or stage sensitive personal, financial, or security data to repository:
1. **Secrets & Credentials**: Never commit `.env` files, API keys, bearer tokens, passwords, or private encryption keys.
2. **Explicit Staging**: Never use `git add .` when untracked secret files exist; stage explicitly by name.
<!-- sensitive-information-protection-end -->

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

