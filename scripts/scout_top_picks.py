#!/usr/bin/env python3
"""
ROS Frontier-Tech Headhunter — Active Scout.

Mission: every week, surface the 5 most exciting frontier-tech companies
that are NOT yet in the ROS database, with a 150-word briefing per pick.

This is NOT a passive aggregator. It applies opinionated quality filtering
across 7 dimensions, ranks aggressively, and writes a memo Stephen can
read in 5 minutes Monday morning.

Inputs:
  - data/discovery_queue_auto.json  (Form D + VC portfolio + newsletter)
  - data/darpa_programs_auto.json   (DARPA performers not in DB)
  - data/form_d_filings_auto.json   (raw fundraises)
  - data/patent_velocity_auto.json  (cross-reference for tech depth)

Output:
  - data/scout_briefing_auto.json   (top 5 picks + briefings + reject pile)
  - data/scout_briefing_auto.js     (script-tag loadable)

7-DIMENSION QUALITY SCORE (each 0-10):
  1. capital_quality   — Quality of investors (top-tier frontier VCs?)
  2. magnitude         — Size of fundraise / DARPA $ (ambition signal)
  3. tech_depth        — Patent activity, DARPA program complexity
  4. frontier_fit      — How squarely in frontier-tech (defense/space/etc)
  5. stealth_signal    — Recently emerged + low public profile = found early
  6. founder_signal    — Founder pedigree heuristics (when extractable)
  7. excitement        — Gestalt: would Vance write about this?

Total /70. Picks with score ≥ 40 get briefings. Top 5 are "this week's elite".
"""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_JSON = DATA / "scout_briefing_auto.json"
OUT_JS = DATA / "scout_briefing_auto.js"

# ────────────────────────────────────────────────────────────
# Source-quality maps (drive the capital_quality dimension)

ELITE_VCS = {
    "founders fund", "lux capital", "lux", "andreessen horowitz", "a16z",
    "khosla ventures", "khosla", "sequoia", "sequoia capital",
    "8vc", "general catalyst", "thrive capital",
    "dcvc", "shield capital", "anduril ventures", "av",
    "lower carbon", "cantos", "harpoon", "bedrock",
    "kleiner perkins", "bessemer", "first round",
    "lightspeed", "greylock", "index ventures", "playground global",
    "in-q-tel", "iqt", "paypal mafia",
    "trousdale", "fusion fund", "riot ventures", "pillar vc",
    "decisive point", "razor's edge", "8090", "pritzker military",
}

GOOD_VCS = {
    # Strong but not elite
    "y combinator", "yc", "atomic", "unusual ventures", "spark capital",
    "social capital", "draper", "menlo ventures", "battery", "norwest",
    "general atlantic", "tiger global", "softbank", "insight",
    "mayfield", "redpoint", "scale venture", "trinity ventures",
    "true ventures", "u.s. venture partners",
}

# Frontier-tech sectors (high-fit signal)
FRONTIER_SECTORS = {
    "Defense & Security", "Space & Aerospace", "Nuclear Energy",
    "Fusion Energy", "AI & Compute", "Robotics & Manufacturing",
    "Quantum Computing", "Biotech & Health", "Climate & Energy",
    "Chips & Semiconductors", "Supersonic & Hypersonic",
    "Advanced Manufacturing", "Critical Minerals",
}

# Megaprime / SI / govt-lab patterns to suppress + KNOWN SUBSIDIARIES
# of large defense primes (often surface in DARPA but are NOT startups)
SUPPRESS_PATTERNS = [
    "lockheed", "raytheon", "northrop", "boeing", "general dynamics",
    "bae systems", "bae plc", "saic", "leidos", "caci", "mantech",
    "l3harris", "l3 communications", "booz allen", "accenture",
    "deloitte", "kpmg", "mckinsey", "pwc", "kbr",
    "university", "college", "institute of tech", "national lab",
    "sandia", "mit lincoln", "aerospace corp", "mitre", "sri international",
    "johns hopkins", "georgia tech research", "research foundation",
    "battelle memorial", "argonne", "lawrence livermore",
    "department of", "office of", "agency for", "bureau of",
    "u.s. government", "us government",
    # Defense-svc shops (not VC-backed startups)
    "securigence", "strategic analysis", "ecs federal", "system high",
    "schafer government", "two six labs", "peraton", "engility",
    "scientific applications", "perspecta", "ssr",
    "radiance technologies", "applied physical sciences",
    "four points technology",
    # Subsidiaries of mega-primes (NOT independent startups)
    "blue canyon",                  # Raytheon
    "seakr engineering",            # L3Harris
    "aurora flight",                # Boeing
    "millennium space",             # Boeing
    "general atomics",              # General Atomics is private but >$5B mega
    "kratos defense",               # Public co
    "dynetics",                     # Leidos
    "stratasys", "stratus",         # Random false matches we'd want to add
    # Public DARPA performers we know are giants
    "raytheon technologies",
]


