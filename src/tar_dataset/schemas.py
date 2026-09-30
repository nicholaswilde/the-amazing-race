"""Pydantic schemas and models for The Amazing Race dataset.

Follows tidy data principles inspired by doehm/alone, expanded for TV game show mechanics
and AI training.
"""

from typing import Any

from pydantic import BaseModel, Field


class Season(BaseModel):
    """Season level metadata and statistics."""

    version: str = Field(
        default="US", description="Franchise country code (US, CAN, AUS, etc.)"
    )
    season: int = Field(description="Season number")
    title: str | None = Field(
        default=None, description="Subtitle or theme (e.g. Unfinished Business)"
    )
    filming_start: str | None = Field(default=None, description="Filming start date")
    filming_end: str | None = Field(default=None, description="Filming end date")
    air_date_start: str | None = Field(
        default=None, description="Season premiere air date"
    )
    air_date_end: str | None = Field(default=None, description="Season finale air date")
    continents_visited: int | None = Field(
        default=None, description="Total continents visited"
    )
    countries_visited: int | None = Field(
        default=None, description="Total countries visited"
    )
    cities_visited: int | None = Field(default=None, description="Total cities visited")
    distance_miles: float | None = Field(
        default=None, description="Total race distance in miles"
    )
    distance_km: float | None = Field(
        default=None, description="Total race distance in km"
    )
    n_teams: int = Field(default=11, description="Number of teams competing")
    n_legs: int | None = Field(default=None, description="Number of legs")
    winners: str | None = Field(default=None, description="Winning team names")
    starting_line: str | None = Field(
        default=None, description="Starting line location"
    )
    finish_line: str | None = Field(default=None, description="Finish line location")
    wiki_url: str | None = Field(
        default=None, description="Wikipedia or Fandom page URL"
    )


class Episode(BaseModel):
    """Episode metadata, viewership ratings, and broadcast information."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    episode: int = Field(description="Episode number within season")
    episode_overall: int | None = Field(
        default=None, description="Episode count across entire franchise"
    )
    title: str = Field(description="Episode title (often a racer quote)")
    air_date: str | None = Field(
        default=None, description="Original broadcast air date"
    )
    viewers_millions: float | None = Field(
        default=None, description="US television viewers in millions"
    )
    imdb_rating: float | None = Field(default=None, description="IMDb user rating")
    synopsis: str | None = Field(
        default=None, description="Narrative recap or episode summary"
    )


class Contestant(BaseModel):
    """Individual racer demographics and profile."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    contestant_id: str = Field(description="Unique racer ID (e.g. US-S01-01)")
    team_id: str = Field(description="Team ID association")
    name: str = Field(description="Full name of racer")
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    age: int | None = Field(default=None, description="Age during race")
    gender: str | None = Field(default=None, description="Gender (M/F/Non-binary)")
    occupation: str | None = Field(default=None, description="Profession or job")
    hometown: str | None = Field(default=None, description="Hometown city/state")


class Team(BaseModel):
    """Team details, member pairing, relationships, and season outcome."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    team_id: str = Field(description="Unique team slug or ID")
    team_name: str = Field(description="Common team reference (e.g. Rob & Brennan)")
    member_1_name: str
    member_2_name: str | None = None
    member_3_name: str | None = None  # Season 8 Family Edition (4 members)
    member_4_name: str | None = None
    relationship: str | None = Field(
        default=None,
        description="Relationship category (Married, Siblings, Dating, etc.)",
    )
    result: int | None = Field(
        default=None, description="Final finishing position: 1 = Winner"
    )
    status: str | None = Field(
        default=None, description="Final standing (Winners, Runners-up, Eliminated)"
    )
    legs_completed: int | None = Field(
        default=None, description="Number of legs completed"
    )
    legs_won: int | None = Field(
        default=0, description="Number of 1st place leg finishes"
    )
    eliminated_leg: int | None = Field(
        default=None, description="Leg number eliminated on"
    )


class Leg(BaseModel):
    """Leg itinerary, destinations, twists, and challenges."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    leg_number: int = Field(description="Leg number")
    episode: int | None = Field(
        default=None, description="Episode number corresponding to leg"
    )
    origin_city: str | None = None
    origin_country: str | None = None
    destination_city: str | None = None
    destination_country: str | None = None
    pit_stop_location: str | None = None
    leg_type: str = Field(
        default="Standard",
        description="Standard, Non-Elimination, Superleg, Keep Racing, Finale",
    )
    has_detour: bool = Field(default=False)
    has_roadblock: bool = Field(default=False)
    has_fast_forward: bool = Field(default=False)
    has_yield: bool = Field(default=False)
    has_uturn: bool = Field(default=False)
    has_speed_bump: bool = Field(default=False)
    has_hazard: bool = Field(default=False)
    summary: str | None = Field(
        default=None, description="Textual narrative of leg route and drama"
    )


class LegResult(BaseModel):
    """Placement, status, and performance of each team in a specific leg."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    leg_number: int = Field(description="Leg number")
    team_id: str = Field(description="Team ID")
    placement: int = Field(description="Leg finish position")
    status: str = Field(
        default="Finished",
        description="Finished, Eliminated, NEL_Saved, KeepRacing, Disqualified",
    )
    roadblock_performer: str | None = Field(
        default=None, description="Racer who performed the roadblock"
    )
    notes: str | None = Field(
        default=None, description="Penalties, speed bump, powers used, or flight drama"
    )


class Task(BaseModel):
    """Detailed challenges (Detours, Roadblocks, Route Info, Fast Forwards)."""

    version: str = Field(default="US")
    season: int = Field(description="Season number")
    leg_number: int = Field(description="Leg number")
    task_type: str = Field(
        description="Detour, Roadblock, Fast Forward, Route Info, Speed Bump, Hazard"
    )
    task_name: str | None = None
    location: str | None = None
    description: str = Field(
        description="Full text description of challenge requirements"
    )
    detour_option_a: str | None = None
    detour_option_b: str | None = None


class RedditDiscussion(BaseModel):
    """Reddit episode and season discussion threads from r/TheAmazingRace."""

    post_id: str
    season: int | None = None
    episode: int | None = None
    thread_type: str | None = Field(
        default="episode_discussion",
        description="Category: episode_discussion, live_discussion, post_episode, ama, general",
    )
    title: str
    author: str
    score: int
    num_comments: int
    created_utc: str
    url: str
    selftext: str | None = None
    comments: list[dict[str, Any]] = Field(default_factory=list)
