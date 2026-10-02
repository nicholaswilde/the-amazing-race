"""Native R language dataset export and companion R data package scaffolding.

Exports processed The Amazing Race datasets into compressed .rds and .rda formats
and maintains the companion R data package structure in r/.
"""

from __future__ import annotations

import gzip
import logging
import lzma
import re
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadr

logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "episodes",
    "contestants",
    "teams",
    "legs",
    "leg_results",
    "tasks",
]

# Explicit type mapping to ensure idiomatic R types (integers, booleans, strings, numerics)
INTEGER_COLUMNS = {
    "seasons": ["season", "n_teams", "n_legs", "n_episodes"],
    "episodes": ["season", "episode"],
    "contestants": ["season", "age"],
    "teams": ["season", "result", "legs_won", "legs_completed", "podium_count"],
    "legs": ["season", "leg_number", "itinerary_stops", "tasks_count"],
    "leg_results": ["season", "leg_number", "placement"],
    "tasks": ["season", "leg_number"],
}

BOOLEAN_COLUMNS = {
    "leg_results": [
        "is_non_elimination",
        "fast_forward",
        "uturn",
        "yield",
        "speed_bump",
    ],
}

FLOAT_COLUMNS = {
    "seasons": ["distance_miles", "distance_km"],
    "episodes": ["viewers_millions"],
    "teams": ["racing_average", "placement_std", "podium_rate"],
}

