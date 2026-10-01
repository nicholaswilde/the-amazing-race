---
name: tar-predict
description: >-
  Use this skill to predict race outcomes, finale contenders, and elimination risks for upcoming
  and in-progress seasons of The Amazing Race using empirical multi-factor modeling from historical data.
---

# Predict The Amazing Race Seasons

This skill executes the data-driven predictive modeling engine (`SeasonPredictor`) that evaluates active and upcoming Amazing Race teams against 38 seasons of empirical historical data (400+ teams, 78 winners).

## Commands

### 1. Predict an Upcoming or In-Progress Season

```bash
uv run tar-dataset predict --season 39
# Or using Task:
task predict -- --season 39
```

### 2. View Top Contenders with Diagnostic Breakdown

```bash
uv run tar-dataset predict --season 39 --top 5 --detail
```

Flags:
- `--season`, `-s`: Target season number (defaults to current season, e.g. `39`). Automatically scrapes latest Wikipedia cast, leg results, and twist status if not already cached.
- `--top`, `-t`: Number of top contender rankings to display in the terminal table (default: `10`).
- `--detail`, `-d`: Prints detailed factor diagnostics (key statistical strengths, demographic risk factors, racing average, and power item leverage).
- `--output`, `-o`: Exports the full probabilistic forecast and team profiles to a structured JSON file (e.g. `--output data/predictions/season_39_leg1.json`).

## Analytical Modeling Methodology

The predictive engine computes log-odds and calibrated Softmax probabilities across four empirically validated feature dimensions:

1. **Leg Momentum & Consistency (Weight: 45%)**:
   - **Leg 1 Prior**: In 38 US seasons, 57.9% of winners finished in the Top 3 of Leg 1 (26.3% won Leg 1; 21.1% placed 2nd; 10.5% placed 3rd; 15.8% placed 4th). Exactly 0 winners have finished 10th or worse on Leg 1.
   - **Racing Average (PPR)**: Historical winners maintain an average placement $\le 2.45$. Teams with running averages $\le 3.0$ receive significant momentum bonuses.

2. **Age & Generational Dynamics (Weight: 25%)**:
   - **Age Peak Likelihood**: Mean historical winner age is $29.88 \pm 5.5$ years. Evaluated via Gaussian likelihood centered on optimal physical/navigational readiness (ages 24–33).
   - **Generational Gap Penalty**: Teams with inter-partner age differences $\ge 20$ years (e.g. parent/child or grandparent/grandson) face steep penalties reflecting extreme late-race endurance demands. Parent/child teams account for only 2.6% of winners in TAR history; grandparent/grandchild teams have 0 wins.

3. **Relationship Archetype (Weight: 20%)**:
   - **Dating / Romantic Partners**: 28.9% historical win rate (11/38).
   - **Siblings (Brothers / Sisters)**: 21.1% historical win rate (8/38) — high interpersonal resilience and communication under stress.
   - **Married / Spouses**: 18.4% historical win rate (7/38).
   - **Friends / Roommates**: 7.9% historical win rate (3/38).
   - **Parent / Child**: 2.6% historical win rate (1/38).

4. **Tactical Power Items & Twists (Weight: 10%)**:
   - **Express Pass Leverage**: Holds intact Express Pass vs defensive burn (used early from behind) vs offensive burn (used to secure a 1st place finish). Teams retaining an Express Pass into middle legs possess substantial survival equity.

## Weekly Iteration Workflow

As new episodes air throughout the season:
1. Re-run `uv run tar-dataset predict --season <N>` — the Wikipedia scraper automatically parses newly aired leg placements and eliminations.
2. Monitor shifts in Win Probability (%) and Finale Probability (Top 3 %).
3. Export snapshots to track team trajectory over the season.
