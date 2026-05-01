#!/usr/bin/env python3
"""
Fix lat/lng for companies flagged by audit_location_consistency.py.

Strategy: trust the location TEXT field (typically curator-maintained
or manually verified) and reset lat/lng to the curated city coords for
that location. Companies whose location is unusual or international
without a curated reference are skipped (not auto-fixed).

Same threshold as the audit. Reports every change for review.

Usage:
  python scripts/fix_location_coords.py [--dry-run]
"""
import argparse
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "scripts"))
from audit_location_consistency import (
    KNOWN_CITY_COORDS, haversine_miles, parse_companies_with_coords, THRESHOLD_MILES
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--threshold", type=int, default=THRESHOLD_MILES)
    args = ap.parse_args()

    print("=" * 60)
    print(f"Fix location coords — {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("=" * 60)

    companies = parse_companies_with_coords()
    src = (ROOT / "data.js").read_text(encoding="utf-8")

    fixes = []
    for c in companies:
        loc_key = c["location"].lower().strip()
        ref = KNOWN_CITY_COORDS.get(loc_key)
        if not ref:
            continue
        dist = haversine_miles(c["lat"], c["lng"], ref[0], ref[1])
        if dist <= args.threshold:
            continue   # already correct enough
        fixes.append({
            "name": c["name"],
            "location": c["location"],
            "old_lat": c["lat"], "old_lng": c["lng"],
            "new_lat": ref[0],   "new_lng": ref[1],
            "distance": dist,
        })

    fixes.sort(key=lambda x: -x["distance"])

    if not fixes:
        print("  No fixable mismatches found")
        return 0

    print(f"  Found {len(fixes)} companies with curated-table-correctable coords")
    print()
    print(f"  {'Company':<28}  {'Location':<24}  {'Off':>7}  {'Old → New coords'}")
    print("  " + "-" * 95)
    for f in fixes:
        print(f"  {f['name'][:26]:<28}  {f['location'][:22]:<24}  {f['distance']:>5.0f}mi  "
              f"({f['old_lat']:>7.3f}, {f['old_lng']:>9.3f}) → ({f['new_lat']:>7.3f}, {f['new_lng']:>9.3f})")
    print()

    if args.dry_run:
        print("  [DRY RUN] data.js NOT modified")
        return 0

    # Apply: locate each company's lat/lng line and replace
    for f in fixes:
        nm = re.escape(f["name"])
        # Find the company's object
        m = re.search(rf'name:\s*"{nm}"', src)
        if not m:
            print(f"  ⚠ {f['name']} not found by name match")
            continue
        op = src.rfind("{", 0, m.start())
        depth = 0; in_str = False; q = None
        cp = None
        for i in range(op, len(src)):
            cc = src[i]
            if in_str:
                if cc == "\\": continue
                if cc == q: in_str = False
            else:
                if cc in ('"', "'", "`"):
                    in_str = True; q = cc
                elif cc == "{":
                    depth += 1
                elif cc == "}":
                    depth -= 1
                    if depth == 0:
                        cp = i; break
        if cp is None:
            continue
        obj = src[op:cp+1]

        # Replace lat: X and lng: Y (handle both "lat: X, lng: Y" same-line and split-line)
        new_obj = re.sub(
            r"\blat:\s*-?\d+\.?\d*",
            f"lat: {f['new_lat']}",
            obj,
            count=1,
        )
        new_obj = re.sub(
            r"\blng:\s*-?\d+\.?\d*",
            f"lng: {f['new_lng']}",
            new_obj,
            count=1,
        )
        if new_obj != obj:
            src = src[:op] + new_obj + src[cp+1:]

    (ROOT / "data.js").write_text(src, encoding="utf-8")
    print(f"  ✅ data.js updated — {len(fixes)} coordinate fixes applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
