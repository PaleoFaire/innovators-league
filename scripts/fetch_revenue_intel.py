#!/usr/bin/env python3
"""
Revenue Intelligence Fetcher for The Innovators League
Extracts revenue data from SEC 10-K/10-Q filings for public companies.
Uses SEC EDGAR XBRL API (free, no key required).

Supplements manual revenue estimates for private companies.
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path
import time

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

SEC_HEADERS = {
    "User-Agent": "InnovatorsLeague contact@innovatorsleague.com",
    "Accept": "application/json"
}

# Public companies with CIK numbers for revenue tracking
PUBLIC_REVENUE_TARGETS = {
    "PLTR": {"name": "Palantir", "cik": "0001321655"},
    "RKLB": {"name": "Rocket Lab", "cik": "0001819994"},
    "PL": {"name": "Planet Labs", "cik": "0001836935"},
    "LUNR": {"name": "Intuitive Machines", "cik": "0001881487"},
    "OKLO": {"name": "Oklo", "cik": "0001849056"},
    "AI": {"name": "C3.ai", "cik": "0001577526"},
    "IONQ": {"name": "IonQ", "cik": "0001820302"},
    "RGTI": {"name": "Rigetti Computing", "cik": "0001838359"},
    "QBTS": {"name": "D-Wave Quantum", "cik": "0001907982"},
    "RXRX": {"name": "Recursion Pharmaceuticals", "cik": "0001601830"},
    "ACHR": {"name": "Archer Aviation", "cik": "0001824502"},
    "JOBY": {"name": "Joby Aviation", "cik": "0001819974"},
    "RIVN": {"name": "Rivian", "cik": "0001874178"},
    "ASTS": {"name": "AST SpaceMobile", "cik": "0001780312"},
    "TEM": {"name": "Tempus AI", "cik": "0001786842"},
    "NVDA": {"name": "NVIDIA", "cik": "0001045810"},
    "TSLA": {"name": "Tesla", "cik": "0001318605"},
}


def fetch_company_financials(cik, ticker):
    """Fetch latest revenue from SEC EDGAR XBRL companyfacts API."""
    cik_padded = cik.lstrip("0").zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"

    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        data = resp.json()
        facts = data.get("facts", {})

        # Try US-GAAP revenue concepts
        us_gaap = facts.get("us-gaap", {})
        revenue_concepts = [
            "Revenues", "Revenue", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax",
            "TotalRevenue",
        ]

        for concept in revenue_concepts:
            if concept in us_gaap:
                units = us_gaap[concept].get("units", {})
                usd_entries = units.get("USD", [])
                if not usd_entries:
                    continue

                # Get annual (10-K) entries
                annual = [e for e in usd_entries if e.get("form") == "10-K" and e.get("fp") == "FY"]
                quarterly = [e for e in usd_entries if e.get("form") == "10-Q"]

                # Get most recent annual revenue
                if annual:
                    annual.sort(key=lambda x: x.get("end", ""), reverse=True)
                    latest = annual[0]
                    val = latest.get("val", 0)
                    period = latest.get("end", "")[:4]

                    # Calculate YoY growth
                    growth = ""
                    if len(annual) >= 2:
                        prev_val = annual[1].get("val", 0)
                        if prev_val > 0:
                            pct = ((val - prev_val) / prev_val) * 100
                            growth = f"{pct:+.0f}% YoY"

                    return {
                        "revenue": format_revenue(val),
                        "period": f"{period} Annual",
                        "growth": growth,
                        "source": f"SEC 10-K ({ticker})",
                        "raw_value": val,
                    }

        return None

    except Exception as e:
        print(f"  Error for {ticker}: {e}")
        return None


def format_revenue(val):
    """Format revenue value to human-readable string."""
    if val >= 1e12:
        return f"${val/1e12:.1f}T"
    elif val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.0f}M"
    elif val >= 1e3:
        return f"${val/1e3:.0f}K"
    return f"${val:.0f}"


def load_existing_revenue():
    """Load existing REVENUE_INTEL from data.js."""
    if not DATA_JS_PATH.exists():
        return []

    with open(DATA_JS_PATH) as f:
        content = f.read()

    match = re.search(r'const REVENUE_INTEL = \[([\s\S]*?)\];', content)
    if not match:
        return []

    entries = []
    for obj in re.finditer(r'\{([^}]+)\}', match.group(1)):
        entry = {}
        for field in ['company', 'revenue', 'period', 'growth', 'source']:
            fm = re.search(rf'{field}:\s*"([^"]*)"', obj.group(1))
            if fm:
                entry[field] = fm.group(1)
        if entry.get('company'):
            entries.append(entry)

    return entries


def merge_revenue(existing, new_data):
    """Merge new SEC data with existing manual data."""
    # Index existing by company name
    existing_by_company = {e["company"].lower(): e for e in existing}

    updated_count = 0
    for ticker, data in new_data.items():
        info = PUBLIC_REVENUE_TARGETS[ticker]
        company_lower = info["name"].lower()

        if company_lower in existing_by_company:
            # Update existing entry with fresh SEC data
            existing_by_company[company_lower].update({
                "revenue": data["revenue"],
                "period": data["period"],
                "growth": data["growth"],
                "source": data["source"],
            })
            updated_count += 1
        else:
            # Add new entry
            existing.append({
                "company": info["name"],
                "revenue": data["revenue"],
                "period": data["period"],
                "growth": data["growth"],
                "source": data["source"],
            })
            updated_count += 1

    return existing, updated_count


def main():
    print("=" * 60)
    print("Revenue Intelligence Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tracking: {len(PUBLIC_REVENUE_TARGETS)} public companies")
    print("=" * 60)

    # Fetch from SEC
    new_data = {}
    for ticker, info in PUBLIC_REVENUE_TARGETS.items():
        print(f"Fetching: {ticker} ({info['name']})...")
        result = fetch_company_financials(info["cik"], ticker)
        if result:
            new_data[ticker] = result
            print(f"  Revenue: {result['revenue']} ({result['period']}) {result['growth']}")
        else:
            print(f"  No revenue data found")
        time.sleep(0.2)  # Rate limit

    print(f"\nSuccessfully fetched: {len(new_data)} companies")

    # Load existing and merge
    existing = load_existing_revenue()
    print(f"Existing entries: {len(existing)}")

    merged, updated = merge_revenue(existing, new_data)
    print(f"Updated entries: {updated}")

    # Sort by revenue descending
    def sort_key(e):
        rev = e.get("revenue", "$0")
        match = re.search(r'\$(\d+(?:\.\d+)?)\s*([TBMKtbmk])', rev)
        if match:
            num = float(match.group(1))
            unit = match.group(2).upper()
            multiplier = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(unit, 1)
            return num * multiplier
        return 0

    merged.sort(key=sort_key, reverse=True)

    # Save
    output_path = DATA_DIR / "revenue_intel_auto.json"
    with open(output_path, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"Saved {len(merged)} entries to {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
