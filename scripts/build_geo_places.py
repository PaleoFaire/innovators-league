#!/usr/bin/env python3
"""
Build data/geo/us_places.json, the one static file the jobs board uses to turn
"a city or a ZIP code" into a point on the map.

Why a file: the board's "search near home" runs in the reader's browser.
Nothing the reader types, and nothing their browser says about where they are,
is sent anywhere, so there can be no geocoding service. The page loads this
file and looks the place up itself. scripts/enrich_jobs.py reads the same file
to give each job posting a place.

Two ways to build it
--------------------
1. FULL: every US town and ZIP code. Put the two US Census Bureau Gazetteer
   "national" files in data/geo/src/ and run this script:

       data/geo/src/2024_Gaz_place_national.txt    (or the .zip it comes in)
       data/geo/src/2024_Gaz_zcta_national.txt     (or the .zip it comes in)

   They are on the Census Bureau's Gazetteer Files page, under "Places" and
   "ZIP Code Tabulation Areas":
       https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html
   Direct downloads, if the folder layout has not changed:
       https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip
       https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip
   Any year works: the script takes the newest *_Gaz_place_national.* and
   *_Gaz_zcta_national.* it finds. Both are tab-separated text in the public
   domain. This script never downloads anything; a person fetches the two
   files once. The columns it reads:
       Places: USPS (state code), NAME ("Costa Mesa city"), ALAND, INTPTLAT, INTPTLONG
       ZCTA:   GEOID (the five digits), INTPTLAT, INTPTLONG
   A ZIP Code Tabulation Area is the Census Bureau's map of a ZIP code. A few
   ZIP codes (PO boxes, single buildings) have none. Towns the repo knows and
   the Census file does not (Starbase, TX in the 2024 file) are kept.

2. FALLBACK: what the repo already knows. With no Census files the script uses
   only data that is already in this repository:
       data.js                                  each tracked US company's "City, ST" and lat/lng
       data/geocode_cache.json                  about 375 "Company|City, ST|ST" points
       scripts/audit_location_consistency.py    KNOWN_CITY_COORDS, the curated table that
                                                script checks company coordinates against
   A town's point is the curated value when that table has the town, else the
   median of every point on record for it. A town whose point is a copy of a
   neighbouring town's is left off the map rather than guessed (see
   repo_places). ZIP codes are not available in this mode ("zips" is empty)
   and the page says so.

Hubs: the eight US hubs in METRO_RULES (scripts/enrich_jobs.py) are written in
both modes. A hub's point is its main town's point from the data above;
APPROX_HUB_CENTRES below is used only if that town is missing.

Output schema (version 1)
-------------------------
    {
      "schema": 1,
      "source": "census" | "repo",
      "builtFrom": [...],                             the inputs used
      "counts": {"places": N, "zips": N, "hubs": 8},
      "states": ["AK", "AL", ...],                    state codes used by "places"
      "places": [[name, stateIndex, lat, lng], ...],  sorted by state, then name
      "aliases": {"new york city|NY": 123, "nyc|": 123, ...},
                 other spellings -> index into "places". The key is the
                 normalised name (enrich_jobs.norm_place), a bar, and the state
                 as written ("" when the spelling carries no state).
      "hubs": [[code, label, lat, lng, approx], ...], approx = 1 when the point is from APPROX_HUB_CENTRES
      "zips": {"926": "14gfx4tf...", ...}             {} when there is no ZIP data
    }
ZIP packing: one string per three-digit prefix, eight characters per ZIP code:
its last two digits, then latitude and longitude as three base-36 digits each,
of round((lat + 90) * 100) and round((lng + 180) * 100). That is the point to
a hundredth of a degree (under a mile), plenty for a 25-mile search.

Deterministic: the same inputs give a byte-identical file (no dates inside).

Usage:
    python3 scripts/build_geo_places.py              # write data/geo/us_places.json
    python3 scripts/build_geo_places.py --check      # exit 1 if the file on disk is out of date
    python3 scripts/build_geo_places.py --src DIR --out FILE
"""

import argparse
import json
import re
import string
import sys
import zipfile
from collections import OrderedDict, defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import enrich_jobs as E  # noqa: E402  (place rules, hub list and the data.js reader live there)

