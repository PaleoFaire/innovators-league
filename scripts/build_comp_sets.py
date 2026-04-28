#!/usr/bin/env python3
"""
Comp-Set Builder + Valuation Triangulation Engine.

For every company in COMPANIES, builds a custom comparable set and
triangulates a fair valuation range using ONLY data we actually have.

ACCURACY CONTRACT (Stephen's hard requirement):
  - Every number traced to a source field in our data
  - All math is deterministic — Python, not LLM
  - LLM ONLY writes the narrative paragraph; never produces numbers
  - "Data unavailable" is shown explicitly when we don't have something
  - Each comp links back to its source row in our DB

THREE TRIANGULATION METHODS (any subset applicable):

  A. Stage-Progression Method
     If target has last-round post-money + stage:
       implied = last_post × stage_step_up
     stage_step_up is a curated industry-typical multiplier per stage.

  B. Peer-Median Method
     Median valuation of same-sector + same-stage peers. Robust when we
     have ≥3 peer datapoints. Falls back to wider sector if needed.

  C. Public-Comp Anchoring Method
     For sectors with public-co coverage (e.g. AI, semis, space):
     sector_median_P/S × estimated_target_revenue → implied EV.
     Only applied when target has known revenue (rare for private cos).

Triangulated range:
  low    = min(applicable_methods) × 0.85
  median = median of applicable methods
  high   = max(applicable_methods) × 1.15

Output:
  data/comp_sets_auto.json — keyed by company name
  data/comp_sets_auto.js   — script-tag loadable
"""

import json
import os
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
OUT_PATH = DATA / "comp_sets_auto.json"
OUT_JS = DATA / "comp_sets_auto.js"

# ─── Stage-progression typical multipliers (industry heuristic) ───
# Source: aggregated from Crunchbase, Pitchbook, AngelList, ROS curated
# data on frontier-tech step-up multiples by stage transition.
STAGE_ORDER = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C",
               "Series D", "Series E", "Series F", "Series G", "Late Stage",
               "Growth", "Pre-IPO"]
STAGE_STEP_UP = {
    "Pre-Seed": 2.5,    # → Seed
    "Seed": 2.5,        # → Series A
    "Series A": 2.0,    # → Series B
    "Series B": 1.9,    # → Series C
    "Series C": 1.7,    # → Series D
    "Series D": 1.5,    # → Series E
    "Series E": 1.4,    # → Series F
    "Series F": 1.3,    # → Series G
    "Series G": 1.25,   # → Late Stage / Growth
    "Late Stage": 1.2,  # → Pre-IPO
    "Growth": 1.2,      # → Pre-IPO
}

# Hard sanity bounds — flag absurd P/S sectors (single-ticker noise)
MAX_REASONABLE_PS = 100  # Anything above is single-ticker pre-revenue noise


# ────────────────────────────────────────────────────────────
# Number parsing


def parse_dollar(s):
    """Parse '$2.5B', '$500M', '500000', '$1.35B' → USD float. Returns 0
    if unparseable. Strips '+' suffixes."""
    if not s: return 0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "").replace("+", "")
    m = re.match(r"\$?\s*([\d.]+)\s*([KMBT])?", s)
    if not m: return 0
    try:
        n = float(m.group(1))
    except ValueError:
        return 0
    u = (m.group(2) or "").upper()
    return n * {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(u, 1)


def fmt_dollar(n):
    if not n: return None
    if n >= 1e12: return f"${n/1e12:.1f}T"
    if n >= 1e9: return f"${n/1e9:.1f}B"
    if n >= 1e6: return f"${n/1e6:.0f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"


# ────────────────────────────────────────────────────────────
# Data loaders


def parse_companies():
    """Extract all relevant fields from COMPANIES array in data.js."""
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'const COMPANIES\s*=\s*\[', src)
    if not m: return []
    start = m.end() - 1
    depth = 0
    in_str = False
    str_q = None
    i = start
    while i < len(src):
        ch = src[i]
        if in_str:
            if ch == '\\': i += 2; continue
            if ch == str_q: in_str = False
        else:
            if ch in ('"', "'", '`'): in_str = True; str_q = ch
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = src[start:i+1]
                    break
        i += 1
    else:
        return []

    companies = []
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
                    obj = block[obj_start:i+1]
                    def grab(field):
                        m = re.search(rf'{field}:\s*"([^"]*)"', obj)
                        return m.group(1) if m else None
                    name = grab("name")
                    if not name: continue
                    companies.append({
                        "name": name,
                        "sector": grab("sector"),
                        "fundingStage": grab("fundingStage"),
                        "totalRaised": grab("totalRaised"),
                        "valuation": grab("valuation"),
                        "founder": grab("founder"),
                        "ticker": grab("ticker"),
                        "rosLink": grab("rosLink"),
                        "founded": (re.search(r'founded:\s*(\d+)', obj) or [None,None])[1],
                    })
                    obj_start = None
    return companies


