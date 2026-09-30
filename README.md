# :card_index_dividers: The Amazing Race Dataset & AI Training Corpus :checkered_flag:
[![CI](https://img.shields.io/github/actions/workflow/status/nicholaswilde/the-amazing-race/ci.yml?branch=main&style=for-the-badge&logo=github&logoColor=white&label=CI)](https://github.com/nicholaswilde/the-amazing-race/actions/workflows/ci.yml)
[![task](https://img.shields.io/badge/Task-Enabled-brightgreen?style=for-the-badge&logo=task&logoColor=white)](https://taskfile.dev/#/)
[![Coverage](https://img.shields.io/coveralls/github/nicholaswilde/the-amazing-race/main?style=for-the-badge&logo=coveralls)](https://coveralls.io/github/nicholaswilde/the-amazing-race?branch=main)

A comprehensive tidy dataset and AI training corpus for the CBS reality competition television series **[The Amazing Race](https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series))**.

Inspired by [doehm/alone](https://github.com/doehm/alone), this repository provides structured, relational datasets in tidy format (available in both **CSV** and **Apache Parquet**) alongside JSONL corpora designed for **LLM fine-tuning, RAG (Retrieval-Augmented Generation), and pre-training**.

---

## :card_index_dividers: Architecture & Dataset Schema

The dataset is partitioned into clean relational tables adhering to tidy data principles:

### Tidy Datasets (`data/processed/`)

> **Comprehensive Documentation**: See the [Data Dictionary & Schema Reference](docs/data_dictionary.md) for complete column descriptions, primary/foreign keys, and Entity-Relationship diagrams across all 7 tables.  
> **Interactive Notebook**: Check out [`notebooks/tar_exploration.ipynb`](notebooks/tar_exploration.ipynb) for a reference starter guide covering racing averages, route maps, and data analysis.

All processed tables are provided in **CSV**, **Apache Parquet**, **Apache Arrow IPC** (`data/processed/arrow/`), and native **R** formats (`.rds` and `.rda` in `data/processed/r/`), alongside a unified **SQLite** relational database (`data/processed/tar.db`) for zero-dependency SQL querying.

| Dataset | Formats | Description |
| :--- | :--- | :--- |
| **`seasons`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Season-level summary: franchise country (`version`), season number, winner names, total legs, teams count, route distance (miles & km), filming dates, and broadcast dates. |
| **`episodes`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Episode broadcast metadata, titles (racer quotes), air dates, and Nielsen television viewership ratings (millions). |
| **`contestants`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Individual racer demographics: unique `contestant_id`, full name, age, relationship, hometown, and final finish status. |
| **`teams`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Team-level profiles: `team_id`, member pairing, relationship type, final standing/placement, legs won, and total legs completed. |
| **`legs`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Leg itineraries: origin and destination countries/cities, number of route stops, challenge count, and full narrative summary. |
| **`leg_results`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Granular leg finish placements for every team: placement rank (1st, 2nd, etc.), Non-Elimination Leg (NEL) saves, Fast Forward usage, U-Turns, and Speed Bumps. |
| **`tasks`** | `.csv`, `.parquet`, `.arrow`, `.rds`, `.rda`, `tar.db` | Detailed challenges: Detours, Roadblocks, Route Info, Speed Bumps, and Fast Forwards with full task descriptions. |

### AI Training Corpora & Benchmarks (`data/ai/`)

| File | Format | Use Case | Description |
| :--- | :--- | :--- | :--- |
| **`tar_qa_finetuning.jsonl`** | Chat JSONL | SFT / Instruction Tuning | High-quality multi-turn question-answer pairs formatted for OpenAI / Gemini fine-tuning covering winners, rules, eliminations, routes, and challenges. |
| **`tar_knowledge_corpus.jsonl`** | JSONL | RAG / Embeddings / Pre-training | Structured narrative documents with metadata (season, leg, route) suitable for vector database retrieval and context injection. |
| **`tar_benchmark_suite.jsonl`** | JSONL | Evaluation & Benchmarking | 45 curated evaluation benchmark questions with rubrics, scoring trivia, rules comprehension, and route accuracy. |
| **`huggingface/`** | Arrow Datasets | HF `datasets` Direct Loading | Ready-to-load HuggingFace Datasets disk bundles for high-throughput training. |

### Companion R Data Package (`r/`)

A companion R package, **`theamazingrace`**, is located in the [`r/`](r/) directory, providing instant access to all 7 tidy datasets following the conventions of reality TV data packages (`alone`, `survivoR`, `bakeoff`):

```r
# Install development version directly from GitHub:
remotes::install_github("nicholaswilde/the-amazing-race/r")

# Load library and datasets:
library(theamazingrace)
data(seasons)
data(episodes)
```

Direct high-performance columnar reading in R without loading package `.rda` objects is also supported via `{arrow}`:
```r
library(arrow)
seasons <- read_parquet("data/processed/seasons.parquet")
```

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
task test:coverage    # Run pytest with branch test coverage reporting
task coverage:report  # Generate HTML test coverage report (htmlcov/)
task coverage:upload  # Upload coverage results to Coveralls.io
task lint             # Lint code with ruff
task format           # Format code with ruff
task pipeline         # Full end-to-end rebuild: build, export all formats, eval, and check
task build            # Compile raw data into tidy CSV + Parquet + SQLite tables
task export:sqlite    # Export unified SQLite bundle (tar.db)
task export:arrow     # Export Apache Arrow IPC files and HuggingFace datasets
task export:r         # Export native R datasets (.rds, .rda) and companion package (r/)
task export:ai        # Export fine-tuning and RAG JSONL corpora
task package          # Build all segmented release bundles and checksums
task package:csv      # Build tidy CSV release bundle
task package:parquet  # Build Parquet columnar release bundle
task package:ai       # Build AI training datasets bundle
task package:r        # Build R companion source package tarball
task eval:benchmark   # Evaluate 45 curated AI benchmark questions
task validate         # Verify dataset schema and relational integrity
task stats            # Show table row counts and summary stats
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
Collects episode discussion threads, live broadcast reactions, post-episode debriefs, and racer AMAs from `r/TheAmazingRace`:
```bash
# Scrape official episode discussions
uv run tar-dataset scrape-reddit --query "Discussion Thread" --limit 50

# Scrape live broadcast reactions
uv run tar-dataset scrape-reddit --query "Live Discussion" --limit 50

# Scrape post-episode debriefs
uv run tar-dataset scrape-reddit --query "Post-Episode Discussion" --limit 50

# Scrape racer AMAs
uv run tar-dataset scrape-reddit --query "AMA" --limit 25

# Batch scrape all 4 discussion categories in one shot
task scrape:reddit:all
# or: uv run tar-dataset scrape-reddit --batch
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

### 8. Export SQLite Bundle
Generates the composite `tar.db` SQLite database:
```bash
uv run tar-dataset export-sqlite
# or via task:
task export:sqlite
```

### 9. Export Apache Arrow & HuggingFace Datasets
Serializes tables to `.arrow` files and builds HuggingFace disk datasets:
```bash
uv run tar-dataset export-arrow
# or via task:
task export:arrow
```

### 10. Export Native R Datasets & Companion Package (.rds, .rda)
Exports compressed `.rds` files to `data/processed/r/`, `.rda` objects to `r/data/`, and generates roxygen2 documentation:
```bash
uv run tar-dataset export-r
# or via task:
task export:r
```

### 11. Evaluate AI Benchmark Suite
Scores LLM trivia, rules comprehension, and route accuracy against 45 curated prompts:
```bash
uv run tar-dataset eval-benchmark
# or via task:
task eval:benchmark
```

### 12. Inspect Seasons, Teams, and Racers in the Terminal
Interactively inspect details, routes, and statistics with Rich terminal formatting:
```bash
# Inspect Season overview, legs itinerary, and leaderboard
uv run tar-dataset show season 1

# Inspect Team profile, members, racing average, and leg-by-leg placements
uv run tar-dataset show team "Rob & Brennan"

# Inspect Contestant profile
uv run tar-dataset show racer "Rob Frisbee"

# Inspect specific Leg challenges and narrative
uv run tar-dataset show leg 1 --season 1
```

### 13. View Dataset Statistics
```bash
uv run tar-dataset stats
```

### 14. Audit Dataset Gaps & Missingness
Identifies null cells, season-level missingness, and column completeness rates:
```bash
# Run full completeness audit across all 7 tables
uv run tar-dataset gaps
# or via task:
task gaps

# Drill down into specific tables or seasons
uv run tar-dataset gaps --table contestants
uv run tar-dataset gaps --season 29 --detail

# Export markdown audit report
uv run tar-dataset gaps --export-md docs/dataset_gaps.md
```

### 15. Package Release Distribution Bundles
Generates targeted asset packages for CSV, Parquet, AI corpora, R, and Python distributions with SHA-256 checksums:
```bash
# Package all distribution bundles
uv run tar-dataset package --version 0.1.0

# Package specific component
uv run tar-dataset package --component csv
uv run tar-dataset package --component parquet
uv run tar-dataset package --component ai
uv run tar-dataset package --component r
uv run tar-dataset package --component python
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
