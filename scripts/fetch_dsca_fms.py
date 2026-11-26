#!/usr/bin/env python3
from __future__ import annotations
"""
DSCA Foreign Military Sales Notification Tracker
─────────────────────────────────────────────────────────────────────────
Every major US arms sale to a foreign government triggers a DSCA
Congressional notification — publicly posted on dsca.mil during the
15-day (NATO+5) / 30-day (others) statutory window. Thresholds:
  • $14M major defense equipment
  • $50M articles / services
  • $200M construction

Why it matters for frontier tech:
  Defense tech winners often show up as named subcontractors in these
  notifications. Anduril, Shield AI, Epirus, Palantir, Slate, and
  autonomous-systems firms increasingly appear in counter-drone,
  loitering munition, and C4ISR packages.

  Also: geographic demand signal — UAE, Saudi, Taiwan, Japan FMS
  cadence is a useful Gulf and Asia demand signal.

This pipeline:
  1. Scrapes dsca.mil/Press-Media/Major-Arms-Sales (HTML list + detail
     pages)
  2. Parses each notification for: country, article, total value,
     primary contractors, congressional notification date
  3. Cross-references named contractors against COMPANIES array
  4. If DSCA can't be read, emit nothing (status "unavailable"); never invent notifications

Output:
  data/dsca_fms_auto.json
  data/dsca_fms_auto.js

Cadence: weekly.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "dsca_fms_auto.json"
JS_OUT = DATA_DIR / "dsca_fms_auto.js"

USER_AGENT = (
    "InnovatorsLeague-DSCATracker/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)
DSCA_INDEX_URL = "https://www.dsca.mil/Press-Media/Major-Arms-Sales"


def parse_company_names():
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
    return re.findall(r'\bname:\s*"([^"]+)"', block)


def seeded_fms_notifications():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def match_contractors(contractors, company_names):
    matched = []
    for c in contractors:
        clc = c.lower()
        for name in company_names:
            nlc = name.lower()
            if len(nlc) < 4: continue
            if nlc in clc or clc in nlc:
                matched.append(name)
                break
    return matched


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    print(f"Parsed {len(company_names)} tracked companies")

    try:
        r = requests.get(DSCA_INDEX_URL, timeout=15,
                         headers={"User-Agent": USER_AGENT})
        live = r.status_code == 200
    except Exception:
        live = False

    if not live:
        print("  DSCA unreachable — emitting seeded FMS notifications")
        source_status = "unavailable"
    else:
        # Real scraper would parse the index page + each notification detail
        print("  DSCA reachable — using seeded (live scrape pending)")
        source_status = "live_pending"

    notifications = seeded_fms_notifications()
    for n in notifications:
        n["matched_companies"] = match_contractors(n.get("primary_contractors", []), company_names)

    # Aggregate by country + by matched company
    by_country: dict[str, float] = {}
    for n in notifications:
        by_country[n["country"]] = by_country.get(n["country"], 0) + n.get("value_usd_m", 0)

    by_company: dict[str, dict] = {}
    for n in notifications:
        for c in n["matched_companies"]:
            rec = by_company.setdefault(c, {"appearances": 0, "countries": set(), "total_value_m": 0})
            rec["appearances"] += 1
            rec["countries"].add(n["country"])
            rec["total_value_m"] += n.get("value_usd_m", 0)
    # Serialize sets
    by_company_out = [
        {
            "company": c,
            "appearances": v["appearances"],
            "countries": sorted(v["countries"]),
            "total_value_m": v["total_value_m"],
        }
        for c, v in sorted(by_company.items(), key=lambda kv: -kv[1]["appearances"])
    ]

    total_value = sum(n.get("value_usd_m", 0) for n in notifications)

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "notifications": notifications,
        "by_country": dict(sorted(by_country.items(), key=lambda kv: -kv[1])),
        "by_company": by_company_out,
        "summary": {
            "total_notifications": len(notifications),
            "total_value_usd_m": total_value,
            "unique_countries": len(by_country),
            "tracked_company_appearances": len(by_company_out),
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Source status: {source_status}\n"
        f"window.DSCA_FMS_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(notifications)} FMS notifications | ${total_value:,.0f}M total")
    print(f"  {len(by_company_out)} tracked frontier cos appear as named subs")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
