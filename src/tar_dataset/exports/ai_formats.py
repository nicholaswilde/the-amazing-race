"""Exports processed TAR datasets into AI training formats (JSONL for fine-tuning, RAG, and pretraining)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert encyclopedia and analyst of the reality TV competition series The Amazing Race. "
    "You possess comprehensive knowledge of every season, team, leg itinerary, Detour, Roadblock, "
    "Fast Forward, U-Turn, pit stop results, and historical statistics."
)


class AIExportBuilder:
    """Builds LLM-ready datasets (fine-tuning JSONL, RAG chunks, and knowledge corpus)."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.ai_dir = Path(ai_dir)
        self.ai_dir.mkdir(parents=True, exist_ok=True)

    def load_table(self, name: str) -> pd.DataFrame:
        """Load a processed CSV table."""
        path = self.processed_dir / f"{name}.csv"
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)

    def generate_qa_pairs(self) -> list[dict[str, Any]]:
        """Generate fine-tuning Q&A pairs in OpenAI/Gemini chat messages format."""
        seasons = self.load_table("seasons")
        teams = self.load_table("teams")
        legs = self.load_table("legs")
        tasks = self.load_table("tasks")
        episodes = self.load_table("episodes")

        qa_records: list[dict[str, Any]] = []

        def add_qa(
            user_prompt: str,
            assistant_response: str,
            category: str,
            season: int | None = None,
        ) -> None:
            qa_records.append(
                {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_response},
                    ],
                    "metadata": {
                        "category": category,
                        "season": season,
                    },
                }
            )

        # 1. Season Winners & Stats
        if not seasons.empty:
            for _, s in seasons.iterrows():
                season_num = int(s["season"])
                winners = s.get("winners")
                dist_mi = s.get("distance_miles")
                n_legs = s.get("n_legs")

                if pd.notna(winners):
                    add_qa(
                        f"Who won Season {season_num} of The Amazing Race?",
                        f"The winners of The Amazing Race Season {season_num} were {winners}.",
                        "winners",
                        season_num,
                    )
                if pd.notna(dist_mi) and pd.notna(n_legs):
                    add_qa(
                        f"What was the total distance and number of legs in The Amazing Race Season {season_num}?",
                        f"The Amazing Race Season {season_num} covered approximately {dist_mi:,.0f} miles across {int(n_legs)} legs.",
                        "season_stats",
                        season_num,
                    )

        # 2. Team Finishes & Outcomes
        if not teams.empty:
            for _, t in teams.iterrows():
                season_num = int(t["season"])
                team_name = t["team_name"]
                status = t.get("status")
                rank = t.get("result")
                legs_won = t.get("legs_won", 0)

                if pd.notna(rank):
                    add_qa(
                        f"What was the final placement of {team_name} in The Amazing Race Season {season_num}?",
                        f"In Season {season_num} of The Amazing Race, {team_name} finished in {int(rank)} place ({status}) with {int(legs_won)} leg wins.",
                        "team_placement",
                        season_num,
                    )

        # 3. Leg Itineraries & Routes
        if not legs.empty:
            for _, l in legs.iterrows():
                season_num = int(l["season"])
                leg_num = int(l["leg_number"])
                route = l.get("route_header")
                narrative = l.get("narrative")

                if pd.notna(route) and route:
                    add_qa(
                        f"What was the route for Leg {leg_num} of The Amazing Race Season {season_num}?",
                        f"Leg {leg_num} of The Amazing Race Season {season_num} traveled along the route: {route}."
                        + (
                            f" Summary: {narrative[:300]}..."
                            if pd.notna(narrative) and len(str(narrative)) > 50
                            else ""
                        ),
                        "leg_route",
                        season_num,
                    )

        # 4. Challenge and Tasks
        if not tasks.empty:
            for _, task in tasks.iterrows():
                season_num = int(task["season"])
                leg_num = int(task["leg_number"])
                task_type = task["task_type"]
                desc = task["description"]

                if pd.notna(desc) and len(str(desc)) > 20:
                    add_qa(
                        f"What was the {task_type} challenge in Leg {leg_num} of The Amazing Race Season {season_num}?",
                        f"In Leg {leg_num} of The Amazing Race Season {season_num}, the {task_type} was: {desc}",
                        "task_challenge",
                        season_num,
                    )

        # 5. Episodes
        if not episodes.empty:
            for _, ep in episodes.iterrows():
                if pd.isna(ep.get("episode")):
                    continue
                season_num = int(ep["season"])
                ep_num = int(ep["episode"])
                title = ep.get("title")
                air_date = ep.get("air_date")
                viewers = ep.get("viewers_millions")

                if pd.notna(title):
                    resp = f"Episode {ep_num} of The Amazing Race Season {season_num} is titled '{title}'."
                    if pd.notna(air_date):
                        resp += f" It originally aired on {air_date}."
                    if pd.notna(viewers):
                        resp += f" It was watched by approximately {viewers:.2f} million viewers."
                    add_qa(
                        f"What is the title and broadcast information for Season {season_num}, Episode {ep_num} of The Amazing Race?",
                        resp,
                        "episode_info",
                        season_num,
                    )

        # 6. Reddit Community Discussions, Live Reactions, & Contestant AMAs
        reddit_discs = self.load_reddit_discussions()
        for disc in reddit_discs:
            title = disc.get("title", "")
            s_num = disc.get("season")
            ep_num = disc.get("episode")
            thread_type = disc.get("thread_type", "episode_discussion")
            comments = disc.get("comments", [])

            substantive_comments = [
                c
                for c in comments
                if len(c.get("body", "").strip()) >= 30
                and not c.get("body", "").startswith("Welcome to")
            ]

            if thread_type == "ama":
                qa_summary = [
                    f'- Viewer/Racer Q&A: "{c.get("body")}"'
                    for c in substantive_comments[:4]
                ]
                comment_text = (
                    "\n".join(qa_summary)
                    if qa_summary
                    else "Racers answered fan questions about behind-the-scenes race dynamics and casting."
                )
                prompt = f"What insights were shared during the r/TheAmazingRace contestant AMA '{title}'?"
                response = (
                    f"In the r/TheAmazingRace contestant AMA '{title}', racers discussed their time on the show:\n\n"
                    f"{comment_text}"
                )
                add_qa(prompt, response, "reddit_ama", season=s_num)

            elif s_num and ep_num:
                top_comments_summary = [
                    f'- {c.get("author", "Viewer")}: "{c.get("body")}"'
                    for c in substantive_comments[:4]
                ]
                summary_block = (
                    "\n".join(top_comments_summary)
                    if top_comments_summary
                    else "Viewers discussed team navigation, Detour performance, and Pit Stop placements."
                )
                type_label = (
                    "live broadcast reactions"
                    if thread_type == "live_discussion"
                    else (
                        "post-episode reactions"
                        if thread_type == "post_episode"
                        else "episode discussion"
                    )
                )
                prompt = f"What were the fan {type_label} on r/TheAmazingRace for Season {s_num} Episode {ep_num}?"
                response = (
                    f"During Season {s_num}, Episode {ep_num} of The Amazing Race ('{title}'), the Reddit community shared the following {type_label}:\n\n"
                    f"{summary_block}"
                )
                add_qa(prompt, response, f"reddit_{thread_type}", season=s_num)

        return qa_records

    def load_reddit_discussions(self) -> list[dict[str, Any]]:
        """Load and deduplicate raw scraped Reddit discussions and comments."""
        reddit_dir = Path("data/raw/reddit")
        if not reddit_dir.exists():
            return []

        seen_ids: set[str] = set()
        discussions: list[dict[str, Any]] = []

        for json_file in sorted(reddit_dir.glob("*.json")):
            try:
                with open(json_file, encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        for item in data:
                            pid = item.get("post_id")
                            if pid and pid not in seen_ids:
                                seen_ids.add(pid)
                                discussions.append(item)
            except Exception as e:
                logger.warning("Could not read reddit data file %s: %s", json_file, e)

        return discussions

    def generate_knowledge_corpus(self) -> list[dict[str, Any]]:
        """Generate structured document chunks with metadata for RAG and embedding."""
        legs = self.load_table("legs")
        tasks = self.load_table("tasks")
        seasons = self.load_table("seasons")

        corpus: list[dict[str, Any]] = []

        # Season level documents
        if not seasons.empty:
            for _, s in seasons.iterrows():
                season_num = int(s["season"])
                doc_id = f"tar-s{season_num:02d}-overview"
                text = (
                    f"The Amazing Race Season {season_num} Summary:\n"
                    f"- Winners: {s.get('winners', 'Unknown')}\n"
                    f"- Teams: {s.get('n_teams', 'Unknown')}\n"
                    f"- Total Legs: {s.get('n_legs', 'Unknown')}\n"
                    f"- Race Distance: {s.get('distance_miles', 'Unknown')} miles ({s.get('distance_km', 'Unknown')} km)\n"
                    f"- Air Dates: {s.get('air_dates', 'Unknown')}\n"
                    f"- Filming Dates: {s.get('filming_dates', 'Unknown')}\n"
                    f"- Wikipedia URL: {s.get('wiki_url', '')}"
                )
                corpus.append(
                    {
                        "id": doc_id,
                        "title": f"The Amazing Race Season {season_num} Overview",
                        "text": text,
                        "metadata": {"type": "season_overview", "season": season_num},
                    }
                )

        # Leg level narrative documents
        if not legs.empty:
            for _, l in legs.iterrows():
                season_num = int(l["season"])
                leg_num = int(l["leg_number"])
                doc_id = f"tar-s{season_num:02d}-leg{leg_num:02d}"

                leg_tasks = (
                    tasks[
                        (tasks["season"] == season_num)
                        & (tasks["leg_number"] == leg_num)
                    ]
                    if not tasks.empty
                    else pd.DataFrame()
                )

                task_texts = []
                for _, t in leg_tasks.iterrows():
                    task_texts.append(f"[{t['task_type']}]: {t['description']}")

                tasks_block = (
                    "\n".join(task_texts)
                    if task_texts
                    else "No specific task descriptions recorded."
                )

                text = (
                    f"The Amazing Race Season {season_num}, Leg {leg_num}\n"
                    f"Route: {l.get('route_header', 'Unknown')}\n\n"
                    f"Challenges & Tasks:\n{tasks_block}\n\n"
                    f"Leg Narrative:\n{l.get('narrative', 'N/A')}"
                )
                corpus.append(
                    {
                        "id": doc_id,
                        "title": f"Season {season_num} Leg {leg_num} ({l.get('route_header', '')})",
                        "text": text,
                        "metadata": {
                            "type": "leg_narrative",
                            "season": season_num,
                            "leg": leg_num,
                            "route": l.get("route_header"),
                        },
                    }
                )

        # 3. Reddit Community Discussions, Live Reactions, and AMAs
        reddit_discs = self.load_reddit_discussions()
        for disc in reddit_discs:
            pid = disc.get("post_id", "")
            title = disc.get("title", "")
            s_num = disc.get("season")
            ep_num = disc.get("episode")
            thread_type = disc.get("thread_type", "episode_discussion")
            author = disc.get("author", "unknown")
            score = disc.get("score", 0)
            num_comments = disc.get("num_comments", 0)
            selftext = disc.get("selftext", "") or ""
            comments = disc.get("comments", [])

            substantive_comments = [
                c
                for c in comments
                if len(c.get("body", "").strip()) >= 30
                and not c.get("body", "").startswith("Welcome to")
            ]

            comment_lines = []
            for c in substantive_comments[:6]:
                comment_lines.append(
                    f'  • {c.get("author", "Viewer")} (Score: {c.get("score", 0)}): "{c.get("body", "").strip()}"'
                )

            comments_block = (
                "\n".join(comment_lines)
                if comment_lines
                else "No top community comments recorded."
            )
            selftext_block = f"\nOriginal Post:\n{selftext}\n" if selftext else ""

            body = (
                f"r/TheAmazingRace Community Discussion: {title}\n"
                f"Category: {thread_type.replace('_', ' ').title()} | Season: {s_num or 'N/A'} | Episode: {ep_num or 'N/A'}\n"
                f"Posted by u/{author} | Upvotes: {score} | Total Comments: {num_comments}\n"
                f"{selftext_block}\n"
                f"Key Fan Reactions & Community Insights:\n"
                f"{comments_block}"
            )

            corpus.append(
                {
                    "id": f"reddit_{pid}",
                    "title": f"r/TheAmazingRace: {title}",
                    "text": body,
                    "metadata": {
                        "type": "reddit_discussion",
                        "thread_type": thread_type,
                        "season": s_num,
                        "episode": ep_num,
                        "post_id": pid,
                        "score": score,
                    },
                }
            )

        return corpus

    def export_all(self) -> dict[str, int]:
        """Export all AI formats to JSONL files."""
        counts = {}

        qa_data = self.generate_qa_pairs()
        if qa_data:
            qa_path = self.ai_dir / "tar_qa_finetuning.jsonl"
            with open(qa_path, "w", encoding="utf-8") as f:
                f.writelines(
                    json.dumps(row, ensure_ascii=False) + "\n" for row in qa_data
                )
            counts["qa_pairs"] = len(qa_data)
            logger.info(
                "Saved %d Q&A fine-tuning examples to %s", len(qa_data), qa_path
            )

        corpus_data = self.generate_knowledge_corpus()
        if corpus_data:
            corpus_path = self.ai_dir / "tar_knowledge_corpus.jsonl"
            with open(corpus_path, "w", encoding="utf-8") as f:
                f.writelines(
                    json.dumps(row, ensure_ascii=False) + "\n" for row in corpus_data
                )
            counts["corpus_chunks"] = len(corpus_data)
            logger.info(
                "Saved %d knowledge corpus chunks to %s", len(corpus_data), corpus_path
            )

        return counts
