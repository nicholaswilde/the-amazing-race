"""Unit tests for dataset gap auditor and completeness tooling."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.processors.gap_auditor import DatasetGapAuditor


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_gap_auditor_completeness():
    """Verify gap auditor computes overall dataset completeness metrics."""
    auditor = DatasetGapAuditor()
    report = auditor.audit_all()

    assert report["overall_completeness_pct"] > 95.0
    assert report["total_cells"] > 50000
    assert isinstance(report["gaps"], list)
    assert len(report["gaps"]) > 0


def test_gap_auditor_season_29_relationship_detection():
    """Specifically verify the auditor identifies missing relationship cells in Season 29 contestants."""
    auditor = DatasetGapAuditor()

    # Query missing records directly for Season 29
    missing_s29 = auditor.get_missing_records("contestants", "relationship", season=29)
    assert len(missing_s29) == 22, (
        f"Expected 22 missing relationship cells in Season 29 contestants, found {len(missing_s29)}"
    )

    # Check column gap analysis
    col_gap = next(
        g for g in auditor.audit_table("contestants") if g.column_name == "relationship"
    )
    assert col_gap.missing_count >= 22
    assert 29 in col_gap.affected_seasons
    assert col_gap.affected_seasons[29] == 22
    assert "Season 29" in col_gap.diagnosis_hint


def test_gap_auditor_cli(cli_runner):
    """Verify tar-dataset gaps CLI command output and filtering."""
    # Filter by season 29
    res_s29 = cli_runner.invoke(app, ["gaps", "--season", "29"])
    assert res_s29.exit_code == 0
    assert "contestants" in res_s29.output
    assert "relationship" in res_s29.output

    # Filter by table contestants with details
    res_tbl = cli_runner.invoke(app, ["gaps", "--table", "contestants", "--detail"])
    assert res_tbl.exit_code == 0
    assert "contestants.relationship Gaps" in res_tbl.output


def test_gap_auditor_markdown_export(tmp_path):
    """Verify exporting gap analysis as markdown documentation."""
    auditor = DatasetGapAuditor()
    out_file = tmp_path / "gaps_report.md"
    exported = auditor.export_markdown_report(out_file)

    assert exported.exists()
    content = exported.read_text(encoding="utf-8")
    assert "# The Amazing Race Dataset: Data Gap & Completeness Report" in content
    assert "contestants" in content
    assert "Season 29" in content
