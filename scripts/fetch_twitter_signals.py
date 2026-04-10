#!/usr/bin/env python3
"""
Twitter/X Signals Fetcher (EXPERIMENTAL / PLACEHOLDER)
======================================================
Intended to track X/Twitter follower counts and recent posts for founders and
companies in the frontier tech database.

CURRENT STATUS: PLACEHOLDER
--------------------------
Twitter/X no longer has a free, unauthenticated scraping path that is robust
enough for a daily batch job:

  1. The official X API v2 costs $100/month minimum at the Basic tier, and
     the Free tier is write-only.
  2. Third-party mirrors like Nitter have gone dark; nearly all public
     Nitter instances stopped working after X tightened its anti-scraping
     measures in late 2023.
  3. Libraries such as twscrape / snscrape depend on authenticated cookies
     which must be manually refreshed from a real X account — not suitable
     for an unattended GitHub Actions pipeline.

This script therefore:
    - Loads candidate founder handles from the company master list.
    - Writes an empty `twitter_signals_auto.json` with the correct schema.
    - Writes a detailed `twitter_signals_status.json` explaining the
      situation, so the pipeline doesn't silently treat "no data" as a bug.
    - Documents exactly how a future real fetcher would work, so whoever
     swaps in paid API access (or a credentialed scraper) can drop in a
     working `fetch_founder_signal()` and everything else will just work.

Future implementation options (ordered from cheapest to most reliable):
    a) Apify "Twitter Scraper" actor — pay-as-you-go, ~$0.25 per 1k tweets.
       Requires APIFY_TOKEN secret.
    b) RapidAPI "Twitter API v2" mirrors — free tiers ~100 req/day.
       Requires RAPIDAPI_KEY secret.
    c) Official X API Basic tier — $100/mo, 10k reads/mo.
       Requires X_BEARER_TOKEN secret.
    d) twscrape with persistent cookie pool — fragile, not recommended.

Output (always written, even on graceful failure):
    data/twitter_signals_auto.json    — list of founder signal records (empty
                                        under current placeholder logic)
    data/twitter_signals_status.json  — fetch metadata + reason-for-empty

Run standalone:
    python3 scripts/fetch_twitter_signals.py
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("twitter_signals")

# ─────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_JS_PATH = SCRIPT_DIR.parent / "data.js"

# ─────────────────────────────────────────────────────────────────
# Data source selection — checks available API keys
# ─────────────────────────────────────────────────────────────────
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "").strip()


def available_data_source():
    """Return the first available data source or None."""
    if X_BEARER_TOKEN:
        return "x_api_v2"
    if APIFY_TOKEN:
        return "apify"
    if RAPIDAPI_KEY:
        return "rapidapi"
    return None


# ─────────────────────────────────────────────────────────────────
# Founder extraction from data.js
# ─────────────────────────────────────────────────────────────────
# data.js contains COMPANIES array entries with `founder: "..."` and
# `name: "..."` fields. We extract (founder, company) tuples for each entry.
FOUNDER_BLOCK_RE = re.compile(
    r'name:\s*"([^"]+)".*?founder:\s*"([^"]+)"',
    re.DOTALL,
)


def load_company_founders():
    """
    Parse data.js for (company, founder) pairs.
    Returns a list of dicts: {"company": ..., "founder": ...}.
    """
    if not DATA_JS_PATH.exists():
        logger.warning("data.js not found at %s", DATA_JS_PATH)
        return []

    try:
        content = DATA_JS_PATH.read_text()
    except Exception as e:
        logger.warning("Could not read data.js: %s", e)
        return []

    founders = []
    seen = set()
    for match in FOUNDER_BLOCK_RE.finditer(content):
        company = match.group(1).strip()
        founder = match.group(2).strip()
        if not founder or founder.lower() in {"null", "unknown", "n/a"}:
            continue
        key = (company, founder)
        if key in seen:
            continue
        seen.add(key)
        founders.append({"company": company, "founder": founder})
    logger.info("Loaded %d (company, founder) pairs from data.js", len(founders))
    return founders


# ─────────────────────────────────────────────────────────────────
# Handle guesser (used when a real fetcher is plugged in)
# ─────────────────────────────────────────────────────────────────
def guess_handles(founder_name):
    """
    Generate plausible Twitter/X handles for a founder name.
    A real fetcher would iterate these candidates and probe each one.
    """
    parts = [p for p in re.split(r"\s+", founder_name.strip()) if p]
    if not parts:
        return []
    first = parts[0].lower()
    last = parts[-1].lower()
    candidates = [
        f"{first}{last}",
        f"{first}_{last}",
        f"{first[0]}{last}",
        f"{first}",
        f"{last}",
    ]
    return [f"@{re.sub(r'[^a-z0-9_]', '', c)}" for c in candidates if c]


# ─────────────────────────────────────────────────────────────────
# Real fetcher placeholder (swap-in point for future implementation)
# ─────────────────────────────────────────────────────────────────
def fetch_founder_signal(founder, company, source):
    """
    Placeholder for the real founder signal fetcher.

    When a data source is plugged in (Apify, RapidAPI, X API v2), this
    function should return a dict matching the target schema:

        {
            "founder": "Palmer Luckey",
            "company": "Anduril Industries",
            "handle": "@PalmerLuckey",
            "followers": 285000,
            "recent_posts": 15,
            "recent_engagement": 12500,
            "recent_topics": ["Lattice OS", "defense", "innovation"],
            "fetched_at": "..."
        }

    Or None if the founder has no findable Twitter/X presence.
    """
    # No data source available in placeholder mode — always return None.
    _ = guess_handles(founder)  # reference for future use
    return None


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
    logger.info("Twitter/X Signals Fetcher (placeholder)")
    logger.info("=" * 60)

    started_at = datetime.now(timezone.utc).isoformat()
    source = available_data_source()

    if not source:
        logger.warning(
            "No Twitter/X data source configured. Set one of the following "
            "env vars to enable a real fetcher: X_BEARER_TOKEN, APIFY_TOKEN, "
            "RAPIDAPI_KEY."
        )
        logger.info("Running in PLACEHOLDER mode — writing empty structured output.")

    founders = load_company_founders()

    signals = []
    attempted = 0
    skipped = 0

    for entry in founders:
        founder = entry["founder"]
        company = entry["company"]

        if not source:
            skipped += 1
            continue

        attempted += 1
        try:
            sig = fetch_founder_signal(founder, company, source)
            if sig:
                signals.append(sig)
        except Exception as e:
            logger.warning("  error fetching %s: %s", founder, e)

    save_json(signals, "twitter_signals_auto.json")

    status = {
        "script": "fetch_twitter_signals.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "mode": "real" if source else "placeholder",
        "data_source": source,
        "founders_in_dataset": len(founders),
        "founders_attempted": attempted,
        "founders_skipped": skipped,
        "signals_collected": len(signals),
        "ok": True,
        "notes": (
            "Placeholder mode: writes an empty list because Twitter/X has no "
            "reliable free unauthenticated source. Set X_BEARER_TOKEN, "
            "APIFY_TOKEN, or RAPIDAPI_KEY to enable real fetching."
        ) if not source else None,
    }
    save_json(status, "twitter_signals_status.json")

    logger.info("Founders loaded: %d", len(founders))
    logger.info("Signals collected: %d", len(signals))
    logger.info("Mode: %s", "real" if source else "placeholder")
    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_twitter_signals.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "twitter_signals_status.json")
        raise
