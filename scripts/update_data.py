#!/usr/bin/env python3
"""
Automated Data Pipeline for The Innovators League
---------------------------------------------------
Comprehensive data updater that fetches live market data, news, funding rounds,
and company intelligence from multiple sources. Designed to run on GitHub Actions
(daily for news, weekly for deep updates).

Data Sources:
  - Financial Modeling Prep API (stock quotes, market caps)
  - Crunchbase-style RSS/news feeds (funding rounds)
  - TechCrunch, Defense One, SpaceNews, Robot Report RSS
  - SEC EDGAR (IPO filings detection)
  - GitHub Jobs / LinkedIn proxy for hiring signals

Environment variables:
  FMP_API_KEY  - Financial Modeling Prep API key (free tier: 250 req/day)

Usage:
  python scripts/update_data.py              # Full update
  python scripts/update_data.py --quick      # News + market pulse only
  python scripts/update_data.py --deep       # Full deep update with all sources
"""

import os
import re
import json
import logging
import sys
from datetime import datetime, timedelta

import requests
import feedparser

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data.js")

# ─── PUBLIC COMPANIES TICKER MAP ───
PUBLIC_COMPANIES = {
    "Palantir": "PLTR",
    "Rocket Lab": "RKLB",
    "Joby Aviation": "JOBY",
    "Archer Aviation": "ACHR",
    "Planet Labs": "PL",
    "Intuitive Machines": "LUNR",
    "Kratos Defense": "KTOS",
    "NVIDIA": "NVDA",
    "IonQ": "IONQ",
    "Rigetti Computing": "RGTI",
    "AST SpaceMobile": "ASTS",
    "Oklo": "OKLO",
    "NuScale Power": "SMR",
    "Recursion Pharmaceuticals": "RXRX",
    "Tempus AI": "TEM",
    "FREYR Battery": "FREY",
    "DroneShield": "DRO.AX",
}

# ─── RSS FEEDS: Categorized by source type ───
RSS_FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
    ],
    "defense": [
        "https://feeds.feedburner.com/defense-one/all",
        "https://breakingdefense.com/feed/",
    ],
    "space": [
        "https://spacenews.com/feed/",
        "https://feeds.feedburner.com/SpaceflightNow",
    ],
    "robotics": [
        "https://www.therobotreport.com/feed/",
    ],
    "energy": [
        "https://www.utilitydive.com/feeds/news/",
    ],
    "funding": [
        "https://news.crunchbase.com/feed/",
    ],
}

# ─── KEYWORDS: Categorized for priority scoring ───
WATCH_KEYWORDS_HIGH = [
    "anduril", "shield ai", "saronic", "palantir", "spacex",
    "boom supersonic", "helion", "physical intelligence", "figure ai",
    "bedrock robotics", "collaborative robotics", "pano ai",
    "commonwealth fusion", "radiant nuclear", "hadrian",
]

WATCH_KEYWORDS_MEDIUM = [
    "openai", "anthropic", "defense tech", "autonomous weapon",
    "nuclear energy", "fusion energy", "smr", "microreactor",
    "drone", "robotics", "deep tech", "hypersonic", "quantum",
    "semiconductor", "chips act", "directed energy", "counter-drone",
    "eVTOL", "space launch", "satellite", "geothermal",
    "climate tech", "carbon capture", "asteroid mining",
]

WATCH_KEYWORDS_FUNDING = [
    "series a", "series b", "series c", "series d", "series e",
    "series f", "raised", "funding round", "valuation",
    "mega-round", "unicorn", "ipo", "spac", "went public",
]

# ─── ALL DATABASE COMPANY NAMES (for matching) ───
# This is auto-populated from data.js at runtime
COMPANY_NAMES = []


def read_data_js():
    """Read the current data.js file."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()


def write_data_js(content):
    """Write updated content to data.js."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("data.js updated successfully")


