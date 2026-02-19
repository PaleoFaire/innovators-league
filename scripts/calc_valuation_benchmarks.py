#!/usr/bin/env python3
"""
Valuation Benchmarks Calculator for The Innovators League
Calculates valuation metrics from available data:
  - Market cap from live stock prices (public companies)
  - Implied valuations from deal tracker (private companies)
  - Revenue multiples from revenue intel + market cap

Free data sources only.
"""

import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"


def load_stock_data():
    """Load market caps from stocks_auto.js."""
    filepath = DATA_DIR / "stocks_auto.js"
    if not filepath.exists():
        return {}

    with open(filepath) as f:
        content = f.read()

    match = re.search(r'const STOCK_PRICES = (\{[\s\S]*?\});', content)
    if not match:
        return {}

    try:
        stocks = json.loads(match.group(1))
        result = {}
        for ticker, data in stocks.items():
            result[data.get("company", "")] = {
                "ticker": ticker,
                "marketCap": data.get("marketCap", "N/A"),
                "marketCapRaw": data.get("marketCapRaw", 0),
                "price": data.get("price", 0),
                "changePercent": data.get("changePercent", 0),
            }
        return result
    except json.JSONDecodeError:
        return {}


def load_deal_valuations():
    """Extract latest valuations from deals data."""
    deals = []
    deals_path = DATA_DIR / "deals_auto.json"
    if deals_path.exists():
        with open(deals_path) as f:
            deals = json.load(f)

    valuations = {}
    for d in deals:
        company = d.get("company", "")
        val = d.get("valuation", "")
        if company and val:
            valuations[company] = val

    return valuations


def load_revenue_data():
    """Load revenue data for multiples calculation."""
    rev_path = DATA_DIR / "revenue_intel_auto.json"
    if rev_path.exists():
        with open(rev_path) as f:
            return {r["company"]: r for r in json.load(f) if "company" in r}
    return {}


def parse_value(val_str):
    """Parse $2.5B or $600M to raw number."""
    if not val_str or val_str == "N/A":
        return 0
    val_str = val_str.replace('+', '').replace('~', '').strip()
    match = re.match(r'\$(\d+(?:\.\d+)?)\s*([TBMKtbmk])', val_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2).upper()
        multiplier = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(unit, 1)
        return num * multiplier
    return 0


def format_value(val):
    """Format raw number to human-readable."""
    if val >= 1e12:
        return f"${val/1e12:.1f}T"
    elif val >= 1e9:
        return f"${val/1e9:.1f}B"
    elif val >= 1e6:
        return f"${val/1e6:.0f}M"
    return "N/A"


def main():
    print("=" * 60)
    print("Valuation Benchmarks Calculator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    stock_data = load_stock_data()
    deal_valuations = load_deal_valuations()
    revenue_data = load_revenue_data()

    print(f"Public companies (stocks): {len(stock_data)}")
    print(f"Private valuations (deals): {len(deal_valuations)}")
    print(f"Revenue data: {len(revenue_data)}")

    benchmarks = []

    # Public companies — use market cap
    for company, data in stock_data.items():
        mcap_raw = data.get("marketCapRaw", 0)
        if mcap_raw <= 0:
            continue

        entry = {
            "company": company,
            "valuation": data["marketCap"],
            "valuationRaw": mcap_raw,
            "source": "market_cap",
            "ticker": data["ticker"],
            "dayChange": f"{data['changePercent']:+.1f}%",
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        }

        # Calculate revenue multiple if we have revenue
        if company in revenue_data:
            rev_str = revenue_data[company].get("revenue", "")
            rev_raw = parse_value(rev_str)
            if rev_raw > 0:
                multiple = mcap_raw / rev_raw
                entry["revenueMultiple"] = f"{multiple:.1f}x"
                entry["revenue"] = rev_str

        benchmarks.append(entry)

    # Private companies — use deal valuations
    public_names = {c.lower() for c in stock_data.keys()}
    for company, val_str in deal_valuations.items():
        if company.lower() in public_names:
            continue  # Skip if already have market cap

        val_raw = parse_value(val_str)
        if val_raw <= 0:
            continue

        entry = {
            "company": company,
            "valuation": val_str,
            "valuationRaw": val_raw,
            "source": "last_round",
            "ticker": None,
            "dayChange": None,
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        }

        if company in revenue_data:
            rev_str = revenue_data[company].get("revenue", "")
            rev_raw = parse_value(rev_str)
            if rev_raw > 0:
                multiple = val_raw / rev_raw
                entry["revenueMultiple"] = f"{multiple:.1f}x"
                entry["revenue"] = rev_str

        benchmarks.append(entry)

    # Sort by valuation descending
    benchmarks.sort(key=lambda x: x.get("valuationRaw", 0), reverse=True)

    print(f"\nTotal benchmarks: {len(benchmarks)}")

    # Save
    output_path = DATA_DIR / "valuation_benchmarks_auto.json"
    with open(output_path, "w") as f:
        json.dump(benchmarks, f, indent=2)

    print(f"Saved to {output_path}")

    if benchmarks:
        print("\nTop 10 by Valuation:")
        for b in benchmarks[:10]:
            mult = b.get("revenueMultiple", "N/A")
            print(f"  {b['company']:30s} | {b['valuation']:>10s} | Rev Multiple: {mult}")

    print("=" * 60)


if __name__ == "__main__":
    main()
