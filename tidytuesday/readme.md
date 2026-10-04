# The Amazing Race (US Seasons 1–38)

Welcome to **The Amazing Race** dataset curated for the [R for Data Science (R4DS) TidyTuesday](https://github.com/rfordatascience/tidytuesday) community!

The Amazing Race is a multi-Emmy award-winning reality competition television franchise created by Bertram van Munster and Elise Doganieri, and hosted by Phil Keoghan. In each season, teams of two individuals who possess a pre-existing personal relationship (e.g. married couples, siblings, best friends, parent/child) race around the world across multiple continents and countries. Teams decipher cryptic clues, navigate foreign public transit and self-drive routes, perform demanding physical and cultural tasks, and race to a Pit Stop mat. The last team to arrive at a Pit Stop is typically eliminated, until three teams remain to race in the finale for a US $1,000,000 grand prize.

This dataset provides a tidy, relational representation of the first 38 seasons of the flagship US franchise.

---

## The Data

The dataset is organized into 7 relational tables available as CSV files:

| Table | File | Description | Rows |
| :--- | :--- | :--- | :---: |
| `seasons` | `seasons.csv` | Season-level summary, dates, total route distance, and champions | 38 |
| `episodes` | `episodes.csv` | Episode broadcast schedule, titles, and Nielsen TV viewership | 440 |
| `contestants` | `contestants.csv` | Demographic profiles, age, gender, hometown, and Roadblocks completed | 886 |
| `teams` | `teams.csv` | Two-person teams, relationship categories, finish results, and racing averages | 431 |
| `legs` | `legs.csv` | Leg routing, origin/destination cities and countries, waypoint coordinates, and narrative | 453 |
| `leg_results` | `leg_results.csv` | Leg arrival placements, non-eliminations, Fast Forwards, and penalty markers | 3,189 |
| `tasks` | `tasks.csv` | Detailed descriptions of Detours, Roadblocks, Fast Forwards, and Route Info | 1,699 |

### How to Read the Data in R

```r
# Option 1: Load directly from GitHub
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/data/processed/"

seasons     <- readr::read_csv(paste0(base_url, "seasons.csv"))
episodes    <- readr::read_csv(paste0(base_url, "episodes.csv"))
contestants <- readr::read_csv(paste0(base_url, "contestants.csv"))
teams       <- readr::read_csv(paste0(base_url, "teams.csv"))
legs        <- readr::read_csv(paste0(base_url, "legs.csv"))
leg_results <- readr::read_csv(paste0(base_url, "leg_results.csv"))
tasks       <- readr::read_csv(paste0(base_url, "tasks.csv"))

# Option 2: Install and use the companion R package
# remotes::install_github("nicholaswilde/the-amazing-race", subdir = "r")
# library(theamazingrace)
# data(seasons)
# data(teams)
# data(legs)
```

---

## Game Mechanics Glossary

Understanding the rules of *The Amazing Race* helps frame meaningful analytical hypotheses:

- **Route Marker / Route Info**: Yellow and red flags marking physical clue boxes. Clues instruct teams where to travel next or which challenge to undertake.
- **Detour**: A choice between two different challenges, each with its own pros and cons (e.g., mental/finesse vs. physical/endurance). Both teammates must participate. Teams may switch tasks at any point if they struggle, incurring a travel and time penalty.
- **Roadblock**: A task that only one team member may perform. Once chosen based on a brief clue clue without knowing the full task details, the racer cannot switch. Rules (introduced in Season 6) enforce strict limits on the maximum number of Roadblocks any single racer may perform across the season (e.g. at most 6 or 7), requiring strategic task allocation between partners.
- **Fast Forward**: A task that allows the first team to complete it to skip all subsequent leg challenges and travel immediately to the Pit Stop mat. Only one Fast Forward is typically available per leg, and a team may only claim one Fast Forward per season.
- **Yield**: A game mechanic allowing one team to force a trailing team to stop racing for a set duration (e.g., 30 minutes).
- **U-Turn**: A hazard appearing immediately after a Detour where a team can force a trailing team to backtrack and complete the other side of the Detour as well. Blind U-Turns keep the perpetrator anonymous.
- **Pit Stop**: The final checkpoint of each leg. Teams step onto a check-in mat where host Phil Keoghan officially registers their arrival time and placement.
- **Non-Elimination Leg (NEL)**: Pre-determined legs where the last team to arrive is not eliminated. Spared teams often receive penalties on the subsequent leg (such as having to complete a **Speed Bump** or forfeiting all their money/possessions).

---

## Analytical & Visualization Ideas

Here are some starting questions to explore:

1. **Team Survival Curves & Archetypes**:
   - Do certain relationship archetypes (e.g. Married, Dating, Siblings, Parent/Child, Friends) have higher survival probabilities or average placements?
   - How do team survival curves differ by gender composition (`MM`, `FF`, `MF`) across the 12 legs of a season?
2. **Race Routes & Network Flows**:
   - How are race legs connected globally? Which countries and cities serve as frequent continental gateways or transit hubs?
   - How has total race travel distance (`distance_miles`) evolved from the globe-trotting early 2000s seasons to modern seasons?
3. **Roadblock Parity & Equity**:
   - Teams have `roadblock_equity_score` measured from 0.0 (unequal) to 1.0 (perfect parity). Do teams with higher task equality perform better or win more championships?
   - How did the implementation of the Roadblock rule in Season 6 alter partner workload balance?
4. **Leg Placement Trajectories**:
   - Trace the leg-by-leg placement trajectories of race winners. Do future champions consistently stay near the top, or do they experience erratic placement swings?
   - Can you identify "comeback" teams who survived multiple non-elimination legs or bottom-two finishes to reach the finale?
5. **Television Viewership & Cultural Trends**:
   - Plot live Nielsen viewership (`viewers_millions`) across 400+ episodes. Which seasons and finales captured peak broadcast viewership? How did Sunday/Wednesday broadcast time slot shifts affect ratings?

---

## Data Dictionary

### 1. `seasons.csv`

| Variable | Class | Description |
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

### 2. `episodes.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `episode` | integer | Episode sequence number within the season |
| `title` | character | Official broadcast episode title (often a racer quotation) |
| `air_date` | character | Original television broadcast date (`YYYY-MM-DD`) |
| `viewers_millions` | double | Live US television viewership in millions (Nielsen ratings) |

### 3. `contestants.csv`

| Variable | Class | Description |
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

### 4. `teams.csv`

| Variable | Class | Description |
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

### 5. `legs.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `leg_number` | integer | Leg sequence number within the season |
| `route_header` | character | Route itinerary summary (origin and destination) |
| `origin_country` | character | Origin country three-letter ISO code (e.g. `USA`, `FRA`) |
| `destination_country` | character | Destination country three-letter ISO code (e.g. `ZMB`, `JPN`) |
| `destination_city` | character | Primary destination city of the leg |
| `destination_continent` | character | Destination continent name (`North America`, `South America`, `Europe`, `Africa`, `Asia`, `Oceania`) |
| `destination_lat` | double | Destination latitude coordinate (WGS84) |
| `destination_lon` | double | Destination longitude coordinate (WGS84) |
| `itinerary_stops` | integer | Count of distinct route waypoints and stops |
| `tasks_count` | integer | Count of challenge checkpoints on the leg |
| `narrative` | character | Detailed storyline describing route navigation, travel hurdles, and leg events |

### 6. `leg_results.csv`

| Variable | Class | Description |
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

### 7. `tasks.csv`

| Variable | Class | Description |
| :--- | :--- | :--- |
| `version` | character | Franchise country code (`US`) |
| `season` | integer | Season number |
| `leg_number` | integer | Leg sequence number within the season |
| `task_type` | character | Challenge category (`Roadblock`, `Detour`, `Fast Forward`, `Route Info`, `Speed Bump`) |
| `description` | character | Full narrative description of challenge rules, location, and execution |
| `performed_by` | character | Name of the racer who performed the task (for Roadblocks) |

---

## Source & Attribution

Data curated and cleaned from:
- [Wikipedia: The Amazing Race (American TV series)](https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series))
- [The Amazing Race Wiki (Fandom)](https://amazingrace.fandom.com/)
- Nielsen Media Research broadcast ratings
- Companion R package: [`theamazingrace`](https://github.com/nicholaswilde/the-amazing-race)
