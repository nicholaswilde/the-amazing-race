"""Tests for Fandom, Reddit, Wikipedia scrapers, and Sheets importer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from tar_dataset.importers.sheets import (
    SheetsImporter,
    google_sheet_to_csv_url,
    google_sheet_to_xlsx_url,
)
from tar_dataset.scrapers.fandom import (
    FandomScraper,
    clean_wikitext,
    compute_roadblock_equity,
)
from tar_dataset.scrapers.reddit import RedditScraper
from tar_dataset.scrapers.wikipedia import WikipediaScraper

# --- Fandom Scraper Tests ---


def test_clean_wikitext():
    assert clean_wikitext("") == ""
    assert clean_wikitext("Hello [[World]]") == "Hello World"
    assert clean_wikitext("Visit [[Paris, France|Paris]] now") == "Visit Paris now"
    assert clean_wikitext("Facts <ref name='test'>Source</ref>") == "Facts"
    assert clean_wikitext("Version {{ver|1.0}} here") == "Version 1.0 here"
    assert (
        clean_wikitext("See {{wp|Amazing Race|The Amazing Race}}")
        == "See The Amazing Race"
    )


def test_fandom_parse_infobox():
    wikitext = """
    {{Season
    | continentsvisited = 4
    | countriesvisited = 9
    | citiesvisited = 24
    | distance = 35,000 mi (56,000 km)
    | startingline = Central Park, NYC
    | finishline = Flushing Meadows Park, NYC
    | filmingdates = March 5 – April 8, 2001
    | airdates = September 5 – December 13, 2001
    | winners = Rob & Brennan
    | runnersup = Frank & Margarita
    }}
    """
    scraper = FandomScraper()
    info = scraper.parse_season_infobox(wikitext)
    assert info["continents_visited"] == 4
    assert info["countries_visited"] == 9
    assert info["cities_visited"] == 24
    assert "35,000" in info["distance_str"]
    assert "Central Park" in info["starting_line"]
    assert "Rob & Brennan" in info["winners"]
    assert "Frank & Margarita" in info["runners_up"]

    # When no template is present
    assert scraper.parse_season_infobox("No infobox here") == {}


def test_fandom_fetch_and_scrape(tmp_path):
    scraper = FandomScraper(raw_dir=tmp_path)

    sample_api_response = {
        "parse": {
            "wikitext": {
                "*": "{{Season\n| continentsvisited = 3\n| winners = Test Winners\n}}"
            }
        }
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = sample_api_response
    mock_resp.raise_for_status.return_value = None

    with patch.object(scraper.client, "get", return_value=mock_resp):
        wt = scraper.fetch_page_wikitext("The_Amazing_Race_1")
        assert wt is not None
        assert "Test Winners" in wt

        data = scraper.scrape_season(1, version="US", save=True)
        assert data["season"] == 1
        assert data["infobox"]["winners"] == "Test Winners"
        assert (tmp_path / "fandom_us_01.json").exists()

    # Test API error response
    mock_err_resp = MagicMock()
    mock_err_resp.json.return_value = {"error": {"code": "missingtitle"}}
    with patch.object(scraper.client, "get", return_value=mock_err_resp):
        assert scraper.fetch_page_wikitext("Nonexistent") is None
        assert scraper.scrape_season(99, save=False) == {}


# --- Sheets Importer Tests ---


def test_google_sheet_url_helpers():
    url = "https://docs.google.com/spreadsheets/d/abc-123_XYZ/edit#gid=456"
    assert (
        google_sheet_to_csv_url(url)
        == "https://docs.google.com/spreadsheets/d/abc-123_XYZ/export?format=csv&gid=456"
    )
    assert (
        google_sheet_to_xlsx_url(url)
        == "https://docs.google.com/spreadsheets/d/abc-123_XYZ/export?format=xlsx"
    )

    with pytest.raises(ValueError, match="Invalid Google Sheets URL"):
        google_sheet_to_csv_url("https://example.com/not-a-sheet")

    with pytest.raises(ValueError, match="Invalid Google Sheets URL"):
        google_sheet_to_xlsx_url("https://example.com/not-a-sheet")


def test_sheets_importer_csv(tmp_path):
    importer = SheetsImporter(raw_dir=tmp_path)

    csv_data = (
        "Team Name,Placement,Legs Won\nRob & Brennan,1,5\nFrank & Margarita,2,2\n"
    )
    mock_resp = MagicMock()
    mock_resp.text = csv_data
    mock_resp.raise_for_status.return_value = None

    with patch.object(importer.client, "get", return_value=mock_resp):
        df = importer.import_public_sheet(
            "https://docs.google.com/spreadsheets/d/test1234/edit",
            name="test_sheet",
            save=True,
        )
        assert len(df) == 2
        assert "team_name" in df.columns
        assert (tmp_path / "test_sheet.csv").exists()


def test_sheets_importer_xlsx(tmp_path):
    importer = SheetsImporter(raw_dir=tmp_path)

    sample_df = pd.DataFrame({"racer": ["Rob", "Brennan"], "age": [27, 29]})
    mock_resp = MagicMock()
    mock_resp.content = b"PK..."
    mock_resp.raise_for_status.return_value = None

    with (
        patch.object(importer.client, "get", return_value=mock_resp),
        patch.object(
            importer, "_parse_and_save_xlsx", return_value=sample_df
        ) as mock_parse,
    ):
        df = importer.import_public_sheet(
            "https://docs.google.com/spreadsheets/d/test_excel/edit",
            name="test_excel",
            prefer_xlsx=True,
            sheet_name="Racers",
            save=True,
        )
        assert len(df) == 2
        assert "racer" in df.columns
        mock_parse.assert_called_once()


def test_sheets_importer_parse_and_save_xlsx_internals(tmp_path):
    importer = SheetsImporter(raw_dir=tmp_path)

    mock_xl = MagicMock()
    mock_xl.sheet_names = ["welcome page", "SQL_Data", "legs"]

    def mock_read_excel(xl, sheet_name=None):
        if sheet_name == "SQL_Data":
            return pd.DataFrame({"Col A": [1, 2]})
        return pd.DataFrame({"Leg": [1, 2]})

    with (
        patch("pandas.ExcelFile", return_value=mock_xl),
        patch("pandas.read_excel", side_effect=mock_read_excel),
    ):
        df = importer._parse_and_save_xlsx(
            content=b"fake_bytes", name="test_workbook", sheet_name=None, save=True
        )
        assert "col_a" in df.columns
        assert (tmp_path / "test_workbook.xlsx").exists()
        assert (tmp_path / "test_workbook.csv").exists()
        assert (tmp_path / "test_workbook_legs.csv").exists()


def test_sheets_importer_http_400_fallback(tmp_path):
    import httpx

    importer = SheetsImporter(raw_dir=tmp_path)
    sample_df = pd.DataFrame({"col": [1]})

    mock_400_resp = MagicMock()
    mock_400_resp.status_code = 400
    mock_err = httpx.HTTPStatusError(
        "400 error", request=MagicMock(), response=mock_400_resp
    )

    mock_xlsx_resp = MagicMock()
    mock_xlsx_resp.content = b"fake_bytes"
    mock_xlsx_resp.raise_for_status.return_value = None

    def mock_get(url):
        if "format=csv" in url:
            raise mock_err
        return mock_xlsx_resp

    with (
        patch.object(importer.client, "get", side_effect=mock_get),
        patch.object(
            importer, "_parse_and_save_xlsx", return_value=sample_df
        ) as mock_parse,
    ):
        df = importer.import_public_sheet(
            "https://docs.google.com/spreadsheets/d/test_fallback/edit",
            name="fallback_sheet",
            save=False,
        )
        assert len(df) == 1
        mock_parse.assert_called_once()


def test_sheets_importer_public_sheet_csv_wrapper(tmp_path):
    importer = SheetsImporter(raw_dir=tmp_path)
    sample_df = pd.DataFrame({"col": [1]})

    with patch.object(
        importer, "import_public_sheet", return_value=sample_df
    ) as mock_import:
        # Pass ID only
        df1 = importer.import_public_sheet_csv("1BxiMVs...", name="test1")
        assert len(df1) == 1
        assert "spreadsheets/d/1BxiMVs" in mock_import.call_args[0][0]

        # Pass direct CSV URL
        df2 = importer.import_public_sheet(
            "https://example.com/raw.csv", name="test2", save=False
        )
        assert len(df2) == 1


def test_sheets_importer_local_csv(tmp_path):
    importer = SheetsImporter(raw_dir=tmp_path)
    csv_file = tmp_path / "local.csv"
    csv_file.write_text("Column A,Column B\n1,2\n3,4\n", encoding="utf-8")

    df = importer.import_local_csv(csv_file, name="imported_local")
    assert len(df) == 2
    assert "column_a" in df.columns
    assert (tmp_path / "imported_local.csv").exists()

    with pytest.raises(FileNotFoundError):
        importer.import_local_csv(tmp_path / "nonexistent.csv")


# --- Reddit Scraper Tests ---


def test_reddit_scraper_flow(tmp_path):
    scraper = RedditScraper(raw_dir=tmp_path)

    # Classifications
    assert (
        scraper.classify_thread_type("Episode 1 Discussion Thread")
        == "episode_discussion"
    )
    assert (
        scraper.classify_thread_type("Live Discussion TAR S36E01") == "live_discussion"
    )
    assert (
        scraper.classify_thread_type("Post-Episode Discussion: Season 36 Leg 1")
        == "post_episode"
    )
    assert scraper.classify_thread_type("I am Colin Guinn, AMA!") == "ama"
    assert scraper.classify_thread_type("Random thought about the show") == "general"

    # Search submissions with mocked response
    mock_posts = [
        {
            "id": "post123",
            "title": "The Amazing Race S35E01 - Episode Discussion",
            "selftext": "Welcome to season 35!",
            "author": "TARMod",
            "score": 100,
            "num_comments": 2,
            "created_utc": 1695860000,
            "permalink": "/r/TheAmazingRace/comments/post123",
        }
    ]
    mock_comments = [
        {
            "id": "c1",
            "author": "fan1",
            "body": "Great premiere!",
            "score": 15,
            "created_utc": 1695860100,
        },
        {
            "id": "c2",
            "author": "AutoModerator",
            "body": "Reminder of rules",
            "score": 1,
            "created_utc": 1695860101,
        },
        {
            "id": "c3",
            "author": "[deleted]",
            "body": "[deleted]",
            "score": 0,
            "created_utc": 1695860102,
        },
    ]

    def mock_get(url, params=None):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "submission" in url:
            resp.json.return_value = {"data": mock_posts}
        elif "comment" in url:
            resp.json.return_value = {"data": mock_comments}
        else:
            resp.json.return_value = {"data": []}
        return resp

    with patch.object(scraper.client, "get", side_effect=mock_get):
        discussions = scraper.scrape_discussions(
            query="Episode Discussion", limit=1, fetch_comments=True, save=True
        )
        assert len(discussions) == 1
        disc = discussions[0]
        assert disc.post_id == "post123"
        assert disc.season == 35
        assert disc.episode == 1
        # AutoModerator and deleted comments should be filtered out
        assert len(disc.comments) == 1
        assert disc.comments[0]["body"] == "Great premiere!"

        # Test scrape_all_categories
        all_cats = scraper.scrape_all_categories(
            limits={"episode_discussion": 1}, fetch_comments=False
        )
        assert len(all_cats) >= 1

        # Test load_cached_discussions
        cached = scraper.load_cached_discussions()
        assert len(cached) >= 1


# --- Wikipedia Scraper Extended Tests ---


def test_wikipedia_episodes_and_legs_parsing():
    scraper = WikipediaScraper()

    html_episodes = """
    <table class="wikitable">
      <tr><th>No. overall</th><th>No. in season</th><th>Title</th><th>Original air date</th><th>U.S. viewers (millions)</th></tr>
      <tr><td>1</td><td>1</td><td>"The Race Begins"</td><td>September 5, 2001</td><td>11.83</td></tr>
      <tr><td>2</td><td>2</td><td>"Divide and Conquer"</td><td>September 19, 2001</td><td>8.60</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_episodes, "html.parser")
    episodes = scraper.parse_episodes_table(soup.find("table"))
    assert len(episodes) == 2
    assert episodes[0]["episode"] == 1
    assert episodes[0]["title"] == "The Race Begins"
    assert episodes[0]["air_date"] == "September 5, 2001"
    assert episodes[0]["viewers_millions"] == 11.83

    html_legs = """
    <div>
      <div class="mw-heading mw-heading3">
        <h3>Leg 1 (United States → South Africa)</h3>
      </div>
      <p>Teams departed Central Park in New York City and flew to Johannesburg, South Africa.</p>
      <ul>
        <li>Detour: In <b>Physics</b>, teams solved a puzzle. In <b>Chemistry</b>, teams mixed compounds.</li>
        <li>Roadblock: One team member had to bungee jump off the bridge.</li>
      </ul>
      <div class="mw-heading mw-heading3">
        <h3>Leg 2 (South Africa → France)</h3>
      </div>
      <p>Teams flew from Johannesburg to Paris, France.</p>
    </div>
    """
    soup_legs = BeautifulSoup(html_legs, "html.parser")
    legs = scraper.parse_legs_summary(soup_legs)
    assert len(legs) == 2
    assert legs[0]["leg_number"] == 1
    assert "South Africa" in legs[0]["route_header"]
    assert len(legs[0]["tasks"]) >= 2
    assert legs[0]["tasks"][0]["task_type"] == "Detour"
    assert legs[0]["tasks"][1]["task_type"] == "Roadblock"


