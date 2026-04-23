#!/usr/bin/env python3
"""
Press Release Aggregator
========================
Fetches press releases from a broad set of free RSS feeds and filters them
for mentions of companies tracked in The Innovators League.

Sources:
  - PR Newswire (4 industry feeds)
  - GlobeNewswire (general + technology)
  - BusinessWire (top-news)
  - Reuters Business news

Improvements over v1:
  - Retries with backoff on transient errors
  - URL-level dedup across sources
  - Keeps only the last 14 days of releases
  - Loads the master company list the same way fetch_deals.py does,
    giving much better matching coverage
  - Targets 100+ relevant records per run
  - Writes `press_releases_auto.js` with 100 entries (was 5)
"""

import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore


# ─────────────────────────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────────────────────────
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
        "User-Agent": "InnovatorsLeague-PressReleaseBot/2.0",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    return session


SESSION = _make_session()
REQUEST_TIMEOUT = 20
WINDOW_DAYS = 14


# ─────────────────────────────────────────────────────────────────
# Master company list
# ─────────────────────────────────────────────────────────────────
def load_master_companies():
    script_dir = Path(__file__).parent
    master_list_path = script_dir / "company_master_list.js"

    companies = []
    if master_list_path.exists():
        content = master_list_path.read_text()
        pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
        for match in re.finditer(pattern, content):
            name = match.group(1)
            aliases_str = match.group(2)
            aliases = [a.strip().strip('"') for a in aliases_str.split(',') if a.strip()]
            companies.append({
                'name': name,
                'aliases': aliases,
                'search_terms': [name] + aliases
            })
    return companies


MASTER_COMPANIES = load_master_companies()


# ─────────────────────────────────────────────────────────────────
# Feed configuration
# ─────────────────────────────────────────────────────────────────
# 2026-04-23 overhaul: audited all 11 original sources. PR Newswire feeds
# started blocking our IP (ConnectionResetError), Reuters endpoints went
# 404, and BusinessWire's RSS started returning 0 items despite 200 OK.
# The original GlobeNewswire "all" feed is the only survivor.
#
# Swapped the dead generic wire services for 6 frontier-tech-specific
# outlets, which are strictly more relevant to our audience: SpaceNews,
# DefenseNews, Breaking Defense, Space Policy Online, BioPharma Dive,
# and Inside Defense. Net result: richer signal and 90 + items per
# fetch vs. the old ~20.
PR_NEWSWIRE_FEEDS = {
    # Intentionally empty — PR Newswire RSS endpoints are blocking our IP.
    # Kept as a hook so future attempts to re-enable them can reuse the
    # existing iteration code without reshaping the pipeline.
}

GLOBENEWSWIRE_FEEDS = {
    "all": "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20News%20Releases",
}

# New vertical trade-press feeds replace the generic wire services.
# These surface higher-signal frontier-tech news that our old generic
# wires were not tagging correctly.
VERTICAL_FEEDS = {
    "spacenews":          "https://spacenews.com/feed/",
    "defensenews":        "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
    "breakingdefense":    "https://breakingdefense.com/feed/",
    "spacepolicyonline":  "https://spacepolicyonline.com/feed/",
    "biopharmadive":      "https://www.biopharmadive.com/feeds/news/",
    "insidedefense":      "https://insidedefense.com/rss.xml",
}

# Kept as empty hooks so existing iteration code keeps working without
# major refactor. Can be reseeded if these services ever come back.
BUSINESSWIRE_FEEDS = {}
REUTERS_FEEDS = {}

CATEGORY_KEYWORDS = {
    "funding": ["funding", "raises", "raised", "million", "billion", "investment", "series", "round"],
    "contract": ["contract", "award", "selected", "wins", "awarded"],
    "partnership": ["partnership", "partner", "collaboration", "agreement", "alliance"],
    "product": ["launches", "announces", "introduces", "unveils", "releases"],
    "milestone": ["milestone", "achieves", "completes", "breakthrough", "first"],
    "ipo": ["IPO", "public", "SPAC", "merger", "acquisition"],
    "hiring": ["hires", "appoints", "names", "executive", "CEO", "CTO"],
}

# ─────────────────────────────────────────────────────────────────
# Quality filters — Round 6 fix for garbage in Live Signals
# ─────────────────────────────────────────────────────────────────
GARBAGE_KEYWORDS = [
    "coupon", "discount code", "promo code", "deal of the day",
    "best of ", "review:", "review |", "how to ", "guide to ",
    "shopping", "flash sale", "amazon prime", "save $", "save on",
    "top 10 ", "listicle", "gift guide", "best gifts",
    "black friday", "cyber monday", "unboxing", "hands-on review",
]

