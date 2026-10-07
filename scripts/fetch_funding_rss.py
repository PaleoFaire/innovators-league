#!/usr/bin/env python3
"""
Funding RSS Aggregator
======================
Pulls real-time funding announcements from a curated set of startup/VC RSS feeds
and extracts structured funding round information (amount, round, investors).

Sources:
    - TechCrunch Venture
    - Crunchbase News
    - The Information (free headlines)
    - BusinessWire Tech
    - Axios Pro Rata

Filters to frontier tech companies with the deal feed's own matcher: company,
amount, round and investors come from fetch_deals.extract_deal_from_article(),
so a headline is credited here only when scripts/fetch_deals.py would credit
it (subject before the verb, context and collision guards, data.js status
and size checks). Completely free — public RSS feeds, no API keys required.

Output:
    data/funding_feed_auto.json  — structured list of funding events
    data/funding_feed_status.json — fetch status metadata (always written)

Run standalone:
    python3 scripts/fetch_funding_rss.py
"""

import json
import re
import sys
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_deals  # noqa: E402  (the guarded matcher and parsers)

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("funding_rss")

# ─────────────────────────────────────────────────────────────────
# Paths and constants
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

USER_AGENT = "InnovatorsLeague-FundingBot/1.0 (+https://innovatorsleague.com)"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds — doubled on each retry

# RSS feeds to parse — (source name, url)
FUNDING_FEEDS = [
    ("TechCrunch",       "https://techcrunch.com/category/venture/feed/"),
    ("Crunchbase News",  "https://news.crunchbase.com/feed/"),
    ("The Information",  "https://www.theinformation.com/feed"),
    ("BusinessWire",     "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVtRXw=="),
    ("Axios Pro Rata",   "https://api.axios.com/feed/"),
]

