#!/usr/bin/env python3
"""
ROS Fund — Top 50 Cold-Outreach Candidate Ranker
─────────────────────────────────────────────────────────────────────────
Combs COMPANIES + INNOVATOR_SCORES + FIELD_NOTES + Form D filings + SBIR
bid-fit + gov contracts and produces a ranked list of $100–250K-check
candidates for the Rational Optimist Society fund.

Filters OUT companies too large for our check to matter (IPO'd, public,
SPAC, acquired, raised > $200M, valuation > $1.5B).

Scores every remaining company on an 11-factor model — see weights in
ROS_FUND_TOP50.md. Penalizes founders already in FIELD_NOTES warm
network so the output skews toward COLD outreach.

Output:
  ROS_FUND_TOP50.md  — polished markdown brief
  /tmp/ros_fund_scored.json — full ranked list (for further analysis)

Run:  python3 scripts/calc_ros_fund_top50.py
Re-run quarterly as companies raise and get acquired.
"""

import json
import os
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
    "Transportation": 2, "Ocean & Maritime": 3,
    "Consumer Tech": 1, "Housing & Construction": 2,
    "Infrastructure & Logistics": 2,
}

FOUNDER_MAFIA_KEYWORDS = [
    "ex-spacex", "spacex alum", "former spacex",
    "ex-palantir", "palantir alum",
    "ex-openai", "openai co-founder",
    "ex-anduril", "anduril alum", "ex-anthropic",
    "ex-tesla", "tesla alum",
    "ex-google", "deepmind alum", "ex-deepmind",
    "ex-nvidia", "ex-meta", "ex-apple", "ex-microsoft",
    "thiel fellow", "mit csail", "stanford spinout",
    "caltech spinout", "cmu spinout",
    "ex-nasa", "jpl alum", "ex-darpa",
    "y combinator",
]

# ───────────────────────────────────────────────────────────────
# Data loading
# ───────────────────────────────────────────────────────────────

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
    """Handle C$, €, £, ¥, ₹. Return amount in millions USD."""
    if not s: return 0
    s_lower = s.lower()
    fx = 1.0
    if s.startswith("€") or "eur" in s_lower: fx = 1.08
    elif "c$" in s_lower or "cad" in s_lower: fx = 0.74
    elif s.startswith("£") or "gbp" in s_lower: fx = 1.25
    elif "¥" in s or "jpy" in s_lower: fx = 0.0068
    elif "₹" in s or "cr" in s_lower or "inr" in s_lower:
        m = re.search(r"([\d.]+)\s*cr", s_lower)
        if m: return float(m.group(1)) * 10 / 83
    cleaned = re.sub(r"[^0-9.BMKT]", "", s.upper())
    m = re.match(r"([\d.]+)\s*([TBMK]?)", cleaned)
    if not m: return 0
    val = float(m.group(1))
    mult = {"T": 1_000_000, "B": 1000, "M": 1, "K": 0.001}.get(m.group(2), 1)
    return val * mult * fx

# ───────────────────────────────────────────────────────────────
# Scoring
# ───────────────────────────────────────────────────────────────

def stage_pts(stage):
    s = (stage or "").lower()
    if "pre-seed" in s or "preseed" in s: return 30
    if "seed" in s and "series" not in s: return 25
    if "series a" in s: return 18
    if "series b" in s: return 8
    if "series c" in s: return 3
    if any(k in s for k in ["series d", "series e", "series f", "series g",
                             "ipo", "public", "spac", "acquired", "growth", "private"]):
        return 0
    return 12

def capital_pts(m):
    if m is None: return 10
    if m < 10: return 25
    if m < 30: return 20
    if m < 75: return 12
    if m < 150: return 5
    return 0

def age_pts(founded):
    if not founded or founded < 2005: return 0
    age = 2026 - founded
    if age <= 4: return 10
    if age <= 6: return 7
    if age <= 8: return 4
    if age <= 10: return 2
    return 0

def founder_mafia_pts(*texts):
    joined = " ".join(t or "" for t in texts).lower()
    for k in FOUNDER_MAFIA_KEYWORDS:
        if k in joined: return 5
    return 0

def disqualify(c):
    stage = (c.get("fundingStage") or "").lower()
    raised = parse_usd(c.get("totalRaised") or "")
    val = parse_usd(c.get("valuation") or "")
    if any(k in stage for k in ["ipo", "public", "spac", "acquired", "growth",
                                 "series e", "series f", "series g"]):
        return True
    if raised > 200: return True
    if val > 1500: return True
    val_str = (c.get("valuation") or "").lower()
    if any(k in val_str for k in ["cerberus", "blackstone", "kkr", "apollo-owned", "pe-owned"]):
        return True
    return False

