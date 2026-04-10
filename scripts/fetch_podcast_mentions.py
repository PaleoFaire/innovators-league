#!/usr/bin/env python3
"""
Podcast Mentions Fetcher
========================
Tracks mentions of frontier tech companies across popular tech/VC podcasts
via their public RSS feeds. Does NOT transcribe audio — uses only episode
titles and descriptions (shownotes) which are typically rich enough to catch
the vast majority of company discussions.

Sources:
    - Acquired
    - All-In
    - 20VC
    - Lex Fridman
    - Invest Like the Best

Output:
    data/podcast_mentions_auto.json — list of mention records
    data/podcast_mentions_status.json — fetch status metadata

Run standalone:
    python3 scripts/fetch_podcast_mentions.py
"""

import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("podcast_mentions")

# ─────────────────────────────────────────────────────────────────
# Paths and constants
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
MASTER_LIST_PATH = SCRIPT_DIR / "company_master_list.js"

USER_AGENT = "InnovatorsLeague-PodcastBot/1.0 (+https://innovatorsleague.com)"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds
LOOKBACK_DAYS = 30

# Podcast RSS feeds — (display name, url)
PODCAST_FEEDS = [
    ("Acquired",              "https://feeds.transistor.fm/acquired"),
    ("All-In",                "https://allinchamathjason.libsyn.com/rss"),
    ("20VC",                  "https://feeds.megaphone.fm/1071392"),
    ("Lex Fridman",           "https://lexfridman.com/feed/podcast/"),
    ("Invest Like the Best",  "https://feeds.megaphone.fm/EGP9797299583"),
]

# Words that look like company names but are generic and should be skipped
GENERIC_ALIAS_STOPWORDS = {
    "aging", "allies", "arctic", "array", "atomic", "audio", "beacon",
    "carbon", "charge", "condor", "desert", "energy", "fabric", "falcon",
    "forge", "fusion", "garden", "ghost", "global", "harbor", "ignite",
    "impact", "launch", "matter", "merge", "neural", "ocean", "orbit",
    "radar", "radiant", "rocket", "scout", "shield", "signal", "solar",
    "space", "spark", "target", "terra", "tower", "vapor", "vertex",
    "blimps", "agtech", "quantum", "robotics",
    "autonomous drones", "laser communications", "space laser",
    "optical inter-satellite link", "road runner",
}


# ─────────────────────────────────────────────────────────────────
# Master company list loader
# ─────────────────────────────────────────────────────────────────
def load_master_companies():
    """Load companies with aliases from company_master_list.js."""
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


# ─────────────────────────────────────────────────────────────────
# Company matching (returns ALL matched companies, not just first)
# ─────────────────────────────────────────────────────────────────
def find_matching_companies(text):
    """Return list of canonical company names mentioned in `text`."""
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

        # Longer names: substring
        if len(name_lower) >= 6:
            if name_lower in text_lower:
                matched.append(name)
                seen.add(name)
                continue
        else:
            # Short names: word boundary
            if re.search(r"\b" + re.escape(name_lower) + r"\b", text_lower):
                matched.append(name)
                seen.add(name)
                continue

        # Aliases
        for alias in company["aliases"]:
            alias_lower = alias.lower()
            if len(alias_lower) < 5:
                continue
            if alias_lower in GENERIC_ALIAS_STOPWORDS:
                continue
            if alias_lower in text_lower:
                matched.append(name)
                seen.add(name)
                break

    return matched