TABLE_DOCUMENTATION = {
    "seasons": {
        "title": "Seasons in The Amazing Race",
        "description": "Season-level metadata, route summary statistics, and winning teams across all seasons.",
        "columns": {
            "version": "Franchise country code ('US', 'CAN', 'AUS', etc.)",
            "season": "Season number (integer)",
            "n_teams": "Total number of competing teams",
            "n_legs": "Total number of legs in the season",
            "n_episodes": "Total number of broadcast episodes",
            "winners": "Names of the winning team members",
            "distance_miles": "Total race travel distance in miles",
            "distance_km": "Total race travel distance in kilometers",
            "air_dates": "Season premiere and finale broadcast date range",
            "filming_dates": "Season filming date range",
            "wiki_url": "Wikipedia source page URL",
        },
    },
    "episodes": {
        "title": "Episodes of The Amazing Race",
        "description": "Episode-level broadcast metadata, titles, premiere air dates, and Nielsen television viewership ratings.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "episode": "Episode number within the season (integer)",
            "title": "Official broadcast episode title",
            "air_date": "Original television broadcast date (YYYY-MM-DD)",
            "viewers_millions": "US broadcast viewership in millions",
        },
    },
    "contestants": {
        "title": "Contestants in The Amazing Race",
        "description": "Individual contestant demographics, ages, relationship categories, and hometown residences.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "contestant_id": "Unique alphanumeric contestant identifier",
            "name": "Full name of the contestant",
            "age": "Age of the contestant during filming (integer)",
            "gender": "Gender of the contestant (M, F, NB)",
            "relationship": "Stated relationship to race teammate",
            "hometown": "City and state of permanent residence",
            "hometown_state": "Parsed US state two-letter postal code or region",
            "hometown_country": "Hometown country code (e.g. USA)",
            "status": "Finishing status (e.g. Winners, Runners-up, Eliminated)",
        },
    },
    "teams": {
        "title": "Teams in The Amazing Race",
        "description": "Two-person team statistics, relationship classifications, final finish placement, and total leg victories.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "team_id": "Unique team identifier",
            "team_name": "Combined names of both team members",
            "relationship": "Relationship classification (e.g. Married, Dating, Siblings, Friends)",
            "hometown": "Hometown location of the team",
            "result": "Final race finish placement (1 = Champions, integer)",
            "status": "Finishing status description",
            "legs_won": "Count of first-place leg finishes won by the team (integer)",
            "legs_completed": "Total number of legs completed before elimination or victory (integer)",
            "racing_average": "Average leg finish placement across all completed legs (numeric)",
            "placement_std": "Standard deviation of leg finish placements (numeric)",
            "podium_count": "Total count of Top-3 leg finishes (integer)",
            "podium_rate": "Proportion of completed legs finishing in Top-3 (numeric)",
            "gender_composition": "Team gender composition (MM, FF, MF)",
        },
    },
    "legs": {
        "title": "Legs and Travel Routes in The Amazing Race",
        "description": "Leg-level travel route summaries, itinerary waypoints count, task counts, and route narratives.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "leg_number": "Leg number within the season (integer)",
            "route_header": "Locations and countries traversed during the leg",
            "origin_country": "Origin country three-letter ISO code (e.g. USA, FRA)",
            "destination_country": "Destination country three-letter ISO code (e.g. ZMB, JPN)",
            "destination_city": "Primary destination city or region of the leg",
            "destination_continent": "Destination continent name (e.g. Africa, Europe, Asia)",
            "itinerary_stops": "Count of distinct route waypoints and stops (integer)",
            "tasks_count": "Count of challenge checkpoints on the leg (integer)",
            "narrative": "Comprehensive narrative detailing route travel, navigation challenges, and leg storyline",
        },
    },
    "leg_results": {
        "title": "Leg Results and Placements in The Amazing Race",
        "description": "Finish placements, arrival ranks, and game-mechanic penalties/advantages for each team on every leg.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "leg_number": "Leg number within the season (integer)",
            "team_name": "Name of the competing team",
            "placement": "Finishing rank on this leg (integer)",
            "raw_cell": "Original unparsed result table cell indicator",
            "is_non_elimination": "Logical flag indicating if the leg was a predetermined Non-Elimination Leg",
            "fast_forward": "Logical flag indicating if the team successfully utilized a Fast Forward",
            "uturn": "Logical flag indicating if the team was targeted by a U-Turn penalty",
            "yield": "Logical flag indicating if the team was targeted by a Yield penalty",
            "speed_bump": "Logical flag indicating if the team served a Speed Bump penalty",
        },
    },
    "tasks": {
        "title": "Tasks and Challenges in The Amazing Race",
        "description": "Detailed breakdowns of all Roadblocks, Detours, Fast Forwards, and Route Info challenges.",
        "columns": {
            "version": "Franchise country code",
            "season": "Season number (integer)",
            "leg_number": "Leg number within the season (integer)",
            "task_type": "Task category ('Roadblock', 'Detour', 'Fast Forward', 'Route Info', 'Speed Bump')",
            "description": "Full description of task requirements, rules, and location",
        },
    },
}


