# ------------------------------------------------------------------------------
# TidyTuesday: The Amazing Race (US Seasons 1–38)
# Data Cleaning & Preparation Script
# ------------------------------------------------------------------------------
# This script loads, validates, and cleans the relational tables comprising
# The Amazing Race dataset for R4DS TidyTuesday.
# ------------------------------------------------------------------------------

library(tidyverse)

# Base raw repository URL
base_raw_url <- "https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/data/processed/"

# Helper to load either from local directory if available, or fall back to GitHub raw
load_table <- function(name) {
  local_path <- file.path("data", "processed", paste0(name, ".csv"))
  if (file.exists(local_path)) {
    message("Loading local: ", local_path)
    read_csv(local_path, show_col_types = FALSE)
  } else {
    remote_url <- paste0(base_raw_url, name, ".csv")
    message("Fetching remote: ", remote_url)
    read_csv(remote_url, show_col_types = FALSE)
  }
}

# 1. Load Raw Tables
message("--- Loading raw tables ---")
raw_seasons     <- load_table("seasons")
raw_episodes    <- load_table("episodes")
raw_contestants <- load_table("contestants")
raw_teams       <- load_table("teams")
raw_legs        <- load_table("legs")
raw_leg_results <- load_table("leg_results")
raw_tasks       <- load_table("tasks")

# 2. Clean Seasons Table
# Standardize numeric types and factor levels
seasons <- raw_seasons |>
  mutate(
    season = as.integer(season),
    n_teams = as.integer(n_teams),
    n_legs = as.integer(n_legs),
    n_episodes = as.integer(n_episodes),
    distance_miles = as.numeric(distance_miles),
    distance_km = as.numeric(distance_km)
  ) |>
  arrange(season)

# 3. Clean Episodes Table
# Format dates and round viewership figures
episodes <- raw_episodes |>
  mutate(
    season = as.integer(season),
    episode = as.integer(episode),
    air_date = as.Date(air_date),
    viewers_millions = round(as.numeric(viewers_millions), 2)
  ) |>
  arrange(season, episode)

# 4. Clean Contestants Table
# Normalize gender codes, clean string fields, and cast integers
contestants <- raw_contestants |>
  mutate(
    season = as.integer(season),
    age = as.numeric(age),
    gender = case_when(
      gender %in% c("M", "Male") ~ "M",
      gender %in% c("F", "Female") ~ "F",
      gender %in% c("NB", "Non-binary") ~ "NB",
      TRUE ~ gender
    ),
    roadblocks_completed = as.integer(replace_na(roadblocks_completed, 0L))
  ) |>
  arrange(season, contestant_id)

# 5. Clean Teams Table
# Classify relationship archetypes, clean numeric metrics, and compute equity score
teams <- raw_teams |>
  mutate(
    season = as.integer(season),
    result = as.integer(result),
    legs_won = as.integer(replace_na(legs_won, 0L)),
    legs_completed = as.integer(legs_completed),
    racing_average = round(as.numeric(racing_average), 2),
    podium_count = as.integer(replace_na(podium_count, 0L)),
    podium_rate = round(as.numeric(podium_rate), 3),
    roadblock_equity_score = round(as.numeric(roadblock_equity_score), 2),
    relationship_category = case_when(
      str_detect(str_to_lower(relationship), "brother|sister|sibling|twin") ~ "Siblings",
      str_detect(str_to_lower(relationship), "dating|engaged|romantic|couple|boyfriend|girlfriend|partner") ~ "Dating",
      str_detect(str_to_lower(relationship), "married|husband|wife|spouse") ~ "Married",
      str_detect(str_to_lower(relationship), "father|mother|parent|son|daughter") ~ "Parent/Child",
      str_detect(str_to_lower(relationship), "friend|buddy|roommate|coworker|colleague") ~ "Friends",
      TRUE ~ "Other"
    )
  ) |>
  arrange(season, result)

# 6. Clean Legs Table
# Convert coordinates to numeric and ensure valid continent names
legs <- raw_legs |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number),
    destination_lat = as.numeric(destination_lat),
    destination_lon = as.numeric(destination_lon),
    itinerary_stops = as.integer(itinerary_stops),
    tasks_count = as.integer(tasks_count)
  ) |>
  arrange(season, leg_number)

# 7. Clean Leg Results Table
# Ensure boolean flags and numeric placement ranks
leg_results <- raw_leg_results |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number),
    placement = as.numeric(placement),
    is_non_elimination = as.logical(is_non_elimination),
    fast_forward = as.logical(fast_forward),
    uturn = as.logical(uturn),
    yield = as.logical(yield),
    speed_bump = as.logical(speed_bump)
  ) |>
  arrange(season, leg_number, placement)

# 8. Clean Tasks Table
# Categorize task types and trim white space
tasks <- raw_tasks |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number),
    task_type = str_trim(task_type),
    description = str_trim(description)
  ) |>
  arrange(season, leg_number, task_type)

# 9. Export Tidy Datasets
out_dir <- file.path("tidytuesday", "data")
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE)
}

message("--- Writing cleaned CSV files to ", out_dir, " ---")
write_csv(seasons,     file.path(out_dir, "seasons.csv"))
write_csv(episodes,    file.path(out_dir, "episodes.csv"))
write_csv(contestants, file.path(out_dir, "contestants.csv"))
write_csv(teams,       file.path(out_dir, "teams.csv"))
write_csv(legs,        file.path(out_dir, "legs.csv"))
write_csv(leg_results, file.path(out_dir, "leg_results.csv"))
write_csv(tasks,       file.path(out_dir, "tasks.csv"))

message("✓ All 7 TidyTuesday tables cleaned and exported successfully.")