# ─────────────────────────────────────────────────────────────────
# RSS fetching
# ─────────────────────────────────────────────────────────────────
def fetch_feed(name, url):
    """Fetch a podcast RSS feed with retry. Returns (items, error_or_None)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return _parse_rss(resp.content, name), None
            logger.warning("  %s returned %s (attempt %d/%d)",
                           name, resp.status_code, attempt, MAX_RETRIES)
            if resp.status_code in (403, 404):
                return [], f"HTTP {resp.status_code}"
            time.sleep(RETRY_BACKOFF * attempt)
        except requests.exceptions.RequestException as e:
            logger.warning("  %s request error (attempt %d/%d): %s",
                           name, attempt, MAX_RETRIES, e)
            time.sleep(RETRY_BACKOFF * attempt)

    return [], "all retries failed"


def _parse_rss(content, source_name):
    """Parse podcast RSS XML into list of episode dicts."""
    items = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.warning("  XML parse error in %s: %s", source_name, e)
        return items

    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

    for item in root.iter("item"):
        try:
            title = (item.findtext("title") or "").strip()
            description = (item.findtext("description") or "").strip()
            # Prefer itunes:summary if description is empty
            if not description:
                description = (item.findtext("itunes:summary", "", ns) or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            link = (item.findtext("link") or "").strip()

            description = unescape(re.sub(r"<[^>]+>", " ", description))
            description = re.sub(r"\s+", " ", description)[:1500]
            title = unescape(title)

            items.append({
                "title": title,
                "description": description,
                "pub_date": pub_date,
                "url": link,
                "podcast": source_name,
            })
        except Exception as e:
            logger.debug("  item parse error in %s: %s", source_name, e)

    return items


# ─────────────────────────────────────────────────────────────────
# Date parsing + recency filter
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


def parse_pub_date(s):
    """Parse various date formats to a datetime. Returns None if unparseable."""
    if not s:
        return None
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # Strip trailing timezone and retry
    m = re.match(r"(.*?\d{4} \d{2}:\d{2}:\d{2})", s)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%a, %d %b %Y %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def is_recent(dt, days=LOOKBACK_DAYS):
    if not dt:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


# ─────────────────────────────────────────────────────────────────
# Excerpt builder (show text around first mention)
# ─────────────────────────────────────────────────────────────────
def build_excerpt(text, company, context=120):
    """Return a short excerpt of the description around the company mention."""
    if not text or not company:
        return (text or "")[:300]
    idx = text.lower().find(company.lower())
    if idx < 0:
        return text[:300]
    start = max(0, idx - context)
    end = min(len(text), idx + len(company) + context)
    snippet = text[start:end].strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


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
    logger.info("Podcast Mentions Fetcher")
    logger.info("=" * 60)
    logger.info("Tracking %d companies across %d podcasts",
                len(MASTER_COMPANIES), len(PODCAST_FEEDS))
    logger.info("Lookback window: %d days", LOOKBACK_DAYS)

    started_at = datetime.now(timezone.utc).isoformat()
    feed_status = []
    all_episodes = []

    for name, url in PODCAST_FEEDS:
        logger.info("Fetching %s …", name)
        items, err = fetch_feed(name, url)
        feed_status.append({
            "podcast": name,
            "url": url,
            "episodes_fetched": len(items),
            "error": err,
        })
        logger.info("  -> %d episodes", len(items))
        all_episodes.extend(items)
        time.sleep(0.5)

    logger.info("Total episodes fetched: %d", len(all_episodes))

    # Filter to recent + match
    mentions = []
    for ep in all_episodes:
        pub_dt = parse_pub_date(ep.get("pub_date", ""))
        if not is_recent(pub_dt):
            continue

        combined = f"{ep.get('title', '')} {ep.get('description', '')}"
        matches = find_matching_companies(combined)
        if not matches:
            continue

        date_str = pub_dt.strftime("%Y-%m-%d") if pub_dt else ""
        for company in matches:
            mentions.append({
                "company": company,
                "podcast": ep.get("podcast", ""),
                "episode_title": ep.get("title", "")[:200],
                "episode_date": date_str,
                "url": ep.get("url", ""),
                "description_excerpt": build_excerpt(
                    ep.get("description", ""), company
                ),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

    # Sort newest first
    mentions.sort(key=lambda m: m.get("episode_date", ""), reverse=True)
    logger.info("Found %d company mentions in recent episodes", len(mentions))

    # Save outputs
    save_json(mentions, "podcast_mentions_auto.json")

    status = {
        "script": "fetch_podcast_mentions.py",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "podcasts": feed_status,
        "total_episodes": len(all_episodes),
        "total_mentions": len(mentions),
        "ok": any(f["episodes_fetched"] > 0 for f in feed_status),
    }
    save_json(status, "podcast_mentions_status.json")

    # Summary
    if mentions:
        logger.info("\nMost-mentioned companies:")
        company_counts = {}
        for m in mentions:
            company_counts[m["company"]] = company_counts.get(m["company"], 0) + 1
        for company, count in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
            logger.info("  %-25s %d", company[:25], count)

        logger.info("\nRecent mentions:")
        for m in mentions[:5]:
            logger.info("  %s | %-20s | %s | %s",
                        m["episode_date"], m["podcast"][:20],
                        m["company"][:20], m["episode_title"][:50])

    logger.info("=" * 60)
    logger.info("Done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        save_json({
            "script": "fetch_podcast_mentions.py",
            "ok": False,
            "fatal_error": str(e),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }, "podcast_mentions_status.json")
        raise
