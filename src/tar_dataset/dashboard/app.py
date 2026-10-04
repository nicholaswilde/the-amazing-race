"""Main entrypoint for The Amazing Race Streamlit web dashboard."""

from __future__ import annotations

import streamlit as st

from tar_dataset.dashboard.data import load_all_datasets
from tar_dataset.dashboard.views.challenge_browser import render_challenge_browser
from tar_dataset.dashboard.views.predictor_view import render_predictor_view
from tar_dataset.dashboard.views.season_explorer import render_season_explorer


def main() -> None:
    """Run the Streamlit web application."""
    st.set_page_config(
        page_title="The Amazing Race Analytics Dashboard",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    datasets = load_all_datasets()

    st.sidebar.title("🌍 The Amazing Race")
    st.sidebar.caption("Tidy Dataset & Empirical Analytics Platform")

    nav_selection = st.sidebar.radio(
        "Navigation",
        [
            "🗺️ Season Explorer",
            "🔮 Interactive Predictor",
            "🧩 Challenge Browser",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Dataset Footprint")
    seasons_cnt = len(datasets.get("seasons", []))
    teams_cnt = len(datasets.get("teams", []))
    legs_cnt = len(datasets.get("legs", []))
    tasks_cnt = len(datasets.get("tasks", []))

    st.sidebar.write(f"• **Seasons:** {seasons_cnt}")
    st.sidebar.write(f"• **Teams:** {teams_cnt}")
    st.sidebar.write(f"• **Legs:** {legs_cnt}")
    st.sidebar.write(f"• **Challenges:** {tasks_cnt}")

    st.sidebar.markdown("---")
    st.sidebar.caption("Data source: Wikipedia & Community Curations")

    if nav_selection == "🗺️ Season Explorer":
        render_season_explorer(datasets)
    elif nav_selection == "🔮 Interactive Predictor":
        render_predictor_view(datasets)
    elif nav_selection == "🧩 Challenge Browser":
        render_challenge_browser(datasets)


if __name__ == "__main__":
    main()
