#!/usr/bin/env python3
"""
SBIR/STTR Government Grant Awards Fetcher
Identifies frontier tech companies receiving early-stage government funding.
SBIR awards are the strongest early signal — companies appear here 2-5 years
before they show up on Crunchbase or PitchBook.

API: https://api.www.sbir.gov/public/api/awards
Free, no API key required.
"""

import json
import os
import re
import requests
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"
SBIR_API = "https://api.www.sbir.gov/public/api/awards"

# Agencies most relevant to frontier tech
AGENCIES = ["DOD", "DOE", "NASA", "NSF", "HHS"]

# Keywords for frontier tech searches
SEARCH_KEYWORDS = [
    "artificial intelligence machine learning",
    "autonomous systems robotics",
    "hypersonic missile defense",
    "quantum computing",
    "nuclear fusion fission reactor",
    "satellite space launch",
    "gene therapy CRISPR",
    "advanced manufacturing 3D printing",
    "battery energy storage",
    "cybersecurity zero trust",
    "drone unmanned aerial",
    "semiconductor chip fabrication",
    "directed energy laser",
    "synthetic biology",
    "carbon capture climate",
]


def extract_companies_from_datajs():
    """Extract company names from data.js for matching."""
    if not DATA_JS.exists():
        return set()
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")
    # Extract company names from the COMPANIES array
    names = set()
    for match in re.finditer(r'name:\s*["\']([^"\']+)["\']', content):
        names.add(match.group(1).lower().strip())
    return names


def fetch_sbir_awards(keyword, agency=None, year=None, max_results=100):
    """Fetch SBIR awards matching a keyword with retry on rate limit."""
    params = {
        "keyword": keyword,
        "rows": min(max_results, 100),
        "start": 0,
    }
    if agency:
        params["agency"] = agency
    if year:
        params["year"] = year

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(SBIR_API, params=params, timeout=30,
                               headers={"User-Agent": "InnovatorsLeague/1.0"})
            if resp.status_code == 403:
                return None  # API under maintenance
            if resp.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"  Rate limited (429), waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("results", data.get("data", []))
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  Error fetching SBIR: {e}")
            return []
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def main():
    print("=" * 60)
    print("SBIR/STTR Government Grant Awards Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Searching {len(SEARCH_KEYWORDS)} keyword sets across {len(AGENCIES)} agencies")
    print("=" * 60)

    known_companies = extract_companies_from_datajs()
    print(f"Loaded {len(known_companies)} company names from data.js for matching")

    all_awards = []
    seen_ids = set()
    api_available = True

    # Search by keyword only (no agency/year breakdown) to minimize API calls
    # This fetches the 100 most recent results per keyword = ~1,500 total (deduplicated)
    for keyword in SEARCH_KEYWORDS:
        if not api_available:
            break

        awards = fetch_sbir_awards(keyword)

        if awards is None:
            print("\n  ⚠️ SBIR API returned 403 (maintenance mode). Using cached data.")
            api_available = False
            break

        new_count = 0
        for award in (awards or []):
            # Deduplicate by tracking number
            award_id = award.get("agency_tracking_number", "") or award.get("contract", "")
            if not award_id or award_id in seen_ids:
                continue
            seen_ids.add(award_id)

            firm = award.get("firm", "").strip()
            if not firm:
                continue

            # Check if this company is in our database
            firm_lower = firm.lower()
            is_known = any(known in firm_lower or firm_lower in known
                          for known in known_companies)

            entry = {
                "firm": firm,
                "title": award.get("award_title", ""),
                "agency": award.get("agency", ""),
                "branch": award.get("branch", ""),
                "phase": award.get("phase", ""),
                "program": award.get("program", "SBIR"),
                "awardYear": award.get("award_year", 0),
                "awardAmount": award.get("award_amount", 0),
                "awardDate": award.get("proposal_award_date", ""),
                "abstract": (award.get("abstract", "") or "")[:500],
                "city": award.get("city", ""),
                "state": award.get("state", ""),
                "employees": award.get("number_employees", ""),
                "companyUrl": award.get("company_url", ""),
                "keywords": award.get("research_area_keywords", ""),
                "piName": award.get("pi_name", ""),
                "isKnownCompany": is_known,
            }
            all_awards.append(entry)
            new_count += 1

        if api_available:
            print(f"  [{keyword[:40]}...] → +{new_count} new ({len(all_awards)} total)")

        time.sleep(1.5)  # Rate limiting — SBIR API is strict

    # If API was down, try to load existing cached data
    if not api_available:
        raw_path = DATA_DIR / "sbir_awards_raw.json"
        if raw_path.exists():
            try:
                cached = json.load(open(raw_path))
                if cached:
                    print(f"  Loaded {len(cached)} cached awards")
                    all_awards = cached
            except (json.JSONDecodeError, IOError):
                pass

    if not all_awards:
        print("\nNo SBIR awards found. Generating empty output.")

    # Sort by award year (newest first), then amount
    all_awards.sort(key=lambda a: (
        -int(a.get("awardYear", 0) or 0),
        -float(a.get("awardAmount", 0) or 0)
    ))

    # Separate known vs discovered companies
    known_awards = [a for a in all_awards if a.get("isKnownCompany")]
    new_companies = [a for a in all_awards if not a.get("isKnownCompany")]

    print(f"\nTotal unique awards: {len(all_awards)}")
    print(f"  Awards to known companies: {len(known_awards)}")
    print(f"  Awards to new/unknown companies: {len(new_companies)}")

    # Save raw JSON
    raw_path = DATA_DIR / "sbir_awards_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_awards, f, indent=2)
    print(f"Saved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated SBIR/STTR award data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total awards: {len(all_awards)} | Known companies: {len(known_awards)}",
        "const SBIR_AWARDS_AUTO = [",
    ]

    for award in all_awards[:500]:  # Cap at 500 for JS file size
        firm_esc = award["firm"].replace('"', '\\"')
        title_esc = award["title"][:100].replace('"', '\\"')
        abstract_esc = award["abstract"][:200].replace('"', '\\"').replace("\n", " ")
        js_lines.append("  {")
        js_lines.append(f'    firm: "{firm_esc}",')
        js_lines.append(f'    title: "{title_esc}",')
        js_lines.append(f'    agency: "{award["agency"]}",')
        js_lines.append(f'    phase: "{award["phase"]}",')
        js_lines.append(f'    program: "{award["program"]}",')
        js_lines.append(f'    awardYear: {award["awardYear"] or 0},')
        js_lines.append(f'    awardAmount: {award["awardAmount"] or 0},')
        js_lines.append(f'    state: "{award["state"]}",')
        js_lines.append(f'    abstract: "{abstract_esc}",')
        js_lines.append(f'    isKnownCompany: {"true" if award["isKnownCompany"] else "false"},')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "sbir_awards_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Top agencies summary
    agency_counts = {}
    for a in all_awards:
        ag = a.get("agency", "Unknown")
        agency_counts[ag] = agency_counts.get(ag, 0) + 1
    print("\nTop Agencies:")
    for ag, count in sorted(agency_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {ag}: {count} awards")

    print("=" * 60)


if __name__ == "__main__":
    main()
