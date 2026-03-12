#!/usr/bin/env python3
"""
Geocode companies in data.js that share duplicate coordinates.

This script:
1. Reads data.js and extracts all company entries with name, location, state, lat, lng
2. Identifies companies sharing duplicate coordinates (same lat/lng as another company)
3. For those companies, geocodes their real office address using Nominatim (OpenStreetMap)
4. Updates data.js with the corrected coordinates
5. Specifically fixes Hugging Face (has Paris coords but location is New York, NY)

Uses a persistent cache at data/geocode_cache.json to avoid re-geocoding.
Rate-limited to 1 request per second per Nominatim Terms of Service.
"""

import json
import os
import re
import ssl
import sys
import time
import random
import urllib.request
import urllib.parse
from collections import defaultdict
from pathlib import Path

# Try to use certifi for SSL certificates (common on macOS)
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_JS_PATH = PROJECT_DIR / "data.js"
CACHE_PATH = PROJECT_DIR / "data" / "geocode_cache.json"

# Nominatim config
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "InnovatorsLeague/1.0 (geocoding company HQ locations)"
RATE_LIMIT_SECONDS = 1.1  # Slightly more than 1s to be safe

# Known corrections: companies whose coordinates are clearly wrong
KNOWN_CORRECTIONS = {
    "Hugging Face": {
        "reason": "Has Paris coordinates (48.8566, 2.3522) but location is New York, NY",
        "force_geocode": True,
    },
}


def load_cache():
    """Load the geocode cache from disk."""
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save the geocode cache to disk."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def find_matching_brace(content, start):
    """
    Find the position of the closing brace that matches the opening brace at `start`.
    Handles nested braces, strings (double-quoted), and template literals.
    Returns the index of the closing brace, or -1 if not found.
    """
    depth = 0
    i = start
    in_string = False
    string_char = None
    length = len(content)

    while i < length:
        ch = content[i]

        # Handle escape sequences inside strings
        if in_string:
            if ch == '\\':
                i += 2  # Skip escaped character
                continue
            if ch == string_char:
                in_string = False
            i += 1
            continue

        # Start of string
        if ch in ('"', "'", '`'):
            in_string = True
            string_char = ch
            i += 1
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1


def extract_companies(content):
    """
    Extract company entries from data.js content.
    Returns a list of dicts with name, location, state, lat, lng, and their positions in the file.

    Uses brace-matching to correctly identify each top-level company object,
    handling nested objects like thesis: { ... } and scores: { ... }.
    """
    companies = []

    # First, find the COMPANIES array
    companies_match = re.search(r'const\s+COMPANIES\s*=\s*\[', content)
    if not companies_match:
        print("ERROR: Could not find COMPANIES array in data.js")
        sys.exit(1)

    companies_start = companies_match.end()

    # Find each top-level object in the COMPANIES array by scanning for opening braces
    i = companies_start
    length = len(content)

    while i < length:
        # Skip whitespace and commas
        while i < length and content[i] in ' \t\n\r,':
            i += 1

        if i >= length:
            break

        # Check for end of array
        if content[i] == ']':
            break

        # Skip single-line comments
        if content[i:i+2] == '//':
            newline = content.find('\n', i)
            if newline == -1:
                break
            i = newline + 1
            continue

        # Skip multi-line comments
        if content[i:i+2] == '/*':
            end_comment = content.find('*/', i)
            if end_comment == -1:
                break
            i = end_comment + 2
            continue

        # Should be start of an object
        if content[i] == '{':
            obj_start = i
            obj_end = find_matching_brace(content, i)
            if obj_end == -1:
                print(f"WARNING: Unmatched brace at position {i}")
                break

            block = content[obj_start:obj_end + 1]

            # Extract fields from this block
            name_match = re.search(r'name:\s*"([^"]+)"', block)
            lat_match = re.search(r'(?<!\w)lat:\s*(-?\d+\.?\d*)', block)
            lng_match = re.search(r'(?<!\w)lng:\s*(-?\d+\.?\d*)', block)

            if name_match and lat_match and lng_match:
                name = name_match.group(1)
                lat = float(lat_match.group(1))
                lng = float(lng_match.group(1))

                location_match = re.search(r'location:\s*"([^"]*)"', block)
                state_match = re.search(r'(?<!\w)state:\s*"([^"]*)"', block)

                location = location_match.group(1) if location_match else ""
                state = state_match.group(1) if state_match else ""

                # Calculate absolute positions for lat/lng values in the full content
                lat_abs_start = obj_start + lat_match.start(1)
                lat_abs_end = obj_start + lat_match.end(1)
                lng_abs_start = obj_start + lng_match.start(1)
                lng_abs_end = obj_start + lng_match.end(1)

                companies.append({
                    "name": name,
                    "location": location,
                    "state": state,
                    "lat": lat,
                    "lng": lng,
                    "lat_value_start": lat_abs_start,
                    "lat_value_end": lat_abs_end,
                    "lng_value_start": lng_abs_start,
                    "lng_value_end": lng_abs_end,
                    "lat_str": lat_match.group(1),
                    "lng_str": lng_match.group(1),
                })

            i = obj_end + 1
        else:
            # Unexpected character, advance
            i += 1

    return companies


