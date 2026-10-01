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

        # 4. Gender checks
        if "contestants" in dfs:
            c_df = dfs["contestants"]
            if "gender" in c_df.columns:
                null_gender = c_df["gender"].isna().sum()
                if null_gender > 0:
                    report["issues"].append(
                        f"Found {null_gender} missing gender values in contestants.csv"
                    )
                invalid_gender = (~c_df["gender"].dropna().isin(["M", "F", "NB"])).sum()
                if invalid_gender > 0:
                    report["issues"].append(
                        f"Found {invalid_gender} invalid gender values in contestants.csv"
                    )

        if "teams" in dfs:
            t_df = dfs["teams"]
            if "gender_composition" in t_df.columns:
                null_comp = t_df["gender_composition"].isna().sum()
                if null_comp > 0:
                    report["issues"].append(
                        f"Found {null_comp} missing gender_composition values in teams.csv"
                    )
                invalid_comp = (
                    ~t_df["gender_composition"].dropna().isin(["MM", "FF", "MF"])
                ).sum()
                if invalid_comp > 0:
                    report["issues"].append(
                        f"Found {invalid_comp} invalid gender_composition values in teams.csv"
                    )

            # 5. Racing metrics checks on teams
            if "racing_average" in t_df.columns and "legs_completed" in t_df.columns:
                completed_teams = t_df[t_df["legs_completed"] > 0]
                null_ra = completed_teams["racing_average"].isna().sum()
                if null_ra > 0:
                    report["issues"].append(
                        f"Found {null_ra} teams with completed legs missing racing_average in teams.csv"
                    )
                invalid_ra = (completed_teams["racing_average"] < 1.0).sum()
                if invalid_ra > 0:
                    report["issues"].append(
                        f"Found {invalid_ra} teams with invalid racing_average (< 1.0) in teams.csv"
                    )

            if "podium_rate" in t_df.columns and "legs_completed" in t_df.columns:
                completed_teams = t_df[t_df["legs_completed"] > 0]
                invalid_pr = (
                    (completed_teams["podium_rate"] < 0.0)
                    | (completed_teams["podium_rate"] > 1.0)
                ).sum()
                if invalid_pr > 0:
                    report["issues"].append(
                        f"Found {invalid_pr} teams with invalid podium_rate outside [0, 1] in teams.csv"
                    )

        # 6. Geography checks on legs
        if "legs" in dfs:
            l_df = dfs["legs"]
            if (
                "origin_country" in l_df.columns
                and "destination_country" in l_df.columns
            ):
                null_orig = l_df["origin_country"].isna().sum()
                null_dest = l_df["destination_country"].isna().sum()
                if null_orig > 0:
                    report["issues"].append(
                        f"Found {null_orig} legs with missing origin_country in legs.csv"
                    )
                if null_dest > 0:
                    report["issues"].append(
                        f"Found {null_dest} legs with missing destination_country in legs.csv"
                    )
            if "destination_continent" in l_df.columns:
                valid_continents = {
                    "Africa",
                    "Asia",
                    "Europe",
                    "North America",
                    "Oceania",
                    "South America",
                    "Antarctica",
                }
                invalid_cont = (
                    ~l_df["destination_continent"].dropna().isin(valid_continents)
                ).sum()
                if invalid_cont > 0:
                    report["issues"].append(
                        f"Found {invalid_cont} invalid destination_continent values in legs.csv"
                    )

        # 7. Geography checks on contestants
        if "contestants" in dfs:
            c_df = dfs["contestants"]
            if "hometown_country" in c_df.columns:
                null_hc = c_df["hometown_country"].isna().sum()
                if null_hc > 0:
                    report["issues"].append(
                        f"Found {null_hc} contestants with missing hometown_country in contestants.csv"
                    )

        if report["issues"]:
            report["status"] = (
                "WARNING"
                if all("Missing" not in i for i in report["issues"])
                else "FAIL"
            )

        return report
