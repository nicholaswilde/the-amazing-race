"""Unit tests for dataset gap auditor and completeness tooling."""

from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.gap_auditor import DatasetGapAuditor


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_gap_auditor_completeness():
    """Verify gap auditor computes overall dataset completeness metrics on backfilled dataset."""
    auditor = DatasetGapAuditor()
    report = auditor.audit_all()

    assert report["overall_completeness_pct"] >= 99.0
    assert report["total_cells"] > 50000
    assert report["total_missing"] == 0
    assert isinstance(report["gaps"], list)


def test_gap_auditor_season_29_backfill_verified():
    """Verify that Season 29 contestants relationship backfill has 0 missing records."""
    auditor = DatasetGapAuditor()

    missing_s29 = auditor.get_missing_records("contestants", "relationship", season=29)
    assert len(missing_s29) == 0, (
        f"Expected 0 missing relationship cells in Season 29 contestants after backfill, found {len(missing_s29)}"
    )

    contestants = auditor.load_table("contestants")
    s29 = contestants[contestants["season"] == 29]
    assert len(s29) == 22
    assert (s29["relationship"] == "Strangers (Paired at Starting Line)").all()


def test_gap_auditor_detection_with_synthetic_gaps(tmp_path):
    """Specifically verify the auditor identifies missing cells when gaps are present."""
    # Create synthetic contestants table with missing relationship cells
    df = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 29,
                "contestant_id": f"US-S29-{i:02d}",
                "name": f"Contestant {i}",
                "age": 30,
                "relationship": None if i <= 22 else "Married",
                "hometown": "City, State",
                "status": "Eliminated",
            }
            for i in range(1, 23)
        ]
    )
    df.to_parquet(tmp_path / "contestants.parquet", index=False)

    auditor = DatasetGapAuditor(processed_dir=tmp_path)
    missing_s29 = auditor.get_missing_records("contestants", "relationship", season=29)
    assert len(missing_s29) == 22

    col_gap = next(
        g for g in auditor.audit_table("contestants") if g.column_name == "relationship"
    )
    assert col_gap.missing_count == 22
    assert 29 in col_gap.affected_seasons
    assert col_gap.affected_seasons[29] == 22
    assert "Season 29" in col_gap.diagnosis_hint


def test_gap_auditor_cli(cli_runner):
    """Verify tar-dataset gaps CLI command output and filtering."""
    # Filter by season 29
    res_s29 = cli_runner.invoke(app, ["gaps", "--season", "29"])
    assert res_s29.exit_code == 0
    assert "Gap Analysis Overview" in res_s29.output

    # Filter by table contestants with details
    res_tbl = cli_runner.invoke(app, ["gaps", "--table", "contestants", "--detail"])
    assert res_tbl.exit_code == 0
    assert "Gap Analysis Overview" in res_tbl.output


def test_gap_auditor_markdown_export(tmp_path):
    """Verify exporting gap analysis as markdown documentation."""
    auditor = DatasetGapAuditor()
    out_file = tmp_path / "gaps_report.md"
    exported = auditor.export_markdown_report(out_file)

    assert exported.exists()
    content = exported.read_text(encoding="utf-8")
    assert "# The Amazing Race Dataset: Data Gap & Completeness Report" in content
    assert "Overall Completeness" in content
    assert "100.0%" in content
    assert "Season 29 Contestants & Teams" in content
