#!/usr/bin/env python3
"""
USPTO PatentsView Patent Fetcher
Fetches patent data for companies tracked in The Innovators League.
Free API - no key required.
Now uses master company list for 450+ company coverage.
"""

import json
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path

# Load master company list and generate assignee variants
def load_master_companies():
    """Load company names from master list and generate USPTO assignee variants."""
    script_dir = Path(__file__).parent
    master_list_path = script_dir / "company_master_list.js"

    assignees = []
    if master_list_path.exists():
        content = master_list_path.read_text()
        pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
        for match in re.finditer(pattern, content):
            name = match.group(1)
            aliases_str = match.group(2)
            aliases = [a.strip().strip('"') for a in aliases_str.split(',') if a.strip()]

            # Generate USPTO assignee name variants
            variants = [name]

            # Add common corporate suffixes
            for base in [name] + [a for a in aliases if len(a) > 5]:
                variants.extend([
                    base,
                    f"{base} Inc",
                    f"{base}, Inc.",
                    f"{base} LLC",
                    f"{base} Corp",
                    f"{base} Corporation",
                ])

            # Remove duplicates while preserving order
            seen = set()
            unique_variants = []
            for v in variants:
                if v.lower() not in seen and len(v) > 3:
                    seen.add(v.lower())
                    unique_variants.append(v)

            assignees.append((name, unique_variants[:8]))  # Limit variants

    return assignees

# Load from master list
TRACKED_ASSIGNEES = load_master_companies()

# Fallback if master list not found
if not TRACKED_ASSIGNEES:
    TRACKED_ASSIGNEES = [
        ("SpaceX", ["Space Exploration Technologies Corp", "SpaceX"]),
        ("Anduril Industries", ["Anduril Industries", "Anduril Industries Inc"]),
        ("OpenAI", ["OpenAI", "OpenAI Inc", "OpenAI LP"]),
        ("Anthropic", ["Anthropic", "Anthropic PBC"]),
        ("Palantir", ["Palantir Technologies", "Palantir Technologies Inc"]),
    ]

PATENTSVIEW_API = "https://api.patentsview.org/patents/query"

def fetch_patents_for_assignee(assignee_names, from_date=None):
    """Fetch patents for a specific assignee."""
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # Last 2 years

    # Build OR query for multiple assignee name variants
    assignee_queries = [
        {"_contains": {"assignee_organization": name}}
        for name in assignee_names
    ]

    query = {
        "_and": [
            {"_or": assignee_queries},
            {"_gte": {"patent_date": from_date}}
        ]
    }

    params = {
        "q": json.dumps(query),
        "f": json.dumps([
            "patent_number",
            "patent_title",
            "patent_date",
            "patent_type",
            "patent_abstract",
            "assignee_organization",
            "inventor_first_name",
            "inventor_last_name",
            "cpc_group_id",
            "cpc_group_title"
        ]),
        "o": json.dumps({"per_page": 100}),
        "s": json.dumps([{"patent_date": "desc"}])
    }

    try:
        response = requests.get(
            PATENTSVIEW_API,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        return None

def fetch_all_patents(max_companies=100):
    """Fetch patents for tracked companies (with rate limiting)."""
    all_patents = []
    import time

    # Limit to prevent rate limiting issues
    companies_to_fetch = TRACKED_ASSIGNEES[:max_companies]

    for i, (company_name, assignee_variants) in enumerate(companies_to_fetch):
        print(f"[{i+1}/{len(companies_to_fetch)}] Fetching patents for: {company_name}")
        result = fetch_patents_for_assignee(assignee_variants)

        # Rate limiting - pause every 10 requests
        if (i + 1) % 10 == 0:
            print("  (pausing for rate limiting...)")
            time.sleep(2)

        if result and "patents" in result and result["patents"]:
            patents = result["patents"]
            print(f"  Found {len(patents)} patents")

            for patent in patents:
                # Extract CPC codes (technology categories)
                cpc_codes = []
                if patent.get("cpcs"):
                    cpc_codes = list(set([
                        cpc.get("cpc_group_id", "")[:4]
                        for cpc in patent["cpcs"]
                        if cpc.get("cpc_group_id")
                    ]))[:3]

                # Extract inventor names
                inventors = []
                if patent.get("inventors"):
                    inventors = [
                        f"{inv.get('inventor_first_name', '')} {inv.get('inventor_last_name', '')}".strip()
                        for inv in patent["inventors"][:3]
                    ]

                patent_data = {
                    "company": company_name,
                    "patentNumber": patent.get("patent_number", ""),
                    "title": patent.get("patent_title", ""),
                    "date": patent.get("patent_date", ""),
                    "type": patent.get("patent_type", ""),
                    "abstract": (patent.get("patent_abstract", "") or "")[:300],
                    "cpcCodes": cpc_codes,
                    "inventors": inventors
                }
                all_patents.append(patent_data)
        else:
            print(f"  No patents found")

    return all_patents

def aggregate_by_company(patents):
    """Aggregate patents by company for the PATENT_INTEL format."""
    company_data = {}

    for patent in patents:
        company = patent["company"]
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "patentCount": 0,
                "recentPatents": [],
                "technologyAreas": set(),
                "latestPatentDate": ""
            }

        company_data[company]["patentCount"] += 1

        # Track technology areas from CPC codes
        for cpc in patent.get("cpcCodes", []):
            company_data[company]["technologyAreas"].add(cpc)

        # Track latest date
        if patent["date"] > company_data[company]["latestPatentDate"]:
            company_data[company]["latestPatentDate"] = patent["date"]

        # Keep top 5 recent patents
        if len(company_data[company]["recentPatents"]) < 5:
            company_data[company]["recentPatents"].append({
                "number": patent["patentNumber"],
                "title": patent["title"],
                "date": patent["date"],
                "type": patent["type"]
            })

    # Convert to list format
    result = []
    for company, data in company_data.items():
        if data["patentCount"] > 0:
            result.append({
                "company": company,
                "patentCount": data["patentCount"],
                "recentPatents": data["recentPatents"],
                "technologyAreas": list(data["technologyAreas"])[:5],
                "latestPatentDate": data["latestPatentDate"],
                "lastUpdated": datetime.now().strftime("%Y-%m-%d")
            })

    # Sort by patent count
    result.sort(key=lambda x: x["patentCount"], reverse=True)
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
    js_output = "// Auto-generated patent intelligence data\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const PATENT_INTEL_AUTO = [\n"

    for item in aggregated_data:
        js_output += f"  {{\n"
        js_output += f'    company: "{item["company"]}",\n'
        js_output += f'    patentCount: {item["patentCount"]},\n'
        js_output += f'    technologyAreas: {json.dumps(item["technologyAreas"])},\n'
        js_output += f'    latestPatentDate: "{item["latestPatentDate"]}",\n'
        js_output += f'    lastUpdated: "{item["lastUpdated"]}"\n'
        js_output += f"  }},\n"

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "patent_intel_auto.js"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("USPTO PatentsView Patent Fetcher")
    print("=" * 60)
    print(f"Master company list: {len(TRACKED_ASSIGNEES)} companies loaded")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("Note: API rate limits apply - fetching top priority companies first")
    print("=" * 60)

    # Fetch all patents
    patents = fetch_all_patents()
    print(f"\nTotal patents found: {len(patents)}")

    # Aggregate by company
    aggregated = aggregate_by_company(patents)
    print(f"Companies with patents: {len(aggregated)}")

    # Save raw data
    save_to_json(patents, "patents_raw.json")
    save_to_json(aggregated, "patents_aggregated.json")

    # Generate JS snippet
    generate_js_snippet(aggregated)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