def _write_deterministic_rds(path: Path, df: pd.DataFrame) -> None:
    """Write an RDS file with deterministic gzip compression (mtime=0)."""
    with tempfile.NamedTemporaryFile(suffix=".rds", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        pyreadr.write_rds(tmp_path, df)
        raw_bytes = tmp_path.read_bytes()
        compressed = gzip.compress(raw_bytes, compresslevel=9, mtime=0)
        path.write_bytes(compressed)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _write_deterministic_rdata(
    path: Path, df: pd.DataFrame, df_name: str, compress: str = "xz"
) -> None:
    """Write an RDA file with deterministic xz (or gzip) compression."""
    with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        pyreadr.write_rdata(tmp_path, df, df_name=df_name)
        raw_bytes = tmp_path.read_bytes()
        if compress == "xz":
            compressed = lzma.compress(raw_bytes, preset=9)
        else:
            compressed = gzip.compress(raw_bytes, compresslevel=9, mtime=0)
        path.write_bytes(compressed)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


class RExporter:
    """Exports processed TAR datasets into .rds and .rda files and maintains companion R package."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        r_output_dir: Path | str = "data/processed/r",
        r_pkg_dir: Path | str = "r",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.r_output_dir = Path(r_output_dir)
        self.r_pkg_dir = Path(r_pkg_dir)

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a processed table from Parquet (or fallback to CSV) and format types for R."""
        parquet_file = self.processed_dir / f"{table_name}.parquet"
        csv_file = self.processed_dir / f"{table_name}.csv"

        if parquet_file.exists():
            df = pd.read_parquet(parquet_file)
        elif csv_file.exists():
            df = pd.read_csv(csv_file)
        else:
            raise FileNotFoundError(
                f"Table {table_name} not found in {self.processed_dir} (.parquet or .csv)"
            )

        # Cast integer columns to int32 so pyreadr writes native R 32-bit integers
        int_cols = INTEGER_COLUMNS.get(table_name, [])
        for col in int_cols:
            if col in df.columns:
                df[col] = (
                    pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int32")
                )

        # Cast boolean columns to bool
        bool_cols = BOOLEAN_COLUMNS.get(table_name, [])
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        # Cast float columns
        float_cols = FLOAT_COLUMNS.get(table_name, [])
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

        # Ensure strings
        for col in df.columns:
            if col not in int_cols and col not in bool_cols and col not in float_cols:
                df[col] = df[col].astype(str)

        return df

    def export_rds(self) -> dict[str, Path]:
        """Export each processed table as a gzip-compressed .rds file."""
        self.r_output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)
            out_path = self.r_output_dir / f"{table_name}.rds"
            _write_deterministic_rds(out_path, df)
            results[table_name] = out_path
            logger.info("Exported RDS table: %s (%d rows)", out_path, len(df))

        return results

    def export_rda(self) -> dict[str, Path]:
        """Export each table as a compressed .rda file into the R package data directory."""
        pkg_data_dir = self.r_pkg_dir / "data"
        pkg_data_dir.mkdir(parents=True, exist_ok=True)
        self.r_output_dir.mkdir(parents=True, exist_ok=True)

        results: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)

            # Export to R package data directory
            pkg_out = pkg_data_dir / f"{table_name}.rda"
            _write_deterministic_rdata(pkg_out, df, df_name=table_name)

            # Also mirror into data/processed/r/
            mirror_out = self.r_output_dir / f"{table_name}.rda"
            _write_deterministic_rdata(mirror_out, df, df_name=table_name)

            results[table_name] = pkg_out
            logger.info("Exported RDA table: %s (%d rows)", pkg_out, len(df))

        return results

    def generate_roxygen_docs(self) -> Path:
        """Generate R/data.R roxygen2 documentation for all datasets."""
        r_dir = self.r_pkg_dir / "R"
        r_dir.mkdir(parents=True, exist_ok=True)
        data_r_path = r_dir / "data.R"

        chunks: list[str] = [
            "# Auto-generated documentation for theamazingrace datasets",
            "# Generated from schemas.py and processed tables. Do not edit by hand.",
            "",
        ]

        for table_name in TABLES:
            doc_meta = TABLE_DOCUMENTATION.get(table_name, {})
            title = doc_meta.get(
                "title", f"{table_name.capitalize()} in The Amazing Race"
            )
            desc = doc_meta.get("description", f"Tidy dataset of {table_name}.")
            columns = doc_meta.get("columns", {})

            # Try to get actual row/col count
            parquet_file = self.processed_dir / f"{table_name}.parquet"
            if parquet_file.exists():
                df = pd.read_parquet(parquet_file)
                n_rows = len(df)
                n_cols = len(df.columns)
            else:
                n_rows = 0
                n_cols = len(columns)

            chunks.append(f"#' {title}")
            chunks.append("#'")
            chunks.append(f"#' {desc}")
            chunks.append("#'")
            chunks.append(
                f"#' @format A data frame with {n_rows} rows and {n_cols} variables:"
            )
            chunks.append("#' \\describe{")
            for col_name, col_desc in columns.items():
                chunks.append(f"#'   \\item{{{col_name}}}{{{col_desc}}}")
            chunks.append("#' }")
            chunks.append(
                "#' @source \\url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}"
            )
            chunks.append(f'"{table_name}"')
            chunks.append("")

        data_r_path.write_text("\n".join(chunks), encoding="utf-8")
        logger.info("Generated roxygen documentation in %s", data_r_path)
        return data_r_path

    def scaffold_package(self) -> dict[str, Path]:
        """Scaffold companion R package metadata, vignettes, tests, and documentation."""
        self.r_pkg_dir.mkdir(parents=True, exist_ok=True)
        created_files: dict[str, Path] = {}

        # 1. DESCRIPTION
        desc_path = self.r_pkg_dir / "DESCRIPTION"
        version = "0.1.0"
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            m_ver = re.search(
                r'version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8")
            )
            if m_ver:
                version = m_ver.group(1)
        elif desc_path.exists():
            m_ver = re.search(
                r"Version:\s*([^\n\r]+)", desc_path.read_text(encoding="utf-8")
            )
            if m_ver:
                version = m_ver.group(1).strip()

        desc_content = f"""Package: theamazingrace
Title: The Amazing Race Tidy Datasets
Version: {version}
Authors@R: person("Nicholas", "Wilde", email = "nicholas@nicholaswilde.io", role = c("aut", "cre"))
Description: Comprehensive tidy datasets for the television series The
    Amazing Race. Contains clean tabular data on seasons, episodes,
    contestants, teams, legs, leg results, and tasks for exploratory data
    analysis, statistical modeling, route mapping, and game show survival
    analysis. Inspired by packages like alone, survivoR, and bakeoff.
License: Apache License (== 2.0)
URL: https://github.com/nicholaswilde/the-amazing-race
BugReports: https://github.com/nicholaswilde/the-amazing-race/issues
Depends:
    R (>= 3.5.0)
LazyData: true
LazyDataCompression: xz
ByteCompile: true
RoxygenNote: 7.3.1
Suggests:
    arrow,
    dplyr,
    ggplot2,
    knitr,
    rmarkdown,
    testthat (>= 3.0.0),
    tibble
VignetteBuilder: knitr
Encoding: UTF-8
"""
        desc_path.write_text(desc_content, encoding="utf-8")
        created_files["DESCRIPTION"] = desc_path

        # 2. NAMESPACE
        namespace_path = self.r_pkg_dir / "NAMESPACE"
        namespace_content = """# Generated by roxygen2: do not edit by hand

export(contestants)
export(episodes)
export(leg_results)
export(legs)
export(seasons)
export(tasks)
export(teams)
"""
        namespace_path.write_text(namespace_content, encoding="utf-8")
        created_files["NAMESPACE"] = namespace_path

        # 3. .Rbuildignore
        buildignore_path = self.r_pkg_dir / ".Rbuildignore"
        buildignore_content = """^.*\\.Rproj$
^\\.Rproj\\.user$
^tests/testthat/_snaps$
^LICENSE$
"""
        buildignore_path.write_text(buildignore_content, encoding="utf-8")
        created_files[".Rbuildignore"] = buildignore_path

        # 4. README.md
        readme_path = self.r_pkg_dir / "README.md"
        readme_content = """# theamazingrace <img src="man/figures/logo.png" align="right" height="139" alt="" />

<!-- badges: start -->
[![R-universe](https://nicholaswilde.r-universe.dev/badges/theamazingrace)](https://nicholaswilde.r-universe.dev)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
<!-- badges: end -->

A comprehensive, tidy dataset and companion R package for the multi-Emmy award-winning reality television series **The Amazing Race** (US Franchise, Seasons 1–36+).

Modeled after popular reality TV tidy data packages such as `alone`, `survivoR`, and `bakeoff`.

## Installation

Install the development version of **theamazingrace** directly from GitHub:

```r
# install.packages("remotes")
remotes::install_github("nicholaswilde/the-amazing-race/r")
```

Or install via R-universe:

```r
install.packages("theamazingrace", repos = "https://nicholaswilde.r-universe.dev")
```

## Datasets Included

The package exports 7 clean, relational data frames:

| Dataset | Rows | Description |
| :--- | :--- | :--- |
| `seasons` | 36 | Season dates, distance traveled, winning teams, and route totals |
| `episodes` | 356 | Broadcast episode titles, premiere air dates, and Nielsen ratings |
| `contestants` | 832 | Contestant demographics, ages, hometowns, and occupations |
| `teams` | 404 | Two-person teams, relationship categories, and final placements |
| `legs` | 429 | Leg-by-leg routing, countries visited, itinerary stops, and narratives |
| `leg_results` | 3,001 | Arrival placements, non-eliminations, Fast Forwards, and U-Turns |
| `tasks` | 1,621 | Roadblocks, Detours, Route Info challenges, and descriptions |

## Quickstart

```r
library(theamazingrace)
library(dplyr)
library(ggplot2)

# Inspect seasons overview
head(seasons)

# Average race distance over eras
seasons |>
  mutate(era = case_when(
    season <= 10 ~ "Early Era (1-10)",
    season <= 20 ~ "Middle Era (11-20)",
    season <= 30 ~ "Modern Era (21-30)",
    TRUE         ~ "Recent Era (31-36)"
  )) |>
  group_by(era) |>
  summarize(
    avg_distance = mean(distance_miles, na.rm = TRUE),
    total_episodes = sum(n_episodes)
  )

# Explore Fast Forward usage
leg_results |>
  filter(fast_forward) |>
  count(team_name, sort = TRUE)
```

## Direct Parquet / Arrow Usage

For users who prefer high-performance columnar reads without loading package `.rda` objects, read the pre-compiled Parquet tables directly using the `{arrow}` package:

```r
library(arrow)

seasons <- read_parquet("https://github.com/nicholaswilde/the-amazing-race/raw/main/data/processed/seasons.parquet")
episodes <- read_parquet("https://github.com/nicholaswilde/the-amazing-race/raw/main/data/processed/episodes.parquet")
```

## License

This package is licensed under the Apache License 2.0.
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        created_files["README.md"] = readme_path

        # 5. Vignette: vignettes/introduction.Rmd
        vignettes_dir = self.r_pkg_dir / "vignettes"
        vignettes_dir.mkdir(parents=True, exist_ok=True)
        vignette_path = vignettes_dir / "introduction.Rmd"
        vignette_content = """---
