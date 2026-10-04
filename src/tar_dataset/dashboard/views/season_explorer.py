"""Season Explorer view for the dashboard."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_season_explorer(datasets: dict[str, pd.DataFrame]) -> None:
    """Render the Season Explorer view."""
    seasons_df = datasets.get("seasons", pd.DataFrame())
    episodes_df = datasets.get("episodes", pd.DataFrame())
    teams_df = datasets.get("teams", pd.DataFrame())
    contestants_df = datasets.get("contestants", pd.DataFrame())
    legs_df = datasets.get("legs", pd.DataFrame())
    leg_results_df = datasets.get("leg_results", pd.DataFrame())

    if seasons_df.empty:
        st.warning("No season data found in data/processed.")
        return

    available_seasons = sorted(
        seasons_df["season"].dropna().unique().astype(int).tolist()
    )

    col_sel, _col_space = st.columns([2, 4])
    with col_sel:
        selected_season = st.selectbox(
            "Select Season",
            options=available_seasons,
            index=len(available_seasons) - 1,
            key="season_selector",
        )

    # Filter data for selected season
    s_row = seasons_df[seasons_df["season"] == selected_season].iloc[0]
    s_episodes = episodes_df[episodes_df["season"] == selected_season]
    s_teams = teams_df[teams_df["season"] == selected_season]
    s_contestants = contestants_df[contestants_df["season"] == selected_season]
    s_legs = legs_df[legs_df["season"] == selected_season].sort_values("leg_number")
    s_leg_results = leg_results_df[leg_results_df["season"] == selected_season]

    # Season Summary Metrics
    st.subheader(f"Season {selected_season} Overview")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        winners = s_row.get("winners") or "TBD"
        st.metric("Winners", str(winners))
    with m2:
        st.metric("Teams", int(s_row.get("n_teams", len(s_teams))))
    with m3:
        st.metric("Legs", int(s_row.get("n_legs", len(s_legs))))
    with m4:
        dist_mi = s_row.get("distance_miles")
        dist_str = f"{int(dist_mi):,} mi" if pd.notna(dist_mi) else "N/A"
        st.metric("Distance", dist_str)
    with m5:
        avg_viewers = (
            s_episodes["viewers_millions"].dropna().mean()
            if not s_episodes.empty
            else None
        )
        viewers_str = (
            f"{avg_viewers:.2f}M" if (avg_viewers and pd.notna(avg_viewers)) else "N/A"
        )
        st.metric("Avg Viewers", viewers_str)

    # Sub-tabs for detailed exploration
    tab_placements, tab_routes, tab_roadblocks, tab_episodes = st.tabs(
        [
            "📈 Placements & Standings",
            "🗺️ Leg Routes & Map",
            "🧩 Roadblock Tracker",
            "📺 Episodes & Ratings",
        ]
    )

    with tab_placements:
        st.markdown("### Team Placement Trajectory Across Legs")
        if not s_leg_results.empty:
            all_teams = sorted(s_teams["team_name"].dropna().unique().tolist())
            selected_teams = st.multiselect(
                "Filter Teams to Highlight (leave blank for all):",
                options=all_teams,
                default=[],
                key="trajectory_team_filter",
            )
            plot_df = s_leg_results.copy()
            if selected_teams:
                plot_df = plot_df[plot_df["team_name"].isin(selected_teams)]

            chart = (
                alt.Chart(plot_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X("leg_number:O", title="Leg Number"),
                    y=alt.Y(
                        "placement:Q",
                        title="Placement (1st at Top)",
                        scale=alt.Scale(reverse=True, zero=False),
                    ),
                    color=alt.Color("team_name:N", title="Team"),
                    tooltip=[
                        alt.Tooltip("team_name:N", title="Team"),
                        alt.Tooltip("leg_number:O", title="Leg"),
                        alt.Tooltip("placement:Q", title="Placement"),
                        alt.Tooltip("raw_cell:N", title="Notes"),
                    ],
                )
                .properties(height=420)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No leg results data available for this season.")

        st.markdown("### Final Standings & Team Statistics")
        if not s_teams.empty:
            display_cols = [
                "team_name",
                "relationship",
                "hometown",
                "result",
                "legs_won",
                "legs_completed",
                "racing_average",
                "podium_rate",
                "roadblock_split",
                "roadblock_equity_score",
            ]
            cols_to_show = [c for c in display_cols if c in s_teams.columns]
            teams_table = s_teams[cols_to_show].sort_values(
                "racing_average", ascending=True
            )
            st.dataframe(teams_table, use_container_width=True, hide_index=True)

    with tab_routes:
        st.markdown("### Global Race Route & Destination Map")
        map_coords = s_legs.dropna(subset=["destination_lat", "destination_lon"])[
            [
                "destination_lat",
                "destination_lon",
                "destination_city",
                "destination_country",
            ]
        ].rename(columns={"destination_lat": "lat", "destination_lon": "lon"})

        if not map_coords.empty:
            st.map(map_coords, zoom=1, use_container_width=True)
        else:
            st.info("No coordinate data available for map visualization.")

        st.markdown("### Leg Breakdown & Route Itineraries")
        if not s_legs.empty:
            route_cols = [
                "leg_number",
                "origin_country",
                "destination_country",
                "destination_city",
                "tasks_count",
                "itinerary_stops",
            ]
            valid_route_cols = [c for c in route_cols if c in s_legs.columns]
            st.dataframe(
                s_legs[valid_route_cols], use_container_width=True, hide_index=True
            )

            st.markdown("#### Leg Narratives")
            for _, leg_row in s_legs.iterrows():
                leg_num = leg_row["leg_number"]
                dest = f"{leg_row.get('destination_city', '')}, {leg_row.get('destination_country', '')}"
                with st.expander(f"Leg {leg_num}: {dest}"):
                    st.write(
                        leg_row.get("narrative") or "No narrative summary available."
                    )
                    if pd.notna(leg_row.get("itinerary_stops")):
                        st.caption(f"**Itinerary:** {leg_row['itinerary_stops']}")

    with tab_roadblocks:
        st.markdown("### Team Roadblock Equity & Balance")
        if not s_teams.empty and "roadblock_equity_score" in s_teams.columns:
            rb_teams = s_teams[s_teams["roadblock_split"].notna()][
                [
                    "team_name",
                    "relationship",
                    "roadblock_split",
                    "roadblock_equity_score",
                    "legs_completed",
                ]
            ].sort_values("roadblock_equity_score", ascending=False)
            st.dataframe(rb_teams, use_container_width=True, hide_index=True)

        st.markdown("### Individual Contestant Roadblock Counts")
        if not s_contestants.empty:
            c_cols = [
                "name",
                "relationship",
                "age",
                "roadblocks_completed",
                "hometown",
                "status",
            ]
            valid_c_cols = [c for c in c_cols if c in s_contestants.columns]
            c_sorted = s_contestants[valid_c_cols].sort_values(
                "roadblocks_completed", ascending=False
            )
            st.dataframe(c_sorted, use_container_width=True, hide_index=True)

        st.markdown("### Roadblock Performers by Leg")
        if not s_leg_results.empty:
            rb_legs = s_leg_results[s_leg_results["roadblock_performer"].notna()][
                ["leg_number", "team_name", "roadblock_performer", "placement"]
            ].sort_values(["leg_number", "placement"])
            if not rb_legs.empty:
                st.dataframe(rb_legs, use_container_width=True, hide_index=True)
            else:
                st.info("No recorded individual roadblock performers for this season.")

    with tab_episodes:
        st.markdown("### Episode Broadcasts & Television Ratings")
        if not s_episodes.empty:
            ep_cols = ["episode", "title", "air_date", "viewers_millions"]
            valid_ep_cols = [c for c in ep_cols if c in s_episodes.columns]
            st.dataframe(
                s_episodes[valid_ep_cols].sort_values("episode"),
                use_container_width=True,
                hide_index=True,
            )

            # Viewership trend line chart if viewers data exists
            if s_episodes["viewers_millions"].dropna().count() > 0:
                view_chart = (
                    alt.Chart(s_episodes.dropna(subset=["viewers_millions"]))
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("episode:O", title="Episode"),
                        y=alt.Y("viewers_millions:Q", title="Viewers (Millions)"),
                        tooltip=["episode", "title", "viewers_millions", "air_date"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(view_chart, use_container_width=True)
        else:
            st.info("No episode broadcast data found for this season.")
