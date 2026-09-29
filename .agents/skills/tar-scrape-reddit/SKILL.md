---
name: tar-scrape-reddit
description: >-
  Use this skill to scrape and extract episode discussion threads, post-episode reactions,
  and fan commentary from Reddit's r/TheAmazingRace subreddit for conversational AI training.
---

# Scrape Reddit Discussions for The Amazing Race

This skill allows agents to search and extract episode discussion threads and top user comments from `r/TheAmazingRace`.

## Usage

### 1. Scrape Episode Discussions

Search for episode threads and extract top comments (default query: `"Discussion Thread"`):

```bash
uv run tar-dataset scrape-reddit --query "Episode Discussion" --limit 25 --comments
```

Parameters:
- `--query`, `-q`: Search phrase (e.g. `"Season 35 Episode"`, `"Post-Episode"`, `"AMA"`).
- `--limit`, `-n`: Maximum number of submissions to return (default 25).
- `--comments` / `--no-comments`: Flag to toggle fetching top comments.

### 2. Search for Team AMAs or Season Retrospectives

```bash
uv run tar-dataset scrape-reddit --query "AMA" --limit 10
uv run tar-dataset scrape-reddit --query "Season 35 Review" --limit 10
```

## Raw Output Files

- `data/raw/reddit/reddit_discussions_<timestamp>.json`

## Verification

Inspect the downloaded Reddit submissions and comment trees:
```bash
cat data/raw/reddit/reddit_discussions_*.json | head -n 30
```
