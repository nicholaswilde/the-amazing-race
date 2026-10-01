"""SQLite export utility for The Amazing Race dataset.

Provides zero-dependency relational SQL querying across all 7 processed tables.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "episodes",
    "contestants",
    "teams",
    "legs",
    "leg_results",
    "tasks",
]


class SQLiteExporter:
    """Exports processed TAR Parquet/CSV datasets into a unified SQLite database."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        db_path: Path | str | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.db_path = Path(db_path) if db_path else self.processed_dir / "tar.db"

    def export(self) -> Path:
        """Export all processed tables into SQLite database with optimized indexes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(self.db_path)
        tables_exported = 0

        try:
            for table_name in TABLES:
                parquet_file = self.processed_dir / f"{table_name}.parquet"
                csv_file = self.processed_dir / f"{table_name}.csv"

                if parquet_file.exists():
                    df = pd.read_parquet(parquet_file)
                elif csv_file.exists():
                    df = pd.read_csv(csv_file)
                else:
                    logger.warning("No data file found for table '%s'", table_name)
                    continue

                # Write table to SQLite
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                tables_exported += 1
                logger.info(
                    "Exported %d rows into SQLite table '%s'", len(df), table_name
                )

            # Build query performance indexes only on existing tables
            cursor = conn.cursor()
            existing_tables = {
                r[0]
                for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            table_indexes = {
                "seasons": "CREATE INDEX IF NOT EXISTS idx_seasons_pk ON seasons(version, season);",
                "episodes": "CREATE INDEX IF NOT EXISTS idx_episodes_lookup ON episodes(version, season, episode);",
                "contestants": "CREATE INDEX IF NOT EXISTS idx_contestants_team ON contestants(version, season, contestant_id);",
                "teams": "CREATE INDEX IF NOT EXISTS idx_teams_lookup ON teams(version, season, team_name);",
                "legs": "CREATE INDEX IF NOT EXISTS idx_legs_lookup ON legs(version, season, leg_number);",
                "leg_results": [
                    "CREATE INDEX IF NOT EXISTS idx_leg_results_team ON leg_results(version, season, team_name);",
                    "CREATE INDEX IF NOT EXISTS idx_leg_results_leg ON leg_results(version, season, leg_number);",
                ],
                "tasks": "CREATE INDEX IF NOT EXISTS idx_tasks_leg ON tasks(version, season, leg_number);",
            }

            for tbl, idx_defs in table_indexes.items():
                if tbl in existing_tables:
                    if isinstance(idx_defs, list):
                        for idx_sql in idx_defs:
                            cursor.execute(idx_sql)
                    else:
                        cursor.execute(idx_defs)

            conn.commit()
            logger.info(
                "Successfully created SQLite database at %s with %d tables",
                self.db_path,
                tables_exported,
            )
        finally:
            conn.close()

        # Normalize SQLite database header version bytes (offset 96-100) to ensure
        # cross-platform and cross-Python build determinism
        try:
            if self.db_path.exists():
                with open(self.db_path, "r+b") as f:
                    f.seek(96)
                    f.write(
                        b"\x00\x2e\x8a\x14"
                    )  # Canonical SQLite version 3050004 (3.50.4)
        except OSError as e:
            logger.warning("Could not normalize SQLite header: %s", e)

        return self.db_path


def export_to_sqlite(
    processed_dir: Path | str = "data/processed",
    db_path: Path | str | None = None,
) -> Path:
    """Helper function to run SQLite export."""
    exporter = SQLiteExporter(processed_dir=processed_dir, db_path=db_path)
    return exporter.export()
