"""Unit tests for the-amazing-race package."""

from bs4 import BeautifulSoup

from tar_dataset.importers.sheets import google_sheet_to_csv_url
from tar_dataset.processors.builder import DatasetBuilder
from tar_dataset.processors.validator import DatasetValidator
from tar_dataset.schemas import Episode, Season, Team
from tar_dataset.scrapers.wikipedia import clean_text, parse_html_table


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
            {"name": "Alice", "age": 30, "relationship": "Friends", "hometown": "Chicago"},
            {"name": "Bob", "age": 32, "relationship": "Friends", "hometown": "Chicago"},
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
