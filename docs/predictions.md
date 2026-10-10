# The Amazing Race Season 37 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, team trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Amazing Race Season 37**.

Predictions are calculated using a 4-factor empirical modeling framework trained on 38 historical US seasons (78 winners, 400+ teams): **Leg Momentum (45%)**, **Age Peak Gaussian Likelihood (25%)**, **Relationship Archetype (20%)**, and **Tactical Assets / Express Pass (10%)**.

---

## 🏁 Latest Contender Rankings (After Leg 12)

**Model Context**: Active Teams: 3/14 | Historical Baseline: 38 US Seasons

| Rank | Team | Relationship | Avg Age | Avg Place | Express Pass | Win Prob | Finale Prob (Top 3) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Carson & Jack** | Best Friends & Gamers | 28 | 2.4 | - | **38.5%** | **95.0%** |
| 2 | **Jonathan & Ana** | Married Parents | 38 | 3.0 | - | **34.9%** | **95.0%** |
| 3 | **Han & Holden** | Siblings | 24 | 5.0 | - | **26.6%** | **79.5%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated win probabilities across broadcast legs:

| Team | Status | Leg 12 |
| :--- | :---: | :---: |
| **Carson & Jack** | Active | 38.5% |
| **Jonathan & Ana** | Active | 34.9% |
| **Han & Holden** | Active | 26.6% |
| **Jackye & Lauren** | Eliminated | 0.0% |
| **Mark & Larry** | Eliminated | 0.0% |
| **Ernest & Bridget** | Eliminated | 0.0% |
| **Courtney & Jasmin** | Eliminated | 0.0% |
| **Bernie & Carrigain** | Eliminated | 0.0% |
| **Scott & Lori** | Eliminated | 0.0% |
| **Pops & Jeff** | Eliminated | 0.0% |
| **Nick & Mike** | Eliminated | 0.0% |
| **Melinda & Erika** | Eliminated | 0.0% |
| **Brett & Mark** | Eliminated | 0.0% |
| **Alyssa & Josiah** | Eliminated | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Leg Outcomes

Comparison of actual leg finish placements across broadcast legs:

| Team | Leg 1 | Leg 2 | Leg 3 | Leg 4 | Leg 5 | Leg 6 | Leg 7 | Leg 8 | Leg 9 | Leg 10 | Leg 11 | Leg 12 | Current Racing Avg | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Carson & Jack** | 1 | 4 | 2 | 2 | 2 | 1 | 6 | 4 | 4 | 1 | 1 | 1 | 2.42 | Racing |
| **Jonathan & Ana** | 2 | 1 | 3 | 1 | 8 | 5 | 3 | 3 | 1 | 3 | 3 | 3 | 3.00 | Racing |
| **Han & Holden** | 5 | 11 | 9 | 6 | 5 | 2 | 4 | 5 | 5 | 4 | 2 | 2 | 5.00 | Racing |
| **Jackye & Lauren** | 7 | — | — | — | — | — | — | — | — | — | — | — | 7.00 | Eliminated |
| **Mark & Larry** | 7 | — | — | — | — | — | — | — | — | — | — | — | 7.00 | Eliminated |
| **Ernest & Bridget** | 3 | 12 | — | — | — | — | — | — | — | — | — | — | 7.50 | Eliminated |
| **Courtney & Jasmin** | 6 | 6 | 11 | — | — | — | — | — | — | — | — | — | 7.67 | Eliminated |
| **Bernie & Carrigain** | 4 | 8 | 10 | 10 | — | — | — | — | — | — | — | — | 8.00 | Eliminated |
| **Scott & Lori** | 3 | 2 | 1 | 3 | 9 | — | — | — | — | — | — | — | 3.60 | Eliminated |
| **Pops & Jeff** | 4 | 7 | 6 | 9 | 4 | 8 | — | — | — | — | — | — | 6.33 | Eliminated |
| **Nick & Mike** | 5 | 10 | 8 | 8 | 7 | 7 | 7 | — | — | — | — | — | 7.43 | Eliminated |
| **Melinda & Erika** | 6 | 5 | 4 | 4 | 6 | 6 | 5 | 6 | — | — | — | — | 5.25 | Eliminated |
| **Brett & Mark** | 2 | 9 | 5 | 7 | 1 | 4 | 2 | 1 | 2 | 5 | — | — | 3.80 | Eliminated |
| **Alyssa & Josiah** | 1 | 3 | 7 | 5 | 3 | 3 | 1 | 2 | 3 | 2 | 4 | — | 3.09 | Eliminated |

### Elimination & Contender Verification
- **Jackye & Lauren** (Sisters): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Mark & Larry** (Retired Firefighters): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Ernest & Bridget** (Father & Daughter): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Courtney & Jasmin** (Dating Nurses): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Bernie & Carrigain** (Friends): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Scott & Lori** (Married Parents of Eight): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Pops & Jeff** (Father & Son Lumberjacks): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Nick & Mike** (Brothers): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Melinda & Erika** (Mother & Daughter): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Brett & Mark** (Married Vegas Performers): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Alyssa & Josiah** (Married Nurses): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Leg 1 Prior**: 57.9% of all historical winners placed in the Top 3 of Leg 1; 0% finished 10th or worse.
- **Peak Winner Age**: Gaussian centered at 29.88 ± 5.5 years. Teams with inter-partner gaps ≥ 20 years receive generational disparity penalties.
- **Relationship Archetype**: Empirical win distributions: Dating (28.9%), Siblings (21.1%), Married (18.4%), Friends (7.9%), Parent/Child (2.6%).
- **Express Pass Leverage**: Intact passes provide significant survival and offensive positioning equity.
