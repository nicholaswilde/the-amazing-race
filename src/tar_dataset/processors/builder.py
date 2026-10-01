"""Processes raw scraped data into tidy relational datasets (alone-style) and Parquet/CSV formats."""

from __future__ import annotations

import json
import logging
import re
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert string to URL-safe alphanumeric slug."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


# Known demographic details for withdrawn/returned contestants in Season 33
KNOWN_S33_CONTESTANTS: dict[str, dict[str, Any]] = {
    "Michael Norwood": {
        "age": 36,
        "relationship": "Singing Police Officers",
        "hometown": "Buffalo, New York",
    },
    "Moe Badger": {
        "age": 42,
        "relationship": "Singing Police Officers",
        "hometown": "Buffalo, New York",
    },
    "Arun Kumar": {
        "age": 56,
        "relationship": "Father & Daughter",
        "hometown": "Detroit, Michigan",
    },
    "Natalia Kumar": {
        "age": 28,
        "relationship": "Father & Daughter",
        "hometown": "Detroit, Michigan",
    },
    "Anthony Sadler": {
        "age": 29,
        "relationship": "Childhood Friends",
        "hometown": "Sacramento, California",
    },
    "Spencer Stone": {
        "age": 29,
        "relationship": "Childhood Friends",
        "hometown": "Sacramento, California",
    },
    "Connie Greiner": {
        "age": 37,
        "relationship": "Married",
        "hometown": "Newport News, Virginia",
    },
    "Sam Greiner": {
        "age": 39,
        "relationship": "Married",
        "hometown": "Charlotte, North Carolina",
    },
}


# Canonical overrides for racer names where Wikipedia common names diverge from legal names
KNOWN_CONTESTANT_GENDERS: dict[tuple[int, str], str] = {
    (2, "Deidre Washington"): "F",
    (6, "Don St. Claire"): "M",
    (7, "Ron Young, Jr."): "M",
    (8, "Billy Gaghan, Jr."): "M",
    (8, "Rolly Weaver IV"): "M",
    (20, "Dave Brown, Jr."): "M",
    (27, "Jin Lao Greer"): "M",
    (30, "Tim Janus"): "M",
    (32, "Hung Nguyen"): "F",
    (32, "Chee Lee"): "M",
    (34, 'Latrice "Lumumba" Roberts'): "M",
    (34, 'Madison "Mattie" Lynch'): "F",
}

# Season 39 (in-progress) racer demographics
KNOWN_S39_GENDERS: dict[str, str] = {
    "Zach Johnson": "M",
    "Nate Johnson": "M",
    "Ali Krieger": "F",
    "Joanna Lohman": "F",
    "Ann-Marie Tejcek": "F",
    "Riley Tejcek": "F",
    "Anuar Tager": "M",
    "Andrea Tager Ballesca": "F",
    "Cody Langlois": "M",
    "Jaime Tribo": "F",
    "Conner Wilson": "M",
    "Garrett McGuire": "M",
    "Dafina Dunmore": "F",
    "Saran Dunmore": "F",
    "Daisha Wilks": "F",
    "Dalton Hamby": "M",
    "Doug Matter": "M",
    "Dylan Matter": "M",
    "Erin Taylor": "F",
    "Javi Vintimilla": "M",
    "Jody Rebhun": "F",
    "Jenn Naso": "F",
    "Katie Schultz": "F",
    "Charlotte Schultz": "F",
    "Michelle Rozalski Patterson": "F",
    "Matthew Patterson": "M",
}

KNOWN_TEAM_GENDER_COMPS: dict[tuple[int, str], str] = {
    (2, "Deidre & Hillary"): "FF",
}

KNOWN_S39_TEAM_COMPS: dict[str, str] = {
    "Zach & Nate": "MM",
    "Ali & Joanna": "FF",
    "Ann-Marie & Riley": "FF",
    "Anuar & Andrea": "MF",
    "Cody & Jaime": "MF",
    "Conner & Garrett": "MM",
    "Dafina & Saran": "FF",
    "Daisha & Dalton": "MF",
    "Doug & Dylan": "MM",
    "Erin & Javi": "MF",
    "Jody & Jenn": "FF",
    "Katie & Charlotte": "FF",
    "Michelle & Matthew": "MF",
}


def _clean_name(n: str) -> str:
    n = re.sub(r'".*?"', "", str(n))
    n = re.sub(r"\(.*?\)", "", n)
    n = re.sub(r"Big Brother.*", "", n, flags=re.IGNORECASE)
    n = re.sub(r"The Amazing Race.*", "", n, flags=re.IGNORECASE)
    n = re.sub(r"Survivor.*", "", n, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]", "", n.lower())


def _clean_with_nickname(n: str) -> str:
    match = re.search(r'"(.*?)"', str(n))
    nick = match.group(1) if match else ""
    parts = str(n).split()
    last = parts[-1] if parts else ""
    return re.sub(r"[^a-z0-9]", "", f"{nick} {last}".lower())


def _clean_team(n: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(n).lower())


US_STATES: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "D.C.": "DC",
    "District of Columbia": "DC",
    "Washington, D.C.": "DC",
}

