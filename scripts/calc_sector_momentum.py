#!/usr/bin/env python3
"""
Sector Momentum Calculator for The Innovators League

Automatically calculates sector momentum scores from available data:
  - Funding velocity (from deals_auto.json or DEAL_TRACKER in data.js)
  - News signal frequency (from news_raw.json)
  - Job posting volume (from jobs_auto.js)
  - Stock performance (from stocks_auto.js)

Methodology (weighted composite):
  - Funding velocity (35%): $ raised in trailing 90 days vs baseline
  - News signal frequency (25%): Articles mentioning sector in last 7 days
  - Hiring velocity (20%): Job postings per sector
  - Market sentiment (20%): Average stock price change for public companies

Output: data/sector_momentum_auto.json
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

# Sector definitions — which companies map to which sectors
# Aligned with SECTORS const in app.js
SECTOR_CONFIG = {
    "Defense & Security": {
        "companies": ["Anduril Industries", "Shield AI", "Saronic", "Epirus", "Castelion",
                       "Vannevar Labs", "Palantir", "Mach Industries", "Neros", "Mara",
                       "Theseus", "Blue Water Autonomy", "Skydio"],
        "tickers": ["PLTR"],
        "keywords": ["defense", "military", "pentagon", "dod", "army", "navy", "air force",
                     "drones", "autonomous weapons", "national security"],
        "baseline_funding_90d": 2000,  # $M baseline for normalization
    },
    "AI & Software": {
        "companies": ["Anthropic", "OpenAI", "Cerebras", "Scale AI", "Groq", "Etched",
                       "Physical Intelligence", "Cognition", "Substrate", "Lightmatter"],
        "tickers": ["AI"],
        "keywords": ["artificial intelligence", "machine learning", "llm", "large language model",
                     "ai infrastructure", "gpu", "neural", "deep learning"],
        "baseline_funding_90d": 5000,
    },
    "Robotics & Manufacturing": {
        "companies": ["Figure AI", "Collaborative Robotics", "Agility Robotics",
                       "Machina Labs", "Hadrian", "Bedrock Robotics", "Waymo"],
        "tickers": [],
        "keywords": ["robot", "robotics", "humanoid", "manufacturing", "automation",
                     "factory", "industrial"],
        "baseline_funding_90d": 1000,
    },
    "Nuclear Energy": {
        "companies": ["Commonwealth Fusion Systems", "Helion", "Oklo", "Radiant",
                       "TerraPower", "X-Energy", "TAE Technologies", "Kairos Power",
                       "Pacific Fusion", "Xcimer Energy", "Zap Energy", "Deep Fission",
                       "Last Energy", "Lab 91"],
        "tickers": ["OKLO", "SMR", "LEU"],
        "keywords": ["nuclear", "fusion", "fission", "reactor", "uranium", "microreactor"],
        "baseline_funding_90d": 500,
    },
    "Space & Aerospace": {
        "companies": ["SpaceX", "Rocket Lab", "Planet Labs", "Astranis", "Impulse Space",
                       "Varda Space Industries", "Intuitive Machines", "Firefly Aerospace",
                       "Relativity Space", "Venus Aerospace", "Northwood Space",
                       "Observable Space", "AstroForge", "Starpath Robotics",
                       "Array Labs", "Reflect Orbital", "AST SpaceMobile"],
        "tickers": ["RKLB", "PL", "LUNR", "ASTS"],
        "keywords": ["space", "rocket", "satellite", "launch", "orbit", "lunar", "mars",
                     "constellation", "aerospace"],
        "baseline_funding_90d": 1500,
    },
    "Chips & Semiconductors": {
        "companies": ["NVIDIA", "AMD", "Astera Labs"],
        "tickers": ["NVDA", "AMD", "ALAB"],
        "keywords": ["chip", "semiconductor", "silicon", "gpu", "processor", "fab"],
        "baseline_funding_90d": 500,
    },
    "Drones & Autonomous": {
        "companies": ["Skydio", "Zipline", "Shield AI", "Airship Industries"],
        "tickers": [],
        "keywords": ["drone", "uav", "autonomous", "unmanned", "evtol"],
        "baseline_funding_90d": 500,
    },
    "Climate & Energy": {
        "companies": ["Fervo Energy", "Terraform Industries", "Captura", "Heirloom Carbon",
                       "Antora Energy", "KoBold Metals", "Charm Industrial", "Solugen",
                       "Mazama", "Quaise Energy", "Claros", "Rainmaker"],
        "tickers": ["QS", "FREY"],
        "keywords": ["climate", "clean energy", "carbon", "renewable", "geothermal",
                     "solar", "wind", "battery", "hydrogen", "decarbonization"],
        "baseline_funding_90d": 800,
    },
    "Biotech & Health": {
        "companies": ["Recursion Pharmaceuticals", "Mammoth Biosciences", "Altos Labs",
                       "Colossal Biosciences", "Neuralink", "Tempus AI", "Orchid"],
        "tickers": ["RXRX", "TEM"],
        "keywords": ["biotech", "pharma", "drug", "gene", "crispr", "longevity",
                     "health", "medical", "clinical trial"],
        "baseline_funding_90d": 2000,
    },
    "Supersonic & Hypersonic": {
        "companies": ["Boom Supersonic", "Venus Aerospace", "Karman Industries",
                       "Hermeus"],
        "tickers": [],
        "keywords": ["supersonic", "hypersonic", "mach", "concorde"],
        "baseline_funding_90d": 200,
    },
    "Quantum Computing": {
        "companies": ["IonQ", "Rigetti Computing", "D-Wave Quantum", "PsiQuantum"],
        "tickers": ["IONQ", "RGTI", "QBTS"],
        "keywords": ["quantum", "qubit", "quantum computing", "quantum network"],
        "baseline_funding_90d": 300,
    },
    "Housing & Construction": {
        "companies": ["Cover", "Cuby Technologies"],
        "tickers": [],
        "keywords": ["housing", "construction", "prefab", "modular home", "3d printing house"],
        "baseline_funding_90d": 200,
    },
    "Transportation": {
        "companies": ["Joby Aviation", "Archer Aviation", "Rivian", "The Boring Company"],
        "tickers": ["JOBY", "ACHR", "RIVN"],
        "keywords": ["evtol", "electric vehicle", "autonomous driving", "tunneling",
                     "air taxi", "urban mobility"],
        "baseline_funding_90d": 500,
    },
    "Ocean & Maritime": {
        "companies": ["Saildrone", "Saronic"],
        "tickers": [],
        "keywords": ["ocean", "maritime", "autonomous vessel", "deep sea", "naval"],
        "baseline_funding_90d": 100,
    },
    "Consumer Tech": {
        "companies": [],
        "tickers": [],
        "keywords": ["consumer", "app", "personalization", "social"],
        "baseline_funding_90d": 300,
    },
    "Infrastructure & Logistics": {
        "companies": ["Flexport", "DIRAC"],
        "tickers": [],
        "keywords": ["infrastructure", "logistics", "grid", "smart grid", "energy storage",
                     "supply chain"],
        "baseline_funding_90d": 400,
    },
}


def load_deals():
    """Load deals from deals_auto.json or parse from data.js."""
    deals_path = DATA_DIR / "deals_auto.json"
    if deals_path.exists():
        with open(deals_path) as f:
            return json.load(f)

    # Fallback: parse DEAL_TRACKER from data.js
    if DATA_JS_PATH.exists():
        with open(DATA_JS_PATH) as f:
            content = f.read()
        match = re.search(r'const DEAL_TRACKER = \[([\s\S]*?)\];', content)
        if match:
            deals = []
            for obj in re.finditer(r'\{([^}]+)\}', match.group(1)):
                deal = {}
                for field in ['company', 'amount', 'round', 'date']:
                    fm = re.search(rf'{field}:\s*"([^"]*)"', obj.group(1))
                    if fm:
                        deal[field] = fm.group(1)
                if deal.get('company'):
                    deals.append(deal)
            return deals
    return []


def load_news():
    """Load recent news articles from news_raw.json."""
    news_path = DATA_DIR / "news_raw.json"
    if news_path.exists():
        with open(news_path) as f:
            return json.load(f)
    return []


def load_jobs():
    """Load job data from jobs_auto.js."""
    jobs_path = DATA_DIR / "jobs_auto.js"
    if not jobs_path.exists():
        return []

    with open(jobs_path) as f:
        content = f.read()

    # Extract JOBS_DATA array
    match = re.search(r'const JOBS_DATA = (\[[\s\S]*?\]);', content)
    if not match:
        return []

    try:
        # This is JS, not JSON — do basic extraction
        jobs = []
        for obj in re.finditer(r'company:\s*"([^"]*)"', content):
            jobs.append({"company": obj.group(1)})
        return jobs
    except Exception:
        return []


def load_stocks():
    """Load stock data from stocks_auto.js."""
    stocks_path = DATA_DIR / "stocks_auto.js"
    if not stocks_path.exists():
        return {}

    with open(stocks_path) as f:
        content = f.read()

    # Extract STOCK_PRICES JSON object
    match = re.search(r'const STOCK_PRICES = (\{[\s\S]*?\});', content)
    if not match:
        return {}

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def parse_amount_millions(amount_str):
    """Convert '$600M' or '$2.5B' to millions."""
    if not amount_str:
        return 0
    amount_str = amount_str.replace('+', '').replace('~', '').strip()
    match = re.match(r'\$(\d+(?:\.\d+)?)\s*([BbMm])', amount_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2).upper()
        if unit == 'B':
            return num * 1000
        return num
    return 0


def calculate_funding_score(sector_name, config, deals):
    """Calculate funding velocity score (0-100) for a sector."""
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m")
    sector_companies = set(c.lower() for c in config["companies"])

    total_funding = 0
    deal_count = 0

    for deal in deals:
        company = deal.get("company", "").lower()
        date = deal.get("date", "")

        if date >= cutoff and company in sector_companies:
            amount = parse_amount_millions(deal.get("amount", ""))
            total_funding += amount
            deal_count += 1

    # Normalize: score = (actual / baseline) * 50, capped at 100
    baseline = config["baseline_funding_90d"]
    if baseline > 0:
        raw_score = (total_funding / baseline) * 50
    else:
        raw_score = 25  # default mid-range

    # Bonus for deal count
    deal_bonus = min(deal_count * 3, 15)

    return min(round(raw_score + deal_bonus), 100)


def calculate_news_score(sector_name, config, news):
    """Calculate news frequency score (0-100) for a sector."""
    keywords = config["keywords"]
    companies = config["companies"]

    mention_count = 0
    for article in news:
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()

        # Check for keyword mentions
        if any(kw in text for kw in keywords):
            mention_count += 1
            continue

        # Check for company mentions
        if any(c.lower() in text for c in companies):
            mention_count += 1

    # Normalize: ~10 mentions/week = score 50
    raw_score = (mention_count / 10) * 50
    return min(round(raw_score), 100)


def calculate_hiring_score(sector_name, config, jobs):
    """Calculate hiring velocity score (0-100) for a sector."""
    sector_companies = set(c.lower() for c in config["companies"])

    job_count = 0
    for job in jobs:
        if job.get("company", "").lower() in sector_companies:
            job_count += 1

    # Normalize: ~100 jobs = score 50
    raw_score = (job_count / 100) * 50
    return min(round(raw_score), 100)


def calculate_market_score(sector_name, config, stocks):
    """Calculate market sentiment score (0-100) from stock performance."""
    tickers = config["tickers"]
    if not tickers:
        return 50  # Neutral for sectors without public companies

    changes = []
    for ticker in tickers:
        if ticker in stocks:
            pct = stocks[ticker].get("changePercent", 0)
            changes.append(pct)

    if not changes:
        return 50

    avg_change = sum(changes) / len(changes)
    # Map: -5% = 0, 0% = 50, +5% = 100
    raw_score = 50 + (avg_change * 10)
    return max(0, min(round(raw_score), 100))


def determine_trend(funding_score, news_score):
    """Determine trend direction based on signal strength."""
    avg = (funding_score + news_score) / 2
    if avg >= 70:
        return "accelerating"
    elif avg >= 45:
        return "steady"
    elif avg >= 25:
        return "rising"
    else:
        return "declining"


def generate_catalysts(sector_name, news, config):
    """Extract top catalysts from recent news for a sector."""
    keywords = config["keywords"]
    companies = config["companies"]
    catalysts = []

    for article in news[:50]:  # Check recent articles
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        title = article.get("title", "")

        if any(kw in text for kw in keywords) or any(c.lower() in text for c in companies):
            # Extract a short catalyst phrase from the title
            clean_title = title[:60].strip()
            if clean_title and clean_title not in catalysts:
                catalysts.append(clean_title)
                if len(catalysts) >= 3:
                    break

    # Fallback catalysts if none found from news
    if not catalysts:
        catalysts = [f"Active {sector_name.lower()} ecosystem"]

    return catalysts[:3]


def main():
    print("=" * 60)
    print("Sector Momentum Calculator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sectors: {len(SECTOR_CONFIG)}")
    print("=" * 60)

    # Load all data sources
    deals = load_deals()
    news = load_news()
    jobs = load_jobs()
    stocks = load_stocks()

    print(f"Deals loaded: {len(deals)}")
    print(f"News articles loaded: {len(news)}")
    print(f"Jobs loaded: {len(jobs)}")
    print(f"Stock tickers loaded: {len(stocks)}")
    print()

    # Calculate momentum for each sector
    results = []
    for sector_name, config in SECTOR_CONFIG.items():
        funding_score = calculate_funding_score(sector_name, config, deals)
        news_score = calculate_news_score(sector_name, config, news)
        hiring_score = calculate_hiring_score(sector_name, config, jobs)
        market_score = calculate_market_score(sector_name, config, stocks)

        # Weighted composite
        composite = round(
            funding_score * 0.35 +
            news_score * 0.25 +
            hiring_score * 0.20 +
            market_score * 0.20
        )

        trend = determine_trend(funding_score, news_score)
        catalysts = generate_catalysts(sector_name, news, config)

        results.append({
            "sector": sector_name,
            "momentum": composite,
            "trend": trend,
            "catalysts": catalysts,
            "fundingQ": f"${round(parse_amount_millions_total(deals, config) / 1000, 1)}B" if parse_amount_millions_total(deals, config) >= 1000 else f"${round(parse_amount_millions_total(deals, config))}M",
            "components": {
                "funding": funding_score,
                "news": news_score,
                "hiring": hiring_score,
                "market": market_score
            },
            "lastUpdated": datetime.now().strftime("%Y-%m-%d")
        })

        print(f"  {sector_name:30s} | Momentum: {composite:3d} | {trend:13s} | F:{funding_score:3d} N:{news_score:3d} H:{hiring_score:3d} M:{market_score:3d}")

    # Sort by momentum score descending
    results.sort(key=lambda x: x["momentum"], reverse=True)

    # Save
    output_path = DATA_DIR / "sector_momentum_auto.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved {len(results)} sector scores to {output_path}")
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


def parse_amount_millions_total(deals, config):
    """Total funding in millions for a sector's companies in trailing 90 days."""
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m")
    sector_companies = set(c.lower() for c in config["companies"])
    total = 0
    for deal in deals:
        if deal.get("date", "") >= cutoff and deal.get("company", "").lower() in sector_companies:
            total += parse_amount_millions(deal.get("amount", ""))
    return total


if __name__ == "__main__":
    main()
