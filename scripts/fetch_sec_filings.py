#!/usr/bin/env python3
"""
SEC EDGAR Filings Fetcher
Fetches SEC filings for tracked public companies.
Uses the free SEC EDGAR API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Public companies to track with their CIK numbers
TRACKED_TICKERS = {
    # Defense
    "PLTR": {"name": "Palantir Technologies", "cik": "0001321655"},

    # Space
    "RKLB": {"name": "Rocket Lab", "cik": "0001819994"},
    "ASTS": {"name": "AST SpaceMobile", "cik": "0001780312"},
    "PL": {"name": "Planet Labs", "cik": "0001836935"},
    "BKSY": {"name": "BlackSky Technology", "cik": "0001753539"},
    "RDW": {"name": "Redwire Corporation", "cik": "0001868778"},
    "LUNR": {"name": "Intuitive Machines", "cik": "0001881487"},
    "MNTS": {"name": "Momentus", "cik": "0001781983"},
    "VORB": {"name": "Virgin Orbit", "cik": "0001843388"},
    "SPCE": {"name": "Virgin Galactic", "cik": "0001706946"},

    # Nuclear & Energy
    "SMR": {"name": "NuScale Power", "cik": "0001822966"},
    "OKLO": {"name": "Oklo", "cik": "0001849056"},
    "LEU": {"name": "Centrus Energy", "cik": "0001065059"},
    "FREY": {"name": "FREYR Battery", "cik": "0001851182"},

    # AI & Tech
    "AI": {"name": "C3.ai", "cik": "0001577526"},
    "UPST": {"name": "Upstart Holdings", "cik": "0001647639"},
    "PATH": {"name": "UiPath", "cik": "0001734722"},

    # Quantum
    "IONQ": {"name": "IonQ", "cik": "0001820302"},
    "RGTI": {"name": "Rigetti Computing", "cik": "0001838359"},
    "QBTS": {"name": "D-Wave Quantum", "cik": "0001907982"},

    # Biotech
    "RXRX": {"name": "Recursion Pharmaceuticals", "cik": "0001601830"},
    "DNA": {"name": "Ginkgo Bioworks", "cik": "0001830214"},

    # eVTOL / Transportation
    "ACHR": {"name": "Archer Aviation", "cik": "0001824502"},
    "JOBY": {"name": "Joby Aviation", "cik": "0001819974"},
    "LILM": {"name": "Lilium", "cik": "0001845419"},

    # Robotics
    "AGFY": {"name": "Agrify Corporation", "cik": "0001800637"},

    # 3D Printing / Manufacturing
    "DM": {"name": "Desktop Metal", "cik": "0001754820"},
    "XONE": {"name": "ExOne", "cik": "0001561627"},
    # New additions
    "AUR": {"name": "Aurora Innovation", "cik": "0001828108"},
    "DOBT": {"name": "D-Orbit", "cik": "0001819131"},
    "LNZA": {"name": "LanzaTech", "cik": "0001826667"},
    "NNE": {"name": "Nano Nuclear Energy", "cik": "0001955473"},
    "SLDP": {"name": "Solid Power", "cik": "0001854795"},
    "EVTL": {"name": "Vertical Aerospace", "cik": "0001819584"},
    "TEM": {"name": "Tempus AI", "cik": "0001786842"},
    "RIVN": {"name": "Rivian", "cik": "0001874178"},
    "ALAB": {"name": "Astera Labs", "cik": "0001857853"},
    "SATL": {"name": "Satellogic", "cik": "0001854275"},
    "ASTR": {"name": "Firefly Aerospace", "cik": "0001819012"},
}

# Filing types to track
IMPORTANT_FORMS = ["8-K", "10-K", "10-Q", "S-1", "S-1/A", "424B4", "DEF 14A", "4", "SC 13D", "SC 13G"]

SEC_API_BASE = "https://data.sec.gov"
SEC_HEADERS = {
    "User-Agent": "InnovatorsLeague contact@innovatorsleague.com",
    "Accept": "application/json"
}


def fetch_with_retry(url, headers, max_retries=3, timeout=30):
    """Fetch URL with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"  Rate limited (429), waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"  Request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    print(f"  All {max_retries} attempts failed for {url}")
    return None

def fetch_company_filings(cik, ticker_info):
    """Fetch recent filings for a company by CIK."""
    # Ensure CIK is 10 digits with leading zeros
    cik_padded = cik.lstrip("0").zfill(10)

    url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

    response = fetch_with_retry(url, SEC_HEADERS)
    if response is None:
        return []

    data = response.json()

    filings = []
    recent_filings = data.get("filings", {}).get("recent", {})

    if not recent_filings:
        return []

    forms = recent_filings.get("form", [])
    dates = recent_filings.get("filingDate", [])
    descriptions = recent_filings.get("primaryDocument", [])
    accession_numbers = recent_filings.get("accessionNumber", [])

    for i in range(min(len(forms), 50)):  # Last 50 filings
        form = forms[i]
        if form in IMPORTANT_FORMS:
            filings.append({
                "company": ticker_info["name"],
                "ticker": "",  # Will be filled in by caller
                "form": form,
                "date": dates[i] if i < len(dates) else "",
                "description": descriptions[i] if i < len(descriptions) else form,
                "accessionNumber": accession_numbers[i] if i < len(accession_numbers) else "",
                "isIPO": form in ["S-1", "S-1/A", "424B4"]
            })

    return filings

def fetch_all_filings():
    """Fetch filings for all tracked companies."""
    all_filings = []

    for ticker, info in TRACKED_TICKERS.items():
        print(f"Fetching filings for: {ticker} ({info['name']})")
        filings = fetch_company_filings(info["cik"], info)

        for filing in filings:
            filing["ticker"] = ticker
            all_filings.append(filing)

        if filings:
            print(f"  Found {len(filings)} important filings")
        else:
            print(f"  No recent important filings")

        # Be nice to the SEC servers
        time.sleep(0.2)

    return all_filings

def filter_recent_filings(filings, days=90):
    """Filter to only filings from the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    return [f for f in filings if f["date"] >= cutoff_str]

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(filings):
    """Generate JavaScript code snippet for SEC_FILINGS_LIVE."""
    # Sort by date descending
    filings.sort(key=lambda x: x["date"], reverse=True)

    js_output = "// Auto-updated SEC filings from EDGAR\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const SEC_FILINGS_LIVE = [\n"

    for f in filings[:50]:  # Top 50 most recent
        js_output += f'  {{ company: "{f["company"]}", form: "{f["form"]}", date: "{f["date"]}", '
        js_output += f'description: "{f["description"]}", isIPO: {"true" if f["isIPO"] else "false"}, ticker: "{f["ticker"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "sec_filings_auto.js"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("SEC EDGAR Filings Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_TICKERS)} public companies")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all filings
    filings = fetch_all_filings()
    print(f"\nTotal important filings found: {len(filings)}")

    # Filter to recent filings
    recent = filter_recent_filings(filings, days=90)
    print(f"Filings in last 90 days: {len(recent)}")

    # Save data
    save_to_json(filings, "sec_filings_raw.json")
    save_to_json(recent, "sec_filings_recent.json")

    # Generate JS snippet
    generate_js_snippet(recent)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary of recent important filings
    if recent:
        print("\nRecent Important Filings:")
        for f in recent[:10]:
            print(f"  {f['date']} | {f['ticker']:5} | {f['form']:8} | {f['company']}")

if __name__ == "__main__":
    main()
