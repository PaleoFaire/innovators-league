#!/usr/bin/env python3
"""
Weekly Data Updater for The Innovators League
----------------------------------------------
Fetches public company market caps and recent tech news,
then patches data.js with updated values.

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

# RSS feeds for tech/defense news
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/defense-one/all",
]

# Keywords to watch for in news
WATCH_KEYWORDS = [
    "anduril", "shield ai", "saronic", "palantir", "spacex",
    "boom supersonic", "helion", "openai", "anthropic",
    "defense tech", "autonomous", "nuclear energy", "fusion",
    "drone", "robotics", "deep tech", "series", "raised",
    "valuation", "ipo", "funding round",
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
            name = item.get("name", "")

            # Find our company name for this ticker
            for company_name, ticker in PUBLIC_COMPANIES.items():
                if ticker == symbol:
                    results[company_name] = market_cap
                    logger.info(f"  {company_name} ({symbol}): ${market_cap:,.0f}")
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
    today = datetime.now().strftime("%Y-%m")

    for company_name, cap in market_caps.items():
        formatted = format_market_cap(cap)
        if not formatted:
            continue

        # Find the company entry and update its valuation
        # Look for: name: "CompanyName" ... valuation: "..."
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

    # 2. Fetch news (logged for reference, manual curation recommended)
    logger.info("\n--- Scanning news feeds ---")
    news = fetch_news_items()
    if news:
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