COUNTRY_INFO: dict[str, tuple[str, str]] = {
    "Argentina": ("ARG", "South America"),
    "Armenia": ("ARM", "Asia"),
    "Australia": ("AUS", "Oceania"),
    "Austria": ("AUT", "Europe"),
    "Azerbaijan": ("AZE", "Asia"),
    "Bahrain": ("BHR", "Asia"),
    "Bangladesh": ("BGD", "Asia"),
    "Barbados": ("BRB", "North America"),
    "Belgium": ("BEL", "Europe"),
    "Bolivia": ("BOL", "South America"),
    "Botswana": ("BWA", "Africa"),
    "Brazil": ("BRA", "South America"),
    "Bulgaria": ("BGR", "Europe"),
    "Burkina Faso": ("BFA", "Africa"),
    "Cambodia": ("KHM", "Asia"),
    "Canada": ("CAN", "North America"),
    "Chile": ("CHL", "South America"),
    "China": ("CHN", "Asia"),
    "Colombia": ("COL", "South America"),
    "Costa Rica": ("CRI", "North America"),
    "Croatia": ("HRV", "Europe"),
    "Czech Republic": ("CZE", "Europe"),
    "Czechia": ("CZE", "Europe"),
    "Denmark": ("DNK", "Europe"),
    "Denmark & Sweden": ("SWE", "Europe"),
    "Dominican Republic": ("DOM", "North America"),
    "Ecuador": ("ECU", "South America"),
    "Egypt": ("EGY", "Africa"),
    "England": ("GBR", "Europe"),
    "England & Wales": ("GBR", "Europe"),
    "Estonia": ("EST", "Europe"),
    "Ethiopia": ("ETH", "Africa"),
    "Finland": ("FIN", "Europe"),
    "France": ("FRA", "Europe"),
    "France & Monaco": ("FRA", "Europe"),
    "French Polynesia": ("PYF", "Oceania"),
    "Georgia": ("GEO", "Asia"),
    "Germany": ("DEU", "Europe"),
    "Germany & Austria": ("DEU", "Europe"),
    "Ghana": ("GHA", "Africa"),
    "Greece": ("GRC", "Europe"),
    "Guam": ("GUM", "Oceania"),
    "Hong Kong": ("HKG", "Asia"),
    "Hungary": ("HUN", "Europe"),
    "Iceland": ("ISL", "Europe"),
    "India": ("IND", "Asia"),
    "Indonesia": ("IDN", "Asia"),
    "Ireland": ("IRL", "Europe"),
    "Italy": ("ITA", "Europe"),
    "Jamaica": ("JAM", "North America"),
    "Japan": ("JPN", "Asia"),
    "Jordan": ("JOR", "Asia"),
    "Kazakhstan": ("KAZ", "Asia"),
    "Kenya": ("KEN", "Africa"),
    "Kuwait": ("KWT", "Asia"),
    "Laos": ("LAO", "Asia"),
    "Liechtenstein": ("LIE", "Europe"),
    "Lithuania": ("LTU", "Europe"),
    "Macau": ("MAC", "Asia"),
    "Madagascar": ("MDG", "Africa"),
    "Malawi": ("MWI", "Africa"),
    "Malaysia": ("MYS", "Asia"),
    "Malta": ("MLT", "Europe"),
    "Mauritius": ("MUS", "Africa"),
    "Mexico": ("MEX", "North America"),
    "Monaco": ("MCO", "Europe"),
    "Mongolia": ("MNG", "Asia"),
    "Morocco": ("MAR", "Africa"),
    "Mozambique": ("MOZ", "Africa"),
    "Namibia": ("NAM", "Africa"),
    "Netherlands": ("NLD", "Europe"),
    "New Zealand": ("NZL", "Oceania"),
    "Northern Ireland": ("GBR", "Europe"),
    "Norway": ("NOR", "Europe"),
    "Oman": ("OMN", "Asia"),
    "Panama": ("PAN", "North America"),
    "Paraguay": ("PRY", "South America"),
    "Peru": ("PER", "South America"),
    "Philippines": ("PHL", "Asia"),
    "Poland": ("POL", "Europe"),
    "Portugal": ("PRT", "Europe"),
    "Puerto Rico": ("PRI", "North America"),
    "Romania": ("ROU", "Europe"),
    "Russia": ("RUS", "Europe"),
    "Scotland": ("GBR", "Europe"),
    "Senegal": ("SEN", "Africa"),
    "Seychelles": ("SYC", "Africa"),
    "Singapore": ("SGP", "Asia"),
    "Slovenia": ("SVN", "Europe"),
    "South Africa": ("ZAF", "Africa"),
    "South Korea": ("KOR", "Asia"),
    "Spain": ("ESP", "Europe"),
    "Sri Lanka": ("LKA", "Asia"),
    "Sweden": ("SWE", "Europe"),
    "Switzerland": ("CHE", "Europe"),
    "Taiwan": ("TWN", "Asia"),
    "Tanzania": ("TZA", "Africa"),
    "Thailand": ("THA", "Asia"),
    "Trinidad and Tobago": ("TTO", "North America"),
    "Tunisia": ("TUN", "Africa"),
    "Turkey": ("TUR", "Europe"),
    "U.S. Virgin Islands": ("VIR", "North America"),
    "Uganda": ("UGA", "Africa"),
    "Ukraine": ("UKR", "Europe"),
    "United Arab Emirates": ("ARE", "Asia"),
    "United Kingdom": ("GBR", "Europe"),
    "United States": ("USA", "North America"),
    "USA": ("USA", "North America"),
    "Uruguay": ("URY", "South America"),
    "Vietnam": ("VNM", "Asia"),
    "Wales": ("GBR", "Europe"),
    "Zambia": ("ZMB", "Africa"),
    "Zimbabwe": ("ZWE", "Africa"),
}

for _state, _code in US_STATES.items():
    COUNTRY_INFO[_state] = ("USA", "North America")
    COUNTRY_INFO[_code] = ("USA", "North America")
