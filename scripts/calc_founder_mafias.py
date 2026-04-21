#!/usr/bin/env python3
"""
Derive FOUNDER_MAFIAS from COMPANIES array — clusters companies by
the prior-employer heritage of their founders (SpaceX Mafia, Palantir
Mafia, OpenAI Mafia, etc.).

Output: data/founder_mafias_auto.json
Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_JS = Path(__file__).resolve().parent.parent / "data.js"
OUT_PATH = DATA_DIR / "founder_mafias_auto.json"

# Mafia name → keywords that appear in founder, description, or insight
# fields when a founder came from that parent company.
MAFIAS = {
    "SpaceX Mafia":        ["ex-SpaceX", "SpaceX alum", "former SpaceX", "SpaceX engineer", "SpaceX veteran"],
    "Palantir Mafia":      ["ex-Palantir", "Palantir alum", "former Palantir", "Palantir veteran"],
    "OpenAI Mafia":        ["ex-OpenAI", "OpenAI alum", "OpenAI co-founder", "former OpenAI"],
    "Anthropic Mafia":     ["ex-Anthropic", "Anthropic alum", "former Anthropic"],
    "Anduril Mafia":       ["ex-Anduril", "Anduril alum", "Anduril mafia", "former Anduril"],
    "Tesla Mafia":         ["ex-Tesla", "Tesla alum", "former Tesla"],
    "Google/DeepMind":     ["ex-Google", "Google alum", "ex-DeepMind", "DeepMind alum"],
    "Meta/Facebook":       ["ex-Meta", "Meta alum", "ex-Facebook", "Facebook alum", "ex-Meta FAIR"],
    "Apple Mafia":         ["ex-Apple", "Apple alum", "former Apple"],
    "NVIDIA Mafia":        ["ex-NVIDIA", "ex-Nvidia", "NVIDIA alum", "Nvidia alum"],
    "Stripe Mafia":        ["ex-Stripe", "Stripe alum"],
    "Amazon/AWS Mafia":    ["ex-Amazon", "AWS alum", "ex-AWS"],
    "Microsoft Mafia":     ["ex-Microsoft", "Microsoft Research"],
    "Rocket Lab Mafia":    ["ex-Rocket Lab"],
    "Blue Origin Mafia":   ["ex-Blue Origin"],
    "NASA / JPL":          ["ex-NASA", "NASA veteran", "ex-JPL", "JPL alum"],
    "DARPA Alumni":        ["ex-DARPA", "DARPA veteran", "DARPA program manager"],
    "Thiel Fellows":       ["Thiel Fellow", "Thiel fellowship"],
    "MIT CSAIL Spinouts":  ["MIT CSAIL", "MIT spinout"],
    "Stanford Spinouts":   ["Stanford spinout"],
    "Caltech Spinouts":    ["Caltech spinout", "Caltech alum"],
    "CMU Robotics":        ["CMU spinout", "Carnegie Mellon spinout"],
    "Y Combinator":        ["Y Combinator", "YC W", "YC S", "YC F"],
}


def parse_companies():
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i+1:end]
    entries = []
    idx = 0; n = len(block); d = 0; in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        s = idx
        while idx < n:
            c = block[idx]
            if esc: esc = False; idx += 1; continue
            if c == "\\" and in_str: esc = True; idx += 1; continue
            if in_str:
                if c == sc: in_str = False
                idx += 1; continue
            if c in "\"'": in_str = True; sc = c; idx += 1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: idx += 1; entries.append(block[s:idx]); break
            idx += 1
    result = []
    for e in entries:
        def gs(f):
            m = re.search(rf"\b{f}:\s*\"((?:[^\"\\]|\\.)*)\"", e)
            return m.group(1) if m else ""
        result.append({
            "name": gs("name"),
            "founder": gs("founder"),
            "sector": gs("sector"),
            "description": gs("description"),
            "insight": gs("insight"),
            "totalRaised": gs("totalRaised"),
            "valuation": gs("valuation"),
        })
    return result


def main():
    companies = parse_companies()
    print(f"  Scanning {len(companies)} companies for mafia affiliations")

    mafias = defaultdict(list)
    for c in companies:
        text = c["founder"] + " " + c["description"] + " " + c["insight"]
        for mafia, kws in MAFIAS.items():
            if any(k in text for k in kws):
                mafias[mafia].append({
                    "company": c["name"],
                    "sector": c["sector"],
                    "totalRaised": c["totalRaised"],
                    "valuation": c["valuation"],
                })

    payload = []
    for mafia, comps in sorted(mafias.items(), key=lambda x: -len(x[1])):
        if len(comps) < 2: continue  # need ≥2 to call it a mafia
        payload.append({
            "mafia": mafia,
            "count": len(comps),
            "companies": comps[:30],  # cap display
            "description": f"{len(comps)} companies with founding-team links to {mafia.replace(' Mafia','')}.",
        })

    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote {len(payload)} mafias → {OUT_PATH}")
    for m in payload[:5]:
        print(f"    {m['mafia']:25s} {m['count']:3d} companies")


if __name__ == "__main__":
    main()
