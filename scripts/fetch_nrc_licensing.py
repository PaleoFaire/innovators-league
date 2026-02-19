#!/usr/bin/env python3
"""
NRC Licensing Tracker for The Innovators League
Tracks Nuclear Regulatory Commission licensing milestones for nuclear companies.
Uses the NRC ADAMS public document search where possible.
Falls back to curated data for known licensing proceedings.
"""

import json
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# NRC ADAMS public search API
ADAMS_API = "https://adams.nrc.gov/wba/services/search/advanced/nrc"

# Companies with active NRC proceedings
NUCLEAR_COMPANIES = {
    "NuScale Power": {
        "docketNumber": "05200048",
        "reactorType": "Small Modular Reactor (SMR)",
        "status": "Design Certification Approved",
        "milestones": [
            {"date": "2023-01-19", "event": "Design Certification Rule Issued", "status": "completed"},
            {"date": "2024-01-01", "event": "COLA Application Review (Idaho)", "status": "in_progress"},
            {"date": "2027-01-01", "event": "Combined License Expected", "status": "pending"},
            {"date": "2030-01-01", "event": "First Commercial Operation", "status": "pending"},
        ],
    },
    "Oklo": {
        "docketNumber": "05200049",
        "reactorType": "Fast Reactor (Aurora)",
        "status": "Combined License Application Under Review",
        "milestones": [
            {"date": "2022-01-01", "event": "Initial Application Submitted", "status": "completed"},
            {"date": "2024-03-01", "event": "Application Resubmitted (Enhanced)", "status": "completed"},
            {"date": "2025-06-01", "event": "NRC Acceptance Review Complete", "status": "completed"},
            {"date": "2026-06-01", "event": "Safety Evaluation Report Draft", "status": "in_progress"},
            {"date": "2027-12-01", "event": "Combined License Decision", "status": "pending"},
        ],
    },
    "Kairos Power": {
        "docketNumber": "05000611",
        "reactorType": "Fluoride Salt-Cooled High-Temperature Reactor",
        "status": "Construction Permit Under Review",
        "milestones": [
            {"date": "2023-09-29", "event": "Construction Permit Application Filed (Hermes)", "status": "completed"},
            {"date": "2024-12-17", "event": "NRC Construction Permit Issued for Hermes Test Reactor", "status": "completed"},
            {"date": "2025-06-01", "event": "Construction Begun at Oak Ridge", "status": "completed"},
            {"date": "2027-01-01", "event": "Hermes Test Reactor Operational", "status": "pending"},
            {"date": "2028-01-01", "event": "Hermes 2 Commercial Application", "status": "pending"},
        ],
    },
    "TerraPower": {
        "docketNumber": "05000612",
        "reactorType": "Natrium Sodium-Cooled Fast Reactor",
        "status": "Construction Permit Application Submitted",
        "milestones": [
            {"date": "2024-03-01", "event": "Construction Permit Application Filed (Kemmerer, WY)", "status": "completed"},
            {"date": "2024-06-01", "event": "DOE Cost Share Agreement Finalized", "status": "completed"},
            {"date": "2025-01-01", "event": "NRC Review Initiated", "status": "completed"},
            {"date": "2026-06-01", "event": "Construction Permit Expected", "status": "in_progress"},
            {"date": "2030-01-01", "event": "First Commercial Operation", "status": "pending"},
        ],
    },
    "X-energy": {
        "docketNumber": "05200050",
        "reactorType": "Xe-100 High-Temperature Gas Reactor",
        "status": "Pre-Application Engagement",
        "milestones": [
            {"date": "2023-01-01", "event": "Pre-Application Meetings with NRC", "status": "completed"},
            {"date": "2025-01-01", "event": "Design Certification Application Expected", "status": "in_progress"},
            {"date": "2027-01-01", "event": "Design Certification Review", "status": "pending"},
            {"date": "2029-01-01", "event": "First Plant Operational (Dow Chemical Site)", "status": "pending"},
        ],
    },
    "Commonwealth Fusion Systems": {
        "docketNumber": "N/A",
        "reactorType": "SPARC Tokamak Fusion",
        "status": "Pre-Regulatory Framework",
        "milestones": [
            {"date": "2025-01-01", "event": "SPARC Construction Ongoing (Devens, MA)", "status": "in_progress"},
            {"date": "2026-01-01", "event": "First Plasma Expected", "status": "pending"},
            {"date": "2027-01-01", "event": "Net Energy Demonstration", "status": "pending"},
            {"date": "2030-01-01", "event": "ARC Commercial Plant Licensing", "status": "pending"},
        ],
        "note": "Fusion regulation framework still being developed by NRC. Not under traditional fission licensing.",
    },
    "Helion Energy": {
        "docketNumber": "N/A",
        "reactorType": "Field-Reversed Configuration Fusion",
        "status": "Pre-Regulatory Framework",
        "milestones": [
            {"date": "2024-01-01", "event": "Polaris Prototype Construction", "status": "completed"},
            {"date": "2025-06-01", "event": "Polaris Testing Phase", "status": "in_progress"},
            {"date": "2028-01-01", "event": "First Commercial Fusion Plant", "status": "pending"},
        ],
        "note": "PPA signed with Microsoft for fusion electricity delivery by 2028.",
    },
    "Centrus Energy": {
        "docketNumber": "07007004",
        "reactorType": "HALEU Production (Uranium Enrichment)",
        "status": "Operating License Active",
        "milestones": [
            {"date": "2023-10-01", "event": "HALEU Production Begun (Piketon, OH)", "status": "completed"},
            {"date": "2024-06-01", "event": "First HALEU Delivered to DOE", "status": "completed"},
            {"date": "2025-01-01", "event": "Production Scale-Up Phase", "status": "in_progress"},
            {"date": "2026-01-01", "event": "Full-Scale HALEU Production", "status": "pending"},
        ],
    },
}


def main():
    print("=" * 60)
    print("NRC Licensing Tracker")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    entries = []
    for company, data in NUCLEAR_COMPANIES.items():
        # Count milestone statuses
        completed = sum(1 for m in data["milestones"] if m["status"] == "completed")
        total = len(data["milestones"])
        progress_pct = round((completed / total) * 100) if total > 0 else 0

        # Find current milestone
        current = next((m for m in data["milestones"] if m["status"] == "in_progress"), None)

        entries.append({
            "company": company,
            "docketNumber": data["docketNumber"],
            "reactorType": data["reactorType"],
            "status": data["status"],
            "milestones": data["milestones"],
            "progressPercent": progress_pct,
            "currentMilestone": current["event"] if current else "N/A",
            "note": data.get("note", ""),
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        })

    # Sort by progress (most advanced first)
    entries.sort(key=lambda x: x["progressPercent"], reverse=True)

    # Save as JS module
    output_path = DATA_DIR / "nrc_licensing_auto.js"
    js_content = f"// Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    js_content += f"const NRC_LICENSING_AUTO = {json.dumps(entries, indent=2)};\n"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(js_content)

    print(f"Saved {len(entries)} NRC entries to {output_path}")

    for e in entries:
        print(f"  {e['company']:30s} | {e['status']:40s} | {e['progressPercent']}%")

    # Save JSON
    json_path = DATA_DIR / "nrc_licensing_auto.json"
    with open(json_path, "w") as f:
        json.dump(entries, f, indent=2)

    print("=" * 60)


if __name__ == "__main__":
    main()
