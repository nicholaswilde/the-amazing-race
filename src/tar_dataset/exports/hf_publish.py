"""Hugging Face Hub publisher for The Amazing Race tidy datasets and AI training corpora."""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

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

AI_FILES = [
    "tar_qa_finetuning.jsonl",
    "tar_knowledge_corpus.jsonl",
    "tar_benchmark_suite.jsonl",
]


def get_project_version(repo_root: Path) -> str:
    """Extract project version from pyproject.toml."""
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.1.0"


def generate_dataset_card(version: str = "0.1.0") -> str:
    """Generate Hugging Face Dataset Card (README.md) with complete YAML frontmatter."""
    return f"""---
annotations_creators:
  - no-annotation
language_creators:
  - found
  - expert-generated
language:
  - en
license: apache-2.0
multilinguality:
  - monolingual
size_categories:
  - 1K<n<10K
source_datasets:
  - original
task_categories:
  - question-answering
  - text-generation
  - tabular-classification
  - tabular-regression
task_ids: []
pretty_name: The Amazing Race Dataset & AI Training Corpus
tags:
  - reality-tv
  - television
  - tidy-data
  - tidytuesday
  - the-amazing-race
  - tabular
configs:
  - config_name: default
    data_files: "data/seasons.parquet"
  - config_name: seasons
    data_files: "data/seasons.parquet"
  - config_name: episodes
    data_files: "data/episodes.parquet"
  - config_name: teams
    data_files: "data/teams.parquet"
  - config_name: contestants
    data_files: "data/contestants.parquet"
  - config_name: legs
    data_files: "data/legs.parquet"
  - config_name: leg_results
    data_files: "data/leg_results.parquet"
  - config_name: tasks
    data_files: "data/tasks.parquet"
  - config_name: qa_finetuning
    data_files: "data/qa_finetuning.parquet"
  - config_name: knowledge_corpus
    data_files: "data/knowledge_corpus.parquet"
  - config_name: benchmark_suite
    data_files: "data/benchmark_suite.parquet"
---

# 🏁 The Amazing Race Dataset & AI Training Corpus (v{version})

A comprehensive tidy relational dataset and AI training corpus for the CBS reality competition television series **The Amazing Race** (US Seasons 1–36).

Inspired by [doehm/alone](https://github.com/doehm/alone) and reality TV data packages, this repository structures all seasons, episodes, teams, contestants, leg itineraries, challenge tasks, and leg results into normalized relational tables alongside curated instruction-tuning and retrieval-augmented generation (RAG) corpora.

- **GitHub Repository**: [nicholaswilde/the-amazing-race](https://github.com/nicholaswilde/the-amazing-race)
- **Data Dictionary**: [data_dictionary.md](data_dictionary.md)
- **License**: Apache 2.0
- **Release Version**: {version}

---

## 🚀 Quick Start with `datasets`

Install the Hugging Face `datasets` library:
```bash
pip install datasets
```

### Loading Tabular Configurations

Each relational table is available as an independent configuration:

```python
from datasets import load_dataset

# Load seasons summary table
seasons = load_dataset("nicholascwilde/the-amazing-race", "seasons", split="train")

# Load teams profile and racing averages
teams = load_dataset("nicholascwilde/the-amazing-race", "teams", split="train")

# Load leg-by-leg outcomes
leg_results = load_dataset("nicholascwilde/the-amazing-race", "leg_results", split="train")

# Convert to Pandas DataFrame
df_teams = teams.to_pandas()
print(df_teams[["team_name", "season", "placement", "racing_average"]].head())
```

### Loading AI Fine-Tuning & Knowledge Corpora

```python
# Load chat multi-turn conversational pairs for SFT
qa_ds = load_dataset("nicholascwilde/the-amazing-race", "qa_finetuning", split="train")
print(qa_ds[0]["messages"])

# Load narrative knowledge documents for RAG vector embeddings
knowledge_ds = load_dataset("nicholascwilde/the-amazing-race", "knowledge_corpus", split="train")
print(knowledge_ds[0]["text"][:200])

# Load benchmark evaluation questions
bench_ds = load_dataset("nicholascwilde/the-amazing-race", "benchmark_suite", split="train")
print(bench_ds[0]["question"])
```

---

## 📊 Dataset Configurations & Schema

The dataset provides 10 configurations:

| Config Name | File | Description |
| :--- | :--- | :--- |
| `seasons` | `data/seasons.parquet` | Season records: winner, runner-up, premiere/finale dates, legs count, distance, and countries visited. |
| `episodes` | `data/episodes.parquet` | Episode records: episode title, air date, Nielsen rating (18–49), and viewership in millions. |
| `teams` | `data/teams.parquet` | Team records: team name, relationship, finish placement, and calculated racing average. |
| `contestants` | `data/contestants.parquet` | Individual racer demographics: age, occupation, hometown, and gender. |
| `legs` | `data/legs.parquet` | Leg itineraries: starting point, destination city/country, pit stop, and leg type. |
| `leg_results` | `data/leg_results.parquet` | Leg outcomes: team placement, arrival order, departure order, time delta, yield/u-turn usage, and status. |
| `tasks` | `data/tasks.parquet` | Detailed challenges: task type (roadblock, detour, fast forward, speed bump), description, and location. |
| `qa_finetuning` | `data/tar_qa_finetuning.jsonl` | Multi-turn chat instruction pairs formatted for OpenAI/Gemini/Claude SFT. |
| `knowledge_corpus` | `data/tar_knowledge_corpus.jsonl` | Chunked narrative documents with metadata for semantic search and RAG vector databases. |
| `benchmark_suite` | `data/tar_benchmark_suite.jsonl` | Curated evaluation questions with verified ground truths and scoring rubrics. |

---

## 📖 Citation

If you use this dataset in your research or applications, please cite:

```bibtex
@misc{{wilde_amazing_race_2026,
  author       = {{Nicholas Wilde}},
  title        = {{The Amazing Race Dataset & AI Training Corpus}},
  year         = {{2026}},
  version      = {{{version}}},
  publisher    = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/datasets/nicholascwilde/the-amazing-race}}}}
}}
```
"""


