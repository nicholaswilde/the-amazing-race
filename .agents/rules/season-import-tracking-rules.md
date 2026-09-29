# Season Import Progress Tracking

## Rule
Whenever you import or scrape The Amazing Race seasons (via `task scrape:wiki`, `task scrape:fandom`, or CLI commands), **always update GitHub Issue #4** to record progress.

## Guidelines
1. After successfully scraping a season or batch of seasons, post a status comment on Issue #4 using `rtk gh` piped to `cat`:
   ```bash
   rtk gh issue comment 4 --body "Imported Season <season_number> (<version>): <summary of records>" | cat
   ```
2. When applicable, check off the corresponding season item in Issue #4's task list.
