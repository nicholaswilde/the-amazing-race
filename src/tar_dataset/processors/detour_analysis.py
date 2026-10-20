"""Detour branch switching penalties, task archetypes, and sunk-cost analysis.

Investigates Detour branch archetype distribution, 100%-avoided ("would have had to")
branch rates, single-branch vs. mid-leg switch/bottleneck collapse vs. forced
dual-branch (U-Turn) placement and elimination penalties, and the empirical
sunk-cost survival threshold curve across The Amazing Race franchises.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

ARCHETYPE_RULES: list[tuple[str, str]] = [
    (
        "Thrill / Heights",
        r"\b(?:bungee|skydive|parachute|rappel|abseil|zipline|cliff|canyon|drop|freefall|hang glid|tightrope|ledge)\b",
    ),
    (
        "Judge / Performance",
        r"\b(?:dance|dancing|sing|song|music|perform|instrument|rhythm|routine|judge|judges|approved|recite|memoriz|poem|script|dialect|pronounc|rap|tango|salsa|bollywood|opera|march|parade|costume)\b",
    ),
    (
        "Searching / Needle",
        r"\b(?:search|find|hidden|locate|hunt|buried|haystack|dig|sift|look for|matching|marked|metal detector|clue inside|unmarked)\b",
    ),
    (
        "Attention to Detail / Puzzle",
        r"\b(?:assemble|build|construct|puzzle|arrange|exact|replica|identi|count|measure|weigh|stack|fragile|intricate|sort|decode|math|order|folded|pack|sew|paint|decorate)\b",
    ),
    (
        "Skill / Coordination",
        r"\b(?:steer|navigate|drive|driving|punt|row|paddle|kayak|golf|bowl|shoot|target|throw|toss|kick|herd|camel|donkey|llama|horse|bike|bicycle|skating|ski|sail|surf|raft|balance)\b",
    ),
    (
        "Physical / Brute Force",
        r"\b(?:carry|haul|load|unload|push|pull|climb|hike|run|walk|deliver|transport|heavy|crates|bags|sacks|bales|bricks|wood|coal|water|fill|chop|saw|scrub|wash|clean|stairs|steps|mile|kilometre)\b",
    ),
]

SUNK_COST_BUCKETS: list[tuple[int, str]] = [
    (0, "0 or Gain (<=0)"),
    (1, "+1 Spot Lost"),
    (2, "+2 Spots Lost"),
    (3, "+3 Spots Lost (Switch Zone)"),
    (4, "+4 Spots Lost"),
    (5, "+5+ Spots Lost (Sunk-Cost Trap)"),
]


def classify_detour_branch(text: str) -> str:
    """Classify a Detour branch description into its primary task archetype."""
    for archetype, pattern in ARCHETYPE_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return archetype
    return "Physical / Brute Force"


@dataclass
class DetourBranchInstance:
    """Represents a single branch option (A or B) of a Detour challenge."""

    version: str
    season: int
    leg_number: int
    branch: str
    branch_name: str
    archetype: str
    is_unchosen: bool
    is_blind: bool
    description_excerpt: str


@dataclass
class DetourSwitchEvent:
    """Represents a severe mid-leg Detour drop or forced dual-branch execution."""

    version: str
    season: int
    leg_number: int
    team_name: str
    execution_mode: str
    prev_placement: int
    placement: int
    placement_delta: int
    field_size: int
    is_last_place: bool
    is_eliminated: bool
    detour_names: str


@dataclass
class DetourMetrics:
    """Summary metrics for Detour branch archetypes, switching penalties, and sunk cost."""

    version: str
    total_detours: int
    total_branches: int
    unchosen_branch_count: int
    unchosen_branch_rate: float
    blind_detour_count: int
    archetype_summary: dict[str, dict[str, float | int]]
    total_team_legs: int
    clean_single_count: int
    clean_single_mean_prev: float
    clean_single_mean_curr: float
    clean_single_mean_delta: float
    clean_single_last_place_rate: float
    clean_single_elim_rate: float
    voluntary_switch_count: int
    voluntary_switch_mean_prev: float
    voluntary_switch_mean_curr: float
    voluntary_switch_mean_delta: float
    voluntary_switch_last_place_rate: float
    voluntary_switch_elim_rate: float
    forced_dual_count: int
    forced_dual_mean_prev: float
    forced_dual_mean_curr: float
    forced_dual_mean_delta: float
    forced_dual_last_place_rate: float
    forced_dual_elim_rate: float
    sunk_cost_curve: dict[str, dict[str, float | int]]
    branches: list[DetourBranchInstance]
    switch_events: list[DetourSwitchEvent]

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to a dictionary."""
        return asdict(self)


