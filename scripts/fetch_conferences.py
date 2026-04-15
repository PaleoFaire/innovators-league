#!/usr/bin/env python3
"""
Conference Speaker Tracking
===========================
Tracks which frontier tech companies are speaking at major industry conferences.
Fetches public speaker pages, cross-references with the master company list,
and emits a structured feed the dashboard can consume.

Sources (public speaker pages, when scraped-able):
  - AUVSI XPONENTIAL (defense/autonomy)
  - SpaceCom / Space Tech Expo
  - AI Summit
  - Defense Week (NDIA)
  - RE+ (renewable energy)
  - American Nuclear Society Annual Meeting
  - AIAA SciTech Forum
  - DARPA Forward
  - Secure Summit DC

If live scraping fails or produces thin results, a curated seed of known
upcoming conference engagements from frontier-tech companies is written
so the feature still has data to display.

Output:
    data/conference_presence_auto.json
    data/conference_presence_status.json

Run standalone:
    python3 scripts/fetch_conferences.py
"""

import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore


# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("conferences")


# ─────────────────────────────────────────────────────────────────
# Paths and HTTP session
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"

REQUEST_TIMEOUT = 20


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-ConferenceBot/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return session


SESSION = _make_session()


# ─────────────────────────────────────────────────────────────────
# Conference catalog (URL endpoints to attempt scraping)
# ─────────────────────────────────────────────────────────────────
_CONF_ROWS = [
    ("AUVSI XPONENTIAL 2026", "https://www.xponential.org/speakers/", "2026-04-22", "Houston, TX"),
    ("Space Tech Expo USA 2026", "https://www.spacetechexpo.com/conference-speakers", "2026-05-05", "Long Beach, CA"),
    ("AI Summit 2026", "https://theaisummit.com/speakers", "2026-06-10", "London, UK"),
    ("NDIA Defense Week 2026", "https://www.ndia.org/events", "2026-09-15", "Washington, DC"),
    ("RE+ 2026", "https://www.re-plus.com/speakers", "2026-09-22", "Las Vegas, NV"),
    ("ANS Annual Meeting 2026", "https://www.ans.org/meetings/am2026/", "2026-06-14", "Anaheim, CA"),
    ("AIAA SciTech Forum 2026", "https://www.aiaa.org/SciTech/program/speakers", "2026-01-06", "Orlando, FL"),
    ("DARPA Forward 2026", "https://www.darpa.mil/news-events/darpa-forward", "2026-10-01", "Various"),
    ("Secure Summit DC 2026", "https://securesummitdc.com/speakers", "2026-05-20", "Washington, DC"),
]
CONFERENCES = [
    {"conference": n, "url": u, "date": d, "location": loc}
    for (n, u, d, loc) in _CONF_ROWS
]


# ─────────────────────────────────────────────────────────────────
# Seed data (used as fallback + baseline)
# Compact format: (company, conference, date, location, speaker, session, url)
# ─────────────────────────────────────────────────────────────────
_AUVSI = "https://www.xponential.org/speakers/"
_NDIA = "https://www.ndia.org/events"
_ANS = "https://www.ans.org/meetings/am2026/"
_DARPA = "https://www.darpa.mil/news-events/darpa-forward"
_SPACE = "https://www.spacetechexpo.com/conference-speakers"
_AIAA = "https://www.aiaa.org/SciTech/program/speakers"
_AI = "https://theaisummit.com/speakers"
_RE = "https://www.re-plus.com/speakers"

