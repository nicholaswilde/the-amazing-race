---
name: tar-import-sheets
description: >-
  Use this skill to import community Google Sheets spreadsheets and external CSV tables
  containing leg times, roadblock trackers, or statistical models into the Amazing Race dataset.
---

# Import Community Google Sheets & CSVs

The Amazing Race fan community maintains extensive spreadsheets detailing leg times, flight trackers, roadblock counts, and detour statistics. This skill imports them automatically into standardized formats.

## Usage

### 1. Import a Public Google Sheet

Provide any public sharing or view link to a Google Spreadsheet:

```bash
uv run tar-dataset import-sheet \
  --url "https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit#gid=0" \
  --name "tar_community_times"
```

Parameters:
- `--url`, `-u`: Public Google Sheet URL or direct CSV URL.
- `--name`, `-n`: Output filename slug (saved under `data/raw/sheets/<name>.csv`).
- `--gid`, `-g`: Specific sheet tab GID (default `0`).

### 2. Output Format

Imported sheets are normalized with `snake_case` column headers and saved to:
- `data/raw/sheets/<name>.csv`

## Verification

Check that the CSV file was created and check row count:
```bash
wc -l data/raw/sheets/<name>.csv
head -n 5 data/raw/sheets/<name>.csv
```
