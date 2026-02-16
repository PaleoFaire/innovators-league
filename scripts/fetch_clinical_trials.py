#!/usr/bin/env python3
"""
ClinicalTrials.gov API Fetcher
Tracks clinical trials for biotech companies.
Uses the free ClinicalTrials.gov API v2 - no key required.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Biotech companies to track (sponsors/collaborators)
TRACKED_SPONSORS = [
    "Recursion Pharmaceuticals",
    "Recursion",
    "Ginkgo Bioworks",
    "Tempus",
    "23andMe",
    "Exact Sciences",
    "Illumina",
    "Grail",
    "Guardant Health",
    "Foundation Medicine",
    "Invitae",
    "Color Health",
    "Freenome",
    "Adaptive Biotechnologies",
    "Twist Bioscience",
    "Berkeley Lights",
    "Inscripta",
    "Mammoth Biosciences",
    "Beam Therapeutics",
    "Prime Medicine",
    "Intellia Therapeutics",
    "Editas Medicine",
    "CRISPR Therapeutics",
    "Vertex Pharmaceuticals",
    "Moderna",
    "BioNTech",
    "CureVac",
    "Denali Therapeutics",
    "Alector",
    "Relay Therapeutics",
]

# Therapeutic areas of interest
THERAPEUTIC_AREAS = [
    "cancer",
    "oncology",
    "gene therapy",
    "cell therapy",
    "immunotherapy",
    "CRISPR",
    "mRNA",
    "antibody",
    "rare disease",
    "neurological",
    "alzheimer",
    "parkinson",
]

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"

def fetch_sponsor_trials(sponsor, max_results=20):
    """Fetch clinical trials for a sponsor."""
    params = {
        "query.spons": sponsor,
        "pageSize": max_results,
        "sort": "LastUpdatePostDate:desc",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,StartDate,CompletionDate,LeadSponsorName,Condition,InterventionName,LastUpdatePostDate,EnrollmentCount"
    }

    try:
        response = requests.get(CLINICALTRIALS_API, params=params, timeout=30)
        if response.status_code != 200:
            return []

        data = response.json()
        studies = data.get("studies", [])

        trials = []
        for study in studies:
            protocol = study.get("protocolSection", {})
            id_module = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            design_module = protocol.get("designModule", {})
            conditions_module = protocol.get("conditionsModule", {})
            interventions_module = protocol.get("armsInterventionsModule", {})

            trials.append({
                "nctId": id_module.get("nctId", ""),
                "title": id_module.get("briefTitle", ""),
                "status": status_module.get("overallStatus", ""),
                "phase": ", ".join(design_module.get("phases", [])) if design_module.get("phases") else "N/A",
                "startDate": status_module.get("startDateStruct", {}).get("date", ""),
                "completionDate": status_module.get("completionDateStruct", {}).get("date", ""),
                "sponsor": sponsor_module.get("leadSponsor", {}).get("name", sponsor),
                "conditions": conditions_module.get("conditions", [])[:3],
                "interventions": [i.get("name", "") for i in interventions_module.get("interventions", [])][:3] if interventions_module.get("interventions") else [],
                "lastUpdated": status_module.get("lastUpdatePostDateStruct", {}).get("date", ""),
                "enrollment": design_module.get("enrollmentInfo", {}).get("count", 0) if design_module.get("enrollmentInfo") else 0,
            })

        return trials

    except Exception as e:
        print(f"  Error: {e}")
        return []

def fetch_all_trials():
    """Fetch trials for all tracked sponsors."""
    all_trials = []
    seen_ids = set()

    for sponsor in TRACKED_SPONSORS:
        print(f"Fetching trials for: {sponsor}")
        trials = fetch_sponsor_trials(sponsor)

        # Deduplicate
        new_trials = [t for t in trials if t["nctId"] not in seen_ids]
        for t in new_trials:
            seen_ids.add(t["nctId"])

        if new_trials:
            print(f"  Found {len(new_trials)} unique trials")
            all_trials.extend(new_trials)
        else:
            print(f"  No trials found")

        time.sleep(0.5)  # Rate limiting

    return all_trials

def filter_active_trials(trials):
    """Filter to active/recruiting trials."""
    active_statuses = [
        "RECRUITING",
        "ACTIVE_NOT_RECRUITING",
        "ENROLLING_BY_INVITATION",
        "NOT_YET_RECRUITING"
    ]
    return [t for t in trials if t.get("status", "").upper().replace(", ", "_").replace(" ", "_") in active_statuses or "RECRUITING" in t.get("status", "").upper()]

def save_to_json(data, filename):
    """Save data to JSON file."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} records to {output_path}")

def generate_js_snippet(trials):
    """Generate JavaScript code snippet for CLINICAL_TRIALS."""
    # Sort by last updated descending
    trials.sort(key=lambda x: x.get("lastUpdated", ""), reverse=True)

    js_output = "// Auto-updated clinical trials from ClinicalTrials.gov\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const CLINICAL_TRIALS = [\n"

    for t in trials[:40]:
        title = t.get("title", "").replace('"', '\\"').replace('\n', ' ')[:80]
        conditions = ", ".join(t.get("conditions", []))[:50]
        interventions = ", ".join(t.get("interventions", []))[:50]

        js_output += f'  {{ nctId: "{t["nctId"]}", title: "{title}", '
        js_output += f'status: "{t["status"]}", phase: "{t["phase"]}", '
        js_output += f'sponsor: "{t["sponsor"]}", conditions: "{conditions}", '
        js_output += f'enrollment: {t["enrollment"]}, lastUpdated: "{t["lastUpdated"]}" }},\n'

    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "clinical_trials_auto.js"
    with open(output_path, "w") as f:
        f.write(js_output)

    print(f"Generated JS snippet at {output_path}")

def main():
    print("=" * 60)
    print("ClinicalTrials.gov Fetcher")
    print("=" * 60)
    print(f"Tracking {len(TRACKED_SPONSORS)} biotech sponsors")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Fetch all trials
    trials = fetch_all_trials()
    print(f"\nTotal unique trials found: {len(trials)}")

    # Filter active trials
    active = filter_active_trials(trials)
    print(f"Active/Recruiting trials: {len(active)}")

    # Save data
    save_to_json(trials, "clinical_trials_raw.json")
    save_to_json(active, "clinical_trials_active.json")

    # Generate JS snippet
    generate_js_snippet(trials)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    # Summary by phase
    if trials:
        print("\nTrials by phase:")
        phase_counts = {}
        for t in trials:
            phase = t.get("phase", "N/A")
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        for phase, count in sorted(phase_counts.items()):
            print(f"  {phase}: {count} trials")

if __name__ == "__main__":
    main()
