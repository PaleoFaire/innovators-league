#!/usr/bin/env python3
"""
DOE / EIA Energy Data Fetcher
=============================
Tracks major Department of Energy programs (nuclear, fusion, microreactors,
advanced reactors) and — if EIA_API_KEY is present — live EIA nuclear
generation statistics.

Fault tolerance:
  - Tries three DOE endpoints (two JSON, one HTML scrape).
  - Always writes at least the hardcoded FY2026 program list so the output
    is never empty.
  - Logs WHY no data came back (vs. silently succeeding with a stale file).

Output:
  data/doe_programs_raw.json     (list of programs, always non-empty)
  data/doe_programs_auto.js      (JS snippet consumed by merge_data.py)
  data/eia_statistics_raw.json   (list, present only when EIA_API_KEY set)
"""

import json
import os
import re
import time
import logging
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
log = logging.getLogger("fetch_doe_energy")

DATA_DIR = Path(__file__).parent.parent / "data"

EIA_API_KEY = os.environ.get("EIA_API_KEY", "").strip()

DOE_JSON_ENDPOINTS = [
    "https://api.energy.gov/v2/programs",
    "https://openei.org/services/api/programs",
]
DOE_HTML_ENDPOINT = "https://www.energy.gov/eere/programs"

OSTI_API_BASE = "https://www.osti.gov/api/v1"

REQUEST_TIMEOUT = 30


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-DOEFetcher/2.0",
        "Accept": "application/json, text/html",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Hardcoded FY2026 DOE program list (updated fallback)
# ─────────────────────────────────────────────────────────────────
FY2026_DOE_PROGRAMS = [
    {
        "program": "Advanced Reactor Demonstration Program (ARDP)",
        "agency": "DOE Office of Nuclear Energy",
        "companies": ["TerraPower", "X-energy", "Kairos Power", "Westinghouse"],
        "funding": "3.2B",
        "status": "Active",
        "description": "Funding for advanced reactor demonstrations (Natrium, Xe-100).",
        "lastUpdate": "2026-04-01",
    },
    {
        "program": "HALEU Availability Program",
        "agency": "DOE Office of Nuclear Energy",
        "companies": ["Centrus Energy", "Urenco", "General Matter"],
        "funding": "2.7B",
        "status": "Expanded FY2026",
        "description": "High-assay low-enriched uranium production — 2026 appropriation boosted to $2.7B.",
        "lastUpdate": "2026-03-15",
    },
    {
        "program": "Fusion Energy Sciences",
        "agency": "DOE Office of Science",
        "companies": ["Commonwealth Fusion Systems", "TAE Technologies", "Helion", "General Fusion", "Zap Energy"],
        "funding": "915M",
        "status": "Active",
        "description": "Fusion R&D; FY2026 appropriation includes $58M for the Fusion Innovation Research Engine (FIRE).",
        "lastUpdate": "2026-03-28",
    },
    {
        "program": "Nuclear Thermal Propulsion (NTP)",
        "agency": "NASA/DOE",
        "companies": ["BWXT", "Lockheed Martin", "Aerojet Rocketdyne"],
        "funding": "500M",
        "status": "Active",
        "description": "Nuclear propulsion for deep space missions (DRACO follow-on).",
        "lastUpdate": "2026-02-10",
    },
    {
        "program": "Microreactor Program",
        "agency": "DOE/DoD",
        "companies": ["Oklo", "Radiant", "Westinghouse", "X-energy", "Antares", "Last Energy"],
        "funding": "250M",
        "status": "Expanded FY2026",
        "description": "Transportable microreactors (DoD Project Pele, DOE MARVEL).",
        "lastUpdate": "2026-03-20",
    },
    {
        "program": "Civil Nuclear Credit Program",
        "agency": "DOE Office of Nuclear Energy",
        "companies": ["Constellation Energy", "Vistra", "Holtec"],
        "funding": "6.0B",
        "status": "Active",
        "description": "Preserves at-risk U.S. reactors via credit auctions (Palisades restart).",
        "lastUpdate": "2026-02-25",
    },
    {
        "program": "Loan Programs Office (LPO) — Title 17",
        "agency": "DOE Loan Programs Office",
        "companies": ["Holtec Palisades", "TerraPower Natrium", "X-energy", "Monolith"],
        "funding": "400B",
        "status": "Active",
        "description": "Loan guarantees for innovative energy projects; ~$400B lending authority.",
        "lastUpdate": "2026-04-05",
    },
    {
        "program": "SMR Licensing and Demonstration",
        "agency": "DOE Office of Nuclear Energy",
        "companies": ["NuScale", "Holtec", "GE-Hitachi", "TerraPower"],
        "funding": "900M",
        "status": "Active",
        "description": "Support for NRC licensing of first-of-a-kind small modular reactors.",
        "lastUpdate": "2026-03-01",
    },
    {
        "program": "Gateway for Accelerated Innovation in Nuclear (GAIN)",
        "agency": "DOE Idaho National Lab",
        "companies": ["Oklo", "Radiant", "Kairos Power", "Westinghouse"],
        "funding": "35M",
        "status": "Active",
        "description": "Vouchers giving nuclear startups access to national lab expertise.",
        "lastUpdate": "2026-01-10",
    },
    {
        "program": "Industrial Demonstrations Program (IDP)",
        "agency": "DOE Office of Clean Energy Demonstrations",
        "companies": ["Cleveland-Cliffs", "Century Aluminum", "Heidelberg Materials"],
        "funding": "6.3B",
        "status": "Active",
        "description": "Large-scale decarbonization demonstrations in heavy industry.",
        "lastUpdate": "2026-02-20",
    },
    {
        "program": "Hydrogen Hubs (H2Hubs)",
        "agency": "DOE Office of Clean Energy Demonstrations",
        "companies": ["Air Products", "Plug Power", "Linde"],
        "funding": "7.0B",
        "status": "Active",
        "description": "Seven regional clean hydrogen hubs across the U.S.",
        "lastUpdate": "2026-03-05",
    },
    {
        "program": "Grid Resilience and Innovation Partnerships (GRIP)",
        "agency": "DOE Grid Deployment Office",
        "companies": [],
        "funding": "10.5B",
        "status": "Active",
        "description": "Upgrades to transmission, storage and grid hardening.",
        "lastUpdate": "2026-02-15",
    },
]


