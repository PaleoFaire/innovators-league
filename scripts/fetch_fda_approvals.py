#!/usr/bin/env python3
"""
FDA Drug Approvals and Device Clearances Fetcher
Tracks FDA actions for biotech/health companies.
Uses the free openFDA API - no key required (but rate limited).
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Biotech/Health companies to track (search their products/sponsors)
TRACKED_COMPANIES = {
    "Recursion": {"type": "pharma", "search_terms": ["recursion", "recursion pharmaceuticals"]},
    "Ginkgo Bioworks": {"type": "pharma", "search_terms": ["ginkgo", "ginkgo bioworks"]},
    "Tempus AI": {"type": "device", "search_terms": ["tempus"]},
    "23andMe": {"type": "device", "search_terms": ["23andme", "23 and me"]},
    "Neuralink": {"type": "device", "search_terms": ["neuralink"]},
    "Exact Sciences": {"type": "device", "search_terms": ["exact sciences", "cologuard"]},
    "Illumina": {"type": "device", "search_terms": ["illumina"]},
    "Intuitive Surgical": {"type": "device", "search_terms": ["intuitive surgical", "da vinci"]},
    "Medtronic": {"type": "device", "search_terms": ["medtronic"]},
    "Abbott": {"type": "both", "search_terms": ["abbott laboratories", "abbott"]},
}

FDA_API_BASE = "https://api.fda.gov"

def fetch_drug_approvals(search_term, days=730):
    """Fetch recent drug approvals mentioning a company/product."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    url = f"{FDA_API_BASE}/drug/drugsfda.json"
    # Use broader search - search manufacturer OR brand name, relax date filter
    params = {
        "search": f'openfda.manufacturer_name:"{search_term}"',
        "limit": 20
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        elif response.status_code == 404:
            return []  # No results found
        else:
            print(f"  Drug API error: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        return []

def fetch_device_clearances(search_term, days=730):
    """Fetch recent 510(k) device clearances."""

    url = f"{FDA_API_BASE}/device/510k.json"
    # Use broader search - just search applicant name without strict date filter
    params = {
        "search": f'applicant:"{search_term}"',
        "limit": 20
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        elif response.status_code == 404:
            return []
        else:
            print(f"  Device API error: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        return []

def fetch_all_fda_actions():
    """Fetch FDA actions for all tracked companies."""
    all_actions = []

    for company, info in TRACKED_COMPANIES.items():
        print(f"Fetching FDA actions for: {company}")

        for term in info["search_terms"]:
            # Fetch drug approvals if applicable
            if info["type"] in ["pharma", "both"]:
                drugs = fetch_drug_approvals(term)
                for drug in drugs:
                    all_actions.append({
                        "company": company,
                        "type": "drug_approval",
                        "product": drug.get("products", [{}])[0].get("brand_name", "Unknown"),
                        "date": drug.get("submissions", [{}])[0].get("submission_status_date", ""),
                        "status": drug.get("submissions", [{}])[0].get("submission_status", ""),
                        "application_number": drug.get("application_number", ""),
                    })
                time.sleep(0.5)  # Rate limit

            # Fetch device clearances if applicable
            if info["type"] in ["device", "both"]:
                devices = fetch_device_clearances(term)
                for device in devices:
                    all_actions.append({
                        "company": company,
                        "type": "device_510k",
                        "product": device.get("device_name", "Unknown"),
                        "date": device.get("decision_date", ""),
                        "status": device.get("decision_code", ""),
                        "k_number": device.get("k_number", ""),
                    })
                time.sleep(0.5)  # Rate limit

        if any(a["company"] == company for a in all_actions):
            print(f"  Found {len([a for a in all_actions if a['company'] == company])} FDA actions")
        else:
            print(f"  No recent FDA actions")

    return all_actions

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(actions):
    """Generate JavaScript code snippet for FDA_ACTIONS."""
    # Sort by date descending
    actions.sort(key=lambda x: x.get("date", ""), reverse=True)

    js_output = "// Auto-updated FDA approvals and clearances\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const FDA_ACTIONS = [\n"

    for a in actions[:30]:  # Top 30 most recent
        product = a.get("product", "").replace('"', '\\"')
        js_output += f'  {{ company: "{a["company"]}", type: "{a["type"]}", product: "{product}", '
        js_output += f'date: "{a.get("date", "")}", status: "{a.get("status", "")}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "fda_actions_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("FDA Approvals & Clearances Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_COMPANIES)} biotech/health companies")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all FDA actions
    actions = fetch_all_fda_actions()
    print(f"\nTotal FDA actions found: {len(actions)}")

    # Save data
    save_to_json(actions, "fda_actions_raw.json")

    # Generate JS snippet
    generate_js_snippet(actions)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
