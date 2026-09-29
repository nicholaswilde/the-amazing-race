"""Scrapers for The Amazing Race dataset."""

from tar_dataset.scrapers.fandom import FandomScraper
from tar_dataset.scrapers.reddit import RedditScraper
from tar_dataset.scrapers.wikipedia import WikipediaScraper

__all__ = ["FandomScraper", "RedditScraper", "WikipediaScraper"]
