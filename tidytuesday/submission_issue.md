- [x] This dataset has not already been used in TidyTuesday.
- [x] The dataset will (probably) be less than 20MB when saved as a tidy CSV.
- [x] I can imagine a data visualization related to this dataset.

- [x] **title:** The Amazing Race (US Seasons 1–38)
- [x] **article:** An example of the dataset being used, such as a blog post or a README about the dataset.
  - [x] **title:** The Amazing Race Tidy Dataset & R Package Repository
  - [x] **url:** https://github.com/nicholaswilde/the-amazing-race
- [x] **data_source:** A source where the dataset can be downloaded.
  - [x] **title:** The Amazing Race Processed CSV Tables & Tidy Release Assets
  - [x] **url:** https://github.com/nicholaswilde/the-amazing-race/tree/main/data/processed
- [x] **images:** One or more images related to the dataset. For each image, provide:
  - [x] **file:** https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/dev/images/survival.png
  - [x] **alt:** Kaplan-Meier style team survival curves across 12 race legs grouped by relationship archetype (Dating, Married, Siblings, Friends, Parent/Child) with inset boxplots.
  - [x] **file:** https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/dev/images/roadblock_equity.png
  - [x] **alt:** Roadblock equity score evolution across seasons and task balance across team gender compositions.
  - [x] **file:** https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/dev/images/theamazingrace%20hex.png
  - [x] **alt:** Hexagonal sticker logo for the companion R package theamazingrace.

- [x] **cleaning_script:** A script to fetch and clean the data, resulting in one or more data.frames (or equivalent structures) that can be saved as CSVs.

```r
library(tidyverse)

# Base URL for processed data in GitHub repository
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/data/processed/"

# 1. Seasons summary
seasons <- read_csv(paste0(base_url, "seasons.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    n_teams = as.integer(n_teams),
    n_legs = as.integer(n_legs),
    n_episodes = as.integer(n_episodes),
    distance_miles = as.numeric(distance_miles),
    distance_km = as.numeric(distance_km)
  )

# 2. Episodes and broadcast ratings
episodes <- read_csv(paste0(base_url, "episodes.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    episode = as.integer(episode),
    air_date = as.Date(air_date),
    viewers_millions = as.numeric(viewers_millions)
  )

# 3. Contestants demographics
contestants <- read_csv(paste0(base_url, "contestants.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    age = as.numeric(age),
    roadblocks_completed = as.integer(replace_na(roadblocks_completed, 0L))
  )

# 4. Teams, relationships, and performance
teams <- read_csv(paste0(base_url, "teams.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    result = as.integer(result),
    legs_won = as.integer(replace_na(legs_won, 0L)),
    legs_completed = as.integer(legs_completed),
    racing_average = as.numeric(racing_average),
    podium_count = as.integer(replace_na(podium_count, 0L)),
    podium_rate = as.numeric(podium_rate),
    roadblock_equity_score = as.numeric(roadblock_equity_score)
  )

# 5. Leg routes and waypoints
legs <- read_csv(paste0(base_url, "legs.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number),
    destination_lat = as.numeric(destination_lat),
    destination_lon = as.numeric(destination_lon),
    itinerary_stops = as.integer(itinerary_stops),
    tasks_count = as.integer(tasks_count)
  )

# 6. Leg results and finish placements
leg_results <- read_csv(paste0(base_url, "leg_results.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number),
    placement = as.numeric(placement),
    is_non_elimination = as.logical(is_non_elimination),
    fast_forward = as.logical(fast_forward),
    uturn = as.logical(uturn),
    yield = as.logical(yield),
    speed_bump = as.logical(speed_bump)
  )

# 7. Task and challenge details
tasks <- read_csv(paste0(base_url, "tasks.csv"), show_col_types = FALSE) |>
  mutate(
    season = as.integer(season),
    leg_number = as.integer(leg_number)
  )
```

- [x] **data_dictionary:** A description of each column in the dataset, including the column name, the data type of the column, and a description of the column.

### `seasons`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number (1 to 38) |
| `n_teams` | integer | Total competing teams at season start |
| `n_legs` | integer | Total race legs in the season |
| `n_episodes` | integer | Total broadcast television episodes |
| `winners` | character | Names of the championship winning team members |
| `distance_miles` | double | Total official race route distance in miles |
| `distance_km` | double | Total official race route distance in kilometers |
| `air_dates` | character | Premiere and finale television broadcast dates |
| `filming_dates` | character | Production filming date window |
| `wiki_url` | character | Source Wikipedia article URL |

