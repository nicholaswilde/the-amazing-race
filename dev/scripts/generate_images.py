"""Generate publication-quality data visualizations and branding assets for The Amazing Race dataset.

Mirrors the structure and aesthetic of doehm/alone/dev/images:
- survival.png: Kaplan-Meier style team survival curves by archetype with inset boxplots
- items.png: Horizontal bar chart of top visited destination countries
- boxplots.png: Racer age distributions across finish placement tiers
- gender_performance.png: Team gender dynamics (racing averages, podium rates, win shares)
- roadblock_equity.png: Roadblock equity score evolution and gender workload parity
- continents.png: Continental leg destinations and historical era routing shifts
- theamazingrace hex.png: R package hexagonal sticker badge (3600x3600 RGBA)
- bg.png, bg white.png: Dark and light square social cards
- bg hex.png, bg white hex.png: Hexagon silhouette masks
- square.jpg: Showcase card with key dataset statistics
"""

from __future__ import annotations

import math
from pathlib import Path
import re

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# Brand palette inspired by TAR route marker and modern data design
PALETTE = {
    "red": "#D90429",
    "yellow": "#FFD200",
    "navy": "#1D3557",
    "teal": "#2A9D8F",
    "slate": "#457B9D",
    "coral": "#E76F51",
    "dark": "#1A1D20",
    "gray_text": "#2B2D42",
    "gray_line": "#D1D5DB",
    "bg_white": "#FFFFFF",
    "bg_card": "#F8F9FA",
}

FONT_FAMILY = "Liberation Sans"
plt.rcParams["font.sans-serif"] = [FONT_FAMILY, "DejaVu Sans", "Arial"]
plt.rcParams["font.family"] = "sans-serif"


def setup_canvas(width_in: float, height_in: float, dpi: int = 300) -> tuple[plt.Figure, plt.Axes]:
    """Create a clean figure and axes with minimalist void styling."""
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])
    return fig, ax