def parse_funding_tracker():
    """Get latest-round-per-company from FUNDING_TRACKER."""
    src = DATA_JS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'const FUNDING_TRACKER\s*=\s*\[(.*?)\n\];', src, re.DOTALL)
    if not m: return {}
    block = m.group(1)
    by_co = {}
    for entry in re.finditer(r'\{[^}]*\}', block):
        e = entry.group(0)
        def g(f):
            m2 = re.search(rf'{f}:\s*"([^"]*)"', e)
            return m2.group(1) if m2 else None
        name = g("company")
        if not name: continue
        by_co[name] = {
            "totalRaised": g("totalRaised"),
            "lastRound": g("lastRound"),
            "lastRoundAmount": g("lastRoundAmount"),
            "lastRoundDate": g("lastRoundDate"),
            "valuation": g("valuation"),
        }
    return by_co


def load_public_multiples():
    fp = DATA / "public_multiples_auto.json"
    if not fp.exists(): return {}
    return json.load(open(fp))


# ────────────────────────────────────────────────────────────
# Sector mapping (data.js sector names → public_multiples sector keys)

SECTOR_TO_PUBLIC_KEY = {
    "AI": "ai", "AI Software": "ai", "AI & Software": "ai", "AI & Compute": "ai",
    "Defense": "defense", "Defense & Security": "defense",
    "Defense & Dual-use": "defense",
    "Space": "space", "Space & Aerospace": "space",
    "Nuclear": "nuclear", "Nuclear Energy": "nuclear",
    "Fusion": "fusion", "Fusion Energy": "fusion",
    "Quantum": "quantum", "Quantum Computing": "quantum",
    "Robotics": "robotics", "Robotics & Manufacturing": "robotics",
    "Biotech": "biotech", "Biotech & Health": "biotech",
    "Autonomy": "autonomy", "Autonomous Driving": "autonomy",
    "Climate": "climate", "Climate & Energy": "climate",
    "Energy Storage": "battery",
    "EV": "ev", "Electric Vehicles": "ev", "EVs": "ev",
    "evtol": "evtol", "EVTOL": "evtol", "Advanced Air Mobility": "evtol",
    "Chips": "chips", "Chips & Semiconductors": "chips",
    "Semiconductors": "chips",
    "Supersonic & Hypersonic": "defense",
}


def public_key_for_sector(sector):
    if not sector: return None
    return SECTOR_TO_PUBLIC_KEY.get(sector)


# ────────────────────────────────────────────────────────────
# Valuation triangulation methods