def _safe_get(url, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    try:
        resp = SESSION.get(url, **kwargs)
    except requests.exceptions.RequestException as e:
        log.warning(f"  {url}: connection error: {e}")
        return None
    if not resp.ok:
        log.warning(f"  {url}: HTTP {resp.status_code}")
        return None
    return resp


# ─────────────────────────────────────────────────────────────────
# Live endpoints
# ─────────────────────────────────────────────────────────────────
def fetch_doe_json_endpoint(url):
    resp = _safe_get(url)
    if resp is None:
        return []
    try:
        data = resp.json()
    except ValueError:
        log.warning(f"  {url}: non-JSON response")
        return []
    # shape: {"programs": [...]} or {"data": [...]}
    for key in ("programs", "data", "results", "items"):
        if key in data and isinstance(data[key], list):
            return data[key]
    if isinstance(data, list):
        return data
    log.info(f"  {url}: JSON had no known list key")
    return []


def scrape_doe_html(url):
    """Minimal HTML scrape of the EERE programs page (short timeout — don't hang)."""
    resp = _safe_get(url, timeout=15)
    if resp is None:
        return []
    html = resp.text
    items = []
    # Look for program cards: <a class="program-link" ...>Program Name</a>
    for m in re.finditer(
        r'<h[23][^>]*>\s*<a\s+[^>]*href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>\s*</h[23]>',
        html,
    ):
        title = m.group(2).strip()
        link = m.group(1).strip()
        if title and len(title) > 5:
            items.append({
                "program": title,
                "agency": "DOE",
                "companies": [],
                "funding": "",
                "status": "Active",
                "description": "",
                "lastUpdate": datetime.now().strftime("%Y-%m-%d"),
                "source_url": link,
            })
    return items


def fetch_live_doe_programs():
    """Try each live endpoint. Return combined deduped list (possibly empty)."""
    seen_names = set()
    combined = []

    # Tier 1/2: JSON APIs
    for url in DOE_JSON_ENDPOINTS:
        log.info(f"  Trying {url}")
        programs = fetch_doe_json_endpoint(url)
        if not programs:
            continue
        for p in programs:
            name = (p.get("program") or p.get("name") or p.get("title") or "").strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            combined.append({
                "program": name,
                "agency": p.get("agency", "DOE"),
                "companies": p.get("companies", []) or [],
                "funding": str(p.get("funding", "") or p.get("amount", "")),
                "status": p.get("status", "Active"),
                "description": p.get("description", "") or p.get("summary", ""),
                "lastUpdate": p.get("lastUpdate") or p.get("updated") or datetime.now().strftime("%Y-%m-%d"),
                "source_url": p.get("url", ""),
            })
        if combined:
            log.info(f"  Got {len(combined)} programs from {url}")
            return combined

    # Tier 3: HTML scrape
    log.info(f"  Trying HTML scrape of {DOE_HTML_ENDPOINT}")
    scraped = scrape_doe_html(DOE_HTML_ENDPOINT)
    if scraped:
        log.info(f"  Scraped {len(scraped)} programs from HTML")
        return scraped

    return []


# ─────────────────────────────────────────────────────────────────
# Merge live + hardcoded list (idempotent)
# ─────────────────────────────────────────────────────────────────
def merge_programs(live, fallback):
    """
    Merge live DOE data with the hardcoded FY2026 list.
    - Live programs override fallback if names match (case-insensitive).
    - Hardcoded list ensures we ALWAYS have at least ~12 quality records.
    Idempotent: running twice yields the same file.
    """
    by_key = {p["program"].lower(): p for p in fallback}
    for p in live:
        key = p["program"].lower()
        if key in by_key:
            # Merge: keep fallback richness, update lastUpdate and description
            base = dict(by_key[key])
            if p.get("description"):
                base["description"] = p["description"]
            base["lastUpdate"] = p.get("lastUpdate", base["lastUpdate"])
            if p.get("status"):
                base["status"] = p["status"]
            if p.get("source_url"):
                base["source_url"] = p["source_url"]
            by_key[key] = base
        else:
            by_key[key] = p
    return list(by_key.values())


# ─────────────────────────────────────────────────────────────────
# EIA statistics
# ─────────────────────────────────────────────────────────────────
def fetch_eia_statistics():
    if not EIA_API_KEY:
        log.info("  No EIA_API_KEY — skipping EIA stats. Get a free key at https://www.eia.gov/opendata/register.php")
        return []

    stats = []
    url = "https://api.eia.gov/v2/electricity/state-electricity-profiles/source-disposition/data/"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "annual",
        "data[0]": "nuclear-gwh",
        "facets[stateId][]": "US",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5,
    }
    try:
        resp = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        log.warning(f"  EIA connection error: {e}")
        return stats
    if not resp.ok:
        log.warning(f"  EIA HTTP {resp.status_code}")
        return stats
    try:
        data = resp.json()
    except ValueError:
        log.warning("  EIA returned non-JSON")
        return stats
    stats.append({
        "metric": "US Nuclear Generation",
        "source": "EIA",
        "data": data.get("response", {}).get("data", []),
    })
    return stats


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_to_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    count = len(data) if isinstance(data, list) else 1
    log.info(f"Saved {count} records to {output_path}")


