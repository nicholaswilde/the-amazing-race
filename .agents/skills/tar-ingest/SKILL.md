---
name: tar-ingest
description: >-
  Automates checking for new broadcast episodes and seasons of The Amazing Race,
  checking Wikipedia revision changes (revid), executing the pipeline, and updating GitHub Issue #4.
---

# Ingest and Track The Amazing Race Broadcast Seasons

This skill automates checking for newly aired episodes, scraping fresh broadcast data with MediaWiki revision (`revid`) change detection, running the data pipeline, and updating **GitHub Issue #4** per project guidelines.

## Protocol & Workflows

### 1. Check for New Broadcast Episodes or Seasons (Lightweight)

Check if new episode or season data is available without executing the full build pipeline:

```bash
task ingest:check
# Or directly via script:
./scripts/schedule_ingest.py --check-only
```

This uses MediaWiki `revid` queries (<200 bytes) to detect whether Wikipedia has new edits since the last cached scrape.

### 2. Run Scheduled Ingestion & Pipeline Sync

To fetch new episodes, execute the compilation pipeline, and log progress to GitHub Issue #4:

```bash
task ingest:run
# Or with explicit arguments:
./scripts/schedule_ingest.py --post-comment --issue-num 4
```

### 3. Force Re-ingestion for In-Progress Season

To force re-scraping and rebuilding regardless of cache status:

```bash
./scripts/schedule_ingest.py --force --post-comment --issue-num 4
```

### 4. Manual Season Ingestion Steps

If running individual steps manually:

1. **Scrape Wikipedia & Fandom**:
   ```bash
   uv run tar-dataset scrape-wiki --season <N>
   uv run tar-dataset scrape-fandom --season <N>
   ```

2. **Rebuild Pipeline Tables**:
   ```bash
   task pipeline
   # Or include in-progress seasons in tidy output:
   uv run tar-dataset build --include-in-progress
   ```

3. **Update GitHub Issue #4**:
   Always post progress tracking to Issue #4:
   ```bash
   rtk gh issue comment 4 --body "Imported Season <N> (<version>): <summary details>" | cat
   ```
