# The Amazing Race Dataset: Data Gap & Completeness Report
**Overall Completeness**: 100.0%
**Total Data Cells**: 101,633 | **Missing Cells**: 1

## Column Gaps Summary

| Table | Column | Total Rows | Missing Count | Missing % | Severity | Affected Seasons | Root Cause / Diagnosis |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `episodes` | `viewers_millions` | 644 | 1 | 0.2% | **LOW** | S4 (1) | Non-competition recap special (CAN S4E08 'Top 20 Moments') aired opposite Rio 2016 Olympics; Numeris rank >30 (unreported). |

## Data Gap Resolution & Backfill Status

1. **Season 29 Contestants & Teams**: Set relationship to `'Strangers (Paired at Starting Line)'` (100% resolved).
2. **Season 8 Family Edition Teams**: Assigned `'Family Team (4 members)'` and populated family hometown origins (100% resolved).
3. **Returnee Teams (S15, S18, S24)**: Backfilled relationships and hometowns for Flight Time & Big Easy (100% resolved).
4. **Season 33 Contestants**: Backfilled ages, relationships, and hometowns for returned and withdrawn racers (100% resolved).
5. **Episode Air Dates**: Scraped and backfilled 149 broadcast air dates across Seasons 12 and 14–25 (100% resolved).
6. **Leg Results Placements**: Resolved off-mat withdrawal/elimination placements for S22L5 and S34L5 (100% resolved).
7. **Leg Narratives**: Scraped and populated rich route narratives across all legs (100% resolved).
8. **Season 38 Viewership**: Backfilled episodes 10–12 broadcast ratings from The TV Ratings Guide & USTVDB (100% resolved).
9. **International Viewership & Demographics**: Resolved Australian (S1–S8) episode numbers, air dates, and million-scaled viewership; mapped NZ regions and Australian celebrity hometowns/states; resolved returned-to-competition team relationships and hometowns across CAN S8, AUS S5, and US S33 (100% resolved).
10. **Canadian Season 4 Recap Special**: Documented lone missing cell as CAN S4E08 ('Top 20 Moments' clip show, aired August 16, 2016). Retained as empirical `NaN` per Option A (Numeris rank >30 cutoff; unrated broadcast).
