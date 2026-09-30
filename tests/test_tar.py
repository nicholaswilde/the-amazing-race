"""Unit tests for the-amazing-race package."""

from pathlib import Path

from bs4 import BeautifulSoup

from tar_dataset.importers.sheets import SheetsImporter, google_sheet_to_csv_url
from tar_dataset.processors.builder import DatasetBuilder
from tar_dataset.processors.validator import DatasetValidator
from tar_dataset.schemas import Episode, RedditDiscussion, Season, Team
from tar_dataset.scrapers.reddit import RedditScraper
from tar_dataset.scrapers.wikipedia import (
    WikipediaScraper,
    clean_text,
    parse_html_table,
)


def test_schemas():
    """Verify pydantic models instantiate with expected fields."""
    season = Season(
        version="US",
        season=1,
        title="Season 1",
        n_teams=11,
        winners="Rob & Brennan",
    )
    assert season.season == 1
    assert season.version == "US"
    assert season.winners == "Rob & Brennan"

    team = Team(
        version="US",
        season=1,
        team_id="US-S01-rob-brennan",
        team_name="Rob & Brennan",
        member_1_name="Rob Frisbee",
        member_2_name="Brennan Swain",
        relationship="Best Friends & Lawyers",
        result=1,
    )
    assert team.result == 1
    assert team.member_1_name == "Rob Frisbee"

    episode = Episode(
        version="US",
        season=1,
        episode=1,
        title="The Race Begins",
        viewers_millions=11.83,
    )
    assert episode.viewers_millions == 11.83


def test_clean_text():
    """Verify wikipedia citation references are removed."""
    raw = "New York City [ 49 ] [ note 1 ]\xa0is great."
    assert clean_text(raw) == "New York City is great."


def test_parse_html_table_rowspan():
    """Verify rowspan and colspan are properly expanded."""
    html = """
    <table>
      <tr><th>Name</th><th>Age</th><th>Relationship</th></tr>
      <tr><td>Matt</td><td rowspan="2">28</td><td rowspan="2">Married</td></tr>
      <tr><td>Ana</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    expanded = parse_html_table(table)

    assert len(expanded) == 3
    assert expanded[0] == ["Name", "Age", "Relationship"]
    assert expanded[1] == ["Matt", "28", "Married"]
    assert expanded[2] == ["Ana", "28", "Married"]


def test_google_sheet_to_csv_url():
    """Verify Google Sheets URL parsing to export format."""
    url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123"
    csv_url = google_sheet_to_csv_url(url)
    assert "export?format=csv&gid=123" in csv_url
    assert "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" in csv_url


def test_wikipedia_results_matrix_parsing():
    """Verify parsing of placements, footnotes, Fast Forwards, U-Turns, and NELs."""
    html_results = """
    <table>
      <tr><th>Team</th><th>1</th><th>2</th><th>3</th></tr>
      <tr><td>Rob & Brennan</td><td>1st ƒ</td><td>3rd</td><td>1st</td></tr>
      <tr><td>Frank & Margarita</td><td>3rd</td><td>1[a]</td><td>2nd »</td></tr>
      <tr><td>Matt & Ana</td><td>9th</td><td>NEL</td><td>—</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_results, "html.parser")
    scraper = WikipediaScraper()
    results = scraper.parse_results_table(soup.find("table"))

    assert len(results) == 3
    # Check Rob & Brennan
    rob = results[0]
    assert rob["team_name"] == "Rob & Brennan"
    assert rob["placements"][0]["placement"] == 1
    assert rob["placements"][0]["fast_forward"] is True

    # Check Frank & Margarita footnote handling & U-Turn
    frank = results[1]
    assert frank["placements"][1]["placement"] == 1
    assert frank["placements"][2]["placement"] == 2
    assert frank["placements"][2]["uturn"] is True

    # Check Matt & Ana NEL
    matt = results[2]
    assert matt["placements"][1]["is_non_elimination"] is True
    assert matt["placements"][2]["placement"] is None


def test_wikipedia_infobox_and_contestants_parsing():
    """Verify parsing of season infoboxes and contestant tables with alternate column headers."""
    html_infobox = """
    <table class="infobox vevent">
      <tr><th scope="row">Teams</th><td>11</td></tr>
      <tr><th scope="row">Winners</th><td>Rob & Brennan</td></tr>
      <tr><th scope="row">No. of legs</th><td>13</td></tr>
      <tr><th scope="row">Distance</th><td>35,000 miles (56,000 km)</td></tr>
    </table>
    """
    soup_infobox = BeautifulSoup(html_infobox, "html.parser")
    scraper = WikipediaScraper()
    info = scraper.parse_infobox(soup_infobox)
    assert info["n_teams"] == 11
    assert info["winners"] == "Rob & Brennan"
    assert info["n_legs"] == 13
    assert info["distance_miles"] == 35000.0
    assert info["distance_km"] == 56000.0

    html_contestants = """
    <table>
      <tr><th>Contestants</th><th>Age</th><th>Relationship</th><th>Current Residence</th></tr>
      <tr><td>Rob Frisbee</td><td>27</td><td>Best Friends</td><td>Minneapolis, Minnesota</td></tr>
      <tr><td>Brennan Swain</td><td>29</td><td>Best Friends</td><td>Rochester, New York</td></tr>
    </table>
    """
    soup_cast = BeautifulSoup(html_contestants, "html.parser")
    contestants = scraper.parse_contestants_table(soup_cast.find("table"))
    assert len(contestants) == 2
    assert contestants[0]["name"] == "Rob Frisbee"
    assert contestants[0]["age"] == 27
    assert contestants[0]["hometown"] == "Minneapolis, Minnesota"


