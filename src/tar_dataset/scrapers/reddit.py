"""Reddit scraper for r/TheAmazingRace.

Collects episode discussions, post-episode reactions, live threads, and team AMAs.
Supports both unauthenticated Pullpush archive API and authenticated PRAW.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import httpx

from tar_dataset.schemas import RedditDiscussion

logger = logging.getLogger(__name__)


class RedditScraper:
    """Scrapes r/TheAmazingRace submissions and discussions."""

    PULLPUSH_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
    PULLPUSH_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

    def __init__(self, raw_dir: Path | str = "data/raw/reddit") -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            headers={"User-Agent": "TAR-Dataset-Scraper/1.0 (academic/research)"},
            timeout=25.0,
        )

    def extract_season_episode(self, title: str) -> tuple[int | None, int | None]:
        """Extract season and episode number from title (e.g. 'S35E04', 'Season 35 Episode 4')."""
        # S35E04 or S35 E04
        m1 = re.search(r"S(\d{1,2})\s*E(\d{1,2})", title, re.IGNORECASE)
        if m1:
            return int(m1.group(1)), int(m1.group(2))

        # Season 35 Episode 4
        m2 = re.search(r"Season\s+(\d{1,2})", title, re.IGNORECASE)
        season = int(m2.group(1)) if m2 else None

        m3 = re.search(r"Episode\s+(\d{1,2})", title, re.IGNORECASE)
        episode = int(m3.group(1)) if m3 else None

        return season, episode

    def search_discussions_pullpush(
        self,
        query: str = "Episode Discussion",
        subreddit: str = "TheAmazingRace",
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Search submissions via Pullpush API."""
        params = {
            "subreddit": subreddit,
            "q": query,
            "size": min(limit, 100),
            "sort": "desc",
            "sort_type": "created_utc",
        }
        try:
            resp = self.client.get(self.PULLPUSH_SUBMISSION_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as exc:
            logger.error("Pullpush search failed for query '%s': %s", query, exc)
            return []

    def fetch_comments_pullpush(
        self, link_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fetch comments for a submission via Pullpush."""
        params = {
            "link_id": link_id,
            "size": limit,
            "sort": "desc",
            "sort_type": "score",
        }
        try:
            resp = self.client.get(self.PULLPUSH_COMMENT_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            comments = []
            for item in data.get("data", []):
                comments.append(
                    {
                        "id": item.get("id"),
                        "author": item.get("author", "[deleted]"),
                        "body": item.get("body", ""),
                        "score": item.get("score", 0),
                        "created_utc": item.get("created_utc"),
                    }
                )
            return comments
        except Exception as exc:
            logger.warning("Could not fetch comments for post %s: %s", link_id, exc)
            return []

    def scrape_episode_discussions(
        self,
        query: str = "Discussion Thread",
        limit: int = 20,
        fetch_comments: bool = True,
        save: bool = True,
    ) -> list[RedditDiscussion]:
        """Scrape episode discussion threads and save to raw data."""
        logger.info(
            "Searching Reddit r/TheAmazingRace for '%s' (limit=%d)...", query, limit
        )
        posts = self.search_discussions_pullpush(query=query, limit=limit)
        results: list[RedditDiscussion] = []

        for p in posts:
            title = p.get("title", "")
            season, episode = self.extract_season_episode(title)
            post_id = p.get("id", "")

            comments: list[dict[str, Any]] = []
            if fetch_comments and post_id:
                comments = self.fetch_comments_pullpush(link_id=post_id, limit=15)
                time.sleep(0.2)  # Polite rate limit

            disc = RedditDiscussion(
                post_id=post_id,
                season=season,
                episode=episode,
                title=title,
                author=p.get("author", "[deleted]"),
                score=p.get("score", 0),
                num_comments=p.get("num_comments", 0),
                created_utc=str(p.get("created_utc", "")),
                url=p.get(
                    "full_link",
                    f"https://reddit.com/r/TheAmazingRace/comments/{post_id}",
                ),
                selftext=p.get("selftext"),
                comments=comments,
            )
            results.append(disc)

        if save and results:
            out_file = self.raw_dir / f"reddit_discussions_{int(time.time())}.json"
            out_file.write_text(
                json.dumps([r.model_dump() for r in results], indent=2),
                encoding="utf-8",
            )
            logger.info("Saved %d discussions to %s", len(results), out_file)

        return results
