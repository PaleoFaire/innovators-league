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
PR_NEWSWIRE_FEEDS = {
    "aerospace": "https://www.prnewswire.com/rss/aerospace-defense-news.rss",
    "technology": "https://www.prnewswire.com/rss/technology-latest-news.rss",
    "energy": "https://www.prnewswire.com/rss/energy-latest-news.rss",
    "biotech": "https://www.prnewswire.com/rss/biotechnology-latest-news.rss",
    "news_releases_list": "https://www.prnewswire.com/rss/news-releases-list.rss",
}

GLOBENEWSWIRE_FEEDS = {
    "all": "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20News%20Releases",
    "technology": "https://www.globenewswire.com/rss/technology",
}

BUSINESSWIRE_FEEDS = {
    "home": "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVtRXw==",
    "technology": "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeGVtaWA==",
}

REUTERS_FEEDS = {
    "business": "https://www.reutersagency.com/feed/?best-sectors=business-finance&post_type=best",
    "technology": "https://www.reutersagency.com/feed/?best-sectors=technology-innovation&post_type=best",
}

CATEGORY_KEYWORDS = {
    "funding": ["funding", "raises", "raised", "million", "billion", "investment", "series", "round"],
    "contract": ["contract", "award", "selected", "wins", "awarded"],
    "partnership": ["partnership", "partner", "collaboration", "agreement", "alliance"],
    "product": ["launches", "announces", "introduces", "unveils", "releases"],
    "milestone": ["milestone", "achieves", "completes", "breakthrough", "first"],
    "ipo": ["IPO", "public", "SPAC", "merger", "acquisition"],
    "hiring": ["hires", "appoints", "names", "executive", "CEO", "CTO"],
}

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
def _company_mentions(text):
    """Return the list of master-list companies mentioned in `text`."""
    text_lower = text.lower()
    mentioned = []
    if not MASTER_COMPANIES:
        return mentioned
    for company in MASTER_COMPANIES:
        name_lower = company['name'].lower()
        hit = False
        if len(name_lower) >= 6:
            if name_lower in text_lower:
                hit = True
        else:
            if re.search(r'\b' + re.escape(name_lower) + r'\b', text_lower):
                hit = True
        if not hit:
            for alias in company['aliases']:
                if len(alias) >= 4 and alias.lower() in text_lower:
                    hit = True
                    break
        if hit:
            mentioned.append(company['name'])
    return mentioned


def filter_relevant_releases(items, window_days=WINDOW_DAYS):
    """
    Keep only items from the last `window_days` that mention a tracked company.
    Dedup by URL.
    """
    relevant = []
    seen_urls = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

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

        text = (item.get("title", "") + " " + item.get("description", ""))
        matched = _company_mentions(text)
        if not matched:
            continue

        seen = set()
        unique = []
        for c in matched:
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
