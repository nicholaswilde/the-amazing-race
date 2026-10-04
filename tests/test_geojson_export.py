"""Tests for geocoding lookup and GeoJSON route exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from tar_dataset.cli import app
from tar_dataset.exports.geojson_export import GeoJsonExporter, export_to_geojson
from tar_dataset.processors.geocoding import (
    ensure_legs_geocoded,
    fetch_online_coordinates,
    get_city_coordinates,
    load_geocoding_cache,
    update_geocoding_cache,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_data_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create sample processed parquet files for testing GeoJSON export."""
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    seasons_df = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "n_teams": 11,
                "n_legs": 3,
                "n_episodes": 3,
                "winners": "Rob & Brennan",
                "distance_miles": 35000.0,
                "distance_km": 56000.0,
            }
        ]
    )
    legs_df = pd.DataFrame(
        [
            {
                "version": "US",
                "season": 1,
                "leg_number": 1,
                "route_header": "United States → Zambia",
                "origin_country": "USA",
                "destination_country": "ZMB",
                "destination_city": "Livingstone",
                "destination_continent": "Africa",
                "destination_lat": -17.8531,
                "destination_lon": 25.8614,
                "itinerary_stops": 5,
                "tasks_count": 3,
                "narrative": "Teams raced across Livingstone.",
            },
            {
                "version": "US",
                "season": 1,
                "leg_number": 2,
                "route_header": "Zambia → France",
                "origin_country": "ZMB",
                "destination_country": "FRA",
                "destination_city": "Paris",
                "destination_continent": "Europe",
                "destination_lat": 48.8567,
                "destination_lon": 2.3522,
                "itinerary_stops": 6,
                "tasks_count": 4,
                "narrative": "Teams flew to Paris.",
            },
            {
                "version": "US",
                "season": 1,
                "leg_number": 3,
                "route_header": "France → Tunisia",
                "origin_country": "FRA",
                "destination_country": "TUN",
                "destination_city": "El Djem",
                "destination_continent": "Africa",
                "destination_lat": 35.3219,
                "destination_lon": 10.6834,
                "itinerary_stops": 4,
                "tasks_count": 2,
                "narrative": "Teams visited the amphitheatre in El Djem.",
            },
        ]
    )

    seasons_df.to_parquet(proc_dir / "seasons.parquet")
    legs_df.to_parquet(proc_dir / "legs.parquet")

    output_file = tmp_path / "tar_routes.geojson"
    return proc_dir, output_file


def test_geocoding_lookup_basic() -> None:
    """Test get_city_coordinates with various cities and overrides."""
    # Direct city + country lookup
    paris = get_city_coordinates("Paris", "FRA")
    assert paris is not None
    assert abs(paris[0] - 48.8567) < 0.1
    assert abs(paris[1] - 2.3522) < 0.1

    # Override resolution for greeters
    sydney = get_city_coordinates("Graham Keating", "AUS", season=2, leg_number=8)
    assert sydney is not None
    assert sydney[0] < 0  # Southern hemisphere

    # Unknown city returns None
    assert get_city_coordinates("NonExistentCity12345", "XYZ") is None
    assert get_city_coordinates(None) is None


def test_geojson_export_basic(sample_data_dirs: tuple[Path, Path]) -> None:
    """Test building and writing GeoJSON FeatureCollection."""
    proc_dir, output_file = sample_data_dirs
    exporter = GeoJsonExporter(processed_dir=proc_dir, output_file=output_file)
    exported_path = exporter.export()

    assert exported_path.exists()
    assert exported_path == output_file

    doc = json.loads(output_file.read_text(encoding="utf-8"))
    assert doc["type"] == "FeatureCollection"
    assert "name" in doc
    assert "features" in doc

    features = doc["features"]
    # 3 waypoints + 1 season route LineString = 4 features
    assert len(features) == 4

    routes = [f for f in features if f["properties"]["feature_type"] == "route"]
    waypoints = [f for f in features if f["properties"]["feature_type"] == "waypoint"]

    assert len(routes) == 1
    assert len(waypoints) == 3

    # Validate LineString geometry and coordinate order [lon, lat]
    route = routes[0]
    assert route["geometry"]["type"] == "LineString"
    coords = route["geometry"]["coordinates"]
    assert len(coords) == 3
    # Check [lon, lat] format
    for lon, lat in coords:
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0

    assert route["properties"]["season"] == 1
    assert route["properties"]["winners"] == "Rob & Brennan"
    assert "Livingstone" in route["properties"]["destinations"]

    # Validate Point waypoints
    for wp in waypoints:
        assert wp["geometry"]["type"] == "Point"
        lon, lat = wp["geometry"]["coordinates"]
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0
        assert wp["properties"]["season"] == 1
        assert wp["properties"]["leg_number"] in [1, 2, 3]


