#!/usr/bin/env python3
"""
Weekly Data Updater for The Innovators League
----------------------------------------------
Fetches public company market caps, stock changes, and recent tech news,
then patches data.js with updated values. Also updates MARKET_PULSE
for live Bloomberg-style ticker display.

Environment variables:
  FMP_API_KEY  - Financial Modeling Prep API key (free tier: 250 req/day)
  NEWS_API_KEY - NewsAPI.org key (optional, for movement tracker)

Usage:
  python scripts/update_data.py
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta

import requests
import feedparser

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data.js")

# Public companies in our database and their tickers
PUBLIC_COMPANIES = {
    "Palantir": "PLTR",
    "Rocket Lab": "RKLB",
    "Joby Aviation": "JOBY",
    "Archer Aviation": "ACHR",
    "Planet Labs": "PL",
    "Intuitive Machines": "LUNR",
    "Kratos Defense": "KTOS",
    "NVIDIA": "NVDA",
}

# RSS feeds for tech/defense/frontier news
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/defense-one/all",
    "https://spacenews.com/feed/",
    "https://www.therobotreport.com/feed/",
]

# Keywords to watch for in news
WATCH_KEYWORDS = [
    "anduril", "shield ai", "saronic", "palantir", "spacex",
    "boom supersonic", "helion", "openai", "anthropic",
    "defense tech", "autonomous", "nuclear energy", "fusion",
    "drone", "robotics", "deep tech", "series", "raised",
    "valuation", "ipo", "funding round", "rocket lab",
    "hypersonic", "quantum", "semiconductor", "chips act",
    "ai startup", "defense startup", "climate tech",
]


def read_data_js():
    """Read the current data.js file."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()


def write_data_js(content):
    """Write updated content to data.js."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("data.js updated successfully")


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

            # Find our company name for this ticker
            for company_name, ticker in PUBLIC_COMPANIES.items():
                if ticker == symbol:
                    results[company_name] = {
                        "marketCap": market_cap,
                        "change": change_pct,
                        "ticker": ticker,
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

        # Find the company entry and update its valuation
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

    # Build sector mapping from the data
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
    """Fetch recent news from RSS feeds for movement tracker."""
    items = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").lower()
                summary = entry.get("summary", "").lower()
                combined = title + " " + summary

                # Check if any watch keywords match
                matching = [kw for kw in WATCH_KEYWORDS if kw in combined]
                if matching:
                    items.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "keywords": matching,
                        "source": feed_url,
                    })
        except Exception as e:
            logger.warning(f"Error fetching {feed_url}: {e}")

    logger.info(f"Found {len(items)} relevant news items")
    return items


def update_news_ticker(content, news_items):
    """Update the NEWS_TICKER array with latest news."""
    if not news_items:
        return content

    entries = []
    for item in news_items[:8]:
        title = item["title"].replace('"', '\\"')
        # Calculate time ago
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

        # Determine priority based on keyword count
        priority = "high" if len(item["keywords"]) >= 3 else "medium" if len(item["keywords"]) >= 2 else "low"

        entries.append(
            f'  {{ text: "{title}", time: "{time_str}", priority: "{priority}" }}'
        )

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


def main():
    logger.info("=" * 50)
    logger.info("Innovators League Weekly Data Update")
    logger.info("=" * 50)

    content = read_data_js()

    # 1. Fetch and update public company market caps
    logger.info("\n--- Fetching market caps ---")
    market_caps = fetch_market_caps()
    if market_caps:
        content = update_valuations(content, market_caps)
        content = update_market_pulse(content, market_caps)

    # 2. Fetch news
    logger.info("\n--- Scanning news feeds ---")
    news = fetch_news_items()
    if news:
        content = update_news_ticker(content, news)
        logger.info("\nRelevant stories found (for manual review):")
        for item in news[:10]:
            logger.info(f"  - {item['title']}")
            logger.info(f"    Keywords: {', '.join(item['keywords'])}")

    # 3. Update LAST_UPDATED
    logger.info("\n--- Updating timestamp ---")
    content = update_last_updated(content)

    # 4. Write back
    write_data_js(content)

    logger.info("\n" + "=" * 50)
    logger.info("Update complete!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
