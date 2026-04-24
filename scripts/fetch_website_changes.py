#!/usr/bin/env python3
from __future__ import annotations
"""
Wayback Machine / Website Change Detector
─────────────────────────────────────────────────────────────────────────
Every frontier-tech company's homepage is archived weekly by the Internet
Archive. The Wayback CDX API returns up to 10,000 snapshots per URL with
content hashes — so we can detect CHANGES between snapshots for free.

Why it matters:
  • Exec departures show up on the Team page before the press release
  • Product pivots show up on the Home page before the PR
  • Customer wins appear on the logo wall before the announcement
  • Hiring acceleration shows up as a spike in jobs page listings
  • Pricing pivots appear (e.g., "transparent" → "Contact Us")

For each of the ~60 companies with a website field populated, we:
  1. Query Wayback CDX for the last 10 snapshots of their homepage
  2. Detect content-hash changes (simhash-style but using WARC checksums)
  3. When a hash change is detected in the last 30 days, flag a "website
     change" event for that company.

Output:
  data/website_changes_auto.json
  data/website_changes_auto.js

The raw hash change isn't meaningful by itself — the VALUE is in knowing
which companies changed SOMETHING recently, so a human (or an AI skill
layer) can go look at the diff. This pipeline is a trigger, not an
analyst.

Cadence: weekly.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "website_changes_auto.json"
JS_OUT = DATA_DIR / "website_changes_auto.js"

USER_AGENT = (
    "InnovatorsLeague-WebsiteChangeDetector/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
# Days of history to consider; snapshots older than this are ignored
RECENT_WINDOW_DAYS = 90
# Max companies to probe per run (rate-limit friendliness)
MAX_PROBES = 200
# Delay between Wayback requests
THROTTLE_SEC = 0.6


def parse_companies_with_website():
    """Return (name, website) for every company in data.js that has a
    populated website field."""
    try:
        text = DATA_JS.read_text()
    except Exception:
        return []
    start = text.find("const COMPANIES = [")
    if start < 0: return []
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i + 1: end]

    # Split on top-level {...} entries
    entries = []
    idx = 0; n = len(block); d = 0
    in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        start = idx
        while idx < n:
            c = block[idx]
            if esc: esc = False; idx += 1; continue
            if c == "\\" and in_str: esc = True; idx += 1; continue
            if in_str:
                if c == sc: in_str = False
                idx += 1; continue
            if c in "\"'": in_str = True; sc = c; idx += 1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: idx += 1; entries.append(block[start:idx]); break
            idx += 1

    result = []
    for e in entries:
        nm = re.search(r'\bname:\s*"([^"]+)"', e)
        wb = re.search(r'\bwebsite:\s*"([^"]+)"', e)
        if nm and wb and wb.group(1).startswith("http"):
            result.append((nm.group(1), wb.group(1)))
    return result


def probe_wayback(url, limit=10):
    """Return list of (timestamp, sha1) snapshots ordered newest first.
    Empty list on any error."""
    try:
        params = {
            "url": url,
            "output": "json",
            "limit": limit,
            "fl": "timestamp,digest",
            "collapse": "digest",  # only unique content hashes
            "filter": "statuscode:200",
        }
        r = requests.get(
            WAYBACK_CDX, params=params, timeout=25,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code != 200:
            return []
        rows = r.json()
        if len(rows) < 2:
            return []
        # rows[0] is header ["timestamp", "digest"]
        out = []
        for row in rows[1:]:
            if len(row) >= 2:
                out.append({"timestamp": row[0], "digest": row[1]})
        # newest first
        out.sort(key=lambda x: -int(x["timestamp"]))
        return out
    except Exception:
        return []


def summarize_change(name, url, snapshots):
    """Given the snapshot list, produce a per-company change summary."""
    if len(snapshots) < 2:
        return {
            "company": name,
            "url": url,
            "snapshots_seen": len(snapshots),
            "change_in_window": False,
            "latest_snapshot": snapshots[0]["timestamp"] if snapshots else None,
            "latest_digest": snapshots[0]["digest"] if snapshots else None,
            "prior_digest": None,
        }
    latest = snapshots[0]
    prior = snapshots[1]
    # Was latest snapshot within the recent window?
    now = datetime.now(tz=timezone.utc)
    try:
        latest_dt = datetime.strptime(latest["timestamp"][:8], "%Y%m%d").replace(tzinfo=timezone.utc)
    except Exception:
        latest_dt = None
    recent = bool(
        latest_dt and (now - latest_dt).days <= RECENT_WINDOW_DAYS
        and latest["digest"] != prior["digest"]
    )
    return {
        "company": name,
        "url": url,
        "snapshots_seen": len(snapshots),
        "change_in_window": recent,
        "latest_snapshot": latest["timestamp"],
        "latest_digest": latest["digest"],
        "prior_digest": prior["digest"],
        "snapshots": snapshots[:5],  # include 5 recent for UI
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)
    companies = parse_companies_with_website()
    print(f"Found {len(companies)} companies with a website field")

    if len(companies) > MAX_PROBES:
        print(f"  Capping at {MAX_PROBES} probes for this run")
        companies = companies[:MAX_PROBES]

    results = []
    for i, (name, url) in enumerate(companies, 1):
        snapshots = probe_wayback(url)
        result = summarize_change(name, url, snapshots)
        results.append(result)
        if result["change_in_window"]:
            print(f"  [{i}/{len(companies)}] {name}: CHANGE DETECTED")
        else:
            print(f"  [{i}/{len(companies)}] {name}: no recent change")
        time.sleep(THROTTLE_SEC)

    changes = [r for r in results if r["change_in_window"]]
    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "probed_count": len(results),
        "change_count": len(changes),
        "recent_window_days": RECENT_WINDOW_DAYS,
        "changes": changes,
        "all_results": results,  # full detail for admin
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"window.WEBSITE_CHANGES_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(changes)}/{len(results)} companies had website changes in last {RECENT_WINDOW_DAYS}d")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
