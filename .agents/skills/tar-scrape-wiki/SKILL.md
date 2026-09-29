---
name: tar-scrape-wiki
description: >-
  Use this skill to scrape and extract The Amazing Race season summaries, contestant demographics,
  race results matrices, episode ratings, and leg task narratives from Wikipedia and Fandom wikis.
---

# Scrape Wikipedia & Fandom for The Amazing Race

This skill provides step-by-step instructions to scrape structured data from Wikipedia and Fandom (`amazingrace.fandom.com`) using `uv run tar-dataset`.

## Usage

### 1. Scrape a Specific Season from Wikipedia

```bash
uv run tar-dataset scrape-wiki --season 1
```

Parameters:
- `--season`, `-s`: Season number (e.g. `1`, `35`).
- `--version`, `-v`: Franchise code: `US` (default), `CAN` (Canada), `AUS` (Australia).

### 2. Scrape a Range of Seasons

To scrape all US seasons (e.g. 1 through 36):
```bash
uv run tar-dataset scrape-wiki --start 1 --end 36
```

### 3. Scrape Fandom Wiki (Metadata & Infoboxes)

```bash
uv run tar-dataset scrape-fandom --season 1
# or range:
uv run tar-dataset scrape-fandom --start 1 --end 36
```

## Raw Output Files

- `data/raw/wikipedia/season_<version>_<season_num:02d>.json`
- `data/raw/fandom/fandom_<version>_<season_num:02d>.json`

## Verification

Check that files are generated in `data/raw/wikipedia/`:
```bash
ls -la data/raw/wikipedia/
```

After scraping, build the tidy tables using the `tar-dataset-builder` skill.

## Progress Tracking

Whenever seasons are scraped or imported, ensure to update GitHub Issue #4 to record progress:
```bash
rtk gh issue comment 4 --body "Imported Season <N> (<version>): <details>" | cat
```

