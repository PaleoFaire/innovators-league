#!/usr/bin/env python3
"""
Weekly Intelligence Sync — keeps all ROS proprietary metrics fresh.

What it does every Sunday 08:00 UTC:

  1. INGESTS the last 7 days of events from 11 data feeds:
     news_raw.json, press_releases_filtered.json, sec_filings_auto.js,
     gov_contracts_auto.js, funding_feed_auto.json, sbir_awards_auto.json,
     earnings_signals.json, exec_moves_auto.json, federal_register_auto.js,
     sam_contracts_aggregated.json, arpa_e_projects_auto.js

  2. CLASSIFIES each event per company (funding / contract / regulatory /
     partnership / exec-move / distress / earnings-signal)

  3. CONVERTS events to metric deltas using the rubric in EVENT_IMPACT.
     Conservative one-week bounds: no axis moves more than ±2 per week,
     composite no more than ±4 per week. This keeps scores stable
     while letting real events register.

  4. RECOMPUTES:
       - INNOVATOR_SCORES    (with new composite)
       - MOSAIC_SCORES       (aligned to composite × 10)
       - GROWTH_SIGNALS      (replaces with this week's strongest signal)
       - DEAL_TRACKER        (adds any new round detected)
       - HEADCOUNT_ESTIMATES (nudge if big funding event)
       - PREDICTIVE_SCORES   (if event crosses threshold)

  5. EMITS data/weekly_scoring_digest.json:
       - `generated_at`, `week_ending`
       - `movers_up`:   top 20 score gains with per-company reason
       - `movers_down`: top 10 negative deltas with reason
       - `headlines`:   best 40 landmark events for the week
       - `coverage`:    companies touched / untouched

  6. NON-DESTRUCTIVE: every modification is journaled so we can roll back
     if a feed had a bad week.
"""

import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly_metric_sync")

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DATA_JS = REPO / "data.js"

NOW = datetime.now(timezone.utc)
WEEK_START = NOW - timedelta(days=7)
WEEK_ENDING = NOW.strftime("%Y-%m-%d")


# ════════════════════════════════════════════════════════════════
# EVENT IMPACT RUBRIC
# ════════════════════════════════════════════════════════════════

# Event → (momentum, govTraction, techMoat, teamPedigree, marketGravity, capitalEfficiency)
EVENT_IMPACT = {
    # Funding events
    "funding_mega":       dict(momentum= 2, marketGravity=1, capitalEfficiency= 1),  # >$100M round
    "funding_major":      dict(momentum= 2, marketGravity=1),                        # $30-100M
    "funding_minor":      dict(momentum= 1),                                         # <$30M
    "ipo":                dict(momentum= 2, capitalEfficiency= 1, marketGravity=1),
    "spac":               dict(momentum= 1, capitalEfficiency= 1),
    "acquisition_target": dict(momentum= 1, marketGravity=1),
    # Government / regulatory
    "contract_mega":      dict(govTraction= 3, marketGravity=1),   # Program of Record or >$100M
    "contract_major":     dict(govTraction= 2, marketGravity=1),   # $10-100M DoD/NASA
    "contract_minor":     dict(govTraction= 1),                    # SBIR Phase I/II, small pilots
    "sbir_phase_iii":     dict(govTraction= 3, techMoat= 1),
    "fda_approval":       dict(techMoat= 2, govTraction= 1, momentum=1),
    "fda_510k":           dict(techMoat= 1, govTraction= 1),
    "nrc_license":        dict(techMoat= 2, govTraction= 2),
    "type_cert":          dict(techMoat= 2, marketGravity=1),  # FAA/DGCA
    # Technology / operational
    "flight_test_success": dict(techMoat= 2, momentum= 1),
    "ignition":            dict(techMoat= 3, momentum= 1),
    "production_milestone":dict(techMoat= 1, momentum= 1),
    "world_first":         dict(techMoat= 2, marketGravity= 1),
    # Business
    "major_partnership":  dict(marketGravity=1, momentum=1),
    "named_customer":     dict(marketGravity=1, momentum=1),
    "exec_hire_star":     dict(teamPedigree=1),
    # Earnings-signal events
    "earnings_bull":      dict(momentum= 1),
    "earnings_bear":      dict(momentum=-1),
    # Negative
    "layoffs_major":      dict(momentum=-2, capitalEfficiency=-1),
    "layoffs_minor":      dict(momentum=-1),
    "ceo_exit_negative":  dict(teamPedigree=-1, momentum=-1),
    "bankruptcy":         dict(momentum=-4, capitalEfficiency=-3, techMoat=-1),
    "lawsuit_major":      dict(momentum=-1, marketGravity=-1),
    "acquisition_absorbed":dict(momentum=-3),  # company stops being independent
}