# Generic/short company names that require stricter context (capitalized, or
# with company marker within 3 words) — these names are common English words
# and cause false-positive matches when scanned as bare substrings.
SHORT_GENERIC_NAMES = {
    'ada', 'cape', 'sift', 'revel', 'cover', 'modal', 'runway', 'prepared',
    'surge ai', 'rain ai', 'hive ai', 'field ai', 'flux', 'matter', 'dirac',
    'freeform', 'drafter', 'hlabs', 'group1', 'openx', 'emelody', 'advano',
    'rangeview', 'duranium', 'ouster', 'durin', 'attio', 'twelve',
}


def is_garbage(text):
    """True if the release looks like shopping / review / listicle content."""
    t = text.lower()
    return any(kw in t for kw in GARBAGE_KEYWORDS)

DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


# ─────────────────────────────────────────────────────────────────
# RSS parsing
# ─────────────────────────────────────────────────────────────────
def parse_rss_feed(url, source):
    try:
        response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return []
    if response.status_code != 200:
        print(f"  {url}: HTTP {response.status_code}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"  Error parsing {url}: {e}")
        return []

    items = []
    for item in root.findall(".//item"):
        title = item.find("title")
        link = item.find("link")
        description = item.find("description")
        pub_date = item.find("pubDate")
        if title is None:
            continue
        items.append({
            "title": unescape((title.text or "").strip()),
            "link": (link.text or "").strip() if link is not None else "",
            "description": unescape((description.text or "")[:500]) if description is not None else "",
            "pubDate": (pub_date.text or "").strip() if pub_date is not None else "",
            "source": source,
        })
    return items


def parse_pub_date_dt(date_str):
    """Return a timezone-aware datetime or None."""
    if not date_str:
        return None
    s = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def parse_pub_date(date_str):
    dt = parse_pub_date_dt(date_str)
    return dt.strftime("%Y-%m-%d") if dt else ""


# ─────────────────────────────────────────────────────────────────
# Filtering & dedup
# ─────────────────────────────────────────────────────────────────
def _company_mentions(text, original_text=None):
    """Return the list of master-list companies mentioned in `text`.

    Uses strict word-boundary matching for every name and alias (no bare
    substring matches). Short/generic names additionally require a
    capitalized occurrence in the original cased text so they don't trigger
    on common English words (e.g. "cover", "flux", "matter").
    """
    text_lower = text.lower()
    cased = original_text if original_text is not None else text
    mentioned = []
    if not MASTER_COMPANIES:
        return mentioned
    for company in MASTER_COMPANIES:
        name_lower = company['name'].lower()
        hit = False

        # Always word-boundary match
        name_re = re.compile(r'\b' + re.escape(name_lower) + r'\b', re.IGNORECASE)
        if name_re.search(text_lower):
            if name_lower in SHORT_GENERIC_NAMES:
                # Require the properly-cased company name to appear in the
                # original text (avoids matching "cover" as Cover.ai).
                if re.search(r'\b' + re.escape(company['name']) + r'\b', cased):
                    hit = True
            else:
                hit = True

        if not hit:
            for alias in company['aliases']:
                if len(alias) < 5:
                    continue
                alias_lower = alias.lower()
                if alias_lower in SHORT_GENERIC_NAMES:
                    continue
                alias_re = re.compile(r'\b' + re.escape(alias_lower) + r'\b', re.IGNORECASE)
                if alias_re.search(text_lower):
                    hit = True
                    break

        if hit:
            mentioned.append(company['name'])
    return mentioned


def _company_in_title(company_name, title):
    """Word-boundary check that `company_name` appears in the title."""
    if not title:
        return False
    pattern = r'\b' + re.escape(company_name.lower()) + r'\b'
    return re.search(pattern, title.lower()) is not None


def filter_relevant_releases(items, window_days=WINDOW_DAYS):
    """
    Keep only items from the last `window_days` that mention a tracked company.
    Dedup by URL.
    """
    relevant = []
    seen_urls = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    dropped_garbage = 0
    dropped_body_only = 0

    for item in items:
        url = item.get("link") or ""
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)

        # Date filter
        dt = parse_pub_date_dt(item.get("pubDate", ""))
        if dt and dt < cutoff:
            continue

        title = item.get("title", "") or ""
        # Only use first 300 chars of description so we don't grab unrelated
        # boilerplate trailing text that causes cross-matches.
        description = (item.get("description", "") or "")[:300]
        text = title + " " + description

        # Quality gate 1: drop obvious garbage (coupons, reviews, listicles).
        if is_garbage(text):
            dropped_garbage += 1
            continue

        matched = _company_mentions(text)
        if not matched:
            continue

        # Quality gate 2: at least one matched company must appear in the
        # TITLE (word-boundary). Body-only matches are typically coincidental
        # substring hits on unrelated releases.
        title_matched = [c for c in matched if _company_in_title(c, title)]
        if not title_matched:
            dropped_body_only += 1
            continue

        # Preserve order; title-matched companies first, then body mentions.
        seen = set()
        unique = []
        for c in title_matched + matched:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        categories = []
        text_lower = text.lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                categories.append(cat)

        item["companies"] = unique
        item["categories"] = categories
        item["date"] = parse_pub_date(item.get("pubDate", ""))
        relevant.append(item)

    print(f"  Quality filter: dropped {dropped_garbage} garbage, "
          f"{dropped_body_only} body-only matches")
    return relevant