def test_compute_roadblock_equity():
    assert compute_roadblock_equity(None) is None
    assert compute_roadblock_equity("") is None
    assert compute_roadblock_equity("not-a-split") is None
    assert compute_roadblock_equity("0-0") is None
    assert compute_roadblock_equity("6-6") == 1.0
    assert compute_roadblock_equity("7-5") == 0.83
    assert compute_roadblock_equity("3-3-3-3") == 1.0
    assert compute_roadblock_equity("0-0-0-0") is None
    # 4 person with variance
    assert isinstance(compute_roadblock_equity("4-4-2-2"), float)


def test_fandom_scrape_all(tmp_path):
    scraper = FandomScraper(raw_dir=tmp_path)
    with patch.object(
        scraper, "scrape_season", side_effect=[{"season": 1}, None]
    ) as mock_s:
        res = scraper.scrape_all(start=1, end=2)
        assert len(res) == 1
        assert res[0]["season"] == 1
        assert mock_s.call_count == 2


def test_fandom_scrape_roadblocks(tmp_path):
    scraper = FandomScraper(raw_dir=tmp_path)

    template_wt = """
    | 0101 = [[The_Amazing_Race_1/Episode_1]]
    """
    season_wt = """
    ==Leaderboard==
    {| class="wikitable"
    |-
    | [[Rob & Brennan]] || 6-6
    |}
    """
    ep_wt = """
    * [[Rob & Brennan|Rob & <u>Brennan</u>]]
    """

    async def mock_get(url, params=None, timeout=None):
        page = params.get("page", "") if params else ""
        resp = MagicMock()
        if page == "Template:Ep":
            resp.json.return_value = {"parse": {"wikitext": {"*": template_wt}}}
        elif "The_Amazing_Race_1" in page and "Episode" not in page:
            resp.json.return_value = {"parse": {"wikitext": {"*": season_wt}}}
        elif "Episode_1" in page:
            resp.json.return_value = {"parse": {"wikitext": {"*": ep_wt}}}
        else:
            resp.json.return_value = {}
        return resp

    mock_client = MagicMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        res = scraper.scrape_roadblocks(start=1, end=1, save=True)
        assert "team_splits" in res
        assert "leg_performers" in res
        assert (tmp_path / "roadblocks_master.json").exists()


