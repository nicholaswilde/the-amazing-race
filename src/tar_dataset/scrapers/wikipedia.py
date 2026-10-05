"""Wikipedia scraper for The Amazing Race.

Extracts season infoboxes, contestant demographics, race results matrices,
leg itineraries/summaries, challenges (Detours/Roadblocks), and episode viewership.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Strip wikipedia citations [1], [a], non-breaking spaces, and extra whitespace."""
    if not text:
        return ""
    # Remove citations like [1], [note 1], [49]
    cleaned = re.sub(r"\[\s*[\w\s\d]+\s*\]", "", text)
    # Replace non-breaking spaces and collapse whitespace
    cleaned = cleaned.replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_html_table(table: BeautifulSoup) -> list[list[str]]:
    """Parse HTML table with full support for rowspan and colspan cell expansion."""
    grid: list[list[tuple[str, int, int]]] = []
    for tr in table.find_all("tr"):
        row: list[tuple[str, int, int]] = []
        for cell in tr.find_all(["td", "th"]):
            text = clean_text(cell.get_text(" ", strip=True))
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            row.append((text, rowspan, colspan))
        if row:
            grid.append(row)

    expanded: list[list[str]] = []
    spans: dict[int, tuple[str, int]] = {}

    for row in grid:
        expanded_row: list[str] = []
        col_idx = 0
        cell_iter = iter(row)

        while True:
            if col_idx in spans:
                text, rem = spans[col_idx]
                expanded_row.append(text)
                if rem <= 1:
                    del spans[col_idx]
                else:
                    spans[col_idx] = (text, rem - 1)
                col_idx += 1
                continue

            try:
                text, rowspan, colspan = next(cell_iter)
            except StopIteration:
                break

            for _ in range(colspan):
                expanded_row.append(text)
                if rowspan > 1:
                    spans[col_idx] = (text, rowspan - 1)
                col_idx += 1

        expanded.append(expanded_row)

    return expanded


