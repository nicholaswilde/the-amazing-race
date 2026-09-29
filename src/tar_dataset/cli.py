"""CLI for The Amazing Race Dataset creation, scraping, importing, and AI export."""

from __future__ import annotations

import logging

import typer
from rich.console import Console
from rich.table import Table

from tar_dataset.exports.ai_formats import AIExportBuilder
from tar_dataset.importers.sheets import SheetsImporter
from tar_dataset.processors.builder import DatasetBuilder
from tar_dataset.processors.validator import DatasetValidator
from tar_dataset.scrapers.fandom import FandomScraper
from tar_dataset.scrapers.reddit import RedditScraper
from tar_dataset.scrapers.wikipedia import WikipediaScraper

app = typer.Typer(
    name="tar-dataset",
    help="The Amazing Race dataset curation & AI training toolkit.",
    add_completion=False,
)
console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@app.command("scrape-wiki")
def scrape_wiki(
    season: int | None = typer.Option(
        None, "--season", "-s", help="Specific season number to scrape"
    ),
    start: int = typer.Option(1, "--start", help="Start season range"),
    end: int = typer.Option(36, "--end", help="End season range"),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise country code (US, CAN, AUS)"
    ),
) -> None:
    """Scrape Wikipedia for season tables, cast, results matrix, and leg summaries."""
    scraper = WikipediaScraper()
    if season is not None:
        console.print(
            f"[bold blue]Scraping Wikipedia for Season {season} ({version})...[/bold blue]"
        )
        data = scraper.scrape_season(season, version=version, save=True)
        if data:
            console.print(f"[green]✓ Successfully scraped Season {season}[/green]")
            console.print(f"  Contestants: {len(data.get('contestants', []))}")
            console.print(f"  Teams: {len(data.get('results', []))}")
            console.print(f"  Legs: {len(data.get('legs', []))}")
            console.print(f"  Episodes: {len(data.get('episodes', []))}")
        else:
            console.print(f"[red]✗ Failed to scrape Season {season}[/red]")
    else:
        console.print(
            f"[bold blue]Scraping Wikipedia for Seasons {start} to {end} ({version})...[/bold blue]"
        )
        seasons = scraper.scrape_seasons(start=start, end=end, version=version)
        console.print(f"[green]✓ Finished scraping {len(seasons)} seasons.[/green]")


@app.command("scrape-fandom")
def scrape_fandom(
    season: int | None = typer.Option(
        None, "--season", "-s", help="Specific season number to scrape"
    ),
    start: int = typer.Option(1, "--start", help="Start season range"),
    end: int = typer.Option(36, "--end", help="End season range"),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise country code (US, CAN)"
    ),
) -> None:
    """Scrape Fandom Wiki (amazingrace.fandom.com) for infoboxes and metadata."""
    scraper = FandomScraper()
    if season is not None:
        console.print(
            f"[bold blue]Scraping Fandom for Season {season} ({version})...[/bold blue]"
        )
        data = scraper.scrape_season(season, version=version, save=True)
        if data:
            console.print(f"[green]✓ Scraped Fandom Season {season}[/green]")
        else:
            console.print(f"[red]✗ Could not fetch Fandom Season {season}[/red]")
    else:
        console.print(
            f"[bold blue]Scraping Fandom for Seasons {start} to {end}...[/bold blue]"
        )
        for s in range(start, end + 1):
            scraper.scrape_season(s, version=version, save=True)
        console.print("[green]✓ Fandom scrape completed.[/green]")


@app.command("scrape-reddit")
def scrape_reddit(
    query: str = typer.Option(
        "Discussion Thread", "--query", "-q", help="Search query for r/TheAmazingRace"
    ),
    limit: int = typer.Option(25, "--limit", "-n", help="Max submissions to fetch"),
    comments: bool = typer.Option(
        True, "--comments/--no-comments", help="Fetch top comments for each thread"
    ),
) -> None:
    """Fetch episode discussion threads and fan reactions from r/TheAmazingRace."""
    console.print(
        f"[bold blue]Scraping Reddit r/TheAmazingRace for '{query}' (limit={limit})...[/bold blue]"
    )
    scraper = RedditScraper()
    discussions = scraper.scrape_episode_discussions(
        query=query, limit=limit, fetch_comments=comments, save=True
    )
    console.print(
        f"[green]✓ Successfully collected {len(discussions)} Reddit discussions.[/green]"
    )


