# Auto-generated documentation for theamazingrace datasets
# Generated from schemas.py and processed tables. Do not edit by hand.

#' Seasons in The Amazing Race
#'
#' Season-level metadata, route summary statistics, and winning teams across all seasons.
#'
#' @format A data frame with 38 rows and 11 variables:
#' \describe{
#'   \item{version}{Franchise country code ('US', 'CAN', 'AUS', etc.)}
#'   \item{season}{Season number (integer)}
#'   \item{n_teams}{Total number of competing teams}
#'   \item{n_legs}{Total number of legs in the season}
#'   \item{n_episodes}{Total number of broadcast episodes}
#'   \item{winners}{Names of the winning team members}
#'   \item{distance_miles}{Total race travel distance in miles}
#'   \item{distance_km}{Total race travel distance in kilometers}
#'   \item{air_dates}{Season premiere and finale broadcast date range}
#'   \item{filming_dates}{Season filming date range}
#'   \item{wiki_url}{Wikipedia source page URL}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"seasons"

#' Episodes of The Amazing Race
#'
#' Episode-level broadcast metadata, titles, premiere air dates, and Nielsen television viewership ratings.
#'
#' @format A data frame with 380 rows and 6 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{episode}{Episode number within the season (integer)}
#'   \item{title}{Official broadcast episode title}
#'   \item{air_date}{Original television broadcast date (YYYY-MM-DD)}
#'   \item{viewers_millions}{US broadcast viewership in millions}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"episodes"

#' Contestants in The Amazing Race
#'
#' Individual contestant demographics, ages, relationship categories, and hometown residences.
#'
#' @format A data frame with 886 rows and 12 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{contestant_id}{Unique alphanumeric contestant identifier}
#'   \item{name}{Full name of the contestant}
#'   \item{age}{Age of the contestant during filming (integer)}
#'   \item{gender}{Gender of the contestant (M, F, NB)}
#'   \item{relationship}{Stated relationship to race teammate}
#'   \item{hometown}{City and state of permanent residence}
#'   \item{hometown_state}{Parsed US state two-letter postal code or region}
#'   \item{hometown_country}{Hometown country code (e.g. USA)}
#'   \item{status}{Finishing status (e.g. Winners, Runners-up, Eliminated)}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"contestants"

#' Teams in The Amazing Race
#'
#' Two-person team statistics, relationship classifications, final finish placement, and total leg victories.
#'
#' @format A data frame with 431 rows and 17 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{team_id}{Unique team identifier}
#'   \item{team_name}{Combined names of both team members}
#'   \item{relationship}{Relationship classification (e.g. Married, Dating, Siblings, Friends)}
#'   \item{hometown}{Hometown location of the team}
#'   \item{result}{Final race finish placement (1 = Champions, integer)}
#'   \item{status}{Finishing status description}
#'   \item{legs_won}{Count of first-place leg finishes won by the team (integer)}
#'   \item{legs_completed}{Total number of legs completed before elimination or victory (integer)}
#'   \item{racing_average}{Average leg finish placement across all completed legs (numeric)}
#'   \item{placement_std}{Standard deviation of leg finish placements (numeric)}
#'   \item{podium_count}{Total count of Top-3 leg finishes (integer)}
#'   \item{podium_rate}{Proportion of completed legs finishing in Top-3 (numeric)}
#'   \item{gender_composition}{Team gender composition (MM, FF, MF)}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"teams"

#' Legs and Travel Routes in The Amazing Race
#'
#' Leg-level travel route summaries, itinerary waypoints count, task counts, and route narratives.
#'
#' @format A data frame with 453 rows and 11 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{leg_number}{Leg number within the season (integer)}
#'   \item{route_header}{Locations and countries traversed during the leg}
#'   \item{origin_country}{Origin country three-letter ISO code (e.g. USA, FRA)}
#'   \item{destination_country}{Destination country three-letter ISO code (e.g. ZMB, JPN)}
#'   \item{destination_city}{Primary destination city or region of the leg}
#'   \item{destination_continent}{Destination continent name (e.g. Africa, Europe, Asia)}
#'   \item{itinerary_stops}{Count of distinct route waypoints and stops (integer)}
#'   \item{tasks_count}{Count of challenge checkpoints on the leg (integer)}
#'   \item{narrative}{Comprehensive narrative detailing route travel, navigation challenges, and leg storyline}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"legs"

#' Leg Results and Placements in The Amazing Race
#'
#' Finish placements, arrival ranks, and game-mechanic penalties/advantages for each team on every leg.
#'
#' @format A data frame with 3189 rows and 12 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{leg_number}{Leg number within the season (integer)}
#'   \item{team_name}{Name of the competing team}
#'   \item{placement}{Finishing rank on this leg (integer)}
#'   \item{raw_cell}{Original unparsed result table cell indicator}
#'   \item{is_non_elimination}{Logical flag indicating if the leg was a predetermined Non-Elimination Leg}
#'   \item{fast_forward}{Logical flag indicating if the team successfully utilized a Fast Forward}
#'   \item{uturn}{Logical flag indicating if the team was targeted by a U-Turn penalty}
#'   \item{yield}{Logical flag indicating if the team was targeted by a Yield penalty}
#'   \item{speed_bump}{Logical flag indicating if the team served a Speed Bump penalty}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"leg_results"

#' Tasks and Challenges in The Amazing Race
#'
#' Detailed breakdowns of all Roadblocks, Detours, Fast Forwards, and Route Info challenges.
#'
#' @format A data frame with 1699 rows and 6 variables:
#' \describe{
#'   \item{version}{Franchise country code}
#'   \item{season}{Season number (integer)}
#'   \item{leg_number}{Leg number within the season (integer)}
#'   \item{task_type}{Task category ('Roadblock', 'Detour', 'Fast Forward', 'Route Info', 'Speed Bump')}
#'   \item{description}{Full description of task requirements, rules, and location}
#' }
#' @source \url{https://en.wikipedia.org/wiki/The_Amazing_Race_(American_TV_series)}
"tasks"
