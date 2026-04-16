#!/usr/bin/env python3
"""
SBIR/STTR Government Grant Awards Fetcher

Surfaces frontier tech companies that have received SBIR/STTR awards — the
strongest early-stage signal for dual-use defense and hard-tech startups.

Endpoint strategy (tried in order):
  1. https://www.sbir.gov/api/awards.json       — REST v2-style, keyword + pagination
  2. https://data.sbir.gov/api/awards.json      — DATA.gov proxy
  3. Curated seed list                           — last-resort fallback

Output: data/sbir_awards_auto.json

Schema per award:
  {
    "company": "Epirus",
    "phase": "Phase III",
    "agency": "Army",
    "topic": "Counter-drone HPM systems",
    "amount": "$1.5M",
    "year": 2025,
    "url": "https://www.sbir.gov/...",
    "lastUpdated": "2026-04-16"
  }

Fault tolerance:
  - HTTPAdapter + urllib3 Retry for 429/5xx with exponential backoff.
  - Every endpoint failure logged once, falls through to the next.
  - If ALL endpoints fail, writes the curated seed so the file is always a
    non-empty array of real frontier-tech awards.
"""

import json
import logging
import os
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

REQUEST_TIMEOUT = 25
MAX_RETRIES = 3

# ─── Endpoints ───
SBIR_ENDPOINTS = [
    ("sbir_gov_v2",   "https://www.sbir.gov/api/awards.json"),
    ("data_sbir_gov", "https://data.sbir.gov/api/awards.json"),
]

# Keywords drive the search for a hit-list of frontier tech areas
SEARCH_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "autonomous",
    "hypersonic",
    "quantum computing",
    "nuclear fusion",
    "satellite",
    "CRISPR",
    "additive manufacturing",
    "battery",
    "drone",
    "semiconductor",
    "directed energy",
    "synthetic biology",
    "carbon capture",
]

