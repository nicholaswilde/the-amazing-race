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


class DatasetBuilder:
    """Compiles raw Wikipedia, Fandom, and Reddit files into clean tidy datasets."""

    def __init__(
        self,
        raw_dir: Path | str = "data/raw",
        processed_dir: Path | str = "data/processed",
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_wikipedia_seasons(self) -> list[dict[str, Any]]:
        """Load all raw Wikipedia season files."""
        wiki_dir = self.raw_dir / "wikipedia"
        if not wiki_dir.exists():
            return []

        seasons = []
        for file in sorted(wiki_dir.glob("season_*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                seasons.append(data)
            except Exception as e:
                logger.error("Failed to load %s: %s", file, e)
        return seasons

    def build_seasons_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create seasons summary dataframe."""
        cols = [
            "version", "season", "n_teams", "n_legs", "n_episodes",
            "winners", "distance_miles", "distance_km", "air_dates",
            "filming_dates", "wiki_url"
        ]
        rows = []
        for s in raw_seasons:
            info = s.get("infobox", {})
            rows.append({
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
            })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_episodes_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create episodes dataframe."""
        cols = ["version", "season", "episode", "title", "air_date", "viewers_millions"]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for ep in s.get("episodes", []):
                rows.append({
                    "version": version,
                    "season": season_num,
                    "episode": ep.get("episode"),
                    "title": ep.get("title"),
                    "air_date": ep.get("air_date"),
                    "viewers_millions": ep.get("viewers_millions"),
                })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_contestants_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create contestants demographics dataframe."""
        cols = ["version", "season", "contestant_id", "name", "age", "relationship", "hometown", "status"]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for idx, c in enumerate(s.get("contestants", []), start=1):
                name = c.get("name", "")
                rows.append({
                    "version": version,
                    "season": season_num,
                    "contestant_id": f"{version}-S{season_num:02d}-{idx:02d}",
                    "name": name,
                    "age": c.get("age"),
                    "relationship": c.get("relationship"),
                    "hometown": c.get("hometown"),
                    "status": c.get("status"),
                })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_teams_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create teams summary dataframe."""
        cols = [
            "version", "season", "team_id", "team_name", "relationship",
            "hometown", "result", "status", "legs_won", "legs_completed"
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
                active_placements = [p for p in placements if p.get("placement") is not None]
                legs_completed = len(active_placements)

                rel = None
                hometown = None
                for c in contestants:
                    c_name = c.get("name", "")
                    if any(part in c_name for part in team_name.split("&")):
                        rel = c.get("relationship")
                        hometown = c.get("hometown")
                        break

                status = "Winner" if rank == 1 else ("Runner-up" if rank in [2, 3] else "Eliminated")

                rows.append({
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
                })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_legs_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create legs dataframe with itinerary and challenge details."""
        cols = ["version", "season", "leg_number", "route_header", "itinerary_stops", "tasks_count", "narrative"]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for leg in s.get("legs", []):
                leg_num = leg.get("leg_number")
                tasks = leg.get("tasks", [])
                rows.append({
                    "version": version,
                    "season": season_num,
                    "leg_number": leg_num,
                    "route_header": leg.get("route_header"),
                    "itinerary_stops": len(leg.get("itinerary", [])),
                    "tasks_count": len(tasks),
                    "narrative": leg.get("narrative"),
                })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_leg_results_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create leg-by-leg team placement results dataframe (active legs only)."""
        cols = [
            "version", "season", "leg_number", "team_name", "placement",
            "raw_cell", "is_non_elimination", "fast_forward", "uturn",
            "yield", "speed_bump"
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for r in s.get("results", []):
                team_name = r.get("team_name")
                for p in r.get("placements", []):
                    m_leg = re.search(r"\d+", str(p.get("leg_label", "")))
                    leg_num = int(m_leg.group(0)) if m_leg else None
                    if leg_num is None:
                        continue

                    raw_cell = p.get("raw_cell")
                    placement = p.get("placement")

                    # Skip empty cells where team was already eliminated
                    if placement is None and (not raw_cell or str(raw_cell).strip() == ""):
                        continue

                    rows.append({
                        "version": version,
                        "season": season_num,
                        "leg_number": leg_num,
                        "team_name": team_name,
                        "placement": placement,
                        "raw_cell": raw_cell,
                        "is_non_elimination": p.get("is_non_elimination", False),
                        "fast_forward": p.get("fast_forward", False),
                        "uturn": p.get("uturn", False),
                        "yield": p.get("yield", False),
                        "speed_bump": p.get("speed_bump", False),
                    })
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

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
                    rows.append({
                        "version": version,
                        "season": season_num,
                        "leg_number": leg_num,
                        "task_type": t.get("task_type"),
                        "description": t.get("description"),
                    })
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

        return dfs
