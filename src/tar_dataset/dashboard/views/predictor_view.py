"""Interactive Predictor view for the dashboard."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from tar_dataset.processors.predictor import SeasonPredictor


def render_predictor_view(datasets: dict[str, pd.DataFrame]) -> None:
    """Render the Interactive Season & Team Predictor view."""
    st.subheader("Interactive Outcome & Elimination Risk Predictor")
    st.markdown(
        "Leverage empirical multi-factor modeling across 38 seasons (400+ teams, 78 winners) "
        "to evaluate win probabilities, finale qualification odds, and demographic advantages."
    )

    pred_mode = st.radio(
        "Prediction Mode",
        ["🏁 Season Forecast", "🧪 Custom Team 'What-If' Simulator"],
        horizontal=True,
    )

    if pred_mode == "🏁 Season Forecast":
        _render_season_forecast(datasets)
    else:
        _render_custom_team_simulator()


def _render_season_forecast(datasets: dict[str, pd.DataFrame]) -> None:
    """Render full season forecast interface."""
    seasons_df = datasets.get("seasons", pd.DataFrame())
    if not seasons_df.empty and "season" in seasons_df.columns:
        available_seasons = sorted(
            seasons_df["season"].dropna().unique().astype(int).tolist()
        )
    else:
        available_seasons = list(range(1, 40))

    def _format_pred_season(s: int) -> str:
        row = (
            seasons_df[seasons_df["season"] == s]
            if not seasons_df.empty
            else pd.DataFrame()
        )
        if not row.empty:
            w = row.iloc[0].get("winners")
            if not w or str(w).strip().lower() in ("none", "nan", "tbd", ""):
                return f"Season {s} 🔴 (In Progress)"
        return f"Season {s}"

    col1, _col2 = st.columns([2, 4])
    with col1:
        target_season = st.selectbox(
            "Target Season",
            options=available_seasons,
            index=len(available_seasons) - 1,
            format_func=_format_pred_season,
            key="pred_season_select",
        )

    with st.spinner(f"Computing empirical predictions for Season {target_season}..."):
        try:
            predictor = SeasonPredictor()
            results = predictor.predict_season(season=int(target_season))
        except Exception as e:
            st.error(f"Error predicting Season {target_season}: {e}")
            return

    rankings = results.get("rankings", [])
    if not rankings:
        st.warning(
            f"No active or historical team data found for Season {target_season}."
        )
        return

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Teams", results.get("total_teams", 0))
    with m2:
        st.metric("Active Contenders", results.get("active_teams_count", 0))
    with m3:
        st.metric("Eliminated Teams", results.get("eliminated_teams_count", 0))
    with m4:
        st.metric("Race Stage", f"Leg {results.get('current_leg', 1)}")

    # Contender Rankings Table
    st.markdown("### Contender Probabilities & Rankings")
    rows = []
    for rank, team in enumerate(rankings, 1):
        rows.append(
            {
                "Rank": rank,
                "Team Name": team["team_name"],
                "Relationship": team["relationship"],
                "Archetype": team.get("archetype", "other"),
                "Avg Age": f"{team['avg_age']:.1f}" if team["avg_age"] else "N/A",
                "Racing Avg": f"{team['avg_placement']:.2f}"
                if team["avg_placement"]
                else "N/A",
                "Express Pass": team["express_pass_status"],
                "Win Prob (%)": team["win_probability"],
                "Top 3 Prob (%)": team["top3_probability"],
                "Status": "Eliminated" if team["is_eliminated"] else "Active",
            }
        )
    rankings_df = pd.DataFrame(rows)
    st.dataframe(rankings_df, use_container_width=True, hide_index=True)

    # Probability Chart (Active Teams)
    active_df = rankings_df[rankings_df["Status"] == "Active"]
    if not active_df.empty:
        st.markdown("### Probability Distribution (Active Teams)")
        chart_df = active_df.melt(
            id_vars=["Team Name"],
            value_vars=["Win Prob (%)", "Top 3 Prob (%)"],
            var_name="Metric",
            value_name="Probability",
        )
        bar_chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("Probability:Q", title="Probability (%)"),
                y=alt.Y("Team Name:N", sort="-x", title="Team"),
                color=alt.Color(
                    "Metric:N",
                    scale=alt.Scale(
                        domain=["Win Prob (%)", "Top 3 Prob (%)"],
                        range=["#cba6f7", "#89b4fa"],
                    ),
                ),
                tooltip=["Team Name", "Metric", "Probability"],
            )
            .properties(height=350)
        )
        st.altair_chart(bar_chart, use_container_width=True)

    # Detailed Team Diagnostics
    st.markdown("### Team Analytical Profile & Factor Diagnostics")
    active_team_names = [t["team_name"] for t in rankings if not t["is_eliminated"]]
    if active_team_names:
        selected_team_name = st.selectbox(
            "Select Team to Inspect Diagnostics:", options=active_team_names
        )
        selected_team = next(
            (t for t in rankings if t["team_name"] == selected_team_name), None
        )
        if selected_team:
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown("#### ✅ Analytical Strengths")
                strengths = selected_team.get("strengths", [])
                if strengths:
                    for s in strengths:
                        st.success(s)
                else:
                    st.info("No significant statistical advantages identified.")

            with d_col2:
                st.markdown("#### ⚠️ Risk Factors")
                risks = selected_team.get("risks", [])
                if risks:
                    for r in risks:
                        st.error(r)
                else:
                    st.info("No significant statistical risk penalties identified.")


def _render_custom_team_simulator() -> None:
    """Render interactive what-if team evaluator."""
    st.markdown("### Custom Team Evaluator & 'What-If' Simulator")
    st.markdown(
        "Configure hypothetical team demographics, leg results, and power item statuses "
        "to evaluate their raw log-odds score and empirical win probability against TAR baselines."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        team_name = st.text_input("Team Name", value="Hypothetical Duo")
        rel_options = [
            "Dating / Romantic",
            "Siblings",
            "Married",
            "Friends / Roommates",
            "Parent / Child",
            "Strangers",
            "Other",
        ]
        relationship = st.selectbox("Relationship Type", options=rel_options)

    with col2:
        age1 = st.slider("Racer 1 Age", min_value=18, max_value=75, value=28)
        age2 = st.slider("Racer 2 Age", min_value=18, max_value=75, value=30)
        has_ep = st.checkbox("Holds Intact Express Pass", value=False)
        used_ep = st.checkbox("Used Express Pass Defensively", value=False)

    with col3:
        leg1_place = st.number_input(
            "Leg 1 Placement", min_value=1, max_value=12, value=2, step=1
        )
        racing_avg = st.slider(
            "Running Racing Average", min_value=1.0, max_value=11.0, value=2.2, step=0.1
        )

    # Run prediction scoring
    predictor = SeasonPredictor()
    racers = [
        {"name": "Partner 1", "age": age1, "relationship": relationship},
        {"name": "Partner 2", "age": age2, "relationship": relationship},
    ]
    placements = [
        {"leg_number": 1, "placement": leg1_place},
        {"leg_number": 2, "placement": round(racing_avg)},
    ]

    scored = predictor.score_team(
        team_name=team_name,
        relationship=relationship,
        racers=racers,
        placements=placements,
        has_express_pass=has_ep,
        used_express_pass=used_ep,
    )

    st.markdown("---")
    st.markdown("### Simulated Performance & Factor Breakdown")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Raw Analytical Score", f"{scored['raw_score']:.2f}")
    with r2:
        avg_age = (age1 + age2) / 2.0
        age_gap = abs(age1 - age2)
        st.metric("Avg Age / Age Gap", f"{avg_age:.1f} yrs / {age_gap} yrs")
    with r3:
        st.metric("Archetype", scored["archetype"])

    diag_col1, diag_col2 = st.columns(2)
    with diag_col1:
        st.markdown("#### ✅ Identified Strengths")
        if scored.get("strengths"):
            for s in scored["strengths"]:
                st.success(s)
        else:
            st.info("No notable empirical strengths.")

    with diag_col2:
        st.markdown("#### ⚠️ Identified Risk Penalties")
        if scored.get("risks"):
            for r in scored["risks"]:
                st.error(r)
        else:
            st.info("No notable empirical risk penalties.")