### `episodes`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `episode` | integer | Episode sequence number within the season |
| `title` | character | Official broadcast episode title |
| `air_date` | character | Original television broadcast date (`YYYY-MM-DD`) |
| `viewers_millions` | double | Live US television broadcast viewership in millions |

### `contestants`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `contestant_id` | character | Unique alphanumeric racer identifier (e.g. `US-S01-01`) |
| `name` | character | Full name of the contestant |
| `age` | double | Age of the contestant during filming |
| `gender` | character | Gender of the contestant (`M`, `F`, `NB`) |
| `relationship` | character | Occupation or team relationship role |
| `hometown` | character | Hometown city and state / province |
| `hometown_state` | character | Two-letter US state code or province |
| `hometown_country` | character | Three-letter ISO country code (`USA`) |
| `status` | character | Finishing status (e.g. `Winners`, `Runners-up`, `Eliminated`) |
| `roadblocks_completed` | integer | Total Roadblocks completed by this racer |

### `teams`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `team_id` | character | Unique alphanumeric team identifier (e.g. `US-S01-rob-brennan`) |
| `team_name` | character | Combined display names of both team members |
| `relationship` | character | Pre-existing relationship category (e.g. `Married`, `Dating`, `Siblings`, `Friends`) |
| `hometown` | character | Hometown location of the team |
| `result` | integer | Final race finish placement (`1` = Champions) |
| `status` | character | Summary finishing status description |
| `legs_won` | integer | Count of first-place leg finishes won by the team |
| `legs_completed` | integer | Total number of legs raced before elimination or finale |
| `racing_average` | double | Average leg finish placement across all completed legs |
| `placement_std` | double | Standard deviation of leg finish placements |
| `podium_count` | integer | Total count of Top-3 leg finishes |
| `podium_rate` | double | Proportion of completed legs finishing in the Top-3 |
| `gender_composition` | character | Team gender makeup (`MM`, `FF`, `MF`) |
| `roadblock_split` | character | Partner split of completed Roadblocks (e.g. `'6-6'`, `'7-5'`) |
| `roadblock_equity_score` | double | Roadblock task balance score from 0.0 (unequal) to 1.0 (perfect parity) |

### `legs`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `leg_number` | integer | Leg sequence number within the season |
| `route_header` | character | Route itinerary summary (origin and destination) |
| `origin_country` | character | Origin country three-letter ISO code (e.g. `USA`, `FRA`) |
| `destination_country` | character | Destination country three-letter ISO code (e.g. `ZMB`, `JPN`) |
| `destination_city` | character | Primary destination city of the leg |
| `destination_continent` | character | Destination continent name |
| `destination_lat` | double | Destination latitude coordinate (WGS84) |
| `destination_lon` | double | Destination longitude coordinate (WGS84) |
| `itinerary_stops` | integer | Count of distinct route waypoints and stops |
| `tasks_count` | integer | Count of challenge checkpoints on the leg |
| `narrative` | character | Detailed storyline describing route navigation, travel hurdles, and leg events |

### `leg_results`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `leg_number` | integer | Leg sequence number within the season |
| `team_name` | character | Competing team display name |
| `placement` | double | Finishing position rank at the Pit Stop mat |
| `raw_cell` | character | Original unparsed result table cell indicator |
| `is_non_elimination` | logical | `TRUE` if the leg was a predetermined Non-Elimination Leg (NEL) |
| `fast_forward` | logical | `TRUE` if the team won and used a Fast Forward |
| `uturn` | logical | `TRUE` if the team was affected by or used a U-Turn |
| `yield` | logical | `TRUE` if the team was affected by or used a Yield |
| `speed_bump` | logical | `TRUE` if the team was required to serve a Speed Bump penalty |
| `roadblock_performer` | character | Name of the teammate who performed the Roadblock |

### `tasks`

| variable | class | description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `leg_number` | integer | Leg sequence number within the season |
| `task_type` | character | Challenge category (`Roadblock`, `Detour`, `Fast Forward`, `Route Info`, `Speed Bump`) |
| `description` | character | Full narrative description of challenge rules, location, and execution |
| `performed_by` | character | Name of the racer who performed the task (for Roadblocks) |
