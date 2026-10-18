"""Speed Bump penalty efficacy and post-NEL survival lag analysis.

Investigates empirical survival rates, placement dynamics, and championship
conversion for teams subjected to the Speed Bump penalty following a
Non-Elimination Leg (NEL) save.
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


@dataclass
class SpeedBumpInstance:
    """Represents a single Speed Bump penalty execution event."""

    version: str
    season: int
    leg_number: int
    team_name: str
    placement: int
    raw_cell: str
    prev_placement: int | None
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
class SpeedBumpMetrics:
    """Summary metrics of Speed Bump penalty efficacy and survival trajectory."""

    version: str
    total_instances: int
    eliminated_on_leg_count: int
    eliminated_on_leg_rate: float
    survived_leg_count: int
    survived_leg_rate: float
    mean_placement: float
    median_placement: float
    placement_counts: dict[int, int]
    survival_lag_distribution: dict[int, int]
    mean_survival_lag: float
    median_survival_lag: float
    podium_count: int
    podium_rate: float
    winner_count: int
    winner_rate: float
    finale_count: int
    finale_rate: float
    instances: list[SpeedBumpInstance]


def normalize_text(text: str) -> str:
    """Normalize text for consistent token matching."""
    t = text.lower().replace("&", " and ")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return " ".join(t.split())


def match_team_from_description(desc: str, team_names: list[str]) -> str | None:
    """Match team name mentioned in Speed Bump challenge narrative.

    Args:
        desc: Challenge description string.
        team_names: List of candidate team names in the season.

    Returns:
        Matched team name or None.
    """
    norm_desc = normalize_text(desc)
    desc_words = set(norm_desc.split())

    # 1. Exact normalized team name substring in normalized description
    for tm in sorted(team_names, key=len, reverse=True):
        norm_tm = normalize_text(tm)
        if f" {norm_tm} " in f" {norm_desc} ":
            return tm

    # 2. Both partner names present as discrete tokens
    for tm in sorted(team_names, key=len, reverse=True):
        parts = [normalize_text(p) for p in re.split(r"[&/]| and ", tm)]
        if len(parts) == 2:
            p0, p1 = parts[0].split(), parts[1].split()
            if all(w in desc_words for w in p0) and all(w in desc_words for w in p1):
                return tm
    return None


class SpeedBumpAnalyzer:
    """Statistical model and analyzer for Speed Bump penalties and post-NEL survival."""

    def __init__(self, data_dir: Path | str = "data/processed") -> None:
        """Initialize analyzer with directory of processed dataset tables."""
        self.data_dir = Path(data_dir)
        self._tasks_df: pd.DataFrame | None = None
        self._legs_df: pd.DataFrame | None = None
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
    def tasks_df(self) -> pd.DataFrame:
        """Cached tasks table."""
        if self._tasks_df is None:
            self._tasks_df = self._load_table("tasks")
        return self._tasks_df

    @property
    def legs_df(self) -> pd.DataFrame:
        """Cached leg results table."""
        if self._legs_df is None:
            self._legs_df = self._load_table("leg_results")
        return self._legs_df

    @property
    def teams_df(self) -> pd.DataFrame:
        """Cached teams table."""
        if self._teams_df is None:
            self._teams_df = self._load_table("teams")
        return self._teams_df

    def extract_instances(self, version: str = "US") -> list[SpeedBumpInstance]:
        """Extract and link all authentic Speed Bump penalty events.

        Args:
            version: Franchise version code ('US', 'CAN', 'AUS', or 'ALL').

        Returns:
            List of linked SpeedBumpInstance records.
        """
        tasks = self.tasks_df
        legs = self.legs_df
        teams = self.teams_df

        sb_mask = tasks["task_type"].str.lower().str.contains("speed bump", na=False)
        if version.upper() != "ALL":
            sb_mask = sb_mask & (tasks["version"] == version.upper())

        sb_tasks = tasks[sb_mask].copy()
        if sb_tasks.empty:
            return []

        # Deduplicate task rows by season, leg, and description
        records: list[dict[str, Any]] = []
        for _, row in sb_tasks.iterrows():
            ver = str(row["version"])
            s = int(row["season"])
            l = int(row["leg_number"])
            desc = str(row["description"])

            season_teams = teams[(teams["version"] == ver) & (teams["season"] == s)][
                "team_name"
            ].tolist()

            matched_tm = match_team_from_description(desc, season_teams)
            if not matched_tm:
                logger.warning(
                    "Could not resolve team for Speed Bump task in %s S%02d E%02d",
                    ver,
                    s,
                    l,
                )
                continue

            records.append(
                {
                    "version": ver,
                    "season": s,
                    "leg_number": l,
                    "team_name": matched_tm,
                    "description": desc,
                }
            )

        raw_df = pd.DataFrame(records).drop_duplicates(
            subset=["version", "season", "leg_number", "team_name"]
        )

        instances: list[SpeedBumpInstance] = []
        for _, r in raw_df.iterrows():
            ver, s, l, tm = (
                r["version"],
                r["season"],
                r["leg_number"],
                r["team_name"],
            )

            leg_match = legs[
                (legs["version"] == ver)
                & (legs["season"] == s)
                & (legs["leg_number"] == l)
                & (legs["team_name"] == tm)
            ]
            team_match = teams[
                (teams["version"] == ver)
                & (teams["season"] == s)
                & (teams["team_name"] == tm)
            ]

            if leg_match.empty or team_match.empty:
                logger.warning(
                    "Missing relational match for %s S%02d E%02d %s", ver, s, l, tm
                )
                continue

            leg_row = leg_match.iloc[0]
            team_row = team_match.iloc[0]

            team_all_legs = legs[
                (legs["version"] == ver)
                & (legs["season"] == s)
                & (legs["team_name"] == tm)
            ]

            max_leg_s = int(
                legs[(legs["version"] == ver) & (legs["season"] == s)][
                    "leg_number"
                ].max()
            )
            last_leg_team = int(team_all_legs["leg_number"].max())

            # Elimination on penalty leg: last leg raced is current leg, before finale
            eliminated = (last_leg_team == l) and (l < max_leg_s)
            survival_lag = max(0, last_leg_team - l)

            # Previous leg placement
            prev_leg_match = legs[
                (legs["version"] == ver)
                & (legs["season"] == s)
                & (legs["leg_number"] == l - 1)
                & (legs["team_name"] == tm)
            ]
            prev_place = (
                int(prev_leg_match.iloc[0]["placement"])
                if not prev_leg_match.empty
                and pd.notna(prev_leg_match.iloc[0]["placement"])
                else None
            )

            # Final finish result
            raw_res = team_row.get("result")
            final_res: int | None = None
            if pd.notna(raw_res):
                try:
                    final_res = int(raw_res)
                except ValueError:
                    # In case of string like '1st'
                    match = re.search(r"\d+", str(raw_res))
                    if match:
                        final_res = int(match.group(0))

            is_win = final_res == 1
            is_pod = final_res is not None and final_res <= 3
            finale = last_leg_team == max_leg_s

            instances.append(
                SpeedBumpInstance(
                    version=ver,
                    season=s,
                    leg_number=l,
                    team_name=tm,
                    placement=int(leg_row["placement"])
                    if pd.notna(leg_row["placement"])
                    else 0,
                    raw_cell=str(leg_row.get("raw_cell", "")),
                    prev_placement=prev_place,
                    eliminated_on_leg=eliminated,
                    legs_survived_after=survival_lag,
                    total_legs_completed=int(team_row.get("legs_completed", 0)),
                    season_max_legs=max_leg_s,
                    final_result=final_res,
                    is_winner=is_win,
                    is_podium=is_pod,
                    reached_finale=finale,
                    description=r["description"],
                )
            )

        return instances

    def analyze(self, version: str = "US") -> SpeedBumpMetrics:
        """Compute aggregated Speed Bump survival and efficacy metrics.

        Args:
            version: Franchise version code ('US', 'CAN', 'AUS', or 'ALL').

        Returns:
            SpeedBumpMetrics object.
        """
        instances = self.extract_instances(version=version)
        n = len(instances)
        if n == 0:
            return SpeedBumpMetrics(
                version=version,
                total_instances=0,
                eliminated_on_leg_count=0,
                eliminated_on_leg_rate=0.0,
                survived_leg_count=0,
                survived_leg_rate=0.0,
                mean_placement=0.0,
                median_placement=0.0,
                placement_counts={},
                survival_lag_distribution={},
                mean_survival_lag=0.0,
                median_survival_lag=0.0,
                podium_count=0,
                podium_rate=0.0,
                winner_count=0,
                winner_rate=0.0,
                finale_count=0,
                finale_rate=0.0,
                instances=[],
            )

        elim_count = sum(1 for i in instances if i.eliminated_on_leg)
        surv_count = n - elim_count

        placements = [i.placement for i in instances if i.placement > 0]
        mean_pl = float(np.mean(placements)) if placements else 0.0
        med_pl = float(np.median(placements)) if placements else 0.0

        p_counts: dict[int, int] = {}
        for p in placements:
            p_counts[p] = p_counts.get(p, 0) + 1

        lags = [i.legs_survived_after for i in instances]
        mean_lag = float(np.mean(lags))
        med_lag = float(np.median(lags))

        lag_dist: dict[int, int] = {}
        for lag in lags:
            lag_dist[lag] = lag_dist.get(lag, 0) + 1

        pod_count = sum(1 for i in instances if i.is_podium)
        win_count = sum(1 for i in instances if i.is_winner)
        fin_count = sum(1 for i in instances if i.reached_finale)

        return SpeedBumpMetrics(
            version=version,
            total_instances=n,
            eliminated_on_leg_count=elim_count,
            eliminated_on_leg_rate=elim_count / n,
            survived_leg_count=surv_count,
            survived_leg_rate=surv_count / n,
            mean_placement=mean_pl,
            median_placement=med_pl,
            placement_counts=dict(sorted(p_counts.items())),
            survival_lag_distribution=dict(sorted(lag_dist.items())),
            mean_survival_lag=mean_lag,
            median_survival_lag=med_lag,
            podium_count=pod_count,
            podium_rate=pod_count / n,
            winner_count=win_count,
            winner_rate=win_count / n,
            finale_count=fin_count,
            finale_rate=fin_count / n,
            instances=instances,
        )

    def to_dataframe(self, version: str = "US") -> pd.DataFrame:
        """Convert extracted instances to pandas DataFrame."""
        instances = self.extract_instances(version=version)
        if not instances:
            return pd.DataFrame()
        return pd.DataFrame([asdict(i) for i in instances])

    def summary_dict(self, version: str = "US") -> dict[str, Any]:
        """Return serializable summary dictionary."""
        metrics = self.analyze(version=version)
        data = asdict(metrics)
        data.pop("instances")  # Omit large nested list for concise summary
        return data