title: "Introduction to theamazingrace"
output: rmarkdown::html_vignette
vignette: >
  %\\VignetteIndexEntry{Introduction to theamazingrace}
  %\\VignetteEngine{knitr::rmarkdown}
  %\\VignetteEncoding{UTF-8}
---

```{r, include = FALSE}
knitr::opts_chunk$set(
  collapse = TRUE,
  comment = "#>"
)
```

## Overview

The `theamazingrace` package provides tidy datasets for the multi-Emmy award-winning television series **The Amazing Race** (US Franchise, Seasons 1–36).

The data is structured into seven relational tables:
1. `seasons`: Season summaries, dates, distance traveled, and winners.
2. `episodes`: Episode titles, premiere air dates, and Nielsen television ratings.
3. `contestants`: Individual contestant demographics, ages, hometowns, and relationships.
4. `teams`: Team configurations, relationships, final finish placements, and legs won.
5. `legs`: Leg-level routing, countries visited, itinerary stops, and detailed narratives.
6. `leg_results`: Team finishing order on each leg, non-eliminations, Fast Forwards, and U-Turns.
7. `tasks`: Challenge descriptions across Roadblocks, Detours, Route Info, and Speed Bumps.

## Setup and Data Inspection

```{r setup, eval = FALSE}
library(theamazingrace)
library(dplyr)
library(ggplot2)

data(seasons)
data(episodes)
data(leg_results)
data(tasks)
```