def find_duplicates(companies):
    """
    Group companies by their exact lat/lng coordinates.
    Returns only groups with 2+ companies sharing the same coords.
    """
    coord_groups = defaultdict(list)
    for company in companies:
        key = (company["lat"], company["lng"])
        coord_groups[key].append(company)

    duplicates = {k: v for k, v in coord_groups.items() if len(v) >= 2}
    return duplicates


def find_known_corrections(companies):
    """Find companies with known coordinate errors that need fixing."""
    corrections = []
    for company in companies:
        if company["name"] in KNOWN_CORRECTIONS:
            corrections.append(company)
    return corrections


def geocode_nominatim(query):
    """
    Geocode a query string using Nominatim.
    Returns (lat, lng) or None if not found.
    """
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
    })
    url = f"{NOMINATIM_URL}?{params}"

    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
    })

    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    Nominatim error for '{query}': {e}")

    return None


def is_us_state(state):
    """Check if a state code corresponds to a US state or territory."""
    us_states = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC", "PR", "VI", "GU", "AS", "MP",
    }
    return state.upper() in us_states if state else False


def geocode_company(company, cache):
    """
    Attempt to geocode a company using multiple query strategies.
    Uses Nominatim which works best with city/place names.
    Strategy:
      1. Try "{company_name} headquarters {location}"
      2. Try "{company_name} {location}"
      3. Fall back to just "{location}" (city, state)
      4. For companies with no location, try "{company_name} {state}"

    Returns (lat, lng) or None.
    """
    name = company["name"]
    location = company["location"]
    state = company["state"]

    # Check cache first
    cache_key = f"{name}|{location}|{state}"
    if cache_key in cache:
        cached = cache[cache_key]
        print(f"    [CACHE] {name}: ({cached['lat']}, {cached['lng']})")
        return cached["lat"], cached["lng"]

    queries = []

    if location:
        # Try company-specific queries first (may work for well-known companies)
        queries.append(f"{name} headquarters {location}")
        queries.append(f"{name} {location}")
        # Fall back to just the location (most reliable with Nominatim)
        queries.append(location)
    elif state:
        queries.append(f"{name} headquarters {state}")
        queries.append(f"{name} {state}")
        queries.append(state)
    else:
        queries.append(f"{name} headquarters")
        queries.append(name)

    for query in queries:
        print(f"    Trying: '{query}'")
        result = geocode_nominatim(query)
        time.sleep(RATE_LIMIT_SECONDS)

        if result:
            lat, lng = result
            # Sanity check: for US-state companies, ensure coords are in US range
            if is_us_state(state):
                if not (18 <= lat <= 72 and -180 <= lng <= -60):
                    print(f"    Result ({lat:.4f}, {lng:.4f}) outside US, skipping")
                    continue

            print(f"    Found: ({lat:.4f}, {lng:.4f}) via '{query}'")
            cache[cache_key] = {"lat": round(lat, 4), "lng": round(lng, 4), "query": query}
            save_cache(cache)
            return round(lat, 4), round(lng, 4)

    return None


