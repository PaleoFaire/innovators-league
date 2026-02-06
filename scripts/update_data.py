#!/usr/bin/env python3
"""
Automated Data Pipeline for The Innovators League
---------------------------------------------------
Comprehensive data updater that fetches live market data, news, funding rounds,
and company intelligence from multiple sources. Designed to run on GitHub Actions
(daily for news, weekly for deep updates, monthly for comprehensive).

Data Sources:
  - Financial Modeling Prep API (stock quotes, market caps)
  - USASpending.gov API (government contracts) [FREE]
  - USPTO PatentsView API (patent filings) [FREE]
  - SEC EDGAR API (IPO filings, S-1s, 10-Ks) [FREE]
  - Crunchbase-style RSS/news feeds (funding rounds)
  - TechCrunch, Defense One, SpaceNews, Robot Report RSS

Environment variables:
  FMP_API_KEY       - Financial Modeling Prep API key (free tier: 250 req/day)
  MEDIASTACK_API_KEY - Mediastack news API (free tier: 100 req/mo, optional)
  RAPIDAPI_KEY      - RapidAPI for job search (optional, paid)

Usage:
  python scripts/update_data.py                  # Full update
  python scripts/update_data.py --quick          # News + market pulse only
  python scripts/update_data.py --deep           # Weekly: contracts + patents + SEC
  python scripts/update_data.py --comprehensive  # Monthly: all sources + hiring
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

# ─── SEC CIK NUMBERS FOR PUBLIC COMPANIES ───
SEC_COMPANY_CIKs = {
    "Palantir": "0001321655",
    "Rocket Lab": "0001819994",
    "Joby Aviation": "0001819978",
    "Archer Aviation": "0001818502",
    "Planet Labs": "0001836935",
    "Intuitive Machines": "0001881487",
    "Kratos Defense": "0001069258",
    "IonQ": "0001835535",
    "Rigetti Computing": "0001838359",
    "AST SpaceMobile": "0001780312",
    "Oklo": "0001849056",
    "NuScale Power": "0001822966",
    "Recursion Pharmaceuticals": "0001601280",
    "Tempus AI": "0001881884",
    "FREYR Battery": "0001844224",
}

# ─── PRIORITY COMPANIES FOR CONTRACT SEARCHES ───
# Companies most likely to have government contracts
PRIORITY_COMPANIES = [
    "Anduril Industries", "Shield AI", "Palantir", "SpaceX", "Rocket Lab",
    "Saronic", "Hadrian", "Skydio", "Hermeus", "Kratos Defense",
    "L3Harris", "Northrop Grumman", "Lockheed Martin", "Boeing",
    "Joby Aviation", "Archer Aviation", "AeroVironment", "General Atomics",
    "Leidos", "SAIC", "Booz Allen Hamilton", "Raytheon",
    "Maxar Technologies", "Planet Labs", "Orbital Insight",
    "Rebellion Defense", "Second Front Systems", "Vannevar Labs",
    "Scale AI", "Primer AI", "Gecko Robotics", "Boston Dynamics",
    "Relativity Space", "Firefly Aerospace", "ABL Space Systems",
    "Astro Forge", "Varda Space Industries", "Impulse Space",
    "Helion Energy", "Commonwealth Fusion", "TAE Technologies",
    "Oklo", "NuScale Power", "TerraPower", "X-energy",
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


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNMENT CONTRACT INTELLIGENCE (USASpending.gov API - FREE)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_government_contracts():
    """Fetch recent contracts for tracked companies from USASpending.gov."""
    logger.info("Fetching government contracts from USASpending.gov...")
    contracts = []

    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    # Use priority companies that are most likely to have government contracts
    search_companies = [c for c in PRIORITY_COMPANIES if c in COMPANY_NAMES][:30]

    for company_name in search_companies:
        payload = {
            "filters": {
                "recipient_search_text": [company_name],
                "time_period": [
                    {"start_date": "2023-01-01", "end_date": datetime.now().strftime("%Y-%m-%d")}
                ],
                "award_type_codes": ["A", "B", "C", "D", "IDV_A", "IDV_B", "IDV_C", "IDV_D", "IDV_E"]
            },
            "fields": [
                "Award ID", "Recipient Name", "Award Amount",
                "Awarding Agency", "Award Type", "Start Date", "Description"
            ],
            "limit": 5,
            "order": "desc",
            "sort": "Award Amount"
        }

        try:
            resp = requests.post(base_url, json=payload, timeout=30,
                               headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])

                for award in results:
                    amount = award.get("Award Amount", 0) or 0
                    if amount > 100000:  # Only include contracts > $100K
                        contracts.append({
                            "company": company_name,
                            "agency": award.get("Awarding Agency", "Unknown"),
                            "amount": int(amount),
                            "type": award.get("Award Type", ""),
                            "date": award.get("Start Date", ""),
                            "description": (award.get("Description", "") or "")[:100]
                        })

                if results:
                    logger.info(f"  ✓ {company_name}: {len(results)} contracts found")

        except Exception as e:
            logger.warning(f"  ✗ Error fetching contracts for {company_name}: {e}")

        # Rate limiting - be nice to the API
        import time
        time.sleep(0.5)

    logger.info(f"Total: {len(contracts)} government contracts fetched")
    return contracts


def format_contract_amount(amount):
    """Format contract amount as human-readable string."""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


def update_gov_contracts_live(content, contracts):
    """Update GOV_CONTRACTS_LIVE array in data.js."""
    if not contracts:
        return content

    # Sort by amount descending
    contracts.sort(key=lambda x: x["amount"], reverse=True)

    entries = []
    for c in contracts[:75]:  # Limit to top 75 contracts
        desc = c["description"].replace('"', '\\"').replace("'", "\\'")
        entries.append(
            f'  {{ company: "{c["company"]}", agency: "{c["agency"]}", '
            f'amount: "{format_contract_amount(c["amount"])}", rawAmount: {c["amount"]}, '
            f'type: "{c["type"]}", date: "{c["date"]}", description: "{desc}" }}'
        )

    new_contracts = "const GOV_CONTRACTS_LIVE = [\n" + ",\n".join(entries) + "\n];"

    # Check if GOV_CONTRACTS_LIVE exists, if not add it after GOV_CONTRACTS
    if "const GOV_CONTRACTS_LIVE = [" in content:
        content = re.sub(
            r'const GOV_CONTRACTS_LIVE = \[.*?\];',
            new_contracts,
            content,
            flags=re.DOTALL
        )
    else:
        # Add after GOV_CONTRACTS
        content = re.sub(
            r'(const GOV_CONTRACTS = \[.*?\];)',
            r'\1\n\n// Auto-updated government contracts from USASpending.gov\n' + new_contracts,
            content,
            flags=re.DOTALL
        )

    logger.info(f"Updated GOV_CONTRACTS_LIVE with {len(entries)} contracts")
    return content


# ═══════════════════════════════════════════════════════════════════════════════
# PATENT INTELLIGENCE (USPTO PatentsView API - FREE)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_patent_data():
    """Fetch patent counts and recent filings for tracked companies."""
    logger.info("Fetching patent data from USPTO PatentsView API...")
    patent_data = {}

    base_url = "https://api.patentsview.org/patents/query"

    search_companies = [c for c in PRIORITY_COMPANIES if c in COMPANY_NAMES][:25]

    for company_name in search_companies:
        # Try exact match first, then fuzzy
        query = {
            "q": {"_contains": {"assignee_organization": company_name}},
            "f": ["patent_number", "patent_date", "patent_title", "patent_abstract"],
            "o": {"per_page": 50},
            "s": [{"patent_date": "desc"}]
        }

        try:
            resp = requests.post(base_url, json=query, timeout=30,
                               headers={"Content-Type": "application/json"})

            if resp.status_code == 200:
                data = resp.json()
                patents = data.get("patents", []) or []

                if patents:
                    # Calculate velocity (patents in last 12 months)
                    cutoff_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                    recent = [p for p in patents if (p.get("patent_date") or "") >= cutoff_date]

                    total = data.get("total_patent_count", len(patents))

                    patent_data[company_name] = {
                        "total": total,
                        "recent": len(recent),
                        "velocity": "up" if len(recent) > 3 else "stable" if len(recent) > 0 else "low",
                        "latestPatent": (patents[0].get("patent_title", "") or "")[:80] if patents else "",
                        "latestDate": patents[0].get("patent_date", "") if patents else ""
                    }
                    logger.info(f"  ✓ {company_name}: {total} patents ({len(recent)} recent)")

        except Exception as e:
            logger.warning(f"  ✗ Error fetching patents for {company_name}: {e}")

        import time
        time.sleep(0.3)

    logger.info(f"Total: {len(patent_data)} companies with patent data")
    return patent_data


def update_patent_intel_live(content, patent_data):
    """Update PATENT_INTEL_LIVE object in data.js."""
    if not patent_data:
        return content

    entries = []
    for company, data in patent_data.items():
        key = company.lower().replace(" ", "-").replace(".", "")
        latest = data["latestPatent"].replace('"', '\\"').replace("'", "\\'")
        entries.append(
            f'  "{key}": {{ total: {data["total"]}, recent: {data["recent"]}, '
            f'velocity: "{data["velocity"]}", latestPatent: "{latest}", '
            f'latestDate: "{data["latestDate"]}" }}'
        )

    new_patent_intel = "const PATENT_INTEL_LIVE = {\n" + ",\n".join(entries) + "\n};"

    # Check if PATENT_INTEL_LIVE exists
    if "const PATENT_INTEL_LIVE = {" in content:
        content = re.sub(
            r'const PATENT_INTEL_LIVE = \{.*?\};',
            new_patent_intel,
            content,
            flags=re.DOTALL
        )
    else:
        # Add after PATENT_INTEL
        content = re.sub(
            r'(const PATENT_INTEL = \{.*?\};)',
            r'\1\n\n// Auto-updated patent data from USPTO PatentsView\n' + new_patent_intel,
            content,
            flags=re.DOTALL
        )

    logger.info(f"Updated PATENT_INTEL_LIVE with {len(entries)} companies")
    return content


# ═══════════════════════════════════════════════════════════════════════════════
# SEC EDGAR FILINGS (SEC API - FREE)
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_sec_filings():
    """Fetch recent SEC filings for IPO/SPAC detection."""
    logger.info("Fetching SEC filings from EDGAR API...")
    filings = []

    for company_name, cik in SEC_COMPANY_CIKs.items():
        url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
        headers = {"User-Agent": "InnovatorsLeague research@innovatorsleague.com"}

        try:
            resp = requests.get(url, headers=headers, timeout=30)

            if resp.status_code == 200:
                data = resp.json()

                recent = data.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])[:15]
                dates = recent.get("filingDate", [])[:15]
                descriptions = recent.get("primaryDocDescription", [])[:15]

                company_filings = []
                for i, (form, date) in enumerate(zip(forms, dates)):
                    if form in ["S-1", "S-1/A", "424B1", "424B2", "424B3", "424B4",
                               "10-K", "10-Q", "8-K", "DEF 14A", "DEFA14A"]:
                        desc = descriptions[i] if i < len(descriptions) else ""
                        company_filings.append({
                            "company": company_name,
                            "form": form,
                            "date": date,
                            "description": desc[:100] if desc else "",
                            "isIPO": form in ["S-1", "S-1/A", "424B1", "424B2", "424B3", "424B4"],
                            "ticker": PUBLIC_COMPANIES.get(company_name, "")
                        })

                filings.extend(company_filings)
                if company_filings:
                    logger.info(f"  ✓ {company_name}: {len(company_filings)} filings")

        except Exception as e:
            logger.warning(f"  ✗ Error fetching SEC filings for {company_name}: {e}")

        import time
        time.sleep(0.2)

    # Sort by date descending
    filings.sort(key=lambda x: x["date"], reverse=True)

    logger.info(f"Total: {len(filings)} SEC filings fetched")
    return filings


def update_sec_filings_live(content, filings):
    """Update SEC_FILINGS_LIVE array in data.js."""
    if not filings:
        return content

    entries = []
    for f in filings[:50]:  # Limit to 50 most recent
        desc = f["description"].replace('"', '\\"').replace("'", "\\'")
        entries.append(
            f'  {{ company: "{f["company"]}", form: "{f["form"]}", '
            f'date: "{f["date"]}", description: "{desc}", '
            f'isIPO: {"true" if f["isIPO"] else "false"}, ticker: "{f["ticker"]}" }}'
        )

    new_filings = "const SEC_FILINGS_LIVE = [\n" + ",\n".join(entries) + "\n];"

    # Check if SEC_FILINGS_LIVE exists
    if "const SEC_FILINGS_LIVE = [" in content:
        content = re.sub(
            r'const SEC_FILINGS_LIVE = \[.*?\];',
            new_filings,
            content,
            flags=re.DOTALL
        )
    else:
        # Add before LAST_UPDATED
        content = re.sub(
            r'(const LAST_UPDATED = )',
            '// Auto-updated SEC filings from EDGAR\n' + new_filings + '\n\n\\1',
            content
        )

    logger.info(f"Updated SEC_FILINGS_LIVE with {len(entries)} filings")
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


def generate_update_report(market_caps, news_items, funding_rounds,
                          contracts=None, patents=None, sec_filings=None):
    """Generate a summary report of what was updated."""
    report = []
    report.append("\n" + "=" * 60)
    report.append("  INNOVATORS LEAGUE - UPDATE REPORT")
    report.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    if market_caps:
        report.append(f"\n📈 MARKET DATA: {len(market_caps)} stocks updated")
        for name, data in sorted(market_caps.items(), key=lambda x: x[1]["marketCap"], reverse=True)[:5]:
            change = data["change"]
            arrow = "▲" if change >= 0 else "▼"
            report.append(f"   {arrow} {name} ({data['ticker']}): {format_market_cap(data['marketCap'])} ({change:+.1f}%)")

    if news_items:
        report.append(f"\n📰 NEWS: {len(news_items)} relevant items found")
        for item in news_items[:5]:
            report.append(f"   • {item['title'][:70]}...")

    if funding_rounds:
        report.append(f"\n💰 FUNDING: {len(funding_rounds)} rounds detected")
        for r in funding_rounds:
            report.append(f"   • {r['company']}: {r['amount']}")

    if contracts:
        report.append(f"\n🏛️ GOVERNMENT CONTRACTS: {len(contracts)} contracts updated")
        top_contracts = sorted(contracts, key=lambda x: x["amount"], reverse=True)[:5]
        for c in top_contracts:
            report.append(f"   • {c['company']}: {format_contract_amount(c['amount'])} ({c['agency']})")

    if patents:
        report.append(f"\n📜 PATENTS: {len(patents)} companies with patent data")
        for company, data in list(patents.items())[:5]:
            report.append(f"   • {company}: {data['total']} patents ({data['recent']} recent)")

    if sec_filings:
        report.append(f"\n📋 SEC FILINGS: {len(sec_filings)} filings tracked")
        for f in sec_filings[:5]:
            report.append(f"   • {f['company']}: {f['form']} ({f['date']})")

    report.append("\n" + "=" * 60)
    return "\n".join(report)


def main():
    quick_mode = "--quick" in sys.argv
    deep_mode = "--deep" in sys.argv
    comprehensive_mode = "--comprehensive" in sys.argv

    logger.info("=" * 60)
    logger.info("  Innovators League Automated Data Pipeline")
    if comprehensive_mode:
        mode = "COMPREHENSIVE"
    elif deep_mode:
        mode = "DEEP"
    elif quick_mode:
        mode = "QUICK"
    else:
        mode = "STANDARD"
    logger.info(f"  Mode: {mode}")
    logger.info("=" * 60)

    content = read_data_js()

    # Load company names for matching
    extract_company_names(content)

    # Initialize tracking variables
    contracts = None
    patents = None
    sec_filings = None

    # ─── Phase 1: Market Data (All modes) ───
    logger.info("\n--- Phase 1: Market Data ---")
    market_caps = fetch_market_caps()
    if market_caps:
        content = update_valuations(content, market_caps)
        content = update_market_pulse(content, market_caps)

    # ─── Phase 2: News & Intelligence (All modes) ───
    logger.info("\n--- Phase 2: News & Intelligence ---")
    news = fetch_news_items()
    if news:
        content = update_news_ticker(content, news)

        # Detect funding rounds from news
        logger.info("\n--- Phase 3: Funding Detection ---")
        funding_rounds = detect_funding_rounds(news)
        content = update_funding_tracker(content, funding_rounds)

        # Log relevant stories (not in quick mode)
        if not quick_mode:
            logger.info("\nTop stories for manual review:")
            for item in news[:5]:
                logger.info(f"  [{item['category'].upper()}] {item['title']}")
    else:
        funding_rounds = []

    # ─── Phase 4: Government Contracts (Deep & Comprehensive) ───
    if deep_mode or comprehensive_mode:
        logger.info("\n--- Phase 4: Government Contracts (USASpending.gov) ---")
        contracts = fetch_government_contracts()
        if contracts:
            content = update_gov_contracts_live(content, contracts)

    # ─── Phase 5: Patent Intelligence (Deep & Comprehensive) ───
    if deep_mode or comprehensive_mode:
        logger.info("\n--- Phase 5: Patent Intelligence (USPTO PatentsView) ---")
        patents = fetch_patent_data()
        if patents:
            content = update_patent_intel_live(content, patents)

    # ─── Phase 6: SEC Filings (Deep & Comprehensive) ───
    if deep_mode or comprehensive_mode:
        logger.info("\n--- Phase 6: SEC Filings (EDGAR) ---")
        sec_filings = fetch_sec_filings()
        if sec_filings:
            content = update_sec_filings_live(content, sec_filings)

    # ─── Phase 7: Update Timestamp ───
    logger.info("\n--- Phase 7: Timestamp ---")
    content = update_last_updated(content)

    # ─── Phase 8: Write Back ───
    write_data_js(content)

    # ─── Phase 9: Generate Report ───
    report = generate_update_report(
        market_caps, news, funding_rounds,
        contracts=contracts, patents=patents, sec_filings=sec_filings
    )
    logger.info(report)

    # Save report to file for GitHub Actions artifacts
    report_file = os.path.join(os.path.dirname(__file__), "..", "update_report.txt")
    with open(report_file, "w") as f:
        f.write(report)

    logger.info("\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
