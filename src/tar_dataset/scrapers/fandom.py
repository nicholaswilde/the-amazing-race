"""Fandom Wiki scraper for The Amazing Race (amazingrace.fandom.com).

Extracts wikitext metadata, route markers, trivia, pit stop times, and clues.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def clean_wikitext(text: str) -> str:
    """Clean wikitext markup (links, templates, references)."""
    if not text:
        return ""
    # Strip references <ref>...</ref>
    text = re.sub(r"<ref.*?(?:/>|</ref>)", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Strip templates {{...}} or convert simple ones
    text = re.sub(r"\{\{wp\|([^|]+)(?:\|([^}]+))?\}\}", r"\2", text)
    text = re.sub(r"\{\{ver\|([^}]+)\}\}", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    # Convert internal links [[Target|Display]] -> Display, [[Target]] -> Target
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # Clean whitespace
    return re.sub(r"\s+", " ", text).strip()


def compute_roadblock_equity(split_str: str | None) -> float | None:
    """Compute normalized partner balance ratio from roadblock split string (e.g. '6-6' -> 1.0)."""
    if not split_str or not isinstance(split_str, str):
        return None
    try:
        parts = [int(p) for p in split_str.split("-")]
        total = sum(parts)
        if total == 0:
            return None
        if len(parts) == 2:
            a, b = parts
            return round(1.0 - abs(a - b) / total, 2)
        else:
            mean = total / len(parts)
            mad = sum(abs(p - mean) for p in parts)
            max_mad = 2.0 * total * (len(parts) - 1) / len(parts)
            return round(1.0 - (mad / max_mad), 2) if max_mad > 0 else 1.0
    except Exception:
        return None


class FandomScraper:
    """Scrapes The Amazing Race Wiki on Fandom."""

    BASE_API = "https://amazingrace.fandom.com/api.php"
    compute_roadblock_equity = staticmethod(compute_roadblock_equity)

    def __init__(
        self, raw_dir: Path | str = "data/raw/fandom", version: str = "US"
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.version = version
        self.client = httpx.Client(
            headers={
                "User-Agent": "TheAmazingRaceDataset/1.0 (https://github.com/nicholaswilde/the-amazing-race)"
            },
            timeout=30.0,
        )

    def scrape_all(
        self, start: int = 1, end: int = 36, version: str | None = None
    ) -> list[dict[str, Any]]:
        """Scrape range of seasons sequentially."""
        ver = version or self.version
        results = []
        for s in range(start, end + 1):
            res = self.scrape_season(s, version=ver)
            if res:
                results.append(res)
        return results

    def fetch_page_wikitext(self, title: str) -> str | None:
        """Fetch raw wikitext of a page using Fandom's MediaWiki API."""
        params = {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
            "redirects": "1",
        }
        try:
            resp = self.client.get(self.BASE_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error("Fandom API error for %s: %s", title, data["error"])
                return None
            return data["parse"]["wikitext"]["*"]
        except Exception as exc:
            logger.error("Failed to fetch Fandom page %s: %s", title, exc)
            return None

    def parse_season_infobox(self, wikitext: str) -> dict[str, Any]:
        """Parse the {{Season ...}} wikitext template into structured key-values."""
        info: dict[str, Any] = {}
        # Find {{Season ... \n}}
        m = re.search(
            r"\{\{Season\s*(.*?)\n\s*\}\}", wikitext, re.DOTALL | re.IGNORECASE
        )
        if not m:
            return info

        body = m.group(1)
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("|") and "=" in line:
                key, val = line[1:].split("=", 1)
                k = key.strip().lower()
                v = clean_wikitext(val.strip())
                if k == "continentsvisited" and v.isdigit():
                    info["continents_visited"] = int(v)
                elif k == "countriesvisited" and v.isdigit():
                    info["countries_visited"] = int(v)
                elif k == "citiesvisited" and v.isdigit():
                    info["cities_visited"] = int(v)
                elif k == "distance":
                    info["distance_str"] = v
                elif k == "startingline":
                    info["starting_line"] = v
                elif k == "finishline":
                    info["finish_line"] = v
                elif k == "filmingdates":
                    info["filming_dates"] = v
                elif k == "airdates":
                    info["air_dates"] = v
                elif k == "winners":
                    info["winners"] = v
                elif k == "runnersup" or k == "runners-up":
                    info["runners_up"] = v

        return info

    def get_page_title(self, season: int, version: str = "US") -> str:
        """Get Fandom page title for given season and franchise."""
        ver = version.upper()
        if ver == "US":
            return f"The_Amazing_Race_{season}"
        elif ver == "CAN":
            return f"The_Amazing_Race_Canada_{season}"
        elif ver == "AUS":
            return f"The_Amazing_Race_Australia_{season}"
        return f"The_Amazing_Race_{season}"

    def scrape_season(
        self, season: int, version: str = "US", save: bool = True
    ) -> dict[str, Any]:
        """Scrape season from Fandom wiki."""
        ver = version or self.version
        title = self.get_page_title(season, version=ver)
        logger.info("Scraping Fandom: %s", title)

        wikitext = self.fetch_page_wikitext(title)
        if not wikitext:
            return {}

        infobox = self.parse_season_infobox(wikitext)

        season_data = {
            "version": ver,
            "season": season,
            "fandom_title": title,
            "fandom_url": f"https://amazingrace.fandom.com/wiki/{title}",
            "infobox": infobox,
            "wikitext_length": len(wikitext),
        }

        if save:
            out_path = self.raw_dir / f"fandom_{ver.lower()}_{season:02d}.json"
            out_path.write_text(json.dumps(season_data, indent=2), encoding="utf-8")
            logger.info("Saved Fandom season %d to %s", season, out_path)

        return season_data

    def scrape_roadblocks(
        self, start: int = 1, end: int = 36, save: bool = True
    ) -> dict[str, Any]:
        """Scrape roadblock splits from leaderboards and leg performers from episode pages."""
        import asyncio
        from collections import defaultdict

        def clean_team_name(t: str) -> str:
            t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", t)
            t = re.sub(r"\{\{[^}]+\}\}", "", t)
            t = re.sub(r"<[^>]+>", "", t)
            t = t.replace("'''", "").strip()
            return t

        def clean_team_norm(n: str) -> str:
            n = re.sub(r'".*?"', "", str(n))
            return re.sub(r"[^a-z0-9]", "", n.lower())

        def clean_name_norm(n: str) -> str:
            n = re.sub(r'".*?"', "", str(n))
            n = re.sub(r"\(.*?\)", "", n)
            return re.sub(r"[^a-z0-9]", "", n.lower())

        def extract_split(cell: str) -> str | None:
            m = re.search(r"(\d+(?:-\d+)+)", cell)
            return m.group(1) if m else None

        async def fetch_wikitext(
            client: httpx.AsyncClient, title: str, sem: asyncio.Semaphore
        ) -> tuple[str, str | None]:
            async with sem:
                params = {
                    "action": "parse",
                    "page": title,
                    "prop": "wikitext",
                    "format": "json",
                    "redirects": "1",
                }
                try:
                    r = await client.get(self.BASE_API, params=params, timeout=30.0)
                    data = r.json()
                    if "parse" in data and "wikitext" in data["parse"]:
                        return title, data["parse"]["wikitext"]["*"]
                except Exception as exc:
                    logger.debug("Failed to fetch %s: %s", title, exc)
                return title, None

        async def _run() -> dict[str, Any]:
            sem = asyncio.Semaphore(15)
            headers = {
                "User-Agent": "TheAmazingRaceDataset/1.0 (https://github.com/nicholaswilde/the-amazing-race)"
            }
            async with httpx.AsyncClient(headers=headers) as client:
                _, wt_template = await fetch_wikitext(client, "Template:Ep", sem)
                season_tasks = [
                    fetch_wikitext(client, f"The_Amazing_Race_{s}", sem)
                    for s in range(start, end + 1)
                ]
                season_results = await asyncio.gather(*season_tasks)

                episodes: list[tuple[int, int, str]] = []
                if wt_template:
                    for s in range(start, end + 1):
                        prefix = f"{s:02d}"
                        pattern = r"\|\s*" + prefix + r"(\d\d)\s*=\s*\[\[([^\]]+)\]\]"
                        for ep_num, title in re.findall(pattern, wt_template):
                            episodes.append((s, int(ep_num), title))

                ep_tasks = [
                    fetch_wikitext(client, title, sem) for _, _, title in episodes
                ]
                ep_results = await asyncio.gather(*ep_tasks)

            # Process season leaderboards
            team_splits: dict[str, dict[str, Any]] = {}
            for s, (title, wt) in zip(range(start, end + 1), season_results):
                if not wt:
                    continue
                m = re.search(r"==Leaderboard==.*?({\|[^\n]*\n.*?\n\|})", wt, re.DOTALL)
                if m:
                    for row in m.group(1).split("|-"):
                        m_team = re.search(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", row)
                        if m_team:
                            team = clean_team_name(m_team.group(1))
                            cells = [c.strip() for c in row.split("\n|") if c.strip()]
                            for c in reversed(cells):
                                sp = extract_split(c)
                                if sp:
                                    eq = self.compute_roadblock_equity(sp)
                                    key = f"{self.version}_{s}_{team}"
                                    team_splits[key] = {"split": sp, "equity_score": eq}
                                    team_splits[
                                        f"{self.version}_{s}_{clean_team_norm(team)}"
                                    ] = {"split": sp, "equity_score": eq}
                                    break
                if s == 8:
                    team_splits[f"{self.version}_8_Black Family"] = {
                        "split": "0-0-0-0",
                        "equity_score": 1.0,
                    }
                    team_splits[f"{self.version}_8_blackfamily"] = {
                        "split": "0-0-0-0",
                        "equity_score": 1.0,
                    }

            # Process episode performers
            leg_performers: dict[str, str] = {}
            leg_task_performers: dict[str, list[str]] = defaultdict(list)
            contestant_counts: dict[str, int] = defaultdict(int)

            for (s, ep_num, title), (_, wt) in zip(episodes, ep_results):
                if not wt:
                    continue
                pattern = r"\*\s*\[\[([^|\]]+)\|(.*?)\]\]"
                for team, display in re.findall(pattern, wt):
                    if "<u>" in display:
                        m_perf = re.search(r"<u>\s*([^<]+?)\s*</u>", display)
                        if m_perf:
                            c_team = clean_team_norm(clean_team_name(team))
                            perf = clean_team_name(m_perf.group(1))
                            leg_performers[f"{s}_{ep_num}_{c_team}"] = perf
                            leg_task_performers[f"{s}_{ep_num}"].append(perf)
                            contestant_counts[f"{s}_{clean_name_norm(perf)}"] += 1

            master_data = {
                "team_splits": team_splits,
                "leg_performers": leg_performers,
                "leg_task_performers": dict(leg_task_performers),
                "contestant_counts": dict(contestant_counts),
            }

            if save:
                out_path = self.raw_dir / "roadblocks_master.json"
                out_path.write_text(json.dumps(master_data, indent=2), encoding="utf-8")
                logger.info("Saved master Roadblock data to %s", out_path)

            return master_data

        try:
            return asyncio.run(_run())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_run())