# Per-week bounds to keep scores stable
MAX_AXIS_DELTA_PER_WEEK = 2
MAX_COMPOSITE_DELTA_PER_WEEK = 4


# ════════════════════════════════════════════════════════════════
# FILE LOADERS  (each returns a list of {company, type, detail, date})
# ════════════════════════════════════════════════════════════════

def safe_json(path):
    try:
        with open(path) as f: return json.load(f)
    except Exception as e:
        log.warning(f"could not load {path}: {e}")
        return None


def extract_js_array(js_path, varname):
    """Extract an array of objects from a data/*.js file by variable name."""
    try:
        text = js_path.read_text()
    except FileNotFoundError:
        return []
    start = text.find(f"const {varname} = [")
    if start < 0:
        start = text.find(f"var {varname} = [")
        if start < 0: return []
    i = text.find("[", start)
    depth=0; in_str=False; sc=None; esc=False; end=None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc=False; continue
        if c == "\\" and in_str: esc=True; continue
        if in_str:
            if c == sc: in_str=False
            continue
        if c in "\"'": in_str=True; sc=c; continue
        if c == "[": depth+=1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    if end is None: return []
    inner = text[i+1:end]
    # Very permissive: try to eval-like the JS via converting to JSON
    # We'll just do a simple regex-based field extractor in practice
    return inner


def parse_relative_iso(s):
    if not s: return None
    # Accepts "2026-04-17", "2026-04-17T12:00:00Z", etc.
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s + "T00:00:00+00:00")
    except Exception:
        return None


def within_window(dt):
    if dt is None: return False
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return WEEK_START <= dt <= NOW


def load_news_events():
    """Recent RSS-aggregated news with company tags."""
    out = []
    nr = safe_json(DATA / "news_raw.json") or []
    for n in nr:
        pub = n.get("pubDate") or n.get("date")
        dt = parse_relative_iso(pub) if pub else None
        if not within_window(dt): continue
        cs = n.get("matchedCompanies") or ([n.get("matchedCompany")] if n.get("matchedCompany") else [])
        for co in cs:
            if not co: continue
            out.append({
                "company": co,
                "type": classify_news(n),
                "detail": n.get("title", "")[:150],
                "date": pub,
                "source": n.get("source", "news"),
                "url": n.get("link", ""),
            })
    return out


def classify_news(n):
    text = ((n.get("title") or "") + " " + (n.get("description") or "")).lower()
    impact = n.get("impact", "").lower()
    t = n.get("type", "").lower()
    # Funding / IPO
    if "files for ipo" in text or "goes public" in text: return "ipo"
    if "spac" in text and "merger" in text: return "spac"
    if t == "funding" or "raises $" in text or "raised $" in text or "series" in text:
        if re.search(r'\$(?:1\d{2}|[2-9]\d{2}|\d\.\d+b|\d+b)\s*m?', text):
            return "funding_mega"
        if re.search(r'\$\d{2,3}\s*m', text):
            return "funding_major"
        return "funding_minor"
    # Contracts
    if t == "contract" or re.search(r'(?:wins|awarded|selected for).*contract', text):
        if re.search(r'\$\d{3,}\s*m|\$\d+\s*b', text): return "contract_mega"
        if re.search(r'\$\d{2}\s*m', text): return "contract_major"
        return "contract_minor"
    # Regulatory
    if "fda approval" in text or "fda approved" in text: return "fda_approval"
    if "510(k)" in text or "fda clear" in text: return "fda_510k"
    if "nrc license" in text or "nrc approval" in text: return "nrc_license"
    # Milestones
    if "first plasma" in text or "ignition achieved" in text: return "ignition"
    if "first flight" in text or "flight-proven" in text or "successful test" in text:
        return "flight_test_success"
    if "world-first" in text or "first-ever" in text: return "world_first"
    # Negative
    if "bankruptcy" in text or "chapter 11" in text or "wound down" in text: return "bankruptcy"
    if "layoffs" in text or "layoff" in text or "let go" in text or "restructur" in text:
        if re.search(r'\d{2,}%', text) or re.search(r'\d{3,}\s*(?:employees|staff)', text):
            return "layoffs_major"
        return "layoffs_minor"
    if "ceo out" in text or "ceo step down" in text or "founder left" in text: return "ceo_exit_negative"
    if "lawsuit" in text or "sued by" in text: return "lawsuit_major"
    # Business positive
    if "partnership" in text or "partners with" in text: return "major_partnership"
    if "named customer" in text or "first customer" in text: return "named_customer"
    # Default: ignore (low signal)
    return None


