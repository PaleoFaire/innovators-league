#!/usr/bin/env python3
"""
Audit COMPANIES.location text against COMPANIES.lat/lng for self-inconsistency.

How it works:
  1. Group companies by location string (e.g., "Austin, TX") and collect
     all the lat/lng values used for that location.
  2. Compute the median (consensus) coords per location string.
  3. For each company, compute the haversine distance between its claimed
     coords and the median coords for its location.
  4. Flag anything more than THRESHOLD_MILES off as suspicious.
  5. Also seed with a curated table of known major cities so single-entry
     locations are still validated.

This is meta-analysis: the DB flags its own inconsistencies. Surfaces
the same class of bug as Galadyne (location said Houston, coords were
Austin).

Usage:
  python scripts/audit_location_consistency.py [--top N]
"""
import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent

# Distance threshold (miles) for flagging
THRESHOLD_MILES = 50

# Curated reference for the most common locations — used when a location
# only has 1 entry and there's no internal consensus to compare against.
KNOWN_CITY_COORDS = {
    # United States
    "san francisco, ca":      (37.7749, -122.4194),
    "palo alto, ca":          (37.4419, -122.1430),
    "menlo park, ca":         (37.4530, -122.1817),
    "mountain view, ca":      (37.3861, -122.0839),
    "redwood city, ca":       (37.4852, -122.2364),
    "sunnyvale, ca":          (37.3688, -122.0363),
    "santa clara, ca":        (37.3541, -121.9552),
    "san jose, ca":           (37.3382, -121.8863),
    "oakland, ca":            (37.8044, -122.2712),
    "berkeley, ca":           (37.8715, -122.2730),
    "alameda, ca":            (37.7652, -122.2416),
    "los angeles, ca":        (34.0522, -118.2437),
    "el segundo, ca":         (33.9192, -118.4165),
    "torrance, ca":           (33.8358, -118.3406),
    "redondo beach, ca":      (33.8492, -118.3884),
    "long beach, ca":         (33.7701, -118.1937),
    "huntington beach, ca":   (33.6603, -117.9992),
    "irvine, ca":             (33.6846, -117.8265),
    "san diego, ca":          (32.7157, -117.1611),
    "culver city, ca":        (34.0211, -118.3965),
    "marina del rey, ca":     (33.9802, -118.4517),
    "playa vista, ca":        (33.9706, -118.4218),
    "san mateo, ca":          (37.5630, -122.3255),
    "south san francisco, ca":(37.6547, -122.4077),
    "boston, ma":             (42.3601, -71.0589),
    "cambridge, ma":          (42.3736, -71.1097),
    "somerville, ma":         (42.3876, -71.0995),
    "new york, ny":           (40.7128, -74.0060),
    "manhattan, ny":          (40.7831, -73.9712),
    "brooklyn, ny":           (40.6782, -73.9442),
    "austin, tx":             (30.2672, -97.7431),
    "houston, tx":            (29.7604, -95.3698),
    "dallas, tx":             (32.7767, -96.7970),
    "san antonio, tx":        (29.4241, -98.4936),
    "midland, tx":            (31.9974, -102.0779),
    "seattle, wa":             (47.6062, -122.3321),
    "redmond, wa":            (47.6740, -122.1215),
    "bellevue, wa":           (47.6101, -122.2015),
    "denver, co":             (39.7392, -104.9903),
    "boulder, co":            (40.0150, -105.2705),
    "salt lake city, ut":     (40.7608, -111.8910),
    "chicago, il":            (41.8781, -87.6298),
    "atlanta, ga":            (33.7490, -84.3880),
    "miami, fl":              (25.7617, -80.1918),
    "orlando, fl":            (28.5383, -81.3792),
    "philadelphia, pa":       (39.9526, -75.1652),
    "pittsburgh, pa":         (40.4406, -79.9959),
    "washington, dc":         (38.9072, -77.0369),
    "arlington, va":          (38.8816, -77.0910),
    "alexandria, va":         (38.8048, -77.0469),
    "minneapolis, mn":        (44.9778, -93.2650),
    "phoenix, az":            (33.4484, -112.0740),
    "las vegas, nv":          (36.1699, -115.1398),
    "raleigh, nc":            (35.7796, -78.6382),
    "durham, nc":             (35.9940, -78.8986),

    # International
    "london, uk":             (51.5074, -0.1278),
    "london, england":        (51.5074, -0.1278),
    "london, united kingdom": (51.5074, -0.1278),
    "berlin, germany":        (52.5200, 13.4050),
    "munich, germany":        (48.1351, 11.5820),
    "paris, france":          (48.8566, 2.3522),
    "tel aviv, israel":       (32.0853, 34.7818),
    "haifa, israel":          (32.7940, 34.9896),
    "tokyo, japan":           (35.6762, 139.6503),
    "singapore":              (1.3521, 103.8198),
    "toronto, canada":        (43.6532, -79.3832),
    "vancouver, canada":      (49.2827, -123.1207),
    "montreal, canada":       (45.5017, -73.5673),
    "sydney, australia":      (-33.8688, 151.2093),
    "stockholm, sweden":      (59.3293, 18.0686),
    "amsterdam, netherlands": (52.3676, 4.9041),
    "zurich, switzerland":    (47.3769, 8.5417),
    "abu dhabi, uae":         (24.4539, 54.3773),
    "abu dhabi, united arab emirates": (24.4539, 54.3773),
    "dubai, uae":             (25.2048, 55.2708),
}


