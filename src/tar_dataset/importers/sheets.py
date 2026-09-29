"""Google Sheets importer for The Amazing Race datasets."""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


def google_sheet_to_csv_url(url: str, gid: str = "0") -> str:
    """Convert a standard Google Sheets sharing/edit URL to a direct CSV export URL.

    Example input:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0
    Output:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv&gid=0
    """
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError(f"Invalid Google Sheets URL format: {url}")
    sheet_id = match.group(1)

    # Check for gid in URL
    gid_match = re.search(r"gid=(\d+)", url)
    if gid_match:
        gid = gid_match.group(1)

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


class SheetsImporter:
    """Imports community spreadsheets from Google Sheets or CSV URLs."""

    def __init__(self, raw_dir: Path | str = "data/raw/sheets") -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=30.0)

    def import_public_sheet(
        self,
        sheet_url: str,
        name: str,
        gid: str = "0",
        save: bool = True,
    ) -> pd.DataFrame:
        """Fetch a public Google Sheet as a pandas DataFrame."""
        if "spreadsheets/d" in sheet_url:
            export_url = google_sheet_to_csv_url(sheet_url, gid=gid)
        else:
            export_url = sheet_url

        logger.info("Importing Google Sheet from %s (name: %s)", export_url, name)
        resp = self.client.get(export_url)
        resp.raise_for_status()

        # Parse CSV
        df = pd.read_csv(io.StringIO(resp.text))

        # Standardize column headers: snake_case
        df.columns = [
            re.sub(r"[^\w\s]", "", str(col)).strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        if save:
            out_file = self.raw_dir / f"{name}.csv"
            df.to_csv(out_file, index=False)
            logger.info("Saved imported sheet to %s (%d rows)", out_file, len(df))

        return df

    def import_local_csv(self, file_path: Path | str, name: str | None = None) -> pd.DataFrame:
        """Import a local CSV into the sheets raw directory."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        name = name or path.stem
        df = pd.read_csv(path)
        df.columns = [
            re.sub(r"[^\w\s]", "", str(col)).strip().lower().replace(" ", "_")
            for col in df.columns
        ]
        out_file = self.raw_dir / f"{name}.csv"
        df.to_csv(out_file, index=False)
        return df
