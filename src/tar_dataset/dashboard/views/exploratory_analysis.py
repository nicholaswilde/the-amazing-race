"""Exploratory Analysis & Strategic Visualizations view for the dashboard."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from tar_dataset.dashboard.data import load_empirical_metrics

CATPPUCCIN_COLORS = {
    "mauve": "#cba6f7",
    "blue": "#89b4fa",
    "green": "#a6e3a1",
    "peach": "#fab387",
    "red": "#f38ba8",
    "yellow": "#f9e2af",
    "teal": "#94e2d5",
}

SHORT_SUNK_LABELS = {
    "0 or Gain (<=0)": "≤ 0 (Hold/Gain)",
    "+1 Spot Lost": "+1 Spot",
    "+2 Spots Lost": "+2 Spots",
    "+3 Spots Lost (Switch Zone)": "+3 Spots (Switch)",
    "+4 Spots Lost": "+4 Spots",
    "+5+ Spots Lost (Sunk-Cost Trap)": "+5+ Spots (Trap)",
}

SHORT_LEG1_TIERS = {
    "1st (Leg 1 Winner)": "1st (Winner)",
    "2nd-3rd (Leg 1 Podium)": "2nd-3rd (Podium)",
    "4th-7th (Mid-Pack)": "4th-7th (Mid-Pack)",
    "8th+ (Back-Pack)": "8th+ (Back-Pack)",
}


def _filter_by_version(df: pd.DataFrame, version: str) -> pd.DataFrame:
    """Filter a dataset table by franchise version if column exists."""
    if df.empty or version.upper() == "ALL" or "version" not in df.columns:
        return df
    return df[df["version"] == version.upper()]


def _render_demographics_tab(datasets: dict[str, pd.DataFrame], version: str) -> None:
    """Render Team Survival Curves, Age/Relationship Distributions, and Roadblock Equity."""
    teams_df = _filter_by_version(datasets.get("teams", pd.DataFrame()), version)
    lr_df = _filter_by_version(datasets.get("leg_results", pd.DataFrame()), version)

    st.markdown("### Team Survival Curve & Demographic Performance")
    if teams_df.empty and lr_df.empty:
        st.info("No demographic or team survival data available for this selection.")
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Kaplan-Meier Leg Survival Trajectory")
        if not lr_df.empty and "leg_number" in lr_df.columns:
            valid_lr = lr_df.dropna(subset=["placement"]).copy()
            valid_lr["leg_number"] = valid_lr["leg_number"].astype(int)
            leg_counts = (
                valid_lr.groupby("leg_number")["team_name"]
                .count()
                .reset_index(name="active_teams")
            )
            leg1_total = (
                int(leg_counts.iloc[0]["active_teams"]) if not leg_counts.empty else 1
            )
            leg_counts["survival_pct"] = (
                leg_counts["active_teams"] / max(leg1_total, 1) * 100.0
            ).round(1)
            leg_counts = leg_counts[leg_counts["leg_number"] <= 13]

            surv_chart = (
                alt.Chart(leg_counts)
                .mark_area(
                    line={"color": CATPPUCCIN_COLORS["mauve"], "strokeWidth": 3},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(
                                color=CATPPUCCIN_COLORS["mauve"], offset=0
                            ),
                            alt.GradientStop(color="#1e1e2e", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                    opacity=0.45,
                    point={"color": CATPPUCCIN_COLORS["blue"], "size": 65},
                )
                .encode(
                    x=alt.X(
                        "leg_number:O",
                        title="Leg Number",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y(
                        "survival_pct:Q",
                        title="Teams Remaining (%)",
                        scale=alt.Scale(domain=[0, 105]),
                    ),
                    tooltip=[
                        alt.Tooltip("leg_number:O", title="Leg"),
                        alt.Tooltip("active_teams:Q", title="Active Team-Legs"),
                        alt.Tooltip("survival_pct:Q", title="Survival (%)"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(surv_chart, use_container_width=True)
        else:
            st.info("No leg results available for survival trajectory.")

    with col_right:
        st.markdown("#### Roadblock 50/50 Workload Equity vs. Racing Average")
        if (
            not teams_df.empty
            and "roadblock_equity_score" in teams_df.columns
            and "racing_average" in teams_df.columns
        ):
            eq_df = teams_df.dropna(
                subset=["roadblock_equity_score", "racing_average"]
            ).copy()
            if not eq_df.empty:
                win_col = (
                    eq_df.get("winner", pd.Series(False, index=eq_df.index))
                    .fillna(False)
                    .astype(bool)
                )
                if "result" in eq_df.columns:
                    res_col = eq_df["result"].astype(str).str.strip().str.lower()
                    is_champ = win_col | res_col.isin(
                        ["1", "1st", "1.0", "winner", "winners"]
                    )
                else:
                    is_champ = win_col
                eq_df["outcome_group"] = is_champ.apply(
                    lambda w: "Champion (1st)" if bool(w) else "Other Teams"
                )
                eq_df["z_order"] = eq_df["outcome_group"].apply(
                    lambda g: 1 if g == "Champion (1st)" else 0
                )
                eq_df = eq_df.sort_values("z_order", ascending=True)
                eq_chart = (
                    alt.Chart(eq_df)
                    .mark_circle(opacity=0.85)
                    .encode(
                        x=alt.X(
                            "roadblock_equity_score:Q",
                            title="Roadblock Equity Score (1.0 = Perfect 50/50 Split)",
                        ),
                        y=alt.Y(
                            "racing_average:Q",
                            title="Season Racing Average (Lower is Better)",
                            scale=alt.Scale(reverse=True),
                        ),
                        size=alt.condition(
                            alt.datum.outcome_group == "Champion (1st)",
                            alt.value(110),
                            alt.value(55),
                        ),
                        order=alt.Order("z_order:Q", sort="ascending"),
                        color=alt.Color(
                            "outcome_group:N",
                            legend=alt.Legend(orient="top", title=None),
                            scale=alt.Scale(
                                domain=["Champion (1st)", "Other Teams"],
                                range=[
                                    CATPPUCCIN_COLORS["green"],
                                    CATPPUCCIN_COLORS["blue"],
                                ],
                            ),
                        ),
                        tooltip=[
                            alt.Tooltip("team_name:N", title="Team"),
                            alt.Tooltip("season:Q", title="Season"),
                            alt.Tooltip(
                                "roadblock_equity_score:Q",
                                title="Equity Score",
                                format=".2f",
                            ),
                            alt.Tooltip(
                                "racing_average:Q",
                                title="Racing Avg",
                                format=".2f",
                            ),
                        ],
                    )
                    .properties(height=320)
                    .interactive()
                )
                st.altair_chart(eq_chart, use_container_width=True)
            else:
                st.info("No Roadblock equity score records available.")
        else:
            st.info("Roadblock equity columns not found in teams table.")


def _render_hazards_tab(metrics_bundle: dict[str, Any], version: str) -> None:
    """Render U-Turn and Speed Bump empirical hazard analytics."""
    ut = metrics_bundle["uturn"]
    sb = metrics_bundle["speedbump"]

    st.markdown(f"### Tactical Hazards: U-Turn & Speed Bump Lethality ({version})")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("U-Turn Victims", f"{ut.total_victims}")
    with m2:
        st.metric("U-Turn Elim Rate", f"{ut.eliminated_on_leg_rate:.1%}")
    with m3:
        st.metric("Chain U-Turn Survival", f"{ut.chain_uturn_survival_rate:.1%}")
    with m4:
        st.metric(
            "Defensive Burn Elim",
            f"{ut.intentional_defensive_burn_elim_rate:.1%}",
        )
    with m5:
        st.metric("Speed Bump Victims", f"{sb.total_instances}")
    with m6:
        st.metric("Speed Bump Elim Rate", f"{sb.eliminated_on_leg_rate:.1%}")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### U-Turn Victim Leg Placement Distribution")
        if ut.placement_counts:
            ut_rows = [
                {"Placement": f"#{k}", "order": int(k), "Teams": int(v)}
                for k, v in sorted(ut.placement_counts.items())
            ]
            ut_df = pd.DataFrame(ut_rows)
            ut_chart = (
                alt.Chart(ut_df)
                .mark_bar(
                    color=CATPPUCCIN_COLORS["red"],
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                )
                .encode(
                    x=alt.X(
                        "Placement:N",
                        sort=alt.EncodingSortField(field="order", order="ascending"),
                        title="Pit Stop Placement on U-Turn Leg",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("Teams:Q", title="Number of Victims"),
                    tooltip=[
                        alt.Tooltip("Placement:N", title="Leg Finish"),
                        alt.Tooltip("Teams:Q", title="Victim Teams"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(ut_chart, use_container_width=True)
        else:
            st.info("No U-Turn placement distribution available.")

    with col_right:
        st.markdown("#### Speed Bump Post-NEL Survival Lag (Additional Legs Survived)")
        if sb.survival_lag_distribution:
            sb_rows = [
                {
                    "Legs Survived": f"+{k}" if int(k) > 0 else "0 (Elim)",
                    "order": int(k),
                    "Teams": int(v),
                }
                for k, v in sorted(sb.survival_lag_distribution.items())
            ]
            sb_df = pd.DataFrame(sb_rows)
            sb_chart = (
                alt.Chart(sb_df)
                .mark_bar(
                    color=CATPPUCCIN_COLORS["peach"],
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                )
                .encode(
                    x=alt.X(
                        "Legs Survived:N",
                        sort=alt.EncodingSortField(field="order", order="ascending"),
                        title="Additional Legs Survived After Speed Bump",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("Teams:Q", title="Number of Penalized Teams"),
                    tooltip=[
                        alt.Tooltip("Legs Survived:N", title="Survival Lag"),
                        alt.Tooltip("Teams:Q", title="Teams"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(sb_chart, use_container_width=True)
        else:
            st.info("No Speed Bump survival distribution available.")

    with st.expander("📋 Inspect All U-Turn & Speed Bump Events"):
        if ut.instances:
            st.markdown("**U-Turn Victim Ledger**")
            st.dataframe(
                pd.DataFrame([asdict(i) for i in ut.instances]),
                use_container_width=True,
                hide_index=True,
            )
        if sb.instances:
            st.markdown("**Speed Bump Penalty Ledger**")
            st.dataframe(
                pd.DataFrame([asdict(i) for i in sb.instances]),
                use_container_width=True,
                hide_index=True,
            )


def _render_advantages_tab(metrics_bundle: dict[str, Any], version: str) -> None:
    """Render Fast Forward timing optimization and scarcity shift analytics."""
    ff = metrics_bundle["fastforward"]

    st.markdown(
        f"### Strategic Advantages: Fast Forward Timing & Scarcity Shift ({version})"
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Total Fast Forwards", f"{ff.total_instances}")
    with m2:
        st.metric("1st-Place Prize Capture", f"{ff.leg_win_rate:.1%}")
    with m3:
        st.metric("Leg Top-3 Rate", f"{ff.leg_podium_rate:.1%}")
    with m4:
        st.metric("Final Podium Rate", f"{ff.podium_rate:.1%}")
    with m5:
        st.metric("Championship Rate", f"{ff.winner_rate:.1%}")
    with m6:
        st.metric("Late-Race (7+) Win Rate", f"{ff.late_winner_rate:.1%}")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Championship & Final Podium Conversion by Race Timing Tier")
        if ff.total_instances > 0:
            tier_rows = [
                {
                    "Tier": "Early (Legs 1-4)",
                    "order": 1,
                    "Metric": "Leg 1st Place (%)",
                    "Rate": round(ff.early_leg_win_rate * 100, 1),
                },
                {
                    "Tier": "Early (Legs 1-4)",
                    "order": 1,
                    "Metric": "Final Podium (%)",
                    "Rate": round(ff.early_podium_rate * 100, 1),
                },
                {
                    "Tier": "Early (Legs 1-4)",
                    "order": 1,
                    "Metric": "Season Champion (%)",
                    "Rate": round(ff.early_winner_rate * 100, 1),
                },
                {
                    "Tier": "Mid (Legs 5-6)",
                    "order": 2,
                    "Metric": "Leg 1st Place (%)",
                    "Rate": round(ff.mid_leg_win_rate * 100, 1),
                },
                {
                    "Tier": "Mid (Legs 5-6)",
                    "order": 2,
                    "Metric": "Final Podium (%)",
                    "Rate": round(ff.mid_podium_rate * 100, 1),
                },
                {
                    "Tier": "Mid (Legs 5-6)",
                    "order": 2,
                    "Metric": "Season Champion (%)",
                    "Rate": round(ff.mid_winner_rate * 100, 1),
                },
                {
                    "Tier": "Late (Legs 7+)",
                    "order": 3,
                    "Metric": "Leg 1st Place (%)",
                    "Rate": round(ff.late_leg_win_rate * 100, 1),
                },
                {
                    "Tier": "Late (Legs 7+)",
                    "order": 3,
                    "Metric": "Final Podium (%)",
                    "Rate": round(ff.late_podium_rate * 100, 1),
                },
                {
                    "Tier": "Late (Legs 7+)",
                    "order": 3,
                    "Metric": "Season Champion (%)",
                    "Rate": round(ff.late_winner_rate * 100, 1),
                },
            ]
            t_df = pd.DataFrame(tier_rows)
            t_chart = (
                alt.Chart(t_df)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X(
                        "Tier:N",
                        sort=alt.EncodingSortField(field="order", order="ascending"),
                        title="Fast Forward Timing Window",
                        axis=alt.Axis(labelAngle=0, labelLimit=180, labelOverlap=False),
                    ),
                    xOffset="Metric:N",
                    y=alt.Y(
                        "Rate:Q",
                        title="Conversion Rate (%)",
                        scale=alt.Scale(domain=[0, 105]),
                    ),
                    color=alt.Color(
                        "Metric:N",
                        legend=alt.Legend(orient="top", title=None),
                        scale=alt.Scale(
                            domain=[
                                "Leg 1st Place (%)",
                                "Final Podium (%)",
                                "Season Champion (%)",
                            ],
                            range=[
                                CATPPUCCIN_COLORS["blue"],
                                CATPPUCCIN_COLORS["yellow"],
                                CATPPUCCIN_COLORS["green"],
                            ],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Tier:N"),
                        alt.Tooltip("Metric:N"),
                        alt.Tooltip("Rate:Q", format=".1f"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(t_chart, use_container_width=True)
        else:
            st.info("No Fast Forward instances found for this selection.")

    with col_right:
        st.markdown(
            "#### The Season 5 Scarcity Shift: Classic (S1-S4) vs. Scarce Era (S5+)"
        )
        if ff.total_instances > 0:
            era_rows = [
                {
                    "Era": f"Classic (S1-S4, n={ff.classic_era_count})",
                    "Metric": "Final Podium (%)",
                    "Rate": round(ff.classic_era_podium_rate * 100, 1),
                },
                {
                    "Era": f"Classic (S1-S4, n={ff.classic_era_count})",
                    "Metric": "Season Champion (%)",
                    "Rate": round(ff.classic_era_winner_rate * 100, 1),
                },
                {
                    "Era": f"Scarce Era (S5+, n={ff.modern_era_count})",
                    "Metric": "Final Podium (%)",
                    "Rate": round(ff.modern_era_podium_rate * 100, 1),
                },
                {
                    "Era": f"Scarce Era (S5+, n={ff.modern_era_count})",
                    "Metric": "Season Champion (%)",
                    "Rate": round(ff.modern_era_winner_rate * 100, 1),
                },
            ]
            e_df = pd.DataFrame(era_rows)
            e_chart = (
                alt.Chart(e_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X(
                        "Era:N",
                        title="Fast Forward Availability Rule Era",
                        axis=alt.Axis(labelAngle=0, labelLimit=200, labelOverlap=False),
                    ),
                    xOffset="Metric:N",
                    y=alt.Y(
                        "Rate:Q",
                        title="Conversion Rate (%)",
                        scale=alt.Scale(domain=[0, 80]),
                    ),
                    color=alt.Color(
                        "Metric:N",
                        legend=alt.Legend(orient="top", title=None),
                        scale=alt.Scale(
                            domain=["Final Podium (%)", "Season Champion (%)"],
                            range=[
                                CATPPUCCIN_COLORS["mauve"],
                                CATPPUCCIN_COLORS["teal"],
                            ],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Era:N"),
                        alt.Tooltip("Metric:N"),
                        alt.Tooltip("Rate:Q", format=".1f"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(e_chart, use_container_width=True)
        else:
            st.info("No era comparison data available.")

    if ff.instances:
        with st.expander("📋 Inspect All Fast Forward Plays"):
            st.dataframe(
                pd.DataFrame([asdict(i) for i in ff.instances]),
                use_container_width=True,
                hide_index=True,
            )


def _render_detour_tab(metrics_bundle: dict[str, Any], version: str) -> None:
    """Render Detour task archetypes, switching penalties, and sunk-cost curves."""
    det = metrics_bundle["detour"]

    st.markdown(
        f"### Detour Branch Switching Penalties & Sunk-Cost Thresholds ({version})"
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Parsed Detour Branches", f"{det.total_branches}")
    with m2:
        st.metric(
            "100% Avoided Branches",
            f"{det.unchosen_branch_count} ({det.unchosen_branch_rate:.1%})",
        )
    with m3:
        st.metric("Clean Single-Branch Elim", f"{det.clean_single_elim_rate:.1%}")
    with m4:
        st.metric(
            "Mid-Leg Switch / Drop Elim",
            f"{det.voluntary_switch_elim_rate:.1%}",
        )
    with m5:
        st.metric(
            "Forced Dual-Branch Elim",
            f"{det.forced_dual_elim_rate:.1%}",
        )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Sunk-Cost Survival Threshold Curve by Positions Lost (Δ)")
        if det.sunk_cost_curve:
            sc_rows = []
            for idx, (bucket, stats) in enumerate(det.sunk_cost_curve.items()):
                short_b = SHORT_SUNK_LABELS.get(bucket, bucket)
                sc_rows.append(
                    {
                        "Bucket": short_b,
                        "order": idx,
                        "Metric": "Last-Place Arrival (%)",
                        "Rate": round(float(stats["last_place_rate"]) * 100, 1),
                        "Count": int(stats["count"]),
                    }
                )
                sc_rows.append(
                    {
                        "Bucket": short_b,
                        "order": idx,
                        "Metric": "Direct Elimination (%)",
                        "Rate": round(float(stats["elim_rate"]) * 100, 1),
                        "Count": int(stats["count"]),
                    }
                )
            sc_df = pd.DataFrame(sc_rows)
            sc_chart = (
                alt.Chart(sc_df)
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X(
                        "Bucket:N",
                        sort=alt.EncodingSortField(field="order", order="ascending"),
                        title="Positions Lost on Detour Leg (Δ)",
                        axis=alt.Axis(labelAngle=0, labelOverlap=False, labelLimit=180),
                    ),
                    y=alt.Y("Rate:Q", title="Contender Hazard Rate (%)"),
                    color=alt.Color(
                        "Metric:N",
                        legend=alt.Legend(orient="top", title=None),
                        scale=alt.Scale(
                            domain=[
                                "Last-Place Arrival (%)",
                                "Direct Elimination (%)",
                            ],
                            range=[
                                CATPPUCCIN_COLORS["yellow"],
                                CATPPUCCIN_COLORS["red"],
                            ],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Bucket:N", title="Positions Lost"),
                        alt.Tooltip("Metric:N"),
                        alt.Tooltip("Rate:Q", title="Rate (%)", format=".1f"),
                        alt.Tooltip("Count:Q", title="Team-Legs"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(sc_chart, use_container_width=True)
        else:
            st.info("No Detour sunk-cost curve data available.")

    with col_right:
        st.markdown("#### Detour Task Archetype Share & 100%-Avoidance Rate")
        if det.archetype_summary:
            arch_rows = [
                {
                    "Archetype": arch,
                    "Branches": int(st_dict["branches"]),
                    "Share (%)": round(float(st_dict["pct_of_all"]) * 100, 1),
                    "100% Avoided": int(st_dict["unchosen_count"]),
                    "Avoidance Rate (%)": round(
                        float(st_dict["unchosen_rate"]) * 100, 1
                    ),
                }
                for arch, st_dict in det.archetype_summary.items()
            ]
            arch_df = pd.DataFrame(arch_rows)
            arch_chart = (
                alt.Chart(arch_df)
                .mark_bar(
                    color=CATPPUCCIN_COLORS["teal"],
                    cornerRadiusTopRight=4,
                    cornerRadiusBottomRight=4,
                )
                .encode(
                    y=alt.Y(
                        "Archetype:N",
                        sort="-x",
                        title="Detour Task Archetype",
                        axis=alt.Axis(labelLimit=220),
                    ),
                    x=alt.X("Share (%):Q", title="Share of All Detour Branches (%)"),
                    tooltip=[
                        alt.Tooltip("Archetype:N"),
                        alt.Tooltip("Branches:Q"),
                        alt.Tooltip("Share (%):Q", format=".1f"),
                        alt.Tooltip("100% Avoided:Q"),
                        alt.Tooltip("Avoidance Rate (%):Q", format=".1f"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(arch_chart, use_container_width=True)
        else:
            st.info("No Detour archetype data available.")

    if det.switch_events:
        with st.expander("📋 Inspect Detour Mid-Leg Drop & Dual-Branch Events"):
            st.dataframe(
                pd.DataFrame([asdict(e) for e in det.switch_events]),
                use_container_width=True,
                hide_index=True,
            )


def _render_leg1_and_routes_tab(
    datasets: dict[str, pd.DataFrame],
    metrics_bundle: dict[str, Any],
    version: str,
) -> None:
    """Render Leg 1 Winner Trajectory ('Episode 1 Curse') and Global Route Footprint."""
    l1 = metrics_bundle["leg1"]
    legs_df = _filter_by_version(datasets.get("legs", pd.DataFrame()), version)

    st.markdown(f"### First Leg Winner Trajectory & Global Route Footprint ({version})")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Leg 1 Winners", f"{l1.total_leg1_winners}")
    with m2:
        st.metric("Champion Rate", f"{l1.champion_rate:.1%}")
    with m3:
        st.metric("Final Podium Rate", f"{l1.podium_rate:.1%}")
    with m4:
        st.metric("Leg 1-to-Final r", f"{l1.pearson_r:.3f}")
    with m5:
        st.metric("Non-Podium Collapse", f"{l1.collapse_rate:.1%}")
    with m6:
        st.metric("U-Turned Winner Elim", f"{l1.uturned_winner_elim_rate:.1%}")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Leg 1 Placement Tier to Final Outcome Transition Matrix")
        if l1.transition_matrix:
            tm_rows = []
            for idx, (l1_tier, out_dict) in enumerate(l1.transition_matrix.items()):
                short_tier = SHORT_LEG1_TIERS.get(l1_tier, l1_tier)
                tot = max(sum(out_dict.values()), 1)
                for out_tier, cnt in out_dict.items():
                    tm_rows.append(
                        {
                            "Leg 1 Tier": short_tier,
                            "order": idx,
                            "Final Outcome": out_tier,
                            "Teams": int(cnt),
                            "Share (%)": round(cnt / tot * 100.0, 1),
                        }
                    )
            tm_df = pd.DataFrame(tm_rows)
            tm_chart = (
                alt.Chart(tm_df)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "Leg 1 Tier:N",
                        sort=alt.EncodingSortField(field="order", order="ascending"),
                        title="Leg 1 Finishing Tier",
                        axis=alt.Axis(labelAngle=0, labelOverlap=False, labelLimit=180),
                    ),
                    y=alt.Y("Share (%):Q", title="Final Season Outcome Share (%)"),
                    color=alt.Color(
                        "Final Outcome:N",
                        legend=alt.Legend(orient="top", title=None),
                        scale=alt.Scale(
                            domain=[
                                "1st (Champion)",
                                "2nd-3rd (Finalist)",
                                "4th-7th (Mid-Race Exit)",
                                "8th+ (Early Exit)",
                            ],
                            range=[
                                CATPPUCCIN_COLORS["green"],
                                CATPPUCCIN_COLORS["teal"],
                                CATPPUCCIN_COLORS["yellow"],
                                CATPPUCCIN_COLORS["red"],
                            ],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Leg 1 Tier:N"),
                        alt.Tooltip("Final Outcome:N"),
                        alt.Tooltip("Teams:Q"),
                        alt.Tooltip("Share (%):Q", format=".1f"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(tm_chart, use_container_width=True)
        else:
            st.info("No Leg 1 transition matrix data available.")

    with col_right:
        st.markdown("#### All-Time Continental Route Footprint")
        if not legs_df.empty and "destination_continent" in legs_df.columns:
            cont_counts = (
                legs_df["destination_continent"].dropna().value_counts().reset_index()
            )
            cont_counts.columns = ["Continent", "Legs Visited"]
            cont_chart = (
                alt.Chart(cont_counts)
                .mark_bar(
                    color=CATPPUCCIN_COLORS["mauve"],
                    cornerRadiusTopRight=4,
                    cornerRadiusBottomRight=4,
                )
                .encode(
                    y=alt.Y(
                        "Continent:N",
                        sort="-x",
                        title="Destination Continent",
                        axis=alt.Axis(labelLimit=180),
                    ),
                    x=alt.X("Legs Visited:Q", title="Total Legs Visited"),
                    tooltip=[
                        alt.Tooltip("Continent:N"),
                        alt.Tooltip("Legs Visited:Q"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(cont_chart, use_container_width=True)
        else:
            st.info("No continental route data available.")

    if l1.instances:
        with st.expander("📋 Inspect All Leg 1 Winning Teams"):
            st.dataframe(
                pd.DataFrame([asdict(i) for i in l1.instances]),
                use_container_width=True,
                hide_index=True,
            )


def render_exploratory_analysis(
    datasets: dict[str, pd.DataFrame], data_dir: str | None = None
) -> None:
    """Render the Exploratory Analysis & Strategic Visualizations view."""
    teams_df = datasets.get("teams", pd.DataFrame())
    leg_results_df = datasets.get("leg_results", pd.DataFrame())

    if teams_df.empty and leg_results_df.empty:
        st.warning("No processed dataset tables found in data/processed.")
        return

    st.subheader("📈 Exploratory Analysis & Strategic Visualizations")
    st.markdown(
        "Cross-season empirical analysis of **team survival trajectories**, **tactical hazards** "
        "(U-Turns & Speed Bumps), **strategic advantages** (Fast Forwards & Express Passes), "
        "**Detour branch switching & sunk-cost curves**, and **First Leg Winner outcomes**."
    )

    col_ver, _col_spacer = st.columns([2, 4])
    with col_ver:
        selected_version = st.selectbox(
            "Franchise Edition",
            options=["US", "ALL", "CAN", "AUS"],
            index=0,
            key="exploratory_version_selector",
        )

    metrics_bundle = load_empirical_metrics(version=selected_version, data_dir=data_dir)

    tabs = st.tabs(
        [
            "👥 Demographics & Survival",
            "⚠️ Hazards (U-Turn & Speed Bump)",
            "⚡ Advantages (Fast Forward)",
            "🔀 Detour Switching & Sunk Cost",
            "🏁 Leg 1 Trajectory & Routes",
        ]
    )

    with tabs[0]:
        _render_demographics_tab(datasets, selected_version)

    with tabs[1]:
        _render_hazards_tab(metrics_bundle, selected_version)

    with tabs[2]:
        _render_advantages_tab(metrics_bundle, selected_version)

    with tabs[3]:
        _render_detour_tab(metrics_bundle, selected_version)

    with tabs[4]:
        _render_leg1_and_routes_tab(datasets, metrics_bundle, selected_version)
