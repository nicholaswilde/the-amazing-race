---
version: alpha
name: The Amazing Race Dataset & Dashboard
description: Visual identity and design system for The Amazing Race dataset, empirical analytics platform, and Streamlit dashboard.
colors:
  primary: "#cba6f7"
  secondary: "#89b4fa"
  tertiary: "#fab387"
  neutral: "#cdd6f4"
  base: "#1e1e2e"
  mantle: "#181825"
  crust: "#11111b"
  surface0: "#313244"
  surface1: "#45475a"
  subtext0: "#a6adc8"
  subtext1: "#bac2de"
  mauve: "#cba6f7"
  blue: "#89b4fa"
  green: "#a6e3a1"
  peach: "#fab387"
  red: "#f38ba8"
  yellow: "#f9e2af"
  teal: "#94e2d5"
typography:
  h1:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
  h2:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
  h3:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
  body-md:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  code:
    fontFamily: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
components:
  card:
    backgroundColor: "{colors.mantle}"
    borderColor: "{colors.surface0}"
    textColor: "{colors.neutral}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.lg}"
  button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.crust}"
    borderRadius: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  metric:
    backgroundColor: "{colors.mantle}"
    borderColor: "{colors.surface0}"
    labelColor: "{colors.subtext1}"
    valueColor: "{colors.primary}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.md} {spacing.lg}"
  expander:
    backgroundColor: "{colors.mantle}"
    borderColor: "{colors.surface0}"
    borderRadius: "{rounded.md}"
  chart:
    backgroundColor: "{colors.base}"
    textColor: "{colors.neutral}"
    gridColor: "{colors.surface0}"
    accentColor: "{colors.primary}"
---

## Overview

The Amazing Race (TAR) Dataset & Dashboard platform delivers empirical analytics, predictions, race telemetry, and interactive challenge exploration across 38+ seasons. The visual style follows a high-density, modern dark theme utilizing the canonical **Catppuccin Mocha** palette. It communicates analytical clarity, legibility across rich tabular and spatial metrics, and thematic ties to global travel and race tracking.

## Colors

The system uses the **Catppuccin Mocha** theme specification:

- **Primary (`#cba6f7` - Mauve)**: Primary brand accent, selected tab indicators, primary metrics, active status.
- **Secondary (`#89b4fa` - Blue)**: Secondary highlights, hyperlinks, interactive controls, area chart vertices.
- **Tertiary (`#fab387` - Peach)**: Alert indicators, speed bumps, hazard warnings, route markers.
- **Neutral (`#cdd6f4` - Text)**: High-contrast primary reading text across views.
- **Subtext Layers**:
  - `subtext1` (`#bac2de`): Metric labels, timestamps, secondary metadata.
  - `subtext0` (`#a6adc8`): Inactive tabs, disabled states, subtle notes.
- **Background Tiers**:
  - Base (`#1e1e2e`): Application canvas and primary chart backgrounds.
  - Mantle (`#181825`): Cards, sidebars, metrics, containers, expander headers.
  - Crust (`#11111b`): Input fields, code containers, deeply recessed regions.
  - Surface0 (`#313244`): Borders, dividers, table grid lines, subtle active outlines.
  - Surface1 (`#45475a`): Elevated borders, hover outlines.
- **Visualization & Status Palette**:
  - Success / Pit Stop (`#a6e3a1` - Green): Legs won, top placement, active racing status.
  - Elimination / Hazard (`#f38ba8` - Red): Elimination, U-turned, sunk-cost trap warning.
  - Warning / Caution (`#f9e2af` - Yellow): Yields, switch-zone hazards, mid-pack caution.
  - Analytical Accents (`#94e2d5` - Teal): Detours, roadblock parity metrics, secondary series.

All foreground-background text pairings maintain WCAG AA minimum 4.5:1 contrast against `#1e1e2e` and `#181825`.

## Typography

