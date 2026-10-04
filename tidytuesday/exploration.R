# ==============================================================================
# TidyTuesday Starter Exploration: The Amazing Race (US Seasons 1–38)
# ==============================================================================
# Visualizing Team Survival Curves, Race Route Networks, Placement Trajectories,
# and Roadblock Task Balance.
#
# Packages required:
#   install.packages(c("tidyverse", "ggraph", "tidygraph", "scales"))
# ==============================================================================

library(tidyverse)
library(tidygraph)
library(ggraph)
library(scales)

# ------------------------------------------------------------------------------
# 1. Load Datasets
# ------------------------------------------------------------------------------
# Try loading from local path first; fall back to GitHub raw data
base_url <- "https://raw.githubusercontent.com/nicholaswilde/the-amazing-race/main/data/processed/"

load_tar_data <- function(filename) {
  local_path <- file.path("data", "processed", filename)
  if (file.exists(local_path)) {
    read_csv(local_path, show_col_types = FALSE)
  } else {
    read_csv(paste0(base_url, filename), show_col_types = FALSE)
  }
}

seasons     <- load_tar_data("seasons.csv")
episodes    <- load_tar_data("episodes.csv")
contestants <- load_tar_data("contestants.csv")
teams       <- load_tar_data("teams.csv")
legs        <- load_tar_data("legs.csv")
leg_results <- load_tar_data("leg_results.csv")
tasks       <- load_tar_data("tasks.csv")

# ------------------------------------------------------------------------------
# 2. Exploration 1: Team Survival Curves by Relationship Archetype
# ------------------------------------------------------------------------------
# Do sibling teams survive longer than dating or married couples?
# We compute step-down survival rates (proportion of teams active at each leg).

# Categorize relationship archetypes
teams_archetypes <- teams |>
  filter(version == "US") |>
  mutate(
    archetype = case_when(
      str_detect(str_to_lower(relationship), "brother|sister|sibling|twin") ~ "Siblings",
      str_detect(str_to_lower(relationship), "dating|engaged|romantic|couple|boyfriend|girlfriend|partner") ~ "Dating",
      str_detect(str_to_lower(relationship), "married|husband|wife|spouse") ~ "Married",
      str_detect(str_to_lower(relationship), "father|mother|parent|son|daughter") ~ "Parent/Child",
      str_detect(str_to_lower(relationship), "friend|buddy|roommate|coworker|colleague") ~ "Friends",
      TRUE ~ "Other"
    )
  ) |>
  filter(archetype %in% c("Dating", "Married", "Siblings", "Friends", "Parent/Child"))

# Compute survival curves across legs 1 to 12
max_legs <- 12
survival_df <- expand_grid(
  archetype = unique(teams_archetypes$archetype),
  leg_number = 0:max_legs
) |>
  rowwise() |>
  mutate(
    n_total = sum(teams_archetypes$archetype == archetype),
    surviving = if (leg_number == 0) {
      n_total
    } else {
      sum(teams_archetypes$archetype == archetype & teams_archetypes$legs_completed >= leg_number)
    },
    survival_rate = surviving / n_total
  ) |>
  ungroup()

# Plot survival step curves
p1_survival <- ggplot(survival_df, aes(x = leg_number, y = survival_rate, color = archetype)) +
  geom_step(linewidth = 1.1) +
  geom_point(size = 2.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1)) +
  scale_x_continuous(breaks = 0:12) +
  scale_color_brewer(palette = "Set1") +
  labs(
    title = "The Amazing Race: Team Survival Curves by Relationship Archetype",
    subtitle = "Proportion of teams remaining active across race legs (US Seasons 1–38)",
    x = "Leg Number",
    y = "Survival Probability",
    color = "Relationship",
    caption = "Source: The Amazing Race Dataset (theamazingrace R package)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(color = "gray30", margin = margin(b = 10)),
    legend.position = "bottom",
    panel.grid.minor = element_blank()
  )

print(p1_survival)

# ------------------------------------------------------------------------------
# 3. Exploration 2: Race Route Network Visualization using ggraph
# ------------------------------------------------------------------------------
# Visualize the global directed graph of country-to-country leg transitions.

route_edges <- legs |>
  filter(!is.na(origin_country), !is.na(destination_country)) |>
  filter(origin_country != destination_country) |>
  count(from = origin_country, to = destination_country, sort = TRUE, name = "weight")

# Top connected countries for a clean graph layout
top_countries <- unique(c(route_edges$from, route_edges$to))
country_counts <- tibble(country = c(route_edges$from, route_edges$to)) |>
  count(country, sort = TRUE) |>
  slice_head(n = 35)

filtered_edges <- route_edges |>
  filter(from %in% country_counts$country, to %in% country_counts$country)

route_graph <- as_tbl_graph(filtered_edges, directed = TRUE) |>
  mutate(
    degree = centrality_degree(mode = "all"),
    is_usa = name == "USA"
  )