def test_wikipedia_fetch_page_html_errors():
    scraper = WikipediaScraper()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "Missing page"}
    mock_resp.raise_for_status.return_value = None

    with patch.object(scraper.client, "get", return_value=mock_resp):
        assert scraper.fetch_page_html("Missing_Page") is None

    with patch.object(scraper.client, "get", side_effect=Exception("Network error")):
        assert scraper.fetch_page_html("Error_Page") is None


def test_wikipedia_scrape_all_episodes():
    scraper = WikipediaScraper()
    html_page = """
    <div>
      <h2>Season 1</h2>
      <table class="wikiepisodetable">
        <tr class="vevent">
          <td>1</td><td>1</td><td>"The Race Begins"</td><td>2001-09-05</td><td>11.83</td>
        </tr>
      </table>
    </div>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html_page

    with patch.object(scraper.client, "get", return_value=mock_resp):
        episodes = scraper.scrape_all_episodes()
        assert "1_1" in episodes
        assert episodes["1_1"]["title"] == "The Race Begins"
        assert episodes["1_1"]["viewers_millions"] == 11.83


def test_wikipedia_leg_narratives_extended():
    scraper = WikipediaScraper()
    html_legs = """
    <div>
      <div class="mw-heading mw-heading3">
        <h3>Leg 1 (USA → France)</h3>
      </div>
      <p>Teams departed New York and flew to Paris.</p>
      <ul>
        <li>Fast Forward: Teams had to find a hidden key.</li>
        <li>Speed Bump: A team had to wash dirty cars.</li>
        <li>Teams must drive across the desert to reach the pit stop before sundown.</li>
        <li>Short note</li>
      </ul>
    </div>
    """
    soup = BeautifulSoup(html_legs, "html.parser")
    legs = scraper.parse_legs_summary(soup)
    assert len(legs) == 1
    task_types = [t["task_type"] for t in legs[0]["tasks"]]
    assert "Fast Forward" in task_types
    assert "Speed Bump" in task_types
    assert len(legs[0]["itinerary"]) >= 1


def test_wikipedia_get_latest_revision():
    scraper = WikipediaScraper()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "revisions": [
                        {
                            "revid": 999999,
                            "parentid": 888888,
                            "timestamp": "2026-10-01T12:00:00Z",
                        }
                    ],
                }
            }
        }
    }
    mock_resp.raise_for_status.return_value = None

    with patch.object(scraper.client, "get", return_value=mock_resp):
        rev = scraper.get_latest_revision(1, version="US")
        assert rev is not None
        assert rev["revid"] == 999999
        assert rev["timestamp"] == "2026-10-01T12:00:00Z"

    # Test missing page
    mock_resp.json.return_value = {"query": {"pages": {"-1": {"missing": ""}}}}
    with patch.object(scraper.client, "get", return_value=mock_resp):
        assert scraper.get_latest_revision(999, version="US") is None


def test_wikipedia_scrape_season_revision_caching(tmp_path):
    import json

    scraper = WikipediaScraper(raw_dir=tmp_path)
    cached_file = tmp_path / "season_us_01.json"
    cached_file.write_text(
        json.dumps({"season": 1, "wiki_revid": 12345, "cached": True}),
        encoding="utf-8",
    )

    # 1. Unchanged revision -> should return cached data without fetching HTML
    with (
        patch.object(
            scraper,
            "get_latest_revision",
            return_value={"revid": 12345, "timestamp": "2026-10-01T00:00:00Z"},
        ),
        patch.object(scraper, "fetch_page_html") as mock_fetch,
    ):
        res = scraper.scrape_season(1, version="US")
        assert res.get("cached") is True
        mock_fetch.assert_not_called()

    # 2. Changed revision -> should fetch HTML and update revid
    sample_html = """
    <div>
      <table class="infobox"><tr><th>Winners</th><td>Test Winners</td></tr></table>
    </div>
    """
    with (
        patch.object(
            scraper,
            "get_latest_revision",
            return_value={"revid": 67890, "timestamp": "2026-10-02T00:00:00Z"},
        ),
        patch.object(scraper, "fetch_page_html", return_value=sample_html),
    ):
        res = scraper.scrape_season(1, version="US")
        assert res.get("wiki_revid") == 67890
        assert res.get("wiki_timestamp") == "2026-10-02T00:00:00Z"

    # 3. Force flag -> should fetch HTML even if revid matches
    with (
        patch.object(
            scraper,
            "get_latest_revision",
            return_value={"revid": 67890, "timestamp": "2026-10-02T00:00:00Z"},
        ),
        patch.object(
            scraper, "fetch_page_html", return_value=sample_html
        ) as mock_fetch,
    ):
        res = scraper.scrape_season(1, version="US", force=True)
        assert res.get("wiki_revid") == 67890
        mock_fetch.assert_called_once()