def test_geojson_export_filters(sample_data_dirs: tuple[Path, Path]) -> None:
    """Test include_routes and include_waypoints flags."""
    proc_dir, output_file = sample_data_dirs

    # Routes only
    export_to_geojson(
        processed_dir=proc_dir,
        output_file=output_file,
        include_routes=True,
        include_waypoints=False,
    )
    doc_routes = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(doc_routes["features"]) == 1
    assert doc_routes["features"][0]["geometry"]["type"] == "LineString"

    # Waypoints only
    export_to_geojson(
        processed_dir=proc_dir,
        output_file=output_file,
        include_routes=False,
        include_waypoints=True,
    )
    doc_wp = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(doc_wp["features"]) == 3
    for f in doc_wp["features"]:
        assert f["geometry"]["type"] == "Point"


def test_cli_export_geojson(
    cli_runner: CliRunner, sample_data_dirs: tuple[Path, Path]
) -> None:
    """Test running tar-dataset export-geojson through Typer CLI."""
    proc_dir, output_file = sample_data_dirs

    result = cli_runner.invoke(
        app,
        [
            "export-geojson",
            "--processed-dir",
            str(proc_dir),
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "Exported GeoJSON dataset" in result.stdout
    assert output_file.exists()


def test_dynamic_geocoding_cache(tmp_path: Path) -> None:
    """Test manual and dynamic cache updates and disk persistence."""
    cache_file = tmp_path / "geocoding_cache.json"

    # Pre-condition: cache empty on new file
    cache = load_geocoding_cache(cache_file)
    assert isinstance(cache, dict)

    # Update cache
    update_geocoding_cache("Kyoto", "JPN", 35.0116, 135.7681, cache_file=cache_file)
    assert cache_file.exists()

    # Verify retrieval
    coords = get_city_coordinates(
        "Kyoto", "JPN", allow_network=False, cache_file=cache_file
    )
    assert coords == (35.0116, 135.7681)

    # Verify case-insensitive match
    coords_lower = get_city_coordinates(
        "kyoto", "jpn", allow_network=False, cache_file=cache_file
    )
    assert coords_lower == (35.0116, 135.7681)


def test_fetch_online_coordinates_nominatim(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test online fetching via Nominatim response."""

    class FakeResponse:
        status_code = 200

        def json(self) -> list[dict]:
            return [{"lat": "35.011636", "lon": "135.768029"}]

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get(self, url: str, **kwargs) -> FakeResponse:
            return FakeResponse()

        def close(self) -> None:
            pass

    import httpx

    monkeypatch.setattr(httpx, "Client", FakeClient)

    coords = fetch_online_coordinates("Kyoto", "JPN")
    assert coords == (35.0116, 135.768)


def test_fetch_online_coordinates_wikipedia_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test online fetching falling back to Wikipedia search."""

    class FakeResponse:
        def __init__(self, url: str) -> None:
            self.url = url
            self.status_code = 200

        def json(self) -> dict | list:
            if "nominatim" in self.url:
                return []  # Nominatim returns no results
            return {
                "query": {
                    "pages": {
                        "123": {
                            "title": "Kyoto",
                            "coordinates": [{"lat": 35.0116, "lon": 135.7681}],
                        }
                    }
                }
            }

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get(self, url: str, **kwargs) -> FakeResponse:
            return FakeResponse(url)

        def close(self) -> None:
            pass

    import httpx

    monkeypatch.setattr(httpx, "Client", FakeClient)

    coords = fetch_online_coordinates("Kyoto", "JPN")
    assert coords == (35.0116, 135.7681)


def test_ensure_legs_geocoded_dataframe(tmp_path: Path) -> None:
    """Test ensure_legs_geocoded with DataFrame."""
    cache_file = tmp_path / "geocoding_cache.json"
    df = pd.DataFrame(
        [
            {"destination_city": "Paris", "destination_country": "FRA"},
            {"destination_city": "Livingstone", "destination_country": "ZMB"},
            {"destination_city": "UnknownCity", "destination_country": "USA"},
        ]
    )
    # With network disallowed, existing static coordinates are matched without errors
    count = ensure_legs_geocoded(df, allow_network=False, cache_file=cache_file)
    assert count == 0  # Paris and Livingstone are in static CITY_COORDINATES


def test_ensure_legs_geocoded_dict_list(tmp_path: Path) -> None:
    """Test ensure_legs_geocoded with raw scraped leg dicts."""
    cache_file = tmp_path / "geocoding_cache.json"
    raw_legs = [
        {"route_header": "United States → France, Paris", "itinerary": []},
        {"destination_city": "Sydney", "destination_country": "AUS"},
    ]
    count = ensure_legs_geocoded(raw_legs, allow_network=False, cache_file=cache_file)
    assert count == 0  # Both already in static dictionary
