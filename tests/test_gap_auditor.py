"""Unit tests for dataset gap auditor and completeness tooling."""

from __future__ import annotations

from unittest.mock import patch

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
                "gender": "M" if i % 2 == 0 else "F",
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


def test_column_gap_severity_and_to_dict():
    from tar_dataset.processors.gap_auditor import ColumnGap

    g_ok = ColumnGap("tbl", "col", 100, 0, {}, [], "hint")
    assert g_ok.severity == "OK"
    d_ok = g_ok.to_dict()
    assert d_ok["severity"] == "OK"
    assert d_ok["missing_pct"] == 0.0

    g_low = ColumnGap("tbl", "col", 100, 3, {1: 3}, ["key1"], "hint")
    assert g_low.severity == "LOW"

    g_med = ColumnGap("tbl", "col", 100, 15, {1: 15}, ["key1"], "hint")
    assert g_med.severity == "MEDIUM"

    g_high = ColumnGap("tbl", "col", 100, 35, {1: 35}, ["key1"], "hint")
    assert g_high.severity == "HIGH"


def test_gap_auditor_load_table_fallback(tmp_path):
    auditor = DatasetGapAuditor(processed_dir=tmp_path)
    # Non-existent
    assert auditor.load_table("missing").empty

    # CSV fallback
    csv_file = tmp_path / "seasons.csv"
    csv_file.write_text("season,year\n1,2001\n", encoding="utf-8")
    loaded = auditor.load_table("seasons")
    assert len(loaded) == 1
    assert loaded.iloc[0]["season"] == 1


def test_gap_auditor_render_report_and_markdown_with_gaps(tmp_path):
    from tar_dataset.processors.gap_auditor import ColumnGap

    auditor = DatasetGapAuditor(processed_dir=tmp_path)
    # Create fake audit with gaps
    fake_gaps = [
        ColumnGap("contestants", "relationship", 100, 25, {29: 25}, ["C1"], "Test hint")
    ]
    with patch.object(
        auditor,
        "audit_all",
        return_value={
            "overall_completeness_pct": 75.0,
            "total_cells": 100,
            "total_missing": 25,
            "gaps": fake_gaps,
        },
    ):
        # Test render_report with detail and season filter
        auditor.render_report(show_detail=True, season_filter=29)

        # Test export markdown report with gaps
        out_file = tmp_path / "report_with_gaps.md"
        auditor.export_markdown_report(out_file)
        assert out_file.exists()
        txt = out_file.read_text(encoding="utf-8")
        assert "contestants" in txt
        assert "Test hint" in txt
