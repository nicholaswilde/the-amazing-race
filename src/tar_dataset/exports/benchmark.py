"""RAG & AI Benchmark Suite for The Amazing Race.

Curates an evaluation benchmark prompt set and scoring harness to evaluate LLMs on:
1. TAR Trivia
2. Rules Comprehension
3. Route & Geographic Accuracy
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

BENCHMARK_ITEMS: list[dict[str, Any]] = [
    # ==========================
    # CATEGORY: TRIVIA
    # ==========================
    {
        "id": "bench-trivia-001",
        "category": "trivia",
        "difficulty": "easy",
        "season": 1,
        "question": "Who won the very first season of The Amazing Race (US)?",
        "reference_answer": "Rob Frisbee and Brennan Swain (lawyers and best friends) won Season 1.",
        "key_facts": ["Rob", "Brennan"],
        "context_docs": ["season_1_overview"],
    },
    {
        "id": "bench-trivia-002",
        "category": "trivia",
        "difficulty": "medium",
        "season": 5,
        "question": "Which married parents team won The Amazing Race Season 5 after overcoming a flight delay in the final leg?",
        "reference_answer": "Chip and Kim McAllister won Season 5.",
        "key_facts": ["Chip", "Kim", "McAllister"],
        "context_docs": ["season_5_overview"],
    },
    {
        "id": "bench-trivia-003",
        "category": "trivia",
        "difficulty": "hard",
        "season": 7,
        "question": "Which famous Survivor couple finished as runners-up in Season 7 and later returned for All-Stars?",
        "reference_answer": "Rob Mariano and Amber Brkich (Boston Rob and Amber) finished second in Season 7.",
        "key_facts": ["Rob", "Amber"],
        "context_docs": ["season_7_teams"],
    },
    {
        "id": "bench-trivia-004",
        "category": "trivia",
        "difficulty": "medium",
        "season": 20,
        "question": "Which team holds the record for the most leg wins in a single season of The Amazing Race (US)?",
        "reference_answer": "Rachel and Dave Brown Jr. in Season 20, winning 8 legs.",
        "key_facts": ["Rachel", "Dave", "Season 20"],
        "context_docs": ["season_20_records"],
    },
    {
        "id": "bench-trivia-005",
        "category": "trivia",
        "difficulty": "hard",
        "season": 9,
        "question": "What team holds the best average placement across an entire season without winning the race?",
        "reference_answer": "Eric and Jeremy in Season 9, with a record racing average of ~1.69.",
        "key_facts": ["Eric", "Jeremy", "Season 9"],
        "context_docs": ["season_9_results"],
    },
    {
        "id": "bench-trivia-006",
        "category": "trivia",
        "difficulty": "easy",
        "season": 17,
        "question": "Which team became the first all-female team to win The Amazing Race US?",
        "reference_answer": "Nat Strand and Kat Chang (doctors) won Season 17.",
        "key_facts": ["Nat", "Kat", "all-female"],
        "context_docs": ["season_17_overview"],
    },
    {
        "id": "bench-trivia-007",
        "category": "trivia",
        "difficulty": "medium",
        "season": 21,
        "question": "Which team won the $1 million prize in Season 21 after barely surviving multiple legs at the back of the pack?",
        "reference_answer": "Josh Kilmer-Purcell and Brent Ridge (The Beekman Boys) won Season 21.",
        "key_facts": ["Josh", "Brent", "Beekman"],
        "context_docs": ["season_21_overview"],
    },
    {
        "id": "bench-trivia-008",
        "category": "trivia",
        "difficulty": "easy",
        "season": 36,
        "question": "Who won The Amazing Race Season 36?",
        "reference_answer": "Ricky Valero and César Aldrete won Season 36.",
        "key_facts": ["Ricky", "Cesar"],
        "context_docs": ["season_36_overview"],
    },
    {
        "id": "bench-trivia-009",
        "category": "trivia",
        "difficulty": "hard",
        "season": 12,
        "question": "Who won Season 12 of The Amazing Race, becoming the first newly dating couple to win?",
        "reference_answer": "TK Erwin and Rachel Rosales won Season 12.",
        "key_facts": ["TK", "Rachel"],
        "context_docs": ["season_12_overview"],
    },
    {
        "id": "bench-trivia-010",
        "category": "trivia",
        "difficulty": "medium",
        "season": 18,
        "question": "What was the subtitle of The Amazing Race Season 18?",
        "reference_answer": "Unfinished Business.",
        "key_facts": ["Unfinished Business"],
        "context_docs": ["season_18_overview"],
    },
    {
        "id": "bench-trivia-011",
        "category": "trivia",
        "difficulty": "medium",
        "season": 24,
        "question": "Which father-son cancer survivors became the first parent-child team to win The Amazing Race in Season 24 All-Stars?",
        "reference_answer": "Dave and Connor O'Leary won Season 24.",
        "key_facts": ["Dave", "Connor", "O'Leary"],
        "context_docs": ["season_24_overview"],
    },
    {
        "id": "bench-trivia-012",
        "category": "trivia",
        "difficulty": "medium",
        "season": 30,
        "question": "Which reality television couple from Big Brother won The Amazing Race Season 30?",
        "reference_answer": "Cody Nickson and Jessica Graf won Season 30.",
        "key_facts": ["Cody", "Jessica", "Big Brother"],
        "context_docs": ["season_30_overview"],
    },
    {
        "id": "bench-trivia-013",
        "category": "trivia",
        "difficulty": "hard",
        "season": 25,
        "question": "Which food scientist team won Season 25 after surviving Leg 11 as a surprise non-elimination final 4 leg?",
        "reference_answer": "Amy DeJong and Maya Warren won Season 25.",
        "key_facts": ["Amy", "Maya", "food scientists"],
        "context_docs": ["season_25_overview"],
    },
    {
        "id": "bench-trivia-014",
        "category": "trivia",
        "difficulty": "medium",
        "season": 29,
        "question": "Which team of complete strangers paired up at the starting line won Season 29?",
        "reference_answer": "Brooke Camhi and Scott Flanary won Season 29.",
        "key_facts": ["Brooke", "Scott"],
        "context_docs": ["season_29_overview"],
    },
    {
        "id": "bench-trivia-015",
        "category": "trivia",
        "difficulty": "easy",
        "season": 34,
        "question": "Which Big Brother alumni couple won The Amazing Race Season 34?",
        "reference_answer": "Derek Xiao and Claire Rehfuss won Season 34.",
        "key_facts": ["Derek", "Claire"],
        "context_docs": ["season_34_overview"],
    },
    # ==========================
    # CATEGORY: RULES COMPREHENSION
    # ==========================
    {
        "id": "bench-rules-001",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": None,
        "question": "How did the Fast Forward rule change after the early seasons of The Amazing Race?",
        "reference_answer": "In Seasons 1-4, a Fast Forward was available on almost every leg, and teams could only use it once per race. Starting in Season 5, the number of Fast Forwards per season was drastically reduced to only two per race.",
        "key_facts": ["once per race", "reduced", "Season 5"],
        "context_docs": ["rules_fast_forward"],
    },
    {
        "id": "bench-rules-002",
        "category": "rules_comprehension",
        "difficulty": "hard",
        "season": 6,
        "question": "What rule was implemented in Season 6 regarding Roadblock task distribution between team members?",
        "reference_answer": "A rule was introduced capping the maximum number of Roadblocks an individual team member could perform (typically a maximum of 6 or 7 per racer before the final leg), ensuring both teammates shared task duties equally.",
        "key_facts": ["maximum", "Roadblock", "limit"],
        "context_docs": ["rules_roadblock_limits"],
    },
    {
        "id": "bench-rules-003",
        "category": "rules_comprehension",
        "difficulty": "easy",
        "season": 12,
        "question": "What penalty was introduced in Season 12 for the team arriving last on a non-elimination leg?",
        "reference_answer": "The Speed Bump was introduced, requiring the trailing team to complete an extra task on the subsequent leg.",
        "key_facts": ["Speed Bump", "extra task"],
        "context_docs": ["rules_non_elimination_penalties"],
    },
    {
        "id": "bench-rules-004",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 5,
        "question": "What race mechanic was introduced in Season 5 allowing one team to force another team to stop racing for a predetermined amount of time?",
        "reference_answer": "The Yield was introduced in Season 5, forcing the yielded team to turn an hourglass and wait before continuing.",
        "key_facts": ["Yield", "wait"],
        "context_docs": ["rules_yield"],
    },
    {
        "id": "bench-rules-005",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 12,
        "question": "What obstacle replaced the Yield starting in Season 12, forcing a team behind them to complete the other Detour branch?",
        "reference_answer": "The U-Turn was introduced in Season 12, forcing the U-Turned team to complete both sides of the Detour.",
        "key_facts": ["U-Turn", "Detour"],
        "context_docs": ["rules_uturn"],
    },
    {
        "id": "bench-rules-006",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 17,
        "question": "What reward was introduced in Season 17 given to the winner of the first leg, allowing them to skip any non-Roadblock task before Leg 8?",
        "reference_answer": "The Express Pass was introduced in Season 17.",
        "key_facts": ["Express Pass", "skip"],
        "context_docs": ["rules_express_pass"],
    },
    {
        "id": "bench-rules-007",
        "category": "rules_comprehension",
        "difficulty": "hard",
        "season": 10,
        "question": "In Seasons 10 and 11, what penalty was assessed to teams finishing last on a non-elimination leg?",
        "reference_answer": "Teams were 'Marked for Elimination' and had to finish first on the next leg or incur a 30-minute time penalty at the Pit Stop.",
        "key_facts": ["Marked for Elimination", "30-minute"],
        "context_docs": ["rules_marked_for_elimination"],
    },
    {
        "id": "bench-rules-008",
        "category": "rules_comprehension",
        "difficulty": "easy",
        "season": None,
        "question": "What is the fundamental difference between a Detour and a Roadblock in The Amazing Race?",
        "reference_answer": "A Detour is a choice between two tasks that both team members perform together, whereas a Roadblock is a task that only one team member must perform alone.",
        "key_facts": ["Detour", "Roadblock", "alone"],
        "context_docs": ["rules_detour_vs_roadblock"],
    },
    {
        "id": "bench-rules-009",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 7,
        "question": "What happened to teams in Seasons 7 through 9 if they finished last on a non-elimination leg?",
        "reference_answer": "Teams had to surrender all their money, and started the next leg with zero dollars, forcing them to beg or borrow money from locals.",
        "key_facts": ["surrender", "money", "zero dollars"],
        "context_docs": ["rules_mugging_penalty"],
    },
    {
        "id": "bench-rules-010",
        "category": "rules_comprehension",
        "difficulty": "hard",
        "season": 14,
        "question": "What variation of the U-Turn was introduced in Season 14 that allowed the team using it to keep their identity anonymous?",
        "reference_answer": "The Blind U-Turn.",
        "key_facts": ["Blind U-Turn", "anonymous"],
        "context_docs": ["rules_blind_uturn"],
    },
    {
        "id": "bench-rules-011",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 10,
        "question": "What twist introduced in Season 10 and 11 required two teams to cooperate and complete tasks together?",
        "reference_answer": "The Intersection.",
        "key_facts": ["Intersection", "together"],
        "context_docs": ["rules_intersection"],
    },
    {
        "id": "bench-rules-012",
        "category": "rules_comprehension",
        "difficulty": "hard",
        "season": 25,
        "question": "What advantage awarded in Leg 1 of Season 25 allowed a team to avoid elimination if they arrived in last place on an elimination leg?",
        "reference_answer": "The Save.",
        "key_facts": ["The Save", "avoid elimination"],
        "context_docs": ["rules_the_save"],
    },
    {
        "id": "bench-rules-013",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 30,
        "question": "What competitive task structure was introduced in Season 30 where teams had to directly compete against each other in a bracket/duel before checking in at the Pit Stop?",
        "reference_answer": "The Head-to-Head (also known as Face-Off in international editions).",
        "key_facts": ["Head-to-Head", "Face-Off"],
        "context_docs": ["rules_head_to_head"],
    },
    {
        "id": "bench-rules-014",
        "category": "rules_comprehension",
        "difficulty": "hard",
        "season": 19,
        "question": "What penalty was assessed to the team that finished last in the starting line task of Season 19?",
        "reference_answer": "The Hazard, which was a special penalty task completed before or during the first leg.",
        "key_facts": ["The Hazard", "penalty"],
        "context_docs": ["rules_hazard"],
    },
    {
        "id": "bench-rules-015",
        "category": "rules_comprehension",
        "difficulty": "medium",
        "season": 17,
        "question": "How does a Double U-Turn differ from a standard single U-Turn?",
        "reference_answer": "A Double U-Turn allows two different teams to each use a U-Turn on another team during the same leg.",
        "key_facts": ["two different teams", "two"],
        "context_docs": ["rules_double_uturn"],
    },
    # ==========================
    # CATEGORY: ROUTE ACCURACY
    # ==========================
    {
        "id": "bench-route-001",
        "category": "route_accuracy",
        "difficulty": "easy",
        "season": 1,
        "question": "Where was the starting line and finish line for The Amazing Race Season 1?",
        "reference_answer": "The starting line was Central Park in New York City, and the finish line was Flushing Meadows-Corona Park in Queens, New York.",
        "key_facts": ["Central Park", "New York", "Flushing Meadows"],
        "context_docs": ["season_1_route"],
    },
    {
        "id": "bench-route-002",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 1,
        "question": "Which African countries were visited in the initial legs of Season 1?",
        "reference_answer": "South Africa and Zambia.",
        "key_facts": ["South Africa", "Zambia"],
        "context_docs": ["season_1_legs"],
    },
    {
        "id": "bench-route-003",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 5,
        "question": "In Season 5, what country served as the Pit Stop where Colin and Christie had their famous ox breakdown?",
        "reference_answer": "Egypt (near Cairo/Luxor/Giza).",
        "key_facts": ["Egypt"],
        "context_docs": ["season_5_egypt"],
    },
    {
        "id": "bench-route-004",
        "category": "route_accuracy",
        "difficulty": "hard",
        "season": 6,
        "question": "In Season 6, what South Asian island country did teams race across before the 2004 tsunami struck?",
        "reference_answer": "Sri Lanka.",
        "key_facts": ["Sri Lanka"],
        "context_docs": ["season_6_route"],
    },
    {
        "id": "bench-route-005",
        "category": "route_accuracy",
        "difficulty": "easy",
        "season": 2,
        "question": "In what South American country did Season 2 begin its international legs immediately after leaving the United States?",
        "reference_answer": "Brazil (Rio de Janeiro).",
        "key_facts": ["Brazil"],
        "context_docs": ["season_2_route"],
    },
    {
        "id": "bench-route-006",
        "category": "route_accuracy",
        "difficulty": "hard",
        "season": 28,
        "question": "What Asian country did Season 28 visit for its penultimate legs, featuring a Roadblock climbing the Canton Tower?",
        "reference_answer": "China (Guangzhou / Shenzhen).",
        "key_facts": ["China", "Guangzhou"],
        "context_docs": ["season_28_route"],
    },
    {
        "id": "bench-route-007",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 31,
        "question": "Season 31 pitted reality show stars from Survivor, Big Brother, and TAR. Where was the starting line located?",
        "reference_answer": "Hermosa Beach Pier in Hermosa Beach, California.",
        "key_facts": ["Hermosa Beach", "California"],
        "context_docs": ["season_31_route"],
    },
    {
        "id": "bench-route-008",
        "category": "route_accuracy",
        "difficulty": "hard",
        "season": 33,
        "question": "How did the route of Season 33 change dramatically due to the COVID-19 pandemic suspension?",
        "reference_answer": "Filming was suspended after Leg 3 in Scotland. When production restarted 19 months later, teams flew exclusively on a chartered Boeing 757 aircraft and visited only European countries.",
        "key_facts": ["COVID", "charter", "Scotland", "Europe"],
        "context_docs": ["season_33_route"],
    },
    {
        "id": "bench-route-009",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 35,
        "question": "Where was the final finish line pit stop located in Season 35?",
        "reference_answer": "Philadelphia, Pennsylvania (Benjamin Franklin National Memorial / Philadelphia Museum of Art).",
        "key_facts": ["Philadelphia", "Pennsylvania"],
        "context_docs": ["season_35_route"],
    },
    {
        "id": "bench-route-010",
        "category": "route_accuracy",
        "difficulty": "easy",
        "season": 36,
        "question": "What Mexican city served as the starting international destination in Season 36?",
        "reference_answer": "Puerto Vallarta, Mexico.",
        "key_facts": ["Puerto Vallarta", "Mexico"],
        "context_docs": ["season_36_route"],
    },
    {
        "id": "bench-route-011",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 7,
        "question": "What direction did Season 7 travel around the globe, making it the first season to do so?",
        "reference_answer": "Westward around the world.",
        "key_facts": ["Westward", "west"],
        "context_docs": ["season_7_route"],
    },
    {
        "id": "bench-route-012",
        "category": "route_accuracy",
        "difficulty": "hard",
        "season": 11,
        "question": "In Season 11 (All-Stars), how many continents were visited during the race route?",
        "reference_answer": "6 continents (North America, South America, Africa, Europe, Asia, and Oceania/Australia).",
        "key_facts": ["6 continents", "6"],
        "context_docs": ["season_11_route"],
    },
    {
        "id": "bench-route-013",
        "category": "route_accuracy",
        "difficulty": "medium",
        "season": 16,
        "question": "Where was the starting line of The Amazing Race Season 16?",
        "reference_answer": "Dodger Stadium in Los Angeles, California.",
        "key_facts": ["Dodger Stadium", "Los Angeles"],
        "context_docs": ["season_16_route"],
    },
    {
        "id": "bench-route-014",
        "category": "route_accuracy",
        "difficulty": "hard",
        "season": 23,
        "question": "Where was the starting line for The Amazing Race Season 23?",
        "reference_answer": "Melody Ranch Motion Picture Studio in Santa Clarita, California.",
        "key_facts": ["Melody Ranch", "Santa Clarita"],
        "context_docs": ["season_23_route"],
    },
    {
        "id": "bench-route-015",
        "category": "route_accuracy",
        "difficulty": "easy",
        "season": 32,
        "question": "Where was the starting line for The Amazing Race Season 32?",
        "reference_answer": "The Hollywood Bowl in Los Angeles, California.",
        "key_facts": ["Hollywood Bowl", "Los Angeles"],
        "context_docs": ["season_32_route"],
    },
]


class BenchmarkSuite:
    """Manages TAR AI evaluation prompts and scoring harness."""

    def __init__(
        self,
        benchmark_file: Path | str = "data/ai/tar_benchmark_suite.jsonl",
    ) -> None:
        self.benchmark_file = Path(benchmark_file)

    def save_default_suite(self) -> Path:
        """Save the default curated benchmark items to disk."""
        self.benchmark_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.benchmark_file, "w", encoding="utf-8") as f:
            f.writelines(
                json.dumps(item, ensure_ascii=False) + "\n" for item in BENCHMARK_ITEMS
            )
        logger.info(
            "Saved %d benchmark test items to %s",
            len(BENCHMARK_ITEMS),
            self.benchmark_file,
        )
        return self.benchmark_file

    def load_suite(self) -> list[dict[str, Any]]:
        """Load benchmark suite from file or default to built-in items."""
        if not self.benchmark_file.exists():
            self.save_default_suite()

        items = []
        with open(self.benchmark_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    @staticmethod
    def score_response(item: dict[str, Any], response: str) -> dict[str, Any]:
        """Score a response by checking keyword/factual accuracy criteria."""
        response_lower = response.lower()
        key_facts = item.get("key_facts", [])

        if not key_facts:
            return {
                "score": 1.0,
                "passed": True,
                "matched_facts": [],
                "missing_facts": [],
            }

        matched = [fact for fact in key_facts if fact.lower() in response_lower]
        missing = [fact for fact in key_facts if fact.lower() not in response_lower]

        # Score is proportional to matched facts
        score = len(matched) / len(key_facts)
        passed = score >= 0.5  # Passing threshold

        return {
            "score": round(score, 3),
            "passed": passed,
            "matched_facts": matched,
            "missing_facts": missing,
        }

    def evaluate_benchmark(
        self,
        eval_fn: Callable[[str], str] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a model or run self-evaluation using the reference answers."""
        suite = self.load_suite()

        results_by_cat: dict[str, list[dict[str, Any]]] = {
            "trivia": [],
            "rules_comprehension": [],
            "route_accuracy": [],
        }

        total_score = 0.0
        total_passed = 0

        for item in suite:
            cat = item.get("category", "trivia")
            question = item.get("question", "")

            # If no eval function provided, test reference answer against rubrics
            response = (
                eval_fn(question) if eval_fn else item.get("reference_answer", "")
            )
            eval_result = self.score_response(item, response)

            result_entry = {
                "id": item.get("id"),
                "question": question,
                "score": eval_result["score"],
                "passed": eval_result["passed"],
                "matched_facts": eval_result["matched_facts"],
                "missing_facts": eval_result["missing_facts"],
            }
            results_by_cat.setdefault(cat, []).append(result_entry)

            total_score += eval_result["score"]
            if eval_result["passed"]:
                total_passed += 1

        total_questions = len(suite)
        avg_score = total_score / total_questions if total_questions else 0.0

        summary = {
            "total_questions": total_questions,
            "total_passed": total_passed,
            "pass_rate": round(total_passed / total_questions, 3)
            if total_questions
            else 0.0,
            "average_score": round(avg_score, 3),
            "categories": {},
        }

        for cat, items in results_by_cat.items():
            cat_count = len(items)
            cat_passed = sum(1 for i in items if i["passed"])
            cat_score = sum(i["score"] for i in items) / cat_count if cat_count else 0.0
            summary["categories"][cat] = {
                "count": cat_count,
                "passed": cat_passed,
                "pass_rate": round(cat_passed / cat_count, 3) if cat_count else 0.0,
                "avg_score": round(cat_score, 3),
            }

        return summary

    def render_summary(self, summary: dict[str, Any]) -> None:
        """Render evaluation summary using Rich."""
        console = Console()
        table = Table(title="The Amazing Race AI Benchmark Results", show_lines=True)
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Evaluated", style="magenta", justify="right")
        table.add_column("Passed", style="green", justify="right")
        table.add_column("Pass Rate", style="yellow", justify="right")
        table.add_column("Average Score", style="bold green", justify="right")

        for cat, data in summary.get("categories", {}).items():
            table.add_row(
                cat.replace("_", " ").title(),
                str(data["count"]),
                str(data["passed"]),
                f"{data['pass_rate'] * 100:.1f}%",
                f"{data['avg_score'] * 100:.1f}%",
            )

        table.add_row(
            "[bold]Total / Overall[/bold]",
            f"[bold]{summary['total_questions']}[/bold]",
            f"[bold]{summary['total_passed']}[/bold]",
            f"[bold]{summary['pass_rate'] * 100:.1f}%[/bold]",
            f"[bold]{summary['average_score'] * 100:.1f}%[/bold]",
        )
        console.print(table)