class WikipediaScraper:
    """Scrapes The Amazing Race seasons, results, and recaps from Wikipedia."""

    BASE_API = "https://en.wikipedia.org/w/api.php"

    def __init__(
        self, raw_dir: Path | str = "data/raw/wikipedia", version: str = "US"
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

    def get_page_title(self, season: int, version: str = "US") -> str:
        """Get Wikipedia page title for given season and franchise."""
        if version.upper() == "US":
            return f"The_Amazing_Race_{season}"
        elif version.upper() == "CAN":
            return f"The_Amazing_Race_Canada_{season}"
        elif version.upper() == "AUS":
            return f"The_Amazing_Race_Australia_{season}"
        return f"The_Amazing_Race_{season}"

    def get_latest_revision(
        self, season: int, version: str = "US"
    ) -> dict[str, Any] | None:
        """Fetch latest revision metadata (revid, timestamp) for a season page without fetching HTML."""
        title = self.get_page_title(season, version)
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "ids|timestamp",
            "format": "json",
            "redirects": "1",
        }
        try:
            resp = self.client.get(self.BASE_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if "missing" in page:
                    return None
                revs = page.get("revisions", [])
                if revs:
                    return {
                        "revid": revs[0].get("revid"),
                        "parentid": revs[0].get("parentid"),
                        "timestamp": revs[0].get("timestamp"),
                    }
            return None
        except Exception as exc:
            logger.debug("Failed to fetch revision info for %s: %s", title, exc)
            return None

    def fetch_page_html(self, title: str) -> str | None:
        """Fetch parsed page HTML from Wikipedia MediaWiki API."""
        params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json",
            "redirects": "1",
        }
        try:
            resp = self.client.get(self.BASE_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error("Wikipedia API error for %s: %s", title, data["error"])
                return None
            return data["parse"]["text"]["*"]
        except Exception as exc:
            logger.error("Failed to fetch Wikipedia page %s: %s", title, exc)
            return None

    def parse_infobox(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract metadata from the Wikipedia season infobox."""
        infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
        data: dict[str, Any] = {}
        if not infobox:
            return data

        for tr in infobox.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td:
                key = clean_text(th.get_text()).lower()
                val = clean_text(td.get_text())
                if "teams" in key:
                    data["n_teams"] = (
                        int(re.search(r"\d+", val).group(0))
                        if re.search(r"\d+", val)
                        else None
                    )
                elif "winner" in key:
                    data["winners"] = val
                elif "legs" in key:
                    data["n_legs"] = (
                        int(re.search(r"\d+", val).group(0))
                        if re.search(r"\d+", val)
                        else None
                    )
                elif "distance" in key:
                    data["distance_raw"] = val
                    m_mi = re.search(r"([\d,]+)\s*(?:mi|miles)", val, re.IGNORECASE)
                    m_km = re.search(
                        r"([\d,]+)\s*(?:km|kilometers)", val, re.IGNORECASE
                    )
                    if m_mi:
                        data["distance_miles"] = float(m_mi.group(1).replace(",", ""))
                    if m_km:
                        data["distance_km"] = float(m_km.group(1).replace(",", ""))
                elif "episodes" in key:
                    data["n_episodes"] = (
                        int(re.search(r"\d+", val).group(0))
                        if re.search(r"\d+", val)
                        else None
                    )
                elif "filming" in key:
                    data["filming_dates"] = val
                elif "release" in key or "broadcast" in key:
                    data["air_dates"] = val

        return data

    def parse_contestants_table(self, table: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse contestants table with names, ages, relationships, and hometowns."""
        expanded = parse_html_table(table)
        if not expanded or len(expanded) < 2:
            return []

        header = [h.lower() for h in expanded[0]]
        # Find column indices
        name_idx = next(
            (
                i
                for i, h in enumerate(header)
                if "contestant" in h or "name" in h or "racer" in h
            ),
            0,
        )
        age_idx = next((i for i, h in enumerate(header) if "age" in h), None)
        rel_idx = next(
            (i for i, h in enumerate(header) if "relationship" in h or "subtitle" in h),
            None,
        )
        home_idx = next(
            (i for i, h in enumerate(header) if "hometown" in h or "residence" in h),
            None,
        )
        status_idx = next(
            (i for i, h in enumerate(header) if "status" in h or "finish" in h), None
        )

        contestants: list[dict[str, Any]] = []
        for row in expanded[1:]:
            if len(row) <= name_idx:
                continue
            name = row[name_idx]
            if not name or "team" in name.lower() or "contestant" in name.lower():
                continue

            entry: dict[str, Any] = {
                "name": name,
                "age": int(row[age_idx])
                if age_idx is not None and row[age_idx].isdigit()
                else None,
                "relationship": row[rel_idx]
                if rel_idx is not None and rel_idx < len(row)
                else None,
                "hometown": row[home_idx]
                if home_idx is not None and home_idx < len(row)
                else None,
                "status": row[status_idx]
                if status_idx is not None and status_idx < len(row)
                else None,
            }
            contestants.append(entry)

        return contestants

    def parse_results_table(self, table: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse season results matrix (placements by leg)."""
        expanded = parse_html_table(table)
        if not expanded or len(expanded) < 2:
            return []

        header = expanded[0]
        # Identify team column and leg columns
        team_idx = next((i for i, h in enumerate(header) if "team" in h.lower()), 0)
        leg_cols: list[tuple[int, str]] = []
        for i, h in enumerate(header):
            if i != team_idx and (
                h.isdigit() or "leg" in h.lower() or re.match(r"^\d+", h)
            ):
                leg_cols.append((i, h))

        results: list[dict[str, Any]] = []
        for row in expanded[1:]:
            if len(row) <= team_idx:
                continue
            team_name = row[team_idx]
            if (
                not team_name
                or "notes" in team_name.lower()
                or "repeat" in team_name.lower()
            ):
                continue

            leg_placements: list[dict[str, Any]] = []
            for col_idx, leg_label in leg_cols:
                if col_idx < len(row):
                    cell = row[col_idx]
                    # Parse placement number (e.g. "1st", "2nd", "3rd", "1st ƒ", "10th»")
                    m = re.search(r"(\d+)(?:st|nd|rd|th)?", cell)
                    placement = int(m.group(1)) if m else None

                    # Parse special symbols
                    is_nel = "nel" in cell.lower() or "blue" in cell.lower()
                    has_fast_forward = "ƒ" in cell or "ff" in cell.lower()
                    has_uturn = "»" in cell or "«" in cell or "u-turn" in cell.lower()
                    has_yield = "»" in cell or "yield" in cell.lower()
                    has_speed_bump = (
                        "speed bump" in cell.lower() or "sb" in cell.lower()
                    )

                    leg_placements.append(
                        {
                            "leg_label": leg_label,
                            "raw_cell": cell,
                            "placement": placement,
                            "is_non_elimination": is_nel,
                            "fast_forward": has_fast_forward,
                            "uturn": has_uturn,
                            "yield": has_yield,
                            "speed_bump": has_speed_bump,
                        }
                    )

            results.append(
                {
                    "team_name": team_name,
                    "placements": leg_placements,
                }
            )

        return results

    def parse_episodes_table(self, table: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse episodes table with titles, air dates, viewers, ratings."""
        expanded = parse_html_table(table)
        if not expanded or len(expanded) < 2:
            return []

        header = [h.lower() for h in expanded[0]]
        num_idx = next(
            (i for i, h in enumerate(header) if "in season" in h or "no." in h), 0
        )
        title_idx = next((i for i, h in enumerate(header) if "title" in h), 1)
        air_idx = next(
            (i for i, h in enumerate(header) if "air date" in h or "release date" in h),
            None,
        )
        viewer_idx = next((i for i, h in enumerate(header) if "viewer" in h), None)

        episodes: list[dict[str, Any]] = []
        for row in expanded[1:]:
            if len(row) <= title_idx:
                continue
            title = row[title_idx].strip('"').strip("'")
            if not title:
                continue

            num_str = row[num_idx] if num_idx < len(row) else ""
            m_num = re.search(r"\d+", num_str)
            ep_num = int(m_num.group(0)) if m_num else None
            if ep_num is None or title.lower() in {
                "title",
                "episode",
                "airdate",
                "air date",
                "rating",
                "#",
            }:
                continue

            air_date = (
                row[air_idx] if air_idx is not None and air_idx < len(row) else None
            )
            # Extract standard date if possible
            if air_date:
                m_date = re.search(r"(\d{4}-\d{2}-\d{2})", air_date)
                if m_date:
                    air_date = m_date.group(1)

            viewers = None
            if viewer_idx is not None and viewer_idx < len(row):
                m_view = re.search(r"([\d.]+)", row[viewer_idx])
                if m_view:
                    try:
                        viewers = float(m_view.group(1))
                    except ValueError:
                        pass

            episodes.append(
                {
                    "episode": ep_num,
                    "title": title,
                    "air_date": air_date,
                    "viewers_millions": viewers,
                    "raw_row": row,
                }
            )

        return episodes

    def parse_legs_summary(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract leg route descriptions, challenges, Detours, and Roadblocks."""
        legs: list[dict[str, Any]] = []

        # Wikipedia organizes sections with headings like 'Leg 1 (Country -> Country)'
        heading_divs = soup.find_all("div", class_=lambda c: c and "mw-heading" in c)
        for h_div in heading_divs:
            heading = h_div.find(["h3", "h4"])
            if not heading:
                continue
            text = heading.get_text(strip=True)
            m = re.search(r"Leg\s+(\d+)(?:\s*\((.*?)\))?", text, re.IGNORECASE)
            if not m:
                continue

            leg_num = int(m.group(1))
            route_str = m.group(2) or ""

            # Collect subsequent paragraphs and lists until next heading
            paragraphs: list[str] = []
            itinerary: list[str] = []
            tasks: list[dict[str, Any]] = []

            curr = h_div.find_next_sibling()
            while curr and not (
                curr.name == "div" and "mw-heading" in curr.get("class", [])
            ):
                if curr.name == "p":
                    p_text = clean_text(curr.get_text())
                    if p_text:
                        paragraphs.append(p_text)
                elif curr.name == "ul":
                    for li in curr.find_all("li", recursive=False):
                        li_text = clean_text(li.get_text())
                        if li_text.startswith(
                            (
                                "Episode ",
                                "Eliminated:",
                                "Prize:",
                                "Winners:",
                                "Runners-up:",
                            )
                        ):
                            continue
                        if any(
                            k in li_text.lower()
                            for k in [
                                "roadblock",
                                "detour",
                                "fast forward",
                                "speed bump",
                            ]
                        ):
                            # Extract task
                            task_type = "Task"
                            if "roadblock" in li_text.lower():
                                task_type = "Roadblock"
                            elif "detour" in li_text.lower():
                                task_type = "Detour"
                            elif "fast forward" in li_text.lower():
                                task_type = "Fast Forward"
                            elif "speed bump" in li_text.lower():
                                task_type = "Speed Bump"
                            tasks.append(
                                {
                                    "task_type": task_type,
                                    "description": li_text,
                                }
                            )
                        elif (
                            len(li_text) > 60
                            and any(li_text.endswith(p) for p in [".", "!", '"', "'"])
                        ) or (
                            any(
                                li_text.startswith(p)
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
                            and len(li_text) > 40
                        ):
                            paragraphs.append(li_text)
                        else:
                            itinerary.append(li_text)
                curr = curr.find_next_sibling()

            # Fallback to task descriptions for narrative if none found
            if not paragraphs and tasks:
                paragraphs = [
                    t["description"]
                    for t in tasks
                    if len(t.get("description", "")) > 40
                ]

            # Check for tasks mentioned in paragraphs if none found in lists
            if not tasks:
                for p in paragraphs:
                    lower = p.lower()
                    if (
                        "detour" in lower
                        or "roadblock" in lower
                        or "fast forward" in lower
                    ):
                        tasks.append(
                            {
                                "task_type": "Challenge",
                                "description": p,
                            }
                        )

            legs.append(
                {
                    "leg_number": leg_num,
                    "route_header": route_str,
                    "itinerary": itinerary,
                    "narrative": " ".join(paragraphs),
                    "tasks": tasks,
                }
            )

        return legs

    def scrape_all_episodes(self) -> dict[str, Any]:
        """Scrape episode tables across all seasons from master episode list articles."""
        urls = [
            "https://en.wikipedia.org/wiki/List_of_The_Amazing_Race_(American_TV_series)_episodes_(seasons_1%E2%80%9320)",
            "https://en.wikipedia.org/wiki/List_of_The_Amazing_Race_(American_TV_series)_episodes",
        ]
        master_episodes: dict[str, Any] = {}
        for url in urls:
            try:
                resp = self.client.get(url)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
            except Exception as e:
                logger.error("Failed to fetch episode list %s: %s", url, e)
                continue

            for table in soup.find_all("table", class_="wikiepisodetable"):
                h = table.find_previous(["h2", "h3"])
                h_text = h.get_text() if h else ""
                m = re.search(r"Season\s+(\d+)", h_text)
                if not m:
                    continue
                s_num = int(m.group(1))
                for row in table.find_all("tr", class_="vevent"):
                    tds = row.find_all(["td", "th"])
                    if len(tds) < 4:
                        continue
                    cells = [c.get_text(separator=" ").strip() for c in tds]
                    m_ep = re.search(r"\d+", cells[1])
                    if not m_ep:
                        continue
                    ep_num = int(m_ep.group(0))
                    title = cells[2].strip("\"'")
                    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", cells[3])
                    air_date = m_date.group(1) if m_date else None
                    viewers = None
                    if len(cells) > 4:
                        m_v = re.search(r"(\d+\.\d+)", cells[4])
                        if m_v:
                            try:
                                viewers = float(m_v.group(1))
                            except ValueError:
                                pass
                    key = f"{s_num}_{ep_num}"
                    master_episodes[key] = {
                        "season": s_num,
                        "episode": ep_num,
                        "title": title,
                        "air_date": air_date,
                        "viewers_millions": viewers,
                    }
        return master_episodes

    def scrape_season(
        self,
        season: int,
        version: str = "US",
        save: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """Scrape full season data from Wikipedia and return structured dictionary."""
        out_path = self.raw_dir / f"season_{version.lower()}_{season:02d}.json"
        cached_data = None
        if out_path.exists():
            try:
                cached_data = json.loads(out_path.read_text(encoding="utf-8"))
            except Exception:
                cached_data = None

        title = self.get_page_title(season, version)
        latest_rev = self.get_latest_revision(season, version)

        # Skip scraping if cached version matches Wikipedia revision
        if not force and cached_data and latest_rev:
            cached_revid = cached_data.get("wiki_revid")
            if cached_revid and cached_revid == latest_rev.get("revid"):
                logger.info(
                    "Wikipedia page for Season %d (%s) is unchanged (revid: %s); using cached data.",
                    season,
                    version,
                    cached_revid,
                )
                return cached_data

        logger.info(
            "Scraping Wikipedia: %s (Season %d, %s, revid: %s)",
            title,
            season,
            version,
            latest_rev.get("revid") if latest_rev else "unknown",
        )

        html = self.fetch_page_html(title)
        if not html:
            logger.warning("Could not fetch page for %s", title)
            return cached_data if cached_data else {}

        soup = BeautifulSoup(html, "lxml")
        infobox = self.parse_infobox(soup)
        tables = soup.find_all("table", class_="wikitable")

        contestants: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        episodes: list[dict[str, Any]] = []

        for table in tables:
            headers = [clean_text(th.get_text()).lower() for th in table.find_all("th")]
            h_text = " ".join(headers)
            if ("contestant" in h_text or "racer" in h_text) and not contestants:
                contestants = self.parse_contestants_table(table)
            elif (
                "team" in h_text and any(str(i) in h_text for i in range(1, 10))
            ) and not results:
                results = self.parse_results_table(table)
            elif (
                "episode" in h_text or "viewer" in h_text or "title" in h_text
            ) and not episodes:
                episodes = self.parse_episodes_table(table)

        legs = self.parse_legs_summary(soup)
        if legs:
            try:
                from tar_dataset.processors.geocoding import ensure_legs_geocoded

                new_geocoded = ensure_legs_geocoded(legs)
                if new_geocoded > 0:
                    logger.info(
                        "Geocoded %d new destination(s) for season %d",
                        new_geocoded,
                        season,
                    )
            except Exception as e:
                logger.warning(
                    "Could not auto-geocode legs for season %d: %s", season, e
                )

        season_data = {
            "version": version,
            "season": season,
            "wiki_title": title,
            "wiki_url": f"https://en.wikipedia.org/wiki/{title}",
            "wiki_revid": latest_rev.get("revid") if latest_rev else None,
            "wiki_timestamp": latest_rev.get("timestamp") if latest_rev else None,
            "infobox": infobox,
            "contestants": contestants,
            "results": results,
            "episodes": episodes,
            "legs": legs,
        }

        if save:
            out_path.write_text(json.dumps(season_data, indent=2), encoding="utf-8")
            logger.info("Saved season %d data to %s", season, out_path)

        return season_data

    def scrape_seasons(
        self,
        start: int = 1,
        end: int = 38,
        version: str = "US",
        force: bool = False,
    ) -> list[dict[str, Any]]:
        """Scrape range of seasons sequentially."""
        data_list = []
        for s in range(start, end + 1):
            try:
                data = self.scrape_season(s, version=version, save=True, force=force)
                if data:
                    data_list.append(data)
            except Exception as e:
                logger.error("Error scraping Season %d: %s", s, e)
        return data_list

    scrape_all_seasons = scrape_seasons
