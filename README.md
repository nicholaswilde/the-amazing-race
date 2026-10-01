# :card_index_dividers: The Amazing Race Dataset & AI Training Corpus :checkered_flag:
[![CI](https://img.shields.io/github/actions/workflow/status/nicholaswilde/the-amazing-race/ci.yml?branch=main&style=for-the-badge&logo=github&logoColor=white&label=CI)](https://github.com/nicholaswilde/the-amazing-race/actions/workflows/ci.yml)
[![task](https://img.shields.io/badge/Task-Enabled-brightgreen?style=for-the-badge&logo=task&logoColor=white)](https://taskfile.dev/#/)
[![Coverage](https://img.shields.io/coveralls/github/nicholaswilde/the-amazing-race/main?style=for-the-badge&logo=coveralls)](https://coveralls.io/github/nicholaswilde/the-amazing-race?branch=main)
[![DOI](https://zenodo.org/badge/1394466925.svg)](https://zenodo.org/badge/latestdoi/1394466925)

A comprehensive tidy dataset and AI training corpus for the CBS reality competition television series **[The Amazing Race](https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series))**.

Inspired by [doehm/alone](https://github.com/doehm/alone), this repository provides structured, relational datasets in tidy format (available in both **CSV** and **Apache Parquet**) alongside JSONL corpora designed for **LLM fine-tuning, RAG (Retrieval-Augmented Generation), and pre-training**.

> [!WARNING]
> This project is currently in a `v0.X.X` development stage. Features and configurations are subject to change, and breaking changes may be introduced at any time.

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
| **[`llms.txt`](llms.txt)** | Text / Markdown | LLM Context Index | Standardized compact index and link manifest conforming to the [`/llms.txt`](https://llmstxt.org) standard for fast agent context ingestion. |
| **[`llms-full.txt`](llms-full.txt)** | Text / Markdown | Zero-Hop LLM Context | Standalone, complete repository reference, data dictionary, CLI guide, and analytical formulas for LLM context windows. |

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

## :package: Release Asset Packages

Pre-built distribution bundles are published with every [GitHub Release](https://github.com/nicholaswilde/the-amazing-race/releases). You can download and use these standalone assets immediately without cloning the repository or setting up the development environment.

| Package | Asset Pattern | Format | Primary Use Case |
| :--- | :--- | :--- | :--- |
| **Tidy CSV Bundle** | `tar-dataset-csv-<version>.zip` | CSV + Markdown | Universal data analysis (Python, R, Excel, Google Sheets, BI tools) |
| **Apache Parquet Bundle** | `tar-dataset-parquet-<version>.zip` | Apache Parquet | High-performance analytics (DuckDB, Polars, PyArrow, Pandas) |
| **SQLite Database** | `tar-dataset-sqlite-<version>.zip` | SQLite (`tar.db`) | Relational SQL querying, database browsers, local apps |
| **AI Training Corpus** | `tar-dataset-ai-<version>.zip` | JSONL | LLM fine-tuning, RAG vector search, benchmark evaluation |
| **R Data Package** | `theamazingrace_<version>.tar.gz` | R Source Tarball | Native R data package (`library(theamazingrace)`) |
| **Python Package** | `the_amazing_race-<version>-py3-none-any.whl`<br>`the_amazing_race-<version>.tar.gz` | Wheel / Sdist | Standalone `tar-dataset` CLI and Python schemas library |
| **Integrity & Metadata** | `checksums.txt`<br>`manifest.json` | Text / JSON | SHA-256 verification and dataset build metadata |

---

### 1. Tidy CSV Bundle (`tar-dataset-csv-<version>.zip`)

Contains all 7 relational tidy datasets (`seasons.csv`, `episodes.csv`, `contestants.csv`, `teams.csv`, `legs.csv`, `leg_results.csv`, `tasks.csv`) alongside the data dictionary.

```bash
# Extract archive
unzip tar-dataset-csv-*.zip
```

- **Python (Pandas)**:
  ```python
  import pandas as pd

  seasons = pd.read_csv("seasons.csv")
  teams = pd.read_csv("teams.csv")
  winners = teams[teams["winner"] == 1]
  ```

- **R (`readr` / `tidyverse`)**:
  ```r
  library(readr)
  library(dplyr)

  seasons <- read_csv("seasons.csv")
  teams <- read_csv("teams.csv")
  ```

- **Spreadsheets / BI**: Import directly into Microsoft Excel, Google Sheets, Tableau, or Power BI.

---

### 2. Apache Parquet Bundle (`tar-dataset-parquet-<version>.zip`)

Contains columnar Apache Parquet files preserving strict data types, nested fields, and columnar compression for zero-copy high-throughput analysis.

```bash
# Extract archive
unzip tar-dataset-parquet-*.zip
```

- **DuckDB (Direct SQL)**:
  ```python
  import duckdb

  # Query parquet files directly with SQL without loading into memory:
  duckdb.sql("""
      SELECT season, winner, legs, countries_visited
      FROM 'seasons.parquet'
      ORDER BY season ASC
  """).show()
  ```

- **Polars / Pandas**:
  ```python
  import polars as pl
  seasons = pl.read_parquet("seasons.parquet")

  import pandas as pd
  teams = pd.read_parquet("teams.parquet")
  ```

- **R (`arrow`)**:
  ```r
  library(arrow)
  seasons <- read_parquet("seasons.parquet")
  ```

---

### 3. SQLite Database Bundle (`tar-dataset-sqlite-<version>.zip`)

Contains a ready-to-query, indexed SQLite relational database (`tar.db`) with primary/foreign keys configured across all 7 tables.

```bash
# Extract archive
unzip tar-dataset-sqlite-*.zip
```

- **Command Line (`sqlite3`)**:
  ```bash
  sqlite3 -header -column tar.db "
    SELECT season, winner, destination_summary
    FROM seasons
    LIMIT 5;
  "
  ```

- **Python (`sqlite3`)**:
  ```python
  import sqlite3
  import pandas as pd

  conn = sqlite3.connect("tar.db")
  query = """
    SELECT t.team_name, t.season, t.racing_average, s.winner
    FROM teams t
    JOIN seasons s ON t.season = s.season
    WHERE t.winner = 1
    ORDER BY t.racing_average ASC
  """
  winning_teams = pd.read_sql_query(query, conn)
  conn.close()
  ```

- **GUI Clients**: Open directly with [DB Browser for SQLite](https://sqlitebrowser.org/), DBeaver, or Datasette (`datasette tar.db`).

---

### 4. AI Training & Fine-Tuning Corpus (`tar-dataset-ai-<version>.zip`)

Contains JSONL corpora optimized for training, fine-tuning, and evaluating Large Language Models:

- **`tar_qa_finetuning.jsonl`**: Supervised fine-tuning (SFT) conversation pairs formatted with multi-turn messages (system, user, assistant) for OpenAI, Gemini, Claude, or local model tuning (Unsloth, Axolotl).
- **`tar_knowledge_corpus.jsonl`**: Curated reference knowledge documents with rich metadata (`season`, `leg`, `route`) for semantic search, vector indexing, and RAG pipelines (LangChain, LlamaIndex, ChromaDB, Qdrant).
- **`tar_benchmark_suite.jsonl`**: 45 evaluation questions with verified ground truths and rubrics covering game rules, racing statistics, route itineraries, and trivia.

```bash
# Extract archive
unzip tar-dataset-ai-*.zip
```

- **Inspect Fine-Tuning Pairs**:
  ```bash
  head -n 2 tar_qa_finetuning.jsonl
  ```

- **Load Knowledge Corpus in Python**:
  ```python
  import json

  # Load documents for RAG vector embedding:
  with open("tar_knowledge_corpus.jsonl", "r", encoding="utf-8") as f:
      corpus = [json.loads(line) for line in f]

  print(f"Loaded {len(corpus)} knowledge documents.")
  print("Sample document:", corpus[0]["text"][:200])
  ```

---

### 5. Companion R Package Source (`theamazingrace_<version>.tar.gz`)

A CRAN-compliant R source package archive containing all 7 datasets pre-loaded as native `.rda` objects with comprehensive Roxygen documentation and dataset schemas.

- **Install from Downloaded Release Asset**:
  ```r
  install.packages("theamazingrace_0.1.0.tar.gz", repos = NULL, type = "source")
  ```

- **Install Direct from GitHub (Development)**:
  ```r
  remotes::install_github("nicholaswilde/the-amazing-race/r")
  ```

- **Usage in R**:
  ```r
  library(theamazingrace)

  # Load datasets
  data(seasons)
  data(teams)
  data(leg_results)

  # View help pages and schema definitions
  ?seasons
  ?teams
  ```

---

### 6. Python Distribution Wheel & Sdist (`.whl` and `.tar.gz`)

Pre-compiled Python packages that allow installing the `tar_dataset` library and `tar-dataset` CLI directly via `pip` or `uv` without cloning the repository.

- **Installation**:
  ```bash
  # Using uv:
  uv pip install the_amazing_race-0.1.0-py3-none-any.whl

  # Or using pip:
  pip install the_amazing_race-0.1.0-py3-none-any.whl
  ```

- **Use the CLI**:
  ```bash
  # Inspect seasons, teams, and challenges:
  tar-dataset inspect season 1
  tar-dataset inspect team "Rob & Amber"

  # Display dataset statistics:
  tar-dataset stats

  # Audit dataset completeness:
  tar-dataset audit
  ```

- **Use the Python Library**:
  ```python
  from tar_dataset.schemas import Season, Team, LegResult
  ```

---

### 7. Integrity Checksums & Manifest (`checksums.txt`, `manifest.json`)

Every release includes cryptographic hashes and build metadata to verify package authenticity and inspect schema versions.

- **Verify Asset Integrity**:
  ```bash
  # Verify all downloaded files against SHA-256 checksums:
  sha256sum --check checksums.txt
  ```

- **Inspect Manifest Metadata**:
  ```bash
  # Inspect table row counts, file sizes, and release metadata:
  jq . manifest.json
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
task release          # Automated release tagging, validation, and bump (./scripts/release.sh)
task release:summary  # Generate categorized release notes and update draft release
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
- **`release`**: Automated version bumping, validation (`task check`), tagging, and atomic push.
- **`release-summary`**: Changelog formatting from git logs and GitHub draft release updating.

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

---

## :books: Sources & References

This dataset synthesizes information from encyclopedic records, fan community databases, and discussion forums:

### 1. Primary Encyclopedic Records
- **[Wikipedia - The Amazing Race](https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series))**: Primary source for official season broadcast dates, episode titles, Nielsen television viewership ratings, contestant demographics, route itineraries, and elimination results matrices across US and international editions.
- **[The Amazing Race Fandom Wiki](https://amazingrace.fandom.com/)**: Detailed challenge descriptions, clue transcriptions, route marker locations, Detour options, Roadblock performers, Speed Bumps, Fast Forwards, and racer background trivia.

### 2. Fan Discussions & Commentary
- **[r/TheAmazingRace Subreddit](https://www.reddit.com/r/TheAmazingRace/)**: Source for episodic reaction threads, live discussions, post-episode analysis, and contestant AMA archives used in AI conversational training datasets.

### 3. Community Spreadsheets & Tracking Databases
- **[wavesei Comprehensive TAR Spreadsheet](https://docs.google.com/spreadsheets/d/1fiPwfl9fVSzrZbYn8IwbRWpV_5OUPl2A/edit)**: Challenge-by-challenge breakdowns, detour selections, roadblock tracking, finishing positions, leg-by-leg outcomes, and COVID-era season mechanics.
- **[TAR Statistics](https://docs.google.com/spreadsheets/d/1UEZRVYLCDnWjBhrDWxRar_dvUrkgcsqP1CREOkHHSc4/edit)**: Historical statistics covering US and international franchises, age gap vs. placement, gender performance metrics, returning racer records, top-3 relative ranks, and racing averages.
- **[The Amazing Race Placement Database](https://docs.google.com/spreadsheets/d/1jjp3mq4uTThVx3IArUE-wOktGKO_zsr3KWfefGPLM8Q/edit)**: Relational tables of seasons, teams, racers, legs, and placements across global franchises.

### 4. Architectural & Schema Inspiration
- **[doehm/alone](https://github.com/doehm/alone)**: Reference package architecture for tidy TV survival and reality show datasets in R and Parquet.
- **[doehm/survivoR](https://github.com/doehm/survivoR)**: Design principles for game show statistics and survival analytics.

---

## :bookmark: Citation

If you use this dataset, companion R package, or AI training corpus in your research, visualizations, or educational coursework, please cite it as:

```bibtex
@misc{wilde_amazing_race_2026,
  author       = {Nicholas Wilde},
  title        = {The Amazing Race Dataset & AI Training Corpus},
  year         = {2026},
  version      = {0.1.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.1394466925},
  url          = {https://github.com/nicholaswilde/the-amazing-race}
}
```

Or in APA format:
> Wilde, N. (2026). *The Amazing Race Dataset & AI Training Corpus* (Version 0.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.1394466925

---

## :balance_scale: License

[Apache License 2.0](LICENSE)

## :writing_hand: Author

This project was started in 2026 by [Nicholas Wilde](https://github.com/nicholaswilde/).
