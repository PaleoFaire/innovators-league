#!/usr/bin/env python3
"""
SAM.gov Contract Awards Fetcher for The Innovators League
Supplements USAspending data with more current contract awards from SAM.gov.
Focuses on defense, space, energy, and manufacturing companies.

API: SAM.gov Opportunities API (https://api.sam.gov/opportunities/v2/search)
Requires SAM_API_KEY (already in GitHub secrets, free registration).
Rate limit: 10 requests/second, 1,000 requests/day.
"""

import json
import os
import re
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SAM_API_KEY = os.environ.get("SAM_API_KEY", "")

# SAM.gov Opportunities API (contract opportunities, not awards)
SAM_OPPORTUNITIES_URL = "https://api.sam.gov/opportunities/v2/search"

# Keywords to search for that relate to our tracked companies/sectors
SEARCH_KEYWORDS = [
    # Defense tech keywords
    "autonomous systems", "counter-UAS", "unmanned aerial", "drone",
    "electronic warfare", "directed energy", "hypersonic",
    "artificial intelligence defense", "machine learning defense",
    "cybersecurity defense", "command and control",
    # Space keywords
    "satellite launch", "space launch", "orbital", "small satellite",
    "earth observation", "space situational awareness",
    # Nuclear & Energy
    "advanced nuclear", "nuclear reactor", "microreactor",
    "small modular reactor", "fusion energy", "geothermal",
    # Robotics & Manufacturing
    "robotics manufacturing", "autonomous vehicle", "additive manufacturing",
    "advanced manufacturing", "3D printing metal",
    # Semiconductors
    "semiconductor", "chip manufacturing", "CHIPS Act",
]

# Company names to search for directly
TRACKED_COMPANY_NAMES = [
    "Anduril", "Shield AI", "Palantir", "SpaceX", "Epirus", "Saronic",
    "Skydio", "Castelion", "Forterra", "Vannevar Labs", "Hadrian",
    "Rocket Lab", "Relativity Space", "Axiom Space", "Sierra Space",
    "Varda Space", "Planet Labs", "Capella Space", "BlackSky",
    "Oklo", "Kairos Power", "TerraPower", "X-energy", "NuScale",
    "Radiant", "Fervo Energy", "Scale AI", "Figure AI",
    "Boom Supersonic", "Joby Aviation", "Archer Aviation",
    "Cerebras", "Groq", "Tenstorrent",
]


def fetch_with_retry(url, params=None, max_retries=3, timeout=15):
    """Fetch URL with retry and exponential backoff."""
    headers = {
        "User-Agent": "InnovatorsLeague-Bot/1.0",
        "Accept": "application/json",
    }
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) * 2
                print(f"  Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"  Failed after {max_retries} retries: {e}")
                return None
    return None


def search_opportunities(keyword, api_key, days_back=90):
    """Search SAM.gov for contract opportunities matching a keyword."""
    if not api_key:
        return []

    posted_from = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "q": keyword,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": 25,
        "offset": 0,
    }

    data = fetch_with_retry(SAM_OPPORTUNITIES_URL, params=params)
    if not data:
        return []

    opportunities = data.get("opportunitiesData", [])
    return opportunities


def match_company(text, company_names):
    """Check if any tracked company name appears in the text."""
    text_lower = text.lower()
    for company in company_names:
        if company.lower() in text_lower:
            return company
    return None


def format_amount(amount):
    """Format dollar amount for display."""
    if amount is None:
        return "Undisclosed"
    amount = float(amount)
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,.0f}"


