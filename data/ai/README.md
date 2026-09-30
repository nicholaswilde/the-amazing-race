# The Amazing Race AI Training Corpora & Benchmark Suite

This directory contains curated machine learning datasets formatted for Large Language Model (LLM) instruction fine-tuning, Retrieval-Augmented Generation (RAG) vector embeddings, and evaluation benchmarking on **The Amazing Race** (TAR).

---

## 📁 Files in this Dataset

### 1. `tar_qa_finetuning.jsonl`
- **Format**: JSON Lines, OpenAI/ChatML conversation message format (`messages`).
- **Use Case**: Supervised Fine-Tuning (SFT), instruction tuning, conversational Q&A training.
- **Example Record**:
  ```json
  {
    "messages": [
      {"role": "system", "content": "You are an expert AI assistant specializing in the television reality competition series The Amazing Race."},
      {"role": "user", "content": "Who won The Amazing Race season 1, and what was their relationship?"},
      {"role": "assistant", "content": "The winners of The Amazing Race Season 1 were Rob Frisbee & Brennan Swain, a team of Lawyers and best friends from Los Angeles, California."}
    ],
    "category": "winners",
    "season": 1,
    "version": "US"
  }
  ```

### 2. `tar_knowledge_corpus.jsonl`
- **Format**: JSON Lines, document chunks with structural metadata.
- **Use Case**: RAG chunking, vector database ingestion (Chroma, Qdrant, Pinecone), BM25 hybrid search, and continuous domain pre-training.
- **Example Record**:
  ```json
  {
    "id": "tar_us_s01_leg_01",
    "title": "The Amazing Race US Season 1 Leg 1",
    "text": "Season 1 Leg 1 began at Central Park in New York City... Teams flew to Johannesburg, South Africa...",
    "metadata": {
      "version": "US",
      "season": 1,
      "leg_number": 1,
      "route": "New York City, USA to Johannesburg, South Africa"
    }
  }
  ```

### 3. `tar_benchmark_suite.jsonl`
- **Format**: JSON Lines, benchmark evaluation prompts with golden reference answers.
- **Use Case**: Evaluating model factual recall, hallucination rates, and multi-hop reasoning across 45+ curated test questions.
- **Example Record**:
  ```json
  {
    "id": "bench_01",
    "category": "factual_recall",
    "question": "Which team was eliminated in Leg 1 of Season 1?",
    "golden_answer": "Matt & Ana",
    "eval_type": "exact_match_or_contains"
  }
  ```

---

## 🚀 Loading in Python

```python
import json

# Read fine-tuning examples
with open("tar_qa_finetuning.jsonl", "r", encoding="utf-8") as f:
    sft_data = [json.loads(line) for line in f]
print(f"Loaded {len(sft_data)} instruction tuning examples")

# Using Hugging Face Datasets
from datasets import load_dataset
dataset = load_dataset("json", data_files="tar_qa_finetuning.jsonl")
```

---

## 📜 License & Citation

Distributed under the **Apache License 2.0**.
See [LICENSE](../../LICENSE) for full details.
