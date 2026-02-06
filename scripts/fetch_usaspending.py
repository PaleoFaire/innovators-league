#!/usr/bin/env python3
"""
USAspending.gov Government Contracts Fetcher
Fetches federal contract data for companies tracked in The Innovators League.
Free API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Companies to track for government contracts
TRACKED_COMPANIES = [
    # Defense & Security
    "Anduril", "Anduril Industries",
    "Shield AI",
    "Palantir", "Palantir Technologies",
    "SpaceX", "Space Exploration Technologies",
    "Epirus",
    "Saronic",
    "Skydio",
    "Neros",
    "Chaos Industries",
    "Castelion",
    "Forterra",
    "Vannevar Labs",
    "Rebellion Defense",
    "Primer",
    "Second Front Systems",
    "Hadrian",

    # Space & Aerospace
    "Rocket Lab", "Rocket Lab USA",
    "Relativity Space",
    "Axiom Space",
    "Sierra Space",
    "Varda Space Industries",
    "Impulse Space",
    "Planet Labs",
    "Muon Space",
    "Albedo",
    "BlackSky", "BlackSky Technology",
    "Capella Space",

    # Nuclear & Energy
    "Oklo",
    "Kairos Power",
    "TerraPower",
    "X-energy",
    "NuScale", "NuScale Power",
    "Radiant",
    "Fervo Energy",

    # AI & Robotics
    "Scale AI",
    "OpenAI",
    "Anthropic",
    "Figure AI",
    "Boston Dynamics",
    "Agility Robotics",

    # Biotech
    "Moderna",
    "Ginkgo Bioworks",
]

USASPENDING_API = "https://api.usaspending.gov/api/v2"

def fetch_contracts_for_company(company_name, start_date=None):
    """Fetch federal contracts for a specific company."""
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    end_date = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "recipient_search_text": [company_name],
            "time_period": [
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            ],
            "award_type_codes": ["A", "B", "C", "D"]  # Contracts only
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Award Type",
            "Start Date",
            "End Date",
            "Description"
        ],
        "page": 1,
        "limit": 100,
        "sort": "Award Amount",
        "order": "desc"
    }

    try:
        response = requests.post(
            f"{USASPENDING_API}/search/spending_by_award/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contracts for {company_name}: {e}")
        return None

def fetch_all_contracts():
    """Fetch contracts for all tracked companies."""
    all_contracts = []

    for company in TRACKED_COMPANIES:
        print(f"Fetching contracts for: {company}")
        result = fetch_contracts_for_company(company)

        if result and "results" in result:
            for award in result["results"]:
                contract = {
                    "company": company,
                    "awardId": award.get("Award ID", ""),
                    "recipientName": award.get("Recipient Name", ""),
                    "amount": award.get("Award Amount", 0),
                    "agency": award.get("Awarding Agency", ""),
                    "subAgency": award.get("Awarding Sub Agency", ""),
                    "awardType": award.get("Award Type", ""),
                    "startDate": award.get("Start Date", ""),
                    "endDate": award.get("End Date", ""),
                    "description": award.get("Description", "")[:200] if award.get("Description") else ""
                }
                all_contracts.append(contract)

            print(f"  Found {len(result['results'])} contracts")

    return all_contracts

def aggregate_by_company(contracts):
    """Aggregate contracts by company for the GOV_CONTRACTS format."""
    company_data = {}

    for contract in contracts:
        company = contract["company"]
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "totalGovValue": 0,
                "contractCount": 0,
                "agencies": set(),
                "recentContracts": []
            }

        amount = contract.get("amount", 0) or 0
        company_data[company]["totalGovValue"] += amount
        company_data[company]["contractCount"] += 1

        if contract.get("agency"):
            company_data[company]["agencies"].add(contract["agency"])

        # Keep top 5 recent contracts
        if len(company_data[company]["recentContracts"]) < 5:
            company_data[company]["recentContracts"].append({
                "amount": amount,
                "agency": contract.get("agency", ""),
                "description": contract.get("description", ""),
                "date": contract.get("startDate", "")
            })

    # Convert to list format
    result = []
    for company, data in company_data.items():
        if data["contractCount"] > 0:
            total = data["totalGovValue"]
            if total >= 1_000_000_000:
                total_str = f"${total/1_000_000_000:.1f}B+"
            elif total >= 1_000_000:
                total_str = f"${total/1_000_000:.0f}M+"
            else:
                total_str = f"${total/1_000:.0f}K"

            result.append({
                "company": company,
                "totalGovValue": total_str,
                "contractCount": data["contractCount"],
                "agencies": list(data["agencies"])[:5],
                "recentContracts": data["recentContracts"],
                "lastUpdated": datetime.now().strftime("%Y-%m-%d")
            })

    # Sort by total value
    result.sort(key=lambda x: x["contractCount"], reverse=True)
    return result

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(aggregated_data):
    """Generate JavaScript code snippet to update data.js."""
    js_output = "// Auto-generated government contracts data\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const GOV_CONTRACTS_AUTO = [\n"

    for item in aggregated_data:
        js_output += f"  {{\n"
        js_output += f'    company: "{item["company"]}",\n'
        js_output += f'    totalGovValue: "{item["totalGovValue"]}",\n'
        js_output += f'    contractCount: {item["contractCount"]},\n'
        js_output += f'    agencies: {json.dumps(item["agencies"])},\n'
        js_output += f'    lastUpdated: "{item["lastUpdated"]}"\n'
        js_output += f"  }},\n"

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "gov_contracts_auto.js"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("USAspending.gov Government Contracts Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_COMPANIES)} companies")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all contracts
    contracts = fetch_all_contracts()
    print(f"\nTotal contracts found: {len(contracts)}")

    # Aggregate by company
    aggregated = aggregate_by_company(contracts)
    print(f"Companies with contracts: {len(aggregated)}")

    # Save raw data
    save_to_json(contracts, "gov_contracts_raw.json")
    save_to_json(aggregated, "gov_contracts_aggregated.json")

    # Generate JS snippet
    generate_js_snippet(aggregated)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
