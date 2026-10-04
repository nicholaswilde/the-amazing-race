"""Data loading and caching utilities for the dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def _get_data_dir() -> Path:
    """Resolve data directory relative to repository root."""
    # Try current directory data/processed
    cwd_data = Path("data/processed")
    if cwd_data.exists():
        return cwd_data
    # Fallback to traversing upwards
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / "data" / "processed"
        if candidate.exists():
            return candidate
    return cwd_data


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
def load_all_datasets(data_dir: str | None = None) -> dict[str, pd.DataFrame]:
    """Load all processed dataset tables with Streamlit caching."""
    resolved_dir = Path(data_dir) if data_dir else _get_data_dir()
    table_names = [
        "seasons",
        "episodes",
        "teams",
        "contestants",
        "legs",
        "leg_results",
        "tasks",
    ]
    return {name: load_table(name, resolved_dir) for name in table_names}
