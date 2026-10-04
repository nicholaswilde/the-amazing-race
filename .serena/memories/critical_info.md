# The Amazing Race - Project Critical Information

## Core Architecture
- Primary data pipeline and CLI: `src/tar_dataset/`
- Streamlit interactive web dashboard: `src/tar_dataset/dashboard/app.py`
- Root entrypoints for Cloud & Docker: `app.py`, `compose.yaml`, `Dockerfile`
- Relational tables format: Apache Parquet & CSV in `data/processed/`
- Primary testing command: `task check` or `task test`
- Release automation: `./scripts/release.sh [patch|minor|major]`

## Development Standards
- Python environment managed via `uv` (`uv run ...`, never bare `python` or `pip`).
- Conventional commits enforced for releases.
- Never commit `.env` or files containing secrets.