# ─────────────────────────────────────────────────────────────────
# Fetcher
# ─────────────────────────────────────────────────────────────────
def fetch_all_press_releases():
    all_releases = []
    feed_stats = []

    all_feeds = []
    for industry, url in PR_NEWSWIRE_FEEDS.items():
        all_feeds.append((f"prnewswire_{industry}", url))
    for feed_name, url in GLOBENEWSWIRE_FEEDS.items():
        all_feeds.append((f"globenewswire_{feed_name}", url))
    for feed_name, url in BUSINESSWIRE_FEEDS.items():
        all_feeds.append((f"businesswire_{feed_name}", url))
    for feed_name, url in REUTERS_FEEDS.items():
        all_feeds.append((f"reuters_{feed_name}", url))
    for feed_name, url in VERTICAL_FEEDS.items():
        all_feeds.append((feed_name, url))

    for source_name, url in all_feeds:
        print(f"Fetching {source_name}...")
        items = parse_rss_feed(url, source_name)
        print(f"  Found {len(items)} items")
        all_releases.extend(items)
        feed_stats.append((source_name, len(items)))
        time.sleep(0.5)

    return all_releases, feed_stats


# ─────────────────────────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────────────────────────
def save_to_json(data, filename):
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} records to {output_path}")


def generate_js_snippet(releases):
    for r in releases:
        r["date"] = r.get("date") or parse_pub_date(r.get("pubDate", ""))
    releases.sort(key=lambda x: x.get("date", ""), reverse=True)

    js_output = "// Auto-updated press releases\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const PRESS_RELEASES = [\n"

    for r in releases[:100]:
        title = r.get("title", "").replace('"', '\\"').replace('\n', ' ')[:100]
        companies = ", ".join(r.get("companies", [])[:3])
        categories = ", ".join(r.get("categories", [])[:2])
        js_output += f'  {{ title: "{title}", '
        js_output += f'date: "{r.get("date", "")}", companies: "{companies}", '
        js_output += f'categories: "{categories}", source: "{r["source"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "press_releases_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)
    print(f"Generated JS snippet at {output_path}")


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Press Release Aggregator")
    print("=" * 60)
    print(f"Master company list: {len(MASTER_COMPANIES)} companies loaded")
    print(f"Window: last {WINDOW_DAYS} days")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_releases, feed_stats = fetch_all_press_releases()
    print(f"\nTotal releases fetched: {len(all_releases)}")

    relevant = filter_relevant_releases(all_releases)
    print(f"Relevant to tracked companies (last {WINDOW_DAYS} days): {len(relevant)}")

    save_to_json(all_releases, "press_releases_raw.json")
    save_to_json(relevant, "press_releases_filtered.json")

    generate_js_snippet(relevant)

    print("\n" + "=" * 60)
    print("Feed Summary")
    print("=" * 60)
    for source, count in feed_stats:
        print(f"  {source}: {count}")

    if relevant:
        print("\nMost mentioned companies:")
        company_counts = {}
        for r in relevant:
            for c in r.get("companies", []):
                company_counts[c] = company_counts.get(c, 0) + 1
        for company, count in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {company}: {count} releases")

        print("\nRecent relevant releases:")
        for r in sorted(relevant, key=lambda x: x.get("date", ""), reverse=True)[:5]:
            title = r.get('title', '')
            print(f"  [{r.get('date', 'N/A')}] {title[:60]}...")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