DATA = ROOT / "data"
SRC_DIR = DATA / "geo" / "src"
OUT_PATH = DATA / "geo" / "us_places.json"
GEOCODE_CACHE_PATH = DATA / "geocode_cache.json"
SCHEMA = 1

US_COUNTRY_VALUES = {"United States", "USA", "US", "United States of America"}

# Approximate city-centre coordinates, typed by hand to two decimal places (about half a mile).
# Used ONLY when the data has no point for a hub's main town; that hub is then written with approx = 1.
APPROX_HUB_CENTRES = {
    "sf":  (37.77, -122.42),   # San Francisco (approximate)
    "la":  (34.05, -118.24),   # Los Angeles (approximate)
    "tx":  (30.27, -97.74),    # Austin (approximate)
    "sea": (47.61, -122.33),   # Seattle (approximate)
    "den": (39.74, -104.99),   # Denver (approximate)
    "dc":  (38.90, -77.04),    # Washington, DC (approximate)
    "nyc": (40.71, -74.01),    # New York (approximate)
    "bos": (42.36, -71.06),    # Boston (approximate)
}

# Towns whose only point in the repo is known to be wrong, and why. They are left off the map,
# never moved by hand; the Census build puts them back in the right place.
REPO_POINTS_NOT_TRUSTED = {
    "san bernardino|CA": "its point on record is the middle of San Bernardino County, about 75 miles from the town",
}
# Two different towns closer than this have, in practice, been given one town's coordinates.
SAME_POINT_MILES = 0.5

# The Census file names a place with its legal description on the end ("Costa Mesa city").
# The description is in lower case ("CDP" apart), which is how "Oklahoma City city" loses one
# "city" and "Carson City", which has no description, keeps its name.
CENSUS_SUFFIXES = (
    "city and borough", "consolidated government", "metropolitan government", "metro government",
    "unified government", "urban county", "municipality", "borough", "village", "town", "city", "CDP",
    "comunidad", "zona urbana", "corporation",
)

# Everyday names for a few merged city-county governments: (Census name, state, everyday name).
CENSUS_EVERYDAY_NAMES = [
    ("Urban Honolulu", "HI", "Honolulu"), ("Nashville-Davidson", "TN", "Nashville"),
    ("Louisville/Jefferson County", "KY", "Louisville"), ("Lexington-Fayette", "KY", "Lexington"),
    ("Boise City", "ID", "Boise"), ("Augusta-Richmond County", "GA", "Augusta"),
    ("Athens-Clarke County", "GA", "Athens"), ("Macon-Bibb County", "GA", "Macon"),
    ("Butte-Silver Bow", "MT", "Butte"),
]

BASE36 = string.digits + string.ascii_lowercase


# ─────────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────────

def plausible_us_point(lat, lng):
    """Inside the box that holds the 50 states, DC and Puerto Rico. Catches swapped or zero coordinates."""
    return 17.0 <= lat <= 72.0 and -180.0 <= lng <= -64.0


def split_town(location):
    """'Costa Mesa, CA' -> ('Costa Mesa', 'CA'); anything that is not 'Town, State' -> None."""
    m = re.match(r"^\s*([^,]+?)\s*,\s*([A-Za-z. ]+?)\s*$", location or "")
    if not m:
        return None
    code = E.state_code(m.group(2))
    return (m.group(1), code) if code else None


def b36(n, width):
    if n < 0 or n >= 36 ** width:
        raise ValueError("%d does not fit in %d base-36 digits" % (n, width))
    out = ""
    for _ in range(width):
        n, r = divmod(n, 36)
        out = BASE36[r] + out
    return out


def pack_zips(zips):
    """{'92614': (33.68, -117.83), ...} -> {'926': '14' + lat36 + lng36 + ...} (see the module docstring)."""
    groups = defaultdict(list)
    for code in sorted(zips):
        lat, lng = zips[code]
        groups[code[:3]].append(code[3:] + b36(int(round((lat + 90) * 100)), 3) + b36(int(round((lng + 180) * 100)), 3))
    return OrderedDict((prefix, "".join(groups[prefix])) for prefix in sorted(groups))


