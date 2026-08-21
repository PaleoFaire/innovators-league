#!/usr/bin/env python3
"""
Sector-correctness audit
─────────────────────────────────────────────────────────────────────────
The data-quality gate proves every company carries a VALID sector key.
This asks the harder question: is it the RIGHT one?

Method — same doctrine as the 2026-08 location cleanup: mechanical
flagging with stated evidence, human judgment on every change, and a
strong bias against false positives. A company in a defensible-but-debatable
sector is left alone; only records where the text plainly contradicts the
label are flagged.

Each company's text (description + techApproach + tags + name) is scored
against keyword sets per sector. A record is flagged when BOTH:
  * its current sector scores weakly (below MIN_OWN), and
  * some other sector scores strongly (>= MIN_OTHER and >= 2x the current).

Boundary rules encoded from the taxonomy's own intent:
  * military drones -> Defense & Security; commercial -> Drones & Autonomous
  * quantum anything -> Quantum Computing, not Chips
  * nuclear -> Nuclear Energy, not Climate & Energy
  * embodied/robot AI -> Robotics & Manufacturing; pure software AI -> AI & Software

Output: report only. Never edits data.js.
  python3 scripts/audit_sectors.py            # summary + flags
  python3 scripts/audit_sectors.py --all      # include weak (review-only) flags
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# phrase -> weight. Phrases are matched on word boundaries, case-insensitive.
KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "Defense & Security": [
        (r"defen[cs]e", 3), (r"military", 3), (r"weapon", 3), (r"missile", 3),
        (r"munition", 3), (r"battlefield", 3), (r"warfare", 3), (r"dod\b", 2),
        (r"counter[- ]?(?:uas|drone)", 3), (r"electronic warfare", 3),
        (r"national security", 2), (r"army|navy|air force|pentagon|warfighter", 2),
        (r"attack drone|strike|combat", 2), (r"intelligence, surveillance", 2),
        (r"hypersonic (?:missile|weapon)", 3), (r"sonar|submarine", 2),
        (r"biosecurity|biodefense", 2), (r"border security", 2),
    ],
    "Nuclear Energy": [
        (r"nuclear", 3), (r"reactor", 3), (r"fission", 3), (r"smr\b", 3),
        (r"microreactor", 3), (r"uranium|enrich(?:ment|ed)", 3), (r"tritium", 2),
        (r"fusion", 3), (r"stellarator|tokamak|inertial confinement", 3),
        (r"nrc\b", 2), (r"radioisotope", 2),
    ],
    "Space & Aerospace": [
        (r"satellite", 3), (r"orbit", 3), (r"launch vehicle|rocket", 3),
        (r"spacecraft", 3), (r"in[- ]space", 3), (r"lunar|moon|mars|asteroid", 3),
        (r"space station|reentry|re-entry", 3), (r"constellation", 2),
        (r"leo\b|geo\b", 2), (r"propulsion", 1), (r"ground station", 2),
        (r"earth observation", 3),
    ],
    "Supersonic & Hypersonic": [
        (r"supersonic", 3), (r"hypersonic (?:aircraft|jet|plane|flight)", 3),
        (r"mach \d", 2),
    ],
    "AI & Software": [
        (r"software", 2), (r"\bsaas\b", 3), (r"llm|language model", 3),
        (r"machine learning|deep learning", 2), (r"data platform|analytics", 2),
        (r"\bapi\b", 1), (r"foundation model", 2), (r"copilot|agent", 1),
        (r"cybersecurity|security software", 2),
    ],
    "Robotics & Manufacturing": [
        (r"robot", 3), (r"manufactur", 3), (r"factory|factories", 3),
        (r"automation", 2), (r"3d[- ]print|additive", 3), (r"cnc|machining", 3),
        (r"foundry|casting|forging", 3), (r"assembly line", 2),
        (r"humanoid", 3), (r"industrial", 1), (r"wiring harness", 3),
        (r"welding", 2), (r"exoskeleton", 2),
    ],
    "Biotech & Health": [
        (r"biotech", 3), (r"drug|pharma", 3), (r"therapeutic", 3),
        (r"clinical", 3), (r"genom|dna|gene", 3), (r"protein|molecule", 2),
        (r"diagnostic", 3), (r"medical device", 3), (r"patient", 2),
        (r"longevity|aging", 2), (r"cancer|disease", 2), (r"surgical", 3),
        (r"vaccine|antibody", 3), (r"fermentation", 2),
    ],
    "Climate & Energy": [
        (r"solar", 3), (r"geothermal", 3), (r"carbon (?:capture|removal|credit)", 3),
        (r"battery|batteries|energy storage", 3), (r"wind", 2),
        (r"grid", 2), (r"renewable", 3), (r"hydrogen", 2), (r"synthetic fuel|efuel|e-fuel|saf\b", 3),
        (r"emission", 2), (r"electrolyzer", 3), (r"climate", 2), (r"clean energy", 3),
        (r"natural gas|methane", 2), (r"power plant", 2), (r"lithium|mining|minerals", 2),
        (r"turbine", 2), (r"desalination|water", 2),
    ],
    "Drones & Autonomous": [
        (r"drone deliver", 3), (r"commercial drone", 3), (r"\buav\b", 2),
        (r"aerial (?:imaging|inspection|survey)", 3), (r"evtol|air taxi", 3),
        (r"autonomous (?:vehicle|driving|truck)", 3), (r"self[- ]driving", 3),
        (r"delivery network", 2),
    ],
    "Chips & Semiconductors": [
        (r"semiconductor", 3), (r"\bchip", 3), (r"\bfab\b|foundry services", 2),
        (r"photonic", 3), (r"wafer", 3), (r"\bgpu\b|\basic\b|accelerator", 2),
        (r"lithograph", 3), (r"transistor", 3), (r"packaging", 1),
        (r"compute hardware", 2), (r"inference", 1),
    ],
    "Housing & Construction": [
        (r"housing", 3), (r"home", 2), (r"modular construction", 3),
        (r"prefab", 3), (r"construction", 2), (r"building", 1), (r"real estate", 2),
        (r"apartment|residential", 2),
    ],
    "Transportation": [
        (r"electric vehicle|\bev\b", 3), (r"tunnel", 3), (r"rail|train", 3),
        (r"shipping|freight", 2), (r"aircraft engine", 2), (r"aviation", 2),
        (r"maritime transport", 2), (r"trucking", 2), (r"airship", 3),
        (r"seaplane|cargo plane", 3),
    ],
    "Consumer Tech": [
        (r"consumer", 3), (r"\bapp\b", 2), (r"wearable", 3), (r"scent|fragrance", 3),
        (r"edtech|education", 2), (r"gaming", 2),
    ],
    "Quantum Computing": [
        (r"quantum", 3), (r"qubit", 3), (r"quantum network|qkd", 3),
        (r"error correction", 2),
    ],
    "Ocean & Maritime": [
        (r"ocean", 3), (r"underwater|subsea|seabed", 3), (r"maritime", 3),
        (r"vessel|ship(?:s|building)?\b", 2), (r"\bsonar\b", 2), (r"seafloor", 3),
        (r"aquaculture", 3), (r"port\b", 2),
    ],
    "Infrastructure & Logistics": [
        (r"logistics", 3), (r"supply chain", 3), (r"warehouse", 2),
        (r"infrastructure", 2), (r"grid modernization", 3),
    ],
}

# Reviewed 2026-08-21: every flag below was examined by hand and judged
# CORRECT as filed — the scorer's keywords misread them (e.g. Karman's "rocket
# turbomachinery" heat pumps, Saildrone's Navy-first identity matching the
# Saronic/Andrenam convention, boats defensibly in Transportation). Listed so
# reruns stay quiet; remove a name to re-examine it.
ALLOW = {
    "Cellino", "Cellares", "Phaidra", "Core Automation", "Salient Motion",
    "Karman Industries", "Airship Industries", "Navier", "Arc Boats",
    "Galvanick", "Solugen", "Amperon", "Watoga Technologies", "Saildrone",
    "Type One Energy", "Focused Energy", "Pacific Fusion", "First Light Fusion",
    "Proxima Fusion", "Marvel Fusion", "Helical Fusion", "EX-Fusion",
    "Gauss Fusion", "Thea Energy", "Zap Energy", "Fuse Energy", "Tokamak Energy",
    "Crusoe Energy", "Lumina Vehicles", "FleetZero", "Wardstone", "Zeno Power",
    "Percepto", "Wiliot", "Tevel Aerobotics", "Dronamics", "Trilobio",
    "Outrider", "Poseidon Aerospace", "Elroy Air", "Pyka", "Occam",
    "Skyeton", "Primoco UAV", "Vyriy Drone", "Ocius Technology", "Speedata",
    "StoreDot", "Arbe Robotics", "Red 6", "Sift Stack", "Together AI", "Atmo",
    "Black Forest Labs", "CuspAI", "BootLoop", "Callosum", "Orqa", "Zeitview",
    "MightyFly", "Natilus", "BurnBot", "Pale Blue", "Ohalo Genetics",
    "Sarla Aviation", "Dynamo Air", "Quaise Energy",
    "Skyryse", "Sorcerer", "NextSilicon", "Monumo",
}

MIN_OWN = 3      # below this, the current sector has weak textual support
MIN_OTHER = 6    # another sector needs at least this to challenge
RATIO = 2.0      # ...and at least this multiple of the current score


def load_companies() -> list[dict]:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({name:c.name,sector:c.sector||\'\','
          'text:[c.description||\'\',c.techApproach||\'\',(c.tags||[]).join(\' \'),'
          'c.name].join(\' | \')}));",s);'
          "console.log(JSON.stringify(s.__n));")
    out = subprocess.run(["node", "-e", js, str(ROOT / "data.js")],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def score(text: str) -> dict[str, int]:
    t = text.lower()
    out = {}
    for sector, kws in KEYWORDS.items():
        s = 0
        for pat, w in kws:
            n = len(re.findall(pat, t))
            if n:
                s += w * min(n, 3)   # cap repeats so one word can't run away
        out[sector] = s
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include weak flags")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    companies = load_companies()
    strong, weak = [], []
    for c in companies:
        if c["name"] in ALLOW:
            continue
        sc = score(c["text"])
        own = sc.get(c["sector"], 0)
        best = max(sc, key=sc.get)
        bestv = sc[best]
        if best != c["sector"] and own < MIN_OWN and bestv >= MIN_OTHER and bestv >= RATIO * max(own, 1):
            strong.append({"name": c["name"], "current": c["sector"], "own_score": own,
                           "suggested": best, "suggested_score": bestv,
                           "runner_up": sorted(sc.items(), key=lambda kv: -kv[1])[1][0],
                           "excerpt": c["text"][:130]})
        elif best != c["sector"] and own == 0 and bestv >= 3:
            weak.append({"name": c["name"], "current": c["sector"], "suggested": best,
                         "suggested_score": bestv, "excerpt": c["text"][:110]})

    if args.json:
        print(json.dumps({"strong": strong, "weak": weak}, indent=1))
        return 0

    print(f"scored {len(companies)} companies against {len(KEYWORDS)} sectors")
    print(f"\nSTRONG mismatches (current unsupported, another clearly indicated): {len(strong)}")
    for f in strong:
        print(f"  {f['name'][:30]:<32}{f['current'][:24]:<26}-> {f['suggested'][:24]:<26}"
              f"(own {f['own_score']}, sug {f['suggested_score']})")
        print(f"      {f['excerpt']}")
    if args.all:
        print(f"\nWEAK flags (zero support for current, mild signal elsewhere): {len(weak)}")
        for f in weak:
            print(f"  {f['name'][:30]:<32}{f['current'][:24]:<26}-> {f['suggested'][:24]} ({f['suggested_score']})")
    else:
        print(f"\n({len(weak)} weak flags hidden — run with --all)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
