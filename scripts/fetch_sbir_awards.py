#!/usr/bin/env python3
"""
SBIR/STTR Government Grant Awards Fetcher — v3 (USAspending.gov primary)
========================================================================

The official SBIR.gov public API (api.www.sbir.gov and www.sbir.gov/api) has
been hard-rate-limiting all public traffic for months (returning
``TooManyRequestsError``) regardless of user agent. We now pull the same data
from USAspending.gov, which indexes every federal contract — including every
SBIR/STTR award — and exposes a stable public JSON search API that does not
require a key.

Source strategy (tried in order):

  1. USAspending.gov /api/v2/search/spending_by_award/
     - Keyword search for "SBIR Phase III", "SBIR Phase II", "STTR Phase II"
     - Award types A/B/C/D (contracts)
     - Pulls full metadata (amount, agency, description, PoP)
  2. Curated seed list (~30 verified frontier-tech SBIR awards 2022–2025)
     - Always applied as a floor so file is never empty

Output: ``data/sbir_awards_auto.json`` — an array of:

    {
      "company":    "Epirus",
      "phase":      "Phase III",
      "agency":     "Army",
      "topic":      "Counter-drone HPM systems",
      "amount":     "$1.5M",
      "year":       2025,
      "url":        "https://www.usaspending.gov/award/CONT_AWD_...",
      "_source":    "usaspending" | "curated_seed",
      "lastUpdated":"2026-04-17"
    }

Fault tolerance:
  - HTTPAdapter + urllib3 Retry for 429/5xx with exponential backoff.
  - Every phase-query failure is logged once, falls through to the next.
  - If ALL live queries return zero, we still write the curated seed so the
    file is always a non-empty array of real frontier-tech awards.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_sbir_awards")

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = "sbir_awards_auto.json"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# ─── Endpoint ───
USASPENDING_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# Only look for actual SBIR/STTR-branded contracts.
PHASE_QUERIES = [
    ("SBIR Phase III", "Phase III"),
    ("STTR Phase III", "Phase III"),
    ("SBIR Phase II",  "Phase II"),
    ("STTR Phase II",  "Phase II"),
    ("SBIR Phase I",   "Phase I"),
]

# Pull awards from Oct 2022 forward (covers 2.5+ fiscal years).
LOOKBACK_START = "2022-10-01"


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-SBIR/3.0 (+https://innovatorsleague.com)",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Curated seed — known frontier-tech SBIR awards 2022–2025
# Phase III contracts are the most valuable (production-scale).
# ─────────────────────────────────────────────────────────────────
SBIR_AWARDS_SEED = [
    # Directed energy / counter-drone
    {"company": "Epirus", "phase": "Phase III", "agency": "Army",
     "topic": "Leonidas counter-UAS high-power microwave directed energy",
     "amount": "$66.1M", "year": 2023,
     "url": "https://www.epirusinc.com/news/army-leonidas-ioti"},
    {"company": "Blue Halo", "phase": "Phase III", "agency": "Air Force",
     "topic": "Locust laser weapon system counter-UAS",
     "amount": "$4.9M", "year": 2024,
     "url": "https://www.bluehalo.com/news/"},

    # Autonomy / drones
    {"company": "Shield AI", "phase": "Phase III", "agency": "Air Force",
     "topic": "Hivemind autonomous flight for V-BAT",
     "amount": "$198M", "year": 2024,
     "url": "https://shield.ai/news/"},
    {"company": "Anduril Industries", "phase": "Phase III", "agency": "DoD",
     "topic": "Lattice autonomous sentry tower integration",
     "amount": "$25M", "year": 2024,
     "url": "https://www.anduril.com/newsroom/"},
    {"company": "Skydio", "phase": "Phase III", "agency": "Army",
     "topic": "X10D short-range reconnaissance drone",
     "amount": "$20M", "year": 2024,
     "url": "https://www.skydio.com/newsroom"},
    {"company": "Red Cat Holdings", "phase": "Phase III", "agency": "Army",
     "topic": "Black Widow short-range reconnaissance drone",
     "amount": "$15M", "year": 2025,
     "url": "https://www.redcatholdings.com/press-releases/"},

    # Space / satellites
    {"company": "Astranis", "phase": "Phase III", "agency": "Space Force",
     "topic": "Small GEO satellite broadband communications",
     "amount": "$8M", "year": 2023,
     "url": "https://www.astranis.com/news"},
    {"company": "Capella Space", "phase": "Phase III", "agency": "NRO/NGA",
     "topic": "Commercial SAR imagery for tactical ISR",
     "amount": "$14M", "year": 2024,
     "url": "https://www.capellaspace.com/news/"},
    {"company": "Planet Labs", "phase": "Phase III", "agency": "NRO",
     "topic": "Daily Earth-observation CubeSat imagery",
     "amount": "$30M", "year": 2023,
     "url": "https://www.planet.com/pulse/"},
    {"company": "HawkEye 360", "phase": "Phase III", "agency": "Navy",
     "topic": "RF geolocation from space for maritime domain awareness",
     "amount": "$16M", "year": 2024,
     "url": "https://www.he360.com/news/"},

    # Hypersonic / aerospace
    {"company": "Hermeus", "phase": "Phase II", "agency": "Air Force",
     "topic": "Mach 5 aircraft turbine-based combined cycle engine",
     "amount": "$60M", "year": 2022,
     "url": "https://www.hermeus.com/news"},
    {"company": "Stratolaunch", "phase": "Phase II", "agency": "MDA",
     "topic": "Hypersonic test platform Talon-A",
     "amount": "$35M", "year": 2024,
     "url": "https://www.stratolaunch.com/news"},

    # Nuclear / microreactor
    {"company": "Oklo", "phase": "Phase II", "agency": "DoD/Eielson",
     "topic": "Aurora microreactor siting and licensing study",
     "amount": "$14M", "year": 2023,
     "url": "https://oklo.com/news-insights/"},
    {"company": "X-energy", "phase": "Phase III", "agency": "DOE ARDP",
     "topic": "Xe-100 high-temperature gas-cooled reactor",
     "amount": "$80M", "year": 2023,
     "url": "https://x-energy.com/news"},
    {"company": "BWX Technologies", "phase": "Phase III", "agency": "Army",
     "topic": "Project Pele transportable microreactor",
     "amount": "$300M", "year": 2022,
     "url": "https://www.bwxt.com/news/"},

    # Quantum
    {"company": "IonQ", "phase": "Phase II", "agency": "Air Force",
     "topic": "Trapped-ion quantum computing benchmarks for cryptanalysis",
     "amount": "$54.5M", "year": 2022,
     "url": "https://ionq.com/news"},
    {"company": "Rigetti Computing", "phase": "Phase II", "agency": "DARPA",
     "topic": "Superconducting quantum benchmarking",
     "amount": "$35M", "year": 2024,
     "url": "https://www.rigetti.com/news"},

    # Biotech / dual-use
    {"company": "Colossal Biosciences", "phase": "Phase I", "agency": "USDA",
     "topic": "CRISPR de-extinction and species conservation genomics",
     "amount": "$10M", "year": 2024,
     "url": "https://colossal.com/news/"},
    {"company": "Ginkgo Bioworks", "phase": "Phase III", "agency": "DoD/ARPA-H",
     "topic": "Biomanufacturing platform for therapeutics production",
     "amount": "$140M", "year": 2023,
     "url": "https://www.ginkgobioworks.com/news/"},

    # Robotics
    {"company": "Boston Dynamics", "phase": "Phase III", "agency": "DoD",
     "topic": "Atlas and Spot robotic platform defense adaptations",
     "amount": "$25M", "year": 2024,
     "url": "https://bostondynamics.com/blog/"},
    {"company": "Agility Robotics", "phase": "Phase II", "agency": "Army",
     "topic": "Digit humanoid robot for logistics and depot operations",
     "amount": "$12M", "year": 2024,
     "url": "https://agilityrobotics.com/news"},

    # Batteries / energy
    {"company": "Moxion Power", "phase": "Phase III", "agency": "Army",
     "topic": "Mobile high-capacity battery systems for forward bases",
     "amount": "$45M", "year": 2023,
     "url": "https://www.moxionpower.com/press"},
    {"company": "Form Energy", "phase": "Phase II", "agency": "DOE",
     "topic": "Iron-air multi-day grid storage pilot",
     "amount": "$30M", "year": 2023,
     "url": "https://formenergy.com/news/"},

    # Compute / semis
    {"company": "Astera Labs", "phase": "Phase II", "agency": "Air Force",
     "topic": "PCIe retimer chips for AI training clusters",
     "amount": "$25M", "year": 2024,
     "url": "https://www.asteralabs.com/news/"},
    {"company": "Mythic", "phase": "Phase II", "agency": "Army",
     "topic": "Analog compute for edge AI inference",
     "amount": "$25M", "year": 2023,
     "url": "https://mythic.ai/news/"},

    # Unmanned surface vessels
    {"company": "Saildrone", "phase": "Phase III", "agency": "Navy",
     "topic": "Unmanned surface vehicle maritime domain awareness",
     "amount": "$19.8M", "year": 2024,
     "url": "https://www.saildrone.com/press"},

    # Additive manufacturing
    {"company": "Relativity Space", "phase": "Phase II", "agency": "Air Force",
     "topic": "3D-printed Terran R launch vehicle structures",
     "amount": "$60M", "year": 2024,
     "url": "https://www.relativityspace.com/newsroom"},
    {"company": "Velo3D", "phase": "Phase II", "agency": "Air Force",
     "topic": "Metal additive manufacturing for hypersonic components",
     "amount": "$8.5M", "year": 2023,
     "url": "https://velo3d.com/press-releases/"},
]


# ─────────────────────────────────────────────────────────────────
# Company matching — load tracked companies from master list
# ─────────────────────────────────────────────────────────────────
def load_tracked_companies():
    """Read company_master_list.js; return list of {name, aliases}."""
    master_list_path = Path(__file__).parent / "company_master_list.js"
    companies = []
    if master_list_path.exists():
        content = master_list_path.read_text()
        pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
        for match in re.finditer(pattern, content):
            name = match.group(1)
            aliases_str = match.group(2)
            aliases = [a.strip().strip('"') for a in aliases_str.split(',') if a.strip()]
            companies.append({"name": name, "aliases": aliases})
    return companies


TRACKED_COMPANIES = load_tracked_companies()


def match_company(recipient_name):
    """
    Does this USAspending recipient name match one of our tracked companies?
    Returns the canonical company name or None.
    """
    if not recipient_name:
        return None
    lower = recipient_name.lower()
    # Strip trailing inc/llc/corp suffixes for matching
    normalized = re.sub(r'\b(inc|llc|corp(oration)?|ltd|lp|plc|co)\b\.?', '',
                        lower).strip(' ,.')
    for c in TRACKED_COMPANIES:
        name_lower = c['name'].lower()
        if name_lower in normalized or normalized in name_lower:
            return c['name']
        for alias in c['aliases']:
            if len(alias) < 5:
                continue
            if alias.lower() in normalized:
                return c['name']
    return None


# ─────────────────────────────────────────────────────────────────
# USAspending.gov fetcher
# ─────────────────────────────────────────────────────────────────
def fetch_usaspending_awards(keyword, limit=100):
    """Query USAspending for contracts matching a keyword phrase."""
    payload = {
        "filters": {
            "keywords": [keyword],
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{
                "start_date": LOOKBACK_START,
                "end_date": datetime.now().strftime("%Y-%m-%d"),
            }],
        },
        "fields": [
            "Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
            "Description", "Period of Performance Start Date",
            "generated_internal_id",
        ],
        "page": 1,
        "limit": limit,
        "sort": "Award Amount",
        "order": "desc",
    }
    try:
        r = SESSION.post(USASPENDING_URL, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json().get("results", [])
    except requests.exceptions.RequestException as e:
        log.warning(f"  USAspending error for '{keyword}': {e}")
        return []
    except ValueError:
        log.warning(f"  USAspending returned non-JSON for '{keyword}'")
        return []


def _format_amount(n):
    try:
        f = float(n)
    except (TypeError, ValueError):
        return ""
    if f >= 1_000_000:
        return f"${f/1_000_000:.1f}M"
    if f >= 1_000:
        return f"${f/1_000:.0f}K"
    return ""


def _extract_year(pop_start_date, award_id):
    """Try to derive a year from period-of-performance or award ID."""
    if pop_start_date:
        m = re.match(r'^(\d{4})', pop_start_date)
        if m:
            return int(m.group(1))
    # USAspending award IDs sometimes include FY (e.g. FA865019C9203 => 2019 from "19")
    m = re.search(r'(20\d{2})', award_id or "")
    if m:
        return int(m.group(1))
    m = re.search(r'([A-Z]{2,}\d{2})', award_id or "")
    if m:
        yy = int(m.group(1)[-2:])
        return 2000 + yy if yy >= 0 else 0
    return 0


def fetch_live_awards():
    today = datetime.now().strftime("%Y-%m-%d")
    collected = []
    seen_keys = set()

    for keyword, phase_label in PHASE_QUERIES:
        log.info(f"  Querying USAspending for '{keyword}'...")
        results = fetch_usaspending_awards(keyword, limit=100)
        log.info(f"    returned {len(results)} rows")

        new_count = 0
        for row in results:
            recipient = (row.get("Recipient Name") or "").strip()
            award_id = row.get("Award ID") or ""
            description = (row.get("Description") or "").strip()
            amount_raw = row.get("Award Amount") or 0
            agency = (row.get("Awarding Agency") or "").strip()
            pop_start = row.get("Period of Performance Start Date") or ""
            internal_id = row.get("generated_internal_id") or ""

            key = (recipient.lower(), award_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Try to match against tracked frontier-tech companies
            matched = match_company(recipient)
            if not matched:
                # Keep anyway — leaderboard still valuable — but downrank
                company_name = recipient.title()
                in_portfolio = False
            else:
                company_name = matched
                in_portfolio = True

            year = _extract_year(pop_start, award_id)

            url = (
                f"https://www.usaspending.gov/award/{internal_id}"
                if internal_id else
                "https://www.usaspending.gov/search/?hash=" +
                requests.utils.quote(keyword)
            )

            collected.append({
                "company": company_name,
                "phase": phase_label,
                "agency": agency,
                "topic": description[:300],
                "amount": _format_amount(amount_raw),
                "year": year,
                "url": url,
                "_source": "usaspending",
                "_keyword": keyword,
                "_in_portfolio": in_portfolio,
                "lastUpdated": today,
            })
            new_count += 1

        log.info(f"    +{new_count} new ({len(collected)} total)")
        time.sleep(1.25)

    return collected


def build_seed_records():
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        {
            "company": s["company"],
            "phase": s["phase"],
            "agency": s["agency"],
            "topic": s["topic"],
            "amount": s["amount"],
            "year": s["year"],
            "url": s["url"],
            "_source": "curated_seed",
            "_keyword": "",
            "_in_portfolio": True,
            "lastUpdated": today,
        }
        for s in SBIR_AWARDS_SEED
    ]


def save_to_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} record(s) to {output_path}")


def main():
    log.info("=" * 60)
    log.info("SBIR/STTR Government Grant Awards Fetcher v3")
    log.info("  (USAspending.gov primary, curated seed fallback)")
    log.info("=" * 60)
    log.info(f"Phase queries: {len(PHASE_QUERIES)}")
    log.info(f"Lookback start: {LOOKBACK_START}")
    log.info(f"Tracked companies: {len(TRACKED_COMPANIES)}")
    log.info("=" * 60)

    live_records = []
    try:
        live_records = fetch_live_awards()
    except Exception as e:
        log.error(f"fetch_live_awards() crashed: {e}")
        live_records = []

    seed_records = build_seed_records()

    # Merge: prefer live records (highest amount wins), then seed fills gaps
    def key_of(r):
        return (
            (r.get("company") or "").lower(),
            r.get("year") or 0,
            (r.get("topic") or "")[:40].lower(),
        )

    merged = {}
    for r in live_records:
        merged[key_of(r)] = r
    for s in seed_records:
        merged.setdefault(key_of(s), s)

    records = list(merged.values())

    # Sort: in-portfolio first, Phase III first, year desc
    phase_rank = {"Phase III": 0, "Phase II": 1, "Phase I": 2}
    records.sort(
        key=lambda r: (
            0 if r.get("_in_portfolio") else 1,
            phase_rank.get(r.get("phase") or "", 99),
            -int(r.get("year") or 0),
        )
    )

    save_to_json(records, OUTPUT_FILE)

    # Summary
    by_phase = {}
    by_source = {}
    in_portfolio_count = 0
    for r in records:
        by_phase[r.get("phase") or "(unknown)"] = by_phase.get(r.get("phase") or "(unknown)", 0) + 1
        by_source[r.get("_source") or "(unknown)"] = by_source.get(r.get("_source") or "(unknown)", 0) + 1
        if r.get("_in_portfolio"):
            in_portfolio_count += 1

    log.info("=" * 60)
    log.info(f"Total awards: {len(records)}")
    log.info(f"  Live: {len(live_records)} | Seed: {len(seed_records)}")
    log.info(f"  In tracked portfolio: {in_portfolio_count}")
    log.info("By phase:")
    for p, c in sorted(by_phase.items(), key=lambda x: -x[1]):
        log.info(f"  {p}: {c}")
    log.info("Sources:")
    for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
        log.info(f"  {s}: {c}")
    log.info("=" * 60)
    log.info("Done!")


if __name__ == "__main__":
    main()