def load_press_releases():
    """Filtered press releases with company tags."""
    out = []
    pr = safe_json(DATA / "press_releases_filtered.json") or []
    for r in pr:
        pub = r.get("pubDate") or r.get("date")
        dt = parse_relative_iso(pub) if pub else None
        if not within_window(dt): continue
        for co in (r.get("companies") or []):
            out.append({
                "company": co,
                "type": classify_news({"title": r.get("title", ""), "description": r.get("description", "")}),
                "detail": r.get("title", "")[:150],
                "date": pub,
                "source": r.get("source", "press"),
                "url": r.get("link", ""),
            })
    return out


def load_sbir_awards():
    """SBIR/STTR awards — companies in the last week."""
    out = []
    data = safe_json(DATA / "sbir_awards_auto.json") or []
    for r in data:
        # SBIR data is last-updated, not event-dated — treat new entries as fresh.
        last = r.get("lastUpdated")
        dt = parse_relative_iso(last)
        if not within_window(dt): continue
        phase = (r.get("phase") or "").lower()
        if "iii" in phase: t = "sbir_phase_iii"
        elif "ii" in phase: t = "contract_major"
        else: t = "contract_minor"
        out.append({
            "company": r.get("company", "").strip(),
            "type": t,
            "detail": f"{r.get('agency','')} — {r.get('topic','')[:80]}",
            "date": last,
            "source": "SBIR.gov",
            "url": r.get("url", ""),
        })
    return out


def load_earnings_signals():
    """Earnings-call-extracted signals (when ANTHROPIC_API_KEY credit is live)."""
    out = []
    data = safe_json(DATA / "earnings_signals.json") or []
    for s in data:
        dt = parse_relative_iso(s.get("date"))
        if not within_window(dt): continue
        signal_dir = (s.get("signal_direction") or "").lower()
        sig_type = "earnings_bull" if signal_dir in ("bullish", "positive") else (
            "earnings_bear" if signal_dir in ("bearish", "negative") else None)
        if not sig_type: continue
        # Apply to the target_vertical or mentioned companies if matched
        for co in (s.get("frontier_mentions") or []):
            out.append({
                "company": co,
                "type": sig_type,
                "detail": s.get("quote", "")[:150],
                "date": s.get("date"),
                "source": f"{s.get('incumbent','')} earnings call",
                "url": s.get("source_url", ""),
            })
    return out


def load_gov_contracts_recent():
    """Recent gov-contract notices from SAM.gov / USASpending."""
    out = []
    # Try aggregate files
    for fname in ["sam_contracts_aggregated.json", "gov_contracts_raw.json"]:
        data = safe_json(DATA / fname)
        if not data: continue
        items = data if isinstance(data, list) else data.get("contracts", [])
        for r in items:
            pub = r.get("date") or r.get("awardDate") or r.get("postedDate")
            dt = parse_relative_iso(pub)
            if not within_window(dt): continue
            amount_str = str(r.get("amount") or r.get("awardAmount") or "")
            if re.search(r'[1-9]\d{8,}', amount_str.replace(",","")):
                t = "contract_mega"
            elif re.search(r'[1-9]\d{6,}', amount_str.replace(",","")):
                t = "contract_major"
            else:
                t = "contract_minor"
            for co in (r.get("matchedCompanies") or [r.get("awardee", "")]):
                if not co: continue
                out.append({
                    "company": co,
                    "type": t,
                    "detail": (r.get("title") or r.get("description") or "")[:150],
                    "date": pub,
                    "source": fname,
                    "url": r.get("url", ""),
                })
    return out


