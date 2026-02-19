#!/usr/bin/env python3
"""
SBIR/STTR Topics Fetcher for The Innovators League
Fetches active SBIR and STTR topics from the SBIR.gov API.
Uses the free SBIR.gov API - no key required.
Falls back to curated seed data if API is unavailable.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

DATA_DIR = Path(__file__).parent.parent / "data"
SBIR_API = "https://www.sbir.gov/api/solicitations.json"

# Agencies we care about
TRACKED_AGENCIES = [
    "Department of Defense",
    "Department of Energy",
    "National Aeronautics and Space Administration",
    "National Science Foundation",
    "Department of Homeland Security",
    "Department of Commerce",
]

# Keywords relevant to our frontier tech sectors
SECTOR_KEYWORDS = {
    "defense": ["defense", "military", "weapon", "munitions", "warfighter", "tactical", "C4ISR"],
    "space": ["space", "satellite", "launch", "orbital", "payload", "LEO", "cislunar"],
    "nuclear": ["nuclear", "reactor", "fission", "fusion", "HALEU", "SMR", "isotope"],
    "ai": ["artificial intelligence", "machine learning", "deep learning", "neural network", "autonomy", "computer vision"],
    "quantum": ["quantum", "qubit", "entanglement", "quantum computing", "quantum sensing"],
    "biotech": ["biotech", "synthetic biology", "gene", "cell therapy", "biomanufacturing", "protein"],
    "cyber": ["cybersecurity", "cyber", "encryption", "zero trust", "network security"],
    "robotics": ["robot", "unmanned", "drone", "UAS", "autonomous vehicle", "manipulation"],
    "advanced_materials": ["materials", "composite", "metamaterial", "additive manufacturing", "3D printing"],
    "energy": ["energy storage", "battery", "solar", "hydrogen", "grid", "microreactor"],
}

# Company relevance mapping
COMPANY_RELEVANCE = {
    "defense": ["Anduril Industries", "Shield AI", "Skydio", "Palantir", "L3Harris", "Saronic"],
    "space": ["SpaceX", "Rocket Lab", "Relativity Space", "Firefly Aerospace", "Astra"],
    "nuclear": ["Oklo", "Kairos Power", "TerraPower", "X-energy", "NuScale Power"],
    "ai": ["Scale AI", "Anthropic", "OpenAI", "Palantir", "Databricks"],
    "quantum": ["IonQ", "Rigetti Computing", "PsiQuantum", "Atom Computing"],
    "biotech": ["Ginkgo Bioworks", "Recursion", "Mammoth Biosciences"],
    "robotics": ["Figure AI", "Apptronik", "Boston Dynamics", "Saronic"],
    "energy": ["Commonwealth Fusion", "Form Energy", "Malta Inc"],
}


def tag_sectors(text):
    """Tag a topic with relevant sectors."""
    text_lower = text.lower()
    tags = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            tags.append(sector)
    return tags or ["general"]


def get_relevant_companies(sectors):
    """Get relevant companies for a set of sector tags."""
    companies = set()
    for sector in sectors:
        for c in COMPANY_RELEVANCE.get(sector, []):
            companies.add(c)
    return sorted(companies)


def fetch_sbir_topics():
    """Fetch active SBIR/STTR topics from SBIR.gov."""
    topics = []

    try:
        params = {
            "keyword": "",
            "agency": "",
            "open": "1",  # Only open topics
        }

        response = requests.get(SBIR_API, params=params, timeout=30)
        if response.status_code != 200:
            print(f"SBIR API returned {response.status_code}")
            return []

        data = response.json()

        for item in data[:100]:  # Limit to 100 most recent
            topic_text = f"{item.get('solicitation_title', '')} {item.get('solicitation_agency', '')}"
            sectors = tag_sectors(topic_text)

            # Only include topics relevant to our sectors
            if sectors == ["general"]:
                continue

            topics.append({
                "id": item.get("solicitation_id", ""),
                "title": item.get("solicitation_title", ""),
                "agency": item.get("solicitation_agency", ""),
                "type": item.get("solicitation_type", "SBIR"),
                "phase": item.get("phase", ""),
                "openDate": item.get("open_date", ""),
                "closeDate": item.get("close_date", ""),
                "url": item.get("solicitation_url", ""),
                "sectors": sectors,
                "relevantCompanies": get_relevant_companies(sectors),
            })

        return topics

    except Exception as e:
        print(f"Error fetching SBIR topics: {e}")
        return []


def generate_seed_data():
    """Curated seed data for known SBIR/STTR topics."""
    return [
        {
            "id": "DOD-SBIR-2026-001",
            "title": "AI-Enabled Electronic Warfare Systems",
            "agency": "Department of Defense",
            "type": "SBIR",
            "phase": "Phase I",
            "openDate": "2025-11-01",
            "closeDate": "2026-03-15",
            "award": "$250K",
            "sectors": ["defense", "ai"],
            "relevantCompanies": ["Anduril Industries", "Shield AI", "Palantir"],
            "description": "Develop AI/ML approaches for real-time electronic warfare signal classification and response.",
        },
        {
            "id": "NASA-STTR-2026-002",
            "title": "Advanced In-Space Propulsion Technologies",
            "agency": "National Aeronautics and Space Administration",
            "type": "STTR",
            "phase": "Phase I",
            "openDate": "2025-12-01",
            "closeDate": "2026-04-01",
            "award": "$150K",
            "sectors": ["space"],
            "relevantCompanies": ["SpaceX", "Rocket Lab", "Relativity Space", "Firefly Aerospace"],
            "description": "Novel propulsion concepts for cislunar operations and deep space missions.",
        },
        {
            "id": "DOE-SBIR-2026-003",
            "title": "Advanced Nuclear Fuel Manufacturing",
            "agency": "Department of Energy",
            "type": "SBIR",
            "phase": "Phase II",
            "openDate": "2025-10-15",
            "closeDate": "2026-02-28",
            "award": "$1.5M",
            "sectors": ["nuclear", "energy"],
            "relevantCompanies": ["Oklo", "Kairos Power", "TerraPower", "X-energy"],
            "description": "Innovative manufacturing processes for HALEU and advanced nuclear fuels.",
        },
        {
            "id": "DOD-SBIR-2026-004",
            "title": "Autonomous Swarm Systems for Maritime Operations",
            "agency": "Department of Defense",
            "type": "SBIR",
            "phase": "Phase I",
            "openDate": "2026-01-15",
            "closeDate": "2026-05-01",
            "award": "$250K",
            "sectors": ["defense", "robotics", "ai"],
            "relevantCompanies": ["Saronic", "Shield AI", "Anduril Industries"],
            "description": "Develop coordinated autonomous systems for naval surface and undersea operations.",
        },
        {
            "id": "NSF-SBIR-2026-005",
            "title": "Quantum Error Correction Hardware",
            "agency": "National Science Foundation",
            "type": "SBIR",
            "phase": "Phase I",
            "openDate": "2025-11-15",
            "closeDate": "2026-03-30",
            "award": "$275K",
            "sectors": ["quantum"],
            "relevantCompanies": ["IonQ", "Rigetti Computing", "PsiQuantum", "Atom Computing"],
            "description": "Hardware-level quantum error correction approaches for fault-tolerant quantum computing.",
        },
        {
            "id": "DOD-SBIR-2026-006",
            "title": "Counter-UAS Detection and Neutralization",
            "agency": "Department of Defense",
            "type": "SBIR",
            "phase": "Phase II",
            "openDate": "2025-09-01",
            "closeDate": "2026-01-31",
            "award": "$1.75M",
            "sectors": ["defense", "robotics"],
            "relevantCompanies": ["Anduril Industries", "Shield AI", "Skydio"],
            "description": "Scalable C-UAS solutions for base defense and expeditionary operations.",
        },
        {
            "id": "DOE-STTR-2026-007",
            "title": "Compact Fusion Pilot Plant Technologies",
            "agency": "Department of Energy",
            "type": "STTR",
            "phase": "Phase I",
            "openDate": "2026-01-01",
            "closeDate": "2026-04-15",
            "award": "$200K",
            "sectors": ["nuclear", "energy"],
            "relevantCompanies": ["Commonwealth Fusion", "TAE Technologies"],
            "description": "Component technologies for compact fusion pilot plants targeting net energy by 2030.",
        },
        {
            "id": "DHS-SBIR-2026-008",
            "title": "AI-Powered Cybersecurity for Critical Infrastructure",
            "agency": "Department of Homeland Security",
            "type": "SBIR",
            "phase": "Phase I",
            "openDate": "2025-12-15",
            "closeDate": "2026-03-31",
            "award": "$200K",
            "sectors": ["cyber", "ai"],
            "relevantCompanies": ["Palantir", "Scale AI"],
            "description": "Machine learning approaches for detecting and responding to cyber threats targeting energy and water infrastructure.",
        },
        {
            "id": "NASA-SBIR-2026-009",
            "title": "Synthetic Biology for Space Life Support",
            "agency": "National Aeronautics and Space Administration",
            "type": "SBIR",
            "phase": "Phase I",
            "openDate": "2026-02-01",
            "closeDate": "2026-05-15",
            "award": "$150K",
            "sectors": ["biotech", "space"],
            "relevantCompanies": ["Ginkgo Bioworks"],
            "description": "Engineered biological systems for air revitalization and waste processing in long-duration space missions.",
        },
        {
            "id": "DOD-SBIR-2026-010",
            "title": "Hypersonic Vehicle Materials and Thermal Protection",
            "agency": "Department of Defense",
            "type": "SBIR",
            "phase": "Phase II",
            "openDate": "2025-10-01",
            "closeDate": "2026-02-15",
            "award": "$1.5M",
            "sectors": ["defense", "advanced_materials"],
            "relevantCompanies": ["Hermeus", "Ursa Major"],
            "description": "Advanced materials for thermal protection systems on hypersonic flight vehicles.",
        },
    ]


def main():
    print("=" * 60)
    print("SBIR/STTR Topics Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    topics = fetch_sbir_topics()

    if not topics:
        print("API fetch returned 0 results — using curated seed data")
        topics = generate_seed_data()
    else:
        print(f"Fetched {len(topics)} relevant topics from SBIR.gov")

    # Sort by close date (soonest deadline first)
    topics.sort(key=lambda x: x.get("closeDate", "9999"), reverse=False)

    # Save as JS module
    output_path = DATA_DIR / "sbir_topics_auto.js"
    js_content = f"// Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    js_content += f"const SBIR_TOPICS_AUTO = {json.dumps(topics, indent=2)};\n"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(js_content)

    print(f"Saved {len(topics)} topics to {output_path}")

    # Also save raw JSON
    json_path = DATA_DIR / "sbir_topics_auto.json"
    with open(json_path, "w") as f:
        json.dump(topics, f, indent=2)

    # Summary
    if topics:
        print("\nTop topics by deadline:")
        for t in topics[:5]:
            print(f"  [{t.get('type', 'SBIR')}] {t['title'][:60]}... | Close: {t.get('closeDate', 'N/A')}")

    print("=" * 60)


if __name__ == "__main__":
    main()
