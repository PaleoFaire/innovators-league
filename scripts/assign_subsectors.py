#!/usr/bin/env python3
"""
Subsector layer — assignment engine
─────────────────────────────────────────────────────────────────────────
Stephen, 2026-08-21: "eVTOLs are really their own thing. so are self
driving cars." The audit agreed: four mega-buckets of ~180-200 companies
hold 65% of the database, hiding real industries (21 humanoid companies
invisible inside Robotics & Manufacturing, 32 launch companies inside
Space, 7 eVTOL makers sharing a shelf with Waymo).

Design decision (approved): a SECOND level, not more top-level sectors.
The 16 sectors stay untouched — every page, color, filter and analytics
join keeps working — and a controlled `subsector` field is added beneath
them. PitchBook structure: industry -> vertical.

Rules of the vocabulary
  * A named subsector exists only where ~6+ companies form a coherent
    market. Everything else is "General" — an honest residual, never a
    shelf label invented for two companies.
  * Subsectors are SECTOR-SCOPED. Rules for one sector cannot see another
    sector's companies, so cross-sector bleed — the failure mode of the
    sector audit's first draft — is structurally impossible here. A wrong
    call within a sector degrades to its General, which is low-stakes.
  * First matching rule wins; rules are ordered most-specific first.

Usage
  python3 scripts/assign_subsectors.py --dry     # report, change nothing
  python3 scripts/assign_subsectors.py           # write subsector fields
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"

# sector -> ordered [(subsector, regex)] ; first match wins; else "General".
RULES: dict[str, list[tuple[str, str]]] = {
    "Defense & Security": [
        ("Maritime Defense", r"maritime|underwater|subsea|seabed|sonar|naval|unmanned surface|usv\b|uuv\b|vessel"),
        ("Missiles & Munitions", r"missile|munition|hypersonic|solid rocket|propellant|warhead|strike weapon|interceptor|energetics"),
        ("Electronic Warfare & Sensing", r"electronic warfare|\bew\b|jamm|spoof|radar|rf |radio.?frequency|signals intelligence|sigint|spectrum|sensor fusion|night vision"),
        ("Drones & Counter-UAS", r"counter[- ]?(?:uas|drone)|fpv|attack drone|drone swarm|loitering|quadcopter|\buas\b|\buav\b|drone"),
        ("Defense Software & Intelligence", r"software|intelligence platform|data platform|command and control|\bc2\b|osint|autonomy stack|simulation|digital twin|cyber"),
        ("Space & Air Defense", r"air defen|missile defen|space domain|orbital|satellite"),
    ],
    "Space & Aerospace": [
        ("Launch", r"launch vehicle|orbital launch|small.?lift|medium.?lift|heavy.?lift rocket|launch services|launch provider|reusable rocket|launch(?:es|ing)? (?:satellites|payloads)|rocket (?:engine|propulsion|company)|spaceplane"),
        ("Earth Observation", r"earth observation|imaging satellite|remote sensing|hyperspectral|\bsar\b|synthetic aperture"),
        ("In-Space Manufacturing & Stations", r"in[- ]space (?:manufactur|production)|space station|microgravity|orbital (?:factory|manufactur|warehouse)|reentry capsule|re-entry"),
        ("Space Logistics & Servicing", r"servicing|debris|tug|last[- ]mile|orbital transfer|docking|refuel|deorbit|space logistics"),
        ("Communications & PNT", r"\bpnt\b|navigation|gps|comms constellation|communications satellite|laser comm|optical link|ground station"),
        ("Deep Space & Resources", r"asteroid|lunar|moon|mars|deep space|helium-3|space resources|mining"),
        ("Satellites & Buses", r"satellite bus|smallsat|cubesat|satellite platform|constellation|spacecraft"),
    ],
    "Robotics & Manufacturing": [
        ("Robot Foundation Models", r"foundation model|vision[- ]language[- ]action|\bvla\b|embodied (?:ai|foundation|intelligence)|robot (?:intelligence|brains?|foundation)|cross[- ]embodiment"),
        ("Humanoids", r"humanoid|bipedal|general[- ]purpose robot"),
        ("Construction & Heavy Equipment", r"construction|excavat|bulldoz|heavy equipment|earthmov|mining robot|drill rig"),
        ("Warehouse & Logistics Robotics", r"warehouse|fulfillment|order[- ]?picking|palletiz|yard truck|logistics robot"),
        ("Food & Agriculture Robotics", r"agricultur|farm|crop|harvest|food (?:prep|service|robot)|kitchen"),
        ("Advanced Manufacturing", r"3d[- ]print|additive|cnc|machining|casting|forging|foundry|precision (?:parts|manufactur)|machine shop|injection mold|composites|semiconductor equipment|wiring harness"),
        ("Industrial Automation", r"automation|assembly|robotic arm|cobot|pick[- ]and[- ]place|inspection|welding|factory software|manufacturing (?:os|software|platform)"),
    ],
    "Climate & Energy": [
        ("Geothermal", r"geothermal"),
        ("Fuels & Hydrogen", r"hydrogen|electrolyz|synthetic fuel|efuel|e-fuel|\bsaf\b|sustainable aviation fuel|methanol|ammonia|biofuel|natural gas from"),
        ("Carbon Capture & Removal", r"carbon (?:capture|removal|dioxide)|direct air capture|\bdac\b|co2|sequestration"),
        ("Critical Minerals & Mining", r"lithium|copper|rare earth|critical mineral|mining|extraction|refining metals"),
        ("Batteries & Storage", r"battery|batteries|energy storage|grid storage|long[- ]duration"),
        ("Solar", r"solar|photovoltaic|\bpv\b"),
        ("Grid & Power Delivery", r"grid|transmission|substation|transformer|power (?:plant|delivery|electronics)|utility|microgrid|turbine|generator"),
        ("Industrial Heat & Efficiency", r"industrial heat|heat pump|thermal (?:battery|storage)|boiler|hvac|cooling|efficiency"),
        ("Water", r"desalination|water (?:treatment|filtration|purification|from air)"),
    ],
    "Nuclear Energy": [
        ("Fusion", r"fusion|stellarator|tokamak|inertial confinement|plasma"),
        ("Fuels & Isotopes", r"haleu|enrich|uranium|fuel (?:cycle|fabrication|supply)|isotope|radioisotope|medical isotope"),
        ("Fission Reactors", r"reactor|\bsmr\b|microreactor|fission|molten salt|pebble|heat pipe"),
    ],
    "Biotech & Health": [
        ("Agriculture & Food Bio", r"crop|agricultur|plant|seed|farm|food|protein production|precision fermentation"),
        ("Neurotech", r"neuro|brain|neural interface|bci\b"),
        ("Longevity", r"longevity|aging|age[- ]related|rejuvenation"),
        ("Biomanufacturing & Tools", r"biomanufactur|cell therapy manufactur|bioreactor|lab automation|lab[- ]in[- ]a[- ]box|dna synthesis|sequencing platform|biofoundry"),
        ("Devices & Diagnostics", r"medical device|diagnostic|imaging|wearable|prosthetic|surgical|implant|monitor"),
        ("Drug Discovery & TechBio", r"drug|therapeutic|antibody|molecule|protein design|target discovery|clinical|pharma|vaccine|oncology|gene therapy"),
    ],
    "Chips & Semiconductors": [
        ("AI Compute", r"ai (?:chip|accelerator|compute|processor)|inference|training chip|wafer[- ]scale|\bgpu\b|\basic\b|\bnpu\b|tensor|transformer chip|hpc"),
        ("Photonics & Interconnect", r"photonic|optical (?:i/o|interconnect|computing)|silicon photonics|laser chip"),
        ("Fabs & Manufacturing Equipment", r"\bfab\b|foundry|lithograph|wafer fab|semiconductor (?:manufactur|equipment|tool)|packaging|metrology"),
        ("Sensors & Specialty Silicon", r"sensor|lidar|radar chip|imaging chip|iot |rf chip|gps|analog|power semiconductor"),
    ],
    "Quantum Computing": [
        ("Quantum Software & Networking", r"quantum (?:software|algorithm|network|internet|security|sensing)|post[- ]quantum|qkd"),
        ("Quantum Hardware", r"qubit|superconducting|trapped ion|neutral atom|photonic quantum|quantum (?:computer|processor|hardware|chip)"),
    ],
    "Drones & Autonomous": [
        ("eVTOL & Air Mobility", r"evtol|air taxi|air mobility|vtol aircraft|personal aircraft|electric aircraft"),
        ("Autonomous Vehicles", r"self[- ]driving|robotaxi|autonomous (?:vehicle|driving|truck|rail)|driverless"),
        ("Cargo & Delivery Drones", r"cargo|delivery|resupply|freight|logistics"),
        ("Industrial & Commercial UAS", r"inspection|survey|imaging|monitoring|spraying|drone[- ]in[- ]a[- ]box|enterprise drone"),
    ],
    "AI & Software": [
        ("Frontier Models", r"foundation model|frontier (?:model|ai lab)|\bllm\b|generative|multimodal model"),
        ("Industrial & Engineering Software", r"engineering|simulation|cad\b|manufactur|industrial|construction software|energy software|physics"),
    ],
    "Transportation": [
        ("Marine Vessels", r"boat|ship|vessel|ferry|hydrofoil|marine"),
        ("Aviation & Engines", r"aircraft|aviation|jet|engine|airship|seaplane|airline"),
        ("Rail & Freight", r"rail|train|freight|trucking|locomotive"),
    ],
    "Housing & Construction": [
        ("Industrialized Housing", r"modular|prefab|factory[- ]built|kit[- ]of[- ]parts|offsite|industrialized"),
    ],
    # Ocean & Maritime, Supersonic & Hypersonic, Consumer Tech,
    # Infrastructure & Logistics: General only — too few for named shelves.
}


# Companies whose breadth defies a single vertical, set by hand. The engine
# would file Anduril under Missiles because Barracuda appears in its text —
# but a platform prime belongs to no one shelf, and General is the honest
# answer for it.
OVERRIDES = {
    "Anduril Industries": "General",
    "SpaceX": "Launch",
}


def load_companies() -> list[dict]:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({name:c.name,sector:c.sector||\'\','
          'subsector:c.subsector||\'\','
          'text:[c.description||\'\',c.techApproach||\'\',(c.tags||[]).join(\' \')].join(\' | \')}));",s);'
          "console.log(JSON.stringify(s.__n));")
    out = subprocess.run(["node", "-e", js, str(DATA_JS)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def assign(sector: str, text: str) -> str:
    for sub, rx in RULES.get(sector, []):
        if re.search(rx, text, re.I):
            return sub
    return "General"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    companies = load_companies()
    plan = []
    for c in companies:
        sub = OVERRIDES.get(c["name"]) or assign(c["sector"], c["text"])
        plan.append((c["name"], c["sector"], sub))

    dist = Counter((s, sub) for _, s, sub in plan)
    print("assignment distribution:")
    cur = None
    for (sec, sub), n in sorted(dist.items()):
        if sec != cur:
            print(f"  {sec}")
            cur = sec
        print(f"      {n:>4}  {sub}")
    gen = sum(1 for _, _, sub in plan if sub == "General")
    print(f"\n  General share: {gen}/{len(plan)} ({gen/len(plan):.0%})")

    if args.dry:
        print("DRY RUN — nothing written")
        return 0

    d = DATA_JS.read_text()
    written = replaced = 0
    for name, sector, sub in plan:
        i = d.find(f'name: "{name}"')
        if i < 0:
            continue
        s = d.rfind("{", 0, i)
        depth = 0
        j = s
        while j < len(d):
            if d[j] == "{":
                depth += 1
            elif d[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        rec = d[s:j + 1]
        m = re.search(r'(\n(\s*)subsector:\s*")[^"]*(")', rec)
        if m:
            new = rec[:m.start()] + m.group(1) + sub + m.group(3) + rec[m.end():]
            replaced += 1
        else:
            sm = re.search(r'(\n(\s*)sector:\s*"[^"]*",)', rec)
            if not sm:
                continue
            new = (rec[:sm.end()] + f'\n{sm.group(2)}subsector: "{sub}",'
                   + rec[sm.end():])
            written += 1
        d = d[:s] + new + d[j + 1:]

    DATA_JS.write_text(d)
    print(f"wrote {written} new subsector fields, updated {replaced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