def normalize(name):
    if not name: return ""
    s = name.lower().strip()
    s = re.sub(r'[,.]?\s+(inc|llc|ltd|limited|corp|corporation|incorporated|gmbh|co)\.?$', '', s)
    s = re.sub(r'[\s\-_\.]+', ' ', s)
    return s.strip()


def is_suppressed(name):
    n = name.lower()
    return any(p in n for p in SUPPRESS_PATTERNS)


# ────────────────────────────────────────────────────────────
# Loaders


def load_existing_companies():
    src = (ROOT / "data.js").read_text(encoding="utf-8", errors="replace")
    names = set()
    for m in re.finditer(r'name:\s*"([^"]+)"', src):
        names.add(normalize(m.group(1)))
    return names


def load_company_data():
    """Pull fielded data per ROS company (sector, founder, etc.) for use
    in cross-reference lookups."""
    src = (ROOT / "data.js").read_text(encoding="utf-8", errors="replace")
    m = re.search(r'const COMPANIES\s*=\s*\[', src)
    if not m: return {}
    # Brace-aware extract
    start = m.end() - 1
    depth = 0
    in_str = False
    str_q = None
    i = start
    while i < len(src):
        ch = src[i]
        nx = src[i + 1] if i + 1 < len(src) else ''
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = src[start:i + 1]
                    break
        i += 1
    else:
        return {}

    by_name = {}
    obj_depth = 0
    obj_start = None
    in_str = False
    str_q = None
    for i, ch in enumerate(block):
        if in_str:
            if ch == '\\': continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '{':
                if obj_depth == 0: obj_start = i
                obj_depth += 1
            elif ch == '}':
                obj_depth -= 1
                if obj_depth == 0 and obj_start is not None:
                    obj = block[obj_start:i + 1]
                    nm = re.search(r'name:\s*"([^"]+)"', obj)
                    if nm:
                        by_name[normalize(nm.group(1))] = obj
                    obj_start = None
    return by_name


# ────────────────────────────────────────────────────────────
# Scoring


def score_capital_quality(signals):
    """0-15. Heavily weights elite VC backing — the highest-conviction signal.
    A known elite VC having added a company to its portfolio = real startup,
    real frontier-tech bet, real check size."""
    text = " ".join((s.get("vc", "") + " " + s.get("source", "") + " " + s.get("issuerName", ""))
                    for s in signals).lower()
    for vc in ELITE_VCS:
        if vc in text:
            return 15  # Capped higher than other dimensions
    for vc in GOOD_VCS:
        if vc in text:
            return 8
    # Form D with real $ but no VC info: medium signal
    if any(s.get("source") == "Form D filing" for s in signals):
        return 5
    return 0


def score_magnitude(signals):
    """0-10. $$ raised (Form D) or DARPA $$. CAPPED for DARPA-only signals
    above $50M because that suggests a defense prime, not a startup."""
    max_amt = 0
    is_darpa_only = all(
        s.get("source") in ("DARPA performer", "DARPA")
        for s in signals
    )
    for s in signals:
        amt = s.get("amount", 0) or 0
        if isinstance(amt, str):
            try: amt = float(amt)
            except: amt = 0
        if amt > max_amt: max_amt = amt
        if s.get("totalAwarded"):
            if s["totalAwarded"] > max_amt: max_amt = s["totalAwarded"]
    # CRITICAL: DARPA-only candidates with massive $ are usually primes
    if is_darpa_only and max_amt >= 200e6:
        return 2  # Suspect prime, not startup
    if max_amt >= 100e6: return 8
    if max_amt >= 50e6: return 7
    if max_amt >= 20e6: return 6
    if max_amt >= 5e6: return 4
    if max_amt >= 1e6: return 2
    return 0


