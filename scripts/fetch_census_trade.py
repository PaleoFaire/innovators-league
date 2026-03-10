#!/usr/bin/env python3
"""
US Census Bureau International Trade Data Fetcher for The Innovators League
Tracks US import/export trends for manufacturing-relevant HS codes.
Valuable for the 55+ manufacturing/reindustrialization companies in the database.

API: Census Bureau International Trade API
  - Imports: https://api.census.gov/data/timeseries/intltrade/imports/hs
  - Exports: https://api.census.gov/data/timeseries/intltrade/exports/hs
Requires CENSUS_API_KEY (free, register at api.census.gov/data/key_signup.html).
"""

import json
import os
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")

IMPORTS_URL = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
EXPORTS_URL = "https://api.census.gov/data/timeseries/intltrade/exports/hs"

# HS codes relevant to Innovators League manufacturing companies
# 4-digit level provides good sector granularity
HS_CODES = {
    "8542": {
        "name": "Integrated circuits / semiconductors",
        "sector": "chips",
        "companies": ["Cerebras", "Etched", "Lightmatter", "Astera Labs", "Tenstorrent", "Groq"],
    },
    "8541": {
        "name": "Diodes, transistors, semiconductor devices",
        "sector": "chips",
        "companies": ["Finwave Semiconductor", "Gallox Semiconductors", "Vertical Semiconductor"],
    },
    "8802": {
        "name": "Aircraft and spacecraft parts",
        "sector": "space",
        "companies": ["SpaceX", "Rocket Lab", "Relativity Space", "Boom Supersonic"],
    },
    "2844": {
        "name": "Radioactive elements (nuclear fuel)",
        "sector": "nuclear",
        "companies": ["Oklo", "Kairos Power", "TerraPower", "X-Energy", "NuScale"],
    },
    "8501": {
        "name": "Electric motors and generators",
        "sector": "robotics",
        "companies": ["Figure AI", "Agility Robotics", "RISE Robotics", "Standard Bots"],
    },
    "8507": {
        "name": "Electric accumulators (batteries)",
        "sector": "energy",
        "companies": ["Form Energy", "Natron Energy", "EnerVenue", "Solid Power", "Advano"],
    },
    "7601": {
        "name": "Unwrought aluminum",
        "sector": "manufacturing",
        "companies": ["Hadrian", "Machina Labs", "Divergent"],
    },
    "3926": {
        "name": "Plastics/composite articles",
        "sector": "manufacturing",
        "companies": ["Axial Composites", "Layup Parts", "Fiber Dynamics"],
    },
    "9013": {
        "name": "Lasers and optical devices",
        "sector": "sensors",
        "companies": ["Lumotive", "Ouster", "Aeva Technologies", "Voyant Photonics"],
    },
    "8471": {
        "name": "Data processing machines / computers",
        "sector": "ai",
        "companies": ["NVIDIA", "Cerebras", "Groq"],
    },
}


def fetch_trade_data(hs_code, trade_type="imports", months=12):
    """Fetch monthly import or export data for a specific HS code."""
    base_url = IMPORTS_URL if trade_type == "imports" else EXPORTS_URL

    # Calculate time range
    now = datetime.now()
    # Census data has ~3 month lag for imports, longer for exports
    lag_days = 90 if trade_type == "imports" else 120
    end_date = now - timedelta(days=lag_days)
    start_date = end_date - timedelta(days=30 * months)

    # Imports use GEN_VAL_MO (general value), exports use ALL_VAL_MO (all methods)
    value_field = "GEN_VAL_MO" if trade_type == "imports" else "ALL_VAL_MO"
    commodity_key = "I_COMMODITY" if trade_type == "imports" else "E_COMMODITY"
    params = {
        "get": value_field,
        "COMM_LVL": "HS4",
        commodity_key: hs_code,
        "time": f"from {start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}",
    }
    # Only include key if set — API works without it (lower rate limit)
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    try:
        resp = requests.get(base_url, params=params, timeout=30)
        resp.raise_for_status()
        # Census API returns HTML on invalid key — detect and retry without key
        if resp.text.strip().startswith("<"):
            print(f"  Warning: API returned HTML (likely invalid key), retrying without key...")
            params.pop("key", None)
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            if resp.text.strip().startswith("<"):
                print(f"  Error: API still returning HTML, skipping")
                return []
        data = resp.json()

        if not data or len(data) < 2:
            return []

        # First row is headers, rest is data
        headers = data[0]
        rows = data[1:]

        results = []
        for row in rows:
            entry = dict(zip(headers, row))
            try:
                value = int(entry.get(value_field, 0) or 0)
                period = entry.get("time", "")
                results.append({
                    "period": period,
                    "value": value,
                })
            except (ValueError, TypeError):
                continue

        # Sort by period
        results.sort(key=lambda x: x["period"])
        return results

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {trade_type} for HS {hs_code}: {e}")
        return []
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  Parse error for HS {hs_code}: {e}")
        return []


