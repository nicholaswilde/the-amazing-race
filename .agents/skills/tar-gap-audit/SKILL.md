---
name: tar-gap-audit
description: >-
  Audit dataset completeness, calculate missing cell rates, and backfill broadcast ratings or demographic gaps.
---

# Dataset Gap Auditor & Backfill Guide

This skill audits missing cells, null rates, and incomplete fields across all 7 processed tables in The Amazing Race dataset, and guides backfilling television ratings and demographic gaps.

## Auditing Commands

### 1. High-Level Dataset Gap Summary

```bash
task gaps
# Or directly via CLI:
uv run tar-dataset gaps
```

### 2. Detailed Column-by-Column & Season Breakdown

```bash
uv run tar-dataset gaps --detail
```

### 3. Filter by Specific Table or Season

```bash
# Check episode viewership gaps
uv run tar-dataset gaps --table episodes --detail

# Check specific season gaps
uv run tar-dataset gaps --season 39 --detail
```

### 4. Export Markdown Gap Report

Export the latest audit report to `docs/dataset_gaps.md`:

```bash
uv run tar-dataset gaps --export-md docs/dataset_gaps.md
```

## Viewership & Ratings Backfill Protocol

Per project guidelines:
> When auditing or backfilling broadcast viewership (`viewers_millions`) or ratings where Wikipedia or Fandom tables list `TBD` or pending data, cross-reference industry television ratings databases such as **The TV Ratings Guide** (`thetvratingsguide.com`) and **USTVDB** (`ustvdb.com`).

### Workflow:
1. Identify missing or pending `viewers_millions` values using `tar-dataset gaps --table episodes --detail`.
2. Look up broadcast ratings on:
   - **The TV Ratings Guide**: `https://www.thetvratingsguide.com/`
   - **USTVDB**: `https://ustvdb.com/`
3. Add hardcoded or scraped overrides to the episode parser in `src/tar_dataset/scrapers/wikipedia.py` or `src/tar_dataset/processors/builder.py`.
4. Rebuild the dataset:
   ```bash
   task build
   task validate
   ```