class DetourAnalyzer:
    """Analyzes Detour branch archetypes, switching penalties, and sunk-cost curves."""

    def __init__(self, data_dir: Path | str = Path("data/processed")) -> None:
        self.data_dir = Path(data_dir)
        self._tasks_df: pd.DataFrame | None = None
        self._leg_results_df: pd.DataFrame | None = None

    def _load_table(self, name: str) -> pd.DataFrame:
        parquet_path = self.data_dir / f"{name}.parquet"
        csv_path = self.data_dir / f"{name}.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        logger.warning("Table %s not found in %s", name, self.data_dir)
        return pd.DataFrame()

    @property
    def tasks_df(self) -> pd.DataFrame:
        """Cached tasks table."""
        if self._tasks_df is None:
            self._tasks_df = self._load_table("tasks")
        return self._tasks_df

    @property
    def leg_results_df(self) -> pd.DataFrame:
        """Cached leg_results table."""
        if self._leg_results_df is None:
            self._leg_results_df = self._load_table("leg_results")
        return self._leg_results_df

    def extract_branches(self, version: str = "US") -> list[DetourBranchInstance]:
        """Extract and classify individual Detour branch options (A and B)."""
        tasks = self.tasks_df
        if tasks.empty or "task_type" not in tasks.columns:
            return []

        detours = tasks[tasks["task_type"] == "Detour"].copy()
        if version.upper() != "ALL":
            detours = detours[detours["version"] == version.upper()]
        if detours.empty:
            return []

        choice_rows = detours[
            detours["description"]
            .astype(str)
            .str.contains(r"choice between|Blind Detour", case=False, na=False)
        ].copy()
        choice_rows = choice_rows.drop_duplicates(
            subset=["version", "season", "leg_number"]
        ).sort_values(["version", "season", "leg_number"])

        instances: list[DetourBranchInstance] = []
        for _, row in choice_rows.iterrows():
            ver = str(row["version"])
            season = int(row["season"])
            leg_num = int(row["leg_number"])
            desc = str(row["description"])
            is_blind = bool(re.search(r"blind detour", desc, flags=re.IGNORECASE))

            m = re.search(
                r"choice between\s+(.+?)\s+(?:or|and)\s+([^.]+)\.",
                desc,
                flags=re.IGNORECASE,
            )
            if not m:
                continue

            b1_name = m.group(1).strip()
            b2_name = m.group(2).strip()
            m2 = re.search(
                r"\bIn\s+" + re.escape(b2_name[:12]),
                desc[m.end() :],
                flags=re.IGNORECASE,
            )
            if m2:
                split_idx = m.end() + m2.start()
                b1_text = desc[m.end() : split_idx].strip()
                b2_text = desc[split_idx:].strip()
            else:
                sentences = desc[m.end() :].split(". ")
                mid = max(1, len(sentences) // 2)
                b1_text = ". ".join(sentences[:mid]).strip()
                b2_text = ". ".join(sentences[mid:]).strip()

            for b_code, b_name, b_text in [
                ("A", b1_name, b1_text),
                ("B", b2_name, b2_text),
            ]:
                unchosen = bool(
                    re.search(
                        r"would have|no teams? chose|neither team chose|none of the teams chose",
                        b_text,
                        flags=re.IGNORECASE,
                    )
                )
                archetype = classify_detour_branch(f"{b_name} {b_text}")
                instances.append(
                    DetourBranchInstance(
                        version=ver,
                        season=season,
                        leg_number=leg_num,
                        branch=b_code,
                        branch_name=b_name,
                        archetype=archetype,
                        is_unchosen=unchosen,
                        is_blind=is_blind,
                        description_excerpt=b_text[:160],
                    )
                )

        return instances

    def extract_team_leg_df(self, version: str = "US") -> pd.DataFrame:
        """Build team-leg dataframe on Detour legs with placement deltas and U-Turn flags."""
        tasks = self.tasks_df
        lr = self.leg_results_df
        if tasks.empty or lr.empty:
            return pd.DataFrame()

        detours = tasks[tasks["task_type"] == "Detour"].copy()
        if detours.empty:
            return pd.DataFrame()

        detour_legs = detours[["version", "season", "leg_number"]].drop_duplicates()
        detour_legs["has_detour"] = True

        df = lr.dropna(subset=["placement"]).copy()
        if version.upper() != "ALL":
            df = df[df["version"] == version.upper()]
        if df.empty:
            return pd.DataFrame()

        df["placement"] = df["placement"].astype(int)
        df["leg_number"] = df["leg_number"].astype(int)
        raw_series = (
            df["raw_cell"].astype(str)
            if "raw_cell" in df.columns
            else pd.Series("", index=df.index)
        )
        uturn_col = (
            df["uturn"].fillna(False).astype(bool)
            if "uturn" in df.columns
            else pd.Series(False, index=df.index)
        )
        df["is_uturn_victim"] = uturn_col | raw_series.str.contains(
            "⊂", regex=False, na=False
        )
        df = df.sort_values(["version", "season", "team_name", "leg_number"])
        df["prev_placement"] = df.groupby(["version", "season", "team_name"])[
            "placement"
        ].shift(1)
        df["team_last_leg"] = df.groupby(["version", "season", "team_name"])[
            "leg_number"
        ].transform("max")

        leg_stats = (
            df.groupby(["version", "season", "leg_number"])
            .agg(
                field_size=("placement", "count"),
                max_placement=("placement", "max"),
            )
            .reset_index()
        )
        season_max_leg = (
            df.groupby(["version", "season"])["leg_number"]
            .max()
            .rename("max_season_leg")
            .reset_index()
        )

        df = df.merge(leg_stats, on=["version", "season", "leg_number"], how="left")
        df = df.merge(season_max_leg, on=["version", "season"], how="left")
        df = df.merge(detour_legs, on=["version", "season", "leg_number"], how="left")
        df["has_detour"] = df["has_detour"].fillna(False)

        det_df = df[
            df["has_detour"]
            & df["prev_placement"].notna()
            & (df["leg_number"] < df["max_season_leg"])
        ].copy()
        if det_df.empty:
            return pd.DataFrame()

        det_df["prev_placement"] = det_df["prev_placement"].astype(int)
        det_df["placement_delta"] = det_df["placement"] - det_df["prev_placement"]
        det_raw = (
            det_df["raw_cell"].astype(str)
            if "raw_cell" in det_df.columns
            else pd.Series("", index=det_df.index)
        )
        det_df["is_eliminated"] = det_raw.str.contains("†", regex=False, na=False) | (
            (det_df["team_last_leg"] == det_df["leg_number"])
            & (det_df["leg_number"] < det_df["max_season_leg"])
        )
        det_df["is_last_place"] = det_df["placement"] == det_df["max_placement"]
        return det_df

    def analyze(self, version: str = "US") -> DetourMetrics:
        """Compute full Detour archetype, switching penalty, and sunk-cost metrics."""
        ver = version.upper()
        branches = self.extract_branches(version=ver)
        det_df = self.extract_team_leg_df(version=ver)

        total_branches = len(branches)
        total_detours = total_branches // 2
        unchosen_count = sum(1 for b in branches if b.is_unchosen)
        unchosen_rate = unchosen_count / total_branches if total_branches else 0.0
        blind_legs = {
            (b.version, b.season, b.leg_number) for b in branches if b.is_blind
        }
        blind_detour_count = len(blind_legs)

        # Build branch lookup per leg for switch event context
        leg_branch_names: dict[tuple[str, int, int], list[str]] = {}
        for b in branches:
            key = (b.version, b.season, b.leg_number)
            leg_branch_names.setdefault(key, []).append(b.branch_name)

        archetype_summary: dict[str, dict[str, float | int]] = {}
        if branches:
            bdf = pd.DataFrame([asdict(b) for b in branches])
            for arch, grp in bdf.groupby("archetype"):
                cnt = len(grp)
                unch = int(grp["is_unchosen"].sum())
                archetype_summary[str(arch)] = {
                    "branches": cnt,
                    "pct_of_all": round(cnt / total_branches, 4),
                    "unchosen_count": unch,
                    "unchosen_rate": round(unch / cnt, 4) if cnt else 0.0,
                }
            # Sort by branch count descending
            archetype_summary = dict(
                sorted(
                    archetype_summary.items(),
                    key=lambda kv: int(kv[1]["branches"]),
                    reverse=True,
                )
            )

        if det_df.empty:
            return DetourMetrics(
                version=ver,
                total_detours=total_detours,
                total_branches=total_branches,
                unchosen_branch_count=unchosen_count,
                unchosen_branch_rate=round(unchosen_rate, 4),
                blind_detour_count=blind_detour_count,
                archetype_summary=archetype_summary,
                total_team_legs=0,
                clean_single_count=0,
                clean_single_mean_prev=0.0,
                clean_single_mean_curr=0.0,
                clean_single_mean_delta=0.0,
                clean_single_last_place_rate=0.0,
                clean_single_elim_rate=0.0,
                voluntary_switch_count=0,
                voluntary_switch_mean_prev=0.0,
                voluntary_switch_mean_curr=0.0,
                voluntary_switch_mean_delta=0.0,
                voluntary_switch_last_place_rate=0.0,
                voluntary_switch_elim_rate=0.0,
                forced_dual_count=0,
                forced_dual_mean_prev=0.0,
                forced_dual_mean_curr=0.0,
                forced_dual_mean_delta=0.0,
                forced_dual_last_place_rate=0.0,
                forced_dual_elim_rate=0.0,
                sunk_cost_curve={},
                branches=branches,
                switch_events=[],
            )

        clean = det_df[(~det_df["is_uturn_victim"]) & (det_df["placement_delta"] <= 2)]
        vol_switch = det_df[
            (~det_df["is_uturn_victim"]) & (det_df["placement_delta"] >= 3)
        ]
        forced_dual = det_df[det_df["is_uturn_victim"]]

        def _grp_stats(
            grp: pd.DataFrame,
        ) -> tuple[int, float, float, float, float, float]:
            n = len(grp)
            if n == 0:
                return 0, 0.0, 0.0, 0.0, 0.0, 0.0
            return (
                n,
                round(float(grp["prev_placement"].mean()), 2),
                round(float(grp["placement"].mean()), 2),
                round(float(grp["placement_delta"].mean()), 2),
                round(float(grp["is_last_place"].mean()), 4),
                round(float(grp["is_eliminated"].mean()), 4),
            )

        (
            c_n,
            c_prev,
            c_curr,
            c_delta,
            c_last,
            c_elim,
        ) = _grp_stats(clean)
        (
            v_n,
            v_prev,
            v_curr,
            v_delta,
            v_last,
            v_elim,
        ) = _grp_stats(vol_switch)
        (
            f_n,
            f_prev,
            f_curr,
            f_delta,
            f_last,
            f_elim,
        ) = _grp_stats(forced_dual)

        contenders = det_df[
            (~det_df["is_uturn_victim"])
            & (det_df["prev_placement"] <= det_df["field_size"] - 2)
        ].copy()
        sunk_cost_curve: dict[str, dict[str, float | int]] = {}
        for delta_val, label in SUNK_COST_BUCKETS:
            if delta_val == 0:
                g = contenders[contenders["placement_delta"] <= 0]
            elif delta_val == 5:
                g = contenders[contenders["placement_delta"] >= 5]
            else:
                g = contenders[contenders["placement_delta"] == delta_val]
            gn = len(g)
            sunk_cost_curve[label] = {
                "count": gn,
                "last_place_rate": round(float(g["is_last_place"].mean()), 4)
                if gn
                else 0.0,
                "elim_rate": round(float(g["is_eliminated"].mean()), 4) if gn else 0.0,
            }

        switch_events: list[DetourSwitchEvent] = []
        event_rows = det_df[
            det_df["is_uturn_victim"] | (det_df["placement_delta"] >= 3)
        ].sort_values(["version", "season", "leg_number", "placement"])
        for _, r in event_rows.iterrows():
            rk = (str(r["version"]), int(r["season"]), int(r["leg_number"]))
            b_names = leg_branch_names.get(rk, [])
            detour_label = " vs. ".join(b_names[:2]) if b_names else "Detour"
            mode = (
                "Forced Dual-Branch (U-Turn)"
                if bool(r["is_uturn_victim"])
                else "Mid-Leg Switch / Bottleneck Drop"
            )
            switch_events.append(
                DetourSwitchEvent(
                    version=str(r["version"]),
                    season=int(r["season"]),
                    leg_number=int(r["leg_number"]),
                    team_name=str(r["team_name"]),
                    execution_mode=mode,
                    prev_placement=int(r["prev_placement"]),
                    placement=int(r["placement"]),
                    placement_delta=int(r["placement_delta"]),
                    field_size=int(r["field_size"]),
                    is_last_place=bool(r["is_last_place"]),
                    is_eliminated=bool(r["is_eliminated"]),
                    detour_names=detour_label,
                )
            )

        return DetourMetrics(
            version=ver,
            total_detours=total_detours,
            total_branches=total_branches,
            unchosen_branch_count=unchosen_count,
            unchosen_branch_rate=round(unchosen_rate, 4),
            blind_detour_count=blind_detour_count,
            archetype_summary=archetype_summary,
            total_team_legs=len(det_df),
            clean_single_count=c_n,
            clean_single_mean_prev=c_prev,
            clean_single_mean_curr=c_curr,
            clean_single_mean_delta=c_delta,
            clean_single_last_place_rate=c_last,
            clean_single_elim_rate=c_elim,
            voluntary_switch_count=v_n,
            voluntary_switch_mean_prev=v_prev,
            voluntary_switch_mean_curr=v_curr,
            voluntary_switch_mean_delta=v_delta,
            voluntary_switch_last_place_rate=v_last,
            voluntary_switch_elim_rate=v_elim,
            forced_dual_count=f_n,
            forced_dual_mean_prev=f_prev,
            forced_dual_mean_curr=f_curr,
            forced_dual_mean_delta=f_delta,
            forced_dual_last_place_rate=f_last,
            forced_dual_elim_rate=f_elim,
            sunk_cost_curve=sunk_cost_curve,
            branches=branches,
            switch_events=switch_events,
        )