# Draw circular or stress-layout network graph
p2_network <- ggraph(route_graph, layout = "stress") +
  geom_edge_arc(
    aes(width = weight, alpha = weight),
    arrow = arrow(length = unit(2.5, "mm"), type = "closed"),
    color = "#D90429",
    curvature = 0.15,
    show.legend = FALSE
  ) +
  geom_node_point(aes(size = degree, color = is_usa), show.legend = FALSE) +
  geom_node_text(aes(label = name), repel = TRUE, size = 3.5, fontface = "bold") +
  scale_edge_width(range = c(0.4, 2.5)) +
  scale_edge_alpha(range = c(0.3, 0.9)) +
  scale_color_manual(values = c("TRUE" = "#1D3557", "FALSE" = "#457B9D")) +
  scale_size(range = c(3, 9)) +
  labs(
    title = "The Amazing Race: Global Route Network",
    subtitle = "Directed flight and transit legs connecting top international host countries",
    caption = "Source: The Amazing Race Dataset"
  ) +
  theme_graph(base_family = "sans")

print(p2_network)

# ------------------------------------------------------------------------------
# 4. Exploration 3: Roadblock Parity vs. Championship Success
# ------------------------------------------------------------------------------
# Does balanced task sharing (higher Roadblock equity) correlate with winning?

teams_equity <- teams |>
  filter(version == "US", !is.na(roadblock_equity_score), legs_completed >= 6) |>
  mutate(
    placement_tier = case_when(
      result == 1 ~ "1st (Champions)",
      result %in% 2:3 ~ "2nd–3rd (Finalists)",
      result %in% 4:6 ~ "4th–6th (Late Exits)",
      TRUE ~ "7th+ (Early Exits)"
    ),
    placement_tier = factor(
      placement_tier,
      levels = c("1st (Champions)", "2nd–3rd (Finalists)", "4th–6th (Late Exits)", "7th+ (Early Exits)")
    )
  )

p3_roadblock <- ggplot(teams_equity, aes(x = placement_tier, y = roadblock_equity_score, fill = placement_tier)) +
  geom_boxplot(alpha = 0.7, outlier.shape = 21, width = 0.5) +
  geom_jitter(width = 0.15, alpha = 0.4, size = 1.8) +
  scale_fill_brewer(palette = "Blues", direction = -1) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2)) +
  labs(
    title = "Does Roadblock Task Equality Predict Champions?",
    subtitle = "Distribution of Roadblock equity score (1.0 = equal split) across finish placement tiers",
    x = "Final Finish Placement Tier",
    y = "Roadblock Equity Score",
    caption = "Only teams completing >= 6 legs shown. Source: The Amazing Race Dataset"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    legend.position = "none",
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(face = "bold")
  )

print(p3_roadblock)

# ------------------------------------------------------------------------------
# 5. Exploration 4: Placement Trajectories of Selected Champions
# ------------------------------------------------------------------------------
# Trace leg-by-leg placements of memorable winning teams across seasons.

selected_seasons <- c(1, 7, 21, 31)
champions_trajectories <- leg_results |>
  filter(season %in% selected_seasons) |>
  inner_join(
    teams |> filter(result == 1) |> select(season, team_name),
    by = c("season", "team_name")
  )

p4_trajectories <- ggplot(champions_trajectories, aes(x = leg_number, y = placement, color = factor(season), group = team_name)) +
  geom_line(linewidth = 1.2) +
  geom_point(size = 3) +
  scale_y_reverse(breaks = 1:12) +
  scale_x_continuous(breaks = 1:13) +
  scale_color_brewer(palette = "Dark2") +
  labs(
    title = "The Champions' Path: Leg Placement Trajectories",
    subtitle = "Leg finishes across the season for winners of Seasons 1, 7, 21, and 31",
    x = "Leg Number",
    y = "Placement (1st = Mat Victory)",
    color = "Season",
    caption = "Source: The Amazing Race Dataset"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = "bottom"
  )

print(p4_trajectories)

# ------------------------------------------------------------------------------
# 6. Exploration 5: Television Viewership Across 38 Seasons
# ------------------------------------------------------------------------------
season_ratings <- episodes |>
  filter(!is.na(viewers_millions)) |>
  group_by(season) |>
  summarise(
    avg_viewers = mean(viewers_millions),
    premiere_viewers = first(viewers_millions),
    finale_viewers = last(viewers_millions),
    .groups = "drop"
  )

p5_ratings <- ggplot(season_ratings, aes(x = season, y = avg_viewers)) +
  geom_area(fill = "#457B9D", alpha = 0.25) +
  geom_line(color = "#1D3557", linewidth = 1.2) +
  geom_point(color = "#D90429", size = 2.5) +
  scale_x_continuous(breaks = seq(1, 38, 4)) +
  scale_y_continuous(labels = label_number(suffix = "M")) +
  labs(
    title = "The Amazing Race: US Television Viewership (Seasons 1–38)",
    subtitle = "Average live Nielsen broadcast viewership in millions per season",
    x = "Season",
    y = "Average Viewers",
    caption = "Source: Nielsen Media Research / The Amazing Race Dataset"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold"),
    panel.grid.minor = element_blank()
  )

print(p5_ratings)

message("✓ All starter exploratory visualizations rendered successfully.")
