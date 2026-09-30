"""Unit and integration tests for release packaging and segmented dataset bundles."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.packaging import (
    ReleasePackager,
    get_project_version,
    package_release,
)

runner = CliRunner()


def test_get_project_version(tmp_path: Path) -> None:
    # Test fallback
    assert get_project_version(tmp_path) == "0.1.0"

    # Test pyproject.toml detection
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    assert get_project_version(tmp_path) == "1.2.3"

    # Test r/DESCRIPTION detection
    tmp_path_r = tmp_path / "subdir"
    r_dir = tmp_path_r / "r"
    r_dir.mkdir(parents=True)
    (r_dir / "DESCRIPTION").write_text(
        "Package: test\nVersion: 2.3.4\n", encoding="utf-8"
    )
    assert get_project_version(tmp_path_r) == "2.3.4"


def test_release_packager_all(tmp_path: Path) -> None:
    out_dir = tmp_path / "dist" / "release"
    packager = ReleasePackager(output_dir=out_dir, version="0.2.0")

    assert packager.clean_version == "0.2.0"
    assert packager.tag_version == "v0.2.0"

    results = packager.package_all()

    # Check CSV bundle
    assert "csv" in results
    csv_zip = results["csv"]
    assert csv_zip.exists()
    with zipfile.ZipFile(csv_zip, "r") as zf:
        names = zf.namelist()
        assert "csv/seasons.csv" in names
        assert "data_dictionary.md" in names
        assert "LICENSE" in names
        assert "README.md" in names

    # Check Parquet bundle
    assert "parquet" in results
    parquet_zip = results["parquet"]
    assert parquet_zip.exists()
    with zipfile.ZipFile(parquet_zip, "r") as zf:
        names = zf.namelist()
        assert "parquet/seasons.parquet" in names
        assert "data_dictionary.md" in names
        assert "LICENSE" in names
        assert "README.md" in names

    # Check AI bundle
    assert "ai" in results
    ai_zip = results["ai"]
    assert ai_zip.exists()
    with zipfile.ZipFile(ai_zip, "r") as zf:
        names = zf.namelist()
        assert "ai/tar_qa_finetuning.jsonl" in names
        assert "README.md" in names
        assert "data_dictionary.md" in names
        assert "LICENSE" in names

    # Check SQLite bundle
    if (Path("data/processed") / "tar.db").exists():
        assert "sqlite" in results
        assert results["sqlite"].exists()
        with zipfile.ZipFile(results["sqlite"], "r") as zf:
            names = zf.namelist()
            assert "tar.db" in names
            assert "data_dictionary.md" in names
            assert "LICENSE" in names
            assert "README.md" in names

    # Check R bundle
    assert "r" in results
    r_pkg = results["r"]
    assert r_pkg.exists()
    assert r_pkg.name == "theamazingrace_0.2.0.tar.gz"
    import tarfile

    with tarfile.open(r_pkg, "r:gz") as tf:
        r_names = tf.getnames()
        assert any(n.endswith("LICENSE") for n in r_names)
        assert any(n.endswith("README.md") for n in r_names)

    # Check Manifest
    assert "manifest" in results
    manifest_file = results["manifest"]
    assert manifest_file.exists()
    import json

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["version"] == "0.2.0"
    assert manifest_data["tag"] == "v0.2.0"
    assert len(manifest_data["assets"]) > 0

    # Check Checksums
    assert "checksums" in results
    chk_file = results["checksums"]
    assert chk_file.exists()
    chk_content = chk_file.read_text(encoding="utf-8")
    assert "tar-dataset-csv-0.2.0.zip" in chk_content
    assert "theamazingrace_0.2.0.tar.gz" in chk_content
    assert "manifest.json" in chk_content

    # Verify checksum matches
    hasher = hashlib.sha256()
    with open(csv_zip, "rb") as f:
        hasher.update(f.read())
    assert f"{hasher.hexdigest()}  {csv_zip.name}" in chk_content


def test_package_release_function(tmp_path: Path) -> None:
    out_dir = tmp_path / "pkg_func"
    res = package_release(output_dir=out_dir, version="v1.0.0")
    assert "csv" in res
    assert "checksums" in res
    assert (out_dir / "tar-dataset-csv-1.0.0.zip").exists()
    assert (out_dir / "checksums.txt").exists()


def test_cli_package_command(tmp_path: Path) -> None:
    out_dir = tmp_path / "cli_pkg"

    # Test single component
    result = runner.invoke(
        app,
        [
            "package",
            "--output-dir",
            str(out_dir),
            "--version",
            "0.5.0",
            "--component",
            "csv",
        ],
    )
    assert result.exit_code == 0
    assert (out_dir / "tar-dataset-csv-0.5.0.zip").exists()
    assert (out_dir / "checksums.txt").exists()

    # Test invalid component
    bad_result = runner.invoke(
        app,
        ["package", "--output-dir", str(out_dir), "--component", "invalid_comp"],
    )
    assert bad_result.exit_code != 0