def calculate_trends(monthly_data):
    """Calculate year-over-year and month-over-month trends."""
    if len(monthly_data) < 2:
        return {"yoyChange": "", "momChange": "", "trend": "unknown"}

    latest = monthly_data[-1]["value"]
    prev_month = monthly_data[-2]["value"] if len(monthly_data) >= 2 else 0

    # Month-over-month
    mom_change = ""
    if prev_month > 0:
        mom_pct = ((latest - prev_month) / prev_month) * 100
        mom_change = f"{mom_pct:+.1f}%"

    # Year-over-year (compare to 12 months ago if available)
    yoy_change = ""
    if len(monthly_data) >= 12:
        year_ago = monthly_data[-12]["value"]
        if year_ago > 0:
            yoy_pct = ((latest - year_ago) / year_ago) * 100
            yoy_change = f"{yoy_pct:+.1f}%"

    # Determine trend direction
    trend = "stable"
    if yoy_change:
        yoy_num = float(yoy_change.replace("%", "").replace("+", ""))
        if yoy_num > 10:
            trend = "surging"
        elif yoy_num > 3:
            trend = "growing"
        elif yoy_num < -10:
            trend = "declining"
        elif yoy_num < -3:
            trend = "contracting"

    return {
        "yoyChange": yoy_change,
        "momChange": mom_change,
        "trend": trend,
    }


def format_value(value):
    """Format trade value for display."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def main():
    print("=" * 60)
    print("Census Bureau Trade Data Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not CENSUS_API_KEY:
        print("WARNING: CENSUS_API_KEY not set. Generating empty output files.")
        with open(DATA_DIR / "trade_data_raw.json", "w") as f:
            json.dump([], f)
        js_path = DATA_DIR / "trade_data_auto.js"
        with open(js_path, "w") as f:
            f.write(f"// Census trade data — API key not configured\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const TRADE_DATA_AUTO = [];\n")
        print("Empty output files created.")
        return

    print(f"API Key: {'*' * 8}...{CENSUS_API_KEY[-4:]}")
    print(f"Tracking {len(HS_CODES)} HS codes across manufacturing sectors")
    print("=" * 60)

    all_trade_data = []

    for hs_code, info in HS_CODES.items():
        print(f"\nHS {hs_code}: {info['name']} ({info['sector']})")

        for trade_type in ["imports", "exports"]:
            monthly = fetch_trade_data(hs_code, trade_type, months=14)
            time.sleep(0.5)  # Rate limiting

            if not monthly:
                print(f"  {trade_type}: No data available")
                continue

            trends = calculate_trends(monthly)
            latest_value = monthly[-1]["value"] if monthly else 0
            latest_period = monthly[-1]["period"] if monthly else ""

            entry = {
                "hsCode": hs_code,
                "category": info["name"],
                "tradeType": trade_type,
                "latestMonthValue": latest_value,
                "latestMonthFormatted": format_value(latest_value),
                "yoyChange": trends["yoyChange"],
                "momChange": trends["momChange"],
                "trend": trends["trend"],
                "relevantCompanies": info["companies"],
                "relevantSector": info["sector"],
                "period": latest_period,
                "monthlyData": monthly[-6:],  # Last 6 months for sparklines
                "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
            }
            all_trade_data.append(entry)
            print(f"  {trade_type}: {format_value(latest_value)} ({latest_period}) YoY: {trends['yoyChange'] or 'N/A'} | {trends['trend']}")

    print(f"\nTotal trade data entries: {len(all_trade_data)}")

    # Save raw JSON
    raw_path = DATA_DIR / "trade_data_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_trade_data, f, indent=2)
    print(f"Saved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated Census Bureau trade data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Tracking {len(HS_CODES)} HS codes across manufacturing sectors",
        "const TRADE_DATA_AUTO = [",
    ]

    for entry in all_trade_data:
        companies_str = json.dumps(entry["relevantCompanies"])
        # Exclude monthlyData from JS snippet (too verbose), keep in raw JSON
        js_lines.append("  {")
        js_lines.append(f'    hsCode: "{entry["hsCode"]}",')
        js_lines.append(f'    category: "{entry["category"]}",')
        js_lines.append(f'    tradeType: "{entry["tradeType"]}",')
        js_lines.append(f'    latestMonthValue: {entry["latestMonthValue"]},')
        js_lines.append(f'    latestMonthFormatted: "{entry["latestMonthFormatted"]}",')
        js_lines.append(f'    yoyChange: "{entry["yoyChange"]}",')
        js_lines.append(f'    momChange: "{entry["momChange"]}",')
        js_lines.append(f'    trend: "{entry["trend"]}",')
        js_lines.append(f'    relevantCompanies: {companies_str},')
        js_lines.append(f'    relevantSector: "{entry["relevantSector"]}",')
        js_lines.append(f'    period: "{entry["period"]}",')
        js_lines.append(f'    lastUpdated: "{entry["lastUpdated"]}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "trade_data_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Summary by sector
    print("\nTrade Trends by Sector:")
    sectors = {}
    for entry in all_trade_data:
        sector = entry["relevantSector"]
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(entry)

    for sector, entries in sorted(sectors.items()):
        import_entries = [e for e in entries if e["tradeType"] == "imports"]
        export_entries = [e for e in entries if e["tradeType"] == "exports"]
        total_imports = sum(e["latestMonthValue"] for e in import_entries)
        total_exports = sum(e["latestMonthValue"] for e in export_entries)
        print(f"  {sector:15s} | Imports: {format_value(total_imports)} | Exports: {format_value(total_exports)}")

    print("=" * 60)


if __name__ == "__main__":
    main()