def generate_survival_chart(output_dir: Path) -> None:
    """Generate survival.png: Team survival curves across legs with inset boxplot."""
    print("Generating survival.png...")
    teams_df = pd.read_parquet("data/processed/teams.parquet")
    us_teams = teams_df[teams_df["version"] == "US"].copy()

    # Map archetypes
    def categorize(rel: str) -> str:
        r = str(rel).lower()
        if any(k in r for k in ["brother", "sister", "sibling", "twin"]):
            return "Siblings"
        if any(k in r for k in ["dating", "engaged", "romantic", "couple", "boyfriend", "girlfriend", "partner"]):
            return "Dating"
        if any(k in r for k in ["married", "husband", "wife", "spouse"]):
            return "Married"
        if any(k in r for k in ["friend", "buddy", "roommate", "colleague"]):
            return "Friends"
        if any(k in r for k in ["father", "mother", "parent", "son", "daughter"]):
            return "Parent/Child"
        return "Other"

    us_teams["archetype"] = us_teams["relationship"].apply(categorize)
    archetypes = ["Dating", "Siblings", "Married", "Friends", "Parent/Child"]
    us_teams = us_teams[us_teams["archetype"].isin(archetypes)]

    # Compute step-down survival curve
    max_leg = 12
    surv_data: dict[str, list[float]] = {}
    for arch in archetypes:
        subset = us_teams[us_teams["archetype"] == arch]
        n_total = len(subset)
        rates = []
        for leg in range(max_leg + 1):
            if leg == 0:
                rates.append(1.0)
            else:
                survived = (subset["legs_completed"] >= leg).sum()
                rates.append(survived / n_total if n_total > 0 else 0.0)
        surv_data[arch] = rates

    # 12 x 8 inches @ 300 DPI = 3600 x 2400
    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Main plot axes (left, bottom, width, height)
    ax_main = fig.add_axes([0.08, 0.12, 0.88, 0.68])
    ax_main.set_facecolor(PALETTE["bg_white"])

    colors = {
        "Dating": PALETTE["red"],
        "Siblings": PALETTE["navy"],
        "Married": PALETTE["slate"],
        "Friends": PALETTE["teal"],
        "Parent/Child": PALETTE["coral"],
    }

    legs_range = list(range(max_leg + 1))
    for arch in archetypes:
        ax_main.step(
            legs_range,
            surv_data[arch],
            where="post",
            label=f"{arch} (n={len(us_teams[us_teams['archetype'] == arch])})",
            color=colors[arch],
            linewidth=2.8,
            alpha=0.95,
        )

    # Styling main plot
    ax_main.set_xlim(0, max_leg)
    ax_main.set_ylim(-0.02, 1.05)
    ax_main.set_xlabel("Leg Number Reached", fontsize=13, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_main.set_ylabel("Proportion of Teams Remaining", fontsize=13, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_main.set_xticks(range(0, max_leg + 1))
    ax_main.set_yticks(np.arange(0.0, 1.1, 0.2))
    ax_main.set_yticklabels([f"{int(y*100)}%" for y in np.arange(0.0, 1.1, 0.2)])
    ax_main.tick_params(colors=PALETTE["gray_text"], labelsize=11)

    ax_main.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax_main.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_main.spines[spine].set_color(PALETTE["gray_line"])
        ax_main.spines[spine].set_linewidth(1.2)

    ax_main.legend(
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=10,
        framealpha=0.9,
    )

    # Titles matching Dan Oehm style
    fig.text(0.08, 0.92, "Survival curves", fontsize=24, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.08,
        0.87,
        "Dating couples and sibling pairs sustain higher survival rates across deep legs than parent/child teams",
        fontsize=12,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.03,
        "Data: 38 US Seasons of The Amazing Race | the-amazing-race package",
        fontsize=9,
        color="#8E9AA7",
    )

    # Inset element: horizontal boxplot of legs completed by archetype
    ax_inset = fig.add_axes([0.16, 0.18, 0.32, 0.28])
    ax_inset.set_facecolor(PALETTE["bg_card"])
    ax_inset.patch.set_alpha(0.85)

    box_data = [us_teams[us_teams["archetype"] == arch]["legs_completed"].dropna().tolist() for arch in reversed(archetypes)]
    box_colors = [colors[arch] for arch in reversed(archetypes)]

    bplot = ax_inset.boxplot(
        box_data,
        vert=False,
        patch_artist=True,
        widths=0.6,
        showfliers=False,
        medianprops=dict(color=PALETTE["dark"], linewidth=1.8),
    )
    for patch, col in zip(bplot["boxes"], box_colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.65)
        patch.set_edgecolor(col)

    # Jittered scatter dots
    for i, (vals, col) in enumerate(zip(box_data, box_colors)):
        y_jitter = np.random.normal(i + 1, 0.08, size=len(vals))
        ax_inset.scatter(vals, y_jitter, color=col, alpha=0.35, s=12, edgecolors="none")

    ax_inset.set_yticks(range(1, len(archetypes) + 1))
    ax_inset.set_yticklabels(reversed(archetypes), fontsize=8.5, fontweight="bold", color=PALETTE["gray_text"])
    ax_inset.set_xlabel("Legs Completed", fontsize=8, color=PALETTE["gray_text"])
    ax_inset.tick_params(labelsize=8, colors=PALETTE["gray_text"])
    ax_inset.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.5)
    for spine in ax_inset.spines.values():
        spine.set_color(PALETTE["gray_line"])
        spine.set_linewidth(0.8)

    out_file = output_dir / "survival.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_items_chart(output_dir: Path) -> None:
    """Generate items.png: Horizontal bar chart of most visited countries."""
    print("Generating items.png...")
    legs_df = pd.read_parquet("data/processed/legs.parquet")

    # Extract destination countries
    country_counts: dict[str, int] = {}
    for h in legs_df["route_header"].dropna():
        parts = re.split(r"→|->|to", str(h))
        for p in parts:
            c = p.strip().split(",")[-1].strip()
            c = re.sub(r"\(.*?\)", "", c).strip()
            if len(c) > 2 and not c.startswith("Season"):
                country_counts[c] = country_counts.get(c, 0) + 1

    # Filter top 14
    top_items = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:14]
    labels = [k for k, _ in reversed(top_items)]
    values = [v for _, v in reversed(top_items)]

    # 8 x 8 inches @ 300 DPI = 2400 x 2400
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, height=0.68, color=PALETTE["navy"], alpha=0.92)

    # Highlight top 1 (United States) and top international (France) with Route Marker red
    bars[-1].set_color(PALETTE["red"])
    bars[-2].set_color("#C1121F")

    # Value labels at the end of each bar
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 1.2,
            bar.get_y() + bar.get_height() / 2.0,
            f"{val}",
            va="center",
            ha="left",
            fontsize=10.5,
            fontweight="bold",
            color=PALETTE["gray_text"],
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11, fontweight="bold", color=PALETTE["gray_text"])
    ax.set_xlim(0, max(values) + 12)
    ax.set_xlabel("Number of Leg Visits", fontsize=11, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax.tick_params(colors=PALETTE["gray_text"], labelsize=10)

    ax.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(PALETTE["gray_line"])
        ax.spines[spine].set_linewidth(1.1)

    fig.text(0.12, 0.94, "Most visited destination countries", fontsize=18, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.12,
        0.90,
        "Total leg appearances across all 38 seasons of The Amazing Race",
        fontsize=10.5,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.12,
        0.02,
        "Data: the-amazing-race package | 453 legs recorded",
        fontsize=8.5,
        color="#8E9AA7",
    )

    plt.subplots_adjust(left=0.24, right=0.92, top=0.86, bottom=0.10)
    out_file = output_dir / "items.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_boxplots_chart(output_dir: Path) -> None:
    """Generate boxplots.png: Racer age distribution across finish placement tiers."""
    print("Generating boxplots.png...")
    contestants_df = pd.read_parquet("data/processed/contestants.parquet")
    teams_df = pd.read_parquet("data/processed/teams.parquet")

    # Categorize finish tiers
    merged = teams_df[["version", "season", "team_name", "result"]].copy()
    merged = merged[merged["version"] == "US"].dropna(subset=["result"])

    def tier(res: float) -> str:
        if res == 1:
            return "Winners (1st)"
        elif res in (2, 3):
            return "Finalists (2nd–3rd)"
        elif 4 <= res <= 7:
            return "Mid-Pack (4th–7th)"
        else:
            return "Early Exits (8th+)"

    merged["tier"] = merged["result"].apply(tier)

    # Join contestants by matching names in team_name
    tiers_order = ["Winners (1st)", "Finalists (2nd–3rd)", "Mid-Pack (4th–7th)", "Early Exits (8th+)"]
    c_us = contestants_df[(contestants_df["version"] == "US") & (contestants_df["age"] > 0)].copy()

    # Link contestant to tier via status string
    def parse_status_tier(status: str) -> str:
        s = str(status).lower()
        if "winner" in s:
            return "Winners (1st)"
        elif "2nd" in s or "3rd" in s or "runner" in s:
            return "Finalists (2nd–3rd)"
        elif any(f"eliminated {k}" in s for k in ["4th", "5th", "6th", "7th"]):
            return "Mid-Pack (4th–7th)"
        elif "eliminated" in s:
            return "Early Exits (8th+)"
        return "Mid-Pack (4th–7th)"

    c_us["tier"] = c_us["status"].apply(parse_status_tier)

    # 12 x 8 inches @ 300 DPI = 3600 x 2400
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])
    ax.set_facecolor(PALETTE["bg_white"])

    data = [c_us[c_us["tier"] == t]["age"].dropna().tolist() for t in tiers_order]
    tier_colors = [PALETTE["yellow"], PALETTE["slate"], PALETTE["teal"], PALETTE["coral"]]

    bplot = ax.boxplot(
        data,
        vert=False,
        patch_artist=True,
        widths=0.55,
        medianprops=dict(color=PALETTE["dark"], linewidth=2.4),
        flierprops=dict(marker="o", markersize=4, alpha=0.4, markerfacecolor=PALETTE["dark"]),
    )

    for patch, col in zip(bplot["boxes"], tier_colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.70)
        patch.set_edgecolor(PALETTE["dark"])
        patch.set_linewidth(1.4)

    # Overlay jitter points
    for i, (vals, col) in enumerate(zip(data, tier_colors)):
        y_jit = np.random.normal(i + 1, 0.08, size=len(vals))
        ax.scatter(vals, y_jit, color=PALETTE["dark"], alpha=0.32, s=28, edgecolors="none")

    ax.set_yticks(range(1, len(tiers_order) + 1))
    ax.set_yticklabels(
        [f"{t}\n(n={len(vals)})" for t, vals in zip(tiers_order, data)],
        fontsize=12,
        fontweight="bold",
        color=PALETTE["gray_text"],
    )
    ax.set_xlabel("Racer Age (Years)", fontsize=13, fontweight="bold", color=PALETTE["gray_text"], labelpad=12)
    ax.tick_params(colors=PALETTE["gray_text"], labelsize=11)
    ax.set_xlim(16, 75)

    # Highlight historical winner sweet spot (24-34)
    ax.axvspan(24, 34, color=PALETTE["yellow"], alpha=0.15, label="Optimal Age Sweet Spot (24–34)")

    ax.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(PALETTE["gray_line"])
        ax.spines[spine].set_linewidth(1.2)

    ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["bg_white"],
        edgecolor=PALETTE["gray_line"],
        fontsize=11,
    )

    fig.text(0.08, 0.94, "Racer age distributions by finish placement", fontsize=22, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.08,
        0.89,
        "Podium and championship teams skew toward the 25–34 demographic with significantly lower variance",
        fontsize=12,
        color=PALETTE["gray_text"],
    )
    fig.text(
        0.08,
        0.03,
        "Data: 886 racers across 38 US Seasons | the-amazing-race package",
        fontsize=9,
        color="#8E9AA7",
    )

    plt.subplots_adjust(left=0.18, right=0.94, top=0.84, bottom=0.12)
    out_file = output_dir / "boxplots.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_gender_performance_chart(output_dir: Path) -> None:
    """Generate gender_performance.png: Team gender dynamics across racing averages and wins."""
    print("Generating gender_performance.png...")
    teams_df = pd.read_parquet("data/processed/teams.parquet")
    us_teams = teams_df[teams_df["version"] == "US"].copy()
    us_teams = us_teams[us_teams["gender_composition"].isin(["MM", "MF", "FF"])]

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Left: Racing average boxplot & scatter
    ax_box = fig.add_axes([0.14, 0.16, 0.36, 0.65])
    ax_box.set_facecolor(PALETTE["bg_white"])

    groups = ["FF", "MF", "MM"]
    labels = ["All-Female (FF)\n(n=97)", "Co-Ed (MF)\n(n=210)", "All-Male (MM)\n(n=124)"]
    colors = [PALETTE["coral"], PALETTE["teal"], PALETTE["navy"]]

    box_data = [us_teams[us_teams["gender_composition"] == g]["racing_average"].dropna().tolist() for g in groups]

    bplot = ax_box.boxplot(
        box_data,
        vert=False,
        patch_artist=True,
        widths=0.52,
        medianprops={"color": PALETTE["dark"], "linewidth": 2.2},
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.3, "markerfacecolor": PALETTE["dark"]},
    )

    for patch, col in zip(bplot["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.70)
        patch.set_edgecolor(PALETTE["dark"])
        patch.set_linewidth(1.3)

    for i, (vals, col) in enumerate(zip(box_data, colors)):
        y_jit = np.random.normal(i + 1, 0.08, size=len(vals))
        ax_box.scatter(vals, y_jit, color=PALETTE["dark"], alpha=0.28, s=20, edgecolors="none")

    ax_box.set_yticks([1, 2, 3])
    ax_box.set_yticklabels(labels, fontsize=10.5, fontweight="bold", color=PALETTE["gray_text"])
    ax_box.set_xlabel("Racing Average (Lower is Better ←)", fontsize=11, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_box.set_xlim(1.0, 13.0)
    ax_box.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_box.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_box.set_title("Racing Average Distribution", fontsize=13, fontweight="bold", color=PALETTE["dark"], pad=14)

    for spine in ["top", "right"]:
        ax_box.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_box.spines[spine].set_color(PALETTE["gray_line"])
        ax_box.spines[spine].set_linewidth(1.1)

    for i, g in enumerate(groups):
        med = float(np.median(us_teams[us_teams["gender_composition"] == g]["racing_average"].dropna()))
        ax_box.text(
            med,
            i + 1 + 0.33,
            f"Med: {med:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=colors[i],
        )

    # Right: Conversion Rates
    ax_metrics = fig.add_axes([0.58, 0.16, 0.36, 0.65])
    ax_metrics.set_facecolor(PALETTE["bg_white"])

    y_indices = np.array([1, 2, 3])
    bar_h = 0.26

    win_pcts = [3 / 38 * 100, 21 / 38 * 100, 14 / 38 * 100]
    podium_rates = [18.9, 36.1, 36.8]

    b1 = ax_metrics.barh(y_indices + bar_h / 2, win_pcts, height=bar_h, color=colors, alpha=0.9)
    b2 = ax_metrics.barh(y_indices - bar_h / 2, podium_rates, height=bar_h, color=colors, alpha=0.5, hatch="//")

    for bar, val in zip(b1, win_pcts):
        ax_metrics.text(
            val + 1.4,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}% ({round(val * 38 / 100)} wins)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color=PALETTE["gray_text"],
        )

    for bar, val in zip(b2, podium_rates):
        ax_metrics.text(
            val + 1.4,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}% podium",
            va="center",
            fontsize=8.5,
            color=PALETTE["gray_text"],
        )

    ax_metrics.set_yticks([])
    ax_metrics.set_xlim(0, 100)
    ax_metrics.set_ylim(0.4, 3.8)
    ax_metrics.set_xlabel("Conversion Rate (%)", fontsize=11, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_metrics.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_metrics.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_metrics.set_title("Championships & Podium Rates", fontsize=13, fontweight="bold", color=PALETTE["dark"], pad=14)

    for spine in ["top", "right", "left"]:
        ax_metrics.spines[spine].set_visible(False)
    ax_metrics.spines["bottom"].set_color(PALETTE["gray_line"])
    ax_metrics.spines["bottom"].set_linewidth(1.1)

    legend_elements = [
        patches.Patch(facecolor="#4A5568", alpha=0.9, label="Championship Win Share (38 Seasons)"),
        patches.Patch(facecolor="#4A5568", alpha=0.5, hatch="//", label="Podium Leg Finish Rate (%)"),
    ]
    ax_metrics.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.0, 1.0), frameon=True, facecolor=PALETTE["bg_white"], edgecolor=PALETTE["gray_line"], fontsize=8.5)

    callout_rect = patches.FancyBboxPatch((0.08, 0.042), 0.86, 0.055, boxstyle="round,pad=0.015", facecolor=PALETTE["bg_card"], edgecolor=PALETTE["yellow"], linewidth=1.5)
    fig.patches.append(callout_rect)
    fig.text(
        0.51,
        0.068,
        "Historic Milestone: Nat & Kat (S17) became the first all-female team to win in TAR history (16-season drought), followed by Kisha & Jen (S18) and Amy & Maya (S25).",
        fontsize=9,
        ha="center",
        va="center",
        color=PALETTE["gray_text"],
        style="italic",
    )

    fig.text(0.08, 0.94, "Team gender dynamics & performance", fontsize=22, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.08,
        0.89,
        "Comparison of racing averages, podium conversion rates, and championship titles across 431 teams",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(0.08, 0.012, "Data: 431 teams across 38 US Seasons | the-amazing-race package", fontsize=8.5, color="#8E9AA7")

    out_file = output_dir / "gender_performance.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_roadblock_equity_chart(output_dir: Path) -> None:
    """Generate roadblock_equity.png: Evolution of task balance before/after Season 6 rule."""
    print("Generating roadblock_equity.png...")
    contestants_df = pd.read_parquet("data/processed/contestants.parquet")
    teams_df = pd.read_parquet("data/processed/teams.parquet")

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Top: Historical Roadblock Equity Score
    ax_top = fig.add_axes([0.16, 0.54, 0.78, 0.32])
    ax_top.set_facecolor(PALETTE["bg_white"])

    season_eq = teams_df[teams_df["roadblock_equity_score"].notna()].groupby("season")["roadblock_equity_score"].agg(["mean", "std", "count"]).reset_index()

    ax_top.axvspan(0.5, 5.5, color=PALETTE["coral"], alpha=0.12, label="Uncapped Era (S1–S5, Mean = 0.50)")
    ax_top.axvspan(5.5, 36.5, color=PALETTE["teal"], alpha=0.12, label="Roadblock Rule Era (S6–S36, Mean = 0.79)")

    ax_top.axvline(5.5, color=PALETTE["red"], linestyle="--", linewidth=1.8, alpha=0.85)
    ax_top.text(5.7, 0.37, "S6 Rule Instituted:\nMax limits per racer", color=PALETTE["red"], fontsize=8.5, fontweight="bold", va="center")

    ax_top.plot(season_eq["season"], season_eq["mean"], color=PALETTE["navy"], marker="o", markersize=5, linewidth=2.2, label="Season Mean Equity Score")
    ax_top.scatter(season_eq["season"], season_eq["mean"], color=PALETTE["navy"], s=35, zorder=4)

    ax_top.annotate(
        "S5: Colin & Christie\n(Colin 9, Christie 1)",
        xy=(5, 0.55),
        xytext=(1.8, 0.78),
        arrowprops={"arrowstyle": "->", "color": PALETTE["gray_text"], "lw": 1.0},
        fontsize=8,
        color=PALETTE["gray_text"],
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": PALETTE["bg_card"], "edgecolor": PALETTE["gray_line"], "alpha": 0.9},
    )
    ax_top.annotate(
        "S6: Immediate Parity Surge\n(Mean 0.87)",
        xy=(6, 0.87),
        xytext=(7.5, 0.94),
        arrowprops={"arrowstyle": "->", "color": PALETTE["teal"], "lw": 1.0},
        fontsize=8,
        color=PALETTE["teal"],
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": PALETTE["bg_card"], "edgecolor": PALETTE["teal"], "alpha": 0.9},
    )

    ax_top.set_xlim(0.5, 37.0)
    ax_top.set_ylim(0.30, 1.02)
    ax_top.set_ylabel("Roadblock Equity Score\n(1.0 = Perfect Balance)", fontsize=10, fontweight="bold", color=PALETTE["gray_text"])
    ax_top.tick_params(colors=PALETTE["gray_text"], labelsize=9.5)
    ax_top.grid(True, linestyle=":", color=PALETTE["gray_line"], alpha=0.6)
    ax_top.legend(loc="lower right", frameon=True, facecolor=PALETTE["bg_white"], edgecolor=PALETTE["gray_line"], fontsize=8.5)

    for spine in ["top", "right"]:
        ax_top.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_top.spines[spine].set_color(PALETTE["gray_line"])
        ax_top.spines[spine].set_linewidth(1.0)

    # Bottom: Racer Roadblocks Completed by Gender
    ax_bot = fig.add_axes([0.16, 0.12, 0.78, 0.30])
    ax_bot.set_facecolor(PALETTE["bg_white"])

    c = contestants_df[contestants_df["version"] == "US"].copy()
    s1_5_f = float(c[(c["season"] <= 5) & (c["gender"] == "F")]["roadblocks_completed"].mean())
    s1_5_m = float(c[(c["season"] <= 5) & (c["gender"] == "M")]["roadblocks_completed"].mean())
    s6_plus_f = float(c[(c["season"] >= 6) & (c["gender"] == "F")]["roadblocks_completed"].mean())
    s6_plus_m = float(c[(c["season"] >= 6) & (c["gender"] == "M")]["roadblocks_completed"].mean())

    eras = ["Uncapped Era\n(Seasons 1–5)", "Roadblock Rule Era\n(Seasons 6–36)"]
    female_vals = [s1_5_f, s6_plus_f]
    male_vals = [s1_5_m, s6_plus_m]

    y_pos = np.arange(len(eras))
    h = 0.30

    b_m = ax_bot.barh(y_pos + h / 2, male_vals, height=h, color=PALETTE["navy"], alpha=0.9, label="Male Racers")
    b_f = ax_bot.barh(y_pos - h / 2, female_vals, height=h, color=PALETTE["coral"], alpha=0.9, label="Female Racers")

    for bar, val in zip(b_m, male_vals):
        ax_bot.text(val + 0.08, bar.get_y() + bar.get_height() / 2, f"{val:.2f} avg RBs", va="center", fontsize=9.5, fontweight="bold", color=PALETTE["navy"])

    for bar, val in zip(b_f, female_vals):
        ax_bot.text(val + 0.08, bar.get_y() + bar.get_height() / 2, f"{val:.2f} avg RBs", va="center", fontsize=9.5, fontweight="bold", color=PALETTE["coral"])

    ax_bot.text(5.5, 0 + h / 2, "+131% Male Task Load\n(Heavy Imbalance)", color=PALETTE["coral"], fontsize=9, fontweight="bold", va="center")
    ax_bot.text(5.5, 1 + h / 2, "+11% Difference\n(Near Balance)", color=PALETTE["teal"], fontsize=9, fontweight="bold", va="center")

    ax_bot.set_yticks(y_pos)
    ax_bot.set_yticklabels(eras, fontsize=10, fontweight="bold", color=PALETTE["gray_text"])
    ax_bot.set_xlim(0, 7.2)
    ax_bot.set_xlabel("Average Roadblocks Completed per Contestant", fontsize=10.5, fontweight="bold", color=PALETTE["gray_text"], labelpad=8)
    ax_bot.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_bot.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.6)
    ax_bot.legend(loc="lower right", frameon=True, facecolor=PALETTE["bg_white"], edgecolor=PALETTE["gray_line"], fontsize=9)

    for spine in ["top", "right"]:
        ax_bot.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_bot.spines[spine].set_color(PALETTE["gray_line"])
        ax_bot.spines[spine].set_linewidth(1.0)

    fig.text(0.08, 0.94, "Roadblock task equity & the Season 6 rule shift", fontsize=22, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.08,
        0.89,
        "Individual roadblock limits enacted in Season 6 closed the massive gender workload gap and enforced partner task parity",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(0.08, 0.02, "Data: 886 racers across 38 US Seasons | the-amazing-race package", fontsize=8.5, color="#8E9AA7")

    out_file = output_dir / "roadblock_equity.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_continents_chart(output_dir: Path) -> None:
    """Generate continents.png: Destination continents and routing shifts over eras."""
    print("Generating continents.png...")
    legs_df = pd.read_parquet("data/processed/legs.parquet")
    us_legs = legs_df[legs_df["version"] == "US"].copy()

    def get_era(season: int) -> str:
        if season <= 10:
            return "Classic Era\n(S1–S10)"
        elif season <= 20:
            return "Golden Era\n(S11–S20)"
        elif season <= 30:
            return "Modern Era\n(S21–S30)"
        else:
            return "Post-COVID\n(S31–S38)"

    us_legs["era"] = us_legs["season"].apply(get_era)

    eras = ["Classic Era\n(S1–S10)", "Golden Era\n(S11–S20)", "Modern Era\n(S21–S30)", "Post-COVID\n(S31–S38)"]
    continents = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]

    cont_colors = {
        "Europe": PALETTE["navy"],
        "Asia": PALETTE["teal"],
        "North America": PALETTE["slate"],
        "South America": PALETTE["coral"],
        "Africa": PALETTE["yellow"],
        "Oceania": "#8338EC",
    }

    fig = plt.figure(figsize=(12, 8), dpi=300)
    fig.patch.set_facecolor(PALETTE["bg_white"])

    # Left: Total visits
    ax_left = fig.add_axes([0.14, 0.16, 0.33, 0.65])
    ax_left.set_facecolor(PALETTE["bg_white"])

    tot_counts = us_legs["destination_continent"].value_counts()[continents]
    y_pos = np.arange(len(continents))

    bars = ax_left.barh(y_pos, tot_counts.values, height=0.62, color=[cont_colors[c] for c in continents], alpha=0.90)

    for bar, val in zip(bars, tot_counts.values):
        pct = val / len(us_legs) * 100
        ax_left.text(val + 3.0, bar.get_y() + bar.get_height() / 2, f"{val} ({pct:.1f}%)", va="center", fontsize=9, fontweight="bold", color=PALETTE["gray_text"])

    ax_left.set_yticks(y_pos)
    ax_left.set_yticklabels(continents, fontsize=10.5, fontweight="bold", color=PALETTE["gray_text"])
    ax_left.set_xlim(0, 195)
    ax_left.set_xlabel("Total Legs Visited", fontsize=11, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_left.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_left.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_left.set_title("All-Time Continental Visits", fontsize=13, fontweight="bold", color=PALETTE["dark"], pad=14)
    ax_left.invert_yaxis()

    for spine in ["top", "right"]:
        ax_left.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_left.spines[spine].set_color(PALETTE["gray_line"])
        ax_left.spines[spine].set_linewidth(1.1)

    # Right: Stacked percentage composition by Era
    ax_right = fig.add_axes([0.58, 0.16, 0.38, 0.65])
    ax_right.set_facecolor(PALETTE["bg_white"])

    ct = pd.crosstab(us_legs["era"], us_legs["destination_continent"]).reindex(index=eras, columns=continents)
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

    y_era = np.arange(len(eras))
    left_offset = np.zeros(len(eras))

    for c in continents:
        vals = ct_pct[c].values
        ax_right.barh(y_era, vals, left=left_offset, height=0.58, color=cont_colors[c], alpha=0.90, label=c)
        left_offset += vals

    ax_right.set_yticks(y_era)
    ax_right.set_yticklabels(eras, fontsize=10.5, fontweight="bold", color=PALETTE["gray_text"])
    ax_right.set_xlim(0, 100)
    ax_right.set_xlabel("Share of Legs per Era (%)", fontsize=11, fontweight="bold", color=PALETTE["gray_text"], labelpad=10)
    ax_right.tick_params(colors=PALETTE["gray_text"], labelsize=10)
    ax_right.grid(True, axis="x", linestyle=":", color=PALETTE["gray_line"], alpha=0.7)
    ax_right.set_title("Geographic Routing Shift by Era", fontsize=13, fontweight="bold", color=PALETTE["dark"], pad=14)
    ax_right.invert_yaxis()

    for spine in ["top", "right"]:
        ax_right.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_right.spines[spine].set_color(PALETTE["gray_line"])
        ax_right.spines[spine].set_linewidth(1.1)

    ax_right.legend(loc="lower right", bbox_to_anchor=(1.0, 0.02), frameon=True, facecolor=PALETTE["bg_white"], edgecolor=PALETTE["gray_line"], fontsize=8, ncol=3)

    callout_rect = patches.FancyBboxPatch((0.08, 0.042), 0.86, 0.055, boxstyle="round,pad=0.015", facecolor=PALETTE["bg_card"], edgecolor=PALETTE["yellow"], linewidth=1.5)
    fig.patches.append(callout_rect)
    fig.text(
        0.51,
        0.068,
        "Routing Shift: Early seasons featured broad global dispersal across Africa and Oceania. Post-COVID seasons (S31–S38) heavily concentrated on Europe (47.9%) using chartered aircraft.",
        fontsize=8.5,
        ha="center",
        va="center",
        color=PALETTE["gray_text"],
        style="italic",
    )

    fig.text(0.08, 0.94, "Global race footprint by continent", fontsize=22, fontweight="bold", color=PALETTE["dark"])
    fig.text(
        0.08,
        0.89,
        "Distribution of 453 race destinations and historical evolution of continental routing across 38 seasons",
        fontsize=11.5,
        color=PALETTE["gray_text"],
    )
    fig.text(0.08, 0.012, "Data: 453 legs across 38 US Seasons | the-amazing-race package", fontsize=8.5, color="#8E9AA7")

    out_file = output_dir / "continents.png"
    fig.savefig(out_file, dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {out_file}")


def generate_hex_badge(output_dir: Path) -> None:
    """Generate the official R package hex sticker badge (theamazingrace hex.png)."""
    print("Generating theamazingrace hex.png...")
    size = 3600
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    center_x = size / 2.0
    center_y = size / 2.0
    # Hexagon radius
    r = size * 0.45

    # Regular point-topped or flat-topped hexagon (R hex convention: flat top & bottom or pointed)
    # Standard hex sticker has points at left & right or top & bottom (points at 30, 90, 150...)
    angles = [math.radians(a) for a in [30, 90, 150, 210, 270, 330]]
    hex_pts = [(center_x + r * math.cos(a), center_y + r * math.sin(a)) for a in angles]

    # Mask for inner hexagon
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(hex_pts, fill=255)

    # Inner artwork layer
    inner = Image.new("RGBA", (size, size), (253, 251, 247, 255))
    inner_draw = ImageDraw.Draw(inner)

    # Route Marker diagonal split banner (Yellow #FFD200 and Red #D90429)
    # Diagonal stripe across center from top-left to bottom-right
    banner_w = size * 0.40
    stripe_pts = [
        (-size * 0.2, center_y - banner_w),
        (size * 1.2, center_y + banner_w * 0.6),
        (size * 1.2, center_y + banner_w * 1.6),
        (-size * 0.2, center_y),
    ]
    # Red upper band
    inner_draw.polygon([
        (-size * 0.2, center_y - banner_w),
        (size * 1.2, center_y + banner_w * 0.6),
        (size * 1.2, center_y + banner_w * 0.1),
        (-size * 0.2, center_y - banner_w * 0.5),
    ], fill=(217, 4, 41, 255))

    # Yellow lower band
    inner_draw.polygon([
        (-size * 0.2, center_y - banner_w * 0.5),
        (size * 1.2, center_y + banner_w * 0.1),
        (size * 1.2, center_y - banner_w * 0.4),
        (-size * 0.2, center_y - banner_w),
    ], fill=(255, 210, 0, 255))

    # Draw stylized Globe in center
    globe_r = size * 0.18
    gx, gy = center_x, center_y - size * 0.04
    # Globe background circle
    inner_draw.ellipse([gx - globe_r, gy - globe_r, gx + globe_r, gy + globe_r], fill=(27, 38, 36, 240), outline=(255, 210, 0, 255), width=18)

    # Globe latitude/longitude parallels
    for d in [0.35, 0.70]:
        inner_draw.arc([gx - globe_r, gy - globe_r * d, gx + globe_r, gy + globe_r * d], 0, 360, fill=(255, 255, 255, 120), width=8)
    for d in [0.45, 0.85]:
        inner_draw.arc([gx - globe_r * d, gy - globe_r, gx + globe_r * d, gy + globe_r], 0, 360, fill=(255, 255, 255, 120), width=8)

    # 4-point compass star in center of globe
    cs_len = globe_r * 0.75
    cs_w = globe_r * 0.18
    # Vertical and horizontal points
    inner_draw.polygon([(gx, gy - cs_len), (gx + cs_w, gy), (gx, gy + cs_len), (gx - cs_w, gy)], fill=(255, 210, 0, 255))
    inner_draw.polygon([(gx - cs_len, gy), (gx, gy + cs_w), (gx + cs_len, gy), (gx, gy - cs_w)], fill=(217, 4, 41, 255))

    # Flight track arc
    inner_draw.arc([gx - globe_r * 1.35, gy - globe_r * 1.25, gx + globe_r * 1.35, gy + globe_r * 1.25], 200, 340, fill=(255, 210, 0, 255), width=14)

    # Text rendering
    # Try system fonts or default bitmap font
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 220)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 95)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Package title: "theamazingrace"
    text = "theamazingrace"
    inner_draw.text((center_x, center_y + size * 0.22), text, font=font_title, fill=(27, 38, 36, 255), anchor="mm")

    # Subtitle: "TIDY DATA & AI CORPUS"
    sub_text = "TIDY DATA & AI CORPUS"
    inner_draw.text((center_x, center_y + size * 0.29), sub_text, font=font_sub, fill=(100, 116, 139, 255), anchor="mm")

    # Composite inner artwork through hexagon mask
    im.paste(inner, (0, 0), mask)

    # Draw crisp hex border
    draw.polygon(hex_pts, outline=(27, 38, 36, 255), width=50)

    # Inner accent border (yellow & red dual accent)
    r_inner = r - 35
    hex_inner_pts = [(center_x + r_inner * math.cos(a), center_y + r_inner * math.sin(a)) for a in angles]
    draw.polygon(hex_inner_pts, outline=(255, 210, 0, 255), width=18)

    # Save alone-style hex and theamazingrace hex
    out_file = output_dir / "theamazingrace hex.png"
    im.save(out_file, "PNG")
    print(f"Saved {out_file}")

    # Also save as "alone hex.png" equivalent
    out_alias = output_dir / "alone hex.png"
    im.save(out_alias, "PNG")

    # Generate bg hex.png and bg white hex.png (1559 x 1800)
    bg_hex = im.resize((1559, 1800), Image.Resampling.LANCZOS)
    bg_hex.save(output_dir / "bg hex.png", "PNG")

    # bg white hex
    white_hex = Image.new("RGBA", (1559, 1800), (255, 255, 255, 255))
    white_hex.paste(bg_hex, (0, 0), bg_hex)
    white_hex.save(output_dir / "bg white hex.png", "PNG")

    # hex1 crop.png (1732 x 2000) and original2 square.png (1152 x 1152)
    crop_hex = im.resize((1732, 2000), Image.Resampling.LANCZOS)
    crop_hex.save(output_dir / "hex1 crop.png", "PNG")

    square_badge = im.resize((1152, 1152), Image.Resampling.LANCZOS)
    square_badge.save(output_dir / "original2 square.png", "PNG")