def unpack_zip(packed, code):
    """The reverse of pack_zips for one ZIP code -> (lat, lng) or None. jobs.js does the same in the browser."""
    row = (packed or {}).get(code[:3], "")
    for i in range(0, len(row), 8):
        if row[i:i + 2] == code[3:]:
            return (round(int(row[i + 2:i + 5], 36) / 100 - 90, 2), round(int(row[i + 5:i + 8], 36) / 100 - 180, 2))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Source 1: Census Gazetteer files (only if a person has put them in data/geo/src/)
# ─────────────────────────────────────────────────────────────────────────────

def find_census_files(src_dir):
    """-> (places_path or None, zcta_path or None): the newest year of each, .txt before .zip."""
    def newest(pattern):
        found = sorted(Path(src_dir).glob(pattern), key=lambda p: (p.name[:4], p.suffix.lower() == ".txt", p.name))
        return found[-1] if found else None
    if not Path(src_dir).is_dir():
        return None, None
    return newest("*_Gaz_place_national.*"), newest("*_Gaz_zcta_national.*")


def read_gazetteer(path):
    """Tab-separated Gazetteer file (.txt, or the .zip it ships in) -> [{COLUMN: value}], all stripped."""
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            inner = sorted(n for n in z.namelist() if n.lower().endswith(".txt"))
            if not inner:
                raise ValueError("%s holds no .txt file" % path.name)
            raw = z.read(inner[0])
    else:
        raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    header = [h.strip().upper() for h in lines[0].split("\t")]
    rows = []
    for ln in lines[1:]:
        cells = [c.strip() for c in ln.split("\t")]
        if len(cells) >= len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def clean_census_name(name):
    """'Costa Mesa city' -> 'Costa Mesa'; 'Indianapolis city (balance)' -> 'Indianapolis'; 'Carson City' stays."""
    n = re.sub(r"\s*\(balance\)\s*$", "", (name or "").strip(), flags=re.I)
    for suffix in CENSUS_SUFFIXES:
        if n.endswith(" " + suffix):
            return n[: -len(suffix) - 1].rstrip()
    return n


def census_places(rows):
    """Places rows -> ({key: (name, state, lat, lng)}, [(other name, state, name, state)]).

    Where one state has two places of the same name, the one with more land wins.
    'San Buenaventura (Ventura) city' becomes San Buenaventura with Ventura as another spelling.
    """
    best, others = {}, []
    for r in rows:
        state = (r.get("USPS") or "").upper()
        name = clean_census_name(r.get("NAME"))
        try:
            lat, lng = float(r.get("INTPTLAT")), float(r.get("INTPTLONG"))
            land = float(r.get("ALAND") or 0)
        except (TypeError, ValueError):
            continue
        if not name or not re.fullmatch(r"[A-Z]{2}", state) or not plausible_us_point(lat, lng):
            continue
        alt = None
        m = re.match(r"^(.*?)\s*\(([^)]+)\)$", name)
        if m and m.group(1).strip():
            name, alt = m.group(1).strip(), m.group(2).strip()
        key = E.place_key(name, state)
        if not key.split("|")[0]:
            continue
        if key not in best or land > best[key][0]:
            best[key] = (land, name, state, lat, lng)
        if alt:
            others.append((alt, state, name, state))
    return {k: v[1:] for k, v in best.items()}, others


def census_zips(rows):
    """ZCTA rows -> {'92614': (lat, lng)}."""
    out = {}
    for r in rows:
        code = r.get("GEOID") or ""
        try:
            lat, lng = float(r.get("INTPTLAT")), float(r.get("INTPTLONG"))
        except (TypeError, ValueError):
            continue
        if re.fullmatch(r"\d{5}", code) and plausible_us_point(lat, lng):
            out[code] = (lat, lng)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Source 2: what the repo already knows
# ─────────────────────────────────────────────────────────────────────────────

def _number(rec, key):
    m = re.search(r"(?<![\w.])" + re.escape(key) + r"\s*:\s*(-?\d+(?:\.\d+)?)", rec)
    return float(m.group(1)) if m else None


