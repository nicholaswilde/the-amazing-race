"""Predictive modeling engine for upcoming and in-progress Amazing Race seasons."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Empirical historical baselines across US Seasons 1-38
DEFAULT_HISTORICAL_BASELINES = {
    "winner_mean_age": 29.88,
    "winner_std_age": 5.5,
    "avg_winning_racing_average": 2.45,
    "relationship_weights": {
        "dating": 0.289,
        "siblings": 0.211,
        "married": 0.184,
        "friends": 0.079,
        "parent_child": 0.026,
        "strangers": 0.026,
        "other": 0.185,
    },
    "leg1_finish_win_rates": {
        1: 0.263,
        2: 0.211,
        3: 0.105,
        4: 0.158,
        5: 0.020,
        6: 0.053,
        7: 0.026,
        8: 0.132,
        9: 0.053,
        10: 0.005,
        11: 0.005,
        12: 0.001,
        13: 0.000,
    },
}


def categorize_relationship(rel_str: str) -> str:
    """Classify relationship string into canonical analytical categories."""
    rel = (rel_str or "").lower()
    if any(k in rel for k in ["brother", "sister", "sibling", "twin"]):
        return "siblings"
    if any(
        k in rel
        for k in [
            "dating",
            "engaged",
            "romantic",
            "couple",
            "boyfriend",
            "girlfriend",
            "partner",
        ]
    ):
        return "dating"
    if any(k in rel for k in ["married", "husband", "wife", "spouse"]):
        return "married"
    if any(k in rel for k in ["friend", "buddy", "roommate", "colleague", "coworker"]):
        return "friends"
    if any(
        k in rel
        for k in ["grand", "grandfather", "grandson", "grandmother", "granddaughter"]
    ):
        return "grandparent_grandchild"
    if any(k in rel for k in ["father", "mother", "parent", "son", "daughter"]):
        return "parent_child"
    if "stranger" in rel:
        return "strangers"
    return "other"


class SeasonPredictor:
    """Calculates data-driven win and finale probabilities for TAR teams."""

    def __init__(self, processed_dir: Path | str = "data/processed") -> None:
        self.processed_dir = Path(processed_dir)
        self.baselines = self._compute_or_load_baselines()

    def _compute_or_load_baselines(self) -> dict[str, Any]:
        """Compute empirical statistics from processed database or fallback to cached values."""
        baselines = dict(DEFAULT_HISTORICAL_BASELINES)
        teams_path = self.processed_dir / "teams.parquet"
        contestants_path = self.processed_dir / "contestants.parquet"
        leg_results_path = self.processed_dir / "leg_results.parquet"

        if teams_path.exists() and contestants_path.exists():
            try:
                teams_df = pd.read_parquet(teams_path)
                contestants_df = pd.read_parquet(contestants_path)

                # Filter winners in US franchise
                winner_contestants = contestants_df[
                    (contestants_df["version"] == "US")
                    & (
                        contestants_df["status"].str.contains(
                            "Winner", case=False, na=False
                        )
                    )
                    & (contestants_df["age"].notna())
                    & (contestants_df["age"] > 0)
                ]
                if not winner_contestants.empty:
                    baselines["winner_mean_age"] = float(
                        winner_contestants["age"].mean()
                    )
                    baselines["winner_std_age"] = float(winner_contestants["age"].std())

                if leg_results_path.exists():
                    leg_results_df = pd.read_parquet(leg_results_path)
                    winners_df = teams_df[
                        (teams_df["version"] == "US") & (teams_df["result"] == 1)
                    ]
                    merged = leg_results_df.merge(
                        winners_df[["version", "season", "team_name"]],
                        on=["version", "season", "team_name"],
                    )
                    leg1_winners = merged[merged["leg_number"] == 1][
                        "placement"
                    ].dropna()
                    if not leg1_winners.empty:
                        counts = leg1_winners.value_counts(normalize=True).to_dict()
                        for p, rate in counts.items():
                            baselines["leg1_finish_win_rates"][int(p)] = float(rate)
            except Exception as exc:
                logger.warning(
                    "Error computing live baselines from data: %s. Using defaults.", exc
                )

        return baselines

    def score_team(
        self,
        team_name: str,
        relationship: str,
        racers: list[dict[str, Any]],
        placements: list[dict[str, Any]],
        has_express_pass: bool = False,
        used_express_pass: bool = False,
        is_eliminated: bool = False,
    ) -> dict[str, Any]:
        """Score an individual team based on demographic, historical, and performance features."""
        if is_eliminated:
            return {
                "team_name": team_name,
                "relationship": relationship,
                "racers": racers,
                "avg_age": None,
                "legs_completed": len(placements),
                "avg_placement": None,
                "is_eliminated": True,
                "express_pass_status": "Eliminated",
                "win_probability": 0.0,
                "top3_probability": 0.0,
                "raw_score": -999.0,
                "strengths": [],
                "risks": ["Eliminated from competition"],
                "archetype": categorize_relationship(relationship),
            }

        # 1. Age Factor Analysis
        ages = [
            r.get("age")
            for r in racers
            if r.get("age") is not None and r.get("age") > 0
        ]
        avg_age = sum(ages) / len(ages) if ages else self.baselines["winner_mean_age"]
        age_gap = abs(ages[0] - ages[1]) if len(ages) >= 2 else 0

        # Gaussian likelihood distance from peak winner age (~29.9)
        mean_age = self.baselines["winner_mean_age"]
        std_age = self.baselines["winner_std_age"] or 5.5
        z_age = abs(avg_age - mean_age) / std_age
        age_score = math.exp(-0.5 * (z_age**2))

        # Inter-generational age gap penalty (e.g. >20 years difference)
        if age_gap >= 30:
            age_score *= 0.35  # Major fatigue/pace disparity penalty
        elif age_gap >= 20:
            age_score *= 0.65

        # 2. Relationship Archetype Factor
        archetype = categorize_relationship(relationship)
        rel_weight = self.baselines["relationship_weights"].get(archetype, 0.15)
        if archetype == "grandparent_grandchild":
            rel_weight = 0.01  # 0 wins in 38 seasons

        # 3. Leg Performance & Momentum Factor
        valid_placements = [
            p.get("placement") for p in placements if p.get("placement") is not None
        ]
        avg_placement = (
            sum(valid_placements) / len(valid_placements) if valid_placements else 6.0
        )

        perf_score = 1.0
        strengths: list[str] = []
        risks: list[str] = []

        if valid_placements:
            leg1_p = valid_placements[0]

            # Invert placement: lower placement is better (1st -> 1.0, 12th -> 0.08)
            perf_score = math.exp(-0.28 * (avg_placement - 1.0))

            # Empirical Leg 1 prior
            leg1_win_rate = self.baselines["leg1_finish_win_rates"].get(leg1_p, 0.01)
            perf_score *= 1.0 + 2.0 * leg1_win_rate

            if leg1_p <= 3:
                strengths.append(
                    f"Top-3 Leg 1 finish ({leg1_p}{'st' if leg1_p == 1 else 'nd' if leg1_p == 2 else 'rd'}) matches 58% of historical winners"
                )
            elif leg1_p >= 10:
                risks.append(
                    "Finished 10th or worse in Leg 1 (historically 0% win rate across all 38 seasons)"
                )

            if avg_placement <= 3.0:
                strengths.append(f"Elite racing average ({avg_placement:.2f})")
        else:
            perf_score = 0.8  # Pre-season unobserved baseline

        # 4. Tactical Assets (Express Pass)
        tactical_score = 1.0
        express_status = "None"
        if has_express_pass:
            express_status = "Active / Intact"
            tactical_score = 1.25
            strengths.append("Holds intact Express Pass for upcoming legs")
        elif used_express_pass:
            express_status = "Used"
            if valid_placements and valid_placements[0] == 1:
                tactical_score = 1.05
                strengths.append("Offensive Express Pass burn yielded Leg 1 victory")
                risks.append(
                    "Safety net depleted; no Express Pass remaining for legs 2-6"
                )
            else:
                tactical_score = 0.90
                risks.append("Defensive Express Pass burn early to avoid elimination")

        # Contextual strengths and risks
        if 24 <= avg_age <= 33:
            strengths.append(
                f"Optimal physical age bracket ({avg_age:.0f} yrs, historical mean ~30)"
            )
        elif avg_age > 45:
            risks.append(
                f"Elevated age bracket ({avg_age:.0f} yrs) in high-endurance race"
            )
        elif avg_age < 22:
            risks.append(
                f"Younger racer demographic ({avg_age:.0f} yrs) with lower navigation experience"
            )

        if archetype in ("siblings", "dating", "married"):
            strengths.append(f"High-cohesion {archetype.replace('_', ' ')} archetype")
        elif archetype == "parent_child":
            risks.append(
                "Parent/child archetype historically produces only 2.6% of winners"
            )

        # 5. Composite Log-odds Score
        # Weighting: Performance (0.45), Age (0.25), Relationship (0.20), Tactical (0.10)
        log_score = (
            0.45 * math.log(max(perf_score, 0.001))
            + 0.25 * math.log(max(age_score, 0.001))
            + 0.20 * math.log(max(rel_weight, 0.001))
            + 0.10 * math.log(max(tactical_score, 0.001))
        )

        return {
            "team_name": team_name,
            "relationship": relationship,
            "racers": racers,
            "avg_age": round(avg_age, 1),
            "age_gap": age_gap,
            "legs_completed": len(valid_placements),
            "avg_placement": round(avg_placement, 2) if valid_placements else None,
            "is_eliminated": False,
            "express_pass_status": express_status,
            "raw_score": log_score,
            "strengths": strengths,
            "risks": risks,
            "archetype": archetype,
        }

    def predict_season(
        self,
        season: int = 39,
        raw_dir: Path | str = "data/raw/wikipedia",
        scrape_if_missing: bool = True,
    ) -> dict[str, Any]:
        """Generate full season prediction rankings for the requested season."""
        raw_path = Path(raw_dir) / f"season_{season}.json"
        season_data: dict[str, Any] = {}

        if raw_path.exists():
            try:
                with open(raw_path, encoding="utf-8") as f:
                    season_data = json.load(f)
            except Exception as exc:
                logger.warning("Could not read cached season %d: %s", season, exc)

        if not season_data and scrape_if_missing:
            from tar_dataset.scrapers.wikipedia import WikipediaScraper

            scraper = WikipediaScraper(raw_dir=raw_dir)
            season_data = scraper.scrape_season(season) or {}

        if not season_data:
            raise ValueError(
                f"No data available for Season {season}. Scrape failed or page unavailable."
            )

        contestants = season_data.get("contestants", [])
        results = season_data.get("results", [])

        # Match contestants to teams
        # In TAR Wikipedia tables, contestants are grouped in pairs sharing relationship & status
        teams_list: list[dict[str, Any]] = []

        # Map results by team name or match
        results_by_name = {
            r.get("team_name", ""): r for r in results if r.get("team_name")
        }

        # Group contestants into pairs of 2
        for i in range(0, len(contestants), 2):
            if i + 1 < len(contestants):
                pair = [contestants[i], contestants[i + 1]]
                rel = (
                    pair[0].get("relationship")
                    or pair[1].get("relationship")
                    or "Teammates"
                )
                status = pair[0].get("status", "")

                # Derive team name
                name1 = pair[0].get("name", "").split()[0]
                name2 = pair[1].get("name", "").split()[0]
                derived_name = f"{name1} & {name2}"

                # Find matching result row
                matching_res = None
                for res_name, r_obj in results_by_name.items():
                    if (
                        name1.lower() in res_name.lower()
                        and name2.lower() in res_name.lower()
                    ):
                        matching_res = r_obj
                        derived_name = res_name
                        break

                placements: list[dict[str, Any]] = []
                used_ep = False
                has_ep = False
                is_eliminated = "Eliminated" in status

                if matching_res:
                    for p_info in matching_res.get("placements", []):
                        pl = p_info.get("placement")
                        raw_cell = str(p_info.get("raw_cell", ""))
                        if "ɛ" in raw_cell or "express" in raw_cell.lower():
                            used_ep = True
                        if "†" in raw_cell or "eliminated" in raw_cell.lower():
                            is_eliminated = True
                        if pl is not None:
                            placements.append(p_info)

                # Special season 39 rule: every team received an Express Pass at start
                if season == 39 and not used_ep and not is_eliminated:
                    has_ep = True

                teams_list.append(
                    {
                        "team_name": derived_name,
                        "relationship": rel,
                        "racers": pair,
                        "placements": placements,
                        "has_express_pass": has_ep,
                        "used_express_pass": used_ep,
                        "is_eliminated": is_eliminated,
                    }
                )

        # Score all teams
        scored_teams: list[dict[str, Any]] = []
        for t in teams_list:
            score_data = self.score_team(
                team_name=t["team_name"],
                relationship=t["relationship"],
                racers=t["racers"],
                placements=t["placements"],
                has_express_pass=t["has_express_pass"],
                used_express_pass=t["used_express_pass"],
                is_eliminated=t["is_eliminated"],
            )
            scored_teams.append(score_data)

        # Softmax normalization across active teams for Win Probability
        active_teams = [t for t in scored_teams if not t["is_eliminated"]]
        eliminated_teams = [t for t in scored_teams if t["is_eliminated"]]

        if active_teams:
            max_raw = max(t["raw_score"] for t in active_teams)
            exp_scores = [math.exp(t["raw_score"] - max_raw) for t in active_teams]
            total_exp = sum(exp_scores)

            for t, exp_val in zip(active_teams, exp_scores):
                win_prob = exp_val / total_exp
                t["win_probability"] = round(win_prob * 100.0, 1)

            # Top 3 / Finale Probability (approximate via logistic scaling)
            # Active teams with higher win probability naturally dominate top 3
            for t in active_teams:
                # Scaled top 3 probability bounded between [win_prob, 95.0]
                t3_prob = min(round(t["win_probability"] * 2.8 + 5.0, 1), 95.0)
                t["top3_probability"] = t3_prob

        # Sort all teams by win probability descending
        ranked_teams = (
            sorted(active_teams, key=lambda x: x["win_probability"], reverse=True)
            + eliminated_teams
        )

        # Determine current leg
        completed_legs = max((len(t["placements"]) for t in teams_list), default=0)

        return {
            "season": season,
            "current_leg": completed_legs,
            "total_teams": len(teams_list),
            "active_teams_count": len(active_teams),
            "eliminated_teams_count": len(eliminated_teams),
            "rankings": ranked_teams,
            "historical_baselines": self.baselines,
        }