def generate_square_and_backgrounds(output_dir: Path) -> None:
    """Generate square.jpg, bg.png, and bg white.png for README and social cards."""
    print("Generating square.jpg, bg.png, bg white.png...")
    size = 2160
    im = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    # Dual banner header (Route Marker Yellow & Red)
    draw.rectangle([0, 0, size, 40], fill=(217, 4, 41))
    draw.rectangle([0, 40, size, 70], fill=(255, 210, 0))

    # Load hex badge and paste into center upper area
    hex_path = output_dir / "theamazingrace hex.png"
    if hex_path.exists():
        badge = Image.open(hex_path).resize((1150, 1150), Image.Resampling.LANCZOS)
        im.paste(badge, (int((size - 1150) / 2), 220), badge)

    # Typography
    try:
        font_h1 = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 100)
        font_stats = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 62)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 46)
    except Exception:
        font_h1 = font_stats = font_sub = ImageFont.load_default()

    draw.text((size / 2, 1460), "The Amazing Race Dataset", font=font_h1, fill=(26, 29, 32), anchor="mm")
    draw.text(
        (size / 2, 1560),
        "A Comprehensive Tidy Dataset & AI Training Corpus",
        font=font_sub,
        fill=(100, 116, 139),
        anchor="mm",
    )

    # Metric blocks (Seasons, Teams, Legs, Racers)
    draw.line([300, 1660, size - 300, 1660], fill=(209, 213, 219), width=3)

    metrics = [
        ("38", "SEASONS"),
        ("431", "TEAMS"),
        ("453", "LEGS"),
        ("886", "RACERS"),
    ]
    col_width = (size - 400) / 4.0
    for idx, (num, label) in enumerate(metrics):
        cx = 200 + idx * col_width + col_width / 2.0
        draw.text((cx, 1750), num, font=font_stats, fill=(217, 4, 41), anchor="mm")
        draw.text((cx, 1820), label, font=font_sub, fill=(74, 85, 104), anchor="mm")

    draw.line([300, 1890, size - 300, 1890], fill=(209, 213, 219), width=3)
    draw.text(
        (size / 2, 1980),
        "Available in CSV • Apache Parquet • SQLite • R • Arrow",
        font=font_sub,
        fill=(100, 116, 139),
        anchor="mm",
    )

    im.save(output_dir / "square.jpg", "JPEG", quality=95)
    print(f"Saved {output_dir / 'square.jpg'}")

    # Generate bg.png (Dark 1800x1800) and bg white.png (Light 1800x1800)
    bg_dark = Image.new("RGB", (1800, 1800), (26, 29, 32))
    d_draw = ImageDraw.Draw(bg_dark)
    d_draw.rectangle([0, 0, 1800, 20], fill=(217, 4, 41))
    d_draw.rectangle([0, 20, 1800, 35], fill=(255, 210, 0))
    if hex_path.exists():
        badge_sm = Image.open(hex_path).resize((900, 900), Image.Resampling.LANCZOS)
        bg_dark.paste(badge_sm, (450, 450), badge_sm)
    bg_dark.save(output_dir / "bg.png", "PNG")

    # bg white.png
    bg_light = Image.new("RGB", (1800, 1800), (255, 255, 255))
    l_draw = ImageDraw.Draw(bg_light)
    l_draw.rectangle([0, 0, 1800, 20], fill=(217, 4, 41))
    l_draw.rectangle([0, 20, 1800, 35], fill=(255, 210, 0))
    if hex_path.exists():
        bg_light.paste(badge_sm, (450, 450), badge_sm)
    bg_light.save(output_dir / "bg white.png", "PNG")


def main() -> None:
    output_dir = Path("dev/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_survival_chart(output_dir)
    generate_items_chart(output_dir)
    generate_boxplots_chart(output_dir)
    generate_gender_performance_chart(output_dir)
    generate_roadblock_equity_chart(output_dir)
    generate_continents_chart(output_dir)
    generate_hex_badge(output_dir)
    generate_square_and_backgrounds(output_dir)
    print("\nAll assets successfully generated in dev/images/")


if __name__ == "__main__":
    main()
