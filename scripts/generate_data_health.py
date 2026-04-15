#!/usr/bin/env python3
"""
Data Health Generator
=====================
Scans the data/ directory, inspects every tracked data file
(JSON + the JS snippet wrappers), and writes a structured health
feed that the Data Health Dashboard can consume.

Status rules:
  - broken : file missing OR zero bytes OR JSON parse failure OR
             record count of 0.
  - stale  : file exists and has content, but mtime is older than 24h.
  - fresh  : file exists, has content, mtime within the last 24h.

Output:
    data/data_health.json

Run standalone:
    python3 scripts/generate_data_health.py
"""

import json
import logging
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("data_health")


SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUTPUT_PATH = DATA_DIR / "data_health.json"

FRESH_WINDOW = timedelta(hours=24)


# Curated catalog of sources we care about. Any data file shipped
# by the pipeline can live here. Files not listed below are still
# picked up by the generic scan at the bottom.
SOURCES = [
    ("sec_filings", "SEC Filings", "sec_filings_auto.js"),
    ("gov_contracts", "Gov Contracts", "gov_contracts_auto.js"),
    ("sam_contracts", "SAM Contracts", "sam_contracts_auto.js"),
    ("sbir_awards", "SBIR Awards", "sbir_awards_auto.js"),
    ("sbir_topics", "SBIR Topics", "sbir_topics_auto.json"),
    ("stocks", "Stock Prices", "stocks_auto.js"),
    ("jobs", "Job Postings", "jobs_auto.js"),
    ("hackernews", "HN Buzz", "hackernews_buzz_auto.js"),
    ("patents", "Patent Intel", "patent_intel_auto.js"),
    ("news", "News Feed", "news_signals_auto.js"),
    ("funding_tracker", "Funding Tracker", "funding_tracker_auto.json"),
    ("deals", "Deal Flow", "deals_auto.json"),
    ("demand_signals", "Demand Signals", "demand_signals_auto.json"),
    ("moat_profiles", "Moat Profiles", "moat_profiles.js"),
    ("founder_dna", "Founder DNA", "founder_dna.js"),
    ("clinical_trials", "Clinical Trials", "clinical_trials_auto.js"),
    ("arxiv", "arXiv Papers", "arxiv_papers_auto.js"),
    ("federal_register", "Federal Register", "federal_register_auto.js"),
    ("github_releases", "GitHub Releases", "github_releases_auto.js"),
    ("github_signals", "GitHub Signals", "github_signals_auto.json"),
    ("insider_trading", "Insider Trading", "insider_transactions_auto.js"),
    ("ipo_pipeline", "IPO Pipeline", "ipo_pipeline_auto.json"),
    ("nasa", "NASA Tech", "nasa_projects_auto.js"),
    ("nih_grants", "NIH Grants", "nih_grants_auto.js"),
    ("nrc", "NRC Licensing", "nrc_licensing_auto.js"),
    ("nsf", "NSF Awards", "nsf_awards_auto.js"),
    ("doe", "DOE Programs", "doe_programs_auto.js"),
    ("arpa_e", "ARPA-E", "arpa_e_projects_auto.js"),
    ("faa", "FAA Certification", "faa_certification_auto.js"),
    ("fda", "FDA Actions", "fda_actions_auto.js"),
    ("trade_data", "Trade Data", "trade_data_auto.js"),
    ("product_launches", "Product Launches", "product_launches_auto.js"),
    ("press_releases", "Press Releases", "press_releases_auto.js"),
    ("headcount_estimates", "Headcount Estimates", "headcount_estimates_auto.js"),
    ("innovator_scores", "Innovator Scores", "innovator_scores_auto.json"),
    ("predictive_scores", "Predictive Scores", "predictive_scores_auto.json"),
    ("growth_signals", "Growth Signals", "growth_signals_auto.json"),
    ("sector_momentum", "Sector Momentum", "sector_momentum_auto.json"),
    ("valuation_benchmarks", "Valuation Benchmarks", "valuation_benchmarks_auto.json"),
    ("revenue_intel", "Revenue Intel", "revenue_intel_auto.json"),
    ("vc_portfolios", "VC Portfolios", "vc_portfolio_changes.json"),
    ("twitter", "Twitter Signals", "twitter_signals_auto.json"),
    ("podcasts", "Podcast Mentions", "podcast_mentions_auto.json"),
    # New sources added in this pass
    ("conferences", "Conference Presence", "conference_presence_auto.json"),
    ("secondary_market", "Secondary Market", "secondary_market_auto.json"),
    ("linkedin_headcount", "LinkedIn Headcount", "linkedin_headcount_auto.json"),
    ("reddit", "Reddit Mentions", "reddit_mentions_auto.json"),
]


