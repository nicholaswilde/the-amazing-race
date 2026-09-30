# The Amazing Race AI Datasets

This directory contains Apache Arrow IPC and HuggingFace Datasets-compatible bundles for instruction fine-tuning and retrieval-augmented generation (RAG).

## Loading with HuggingFace `datasets`

```python
from datasets import load_from_disk

# Load Q&A Fine-Tuning Dataset
ds_qa = load_from_disk('data/ai/huggingface/qa_finetuning')
print(ds_qa)
print(ds_qa[0])

# Load Knowledge Retrieval Corpus
ds_corpus = load_from_disk('data/ai/huggingface/knowledge_corpus')
print(ds_corpus)
```

## Direct Apache Arrow IPC Loading

```python
import pyarrow.feather as feather

table = feather.read_table('data/processed/arrow/teams.arrow')
df = table.to_pandas()
```