def repo_places(data_js_path=None, cache_path=None, curated=None, left_out=None):
    """-> {key: (name, state, lat, lng)} from data.js, the geocode cache and the curated city table.

    A town's point is the curated value when the curated table has the town, else the median of
    every point on record for it (a median shrugs off the odd geocode that returned the county).
    Two checks keep bad points off the map; what they drop is appended to `left_out` as
    (name, state, reason):
      - REPO_POINTS_NOT_TRUSTED, towns whose only point is known to be wrong;
      - a town whose point is a copy of a different town's point (within SAME_POINT_MILES). The
        repo has a handful of companies carrying a neighbouring city's coordinates. The better
        attested town keeps the point (curated beats recorded, more points beat fewer); when
        neither is better, both are dropped.
    """
    data_js_path = Path(data_js_path or E.DATA_JS_PATH)
    cache_path = Path(cache_path or GEOCODE_CACHE_PATH)
    left_out = [] if left_out is None else left_out
    names = {}                      # key -> (name, state) as first written
    points = defaultdict(list)      # key -> [(lat, lng)]: every point on record for that town

    def note(town, lat, lng):
        if not town or lat is None or lng is None or not plausible_us_point(lat, lng):
            return
        key = E.place_key(town[0], town[1])
        if not key.split("|")[0]:
            return
        names.setdefault(key, (town[0].strip(), town[1]))
        points[key].append((lat, lng))

    if data_js_path.exists():
        src = data_js_path.read_text(encoding="utf-8")
        for rec in E._split_records(E._extract_const_array(src, "COMPANIES") or "[]"):
            if (E._field(rec, "country") or "") not in US_COUNTRY_VALUES:
                continue
            note(split_town(E._field(rec, "location") or ""), _number(rec, "lat"), _number(rec, "lng"))

    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except ValueError:
            cache = {}
        for key in sorted(cache):
            parts, hit = key.split("|"), cache[key]
            if len(parts) != 3 or not isinstance(hit, dict):
                continue
            lat, lng = hit.get("lat"), hit.get("lng")
            if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                note(split_town(parts[1]), float(lat), float(lng))

    if curated is None:
        try:
            from audit_location_consistency import KNOWN_CITY_COORDS as curated
        except Exception:  # noqa: BLE001 - the table is a bonus; build without it
            curated = {}
    curated_points = {}
    for written in sorted(curated):
        town = split_town(written)
        if not town:
            continue
        lat, lng = curated[written]
        if not plausible_us_point(lat, lng):
            continue
        key = E.place_key(town[0], town[1])
        names.setdefault(key, (string.capwords(town[0]), town[1]))
        curated_points.setdefault(key, (float(lat), float(lng)))

    towns, rank = {}, {}
    for key in sorted(names):
        name, state = names[key]
        if key in REPO_POINTS_NOT_TRUSTED:
            left_out.append((name, state, REPO_POINTS_NOT_TRUSTED[key]))
            continue
        if key in curated_points:
            lat, lng = curated_points[key]
        else:
            lat, lng = median(p[0] for p in points[key]), median(p[1] for p in points[key])
        towns[key] = (name, state, lat, lng)
        rank[key] = (1 if key in curated_points else 0, len(points[key]))

    drop = {}
    keys = sorted(towns)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if E.haversine_miles(towns[a][2], towns[a][3], towns[b][2], towns[b][3]) > SAME_POINT_MILES:
                continue
            for loser, other in ((a, b), (b, a)):
                if rank[loser] <= rank[other]:
                    drop[loser] = "its point on record is the same as %s, %s's" % (towns[other][0], towns[other][1])
    for key in sorted(drop):
        left_out.append((towns[key][0], towns[key][1], drop[key]))
        del towns[key]
    return towns


# ─────────────────────────────────────────────────────────────────────────────
# Assemble and write
# ─────────────────────────────────────────────────────────────────────────────

