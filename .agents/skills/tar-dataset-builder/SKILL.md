---
name: tar-dataset-builder
description: >-
  Use this skill to transform raw scraped data into tidy relational datasets (alone-style CSV/Parquet),
  validate data integrity, and export AI training corpora (JSONL for fine-tuning, RAG, and pretraining).
---

# Build & Export The Amazing Race Dataset

This skill executes the transformation pipeline that takes raw scraped data (from Wikipedia, Fandom, Reddit, and Sheets) and compiles it into:
1. **Tidy relational tables** in `data/processed/` (both CSV and Apache Parquet formats, following the `doehm/alone` structure; local reference at `/home/nicholas/git/doehm/alone`).
2. **AI Training corpora** in `data/ai/` (JSONL formatted for chat fine-tuning and RAG embeddings).

## Commands

### 1. Build Tidy Tables

```bash
uv run tar-dataset build
```

This processes all raw JSON files in `data/raw/wikipedia/` and outputs:
- `data/processed/seasons.csv` & `.parquet`: Season overview, winners, route distance, filming dates.
- `data/processed/episodes.csv` & `.parquet`: Episode air dates, viewers (millions), titles.
- `data/processed/contestants.csv` & `.parquet`: Individual racers, ages, relationships, hometowns, finish status.
- `data/processed/teams.csv` & `.parquet`: Teams, relationships, placements, legs won, legs completed.
- `data/processed/legs.csv` & `.parquet`: Route destinations, stops count, tasks count, narrative summaries.
- `data/processed/leg_results.csv` & `.parquet`: Leg-by-leg placements, Fast Forwards, U-Turns, NEL saves.
- `data/processed/tasks.csv` & `.parquet`: Detailed descriptions of Detours, Roadblocks, and Route challenges.

### 2. Export AI Training Datasets

```bash
uv run tar-dataset export-ai
```

Generates:
- `data/ai/tar_qa_finetuning.jsonl`: Multi-turn instruction fine-tuning dataset formatted with `system`, `user`, and `assistant` messages covering winners, team stats, leg routes, and challenge rules.
- `data/ai/tar_knowledge_corpus.jsonl`: Structured narrative chunks with metadata for RAG vector stores or LLM continuous pre-training.

### 3. Validate Integrity

```bash
uv run tar-dataset validate
```

Checks table schemas, validates relational consistency between contestants and teams, checks for unexpected null placements, and reports PASS/WARNING/FAIL status.

### 4. View Dataset Statistics

```bash
uv run tar-dataset stats
```
