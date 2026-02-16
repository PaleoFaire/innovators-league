#!/usr/bin/env python3
"""
Government Opportunities Fetcher for The Innovators League
Fetches open RFPs, BAAs, SBIRs from government portals.

Sources:
- SAM.gov (System for Award Management)
- SBIR.gov
- Beta.SAM.gov API
- Agency-specific portals

Note: Some sources require API keys. This script uses public endpoints where available.
"""

import json
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path

# Company to tech area mapping for auto-matching
COMPANY_TECH_AREAS = {
    # Defense
    "Anduril Industries": ["defense", "autonomous", "counter-drone", "AI", "surveillance"],
    "Shield AI": ["AI", "autonomous", "drones", "defense"],
    "Saronic": ["maritime", "autonomous", "naval", "defense"],
    "Epirus": ["directed energy", "counter-drone", "EW", "defense"],
    "Skydio": ["drones", "autonomous", "AI", "surveillance"],
    "Chaos Industries": ["defense", "AI", "autonomy"],
    "Allen Control Systems": ["control systems", "defense", "autonomy"],

    # Space
    "SpaceX": ["space", "launch", "rockets", "satellites"],
    "Rocket Lab": ["space", "launch", "small satellites"],
    "Relativity Space": ["space", "3D printing", "rockets"],
    "Firefly Aerospace": ["space", "launch", "lunar"],
    "Vast": ["space stations", "microgravity", "habitation"],
    "Axiom Space": ["space stations", "commercial space"],
    "Varda Space Industries": ["in-space manufacturing", "pharmaceuticals"],

    # Nuclear
    "Oklo": ["nuclear", "microreactor", "fission", "energy"],
    "Kairos Power": ["nuclear", "molten salt", "advanced reactor"],
    "Radiant": ["nuclear", "microreactor", "portable power"],
    "TerraPower": ["nuclear", "advanced reactor", "energy"],
    "X-Energy": ["nuclear", "HTGR", "advanced reactor"],
    "The Nuclear Company": ["nuclear", "SMR", "energy"],
    "Valar Atomics": ["nuclear", "energy"],

    # Hypersonic/Aviation
    "Hermeus": ["hypersonic", "propulsion", "aviation"],
    "Venus Aerospace": ["hypersonic", "propulsion"],
    "Castelion": ["hypersonic", "weapons"],

    # AI/Software
    "Anthropic": ["AI", "ML", "safety"],
    "OpenAI": ["AI", "ML", "AGI"],
    "Scale AI": ["AI", "data labeling", "ML"],
    "Palantir": ["data analytics", "AI", "defense software"],

    # Robotics
    "Figure AI": ["robotics", "humanoid", "AI"],
    "Agility Robotics": ["robotics", "humanoid", "logistics"],
    "Boston Dynamics": ["robotics", "legged robots"],

    # Energy
    "Commonwealth Fusion Systems": ["fusion", "energy", "magnets"],
    "Helion": ["fusion", "energy"],
    "TAE Technologies": ["fusion", "energy"],
}

def match_companies_to_opportunity(tech_areas):
    """Match companies based on overlapping tech areas."""
    matched = []
    tech_areas_lower = [t.lower() for t in tech_areas]

    for company, areas in COMPANY_TECH_AREAS.items():
        areas_lower = [a.lower() for a in areas]
        overlap = len(set(tech_areas_lower) & set(areas_lower))
        if overlap > 0:
            matched.append((company, overlap))

    # Sort by overlap count, return top 5
    matched.sort(key=lambda x: -x[1])
    return [m[0] for m in matched[:5]]


def fetch_sbir_opportunities():
    """Fetch SBIR/STTR opportunities from SBIR.gov API."""
    opportunities = []

    # SBIR.gov has a public API
    url = "https://www.sbir.gov/api/solicitations.json"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()

            for item in data.get('results', [])[:20]:  # Top 20
                opp = {
                    "id": f"SBIR-{item.get('solicitation_id', '')}",
                    "title": item.get('solicitation_title', 'SBIR Opportunity'),
                    "agency": item.get('agency', 'Multiple'),
                    "type": "SBIR/STTR",
                    "deadline": item.get('close_date', 'Rolling'),
                    "value": "$50K-$2M",  # Typical SBIR range
                    "priority": "High",
                    "description": item.get('abstract', '')[:500],
                    "techAreas": item.get('topics', [])[:5] if isinstance(item.get('topics'), list) else [],
                    "relevantCompanies": [],
                    "source": f"https://www.sbir.gov/solicitation/{item.get('solicitation_id', '')}",
                    "posted": item.get('open_date', datetime.now().strftime('%Y-%m-%d'))
                }

                # Auto-match companies
                if opp['techAreas']:
                    opp['relevantCompanies'] = match_companies_to_opportunity(opp['techAreas'])

                opportunities.append(opp)

    except Exception as e:
        print(f"Error fetching SBIR data: {e}")

    return opportunities