# Record-count extractors for the .js snippet wrappers. The workflow
# emits files like `const FOO = [...]` or `const BAR = {...}`. We count
# top-level array elements or object keys using a light regex. If that
# fails we fall back to 0.
ARRAY_COUNT_RE = re.compile(r"const\s+\w+\s*=\s*\[(.*?)\];", re.DOTALL)
OBJECT_COUNT_RE = re.compile(r"const\s+\w+\s*=\s*\{(.*?)\};", re.DOTALL)


def count_js_records(path: Path) -> int:
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return 0

    m = ARRAY_COUNT_RE.search(text)
    if m:
        body = m.group(1).strip()
        if not body:
            return 0
        # Count top-level commas at depth 0 to estimate entries
        depth = 0
        entries = 1
        in_str = False
        str_ch = ""
        prev = ""
        for ch in body:
            if in_str:
                if ch == str_ch and prev != "\\":
                    in_str = False
            else:
                if ch in ('"', "'"):
                    in_str = True
                    str_ch = ch
                elif ch in "[{(":
                    depth += 1
                elif ch in "]})":
                    depth -= 1
                elif ch == "," and depth == 0:
                    entries += 1
            prev = ch
        return entries

    m = OBJECT_COUNT_RE.search(text)
    if m:
        body = m.group(1)
        return len(re.findall(r'^\s*["\']?\w+["\']?\s*:', body, re.MULTILINE))
    return 0


def count_json_records(path: Path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return None, f"JSON parse error: {e}"
    if isinstance(data, list):
        return len(data), None
    if isinstance(data, dict):
        # Some feeds nest records under known keys
        for k in ("records", "items", "results", "entries", "data",
                  "sources", "companies"):
            if k in data and isinstance(data[k], list):
                return len(data[k]), None
        return len(data), None
    return 0, None


def evaluate_source(source_id: str, label: str, filename: str) -> dict:
    path = DATA_DIR / filename
    entry = {
        "id": source_id,
        "label": label,
        "file": f"data/{filename}",
        "status": "broken",
        "last_updated": None,
        "record_count": 0,
        "size_bytes": 0,
        "error": None,
    }

    if not path.exists():
        entry["error"] = "file missing"
        return entry

    try:
        stat = path.stat()
    except OSError as e:
        entry["error"] = f"stat error: {e}"
        return entry

    entry["size_bytes"] = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    entry["last_updated"] = mtime.isoformat()

    if stat.st_size == 0:
        entry["error"] = "empty file"
        entry["record_count"] = 0
        return entry

    if filename.endswith(".json"):
        count, err = count_json_records(path)
        if err:
            entry["error"] = err
            entry["record_count"] = 0
            return entry
        entry["record_count"] = count or 0
    elif filename.endswith(".js"):
        entry["record_count"] = count_js_records(path)
    else:
        entry["record_count"] = 0

    now = datetime.now(timezone.utc)
    age = now - mtime
    if entry["record_count"] == 0:
        entry["status"] = "broken"
        if not entry["error"]:
            entry["error"] = "no records"
    elif age > FRESH_WINDOW:
        entry["status"] = "stale"
    else:
        entry["status"] = "fresh"

    return entry


def main():
    logger.info("Scanning %s for %d known sources", DATA_DIR, len(SOURCES))
    sources = []
    fresh = stale = broken = 0

    for sid, label, filename in SOURCES:
        entry = evaluate_source(sid, label, filename)
        sources.append(entry)
        if entry["status"] == "fresh":
            fresh += 1
        elif entry["status"] == "stale":
            stale += 1
        else:
            broken += 1

    health = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "total": len(sources),
            "fresh": fresh,
            "stale": stale,
            "broken": broken,
        },
        "sources": sources,
    }

    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(health, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", OUTPUT_PATH,
                OUTPUT_PATH.stat().st_size)
    logger.info("Fresh=%d  Stale=%d  Broken=%d", fresh, stale, broken)


if __name__ == "__main__":
    main()
