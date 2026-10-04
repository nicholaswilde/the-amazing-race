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

    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    )


def google_sheet_to_xlsx_url(url: str) -> str:
    """Convert a standard Google Sheets / Drive sharing URL to a direct XLSX export URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError(f"Invalid Google Sheets URL format: {url}")
    sheet_id = match.group(1)
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"


class SheetsImporter:
    """Imports community spreadsheets from Google Sheets, Google Drive Excel workbooks, or CSV URLs."""

    def __init__(self, raw_dir: Path | str = "data/raw/sheets") -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=60.0, follow_redirects=True)

    def import_public_sheet_csv(
        self,
        sheet_id: str,
        name: str,
        gid: str = "0",
        save: bool = True,
    ) -> pd.DataFrame:
        """Fetch a public Google Sheet as CSV given a sheet ID or URL."""
        if not sheet_id.startswith("http"):
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={gid}"
        else:
            url = sheet_id
        return self.import_public_sheet(url, name=name, gid=gid, save=save)

    def import_public_sheet(
        self,
        sheet_url: str,
        name: str,
        gid: str = "0",
        sheet_name: str | None = None,
        prefer_xlsx: bool = False,
        save: bool = True,
    ) -> pd.DataFrame:
        """Fetch a public Google Sheet or Google Drive Excel workbook as a pandas DataFrame."""
        if "spreadsheets/d" in sheet_url:
            csv_export_url = google_sheet_to_csv_url(sheet_url, gid=gid)
            xlsx_export_url = google_sheet_to_xlsx_url(sheet_url)
        else:
            csv_export_url = sheet_url
            xlsx_export_url = None

        logger.info("Importing sheet from %s (name: %s)", sheet_url, name)

        if (prefer_xlsx or sheet_name is not None) and xlsx_export_url:
            logger.info("Directly downloading multi-tab XLSX from %s", xlsx_export_url)
            resp = self.client.get(xlsx_export_url)
            resp.raise_for_status()
            return self._parse_and_save_xlsx(resp.content, name, sheet_name, save)

        try:
            resp = self.client.get(csv_export_url)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 400 and xlsx_export_url:
                logger.info(
                    "CSV export failed with 400; downloading XLSX workbook from %s",
                    xlsx_export_url,
                )
                resp = self.client.get(xlsx_export_url)
                resp.raise_for_status()
                return self._parse_and_save_xlsx(resp.content, name, sheet_name, save)
            raise

        # Standardize column headers: snake_case
        df.columns = [
            re.sub(r"[^\w\s]", "", str(col)).strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        if save:
            out_file = self.raw_dir / f"{name}.csv"
            df.to_csv(out_file, index=False)
            logger.info("Saved imported sheet to %s (%d rows)", out_file, len(df))

        try:
            from tar_dataset.processors.geocoding import ensure_legs_geocoded

            ensure_legs_geocoded(df)
        except Exception as e:
            logger.debug("Auto-geocoding skipped for sheet '%s': %s", name, e)

        return df

    def _parse_and_save_xlsx(
        self,
        content: bytes,
        name: str,
        sheet_name: str | None,
        save: bool,
    ) -> pd.DataFrame:
        """Parse raw XLSX workbook bytes, save raw file, and export tabs as CSVs."""
        xlsx_file = self.raw_dir / f"{name}.xlsx"
        if save:
            xlsx_file.write_bytes(content)

        xl = pd.ExcelFile(xlsx_file if save else io.BytesIO(content))
        target_sheet = sheet_name
        if not target_sheet:
            if "SQL_Data" in xl.sheet_names:
                target_sheet = "SQL_Data"
            elif len(xl.sheet_names) > 1 and xl.sheet_names[0].lower() in {
                "title",
                "welcome page",
                "logs",
            }:
                target_sheet = xl.sheet_names[1]
            else:
                target_sheet = xl.sheet_names[0]

        df = pd.read_excel(xl, sheet_name=target_sheet)
        df.columns = [
            re.sub(r"[^\w\s]", "", str(col)).strip().lower().replace(" ", "_")
            for col in df.columns
        ]

        if save:
            out_file = self.raw_dir / f"{name}.csv"
            df.to_csv(out_file, index=False)
            logger.info(
                "Saved imported sheet [%s] to %s (%d rows)",
                target_sheet,
                out_file,
                len(df),
            )

            for s_name in xl.sheet_names:
                if s_name.lower() in {"welcome page", "logs", "presentation"}:
                    continue
                try:
                    s_df = pd.read_excel(xl, sheet_name=s_name)
                    if len(s_df) > 0:
                        s_slug = (
                            re.sub(r"[^\w\s]", "", s_name)
                            .strip()
                            .lower()
                            .replace(" ", "_")
                            .replace("-", "_")
                        )
                        s_df.columns = [
                            re.sub(r"[^\w\s]", "", str(col))
                            .strip()
                            .lower()
                            .replace(" ", "_")
                            for col in s_df.columns
                        ]
                        s_out = self.raw_dir / f"{name}_{s_slug}.csv"
                        s_df.to_csv(s_out, index=False)
                except Exception as e:
                    logger.warning("Could not export tab '%s': %s", s_name, e)

        return df

    def import_local_csv(
        self, file_path: Path | str, name: str | None = None
    ) -> pd.DataFrame:
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

        try:
            from tar_dataset.processors.geocoding import ensure_legs_geocoded

            ensure_legs_geocoded(df)
        except Exception as e:
            logger.debug("Auto-geocoding skipped for csv '%s': %s", name, e)

        return df