def haversine_miles(lat1, lng1, lat2, lng2):
    """Great-circle distance between two points (miles)."""
    R = 3958.8  # Earth radius in miles
    lat1_r, lng1_r = math.radians(lat1), math.radians(lng1)
    lat2_r, lng2_r = math.radians(lat2), math.radians(lng2)
    dlat, dlng = lat2_r - lat1_r, lng2_r - lng1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_companies_with_coords():
    """Extract every company with location + lat/lng."""
    src = (ROOT / "data.js").read_text(encoding="utf-8")
    m = re.search(r"const COMPANIES\s*=\s*\[", src)
    start = m.end() - 1
    depth = 0; in_str = False; str_q = None
    for i in range(start, len(src)):
        c = src[i]
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]
                    break

    companies = []
    obj_depth = 0; obj_start = None; in_str = False; str_q = None
    for i, c in enumerate(block):
        if in_str:
            if c == "\\": continue
            if c == str_q: in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True; str_q = c
            elif c == "{":
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif c == "}":
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i+1]
                    nm = re.search(r'name:\s*"([^"]+)"', obj)
                    loc = re.search(r'location:\s*"([^"]+)"', obj)
                    lat = re.search(r'\blat:\s*(-?\d+\.?\d*)', obj)
                    lng = re.search(r'\blng:\s*(-?\d+\.?\d*)', obj)
                    if nm and loc and lat and lng:
                        try:
                            companies.append({
                                "name": nm.group(1),
                                "location": loc.group(1),
                                "lat": float(lat.group(1)),
                                "lng": float(lng.group(1)),
                            })
                        except ValueError:
                            pass
                    obj_start = None
    return companies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=50, help="show top N mismatches")
    ap.add_argument("--threshold", type=int, default=THRESHOLD_MILES,
                    help="distance threshold (miles) to flag")
    args = ap.parse_args()

    print("=" * 64)
    print("Location Consistency Audit")
    print("=" * 64)

    companies = parse_companies_with_coords()
    print(f"  Companies w/ location + lat/lng: {len(companies)}")

    # Build internal consensus per location (median of >= 2 entries)
    grouped = defaultdict(list)
    for c in companies:
        grouped[c["location"].lower().strip()].append(c)

    consensus = {}
    for loc, cos in grouped.items():
        if len(cos) >= 2:
            consensus[loc] = (
                median(c["lat"] for c in cos),
                median(c["lng"] for c in cos),
            )

    print(f"  Locations with internal consensus (≥2 entries): {len(consensus)}")
    print(f"  Curated city table: {len(KNOWN_CITY_COORDS)} entries")

    # For each company, compute distance from the best reference
    flagged = []
    no_reference = []
    for c in companies:
        loc_key = c["location"].lower().strip()

        # Prefer curated city table; fall back to internal consensus
        ref = KNOWN_CITY_COORDS.get(loc_key) or consensus.get(loc_key)
        if not ref:
            no_reference.append(c)
            continue

        dist = haversine_miles(c["lat"], c["lng"], ref[0], ref[1])
        if dist > args.threshold:
            flagged.append({
                **c,
                "distance_miles": round(dist, 1),
                "expected_lat": ref[0],
                "expected_lng": ref[1],
                "reference_source": ("curated" if KNOWN_CITY_COORDS.get(loc_key)
                                     else "internal_consensus"),
            })

    flagged.sort(key=lambda x: -x["distance_miles"])

    print(f"\n  ⚠ MISMATCHES (>{args.threshold} miles off): {len(flagged)}")
    print(f"  No reference available:                   {len(no_reference)}")
    print()

    if flagged:
        print(f"  {'Company':<32}  {'Claimed location':<26}  {'Off (mi)':>9}  {'Source':<22}")
        print("  " + "-" * 96)
        for f in flagged[:args.top]:
            print(f"  {f['name'][:30]:<32}  {f['location'][:24]:<26}  {f['distance_miles']:>9.0f}  {f['reference_source']:<22}")
        if len(flagged) > args.top:
            print(f"  ... and {len(flagged) - args.top} more")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
