"""GeoJSON export module for The Amazing Race race routes and leg waypoints."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class GeoJsonExporter:
    """Exports race routes and pit stop waypoints to standard GeoJSON."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        output_file: Path | str = "data/processed/tar_routes.geojson",
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.output_file = Path(output_file)

    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load legs and seasons dataframes."""
        legs_file = self.processed_dir / "legs.parquet"
        if not legs_file.exists():
            legs_file = self.processed_dir / "legs.csv"

        seasons_file = self.processed_dir / "seasons.parquet"
        if not seasons_file.exists():
            seasons_file = self.processed_dir / "seasons.csv"

        if not legs_file.exists():
            raise FileNotFoundError(f"Legs dataset not found in {self.processed_dir}")
        if not seasons_file.exists():
            raise FileNotFoundError(
                f"Seasons dataset not found in {self.processed_dir}"
            )

        legs_df = (
            pd.read_parquet(legs_file)
            if legs_file.suffix == ".parquet"
            else pd.read_csv(legs_file)
        )
        seasons_df = (
            pd.read_parquet(seasons_file)
            if seasons_file.suffix == ".parquet"
            else pd.read_csv(seasons_file)
        )

        return legs_df, seasons_df

    def build_features(
        self,
        legs_df: pd.DataFrame,
        seasons_df: pd.DataFrame,
        include_routes: bool = True,
        include_waypoints: bool = True,
    ) -> list[dict[str, Any]]:
        """Construct GeoJSON features for season route LineStrings and leg Point waypoints."""
        features: list[dict[str, Any]] = []

        seasons_meta = {}
        for _, s_row in seasons_df.iterrows():
            seasons_meta[(s_row["version"], int(s_row["season"]))] = s_row.to_dict()

        # Group legs by version and season
        grouped = legs_df.groupby(["version", "season"])

        for (version, season), group in sorted(
            grouped, key=lambda x: (x[0][0], x[0][1])
        ):
            sorted_legs = group.sort_values("leg_number")
            meta = seasons_meta.get((version, int(season)), {})

            line_coords: list[list[float]] = []
            dest_names: list[str] = []
            dest_countries: list[str] = []
            dest_continents: list[str] = []

            for _, leg in sorted_legs.iterrows():
                lat = leg.get("destination_lat")
                lon = leg.get("destination_lon")

                if pd.notna(lat) and pd.notna(lon):
                    coord = [round(float(lon), 4), round(float(lat), 4)]
                    line_coords.append(coord)

                    city = str(leg.get("destination_city") or "")
                    country = str(leg.get("destination_country") or "")
                    continent = str(leg.get("destination_continent") or "")

                    dest_names.append(city)
                    if country and country not in dest_countries:
                        dest_countries.append(country)
                    if continent and continent not in dest_continents:
                        dest_continents.append(continent)

                    # Point feature for waypoint / pit stop
                    if include_waypoints:
                        pt_feature: dict[str, Any] = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": coord,
                            },
                            "properties": {
                                "feature_type": "waypoint",
                                "version": version,
                                "season": int(season),
                                "leg_number": int(leg["leg_number"]),
                                "city": city,
                                "country": country,
                                "continent": continent,
                                "route_header": str(leg.get("route_header") or ""),
                                "itinerary_stops": int(leg.get("itinerary_stops", 0)),
                                "tasks_count": int(leg.get("tasks_count", 0)),
                            },
                        }
                        features.append(pt_feature)

            # LineString feature for season route
            if include_routes and len(line_coords) >= 2:
                route_summary = " → ".join(
                    f"{c} ({iso})"
                    for c, iso in zip(dest_names, sorted_legs["destination_country"])
                )
                line_feature: dict[str, Any] = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": line_coords,
                    },
                    "properties": {
                        "feature_type": "route",
                        "version": version,
                        "season": int(season),
                        "n_legs": len(sorted_legs),
                        "destinations": dest_names,
                        "countries": dest_countries,
                        "continents": dest_continents,
                        "route_summary": route_summary,
                        "distance_miles": float(meta.get("distance_miles", 0.0))
                        if pd.notna(meta.get("distance_miles"))
                        else None,
                        "distance_km": float(meta.get("distance_km", 0.0))
                        if pd.notna(meta.get("distance_km"))
                        else None,
                        "winners": str(meta.get("winners") or ""),
                    },
                }
                features.append(line_feature)

        return features

    def export(
        self,
        include_routes: bool = True,
        include_waypoints: bool = True,
    ) -> Path:
        """Export GeoJSON FeatureCollection to file."""
        legs_df, seasons_df = self.load_data()
        features = self.build_features(
            legs_df,
            seasons_df,
            include_routes=include_routes,
            include_waypoints=include_waypoints,
        )

        geojson_doc = {
            "type": "FeatureCollection",
            "name": "the_amazing_race_routes",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84",
                },
            },
            "features": features,
        }

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(
            json.dumps(geojson_doc, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(
            "Exported %d GeoJSON features to %s",
            len(features),
            self.output_file,
        )
        return self.output_file


def export_to_geojson(
    processed_dir: Path | str = "data/processed",
    output_file: Path | str = "data/processed/tar_routes.geojson",
    include_routes: bool = True,
    include_waypoints: bool = True,
) -> Path:
    """Convenience function to export race routes to GeoJSON."""
    exporter = GeoJsonExporter(processed_dir=processed_dir, output_file=output_file)
    return exporter.export(
        include_routes=include_routes, include_waypoints=include_waypoints
    )