def add_jitter(lat, lng, max_offset=0.01):
    """
    Add small random jitter to coordinates (within ~1km).
    Used when geocoding returns the same city-center coords for multiple companies.
    """
    jitter_lat = random.uniform(-max_offset, max_offset)
    jitter_lng = random.uniform(-max_offset, max_offset)
    return round(lat + jitter_lat, 4), round(lng + jitter_lng, 4)


def update_data_js(content, replacements):
    """
    Apply coordinate replacements to data.js content.

    We work backwards through the file (by position) so that earlier replacements
    don't shift positions for later ones.
    """
    # Build list of all individual replacements with positions
    edits = []
    for r in replacements:
        company_name = r["name"]
        new_lat = r["new_lat"]
        new_lng = r["new_lng"]
        lat_start = r["lat_value_start"]
        lat_end = r["lat_value_end"]
        lng_start = r["lng_value_start"]
        lng_end = r["lng_value_end"]

        new_lat_str = f"{new_lat:.4f}"
        new_lng_str = f"{new_lng:.4f}"

        edits.append((lat_start, lat_end, new_lat_str, company_name, "lat"))
        edits.append((lng_start, lng_end, new_lng_str, company_name, "lng"))

    # Sort by position descending so we can replace without shifting
    edits.sort(key=lambda x: x[0], reverse=True)

    for start, end, new_val, company_name, coord_type in edits:
        old_val = content[start:end]
        content = content[:start] + new_val + content[end:]
        print(f"  Replaced {coord_type} for {company_name}: {old_val} -> {new_val}")

    return content


