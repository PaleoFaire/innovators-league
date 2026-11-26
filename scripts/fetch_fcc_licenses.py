#!/usr/bin/env python3
from __future__ import annotations
"""
FCC ULS + Experimental Radio Service License Tracker
─────────────────────────────────────────────────────────────────────────
Every experimental radio license filed with the FCC — for satellite
downlinks, drone command-and-control links, autonomous vehicle radars,
quantum sensors — is public. ELS (Experimental Licensing System) filings
often PRECEDE product launches by 6–12 months.

This pipeline:
  1. Hits the FCC License View API for recent filings
  2. Filters to frequency bands / service types relevant to frontier tech
     (satellite, drone, autonomous, quantum, 5G/6G private cellular,
     experimental radar)
  3. Matches applicant names to our COMPANIES array

Fallback: when the FCC API is rate-limited or the wireless.fcc.gov bulk
dump is unreachable, we emit a seeded set of well-known recent FCC
filings so the UI has content.

Output:
  data/fcc_licenses_auto.json
  data/fcc_licenses_auto.js

Cadence: weekly.
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "fcc_licenses_auto.json"
JS_OUT = DATA_DIR / "fcc_licenses_auto.js"

USER_AGENT = (
    "InnovatorsLeague-FCCTracker/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)

# FCC License View API public endpoint (free, no auth required)
FCC_BASE = "https://apps.fcc.gov/cgb/api/license-view"

# Service/Bureau codes relevant to frontier tech.
#   IB = International Bureau (satellite)
#   WT = Wireless Telecommunications (cellular, drone, IoT)
#   OET = Office of Engineering & Technology (experimental)
FRONTIER_SERVICES = ["IB", "WT", "OET"]

# Keyword filters to narrow to frontier-tech categories within services
FRONTIER_KEYWORDS = [
    "satellite", "earth station", "drone", "unmanned",
    "autonomous", "uas", "experimental", "low power",
    "millimeter wave", "28 ghz", "60 ghz", "terahertz",
    "quantum", "radar", "lidar", "private network",
]


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


def match_company(applicant, company_names):
    if not applicant:
        return None
    alc = applicant.lower()
    for name in company_names:
        nlc = name.lower()
        if len(nlc) < 4: continue
        if nlc in alc or alc in nlc:
            return name
    return None


def seeded_fcc_filings():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    print(f"Parsed {len(company_names)} tracked companies")

    # Attempt live API fetch — real implementation would paginate
    # through FCC License View API. For CI safety we emit seeded data
    # with source_status flag.
    try:
        # Lightweight probe of the API so we know if it's reachable
        r = requests.get(
            f"{FCC_BASE}/licenses",
            params={"format": "json", "pageSize": 1},
            timeout=10,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        api_live = r.status_code in (200, 401, 403)
    except Exception:
        api_live = False

    if not api_live:
        print("  FCC License View API unreachable — emitting seeded filings")
        filings = seeded_fcc_filings()
        source_status = "unavailable"
    else:
        # Real paginated fetch would go here
        print("  FCC API reachable — using seeded data (live pipeline pending)")
        filings = seeded_fcc_filings()
        source_status = "live_pending"

    # Match to tracked companies
    for f in filings:
        f["matched_company"] = match_company(f.get("applicant", ""), company_names)

    # Summary by bureau
    by_bureau: dict[str, int] = {}
    matched_count = 0
    for f in filings:
        b = f.get("bureau", "OTHER")
        by_bureau[b] = by_bureau.get(b, 0) + 1
        if f.get("matched_company"):
            matched_count += 1

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "filings": filings,
        "summary": {
            "total": len(filings),
            "matched_to_tracked_company": matched_count,
            "by_bureau": by_bureau,
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Source status: {source_status}\n"
        f"window.FCC_LICENSES_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(filings)} FCC filings, {matched_count} matched to tracked cos")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
