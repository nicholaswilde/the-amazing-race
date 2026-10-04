"""Challenge Browser view for the dashboard."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_challenge_browser(datasets: dict[str, pd.DataFrame]) -> None:
    """Render the Challenge Browser view."""
    tasks_df = datasets.get("tasks", pd.DataFrame())
    contestants_df = datasets.get("contestants", pd.DataFrame())

    if tasks_df.empty:
        st.warning("No task data found in data/processed.")
        return

    st.subheader("Challenge Browser & Task Analytics")
    st.markdown(
        f"Search, filter, and explore all **{len(tasks_df):,}** documented Amazing Race challenges "
        "across Roadblocks, Detours, Fast Forwards, and Speed Bumps."
    )

    # Filter Controls
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        task_types = ["All"] + sorted(tasks_df["task_type"].dropna().unique().tolist())
        selected_type = st.selectbox(
            "Task Type", options=task_types, key="filter_task_type"
        )

    with c2:
        seasons = ["All"] + sorted(
            tasks_df["season"].dropna().unique().astype(int).tolist()
        )
        selected_season = st.selectbox(
            "Season", options=seasons, key="filter_task_season"
        )

    with c3:
        search_query = st.text_input(
            "Search Keyword (description or performer)",
            placeholder="e.g. bungee, bungee jump, cheese, taxi, dance...",
            key="filter_task_search",
        )

    # Apply filters
    filtered_df = tasks_df.copy()
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df["task_type"] == selected_type]

    if selected_season != "All":
        filtered_df = filtered_df[filtered_df["season"] == int(selected_season)]

    if search_query.strip():
        q = search_query.strip().lower()
        desc_match = filtered_df["description"].str.lower().str.contains(q, na=False)
        perf_match = filtered_df["performed_by"].str.lower().str.contains(q, na=False)
        filtered_df = filtered_df[desc_match | perf_match]

    # Metrics Summary
    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Matches", f"{len(filtered_df):,}")
    with m2:
        detours = len(filtered_df[filtered_df["task_type"] == "Detour"])
        st.metric("Detours", f"{detours:,}")
    with m3:
        roadblocks = len(filtered_df[filtered_df["task_type"] == "Roadblock"])
        st.metric("Roadblocks", f"{roadblocks:,}")
    with m4:
        ff = len(filtered_df[filtered_df["task_type"] == "Fast Forward"])
        st.metric("Fast Forwards", f"{ff:,}")
    with m5:
        sb = len(filtered_df[filtered_df["task_type"] == "Speed Bump"])
        st.metric("Speed Bumps", f"{sb:,}")

    # Tabs: Analysis & Data View
    tab_list, tab_analytics = st.tabs(
        ["📋 Challenge Directory", "📊 Challenge Analytics"]
    )

    with tab_list:
        if filtered_df.empty:
            st.info("No challenges match the specified criteria.")
        else:
            display_cols = [
                "season",
                "leg_number",
                "task_type",
                "performed_by",
                "description",
            ]
            cols_to_show = [c for c in display_cols if c in filtered_df.columns]
            st.dataframe(
                filtered_df[cols_to_show].sort_values(["season", "leg_number"]),
                use_container_width=True,
                hide_index=True,
            )

    with tab_analytics:
        st.markdown("### Challenge Evolution Across Seasons")
        # Aggregated count by season and task_type
        counts_by_season = (
            tasks_df.groupby(["season", "task_type"]).size().reset_index(name="count")
        )
        season_chart = (
            alt.Chart(counts_by_season)
            .mark_bar()
            .encode(
                x=alt.X("season:O", title="Season"),
                y=alt.Y("count:Q", title="Number of Tasks"),
                color=alt.Color(
                    "task_type:N",
                    title="Task Type",
                    scale=alt.Scale(range=["#cba6f7", "#89b4fa", "#a6e3a1", "#fab387"]),
                ),
                tooltip=["season", "task_type", "count"],
            )
            .properties(height=350)
        )
        st.altair_chart(season_chart, use_container_width=True)

        st.markdown("### All-Time Top Roadblock Performers")
        if (
            not contestants_df.empty
            and "roadblocks_completed" in contestants_df.columns
        ):
            top_rb = (
                contestants_df.dropna(subset=["roadblocks_completed"])
                .sort_values("roadblocks_completed", ascending=False)
                .head(15)[["name", "season", "relationship", "roadblocks_completed"]]
            )
            top_chart = (
                alt.Chart(top_rb)
                .mark_bar()
                .encode(
                    x=alt.X("roadblocks_completed:Q", title="Roadblocks Completed"),
                    y=alt.Y("name:N", sort="-x", title="Contestant"),
                    color=alt.Color(
                        "season:O", title="Season", scale=alt.Scale(scheme="blues")
                    ),
                    tooltip=["name", "season", "relationship", "roadblocks_completed"],
                )
                .properties(height=380)
            )
            st.altair_chart(top_chart, use_container_width=True)
