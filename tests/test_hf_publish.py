"""Tests for Hugging Face Hub dataset publishing and card generation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.hf_publish import (
    HuggingFacePublisher,
    generate_dataset_card,
    get_project_version,
)

runner = CliRunner()


def test_get_project_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    assert get_project_version(tmp_path) == "1.2.3"

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert get_project_version(empty_dir) == "0.1.0"


def test_generate_dataset_card() -> None:
    card = generate_dataset_card("0.2.0")
    assert "---" in card
    assert "license: apache-2.0" in card
    assert "task_categories:" in card
    assert "config_name: seasons" in card
    assert "config_name: qa_finetuning" in card
    assert "v0.2.0" in card


def test_prepare_staging_directory(tmp_path: Path) -> None:
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    ai_dir = tmp_path / "data" / "ai"
    ai_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)

    # Create dummy processed files
    (processed_dir / "seasons.parquet").write_text("dummy seasons", encoding="utf-8")
    (processed_dir / "teams.parquet").write_text("dummy teams", encoding="utf-8")
    (ai_dir / "tar_qa_finetuning.jsonl").write_text(
        '{"messages": []}', encoding="utf-8"
    )
    (docs_dir / "data_dictionary.md").write_text("# Dictionary", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("Apache License", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("cff-version: 1.2.0", encoding="utf-8")

    publisher = HuggingFacePublisher(
        repo_root=tmp_path,
        processed_dir="data/processed",
        ai_dir="data/ai",
        docs_dir="docs",
    )

    stage_dir = tmp_path / "staged"
    publisher.prepare_staging_directory(stage_dir)

    assert (stage_dir / "README.md").exists()
    assert (stage_dir / "data" / "seasons.parquet").exists()
    assert (stage_dir / "data" / "tar_qa_finetuning.jsonl").exists()
    assert (stage_dir / "LICENSE").exists()
    assert (stage_dir / "CITATION.cff").exists()
    assert (stage_dir / "data_dictionary.md").exists()


@patch("huggingface_hub.HfApi")
def test_publish_mocked(mock_api_cls: MagicMock, tmp_path: Path) -> None:
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    mock_api.whoami.return_value = {"name": "testuser"}

    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    ai_dir = tmp_path / "data" / "ai"
    ai_dir.mkdir(parents=True)

    publisher = HuggingFacePublisher(
        repo_root=tmp_path,
        processed_dir="data/processed",
        ai_dir="data/ai",
        docs_dir="docs",
    )

    res = publisher.publish(
        repo_id="custom-org/the-amazing-race",
        token="hf_mock_token",
        private=True,
        commit_message="Test commit",
    )

    assert res["repo_id"] == "custom-org/the-amazing-race"
    assert res["url"] == "https://huggingface.co/datasets/custom-org/the-amazing-race"
    assert res["private"] is True

    mock_api.create_repo.assert_called_once_with(
        repo_id="custom-org/the-amazing-race",
        repo_type="dataset",
        exist_ok=True,
        private=True,
    )
    mock_api.upload_folder.assert_called_once()


def test_cli_publish_hf_stage_only(tmp_path: Path) -> None:
    stage_dir = tmp_path / "cli_staged"
    result = runner.invoke(app, ["publish-hf", "--stage-only", str(stage_dir)])
    assert result.exit_code == 0
    assert "Dataset staged locally" in result.stdout
    assert (stage_dir / "README.md").exists()


@patch("tar_dataset.cli.HuggingFacePublisher")
def test_cli_publish_hf(mock_pub_cls: MagicMock) -> None:
    mock_publisher = MagicMock()
    mock_pub_cls.return_value = mock_publisher
    mock_publisher.publish.return_value = {
        "repo_id": "nicholascwilde/the-amazing-race",
        "url": "https://huggingface.co/datasets/nicholascwilde/the-amazing-race",
        "version": "0.1.0",
        "private": False,
    }

    result = runner.invoke(
        app,
        [
            "publish-hf",
            "--token",
            "hf_test_123",
            "--repo-id",
            "nicholascwilde/the-amazing-race",
        ],
    )
    assert result.exit_code == 0
    assert "Successfully published" in result.stdout
    mock_publisher.publish.assert_called_once_with(
        repo_id="nicholascwilde/the-amazing-race",
        token="hf_test_123",
        private=False,
        commit_message=None,
    )