COUNTRY_INFO["Pennsylvania & New Jersey"] = ("USA", "North America")

# Reverse lookup for ISO codes
for _k, _v in list(COUNTRY_INFO.items()):
    _iso, _cont = _v
    if _iso not in COUNTRY_INFO:
        COUNTRY_INFO[_iso] = (_iso, _cont)


def resolve_country_and_continent(name: str | None) -> tuple[str | None, str | None]:
    """Resolve country name, state, or ISO code to (ISO-3, continent)."""
    if not name:
        return None, None
    clean = name.strip()
    if clean in COUNTRY_INFO:
        return COUNTRY_INFO[clean]
    if "," in clean:
        cand = clean.rsplit(",", 1)[1].strip()
        if cand in COUNTRY_INFO:
            return COUNTRY_INFO[cand]
    return None, None


def extract_city_from_itinerary(itinerary: list[Any] | None) -> str | None:
    """Extract destination city from leg itinerary stops (pit stop / final route stop)."""
    if not itinerary:
        return None
    for it in reversed(itinerary):
        it_str = str(it).strip()
        if len(it_str) > 100:
            continue
        if any(
            it_str.startswith(x)
            for x in (
                "Episode",
                "Eliminated:",
                "Prize:",
                "Winners:",
                "Runners-up:",
                "Teams ",
                "Due to",
            )
        ):
            continue
        # City, Country or City, State
        m = re.match(r"^([^,()]+?),\s*([^()]+)", it_str)
        if m:
            c = m.group(1).strip()
            if not any(
                w in c.lower()
                for w in ("this was", "leg", "episode", "teams", "due to", "note")
            ):
                return c
        # City (Location)
        m = re.match(r"^([^()]+?)\s*\(", it_str)
        if m:
            c = m.group(1).strip()
            if not any(
                w in c.lower()
                for w in ("this was", "leg", "episode", "teams", "due to", "note")
            ):
                return c
    return None


def parse_route_header(
    route_header: str | None, itinerary: list[Any] | None = None
) -> tuple[str | None, str | None, str | None, str | None]:
    """Parse route_header and itinerary into (origin_country, destination_country, destination_city, destination_continent)."""
    if not route_header:
        city = extract_city_from_itinerary(itinerary)
        return None, None, city, None

    parts = [p.strip() for p in re.split(r"→|->", route_header) if p.strip()]
    if not parts:
        city = extract_city_from_itinerary(itinerary)
        return None, None, city, None

    orig_part = parts[0]
    dest_part = parts[-1]

    orig_iso, _ = resolve_country_and_continent(orig_part)
    city = None

    if "," in dest_part:
        city_cand, country_cand = dest_part.rsplit(",", 1)
        city = city_cand.strip()
        dest_iso, dest_cont = resolve_country_and_continent(country_cand)
    else:
        dest_iso, dest_cont = resolve_country_and_continent(dest_part)

    if not city:
        city = extract_city_from_itinerary(itinerary)

    return orig_iso, dest_iso, city, dest_cont


def parse_hometown(hometown: str | None) -> tuple[str | None, str | None]:
    """Parse hometown string into (hometown_state, hometown_country)."""
    if not hometown or pd.isna(hometown):
        return None, None
    h_str = str(hometown).strip()
    if not h_str:
        return None, None
    parts = [p.strip() for p in h_str.split(",")]
    if len(parts) >= 2:
        state_candidate = parts[-1]
        if state_candidate in US_STATES:
            return US_STATES[state_candidate], "USA"
        if state_candidate in US_STATES.values():
            return state_candidate, "USA"
        iso, _ = resolve_country_and_continent(state_candidate)
        if iso:
            return None, iso
        return state_candidate, "USA"
    elif len(parts) == 1:
        if parts[0] in US_STATES:
            return US_STATES[parts[0]], "USA"
        if parts[0] in US_STATES.values():
            return parts[0], "USA"
        iso, _ = resolve_country_and_continent(parts[0])
        if iso:
            return None, iso
        return None, "USA"
    return None, None


