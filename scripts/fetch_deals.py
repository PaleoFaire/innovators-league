#!/usr/bin/env python3
"""
Deal Flow Fetcher for The Innovators League
Extracts funding round data from RSS news and Crunchbase News.
Merges with existing DEAL_TRACKER to keep historical data.

Sources:
  - news_raw.json (from aggregate_news.js — funding-type articles)
  - Crunchbase News RSS (funding announcements)
  - TechCrunch funding tag RSS

Free APIs only — no paid Crunchbase/PitchBook keys needed.
"""

import json
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

# RSS feeds specifically for funding news
FUNDING_FEEDS = [
    ("Crunchbase News", "https://news.crunchbase.com/feed/"),
    ("TechCrunch Startups", "https://techcrunch.com/category/startups/feed/"),
]

# Known company aliases for matching
COMPANY_ALIASES = {
    "anduril": "Anduril Industries",
    "spacex": "SpaceX",
    "palantir": "Palantir",
    "shield ai": "Shield AI",
    "rocket lab": "Rocket Lab",
    "figure": "Figure AI",
    "physical intelligence": "Physical Intelligence",
    "cerebras": "Cerebras",
    "helion": "Helion",
    "commonwealth fusion": "Commonwealth Fusion Systems",
    "oklo": "Oklo",
    "saronic": "Saronic",
    "epirus": "Epirus",
    "relativity": "Relativity Space",
    "boom supersonic": "Boom Supersonic",
    "boom": "Boom Supersonic",
    "zipline": "Zipline",
    "varda": "Varda Space Industries",
    "impulse space": "Impulse Space",
    "astranis": "Astranis",
    "captura": "Captura",
    "terraform": "Terraform Industries",
    "fervo": "Fervo Energy",
    "skydio": "Skydio",
    "waymo": "Waymo",
    "neuralink": "Neuralink",
    "hadrian": "Hadrian",
    "castelion": "Castelion",
    "radiant": "Radiant",
    "lightmatter": "Lightmatter",
    "etched": "Etched",
    "groq": "Groq",
    "scale ai": "Scale AI",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "x-energy": "X-Energy",
    "tae technologies": "TAE Technologies",
    "terrapower": "TerraPower",
    "joby": "Joby Aviation",
    "archer": "Archer Aviation",
    "planet labs": "Planet Labs",
    "intuitive machines": "Intuitive Machines",
    "rivian": "Rivian",
    "ionq": "IonQ",
    "rigetti": "Rigetti Computing",
    "d-wave": "D-Wave Quantum",
    "recursion": "Recursion Pharmaceuticals",
    "mammoth": "Mammoth Biosciences",
    "altos labs": "Altos Labs",
}

# Investor name normalization
INVESTOR_ALIASES = {
    "a16z": "a16z",
    "andreessen horowitz": "a16z",
    "founders fund": "Founders Fund",
    "sequoia": "Sequoia",
    "lux capital": "Lux Capital",
    "8vc": "8VC",
    "khosla": "Khosla Ventures",
    "general catalyst": "General Catalyst",
    "accel": "Accel",
    "benchmark": "Benchmark",
    "greylock": "Greylock",
    "tiger global": "Tiger Global",
    "coatue": "Coatue",
    "softbank": "SoftBank",
    "general atlantic": "General Atlantic",
    "thrive": "Thrive Capital",
    "lightspeed": "Lightspeed Venture Partners",
}


def fetch_rss(url, source_name):
    """Fetch and parse an RSS feed."""
    headers = {
        "User-Agent": "InnovatorsLeague-Bot/1.0 (https://innovatorsleague.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            desc = item.findtext("description", "").strip()
            # Strip HTML from description
            desc = re.sub(r'<[^>]+>', '', desc)[:500]
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "").strip()

            items.append({
                "title": title,
                "description": desc,
                "pubDate": pub_date,
                "link": link,
                "source": source_name
            })

        return items
    except Exception as e:
        print(f"  Error fetching {source_name}: {e}")
        return []


