#!/usr/bin/env python3
"""
Founder Diaspora — who left the mother ships to build what we track
─────────────────────────────────────────────────────────────────────────
Stephen's brief for Exit Watch was "a tool that tracks companies founded by
ex-SpaceX (and other high-signal firms like Anduril) employees." What got
built points outward — scanning news for companies about to exist — and its
extractor currently yields one garbage hit. But the INWARD half needs no
crawler at all: our own founder fields are dense with provenance ("ex-SpaceX
propulsion", "SpaceX veteran who co-founded Hermeus", "ex-DeepMind"). This
script mines that.

Precision rules — a mother-ship NAME is not membership:
  "competing with SpaceX" or "SpaceX contract" must NOT count. A hit needs
  alumni context within a tight window: ex-/former/veteran/alum/spent N years
  at/engineers from/left <ship>. Evidence is quoted in the output so every
  claim is checkable against the record it came from.

Output: data/diaspora_auto.js  →  const FOUNDER_DIASPORA = {...}
Rendered by exitwatch.html as "The Diaspora" section.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "diaspora_auto.js"

# label -> regex for the organisation itself
SHIPS = {
    "SpaceX":          r"space\s?x",
    "Anduril":         r"anduril",
    "Palantir":        r"palantir",
    "Tesla":           r"tesla",
    "Blue Origin":     r"blue origin",
    "NASA / JPL":      r"nasa|jet propulsion lab|jpl\b",
    "Boston Dynamics": r"boston dynamics",
    "Google / DeepMind": r"deepmind|google",
    "Apple":           r"apple",
    "Waymo":           r"waymo",
    "Rivian":          r"rivian",
    "Northrop / Lockheed / Raytheon": r"northrop|lockheed|raytheon",
}

# alumni context, applied around the ship mention (window built per-ship)
def alumni_patterns(ship_rx: str) -> list[re.Pattern]:
    w = ship_rx
    return [re.compile(p, re.I) for p in (
        rf"\bex[- ](?:{w})",
        rf"\bformer\s+(?:{w})",
        rf"(?:{w})\s+(?:veteran|alum|alumni|vet)\b",
        rf"veterans?\s+(?:of|from)\s+(?:the\s+)?(?:{w})",
        rf"(?:engineers?|team|founders?|executives?)\s+from\s+(?:the\s+)?(?:{w})",
        rf"\bleft\s+(?:{w})",
        rf"spent\s+[\w\s]{{0,12}}years?\s+at\s+(?:{w})",
        rf"\b(?:{w})\s+(?:engineers?|founders?)\b",
        rf"early\s+(?:{w})\s+(?:employee|engineer|hire)",
        rf"(?:{w})['’]s\s+(?:former|founding)",
        rf"co[- ]?creator[s]?\s+of\s+[\w\s-]{{0,30}}at\s+(?:{w})",
    )]


def load_companies() -> list[dict]:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>({name:c.name,sector:c.sector||\'\','
          'founder:c.founder||\'\',description:c.description||\'\','
          'raised:c.totalRaised||\'\',stage:c.fundingStage||\'\'}));",s);'
          "console.log(JSON.stringify(s.__n));")
    out = subprocess.run(["node", "-e", js, str(ROOT / "data.js")],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main() -> int:
    companies = load_companies()
    compiled = {ship: alumni_patterns(rx) for ship, rx in SHIPS.items()}

    origins: dict[str, list] = {s: [] for s in SHIPS}
    for c in companies:
        # founder field first (highest precision), then description
        for field, weight in (("founder", "founder-field"), ("description", "description")):
            text = c[field]
            if not text:
                continue
            for ship, pats in compiled.items():
                # skip if this company IS the mother ship
                if re.fullmatch(SHIPS[ship], c["name"].lower().replace(" ", " ")) or \
                   c["name"].lower() in ("spacex", "tesla", "anduril industries", "palantir", "apple", "waymo", "rivian", "blue origin", "boston dynamics"):
                    continue
                for p in pats:
                    m = p.search(text)
                    if m:
                        i = m.start()
                        ev = text[max(0, i - 60):i + 90].strip()
                        if not any(e["name"] == c["name"] for e in origins[ship]):
                            origins[ship].append({
                                "name": c["name"], "sector": c["sector"],
                                "raised": c["raised"], "stage": c["stage"],
                                "evidence": ev, "via": weight,
                            })
                        break

    for s in origins:
        origins[s].sort(key=lambda x: x["name"])

    total = len({e["name"] for v in origins.values() for e in v})
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": ("Companies in the database whose recorded founders carry explicit "
                 "alumni provenance. Evidence is quoted verbatim from the record; "
                 "a mother-ship mention without alumni context does not count."),
        "total_companies": total,
        "origins": {s: {"count": len(v), "companies": v}
                    for s, v in sorted(origins.items(), key=lambda kv: -len(kv[1]))
                    if v},
    }

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    OUT.write_text(
        f"// Founder Diaspora — auto-generated by scripts/build_diaspora.py, {stamp}\n"
        f"const FOUNDER_DIASPORA = {json.dumps(payload, indent=1, ensure_ascii=False)};\n")

    print(f"{total} distinct companies with alumni-founded provenance")
    for s, v in sorted(origins.items(), key=lambda kv: -len(kv[1])):
        if v:
            print(f"  {s:<28}{len(v):>3}  e.g. {', '.join(x['name'] for x in v[:5])}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