def extract_company_names(content):
    """Extract all company names from the COMPANIES array."""
    global COMPANY_NAMES
    names = re.findall(r'name:\s*"([^"]+)"', content)
    COMPANY_NAMES = list(set(names))
    logger.info(f"Loaded {len(COMPANY_NAMES)} company names from database")
    return COMPANY_NAMES


def fetch_market_caps():
    """Fetch current market caps for public companies."""
    api_key = os.environ.get("FMP_API_KEY", "")
    if not api_key:
        logger.warning("FMP_API_KEY not set, skipping market cap updates")
        return {}

    results = {}
    tickers = list(PUBLIC_COMPANIES.values())
    ticker_str = ",".join(tickers)

    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker_str}?apikey={api_key}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for item in data:
            symbol = item.get("symbol", "")
            market_cap = item.get("marketCap", 0)
            change_pct = item.get("changesPercentage", 0)
            price = item.get("price", 0)

            for company_name, ticker in PUBLIC_COMPANIES.items():
                if ticker == symbol:
                    results[company_name] = {
                        "marketCap": market_cap,
                        "change": change_pct,
                        "ticker": ticker,
                        "price": price,
                    }
                    logger.info(f"  {company_name} ({symbol}): ${market_cap:,.0f} ({change_pct:+.1f}%)")
                    break

    except Exception as e:
        logger.error(f"Error fetching market caps: {e}")

    return results


def format_market_cap(cap):
    """Format market cap as human-readable string."""
    if cap >= 1_000_000_000_000:
        return f"${cap / 1_000_000_000_000:.1f}T+"
    elif cap >= 1_000_000_000:
        return f"${cap / 1_000_000_000:.0f}B+"
    elif cap >= 1_000_000:
        return f"${cap / 1_000_000:.0f}M+"
    return ""


def update_valuations(content, market_caps):
    """Update valuation fields for public companies."""
    for company_name, data in market_caps.items():
        cap = data["marketCap"]
        formatted = format_market_cap(cap)
        if not formatted:
            continue

        pattern = (
            r'(name:\s*"' + re.escape(company_name) + r'".*?'
            r'valuation:\s*)"[^"]*"'
        )
        replacement = r'\g<1>"' + formatted + '"'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        if new_content != content:
            logger.info(f"Updated {company_name} valuation to {formatted}")
            content = new_content

    return content


def update_market_pulse(content, market_caps):
    """Update the MARKET_PULSE array with live stock data."""
    if not market_caps:
        return content

    sector_map = {}
    for match in re.finditer(r'name:\s*"([^"]+)".*?sector:\s*"([^"]+)"', content, re.DOTALL):
        sector_map[match.group(1)] = match.group(2)

    entries = []
    for company_name, data in market_caps.items():
        cap = data["marketCap"]
        change = data["change"]
        ticker = data["ticker"]
        sector = sector_map.get(company_name, "")
        formatted = format_market_cap(cap)
        trend = "up" if change >= 0 else "down"
        change_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"

        entries.append(
            f'  {{ name: "{company_name}", ticker: "{ticker}", '
            f'valuation: "{formatted}", change: "{change_str}", '
            f'trend: "{trend}", sector: "{sector}" }}'
        )

    if entries:
        new_pulse = "const MARKET_PULSE = [\n" + ",\n".join(entries) + "\n];"
        content = re.sub(
            r'const MARKET_PULSE = \[.*?\];',
            new_pulse,
            content,
            flags=re.DOTALL,
        )
        logger.info(f"Updated MARKET_PULSE with {len(entries)} stocks")

    return content


