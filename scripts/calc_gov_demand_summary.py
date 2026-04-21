#!/usr/bin/env python3
"""
Aggregate GOV_DEMAND_SUMMARY per sector from demand_signals_auto.js,
sam_contracts_aggregated.json, and sbir_awards_auto.json.

Output: data/gov_demand_summary_auto.json
Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_PATH = DATA_DIR / "gov_demand_summary_auto.json"


def safe_json(name):
    p = DATA_DIR / name
    if not p.exists(): return []
    try: return json.load(open(p))
    except Exception: return []


def load_js_array(name):
    """Extract first [...] array from a data/*.js file."""
    p = DATA_DIR / name
    if not p.exists(): return []
    text = p.read_text()
    m = re.search(r"=\s*(\[)", text)
    if not m: return []
    start = m.start(1)
    depth = 0; in_str = False; sc = None; esc = False
    end = None
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
            if depth == 0: end = i; break
    if end is None: return []
    block = text[start:end+1]
    block = re.sub(r"([{,]\s*)([A-Za-z_][\w]*)\s*:", r'\1"\2":', block)
    block = re.sub(r",(\s*[\]}])", r"\1", block)
    try: return json.loads(block)
    except Exception: return []


SECTOR_MAP = {
    "Defense & Security":       {"icon": "🛡️", "color": "#dc2626",
                                  "keywords": ["defense","military","weapon","uas","drone","counter-drone","pentagon"]},
    "Nuclear Energy":            {"icon": "⚛️", "color": "#f59e0b",
                                  "keywords": ["nuclear","reactor","smr","microreactor","fission","fusion"]},
    "Space & Aerospace":         {"icon": "🚀", "color": "#3b82f6",
                                  "keywords": ["space","satellite","launch","orbital","rocket","nasa","space force"]},
    "AI & Autonomy":             {"icon": "🤖", "color": "#8b5cf6",
                                  "keywords": ["ai","machine learning","autonomous","artificial intelligence"]},
    "Chips & Semiconductors":    {"icon": "💾", "color": "#06b6d4",
                                  "keywords": ["chips","semiconductor","microelectronics","silicon","foundry"]},
    "Biotech & Health":          {"icon": "🧬", "color": "#22c55e",
                                  "keywords": ["biotech","pharma","clinical","drug","therapeutics"]},
    "Climate & Energy":          {"icon": "🌱", "color": "#84cc16",
                                  "keywords": ["climate","battery","energy","grid","hydrogen","geothermal"]},
    "Quantum Computing":         {"icon": "⚡", "color": "#a855f7",
                                  "keywords": ["quantum"]},
    "Supersonic & Hypersonic":   {"icon": "🛩️", "color": "#ef4444",
                                  "keywords": ["hypersonic","supersonic","scramjet","mach"]},
    "Robotics & Manufacturing":  {"icon": "🦾", "color": "#f97316",
                                  "keywords": ["robot","humanoid","manufacturing","additive","automation"]},
}


def sector_of(text):
    t = text.lower()
    for sec, meta in SECTOR_MAP.items():
        if any(k in t for k in meta["keywords"]):
            return sec
    return "Other"


def main():
    demand = load_js_array("demand_signals_auto.js")
    contracts = safe_json("sam_contracts_aggregated.json") or safe_json("gov_contracts_aggregated.json") or []
    sbir = safe_json("sbir_awards_auto.json") or []

    counts = defaultdict(lambda: {"demand": 0, "contracts": 0, "sbir": 0, "examples": []})

    for d in demand:
        sec = sector_of((d.get("title") or "") + " " + (d.get("description") or ""))
        counts[sec]["demand"] += 1
        if len(counts[sec]["examples"]) < 3:
            counts[sec]["examples"].append({
                "type": "demand_signal",
                "title": (d.get("title") or "")[:120],
                "agency": d.get("agency", ""),
            })
    for c in contracts:
        sec = sector_of((c.get("title") or "") + " " + (c.get("description") or ""))
        counts[sec]["contracts"] += 1
    for s in sbir:
        sec = sector_of((s.get("topic") or "") + " " + s.get("agency", ""))
        counts[sec]["sbir"] += 1

    summary = {}
    for sec, data in counts.items():
        if sec == "Other": continue
        total = data["demand"] + data["contracts"] + data["sbir"]
        if total == 0: continue
        meta = SECTOR_MAP.get(sec, {"icon": "📋", "color": "#6b7280"})
        trend = (f"Gov demand index {total}: "
                 f"{data['demand']} active opportunities, "
                 f"{data['contracts']} contract awards, "
                 f"{data['sbir']} SBIR awards in the last 90 days.")
        summary[sec] = {
            "icon": meta["icon"],
            "color": meta["color"],
            "description": f"Federal demand across {sec.lower()}.",
            "trend": trend,
            "demandIndex": total,
            "activeOpps": data["demand"],
            "contractsAwarded": data["contracts"],
            "sbirAwards": data["sbir"],
            "examples": data["examples"],
        }

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sectors": summary,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote gov demand summary: {len(summary)} sectors → {OUT_PATH}")
    for sec, d in summary.items():
        print(f"    {sec:28s}  demand={d['demandIndex']:3d}  contracts={d['contractsAwarded']:3d}  sbir={d['sbirAwards']:3d}")


if __name__ == "__main__":
    main()