def score_tech_depth(signals, name, patent_data):
    """0-10. Patent activity + DARPA program complexity."""
    score = 0
    # DARPA programs
    for s in signals:
        progs = s.get("programs") or []
        if progs:
            # Real DARPA programs (HAWC, BLACKJACK, etc.) = serious tech
            REAL_PROGRAMS = {"HAWC", "BLACKJACK", "OPS-5G", "LONGSHOT", "ALIAS",
                            "GAMBIT", "GLIDE", "REMA", "SubT", "SyNAPSE"}
            if any(p.upper() in REAL_PROGRAMS for p in progs):
                score += 6
                break
            score += min(4, len(progs) * 1.5)
        if s.get("awardCount", 0) >= 5:
            score += 2
            break
    # Patent count cross-reference
    nm = normalize(name)
    for p in patent_data:
        if normalize(p["company"]) == nm:
            qoq = p.get("qoqChangeNum", 0) or 0
            if qoq > 50: score = max(score, 8)
            elif qoq > 20: score = max(score, 6)
            else: score = max(score, 4)
            break
    return min(10, score)


def score_frontier_fit(signals, suggested_sector):
    """0-10. Frontier-tech relevance from sector + keywords."""
    # Direct frontier sector match
    if suggested_sector in FRONTIER_SECTORS:
        return 10
    # Keyword scan in contexts
    text = " ".join(s.get("context", "") + " " + s.get("issuerName", "")
                    for s in signals).lower()
    FRONTIER_KW = ["defense", "drone", "missile", "satellite", "rocket",
                   "nuclear", "fusion", "reactor", "quantum", "biotech",
                   "robot", "autonomous", "hypersonic", "aerospace",
                   "semiconductor", "chip", "fabless", "manufacturing",
                   "sensor", "lidar", "radar", "isr", "directed energy",
                   "neural", "embodied", "foundation model"]
    matches = sum(1 for kw in FRONTIER_KW if kw in text)
    if matches >= 5: return 9
    if matches >= 3: return 7
    if matches >= 1: return 4
    return 0


def score_stealth_signal(candidate):
    """0-10. Bonus for recently emerged + low-profile. We approximate via:
    - Recent date on signals (last 30 days = high stealth)
    - Single-source (newsletters miss = means it's not over-covered)
    """
    score = 0
    most_recent = None
    for s in candidate.get("signals", []):
        d = s.get("date") or s.get("articleDate")
        if d:
            # Try parse
            for fmt in ("%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %Z",
                       "%a, %d %b %Y %H:%M:%S %z"):
                try:
                    dt = datetime.strptime(d.strip()[:30], fmt)
                    if most_recent is None or dt > most_recent:
                        most_recent = dt
                    break
                except (ValueError, TypeError):
                    continue
    if most_recent:
        days_ago = (datetime.now() - most_recent.replace(tzinfo=None)).days
        if days_ago < 14: score += 6
        elif days_ago < 30: score += 4
        elif days_ago < 90: score += 2

    # Single source = high stealth (only one VC has it, no media coverage)
    if len(candidate.get("sources", [])) == 1:
        score += 4
    elif len(candidate.get("sources", [])) >= 3:
        # If many newsletters mention, less stealthy — but more validated
        score += 1
    return min(10, score)


def score_excitement(candidate, capital_q, frontier_fit, stealth):
    """0-10. Gestalt: combination of validated capital, real tech, surprise."""
    # If high capital + high frontier fit + high stealth = exciting
    composite = (capital_q + frontier_fit + stealth) / 3
    return round(composite, 1)


# ────────────────────────────────────────────────────────────
# Auto-briefing generator


