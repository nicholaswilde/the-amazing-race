"""Apache Arrow IPC and HuggingFace Datasets exporter for The Amazing Race dataset.

Provides zero-overhead direct serialization for high-throughput AI/LLM model training.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
from pyarrow import feather

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


class ArrowExporter:
    """Exports processed tables and AI corpora into Apache Arrow IPC format and HuggingFace dataset layouts."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        ai_dir: Path | str = "data/ai",
        arrow_dir: Path | str | None = None,
        hf_dir: Path | str | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.ai_dir = Path(ai_dir)
        self.arrow_dir = Path(arrow_dir) if arrow_dir else self.processed_dir / "arrow"
        self.hf_dir = Path(hf_dir) if hf_dir else self.ai_dir / "huggingface"

    def export_arrow_tables(self) -> dict[str, Path]:
        """Export all processed tables into standalone Apache Arrow IPC (.arrow) files."""
        self.arrow_dir.mkdir(parents=True, exist_ok=True)
        exported: dict[str, Path] = {}

        for table_name in TABLES:
            parquet_path = self.processed_dir / f"{table_name}.parquet"
            csv_path = self.processed_dir / f"{table_name}.csv"

            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
            elif csv_path.exists():
                df = pd.read_csv(csv_path)
            else:
                logger.warning("No data found for table '%s'", table_name)
                continue

            arrow_table = pa.Table.from_pandas(df, preserve_index=False)
            output_file = self.arrow_dir / f"{table_name}.arrow"

            # Write standard Arrow IPC file format
            feather.write_feather(arrow_table, output_file, compression="zstd")
            exported[table_name] = output_file
            logger.info(
                "Exported %s to Arrow IPC (%d rows) -> %s",
                table_name,
                len(df),
                output_file,
            )

        return exported

    def _create_hf_dataset_dir(
        self,
        dataset_name: str,
        df: pd.DataFrame,
        description: str = "",
    ) -> Path:
        """Create a HuggingFace Datasets disk-compatible directory with Arrow IPC shards."""
        target_dir = self.hf_dir / dataset_name
        target_dir.mkdir(parents=True, exist_ok=True)

        arrow_table = pa.Table.from_pandas(df, preserve_index=False)
        arrow_filename = "data-00000-of-00001.arrow"
        arrow_filepath = target_dir / arrow_filename

        feather.write_feather(arrow_table, arrow_filepath, compression="zstd")
        file_size = arrow_filepath.stat().st_size
        num_rows = len(df)

        fingerprint = hashlib.md5(f"{dataset_name}-{num_rows}".encode()).hexdigest()[
            :16
        ]

        # Construct dataset_info.json compliant with Hugging Face datasets.load_from_disk
        info_dict: dict[str, Any] = {
            "builder_name": "arrow_dataset",
            "citation": "The Amazing Race Dataset & AI Training Corpus",
            "description": description
            or f"The Amazing Race dataset for {dataset_name}",
            "homepage": "https://github.com/nicholaswilde/the-amazing-race",
            "license": "Apache-2.0",
            "splits": {
                "train": {
                    "name": "train",
                    "num_bytes": file_size,
                    "num_examples": num_rows,
                    "dataset_name": dataset_name,
                }
            },
        }

        with open(target_dir / "dataset_info.json", "w", encoding="utf-8") as f:
            json.dump(info_dict, f, indent=2)

        state_dict: dict[str, Any] = {
            "_data_files": [{"filename": arrow_filename}],
            "_fingerprint": fingerprint,
            "_format_columns": None,
            "_format_kwargs": {},
            "_format_type": None,
            "_output_all_columns": False,
            "_split": "train",
        }

        with open(target_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

        return target_dir

    def export_huggingface_datasets(self) -> dict[str, Path]:
        """Export AI training corpora (QA finetuning, knowledge corpus) into HF datasets format."""
        self.hf_dir.mkdir(parents=True, exist_ok=True)
        exported: dict[str, Path] = {}

        # 1. QA Finetuning Dataset
        qa_jsonl = self.ai_dir / "tar_qa_finetuning.jsonl"
        if qa_jsonl.exists():
            records = []
            with open(qa_jsonl, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            if records:
                # Flatten chat messages for tablular/Arrow compatibility
                flattened = []
                for idx, r in enumerate(records):
                    messages = r.get("messages", [])
                    user_msg = next(
                        (
                            m.get("content", "")
                            for m in messages
                            if m.get("role") == "user"
                        ),
                        "",
                    )
                    asst_msg = next(
                        (
                            m.get("content", "")
                            for m in messages
                            if m.get("role") == "assistant"
                        ),
                        "",
                    )
                    sys_msg = next(
                        (
                            m.get("content", "")
                            for m in messages
                            if m.get("role") == "system"
                        ),
                        "",
                    )
                    metadata = r.get("metadata", {})
                    flattened.append(
                        {
                            "id": f"qa_{idx:05d}",
                            "system": sys_msg,
                            "instruction": user_msg,
                            "response": asst_msg,
                            "category": metadata.get("type", "general"),
                            "season": metadata.get("season"),
                        }
                    )
                df_qa = pd.DataFrame(flattened)
                exported["qa_finetuning"] = self._create_hf_dataset_dir(
                    "qa_finetuning",
                    df_qa,
                    "Instruction-tuning Q&A dataset for The Amazing Race trivia, stats, and history.",
                )

        # 2. Knowledge Corpus Dataset
        corpus_jsonl = self.ai_dir / "tar_knowledge_corpus.jsonl"
        if corpus_jsonl.exists():
            records = []
            with open(corpus_jsonl, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            if records:
                flattened_corpus = []
                for r in records:
                    meta = r.get("metadata", {})
                    flattened_corpus.append(
                        {
                            "id": r.get("id", ""),
                            "title": r.get("title", ""),
                            "text": r.get("text", ""),
                            "doc_type": meta.get("type", ""),
                            "season": meta.get("season"),
                            "leg": meta.get("leg"),
                        }
                    )
                df_corpus = pd.DataFrame(flattened_corpus)
                exported["knowledge_corpus"] = self._create_hf_dataset_dir(
                    "knowledge_corpus",
                    df_corpus,
                    "RAG knowledge retrieval corpus containing detailed leg narratives, challenge summaries, and team profiles.",
                )

        # 3. Create dataset card / README for HuggingFace
        card_content = (
            "# The Amazing Race AI Datasets\n\n"
            "This directory contains Apache Arrow IPC and HuggingFace Datasets-compatible bundles for "
            "instruction fine-tuning and retrieval-augmented generation (RAG).\n\n"
            "## Loading with HuggingFace `datasets`\n\n"
            "```python\n"
            "from datasets import load_from_disk\n\n"
            "# Load Q&A Fine-Tuning Dataset\n"
            "ds_qa = load_from_disk('data/ai/huggingface/qa_finetuning')\n"
            "print(ds_qa)\n"
            "print(ds_qa[0])\n\n"
            "# Load Knowledge Retrieval Corpus\n"
            "ds_corpus = load_from_disk('data/ai/huggingface/knowledge_corpus')\n"
            "print(ds_corpus)\n"
            "```\n\n"
            "## Direct Apache Arrow IPC Loading\n\n"
            "```python\n"
            "import pyarrow.feather as feather\n\n"
            "table = feather.read_table('data/processed/arrow/teams.arrow')\n"
            "df = table.to_pandas()\n"
            "```\n"
        )
        with open(self.hf_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(card_content)

        return exported

    def export_all(self) -> dict[str, Any]:
        """Run both Arrow IPC table exports and HF dataset exports."""
        arrow_tables = self.export_arrow_tables()
        hf_datasets = self.export_huggingface_datasets()
        return {
            "arrow_tables": arrow_tables,
            "hf_datasets": hf_datasets,
        }


def export_arrow_and_hf(
    processed_dir: Path | str = "data/processed",
    ai_dir: Path | str = "data/ai",
) -> dict[str, Any]:
    """Helper function to run Arrow and HuggingFace exports."""
    exporter = ArrowExporter(processed_dir=processed_dir, ai_dir=ai_dir)
    return exporter.export_all()
