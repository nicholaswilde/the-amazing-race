# The Amazing Race Season 39 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, team trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Amazing Race Season 39**.

Predictions are calculated using a 4-factor empirical modeling framework trained on 38 historical US seasons (78 winners, 400+ teams): **Leg Momentum (45%)**, **Age Peak Gaussian Likelihood (25%)**, **Relationship Archetype (20%)**, and **Tactical Assets / Express Pass (10%)**.

---

## 🏁 Latest Contender Rankings (After Leg 5)

**Model Context**: Active Teams: 8/13 | Historical Baseline: 38 US Seasons

| Rank | Team | Relationship | Avg Age | Avg Place | Express Pass | Win Prob | Finale Prob (Top 3) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Michelle & Matt** | Married Parents | 34 | 2.6 | Held | **23.6%** | **71.1%** |
| 2 | **Erin & Javi** | Married | 29 | 5.4 | Used | **18.6%** | **57.1%** |
| 3 | **Conner & Garrett** | Childhood Friends | 27 | 4.6 | Held | **16.9%** | **52.3%** |
| 4 | **Daisha & Dalton** | Dating | 28 | 6.6 | Used | **14.1%** | **44.5%** |
| 5 | **Ali & Joanna** | Pro Athletes/Moms | 43 | 5.4 | Used | **10.2%** | **33.6%** |
| 6 | **Ann-Marie & Riley** | Mother & Daughter | 42 | 4.6 | Used | **7.2%** | **25.2%** |
| 7 | **Anuar & Andrea** | Father & Daughter | 42 | 5.0 | Used | **6.3%** | **22.6%** |
| 8 | **Doug & Dylan** | Grandfather & Grandson | 46 | 7.8 | Used | **3.0%** | **13.4%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated win probabilities across broadcast legs:

| Team | Status | Leg 3 | Leg 4 | Leg 5 |
| :--- | :---: | :---: | :---: | :---: |
| **Michelle & Matt** | Active | 17.3% | 22.1% | 23.6% |
| **Erin & Javi** | Active | 15.8% | 19.9% | 18.6% |
| **Conner & Garrett** | Active | 13.4% | 15.7% | 16.9% |
| **Daisha & Dalton** | Active | 8.7% | 12.0% | 14.1% |
| **Ali & Joanna** | Active | 9.7% | 10.2% | 10.2% |
| **Ann-Marie & Riley** | Active | 6.5% | 6.9% | 7.2% |
| **Anuar & Andrea** | Active | 5.1% | 6.6% | 6.3% |
| **Doug & Dylan** | Active | 2.8% | 2.8% | 3.0% |
| **Zach & Nate** | Eliminated | 0.0% | 0.0% | 0.0% |
| **Katie & Charlotte** | Eliminated | 0.0% | 0.0% | 0.0% |
| **Jody & Jenn** | Eliminated | 6.5% | 0.0% | 0.0% |
| **Cody & Jaime** | Eliminated | 11.2% | 0.0% | 0.0% |
| **Dafina & Saran** | Eliminated | 2.9% | 3.8% | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Leg Outcomes

Comparison of actual leg finish placements across broadcast legs:

| Team | Leg 1 | Leg 2 | Leg 3 | Leg 4 | Leg 5 | Current Racing Avg | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Michelle & Matt** | 3 | 2 | 6 | 1 | 1 | 2.60 | Racing |
| **Erin & Javi** | 1 | 7 | 8 | 3 | 8 | 5.40 | Racing |
| **Conner & Garrett** | 2 | 9 | 4 | 5 | 3 | 4.60 | Racing |
| **Daisha & Dalton** | 12 | 6 | 9 | 4 | 2 | 6.60 | Racing |
| **Ali & Joanna** | 10 | 1 | 3 | 8 | 5 | 5.40 | Racing |
| **Ann-Marie & Riley** | 7 | 4 | 1 | 7 | 4 | 4.60 | Racing |
| **Anuar & Andrea** | 6 | 8 | 2 | 2 | 7 | 5.00 | Racing |
| **Doug & Dylan** | 4 | 10 | 10 | 9 | 6 | 7.80 | Racing |
| **Zach & Nate** | 13 | — | — | — | — | 13.00 | Eliminated |
| **Katie & Charlotte** | 5 | 12 | — | — | — | 8.50 | Eliminated |
| **Jody & Jenn** | 8 | 5 | 11 | — | — | 8.00 | Eliminated |
| **Cody & Jaime** | 11 | 3 | 5 | 10 | — | 7.25 | Eliminated |
| **Dafina & Saran** | 9 | 11 | 7 | 6 | 9 | 8.40 | Eliminated |

### Elimination & Contender Verification
- **Zach & Nate** (Brothers): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Katie & Charlotte** (Sisters): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Jody & Jenn** (Best Friends/Moms): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Cody & Jaime** (Siblings): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Dafina & Saran** (Sisters/Best Friends): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Leg 1 Prior**: 57.9% of all historical winners placed in the Top 3 of Leg 1; 0% finished 10th or worse.
- **Peak Winner Age**: Gaussian centered at 29.88 ± 5.5 years. Teams with inter-partner gaps ≥ 20 years receive generational disparity penalties.
- **Relationship Archetype**: Empirical win distributions: Dating (28.9%), Siblings (21.1%), Married (18.4%), Friends (7.9%), Parent/Child (2.6%).
- **Express Pass Leverage**: Intact passes provide significant survival and offensive positioning equity.