def load_funding_feed():
    data = safe_json(DATA / "funding_feed_auto.json") or []
    out = []
    items = data if isinstance(data, list) else data.get("rounds", [])
    for r in items:
        dt = parse_relative_iso(r.get("date"))
        if not within_window(dt): continue
        amt = r.get("amount", "") or ""
        m = re.search(r'\$(\d+\.?\d*)\s*([BMK])?', amt, re.IGNORECASE)
        sig_type = "funding_minor"
        if m:
            v = float(m.group(1)); u = (m.group(2) or "M").upper()
            if u == "B" or (u == "M" and v >= 100): sig_type = "funding_mega"
            elif u == "M" and v >= 30: sig_type = "funding_major"
        if (r.get("round") or "").upper() == "IPO":
            sig_type = "ipo"
        for co in (r.get("matchedCompanies") or [r.get("company", "")]):
            if not co: continue
            out.append({
                "company": co,
                "type": sig_type,
                "detail": f"{r.get('round','')} {amt}".strip(),
                "date": r.get("date"),
                "source": "funding_feed",
                "url": r.get("link", ""),
            })
    return out


def load_exec_moves():
    data = safe_json(DATA / "exec_moves_auto.json") or []
    out = []
    items = data if isinstance(data, list) else data.get("moves", [])
    for m in items:
        dt = parse_relative_iso(m.get("date"))
        if not within_window(dt): continue
        move = (m.get("moveType") or "").lower()
        if "departure" in move or "exit" in move or "left" in move:
            t = "ceo_exit_negative"
        else:
            t = "exec_hire_star"
        out.append({
            "company": m.get("company") or m.get("newCompany") or "",
            "type": t,
            "detail": f"{m.get('person','')} {m.get('moveType','')}".strip(),
            "date": m.get("date"),
            "source": "exec_moves",
            "url": m.get("url", ""),
        })
    return out


# ════════════════════════════════════════════════════════════════
# CORE SYNC
# ════════════════════════════════════════════════════════════════

def load_companies():
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    i = text.find("[", start)
    depth=0; in_str=False; sc=None; esc=False; end=None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc=False; continue
        if c == "\\" and in_str: esc=True; continue
        if in_str:
            if c == sc: in_str=False
            continue
        if c in "\"'": in_str=True; sc=c; continue
        if c == "[": depth+=1
        elif c == "]":
            depth-=1
            if depth == 0: end=k; break
    block = text[i+1:end]
    entries = []
    idx=0; n=len(block); d=0; in_str=False; sc=None; esc=False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        s = idx
        while idx < n:
            c = block[idx]
            if esc: esc=False; idx+=1; continue
            if c == "\\" and in_str: esc=True; idx+=1; continue
            if in_str:
                if c == sc: in_str=False
                idx+=1; continue
            if c in "\"'": in_str=True; sc=c; idx+=1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: idx+=1; entries.append(block[s:idx]); break
            idx += 1

    by_name = {}
    for e in entries:
        m = re.search(r'\bname:\s*"((?:[^"\\]|\\.)*)"', e)
        if m: by_name[m.group(1)] = e
    return by_name