def method_stage_progression(target, funding):
    """Method A: last-round post-money × typical stage step-up.
    Returns dict with result + inputs, or None if not applicable."""
    last_amt_str = (funding or {}).get("lastRoundAmount") or target.get("totalRaised")
    last_post_str = (funding or {}).get("valuation") or target.get("valuation")
    stage = target.get("fundingStage")

    if not stage or stage not in STAGE_STEP_UP:
        return None

    # Prefer post-money valuation if known; fall back to total raised
    base_val = parse_dollar(last_post_str)
    base_label = "last_post_money"
    if base_val == 0:
        base_val = parse_dollar(last_amt_str)
        base_label = "total_raised_proxy"
    if base_val == 0:
        return None

    step_up = STAGE_STEP_UP[stage]
    implied = base_val * step_up
    return {
        "name": "Stage-Progression",
        "applicable": True,
        "inputs": {
            "base_value": base_val,
            "base_value_fmt": fmt_dollar(base_val),
            "base_source": base_label,
            "current_stage": stage,
            "step_up_multiplier": step_up,
        },
        "implied": implied,
        "implied_fmt": fmt_dollar(implied),
        "rationale": (
            f"Applies typical {stage} → next-stage step-up multiplier "
            f"({step_up}x) to {fmt_dollar(base_val)} {base_label.replace('_', ' ')}."
        ),
    }


def method_peer_median(target, all_companies):
    """Method B: median valuation of same-sector peers, filtered to a
    NARROW peer set so the median is meaningful. We try filters in order
    of preference + only return an applicable result if ≥3 peers match.

    Filters tried (in order):
      1. Same sector + same stage (e.g., Series G + Defense)
      2. Same sector + adjacent stage (target stage ±1)
      3. Same sector + same valuation tier (within 5x of target's known val)
      4. None apply → skip (return non-applicable, don't pollute with noise)
    """
    sector = target.get("sector")
    stage = target.get("fundingStage")
    target_name = target.get("name")
    if not sector: return None

    # Peers: same sector, NOT the target, with known valuation
    peers = []
    for c in all_companies:
        if c["name"] == target_name: continue
        if c.get("sector") != sector: continue
        v = parse_dollar(c.get("valuation"))
        if v <= 0: continue
        peers.append({
            "name": c["name"],
            "stage": c.get("fundingStage"),
            "valuation": v,
        })

    if len(peers) < 1: return None

    # Filter 1: same stage
    same_stage = [p for p in peers if p["stage"] == stage]

    # Filter 2: adjacent stage (target ± 1 in STAGE_ORDER)
    adjacent = []
    if stage in STAGE_ORDER:
        idx = STAGE_ORDER.index(stage)
        adjacent_stages = set()
        if idx > 0: adjacent_stages.add(STAGE_ORDER[idx - 1])
        if idx < len(STAGE_ORDER) - 1: adjacent_stages.add(STAGE_ORDER[idx + 1])
        adjacent = [p for p in peers if p["stage"] in adjacent_stages and p["stage"] != stage]

    # Filter 3: same valuation tier (within 5x of target's known val)
    target_val = parse_dollar(target.get("valuation"))
    tier_match = []
    if target_val > 0:
        lo, hi = target_val / 5.0, target_val * 5.0
        tier_match = [p for p in peers if lo <= p["valuation"] <= hi]

    # Pick the most-relevant peer set with ≥3 entries
    use = None
    label = None
    if len(same_stage) >= 3:
        use, label = same_stage, "same-sector + same-stage"
    elif len(same_stage) + len(adjacent) >= 3:
        use, label = same_stage + adjacent, "same-sector + same/adjacent-stage"
    elif len(tier_match) >= 3:
        use, label = tier_match, "same-sector + similar-valuation-tier"

    if not use:
        return {
            "name": "Peer-Median",
            "applicable": False,
            "skip_reason": (
                f"insufficient narrow peer set in {sector} "
                f"(found {len(same_stage)} same-stage, {len(adjacent)} adjacent-stage, "
                f"{len(tier_match)} similar-tier; need ≥3)"
            ),
            "rationale": (
                f"{len(peers)} same-sector peers exist in {sector}, but none of "
                f"the narrow filters (same-stage / adjacent-stage / similar-valuation-tier) "
                f"yielded ≥3 datapoints. Falling back to all-sector median would "
                f"be misleading."
            ),
        }

    vals = [p["valuation"] for p in use]
    median_val = statistics.median(vals)
    return {
        "name": "Peer-Median",
        "applicable": True,
        "inputs": {
            "peer_count": len(use),
            "peer_filter": label,
            "peer_median": median_val,
            "peer_median_fmt": fmt_dollar(median_val),
            "peer_min": min(vals),
            "peer_max": max(vals),
            "sample_peers": [
                {"name": p["name"], "stage": p["stage"], "valuation": fmt_dollar(p["valuation"])}
                for p in sorted(use, key=lambda x: -x["valuation"])[:5]
            ],
        },
        "implied": median_val,
        "implied_fmt": fmt_dollar(median_val),
        "rationale": (
            f"Median across {len(use)} {label} peers in {sector}. "
            f"Range: {fmt_dollar(min(vals))} - {fmt_dollar(max(vals))}."
        ),
    }


