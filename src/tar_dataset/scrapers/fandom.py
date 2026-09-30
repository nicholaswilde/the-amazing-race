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


class FandomScraper:
    """Scrapes The Amazing Race Wiki on Fandom."""

    BASE_API = "https://amazingrace.fandom.com/api.php"

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

    def scrape_all(self, start: int = 1, end: int = 36) -> list[dict[str, Any]]:
        """Scrape range of seasons sequentially."""
        results = []
        for s in range(start, end + 1):
            res = self.scrape_season(s, version=self.version)
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

    def scrape_season(
        self, season: int, version: str = "US", save: bool = True
    ) -> dict[str, Any]:
        """Scrape season from Fandom wiki."""
        title = (
            f"The_Amazing_Race_{season}"
            if version.upper() == "US"
            else f"The_Amazing_Race_Canada_{season}"
        )
        logger.info("Scraping Fandom: %s", title)

        wikitext = self.fetch_page_wikitext(title)
        if not wikitext:
            return {}

        infobox = self.parse_season_infobox(wikitext)

        season_data = {
            "version": version,
            "season": season,
            "fandom_title": title,
            "fandom_url": f"https://amazingrace.fandom.com/wiki/{title}",
            "infobox": infobox,
            "wikitext_length": len(wikitext),
        }

        if save:
            out_path = self.raw_dir / f"fandom_{version.lower()}_{season:02d}.json"
            out_path.write_text(json.dumps(season_data, indent=2), encoding="utf-8")
            logger.info("Saved Fandom season %d to %s", season, out_path)

        return season_data
