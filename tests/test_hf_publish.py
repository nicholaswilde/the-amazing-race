"""Tests for Hugging Face Hub dataset publishing and card generation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.hf_publish import (
    HuggingFacePublisher,
    generate_dataset_card,
    generate_space_card,
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


def test_prepare_staging_directory_corrupt_jsonl(tmp_path: Path) -> None:
    ai_dir = tmp_path / "data" / "ai"
    ai_dir.mkdir(parents=True)
    # Write invalid JSON into qa_finetuning.jsonl
    (ai_dir / "tar_qa_finetuning.jsonl").write_text(
        "NOT VALID JSON {{{", encoding="utf-8"
    )

    publisher = HuggingFacePublisher(
        repo_root=tmp_path,
        processed_dir="data/processed",
        ai_dir="data/ai",
        docs_dir="docs",
    )
    stage_dir = tmp_path / "staged"
    # Should not raise exception even when jsonl conversion to parquet fails
    publisher.prepare_staging_directory(stage_dir)
    assert (stage_dir / "data" / "tar_qa_finetuning.jsonl").exists()


@patch("huggingface_hub.HfApi")
def test_publish_repo_id_and_token_fallbacks(
    mock_api_cls: MagicMock, tmp_path: Path
) -> None:
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    mock_api.whoami.return_value = {"name": "autouser"}
    mock_api.create_tag.side_effect = Exception("Tagging failed")

    custom_stage = tmp_path / "my_custom_stage"
    custom_stage.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n', encoding="utf-8"
    )

    publisher = HuggingFacePublisher(
        repo_root=tmp_path,
        processed_dir="data/processed",
        ai_dir="data/ai",
        docs_dir="docs",
    )

    with (
        patch("huggingface_hub.get_token", return_value="stored_token"),
        patch.dict("os.environ", {}, clear=True),
    ):
        # 1. No repo_id -> resolves to autouser/the-amazing-race
        res = publisher.publish(
            repo_id=None,
            token=None,
            staging_dir=custom_stage,
        )
        assert res["repo_id"] == "autouser/the-amazing-race"

        # 2. repo_id without slash -> resolves to autouser/custom-name
        res2 = publisher.publish(
            repo_id="custom-name",
            token="direct_token",
        )
        assert res2["repo_id"] == "autouser/custom-name"


def test_generate_space_card() -> None:
    """Test generating Space card markdown with frontmatter."""
    card = generate_space_card("0.4.1", "The Amazing Race Analytics Dashboard")
    assert "sdk: streamlit" in card
    assert "emoji: 🌍" in card
    assert "app_file: app.py" in card
    assert "v0.4.1" in card


def test_prepare_space_staging_directory(tmp_path: Path) -> None:
    """Test preparing Hugging Face Space staging folder."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    wiki_dir = tmp_path / "data" / "raw" / "wikipedia"
    wiki_dir.mkdir(parents=True)
    src_dir = tmp_path / "src" / "tar_dataset"
    src_dir.mkdir(parents=True)

    (processed_dir / "seasons.parquet").write_text("dummy", encoding="utf-8")
    (wiki_dir / "season_us_39.json").write_text('{"season": 39}', encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("Apache-2.0", encoding="utf-8")

    publisher = HuggingFacePublisher(
        repo_root=tmp_path,
        processed_dir="data/processed",
    )

    stage_dir = tmp_path / "space_staging"
    staged = publisher.prepare_space_staging_directory(stage_dir)

    assert (staged / "README.md").exists()
    assert (staged / "requirements.txt").exists()
    assert (staged / ".streamlit" / "config.toml").exists()
    assert (staged / "app.py").exists()
    assert (staged / "src" / "tar_dataset" / "__init__.py").exists()
    assert (staged / "data" / "processed" / "seasons.parquet").exists()
    assert (staged / "data" / "raw" / "wikipedia" / "season_us_39.json").exists()


@patch("huggingface_hub.HfApi")
def test_publish_space(mock_api_cls: MagicMock, tmp_path: Path) -> None:
    """Test publish_space method logic."""
    mock_api = mock_api_cls.return_value
    mock_api.whoami.return_value = {"name": "testuser"}

    publisher = HuggingFacePublisher(repo_root=tmp_path)

    # 1. Custom staging directory
    custom_stage = tmp_path / "space_stage"
    res = publisher.publish_space(
        repo_id="testuser/the-amazing-race-dashboard",
        token="hf_test_token",
        staging_dir=custom_stage,
    )
    assert res["repo_id"] == "testuser/the-amazing-race-dashboard"
    assert "https://huggingface.co/spaces/" in res["url"]
    mock_api.create_repo.assert_called_with(
        repo_id="testuser/the-amazing-race-dashboard",
        repo_type="space",
        space_sdk="streamlit",
        exist_ok=True,
        private=False,
    )
    mock_api.upload_folder.assert_called()


def test_cli_publish_space_help() -> None:
    """Test tar-dataset publish-space --help."""
    res = runner.invoke(app, ["publish-space", "--help"])
    assert res.exit_code == 0
    assert "Publish interactive Streamlit dashboard" in res.stdout


def test_cli_publish_space_stage_only(tmp_path: Path) -> None:
    """Test tar-dataset publish-space --stage-only."""
    stage_dir = tmp_path / "cli_space_stage"
    res = runner.invoke(app, ["publish-space", "--stage-only", str(stage_dir)])
    assert res.exit_code == 0
    assert "staged locally" in res.stdout
    assert (stage_dir / "app.py").exists()


@patch("tar_dataset.exports.hf_publish.HuggingFacePublisher.publish_space")
def test_cli_publish_space_success(mock_pub: MagicMock) -> None:
    """Test successful CLI publish-space invocation."""
    mock_pub.return_value = {
        "repo_id": "testuser/the-amazing-race-dashboard",
        "url": "https://huggingface.co/spaces/testuser/the-amazing-race-dashboard",
    }
    res = runner.invoke(
        app, ["publish-space", "--repo-id", "testuser/the-amazing-race-dashboard"]
    )
    assert res.exit_code == 0
    assert "Successfully deployed dashboard" in res.stdout


@patch("tar_dataset.exports.hf_publish.HuggingFacePublisher.publish_space")
def test_cli_publish_space_failure(mock_pub: MagicMock) -> None:
    """Test failed CLI publish-space invocation."""
    mock_pub.side_effect = RuntimeError("Auth failed")
    res = runner.invoke(app, ["publish-space"])
    assert res.exit_code == 1
    assert "Error publishing to Hugging Face Spaces" in res.stdout
