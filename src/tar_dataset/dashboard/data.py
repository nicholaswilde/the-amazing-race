"""Data loading and caching utilities for the dashboard."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from tar_dataset.processors.builder import DatasetBuilder

logger = logging.getLogger(__name__)


def _get_data_dir() -> Path:
    """Resolve data directory relative to repository root."""
    cwd_data = Path("data/processed")
    if cwd_data.exists():
        return cwd_data
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / "data" / "processed"
        if candidate.exists():
            return candidate
    return cwd_data


def _get_raw_dir() -> Path:
    """Resolve raw data directory relative to repository root."""
    cwd_raw = Path("data/raw")
    if cwd_raw.exists():
        return cwd_raw
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / "data" / "raw"
        if candidate.exists():
            return candidate
    return cwd_raw


def load_table(name: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    """Load a processed table from Parquet or CSV."""
    p = Path(data_dir) if data_dir else _get_data_dir()
    parquet_path = p / f"{name}.parquet"
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)
    csv_path = p / f"{name}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_all_datasets(
    data_dir: str | None = None,
    raw_dir: str | None = None,
    include_in_progress: bool = True,
) -> dict[str, pd.DataFrame]:
    """Load all processed dataset tables, appending in-progress seasons if found."""
    resolved_dir = Path(data_dir) if data_dir else _get_data_dir()
    resolved_raw = Path(raw_dir) if raw_dir else _get_raw_dir()

    table_names = [
        "seasons",
        "episodes",
        "teams",
        "contestants",
        "legs",
        "leg_results",
        "tasks",
    ]
    base_datasets = {name: load_table(name, resolved_dir) for name in table_names}

    if not include_in_progress:
        return base_datasets

    # Detect in-progress seasons in raw/wikipedia
    wiki_dir = resolved_raw / "wikipedia"
    if not wiki_dir.exists():
        return base_datasets

    known_seasons = set()
    seasons_df = base_datasets.get("seasons", pd.DataFrame())
    if not seasons_df.empty and "season" in seasons_df.columns:
        known_seasons = set(seasons_df["season"].dropna().unique().astype(int))

    in_progress_files = []
    for file in sorted(wiki_dir.glob("season_*.json")):
        try:
            content = json.loads(file.read_text(encoding="utf-8"))
            s_num = int(content.get("season", 0))
            if s_num > 0 and s_num not in known_seasons:
                in_progress_files.append(content)
        except Exception as exc:
            logger.debug("Failed reading %s for in-progress check: %s", file, exc)

    if not in_progress_files:
        return base_datasets

    try:
        builder = DatasetBuilder(raw_dir=resolved_raw, include_in_progress=True)
        in_prog_tables = {
            "seasons": builder.build_seasons_df(in_progress_files),
            "episodes": builder.build_episodes_df(in_progress_files),
            "teams": builder.build_teams_df(in_progress_files),
            "contestants": builder.build_contestants_df(in_progress_files),
            "legs": builder.build_legs_df(in_progress_files),
            "leg_results": builder.build_leg_results_df(in_progress_files),
            "tasks": builder.build_tasks_df(in_progress_files),
        }

        for name in table_names:
            base_tbl = base_datasets[name]
            in_prog_tbl = in_prog_tables[name]
            if not in_prog_tbl.empty:
                if base_tbl.empty:
                    base_datasets[name] = in_prog_tbl
                else:
                    base_datasets[name] = pd.concat(
                        [base_tbl, in_prog_tbl], ignore_index=True
                    )
    except Exception as err:
        logger.warning("Failed appending in-progress seasons: %s", err)

    return base_datasets