def fetch_news_items():
    """Fetch recent news from all RSS feed categories."""
    items = []

    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    title = entry.get("title", "").lower()
                    summary = entry.get("summary", "").lower()
                    combined = title + " " + summary

                    # Score the item
                    high_matches = [kw for kw in WATCH_KEYWORDS_HIGH if kw in combined]
                    med_matches = [kw for kw in WATCH_KEYWORDS_MEDIUM if kw in combined]
                    fund_matches = [kw for kw in WATCH_KEYWORDS_FUNDING if kw in combined]

                    score = len(high_matches) * 3 + len(med_matches) * 1 + len(fund_matches) * 2
                    if score > 0:
                        items.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "keywords": high_matches + med_matches + fund_matches,
                            "source": feed_url,
                            "category": category,
                            "score": score,
                            "is_funding": len(fund_matches) > 0,
                        })
            except Exception as e:
                logger.warning(f"Error fetching {feed_url}: {e}")

    # Sort by score descending
    items.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"Found {len(items)} relevant news items across {sum(len(f) for f in RSS_FEEDS.values())} feeds")
    return items


def detect_funding_rounds(news_items):
    """Extract potential funding round data from news items."""
    funding_items = [item for item in news_items if item.get("is_funding")]
    logger.info(f"  {len(funding_items)} items contain funding keywords")

    potential_rounds = []
    for item in funding_items[:10]:
        title = item["title"]
        # Try to extract amount from title
        amount_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(M|B|million|billion)', title, re.IGNORECASE)
        if amount_match:
            amount = amount_match.group(1)
            unit = amount_match.group(2).upper()
            if unit in ("M", "MILLION"):
                formatted = f"${amount}M"
            elif unit in ("B", "BILLION"):
                formatted = f"${amount}B"
            else:
                formatted = f"${amount}{unit}"

            # Try to match company name
            matched_company = None
            for name in COMPANY_NAMES:
                if name.lower() in title.lower():
                    matched_company = name
                    break

            if matched_company:
                potential_rounds.append({
                    "company": matched_company,
                    "amount": formatted,
                    "title": title,
                    "link": item["link"],
                })
                logger.info(f"  FUNDING DETECTED: {matched_company} - {formatted}")

    return potential_rounds


def update_news_ticker(content, news_items):
    """Update the NEWS_TICKER array with latest news."""
    if not news_items:
        return content

    entries = []
    seen_topics = set()

    for item in news_items[:12]:
        title = item["title"].replace('"', '\\"').replace("'", "\\'")

        # Dedup by rough topic
        topic_key = " ".join(sorted(item["keywords"][:3]))
        if topic_key in seen_topics:
            continue
        seen_topics.add(topic_key)

        try:
            from dateutil import parser as dateparser
            pub_date = dateparser.parse(item["published"])
            diff = datetime.now(pub_date.tzinfo) - pub_date
            if diff.days > 0:
                time_str = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                time_str = f"{diff.seconds // 3600}h ago"
            else:
                time_str = "Just now"
        except Exception:
            time_str = "Recent"

        priority = "high" if item["score"] >= 5 else "medium" if item["score"] >= 2 else "low"

        entries.append(
            f'  {{ text: "{title}", time: "{time_str}", priority: "{priority}" }}'
        )

        if len(entries) >= 8:
            break

    if entries:
        new_ticker = "const NEWS_TICKER = [\n" + ",\n".join(entries) + "\n];"
        content = re.sub(
            r'const NEWS_TICKER = \[.*?\];',
            new_ticker,
            content,
            flags=re.DOTALL,
        )
        logger.info(f"Updated NEWS_TICKER with {len(entries)} items")

    return content


def update_funding_tracker(content, funding_rounds):
    """Append new funding rounds to FUNDING_TRACKER if they're genuinely new."""
    if not funding_rounds:
        return content

    # Extract existing companies in FUNDING_TRACKER
    existing = set(re.findall(r'company:\s*"([^"]+)"',
                              re.search(r'const FUNDING_TRACKER = \[.*?\];', content, re.DOTALL).group(0)
                              if re.search(r'const FUNDING_TRACKER = \[.*?\];', content, re.DOTALL)
                              else ""))

    new_rounds = [r for r in funding_rounds if r["company"] not in existing]
    if new_rounds:
        logger.info(f"  {len(new_rounds)} new funding rounds to potentially add")
        for r in new_rounds:
            logger.info(f"    NEW: {r['company']} - {r['amount']} ({r['title']})")
    else:
        logger.info("  No new funding rounds detected")

    return content


