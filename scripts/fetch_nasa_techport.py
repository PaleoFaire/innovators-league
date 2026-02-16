#!/usr/bin/env python3
"""
NASA TechPort API Fetcher
Tracks NASA technology projects, partnerships, and SBIR contracts.
Uses the free NASA TechPort API - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Keywords to search for our tracked sectors
SEARCH_KEYWORDS = [
    "autonomous", "robotics", "artificial intelligence", "machine learning",
    "nuclear thermal", "nuclear propulsion", "small modular reactor",
    "satellite", "launch vehicle", "spacecraft", "lunar", "mars",
    "quantum computing", "quantum sensing",
    "hypersonic", "reusable rocket",
    "additive manufacturing", "3d printing",
    "directed energy", "lidar", "radar"
]

# Companies we track that might have NASA partnerships
TRACKED_COMPANIES = [
    "SpaceX", "Rocket Lab", "Relativity Space", "Astra", "Firefly",
    "Blue Origin", "Sierra Space", "Axiom Space", "Astrobotic",
    "Intuitive Machines", "Lockheed Martin", "Northrop Grumman",
    "Boeing", "Maxar", "Planet Labs", "Spire Global",
    "Anduril", "Shield AI", "Figure", "Apptronik",
    "Oklo", "NuScale", "Kairos Power", "Radiant",
    "IBM Quantum", "IonQ", "Rigetti", "D-Wave"
]

NASA_TECHPORT_BASE = "https://techport.nasa.gov/api"

def fetch_recent_projects(days=180):
    """Fetch recently updated NASA technology projects."""
    url = f"{NASA_TECHPORT_BASE}/projects"

    # Get project IDs updated in the last N days
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        # First get list of all project IDs
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Error fetching project list: {response.status_code}")
            return []

        project_ids = response.json().get("projects", [])
        print(f"Found {len(project_ids)} total projects")

        # Fetch details for recent projects (sample to avoid rate limits)
        projects = []
        for pid in project_ids[:100]:  # Sample first 100
            project_url = f"{NASA_TECHPORT_BASE}/projects/{pid}"
            try:
                resp = requests.get(project_url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json().get("project", {})

                    # Check if recently updated
                    last_updated = data.get("lastUpdated", "")
                    if last_updated and last_updated >= cutoff:
                        projects.append({
                            "id": pid,
                            "title": data.get("title", ""),
                            "description": (data.get("description", "") or "")[:500],
                            "status": data.get("status", ""),
                            "startDate": data.get("startDateString", ""),
                            "endDate": data.get("endDateString", ""),
                            "lastUpdated": last_updated,
                            "center": data.get("leadOrganization", {}).get("organizationName", ""),
                            "technologyArea": data.get("primaryTaxonomyNodes", [{}])[0].get("taxonomyNodeName", "") if data.get("primaryTaxonomyNodes") else "",
                            "partners": [p.get("organizationName", "") for p in data.get("supportingOrganizations", [])],
                            "website": data.get("website", ""),
                        })
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                continue

        return projects

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

def fetch_sbir_awards():
    """Fetch NASA SBIR/STTR awards (if available via API)."""
    # Note: SBIR awards are also available via sbir.gov
    # This is a placeholder for future enhancement
    return []

def filter_relevant_projects(projects):
    """Filter projects relevant to our tracked sectors."""
    relevant = []

    for project in projects:
        title_desc = (project.get("title", "") + " " + project.get("description", "")).lower()
        partners = " ".join(project.get("partners", [])).lower()

        # Check for keyword matches
        keyword_match = any(kw.lower() in title_desc for kw in SEARCH_KEYWORDS)

        # Check for company matches
        company_match = any(company.lower() in partners for company in TRACKED_COMPANIES)

        if keyword_match or company_match:
            relevant.append(project)

    return relevant

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(projects):
    """Generate JavaScript code snippet for NASA_PROJECTS."""
    # Sort by last updated descending
    projects.sort(key=lambda x: x.get("lastUpdated", ""), reverse=True)

    js_output = "// Auto-updated NASA TechPort projects\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const NASA_PROJECTS = [\n"

    for p in projects[:30]:
        title = p.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        desc = p.get("description", "").replace('"', '\\"').replace('\n', ' ')[:150]
        partners = ", ".join(p.get("partners", [])[:3])
        js_output += f'  {{ id: {p["id"]}, title: "{title}", '
        js_output += f'status: "{p.get("status", "")}", center: "{p.get("center", "")}", '
        js_output += f'techArea: "{p.get("technologyArea", "")}", lastUpdated: "{p.get("lastUpdated", "")}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "nasa_projects_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("NASA TechPort Projects Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch recent projects
    print("\nFetching recent NASA projects...")
    projects = fetch_recent_projects(days=180)
    print(f"Found {len(projects)} recently updated projects")

    # Filter to relevant projects
    relevant = filter_relevant_projects(projects)
    print(f"Relevant to our sectors: {len(relevant)}")

    # Save data
    save_to_json(projects, "nasa_projects_raw.json")
    save_to_json(relevant, "nasa_projects_filtered.json")

    # Generate JS snippet
    generate_js_snippet(relevant)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary
    if relevant:
        print("\nRecent Relevant NASA Projects:")
        for p in relevant[:5]:
            print(f"  {p['lastUpdated'][:10]} | {p['title'][:50]}...")

if __name__ == "__main__":
    main()
