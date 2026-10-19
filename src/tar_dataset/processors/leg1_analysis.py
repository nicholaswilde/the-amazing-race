"""First Leg Winner outcome, trajectory, and Episode 1 curse analysis.

Evaluates the 'First Leg Winner Curse' ('Episode 1 Jinx') hypothesis across
The Amazing Race by computing championship/podium conversion rates, mid-race
and early flame-out collapse tiers, U-Turn targeting hazard on Leg 1 winners,
OLS regression and Pearson correlation between Leg 1 placement and final
season result, and multi-stage alluvial transition matrices.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LEG1_TIERS = [
    "1st (Leg 1 Winner)",
    "2nd-3rd (Leg 1 Podium)",
    "4th-7th (Mid-Pack)",
    "8th+ (Back-Pack)",
]

FINAL_TIERS = [
    "1st (Champion)",
    "2nd-3rd (Finalist)",
    "4th-7th (Mid-Race Exit)",
    "8th+ (Early Exit)",
]


def classify_leg1_tier(placement: int) -> str:
    """Classify a team's Leg 1 finish position into a 4-tier trajectory bucket."""
    if placement == 1:
        return "1st (Leg 1 Winner)"
    if placement <= 3:
        return "2nd-3rd (Leg 1 Podium)"
    if placement <= 7:
        return "4th-7th (Mid-Pack)"
    return "8th+ (Back-Pack)"


def classify_final_tier(result: int) -> str:
    """Classify a team's final season placement into a 4-tier outcome bucket."""
    if result == 1:
        return "1st (Champion)"
    if result <= 3:
        return "2nd-3rd (Finalist)"
    if result <= 7:
        return "4th-7th (Mid-Race Exit)"
    return "8th+ (Early Exit)"


@dataclass
class Leg1WinnerInstance:
    """Represents a single Leg 1 winning team and its full season trajectory."""

    version: str
    season: int
    team_name: str
    leg1_placement: int
    final_result: int
    final_tier: str
    legs_completed: int
    elimination_leg: int
    season_max_legs: int
    racing_average: float
    is_winner: bool
    is_podium: bool
    is_final_four: bool
    is_mid_collapse: bool
    is_early_flameout: bool
    was_uturned: bool
    eliminated_by_uturn: bool


@dataclass
class Leg1Metrics:
    """Aggregated empirical metrics for Leg 1 winners and Leg 1-to-Final correlation."""

    version: str
    total_completed_teams: int
    pearson_r: float
    ols_slope: float
    ols_intercept: float
    total_leg1_winners: int
    champion_count: int
    champion_rate: float
    podium_count: int
    podium_rate: float
    final_four_count: int
    final_four_rate: float
    collapse_count: int
    collapse_rate: float
    mid_collapse_count: int
    mid_collapse_rate: float
    early_flameout_count: int
    early_flameout_rate: float
    mean_final_result: float
    median_final_result: float
    final_result_counts: dict[int, int]
    uturned_winner_count: int
    uturned_winner_elim_count: int
    uturned_winner_elim_rate: float
    transition_matrix: dict[str, dict[str, int]]
    instances: list[Leg1WinnerInstance]