def fetch_sam_opportunities():
    """
    Fetch opportunities from SAM.gov.
    Note: Full API requires registration. Using public search endpoint.
    """
    opportunities = []

    # SAM.gov public opportunities endpoint (limited)
    # For full access, register at SAM.gov and use API key
    keywords = ["defense", "autonomous", "nuclear", "space", "AI", "robotics"]

    for keyword in keywords[:3]:  # Limit queries
        url = f"https://api.sam.gov/opportunities/v2/search"
        params = {
            "api_key": "DEMO_KEY",  # Replace with actual key for production
            "keywords": keyword,
            "postedFrom": (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y"),
            "limit": 10
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('opportunitiesData', []):
                    opp = {
                        "id": item.get('noticeId', f"SAM-{keyword}"),
                        "title": item.get('title', 'Government Opportunity'),
                        "agency": item.get('department', item.get('fullParentPathName', 'Federal')),
                        "type": item.get('type', 'RFP'),
                        "deadline": item.get('responseDeadLine', 'TBD'),
                        "value": item.get('award', {}).get('awardNumber', 'TBD'),
                        "priority": "Medium",
                        "description": item.get('description', '')[:500],
                        "techAreas": [keyword],
                        "relevantCompanies": match_companies_to_opportunity([keyword]),
                        "source": item.get('uiLink', 'https://sam.gov'),
                        "posted": item.get('postedDate', datetime.now().strftime('%Y-%m-%d'))
                    }
                    opportunities.append(opp)
        except Exception as e:
            print(f"Error fetching SAM.gov ({keyword}): {e}")

    return opportunities


def load_existing_opportunities():
    """Load hand-curated opportunities from data.js."""
    opportunities = []

    # Read existing GOV_DEMAND_TRACKER from data.js
    data_path = Path(__file__).parent.parent / "data.js"
    if data_path.exists():
        content = data_path.read_text()

        # Extract GOV_DEMAND_TRACKER array
        match = re.search(r'const GOV_DEMAND_TRACKER = \[(.*?)\];', content, re.DOTALL)
        if match:
            # Parse existing opportunities (simplified)
            # In production, use proper JS parsing
            pass

    return opportunities


def generate_js_output(opportunities):
    """Generate JavaScript file with opportunities data."""

    # De-duplicate by ID
    seen_ids = set()
    unique_opps = []
    for opp in opportunities:
        if opp['id'] not in seen_ids:
            seen_ids.add(opp['id'])
            unique_opps.append(opp)

    js_output = f"""// Auto-generated government opportunities data
// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
// Total opportunities: {len(unique_opps)}

const GOV_OPPORTUNITIES_AUTO = {json.dumps(unique_opps, indent=2)};

const GOV_OPPORTUNITIES_STATS = {{
  totalOpportunities: {len(unique_opps)},
  byAgency: {json.dumps(dict())},
  lastUpdated: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
}};
"""

    output_path = Path(__file__).parent.parent / "data" / "gov_opportunities_auto.js"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(js_output)

    print(f"Generated: {output_path}")
    return unique_opps


def main():
    print("=" * 60)
    print("Government Opportunities Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_opportunities = []

    # Fetch from various sources
    print("\nFetching SBIR opportunities...")
    sbir_opps = fetch_sbir_opportunities()
    print(f"  Found {len(sbir_opps)} SBIR opportunities")
    all_opportunities.extend(sbir_opps)

    # Note: SAM.gov requires API key for production use
    # print("\nFetching SAM.gov opportunities...")
    # sam_opps = fetch_sam_opportunities()
    # print(f"  Found {len(sam_opps)} SAM.gov opportunities")
    # all_opportunities.extend(sam_opps)

    # Generate output
    print("\nGenerating output...")
    unique_opps = generate_js_output(all_opportunities)

    print(f"\n{'=' * 60}")
    print(f"Total unique opportunities: {len(unique_opps)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
