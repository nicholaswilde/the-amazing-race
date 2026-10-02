"""Tests for R language dataset export and companion R package scaffolding."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadr
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.r_export import TABLES, RExporter, export_to_r


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_processed_dir(tmp_path: Path) -> Path:
    """Create mock processed directory with all 7 tables."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    df_seasons = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "n_teams": 11,
                "n_legs": 13,
                "n_episodes": 13,
                "winners": "Rob & Brennan",
                "distance_miles": 35000.0,
                "distance_km": 56327.0,
                "air_dates": "2001",
                "filming_dates": "2001",
                "wiki_url": "https://example.com/s1",
            }
        ]
    )
    df_episodes = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "episode": 1,
                "title": "Premiere",
                "air_date": "2001-09-05",
                "viewers_millions": 8.6,
            }
        ]
    )
    df_contestants = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "contestant_id": "US-S01-rob",
                "name": "Rob",
                "age": 27,
                "gender": "M",
                "relationship": "Lawyers/Best Friends",
                "hometown": "San Francisco, CA",
                "status": "Winners",
            }
        ]
    )
    df_teams = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "team_id": "US-S01-rob-brennan",
                "team_name": "Rob & Brennan",
                "relationship": "Lawyers/Best Friends",
                "hometown": "San Francisco, CA",
                "result": 1,
                "status": "Winners",
                "legs_won": 5,
                "legs_completed": 13,
                "gender_composition": "MM",
            }
        ]
    )
    df_legs = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 1,
                "route_header": "USA to South Africa",
                "itinerary_stops": 4,
                "tasks_count": 3,
                "narrative": "Teams raced across Johannesburg.",
            }
        ]
    )
    df_results = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 1,
                "team_name": "Rob & Brennan",
                "placement": 1,
                "raw_cell": "1st",
                "is_non_elimination": False,
                "fast_forward": True,
                "uturn": False,
                "yield": False,
                "speed_bump": False,
            }
        ]
    )
    df_tasks = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 1,
                "task_type": "Fast Forward",
                "description": "Find the key in the field.",
            }
        ]
    )

    df_seasons.to_parquet(proc_dir / "seasons.parquet")
    df_episodes.to_parquet(proc_dir / "episodes.parquet")
    df_contestants.to_parquet(proc_dir / "contestants.parquet")
    df_teams.to_parquet(proc_dir / "teams.parquet")
    df_legs.to_parquet(proc_dir / "legs.parquet")
    df_results.to_parquet(proc_dir / "leg_results.parquet")
    df_tasks.to_parquet(proc_dir / "tasks.parquet")

    return proc_dir


def test_rexporter_basic(tmp_path: Path, mock_processed_dir: Path) -> None:
    """Test exporting RDS and RDA files with proper types and scaffolding."""
    r_out = tmp_path / "r_processed"
    r_pkg = tmp_path / "theamazingrace_pkg"

    exporter = RExporter(
        processed_dir=mock_processed_dir,
        r_output_dir=r_out,
        r_pkg_dir=r_pkg,
    )
    results = exporter.export_all()

    # Check RDS files
    assert len(results["rds"]) == 7
    for t in TABLES:
        rds_file = r_out / f"{t}.rds"
        assert rds_file.exists()
        df = pyreadr.read_r(rds_file)[None]
        assert len(df) == 1
        assert "season" in df.columns
        assert df["season"].dtype == "int32"

    # Check RDA files in package
    assert len(results["rda"]) == 7
    for t in TABLES:
        rda_file = r_pkg / "data" / f"{t}.rda"
        assert rda_file.exists()
        df = pyreadr.read_r(rda_file)[t]
        assert len(df) == 1

    # Check boolean types in leg_results
    lr_df = pyreadr.read_r(r_out / "leg_results.rds")[None]
    assert lr_df["fast_forward"].dtype == bool
    assert lr_df["is_non_elimination"].dtype == bool

    # Check roxygen file
    roxygen_file = results["roxygen"]
    assert roxygen_file.exists()
    content = roxygen_file.read_text(encoding="utf-8")
    assert "Seasons in The Amazing Race" in content
    assert '"seasons"' in content

    # Check Rd manual documentation files
    assert len(results["rd"]) == 7
    for t in TABLES:
        rd_file = r_pkg / "man" / f"{t}.Rd"
        assert rd_file.exists()
        rd_content = rd_file.read_text(encoding="utf-8")
        assert f"\\name{{{t}}}" in rd_content
        assert "\\docType{data}" in rd_content

    # Check package scaffolding files
    scaffold = results["scaffold"]
    assert "DESCRIPTION" in scaffold
    assert "NAMESPACE" in scaffold
    assert "README.md" in scaffold
    assert "vignettes/introduction.Rmd" in scaffold
    assert "tests/testthat/test-datasets.R" in scaffold

    desc_content = (r_pkg / "DESCRIPTION").read_text(encoding="utf-8")
    assert "Package: theamazingrace" in desc_content
    assert "LazyData: true" in desc_content
    assert "LazyDataCompression: xz" in desc_content


def test_export_to_r_helper(tmp_path: Path, mock_processed_dir: Path) -> None:
    """Test the export_to_r convenience function."""
    r_out = tmp_path / "r_processed"
    r_pkg = tmp_path / "theamazingrace_pkg"

    results = export_to_r(
        processed_dir=mock_processed_dir,
        r_output_dir=r_out,
        r_pkg_dir=r_pkg,
    )

    assert len(results["rds"]) == 7
    assert len(results["rda"]) == 7
    assert (r_pkg / "DESCRIPTION").exists()


def test_rexporter_missing_table(tmp_path: Path) -> None:
    """Test RExporter raises FileNotFoundError when a table is missing."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    exporter = RExporter(processed_dir=empty_dir)

    with pytest.raises(FileNotFoundError):
        exporter.load_table("seasons")


def test_cli_export_r(
    cli_runner: CliRunner, tmp_path: Path, mock_processed_dir: Path
) -> None:
    """Test running tar-dataset export-r via CLI."""
    r_out = tmp_path / "cli_r_processed"
    r_pkg = tmp_path / "cli_r_pkg"

    result = cli_runner.invoke(
        app,
        [
            "export-r",
            "--processed-dir",
            str(mock_processed_dir),
            "--r-dir",
            str(r_out),
            "--pkg-dir",
            str(r_pkg),
        ],
    )

    assert result.exit_code == 0
    assert "Exporting The Amazing Race datasets to R formats" in result.stdout
    assert "Exported 7 RDS tables" in result.stdout
    assert (r_out / "seasons.rds").exists()
    assert (r_pkg / "data" / "seasons.rda").exists()