Standard clean system sans-serif hierarchy for data density and clarity:
- **Font Family**: `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Monospace Family**: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
- **Headings**:
  - `h1`: 32px / 700 weight for page and view titles.
  - `h2`: 24px / 600 weight for view sections and primary module headings.
  - `h3`: 18px / 600 weight for card headers, sub-metrics, and panel titles.
- **Body & Data**:
  - `body-md`: 14px / 400 weight (1.6 line height) for prose and captions.
  - `code`: 13px / 400 weight for leg split times, season codes, placings, and numerical data tables.

## Layout & Spacing

- **Page Grid**: Wide layout mode with an expanded collapsible sidebar.
- **Spacing Scale**: Base 4px rhythm (`xs`: 4px, `sm`: 8px, `md`: 12px, `lg`: 16px, `xl`: 24px, `xxl`: 32px).
- **Rhythm**:
  - Metric cards and UI modules use `16px` padding and `12px` gaps.
  - Content sections separated by `24px` to `32px`.
  - Side-by-side comparative views balance 50/50 split columns on desktop, stacking gracefully on mobile.

## Elevation & Depth

- **Depth via Tones**: Elevation is achieved through background luminance stepping (`#1e1e2e` base -> `#181825` container/card -> `#313244` border) rather than heavy drop shadows.
- **Borders**: 1px subtle stroke with `Surface0` (`#313244`) on elevated cards and interactive elements.
- **Z-Index Strategy**:
  - Base content: 0
  - Sticky controls and table headers: 10
  - Overlays, popovers, and tooltips: 100

## Shapes

- **Corner Radii**:
  - Small elements / tags / badges: `4px` (`rounded.sm`)
  - Inputs, buttons, and expander headers: `6px` (`rounded.md`)
  - Metric cards, chart containers, view panels: `8px` (`rounded.lg`)
  - Avatars / status pills: `9999px` (`rounded.full`)

## Components

- **Metric Cards (`stMetric`)**:
  - Background: Mantle (`#181825`), Border: 1px solid Surface0 (`#313244`), Radius: 8px.
  - Value: Mauve (`#cba6f7`), Label: Subtext1 (`#bac2de`).
- **Navigation & Tabs (`stTabs`)**:
  - Inactive tab text: Subtext0 (`#a6adc8`).
  - Selected tab indicator: Mauve (`#cba6f7`) text and bottom accent bar.
- **Expanders (`stExpander`)**:
  - Header background: Mantle (`#181825`), Radius: 6px.
- **Buttons (`stButton`)**:
  - Primary: Mauve (`#cba6f7`) with dark crust text (`#11111b`).
- **Tables & DataFrames (`stDataFrame`)**:
  - Dark container styled with muted header borders and alternate row shading.
- **Data Visualizations (Altair / Plotly / Matplotlib)**:
  - Background: Base (`#1e1e2e`), Text / Axis: Neutral (`#cdd6f4`), Grid lines: Surface0 (`#313244`).
  - Gradients: Mauve (`#cba6f7`) fading into Base (`#1e1e2e`) for area curves.

## Do's and Don'ts

### Do's
- **Do** stick to Catppuccin Mocha tokens (`--catppuccin-*`) across all UI modules, Streamlit components, and plot styles.
- **Do** ensure all data visualizations (Altair, Plotly, Matplotlib) adopt Mocha colors (`#1e1e2e` background, `#cdd6f4` axis text, palette series).
- **Do** maintain tabular compactness for dense leg and contestant statistics.
- **Do** verify text readability meets WCAG AA 4.5:1 contrast standards.

### Don'ts
- **Don't** use arbitrary inline hex codes or magic pixel dimensions outside the token scale.
- **Don't** mix light mode components into dark dashboard views.
- **Don't** use saturated pure primaries (`#ff0000`, `#00ff00`, `#0000ff`); use Mocha semantic variants (`#f38ba8`, `#a6e3a1`, `#89b4fa`).
- **Don't** create deep multi-level drop shadows; use color stepping (`Mantle` on `Base`) with `Surface0` borders.