class DatasetBuilder:
    """Compiles raw Wikipedia, Fandom, and Reddit files into clean tidy datasets."""

    def __init__(
        self,
        raw_dir: Path | str = "data/raw",
        processed_dir: Path | str = "data/processed",
        include_in_progress: bool = False,
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.include_in_progress = include_in_progress
        self._contestant_gender_lookup: dict[tuple[int, str], str] = {}
        self._team_comp_lookup: dict[tuple[int, str], str] = {}
        self._season_contestants_df: pd.DataFrame | None = None
        self._season_teams_df: pd.DataFrame | None = None
        self._roadblock_splits: dict[tuple[str, int, str], dict[str, Any]] = {}
        self._roadblock_leg_performers: dict[tuple[int, int, str], str] = {}
        self._roadblock_leg_tasks: dict[tuple[int, int], list[str]] = {}
        self._roadblock_contestant_counts: dict[tuple[int, str], int] = {}
        self._load_gender_lookups()
        self._load_roadblock_lookups()

    def _load_roadblock_lookups(self) -> None:
        """Load Fandom master roadblocks dataset."""
        rb_path = self.raw_dir / "fandom" / "roadblocks_master.json"
        if not rb_path.exists():
            rb_path = Path("data/raw/fandom/roadblocks_master.json")
        if not rb_path.exists():
            return
        try:
            data = json.loads(rb_path.read_text(encoding="utf-8"))
            for key, val in data.get("team_splits", {}).items():
                parts = key.split("_", 2)
                if len(parts) == 3:
                    ver, s_str, team = parts
                    s = int(s_str)
                    self._roadblock_splits[(ver, s, team)] = val
                    self._roadblock_splits[(ver, s, _clean_team(team))] = val

            for key, val in data.get("leg_performers", {}).items():
                parts = key.split("_", 2)
                if len(parts) == 3:
                    s_str, leg_str, team = parts
                    self._roadblock_leg_performers[(int(s_str), int(leg_str), team)] = (
                        val
                    )

            for key, val in data.get("leg_task_performers", {}).items():
                parts = key.split("_", 1)
                if len(parts) == 2:
                    self._roadblock_leg_tasks[(int(parts[0]), int(parts[1]))] = val

            for key, val in data.get("contestant_counts", {}).items():
                parts = key.split("_", 1)
                if len(parts) == 2:
                    self._roadblock_contestant_counts[(int(parts[0]), parts[1])] = val
        except Exception as e:
            logger.debug("Could not load roadblocks_master.json: %s", e)

    def resolve_team_roadblock_split(
        self, version: str, season: int, team_name: str
    ) -> tuple[str | None, float | None]:
        """Resolve team roadblock split and equity score."""
        ct = _clean_team(re.sub(r'".*?"', "", str(team_name)))
        ct_norm = ct.replace("ronald", "ron")

        for cand in [team_name, ct, ct_norm]:
            if (version, season, cand) in self._roadblock_splits:
                d = self._roadblock_splits[(version, season, cand)]
                return d.get("split"), d.get("equity_score")

        for (v, s, cand_t), d in self._roadblock_splits.items():
            if (
                v == version
                and s == season
                and (ct in cand_t or cand_t in ct or ct_norm in cand_t)
            ):
                return d.get("split"), d.get("equity_score")

        return None, None

    def resolve_leg_roadblock_performer(
        self, season: int, leg_number: int, team_name: str
    ) -> str | None:
        """Resolve racer who completed the Roadblock for a specific team on a leg."""
        ct = _clean_team(re.sub(r'".*?"', "", str(team_name)))
        ct_norm = ct.replace("ronald", "ron")

        for cand in [ct, ct_norm]:
            if (season, leg_number, cand) in self._roadblock_leg_performers:
                return self._roadblock_leg_performers[(season, leg_number, cand)]

        for (s, leg, cand_t), perf in self._roadblock_leg_performers.items():
            if (
                s == season
                and leg == leg_number
                and (ct in cand_t or cand_t in ct or ct_norm in cand_t)
            ):
                return perf

        return None

    def resolve_contestant_roadblocks(
        self,
        season: int,
        name: str,
        group_names: list[str],
        member_idx: int,
        results: list[dict[str, Any]],
        version: str = "US",
    ) -> int:
        """Resolve roadblocks completed by a contestant."""
        cn = _clean_name(name)
        first = name.split()[0].lower() if name else ""
        c_nick = _clean_with_nickname(name)

        matched_split: list[int] | None = None
        for r in results:
            t_name = r.get("team_name", "")
            if season == 8:
                fam = t_name.replace(" Family", "").lower()
                if any(fam in gn.lower() for gn in group_names):
                    sp_str, _ = self.resolve_team_roadblock_split(
                        version, season, t_name
                    )
                    if sp_str:
                        matched_split = [int(x) for x in sp_str.split("-")]
                        break
            else:
                parts = [p.strip().lower() for p in t_name.split("&")]
                if len(parts) == 2:
                    first_names = [gn.split()[0].lower() for gn in group_names if gn]
                    nick_names = [
                        _clean_with_nickname(gn).split()[0]
                        for gn in group_names
                        if _clean_with_nickname(gn)
                    ]
                    all_cand = set(first_names + nick_names)
                    if "flight time" in t_name.lower():
                        all_cand.add("flight time")
                    if "big easy" in t_name.lower():
                        all_cand.add("big easy")

                    p0_match = any(
                        parts[0] == c or parts[0] in c or c in parts[0]
                        for c in all_cand
                    )
                    p1_match = any(
                        parts[1] == c or parts[1] in c or c in parts[1]
                        for c in all_cand
                    )

                    if p0_match and p1_match:
                        sp_str, _ = self.resolve_team_roadblock_split(
                            version, season, t_name
                        )
                        if sp_str:
                            matched_split = [int(x) for x in sp_str.split("-")]
                            break

        if matched_split and member_idx < len(matched_split):
            return matched_split[member_idx]

        for cand in [cn, first, c_nick]:
            if (season, cand) in self._roadblock_contestant_counts:
                return self._roadblock_contestant_counts[(season, cand)]

        return 0

    def _load_gender_lookups(self) -> None:
        """Load placement database sheets to build gender and team composition lookup indices."""
        sheets_dir = self.raw_dir / "sheets"
        if not (sheets_dir / "placement_database_seasoncontestants.csv").exists():
            sheets_dir = Path("data/raw/sheets")

        c_file = sheets_dir / "placement_database_seasoncontestants.csv"
        if c_file.exists():
            try:
                sc = pd.read_csv(c_file)
                usa_sc = sc[sc["season"].str.startswith("USA")].copy()
                usa_sc["season_num"] = (
                    usa_sc["season"].str.replace("USA", "").astype(int)
                )
                self._season_contestants_df = usa_sc

                for _, r in usa_sc.iterrows():
                    s = r["season_num"]
                    g = (
                        "M"
                        if r["gender"] == "Male"
                        else ("F" if r["gender"] == "Female" else str(r["gender"]))
                    )
                    self._contestant_gender_lookup[(s, r["name"])] = g
                    self._contestant_gender_lookup[(s, _clean_name(r["name"]))] = g
                    if pd.notna(r.get("short_name")):
                        parts = str(r["name"]).split()
                        last = parts[-1] if parts else ""
                        self._contestant_gender_lookup[
                            (s, _clean_name(f"{r['short_name']} {last}"))
                        ] = g
            except Exception as e:
                logger.debug(
                    "Could not load placement_database_seasoncontestants.csv: %s", e
                )

        t_file = sheets_dir / "placement_database_seasonteams.csv"
        if t_file.exists():
            try:
                st = pd.read_csv(t_file)
                usa_st = st[st["season"].str.startswith("USA")].copy()
                usa_st["season_num"] = (
                    usa_st["season"].str.replace("USA", "").astype(int)
                )
                class_map = {"All-Male": "MM", "All-Female": "FF", "Co-Ed": "MF"}
                usa_st["gender_comp"] = usa_st["class"].map(class_map)
                self._season_teams_df = usa_st

                for _, r in usa_st.iterrows():
                    s = r["season_num"]
                    comp = r["gender_comp"]
                    if pd.notna(comp):
                        self._team_comp_lookup[(s, _clean_team(r["names"]))] = str(comp)
            except Exception as e:
                logger.debug("Could not load placement_database_seasonteams.csv: %s", e)

    def resolve_contestant_gender(
        self,
        season: int,
        name: str,
        rel: str | None = None,
        raw_gender: str | None = None,
    ) -> str:
        """Resolve contestant gender to 'M', 'F', or 'NB'."""
        if raw_gender and str(raw_gender).strip():
            rg = str(raw_gender).strip().upper()
            if rg in ("M", "MALE"):
                return "M"
            if rg in ("F", "FEMALE"):
                return "F"
            if rg in ("NB", "NON-BINARY", "NONBINARY"):
                return "NB"

        if (season, name) in KNOWN_CONTESTANT_GENDERS:
            return KNOWN_CONTESTANT_GENDERS[(season, name)]

        if season == 39 and name in KNOWN_S39_GENDERS:
            return KNOWN_S39_GENDERS[name]

        if (season, name) in self._contestant_gender_lookup:
            return self._contestant_gender_lookup[(season, name)]

        cn = _clean_name(name)
        if (season, cn) in self._contestant_gender_lookup:
            return self._contestant_gender_lookup[(season, cn)]

        c_nick = _clean_with_nickname(name)
        if (season, c_nick) in self._contestant_gender_lookup:
            return self._contestant_gender_lookup[(season, c_nick)]

        if self._season_contestants_df is not None:
            s_sc = self._season_contestants_df[
                self._season_contestants_df["season_num"] == season
            ]
            for _, r in s_sc.iterrows():
                rcn = _clean_name(r["name"])
                if cn and rcn and (cn in rcn or rcn in cn):
                    return "M" if r["gender"] == "Male" else "F"

        if rel:
            rl = rel.lower()
            if (
                "brother" in rl
                or "father" in rl
                or "dad" in rl
                or "son" in rl
                or "husband" in rl
            ):
                return "M"
            if (
                "sister" in rl
                or "mother" in rl
                or "mom" in rl
                or "daughter" in rl
                or "wife" in rl
            ):
                return "F"

        first = name.split()[0].lower() if name else ""
        if first in (
            "alice",
            "mary",
            "emily",
            "leslie",
            "brenda",
            "amie",
            "margaretta",
        ):
            return "F"
        return "M"

    def resolve_team_gender_comp(
        self,
        season: int,
        team_name: str,
        member_genders: list[str] | None = None,
    ) -> str:
        """Resolve team gender composition to 'MM', 'FF', or 'MF'."""
        if (season, team_name) in KNOWN_TEAM_GENDER_COMPS:
            return KNOWN_TEAM_GENDER_COMPS[(season, team_name)]

        if season == 39 and team_name in KNOWN_S39_TEAM_COMPS:
            return KNOWN_S39_TEAM_COMPS[team_name]

        ct = _clean_team(team_name)
        if (season, ct) in self._team_comp_lookup:
            return self._team_comp_lookup[(season, ct)]

        if self._season_teams_df is not None:
            s_teams = self._season_teams_df[
                self._season_teams_df["season_num"] == season
            ]
            for _, tr in s_teams.iterrows():
                ctr = _clean_team(tr["names"])
                if ct in ctr or ctr in ct:
                    val = tr["gender_comp"]
                    if pd.notna(val):
                        return str(val)

        if member_genders:
            valid = [g for g in member_genders if g in ("M", "F", "NB")]
            if valid:
                if all(g == "M" for g in valid):
                    return "MM"
                if all(g == "F" for g in valid):
                    return "FF"
                return "MF"

        return "MF"

    def load_wikipedia_seasons(self) -> list[dict[str, Any]]:
        """Load all raw Wikipedia season files."""
        wiki_dir = self.raw_dir / "wikipedia"
        if not wiki_dir.exists():
            return []

        seasons = []
        for file in sorted(wiki_dir.glob("season_*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                # Filter out in-progress seasons (where winners are not yet decided)
                # unless explicitly requested, so official tidy datasets remain complete
                if not self.include_in_progress:
                    info = data.get("infobox", {})
                    winners = info.get("winners")
                    if not winners or "TBD" in str(winners):
                        logger.info(
                            "Skipping in-progress Season %s from official tidy build (winners pending)",
                            data.get("season"),
                        )
                        continue
                seasons.append(data)
            except Exception as e:
                logger.error("Failed to load %s: %s", file, e)
        return seasons

    def build_seasons_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create seasons summary dataframe."""
        cols = [
            "version",
            "season",
            "n_teams",
            "n_legs",
            "n_episodes",
            "winners",
            "distance_miles",
            "distance_km",
            "air_dates",
            "filming_dates",
            "wiki_url",
        ]
        rows = []
        for s in raw_seasons:
            info = s.get("infobox", {})
            rows.append(
                {
                    "version": s.get("version", "US"),
                    "season": s.get("season"),
                    "n_teams": info.get("n_teams"),
                    "n_legs": info.get("n_legs"),
                    "n_episodes": info.get("n_episodes"),
                    "winners": info.get("winners"),
                    "distance_miles": info.get("distance_miles"),
                    "distance_km": info.get("distance_km"),
                    "air_dates": info.get("air_dates"),
                    "filming_dates": info.get("filming_dates"),
                    "wiki_url": s.get("wiki_url"),
                }
            )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_episodes_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create episodes dataframe with backfilled air dates."""
        cols = ["version", "season", "episode", "title", "air_date", "viewers_millions"]
        rows = []

        # Load master episodes lookup if present
        master_episodes: dict[str, Any] = {}
        master_path = self.raw_dir / "wikipedia" / "episodes_master.json"
        if master_path.exists():
            try:
                master_episodes = json.loads(master_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Could not read episodes_master.json: %s", e)

        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for ep in s.get("episodes", []):
                ep_num = ep.get("episode")
                if ep_num is None or pd.isna(ep_num):
                    continue
                ep_num = int(ep_num)
                title = ep.get("title")
                air_date = ep.get("air_date")
                viewers = ep.get("viewers_millions")

                # Fallback to master episode catalogue if air date is missing
                if not air_date and season_num is not None:
                    key = f"{season_num}_{ep_num}"
                    if key in master_episodes:
                        air_date = master_episodes[key].get("air_date")
                        if viewers is None:
                            viewers = master_episodes[key].get("viewers_millions")

                # Fallback to known industry ratings databases (The TV Ratings Guide, USTVDB)
                known_viewership = {
                    ("US", 38, 10): 2.56,
                    ("US", 38, 11): 2.61,
                    ("US", 38, 12): 2.81,
                }
                if (viewers is None or pd.isna(viewers)) and (
                    version,
                    season_num,
                    ep_num,
                ) in known_viewership:
                    viewers = known_viewership[(version, season_num, ep_num)]

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "episode": ep_num,
                        "title": title,
                        "air_date": air_date,
                        "viewers_millions": viewers,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_contestants_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create contestants demographics dataframe with backfilled data."""
        cols = [
            "version",
            "season",
            "contestant_id",
            "name",
            "age",
            "gender",
            "relationship",
            "hometown",
            "hometown_state",
            "hometown_country",
            "status",
            "roadblocks_completed",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            contestants = s.get("contestants", [])
            results = s.get("results", [])
            group_size = 4 if season_num == 8 else 2

            for idx, c in enumerate(contestants, start=1):
                name = c.get("name", "")
                age = c.get("age")
                rel = c.get("relationship")
                hometown = c.get("hometown")
                status = c.get("status")

                # Season 29: contestants were strangers paired at starting line
                if season_num == 29 and (not rel or pd.isna(rel)):
                    rel = "Strangers (Paired at Starting Line)"

                # Season 33: backfill missing demographic fields for withdrawn/returned contestants
                if season_num == 33 and (age is None or pd.isna(age)):
                    if name in KNOWN_S33_CONTESTANTS:
                        age = KNOWN_S33_CONTESTANTS[name]["age"]
                        if not rel or rel == "Returned to competition":
                            rel = KNOWN_S33_CONTESTANTS[name]["relationship"]
                        if not hometown or hometown == "Returned to competition":
                            hometown = KNOWN_S33_CONTESTANTS[name]["hometown"]
                    else:
                        for other in s.get("contestants", []):
                            if (
                                other.get("name") == name
                                and other.get("age") is not None
                            ):
                                age = other.get("age")
                                if not rel or rel == "Returned to competition":
                                    rel = other.get("relationship")
                                if (
                                    not hometown
                                    or hometown == "Returned to competition"
                                ):
                                    hometown = other.get("hometown")
                                break

                gender = self.resolve_contestant_gender(
                    season_num, name, rel, c.get("gender")
                )
                hometown_state, hometown_country = parse_hometown(hometown)

                group_start = ((idx - 1) // group_size) * group_size
                group = contestants[group_start : group_start + group_size]
                group_names = [x.get("name", "") for x in group]
                member_idx = (idx - 1) % group_size
                rb_completed = self.resolve_contestant_roadblocks(
                    season_num, name, group_names, member_idx, results, version=version
                )

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "contestant_id": f"{version}-S{season_num:02d}-{idx:02d}",
                        "name": name,
                        "age": age,
                        "gender": gender,
                        "relationship": rel,
                        "hometown": hometown,
                        "hometown_state": hometown_state,
                        "hometown_country": hometown_country,
                        "status": status,
                        "roadblocks_completed": rb_completed,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_teams_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create teams summary dataframe with resolved relationships and hometowns."""
        cols = [
            "version",
            "season",
            "team_id",
            "team_name",
            "relationship",
            "hometown",
            "result",
            "status",
            "legs_won",
            "legs_completed",
            "racing_average",
            "placement_std",
            "podium_count",
            "podium_rate",
            "gender_composition",
            "roadblock_split",
            "roadblock_equity_score",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            results = s.get("results", [])
            contestants = s.get("contestants", [])

            for rank, r in enumerate(results, start=1):
                team_name = r.get("team_name", "")
                team_id = f"{version}-S{season_num:02d}-{slugify(team_name)}"
                placements = r.get("placements", [])

                active_placements = [
                    p.get("placement")
                    for p in placements
                    if p.get("placement") is not None
                    and isinstance(p.get("placement"), (int, float))
                ]
                legs_completed = len(active_placements)
                legs_won = sum(1 for p in active_placements if p == 1)

                if active_placements:
                    racing_average = round(
                        float(sum(active_placements)) / len(active_placements), 2
                    )
                    placement_std = (
                        round(float(statistics.stdev(active_placements)), 2)
                        if len(active_placements) > 1
                        else 0.0
                    )
                    podium_count = sum(1 for p in active_placements if p <= 3)
                    podium_rate = round(float(podium_count) / len(active_placements), 2)
                else:
                    racing_average = None
                    placement_std = None
                    podium_count = 0
                    podium_rate = None

                rel = None
                hometown = None
                matched_genders: list[str] = []

                # Season 8 (Family Edition): 4-member families
                if season_num == 8:
                    rel = "Family Team (4 members)"
                    fam_name = team_name.replace(" Family", "").strip()
                    for c in contestants:
                        c_name = c.get("name", "")
                        if fam_name.lower() in c_name.lower():
                            hometown = c.get("hometown")
                            matched_genders.append(
                                self.resolve_contestant_gender(
                                    season_num,
                                    c_name,
                                    c.get("relationship"),
                                    c.get("gender"),
                                )
                            )
                elif season_num == 29:
                    rel = "Strangers (Paired at Starting Line)"
                    # Match hometown from contestants
                    parts = [
                        p.strip().strip("\"'")
                        for p in team_name.split("&")
                        if p.strip()
                    ]
                    for p in parts:
                        for c in contestants:
                            c_name = c.get("name", "").replace('"', "").replace("'", "")
                            if any(p.lower() in c_name.lower() for p in parts):
                                hometown = c.get("hometown")
                                matched_genders.append(
                                    self.resolve_contestant_gender(
                                        season_num,
                                        c_name,
                                        c.get("relationship"),
                                        c.get("gender"),
                                    )
                                )
                                break
                else:
                    # Match returnee/standard teams by nickname or contestant name tokens
                    parts = [
                        p.strip().strip("\"'")
                        for p in team_name.split("&")
                        if p.strip()
                    ]
                    for p in parts:
                        for c in contestants:
                            c_name = c.get("name", "").replace('"', "").replace("'", "")
                            if any(p.lower() in c_name.lower() for p in parts):
                                rel = c.get("relationship")
                                hometown = c.get("hometown")
                                matched_genders.append(
                                    self.resolve_contestant_gender(
                                        season_num,
                                        c_name,
                                        c.get("relationship"),
                                        c.get("gender"),
                                    )
                                )
                                break

                status = (
                    "Winner"
                    if rank == 1
                    else ("Runner-up" if rank in [2, 3] else "Eliminated")
                )

                gender_comp = self.resolve_team_gender_comp(
                    season_num, team_name, matched_genders
                )

                rb_split, rb_equity = self.resolve_team_roadblock_split(
                    version, season_num, team_name
                )

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "team_id": team_id,
                        "team_name": team_name,
                        "relationship": rel,
                        "hometown": hometown,
                        "result": rank,
                        "status": status,
                        "legs_won": legs_won,
                        "legs_completed": legs_completed,
                        "racing_average": racing_average,
                        "placement_std": placement_std,
                        "podium_count": podium_count,
                        "podium_rate": podium_rate,
                        "gender_composition": gender_comp,
                        "roadblock_split": rb_split,
                        "roadblock_equity_score": rb_equity,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_legs_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create legs dataframe with itinerary and challenge details."""
        cols = [
            "version",
            "season",
            "leg_number",
            "route_header",
            "origin_country",
            "destination_country",
            "destination_city",
            "destination_continent",
            "itinerary_stops",
            "tasks_count",
            "narrative",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for leg in s.get("legs", []):
                leg_num = leg.get("leg_number")
                tasks = leg.get("tasks", [])
                itinerary = leg.get("itinerary", [])
                narrative = leg.get("narrative") or ""

                (
                    orig_country,
                    dest_country,
                    dest_city,
                    dest_continent,
                ) = parse_route_header(leg.get("route_header"), itinerary)

                # Distinguish route stops from narrative sentences in itinerary
                route_stops = []
                narrative_parts = []
                for item in itinerary:
                    item_str = str(item).strip()
                    if item_str.startswith(
                        ("Episode ", "Eliminated:", "Prize:", "Winners:", "Runners-up:")
                    ):
                        continue
                    if (
                        len(item_str) > 60
                        and any(
                            item_str.endswith(punct) for punct in [".", "!", '"', "'"]
                        )
                    ) or (
                        any(
                            item_str.startswith(p)
                            for p in [
                                "Teams ",
                                "At ",
                                "After ",
                                "Once ",
                                "When ",
                                "In ",
                                "The ",
                                "Upon ",
                            ]
                        )
                        and len(item_str) > 40
                    ):
                        narrative_parts.append(item_str)
                    else:
                        route_stops.append(item_str)

                if not narrative.strip():
                    if narrative_parts:
                        narrative = " ".join(narrative_parts)
                    elif tasks:
                        narrative = " ".join(
                            t["description"]
                            for t in tasks
                            if len(t.get("description", "")) > 40
                        )

                itinerary_stops_count = (
                    len(route_stops) if route_stops else len(itinerary)
                )

                rows.append(
                    {
                        "version": version,
                        "season": season_num,
                        "leg_number": leg_num,
                        "route_header": leg.get("route_header"),
                        "origin_country": orig_country,
                        "destination_country": dest_country,
                        "destination_city": dest_city,
                        "destination_continent": dest_continent,
                        "itinerary_stops": itinerary_stops_count,
                        "tasks_count": len(tasks),
                        "narrative": narrative.strip() if narrative else None,
                    }
                )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_leg_results_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create leg-by-leg team placement results dataframe (active legs only)."""
        cols = [
            "version",
            "season",
            "leg_number",
            "team_name",
            "placement",
            "raw_cell",
            "is_non_elimination",
            "fast_forward",
            "uturn",
            "yield",
            "speed_bump",
            "roadblock_performer",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            results = s.get("results", [])
            for r in results:
                team_name = r.get("team_name")
                for p in r.get("placements", []):
                    m_leg = re.search(r"\d+", str(p.get("leg_label", "")))
                    leg_num = int(m_leg.group(0)) if m_leg else None
                    if leg_num is None:
                        continue

                    raw_cell = p.get("raw_cell")
                    placement = p.get("placement")

                    # Skip empty cells where team was already eliminated
                    if placement is None and (
                        not raw_cell or str(raw_cell).strip() == ""
                    ):
                        continue

                    # Handle off-mat withdrawals / eliminations (e.g. S22 Leg 5 Dave & Connor, S34 Leg 5 Abby & Will marked with †)
                    if placement is None and raw_cell and "†" in str(raw_cell):
                        active_count = sum(
                            1
                            for other_r in results
                            for other_p in other_r.get("placements", [])
                            if other_p.get("leg_label") == p.get("leg_label")
                            and (
                                other_p.get("placement") is not None
                                or (
                                    other_p.get("raw_cell")
                                    and str(other_p.get("raw_cell")).strip() != ""
                                )
                            )
                        )
                        placement = active_count if active_count > 0 else 8

                    rb_perf = self.resolve_leg_roadblock_performer(
                        season_num, leg_num, team_name
                    )

                    rows.append(
                        {
                            "version": version,
                            "season": season_num,
                            "leg_number": leg_num,
                            "team_name": team_name,
                            "placement": int(placement)
                            if placement is not None
                            else None,
                            "raw_cell": raw_cell,
                            "is_non_elimination": p.get("is_non_elimination", False),
                            "fast_forward": p.get("fast_forward", False),
                            "uturn": p.get("uturn", False),
                            "yield": p.get("yield", False),
                            "speed_bump": p.get("speed_bump", False),
                            "roadblock_performer": rb_perf,
                        }
                    )
        df = pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)
        if (
            not df.empty
            and "placement" in df.columns
            and not df["placement"].isna().any()
        ):
            df["placement"] = df["placement"].astype(int)
        return df

    def build_tasks_df(self, raw_seasons: list[dict[str, Any]]) -> pd.DataFrame:
        """Create tasks and challenges dataframe."""
        cols = [
            "version",
            "season",
            "leg_number",
            "task_type",
            "description",
            "performed_by",
        ]
        rows = []
        for s in raw_seasons:
            season_num = s.get("season")
            version = s.get("version", "US")
            for leg in s.get("legs", []):
                leg_num = leg.get("leg_number")
                leg_performers_list = self._roadblock_leg_tasks.get(
                    (season_num, leg_num), []
                )
                for t in leg.get("tasks", []):
                    task_type = t.get("task_type")
                    performed_by = None
                    if task_type == "Roadblock" and leg_performers_list:
                        performed_by = ", ".join(dict.fromkeys(leg_performers_list))

                    rows.append(
                        {
                            "version": version,
                            "season": season_num,
                            "leg_number": leg_num,
                            "task_type": task_type,
                            "description": t.get("description"),
                            "performed_by": performed_by,
                        }
                    )
        return pd.DataFrame(rows, columns=cols) if not rows else pd.DataFrame(rows)

    def build_all(self) -> dict[str, pd.DataFrame]:
        """Compile all tidy datasets, saving CSV and Parquet copies."""
        raw_seasons = self.load_wikipedia_seasons()
        if not raw_seasons:
            logger.warning("No raw Wikipedia seasons found to build.")
            return {}

        dfs = {
            "seasons": self.build_seasons_df(raw_seasons),
            "episodes": self.build_episodes_df(raw_seasons),
            "contestants": self.build_contestants_df(raw_seasons),
            "teams": self.build_teams_df(raw_seasons),
            "legs": self.build_legs_df(raw_seasons),
            "leg_results": self.build_leg_results_df(raw_seasons),
            "tasks": self.build_tasks_df(raw_seasons),
        }

        for name, df in dfs.items():
            csv_path = self.processed_dir / f"{name}.csv"
            parquet_path = self.processed_dir / f"{name}.parquet"
            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)
            logger.info("Saved %s: %d records -> %s", name, len(df), csv_path)

        try:
            from tar_dataset.exports.sqlite_export import export_to_sqlite

            export_to_sqlite(processed_dir=self.processed_dir)
        except Exception as e:
            logger.warning("Could not automatically update SQLite database: %s", e)

        return dfs