def generate_js_snippet(programs):
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [
        "// Auto-updated DOE nuclear/energy programs",
        f"// Last updated: {today}",
        "const DOE_PROGRAMS = [",
    ]
    for p in programs:
        companies = ", ".join(p.get("companies", []))
        program = p["program"].replace('"', '\\"')
        agency = p.get("agency", "").replace('"', '\\"')
        description = (p.get("description") or "").replace('"', '\\"').replace("\n", " ")[:200]
        lines.append("  {")
        lines.append(f'    program: "{program}",')
        lines.append(f'    agency: "{agency}",')
        lines.append(f'    companies: "{companies}",')
        lines.append(f'    funding: "{p.get("funding", "")}",')
        lines.append(f'    status: "{p.get("status", "Active")}",')
        lines.append(f'    description: "{description}",')
        lines.append(f'    lastUpdate: "{p.get("lastUpdate", "")}",')
        lines.append("  },")
    lines.append("];")

    output_path = DATA_DIR / "doe_programs_auto.js"
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    log.info(f"Generated JS snippet at {output_path}")


def main():
    log.info("=" * 60)
    log.info("DOE/EIA Energy Data Fetcher")
    log.info("=" * 60)
    log.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Endpoints: {DOE_JSON_ENDPOINTS + [DOE_HTML_ENDPOINT]}")
    log.info(f"EIA_API_KEY: {'set' if EIA_API_KEY else 'not set'}")
    log.info("=" * 60)

    log.info("Fetching live DOE programs...")
    try:
        live = fetch_live_doe_programs()
    except Exception as e:
        log.error(f"Live DOE fetch failed: {e}")
        live = []

    if not live:
        log.warning(
            "No live DOE data returned from any endpoint. "
            "Falling back entirely to hardcoded FY2026 list."
        )
    else:
        log.info(f"Got {len(live)} live programs; merging with fallback list.")

    programs = merge_programs(live, FY2026_DOE_PROGRAMS)
    log.info(f"Final merged program count: {len(programs)}")

    log.info("Fetching EIA energy statistics...")
    stats = fetch_eia_statistics()
    log.info(f"EIA statistics retrieved: {len(stats)}")

    save_to_json(programs, "doe_programs_raw.json")
    if stats:
        save_to_json(stats, "eia_statistics_raw.json")

    generate_js_snippet(programs)

    log.info("=" * 60)
    log.info("Summary")
    log.info("=" * 60)
    total_funding = 0.0
    for p in programs:
        s = str(p.get("funding", "0"))
        try:
            if "B" in s:
                total_funding += float(s.replace("B", "").replace("$", "").replace(",", "")) * 1000
            elif "M" in s:
                total_funding += float(s.replace("M", "").replace("$", "").replace(",", ""))
        except ValueError:
            continue
    log.info(f"Total tracked DOE funding: ${total_funding:,.0f}M")
    log.info("Tracked Programs:")
    for p in programs[:10]:
        cs = ", ".join(p.get("companies", [])[:3])
        log.info(f"  {p['program']}: ${p.get('funding', '')} ({cs})")

    log.info("=" * 60)
    log.info("Done!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