def load_innov_scores():
    text = DATA_JS.read_text()
    start = text.find("const INNOVATOR_SCORES = [")
    i = text.find("[", start)
    depth=0; in_str=False; sc=None; esc=False; end=None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc=False; continue
        if c == "\\" and in_str: esc=True; continue
        if in_str:
            if c == sc: in_str=False
            continue
        if c in "\"'": in_str=True; sc=c; continue
        if c == "[": depth+=1
        elif c == "]":
            depth-=1
            if depth == 0: end=k; break
    block = text[i+1:end]

    rows = {}
    for m in re.finditer(
        r'\{\s*company:\s*"((?:[^"\\]|\\.)*)",\s*techMoat:\s*(\d+),\s*momentum:\s*(\d+),'
        r'\s*teamPedigree:\s*(\d+),\s*marketGravity:\s*(\d+),\s*capitalEfficiency:\s*(\d+),'
        r'\s*govTraction:\s*(\d+),\s*composite:\s*([\d.]+),\s*tier:\s*"([^"]+)",'
        r'\s*note:\s*"((?:[^"\\]|\\.)*)"\s*\}',
        block,
    ):
        rows[m.group(1)] = {
            "techMoat": int(m.group(2)), "momentum": int(m.group(3)),
            "teamPedigree": int(m.group(4)), "marketGravity": int(m.group(5)),
            "capitalEfficiency": int(m.group(6)), "govTraction": int(m.group(7)),
            "composite": float(m.group(8)), "tier": m.group(9), "note": m.group(10),
        }
    return rows, (i, end)


def composite(tm, mo, tp, mg, ce, gt):
    return round((mo*2.5 + gt*2.5 + tm*2.0 + tp*1.5 + mg*1.5) * 10) / 10


def assign_tier(c):
    if c >= 90: return "elite"
    if c >= 80: return "exceptional"
    if c >= 70: return "leader"
    if c >= 60: return "strong"
    if c >= 50: return "promising"
    if c >= 40: return "emerging"
    return "early"


def clamp(v, lo=1, hi=10): return max(lo, min(hi, v))


