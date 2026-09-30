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
    """Scrapes r/TheAmazingRace submissions, discussions, live reactions, and AMAs."""

    PULLPUSH_SUBMISSION_URL = "https://api.pullpush.io/reddit/search/submission/"
    PULLPUSH_COMMENT_URL = "https://api.pullpush.io/reddit/search/comment/"

    def __init__(
        self,
        raw_dir: Path | str = "data/raw/reddit",
        subreddit_name: str = "TheAmazingRace",
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.subreddit_name = subreddit_name
        self.client = httpx.Client(
            headers={"User-Agent": "TAR-Dataset-Scraper/1.0 (academic/research)"},
            timeout=30.0,
        )

    def extract_season_episode(self, title: str) -> tuple[int | None, int | None]:
        """Extract season and episode number from thread title across varied naming conventions."""
        # 1. Pattern: S35E04, S35 E04, S35.E04
        m_se = re.search(r"S(\d{1,2})\s*[\.xX-]?\s*E(\d{1,2})", title, re.IGNORECASE)
        if m_se:
            return int(m_se.group(1)), int(m_se.group(2))

        # 2. Pattern: Season 35 Episode 4 or The Amazing Race 35 Episode 4 or TAR 35 Episode 4
        m_both = re.search(
            r"(?:Season|TAR|The Amazing Race|The Amazing Race Canada)?\s*(\d{1,2})\s+(?:Episode|Ep\.?)\s*(\d{1,2})",
            title,
            re.IGNORECASE,
        )
        if m_both:
            return int(m_both.group(1)), int(m_both.group(2))

        # 3. Pattern: Season 35, TAR 35
        m_s = re.search(
            r"(?:Season|TAR|The Amazing Race)\s+(\d{1,2})", title, re.IGNORECASE
        )
        season = int(m_s.group(1)) if m_s else None

        # 4. Pattern: Episode 4, Ep 4
        m_e = re.search(r"(?:Episode|Ep\.?)\s*(\d{1,2})", title, re.IGNORECASE)
        episode = int(m_e.group(1)) if m_e else None

        return season, episode

    def classify_thread_type(self, title: str, query: str = "") -> str:
        """Classify thread into episode_discussion, live_discussion, post_episode, ama, or general."""
        lower_title = title.lower()
        lower_query = query.lower()

        if (
            bool(re.search(r"\bama\b", lower_title))
            or "ask me anything" in lower_title
            or bool(re.search(r"\bama\b", lower_query))
        ):
            return "ama"
        if "live" in lower_title or "live" in lower_query:
            return "live_discussion"
        if (
            "post-episode" in lower_title
            or "post episode" in lower_title
            or "post" in lower_query
        ):
            return "post_episode"
        if "discussion" in lower_title or "episode" in lower_title:
            return "episode_discussion"
        return "general"

    def search_discussions_pullpush(
        self,
        query: str = "Episode Discussion",
        subreddit: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search submissions via Pullpush API with pagination support."""
        sub = subreddit or self.subreddit_name
        submissions: list[dict[str, Any]] = []
        before: int | None = None
        remaining = limit

        # Pullpush ignores 3-letter acronyms like 'AMA'; expand to full phrase
        effective_query = "Ask Me Anything" if query.strip().upper() == "AMA" else query

        while remaining > 0:
            batch_size = min(remaining, 100)
            params: dict[str, Any] = {
                "subreddit": sub,
                "q": effective_query,
                "size": batch_size,
                "sort": "desc",
                "sort_type": "created_utc",
            }
            if before is not None:
                params["before"] = before

            try:
                resp = self.client.get(self.PULLPUSH_SUBMISSION_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                batch = data.get("data", [])
                if not batch:
                    break

                submissions.extend(batch)
                remaining -= len(batch)

                # Set before to oldest timestamp in batch for next page
                oldest_timestamp = batch[-1].get("created_utc")
                if oldest_timestamp:
                    before = int(oldest_timestamp)
                else:
                    break

                if len(batch) < batch_size:
                    break

                time.sleep(0.3)  # Rate limit courtesy
            except Exception as exc:
                logger.error("Pullpush search failed for query '%s': %s", query, exc)
                break

        return submissions[:limit]

    def fetch_comments_pullpush(
        self, link_id: str, limit: int = 15
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
                body = item.get("body", "").strip()
                author = item.get("author", "[deleted]")
                # Filter out deleted, removed, or automoderator boilerplate comments
                if (
                    not body
                    or body in ("[deleted]", "[removed]")
                    or author.lower() == "automoderator"
                ):
                    continue
                comments.append(
                    {
                        "id": item.get("id"),
                        "author": author,
                        "body": body,
                        "score": item.get("score", 0),
                        "created_utc": item.get("created_utc"),
                    }
                )
            return comments
        except Exception as exc:
            logger.warning("Could not fetch comments for post %s: %s", link_id, exc)
            return []

    def scrape_discussions(
        self,
        query: str = "Discussion Thread",
        limit: int = 50,
        fetch_comments: bool = True,
        save: bool = True,
    ) -> list[RedditDiscussion]:
        """Scrape discussions matching a query."""
        logger.info(
            "Searching r/%s for '%s' (limit=%d)...", self.subreddit_name, query, limit
        )
        posts = self.search_discussions_pullpush(
            query=query, subreddit=self.subreddit_name, limit=limit
        )
        results: list[RedditDiscussion] = []

        for p in posts:
            title = p.get("title", "")
            season, episode = self.extract_season_episode(title)
            thread_type = self.classify_thread_type(title, query=query)
            post_id = p.get("id", "")
            num_comments = p.get("num_comments", 0)

            comments: list[dict[str, Any]] = []
            if fetch_comments and post_id and num_comments > 0:
                comments = self.fetch_comments_pullpush(link_id=post_id, limit=10)
                time.sleep(0.1)

            disc = RedditDiscussion(
                post_id=post_id,
                season=season,
                episode=episode,
                thread_type=thread_type,
                title=title,
                author=p.get("author", "[deleted]"),
                score=p.get("score", 0),
                num_comments=num_comments,
                created_utc=str(p.get("created_utc", "")),
                url=p.get(
                    "full_link",
                    f"https://reddit.com/r/{self.subreddit_name}/comments/{post_id}",
                ),
                selftext=p.get("selftext"),
                comments=comments,
            )
            results.append(disc)

        if save and results:
            self._save_and_merge_discussions(results, query=query)

        return results

    def scrape_episode_discussions(
        self,
        query: str = "Discussion Thread",
        limit: int = 20,
        fetch_comments: bool = True,
        save: bool = True,
    ) -> list[RedditDiscussion]:
        """Alias for scrape_discussions for backward compatibility."""
        return self.scrape_discussions(
            query=query, limit=limit, fetch_comments=fetch_comments, save=save
        )

    def scrape_all_categories(
        self,
        limits: dict[str, int] | None = None,
        fetch_comments: bool = True,
    ) -> dict[str, list[RedditDiscussion]]:
        """Scrape episode discussions, live discussions, post-episode reactions, and AMAs in batch."""
        category_queries = {
            "episode_discussion": ("Discussion Thread", 100),
            "live_discussion": ("Live Discussion", 50),
            "post_episode": ("Post-Episode Discussion", 50),
            "ama": ("AMA", 25),
        }

        all_results: dict[str, list[RedditDiscussion]] = {}
        for cat, (q, default_limit) in category_queries.items():
            limit = limits.get(cat, default_limit) if limits else default_limit
            logger.info(
                "Scraping category '%s' with query '%s' (limit=%d)...", cat, q, limit
            )
            discs = self.scrape_discussions(
                query=q, limit=limit, fetch_comments=fetch_comments, save=True
            )
            all_results[cat] = discs

        return all_results

    def load_cached_discussions(self) -> list[RedditDiscussion]:
        """Load all unique discussions cached on disk."""
        existing: dict[str, RedditDiscussion] = {}
        for f in self.raw_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    items = json.load(fp)
                    if isinstance(items, list):
                        for item in items:
                            try:
                                disc = RedditDiscussion(**item)
                                existing[disc.post_id] = disc
                            except Exception as exc:
                                logger.debug(
                                    "Skipping invalid discussion item: %s", exc
                                )
            except Exception as exc:
                logger.debug("Skipping unreadable reddit cache file %s: %s", f, exc)
                continue
        return list(existing.values())

    def _save_and_merge_discussions(
        self, new_discussions: list[RedditDiscussion], query: str = ""
    ) -> Path:
        """Merge newly scraped discussions with existing cache deduplicating by post_id."""
        clean_name = re.sub(r"[^\w\-]+", "_", query.lower()).strip("_") or "discussions"
        filename = f"reddit_{clean_name}_{int(time.time())}.json"
        out_file = self.raw_dir / filename

        # Load existing discussions from disk for deduplication
        existing = {d.post_id: d.model_dump() for d in self.load_cached_discussions()}

        # Add new items
        for d in new_discussions:
            existing[d.post_id] = d.model_dump()

        # Write clean timestamped file
        out_file.write_text(
            json.dumps(
                [r.model_dump() for r in new_discussions], indent=2, ensure_ascii=False
            ),
            encoding="utf-8",
        )
        logger.info(
            "Saved %d discussions to %s (Total unique cached across store: %d)",
            len(new_discussions),
            out_file,
            len(existing),
        )
        return out_file