def main():
    src = DATA_JS.read_text()
    companies_raw = parse_array("COMPANIES", src)
    scores_raw = parse_array("INNOVATOR_SCORES", src)
    field_notes_raw = parse_array("FIELD_NOTES", src)

    companies = []
    for e in companies_raw:
        companies.append({
            "name": gs(e, "name"), "sector": gs(e, "sector"),
            "location": gs(e, "location"), "state": gs(e, "state"),
            "founder": gs(e, "founder"),
            "founded": int(gn(e, "founded") or 0),
            "fundingStage": gs(e, "fundingStage"),
            "totalRaised": gs(e, "totalRaised"),
            "valuation": gs(e, "valuation"),
            "thesisCluster": gs(e, "thesisCluster"),
            "description": gs(e, "description"),
            "insight": gs(e, "insight"),
        })

    scores_by = {}
    for s in scores_raw:
        name = gs(s, "company")
        scores_by[name] = {
            "composite": gn(s, "composite") or 0,
            "govTraction": gn(s, "govTraction") or 0,
            "technicalMoat": gn(s, "technicalMoat") or 0,
        }

    met_founders = set()
    for fn in field_notes_raw:
        co = gs(fn, "company")
        if co and gs(fn, "pullQuote"):
            met_founders.add(co)

    # Form D filings
    form_d_by = {}
    form_d_path = ROOT / "data" / "form_d_filings_auto.json"
    if form_d_path.exists():
        try:
            d = json.loads(form_d_path.read_text())
            for f in d.get("filings", []):
                prior = form_d_by.get(f["company"])
                if not prior or (f.get("filed_date", "") > prior.get("filed_date", "")):
                    form_d_by[f["company"]] = f
        except Exception:
            pass

    # SBIR bid-fit
    sbir_bidfit_by = defaultdict(list)
    sbir_path = ROOT / "data" / "sbir_topics_auto.js"
    if sbir_path.exists():
        try:
            raw = sbir_path.read_text()
            m = re.search(r"=\s*(\[[\s\S]*?\])\s*;?\s*$", raw)
            if m:
                topics = json.loads(m.group(1))
                for t in topics:
                    for bf in (t.get("bidFit") or []):
                        sbir_bidfit_by[bf["company"]].append({
                            "topic": t.get("title", ""),
                            "score": bf["bid_fit_score"],
                            "agency": t.get("agency", ""),
                        })
        except Exception:
            pass

    scored = []
    for c in companies:
        if disqualify(c): continue
        name = c["name"]
        s = scores_by.get(name, {})
        fi = s.get("composite") or 0
        gt = s.get("govTraction") or 0
        tm = s.get("technicalMoat") or 0
        raised_m = parse_usd(c.get("totalRaised") or "")

        pts = 0
        signals = []
        for typ, val, desc in [
            ("stage", stage_pts(c.get("fundingStage", "")), c.get("fundingStage") or "—"),
            ("capital", capital_pts(raised_m), c.get("totalRaised") or "—"),
            ("age", age_pts(c.get("founded")), str(c.get("founded") or "—")),
            ("FI", round(fi / 5, 1), f"composite {fi:.1f}"),
            ("govTraction", gt, f"axis {gt}"),
            ("techMoat", tm, f"axis {tm}"),
        ]:
            pts += val
            if val: signals.append((typ, val, desc))

        if name in form_d_by:
            pts += 15
            signals.append(("FORM_D", 15, f"filed {form_d_by[name].get('filed_date','')[:10]}"))
        sbir_matches = sbir_bidfit_by.get(name, [])
        if sbir_matches:
            pts += 5
            top = max(sbir_matches, key=lambda x: x["score"])
            signals.append(("sbir_fit", 5, f"{top['score']:.0f} on {top['topic'][:40]}"))
        if c.get("insight") and len(c["insight"]) > 40:
            pts += 10
            signals.append(("curated_insight", 10, "has ROS thesis"))
        mafia = founder_mafia_pts(c.get("founder", ""), c.get("description", ""), c.get("insight", ""))
        if mafia:
            pts += mafia
            signals.append(("mafia", mafia, "ex-[FAANG|SpaceX|Palantir|Thiel]"))
        sect_pts = HOT_SECTORS.get(c.get("sector", ""), 1)
        pts += sect_pts
        signals.append(("sector", sect_pts, c.get("sector", "—")))
        if name in met_founders:
            pts -= 25
            signals.append(("met_penalty", -25, "already met (FIELD_NOTES)"))
        if not s:
            pts -= 5

        scored.append({
            "name": name, "score": pts, "signals": signals, "company": c,
            "sbir_matches": sbir_matches, "form_d": form_d_by.get(name),
            "raised_usd_m": raised_m,
        })

    scored.sort(key=lambda x: -x["score"])
    top50 = scored[:50]

    print(f"Ranked {len(scored)} / {len(companies)} companies")
    print(f"Top 50 generated. See ROS_FUND_TOP50.md for the full brief.\n")
    print(f"{'#':<4}{'Score':<7}{'Company':<32}{'Stage':<12}{'$M':<7}{'Sector':<24}")
    print("─" * 90)
    for i, r in enumerate(top50, 1):
        c = r["company"]
        print(f"{i:<4}{r['score']:<7.1f}{r['name'][:30]:<32}"
              f"{(c.get('fundingStage') or '—')[:11]:<12}"
              f"{r['raised_usd_m']:<7.1f}"
              f"{c.get('sector','')[:22]:<24}")

    out_path = ROOT / "ROS_FUND_TOP50.md"
    # A full markdown regeneration lives in the shell script that wraps
    # this. This main() prints the top-50 table to stdout and persists
    # the full ranking to disk for further analysis.
    (ROOT / "data" / "ros_fund_scored.json").write_text(
        json.dumps([{
            "rank": i + 1,
            "name": r["name"],
            "score": r["score"],
            "company": r["company"],
            "signals": r["signals"],
            "form_d": r["form_d"],
            "sbir_matches": r["sbir_matches"],
        } for i, r in enumerate(scored[:200])], indent=2)
    )
    print(f"\nFull top-200 written to data/ros_fund_scored.json")


if __name__ == "__main__":
    main()