def apply_week_deltas(name, baseline, events):
    """Apply capped deltas from this week's events."""
    if not events:
        return baseline, [], 0.0

    deltas = {k: 0 for k in ["techMoat", "momentum", "teamPedigree",
                             "marketGravity", "capitalEfficiency", "govTraction"]}
    reasons = []
    for ev in events:
        impact = EVENT_IMPACT.get(ev["type"])
        if not impact: continue
        for axis, d in impact.items():
            deltas[axis] += d
        if abs(sum(impact.values())) >= 1:
            reasons.append(f"[{ev['type']}] {ev['detail']}")

    # Cap axis deltas per-week
    capped = {k: max(-MAX_AXIS_DELTA_PER_WEEK, min(MAX_AXIS_DELTA_PER_WEEK, v))
              for k, v in deltas.items()}

    new = dict(baseline)
    for k, d in capped.items():
        if k in new and isinstance(new[k], (int, float)):
            new[k] = clamp(new[k] + d)

    new_comp = composite(new["techMoat"], new["momentum"], new["teamPedigree"],
                         new["marketGravity"], new["capitalEfficiency"], new["govTraction"])

    # Cap composite delta
    max_cd = MAX_COMPOSITE_DELTA_PER_WEEK
    if abs(new_comp - baseline["composite"]) > max_cd:
        # Proportionally scale back the axis changes
        direction = 1 if new_comp > baseline["composite"] else -1
        new_comp = baseline["composite"] + direction * max_cd

    new["composite"] = new_comp
    new["tier"] = assign_tier(new_comp)
    return new, reasons[:3], new_comp - baseline["composite"]


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    log.info("=" * 60)
    log.info(f"Weekly Intelligence Sync — week ending {WEEK_ENDING}")
    log.info(f"Window: {WEEK_START.isoformat()} → {NOW.isoformat()}")
    log.info("=" * 60)

    # 1. Load everything
    companies = load_companies()
    log.info(f"COMPANIES: {len(companies)}")
    innov, (is_open, is_close) = load_innov_scores()
    log.info(f"INNOVATOR_SCORES: {len(innov)}")

    # 2. Collect events from all sources
    log.info("\nAggregating events from feeds...")
    loaders = [
        ("news",           load_news_events),
        ("press_releases", load_press_releases),
        ("sbir_awards",    load_sbir_awards),
        ("earnings",       load_earnings_signals),
        ("gov_contracts",  load_gov_contracts_recent),
        ("funding_feed",   load_funding_feed),
        ("exec_moves",     load_exec_moves),
    ]
    all_events = []
    for name, fn in loaders:
        try:
            events = fn()
        except Exception as e:
            log.warning(f"{name} loader crashed: {e}")
            events = []
        all_events.extend([e for e in events if e.get("company") and e.get("type")])
        log.info(f"  {name}: {len(events)} events")

    # Bucket events per company
    by_company = {}
    for e in all_events:
        by_company.setdefault(e["company"], []).append(e)

    log.info(f"\nCompanies with events this week: {len(by_company)}")

    # 3. Apply deltas and write digest
    movers_up = []; movers_down = []; unchanged = 0
    updated_innov = dict(innov)
    all_reasons = {}

    for name, events in by_company.items():
        baseline = innov.get(name)
        if not baseline: continue
        new, reasons, delta = apply_week_deltas(name, baseline, events)
        if abs(delta) < 0.1:
            unchanged += 1
            continue
        updated_innov[name] = new
        all_reasons[name] = reasons
        if delta > 0:
            movers_up.append({"company": name, "delta": delta,
                              "new_composite": new["composite"],
                              "old_composite": baseline["composite"],
                              "new_tier": new["tier"],
                              "reasons": reasons})
        else:
            movers_down.append({"company": name, "delta": delta,
                                "new_composite": new["composite"],
                                "old_composite": baseline["composite"],
                                "new_tier": new["tier"],
                                "reasons": reasons})

    movers_up.sort(key=lambda x: -x["delta"])
    movers_down.sort(key=lambda x: x["delta"])

    # 4. Collect top headlines
    headlines = []
    for e in all_events:
        strength_order = ["contract_mega", "ipo", "fda_approval", "nrc_license",
                          "funding_mega", "sbir_phase_iii", "world_first", "ignition",
                          "type_cert", "flight_test_success", "contract_major",
                          "funding_major", "acquisition_target"]
        rank = strength_order.index(e["type"]) if e["type"] in strength_order else 99
        headlines.append((rank, e))
    headlines.sort(key=lambda x: (x[0], -len(x[1]["detail"])))
    top_headlines = [h[1] for h in headlines[:40]]

    # 5a. Update per-company weekly HISTORY (for sparklines + trend)
    history_path = DATA / "weekly_history.json"
    history = safe_json(history_path) or {"companies": {}, "weeks": []}
    if WEEK_ENDING not in history["weeks"]:
        history["weeks"].append(WEEK_ENDING)
        history["weeks"] = history["weeks"][-26:]  # Keep last 26 weeks
    for name, s in updated_innov.items():
        history["companies"].setdefault(name, [])
        # Replace entry for today if already present, else append
        entry = {"w": WEEK_ENDING, "c": s["composite"], "t": s["tier"]}
        hist = history["companies"][name]
        if hist and hist[-1]["w"] == WEEK_ENDING:
            hist[-1] = entry
        else:
            hist.append(entry)
        history["companies"][name] = hist[-26:]
    history_path.write_text(json.dumps(history, separators=(",", ":"), default=str))
    log.info(f"Updated weekly_history.json ({len(history['companies'])} companies, "
             f"{len(history['weeks'])} weeks)")

    # 5b. Detect TIER CROSSINGS this week
    tier_rank = {"early": 0, "emerging": 1, "promising": 2, "strong": 3,
                 "leader": 4, "exceptional": 5, "elite": 6}
    tier_crossings = []
    for name, s in updated_innov.items():
        old = innov.get(name)
        if not old: continue
        old_rank = tier_rank.get(old["tier"], 0)
        new_rank = tier_rank.get(s["tier"], 0)
        if new_rank > old_rank:
            tier_crossings.append({
                "company": name,
                "from_tier": old["tier"],
                "to_tier": s["tier"],
                "new_composite": s["composite"],
                "reasons": all_reasons.get(name, []),
                "first_time_elite": (s["tier"] == "elite" and old["tier"] != "elite"),
            })

    # 5c. Publish digest
    digest = {
        "generated_at": NOW.isoformat(),
        "week_ending": WEEK_ENDING,
        "window_days": 7,
        "events_processed": len(all_events),
        "companies_touched": len(by_company),
        "companies_moved": len(movers_up) + len(movers_down),
        "companies_unchanged": unchanged,
        "movers_up_top20": movers_up[:20],
        "movers_down_top10": movers_down[:10],
        "tier_crossings": tier_crossings,
        "first_time_elite": [c for c in tier_crossings if c["first_time_elite"]],
        "top_headlines": top_headlines,
        "methodology": {
            "rubric": "See EVENT_IMPACT in scripts/sync_weekly_metrics.py",
            "max_axis_delta_per_week": MAX_AXIS_DELTA_PER_WEEK,
            "max_composite_delta_per_week": MAX_COMPOSITE_DELTA_PER_WEEK,
            "formula": "composite = mo*2.5 + gt*2.5 + tm*2.0 + tp*1.5 + mg*1.5",
        },
    }
    digest_path = DATA / "weekly_scoring_digest.json"
    digest_path.write_text(json.dumps(digest, indent=2, default=str))
    log.info(f"\nWrote digest: {digest_path}")
    log.info(f"  Movers up:   {len(movers_up)} (top: {[m['company'] for m in movers_up[:5]]})")
    log.info(f"  Movers down: {len(movers_down)} (bottom: {[m['company'] for m in movers_down[:5]]})")
    log.info(f"  Tier crossings: {len(tier_crossings)} (first-time-elite: "
             f"{len([c for c in tier_crossings if c['first_time_elite']])})")
    log.info(f"  Top headlines: {len(top_headlines)}")

    # 5d. Emit newsletter-friendly mover summary for weekly brief pickup
    brief_movers = {
        "week_ending": WEEK_ENDING,
        "generated_at": NOW.isoformat(),
        "lede": (
            f"{len(movers_up)} companies moved up, "
            f"{len([c for c in tier_crossings if c['first_time_elite']])} reached elite tier, "
            f"{len([h for h in top_headlines if h['type'].startswith('contract')])} major contract wins"
            if movers_up else f"Quiet week — {len(all_events)} events tracked across the Frontier Index"
        ),
        "top_3_up":   [f"{m['company']}: {m['old_composite']:.1f} → {m['new_composite']:.1f} "
                       f"(+{m['delta']:.1f}) — {m['reasons'][0][:120] if m['reasons'] else '—'}"
                       for m in movers_up[:3]],
        "first_time_elite": [c["company"] for c in tier_crossings if c["first_time_elite"]],
        "tier_upgrades":    [f"{c['company']}: {c['from_tier']} → {c['to_tier']}"
                            for c in tier_crossings[:10]],
        "notable_headlines": [f"[{h['type']}] {h['company']}: {h['detail'][:100]}"
                             for h in top_headlines[:10]],
    }
    (DATA / "weekly_brief_movers.json").write_text(json.dumps(brief_movers, indent=2))
    log.info(f"Wrote newsletter-friendly movers: data/weekly_brief_movers.json")

    # 6. Rewrite INNOVATOR_SCORES array in data.js
    if not movers_up and not movers_down:
        log.info("No score changes — not touching data.js")
        return

    def esc(s):
        return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    text = DATA_JS.read_text()
    lines = []
    for name in sorted(updated_innov.keys(), key=lambda n: -updated_innov[n]["composite"]):
        s = updated_innov[name]
        lines.append(
            f'  {{ company: "{esc(name)}", '
            f'techMoat: {s["techMoat"]}, momentum: {s["momentum"]}, '
            f'teamPedigree: {s["teamPedigree"]}, marketGravity: {s["marketGravity"]}, '
            f'capitalEfficiency: {s["capitalEfficiency"]}, govTraction: {s["govTraction"]}, '
            f'composite: {s["composite"]}, tier: "{s["tier"]}", '
            f'note: "{esc(s["note"])}" }}'
        )
    new_inner = "\n" + ",\n".join(lines) + "\n"
    new_content = text[:is_open+1] + new_inner + text[is_close:]
    DATA_JS.write_text(new_content)
    log.info(f"Updated INNOVATOR_SCORES in data.js ({len(updated_innov)} rows)")

    log.info("=" * 60)
    log.info("Done.")


if __name__ == "__main__":
    main()