def build(src_dir=SRC_DIR, repo=None, left_out=None):
    """-> the payload dict (see the module docstring). Towns dropped from the repo data go to `left_out`."""
    places_file, zcta_file = find_census_files(src_dir)
    repo = repo_places(left_out=left_out) if repo is None else repo
    built_from, extra_aliases, zips = [], [], {}
    if places_file:
        towns, extra_aliases = census_places(read_gazetteer(places_file))
        built_from.append(places_file.name)
        added = 0
        for key, row in repo.items():          # towns the repo knows and this Census file does not
            if key not in towns:
                towns[key] = row
                added += 1
        if added:
            built_from.append("repo data for %d towns the Census file lacks" % added)
        extra_aliases += [(everyday, st, census, st) for census, st, everyday in CENSUS_EVERYDAY_NAMES]
        source = "census"
    else:
        towns = dict(repo)
        built_from += ["data.js company locations", "data/geocode_cache.json",
                       "scripts/audit_location_consistency.py KNOWN_CITY_COORDS"]
        source = "repo"
    if zcta_file:
        zips = census_zips(read_gazetteer(zcta_file))
        built_from.append(zcta_file.name)

    ordered = sorted(towns.values(), key=lambda t: (t[1], E.norm_place(t[0]), t[0]))
    states = sorted({t[1] for t in ordered})
    state_index = {s: i for i, s in enumerate(states)}
    rows, index = [], {}
    for name, state, lat, lng in ordered:
        index[E.place_key(name, state)] = len(rows)
        rows.append([name, state_index[state], round(lat, 3), round(lng, 3)])

    aliases = {}
    for written, written_state, name, state in list(E.PLACE_ALIASES) + extra_aliases:
        target = index.get(E.place_key(name, state))
        key = E.place_key(written, written_state)
        if target is not None and key.split("|")[0] and key not in index:
            aliases.setdefault(key, target)

    hubs = []
    for code, (name, state) in E.HUB_ANCHORS.items():
        i = index.get(E.place_key(name, state))
        if i is not None:
            hubs.append([code, E.METROS[code], rows[i][2], rows[i][3], 0])
        else:
            lat, lng = APPROX_HUB_CENTRES[code]
            hubs.append([code, E.METROS[code], lat, lng, 1])

    return OrderedDict([
        ("schema", SCHEMA),
        ("source", source),
        ("builtFrom", built_from),
        ("counts", OrderedDict([("places", len(rows)), ("zips", len(zips)), ("hubs", len(hubs))])),
        ("states", states),
        ("places", rows),
        ("aliases", OrderedDict(sorted(aliases.items()))),
        ("hubs", hubs),
        ("zips", pack_zips(zips)),
    ])


def render(payload):
    """The payload as text: one town, alias, hub and ZIP prefix per line, so diffs stay readable."""
    def dump(v):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))

    def block(open_ch, items, close_ch):
        return open_ch + ("\n" + ",\n".join(items) + "\n" if items else "") + close_ch

    parts = []
    for key, value in payload.items():
        if key in ("places", "hubs"):
            body = block("[", [dump(r) for r in value], "]")
        elif key in ("aliases", "zips"):
            body = block("{", [dump(k) + ":" + dump(v) for k, v in value.items()], "}")
        else:
            body = dump(value)
        parts.append(dump(key) + ":" + body)
    return "{\n" + ",\n".join(parts) + "\n}\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(SRC_DIR), help="folder that may hold the two Census Gazetteer files")
    ap.add_argument("--out", default=str(OUT_PATH), help="file to write")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if the file on disk is out of date")
    ap.add_argument("--allow-fallback", action="store_true",
                    help="let a build from repo data replace a file that was built from the Census files")
    args = ap.parse_args(argv)
    left_out = []
    payload = build(args.src, left_out=left_out)
    text = render(payload)
    out = Path(args.out)
    c = payload["counts"]
    summary = "[geo] source=%s · %d towns · %d ZIP codes · %d hubs · %d other spellings · %d KB" % (
        payload["source"], c["places"], c["zips"], c["hubs"], len(payload["aliases"]), len(text.encode("utf-8")) // 1024)
    current = out.read_text(encoding="utf-8") if out.exists() else ""
    if args.check:
        print(summary + (" · up to date" if current == text else " · OUT OF DATE: run scripts/build_geo_places.py"))
        return 0 if current == text else 1
    if payload["source"] == "repo" and '"source":"census"' in current[:200] and not args.allow_fallback:
        print("[geo] %s was built from the Census files, and they are not in %s now." % (out, args.src), file=sys.stderr)
        print("[geo] Nothing written: a rebuild from repo data would drop every ZIP code. Put the Census files back,"
              " or pass --allow-fallback.", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(summary)
    print("[geo] built from: " + "; ".join(payload["builtFrom"]))
    for name, state, reason in left_out:
        print("[geo] left out of the repo data: %s, %s (%s)" % (name, state, reason))
    if not c["zips"]:
        print("[geo] no ZIP codes: put the Census Gazetteer files in %s to add them (see the top of this script)" % SRC_DIR)
    print("[geo] wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
