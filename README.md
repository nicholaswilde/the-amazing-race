# :card_index_dividers: The Amazing Race Dataset & AI Training Corpus :checkered_flag:
[![task](https://img.shields.io/badge/Task-Enabled-brightgreen?style=for-the-badge&logo=task&logoColor=white)](https://taskfile.dev/#/)

A comprehensive tidy dataset and AI training corpus for the CBS reality competition television series **[The Amazing Race](https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series))**.

Inspired by [doehm/alone](https://github.com/doehm/alone), this repository provides structured, relational datasets in tidy format (available in both **CSV** and **Apache Parquet**) alongside JSONL corpora designed for **LLM fine-tuning, RAG (Retrieval-Augmented Generation), and pre-training**.

---

## :card_index_dividers: Architecture & Dataset Schema

The dataset is partitioned into clean relational tables adhering to tidy data principles:

### Tidy Datasets (`data/processed/`)

| Dataset | Format | Description |
| :--- | :--- | :--- |
| **`seasons`** | `.csv`, `.parquet` | Season-level summary: franchise country (`version`), season number, winner names, total legs, teams count, route distance (miles & km), filming dates, and broadcast dates. |
| **`episodes`** | `.csv`, `.parquet` | Episode broadcast metadata, titles (racer quotes), air dates, and Nielsen television viewership ratings (millions). |
| **`contestants`** | `.csv`, `.parquet` | Individual racer demographics: unique `contestant_id`, full name, age, relationship, hometown, and final finish status. |
| **`teams`** | `.csv`, `.parquet` | Team-level profiles: `team_id`, member pairing, relationship type, final standing/placement, legs won, and total legs completed. |
| **`legs`** | `.csv`, `.parquet` | Leg itineraries: origin and destination countries/cities, number of route stops, challenge count, and full narrative summary. |
| **`leg_results`** | `.csv`, `.parquet` | Granular leg finish placements for every team: placement rank (1st, 2nd, etc.), Non-Elimination Leg (NEL) saves, Fast Forward usage, U-Turns, and Speed Bumps. |
| **`tasks`** | `.csv`, `.parquet` | Detailed challenges: Detours, Roadblocks, Route Info, Speed Bumps, and Fast Forwards with full task descriptions. |

### AI Training Corpora (`data/ai/`)

| File | Format | Use Case | Description |
| :--- | :--- | :--- | :--- |
| **`tar_qa_finetuning.jsonl`** | Chat JSONL | SFT / Instruction Tuning | High-quality multi-turn question-answer pairs formatted for OpenAI / Gemini fine-tuning covering winners, rules, eliminations, routes, and challenges. |
| **`tar_knowledge_corpus.jsonl`** | JSONL | RAG / Embeddings / Pre-training | Structured narrative documents with metadata (season, leg, route) suitable for vector database retrieval and context injection. |

---

## :runner: Quick Start with `uv` & `task`

This repository uses [`uv`](https://docs.astral.sh/uv/) for Python packaging and [`go-task`](https://taskfile.dev/) (`task`) as the task runner.

### Prerequisites

Ensure `uv` and `task` are installed:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install task (macOS / Linux via Homebrew, or see https://taskfile.dev/installation/)
brew install go-task
```

### Installation

Clone and initialize the virtual environment with all extras:
```bash
git clone https://github.com/nicholaswilde/the-amazing-race.git
cd the-amazing-race
task sync
```

---

## :hammer_and_wrench: Task Runner (`task`)

All repository workflows can be driven directly via `task`:

```bash
task                  # List all available tasks
task check            # Run linting, test suite, and dataset validation
task test             # Run pytest test suite
task lint             # Lint code with ruff
task format           # Format code with ruff
task build            # Compile raw data into tidy CSV + Parquet tables
task validate         # Verify dataset schema and relational integrity
task stats            # Show table row counts and summary stats
task export:ai        # Export fine-tuning and RAG JSONL corpora
task scrape:wiki      # Scrape Wikipedia seasons (pass args via --, e.g. -- --season 1)
task scrape:fandom    # Scrape Fandom Wiki infoboxes
task scrape:reddit    # Scrape Reddit discussion threads
task import:sheet     # Import community Google Sheets or external CSVs
task codegraph:status # Inspect CodeGraph index status
```

---

## :computer: CLI Usage

All tasks are also accessible through the direct `tar-dataset` CLI:

### 1. Scrape Wikipedia
Scrapes contestant demographics, results matrices, episode ratings, and leg task narratives:
```bash
# Scrape a specific season
uv run tar-dataset scrape-wiki --season 1

# Scrape all US seasons (1 through 36)
uv run tar-dataset scrape-wiki --start 1 --end 36

# Scrape international franchises (e.g. Canada)
uv run tar-dataset scrape-wiki --start 1 --end 10 --version CAN
```

### 2. Scrape Fandom Wiki
Extracts infoboxes, route coordinates, and show trivia from `amazingrace.fandom.com`:
```bash
uv run tar-dataset scrape-fandom --season 1
uv run tar-dataset scrape-fandom --start 1 --end 36
```

### 3. Scrape Reddit Discussions
Collects episode discussion threads, post-episode reactions, and top user comments from `r/TheAmazingRace` (no API key required):
```bash
uv run tar-dataset scrape-reddit --query "Episode Discussion" --limit 25 --comments
uv run tar-dataset scrape-reddit --query "AMA" --limit 10
```

### 4. Import Google Sheets & CSVs
Imports fan-maintained spreadsheets (leg times, detour choice stats, roadblock tallies):
```bash
uv run tar-dataset import-sheet \
  --url "https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit#gid=0" \
  --name "tar_leg_times"
```

### 5. Build Tidy Datasets
Transforms cached raw scrapes into tidy CSV and Parquet files:
```bash
uv run tar-dataset build
```

### 6. Export AI Training Datasets
Generates conversational Q&A pairs and RAG knowledge corpora:
```bash
uv run tar-dataset export-ai
```

### 7. Validate Data Integrity
Checks relational consistency, missing values, and schema constraints:
```bash
uv run tar-dataset validate
```

### 8. View Dataset Statistics
```bash
uv run tar-dataset stats
```

---

## :robot: Agent / Antigravity Skills

For AI agents operating in this workspace, modular skills are available in `.agents/skills/`:
- **`tar-scrape-wiki`**: Instructions and commands for Wikipedia & Fandom extraction.
- **`tar-scrape-reddit`**: Extraction runbook for r/TheAmazingRace discussions.
- **`tar-import-sheets`**: Workflow for community Google Sheets and CSV import.
- **`tar-dataset-builder`**: Tidy data compilation, validation, and AI JSONL export.

---

## :dash: Running Tests & Quality Checks

Run the test suite and quality checks via `task` or `pytest`:
```bash
# Run pytest test suite
task test
# or: uv run --extra dev pytest

# Run all quality checks (lint, format-check, tests, and dataset validation)
task check
```

## :balance_scale: License

[Apache License 2.0](LICENSE)

## :writing_hand: Author

This project was started in 2026 by [Nicholas Wilde](https://github.com/nicholaswilde/).