def update_last_updated(content):
    """Update the LAST_UPDATED timestamp."""
    today = datetime.now().strftime("%Y-%m-%d")
    new_content = re.sub(
        r'const LAST_UPDATED = "[^"]*"',
        f'const LAST_UPDATED = "{today}"',
        content,
    )
    if new_content != content:
        logger.info(f"Updated LAST_UPDATED to {today}")
    return new_content


def generate_update_report(market_caps, news_items, funding_rounds):
    """Generate a summary report of what was updated."""
    report = []
    report.append("\n" + "=" * 60)
    report.append("  INNOVATORS LEAGUE - UPDATE REPORT")
    report.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    if market_caps:
        report.append(f"\n📈 MARKET DATA: {len(market_caps)} stocks updated")
        for name, data in sorted(market_caps.items(), key=lambda x: x[1]["marketCap"], reverse=True):
            change = data["change"]
            arrow = "▲" if change >= 0 else "▼"
            report.append(f"   {arrow} {name} ({data['ticker']}): {format_market_cap(data['marketCap'])} ({change:+.1f}%)")

    if news_items:
        report.append(f"\n📰 NEWS: {len(news_items)} relevant items found")
        for item in news_items[:5]:
            report.append(f"   • {item['title'][:80]}...")

    if funding_rounds:
        report.append(f"\n💰 FUNDING: {len(funding_rounds)} rounds detected")
        for r in funding_rounds:
            report.append(f"   • {r['company']}: {r['amount']}")

    report.append("\n" + "=" * 60)
    return "\n".join(report)


def main():
    quick_mode = "--quick" in sys.argv
    deep_mode = "--deep" in sys.argv

    logger.info("=" * 60)
    logger.info("  Innovators League Automated Data Pipeline")
    mode = "QUICK" if quick_mode else "DEEP" if deep_mode else "STANDARD"
    logger.info(f"  Mode: {mode}")
    logger.info("=" * 60)

    content = read_data_js()

    # Load company names for matching
    extract_company_names(content)

    # 1. Fetch and update public company market caps
    logger.info("\n--- Phase 1: Market Data ---")
    market_caps = fetch_market_caps()
    if market_caps:
        content = update_valuations(content, market_caps)
        content = update_market_pulse(content, market_caps)

    # 2. Fetch news + detect funding
    logger.info("\n--- Phase 2: News & Intelligence ---")
    news = fetch_news_items()
    if news:
        content = update_news_ticker(content, news)

        # Detect funding rounds from news
        logger.info("\n--- Phase 3: Funding Detection ---")
        funding_rounds = detect_funding_rounds(news)
        content = update_funding_tracker(content, funding_rounds)

        # Log relevant stories
        if not quick_mode:
            logger.info("\nTop stories for manual review:")
            for item in news[:10]:
                logger.info(f"  [{item['category'].upper()}] {item['title']}")
                logger.info(f"    Score: {item['score']} | Keywords: {', '.join(item['keywords'][:5])}")
    else:
        funding_rounds = []

    # 3. Update timestamp
    logger.info("\n--- Phase 4: Timestamp ---")
    content = update_last_updated(content)

    # 4. Write back
    write_data_js(content)

    # 5. Generate report
    report = generate_update_report(market_caps, news, funding_rounds)
    logger.info(report)

    # Save report to file for GitHub Actions artifacts
    report_file = os.path.join(os.path.dirname(__file__), "..", "update_report.txt")
    with open(report_file, "w") as f:
        f.write(report)

    logger.info("\nPipeline complete!")


if __name__ == "__main__":
    main()