## Analysis 1: Season Distance Trends

How has total race distance changed across the 36 seasons?

```{r distance-trend, eval = FALSE}
ggplot(seasons, aes(x = season, y = distance_miles)) +
  geom_line(color = "#1f77b4", size = 1) +
  geom_point(color = "#d62728", size = 2) +
  theme_minimal() +
  labs(
    title = "Total Race Distance per Season",
    x = "Season",
    y = "Distance (Miles)"
  )
```

## Analysis 2: Task Types Breakdown

What types of challenges appear most frequently across all legs?

```{r task-types, eval = FALSE}
tasks |>
  count(task_type, sort = TRUE)
```

## Analysis 3: Team Placement Trajectories

Trace the path of the winning team through the race:

```{r winner-trajectory, eval = FALSE}
s1_winners <- leg_results |>
  filter(season == 1, team_name == "Rob & Brennan")

ggplot(s1_winners, aes(x = leg_number, y = placement)) +
  geom_line() +
  geom_point(size = 3) +
  scale_y_reverse(breaks = 1:11) +
  theme_minimal() +
  labs(
    title = "Rob & Brennan's Leg Placements (Season 1)",
    x = "Leg Number",
    y = "Placement (1st = Top)"
  )
```
"""
        vignette_path.write_text(vignette_content, encoding="utf-8")
        created_files["vignettes/introduction.Rmd"] = vignette_path

        # 6. Tests: tests/testthat.R and tests/testthat/test-datasets.R
        tests_dir = self.r_pkg_dir / "tests" / "testthat"
        tests_dir.mkdir(parents=True, exist_ok=True)

        testthat_runner = self.r_pkg_dir / "tests" / "testthat.R"
        testthat_runner.write_text(
            'library(testthat)\nlibrary(theamazingrace)\n\ntest_check("theamazingrace")\n',
            encoding="utf-8",
        )
        created_files["tests/testthat.R"] = testthat_runner

        test_datasets = tests_dir / "test-datasets.R"
        test_datasets_content = """test_that("all 7 datasets exist and have expected structure", {
  expect_true(exists("seasons"))
  expect_true(exists("episodes"))
  expect_true(exists("contestants"))
  expect_true(exists("teams"))
  expect_true(exists("legs"))
  expect_true(exists("leg_results"))
  expect_true(exists("tasks"))

  tables <- list(
    seasons = seasons,
    episodes = episodes,
    contestants = contestants,
    teams = teams,
    legs = legs,
    leg_results = leg_results,
    tasks = tasks
  )

  for (name in names(tables)) {
    df <- tables[[name]]
    expect_s3_class(df, "data.frame")
    expect_gt(nrow(df), 0)
    expect_gt(ncol(df), 0)
    expect_true("season" %in% names(df))
    expect_true("version" %in% names(df))
  }
})

