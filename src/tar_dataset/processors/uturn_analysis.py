"""U-Turn lethality, retaliation dynamics, and defensive burn strategy analysis.

Investigates empirical single-leg elimination rates, placement recovery,
Double U-Turn chain vs. defensive burn efficacy, and Blind vs. Public
retaliation dynamics across The Amazing Race franchises.
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

# Canonical Blind / Anonymous U-Turn legs across franchises
KNOWN_BLIND_LEGS: set[tuple[str, int, int]] = {
    ("US", 12, 8),
    ("US", 14, 4),
    ("US", 16, 5),
    ("US", 21, 3),
    ("US", 25, 5),
    ("US", 26, 1),
    ("US", 26, 8),
    ("US", 27, 4),
    ("US", 29, 3),
    ("CAN", 1, 5),
    ("CAN", 5, 6),
    ("CAN", 6, 4),
    ("AUS", 2, 5),
}


@dataclass
class UTurnInstance:
    """Represents a single U-Turn victim execution event."""

    version: str
    season: int
    leg_number: int
    team_name: str
    user_team: str
    board_type: str
    is_blind: bool
    is_chain_uturn: bool
    second_slot_burned: bool
    placement: int
    raw_cell: str
    prev_placement: int | None
    eliminated_on_leg: bool
    legs_survived_after: int
    total_legs_completed: int
    season_max_legs: int
    final_result: int | None
    is_leg_podium: bool
    is_winner: bool
    is_podium: bool
    reached_finale: bool


@dataclass
class UTurnBurnEvent:
    """Represents a wasted or defensively burned U-Turn slot targeting a team ahead."""

    version: str
    season: int
    leg_number: int
    burner_team: str
    target_team: str
    is_double_board: bool
    is_intentional_defensive: bool
    primary_victim: str | None
    primary_victim_eliminated: bool
    narrative_excerpt: str


@dataclass
class UTurnMetrics:
    """Summary metrics of U-Turn lethality, recovery, defensive burns, and retaliation."""

    version: str
    total_victims: int
    eliminated_on_leg_count: int
    eliminated_on_leg_rate: float
    survived_leg_count: int
    survived_leg_rate: float
    leg_podium_count: int
    leg_podium_rate: float
    mean_placement: float
    median_placement: float
    placement_counts: dict[int, int]
    survival_lag_distribution: dict[int, int]
    mean_survival_lag: float
    survivor_mean_survival_lag: float
    median_survival_lag: float
    podium_count: int
    podium_rate: float
    winner_count: int
    winner_rate: float
    finale_count: int
    finale_rate: float
    chain_uturn_count: int
    chain_uturn_survived_count: int
    chain_uturn_survival_rate: float
    wasted_uturn_count: int
    double_board_burn_count: int
    double_board_burn_elim_rate: float
    intentional_defensive_burn_count: int
    intentional_defensive_burn_elim_rate: float
    total_users: int
    blind_users_count: int
    public_users_count: int
    blind_user_retaliation_count: int
    blind_user_retaliation_rate: float
    public_user_retaliation_count: int
    public_user_retaliation_rate: float
    blind_victim_elim_rate: float
    public_victim_elim_rate: float
    vote_victim_elim_rate: float
    instances: list[UTurnInstance]
    burn_events: list[UTurnBurnEvent]


def normalize_text(text: str) -> str:
    """Normalize text for consistent token matching."""
    t = text.lower().replace("&", " and ")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return " ".join(t.split())


def match_teams_in_order(text: str, team_names: list[str]) -> list[str]:
    """Return candidate team names matched in order of appearance in text."""
    norm_t = f" {normalize_text(text)} "
    matches: list[tuple[int, str]] = []
    for tm in team_names:
        norm_tm = normalize_text(tm)
        m = re.search(rf"\b{re.escape(norm_tm)}\b", norm_t)
        if m:
            matches.append((m.start(), tm))
        else:
            parts = [normalize_text(p) for p in re.split(r"[&/]| and ", tm)]
            if len(parts) == 2 and parts[1]:
                m2 = re.search(rf"\b{re.escape(parts[1])}\b", norm_t)
                if m2:
                    matches.append((m2.start(), tm))
    matches.sort(key=lambda x: x[0])
    seen: set[str] = set()
    ordered: list[str] = []
    for _, tm in matches:
        if tm not in seen:
            seen.add(tm)
            ordered.append(tm)
    return ordered


def resolve_user_for_victim(
    victim_team: str, user_teams: list[str], narrative: str
) -> str:
    """Resolve which U-Turn user targeted a given victim on a leg."""
    if not user_teams:
        return "Live Vote"
    if len(user_teams) == 1:
        return user_teams[0]

    norm_nar = normalize_text(narrative)
    norm_vic = normalize_text(victim_team)
    for u in user_teams:
        if u == victim_team:
            continue
        norm_u = normalize_text(u)
        pattern = (
            rf"{re.escape(norm_u)}[a-z0-9\s]{{1,50}}?u turn on\s+{re.escape(norm_vic)}"
        )
        if re.search(pattern, norm_nar):
            return u

    if victim_team in user_teams and len(user_teams) == 2:
        other = [u for u in user_teams if u != victim_team]
        if other:
            return other[0]
    return user_teams[0]


class UTurnAnalyzer:
    """Empirical model and analyzer for U-Turn lethality, burns, and retaliation."""

    def __init__(self, data_dir: Path | str = "data/processed") -> None:
        """Initialize analyzer with directory of processed dataset tables."""
        self.data_dir = Path(data_dir)
        self._leg_results_df: pd.DataFrame | None = None
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
    def leg_results_df(self) -> pd.DataFrame:
        """Cached leg_results table."""
        if self._leg_results_df is None:
            self._leg_results_df = self._load_table("leg_results")
        return self._leg_results_df

    @property
    def legs_df(self) -> pd.DataFrame:
        """Cached legs narrative table."""
        if self._legs_df is None:
            self._legs_df = self._load_table("legs")
        return self._legs_df

    @property
    def teams_df(self) -> pd.DataFrame:
        """Cached teams table."""
        if self._teams_df is None:
            self._teams_df = self._load_table("teams")
        return self._teams_df

    def _get_narrative(self, version: str, season: int, leg_number: int) -> str:
        """Retrieve narrative text for a specific leg."""
        legs = self.legs_df
        if legs.empty or "narrative" not in legs.columns:
            return ""
        sub = legs[
            (legs["version"] == version)
            & (legs["season"] == season)
            & (legs["leg_number"] == leg_number)
        ]
        if not sub.empty and pd.notna(sub.iloc[0]["narrative"]):
            return str(sub.iloc[0]["narrative"])
        return ""

    def _is_blind_leg(
        self, version: str, season: int, leg_number: int, narrative: str
    ) -> bool:
        """Determine whether a U-Turn board was Blind / Anonymous."""
        if (version, season, leg_number) in KNOWN_BLIND_LEGS:
            return True
        return bool(
            re.search(
                r"\b(?:blind(?:\s+double)?|anonymous)\s+u-turn\b",
                narrative,
                flags=re.IGNORECASE,
            )
        )

    def extract_burn_events(self, version: str = "US") -> list[UTurnBurnEvent]:
        """Extract all wasted or defensively burned U-Turn attempts on teams ahead."""
        legs = self.legs_df
        lr = self.leg_results_df
        teams = self.teams_df

        if legs.empty or lr.empty or "narrative" not in legs.columns:
            return []

        sub_legs = (
            legs
            if version.upper() == "ALL"
            else legs[legs["version"] == version.upper()]
        )
        events: list[UTurnBurnEvent] = []

        for _, r in sub_legs.iterrows():
            nar = str(r["narrative"]) if pd.notna(r["narrative"]) else ""
            if "unaffected" not in nar.lower() or "u-turn" not in nar.lower():
                continue
            if (
                "already passed" not in nar.lower()
                and "ahead of them" not in nar.lower()
            ):
                continue

            ver = str(r["version"])
            s = int(r["season"])
            l_num = int(r["leg_number"])

            s_teams = teams[(teams["version"] == ver) & (teams["season"] == s)][
                "team_name"
            ].tolist()
            sub_lr = lr[
                (lr["version"] == ver)
                & (lr["season"] == s)
                & (lr["leg_number"] == l_num)
            ]
            vics = sub_lr[
                sub_lr["raw_cell"].astype(str).str.contains("⊂", regex=False, na=False)
            ]
            users = sub_lr[
                sub_lr["raw_cell"].astype(str).str.contains("⊃", regex=False, na=False)
            ]["team_name"].tolist()

            sents = [
                sent.strip()
                for sent in re.split(r"(?<=[.!?])\s+", nar)
                if any(
                    k in sent.lower()
                    for k in ["u-turn", "already passed", "unaffected", "ahead of them"]
                )
            ]
            excerpt = " ".join(sents)

            clause = excerpt
            if "while " in excerpt:
                clause = excerpt.split("while ")[-1]
            elif len(sents) >= 2 and any(
                k in sents[1].lower() for k in ["then used", "second u-turn", "unaired"]
            ):
                clause = " ".join(sents[1:])

            m_teams = match_teams_in_order(clause, s_teams)
            burner = m_teams[0] if len(m_teams) >= 1 else "Unknown"
            target = (
                m_teams[1] if len(m_teams) >= 2 else (users[0] if users else "Unknown")
            )

            prim_vic = str(vics.iloc[0]["team_name"]) if not vics.empty else None
            prim_elim = (
                ("†" in str(vics.iloc[0]["raw_cell"])) if not vics.empty else False
            )
            is_double_board = not vics.empty
            is_defensive = is_double_board and (burner != prim_vic)

            events.append(
                UTurnBurnEvent(
                    version=ver,
                    season=s,
                    leg_number=l_num,
                    burner_team=burner,
                    target_team=target,
                    is_double_board=is_double_board,
                    is_intentional_defensive=is_defensive,
                    primary_victim=prim_vic,
                    primary_victim_eliminated=prim_elim,
                    narrative_excerpt=excerpt,
                )
            )

        return events

    def extract_instances(self, version: str = "US") -> list[UTurnInstance]:
        """Extract all U-Turn victim instances across seasons."""
        lr = self.leg_results_df
        teams = self.teams_df

        if lr.empty or "raw_cell" not in lr.columns:
            return []

        vic_mask = lr["raw_cell"].astype(str).str.contains("⊂", regex=False, na=False)
        if version.upper() != "ALL":
            vic_mask = vic_mask & (lr["version"] == version.upper())

        vic_rows = lr[vic_mask].copy()
        if vic_rows.empty:
            return []

        burn_events = self.extract_burn_events(version=version)
        burn_legs = {
            (b.version, b.season, b.leg_number)
            for b in burn_events
            if b.is_double_board
        }

        instances: list[UTurnInstance] = []
        for _, r in vic_rows.iterrows():
            ver = str(r["version"])
            s = int(r["season"])
            l_num = int(r["leg_number"])
            tm = str(r["team_name"])
            raw_cell = str(r.get("raw_cell", ""))

            leg_all = lr[
                (lr["version"] == ver)
                & (lr["season"] == s)
                & (lr["leg_number"] == l_num)
            ]
            users = leg_all[
                leg_all["raw_cell"].astype(str).str.contains("⊃", regex=False, na=False)
            ]["team_name"].tolist()
            vics_on_leg = leg_all[
                leg_all["raw_cell"].astype(str).str.contains("⊂", regex=False, na=False)
            ]

            nar = self._get_narrative(ver, s, l_num)
            is_blind = self._is_blind_leg(ver, s, l_num, nar)
            second_burned = (ver, s, l_num) in burn_legs

            if not users or "vote" in nar.lower():
                board_type = "Vote"
            elif (
                len(vics_on_leg) >= 2
                or len(users) >= 2
                or "double u-turn" in nar.lower()
                or second_burned
            ):
                board_type = "Double"
            else:
                board_type = "Single"

            user_tm = (
                "Live Vote"
                if board_type == "Vote"
                else resolve_user_for_victim(tm, users, nar)
            )
            is_chain = "⊃" in raw_cell

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

            prev_leg_match = lr[
                (lr["version"] == ver)
                & (lr["season"] == s)
                & (lr["leg_number"] == l_num - 1)
                & (lr["team_name"] == tm)
            ]
            prev_place = (
                int(prev_leg_match.iloc[0]["placement"])
                if not prev_leg_match.empty
                and pd.notna(prev_leg_match.iloc[0]["placement"])
                else None
            )

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

            place = int(r["placement"]) if pd.notna(r["placement"]) else 0
            instances.append(
                UTurnInstance(
                    version=ver,
                    season=s,
                    leg_number=l_num,
                    team_name=tm,
                    user_team=user_tm,
                    board_type=board_type,
                    is_blind=is_blind,
                    is_chain_uturn=is_chain,
                    second_slot_burned=second_burned,
                    placement=place,
                    raw_cell=raw_cell,
                    prev_placement=prev_place,
                    eliminated_on_leg=eliminated,
                    legs_survived_after=survival_lag,
                    total_legs_completed=total_completed,
                    season_max_legs=max_leg_s,
                    final_result=final_res,
                    is_leg_podium=1 <= place <= 3,
                    is_winner=final_res == 1,
                    is_podium=final_res is not None and final_res <= 3,
                    reached_finale=last_leg_team == max_leg_s,
                )
            )

        return instances

    def analyze(self, version: str = "US") -> UTurnMetrics:
        """Compute comprehensive U-Turn lethality, burn, and retaliation metrics."""
        instances = self.extract_instances(version=version)
        burn_events = self.extract_burn_events(version=version)
        n = len(instances)

        if n == 0:
            return UTurnMetrics(
                version=version,
                total_victims=0,
                eliminated_on_leg_count=0,
                eliminated_on_leg_rate=0.0,
                survived_leg_count=0,
                survived_leg_rate=0.0,
                leg_podium_count=0,
                leg_podium_rate=0.0,
                mean_placement=0.0,
                median_placement=0.0,
                placement_counts={},
                survival_lag_distribution={},
                mean_survival_lag=0.0,
                survivor_mean_survival_lag=0.0,
                median_survival_lag=0.0,
                podium_count=0,
                podium_rate=0.0,
                winner_count=0,
                winner_rate=0.0,
                finale_count=0,
                finale_rate=0.0,
                chain_uturn_count=0,
                chain_uturn_survived_count=0,
                chain_uturn_survival_rate=0.0,
                wasted_uturn_count=0,
                double_board_burn_count=0,
                double_board_burn_elim_rate=0.0,
                intentional_defensive_burn_count=0,
                intentional_defensive_burn_elim_rate=0.0,
                total_users=0,
                blind_users_count=0,
                public_users_count=0,
                blind_user_retaliation_count=0,
                blind_user_retaliation_rate=0.0,
                public_user_retaliation_count=0,
                public_user_retaliation_rate=0.0,
                blind_victim_elim_rate=0.0,
                public_victim_elim_rate=0.0,
                vote_victim_elim_rate=0.0,
                instances=[],
                burn_events=[],
            )

        elim_count = sum(1 for i in instances if i.eliminated_on_leg)
        surv_count = n - elim_count
        leg_pod_count = sum(1 for i in instances if i.is_leg_podium)

        placements = [i.placement for i in instances if i.placement > 0]
        mean_pl = float(np.mean(placements)) if placements else 0.0
        med_pl = float(np.median(placements)) if placements else 0.0

        p_counts: dict[int, int] = {}
        for p in placements:
            p_counts[p] = p_counts.get(p, 0) + 1

        lags = [i.legs_survived_after for i in instances]
        surv_lags = [
            i.legs_survived_after for i in instances if not i.eliminated_on_leg
        ]
        mean_lag = float(np.mean(lags))
        surv_mean_lag = float(np.mean(surv_lags)) if surv_lags else 0.0
        med_lag = float(np.median(lags))

        lag_dist: dict[int, int] = {}
        for lag in lags:
            lag_dist[lag] = lag_dist.get(lag, 0) + 1

        pod_count = sum(1 for i in instances if i.is_podium)
        win_count = sum(1 for i in instances if i.is_winner)
        fin_count = sum(1 for i in instances if i.reached_finale)

        # Chain U-Turns vs Defensive Burns
        chain_insts = [i for i in instances if i.is_chain_uturn]
        chain_cnt = len(chain_insts)
        chain_surv_cnt = sum(1 for i in chain_insts if not i.eliminated_on_leg)
        chain_surv_rate = chain_surv_cnt / chain_cnt if chain_cnt > 0 else 0.0

        dbl_burns = [b for b in burn_events if b.is_double_board]
        dbl_burn_cnt = len(dbl_burns)
        dbl_burn_elim_rate = (
            sum(1 for b in dbl_burns if b.primary_victim_eliminated) / dbl_burn_cnt
            if dbl_burn_cnt > 0
            else 0.0
        )

        def_burns = [b for b in burn_events if b.is_intentional_defensive]
        def_burn_cnt = len(def_burns)
        def_burn_elim_rate = (
            sum(1 for b in def_burns if b.primary_victim_eliminated) / def_burn_cnt
            if def_burn_cnt > 0
            else 0.0
        )

        # Victim elimination rates by mode (Blind vs Public vs Vote)
        blind_vics = [i for i in instances if i.board_type != "Vote" and i.is_blind]
        public_vics = [
            i for i in instances if i.board_type != "Vote" and not i.is_blind
        ]
        vote_vics = [i for i in instances if i.board_type == "Vote"]

        blind_vic_elim_rate = (
            sum(1 for i in blind_vics if i.eliminated_on_leg) / len(blind_vics)
            if blind_vics
            else 0.0
        )
        public_vic_elim_rate = (
            sum(1 for i in public_vics if i.eliminated_on_leg) / len(public_vics)
            if public_vics
            else 0.0
        )
        vote_vic_elim_rate = (
            sum(1 for i in vote_vics if i.eliminated_on_leg) / len(vote_vics)
            if vote_vics
            else 0.0
        )

        # User retaliation dynamics (⊃)
        lr = self.leg_results_df
        u_mask = lr["raw_cell"].astype(str).str.contains("⊃", regex=False, na=False)
        if version.upper() != "ALL":
            u_mask = u_mask & (lr["version"] == version.upper())
        u_rows = lr[u_mask]

        blind_u_cnt = 0
        public_u_cnt = 0
        blind_retal_cnt = 0
        public_retal_cnt = 0

        for _, ur in u_rows.iterrows():
            ver = str(ur["version"])
            s = int(ur["season"])
            l_num = int(ur["leg_number"])
            tm = str(ur["team_name"])
            nar = self._get_narrative(ver, s, l_num)
            is_b = self._is_blind_leg(ver, s, l_num, nar)

            later = lr[
                (lr["version"] == ver)
                & (lr["season"] == s)
                & (lr["leg_number"] > l_num)
                & (lr["team_name"] == tm)
            ]
            retaliated = (
                later["raw_cell"]
                .astype(str)
                .apply(lambda c: any(sym in c for sym in ["⊂", "<", "∋", "⇐"]))
                .any()
            )
            if is_b:
                blind_u_cnt += 1
                if retaliated:
                    blind_retal_cnt += 1
            else:
                public_u_cnt += 1
                if retaliated:
                    public_retal_cnt += 1

        return UTurnMetrics(
            version=version,
            total_victims=n,
            eliminated_on_leg_count=elim_count,
            eliminated_on_leg_rate=elim_count / n,
            survived_leg_count=surv_count,
            survived_leg_rate=surv_count / n,
            leg_podium_count=leg_pod_count,
            leg_podium_rate=leg_pod_count / n,
            mean_placement=mean_pl,
            median_placement=med_pl,
            placement_counts=dict(sorted(p_counts.items())),
            survival_lag_distribution=dict(sorted(lag_dist.items())),
            mean_survival_lag=mean_lag,
            survivor_mean_survival_lag=surv_mean_lag,
            median_survival_lag=med_lag,
            podium_count=pod_count,
            podium_rate=pod_count / n,
            winner_count=win_count,
            winner_rate=win_count / n,
            finale_count=fin_count,
            finale_rate=fin_count / n,
            chain_uturn_count=chain_cnt,
            chain_uturn_survived_count=chain_surv_cnt,
            chain_uturn_survival_rate=chain_surv_rate,
            wasted_uturn_count=len(burn_events),
            double_board_burn_count=dbl_burn_cnt,
            double_board_burn_elim_rate=dbl_burn_elim_rate,
            intentional_defensive_burn_count=def_burn_cnt,
            intentional_defensive_burn_elim_rate=def_burn_elim_rate,
            total_users=len(u_rows),
            blind_users_count=blind_u_cnt,
            public_users_count=public_u_cnt,
            blind_user_retaliation_count=blind_retal_cnt,
            blind_user_retaliation_rate=(
                blind_retal_cnt / blind_u_cnt if blind_u_cnt > 0 else 0.0
            ),
            public_user_retaliation_count=public_retal_cnt,
            public_user_retaliation_rate=(
                public_retal_cnt / public_u_cnt if public_u_cnt > 0 else 0.0
            ),
            blind_victim_elim_rate=blind_vic_elim_rate,
            public_victim_elim_rate=public_vic_elim_rate,
            vote_victim_elim_rate=vote_vic_elim_rate,
            instances=instances,
            burn_events=burn_events,
        )

    def to_dataframe(self, version: str = "US") -> pd.DataFrame:
        """Convert extracted U-Turn victim instances to pandas DataFrame."""
        instances = self.extract_instances(version=version)
        if not instances:
            return pd.DataFrame()
        return pd.DataFrame([asdict(i) for i in instances])

    def summary_dict(self, version: str = "US") -> dict[str, Any]:
        """Return serializable summary dictionary without nested lists."""
        metrics = self.analyze(version=version)
        data = asdict(metrics)
        data.pop("instances", None)
        data.pop("burn_events", None)
        return data
