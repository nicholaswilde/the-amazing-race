"""Packaging module for creating segmented release assets and distribution bundles."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TABLE_NAMES = [
    "seasons",
    "episodes",
    "contestants",
    "teams",
    "legs",
    "leg_results",
    "tasks",
]


def get_project_version(root_dir: Path | str = ".") -> str:
    """Extract project version from pyproject.toml or r/DESCRIPTION."""
    root = Path(root_dir)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)

    r_desc = root / "r" / "DESCRIPTION"
    if r_desc.exists():
        content = r_desc.read_text(encoding="utf-8")
        match = re.search(r"Version:\s*([^\n\r]+)", content)
        if match:
            return match.group(1).strip()

    return "0.1.0"


class ReleasePackager:
    """Builds segmented release bundles for CSV, Parquet, AI JSONL, R, and Python."""

    def __init__(
        self,
        output_dir: Path | str = "dist/release",
        version: str | None = None,
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
        r_dir: Path | str = "r",
        docs_dir: Path | str = "docs",
        repo_root: Path | str = ".",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.repo_root = Path(repo_root)
        self.processed_dir = Path(processed_dir)
        self.ai_dir = Path(ai_dir)
        self.r_dir = Path(r_dir)
        self.docs_dir = Path(docs_dir)

        # Resolve version: explicit arg -> GITHUB_REF_NAME -> pyproject.toml
        raw_version = (
            version
            or os.environ.get("RELEASE_VERSION")
            or os.environ.get("GITHUB_REF_NAME")
            or get_project_version(self.repo_root)
        )
        self.clean_version = raw_version.lstrip("v")
        self.tag_version = f"v{self.clean_version}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def package_csv(self) -> Path:
        """Package all tidy CSV tables and documentation into a zip bundle."""
        archive_name = f"tar-dataset-csv-{self.tag_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building CSV bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add all CSV tables
            for table in TABLE_NAMES:
                csv_file = self.processed_dir / f"{table}.csv"
                if csv_file.exists():
                    zf.write(csv_file, arcname=f"csv/{csv_file.name}")

            # Add documentation and license
            data_dict = self.docs_dir / "data_dictionary.md"
            if data_dict.exists():
                zf.write(data_dict, arcname="data_dictionary.md")

            license_file = self.repo_root / "LICENSE"
            if license_file.exists():
                zf.write(license_file, arcname="LICENSE")

            readme_file = self.repo_root / "README.md"
            if readme_file.exists():
                zf.write(readme_file, arcname="README.md")

        return target_path

    def package_parquet(self) -> Path:
        """Package all Parquet tables and documentation into a zip bundle."""
        archive_name = f"tar-dataset-parquet-{self.tag_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building Parquet bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for table in TABLE_NAMES:
                parquet_file = self.processed_dir / f"{table}.parquet"
                if parquet_file.exists():
                    zf.write(parquet_file, arcname=f"parquet/{parquet_file.name}")

            data_dict = self.docs_dir / "data_dictionary.md"
            if data_dict.exists():
                zf.write(data_dict, arcname="data_dictionary.md")

            license_file = self.repo_root / "LICENSE"
            if license_file.exists():
                zf.write(license_file, arcname="LICENSE")

        return target_path

    def package_ai(self) -> Path:
        """Package AI fine-tuning datasets and knowledge corpora into a zip bundle."""
        archive_name = f"tar-dataset-ai-{self.tag_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building AI bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            ai_files = [
                "tar_qa_finetuning.jsonl",
                "tar_knowledge_corpus.jsonl",
                "tar_benchmark_suite.jsonl",
            ]
            for file_name in ai_files:
                f_path = self.ai_dir / file_name
                if f_path.exists():
                    zf.write(f_path, arcname=f"ai/{file_name}")

            license_file = self.repo_root / "LICENSE"
            if license_file.exists():
                zf.write(license_file, arcname="LICENSE")

        return target_path

    def package_sqlite(self) -> Path | None:
        """Package SQLite database into a zip bundle if it exists."""
        db_path = self.processed_dir / "tar.db"
        if not db_path.exists():
            return None

        archive_name = f"tar-dataset-sqlite-{self.tag_version}.zip"
        target_path = self.output_dir / archive_name
        logger.info("Building SQLite bundle: %s", target_path)

        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, arcname="tar.db")
            license_file = self.repo_root / "LICENSE"
            if license_file.exists():
                zf.write(license_file, arcname="LICENSE")

        return target_path

    def package_r(self) -> Path:
        """Build CRAN-compliant R source package tarball."""
        archive_name = f"theamazingrace_{self.clean_version}.tar.gz"
        target_path = self.output_dir / archive_name
        logger.info("Building R source package: %s", target_path)

        # Check if R CMD build is available
        r_bin = shutil.which("R")
        if r_bin:
            try:
                cmd = [
                    r_bin,
                    "CMD",
                    "build",
                    str(self.r_dir),
                    "--no-build-vignettes",
                    "--no-manual",
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    cwd=str(self.output_dir),
                    capture_output=True,
                    text=True,
                )
                built_tarball = self.output_dir / archive_name
                if built_tarball.exists():
                    return built_tarball
            except Exception as e:
                logger.warning(
                    "R CMD build failed (%s); falling back to pure Python packaging", e
                )

        # Pure Python fallback: create the package tarball
        pkg_name = "theamazingrace"
        excluded_patterns = {
            ".git",
            ".Rhistory",
            ".RData",
            ".DS_Store",
            "__pycache__",
        }

        with tarfile.open(target_path, "w:gz") as tf:
            for root, dirs, files in os.walk(self.r_dir):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if d not in excluded_patterns]
                rel_root = Path(root).relative_to(self.r_dir)

                for file in files:
                    if file in excluded_patterns or file.endswith("~"):
                        continue
                    file_path = Path(root) / file
                    arcname = Path(pkg_name) / rel_root / file
                    tf.add(file_path, arcname=str(arcname))

        return target_path

    def package_python(self) -> list[Path]:
        """Build Python wheel and source distribution using uv build."""
        logger.info("Building Python distribution with uv build")
        built_files: list[Path] = []
        try:
            cmd = ["uv", "build", "--out-dir", str(self.output_dir)]
            subprocess.run(
                cmd,
                check=True,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
            )
            for f in self.output_dir.iterdir():
                if f.name.endswith((".whl", ".tar.gz")) and f.name.startswith(
                    "the_amazing_race"
                ):
                    built_files.append(f)
        except Exception as e:
            logger.warning("uv build failed: %s", e)

        return built_files

    def generate_checksums(self) -> Path:
        """Generate SHA-256 checksums file for all release assets in output_dir."""
        checksum_file = self.output_dir / "checksums.txt"
        lines: list[str] = []

        # Find all files except checksums.txt and hidden files
        files = sorted(
            [
                f
                for f in self.output_dir.iterdir()
                if f.is_file()
                and f.name != "checksums.txt"
                and not f.name.startswith(".")
            ]
        )

        for file_path in files:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            lines.append(f"{hasher.hexdigest()}  {file_path.name}")

        checksum_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("Generated checksums: %s", checksum_file)
        return checksum_file

    def package_all(self) -> dict[str, Any]:
        """Package all release assets and generate checksums."""
        results: dict[str, Any] = {}
        results["csv"] = self.package_csv()
        results["parquet"] = self.package_parquet()
        results["ai"] = self.package_ai()
        sqlite_pkg = self.package_sqlite()
        if sqlite_pkg:
            results["sqlite"] = sqlite_pkg
        results["r"] = self.package_r()
        results["python"] = self.package_python()
        results["checksums"] = self.generate_checksums()
        return results


def package_release(
    output_dir: Path | str = "dist/release",
    version: str | None = None,
) -> dict[str, Any]:
    """Convenience function to run full release packaging."""
    packager = ReleasePackager(output_dir=output_dir, version=version)
    return packager.package_all()
