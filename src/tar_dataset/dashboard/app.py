"""Main entrypoint for The Amazing Race Streamlit web dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow running this file directly (e.g. Streamlit Cloud) without installing the package.
_SRC_DIR = str(Path(__file__).resolve().parents[2])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from tar_dataset.dashboard.data import load_all_datasets
from tar_dataset.dashboard.views.challenge_browser import render_challenge_browser
from tar_dataset.dashboard.views.predictor_view import render_predictor_view
from tar_dataset.dashboard.views.season_explorer import render_season_explorer


def _inject_catppuccin_theme() -> None:
    """Inject custom Catppuccin Mocha styling enhancements."""
    st.markdown(
        """
        <style>
        /* Catppuccin Mocha Global Palette */
        :root {
            --catppuccin-mauve: #cba6f7;
            --catppuccin-blue: #89b4fa;
            --catppuccin-green: #a6e3a1;
            --catppuccin-peach: #fab387;
            --catppuccin-red: #f38ba8;
            --catppuccin-text: #cdd6f4;
            --catppuccin-subtext: #bac2de;
            --catppuccin-surface0: #313244;
            --catppuccin-base: #1e1e2e;
            --catppuccin-mantle: #181825;
            --catppuccin-crust: #11111b;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background-color: #181825;
            border: 1px solid #313244;
            border-radius: 8px;
            padding: 12px 16px;
        }
        [data-testid="stMetricLabel"] {
            color: #bac2de !important;
        }
        [data-testid="stMetricValue"] {
            color: #cba6f7 !important;
        }

        /* Tabs styling */
        button[data-baseweb="tab"] {
            color: #a6adc8;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #cba6f7 !important;
            border-bottom-color: #cba6f7 !important;
        }

        /* Expander headers */
        .streamlit-expanderHeader {
            background-color: #181825;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Run the Streamlit web application."""
    st.set_page_config(
        page_title="The Amazing Race Analytics Dashboard",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_catppuccin_theme()

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