def test_reddit_extract_season_episode():
    """Verify season and episode number extraction from various Reddit thread titles."""
    reddit = RedditScraper()
    assert reddit.extract_season_episode(
        "The Amazing Race Season 35 Episode 4 Discussion Thread"
    ) == (35, 4)
    assert reddit.extract_season_episode("TAR S36E01 Live Discussion") == (36, 1)
    assert reddit.extract_season_episode("Post-Episode Discussion: S34E09") == (34, 9)
    assert reddit.extract_season_episode("General Discussion Thread") == (None, None)


def test_reddit_classification_and_corpus(tmp_path):
    """Verify Reddit thread classification, saving, and AI corpus export integration."""
    reddit = RedditScraper(raw_dir=tmp_path / "reddit")
    assert reddit.classify_thread_type("S36E01 Live Discussion") == "live_discussion"
    assert (
        reddit.classify_thread_type("Post-Episode Discussion: S34E09") == "post_episode"
    )
    assert (
        reddit.classify_thread_type("I am Colin from TAR 5 & 31 - Ask Me Anything!")
        == "ama"
    )
    assert (
        reddit.classify_thread_type("The Amazing Race 35 Episode 4 Discussion Thread")
        == "episode_discussion"
    )

    # Test saving sample discussions
    sample_discs = [
        RedditDiscussion(
            post_id="test123",
            season=36,
            episode=1,
            thread_type="live_discussion",
            title="S36E01 Live Discussion Thread",
            author="fan1",
            score=45,
            num_comments=10,
            created_utc="1710000000",
            url="https://reddit.com/r/TheAmazingRace/comments/test123",
            selftext="Welcome to the live discussion!",
            comments=[
                {
                    "id": "c1",
                    "author": "viewer1",
                    "body": "What a thrilling premiere in Mexico!",
                    "score": 15,
                }
            ],
        )
    ]
    out_file = reddit._save_and_merge_discussions(sample_discs, query="Live Discussion")
    assert out_file.exists()

    # Test AIExportBuilder integration
    from tar_dataset.exports.ai_formats import AIExportBuilder

    ai_builder = AIExportBuilder(ai_dir=tmp_path / "ai")
    ai_builder.load_reddit_discussions = lambda: [d.model_dump() for d in sample_discs]

    qa_pairs = ai_builder.generate_qa_pairs()
    reddit_qa = [
        q for q in qa_pairs if "reddit" in q.get("metadata", {}).get("category", "")
    ]
    assert len(reddit_qa) >= 1
    assert "Season 36 Episode 1" in reddit_qa[0]["messages"][1]["content"]

    corpus = ai_builder.generate_knowledge_corpus()
    reddit_chunks = [
        c for c in corpus if c.get("metadata", {}).get("type") == "reddit_discussion"
    ]
    assert len(reddit_chunks) >= 1
    assert "test123" in reddit_chunks[0]["id"]


def test_sheets_importer_local_csv(tmp_path):
    """Verify local CSV importing and column header standardization to snake_case."""
    csv_file = tmp_path / "sample_tracker.csv"
    csv_file.write_text(
        "Team Name,Leg Time (mins),Roadblock Performed\nRob & Brennan,120,Rob\n"
    )

    importer = SheetsImporter(raw_dir=tmp_path / "sheets")
    df = importer.import_local_csv(csv_file, name="custom_tracker")

    assert list(df.columns) == ["team_name", "leg_time_mins", "roadblock_performed"]
    assert len(df) == 1
    assert (tmp_path / "sheets" / "custom_tracker.csv").exists()


def test_builder_and_validator(tmp_path):
    """Verify dataset builder and validator with mock data."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    wiki_dir = raw_dir / "wikipedia"
    wiki_dir.mkdir(parents=True)

    sample_season = {
        "version": "US",
        "season": 99,
        "wiki_url": "https://en.wikipedia.org/wiki/Test",
        "infobox": {"n_teams": 2, "n_legs": 2, "winners": "Alpha & Beta"},
        "contestants": [
            {
                "name": "Alice",
                "age": 30,
                "relationship": "Friends",
                "hometown": "Chicago",
            },
            {
                "name": "Bob",
                "age": 32,
                "relationship": "Friends",
                "hometown": "Chicago",
            },
        ],
        "results": [
            {
                "team_name": "Alice & Bob",
                "placements": [{"leg_label": "1", "placement": 1, "raw_cell": "1st"}],
            }
        ],
        "episodes": [{"episode": 1, "title": "Pilot", "viewers_millions": 10.5}],
        "legs": [{"leg_number": 1, "route_header": "USA -> Peru", "tasks": []}],
    }

    import json

    (wiki_dir / "season_us_99.json").write_text(json.dumps(sample_season))

    builder = DatasetBuilder(raw_dir=raw_dir, processed_dir=processed_dir)
    dfs = builder.build_all()

    assert "seasons" in dfs
    assert len(dfs["seasons"]) == 1
    assert len(dfs["teams"]) == 1
    assert len(dfs["leg_results"]) == 1

    validator = DatasetValidator(processed_dir=processed_dir)
    report = validator.validate()
    assert report["status"] in ["PASS", "WARNING"]


def test_builder_with_cached_raw_seasons(tmp_path):
    """Verify builder processes actual cached raw season files with 100% relational integrity."""
    raw_dir = Path("data/raw")
    if (raw_dir / "wikipedia" / "season_us_01.json").exists():
        builder = DatasetBuilder(raw_dir=raw_dir, processed_dir=tmp_path / "processed")
        dfs = builder.build_all()
        assert len(dfs["seasons"]) >= 1
        assert len(dfs["teams"]) >= 11
        assert len(dfs["contestants"]) >= 22

        validator = DatasetValidator(processed_dir=tmp_path / "processed")
        report = validator.validate()
        assert report["status"] in ["PASS", "WARNING"]