def main():
    print("=" * 60)
    print("GEOCODE COMPANIES - Fixing Duplicate Coordinates")
    print("=" * 60)

    # Read data.js
    print(f"\nReading {DATA_JS_PATH}...")
    with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract companies
    companies = extract_companies(content)
    print(f"Found {len(companies)} companies with lat/lng coordinates.")

    # Load cache
    cache = load_cache()
    print(f"Loaded {len(cache)} cached geocode results.")

    # Find duplicates
    duplicates = find_duplicates(companies)
    print(f"\nFound {len(duplicates)} coordinate groups with duplicates:")
    for coords, group in sorted(duplicates.items(), key=lambda x: -len(x[1])):
        print(f"  ({coords[0]}, {coords[1]}): {len(group)} companies")
        for c in group:
            print(f"    - {c['name']} ({c['location'] or 'no location'})")

    # Find known corrections
    known = find_known_corrections(companies)
    if known:
        print(f"\nFound {len(known)} companies with known coordinate errors:")
        for c in known:
            info = KNOWN_CORRECTIONS[c["name"]]
            print(f"  - {c['name']}: {info['reason']}")

    # Count totals
    companies_to_geocode = set()
    for coords, group in duplicates.items():
        for company in group:
            companies_to_geocode.add(company["name"])
    for company in known:
        companies_to_geocode.add(company["name"])
    print(f"\nTotal companies to geocode: {len(companies_to_geocode)}")

    # Geocode each company
    replacements = []

    # Track which city-center coords we've already used to ensure uniqueness
    # key = (lat, lng), value = list of company names assigned those coords
    used_coords = defaultdict(list)

    # Process duplicate groups
    for coords, group in sorted(duplicates.items(), key=lambda x: -len(x[1])):
        print(f"\n--- Resolving duplicates at ({coords[0]}, {coords[1]}) ---")

        # First, geocode the city/location for this group to get a baseline
        # (all companies in this group share the same coords = same city center)
        city_lat, city_lng = coords

        for i, company in enumerate(group):
            name = company["name"]
            print(f"\n  [{i+1}/{len(group)}] {name} (location: {company['location'] or 'none'}, state: {company['state'] or 'none'})")

            # Try to geocode this specific company
            result = geocode_company(company, cache)

            if result:
                new_lat, new_lng = result

                # Check if the geocoded result is meaningfully different from the city center
                if abs(new_lat - city_lat) > 0.005 or abs(new_lng - city_lng) > 0.005:
                    # Got a specific result different from city center
                    print(f"    Will update: ({company['lat']}, {company['lng']}) -> ({new_lat}, {new_lng})")
                    replacements.append({
                        "name": name,
                        "new_lat": new_lat,
                        "new_lng": new_lng,
                        "lat_value_start": company["lat_value_start"],
                        "lat_value_end": company["lat_value_end"],
                        "lng_value_start": company["lng_value_start"],
                        "lng_value_end": company["lng_value_end"],
                    })
                    used_coords[(new_lat, new_lng)].append(name)
                else:
                    # Got city-center coords back (typical for Nominatim)
                    if i == 0 and name not in KNOWN_CORRECTIONS:
                        # First company in group keeps the original coords
                        print(f"    Keeping original coords (first in group)")
                        used_coords[(company["lat"], company["lng"])].append(name)
                    else:
                        # Add jitter to differentiate
                        new_lat, new_lng = add_jitter(city_lat, city_lng)
                        # Make sure we haven't already used these jittered coords
                        attempts = 0
                        while (new_lat, new_lng) in used_coords and attempts < 10:
                            new_lat, new_lng = add_jitter(city_lat, city_lng)
                            attempts += 1
                        print(f"    Adding jitter: ({company['lat']}, {company['lng']}) -> ({new_lat}, {new_lng})")
                        replacements.append({
                            "name": name,
                            "new_lat": new_lat,
                            "new_lng": new_lng,
                            "lat_value_start": company["lat_value_start"],
                            "lat_value_end": company["lat_value_end"],
                            "lng_value_start": company["lng_value_start"],
                            "lng_value_end": company["lng_value_end"],
                        })
                        used_coords[(new_lat, new_lng)].append(name)
            else:
                # Couldn't geocode at all
                if i == 0 and name not in KNOWN_CORRECTIONS:
                    print(f"    No result, keeping original (first in group)")
                    used_coords[(company["lat"], company["lng"])].append(name)
                else:
                    # Add jitter
                    new_lat, new_lng = add_jitter(city_lat, city_lng)
                    attempts = 0
                    while (new_lat, new_lng) in used_coords and attempts < 10:
                        new_lat, new_lng = add_jitter(city_lat, city_lng)
                        attempts += 1
                    print(f"    No result, adding jitter: ({company['lat']}, {company['lng']}) -> ({new_lat}, {new_lng})")
                    replacements.append({
                        "name": name,
                        "new_lat": new_lat,
                        "new_lng": new_lng,
                        "lat_value_start": company["lat_value_start"],
                        "lat_value_end": company["lat_value_end"],
                        "lng_value_start": company["lng_value_start"],
                        "lng_value_end": company["lng_value_end"],
                    })
                    used_coords[(new_lat, new_lng)].append(name)

    # Process known corrections that weren't already handled in duplicate groups
    already_replaced = {r["name"] for r in replacements}
    for company in known:
        name = company["name"]
        if name not in already_replaced:
            print(f"\n--- Fixing known correction: {name} ---")
            result = geocode_company(company, cache)
            if result:
                new_lat, new_lng = result
                print(f"    Will update: ({company['lat']}, {company['lng']}) -> ({new_lat}, {new_lng})")
                replacements.append({
                    "name": name,
                    "new_lat": new_lat,
                    "new_lng": new_lng,
                    "lat_value_start": company["lat_value_start"],
                    "lat_value_end": company["lat_value_end"],
                    "lng_value_start": company["lng_value_start"],
                    "lng_value_end": company["lng_value_end"],
                })
            else:
                print(f"    ERROR: Could not geocode {name}")

    # Apply replacements
    if replacements:
        print(f"\n{'=' * 60}")
        print(f"APPLYING {len(replacements)} COORDINATE UPDATES")
        print(f"{'=' * 60}")

        updated_content = update_data_js(content, replacements)

        # Write back
        with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"\nSuccessfully updated {DATA_JS_PATH}")
    else:
        print("\nNo coordinate updates needed.")

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Companies scanned: {len(companies)}")
    print(f"  Duplicate coordinate groups: {len(duplicates)}")
    print(f"  Known corrections: {len(known)}")
    print(f"  Total coordinates updated: {len(replacements)}")
    print(f"  Cache entries: {len(cache)}")


if __name__ == "__main__":
    main()
