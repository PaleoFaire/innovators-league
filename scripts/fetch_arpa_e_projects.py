#!/usr/bin/env python3
"""
ARPA-E Project Fetcher for The Innovators League
Tracks early-stage energy/climate tech innovators funded by ARPA-E.
~1,610 projects representing $2.6B+ in funding for frontier energy technologies.
These companies are often 3-7 years ahead of mainstream recognition.

API: https://arpa-e.energy.gov/JSONAPI/custom/index/project
Free, no API key required.
"""

import json
import re
import requests
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"
ARPA_E_API = "https://arpa-e.energy.gov/JSONAPI/custom/index/project"


def extract_companies_from_datajs():
    """Extract company names from data.js for matching."""
    if not DATA_JS.exists():
        return set()
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for match in re.finditer(r'name:\s*["\']([^"\']+)["\']', content):
        names.add(match.group(1).lower().strip())
    return names


def parse_award_amount(award_str):
    """Parse award string like '$3,949,109' to integer."""
    if not award_str:
        return 0
    try:
        return int(award_str.replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def fetch_all_projects():
    """Fetch all ARPA-E projects with pagination."""
    all_projects = []
    url = ARPA_E_API
    page_num = 0
    max_pages = 40

    while url and page_num < max_pages:
        try:
            resp = requests.get(url, timeout=60,
                               headers={"User-Agent": "InnovatorsLeague/1.0",
                                        "Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()

            projects = data.get("data", [])
            if not projects:
                break

            all_projects.extend(projects)
            total = data.get("meta", {}).get("count", {}).get("count", 0)
            print(f"  Page {page_num + 1}: {len(projects)} projects (total so far: {len(all_projects)}/{total})")

            # Use the actual next URL from the API response
            links = data.get("links", {})
            next_link = links.get("next", {})
            if isinstance(next_link, dict):
                url = next_link.get("href", "")
            elif isinstance(next_link, str):
                url = next_link
            else:
                url = ""

            if not url or len(projects) < 50:
                break

            page_num += 1
            time.sleep(0.5)  # Rate limiting

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching page {page_num}: {e}")
            break
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Parse error on page {page_num}: {e}")
            break

    return all_projects


def main():
    print("=" * 60)
    print("ARPA-E Project Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    known_companies = extract_companies_from_datajs()
    print(f"Loaded {len(known_companies)} company names from data.js\n")

    print("Fetching all ARPA-E projects...")
    raw_projects = fetch_all_projects()
    print(f"\nTotal raw projects fetched: {len(raw_projects)}")

    all_projects = []

    for proj in raw_projects:
        attrs = proj.get("attributes", {})
        fields = attrs.get("fields", {})

        title = fields.get("title", "") or attrs.get("title", "")
        award_str = fields.get("award", "")
        award_amount = parse_award_amount(award_str)
        status = fields.get("status", "")
        location = fields.get("location", "")
        state = fields.get("state", "")
        release_date = fields.get("release_date", "")

        # Extract organization info
        orgs = fields.get("organization", []) or []
        org_name = ""
        org_type = ""
        org_website = ""
        if orgs:
            org_fields = orgs[0].get("fields", {}) or {}
            org_attrs = orgs[0].get("attributes", {}) or {}
            org_name = org_attrs.get("title", "") or org_fields.get("title", "")
            org_type_raw = org_fields.get("type", "")
            if isinstance(org_type_raw, list) and org_type_raw:
                org_type = org_type_raw[0].get("name", "") if isinstance(org_type_raw[0], dict) else str(org_type_raw[0])
            elif isinstance(org_type_raw, str):
                org_type = org_type_raw
            else:
                org_type = ""
            org_website = org_fields.get("website", "")

        # Extract program info
        programs = fields.get("related_programs", []) or []
        program_name = ""
        program_acronym = ""
        if programs:
            prog_attrs = programs[0].get("attributes", {}) or {}
            prog_fields = programs[0].get("fields", {}) or {}
            program_name = prog_attrs.get("title", "")
            program_acronym = prog_fields.get("acronym", "")

        # Extract technology areas
        techs = fields.get("related_technologies", []) or []
        tech_areas = [t.get("name", "") for t in techs if t.get("name")]

        # Check if company is known
        org_lower = org_name.lower()
        is_known = any(known in org_lower or org_lower in known
                      for known in known_companies if len(known) > 3) if org_name else False

        # Only include projects with real data
        if not title:
            continue

        entry = {
            "title": title,
            "organization": org_name,
            "orgType": org_type,
            "orgWebsite": org_website,
            "status": status,
            "location": location,
            "state": state,
            "awardAmount": award_amount,
            "awardFormatted": award_str,
            "releaseDate": release_date,
            "programName": program_name,
            "programAcronym": program_acronym,
            "technologyAreas": tech_areas,
            "isKnownCompany": is_known,
            "isPrivateCompany": org_type.lower() in ["small business", "private company", "company",
                                                       "startup", "for-profit"],
        }
        all_projects.append(entry)

    # Sort by award amount descending
    all_projects.sort(key=lambda p: -(p.get("awardAmount", 0) or 0))

    # Stats
    known_projects = [p for p in all_projects if p.get("isKnownCompany")]
    private_projects = [p for p in all_projects if p.get("isPrivateCompany")]
    active_projects = [p for p in all_projects if p.get("status") == "Active"]
    total_funding = sum(p.get("awardAmount", 0) for p in all_projects)

    # Unique organizations
    unique_orgs = set(p.get("organization", "") for p in all_projects if p.get("organization"))

    print(f"\nProcessed projects: {len(all_projects)}")
    print(f"  Active: {len(active_projects)}")
    print(f"  Private companies: {len(private_projects)}")
    print(f"  Known TIL companies: {len(known_projects)}")
    print(f"  Unique organizations: {len(unique_orgs)}")
    print(f"  Total funding: ${total_funding:,.0f}")

    # Save raw JSON
    raw_path = DATA_DIR / "arpa_e_projects_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_projects, f, indent=2)
    print(f"\nSaved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated ARPA-E project data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total projects: {len(all_projects)} | Active: {len(active_projects)}",
        f"// Private companies: {len(private_projects)} | Known TIL: {len(known_projects)}",
        f"// Unique organizations: {len(unique_orgs)} | Total funding: ${total_funding:,.0f}",
        "const ARPA_E_PROJECTS_AUTO = [",
    ]

    for proj in all_projects[:500]:  # Cap at 500
        title_esc = proj["title"][:120].replace('"', '\\"').replace("\n", " ")
        org_esc = proj["organization"].replace('"', '\\"')
        techs_str = json.dumps(proj["technologyAreas"][:5])
        js_lines.append("  {")
        js_lines.append(f'    title: "{title_esc}",')
        js_lines.append(f'    organization: "{org_esc}",')
        js_lines.append(f'    orgType: "{proj["orgType"]}",')
        js_lines.append(f'    status: "{proj["status"]}",')
        js_lines.append(f'    state: "{proj["state"]}",')
        js_lines.append(f'    awardAmount: {proj["awardAmount"]},')
        js_lines.append(f'    awardFormatted: "{proj["awardFormatted"]}",')
        js_lines.append(f'    programAcronym: "{proj["programAcronym"]}",')
        js_lines.append(f'    technologyAreas: {techs_str},')
        js_lines.append(f'    isKnownCompany: {"true" if proj["isKnownCompany"] else "false"},')
        js_lines.append(f'    isPrivateCompany: {"true" if proj["isPrivateCompany"] else "false"},')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "arpa_e_projects_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Top programs
    programs = {}
    for p in all_projects:
        prog = p.get("programAcronym") or p.get("programName") or "Unknown"
        programs[prog] = programs.get(prog, 0) + 1
    print("\nTop ARPA-E Programs:")
    for prog, count in sorted(programs.items(), key=lambda x: -x[1])[:10]:
        print(f"  {prog}: {count} projects")

    print("=" * 60)


if __name__ == "__main__":
    main()