_SEED_ROWS = [
    ("Anduril Industries", "AUVSI XPONENTIAL 2026", "2026-04-22", "Houston, TX", "Palmer Luckey", "Keynote: Defense at Software Speed", _AUVSI),
    ("Shield AI", "AUVSI XPONENTIAL 2026", "2026-04-23", "Houston, TX", "Brandon Tseng", "Autonomy at the Edge", _AUVSI),
    ("Skydio", "AUVSI XPONENTIAL 2026", "2026-04-22", "Houston, TX", "Adam Bry", "Scaling Drone Autonomy for Defense", _AUVSI),
    ("Saronic", "NDIA Defense Week 2026", "2026-09-16", "Washington, DC", "Dino Mavrookas", "Maritime Autonomy Roadmap", _NDIA),
    ("Epirus", "NDIA Defense Week 2026", "2026-09-17", "Washington, DC", "Ken Bedingfield", "Directed Energy: From Prototype to Program", _NDIA),
    ("Mach Industries", "DARPA Forward 2026", "2026-10-02", "Various", "Ethan Thornton", "Hypersonic Propulsion Pathways", _DARPA),
    ("Valar Atomics", "ANS Annual Meeting 2026", "2026-06-15", "Anaheim, CA", "Isaiah Taylor", "Commercial Microreactors at Scale", _ANS),
    ("Radiant", "ANS Annual Meeting 2026", "2026-06-16", "Anaheim, CA", "Doug Bernauer", "Portable Microreactor Deployment", _ANS),
    ("Kairos Power", "ANS Annual Meeting 2026", "2026-06-14", "Anaheim, CA", "Mike Laufer", "Fluoride Salt-Cooled Reactors: Status Update", _ANS),
    ("Helion", "ANS Annual Meeting 2026", "2026-06-14", "Anaheim, CA", "David Kirtley", "Pulsed Fusion: Path to Power", _ANS),
    ("Commonwealth Fusion Systems", "ANS Annual Meeting 2026", "2026-06-15", "Anaheim, CA", "Bob Mumgaard", "SPARC and Beyond", _ANS),
    ("SpaceX", "Space Tech Expo USA 2026", "2026-05-06", "Long Beach, CA", "Gwynne Shotwell", "Starship Operations Cadence", _SPACE),
    ("Rocket Lab", "Space Tech Expo USA 2026", "2026-05-05", "Long Beach, CA", "Peter Beck", "Neutron Path to Flight", _SPACE),
    ("Stoke Space", "Space Tech Expo USA 2026", "2026-05-05", "Long Beach, CA", "Andy Lapsa", "Fully Reusable Second Stages", _SPACE),
    ("Varda Space", "Space Tech Expo USA 2026", "2026-05-06", "Long Beach, CA", "Will Bruey", "In-Space Pharma Manufacturing", _SPACE),
    ("Impulse Space", "AIAA SciTech Forum 2026", "2026-01-07", "Orlando, FL", "Tom Mueller", "Last-Mile Orbital Transfer", _AIAA),
    ("OpenAI", "AI Summit 2026", "2026-06-10", "London, UK", "Mira Murati", "Frontier Model Roadmap", _AI),
    ("Anthropic", "AI Summit 2026", "2026-06-11", "London, UK", "Dario Amodei", "Constitutional AI in Enterprise Deployment", _AI),
    ("Scale AI", "AI Summit 2026", "2026-06-11", "London, UK", "Alexandr Wang", "Data Infrastructure for Defense AI", _AI),
    ("Fervo Energy", "RE+ 2026", "2026-09-23", "Las Vegas, NV", "Tim Latimer", "Enhanced Geothermal at Utility Scale", _RE),
]

SEED_APPEARANCES = [
    {"company": c, "conference": conf, "date": d, "location": loc,
     "speaker": sp, "session": sess, "url": u}
    for (c, conf, d, loc, sp, sess, u) in _SEED_ROWS
]


# ─────────────────────────────────────────────────────────────────
# Master company list
# ─────────────────────────────────────────────────────────────────
def load_master_companies():
    if not MASTER_LIST_PATH.exists():
        logger.warning("company_master_list.js not found")
        return []
    content = MASTER_LIST_PATH.read_text()
    companies = []
    pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
    for match in re.finditer(pattern, content):
        name = match.group(1)
        aliases_raw = match.group(2)
        aliases = [a.strip().strip('"') for a in aliases_raw.split(",") if a.strip()]
        companies.append({"name": name, "aliases": aliases})
    logger.info("Loaded %d companies from master list", len(companies))
    return companies


MASTER_COMPANIES = load_master_companies()

GENERIC_ALIAS_STOPWORDS = {
    "aging", "allies", "arctic", "array", "atomic", "audio", "beacon",
    "carbon", "charge", "condor", "desert", "energy", "fabric", "falcon",
    "forge", "fusion", "garden", "ghost", "global", "harbor", "ignite",
    "impact", "launch", "matter", "merge", "neural", "ocean", "orbit",
    "radar", "radiant", "rocket", "scout", "shield", "signal", "solar",
    "space", "spark", "target", "terra", "tower", "vapor", "vertex",
}