def method_public_comp(target, public_multiples):
    """Method C: sector public-co P/S × target revenue. Only applicable
    if (a) target has known revenue + (b) sector has reliable P/S median
    (n≥3 tickers, P/S < 100x = not single-ticker pre-rev noise)."""
    pub_key = public_key_for_sector(target.get("sector"))
    if not pub_key or not public_multiples.get("sectors"):
        return None

    sector_data = next(
        (s for s in public_multiples["sectors"] if s["sector"] == pub_key),
        None
    )
    if not sector_data: return None

    ps = sector_data.get("priceToSales", {})
    if ps.get("n", 0) < 3: return None
    if ps.get("median") is None: return None
    if ps["median"] > MAX_REASONABLE_PS: return None

    # Need target revenue to apply multiple. We don't reliably have this
    # for private cos — so this method is usually skipped.
    target_rev = parse_dollar(target.get("revenue") or target.get("arr"))
    if target_rev <= 0:
        return {
            "name": "Public-Comp Anchoring",
            "applicable": False,
            "inputs": {
                "sector_label": sector_data["sectorLabel"],
                "ticker_count": ps["n"],
                "sector_ps_median": ps["median"],
                "comp_tickers": sector_data.get("tickers", [])[:5],
            },
            "skip_reason": "target revenue not on file (private companies rarely disclose)",
            "rationale": (
                f"Public {sector_data['sectorLabel']} P/S median is "
                f"{ps['median']:.1f}x across {ps['n']} tickers. Cannot apply "
                f"without target's revenue."
            ),
        }

    implied = target_rev * ps["median"]
    return {
        "name": "Public-Comp Anchoring",
        "applicable": True,
        "inputs": {
            "sector_label": sector_data["sectorLabel"],
            "target_revenue": target_rev,
            "target_revenue_fmt": fmt_dollar(target_rev),
            "sector_ps_median": ps["median"],
            "ticker_count": ps["n"],
            "comp_tickers": sector_data.get("tickers", [])[:5],
        },
        "implied": implied,
        "implied_fmt": fmt_dollar(implied),
        "rationale": (
            f"Target revenue {fmt_dollar(target_rev)} × {sector_data['sectorLabel']} "
            f"sector median P/S {ps['median']:.1f}x (across {ps['n']} public tickers)."
        ),
    }


def triangulate(methods):
    """Combine applicable methods into a low / median / high range."""
    applicable = [m for m in methods if m and m.get("applicable")]
    if not applicable: return None

    values = [m["implied"] for m in applicable]
    med = statistics.median(values)
    lo = min(values) * 0.85
    hi = max(values) * 1.15

    return {
        "low": lo,
        "low_fmt": fmt_dollar(lo),
        "median": med,
        "median_fmt": fmt_dollar(med),
        "high": hi,
        "high_fmt": fmt_dollar(hi),
        "method_count": len(applicable),
    }


