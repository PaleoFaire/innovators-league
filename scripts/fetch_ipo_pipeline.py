#!/usr/bin/env python3
"""
IPO Pipeline Tracker for The Innovators League
Monitors SEC EDGAR for S-1 filings and IPO-related activity.
Merges with existing IPO_PIPELINE to keep editorial assessments.

Free API: SEC EDGAR FULL-TEXT search (EFTS) — no key required.
"""

import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

SEC_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_SEARCH_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_HEADERS = {
    "User-Agent": "InnovatorsLeague contact@innovatorsleague.com",
    "Accept": "application/json"
}

# Companies to watch for IPO activity
IPO_WATCH_LIST = [
    "SpaceX", "Cerebras", "Databricks", "Anduril", "Applied Intuition",
    "Stripe", "Shield AI", "Boom Supersonic", "Helion", "Hadrian",
    "Saronic", "Anthropic", "OpenAI", "Scale AI", "Figma",
    "Discord", "Canva", "Plaid", "Instacart", "Klarna",
    "Relativity Space", "Commonwealth Fusion", "Astranis",
    "Varda Space", "Figure AI", "Zipline", "Skydio",
]


def search_sec_filings(query, form_types=None, date_range=None):
    """Search SEC EDGAR full-text search for filings."""
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": query,
        "dateRange": date_range or "custom",
        "startdt": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        "enddt": datetime.now().strftime("%Y-%m-%d"),
    }
    if form_types:
        params["forms"] = ",".join(form_types)

    try:
        resp = requests.get(url, params=params, headers=SEC_HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  SEC search error: {e}")
    return None


def check_s1_filings():
    """Check for recent S-1 filings from watched companies."""
    s1_filings = []

    # Use the existing SEC filings data
    sec_path = DATA_DIR / "sec_filings_auto.js"
    if sec_path.exists():
        with open(sec_path) as f:
            content = f.read()

        # Parse S-1 and 424B4 (IPO prospectus) filings
        for match in re.finditer(r'company:\s*"([^"]*)".*?form:\s*"(S-1[^"]*|424B4)".*?date:\s*"([^"]*)"', content):
            s1_filings.append({
                "company": match.group(1),
                "form": match.group(2),
                "date": match.group(3),
            })

    # Also check the recent JSON
    sec_json_path = DATA_DIR / "sec_filings_recent.json"
    if sec_json_path.exists():
        with open(sec_json_path) as f:
            filings = json.load(f)
        for f in filings:
            if f.get("form", "") in ["S-1", "S-1/A", "424B4", "DEF 14A"]:
                if f.get("isIPO", False) or f.get("form") in ["S-1", "S-1/A"]:
                    s1_filings.append({
                        "company": f["company"],
                        "form": f["form"],
                        "date": f.get("date", ""),
                    })

    return s1_filings


def load_existing_pipeline():
    """Load existing IPO_PIPELINE from data.js."""
    if not DATA_JS_PATH.exists():
        return []

    with open(DATA_JS_PATH) as f:
        content = f.read()

    match = re.search(r'const IPO_PIPELINE = \[([\s\S]*?)\];', content)
    if not match:
        return []

    entries = []
    for obj in re.finditer(r'\{([^}]+)\}', match.group(1)):
        entry = {}
        for field in ['company', 'status', 'likelihood', 'estimatedDate', 'estimatedValuation', 'sector']:
            fm = re.search(rf'{field}:\s*"([^"]*)"', obj.group(1))
            if fm:
                entry[field] = fm.group(1)
        if entry.get('company'):
            entries.append(entry)

    return entries


def update_pipeline_with_filings(pipeline, s1_filings):
    """Update pipeline entries based on detected S-1 filings."""
    s1_companies = {f["company"] for f in s1_filings}
    updated = False

    for entry in pipeline:
        company = entry.get("company", "")
        if any(s1c.lower() in company.lower() or company.lower() in s1c.lower()
               for s1c in s1_companies):
            if entry.get("likelihood") != "high":
                entry["likelihood"] = "high"
                entry["status"] = f"S-1 Filed — {datetime.now().strftime('%Y')}"
                updated = True

    return pipeline, updated


def main():
    print("=" * 60)
    print("IPO Pipeline Tracker")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Watching: {len(IPO_WATCH_LIST)} companies")
    print("=" * 60)

    # Check for S-1 filings
    s1_filings = check_s1_filings()
    print(f"S-1/IPO filings detected: {len(s1_filings)}")
    for f in s1_filings:
        print(f"  {f['company']}: {f['form']} ({f['date']})")

    # Load existing pipeline
    pipeline = load_existing_pipeline()
    print(f"Existing pipeline entries: {len(pipeline)}")

    # Update based on findings
    pipeline, updated = update_pipeline_with_filings(pipeline, s1_filings)

    # Save
    output_path = DATA_DIR / "ipo_pipeline_auto.json"
    with open(output_path, "w") as f:
        json.dump(pipeline, f, indent=2)

    print(f"Saved {len(pipeline)} entries to {output_path}")
    print(f"Updates made: {'Yes' if updated else 'No new changes'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
