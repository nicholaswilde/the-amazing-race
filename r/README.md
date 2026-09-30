# theamazingrace <img src="man/figures/logo.png" align="right" height="139" alt="" />

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
