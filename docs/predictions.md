# The Amazing Race Season 39 Empirical Predictions & Accuracy Ledger

This document tracks weekly probabilistic forecasts, team trajectory shifts, and empirical model accuracy against actual broadcast outcomes for **The Amazing Race Season 39**.

Predictions are calculated using a 4-factor empirical modeling framework trained on 38 historical US seasons (78 winners, 400+ teams): **Leg Momentum (45%)**, **Age Peak Gaussian Likelihood (25%)**, **Relationship Archetype (20%)**, and **Tactical Assets / Express Pass (10%)**.

---

## 🏁 Latest Contender Rankings (After Leg 3)

**Model Context**: Active Teams: 11/13 | Historical Baseline: 38 US Seasons

| Rank | Team | Relationship | Avg Age | Avg Place | Express Pass | Win Prob | Finale Prob (Top 3) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Michelle & Matt** | Married Parents | 34 | 3.7 | Held | **17.3%** | **53.4%** |
| 2 | **Erin & Javi** | Married | 29 | 5.3 | Used | **15.8%** | **49.2%** |
| 3 | **Conner & Garrett** | Childhood Friends | 27 | 5.0 | Held | **13.4%** | **42.5%** |
| 4 | **Cody & Jaime** | Siblings | 34 | 6.3 | Used | **11.2%** | **36.4%** |
| 5 | **Ali & Joanna** | Pro Athletes/Moms | 43 | 4.7 | Held | **9.7%** | **32.2%** |
| 6 | **Daisha & Dalton** | Dating | 28 | 9.0 | Used | **8.7%** | **29.4%** |
| 7 | **Ann-Marie & Riley** | Mother & Daughter | 42 | 4.0 | Used | **6.5%** | **23.2%** |
| 8 | **Jody & Jenn** | Best Friends/Moms | 44 | 6.5 | Used | **6.5%** | **23.2%** |
| 9 | **Anuar & Andrea** | Father & Daughter | 42 | 5.3 | Used | **5.1%** | **19.3%** |
| 10 | **Dafina & Saran** | Sisters/Best Friends | 52 | 9.0 | Used | **2.9%** | **13.1%** |

---

## 📈 Weekly Win Probability Trajectory

Progression of calibrated win probabilities across broadcast legs:

| Team | Status | Leg 3 |
| :--- | :---: | :---: |
| **Michelle & Matt** | Active | 17.3% |
| **Erin & Javi** | Active | 15.8% |
| **Conner & Garrett** | Active | 13.4% |
| **Cody & Jaime** | Active | 11.2% |
| **Ali & Joanna** | Active | 9.7% |
| **Daisha & Dalton** | Active | 8.7% |
| **Ann-Marie & Riley** | Active | 6.5% |
| **Jody & Jenn** | Active | 6.5% |
| **Anuar & Andrea** | Active | 5.1% |
| **Dafina & Saran** | Active | 2.9% |
| **Doug & Dylan** | Active | 2.8% |
| **Zach & Nate** | Eliminated | 0.0% |
| **Katie & Charlotte** | Eliminated | 0.0% |

---

## 🎯 Prediction Accuracy vs Actual Leg Outcomes

Comparison of actual leg finish placements across broadcast legs:

| Team | Leg 1 | Leg 2 | Leg 3 | Current Racing Avg | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Michelle & Matt** | 3 | 2 | 6 | 3.67 | Racing |
| **Erin & Javi** | 1 | 7 | 8 | 5.33 | Racing |
| **Conner & Garrett** | 2 | 9 | 4 | 5.00 | Racing |
| **Cody & Jaime** | 11 | 3 | 5 | 6.33 | Racing |
| **Ali & Joanna** | 10 | 1 | 3 | 4.67 | Racing |
| **Daisha & Dalton** | 12 | 6 | 9 | 9.00 | Racing |
| **Ann-Marie & Riley** | 7 | 4 | 1 | 4.00 | Racing |
| **Jody & Jenn** | 8 | 5 | — | 6.50 | Racing |
| **Anuar & Andrea** | 6 | 8 | 2 | 5.33 | Racing |
| **Dafina & Saran** | 9 | 11 | 7 | 9.00 | Racing |
| **Doug & Dylan** | 4 | 10 | — | 7.00 | Racing |
| **Zach & Nate** | 13 | — | — | 13.00 | Eliminated |
| **Katie & Charlotte** | 5 | 12 | — | 8.50 | Eliminated |

### Elimination & Contender Verification
- **Zach & Nate** (Brothers): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.
- **Katie & Charlotte** (Sisters): Eliminated. Post-elimination win probability correctly reduced to **0.0%**.

---

## 🔬 Model Diagnostics & Scoring Methodology
- **Leg 1 Prior**: 57.9% of all historical winners placed in the Top 3 of Leg 1; 0% finished 10th or worse.
- **Peak Winner Age**: Gaussian centered at 29.88 ± 5.5 years. Teams with inter-partner gaps ≥ 20 years receive generational disparity penalties.
- **Relationship Archetype**: Empirical win distributions: Dating (28.9%), Siblings (21.1%), Married (18.4%), Friends (7.9%), Parent/Child (2.6%).
- **Express Pass Leverage**: Intact passes provide significant survival and offensive positioning equity.
