#!/usr/bin/env python3
"""
LinkedIn Headcount Signals (placeholder pipeline)
=================================================
Builds a structured headcount feed keyed off the master company list.
When no APIFY_TOKEN is configured, emits a placeholder record per
company (employee count = null, status = awaiting_apify_key) so the
downstream visualization has a usable shape. When APIFY_TOKEN is set,
runs Apify's LinkedIn company scraper and fills in real numbers.

Output:
    data/linkedin_headcount_auto.json
    data/linkedin_headcount_status.json

Run standalone:
    python3 scripts/fetch_linkedin_headcount.py
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
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
logger = logging.getLogger("linkedin_headcount")


# ─────────────────────────────────────────────────────────────────
# Paths and config
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
APIFY_ACTOR = os.environ.get(
    "APIFY_LINKEDIN_ACTOR", "harvest~linkedin-company-scraper"
)
REQUEST_TIMEOUT = 30


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-LinkedInBot/1.0",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()


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


# ─────────────────────────────────────────────────────────────────
# Slug helpers
# ─────────────────────────────────────────────────────────────────
# Manual overrides for companies whose LinkedIn slug differs noticeably
# from an auto-derived one. Extend as needed.
SLUG_OVERRIDES = {
    "Anduril Industries": "anduril",
    "Shield AI": "shieldai",
    "Blue Water Autonomy": "blue-water-autonomy",
    "CX2 Industries": "cx2-industries",
    "General Matter": "generalmatter",
    "Commonwealth Fusion Systems": "commonwealth-fusion-systems",
    "SpaceX": "spacex",
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "Rocket Lab": "rocket-lab",
    "Fervo Energy": "fervo-energy",
}


def slugify(name):
    if name in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[name]
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def linkedin_url(name):
    return f"https://linkedin.com/company/{slugify(name)}"


# ─────────────────────────────────────────────────────────────────
# Apify integration (only runs when APIFY_TOKEN is set)
# ─────────────────────────────────────────────────────────────────
def run_apify_scrape(urls):
    """Run the Apify LinkedIn actor synchronously for a batch of URLs.

    Returns a dict keyed by linkedin url -> {employeeCount, updated_at}
    or an empty dict if the run fails.
    """
    if not APIFY_TOKEN:
        return {}, "APIFY_TOKEN not set"

    endpoint = (
        f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"
        f"?token={APIFY_TOKEN}"
    )
    payload = {"startUrls": [{"url": u} for u in urls]}
    try:
        resp = SESSION.post(endpoint, json=payload, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return {}, f"HTTP {resp.status_code}"
        items = resp.json() or []
    except requests.exceptions.RequestException as e:
        return {}, str(e)
    except ValueError as e:
        return {}, f"json error: {e}"

    results = {}
    for item in items:
        url = (item.get("url") or item.get("companyUrl") or "").strip()
        if not url:
            continue
        count = (
            item.get("employeeCount")
            or item.get("employees")
            or item.get("staffCount")
        )
        try:
            count = int(count) if count is not None else None
        except (ValueError, TypeError):
            count = None
        results[url] = {
            "employeeCount": count,
            "employeeGrowth90d": item.get("employeeGrowth90d"),
            "lastFetched": datetime.now(timezone.utc).isoformat(),
        }
    return results, None


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
    logger.info("LinkedIn Headcount Signals")
    logger.info("=" * 60)

    started_at = datetime.now(timezone.utc).isoformat()
    companies = load_master_companies()
    if not companies:
        logger.error("No companies loaded — aborting")
        return

    records = []
    for c in companies:
        url = linkedin_url(c["name"])
        records.append({
            "company": c["name"],
            "linkedinUrl": url,
            "slug": slugify(c["name"]),
            "employeeCount": None,
            "employeeGrowth90d": None,
            "lastFetched": None,
            "status": "awaiting_apify_key",
        })

    apify_ok = False
    apify_err = None
    scraped_count = 0
    if APIFY_TOKEN:
        logger.info("APIFY_TOKEN detected — invoking Apify scraper "
                    "(actor=%s) for %d URLs", APIFY_ACTOR, len(records))
        # Run in chunks of 25 to avoid huge payloads
        enriched = {}
        for i in range(0, len(records), 25):
            chunk = [r["linkedinUrl"] for r in records[i:i + 25]]
            logger.info("  batch %d: %d URLs", i // 25 + 1, len(chunk))
            result, err = run_apify_scrape(chunk)
            if err:
                apify_err = err
                logger.warning("  Apify error: %s", err)
                break
            enriched.update(result)
            time.sleep(1.0)

        if enriched:
            apify_ok = True
            now_iso = datetime.now(timezone.utc).isoformat()
            for r in records:
                hit = enriched.get(r["linkedinUrl"])
                if not hit:
                    continue
                r["employeeCount"] = hit.get("employeeCount")
                r["employeeGrowth90d"] = hit.get("employeeGrowth90d")
                r["lastFetched"] = hit.get("lastFetched") or now_iso
                r["status"] = "ok" if hit.get("employeeCount") is not None else "partial"
                scraped_count += 1
    else:
        logger.info("APIFY_TOKEN not set — writing placeholder records only")

    save_json(records, "linkedin_headcount_auto.json")

    status = {
        "script": "fetch_linkedin_headcount.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "apify_enabled": bool(APIFY_TOKEN),
        "apify_ok": apify_ok,
        "apify_error": apify_err,
        "scraped_count": scraped_count,
        "ok": True,
    }
    save_json(status, "linkedin_headcount_status.json")

    logger.info("Wrote %d headcount records (enriched=%d)",
                len(records), scraped_count)
    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_linkedin_headcount.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "linkedin_headcount_status.json")
        raise
