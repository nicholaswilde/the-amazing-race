---
name: tar-tidytuesday
description: >-
  Curate, package, validate, and submit The Amazing Race dataset to R for Data Science (R4DS) TidyTuesday.
---

# R4DS TidyTuesday Dataset Curation & Submission

This skill guides maintaining, packaging, and submitting The Amazing Race dataset to the [R for Data Science (R4DS) TidyTuesday](https://github.com/rfordatascience/tidytuesday) community.

## Structure & Core Files

All TidyTuesday materials reside in `tidytuesday/`:
- `tidytuesday/readme.md`: Background, game mechanics, data dictionary, and exploration prompts.
- `tidytuesday/cleaning.R`: Reproducible data cleaning and preparation script.
- `tidytuesday/exploration.R`: Starter exploration script (`tidyverse`, `ggplot2`, `ggraph`, `tidygraph`).
- `tidytuesday/submission_issue.md`: Pre-filled template for GitHub issue submission.

## Workflows

### 1. Build TidyTuesday Distribution Bundle

Create the self-contained zip asset (`tar-dataset-tidytuesday-<version>.zip`):

```bash
task package:tidytuesday
# Or directly via CLI:
uv run tar-dataset package --component tidytuesday
```

The generated archive is written to `dist/release/` and includes all 7 cleaned CSV tables, documentation, cleaning script, exploration script, and license.

### 2. Validate Intake Package (Dry-Run)

Verify that all required files, image URLs, and GitHub authentication are ready:

```bash
./scripts/submit_tidytuesday.py
```

### 3. Submit Dataset to R4DS TidyTuesday

Submit the issue to upstream [`rfordatascience/tidytuesday`](https://github.com/rfordatascience/tidytuesday):

```bash
./scripts/submit_tidytuesday.py --submit
```

*Note: If the active GitHub token lacks permission on external repositories, open the [TidyTuesday Issue Template](https://github.com/rfordatascience/tidytuesday/issues/new?template=dataset_template.md) in the browser, title it `The Amazing Race (US Seasons 1–38)`, and paste the contents of `tidytuesday/submission_issue.md`.*