class Leg1Analyzer:
    """Empirical model and analyzer for Leg 1 winner outcomes and trajectory flows."""

    def __init__(self, data_dir: Path | str = "data/processed") -> None:
        """Initialize analyzer with directory of processed dataset tables."""
        self.data_dir = Path(data_dir)
        self._leg_results_df: pd.DataFrame | None = None
        self._teams_df: pd.DataFrame | None = None

    def _load_table(self, name: str) -> pd.DataFrame:
        """Load Parquet or CSV table."""
        parquet = self.data_dir / f"{name}.parquet"
        if parquet.exists():
            return pd.read_parquet(parquet)
        csv = self.data_dir / f"{name}.csv"
        if csv.exists():
            return pd.read_csv(csv)
        raise FileNotFoundError(f"Table '{name}' not found in {self.data_dir}")

    @property
    def leg_results_df(self) -> pd.DataFrame:
        """Cached leg_results table."""
        if self._leg_results_df is None:
            self._leg_results_df = self._load_table("leg_results")
        return self._leg_results_df

    @property
    def teams_df(self) -> pd.DataFrame:
        """Cached teams table."""
        if self._teams_df is None:
            self._teams_df = self._load_table("teams")
        return self._teams_df

    def _merged_completed_leg1(self, version: str = "US") -> pd.DataFrame:
        """Return merged Leg 1 and final team results for completed seasons."""
        lr = self.leg_results_df
        teams = self.teams_df
        if lr.empty or teams.empty:
            return pd.DataFrame()

        lr_v = lr if version.upper() == "ALL" else lr[lr["version"] == version.upper()]
        t_v = (
            teams
            if version.upper() == "ALL"
            else teams[teams["version"] == version.upper()]
        )
        if lr_v.empty or t_v.empty:
            return pd.DataFrame()

        leg1 = lr_v[lr_v["leg_number"] == 1].copy()
        team_cols = [
            c
            for c in [
                "version",
                "season",
                "team_name",
                "result",
                "legs_completed",
                "racing_average",
            ]
            if c in t_v.columns
        ]
        merged = leg1.merge(
            t_v[team_cols], on=["version", "season", "team_name"], how="left"
        )
        merged = merged[merged["result"].notna() & merged["placement"].notna()].copy()
        merged["result_int"] = pd.to_numeric(merged["result"], errors="coerce")
        merged["placement_int"] = pd.to_numeric(merged["placement"], errors="coerce")
        merged = merged[
            merged["result_int"].notna() & merged["placement_int"].notna()
        ].copy()
        merged["result_int"] = merged["result_int"].astype(int)
        merged["placement_int"] = merged["placement_int"].astype(int)
        return merged

    def extract_winner_instances(self, version: str = "US") -> list[Leg1WinnerInstance]:
        """Extract all Leg 1 winning teams across completed seasons."""
        merged = self._merged_completed_leg1(version=version)
        if merged.empty:
            return []

        lr = self.leg_results_df
        w1 = (
            merged[merged["placement_int"] == 1]
            .sort_values(["version", "season"])
            .copy()
        )
        instances: list[Leg1WinnerInstance] = []

        for _, r in w1.iterrows():
            ver = str(r["version"])
            s = int(r["season"])
            tm = str(r["team_name"])
            res = int(r["result_int"])
            l1_pl = int(r["placement_int"])

            season_legs = lr[(lr["version"] == ver) & (lr["season"] == s)]
            max_leg_s = (
                int(season_legs["leg_number"].max()) if not season_legs.empty else 0
            )

            team_legs = season_legs[season_legs["team_name"] == tm].sort_values(
                "leg_number"
            )
            last_leg = int(team_legs["leg_number"].max()) if not team_legs.empty else 1
            legs_comp = (
                int(r["legs_completed"])
                if pd.notna(r.get("legs_completed"))
                else len(team_legs)
            )
            avg_pl = (
                float(r["racing_average"]) if pd.notna(r.get("racing_average")) else 0.0
            )

            raw_cells = (
                team_legs["raw_cell"].astype(str).tolist()
                if "raw_cell" in team_legs.columns
                else []
            )
            was_ut = any(("⊂" in c) or ("⋑" in c) for c in raw_cells)
            last_cell = raw_cells[-1] if raw_cells else ""
            elim_by_ut = (("⊂" in last_cell) or ("⋑" in last_cell)) and (res > 3)

            instances.append(
                Leg1WinnerInstance(
                    version=ver,
                    season=s,
                    team_name=tm,
                    leg1_placement=l1_pl,
                    final_result=res,
                    final_tier=classify_final_tier(res),
                    legs_completed=legs_comp,
                    elimination_leg=last_leg,
                    season_max_legs=max_leg_s,
                    racing_average=avg_pl,
                    is_winner=res == 1,
                    is_podium=res <= 3,
                    is_final_four=res <= 4,
                    is_mid_collapse=4 <= res <= 7,
                    is_early_flameout=res >= 8,
                    was_uturned=was_ut,
                    eliminated_by_uturn=elim_by_ut,
                )
            )

        return instances

    def analyze(self, version: str = "US") -> Leg1Metrics:
        """Compute correlation, regression, transition matrix, and Leg 1 winner metrics."""
        merged = self._merged_completed_leg1(version=version)
        instances = self.extract_winner_instances(version=version)

        empty_matrix = {lt: dict.fromkeys(FINAL_TIERS, 0) for lt in LEG1_TIERS}
        if merged.empty or not instances:
            return Leg1Metrics(
                version=version,
                total_completed_teams=0,
                pearson_r=0.0,
                ols_slope=0.0,
                ols_intercept=0.0,
                total_leg1_winners=0,
                champion_count=0,
                champion_rate=0.0,
                podium_count=0,
                podium_rate=0.0,
                final_four_count=0,
                final_four_rate=0.0,
                collapse_count=0,
                collapse_rate=0.0,
                mid_collapse_count=0,
                mid_collapse_rate=0.0,
                early_flameout_count=0,
                early_flameout_rate=0.0,
                mean_final_result=0.0,
                median_final_result=0.0,
                final_result_counts={},
                uturned_winner_count=0,
                uturned_winner_elim_count=0,
                uturned_winner_elim_rate=0.0,
                transition_matrix=empty_matrix,
                instances=[],
            )

        total_teams = len(merged)
        x = merged["placement_int"].to_numpy(dtype=float)
        y = merged["result_int"].to_numpy(dtype=float)

        if len(x) > 1 and np.std(x) > 0 and np.std(y) > 0:
            pearson_r = float(np.corrcoef(x, y)[0, 1])
            slope, intercept = np.polyfit(x, y, 1)
            ols_slope = float(slope)
            ols_intercept = float(intercept)
        else:
            pearson_r = 0.0
            ols_slope = 0.0
            ols_intercept = 0.0

        transition_matrix: dict[str, dict[str, int]] = {
            lt: dict.fromkeys(FINAL_TIERS, 0) for lt in LEG1_TIERS
        }
        for _, r in merged.iterrows():
            lt = classify_leg1_tier(int(r["placement_int"]))
            ft = classify_final_tier(int(r["result_int"]))
            transition_matrix[lt][ft] += 1

        n = len(instances)
        champ_cnt = sum(1 for i in instances if i.is_winner)
        pod_cnt = sum(1 for i in instances if i.is_podium)
        f4_cnt = sum(1 for i in instances if i.is_final_four)
        mid_cnt = sum(1 for i in instances if i.is_mid_collapse)
        early_cnt = sum(1 for i in instances if i.is_early_flameout)
        col_cnt = mid_cnt + early_cnt

        results = [i.final_result for i in instances]
        mean_res = float(np.mean(results))
        med_res = float(np.median(results))

        r_counts: dict[int, int] = {}
        for res in results:
            r_counts[res] = r_counts.get(res, 0) + 1

        ut_cnt = sum(1 for i in instances if i.was_uturned)
        ut_elim_cnt = sum(1 for i in instances if i.eliminated_by_uturn)
        ut_elim_rate = (ut_elim_cnt / ut_cnt) if ut_cnt > 0 else 0.0

        return Leg1Metrics(
            version=version,
            total_completed_teams=total_teams,
            pearson_r=pearson_r,
            ols_slope=ols_slope,
            ols_intercept=ols_intercept,
            total_leg1_winners=n,
            champion_count=champ_cnt,
            champion_rate=champ_cnt / n,
            podium_count=pod_cnt,
            podium_rate=pod_cnt / n,
            final_four_count=f4_cnt,
            final_four_rate=f4_cnt / n,
            collapse_count=col_cnt,
            collapse_rate=col_cnt / n,
            mid_collapse_count=mid_cnt,
            mid_collapse_rate=mid_cnt / n,
            early_flameout_count=early_cnt,
            early_flameout_rate=early_cnt / n,
            mean_final_result=mean_res,
            median_final_result=med_res,
            final_result_counts=dict(sorted(r_counts.items())),
            uturned_winner_count=ut_cnt,
            uturned_winner_elim_count=ut_elim_cnt,
            uturned_winner_elim_rate=ut_elim_rate,
            transition_matrix=transition_matrix,
            instances=instances,
        )

    def to_dataframe(self, version: str = "US") -> pd.DataFrame:
        """Convert extracted Leg 1 winner instances to pandas DataFrame."""
        instances = self.extract_winner_instances(version=version)
        if not instances:
            return pd.DataFrame()
        return pd.DataFrame([asdict(i) for i in instances])

    def summary_dict(self, version: str = "US") -> dict[str, Any]:
        """Return serializable summary dictionary without nested instance list."""
        metrics = self.analyze(version=version)
        data = asdict(metrics)
        data.pop("instances", None)
        return data
