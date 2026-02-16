#!/usr/bin/env python3
"""
Press Release Aggregator
Fetches press releases from PR Newswire and GlobeNewswire RSS feeds.
Completely free - uses public RSS feeds.
Now uses master company list for 450+ company coverage.
"""

import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import time
import re
from html import unescape

# Load master company list
def load_master_companies():
    """Load company names and aliases from the JS master list."""
    script_dir = Path(__file__).parent
    master_list_path = script_dir / "company_master_list.js"

    companies = []
    if master_list_path.exists():
        content = master_list_path.read_text()
        # Simple regex extraction of company names and aliases
        import re
        # Match: { name: "...", aliases: [...], ...
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

# Load company list at module level
MASTER_COMPANIES = load_master_companies()

# PR Newswire RSS feeds by industry
PR_NEWSWIRE_FEEDS = {
    "aerospace": "https://www.prnewswire.com/rss/aerospace-defense-news.rss",
    "technology": "https://www.prnewswire.com/rss/technology-latest-news.rss",
    "energy": "https://www.prnewswire.com/rss/energy-latest-news.rss",
    "biotech": "https://www.prnewswire.com/rss/biotechnology-latest-news.rss",
}

# GlobeNewswire RSS feeds
GLOBENEWSWIRE_FEEDS = {
    "all": "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20News%20Releases",
}

# Build TRACKED_COMPANIES from master list (450+ companies with aliases)
def get_tracked_companies():
    """Get all company names and aliases for tracking."""
    if MASTER_COMPANIES:
        all_terms = []
        for company in MASTER_COMPANIES:
            all_terms.append(company['name'])
            # Only add aliases that are 4+ chars to avoid false matches
            all_terms.extend([a for a in company['aliases'] if len(a) >= 4])
        return list(set(all_terms))
    else:
        # Fallback to basic list if master list not found
        return [
            "Anduril", "Shield AI", "Palantir", "SpaceX", "Rocket Lab",
            "OpenAI", "Anthropic", "Figure AI", "Oklo", "Helion",
            "Commonwealth Fusion", "Tesla", "Nvidia", "AMD"
        ]

TRACKED_COMPANIES = get_tracked_companies()

# Keywords for categorization
CATEGORY_KEYWORDS = {
    "funding": ["funding", "raises", "raised", "million", "billion", "investment", "series", "round"],
    "contract": ["contract", "award", "selected", "wins", "awarded"],
    "partnership": ["partnership", "partner", "collaboration", "agreement", "alliance"],
    "product": ["launches", "announces", "introduces", "unveils", "releases"],
    "milestone": ["milestone", "achieves", "completes", "breakthrough", "first"],
    "ipo": ["IPO", "public", "SPAC", "merger", "acquisition"],
    "hiring": ["hires", "appoints", "names", "executive", "CEO", "CTO"],
}

def parse_rss_feed(url, source):
    """Parse an RSS feed and extract items."""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)

        items = []
        for item in root.findall(".//item"):
            title = item.find("title")
            link = item.find("link")
            description = item.find("description")
            pub_date = item.find("pubDate")

            if title is not None:
                items.append({
                    "title": unescape(title.text or ""),
                    "link": link.text if link is not None else "",
                    "description": unescape((description.text or "")[:500]),
                    "pubDate": pub_date.text if pub_date is not None else "",
                    "source": source,
                })

        return items

    except Exception as e:
        print(f"  Error parsing {url}: {e}")
        return []

def filter_relevant_releases(items):
    """Filter press releases for tracked companies using master list."""
    relevant = []

    for item in items:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()

        # Find matching companies from master list
        matched_companies = []
        matched_sectors = set()

        if MASTER_COMPANIES:
            for company in MASTER_COMPANIES:
                # Check company name
                if company['name'].lower() in text:
                    matched_companies.append(company['name'])
                    continue
                # Check aliases (4+ chars only)
                for alias in company['aliases']:
                    if len(alias) >= 4 and alias.lower() in text:
                        matched_companies.append(company['name'])
                        break
        else:
            # Fallback to simple matching
            for company in TRACKED_COMPANIES:
                if company.lower() in text:
                    matched_companies.append(company)

        if matched_companies:
            # Remove duplicates while preserving order
            seen = set()
            unique_companies = []
            for c in matched_companies:
                if c not in seen:
                    seen.add(c)
                    unique_companies.append(c)

            # Categorize the release
            categories = []
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(kw.lower() in text for kw in keywords):
                    categories.append(cat)

            item["companies"] = unique_companies
            item["categories"] = categories
            relevant.append(item)

    return relevant

def parse_pub_date(date_str):
    """Parse various date formats to YYYY-MM-DD."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue

    return ""

def fetch_all_press_releases():
    """Fetch press releases from all feeds."""
    all_releases = []

    # Fetch from PR Newswire
    for industry, url in PR_NEWSWIRE_FEEDS.items():
        print(f"Fetching PR Newswire {industry}...")
        items = parse_rss_feed(url, f"prnewswire_{industry}")
        print(f"  Found {len(items)} items")
        all_releases.extend(items)
        time.sleep(0.5)

    # Fetch from GlobeNewswire
    for feed_name, url in GLOBENEWSWIRE_FEEDS.items():
        print(f"Fetching GlobeNewswire {feed_name}...")
        items = parse_rss_feed(url, f"globenewswire_{feed_name}")
        print(f"  Found {len(items)} items")
        all_releases.extend(items)
        time.sleep(0.5)

    return all_releases

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(releases):
    """Generate JavaScript code snippet for PRESS_RELEASES."""
    # Parse and sort by date
    for r in releases:
        r["date"] = parse_pub_date(r.get("pubDate", ""))

    releases.sort(key=lambda x: x.get("date", ""), reverse=True)

    js_output = "// Auto-updated press releases\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const PRESS_RELEASES = [\n"

    for r in releases[:40]:
        title = r.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        companies = ", ".join(r.get("companies", [])[:3])
        categories = ", ".join(r.get("categories", [])[:2])

        js_output += f'  {{ title: "{title}", '
        js_output += f'date: "{r["date"]}", companies: "{companies}", '
        js_output += f'categories: "{categories}", source: "{r["source"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "press_releases_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("Press Release Aggregator")
    print("=" * 60)
    print(f"Master company list: {len(MASTER_COMPANIES)} companies loaded")
    print(f"Search terms: {len(TRACKED_COMPANIES)} (including aliases)")
    print(f"Fetching from {len(PR_NEWSWIRE_FEEDS) + len(GLOBENEWSWIRE_FEEDS)} RSS feeds")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all releases
    all_releases = fetch_all_press_releases()
    print(f"\nTotal releases fetched: {len(all_releases)}")

    # Filter relevant
    relevant = filter_relevant_releases(all_releases)
    print(f"Relevant to tracked companies: {len(relevant)}")

    # Save data
    save_to_json(all_releases, "press_releases_raw.json")
    save_to_json(relevant, "press_releases_filtered.json")

    # Generate JS snippet
    generate_js_snippet(relevant)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    if relevant:
        print("\nMost mentioned companies:")
        company_counts = {}
        for r in relevant:
            for c in r.get("companies", []):
                company_counts[c] = company_counts.get(c, 0) + 1
        for company, count in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {company}: {count} releases")

        print("\nRecent releases:")
        for r in sorted(relevant, key=lambda x: x.get("date", ""), reverse=True)[:5]:
            print(f"  [{r.get('date', 'N/A')}] {r['title'][:60]}...")

if __name__ == "__main__":
    main()
