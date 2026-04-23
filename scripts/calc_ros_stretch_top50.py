#!/usr/bin/env python3
"""
ROS Fund — STRETCH TIER Top 50 Candidate Ranker
─────────────────────────────────────────────────────────────────────────
Ranks companies that are TOO BIG for a direct $100-250K check but still
worth building a relationship with (SPV / secondary / LP-to-their-lead /
content-for-access / next-round-access strategies).

Size window:
  • Raised $100M - $500M  (too big for seed, not yet growth/PE territory)
  • OR valuation $500M - $5B  (approaching-to-at unicorn)
  • Still private (IPO/SPAC/acquired excluded)

Stage scoring rewards Series A/B/C (not just Pre-Seed/Seed); capital
scoring rewards the $100-300M sweet spot; Frontier Index carries more
weight here than in seed-tier (0.25× vs 0.20×) because when you can't
check-size your way in, only conviction on the name matters.

Output:
  data/ros_stretch_scored.json  — full top-100 for deeper analysis

Re-run quarterly:
  python3 scripts/calc_ros_stretch_top50.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"

HOT_SECTORS = {
    "Defense & Security": 5, "Nuclear Energy": 5, "Space & Aerospace": 5,
    "Drones & Autonomous": 5, "Supersonic & Hypersonic": 5,
    "Quantum Computing": 4, "Chips & Semiconductors": 4,
    "Robotics & Manufacturing": 4, "Biotech & Health": 3,
    "Climate & Energy": 3, "AI & Software": 3,
    "Ocean & Maritime": 3, "Transportation": 2,
    "Infrastructure & Logistics": 2, "Consumer Tech": 1,
    "Housing & Construction": 2,
}

FOUNDER_MAFIA_KEYWORDS = [
    "ex-spacex", "spacex alum", "ex-palantir", "palantir alum",
    "ex-openai", "ex-anduril", "anduril alum", "ex-anthropic",
    "ex-tesla", "tesla alum", "ex-google", "deepmind alum",
    "ex-deepmind", "ex-nvidia", "ex-meta", "ex-apple", "ex-microsoft",
    "thiel fellow", "mit csail", "stanford spinout",
    "caltech spinout", "ex-nasa", "ex-darpa", "y combinator",
]


def parse_array(label, text):
    s = text.find(f"const {label} = [")
    if s < 0: return []
    i = text.find("[", s)
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
    block = text[i + 1:end]
    entries = []
    idx = 0; n = len(block); d = 0; in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        start = idx
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
                if d == 0: idx += 1; entries.append(block[start:idx]); break
            idx += 1
    return entries


def gs(entry, f):
    m = re.search(rf'\b{f}:\s*"((?:[^"\\]|\\.)*)"', entry)
    return m.group(1) if m else ""


def gn(entry, f):
    m = re.search(rf'\b{f}:\s*(-?[\d.]+)', entry)
    return float(m.group(1)) if m else None


def parse_usd(s):
    if not s: return 0
    sl = s.lower()
    fx = 1.0
    if s.startswith("€") or "eur" in sl: fx = 1.08
    elif "c$" in sl or "cad" in sl: fx = 0.74
    elif s.startswith("£") or "gbp" in sl: fx = 1.25
    elif "¥" in s or "jpy" in sl: fx = 0.0068
    elif "₹" in s or "cr" in sl:
        m = re.search(r"([\d.]+)\s*cr", sl)
        if m: return float(m.group(1)) * 10 / 83
    cleaned = re.sub(r"[^0-9.BMKT]", "", s.upper())
    m = re.match(r"([\d.]+)\s*([TBMK]?)", cleaned)
    if not m: return 0
    v = float(m.group(1))
    mu = {"T": 1_000_000, "B": 1000, "M": 1, "K": 0.001}.get(m.group(2), 1)
    return v * mu * fx


def qualifies_stretch(c):
    stage = (c.get("fundingStage") or "").lower()
    raised = parse_usd(c.get("totalRaised") or "")
    val = parse_usd(c.get("valuation") or "")
    if any(k in stage for k in ["ipo", "public", "spac", "acquired"]):
        return False
    val_str = (c.get("valuation") or "").lower()
    if any(k in val_str for k in ["cerberus", "blackstone", "kkr",
                                   "apollo-owned", "pe-owned"]):
        return False
    if raised > 500 or val > 5000: return False
    if raised < 100 and val < 500: return False
    return True


def stage_pts(stage):
    s = (stage or "").lower()
    if "series a" in s: return 20
    if "series b" in s: return 25
    if "series c" in s: return 20
    if "series d" in s: return 10
    if "growth" in s or "private" in s: return 12
    return 15


def capital_pts(m):
    if m is None: return 10
    if 100 <= m <= 300: return 25
    if 300 < m <= 450: return 15
    if m > 450: return 5
    return 8


def age_pts(founded):
    if not founded: return 0
    age = 2026 - founded
    if age <= 5: return 10
    if age <= 8: return 7
    if age <= 12: return 4
    return 0


def founder_mafia_pts(*texts):
    joined = " ".join(t or "" for t in texts).lower()
    for k in FOUNDER_MAFIA_KEYWORDS:
        if k in joined: return 5
    return 0


def main():
    src = DATA_JS.read_text()
    raw = parse_array("COMPANIES", src)
    scores_raw = parse_array("INNOVATOR_SCORES", src)
    field_notes_raw = parse_array("FIELD_NOTES", src)

    companies = []
    for e in raw:
        companies.append({
            "name": gs(e, "name"), "sector": gs(e, "sector"),
            "location": gs(e, "location"), "founder": gs(e, "founder"),
            "founded": int(gn(e, "founded") or 0),
            "fundingStage": gs(e, "fundingStage"),
            "totalRaised": gs(e, "totalRaised"),
            "valuation": gs(e, "valuation"),
            "description": gs(e, "description"),
            "insight": gs(e, "insight"),
        })

    scores_by = {gs(s, "company"): {
        "composite": gn(s, "composite") or 0,
        "govTraction": gn(s, "govTraction") or 0,
        "technicalMoat": gn(s, "technicalMoat") or 0,
    } for s in scores_raw}

    met_founders = set()
    for fn in field_notes_raw:
        co = gs(fn, "company")
        if co and gs(fn, "pullQuote"): met_founders.add(co)

    form_d_by = {}
    fdp = ROOT / "data" / "form_d_filings_auto.json"
    if fdp.exists():
        try:
            d = json.loads(fdp.read_text())
            for f in d.get("filings", []):
                prior = form_d_by.get(f["company"])
                if not prior or (f.get("filed_date", "") > prior.get("filed_date", "")):
                    form_d_by[f["company"]] = f
        except Exception:
            pass

    scored = []
    for c in companies:
        if not qualifies_stretch(c): continue
        name = c["name"]
        s = scores_by.get(name, {})
        fi = s.get("composite") or 0
        gt = s.get("govTraction") or 0
        tm = s.get("technicalMoat") or 0
        raised_m = parse_usd(c.get("totalRaised") or "")
        val_m = parse_usd(c.get("valuation") or "")

        pts = 0
        signals = []
        for typ, val, lbl in [
            ("stage", stage_pts(c.get("fundingStage", "")), c.get("fundingStage") or "—"),
            ("capital", capital_pts(raised_m), c.get("totalRaised") or "—"),
            ("age", age_pts(c.get("founded")), str(c.get("founded") or "—")),
            ("FI", round(fi / 4, 1), f"composite {fi:.1f}"),
            ("govTraction", gt, f"axis {gt}"),
            ("techMoat", tm, f"axis {tm}"),
        ]:
            pts += val
            if val: signals.append((typ, val, lbl))
        if name in form_d_by:
            pts += 15
            signals.append(("FORM_D", 15, f"filed {form_d_by[name].get('filed_date','')[:10]}"))
        if c.get("insight") and len(c["insight"]) > 40:
            pts += 10
            signals.append(("curated_insight", 10, "has ROS thesis"))
        mafia = founder_mafia_pts(c.get("founder", ""), c.get("description", ""),
                                   c.get("insight", ""))
        if mafia:
            pts += mafia
            signals.append(("mafia", mafia, ""))
        sp = HOT_SECTORS.get(c.get("sector", ""), 1)
        pts += sp
        signals.append(("sector", sp, c.get("sector", "—")))
        if name in met_founders:
            pts -= 25
            signals.append(("met_penalty", -25, "already met"))
        if not s:
            pts -= 5

        scored.append({
            "name": name, "score": pts, "signals": signals, "company": c,
            "raised_usd_m": raised_m, "val_usd_m": val_m,
            "form_d": form_d_by.get(name),
        })

    scored.sort(key=lambda x: -x["score"])
    top = scored[:50]

    print(f"Stretch-tier pool: {len(scored)} qualifying companies")
    print(f"{'#':<4}{'Score':<7}{'Company':<32}{'Stage':<12}"
          f"{'$M raised':<10}{'Val $M':<10}{'Sector':<22}")
    print("─" * 100)
    for i, r in enumerate(top, 1):
        c = r["company"]
        print(f"{i:<4}{r['score']:<7.1f}{r['name'][:30]:<32}"
              f"{(c.get('fundingStage') or '—')[:11]:<12}"
              f"{r['raised_usd_m']:<10.0f}{r['val_usd_m']:<10.0f}"
              f"{c.get('sector','')[:20]:<22}")

    (ROOT / "data" / "ros_stretch_scored.json").write_text(
        json.dumps([{
            "rank": i + 1, "name": r["name"], "score": r["score"],
            "company": r["company"], "signals": r["signals"],
            "form_d": r["form_d"],
        } for i, r in enumerate(scored[:100])], indent=2)
    )
    print(f"\nTop 100 → data/ros_stretch_scored.json")


if __name__ == "__main__":
    main()
