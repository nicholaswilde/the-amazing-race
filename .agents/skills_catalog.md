# Agent Skills Catalog

Catalog of custom Antigravity agent skills available in `the-amazing-race`.

| Skill | Description | Task / Command |
|---|---|---|
| [`release`](skills/release/SKILL.md) | Automates versioning, validation, tagging, and atomic push | `./scripts/release.sh` |
| [`release-summary`](skills/release-summary/SKILL.md) | Generates categorized release notes and updates draft release | `./scripts/release_summary.py` |
| [`tar-dataset-builder`](skills/tar-dataset-builder/SKILL.md) | Compiles raw data into tidy tables and exports AI training JSONL | `task build` |
| [`tar-gap-audit`](skills/tar-gap-audit/SKILL.md) | Audits dataset completeness, null rates, and guides backfilling | `task gaps` |
| [`tar-import-sheets`](skills/tar-import-sheets/SKILL.md) | Imports community Google Sheets and CSVs | `task import:sheet` |
| [`tar-ingest`](skills/tar-ingest/SKILL.md) | Automates season checking, revision detection, build, and tracking | `task ingest:run` |
| [`tar-predict`](skills/tar-predict/SKILL.md) | Predicts race outcomes and risks using empirical modeling | `task predict` |
| [`tar-scrape-reddit`](skills/tar-scrape-reddit/SKILL.md) | Extracts discussion threads and comments from r/TheAmazingRace | `task scrape:reddit` |
| [`tar-scrape-wiki`](skills/tar-scrape-wiki/SKILL.md) | Scrapes Wikipedia and Fandom for seasons and results | `task scrape:wiki` |
| [`tar-tidytuesday`](skills/tar-tidytuesday/SKILL.md) | Packages and manages R4DS TidyTuesday intake bundles | `task package:tidytuesday` |