def generate_space_card(
    version: str = "0.1.0",
    title: str = "The Amazing Race Analytics Dashboard",
) -> str:
    """Generate Hugging Face Space Card (README.md) with YAML metadata frontmatter."""
    return f"""---
title: {title}
emoji: 🌍
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Interactive tidy analytics & predictive modeling for The Amazing Race
---

# 🌍 {title} (v{version})

An interactive exploratory analytics platform and empirical predictive engine for the reality competition television series **The Amazing Race**.

- **Season Explorer**: Interactive leg routes, destination maps, placement trajectory charts (1st place at top), and roadblock trackers across Seasons 1–38 and currently airing Season 39.
- **Outcome & Risk Predictor**: Empirical multi-factor modeling evaluating win and finale probabilities based on momentum, age dynamics, relationship archetypes, and power items.
- **Challenge Browser**: Search and filter 1,700+ challenges across Roadblocks, Detours, Fast Forwards, and Speed Bumps.
- **Theme**: Catppuccin Mocha dark theme.

Dataset source: [nicholascwilde/the-amazing-race](https://huggingface.co/datasets/nicholascwilde/the-amazing-race)  
GitHub repository: [nicholaswilde/the-amazing-race](https://github.com/nicholaswilde/the-amazing-race)
"""


class HuggingFacePublisher:
    """Manages staging and synchronization of datasets to the Hugging Face Hub."""

    def __init__(
        self,
        repo_root: Path | str = ".",
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
        docs_dir: Path | str = "docs",
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.processed_dir = self.repo_root / processed_dir
        self.ai_dir = self.repo_root / ai_dir
        self.docs_dir = self.repo_root / docs_dir
        self.version = get_project_version(self.repo_root)

    def prepare_staging_directory(self, target_dir: Path | str) -> Path:
        """Stage all parquet tables, AI corpora, dataset card, and metadata into a directory."""
        stage_path = Path(target_dir).resolve()
        stage_path.mkdir(parents=True, exist_ok=True)
        data_dir = stage_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Copy Parquet files
        for table in TABLES:
            parquet_src = self.processed_dir / f"{table}.parquet"
            if parquet_src.exists():
                shutil.copy2(parquet_src, data_dir / f"{table}.parquet")
            else:
                logger.warning("Parquet table not found: %s", parquet_src)

        # Copy AI JSONL files and convert to Parquet for native Hub loading
        ai_mapping = [
            ("tar_qa_finetuning.jsonl", "qa_finetuning.parquet"),
            ("tar_knowledge_corpus.jsonl", "knowledge_corpus.parquet"),
            ("tar_benchmark_suite.jsonl", "benchmark_suite.parquet"),
        ]
        for jsonl_name, parquet_name in ai_mapping:
            ai_src = self.ai_dir / jsonl_name
            if ai_src.exists():
                shutil.copy2(ai_src, data_dir / jsonl_name)
                try:
                    df = pd.read_json(ai_src, lines=True)
                    df.to_parquet(data_dir / parquet_name, engine="pyarrow")
                except Exception as e:
                    logger.warning("Could not convert %s to parquet: %s", jsonl_name, e)
            else:
                logger.warning("AI corpus file not found: %s", ai_src)

        # Write Dataset Card (README.md)
        card_content = generate_dataset_card(version=self.version)
        (stage_path / "README.md").write_text(card_content, encoding="utf-8")

        # Copy supporting documentation and metadata
        support_files = [
            (self.repo_root / "LICENSE", "LICENSE"),
            (self.repo_root / "CITATION.cff", "CITATION.cff"),
            (self.repo_root / "llms.txt", "llms.txt"),
            (self.repo_root / "llms-full.txt", "llms-full.txt"),
            (self.docs_dir / "data_dictionary.md", "data_dictionary.md"),
        ]
        for src_path, dest_name in support_files:
            if src_path.exists():
                shutil.copy2(src_path, stage_path / dest_name)

        return stage_path

    def publish(
        self,
        repo_id: str | None = None,
        token: str | None = None,
        private: bool = False,
        commit_message: str | None = None,
        staging_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        """Publish the staged dataset to Hugging Face Hub."""
        try:
            from huggingface_hub import HfApi
        except ImportError as err:
            raise ImportError(
                "huggingface_hub is required to publish to Hugging Face. "
                "Install it with `uv pip install huggingface_hub` or `pip install 'the-amazing-race[hf]'`."
            ) from err

        # Resolve authentication token
        auth_token = (
            token
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )
        if not auth_token:
            # Fall back to huggingface-cli logged-in token
            try:
                from huggingface_hub import get_token

                auth_token = get_token()
            except Exception as e:
                logger.debug("Could not retrieve stored Hugging Face token: %s", e)

        api = HfApi(token=auth_token)

        # Resolve repository ID
        target_repo = repo_id or os.environ.get("HF_REPO_ID")
        if not target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/the-amazing-race"
            except Exception as e:
                logger.warning("Could not auto-determine Hugging Face username: %s", e)
                target_repo = "nicholascwilde/the-amazing-race"

        elif "/" not in target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/{target_repo}"
            except Exception as e:
                logger.debug("Could not prepend username to repository ID: %s", e)

        logger.info("Target Hugging Face repository: %s", target_repo)

        # Create or verify repository on Hugging Face Hub
        api.create_repo(
            repo_id=target_repo,
            repo_type="dataset",
            exist_ok=True,
            private=private,
        )

        # Stage files and upload
        msg = commit_message or f"Sync The Amazing Race dataset v{self.version}"

        if staging_dir:
            stage_path = Path(staging_dir)
            self.prepare_staging_directory(stage_path)
            api.upload_folder(
                folder_path=str(stage_path),
                repo_id=target_repo,
                repo_type="dataset",
                commit_message=msg,
            )
        else:
            with tempfile.TemporaryDirectory() as tmp_dir:
                stage_path = Path(tmp_dir)
                self.prepare_staging_directory(stage_path)
                api.upload_folder(
                    folder_path=str(stage_path),
                    repo_id=target_repo,
                    repo_type="dataset",
                    commit_message=msg,
                )

        # Tag version release on Hugging Face Hub
        if self.version:
            try:
                api.create_tag(
                    repo_id=target_repo,
                    repo_type="dataset",
                    tag=f"v{self.version}",
                    tag_message=f"Release v{self.version}",
                    exist_ok=True,
                )
            except Exception as e:
                logger.debug("Could not create tag on Hugging Face Hub: %s", e)

        dataset_url = f"https://huggingface.co/datasets/{target_repo}"
        logger.info("Successfully published dataset to %s", dataset_url)

        return {
            "repo_id": target_repo,
            "url": dataset_url,
            "version": self.version,
            "private": private,
        }

    def prepare_space_staging_directory(
        self,
        staging_dir: Path | str,
        title: str = "The Amazing Race Analytics Dashboard",
    ) -> Path:
        """Prepare staging directory containing all files required for Hugging Face Spaces deployment."""
        stage_path = Path(staging_dir).resolve()
        stage_path.mkdir(parents=True, exist_ok=True)

        # 1. README.md with Space metadata frontmatter
        space_card = generate_space_card(version=self.version, title=title)
        (stage_path / "README.md").write_text(space_card, encoding="utf-8")

        # 2. requirements.txt
        reqs = [
            "streamlit>=1.35.0",
            "pandas>=2.2.2",
            "pyarrow>=16.0.0",
            "altair>=5.0.0",
            "pydantic>=2.7.0",
            "beautifulsoup4>=4.12.3",
            "httpx>=0.27.0",
            "lxml>=5.2.0",
            "rich>=13.7.0",
        ]
        (stage_path / "requirements.txt").write_text(
            "\n".join(reqs) + "\n", encoding="utf-8"
        )

        # 2.5. Dockerfile
        dockerfile = (
            "FROM python:3.11-slim\n\n"
            "RUN useradd -m -u 1000 user\n"
            "USER user\n"
            "ENV HOME=/home/user \\\n"
            "    PATH=/home/user/.local/bin:$PATH\n\n"
            "WORKDIR $HOME/app\n\n"
            "COPY --chown=user requirements.txt .\n"
            "RUN pip install --no-cache-dir --user -r requirements.txt\n\n"
            "COPY --chown=user . $HOME/app\n\n"
            "EXPOSE 7860\n\n"
            'CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]\n'
        )
        (stage_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")

        # 3. .streamlit/config.toml (Catppuccin Mocha theme)
        dot_streamlit = stage_path / ".streamlit"
        dot_streamlit.mkdir(parents=True, exist_ok=True)
        local_config = self.repo_root / ".streamlit" / "config.toml"
        if local_config.exists():
            shutil.copy2(local_config, dot_streamlit / "config.toml")
        else:
            catppuccin_toml = (
                "[theme]\n"
                'base = "dark"\n'
                'primaryColor = "#cba6f7"\n'
                'backgroundColor = "#1e1e2e"\n'
                'secondaryBackgroundColor = "#181825"\n'
                'textColor = "#cdd6f4"\n'
                'font = "sans serif"\n\n'
                "[client]\n"
                'toolbarMode = "minimal"\n'
            )
            (dot_streamlit / "config.toml").write_text(
                catppuccin_toml, encoding="utf-8"
            )

        # 4. Space entrypoint app.py
        space_app_py = (
            '"""Hugging Face Space entrypoint for The Amazing Race Analytics Dashboard."""\n\n'
            "import sys\n"
            "from pathlib import Path\n\n"
            'src_dir = Path(__file__).resolve().parent / "src"\n'
            "if src_dir.exists() and str(src_dir) not in sys.path:\n"
            "    sys.path.insert(0, str(src_dir))\n\n"
            "from tar_dataset.dashboard.app import main\n\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
        )
        (stage_path / "app.py").write_text(space_app_py, encoding="utf-8")

        # 5. Copy src/tar_dataset
        src_target = stage_path / "src" / "tar_dataset"
        src_source = self.repo_root / "src" / "tar_dataset"
        if src_source.exists():
            if src_target.exists():
                shutil.rmtree(src_target)
            shutil.copytree(
                src_source,
                src_target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )

        # 6. Copy processed data tables
        data_proc_target = stage_path / "data" / "processed"
        data_proc_target.mkdir(parents=True, exist_ok=True)
        if self.processed_dir.exists():
            for pq in self.processed_dir.glob("*.parquet"):
                shutil.copy2(pq, data_proc_target / pq.name)
            for csv_file in self.processed_dir.glob("*.csv"):
                shutil.copy2(csv_file, data_proc_target / csv_file.name)

        # 7. Copy in-progress raw wikipedia files
        data_raw_target = stage_path / "data" / "raw" / "wikipedia"
        data_raw_target.mkdir(parents=True, exist_ok=True)
        wiki_raw = self.repo_root / "data" / "raw" / "wikipedia"
        if wiki_raw.exists():
            for json_file in wiki_raw.glob("season_*.json"):
                shutil.copy2(json_file, data_raw_target / json_file.name)

        # 8. Support files
        if (self.repo_root / "LICENSE").exists():
            shutil.copy2(self.repo_root / "LICENSE", stage_path / "LICENSE")

        return stage_path

    def publish_space(
        self,
        repo_id: str | None = None,
        token: str | None = None,
        private: bool = False,
        commit_message: str | None = None,
        staging_dir: Path | str | None = None,
        title: str = "The Amazing Race Analytics Dashboard",
    ) -> dict[str, Any]:
        """Publish the dashboard application to Hugging Face Spaces."""
        try:
            from huggingface_hub import HfApi
        except ImportError as err:
            raise ImportError(
                "huggingface_hub is required to publish to Hugging Face Spaces. "
                "Install it with `uv pip install huggingface_hub` or `pip install 'the-amazing-race[hf]'`."
            ) from err

        auth_token = (
            token
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )
        if not auth_token:
            try:
                from huggingface_hub import get_token

                auth_token = get_token()
            except Exception as e:
                logger.debug("Could not retrieve stored Hugging Face token: %s", e)

        api = HfApi(token=auth_token)

        target_repo = repo_id or os.environ.get("HF_SPACE_REPO_ID")
        if not target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/the-amazing-race-dashboard"
            except Exception as e:
                logger.warning("Could not auto-determine Hugging Face username: %s", e)
                target_repo = "nicholascwilde/the-amazing-race-dashboard"
        elif "/" not in target_repo:
            try:
                user_info = api.whoami(token=auth_token)
                username = user_info.get("name")
                target_repo = f"{username}/{target_repo}"
            except Exception as e:
                logger.debug("Could not prepend username to space repository ID: %s", e)

        logger.info("Target Hugging Face Space repository: %s", target_repo)

        api.create_repo(
            repo_id=target_repo,
            repo_type="space",
            space_sdk="docker",
            exist_ok=True,
            private=private,
        )

        msg = commit_message or f"Deploy The Amazing Race dashboard v{self.version}"

        if staging_dir:
            stage_path = Path(staging_dir)
            self.prepare_space_staging_directory(stage_path, title=title)
            api.upload_folder(
                folder_path=str(stage_path),
                repo_id=target_repo,
                repo_type="space",
                commit_message=msg,
            )
        else:
            with tempfile.TemporaryDirectory() as tmp_dir:
                stage_path = Path(tmp_dir)
                self.prepare_space_staging_directory(stage_path, title=title)
                api.upload_folder(
                    folder_path=str(stage_path),
                    repo_id=target_repo,
                    repo_type="space",
                    commit_message=msg,
                )

        space_url = f"https://huggingface.co/spaces/{target_repo}"
        logger.info(
            "Successfully deployed dashboard to Hugging Face Spaces: %s", space_url
        )

        return {
            "repo_id": target_repo,
            "url": space_url,
            "version": self.version,
            "private": private,
        }
