"""Data integrity validation for The Amazing Race dataset."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DatasetValidator:
    """Validates relational integrity, null rates, and domain rules across tables."""

    def __init__(self, processed_dir: Path | str = "data/processed") -> None:
        self.processed_dir = Path(processed_dir)

    def validate(self) -> dict[str, Any]:
        """Run all validation checks and return summary report."""
        report: dict[str, Any] = {
            "tables_found": [],
            "row_counts": {},
            "issues": [],
            "status": "PASS",
        }

        tables = [
            "seasons",
            "episodes",
            "contestants",
            "teams",
            "legs",
            "leg_results",
            "tasks",
        ]
        dfs: dict[str, pd.DataFrame] = {}

        for t in tables:
            csv_file = self.processed_dir / f"{t}.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                dfs[t] = df
                report["tables_found"].append(t)
                report["row_counts"][t] = len(df)
            else:
                report["issues"].append(f"Missing table: {t}.csv")

        if not dfs:
            report["status"] = "FAIL"
            report["issues"].append("No processed tables found.")
            return report

        # 1. Season checks
        if "seasons" in dfs:
            seasons_df = dfs["seasons"]
            if seasons_df["season"].duplicated().any():
                report["issues"].append("Duplicate season numbers found in seasons.csv")

            # Check that teams exist for each season
            if "teams" in dfs:
                for s in seasons_df["season"]:
                    teams_in_s = dfs["teams"][dfs["teams"]["season"] == s]
                    if len(teams_in_s) == 0:
                        report["issues"].append(f"Season {s} has no teams in teams.csv")

        # 2. Results placement checks
        if "leg_results" in dfs:
            res_df = dfs["leg_results"]
            null_placements = res_df["placement"].isna().sum()
            if null_placements > 0:
                report["issues"].append(
                    f"Found {null_placements} records with unresolved placement in leg_results.csv"
                )

        # 3. Contestant to Team consistency
        if "contestants" in dfs and "teams" in dfs:
            # Each season should have ~2x contestants as teams (except family edition ~4x)
            for s in dfs["teams"]["season"].unique():
                n_t = len(dfs["teams"][dfs["teams"]["season"] == s])
                n_c = len(dfs["contestants"][dfs["contestants"]["season"] == s])
                if n_c < n_t:
                    report["issues"].append(
                        f"Season {s}: fewer contestants ({n_c}) than teams ({n_t})"
                    )

        if report["issues"]:
            report["status"] = (
                "WARNING"
                if all("Missing" not in i for i in report["issues"])
                else "FAIL"
            )

        return report
