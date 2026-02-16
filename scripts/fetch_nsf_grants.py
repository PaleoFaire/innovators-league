#!/usr/bin/env python3
"""
NSF Awards API Fetcher
Tracks NSF research grants in AI, robotics, quantum, and other tech areas.
Uses the free NSF Awards API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# NSF program areas to track
NSF_PROGRAMS = {
    "Computing and Communication Foundations": ["AI", "machine learning", "robotics", "quantum"],
    "Information and Intelligent Systems": ["artificial intelligence", "data science", "human-robot"],
    "Computer and Network Systems": ["autonomous", "edge computing", "5G", "networking"],
    "Electrical, Communications and Cyber Systems": ["sensors", "signal processing", "communications"],
    "Civil, Mechanical and Manufacturing Innovation": ["manufacturing", "3D printing", "materials"],
    "Chemical, Bioengineering, Environmental, and Transport Systems": ["biotech", "synthetic biology"],
    "Physics": ["quantum", "plasma", "fusion", "particle"],
    "Materials Research": ["advanced materials", "semiconductors", "nanomaterials"],
    "Astronomy": ["space", "telescope", "exoplanet"],
}

# Keywords for our tracked sectors
SECTOR_KEYWORDS = {
    "defense": ["autonomous", "drone", "uav", "swarm", "radar", "lidar", "sensor"],
    "space": ["satellite", "spacecraft", "orbital", "rocket", "lunar", "mars", "asteroid"],
    "nuclear": ["nuclear", "fission", "fusion", "plasma", "tokamak"],
    "robotics": ["robot", "humanoid", "manipulation", "locomotion", "actuator"],
    "quantum": ["quantum", "qubit", "entanglement", "superconducting"],
    "ai": ["artificial intelligence", "machine learning", "deep learning", "neural network", "transformer"],
    "biotech": ["synthetic biology", "gene", "crispr", "protein", "genomic"],
}

NSF_API_BASE = "https://api.nsf.gov/services/v1/awards.json"

def fetch_recent_awards(keyword, days=90, max_results=50):
    """Fetch recent NSF awards matching a keyword."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%m/%d/%Y")

    params = {
        "keyword": keyword,
        "dateStart": cutoff,
        "printFields": "id,agency,awardeeCity,awardeeStateCode,awardeeName,awardeeZipCode,date,startDate,expDate,estimatedTotalAmt,fundsObligatedAmt,title,abstractText,piFirstName,piLastName,piEmail",
        "offset": 1,
        "rpp": max_results
    }

    try:
        response = requests.get(NSF_API_BASE, params=params, timeout=30)
        if response.status_code != 200:
            return []

        data = response.json()
        awards = data.get("response", {}).get("award", [])

        results = []
        for award in awards:
            results.append({
                "id": award.get("id", ""),
                "title": award.get("title", ""),
                "abstract": (award.get("abstractText", "") or "")[:500],
                "amount": int(award.get("estimatedTotalAmt", 0) or 0),
                "startDate": award.get("startDate", ""),
                "endDate": award.get("expDate", ""),
                "awardee": award.get("awardeeName", ""),
                "city": award.get("awardeeCity", ""),
                "state": award.get("awardeeStateCode", ""),
                "pi": f"{award.get('piFirstName', '')} {award.get('piLastName', '')}".strip(),
                "piEmail": award.get("piEmail", ""),
                "date": award.get("date", ""),
            })

        return results

    except Exception as e:
        print(f"  Error: {e}")
        return []

def fetch_all_awards():
    """Fetch awards for all tracked keywords."""
    all_awards = []
    seen_ids = set()

    # Collect unique keywords from all sectors
    all_keywords = set()
    for keywords in SECTOR_KEYWORDS.values():
        all_keywords.update(keywords)

    for keyword in list(all_keywords)[:15]:  # Limit to avoid too many requests
        print(f"Fetching awards for: {keyword}")
        awards = fetch_recent_awards(keyword, days=90, max_results=25)

        # Deduplicate
        new_awards = [a for a in awards if a["id"] not in seen_ids]
        for a in new_awards:
            seen_ids.add(a["id"])

        if new_awards:
            print(f"  Found {len(new_awards)} unique awards")
            all_awards.extend(new_awards)
        else:
            print(f"  No new awards")

        time.sleep(0.5)  # Rate limiting

    return all_awards

def categorize_by_sector(awards):
    """Categorize awards by sector."""
    for award in awards:
        text = (award.get("title", "") + " " + award.get("abstract", "")).lower()

        award["sectors"] = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw.lower() in text for kw in keywords):
                award["sectors"].append(sector)

    return awards

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(awards):
    """Generate JavaScript code snippet for NSF_AWARDS."""
    # Sort by amount descending
    awards.sort(key=lambda x: x.get("amount", 0), reverse=True)

    js_output = "// Auto-updated NSF research awards\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const NSF_AWARDS = [\n"

    for a in awards[:40]:
        title = a.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        awardee = a.get("awardee", "").replace('"', '\\"')[:50]
        sectors = ", ".join(a.get("sectors", []))

        js_output += f'  {{ id: "{a["id"]}", title: "{title}", '
        js_output += f'amount: {a["amount"]}, awardee: "{awardee}", '
        js_output += f'state: "{a["state"]}", pi: "{a["pi"]}", '
        js_output += f'sectors: "{sectors}", startDate: "{a["startDate"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "nsf_awards_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("NSF Research Awards Fetcher")
    print("=" * 60)
    print(f"Tracking {len(SECTOR_KEYWORDS)} sectors")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all awards
    awards = fetch_all_awards()
    print(f"\nTotal unique awards found: {len(awards)}")

    # Categorize by sector
    categorized = categorize_by_sector(awards)

    # Calculate total funding
    total_funding = sum(a.get("amount", 0) for a in awards)
    print(f"Total funding tracked: ${total_funding:,.0f}")

    # Save data
    save_to_json(awards, "nsf_awards_raw.json")

    # Generate JS snippet
    generate_js_snippet(categorized)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary by sector
    if awards:
        print("\nAwards by sector:")
        sector_counts = {}
        sector_amounts = {}
        for a in categorized:
            for s in a.get("sectors", []):
                sector_counts[s] = sector_counts.get(s, 0) + 1
                sector_amounts[s] = sector_amounts.get(s, 0) + a.get("amount", 0)
        for sector in sorted(sector_counts.keys()):
            print(f"  {sector}: {sector_counts[sector]} awards (${sector_amounts[sector]:,.0f})")

if __name__ == "__main__":
    main()