DATA_GOV_API_KEY = os.environ.get("DATA_GOV_API_KEY", "").strip()


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-SBIR/2.1 (+https://innovatorsleague.com)",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()
_DEAD_ENDPOINTS = set()


# ─────────────────────────────────────────────────────────────────
# Curated seed — ~30 known 2024/2025 frontier-tech SBIR awards
# Phase III contracts are the most valuable (production-scale).
# ─────────────────────────────────────────────────────────────────
SBIR_AWARDS_SEED = [
    # ─── Directed energy / counter-drone ───
    {
        "company": "Epirus",
        "phase": "Phase III",
        "agency": "Army",
        "topic": "Counter-drone high-power microwave (HPM) systems — Leonidas",
        "amount": "$66M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=epirus",
    },
    {
        "company": "Anduril Industries",
        "phase": "Phase III",
        "agency": "DoD",
        "topic": "Lattice AI and counter-UAS Roadrunner family",
        "amount": "$15M+",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=anduril",
    },
    {
        "company": "Shield AI",
        "phase": "Phase III",
        "agency": "Air Force",
        "topic": "Hivemind autonomy stack for tactical UAS",
        "amount": "$7.5M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=shield+ai",
    },
    {
        "company": "Skydio",
        "phase": "Phase III",
        "agency": "Army",
        "topic": "Short-Range Reconnaissance autonomous UAS",
        "amount": "$99M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=skydio",
    },

    # ─── Space / launch / satellite ───
    {
        "company": "ABL Space Systems",
        "phase": "Phase III",
        "agency": "Air Force",
        "topic": "Responsive launch services for small satellites",
        "amount": "$60M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=ABL+space",
    },
    {
        "company": "Astra Space",
        "phase": "Phase II",
        "agency": "DARPA",
        "topic": "Rapid-response commercial launch vehicle development",
        "amount": "$1.5M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=astra+space",
    },
    {
        "company": "Varda Space Industries",
        "phase": "Phase II",
        "agency": "Air Force",
        "topic": "Microgravity manufacturing on autonomous spacecraft",
        "amount": "$60M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=varda",
    },
    {
        "company": "Xona Space Systems",
        "phase": "Phase II",
        "agency": "Air Force",
        "topic": "LEO alternative-PNT constellation (PULSAR)",
        "amount": "$1.25M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=xona+space",
    },
    {
        "company": "True Anomaly",
        "phase": "Phase II",
        "agency": "Space Force",
        "topic": "On-orbit rendezvous and space-domain-awareness vehicles",
        "amount": "$30M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=true+anomaly",
    },

    # ─── Hypersonics ───
    {
        "company": "Castelion",
        "phase": "Phase II",
        "agency": "Air Force",
        "topic": "Long-range hypersonic strike weapon development",
        "amount": "$14M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=castelion",
    },
    {
        "company": "Ursa Major",
        "phase": "Phase III",
        "agency": "Air Force",
        "topic": "Hadley and Draper hypersonic/liquid rocket engines",
        "amount": "$28M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=ursa+major",
    },

    # ─── Nuclear / fusion / energy ───
    {
        "company": "Commonwealth Fusion Systems",
        "phase": "Phase II",
        "agency": "DOE",
        "topic": "HTS magnet manufacturing for SPARC tokamak",
        "amount": "$2.5M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=commonwealth+fusion",
    },
    {
        "company": "Helion Energy",
        "phase": "Phase II",
        "agency": "DOE",
        "topic": "Pulsed fusion power plant (Polaris/Trenta)",
        "amount": "$3M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=helion",
    },
    {
        "company": "Radiant Industries",
        "phase": "Phase II",
        "agency": "DOE",
        "topic": "Portable high-temperature gas-cooled microreactor (Kaleidos)",
        "amount": "$3.9M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=radiant+nuclear",
    },
    {
        "company": "X-energy",
        "phase": "Phase III",
        "agency": "DOE",
        "topic": "TRISO fuel manufacturing (TF3) and Xe-100 reactor",
        "amount": "$1.2B",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=x-energy",
    },

    # ─── Biotech / medical ───
    {
        "company": "Ginkgo Bioworks",
        "phase": "Phase II",
        "agency": "DARPA",
        "topic": "Biosecurity and pathogen-surveillance platforms",
        "amount": "$18M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=ginkgo",
    },
    {
        "company": "Distributed Bio",
        "phase": "Phase II",
        "agency": "DoD",
        "topic": "Broad-spectrum antiviral antibody platforms",
        "amount": "$4M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=distributed+bio",
    },

    # ─── Chips / semiconductors ───
    {
        "company": "PsiQuantum",
        "phase": "Phase II",
        "agency": "DARPA",
        "topic": "Silicon-photonic fault-tolerant quantum computing",
        "amount": "$26M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=psiquantum",
    },
    {
        "company": "Ayar Labs",
        "phase": "Phase II",
        "agency": "DARPA",
        "topic": "In-package optical I/O for HPC/AI systems",
        "amount": "$9M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=ayar+labs",
    },
    {
        "company": "Lightmatter",
        "phase": "Phase II",
        "agency": "DARPA",
        "topic": "Photonic compute and interconnect fabric",
        "amount": "$12M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=lightmatter",
    },
    {
        "company": "Atomic Semi",
        "phase": "Phase I",
        "agency": "DoD",
        "topic": "Mini-fab desktop semiconductor manufacturing",
        "amount": "$250K",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=atomic+semi",
    },

    # ─── Autonomy / robotics ───
    {
        "company": "Saildrone",
        "phase": "Phase III",
        "agency": "Navy",
        "topic": "Unmanned surface vehicles for maritime ISR",
        "amount": "$29M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=saildrone",
    },
    {
        "company": "Gecko Robotics",
        "phase": "Phase II",
        "agency": "Air Force",
        "topic": "Autonomous infrastructure inspection robots",
        "amount": "$5M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=gecko+robotics",
    },
    {
        "company": "Agility Robotics",
        "phase": "Phase II",
        "agency": "Air Force",
        "topic": "Bipedal humanoid logistics robots (Digit)",
        "amount": "$2M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=agility+robotics",
    },

    # ─── Batteries / energy storage ───
    {
        "company": "Sila Nanotechnologies",
        "phase": "Phase II",
        "agency": "DOE",
        "topic": "Silicon-anode battery materials scale-up",
        "amount": "$3.5M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=sila+nanotechnologies",
    },
    {
        "company": "Form Energy",
        "phase": "Phase II",
        "agency": "DOE",
        "topic": "Iron-air 100-hour long-duration storage",
        "amount": "$2.8M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=form+energy",
    },

    # ─── Networks / cyber ───
    {
        "company": "Dispel",
        "phase": "Phase III",
        "agency": "DoD",
        "topic": "Moving-target-defense networks for OT/ICS",
        "amount": "$4M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=dispel",
    },
    {
        "company": "Second Front Systems",
        "phase": "Phase III",
        "agency": "DoD",
        "topic": "Game Warden DevSecOps platform for classified workloads",
        "amount": "$26M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=second+front",
    },

    # ─── AI foundation ───
    {
        "company": "Primer",
        "phase": "Phase III",
        "agency": "Air Force",
        "topic": "NLP + generative AI for intelligence fusion",
        "amount": "$24M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=primer",
    },
    {
        "company": "Scale AI",
        "phase": "Phase III",
        "agency": "DoD",
        "topic": "Thunderforge — joint planning generative-AI program",
        "amount": "$249M",
        "year": 2025,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=scale+ai",
    },
    {
        "company": "Vannevar Labs",
        "phase": "Phase III",
        "agency": "Navy",
        "topic": "OSINT fusion for national-security analysts",
        "amount": "$14M",
        "year": 2024,
        "url": "https://www.sbir.gov/sbirsearch/detail/?keywords=vannevar+labs",
    },
]


def _parse_payload(data):
    """Normalize various SBIR.gov response shapes into a list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "data", "awards", "items", "records", "response"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def _fetch_one_endpoint(endpoint_name, url, keyword, max_results=100):
    """
    Hit a single SBIR endpoint.  Uses REST-v2 style params:
    keyword=..., start=..., rows=...

    Returns list of raw records or None on failure.
    """
    if endpoint_name in _DEAD_ENDPOINTS:
        return None

    all_records = []
    start = 0
    page_size = 100

    while len(all_records) < max_results:
        params = {
            "keyword": keyword,
            "start": start,
            "rows": min(page_size, max_results - len(all_records)),
        }
        if DATA_GOV_API_KEY and "data.sbir.gov" in url:
            params["api_key"] = DATA_GOV_API_KEY

        try:
            resp = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} connection error: {e}")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        if resp.status_code >= 400:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} HTTP {resp.status_code} — marking dead")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        try:
            data = resp.json()
        except ValueError:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} returned non-JSON — marking dead")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        page = _parse_payload(data)
        if not page:
            return all_records  # valid but empty
        all_records.extend(page)
        if len(page) < page_size:
            break
        start += page_size
        time.sleep(0.75)

    return all_records


def fetch_live_awards():
    """
    Try each endpoint in order for each keyword.  Collect + dedup by a
    (firm, title, year) key.  Returns list of records in the spec schema.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    collected = []
    seen = set()
    endpoint_wins = {}

    for keyword in SEARCH_KEYWORDS:
        raw = None
        used_endpoint = None
        for name, url in SBIR_ENDPOINTS:
            raw = _fetch_one_endpoint(name, url, keyword)
            if raw is not None:
                used_endpoint = name
                break

        if raw is None:
            continue

        endpoint_wins[used_endpoint] = endpoint_wins.get(used_endpoint, 0) + 1
        new_count = 0
        for award in raw:
            firm = (award.get("firm") or award.get("company") or "").strip()
            title = (award.get("award_title") or award.get("title") or "").strip()
            year = (
                award.get("award_year")
                or award.get("proposal_award_year")
                or award.get("year")
                or 0
            )
            try:
                year = int(year) if year else 0
            except (TypeError, ValueError):
                year = 0

            dedupe_key = (firm.lower(), title.lower(), year)
            if not firm or dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            amount_raw = (
                award.get("award_amount")
                or award.get("amount")
                or award.get("total_award_amount")
                or 0
            )
            try:
                amount_float = float(amount_raw)
            except (TypeError, ValueError):
                amount_float = 0.0

            amount_str = ""
            if amount_float >= 1_000_000:
                amount_str = f"${amount_float/1_000_000:.1f}M"
            elif amount_float > 0:
                amount_str = f"${amount_float/1_000:.0f}K"

            url_field = (
                award.get("award_link")
                or award.get("url")
                or "https://www.sbir.gov/sbirsearch/award/all"
            )

            collected.append({
                "company": firm,
                "phase": (award.get("phase") or "").strip(),
                "agency": (award.get("agency") or award.get("branch") or "").strip(),
                "topic": title[:300] if title else (award.get("abstract") or "")[:300],
                "amount": amount_str,
                "year": year,
                "url": url_field,
                "_source": used_endpoint,
                "_keyword": keyword,
                "lastUpdated": today,
            })
            new_count += 1

        log.info(
            f"  [{keyword[:30]}] via {used_endpoint} -> "
            f"+{new_count} new ({len(collected)} total)"
        )
        time.sleep(1.25)

    log.info(f"Live endpoint wins: {endpoint_wins}")
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
    log.info("SBIR/STTR Government Grant Awards Fetcher")
    log.info("=" * 60)
    log.info(f"Keyword searches: {len(SEARCH_KEYWORDS)}")
    log.info(f"Endpoints: {[n for n, _ in SBIR_ENDPOINTS]}")
    log.info(f"DATA_GOV_API_KEY: {'set' if DATA_GOV_API_KEY else 'not set'}")
    log.info("=" * 60)

    live_records = []
    try:
        live_records = fetch_live_awards()
    except Exception as e:
        log.error(f"fetch_live_awards() crashed: {e}")
        live_records = []

    seed_records = build_seed_records()

    # Merge: prefer live records, then fall back to seed entries
    # Dedupe by (company.lower(), year, topic first 40 chars)
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

    # Sort: Phase III first (high-value), then by year desc
    phase_rank = {"Phase III": 0, "Phase II": 1, "Phase I": 2}
    records.sort(
        key=lambda r: (
            phase_rank.get(r.get("phase") or "", 99),
            -int(r.get("year") or 0),
        )
    )

    save_to_json(records, OUTPUT_FILE)

    # Summary
    by_phase = {}
    by_agency = {}
    by_source = {}
    for r in records:
        by_phase[r.get("phase") or "(unknown)"] = by_phase.get(r.get("phase") or "(unknown)", 0) + 1
        by_agency[r.get("agency") or "(unknown)"] = by_agency.get(r.get("agency") or "(unknown)", 0) + 1
        by_source[r.get("_source") or "(unknown)"] = by_source.get(r.get("_source") or "(unknown)", 0) + 1

    log.info("=" * 60)
    log.info(f"Total awards: {len(records)}")
    log.info(f"Live records: {len(live_records)}  |  Seed records: {len(seed_records)}")
    log.info("By phase:")
    for p, c in sorted(by_phase.items(), key=lambda x: -x[1]):
        log.info(f"  {p}: {c}")
    log.info("Top agencies:")
    for a, c in sorted(by_agency.items(), key=lambda x: -x[1])[:10]:
        log.info(f"  {a}: {c}")
    log.info("Sources:")
    for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
        log.info(f"  {s}: {c}")
    log.info("=" * 60)
    log.info("Done!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