# ────────────────────────────────────────────────────────────
# Comp set builder


def build_comp_set(target, all_companies, public_multiples, n=8):
    """Pick top N comparable companies — both public + private — with
    reasoning for each pick."""
    sector = target.get("sector")
    stage = target.get("fundingStage")
    target_name = target.get("name")

    if not sector: return {"public": [], "private": []}

    # Private comps: same sector, prefer same stage, with valuation if possible
    private_candidates = []
    for c in all_companies:
        if c["name"] == target_name: continue
        if c.get("sector") != sector: continue
        same_stage = c.get("fundingStage") == stage
        has_val = parse_dollar(c.get("valuation")) > 0
        score = (2 if same_stage else 0) + (3 if has_val else 0)
        if score == 0: continue
        private_candidates.append({
            "name": c["name"],
            "sector": c.get("sector"),
            "stage": c.get("fundingStage"),
            "valuation": c.get("valuation"),
            "valuationRaw": parse_dollar(c.get("valuation")),
            "totalRaised": c.get("totalRaised"),
            "rosLink": c.get("rosLink"),
            "score": score,
            "rationale": (
                f"Same sector ({c.get('sector')})"
                + (f", same stage ({c.get('fundingStage')})" if same_stage else "")
                + (f", post-money {c.get('valuation')}" if has_val else "")
            ),
        })
    private_candidates.sort(key=lambda x: (-x["score"], -x["valuationRaw"]))
    private_picks = private_candidates[:n]

    # Public comps: same sector if covered by public multiples
    public_picks = []
    pub_key = public_key_for_sector(sector)
    if pub_key and public_multiples.get("sectors"):
        sector_data = next(
            (s for s in public_multiples["sectors"] if s["sector"] == pub_key),
            None
        )
        if sector_data:
            for ticker in sector_data.get("tickers", [])[:5]:
                ticker_data = next(
                    (t for t in public_multiples.get("tickers", []) if t["ticker"] == ticker),
                    None
                )
                if not ticker_data: continue
                public_picks.append({
                    "ticker": ticker_data["ticker"],
                    "company": ticker_data.get("company"),
                    "marketCap": ticker_data.get("marketCap"),
                    "priceToSales": ticker_data.get("priceToSalesTTM"),
                    "evRevenue": ticker_data.get("enterpriseToRevenue"),
                    "revenueGrowth": ticker_data.get("revenueGrowthYoY"),
                    "yahooUrl": ticker_data.get("yahooUrl"),
                    "rationale": f"Public-co frontier-tech comp in {sector_data['sectorLabel']}",
                })

    return {
        "public": public_picks,
        "private": private_picks,
    }


# ────────────────────────────────────────────────────────────
# LLM narrative (optional)


NARRATIVE_PROMPT = """You are writing a 2-3 paragraph valuation narrative for a private frontier-tech company. Use ONLY the data provided below — never invent numbers. Be specific, quantitative, and write in the voice of a sober VC analyst.

Structure:
1. Opening: who's the target, what stage, what's the comp universe (sector + count of public/private comps)
2. Methods applied: walk through which triangulation methods are applicable + their results, citing specific numbers
3. Synthesis: what range does the analysis support, what are the key uncertainties

DO NOT:
- Invent numbers not in the data
- Editorialize beyond what the data supports
- Use marketing language ("revolutionary", "best in class")

Output: plain text (no JSON, no markdown headings). Maximum 220 words.

DATA:
{payload}
"""


def call_claude(client, prompt, model="claude-haiku-4-5", max_retries=2):
    last_err = None
    for attempt in range(max_retries):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1: time.sleep(2 ** attempt)
    print(f"    ⚠ Claude error: {last_err}")
    return ""


# ────────────────────────────────────────────────────────────
# Main


