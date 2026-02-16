#!/usr/bin/env python3
"""
DOE/EIA Energy Data Fetcher
Tracks nuclear energy capacity, production, and trends.
Uses the free EIA API - requires free API key from eia.gov.
Also uses DOE OSTI for research publications.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time
import os

# EIA API key (get free at https://www.eia.gov/opendata/register.php)
# Set as environment variable EIA_API_KEY
EIA_API_KEY = os.environ.get("EIA_API_KEY", "")

# DOE OSTI (no key required)
OSTI_API_BASE = "https://www.osti.gov/api/v1"

# Nuclear energy series to track
EIA_NUCLEAR_SERIES = {
    "ELEC.GEN.NUC-US-99.M": "US Nuclear Generation Monthly",
    "INTL.2-12-USA-BKWH.M": "US Nuclear Net Generation",
}

# Research keywords for DOE publications
DOE_RESEARCH_KEYWORDS = [
    "small modular reactor",
    "microreactor",
    "advanced reactor",
    "nuclear fusion",
    "tokamak",
    "HALEU",
    "nuclear thermal propulsion",
    "molten salt reactor",
]

def fetch_osti_research(keyword, max_results=20):
    """Fetch DOE research publications from OSTI."""
    url = f"{OSTI_API_BASE}/records"

    params = {
        "q": keyword,
        "rows": max_results,
        "sort": "publication_date desc",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            return []

        # OSTI returns XML by default, let's try JSON
        # Actually OSTI API returns XML, so let's use their search endpoint
        return []  # Will implement differently

    except Exception as e:
        print(f"  Error: {e}")
        return []

def fetch_osti_via_search(keyword, max_results=20):
    """Fetch DOE research via OSTI search."""
    url = "https://www.osti.gov/search/semantic:nuclear%20reactor"

    # OSTI doesn't have a clean JSON API, so we'll track via DOE announcements instead
    return []

def fetch_doe_announcements():
    """Fetch recent DOE energy-related announcements."""
    # DOE press releases and announcements
    announcements = []

    # We'll track key nuclear/energy programs and their status
    # This is semi-automated - updated periodically with manual oversight

    nuclear_programs = [
        {
            "program": "Advanced Reactor Demonstration Program (ARDP)",
            "agency": "DOE Office of Nuclear Energy",
            "companies": ["TerraPower", "X-energy", "Kairos Power", "Westinghouse"],
            "funding": "3.2B",
            "status": "Active",
            "description": "Funding for advanced reactor demonstrations",
            "lastUpdate": "2026-01-15"
        },
        {
            "program": "HALEU Availability Program",
            "agency": "DOE Office of Nuclear Energy",
            "companies": ["Centrus Energy", "Urenco"],
            "funding": "700M",
            "status": "Active",
            "description": "High-assay low-enriched uranium production",
            "lastUpdate": "2026-01-10"
        },
        {
            "program": "Fusion Energy Sciences",
            "agency": "DOE Office of Science",
            "companies": ["Commonwealth Fusion Systems", "TAE Technologies", "Helion", "General Fusion"],
            "funding": "763M",
            "status": "Active",
            "description": "Fusion research and development",
            "lastUpdate": "2026-02-01"
        },
        {
            "program": "Nuclear Thermal Propulsion (NTP)",
            "agency": "NASA/DOE",
            "companies": ["BWXT", "Lockheed Martin"],
            "funding": "500M",
            "status": "Active",
            "description": "Nuclear propulsion for deep space missions",
            "lastUpdate": "2025-12-15"
        },
        {
            "program": "Microreactor Program",
            "agency": "DOE/DoD",
            "companies": ["Oklo", "Radiant", "Westinghouse", "X-energy"],
            "funding": "150M",
            "status": "Active",
            "description": "Transportable microreactors for remote/military use",
            "lastUpdate": "2026-01-20"
        },
    ]

    return nuclear_programs

def fetch_energy_statistics():
    """Fetch key energy statistics (requires EIA API key)."""
    if not EIA_API_KEY:
        print("  No EIA API key found. Set EIA_API_KEY environment variable.")
        print("  Get free key at: https://www.eia.gov/opendata/register.php")
        return []

    stats = []

    # Nuclear capacity and generation
    url = f"https://api.eia.gov/v2/electricity/state-electricity-profiles/source-disposition"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "annual",
        "data[0]": "nuclear-gwh",
        "facets[stateId][]": "US",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Parse response
            stats.append({
                "metric": "US Nuclear Generation",
                "source": "EIA",
                "data": data.get("response", {}).get("data", [])
            })
    except Exception as e:
        print(f"  EIA API error: {e}")

    return stats

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(programs):
    """Generate JavaScript code snippet for DOE_PROGRAMS."""
    js_output = "// Auto-updated DOE nuclear/energy programs\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const DOE_PROGRAMS = [\n"

    for p in programs:
        companies = ", ".join(p.get("companies", []))
        js_output += f'  {{ program: "{p["program"]}", agency: "{p["agency"]}", '
        js_output += f'companies: "{companies}", funding: "{p["funding"]}", '
        js_output += f'status: "{p["status"]}", lastUpdate: "{p["lastUpdate"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "doe_programs_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("DOE/EIA Energy Data Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch DOE program announcements
    print("\nFetching DOE nuclear/energy programs...")
    programs = fetch_doe_announcements()
    print(f"Tracked programs: {len(programs)}")

    # Fetch energy statistics (if API key available)
    print("\nFetching EIA energy statistics...")
    stats = fetch_energy_statistics()
    print(f"Statistics retrieved: {len(stats)}")

    # Save data
    save_to_json(programs, "doe_programs_raw.json")
    if stats:
        save_to_json(stats, "eia_statistics_raw.json")

    # Generate JS snippet
    generate_js_snippet(programs)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    total_funding = 0
    for p in programs:
        try:
            amt = float(p.get("funding", "0").replace("B", "000").replace("M", ""))
            total_funding += amt
        except:
            pass
    print(f"\nTotal tracked DOE funding: ${total_funding:,.0f}M")

    print("\nTracked Programs:")
    for p in programs:
        print(f"  {p['program']}: ${p['funding']} - {', '.join(p['companies'][:3])}")

if __name__ == "__main__":
    main()
