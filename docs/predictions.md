# The Amazing Race Season 39 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, team trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Amazing Race Season 39**.

Predictions are calculated using a 4-factor empirical modeling framework trained on 38 historical US seasons (78 winners, 400+ teams): **Leg Momentum (45%)**, **Age Peak Gaussian Likelihood (25%)**, **Relationship Archetype (20%)**, and **Tactical Assets / Express Pass (10%)**.

---

## 🏁 Latest Contender Rankings (After Leg 7)

**Model Context**: Active Teams: 7/13 | Historical Baseline: 38 US Seasons

| Rank | Team | Relationship | Avg Age | Avg Place | Express Pass | Win Prob | Finale Prob (Top 3) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Michelle & Matt** | Married Parents | 34 | 2.4 | Used | **23.4%** | **70.5%** |
| 2 | **Erin & Javi** | Married | 29 | 5.4 | Used | **19.0%** | **58.2%** |
| 3 | **Conner & Garrett** | Childhood Friends | 27 | 4.3 | Used | **17.3%** | **53.4%** |
| 4 | **Daisha & Dalton** | Dating | 28 | 6.0 | Used | **15.3%** | **47.8%** |
| 5 | **Ali & Joanna** | Pro Athletes/Moms | 43 | 5.0 | Used | **11.0%** | **35.8%** |
| 6 | **Ann-Marie & Riley** | Mother & Daughter | 42 | 4.9 | Used | **7.1%** | **24.9%** |
| 7 | **Anuar & Andrea** | Father & Daughter | 42 | 4.4 | Used | **7.0%** | **24.6%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated win probabilities across broadcast legs:

| Team | Status | Leg 3 | Leg 4 | Leg 5 | Leg 6 | Leg 7 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Michelle & Matt** | Active | 17.3% | 22.1% | 23.6% | 23.4% | 23.4% |
| **Erin & Javi** | Active | 15.8% | 19.9% | 18.6% | 18.6% | 19.0% |
| **Conner & Garrett** | Active | 13.4% | 15.7% | 16.9% | 16.7% | 17.3% |
| **Daisha & Dalton** | Active | 8.7% | 12.0% | 14.1% | 15.4% | 15.3% |
| **Ali & Joanna** | Active | 9.7% | 10.2% | 10.2% | 9.8% | 11.0% |
| **Ann-Marie & Riley** | Active | 6.5% | 6.9% | 7.2% | 6.9% | 7.1% |
| **Anuar & Andrea** | Active | 5.1% | 6.6% | 6.3% | 6.4% | 7.0% |
| **Zach & Nate** | Eliminated | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Katie & Charlotte** | Eliminated | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Jody & Jenn** | Eliminated | 6.5% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Cody & Jaime** | Eliminated | 11.2% | 0.0% | 0.0% | 0.0% | 0.0% |
| **Dafina & Saran** | Eliminated | 2.9% | 3.8% | 0.0% | 0.0% | 0.0% |
| **Doug & Dylan** | Eliminated | 2.8% | 2.8% | 3.0% | 2.9% | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Leg Outcomes

Comparison of actual leg finish placements across broadcast legs:

| Team | Leg 1 | Leg 2 | Leg 3 | Leg 4 | Leg 5 | Leg 6 | Leg 7 | Current Racing Avg | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Michelle & Matt** | 3 | 2 | 6 | 1 | 1 | 1 | 3 | 2.43 | Racing |
| **Erin & Javi** | 1 | 7 | 8 | 3 | 8 | 5 | 6 | 5.43 | Racing |
| **Conner & Garrett** | 2 | 9 | 4 | 5 | 3 | 3 | 4 | 4.29 | Racing |
| **Daisha & Dalton** | 12 | 6 | 9 | 4 | 2 | 2 | 7 | 6.00 | Racing |
| **Ali & Joanna** | 10 | 1 | 3 | 8 | 5 | 7 | 1 | 5.00 | Racing |
| **Ann-Marie & Riley** | 7 | 4 | 1 | 7 | 4 | 6 | 5 | 4.86 | Racing |
| **Anuar & Andrea** | 6 | 8 | 2 | 2 | 7 | 4 | 2 | 4.43 | Racing |
| **Zach & Nate** | 13 | — | — | — | — | — | — | 13.00 | Eliminated |
| **Katie & Charlotte** | 5 | 12 | — | — | — | — | — | 8.50 | Eliminated |
| **Jody & Jenn** | 8 | 5 | 11 | — | — | — | — | 8.00 | Eliminated |
| **Cody & Jaime** | 11 | 3 | 5 | 10 | — | — | — | 7.25 | Eliminated |
| **Dafina & Saran** | 9 | 11 | 7 | 6 | 9 | — | — | 8.40 | Eliminated |
| **Doug & Dylan** | 4 | 10 | 10 | 9 | 6 | 8 | 8 | 7.86 | Eliminated |

### Elimination & Contender Verification
- **Zach & Nate** (Brothers): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Katie & Charlotte** (Sisters): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Jody & Jenn** (Best Friends/Moms): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Cody & Jaime** (Siblings): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Dafina & Saran** (Sisters/Best Friends): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Doug & Dylan** (Grandfather & Grandson): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Leg 1 Prior**: 57.9% of all historical winners placed in the Top 3 of Leg 1; 0% finished 10th or worse.
- **Peak Winner Age**: Gaussian centered at 29.88 ± 5.5 years. Teams with inter-partner gaps ≥ 20 years receive generational disparity penalties.
- **Relationship Archetype**: Empirical win distributions: Dating (28.9%), Siblings (21.1%), Married (18.4%), Friends (7.9%), Parent/Child (2.6%).
- **Express Pass Leverage**: Intact passes provide significant survival and offensive positioning equity.