def main():
    print("=" * 64)
    print("Comp-Set + Valuation Triangulation Engine")
    print("=" * 64)

    companies = parse_companies()
    funding = parse_funding_tracker()
    public_multiples = load_public_multiples()
    print(f"  Companies: {len(companies)}")
    print(f"  Funding tracker: {len(funding)}")
    print(f"  Public multiples sectors: {len(public_multiples.get('sectors',[]))}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_llm = bool(api_key)
    client = None
    if use_llm:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print(f"  LLM narrative: ENABLED (Claude Haiku)")
        except ImportError:
            use_llm = False
    if not use_llm:
        print(f"  LLM narrative: SKIPPED (no API key or SDK)")

    by_company = {}
    processed = 0
    with_data = 0
    narratives_generated = 0

    # We only build comp sets for companies that have at least one of:
    # sector + stage, OR a valuation, OR a totalRaised. Skip empty entries.
    targets = [
        c for c in companies
        if c.get("sector") and (c.get("fundingStage") or c.get("valuation") or c.get("totalRaised"))
    ]
    print(f"  Eligible targets: {len(targets)}")

    for t in targets:
        f = funding.get(t["name"])

        method_a = method_stage_progression(t, f)
        method_b = method_peer_median(t, companies)
        method_c = method_public_comp(t, public_multiples)
        methods = [m for m in [method_a, method_b, method_c] if m is not None]
        applicable_methods = [m for m in methods if m.get("applicable")]

        triangulated = triangulate(methods) if applicable_methods else None
        comps = build_comp_set(t, companies, public_multiples, n=8)

        # Skip companies with no useful output (no methods applicable AND no comps)
        if not applicable_methods and not comps["public"] and not comps["private"]:
            continue

        with_data += 1

        # Generate narrative for cos with at least 1 method or 5 comps (worth it)
        narrative = None
        if use_llm and (applicable_methods or len(comps["private"]) >= 5):
            payload = {
                "target": {
                    "name": t["name"], "sector": t.get("sector"),
                    "stage": t.get("fundingStage"),
                    "current_valuation": t.get("valuation"),
                    "total_raised": t.get("totalRaised"),
                    "founder": t.get("founder"),
                },
                "methods": methods,
                "triangulated": triangulated,
                "comp_set_summary": {
                    "public_count": len(comps["public"]),
                    "private_count": len(comps["private"]),
                    "top_private_peers": [p["name"] for p in comps["private"][:5]],
                    "public_tickers": [p["ticker"] for p in comps["public"][:5]],
                },
            }
            prompt = NARRATIVE_PROMPT.format(payload=json.dumps(payload, indent=2, default=str))
            narrative = call_claude(client, prompt)
            if narrative: narratives_generated += 1
            time.sleep(0.2)

        by_company[t["name"]] = {
            "target": {
                "name": t["name"],
                "sector": t.get("sector"),
                "stage": t.get("fundingStage"),
                "currentValuation": t.get("valuation"),
                "totalRaised": t.get("totalRaised"),
                "founder": t.get("founder"),
                "rosLink": t.get("rosLink"),
            },
            "methods": methods,
            "triangulated": triangulated,
            "compSet": comps,
            "narrative": narrative,
            "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

        processed += 1
        if processed % 50 == 0:
            print(f"  ... {processed} processed, {with_data} with data, {narratives_generated} narratives")

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5") if use_llm else None,
        "totalCompanies": len(companies),
        "eligibleTargets": len(targets),
        "withData": with_data,
        "narrativesGenerated": narratives_generated,
        "byCompany": by_company,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))

    js_payload = (
        f"// Auto-generated from {OUT_PATH.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const COMP_SETS_AUTO = {json.dumps(out, indent=2, default=str)};\n"
        f"if (typeof window !== 'undefined') window.COMP_SETS_AUTO = COMP_SETS_AUTO;\n"
    )
    OUT_JS.write_text(js_payload)

    print()
    print(f"✅ Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"   Companies with comp data: {with_data}")
    print(f"   Narratives generated: {narratives_generated}")
    print(f"   File size: {OUT_PATH.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
