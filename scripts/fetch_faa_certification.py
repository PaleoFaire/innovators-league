#!/usr/bin/env python3
"""
FAA Certification Tracker for The Innovators League
Tracks FAA type certificate and certification progress for eVTOL,
commercial space, and drone companies.
Uses curated data based on public FAA announcements and filings.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Companies with active FAA certification processes
FAA_TRACKED = {
    # eVTOL / Advanced Air Mobility
    "Joby Aviation": {
        "type": "Type Certificate",
        "category": "eVTOL",
        "aircraft": "Joby S4",
        "faaProject": "TC Application (Part 21.17)",
        "status": "Flight Testing / Type Certification",
        "milestones": [
            {"date": "2020-02-01", "event": "G-1 Certification Basis Issued by FAA", "status": "completed"},
            {"date": "2022-05-01", "event": "Stage 4 Means of Compliance Approval", "status": "completed"},
            {"date": "2023-06-01", "event": "FAA Issues Special Conditions", "status": "completed"},
            {"date": "2024-01-01", "event": "First Piloted eVTOL FAA Flight Test", "status": "completed"},
            {"date": "2025-06-01", "event": "Type Inspection Authorization", "status": "in_progress"},
            {"date": "2026-01-01", "event": "Type Certificate Expected", "status": "pending"},
            {"date": "2026-06-01", "event": "Part 135 Commercial Operations", "status": "pending"},
        ],
    },
    "Archer Aviation": {
        "type": "Type Certificate",
        "category": "eVTOL",
        "aircraft": "Midnight",
        "faaProject": "TC Application",
        "status": "Flight Testing / Type Certification",
        "milestones": [
            {"date": "2020-10-01", "event": "FAA Accepted TC Application", "status": "completed"},
            {"date": "2023-02-01", "event": "FAA Issued Airworthiness Criteria", "status": "completed"},
            {"date": "2024-08-01", "event": "Midnight First Flight", "status": "completed"},
            {"date": "2025-03-01", "event": "Flight Test Campaign Ongoing", "status": "in_progress"},
            {"date": "2025-12-01", "event": "Type Certificate Expected", "status": "pending"},
            {"date": "2026-06-01", "event": "Launch Commercial Service (LA)", "status": "pending"},
        ],
    },
    "Lilium": {
        "type": "Type Certificate",
        "category": "eVTOL",
        "aircraft": "Lilium Jet",
        "faaProject": "EASA TC + FAA Validation",
        "status": "Restructured — Certification Resumed",
        "milestones": [
            {"date": "2021-06-01", "event": "EASA CRI Published", "status": "completed"},
            {"date": "2024-10-01", "event": "Restructuring Completed", "status": "completed"},
            {"date": "2025-01-01", "event": "Certification Program Resumed", "status": "in_progress"},
            {"date": "2027-01-01", "event": "EASA Type Certificate", "status": "pending"},
            {"date": "2027-06-01", "event": "FAA Validation", "status": "pending"},
        ],
    },
    "Wisk Aero": {
        "type": "Type Certificate",
        "category": "eVTOL (Autonomous)",
        "aircraft": "Cora (Gen 6)",
        "faaProject": "TC Application — First Autonomous eVTOL",
        "status": "Type Certification In Progress",
        "milestones": [
            {"date": "2022-10-01", "event": "FAA Accepted TC Application", "status": "completed"},
            {"date": "2023-03-01", "event": "FAA Granted First Autonomous eVTOL Airworthiness Criteria", "status": "completed"},
            {"date": "2025-01-01", "event": "Flight Test Program", "status": "in_progress"},
            {"date": "2027-01-01", "event": "Type Certificate (Autonomous)", "status": "pending"},
        ],
        "note": "Boeing-backed. First fully autonomous air taxi seeking FAA TC.",
    },
    # Commercial Space
    "SpaceX": {
        "type": "Launch License",
        "category": "Commercial Space",
        "aircraft": "Starship / Super Heavy",
        "faaProject": "Launch/Reentry License (Part 450)",
        "status": "Active Launch License — Iterating",
        "milestones": [
            {"date": "2023-04-20", "event": "Starship IFT-1 (FAA Licensed)", "status": "completed"},
            {"date": "2023-11-18", "event": "IFT-2 Stage Separation Success", "status": "completed"},
            {"date": "2024-03-14", "event": "IFT-3 Orbital Velocity Achieved", "status": "completed"},
            {"date": "2024-06-06", "event": "IFT-4 Booster Soft Splashdown", "status": "completed"},
            {"date": "2024-10-13", "event": "IFT-5 Booster Tower Catch", "status": "completed"},
            {"date": "2025-01-01", "event": "Rapid Reuse License Modification", "status": "in_progress"},
            {"date": "2025-06-01", "event": "Operational Cargo Flights", "status": "pending"},
        ],
    },
    "Rocket Lab": {
        "type": "Launch License",
        "category": "Commercial Space",
        "aircraft": "Neutron",
        "faaProject": "Launch License Application (Wallops VA)",
        "status": "Neutron LC-2 Under Construction",
        "milestones": [
            {"date": "2023-01-01", "event": "Electron FAA License (Wallops) Granted", "status": "completed"},
            {"date": "2024-06-01", "event": "Neutron Pad Construction Begun", "status": "completed"},
            {"date": "2025-03-01", "event": "Neutron Engine Testing (Archimedes)", "status": "in_progress"},
            {"date": "2025-12-01", "event": "Neutron FAA Launch License Application", "status": "pending"},
            {"date": "2026-06-01", "event": "Neutron First Flight", "status": "pending"},
        ],
    },
    "Relativity Space": {
        "type": "Launch License",
        "category": "Commercial Space",
        "aircraft": "Terran R",
        "faaProject": "Launch License Application",
        "status": "Terran R Development",
        "milestones": [
            {"date": "2023-03-23", "event": "Terran 1 First Launch (Partial Success)", "status": "completed"},
            {"date": "2024-01-01", "event": "Pivot to Terran R (Larger Vehicle)", "status": "completed"},
            {"date": "2025-06-01", "event": "Terran R Structure Complete", "status": "in_progress"},
            {"date": "2026-01-01", "event": "FAA Environmental Review", "status": "pending"},
            {"date": "2026-12-01", "event": "Terran R First Flight", "status": "pending"},
        ],
    },
    # Drones
    "Skydio": {
        "type": "Part 107 Waiver / Type Certificate",
        "category": "Drones",
        "aircraft": "Skydio X10",
        "faaProject": "BVLOS Operations Waiver",
        "status": "Operating Under Part 107 Waivers",
        "milestones": [
            {"date": "2023-01-01", "event": "Part 107 Blanket Waiver for Night Operations", "status": "completed"},
            {"date": "2024-01-01", "event": "BVLOS Waiver Granted (Select Customers)", "status": "completed"},
            {"date": "2025-01-01", "event": "X10 Remote ID Compliance", "status": "completed"},
            {"date": "2025-06-01", "event": "Expanded BVLOS Operations", "status": "in_progress"},
        ],
    },
    "Zipline": {
        "type": "Part 135 Certificate",
        "category": "Drone Delivery",
        "aircraft": "Platform 2 (P2)",
        "faaProject": "Part 135 Air Carrier Certificate",
        "status": "Commercial Drone Delivery Operations",
        "milestones": [
            {"date": "2022-04-01", "event": "FAA Part 135 Certificate Issued", "status": "completed"},
            {"date": "2023-06-01", "event": "Arkansas Commercial Operations Launched", "status": "completed"},
            {"date": "2024-01-01", "event": "Platform 2 Autonomy Demonstration", "status": "completed"},
            {"date": "2025-01-01", "event": "Multi-State Expansion", "status": "in_progress"},
            {"date": "2026-01-01", "event": "Urban Delivery Operations", "status": "pending"},
        ],
    },
    # Hypersonic
    "Hermeus": {
        "type": "Experimental Certificate",
        "category": "Hypersonic",
        "aircraft": "Quarterhorse / Darkhorse",
        "faaProject": "Experimental Airworthiness Certificate",
        "status": "Engine Testing Phase",
        "milestones": [
            {"date": "2022-01-01", "event": "Chimera Engine Test (Mach 5 Capable)", "status": "completed"},
            {"date": "2024-01-01", "event": "Quarterhorse Unmanned Test Vehicle Build", "status": "completed"},
            {"date": "2025-06-01", "event": "Quarterhorse Flight Testing", "status": "in_progress"},
            {"date": "2028-01-01", "event": "Darkhorse Piloted Prototype", "status": "pending"},
            {"date": "2030-01-01", "event": "Halcyon Commercial Hypersonic Airliner", "status": "pending"},
        ],
        "note": "USAF contract for Presidential & Executive Airlift rapid transport.",
    },
}


def main():
    print("=" * 60)
    print("FAA Certification Tracker")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    entries = []
    for company, data in FAA_TRACKED.items():
        completed = sum(1 for m in data["milestones"] if m["status"] == "completed")
        total = len(data["milestones"])
        progress_pct = round((completed / total) * 100) if total > 0 else 0

        current = next((m for m in data["milestones"] if m["status"] == "in_progress"), None)
        next_milestone = next((m for m in data["milestones"] if m["status"] == "pending"), None)

        entries.append({
            "company": company,
            "certType": data["type"],
            "category": data["category"],
            "aircraft": data["aircraft"],
            "faaProject": data["faaProject"],
            "status": data["status"],
            "milestones": data["milestones"],
            "progressPercent": progress_pct,
            "currentMilestone": current["event"] if current else "N/A",
            "nextMilestone": next_milestone["event"] if next_milestone else "N/A",
            "nextMilestoneDate": next_milestone["date"] if next_milestone else "N/A",
            "note": data.get("note", ""),
            "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        })

    # Sort by category then progress
    entries.sort(key=lambda x: (-x["progressPercent"], x["category"]))

    # Save as JS module
    output_path = DATA_DIR / "faa_certification_auto.js"
    js_content = f"// Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    js_content += f"const FAA_CERTIFICATION_AUTO = {json.dumps(entries, indent=2)};\n"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(js_content)

    print(f"Saved {len(entries)} FAA entries to {output_path}")

    for e in entries:
        print(f"  {e['company']:25s} | {e['category']:20s} | {e['status']:35s} | {e['progressPercent']}%")

    # Save JSON
    json_path = DATA_DIR / "faa_certification_auto.json"
    with open(json_path, "w") as f:
        json.dump(entries, f, indent=2)

    print("=" * 60)


if __name__ == "__main__":
    main()
