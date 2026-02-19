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

def fetch_with_retry(url, headers=None, params=None, max_retries=3, timeout=30):
    """Fetch URL with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
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



def fetch_recent_projects(days=365):
    """Fetch recently updated NASA technology projects."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        # Use the updatedSince parameter to filter to recently updated projects
        url = f"{NASA_TECHPORT_BASE}/projects"
        params = {"updatedSince": cutoff}
        headers = {"Accept": "application/json"}

        print(f"Fetching projects updated since {cutoff}...")
        response = fetch_with_retry(url, headers=headers, params=params, timeout=60)

        if response is None or response.status_code != 200:
            print(f"Error fetching project list, trying fallback...")
            # Fallback: try without filter
            response = fetch_with_retry(url, headers=headers, timeout=60)
            if response is None or response.status_code != 200:
                print(f"Fallback also failed")
                return []

        data = response.json()

        # Handle different response formats
        project_ids = []
        if isinstance(data, dict):
            project_ids = data.get("projects", data.get("project", []))
            if isinstance(project_ids, dict):
                project_ids = project_ids.get("id", [])
        elif isinstance(data, list):
            project_ids = data

        # Flatten if nested
        if project_ids and isinstance(project_ids[0], dict):
            project_ids = [p.get("projectId", p.get("id", "")) for p in project_ids]

        print(f"Found {len(project_ids)} project IDs")

        # Fetch details for recent projects (sample to avoid rate limits)
        projects = []
        for pid in project_ids[:150]:  # Sample first 150
            if not pid:
                continue
            project_url = f"{NASA_TECHPORT_BASE}/projects/{pid}"
            try:
                resp = fetch_with_retry(project_url, headers=headers)
                if resp is not None and resp.status_code == 200:
                    resp_data = resp.json()
                    proj = resp_data.get("project", resp_data)
                    if isinstance(proj, dict):
                        title = proj.get("title", "")
                        if title:
                            projects.append({
                                "id": pid,
                                "title": title,
                                "description": (proj.get("description", "") or "")[:500],
                                "status": proj.get("statusDescription", proj.get("status", "")),
                                "startDate": proj.get("startDateString", proj.get("startDate", "")),
                                "endDate": proj.get("endDateString", proj.get("endDate", "")),
                                "lastUpdated": proj.get("lastUpdated", ""),
                                "center": (proj.get("leadOrganization") or {}).get("organizationName", ""),
                                "technologyArea": proj.get("primaryTaxonomyNodes", [{}])[0].get("taxonomyNodeName", "") if proj.get("primaryTaxonomyNodes") else "",
                                "partners": [p.get("organizationName", "") for p in (proj.get("supportingOrganizations") or [])],
                                "website": proj.get("website", ""),
                            })
                time.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"  Error fetching project {pid}: {e}")
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
