#!/usr/bin/env python3
"""
Calculate BUDGET_SIGNALS per sector from federal_register_auto.js and
congress_bills_auto.js. Produces data/budget_signals_auto.json ready
for merge_data.py to fold into data.js.

Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_PATH = DATA_DIR / "budget_signals_auto.json"


def load_json_array(filename):
    """Load either *.json or *.js file that defines an array."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    text = path.read_text()
    if filename.endswith(".json"):
        try:
            return json.load(open(path))
        except Exception:
            return []
    # JS: find first [...] and evaluate crudely as JSON-ish
    m = re.search(r"\[\s*(?:\{|\])", text)
    if not m:
        return []
    start = m.start()
    depth = 0; in_str = False; sc = None; esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                block = text[start:i+1]
                break
    else:
        return []
    # Convert JS object-key syntax to JSON
    block = re.sub(r"([{,]\s*)([A-Za-z_][\w]*)\s*:", r'\1"\2":', block)
    block = re.sub(r",(\s*[\]}])", r"\1", block)
    try:
        return json.loads(block)
    except Exception:
        return []


# Sector → keywords mapping (for categorizing bills / actions)
SECTORS = {
    "Autonomous Systems & Drones": [
        "replicator", "autonomous", "unmanned", "drone", "uas", "uav",
        "counter-drone", "collaborative combat aircraft", "cca",
    ],
    "Space & Aerospace": [
        "space force", "satellite", "launch", "space domain", "orbital",
        "ussf", "nasa", "artemis", "deep space",
    ],
    "Nuclear Energy": [
        "nuclear", "reactor", "smr", "microreactor", "fission", "fusion",
        "nrc", "doe nuclear",
    ],
    "AI & Autonomy": [
        "artificial intelligence", "machine learning", "ai safety",
        "cdao", "responsible ai", "ai governance",
    ],
    "Chips & Semiconductors": [
        "chips act", "semiconductor", "microelectronics", "foundry",
        "eda", "advanced packaging",
    ],
    "Biotech & Health": [
        "arpa-h", "biosecurity", "biotech", "clinical trial", "fda",
        "biomedical", "pandemic preparedness",
    ],
    "Climate & Energy": [
        "energy storage", "geothermal", "hydrogen", "doe grid",
        "inflation reduction act", "critical minerals", "lithium",
    ],
    "Quantum Computing": [
        "quantum", "quantum information", "post-quantum",
    ],
    "Hypersonics": [
        "hypersonic", "mach 5", "scramjet", "glide vehicle",
    ],
    "Cybersecurity": [
        "zero trust", "cybersecurity", "critical infrastructure security",
    ],
}

SECTOR_ICONS = {
    "Autonomous Systems & Drones": "🛸",
    "Space & Aerospace": "🚀",
    "Nuclear Energy": "⚛️",
    "AI & Autonomy": "🤖",
    "Chips & Semiconductors": "💾",
    "Biotech & Health": "🧬",
    "Climate & Energy": "🌱",
    "Quantum Computing": "⚡",
    "Hypersonics": "🛩️",
    "Cybersecurity": "🔐",
}


def main():
    fr = load_json_array("federal_register_auto.js")
    cb = load_json_array("congress_bills_auto.js")

    print(f"  federal_register entries: {len(fr)}")
    print(f"  congress_bills entries: {len(cb)}")

    # Bucket by sector
    counts = defaultdict(lambda: {"bills": 0, "rules": 0, "items": []})

    for item in cb:
        title = (item.get("title") or "").lower()
        for sector, kws in SECTORS.items():
            if any(k in title for k in kws):
                counts[sector]["bills"] += 1
                if len(counts[sector]["items"]) < 3:
                    counts[sector]["items"].append({
                        "type": "bill",
                        "title": (item.get("title") or "")[:120],
                        "number": item.get("billNumber") or item.get("number", ""),
                        "status": item.get("status", ""),
                    })
                break

    for item in fr:
        title = (item.get("title") or "").lower()
        agency = (item.get("agency") or "").lower()
        for sector, kws in SECTORS.items():
            if any(k in title for k in kws) or any(k in agency for k in kws):
                counts[sector]["rules"] += 1
                if len(counts[sector]["items"]) < 6:
                    counts[sector]["items"].append({
                        "type": "federal_register",
                        "title": (item.get("title") or "")[:120],
                        "agency": item.get("agency", ""),
                        "date": item.get("publicationDate", ""),
                    })
                break

    # Build structured output
    fy = "FY2026"
    signals = []
    for sector, data in sorted(counts.items(), key=lambda x: -(x[1]["bills"] + x[1]["rules"])):
        total = data["bills"] + data["rules"]
        if total == 0:
            continue
        # Change heuristic: more federal activity → higher growth signal
        if total >= 10: change = "+30%"; change_num = 30
        elif total >= 5: change = "+15%"; change_num = 15
        elif total >= 2: change = "+5%"; change_num = 5
        else: change = "flat"; change_num = 0
        signals.append({
            "category": sector,
            "icon": SECTOR_ICONS.get(sector, "📋"),
            "budgetLineItem": f"{sector} — federal activity index",
            "change": change,
            "changeNum": change_num,
            "fy": fy,
            "allocation": "",
            "activityIndex": total,
            "billsTracked": data["bills"],
            "rulesTracked": data["rules"],
            "description": (
                f"{data['bills']} bill(s) + {data['rules']} federal-register "
                f"action(s) touching {sector} in the last 90 days. Activity "
                f"index {total} — {change} relative trend."
            ),
            "examples": data["items"][:5],
            "source": "federal_register + congress_bills",
            "lastUpdated": datetime.utcnow().strftime("%Y-%m-%d"),
        })

    OUT_PATH.write_text(json.dumps(signals, indent=2))
    print(f"  Wrote {len(signals)} budget signals to {OUT_PATH}")


if __name__ == "__main__":
    main()