# ─────────────────────────────────────────────────────────────────
# Date parsing
# ─────────────────────────────────────────────────────────────────
DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def parse_pub_date(date_str):
    """Parse various RSS/Atom date formats to YYYY-MM-DD string."""
    if not date_str:
        return ""
    s = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Last-ditch: strip timezone and try again
    m = re.match(r"(.*?)(?:\s*[+-]\d{4}|Z)?$", s)
    if m:
        try:
            dt = datetime.strptime(m.group(1).strip(), "%a, %d %b %Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


# ─────────────────────────────────────────────────────────────────
# RSS fetching with retry
# ─────────────────────────────────────────────────────────────────
def fetch_feed(name, url):
    """
    Fetch an RSS/Atom feed with retry logic.
    Returns (items, error_or_None).
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"}
    last_err = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
                logger.warning("  %s returned %s (attempt %d/%d)",
                               name, resp.status_code, attempt, MAX_RETRIES)
                if resp.status_code in (403, 404):
                    break  # no point retrying a 404/403
                time.sleep(RETRY_BACKOFF * attempt)
                continue

            return _parse_feed_xml(resp.content, name), None

        except requests.exceptions.RequestException as e:
            last_err = str(e)
            logger.warning("  %s error on attempt %d/%d: %s",
                           name, attempt, MAX_RETRIES, e)
            time.sleep(RETRY_BACKOFF * attempt)
        except ET.ParseError as e:
            last_err = f"parse error: {e}"
            logger.warning("  %s XML parse error: %s", name, e)
            break

    return [], last_err or "unknown error"


def _parse_feed_xml(content, source_name):
    """Parse RSS/Atom XML into list of item dicts."""
    items = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning("  XML parse error in %s: %s", source_name, e)
        return items

    # Standard RSS <item>
    for item in root.iter("item"):
        parsed = _item_to_dict(item, source_name, is_atom=False)
        if parsed:
            items.append(parsed)

    # Atom <entry>
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            parsed = _item_to_dict(entry, source_name, is_atom=True, ns=ns)
            if parsed:
                items.append(parsed)

    return items


def _item_to_dict(elem, source_name, is_atom, ns=None):
    """Convert RSS item or Atom entry element to dict."""
    try:
        if is_atom:
            ns = ns or {"atom": "http://www.w3.org/2005/Atom"}
            title = (elem.findtext("atom:title", "", ns) or elem.findtext("title", "") or "").strip()
            desc = (elem.findtext("atom:summary", "", ns) or elem.findtext("summary", "") or "").strip()
            pub = (elem.findtext("atom:published", "", ns)
                   or elem.findtext("atom:updated", "", ns)
                   or elem.findtext("published", "")
                   or elem.findtext("updated", "")
                   or "")
            link_el = elem.find("atom:link", ns) or elem.find("link")
            link = link_el.get("href", "") if link_el is not None else ""
        else:
            title = (elem.findtext("title", "") or "").strip()
            desc = (elem.findtext("description", "") or "").strip()
            pub = elem.findtext("pubDate", "") or ""
            link = (elem.findtext("link", "") or "").strip()

        # Strip HTML tags from description
        desc = unescape(re.sub(r"<[^>]+>", "", desc))[:600]
        title = unescape(title)

        return {
            "title": title,
            "description": desc,
            "pubDate": pub,
            "link": link,
            "source": source_name,
        }
    except Exception as e:
        logger.debug("  item parse error in %s: %s", source_name, e)
        return None


# ─────────────────────────────────────────────────────────────────
# Main extraction pipeline
# ─────────────────────────────────────────────────────────────────
def extract_deal(item):
    """
    Try to extract a structured funding deal from an RSS item.
    Returns dict or None.

    Until Oct 2026 this matched any master-list name or alias as a substring
    of headline + summary, then checked that the name's first word appeared
    in the headline. So a round was credited to whichever tracked company the
    story mentioned, and the first dollar figure became its size ("targeting
    the $12 billion market"). It now takes everything from the deal feed's
    guarded code, so the two feeds cannot disagree about who raised what.
    """
    if not fetch_deals.COMPANY_ALIASES:
        fetch_deals.init_matcher()
    title = item.get("title", "") or ""
    deal = fetch_deals.extract_deal_from_article(
        {"title": title, "description": item.get("description", "") or ""})
    if not deal:
        return None
    pub_date = parse_pub_date(item.get("pubDate", ""))
    return {
        "company": deal["company"],
        "amount": deal["amount"],
        "round": deal["round"],
        "investors": deal["investors"],
        "date": pub_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": item.get("source", ""),
        "url": item.get("link", ""),
        "headline": title[:160],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def dedupe_deals(deals):
    """Remove duplicate deals by (company, amount, round) tuple."""
    seen = set()
    out = []
    for d in deals:
        key = (d["company"], d["amount"], d["round"])
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_json(data, filename):
    """Save data to JSON with pretty indent."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


def save_status(status):
    """Write a status metadata file (always, even on total failure)."""
    save_json(status, "funding_feed_status.json")


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Funding RSS Aggregator")
    logger.info("=" * 60)
    fetch_deals.init_matcher()
    tracked = len(set(fetch_deals.COMPANY_ALIASES.values()))
    logger.info("Companies tracked: %d", tracked)
    logger.info("Feeds: %d", len(FUNDING_FEEDS))

    started_at = datetime.now(timezone.utc).isoformat()
    feed_status = []
    all_items = []

    for name, url in FUNDING_FEEDS:
        logger.info("Fetching %s ...", name)
        items, err = fetch_feed(name, url)
        feed_status.append({
            "source": name,
            "url": url,
            "items_fetched": len(items),
            "error": err,
        })
        if items:
            logger.info("  -> %d items", len(items))
            all_items.extend(items)
        time.sleep(0.5)

    logger.info("Total RSS items: %d", len(all_items))

    # Extract deals
    deals = []
    for item in all_items:
        deal = extract_deal(item)
        if deal:
            deals.append(deal)

    deals = dedupe_deals(deals)
    # Sort newest first
    deals.sort(key=lambda d: d.get("date", ""), reverse=True)

    logger.info("Extracted %d structured funding deals", len(deals))
    skipped = {(s["company"], s["headline"]): s for s in fetch_deals.SKIPPED}
    for s in list(skipped.values())[:40]:
        logger.info("  SKIP %s: %s — \"%s\"", s["company"], s["reason"], s["headline"])

    # Write outputs
    save_json(deals, "funding_feed_auto.json")

    status = {
        "script": "fetch_funding_rss.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "companies_tracked": tracked,
        "total_items_fetched": len(all_items),
        "total_deals_extracted": len(deals),
        "feeds": feed_status,
        "ok": any(fs["items_fetched"] > 0 for fs in feed_status),
    }
    save_status(status)

    # Summary
    if deals:
        logger.info("\nTop deals:")
        for d in deals[:10]:
            logger.info("  %s | %-25s %-12s %s",
                        d["date"], d["company"][:25], d["amount"], d["round"])

    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        # Even on fatal error, write status file so pipeline knows what happened
        save_status({
            "script": "fetch_funding_rss.py",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "ok": False,
            "fatal_error": str(e),
        })
        raise
