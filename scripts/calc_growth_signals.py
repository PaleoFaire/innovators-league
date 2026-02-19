#!/usr/bin/env python3
"""
Growth Signals Aggregator for The Innovators League
Calculates growth signals from all available auto-updated data sources:
  - Job postings (hiring velocity)
  - Stock prices (market momentum)
  - News signals (media buzz)
  - Patent filings (IP moat)
  - Gov contracts (government traction)
  - SEC filings (regulatory activity)

Produces a unified GROWTH_SIGNALS array per company.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"


def load_js_const(filename, const_name):
    """Load a JS const from a data file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []

    with open(filepath) as f:
        content = f.read()

    # Try JSON-style parsing for simple arrays
    match = re.search(rf'const {const_name} = (\[[\s\S]*?\]);', content)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: extract company names
    companies = []
    for m in re.finditer(r'company:\s*"([^"]*)"', content):
        companies.append({"company": m.group(1)})
    return companies


def load_json_file(filename):
    """Load a JSON file from data directory."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return []


def count_jobs_by_company(jobs_file="jobs_auto.js"):
    """Count job postings per company."""
    filepath = DATA_DIR / jobs_file
    if not filepath.exists():
        return {}

    with open(filepath) as f:
        content = f.read()

    counts = defaultdict(int)
    for m in re.finditer(r'company:\s*"([^"]*)"', content):
        counts[m.group(1)] += 1

    return dict(counts)


def load_stock_changes(stocks_file="stocks_auto.js"):
    """Load stock price changes."""
    filepath = DATA_DIR / stocks_file
    if not filepath.exists():
        return {}

    with open(filepath) as f:
        content = f.read()

    match = re.search(r'const STOCK_PRICES = (\{[\s\S]*?\});', content)
    if not match:
        return {}

    try:
        stocks = json.loads(match.group(1))
        return {
            v["company"]: v.get("changePercent", 0)
            for v in stocks.values()
            if "company" in v
        }
    except json.JSONDecodeError:
        return {}


def count_news_by_company():
    """Count recent news mentions per company."""
    news = load_json_file("news_raw.json")
    counts = defaultdict(int)
    for article in news:
        company = article.get("matchedCompany", "")
        if company:
            counts[company] += 1
    return dict(counts)


def count_patents_by_company():
    """Count patents per company from patent data."""
    filepath = DATA_DIR / "patent_intel_auto.js"
    if not filepath.exists():
        return {}

    with open(filepath) as f:
        content = f.read()

    patents = {}
    for m in re.finditer(r'company:\s*"([^"]*)"[\s\S]*?patentCount:\s*(\d+)', content):
        patents[m.group(1)] = int(m.group(2))

    return patents


def count_gov_contracts():
    """Count government contract activity."""
    filepath = DATA_DIR / "gov_contracts_auto.js"
    if not filepath.exists():
        return {}

    with open(filepath) as f:
        content = f.read()

    contracts = {}
    for m in re.finditer(r'company:\s*"([^"]*)"[\s\S]*?contractCount:\s*(\d+)', content):
        contracts[m.group(1)] = int(m.group(2))

    return contracts


def determine_signal_type(job_count, stock_change, news_count, patent_count, gov_count):
    """Determine the strongest growth signal type for a company."""
    signals = []

    if job_count >= 50:
        signals.append(("hiring_surge", f"{job_count} open roles"))
    elif job_count >= 20:
        signals.append(("hiring_growth", f"{job_count} open roles"))

    if stock_change and abs(stock_change) >= 5:
        direction = "up" if stock_change > 0 else "down"
        signals.append(("stock_movement", f"{stock_change:+.1f}% {direction}"))

    if news_count >= 5:
        signals.append(("media_buzz", f"{news_count} recent articles"))
    elif news_count >= 2:
        signals.append(("news_activity", f"{news_count} recent articles"))

    if patent_count >= 10:
        signals.append(("ip_moat", f"{patent_count} patents"))

    if gov_count >= 10:
        signals.append(("gov_traction", f"{gov_count} contracts"))

    return signals


def main():
    print("=" * 60)
    print("Growth Signals Aggregator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Gather all data sources
    job_counts = count_jobs_by_company()
    stock_changes = load_stock_changes()
    news_counts = count_news_by_company()
    patent_counts = count_patents_by_company()
    gov_counts = count_gov_contracts()

    print(f"Companies with jobs: {len(job_counts)}")
    print(f"Companies with stocks: {len(stock_changes)}")
    print(f"Companies with news: {len(news_counts)}")
    print(f"Companies with patents: {len(patent_counts)}")
    print(f"Companies with gov contracts: {len(gov_counts)}")

    # Build unified company set
    all_companies = set()
    for source in [job_counts, stock_changes, news_counts, patent_counts, gov_counts]:
        all_companies.update(source.keys())

    print(f"Total unique companies: {len(all_companies)}")

    # Generate growth signals
    signals = []
    for company in sorted(all_companies):
        jobs = job_counts.get(company, 0)
        stock = stock_changes.get(company, None)
        news = news_counts.get(company, 0)
        patents = patent_counts.get(company, 0)
        gov = gov_counts.get(company, 0)

        company_signals = determine_signal_type(jobs, stock, news, patents, gov)

        if company_signals:
            # Calculate composite strength
            strength = 0
            if jobs >= 50:
                strength += 3
            elif jobs >= 20:
                strength += 2
            elif jobs >= 5:
                strength += 1

            if stock and stock > 5:
                strength += 2
            if news >= 3:
                strength += 2
            elif news >= 1:
                strength += 1
            if patents >= 10:
                strength += 2
            if gov >= 10:
                strength += 2

            for signal_type, detail in company_signals:
                signals.append({
                    "company": company,
                    "type": signal_type,
                    "detail": detail,
                    "strength": min(strength, 10),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })

    # Sort by strength descending
    signals.sort(key=lambda x: x["strength"], reverse=True)

    print(f"\nGenerated {len(signals)} growth signals")

    # Save
    output_path = DATA_DIR / "growth_signals_auto.json"
    with open(output_path, "w") as f:
        json.dump(signals, f, indent=2)

    print(f"Saved to {output_path}")

    # Top 10
    if signals:
        print("\nTop 10 Growth Signals:")
        for s in signals[:10]:
            print(f"  {s['company']:30s} | {s['type']:15s} | {s['detail']} (strength: {s['strength']})")

    print("=" * 60)


if __name__ == "__main__":
    main()
