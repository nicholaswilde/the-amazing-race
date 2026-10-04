"""CLI for The Amazing Race Dataset creation, scraping, importing, inspection, and AI export."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tar_dataset.exports.ai_formats import AIExportBuilder
from tar_dataset.exports.arrow_export import export_arrow_and_hf
from tar_dataset.exports.benchmark import BenchmarkSuite
from tar_dataset.exports.geojson_export import export_to_geojson
from tar_dataset.exports.hf_publish import HuggingFacePublisher
from tar_dataset.exports.packaging import ReleasePackager
from tar_dataset.exports.r_export import export_to_r
from tar_dataset.exports.sqlite_export import export_to_sqlite
from tar_dataset.importers.sheets import SheetsImporter
from tar_dataset.processors.builder import DatasetBuilder
from tar_dataset.processors.gap_auditor import DatasetGapAuditor
from tar_dataset.processors.predictor import SeasonPredictor
from tar_dataset.processors.validator import DatasetValidator
from tar_dataset.scrapers.fandom import FandomScraper
from tar_dataset.scrapers.reddit import RedditScraper
from tar_dataset.scrapers.wikipedia import WikipediaScraper

app = typer.Typer(
    name="tar-dataset",
    help="The Amazing Race dataset curation & AI training toolkit.",
    add_completion=False,
)
show_app = typer.Typer(
    name="show",
    help="Inspect seasons, teams, racers, and legs directly in the terminal.",
    add_completion=False,
)
app.add_typer(show_app, name="show")

console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _load_table(
    name: str, processed_dir: Path | str = "data/processed"
) -> pd.DataFrame:
    """Helper to load a processed table from Parquet or CSV."""
    p = Path(processed_dir)
    parquet = p / f"{name}.parquet"
    if parquet.exists():
        return pd.read_parquet(parquet)
    csv = p / f"{name}.csv"
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame()


@app.command("scrape-wiki")
def scrape_wiki(
    season: int | None = typer.Option(
        None, "--season", "-s", help="Specific season number to scrape"
    ),
    start: int = typer.Option(1, "--start", help="Start season range"),
    end: int = typer.Option(38, "--end", help="End season range"),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise version (US, CAN, AUS, etc.)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-scrape even if Wikipedia revision is unchanged",
    ),
) -> None:
    """Scrape Wikipedia season tables, contestants, and results matrices."""
    scraper = WikipediaScraper(version=version)

    if season is not None:
        console.print(
            f"[bold blue]Scraping Wikipedia for {version} Season {season}...[/bold blue]"
        )
        data = scraper.scrape_season(season, version=version, force=force)
        if data:
            console.print(
                f"[green]✓ Successfully scraped and cached Season {season}[/green]"
            )
        else:
            console.print(f"[red]✗ Failed to scrape Season {season}[/red]")
        return

    console.print(
        f"[bold blue]Scraping Wikipedia for {version} Seasons {start} to {end}...[/bold blue]"
    )
    results = scraper.scrape_all_seasons(
        start=start, end=end, version=version, force=force
    )
    console.print(
        f"[green]✓ Successfully scraped {len(results)} seasons for {version}[/green]"
    )


@app.command("scrape-fandom")
def scrape_fandom(
    season: int | None = typer.Option(
        None, "--season", "-s", help="Specific season number to scrape"
    ),
    start: int = typer.Option(1, "--start", help="Start season range"),
    end: int = typer.Option(36, "--end", help="End season range"),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise version (US, CAN, AUS, etc.)"
    ),
) -> None:
    """Scrape Amazing Race Fandom wiki pages and metadata."""
    scraper = FandomScraper(version=version)

    if season is not None:
        console.print(
            f"[bold blue]Scraping Fandom Wiki for {version} Season {season}...[/bold blue]"
        )
        data = scraper.scrape_season(season)
        if data:
            console.print(
                f"[green]✓ Successfully scraped and cached Fandom data for Season {season}[/green]"
            )
        else:
            console.print(
                f"[red]✗ Failed to scrape Fandom data for Season {season}[/red]"
            )
        return

    console.print(
        f"[bold blue]Scraping Fandom Wiki for {version} Seasons {start} to {end}...[/bold blue]"
    )
    results = scraper.scrape_all(start=start, end=end)
    console.print(
        f"[green]✓ Successfully scraped {len(results)} Fandom season pages[/green]"
    )


@app.command("scrape-reddit")
def scrape_reddit(
    query: str = typer.Option(
        "Discussion Thread",
        "--query",
        "-q",
        help="Search query (e.g. 'Discussion Thread', 'Live Discussion', 'Post-Episode Discussion', 'AMA')",
    ),
    limit: int = typer.Option(
        100, "--limit", "-l", help="Number of submissions to scrape"
    ),
    subreddit: str = typer.Option(
        "TheAmazingRace", "--subreddit", help="Subreddit name"
    ),
    comments: bool = typer.Option(
        True, "--comments/--no-comments", help="Fetch top comments for threads"
    ),
    batch: bool = typer.Option(
        False,
        "--batch",
        "--all",
        help="Batch scrape all categories (Episode, Live, Post-Episode, and AMAs)",
    ),
) -> None:
    """Fetch episode discussion threads, live reactions, post-episode debriefs, and racer AMAs from Reddit."""
    scraper = RedditScraper(subreddit_name=subreddit)

    if batch:
        console.print(
            f"[bold blue]Batch scraping all TAR discussion categories from r/{subreddit}...[/bold blue]"
        )
        results = scraper.scrape_all_categories(fetch_comments=comments)
        total_scraped = sum(len(discs) for discs in results.values())
        for cat, discs in results.items():
            console.print(f"  • [cyan]{cat}[/cyan]: {len(discs)} threads")
        console.print(
            f"[green]✓ Successfully scraped and cached {total_scraped} discussions across all categories[/green]"
        )
        return

    console.print(
        f"[bold blue]Scraping up to {limit} posts from r/{subreddit} for '{query}'...[/bold blue]"
    )
    discussions = scraper.scrape_discussions(
        query=query, limit=limit, fetch_comments=comments
    )
    console.print(
        f"[green]✓ Successfully scraped and cached {len(discussions)} Reddit discussions[/green]"
    )


@app.command("import-sheet")
def import_sheet(
    sheet_id: str | None = typer.Option(
        None,
        "--sheet-id",
        help="Google Sheet Document ID or Share Link containing TAR stats",
    ),
    csv_file: Path | None = typer.Option(
        None, "--csv", "-f", help="Local CSV file path to import"
    ),
    table_name: str = typer.Option(
        "external_stats",
        "--name",
        "-n",
        help="Target table name in raw data store",
    ),
) -> None:
    """Import a community Google Sheet or external CSV table."""
    importer = SheetsImporter()

    if sheet_id:
        console.print(
            f"[bold blue]Importing Google Sheet {sheet_id} as '{table_name}'...[/bold blue]"
        )
        df = importer.import_public_sheet_csv(sheet_id=sheet_id, name=table_name)
    elif csv_file:
        console.print(
            f"[bold blue]Importing local CSV {csv_file} as '{table_name}'...[/bold blue]"
        )
        df = importer.import_local_csv(file_path=csv_file, name=table_name)
    else:
        console.print(
            "[red]Error: Must provide either --sheet-id or --csv file path[/red]"
        )
        raise typer.Exit(code=1)

    console.print(
        f"[green]✓ Imported {len(df)} rows with columns: {list(df.columns)}[/green]"
    )


@app.command("build")
def build(
    include_in_progress: bool = typer.Option(
        False,
        "--include-in-progress",
        help="Include in-progress seasons (with unfinalized winners/results) in tidy build.",
    ),
) -> None:
    """Build tidy datasets (CSV + Parquet + SQLite) from all cached raw sources."""
    console.print(
        "[bold blue]Building tidy datasets from raw scraped data...[/bold blue]"
    )
    builder = DatasetBuilder(include_in_progress=include_in_progress)
    dfs = builder.build_all()

    if not dfs:
        console.print(
            "[yellow]No data built. Please run `tar-dataset scrape-wiki` first.[/yellow]"
        )
        return

    # Automatically generate SQLite database bundle
    db_path = export_to_sqlite()

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
    console.print(f"[green]✓ Compiled SQLite database bundle at {db_path}[/green]")


@app.command("export-sqlite")
def export_sqlite_cmd(
    processed_dir: Path = typer.Option(
        "data/processed",
        "--processed-dir",
        "-p",
        help="Directory with processed Parquet/CSV tables",
    ),
    db_path: Path = typer.Option(
        "data/processed/tar.db",
        "--db-path",
        "-d",
        help="Path to write SQLite database",
    ),
) -> None:
    """Export processed tables into a unified SQLite database."""
    console.print(f"[bold blue]Exporting tables to SQLite ({db_path})...[/bold blue]")
    out = export_to_sqlite(processed_dir=processed_dir, db_path=db_path)
    console.print(f"[green]✓ Successfully exported SQLite bundle to {out}[/green]")


@app.command("export-arrow")
def export_arrow_cmd(
    processed_dir: Path = typer.Option(
        "data/processed",
        "--processed-dir",
        "-p",
        help="Processed tables directory",
    ),
    ai_dir: Path = typer.Option("data/ai", "--ai-dir", "-a", help="AI directory"),
) -> None:
    """Export tables to Apache Arrow IPC files and HuggingFace Datasets layouts."""
    console.print(
        "[bold blue]Exporting Apache Arrow IPC & HuggingFace datasets...[/bold blue]"
    )
    results = export_arrow_and_hf(processed_dir=processed_dir, ai_dir=ai_dir)

    arrow_tables = results.get("arrow_tables", {})
    hf_datasets = results.get("hf_datasets", {})

    console.print(
        f"[green]✓ Exported {len(arrow_tables)} tables to Apache Arrow IPC (.arrow)[/green]"
    )
    console.print(
        f"[green]✓ Exported {len(hf_datasets)} HuggingFace Datasets to data/ai/huggingface/[/green]"
    )


@app.command("export-r")
def export_r_cmd(
    processed_dir: Path = typer.Option(
        "data/processed",
        "--processed-dir",
        "-p",
        help="Processed tables directory",
    ),
    r_dir: Path = typer.Option(
        "data/processed/r",
        "--r-dir",
        "-r",
        help="Directory to output .rds and .rda files",
    ),
    pkg_dir: Path = typer.Option(
        "r",
        "--pkg-dir",
        help="Companion R package directory",
    ),
) -> None:
    """Export processed tables to native R formats (.rds, .rda) and scaffold companion R package."""
    console.print(
        "[bold blue]Exporting The Amazing Race datasets to R formats and package...[/bold blue]"
    )
    results = export_to_r(
        processed_dir=processed_dir,
        r_output_dir=r_dir,
        r_pkg_dir=pkg_dir,
    )
    rds_tables = results.get("rds", {})
    rda_tables = results.get("rda", {})

    console.print(f"[green]✓ Exported {len(rds_tables)} RDS tables to {r_dir}[/green]")
    console.print(
        f"[green]✓ Exported {len(rda_tables)} RDA package tables to {Path(pkg_dir) / 'data'}[/green]"
    )
    console.print(
        f"[green]✓ Scaffolding and roxygen2 docs complete in {pkg_dir}/[/green]"
    )


@app.command("export-geojson")
def export_geojson_cmd(
    processed_dir: Path = typer.Option(
        "data/processed",
        "--processed-dir",
        "-p",
        help="Processed tables directory",
    ),
    output_file: Path = typer.Option(
        "data/processed/tar_routes.geojson",
        "--output",
        "-o",
        help="Path to output GeoJSON file",
    ),
    include_routes: bool = typer.Option(
        True,
        "--routes/--no-routes",
        help="Include LineString season routes",
    ),
    include_waypoints: bool = typer.Option(
        True,
        "--waypoints/--no-waypoints",
        help="Include Point pit stop waypoints",
    ),
) -> None:
    """Export race routes and leg pit stops to GeoJSON format."""
    console.print(
        "[bold blue]Exporting The Amazing Race routes and waypoints to GeoJSON...[/bold blue]"
    )
    out = export_to_geojson(
        processed_dir=processed_dir,
        output_file=output_file,
        include_routes=include_routes,
        include_waypoints=include_waypoints,
    )
    console.print(f"[green]✓ Exported GeoJSON dataset to {out}[/green]")


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


@app.command("eval-benchmark")
def eval_benchmark() -> None:
    """Evaluate or verify the TAR AI / RAG benchmark suite."""
    console.print(
        "[bold blue]Running The Amazing Race AI Benchmark evaluation...[/bold blue]"
    )
    suite = BenchmarkSuite()
    summary = suite.evaluate_benchmark()
    suite.render_summary(summary)


@app.command("package")
def package_cmd(
    output_dir: Path = typer.Option(
        Path("dist/release"),
        "--output-dir",
        "-o",
        help="Target directory for release bundles and checksums",
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Release version string (e.g. 0.1.0 or v0.1.0; defaults to pyproject.toml)",
    ),
    component: str = typer.Option(
        "all",
        "--component",
        "-c",
        help="Component to package: all, csv, parquet, ai, sqlite, r, python, tidytuesday, checksums",
    ),
) -> None:
    """Package segmented release archives for CSV, Parquet, AI JSONL, R, Python, and generate checksums."""
    console.print(
        f"[bold blue]Packaging release distribution assets (version: {version or 'auto'})...[/bold blue]"
    )
    packager = ReleasePackager(output_dir=output_dir, version=version)

    comp = component.lower()
    if comp == "all":
        results = packager.package_all()
    elif comp == "csv":
        results = {
            "csv": packager.package_csv(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "parquet":
        results = {
            "parquet": packager.package_parquet(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "ai":
        results = {
            "ai": packager.package_ai(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "sqlite":
        pkg = packager.package_sqlite()
        results = ({"sqlite": pkg} if pkg else {}) | {
            "checksums": packager.generate_checksums()
        }
    elif comp == "r":
        results = {
            "r": packager.package_r(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "python":
        results = {
            "python": packager.package_python(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "tidytuesday":
        results = {
            "tidytuesday": packager.package_tidytuesday(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "manifest":
        results = {
            "manifest": packager.generate_manifest(),
            "checksums": packager.generate_checksums(),
        }
    elif comp == "checksums":
        results = {"checksums": packager.generate_checksums()}
    else:
        console.print(
            f"[bold red]Unknown component '{component}'.[/bold red] Choose from: all, csv, parquet, ai, sqlite, r, python, tidytuesday, manifest, checksums."
        )
        raise typer.Exit(1)

    table = Table(title=f"Release Distribution Assets ({packager.tag_version})")
    table.add_column("Category", style="bold cyan")
    table.add_column("Asset File", style="bold white")
    table.add_column("Size", justify="right", style="green")

    for cat, item in results.items():
        if item is None:
            continue
        items_list = item if isinstance(item, list) else [item]
        for p in items_list:
            if isinstance(p, Path) and p.exists():
                size_kb = p.stat().st_size / 1024
                size_str = (
                    f"{size_kb / 1024:.2f} MB"
                    if size_kb >= 1024
                    else f"{size_kb:.1f} KB"
                )
                table.add_row(cat.upper(), p.name, size_str)

    console.print(table)
    console.print(
        f"[bold green]✓ Release assets successfully created in {output_dir}/[/bold green]"
    )


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


@app.command("gaps")
def audit_gaps(
    table: str | None = typer.Option(
        None,
        "--table",
        "-t",
        help="Filter gaps by table name (e.g. 'contestants', 'teams')",
    ),
    season: int | None = typer.Option(
        None, "--season", "-s", help="Filter gaps by season number (e.g. 29)"
    ),
    detail: bool = typer.Option(
        False,
        "--detail",
        "-d",
        help="Show detailed individual rows with missing cells",
    ),
    export_md: Path | None = typer.Option(
        None, "--export-md", help="Export Markdown gap report to specified path"
    ),
) -> None:
    """Audit the dataset for missing cells, null rates, and season-level data gaps."""
    auditor = DatasetGapAuditor()
    auditor.render_report(table_filter=table, season_filter=season, show_detail=detail)

    if export_md:
        out = auditor.export_markdown_report(export_md)
        console.print(f"[green]✓ Exported gap report to {out}[/green]")


@app.command("publish-hf")
def publish_hf(
    repo_id: str | None = typer.Option(
        None,
        "--repo-id",
        "-r",
        help="Target Hugging Face repository ID (default: <username>/the-amazing-race or HF_REPO_ID)",
    ),
    token: str | None = typer.Option(
        None,
        "--token",
        "-t",
        help="Hugging Face API token with write permissions (or set HF_TOKEN)",
    ),
    private: bool = typer.Option(
        False,
        "--private",
        help="Create dataset repository as private on Hugging Face Hub",
    ),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help="Custom commit message for Hub upload",
    ),
    stage_only: Path | None = typer.Option(
        None,
        "--stage-only",
        help="Only prepare dataset staging directory locally without uploading",
    ),
) -> None:
    """Publish and synchronize tidy datasets and AI corpora to Hugging Face Hub."""
    console.print(
        "[bold blue]Preparing The Amazing Race dataset for Hugging Face Hub...[/bold blue]"
    )
    publisher = HuggingFacePublisher()

    if stage_only:
        staged = publisher.prepare_staging_directory(stage_only)
        console.print(f"[green]✓ Dataset staged locally at {staged}[/green]")
        return

    try:
        result = publisher.publish(
            repo_id=repo_id,
            token=token,
            private=private,
            commit_message=message,
        )
        console.print(
            "[bold green]✓ Successfully published to Hugging Face Hub![/bold green]"
        )
        console.print(f"Repository: [cyan]{result['repo_id']}[/cyan]")
        console.print(f"URL: [link={result['url']}]{result['url']}[/link]")
    except Exception as e:
        console.print(f"[bold red]Error publishing to Hugging Face Hub:[/bold red] {e}")
        raise typer.Exit(1) from e


# ==============================================================================
# CLI Inspection Sub-commands: tar-dataset show ...
# ==============================================================================


@show_app.command("season")
def show_season(
    season_num: int = typer.Argument(..., help="Season number (e.g. 1)"),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise version code (US, CAN, etc.)"
    ),
) -> None:
    """Inspect season details, itinerary legs, and final leaderboard."""
    seasons_df = _load_table("seasons")
    if seasons_df.empty:
        console.print(
            "[red]Error: seasons table not found. Run `tar-dataset build` first.[/red]"
        )
        raise typer.Exit(1)

    s_row = seasons_df[
        (seasons_df["version"] == version) & (seasons_df["season"] == season_num)
    ]
    if s_row.empty:
        console.print(f"[red]Error: {version} Season {season_num} not found.[/red]")
        raise typer.Exit(1)

    season_info = s_row.iloc[0]

    # Season Overview Panel
    dist_str = (
        f"{season_info['distance_miles']:,.0f} mi / {season_info['distance_km']:,.0f} km"
        if pd.notna(season_info.get("distance_miles"))
        else "N/A"
    )
    overview_text = (
        f"[bold cyan]Franchise:[/bold cyan] {season_info['version']} | [bold cyan]Season:[/bold cyan] {season_info['season']}\n"
        f"[bold yellow]Winners:[/bold yellow] [bold green]{season_info.get('winners', 'Unknown')}[/bold green]\n"
        f"[bold]Teams:[/bold] {season_info.get('n_teams', 'N/A')}  |  "
        f"[bold]Legs:[/bold] {season_info.get('n_legs', 'N/A')}  |  "
        f"[bold]Episodes:[/bold] {season_info.get('n_episodes', 'N/A')}\n"
        f"[bold]Total Distance Traveled:[/bold] {dist_str}\n"
        f"[bold]Air Dates:[/bold] {season_info.get('air_dates', 'N/A')}\n"
        f"[bold]Filming Dates:[/bold] {season_info.get('filming_dates', 'N/A')}\n"
        f"[bold]Reference:[/bold] {season_info.get('wiki_url', 'N/A')}"
    )
    console.print(
        Panel(
            overview_text,
            title=f"The Amazing Race {version} Season {season_num} Overview",
            expand=False,
        )
    )

    # Route Legs Table
    legs_df = _load_table("legs")
    if not legs_df.empty:
        s_legs = legs_df[
            (legs_df["version"] == version) & (legs_df["season"] == season_num)
        ].sort_values("leg_number")
        if not s_legs.empty:
            legs_table = Table(
                title=f"Season {season_num} Route Itinerary ({len(s_legs)} Legs)"
            )
            legs_table.add_column("Leg", style="bold cyan", justify="right")
            legs_table.add_column("Route Itinerary", style="white")
            legs_table.add_column("Stops", style="magenta", justify="right")
            legs_table.add_column("Tasks", style="green", justify="right")

            for _, leg in s_legs.iterrows():
                legs_table.add_row(
                    str(leg["leg_number"]),
                    str(leg.get("route_header", "Unknown Route")),
                    str(leg.get("itinerary_stops", 0)),
                    str(leg.get("tasks_count", 0)),
                )
            console.print(legs_table)

    # Teams Leaderboard Table
    teams_df = _load_table("teams")
    results_df = _load_table("leg_results")

    if not teams_df.empty:
        s_teams = teams_df[
            (teams_df["version"] == version) & (teams_df["season"] == season_num)
        ].sort_values("result")
        if not s_teams.empty:
            teams_table = Table(
                title=f"Season {season_num} Final Standings & Teams Leaderboard"
            )
            teams_table.add_column("Place", style="bold yellow", justify="right")
            teams_table.add_column("Team Name", style="bold white")
            teams_table.add_column("Relationship", style="cyan")
            teams_table.add_column("Hometown", style="blue")
            teams_table.add_column("Legs Won", style="green", justify="right")
            teams_table.add_column("Racing Avg", style="magenta", justify="right")
            teams_table.add_column("Final Status", style="italic")

            for _, tm in s_teams.iterrows():
                tm_name = tm["team_name"]
                racing_avg_str = "N/A"
                if not results_df.empty:
                    tm_res = results_df[
                        (results_df["version"] == version)
                        & (results_df["season"] == season_num)
                        & (results_df["team_name"] == tm_name)
                    ]
                    if not tm_res.empty:
                        racing_avg = tm_res["placement"].mean()
                        racing_avg_str = f"{racing_avg:.2f}"

                teams_table.add_row(
                    str(tm["result"]),
                    tm_name,
                    str(tm.get("relationship", "")),
                    str(tm.get("hometown", "")),
                    str(tm.get("legs_won", 0)),
                    racing_avg_str,
                    str(tm.get("status", "")),
                )
            console.print(teams_table)


@show_app.command("team")
def show_team(
    team_query: str = typer.Argument(
        ..., help="Team name or partial query (e.g. 'Rob & Brennan' or 'Colin')"
    ),
    season_num: int | None = typer.Option(
        None, "--season", "-s", help="Filter by specific season"
    ),
    version: str = typer.Option(
        "US", "--version", "-v", help="Franchise version (US, CAN, etc.)"
    ),
) -> None:
    """Inspect team statistics, racing averages, team members, and leg placements."""
    teams_df = _load_table("teams")
    if teams_df.empty:
        console.print(
            "[red]Error: teams table not found. Run `tar-dataset build` first.[/red]"
        )
        raise typer.Exit(1)

    # Search filter
    filtered = teams_df[
        (teams_df["version"] == version)
        & (
            teams_df["team_name"].str.contains(team_query, case=False, na=False)
            | teams_df["team_id"].str.contains(team_query, case=False, na=False)
        )
    ]

    if season_num is not None:
        filtered = filtered[filtered["season"] == season_num]

    if filtered.empty:
        console.print(
            f"[red]No teams found matching '{team_query}' for version {version}.[/red]"
        )
        raise typer.Exit(1)

    if len(filtered) > 1 and season_num is None:
        console.print(
            f"[yellow]Multiple teams matched '{team_query}'. Specify --season to view details:[/yellow]"
        )
        tbl = Table()
        tbl.add_column("Season", style="cyan")
        tbl.add_column("Team Name", style="white")
        tbl.add_column("Relationship", style="blue")
        tbl.add_column("Result", style="green")
        for _, r in filtered.iterrows():
            tbl.add_row(
                str(r["season"]),
                r["team_name"],
                str(r.get("relationship", "")),
                str(r.get("result", "")),
            )
        console.print(tbl)
        return

    tm = filtered.iloc[0]
    season_val = int(tm["season"])
    team_name = tm["team_name"]

    # Calculate Racing Average from leg_results
    results_df = _load_table("leg_results")
    legs_df = _load_table("legs")
    contestants_df = _load_table("contestants")

    tm_results = pd.DataFrame()
    racing_avg_str = "N/A"
    if not results_df.empty:
        tm_results = results_df[
            (results_df["version"] == version)
            & (results_df["season"] == season_val)
            & (results_df["team_name"] == team_name)
        ].sort_values("leg_number")

        if not tm_results.empty:
            avg_placement = tm_results["placement"].mean()
            racing_avg_str = f"{avg_placement:.2f}"

    # Team Members
    members = []
    if not contestants_df.empty:
        s_contestants = contestants_df[
            (contestants_df["version"] == version)
            & (contestants_df["season"] == season_val)
        ]
        # Match by relationship or team name keywords
        for _, c in s_contestants.iterrows():
            c_name = str(c.get("name", ""))
            c_first = c_name.split()[0]
            if c_first.lower() in team_name.lower():
                age_str = f", Age {int(c['age'])}" if pd.notna(c.get("age")) else ""
                ht_str = (
                    f" from {c['hometown']}"
                    if pd.notna(c.get("hometown")) and c["hometown"]
                    else ""
                )
                members.append(f"{c_name}{age_str}{ht_str}")

    members_str = (
        "\n".join(f"  • {m}" for m in members)
        if members
        else "  • No individual profiles recorded."
    )

    panel_text = (
        f"[bold white]Team Name:[/bold white] [bold cyan]{team_name}[/bold cyan]\n"
        f"[bold white]Season:[/bold white] {season_val} ({version})\n"
        f"[bold white]Relationship:[/bold white] {tm.get('relationship', 'N/A')}\n"
        f"[bold white]Hometown:[/bold white] {tm.get('hometown', 'N/A')}\n"
        f"[bold white]Final Result:[/bold white] [bold yellow]Place {tm.get('result', 'N/A')}[/bold yellow] ({tm.get('status', 'N/A')})\n"
        f"[bold white]Legs Won:[/bold white] {tm.get('legs_won', 0)}  |  "
        f"[bold white]Legs Completed:[/bold white] {tm.get('legs_completed', 0)}  |  "
        f"[bold white]Racing Average:[/bold white] [bold green]{racing_avg_str}[/bold green]\n\n"
        f"[bold white]Team Members:[/bold white]\n{members_str}"
    )
    console.print(Panel(panel_text, title=f"Team Profile: {team_name}", expand=False))

    # Leg-by-leg Results Table
    if not tm_results.empty:
        perf_table = Table(title=f"Leg-by-Leg Racing Record for {team_name}")
        perf_table.add_column("Leg", style="cyan", justify="right")
        perf_table.add_column("Route Destination", style="white")
        perf_table.add_column("Placement", style="bold yellow", justify="right")
        perf_table.add_column("Hazards & Special Events", style="magenta")

        for _, res in tm_results.iterrows():
            leg_num = int(res["leg_number"])
            place_val = res.get("placement")
            place_str = (
                f"{int(place_val)}"
                if pd.notna(place_val)
                else str(res.get("raw_cell", "N/A"))
            )

            # Route info
            route_str = "Route Info N/A"
            if not legs_df.empty:
                l_match = legs_df[
                    (legs_df["version"] == version)
                    & (legs_df["season"] == season_val)
                    & (legs_df["leg_number"] == leg_num)
                ]
                if not l_match.empty:
                    route_str = str(l_match.iloc[0].get("route_header", ""))

            # Special events tags
            specials = []
            if res.get("fast_forward"):
                specials.append("[bold green]Fast Forward 🚀[/bold green]")
            if res.get("uturn"):
                specials.append("[bold red]U-Turn ↩️[/bold red]")
            if res.get("yield"):
                specials.append("[bold yellow]Yield ⏳[/bold yellow]")
            if res.get("speed_bump"):
                specials.append("[bold orange1]Speed Bump ⚠️[/bold orange1]")
            if res.get("is_non_elimination"):
                specials.append("[bold blue]Non-Elimination 🛡️[/bold blue]")

            specials_str = ", ".join(specials) if specials else "-"
            perf_table.add_row(str(leg_num), route_str, place_str, specials_str)

        console.print(perf_table)


@show_app.command("racer")
def show_racer(
    racer_query: str = typer.Argument(
        ..., help="Racer full or partial name (e.g. 'Rob Frisbee')"
    ),
    season_num: int | None = typer.Option(
        None, "--season", "-s", help="Filter by specific season"
    ),
    version: str = typer.Option("US", "--version", "-v", help="Franchise version"),
) -> None:
    """Inspect an individual contestant / racer profile."""
    contestants_df = _load_table("contestants")
    if contestants_df.empty:
        console.print(
            "[red]Error: contestants table not found. Run `tar-dataset build` first.[/red]"
        )
        raise typer.Exit(1)

    filtered = contestants_df[
        (contestants_df["version"] == version)
        & contestants_df["name"].str.contains(racer_query, case=False, na=False)
    ]

    if season_num is not None:
        filtered = filtered[filtered["season"] == season_num]

    if filtered.empty:
        console.print(f"[red]No contestants found matching '{racer_query}'.[/red]")
        raise typer.Exit(1)

    teams_df = _load_table("teams")

    for _, c in filtered.iterrows():
        c_season = int(c["season"])
        c_name = c["name"]

        # Find team
        team_str = "Unknown"
        if not teams_df.empty:
            c_first = c_name.split()[0]
            s_teams = teams_df[
                (teams_df["version"] == version) & (teams_df["season"] == c_season)
            ]
            match_tm = s_teams[
                s_teams["team_name"].str.contains(c_first, case=False, na=False)
            ]
            if not match_tm.empty:
                team_str = f"{match_tm.iloc[0]['team_name']} (Place: {match_tm.iloc[0].get('result', 'N/A')})"

        age_val = f"{int(c['age'])}" if pd.notna(c.get("age")) else "N/A"
        racer_text = (
            f"[bold cyan]Contestant ID:[/bold cyan] {c.get('contestant_id', 'N/A')}\n"
            f"[bold cyan]Season:[/bold cyan] Season {c_season} ({version})\n"
            f"[bold cyan]Team:[/bold cyan] {team_str}\n"
            f"[bold]Age:[/bold] {age_val}\n"
            f"[bold]Relationship / Occupation:[/bold] {c.get('relationship', 'N/A')}\n"
            f"[bold]Hometown:[/bold] {c.get('hometown', 'N/A')}\n"
            f"[bold yellow]Finish Status:[/bold yellow] {c.get('status', 'N/A')}"
        )
        console.print(Panel(racer_text, title=f"Racer Profile: {c_name}", expand=False))


@show_app.command("contestant")
def show_contestant(
    racer_query: str = typer.Argument(..., help="Contestant name"),
    season_num: int | None = typer.Option(None, "--season", "-s", help="Season number"),
    version: str = typer.Option("US", "--version", "-v", help="Franchise version"),
) -> None:
    """Alias for `tar-dataset show racer`."""
    show_racer(racer_query=racer_query, season_num=season_num, version=version)


@show_app.command("leg")
def show_leg(
    leg_num: int = typer.Argument(..., help="Leg number"),
    season_num: int = typer.Option(..., "--season", "-s", help="Season number"),
    version: str = typer.Option("US", "--version", "-v", help="Franchise version"),
) -> None:
    """Inspect leg itinerary, challenge descriptions, and tasks."""
    legs_df = _load_table("legs")
    if legs_df.empty:
        console.print("[red]Error: legs table not found.[/red]")
        raise typer.Exit(1)

    l_match = legs_df[
        (legs_df["version"] == version)
        & (legs_df["season"] == season_num)
        & (legs_df["leg_number"] == leg_num)
    ]

    if l_match.empty:
        console.print(
            f"[red]Error: Leg {leg_num} for Season {season_num} not found.[/red]"
        )
        raise typer.Exit(1)

    leg_info = l_match.iloc[0]
    leg_text = (
        f"[bold white]Season {season_num} Leg {leg_num} ({version})[/bold white]\n"
        f"[bold cyan]Route:[/bold cyan] {leg_info.get('route_header', 'Unknown')}\n"
        f"[bold]Itinerary Stops Recorded:[/bold] {leg_info.get('itinerary_stops', 0)}\n\n"
        f"[bold white]Narrative Summary:[/bold white]\n{leg_info.get('narrative', 'N/A')}"
    )
    console.print(
        Panel(
            leg_text,
            title=f"Leg Details: Season {season_num} Leg {leg_num}",
            expand=False,
        )
    )

    # Tasks / Challenges
    tasks_df = _load_table("tasks")
    if not tasks_df.empty:
        leg_tasks = tasks_df[
            (tasks_df["version"] == version)
            & (tasks_df["season"] == season_num)
            & (tasks_df["leg_number"] == leg_num)
        ]
        if not leg_tasks.empty:
            tasks_table = Table(
                title=f"Leg {leg_num} Challenges & Tasks ({len(leg_tasks)} recorded)"
            )
            tasks_table.add_column("Type", style="bold green", no_wrap=True)
            tasks_table.add_column("Description", style="white")

            for _, t in leg_tasks.iterrows():
                tasks_table.add_row(
                    str(t.get("task_type", "Task")), str(t.get("description", ""))
                )
            console.print(tasks_table)


@app.command("predict")
def predict_cmd(
    season: int = typer.Option(
        39, "--season", "-s", help="Season number to predict (e.g. 39)."
    ),
    top: int = typer.Option(10, "--top", "-t", help="Number of top teams to display."),
    detail: bool = typer.Option(
        False, "--detail", "-d", help="Display detailed factor analysis."
    ),
    output_json: Path | None = typer.Option(
        None, "--output", "-o", help="Optional path to export predictions JSON."
    ),
) -> None:
    """Predict winners, finale contenders, and elimination risks using historical empirical data."""
    console.print(
        f"[bold cyan]Running TAR predictive engine for Season {season}...[/bold cyan]"
    )

    predictor = SeasonPredictor()
    try:
        results = predictor.predict_season(season=season)
    except Exception as exc:
        console.print(f"[bold red]Prediction error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    current_leg = results["current_leg"]
    active_count = results["active_teams_count"]
    total_count = results["total_teams"]

    console.print(
        Panel(
            f"[bold white]Season {season} Prediction Model (After Leg {current_leg})[/bold white]\n"
            f"[bold]Active Teams:[/bold] {active_count}/{total_count}  |  "
            f"[bold]Historical Baseline Sample:[/bold] 38 US Seasons (78 winners, 400+ teams)",
            title="The Amazing Race Win & Finale Predictor",
            expand=False,
        )
    )

    table = Table(title=f"Season {season} Contender Rankings (Top {top})")
    table.add_column("Rank", style="bold cyan", justify="right")
    table.add_column("Team", style="bold white")
    table.add_column("Relationship", style="yellow")
    table.add_column("Avg Age", justify="center")
    table.add_column("Avg Place", justify="center")
    table.add_column("Express Pass", justify="center")
    table.add_column("Win Prob", style="bold green", justify="right")
    table.add_column("Finale Prob", style="bold magenta", justify="right")

    rankings = results["rankings"][:top]
    for idx, team in enumerate(rankings, 1):
        if team["is_eliminated"]:
            table.add_row(
                str(idx),
                f"[dim strikethrough]{team['team_name']}[/dim strikethrough]",
                f"[dim]{team['relationship']}[/dim]",
                "-",
                "-",
                "[dim]Eliminated[/dim]",
                "[dim]0.0%[/dim]",
                "[dim]0.0%[/dim]",
            )
        else:
            win_str = f"{team['win_probability']:.1f}%"
            top3_str = f"{team['top3_probability']:.1f}%"
            avg_place_str = (
                f"{team['avg_placement']:.1f}" if team["avg_placement"] else "N/A"
            )
            avg_age_str = f"{team['avg_age']:.0f}" if team["avg_age"] else "N/A"

            ep_status = team["express_pass_status"]
            if ep_status == "Active / Intact":
                ep_display = "[bold green]Held[/bold green]"
            elif ep_status == "Used":
                ep_display = "[yellow]Used[/yellow]"
            else:
                ep_display = "[dim]None[/dim]"

            table.add_row(
                str(idx),
                team["team_name"],
                team["relationship"],
                avg_age_str,
                avg_place_str,
                ep_display,
                win_str,
                top3_str,
            )

    console.print(table)

    if detail:
        console.print(
            "\n[bold cyan]Detailed Team Diagnostics & Analytical Profiles:[/bold cyan]"
        )
        for idx, team in enumerate(rankings, 1):
            if team["is_eliminated"]:
                continue
            console.print(
                f"\n[bold underline]{idx}. {team['team_name']}[/bold underline] ({team['relationship']}, Avg Age {team['avg_age']})"
            )
            if team.get("strengths"):
                for s in team["strengths"]:
                    console.print(f"  [green]+[/green] {s}")
            if team.get("risks"):
                for r in team["risks"]:
                    console.print(f"  [red]-[/red] {r}")

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Saved prediction export to {output_json}[/green]")


@app.command("dashboard")
def dashboard(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run Streamlit on"),
    host: str = typer.Option(
        "localhost", "--host", "-h", help="Host interface to bind"
    ),
    browser: bool = typer.Option(
        True, "--browser/--no-browser", help="Open browser on launch"
    ),
) -> None:
    """Launch interactive web dashboard for race exploration and predictions."""
    import subprocess
    import sys

    try:
        import streamlit  # noqa: F401
    except ImportError:
        console.print(
            "[bold red]Streamlit is not installed.[/bold red]\n"
            "Please install the dashboard dependencies via:\n"
            "  [cyan]uv sync --extra dashboard[/cyan]"
        )
        raise typer.Exit(code=1)

    app_path = Path(__file__).resolve().parent / "dashboard" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.address",
        host,
    ]
    if not browser:
        cmd.extend(["--server.headless", "true"])

    console.print(
        f"[bold green]Starting The Amazing Race Dashboard on http://{host}:{port}...[/bold green]"
    )
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")


if __name__ == "__main__":
    app()