def parse_funding_amount(text):
    """Extract dollar amounts from text like '$600M', '$2.5B', '$30 million'."""
    # Match patterns like $600M, $2.5B, $30 million, $1.5 billion
    patterns = [
        r'\$(\d+(?:\.\d+)?)\s*[Bb](?:illion)?',  # $2.5B or $2.5 billion
        r'\$(\d+(?:\.\d+)?)\s*[Mm](?:illion)?',   # $600M or $600 million
        r'\$(\d+(?:,\d{3})+)',                      # $1,500,000
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = float(match.group(1).replace(',', ''))
            if 'b' in text[match.start():match.end()].lower():
                return f"${num}B" if num != int(num) else f"${int(num)}B"
            elif 'm' in text[match.start():match.end()].lower():
                return f"${int(num)}M" if num == int(num) else f"${num}M"
            else:
                if num >= 1e9:
                    return f"${num/1e9:.1f}B"
                elif num >= 1e6:
                    return f"${int(num/1e6)}M"
    return None


def parse_round_type(text):
    """Extract funding round type."""
    text_lower = text.lower()
    patterns = [
        (r'series\s+([a-z](?:-\d)?)', lambda m: f"Series {m.group(1).upper()}"),
        (r'seed\s+(?:round|funding)', lambda m: "Seed"),
        (r'pre-seed', lambda m: "Pre-Seed"),
        (r'(?:series\s+)?([a-z])\s+(?:round|extension)', lambda m: f"Series {m.group(1).upper()}"),
        (r'ipo', lambda m: "IPO"),
        (r'spac', lambda m: "SPAC"),
        (r'debt\s+(?:round|financing)', lambda m: "Debt"),
    ]

    for pattern, formatter in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return formatter(match)

    if 'funding' in text_lower or 'raise' in text_lower:
        return "Funding Round"
    return None


def match_company(text):
    """Try to match a company name from the text."""
    text_lower = text.lower()
    for alias, canonical in sorted(COMPANY_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in text_lower:
            return canonical
    return None


def match_investors(text):
    """Try to extract investor names from text."""
    text_lower = text.lower()
    found = []
    for alias, canonical in INVESTOR_ALIASES.items():
        if alias in text_lower:
            if canonical not in found:
                found.append(canonical)
    return found


def is_funding_article(title, description):
    """Check if an article is about a funding round."""
    text = f"{title} {description}".lower()
    funding_keywords = [
        'raises', 'raised', 'funding', 'series', 'round',
        'valuation', 'venture', 'investment', 'seed round',
        'capital raise', 'financing'
    ]
    return any(kw in text for kw in funding_keywords)


def extract_deal_from_article(article):
    """Try to extract a deal from a news article."""
    title = article.get("title", "")
    desc = article.get("description", "")
    full_text = f"{title} {desc}"

    company = match_company(full_text)
    if not company:
        return None

    amount = parse_funding_amount(full_text)
    if not amount:
        return None

    round_type = parse_round_type(full_text) or "Funding Round"
    investors = match_investors(full_text)

    # Parse date
    pub_date = article.get("pubDate", "")
    try:
        dt = datetime.strptime(pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
        date_str = dt.strftime("%Y-%m")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m")

    return {
        "company": company,
        "amount": amount,
        "round": round_type,
        "date": date_str,
        "investors": investors,
        "source": article.get("source", ""),
        "headline": title[:120],
    }


def load_existing_deals():
    """Load existing deals from data.js DEAL_TRACKER const."""
    if not DATA_JS_PATH.exists():
        return []

    with open(DATA_JS_PATH, 'r') as f:
        content = f.read()

    # Extract DEAL_TRACKER array
    match = re.search(r'const DEAL_TRACKER = \[([\s\S]*?)\];', content)
    if not match:
        return []

    # Parse the JS array into Python (simplified parser)
    deals = []
    block = match.group(1)
    obj_pattern = re.finditer(r'\{([^}]+)\}', block)

    for obj_match in obj_pattern:
        obj_str = obj_match.group(1)
        deal = {}
        for field in ['company', 'investor', 'amount', 'round', 'date', 'valuation', 'leadOrParticipant']:
            field_match = re.search(rf'{field}:\s*"([^"]*)"', obj_str)
            if field_match:
                deal[field] = field_match.group(1)
        if deal.get('company'):
            deals.append(deal)

    return deals


def deduplicate_deals(existing, new_deals):
    """Merge new deals with existing, avoiding duplicates."""
    # Create a set of existing deal keys
    existing_keys = set()
    for d in existing:
        key = f"{d.get('company', '')}|{d.get('amount', '')}|{d.get('round', '')}|{d.get('date', '')}"
        existing_keys.add(key.lower())

    merged = list(existing)
    added = 0

    for deal in new_deals:
        key = f"{deal['company']}|{deal['amount']}|{deal['round']}|{deal['date']}"
        if key.lower() not in existing_keys:
            # Convert to DEAL_TRACKER format (one entry per investor)
            if deal['investors']:
                for i, investor in enumerate(deal['investors']):
                    entry = {
                        "company": deal["company"],
                        "investor": investor,
                        "amount": deal["amount"],
                        "round": deal["round"],
                        "date": deal["date"],
                        "valuation": "",
                        "leadOrParticipant": "lead" if i == 0 else "participant"
                    }
                    merged.append(entry)
                    added += 1
            else:
                entry = {
                    "company": deal["company"],
                    "investor": "Undisclosed",
                    "amount": deal["amount"],
                    "round": deal["round"],
                    "date": deal["date"],
                    "valuation": "",
                    "leadOrParticipant": "lead"
                }
                merged.append(entry)
                added += 1

            existing_keys.add(key.lower())

    return merged, added


def save_deals_json(deals):
    """Save merged deals to JSON for merge_data.py to consume."""
    output_path = DATA_DIR / "deals_auto.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(deals, f, indent=2)

    print(f"Saved {len(deals)} deals to {output_path}")


def main():
    print("=" * 60)
    print("Deal Flow Fetcher for The Innovators League")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_articles = []

    # 1. Load articles from news_raw.json (already fetched by aggregate_news.js)
    news_raw_path = DATA_DIR / "news_raw.json"
    if news_raw_path.exists():
        with open(news_raw_path) as f:
            news_articles = json.load(f)
        funding_articles = [a for a in news_articles if a.get("type") == "funding"]
        all_articles.extend(funding_articles)
        print(f"Found {len(funding_articles)} funding articles from news_raw.json")
    else:
        print("news_raw.json not found — skipping")

    # 2. Fetch funding-specific RSS feeds
    for feed_name, feed_url in FUNDING_FEEDS:
        print(f"Fetching: {feed_name}...")
        articles = fetch_rss(feed_url, feed_name)
        funding = [a for a in articles if is_funding_article(a.get("title", ""), a.get("description", ""))]
        all_articles.extend(funding)
        print(f"  Found {len(funding)} funding articles out of {len(articles)} total")

    print(f"\nTotal funding articles to process: {len(all_articles)}")

    # 3. Extract deals from articles
    new_deals = []
    for article in all_articles:
        deal = extract_deal_from_article(article)
        if deal:
            new_deals.append(deal)

    print(f"Extracted {len(new_deals)} deals from articles")

    # 4. Load existing deals and merge
    existing = load_existing_deals()
    print(f"Existing deals in DEAL_TRACKER: {len(existing)}")

    merged, added = deduplicate_deals(existing, new_deals)
    print(f"New deals added: {added}")
    print(f"Total deals after merge: {len(merged)}")

    # 5. Sort by date (most recent first)
    merged.sort(key=lambda d: d.get("date", ""), reverse=True)

    # 6. Save
    save_deals_json(merged)

    # Summary
    if new_deals:
        print("\nNew Deals Found:")
        for d in new_deals[:10]:
            investors_str = ", ".join(d["investors"]) if d["investors"] else "Undisclosed"
            print(f"  {d['company']}: {d['amount']} {d['round']} ({d['date']}) — {investors_str}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
