# The Amazing Race Dataset: Data Gap & Completeness Report
**Overall Completeness**: 98.88%
**Total Data Cells**: 57,347 | **Missing Cells**: 643

## Column Gaps Summary

| Table | Column | Total Rows | Missing Count | Missing % | Severity | Affected Seasons | Root Cause / Diagnosis |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `episodes` | `air_date` | 356 | 149 | 41.9% | **HIGH** | S12 (11), S14 (12), S15 (11), S16 (12), S17 (12), S18 (11), S19 (12), S20 (11), S21 (11), S22 (11), S23 (11), S24 (12), S25 (12) | Broadcast dates not recorded or unparsed in early Wikipedia season tables. |
| `contestants` | `age` | 832 | 4 | 0.5% | **LOW** | S33 (4) | Season 33 COVID-19 pandemic replacement/withdrawn contestants (e.g. Anthony & Spencer, Sam & Connie). |
| `contestants` | `relationship` | 832 | 22 | 2.6% | **LOW** | S29 (22) | Season 29 contestants were complete strangers paired at the starting line; source table provides 'Team Name' instead of relationship. |
| `teams` | `relationship` | 404 | 24 | 5.9% | **MEDIUM** | S8 (10), S15 (1), S18 (1), S24 (1), S29 (11) | Season 29 teams were strangers; Season 8 (Family Edition) were 4-person family teams. |
| `teams` | `hometown` | 404 | 13 | 3.2% | **LOW** | S8 (10), S15 (1), S18 (1), S24 (1) | Season 8 (Family Edition) teams have multi-member families; individual hometowns recorded in contestants. |
| `legs` | `narrative` | 429 | 429 | 100.0% | **HIGH** | S1 (13), S2 (13), S3 (13), S4 (13), S5 (13), S6 (12), S7 (12), S8 (11), S9 (12), S10 (12), S11 (13), S12 (11), S13 (11), S14 (11), S15 (12), S16 (12), S17 (12), S18 (12), S19 (12), S20 (12), S21 (12), S22 (12), S23 (12), S24 (12), S25 (12), S26 (12), S27 (12), S28 (12), S29 (12), S30 (12), S31 (12), S32 (11), S33 (11), S34 (10), S35 (12), S36 (11) |  |
| `leg_results` | `placement` | 3,001 | 2 | 0.1% | **LOW** | S22 (1), S34 (1) | Off-mat eliminations, disqualifications, or unaired leg outcomes. |

## Actionable Recommendations

1. **Season 29 Contestants & Teams**: Fallback to `'Strangers (Paired at Starting Line)'` or extract team names as relationship proxies.
2. **Season 8 Family Edition Teams**: Assign `'Family Team (4 members)'` as default relationship description.
3. **Episode Air Dates**: Scrape and backfill missing broadcast air dates from Fandom or Wikipedia episode summary tables.
