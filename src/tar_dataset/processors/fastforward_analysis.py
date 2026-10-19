"""Fast Forward timing, prize capture, and championship conversion analysis.

Investigates empirical 1st-place leg conversion rates, early prize-hunting vs.
late-game survival timing optimization, and Classic Era (Seasons 1-4) vs.
Modern Scarce Era (Season 5+) strategic value across The Amazing Race.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def classify_ff_era(version: str, season: int) -> str:
    """Classify a Fast Forward into Classic Every-Leg Era vs. Modern Scarce Era."""
    if version.upper() == "US" and season <= 4:
        return "Classic (S1-S4)"
    return "Modern Scarce (S5+)"


def classify_ff_timing(leg_number: int) -> str:
    """Classify a Fast Forward play into Early, Mid, or Late leg timing buckets."""
    if leg_number <= 4:
        return "Early (Legs 1-4)"
    if leg_number <= 6:
        return "Mid (Legs 5-6)"
    return "Late (Legs 7+)"


@dataclass
class FastForwardInstance:
    """Represents a single Fast Forward execution event."""

    version: str
    season: int
    leg_number: int
    team_name: str
    placement: int
    raw_cell: str
    era: str
    timing_bucket: str
    won_leg: bool
    is_leg_podium: bool
    eliminated_on_leg: bool
    legs_survived_after: int
    total_legs_completed: int
    season_max_legs: int
    final_result: int | None
    is_winner: bool
    is_podium: bool
    reached_finale: bool
    description: str


@dataclass
class FastForwardMetrics:
    """Summary metrics of Fast Forward conversion, timing, and era dynamics."""

    version: str
    total_instances: int
    leg_win_count: int
    leg_win_rate: float
    leg_podium_count: int
    leg_podium_rate: float
    eliminated_on_leg_count: int
    eliminated_on_leg_rate: float
    mean_placement: float
    median_placement: float
    placement_counts: dict[int, int]
    mean_survival_lag: float
    median_survival_lag: float
    podium_count: int
    podium_rate: float
    winner_count: int
    winner_rate: float
    finale_count: int
    finale_rate: float
    early_count: int
    early_leg_win_rate: float
    early_podium_rate: float
    early_winner_rate: float
    mid_count: int
    mid_leg_win_rate: float
    mid_podium_rate: float
    mid_winner_rate: float
    late_count: int
    late_leg_win_rate: float
    late_podium_rate: float
    late_winner_rate: float
    classic_era_count: int
    classic_era_leg_win_rate: float
    classic_era_podium_rate: float
    classic_era_winner_rate: float
    modern_era_count: int
    modern_era_leg_win_rate: float
    modern_era_podium_rate: float
    modern_era_winner_rate: float
    instances: list[FastForwardInstance]


class FastForwardAnalyzer:
    """Empirical model and analyzer for Fast Forward plays, timing, and conversion."""

    def __init__(self, data_dir: Path | str = "data/processed") -> None:
        """Initialize analyzer with directory of processed dataset tables."""
        self.data_dir = Path(data_dir)
        self._leg_results_df: pd.DataFrame | None = None
        self._tasks_df: pd.DataFrame | None = None
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
    def tasks_df(self) -> pd.DataFrame:
        """Cached tasks table."""
        if self._tasks_df is None:
            self._tasks_df = self._load_table("tasks")
        return self._tasks_df

    @property
    def teams_df(self) -> pd.DataFrame:
        """Cached teams table."""
        if self._teams_df is None:
            self._teams_df = self._load_table("teams")
        return self._teams_df

    def _get_ff_description(self, version: str, season: int, leg_number: int) -> str:
        """Lookup Fast Forward task description for a given leg."""
        tasks = self.tasks_df
        if tasks.empty or "task_type" not in tasks.columns:
            return ""
        sub = tasks[
            (tasks["version"] == version)
            & (tasks["season"] == season)
            & (tasks["leg_number"] == leg_number)
            & (tasks["task_type"].str.lower().str.contains("fast forward", na=False))
        ]
        if not sub.empty and pd.notna(sub.iloc[0].get("description")):
            return str(sub.iloc[0]["description"])
        return ""

    def extract_instances(self, version: str = "US") -> list[FastForwardInstance]:
        """Extract all Fast Forward execution instances across seasons."""
        lr = self.leg_results_df
        teams = self.teams_df

        if lr.empty:
            return []

        if "fast_forward" in lr.columns:
            ff_mask = lr["fast_forward"].fillna(False).astype(bool)
        elif "raw_cell" in lr.columns:
            ff_mask = (
                lr["raw_cell"].astype(str).str.contains("ƒ", regex=False, na=False)
            )
        else:
            return []

        if version.upper() != "ALL":
            ff_mask = ff_mask & (lr["version"] == version.upper())

        ff_rows = lr[ff_mask].copy()
        if ff_rows.empty:
            return []

        instances: list[FastForwardInstance] = []
        for _, r in ff_rows.iterrows():
            ver = str(r["version"])
            s = int(r["season"])
            l_num = int(r["leg_number"])
            tm = str(r["team_name"])
            raw_cell = str(r.get("raw_cell", ""))
            place = int(r["placement"]) if pd.notna(r["placement"]) else 0

            team_all_legs = lr[
                (lr["version"] == ver) & (lr["season"] == s) & (lr["team_name"] == tm)
            ]
            max_leg_s = int(
                lr[(lr["version"] == ver) & (lr["season"] == s)]["leg_number"].max()
            )
            last_leg_team = int(team_all_legs["leg_number"].max())

            eliminated = ("†" in raw_cell) or (
                (last_leg_team == l_num) and (l_num < max_leg_s)
            )
            survival_lag = max(0, last_leg_team - l_num)

            team_match = teams[
                (teams["version"] == ver)
                & (teams["season"] == s)
                & (teams["team_name"] == tm)
            ]
            final_res: int | None = None
            total_completed = len(team_all_legs)
            if not team_match.empty:
                t_row = team_match.iloc[0]
                total_completed = int(t_row.get("legs_completed", total_completed))
                raw_res = t_row.get("result")
                if pd.notna(raw_res):
                    try:
                        final_res = int(raw_res)
                    except ValueError:
                        m = re.search(r"\d+", str(raw_res))
                        if m:
                            final_res = int(m.group(0))

            desc = self._get_ff_description(ver, s, l_num)
            instances.append(
                FastForwardInstance(
                    version=ver,
                    season=s,
                    leg_number=l_num,
                    team_name=tm,
                    placement=place,
                    raw_cell=raw_cell,
                    era=classify_ff_era(ver, s),
                    timing_bucket=classify_ff_timing(l_num),
                    won_leg=place == 1,
                    is_leg_podium=1 <= place <= 3,
                    eliminated_on_leg=eliminated,
                    legs_survived_after=survival_lag,
                    total_legs_completed=total_completed,
                    season_max_legs=max_leg_s,
                    final_result=final_res,
                    is_winner=final_res == 1,
                    is_podium=final_res is not None and final_res <= 3,
                    reached_finale=last_leg_team == max_leg_s,
                    description=desc,
                )
            )

        return instances

    def analyze(self, version: str = "US") -> FastForwardMetrics:
        """Compute aggregated Fast Forward conversion, timing, and era metrics."""
        instances = self.extract_instances(version=version)
        n = len(instances)
        if n == 0:
            return FastForwardMetrics(
                version=version,
                total_instances=0,
                leg_win_count=0,
                leg_win_rate=0.0,
                leg_podium_count=0,
                leg_podium_rate=0.0,
                eliminated_on_leg_count=0,
                eliminated_on_leg_rate=0.0,
                mean_placement=0.0,
                median_placement=0.0,
                placement_counts={},
                mean_survival_lag=0.0,
                median_survival_lag=0.0,
                podium_count=0,
                podium_rate=0.0,
                winner_count=0,
                winner_rate=0.0,
                finale_count=0,
                finale_rate=0.0,
                early_count=0,
                early_leg_win_rate=0.0,
                early_podium_rate=0.0,
                early_winner_rate=0.0,
                mid_count=0,
                mid_leg_win_rate=0.0,
                mid_podium_rate=0.0,
                mid_winner_rate=0.0,
                late_count=0,
                late_leg_win_rate=0.0,
                late_podium_rate=0.0,
                late_winner_rate=0.0,
                classic_era_count=0,
                classic_era_leg_win_rate=0.0,
                classic_era_podium_rate=0.0,
                classic_era_winner_rate=0.0,
                modern_era_count=0,
                modern_era_leg_win_rate=0.0,
                modern_era_podium_rate=0.0,
                modern_era_winner_rate=0.0,
                instances=[],
            )

        leg_win_cnt = sum(1 for i in instances if i.won_leg)
        leg_pod_cnt = sum(1 for i in instances if i.is_leg_podium)
        elim_cnt = sum(1 for i in instances if i.eliminated_on_leg)

        placements = [i.placement for i in instances if i.placement > 0]
        mean_pl = float(np.mean(placements)) if placements else 0.0
        med_pl = float(np.median(placements)) if placements else 0.0

        p_counts: dict[int, int] = {}
        for p in placements:
            p_counts[p] = p_counts.get(p, 0) + 1

        lags = [i.legs_survived_after for i in instances]
        mean_lag = float(np.mean(lags))
        med_lag = float(np.median(lags))

        pod_cnt = sum(1 for i in instances if i.is_podium)
        win_cnt = sum(1 for i in instances if i.is_winner)
        fin_cnt = sum(1 for i in instances if i.reached_finale)

        def _subset_rates(
            sub: list[FastForwardInstance],
        ) -> tuple[int, float, float, float]:
            k = len(sub)
            if k == 0:
                return 0, 0.0, 0.0, 0.0
            return (
                k,
                sum(1 for i in sub if i.won_leg) / k,
                sum(1 for i in sub if i.is_podium) / k,
                sum(1 for i in sub if i.is_winner) / k,
            )

        early_sub = [i for i in instances if i.timing_bucket == "Early (Legs 1-4)"]
        mid_sub = [i for i in instances if i.timing_bucket == "Mid (Legs 5-6)"]
        late_sub = [i for i in instances if i.timing_bucket == "Late (Legs 7+)"]

        e_cnt, e_lw, e_pod, e_win = _subset_rates(early_sub)
        m_cnt, m_lw, m_pod, m_win = _subset_rates(mid_sub)
        l_cnt, l_lw, l_pod, l_win = _subset_rates(late_sub)

        classic_sub = [i for i in instances if i.era == "Classic (S1-S4)"]
        modern_sub = [i for i in instances if i.era == "Modern Scarce (S5+)"]

        c_cnt, c_lw, c_pod, c_win = _subset_rates(classic_sub)
        mod_cnt, mod_lw, mod_pod, mod_win = _subset_rates(modern_sub)

        return FastForwardMetrics(
            version=version,
            total_instances=n,
            leg_win_count=leg_win_cnt,
            leg_win_rate=leg_win_cnt / n,
            leg_podium_count=leg_pod_cnt,
            leg_podium_rate=leg_pod_cnt / n,
            eliminated_on_leg_count=elim_cnt,
            eliminated_on_leg_rate=elim_cnt / n,
            mean_placement=mean_pl,
            median_placement=med_pl,
            placement_counts=dict(sorted(p_counts.items())),
            mean_survival_lag=mean_lag,
            median_survival_lag=med_lag,
            podium_count=pod_cnt,
            podium_rate=pod_cnt / n,
            winner_count=win_cnt,
            winner_rate=win_cnt / n,
            finale_count=fin_cnt,
            finale_rate=fin_cnt / n,
            early_count=e_cnt,
            early_leg_win_rate=e_lw,
            early_podium_rate=e_pod,
            early_winner_rate=e_win,
            mid_count=m_cnt,
            mid_leg_win_rate=m_lw,
            mid_podium_rate=m_pod,
            mid_winner_rate=m_win,
            late_count=l_cnt,
            late_leg_win_rate=l_lw,
            late_podium_rate=l_pod,
            late_winner_rate=l_win,
            classic_era_count=c_cnt,
            classic_era_leg_win_rate=c_lw,
            classic_era_podium_rate=c_pod,
            classic_era_winner_rate=c_win,
            modern_era_count=mod_cnt,
            modern_era_leg_win_rate=mod_lw,
            modern_era_podium_rate=mod_pod,
            modern_era_winner_rate=mod_win,
            instances=instances,
        )

    def to_dataframe(self, version: str = "US") -> pd.DataFrame:
        """Convert extracted Fast Forward instances to pandas DataFrame."""
        instances = self.extract_instances(version=version)
        if not instances:
            return pd.DataFrame()
        return pd.DataFrame([asdict(i) for i in instances])

    def summary_dict(self, version: str = "US") -> dict[str, Any]:
        """Return serializable summary dictionary without nested instance list."""
        metrics = self.analyze(version=version)
        data = asdict(metrics)
        data.pop("instances", None)
        return data