def generate_briefing(c):
    """Generate a 100-150 word briefing in Stephen's voice. Each pick gets
    a hook, capital, tech, why-now, and a question to ask the founder."""
    name = c["name"]
    score = c["score"]
    sector = c.get("suggestedSector") or "frontier tech"
    signals = c.get("signals", [])
    sources = c.get("sources", [])

    # Hook line
    hook_pieces = []
    capital_q = c.get("dimensions", {}).get("capital_quality", 0)
    magnitude = c.get("dimensions", {}).get("magnitude", 0)
    tech_depth = c.get("dimensions", {}).get("tech_depth", 0)

    # Capital line
    vcs_seen = set()
    for s in signals:
        if "vc" in s and s["vc"]:
            vcs_seen.add(s["vc"])
        elif "source" in s and "VC portfolio:" in (s.get("source") or ""):
            vcs_seen.add(s["source"].replace("VC portfolio:", "").strip())
    capital_line = ""
    if vcs_seen:
        capital_line = f"Backing: {', '.join(sorted(vcs_seen)[:3])}."

    # Magnitude / fundraise line
    money_line = ""
    largest_amt = 0
    largest_amt_fmt = ""
    largest_date = ""
    for s in signals:
        amt = s.get("amount", 0) or s.get("totalAwarded", 0) or 0
        if amt and amt > largest_amt:
            largest_amt = amt
            largest_amt_fmt = s.get("amountFmt") or s.get("totalAwardedFormatted") or fmt_amount(amt)
            largest_date = s.get("date", "")
    if largest_amt >= 1e6:
        if any(s.get("source") == "Form D filing" for s in signals):
            money_line = f"SEC Form D filed for {largest_amt_fmt}{' on ' + largest_date if largest_date else ''}."
        elif "DARPA" in str(signals[0]):
            money_line = f"DARPA contracts: {largest_amt_fmt}."
        else:
            money_line = f"Capital signal: {largest_amt_fmt}."

    # Why-now (the headhunter angle)
    why_now = ""
    if c["dimensions"].get("stealth_signal", 0) >= 6:
        why_now = "Surfaced in just one source — early intel, before the rest of the market."
    elif len(sources) >= 2:
        why_now = "Multiple independent signals corroborate — high-conviction find."
    elif tech_depth >= 6:
        why_now = "Tech depth signals (patents/DARPA programs) suggest real engineering substance."
    else:
        why_now = "Worth a closer look this week."

    # Question to ask
    question = ""
    if "Defense" in sector or "Space" in sector:
        question = "Ask: What's the dual-use commercial wedge before the gov-only deal flow takes over?"
    elif "AI" in sector or "Robot" in sector:
        question = "Ask: What's the real-world deployment timeline beyond demos?"
    elif "Nuclear" in sector or "Fusion" in sector:
        question = "Ask: What does the regulatory critical path look like, and who's the first commercial customer?"
    elif "Biotech" in sector or "Health" in sector:
        question = "Ask: What's the FDA path and what's the gap until first revenue?"
    else:
        question = "Ask: Who's the first commercial customer, and how big is the contract?"

    # Source attribution
    src_chips = ", ".join(sources)

    # Compose
    brief = f"""**{name}** — {sector}.

{money_line} {capital_line}

{why_now}

{question}

Source: {src_chips}. Score {score:.0f}/70."""
    return brief.strip()


def fmt_amount(n):
    if not n: return ""
    if n >= 1e9: return f"${n/1e9:.1f}B"
    if n >= 1e6: return f"${n/1e6:.0f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"


# ────────────────────────────────────────────────────────────
# DARPA enrichment: pull non-ROS frontier-tech-plausible performers


def darpa_candidates(known):
    fp = DATA / "darpa_programs_auto.json"
    if not fp.exists(): return []
    d = json.load(open(fp))
    out = []
    for p in d.get("performers", []):
        if p.get("isRosCompany"): continue
        name = p["performer"]
        if normalize(name) in known: continue
        if is_suppressed(name): continue
        if (p.get("totalAwarded") or 0) < 5e6:
            continue  # min $5M threshold for DARPA-only signal
        out.append({
            "name": name,
            "score": 0,
            "sources": ["DARPA"],
            "signals": [{
                "source": "DARPA performer",
                "totalAwarded": p["totalAwarded"],
                "totalAwardedFormatted": p.get("totalAwardedFormatted"),
                "awardCount": p["awardCount"],
                "programs": p.get("programs", []),
                "date": p.get("lastDate"),
                "verifyUrl": (p.get("topAwards") or [{}])[0].get("verifyUrl"),
            }],
            "suggestedSector": "Defense & Security",
        })
    return out


# ────────────────────────────────────────────────────────────
# Main


