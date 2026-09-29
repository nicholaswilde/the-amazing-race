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

        def add_qa(user_prompt: str, assistant_response: str, category: str, season: int | None = None) -> None:
            qa_records.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_response},
                ],
                "metadata": {
                    "category": category,
                    "season": season,
                },
            })

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
                        + (f" Summary: {narrative[:300]}..." if pd.notna(narrative) and len(str(narrative)) > 50 else ""),
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

        return qa_records

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
                corpus.append({
                    "id": doc_id,
                    "title": f"The Amazing Race Season {season_num} Overview",
                    "text": text,
                    "metadata": {"type": "season_overview", "season": season_num},
                })

        # Leg level narrative documents
        if not legs.empty:
            for _, l in legs.iterrows():
                season_num = int(l["season"])
                leg_num = int(l["leg_number"])
                doc_id = f"tar-s{season_num:02d}-leg{leg_num:02d}"

                leg_tasks = tasks[
                    (tasks["season"] == season_num) & (tasks["leg_number"] == leg_num)
                ] if not tasks.empty else pd.DataFrame()

                task_texts = []
                for _, t in leg_tasks.iterrows():
                    task_texts.append(f"[{t['task_type']}]: {t['description']}")

                tasks_block = "\n".join(task_texts) if task_texts else "No specific task descriptions recorded."

                text = (
                    f"The Amazing Race Season {season_num}, Leg {leg_num}\n"
                    f"Route: {l.get('route_header', 'Unknown')}\n\n"
                    f"Challenges & Tasks:\n{tasks_block}\n\n"
                    f"Leg Narrative:\n{l.get('narrative', 'N/A')}"
                )
                corpus.append({
                    "id": doc_id,
                    "title": f"Season {season_num} Leg {leg_num} ({l.get('route_header', '')})",
                    "text": text,
                    "metadata": {
                        "type": "leg_narrative",
                        "season": season_num,
                        "leg": leg_num,
                        "route": l.get("route_header"),
                    },
                })

        return corpus

    def export_all(self) -> dict[str, int]:
        """Export all AI formats to JSONL files."""
        counts = {}

        qa_data = self.generate_qa_pairs()
        if qa_data:
            qa_path = self.ai_dir / "tar_qa_finetuning.jsonl"
            with open(qa_path, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in qa_data)
            counts["qa_pairs"] = len(qa_data)
            logger.info("Saved %d Q&A fine-tuning examples to %s", len(qa_data), qa_path)

        corpus_data = self.generate_knowledge_corpus()
        if corpus_data:
            corpus_path = self.ai_dir / "tar_knowledge_corpus.jsonl"
            with open(corpus_path, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in corpus_data)
            counts["corpus_chunks"] = len(corpus_data)
            logger.info("Saved %d knowledge corpus chunks to %s", len(corpus_data), corpus_path)

        return counts
