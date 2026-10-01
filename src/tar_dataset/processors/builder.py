"""Processes raw scraped data into tidy relational datasets (alone-style) and Parquet/CSV formats."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert string to URL-safe alphanumeric slug."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


# Known demographic details for withdrawn/returned contestants in Season 33
KNOWN_S33_CONTESTANTS: dict[str, dict[str, Any]] = {
    "Michael Norwood": {
        "age": 36,
        "relationship": "Singing Police Officers",
        "hometown": "Buffalo, New York",
    },
    "Moe Badger": {
        "age": 42,
        "relationship": "Singing Police Officers",
        "hometown": "Buffalo, New York",
    },
    "Arun Kumar": {
        "age": 56,
        "relationship": "Father & Daughter",
        "hometown": "Detroit, Michigan",
    },
    "Natalia Kumar": {
        "age": 28,
        "relationship": "Father & Daughter",
        "hometown": "Detroit, Michigan",
    },
    "Anthony Sadler": {
        "age": 29,
        "relationship": "Childhood Friends",
        "hometown": "Sacramento, California",
    },
    "Spencer Stone": {
        "age": 29,
        "relationship": "Childhood Friends",
        "hometown": "Sacramento, California",
    },
    "Connie Greiner": {
        "age": 37,
        "relationship": "Married",
        "hometown": "Newport News, Virginia",
    },
    "Sam Greiner": {
        "age": 39,
        "relationship": "Married",
        "hometown": "Charlotte, North Carolina",
    },
}


class DatasetBuilder:
    """Compiles raw Wikipedia, Fandom, and Reddit files into clean tidy datasets."""

    def __init__(
        self,
        raw_dir: Path | str = "data/raw",
        processed_dir: Path | str = "data/processed",
        include_in_progress: bool = False,
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.include_in_progress = include_in_progress

    def load_wikipedia_seasons(self) -> list[dict[str, Any]]:
        """Load all raw Wikipedia season files."""
        wiki_dir = self.raw_dir / "wikipedia"
        if not wiki_dir.exists():
            return []

        seasons = []
        for file in sorted(wiki_dir.glob("season_*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                # Filter out in-progress seasons (where winners are not yet decided)
                # unless explicitly requested, so official tidy datasets remain complete
                if not self.include_in_progress:
                    info = data.get("infobox", {})
                    winners = info.get("winners")
                    if not winners or "TBD" in str(winners):
                        logger.info(
                            "Skipping in-progress Season %s from official tidy build (winners pending)",
                            data.get("season"),
                        )
                        continue
                seasons.append(data)
            except Exception as e:
                logger.error("Failed to load %s: %s", file, e)
        return seasons

    def build_seasons_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create seasons summary dataframe."""
        cols = [
            "version",
            "season",
            "n_teams",
            "n_legs",
            "n_episodes",
            "winners",
            "distance_miles",
            "distance_km",
            "air_dates",
            "filming_dates",
            "wiki_url",
        ]
        rows = []
        for s in raw_seasons:
            info = s.get("infobox", {})
            rows.append(
                {
                    "version": s.get("version", "US"),
                    "season": s.get("season"),
                    "n_teams": info.get("n_teams"),
                    "n_legs": info.get("n_legs"),
                    "n_episodes": info.get("n_episodes"),
                    "winners": info.get("winners"),
                    "distance_miles": info.get("distance_miles"),
                    "distance_km": info.get("distance_km"),
                    "air_dates": info.get("air_dates"),
                    "filming_dates": info.get("filming_dates"),
                    "wiki_url": s.get("wiki_url"),
                }
            )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_episodes_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create episodes dataframe with backfilled air dates."""
        cols = ["version", "season", "episode", "title", "air_date", "viewers_millions"]
        rows = []

        # Load master episodes lookup if present
        master_episodes: dict[str, Any] = {}
        master_path = self.raw_dir / "wikipedia" / "episodes_master.json"
        if master_path.exists():
            try:
                master_episodes = json.loads(master_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Could not read episodes_master.json: %s", e)

        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for ep in s.get("episodes", []):
                ep_num = ep.get("episode")
                if ep_num is None or pd.isna(ep_num):
                    continue
                ep_num = int(ep_num)
                title = ep.get("title")
                air_date = ep.get("air_date")
                viewers = ep.get("viewers_millions")

                # Fallback to master episode catalogue if air date is missing
                if not air_date and season_num is not None:
                    key = f"{season_num}_{ep_num}"
                    if key in master_episodes:
                        air_date = master_episodes[key].get("air_date")
                        if viewers is None:
                            viewers = master_episodes[key].get("viewers_millions")

                # Fallback to known industry ratings databases (The TV Ratings Guide, USTVDB)
                known_viewership = {
                    ("US", 38, 10): 2.56,
                    ("US", 38, 11): 2.61,
                    ("US", 38, 12): 2.81,
                }
                if (viewers is None or pd.isna(viewers)) and (
                    version,
                    season_num,
                    ep_num,
                ) in known_viewership:
                    viewers = known_viewership[(version, season_num, ep_num)]

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "episode": ep_num,
                        "title": title,
                        "air_date": air_date,
                        "viewers_millions": viewers,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_contestants_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create contestants demographics dataframe with backfilled data."""
        cols = [
            "version",
            "season",
            "contestant_id",
            "name",
            "age",
            "relationship",
            "hometown",
            "status",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for idx, c in enumerate(s.get("contestants", []), start=1):
                name = c.get("name", "")
                age = c.get("age")
                rel = c.get("relationship")
                hometown = c.get("hometown")
                status = c.get("status")

                # Season 29: contestants were strangers paired at starting line
                if season_num == 29 and (not rel or pd.isna(rel)):
                    rel = "Strangers (Paired at Starting Line)"

                # Season 33: backfill missing demographic fields for withdrawn/returned contestants
                if season_num == 33 and (age is None or pd.isna(age)):
                    if name in KNOWN_S33_CONTESTANTS:
                        age = KNOWN_S33_CONTESTANTS[name]["age"]
                        if not rel or rel == "Returned to competition":
                            rel = KNOWN_S33_CONTESTANTS[name]["relationship"]
                        if not hometown or hometown == "Returned to competition":
                            hometown = KNOWN_S33_CONTESTANTS[name]["hometown"]
                    else:
                        for other in s.get("contestants", []):
                            if (
                                other.get("name") == name
                                and other.get("age") is not None
                            ):
                                age = other.get("age")
                                if not rel or rel == "Returned to competition":
                                    rel = other.get("relationship")
                                if (
                                    not hometown
                                    or hometown == "Returned to competition"
                                ):
                                    hometown = other.get("hometown")
                                break

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "contestant_id": f"{version}-S{season_num:02d}-{idx:02d}",
                        "name": name,
                        "age": age,
                        "relationship": rel,
                        "hometown": hometown,
                        "status": status,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_teams_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create teams summary dataframe with resolved relationships and hometowns."""
        cols = [
            "version",
            "season",
            "team_id",
            "team_name",
            "relationship",
            "hometown",
            "result",
            "status",
            "legs_won",
            "legs_completed",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            results = s.get("results", [])
            contestants = s.get("contestants", [])

            for rank, r in enumerate(results, start=1):
                team_name = r.get("team_name", "")
                team_id = f"{version}-S{season_num:02d}-{slugify(team_name)}"
                placements = r.get("placements", [])

                legs_won = sum(1 for p in placements if p.get("placement") == 1)
                active_placements = [
                    p for p in placements if p.get("placement") is not None
                ]
                legs_completed = len(active_placements)

                rel = None
                hometown = None

                # Season 8 (Family Edition): 4-member families
                if season_num == 8:
                    rel = "Family Team (4 members)"
                    fam_name = team_name.replace(" Family", "").strip()
                    for c in contestants:
                        c_name = c.get("name", "")
                        if fam_name.lower() in c_name.lower():
                            hometown = c.get("hometown")
                            break
                elif season_num == 29:
                    rel = "Strangers (Paired at Starting Line)"
                    # Match hometown from contestants
                    parts = [
                        p.strip().strip("\"'")
                        for p in team_name.split("&")
                        if p.strip()
                    ]
                    for c in contestants:
                        c_name = c.get("name", "").replace('"', "").replace("'", "")
                        if any(p.lower() in c_name.lower() for p in parts):
                            hometown = c.get("hometown")
                            break
                else:
                    # Match returnee/standard teams by nickname or contestant name tokens
                    parts = [
                        p.strip().strip("\"'")
                        for p in team_name.split("&")
                        if p.strip()
                    ]
                    for c in contestants:
                        c_name = c.get("name", "").replace('"', "").replace("'", "")
                        if any(p.lower() in c_name.lower() for p in parts):
                            rel = c.get("relationship")
                            hometown = c.get("hometown")
                            break

                status = (
                    "Winner"
                    if rank == 1
                    else ("Runner-up" if rank in [2, 3] else "Eliminated")
                )

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "team_id": team_id,
                        "team_name": team_name,
                        "relationship": rel,
                        "hometown": hometown,
                        "result": rank,
                        "status": status,
                        "legs_won": legs_won,
                        "legs_completed": legs_completed,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_legs_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create legs dataframe with itinerary and challenge details."""
        cols = [
            "version",
            "season",
            "leg_number",
            "route_header",
            "itinerary_stops",
            "tasks_count",
            "narrative",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for leg in s.get("legs", []):
                leg_num = leg.get("leg_number")
                tasks = leg.get("tasks", [])
                itinerary = leg.get("itinerary", [])
                narrative = leg.get("narrative") or ""

                # Distinguish route stops from narrative sentences in itinerary
                route_stops = []
                narrative_parts = []
                for item in itinerary:
                    item_str = str(item).strip()
                    if item_str.startswith(
                        ("Episode ", "Eliminated:", "Prize:", "Winners:", "Runners-up:")
                    ):
                        continue
                    if (
                        len(item_str) > 60
                        and any(
                            item_str.endswith(punct) for punct in [".", "!", '"', "'"]
                        )
                    ) or (
                        any(
                            item_str.startswith(p)
                            for p in [
                                "Teams ",
                                "At ",
                                "After ",
                                "Once ",
                                "When ",
                                "In ",
                                "The ",
                                "Upon ",
                            ]
                        )
                        and len(item_str) > 40
                    ):
                        narrative_parts.append(item_str)
                    else:
                        route_stops.append(item_str)

                if not narrative.strip():
                    if narrative_parts:
                        narrative = " ".join(narrative_parts)
                    elif tasks:
                        narrative = " ".join(
                            t["description"]
                            for t in tasks
                            if len(t.get("description", "")) > 40
                        )

                itinerary_stops_count = (
                    len(route_stops) if route_stops else len(itinerary)
                )

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "leg_number": leg_num,
                        "route_header": leg.get("route_header"),
                        "itinerary_stops": itinerary_stops_count,
                        "tasks_count": len(tasks),
                        "narrative": narrative.strip() if narrative else None,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_leg_results_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create leg-by-leg team placement results dataframe (active legs only)."""
        cols = [
            "version",
            "season",
            "leg_number",
            "team_name",
            "placement",
            "raw_cell",
            "is_non_elimination",
            "fast_forward",
            "uturn",
            "yield",
            "speed_bump",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            results = s.get("results", [])
            for r in results:
                team_name = r.get("team_name")
                for p in r.get("placements", []):
                    m_leg = re.search(r"\d+", str(p.get("leg_label", "")))
                    leg_num = int(m_leg.group(0)) if m_leg else None
                    if leg_num is None:
                        continue

                    raw_cell = p.get("raw_cell")
                    placement = p.get("placement")

                    # Skip empty cells where team was already eliminated
                    if placement is None and (
                        not raw_cell or str(raw_cell).strip() == ""
                    ):
                        continue

                    # Handle off-mat withdrawals / eliminations (e.g. S22 Leg 5 Dave & Connor, S34 Leg 5 Abby & Will marked with †)
                    if placement is None and raw_cell and "†" in str(raw_cell):
                        active_count = sum(
                            1
                            for other_r in results
                            for other_p in other_r.get("placements", [])
                            if other_p.get("leg_label") == p.get("leg_label")
                            and (
                                other_p.get("placement") is not None
                                or (
                                    other_p.get("raw_cell")
                                    and str(other_p.get("raw_cell")).strip() != ""
                                )
                            )
                        )
                        placement = active_count if active_count > 0 else 8

                    rows.append(
                        {
                            "version": version,
                            "season": season_num,
                            "leg_number": leg_num,
                            "team_name": team_name,
                            "placement": int(placement)
                            if placement is not None
                            else None,
                            "raw_cell": raw_cell,
                            "is_non_elimination": p.get("is_non_elimination", False),
                            "fast_forward": p.get("fast_forward", False),
                            "uturn": p.get("uturn", False),
                            "yield": p.get("yield", False),
                            "speed_bump": p.get("speed_bump", False),
                        }
                    )
        df = pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)
        if (
            not df.empty
            and "placement" in df.columns
            and not df["placement"].isna().any()
        ):
            df["placement"] = df["placement"].astype(int)
        return df

    def build_tasks_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create tasks and challenges dataframe."""
        cols = ["version", "season", "leg_number", "task_type", "description"]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for leg in s.get("legs", []):
                leg_num = leg.get("leg_number")
                for t in leg.get("tasks", []):
                    rows.append(
                        {
                            "version": version,
                            "season": season_num,
                            "leg_number": leg_num,
                            "task_type": t.get("task_type"),
                            "description": t.get("description"),
                        }
                    )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_all(self) -> dict[str, pd.DataFrame]:
        """Compile all tidy datasets, saving CSV and Parquet copies."""
        raw_seasons = self.load_wikipedia_seasons()
        if not raw_seasons:
            logger.warning("No raw Wikipedia seasons found to build.")
            return {}

        dfs = {
            "seasons": self.build_seasons_df(raw_seasons),
            "episodes": self.build_episodes_df(raw_seasons),
            "contestants": self.build_contestants_df(raw_seasons),
            "teams": self.build_teams_df(raw_seasons),
            "legs": self.build_legs_df(raw_seasons),
            "leg_results": self.build_leg_results_df(raw_seasons),
            "tasks": self.build_tasks_df(raw_seasons),
        }

        for name, df in dfs.items():
            csv_path = self.processed_dir / f"{name}.csv"
            parquet_path = self.processed_dir / f"{name}.parquet"
            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)
            logger.info("Saved %s: %d records -> %s", name, len(df), csv_path)

        try:
            from tar_dataset.exports.sqlite_export import export_to_sqlite

            export_to_sqlite(processed_dir=self.processed_dir)
        except Exception as e:
            logger.warning("Could not automatically update SQLite database: %s", e)

        return dfs
