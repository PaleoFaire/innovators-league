#!/usr/bin/env python3
"""
NIH Reporter Grant Fetcher for The Innovators League
Tracks biotech companies and research institutions receiving NIH funding.
NIH awards ~$42B/year — this identifies biotech innovators before their first VC round.

API: https://api.reporter.nih.gov/v2/projects/search
Free, no API key required. Rate limit: 100 req/min recommended.
"""

import json
import re
import requests
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"
NIH_API = "https://api.reporter.nih.gov/v2/projects/search"

# Search terms targeting frontier biotech
SEARCH_QUERIES = [
    "CRISPR gene editing therapy",
    "CAR-T cell therapy immunotherapy",
    "mRNA vaccine platform",
    "synthetic biology engineered organisms",
    "brain computer interface neural",
    "organ on chip tissue engineering",
    "AI drug discovery machine learning",
    "gene therapy rare disease",
    "protein engineering directed evolution",
    "nanomedicine drug delivery",
    "microbiome therapeutic",
    "longevity aging senolytic",
    "xenotransplantation",
    "optogenetics neural modulation",
    "liquid biopsy cancer diagnostics",
]

# SBIR/STTR activity codes (small business awards)
SBIR_CODES = ["R43", "R44", "SB1", "U43", "U44"]


def extract_companies_from_datajs():
    """Extract company names from data.js for matching."""
    if not DATA_JS.exists():
        return set()
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for match in re.finditer(r'name:\s*["\']([^"\']+)["\']', content):
        names.add(match.group(1).lower().strip())
    return names


def search_nih(query, limit=50, offset=0, fiscal_years=None):
    """Search NIH Reporter for projects matching a query."""
    criteria = {
        "advanced_text_search": {
            "operator": "and",
            "search_field": "terms",
            "search_text": query,
        },
        "is_active": True,
    }

    if fiscal_years:
        criteria["fiscal_years"] = fiscal_years

    body = {
        "criteria": criteria,
        "offset": offset,
        "limit": limit,
        "sort_field": "award_notice_date",
        "sort_order": "desc",
    }

    try:
        resp = requests.post(NIH_API, json=body, timeout=30,
                            headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", []), data.get("meta", {}).get("total", 0)
    except requests.exceptions.RequestException as e:
        print(f"  Error querying NIH Reporter: {e}")
        return [], 0
    except (json.JSONDecodeError, ValueError):
        return [], 0


def main():
    print("=" * 60)
    print("NIH Reporter Grant Fetcher")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Searching {len(SEARCH_QUERIES)} frontier biotech queries")
    print("=" * 60)

    known_companies = extract_companies_from_datajs()
    print(f"Loaded {len(known_companies)} company names from data.js\n")

    all_grants = []
    seen_ids = set()

    for query in SEARCH_QUERIES:
        results, total = search_nih(query, limit=50, fiscal_years=[2025, 2026])
        time.sleep(0.5)  # Rate limiting

        new_count = 0
        for project in results:
            appl_id = project.get("appl_id")
            if not appl_id or appl_id in seen_ids:
                continue
            seen_ids.add(appl_id)

            org = project.get("organization", {}) or {}
            org_name = org.get("org_name", "").strip()
            pi_list = project.get("principal_investigators", []) or []
            pi_name = pi_list[0].get("full_name", "").strip() if pi_list else ""

            # Check activity code for SBIR/STTR
            activity_code = project.get("activity_code", "")
            is_sbir = activity_code in SBIR_CODES

            # Check if org is a known company
            org_lower = org_name.lower()
            is_known = any(known in org_lower or org_lower in known
                          for known in known_companies if len(known) > 3)

            # Funding info
            award_amount = project.get("award_amount", 0) or 0
            direct_cost = project.get("direct_cost_amt", 0) or 0
            indirect_cost = project.get("indirect_cost_amt", 0) or 0

            # Extract key terms
            terms_raw = project.get("pref_terms", "") or ""
            terms = [t.strip() for t in terms_raw.split(";") if t.strip()][:15]

            entry = {
                "applId": appl_id,
                "projectNum": project.get("project_num", ""),
                "title": project.get("project_title", "").strip(),
                "organization": org_name,
                "orgCity": org.get("org_city", ""),
                "orgState": org.get("org_state", ""),
                "piName": pi_name,
                "fiscalYear": project.get("fiscal_year", 2026),
                "awardAmount": award_amount,
                "directCost": direct_cost,
                "indirectCost": indirect_cost,
                "activityCode": activity_code,
                "isSbir": is_sbir,
                "isActive": project.get("is_active", False),
                "agencyCode": project.get("agency_code", "NIH"),
                "startDate": project.get("project_start_date", ""),
                "endDate": project.get("project_end_date", ""),
                "abstract": (project.get("abstract_text", "") or "")[:500],
                "terms": terms,
                "detailUrl": project.get("project_detail_url", ""),
                "isKnownCompany": is_known,
                "searchQuery": query,
            }
            all_grants.append(entry)
            new_count += 1

        print(f"  [{query[:45]}...] → {new_count} new ({total} total matches)")

    # Sort by award amount descending
    all_grants.sort(key=lambda g: -(g.get("awardAmount", 0) or 0))

    # Stats
    known_grants = [g for g in all_grants if g.get("isKnownCompany")]
    sbir_grants = [g for g in all_grants if g.get("isSbir")]
    total_funding = sum(g.get("awardAmount", 0) for g in all_grants)

    print(f"\nTotal unique grants: {len(all_grants)}")
    print(f"  Known company grants: {len(known_grants)}")
    print(f"  SBIR/STTR grants: {len(sbir_grants)}")
    print(f"  Total funding tracked: ${total_funding:,.0f}")

    # Save raw JSON
    raw_path = DATA_DIR / "nih_grants_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_grants, f, indent=2)
    print(f"\nSaved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated NIH Reporter grant data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total grants: {len(all_grants)} | Known companies: {len(known_grants)} | SBIR: {len(sbir_grants)}",
        f"// Total funding tracked: ${total_funding:,.0f}",
        "const NIH_GRANTS_AUTO = [",
    ]

    for grant in all_grants[:300]:  # Cap at 300
        title_esc = grant["title"][:120].replace('"', '\\"').replace("\n", " ")
        org_esc = grant["organization"].replace('"', '\\"')
        abstract_esc = grant["abstract"][:200].replace('"', '\\"').replace("\n", " ")
        terms_str = json.dumps(grant["terms"][:8])
        js_lines.append("  {")
        js_lines.append(f'    title: "{title_esc}",')
        js_lines.append(f'    organization: "{org_esc}",')
        js_lines.append(f'    orgState: "{grant["orgState"]}",')
        js_lines.append(f'    piName: "{grant["piName"]}",')
        js_lines.append(f'    fiscalYear: {grant["fiscalYear"]},')
        js_lines.append(f'    awardAmount: {grant["awardAmount"]},')
        js_lines.append(f'    activityCode: "{grant["activityCode"]}",')
        js_lines.append(f'    isSbir: {"true" if grant["isSbir"] else "false"},')
        js_lines.append(f'    abstract: "{abstract_esc}",')
        js_lines.append(f'    terms: {terms_str},')
        js_lines.append(f'    isKnownCompany: {"true" if grant["isKnownCompany"] else "false"},')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "nih_grants_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    print("=" * 60)


if __name__ == "__main__":
    main()
