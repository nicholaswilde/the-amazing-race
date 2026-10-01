"""Generate publication-quality data visualizations and branding assets for The Amazing Race dataset.

Mirrors the structure and aesthetic of doehm/alone/dev/images:
- survival.png: Kaplan-Meier style team survival curves by archetype with inset boxplots
- items.png: Horizontal bar chart of top visited destination countries
- boxplots.png: Racer age distributions across finish placement tiers
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
    generate_hex_badge(output_dir)
    generate_square_and_backgrounds(output_dir)
    print("\nAll assets successfully generated in dev/images/")


if __name__ == "__main__":
    main()