@app.command("import-sheet")
def import_sheet(
    url: str = typer.Option(
        ..., "--url", "-u", help="Google Sheet URL or public CSV URL"
    ),
    name: str = typer.Option(
        ..., "--name", "-n", help="Dataset name slug (e.g. tar_leg_times)"
    ),
    gid: str = typer.Option("0", "--gid", "-g", help="Google Sheet tab GID"),
    sheet: str | None = typer.Option(
        None,
        "--sheet",
        "-s",
        help="Specific workbook tab/sheet name (for Excel workbooks)",
    ),
    xlsx: bool = typer.Option(
        False,
        "--xlsx",
        help="Download as full multi-tab XLSX workbook and export all tabs",
    ),
) -> None:
    """Import a community Google Sheet or external CSV table."""
    console.print(f"[bold blue]Importing Sheet: {name}...[/bold blue]")
    importer = SheetsImporter()
    df = importer.import_public_sheet(
        sheet_url=url,
        name=name,
        gid=gid,
        sheet_name=sheet,
        prefer_xlsx=xlsx,
        save=True,
    )
    console.print(
        f"[green]✓ Imported {len(df)} rows with columns: {list(df.columns)}[/green]"
    )


@app.command("build")
def build() -> None:
    """Build tidy datasets (CSV + Parquet) from all cached raw sources."""
    console.print(
        "[bold blue]Building tidy datasets from raw scraped data...[/bold blue]"
    )
    builder = DatasetBuilder()
    dfs = builder.build_all()

    if not dfs:
        console.print(
            "[yellow]No data built. Please run `tar-dataset scrape-wiki` first.[/yellow]"
        )
        return

    table = Table(title="Generated Tidy Datasets (data/processed/)")
    table.add_column("Dataset", style="cyan", no_wrap=True)
    table.add_column("Rows", style="magenta")
    table.add_column("Columns", style="green")

    for name, df in dfs.items():
        table.add_row(
            name,
            str(len(df)),
            ", ".join(df.columns[:5]) + ("..." if len(df.columns) > 5 else ""),
        )

    console.print(table)


@app.command("export-ai")
def export_ai() -> None:
    """Export processed datasets into AI training formats (JSONL for fine-tuning & RAG)."""
    console.print(
        "[bold blue]Generating AI training datasets (data/ai/)...[/bold blue]"
    )
    ai_builder = AIExportBuilder()
    counts = ai_builder.export_all()

    for k, v in counts.items():
        console.print(f"[green]✓ Generated {v} examples for {k}[/green]")


@app.command("validate")
def validate() -> None:
    """Run data integrity, relational constraints, and quality checks."""
    console.print("[bold blue]Running data validation checks...[/bold blue]")
    validator = DatasetValidator()
    report = validator.validate()

    color = (
        "green"
        if report["status"] == "PASS"
        else ("yellow" if report["status"] == "WARNING" else "red")
    )
    console.print(f"Validation Status: [{color}]{report['status']}[/{color}]")

    table = Table(title="Processed Tables Summary")
    table.add_column("Table", style="cyan")
    table.add_column("Row Count", style="magenta")

    for tbl, count in report.get("row_counts", {}).items():
        table.add_row(tbl, str(count))
    console.print(table)

    if report.get("issues"):
        console.print("[bold red]Issues / Warnings found:[/bold red]")
        for issue in report["issues"]:
            console.print(f"  - {issue}")


@app.command("stats")
def stats() -> None:
    """Display overall statistics for all tables in the dataset."""
    validator = DatasetValidator()
    report = validator.validate()

    table = Table(title="The Amazing Race Dataset Statistics")
    table.add_column("Dataset Table", style="cyan")
    table.add_column("Records", style="magenta")

    for tbl, count in report.get("row_counts", {}).items():
        table.add_row(tbl, f"{count:,}")

    console.print(table)


if __name__ == "__main__":
    app()