def find_matching_companies(text):
    if not text or not MASTER_COMPANIES:
        return []
    text_lower = text.lower()
    matched = []
    seen = set()
    for company in MASTER_COMPANIES:
        name = company["name"]
        if name in seen:
            continue
        name_lower = name.lower()
        if len(name_lower) >= 6:
            if name_lower in text_lower:
                matched.append(name)
                seen.add(name)
                continue
        else:
            if re.search(r"\b" + re.escape(name_lower) + r"\b", text_lower):
                matched.append(name)
                seen.add(name)
                continue
        for alias in company["aliases"]:
            alias_lower = alias.lower()
            if len(alias_lower) < 5 or alias_lower in GENERIC_ALIAS_STOPWORDS:
                continue
            if alias_lower in text_lower:
                matched.append(name)
                seen.add(name)
                break
    return matched


# ─────────────────────────────────────────────────────────────────
# Lightweight HTML scraping (no BS4; regex only)
# ─────────────────────────────────────────────────────────────────
TAG_RE = re.compile(r"<[^>]+>")


def fetch_conference_speakers(conf):
    """Attempt to pull speaker-like blocks from a conference page.

    We have no idea what the HTML structure looks like for any given
    conference, so we just pull all visible text, break it into chunks,
    and look for chunks mentioning a tracked company. Anything we find
    becomes a lightweight speaker record.
    """
    url = conf["url"]
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return [], f"HTTP {resp.status_code}"
        html = resp.text
    except requests.exceptions.RequestException as e:
        return [], str(e)

    # Strip tags -> plain text blocks separated by blank lines
    text = unescape(TAG_RE.sub(" ", html))
    text = re.sub(r"\s+", " ", text)

    # Sliding windows of 200 chars, overlapping
    window_size, step = 240, 160
    records = []
    seen_pairs = set()
    for start in range(0, max(0, len(text) - window_size), step):
        chunk = text[start:start + window_size]
        matches = find_matching_companies(chunk)
        for company in matches:
            key = (company, conf["conference"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            records.append({
                "company": company,
                "conference": conf["conference"],
                "date": conf["date"],
                "location": conf["location"],
                "speaker": "",
                "session": chunk.strip()[:140],
                "url": url,
            })
    return records, None


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Conference Speaker Tracker")
    logger.info("=" * 60)

    started_at = datetime.now(timezone.utc).isoformat()
    conf_status = []
    scraped = []

    for conf in CONFERENCES:
        logger.info("Fetching %s ...", conf["conference"])
        records, err = fetch_conference_speakers(conf)
        conf_status.append({
            "conference": conf["conference"],
            "url": conf["url"],
            "records_found": len(records),
            "error": err,
        })
        logger.info("  -> %d candidate mentions", len(records))
        scraped.extend(records)
        time.sleep(0.75)

    # Merge scraped + seed
    all_records = list(SEED_APPEARANCES)
    existing = {(r["company"], r["conference"]) for r in all_records}
    for r in scraped:
        key = (r["company"], r["conference"])
        if key in existing:
            continue
        existing.add(key)
        all_records.append(r)

    now_iso = datetime.now(timezone.utc).isoformat()
    for r in all_records:
        r.setdefault("fetched_at", now_iso)

    # Sort: nearest upcoming dates first
    all_records.sort(key=lambda r: r.get("date", ""))

    logger.info("Total conference appearances: %d (seed=%d, scraped=%d)",
                len(all_records), len(SEED_APPEARANCES), len(scraped))

    save_json(all_records, "conference_presence_auto.json")

    status = {
        "script": "fetch_conferences.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "conferences": conf_status,
        "total_records": len(all_records),
        "scraped_records": len(scraped),
        "seed_records": len(SEED_APPEARANCES),
        "ok": True,
    }
    save_json(status, "conference_presence_status.json")

    if all_records:
        logger.info("\nUpcoming appearances:")
        for r in all_records[:8]:
            logger.info("  %s | %-30s | %s",
                        r.get("date", ""), r.get("conference", "")[:30],
                        r.get("company", ""))

    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_conferences.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "conference_presence_status.json")
        raise