test_that("seasons dataset has all 36 seasons", {
  expect_gte(nrow(seasons), 36)
  expect_true(is.integer(seasons$season))
})

test_that("leg_results has boolean flag columns", {
  expect_true(is.logical(leg_results$is_non_elimination))
  expect_true(is.logical(leg_results$fast_forward))
})
"""
        test_datasets.write_text(test_datasets_content, encoding="utf-8")
        created_files["tests/testthat/test-datasets.R"] = test_datasets

        return created_files

    def export_all(self) -> dict[str, Any]:
        """Perform full R export: RDS files, RDA package data, roxygen docs, and package scaffolding."""
        rds_results = self.export_rds()
        rda_results = self.export_rda()
        roxygen_file = self.generate_roxygen_docs()
        scaffold_files = self.scaffold_package()

        return {
            "rds": rds_results,
            "rda": rda_results,
            "roxygen": roxygen_file,
            "scaffold": scaffold_files,
        }


def export_to_r(
    processed_dir: Path | str = "data/processed",
    r_output_dir: Path | str = "data/processed/r",
    r_pkg_dir: Path | str = "r",
) -> dict[str, Any]:
    """Helper function to run the full R export pipeline."""
    exporter = RExporter(
        processed_dir=processed_dir,
        r_output_dir=r_output_dir,
        r_pkg_dir=r_pkg_dir,
    )
    return exporter.export_all()
