"""Tests for dataset exploration utilities, SQLite export, Arrow export, CLI show, and AI benchmark suite."""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd
import pytest
from pyarrow import feather
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.arrow_export import ArrowExporter
from tar_dataset.exports.benchmark import BENCHMARK_ITEMS, BenchmarkSuite
from tar_dataset.exports.sqlite_export import SQLiteExporter


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_sqlite_exporter_basic(tmp_path):
    """Test exporting processed tables to a unified SQLite database."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    # Create sample seasons and teams tables
    df_seasons = pd.DataFrame(
        [
            {"version": "US", "season": 1, "n_teams": 11, "winners": "Rob & Brennan"},
            {"version": "US", "season": 2, "n_teams": 11, "winners": "Chris & Alex"},
        ]
    )
    df_teams = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "team_id": "US-S01-rob-brennan",
                "team_name": "Rob & Brennan",
                "result": 1,
            },
        ]
    )
    df_results = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 1,
                "team_name": "Rob & Brennan",
                "placement": 1.0,
                "fast_forward": True,
            },
            {
                "version": "US",
                "season": 1,
                "leg_number": 2,
                "team_name": "Rob & Brennan",
                "placement": 3.0,
                "fast_forward": False,
            },
        ]
    )

    df_seasons.to_parquet(proc_dir / "seasons.parquet", index=False)
    df_teams.to_parquet(proc_dir / "teams.parquet", index=False)
    df_results.to_parquet(proc_dir / "leg_results.parquet", index=False)

    db_path = proc_dir / "tar.db"
    exporter = SQLiteExporter(processed_dir=proc_dir, db_path=db_path)
    out = exporter.export()

    assert out.exists()
    assert out == db_path

    # Verify querying
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT season, winners FROM seasons ORDER BY season")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0] == (1, "Rob & Brennan")

    # Verify aggregation query
    cursor.execute("""
        SELECT team_name, AVG(placement) FROM leg_results GROUP BY team_name
    """)
    res = cursor.fetchone()
    assert res[0] == "Rob & Brennan"
    assert res[1] == 2.0
    conn.close()

    # Verify header version normalization
    with open(db_path, "rb") as f:
        f.seek(96)
        assert f.read(4) == b"\x00\x2e\x8a\x14"


def test_arrow_and_hf_exporter(tmp_path):
    """Test exporting to Arrow IPC and HuggingFace disk layouts."""
    proc_dir = tmp_path / "processed"
    ai_dir = tmp_path / "ai"
    proc_dir.mkdir(parents=True, exist_ok=True)
    ai_dir.mkdir(parents=True, exist_ok=True)

    df_teams = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "team_id": "US-S01-rob-brennan",
                "team_name": "Rob & Brennan",
                "result": 1,
            },
        ]
    )
    df_teams.to_parquet(proc_dir / "teams.parquet", index=False)

    # Sample QA JSONL
    qa_file = ai_dir / "tar_qa_finetuning.jsonl"
    qa_file.write_text(
        '{"messages": [{"role": "system", "content": "You are TAR expert."}, {"role": "user", "content": "Who won?"}, {"role": "assistant", "content": "Rob and Brennan."}], "metadata": {"season": 1, "type": "winners"}}\n',
        encoding="utf-8",
    )

    exporter = ArrowExporter(processed_dir=proc_dir, ai_dir=ai_dir)
    results = exporter.export_all()

    arrow_tables = results["arrow_tables"]
    assert "teams" in arrow_tables
    assert arrow_tables["teams"].exists()

    # Verify reading with pyarrow.feather
    read_table = feather.read_table(arrow_tables["teams"])
    assert read_table.num_rows == 1
    assert "team_name" in read_table.column_names

    hf_datasets = results["hf_datasets"]
    assert "qa_finetuning" in hf_datasets
    qa_dir = hf_datasets["qa_finetuning"]
    assert (qa_dir / "dataset_info.json").exists()
    assert (qa_dir / "state.json").exists()
    assert (qa_dir / "data-00000-of-00001.arrow").exists()


def test_benchmark_suite(tmp_path):
    """Test AI evaluation benchmark suite loading, scoring, and rubrics."""
    bench_file = tmp_path / "tar_benchmark.jsonl"
    suite = BenchmarkSuite(benchmark_file=bench_file)

    saved_path = suite.save_default_suite()
    assert saved_path.exists()
    assert len(BENCHMARK_ITEMS) >= 40

    loaded = suite.load_suite()
    assert len(loaded) == len(BENCHMARK_ITEMS)

    # Categories check
    categories = {item["category"] for item in loaded}
    assert "trivia" in categories
    assert "rules_comprehension" in categories
    assert "route_accuracy" in categories

    # Test scoring function
    test_item = {
        "id": "test-001",
        "question": "Who won Season 1?",
        "key_facts": ["Rob", "Brennan"],
    }
    score_pass = suite.score_response(test_item, "Rob and Brennan won Season 1.")
    assert score_pass["passed"] is True
    assert score_pass["score"] == 1.0

    score_partial = suite.score_response(test_item, "Rob won Season 1 alone.")
    assert score_partial["score"] == 0.5
    assert score_partial["passed"] is True

    score_fail = suite.score_response(test_item, "Unknown racers won.")
    assert score_fail["passed"] is False
    assert score_fail["score"] == 0.0

    # Test complete evaluation summary
    summary = suite.evaluate_benchmark()
    assert summary["total_questions"] == len(BENCHMARK_ITEMS)
    assert summary["pass_rate"] >= 0.95


def test_cli_show_season(cli_runner):
    """Test CLI tar-dataset show season."""
    result = cli_runner.invoke(app, ["show", "season", "1"])
    assert result.exit_code == 0
    assert "Rob Frisbee and Brennan Swain" in result.output
    assert "Route Itinerary" in result.output
    assert "Teams Leaderboard" in result.output


def test_cli_show_team(cli_runner):
    """Test CLI tar-dataset show team."""
    result = cli_runner.invoke(app, ["show", "team", "Rob & Brennan"])
    assert result.exit_code == 0
    assert "Rob & Brennan" in result.output
    assert "Racing Average" in result.output
    assert "Fast Forward" in result.output


def test_cli_show_racer(cli_runner):
    """Test CLI tar-dataset show racer."""
    result = cli_runner.invoke(app, ["show", "racer", "Rob Frisbee"])
    assert result.exit_code == 0
    assert "Rob Frisbee" in result.output
    assert "Minneapolis, Minnesota" in result.output


def test_cli_show_leg(cli_runner):
    """Test CLI tar-dataset show leg."""
    result = cli_runner.invoke(app, ["show", "leg", "1", "--season", "1"])
    assert result.exit_code == 0
    assert "Season 1 Leg 1" in result.output
    assert "Fast Forward" in result.output


def test_cli_show_invalid_season(cli_runner):
    """Test CLI error handling on invalid season."""
    result = cli_runner.invoke(app, ["show", "season", "999"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_cli_export_commands(cli_runner, tmp_path):
    """Test CLI export commands."""
    db_test = tmp_path / "test.db"
    res_sql = cli_runner.invoke(app, ["export-sqlite", "--db-path", str(db_test)])
    assert res_sql.exit_code == 0
    assert db_test.exists()

    res_arrow = cli_runner.invoke(app, ["export-arrow"])
    assert res_arrow.exit_code == 0
    assert "Apache Arrow IPC" in res_arrow.output

    res_bench = cli_runner.invoke(app, ["eval-benchmark"])
    assert res_bench.exit_code == 0
    assert "Benchmark Results" in res_bench.output


def test_schema_drift_data_dictionary():
    """Verify that every column in all 7 processed tables matches docs/data_dictionary.md."""
    import re
    from pathlib import Path

    doc_file = Path("docs/data_dictionary.md")
    assert doc_file.exists(), "docs/data_dictionary.md does not exist"

    content = doc_file.read_text(encoding="utf-8")
    sections = re.split(r"### \d+\.\s+", content)[1:]

    documented_tables: dict[str, list[str]] = {}
    for sec in sections:
        first_line = sec.split("\n", 1)[0].strip()
        tbl_name = first_line.strip("`").strip()
        cols = re.findall(r"\|\s*`([a-z_]+)`\s*\|", sec)
        if tbl_name and cols:
            documented_tables[tbl_name] = cols

    assert len(documented_tables) == 7, (
        f"Expected 7 documented tables, found {len(documented_tables)}"
    )

    processed_dir = Path("data/processed")
    for tbl, doc_cols in documented_tables.items():
        parquet_path = processed_dir / f"{tbl}.parquet"
        assert parquet_path.exists(), f"Missing Parquet table: {parquet_path}"

        df = pd.read_parquet(parquet_path)
        actual_cols = list(df.columns)

        missing_in_doc = set(actual_cols) - set(doc_cols)
        extra_in_doc = set(doc_cols) - set(actual_cols)

        assert not missing_in_doc, (
            f"Table '{tbl}' has columns missing from docs/data_dictionary.md: {missing_in_doc}"
        )
        assert not extra_in_doc, (
            f"Table '{tbl}' has columns in docs/data_dictionary.md not present in data: {extra_in_doc}"
        )


def test_tar_exploration_notebook_execution():
    """Execute all code cells of notebooks/tar_exploration.ipynb headlessly to ensure no breakages."""
    import json
    from pathlib import Path

    nb_path = Path("notebooks/tar_exploration.ipynb")
    assert nb_path.exists(), "notebooks/tar_exploration.ipynb does not exist"

    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)

    # Execute cells sequentially in a shared global namespace
    globals_dict: dict[str, Any] = {"__name__": "__main__"}

    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            if source.strip():
                try:
                    exec(  # noqa: S102
                        compile(source, f"<notebook_cell_{idx}>", "exec"), globals_dict
                    )
                except Exception as exc:
                    pytest.fail(
                        f"Notebook execution failed on code cell {idx}:\n{source}\nError: {exc}"
                    )