def main():
    print("=" * 60)
    print("SAM.gov Contract Opportunities Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not SAM_API_KEY:
        print("WARNING: SAM_API_KEY not set. Generating empty output files.")
        # Write empty outputs
        with open(DATA_DIR / "sam_contracts_raw.json", "w") as f:
            json.dump([], f)
        with open(DATA_DIR / "sam_contracts_aggregated.json", "w") as f:
            json.dump([], f)
        js_path = DATA_DIR / "sam_contracts_auto.js"
        with open(js_path, "w") as f:
            f.write(f"// SAM.gov contract data — API key not configured\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const SAM_CONTRACTS_AUTO = [];\n")
        print("Empty output files created.")
        return

    print(f"API Key: {'*' * 8}...{SAM_API_KEY[-4:]}")
    print("=" * 60)

    all_opportunities = []
    seen_ids = set()

    # Search by company names
    print("\nSearching by company names...")
    for company in TRACKED_COMPANY_NAMES:
        opps = search_opportunities(company, SAM_API_KEY, days_back=90)
        new_count = 0
        for opp in opps:
            opp_id = opp.get("noticeId", "")
            if opp_id and opp_id not in seen_ids:
                seen_ids.add(opp_id)
                opp["_matchedCompany"] = company
                all_opportunities.append(opp)
                new_count += 1
        if new_count > 0:
            print(f"  {company}: {new_count} opportunities")
        time.sleep(0.5)  # Rate limiting

    # Search by sector keywords
    print("\nSearching by sector keywords...")
    for keyword in SEARCH_KEYWORDS:
        opps = search_opportunities(keyword, SAM_API_KEY, days_back=60)
        new_count = 0
        for opp in opps:
            opp_id = opp.get("noticeId", "")
            if opp_id and opp_id not in seen_ids:
                seen_ids.add(opp_id)
                # Try to match to a tracked company
                title = opp.get("title", "")
                desc = opp.get("description", "")
                matched = match_company(f"{title} {desc}", TRACKED_COMPANY_NAMES)
                opp["_matchedCompany"] = matched or ""
                opp["_matchedKeyword"] = keyword
                all_opportunities.append(opp)
                new_count += 1
        if new_count > 0:
            print(f"  '{keyword}': {new_count} opportunities")
        time.sleep(0.5)

    print(f"\nTotal unique opportunities found: {len(all_opportunities)}")

    # Save raw data
    raw_path = DATA_DIR / "sam_contracts_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_opportunities, f, indent=2, default=str)
    print(f"Saved raw data to {raw_path}")

    # Aggregate by company
    company_opps = {}
    for opp in all_opportunities:
        company = opp.get("_matchedCompany", "")
        if not company:
            continue

        if company not in company_opps:
            company_opps[company] = {
                "company": company,
                "opportunityCount": 0,
                "agencies": set(),
                "types": set(),
                "recentOpportunities": [],
            }

        entry = company_opps[company]
        entry["opportunityCount"] += 1

        agency = opp.get("departmentName", "") or opp.get("subtierAgency", "")
        if agency:
            entry["agencies"].add(agency)

        notice_type = opp.get("type", "")
        if notice_type:
            entry["types"].add(notice_type)

        if len(entry["recentOpportunities"]) < 5:
            entry["recentOpportunities"].append({
                "title": opp.get("title", "")[:120],
                "agency": agency,
                "postedDate": opp.get("postedDate", ""),
                "type": notice_type,
                "noticeId": opp.get("noticeId", ""),
            })

    # Convert sets to lists for JSON
    aggregated = []
    for company, data in sorted(company_opps.items(), key=lambda x: -x[1]["opportunityCount"]):
        data["agencies"] = sorted(list(data["agencies"]))
        data["types"] = sorted(list(data["types"]))
        data["lastUpdated"] = datetime.now().strftime("%Y-%m-%d")
        aggregated.append(data)

    agg_path = DATA_DIR / "sam_contracts_aggregated.json"
    with open(agg_path, "w") as f:
        json.dump(aggregated, f, indent=2)
    print(f"Saved aggregated data to {agg_path} ({len(aggregated)} companies)")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated SAM.gov contract opportunities data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total opportunities: {len(all_opportunities)}, Companies matched: {len(aggregated)}",
        "const SAM_CONTRACTS_AUTO = [",
    ]

    for item in aggregated:
        agencies_str = json.dumps(item["agencies"][:5])
        recent_str = json.dumps(item["recentOpportunities"][:3])
        js_lines.append("  {")
        js_lines.append(f'    company: "{item["company"]}",')
        js_lines.append(f'    opportunityCount: {item["opportunityCount"]},')
        js_lines.append(f'    agencies: {agencies_str},')
        js_lines.append(f'    types: {json.dumps(item["types"])},')
        js_lines.append(f'    recentOpportunities: {recent_str},')
        js_lines.append(f'    lastUpdated: "{item["lastUpdated"]}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "sam_contracts_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Also save sector-level keyword summary (opportunities not matched to specific companies)
    unmatched = [opp for opp in all_opportunities if not opp.get("_matchedCompany")]
    print(f"\nUnmatched sector-level opportunities: {len(unmatched)}")

    if aggregated:
        print(f"\nTop Companies by Opportunity Count:")
        for item in aggregated[:10]:
            print(f"  {item['company']:30s} | {item['opportunityCount']:3d} opportunities | Agencies: {', '.join(item['agencies'][:3])}")

    print("=" * 60)


if __name__ == "__main__":
    main()