def main():
    print("=" * 64)
    print("ROS Frontier-Tech Headhunter · Active Scout")
    print("=" * 64)

    known = load_existing_companies()
    print(f"  Existing roster: {len(known)} companies")

    # Pull patent velocity for tech_depth cross-references
    patent_data = []
    pv = DATA / "patent_velocity_auto.json"
    if pv.exists():
        patent_data = json.load(open(pv))

    # 1. Pull candidates from existing discovery queue (Form D + VC + newsletters)
    queue = []
    qp = DATA / "discovery_queue_auto.json"
    if qp.exists():
        q = json.load(open(qp))
        queue = q.get("candidates", [])
    print(f"  Discovery queue: {len(queue)} candidates")

    # 2. Add DARPA performers not yet in queue
    darpa = darpa_candidates(known)
    queue_names = {normalize(c["name"]) for c in queue}
    darpa_new = [d for d in darpa if normalize(d["name"]) not in queue_names]
    print(f"  DARPA performers (new): {len(darpa_new)}")
    queue.extend(darpa_new)

    # 3. Filter out suppressed (megaprimes, SIs, universities)
    queue = [c for c in queue if not is_suppressed(c["name"])]
    print(f"  After suppression filter: {len(queue)} candidates")

    # 4. Score each candidate across 7 dimensions
    print()
    for c in queue:
        signals = c.get("signals", [])
        sector = c.get("suggestedSector")
        d = {
            "capital_quality": score_capital_quality(signals),
            "magnitude": score_magnitude(signals),
            "tech_depth": score_tech_depth(signals, c["name"], patent_data),
            "frontier_fit": score_frontier_fit(signals, sector),
            "stealth_signal": score_stealth_signal(c),
            "founder_signal": 0,  # Placeholder — needs founder-data source
        }
        d["excitement"] = score_excitement(c, d["capital_quality"],
                                            d["frontier_fit"],
                                            d["stealth_signal"])
        c["dimensions"] = d
        c["score"] = sum(d.values())

    # 5. Rank + select top picks
    queue.sort(key=lambda x: -x["score"])
    top_picks = [c for c in queue if c["score"] >= 25][:5]
    runner_up = [c for c in queue if c["score"] >= 15 and c not in top_picks][:10]
    rejected = [c for c in queue if c not in top_picks and c not in runner_up]

    print(f"  ⭐ Top picks (score ≥25): {len(top_picks)}")
    print(f"  → Runners-up (score 15-24): {len(runner_up)}")
    print(f"  ✗ Rejected (low score):   {len(rejected)}")

    # 6. Generate briefings for top picks
    for c in top_picks:
        c["briefing"] = generate_briefing(c)

    # 7. Output
    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weekOf": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "summary": {
            "rosterSize": len(known),
            "candidatesScreened": len(queue) + len(darpa),
            "topPicks": len(top_picks),
            "runnerUp": len(runner_up),
            "rejected": len(rejected),
        },
        "topPicks": top_picks,
        "runnersUp": [{
            "name": c["name"],
            "score": c["score"],
            "dimensions": c["dimensions"],
            "sources": c["sources"],
            "suggestedSector": c.get("suggestedSector"),
            "signals": c["signals"][:2],
        } for c in runner_up],
        "rejectedCount": len(rejected),
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    js = (
        f"// Auto-generated from {OUT_JSON.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const SCOUT_BRIEFING_AUTO = {json.dumps(out, indent=2, default=str)};\n"
        f"if (typeof window !== 'undefined') window.SCOUT_BRIEFING_AUTO = SCOUT_BRIEFING_AUTO;\n"
    )
    OUT_JS.write_text(js)

    print()
    print(f"✅ Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"✅ Wrote {OUT_JS.relative_to(ROOT)}")
    print()
    if top_picks:
        print("=" * 64)
        print("THIS WEEK'S TOP PICKS")
        print("=" * 64)
        for i, c in enumerate(top_picks, 1):
            print()
            print(f"#{i} — {c['name']}  ({c['score']:.0f}/70)")
            print(f"   Sector: {c.get('suggestedSector', 'unclassified')}")
            d = c["dimensions"]
            print(f"   Capital:{d['capital_quality']:.0f} Magnitude:{d['magnitude']:.0f} TechDepth:{d['tech_depth']:.0f} "
                  f"FrontierFit:{d['frontier_fit']:.0f} Stealth:{d['stealth_signal']:.0f}")
            print()
            print(c["briefing"])
            print("─" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
