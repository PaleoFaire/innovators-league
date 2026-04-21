#!/usr/bin/env python3
"""
Calculate FUND_INTELLIGENCE — platform-scale intelligence metrics plus
per-VC-firm aggregations derived from existing VC portfolio data and
the main COMPANIES array.

Output: data/fund_intelligence_auto.json
Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_JS = Path(__file__).resolve().parent.parent / "data.js"
OUT_PATH = DATA_DIR / "fund_intelligence_auto.json"


def load_json_file(name):
    p = DATA_DIR / name
    if p.exists():
        try:
            return json.load(open(p))
        except Exception:
            return []
    return []


def parse_companies_from_data_js():
    """Extract COMPANIES array from data.js."""
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    if start < 0: return []
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
    return entries


def parse_dollar_m(s):
    if not s: return 0.0
    t = re.sub(r"[~≈≥+]", "", s.strip())
    t = t.replace("£", "$").replace("€", "$").replace("₹", "$")
    m = re.search(r"\$?([\d,.]+)\s*([BMK]?)", t, re.IGNORECASE)
    if not m: return 0.0
    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return 0.0
    u = (m.group(2) or "").upper()
    if u == "B": return num * 1000
    if u == "K": return num / 1000
    if u == "M": return num
    return num / 1_000_000 if num > 100_000 else num


def main():
    entries = parse_companies_from_data_js()
    print(f"  Parsed {len(entries)} companies from data.js")

    companies = []
    for e in entries:
        def gs(f):
            m = re.search(rf"\b{f}:\s*\"((?:[^\"\\]|\\.)*)\"", e)
            return m.group(1) if m else ""
        companies.append({
            "name": gs("name"),
            "sector": gs("sector"),
            "fundingStage": gs("fundingStage"),
            "totalRaised": gs("totalRaised"),
            "valuation": gs("valuation"),
            "description": gs("description"),
            "insight": gs("insight"),
        })

    # Platform-scale metrics
    total_raised_sum = sum(parse_dollar_m(c["totalRaised"]) for c in companies)
    total_valuation_sum = sum(parse_dollar_m(c["valuation"]) for c in companies)
    with_valuation = sum(1 for c in companies if parse_dollar_m(c["valuation"]) > 0)
    by_sector = defaultdict(int)
    for c in companies:
        by_sector[c["sector"]] += 1

    # Gov contracts from fetched data (if available)
    gc = load_json_file("gov_contracts_aggregated.json") or load_json_file("sam_contracts_aggregated.json") or []
    sbir = load_json_file("sbir_awards_auto.json") or []
    deals = load_json_file("deals_auto.json") or []
    news = load_json_file("news_raw.json") or []

    # Investor → portfolio count (mine from descriptions, insights, VC_FIRMS if present)
    investor_mentions = defaultdict(set)
    top_investors = [
        "Founders Fund", "Sequoia Capital", "Andreessen Horowitz", "a16z",
        "Peter Thiel", "Thrive Capital", "General Catalyst",
        "Kleiner Perkins", "Khosla Ventures", "Lightspeed", "Accel",
        "Benchmark", "Greylock", "Tiger Global", "Coatue",
        "SoftBank", "BlackRock", "Fidelity", "T. Rowe Price",
        "Wellington Management", "Bezos Expeditions", "Breakthrough Energy",
        "NEA", "Lux Capital", "8VC", "Index Ventures", "Valor Equity",
        "NVIDIA", "In-Q-Tel", "NATO Innovation Fund", "Craft Ventures",
    ]
    for c in companies:
        text = c["description"] + " " + c["insight"]
        for inv in top_investors:
            if inv in text:
                investor_mentions[inv].add(c["name"])

    top_funds = sorted(
        [{"fund": inv, "portfolio_count": len(names), "companies": sorted(names)[:10]}
         for inv, names in investor_mentions.items()],
        key=lambda x: -x["portfolio_count"]
    )[:20]

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "platform": {
            "companiesTracked": len(companies),
            "sectorsMonitored": len(by_sector),
            "totalCapitalRaisedTracked": f"${total_raised_sum/1000:.1f}B",
            "totalValuationTracked": f"${total_valuation_sum/1000:.1f}B",
            "companiesWithValuation": with_valuation,
            "govContractsTracked": len(gc),
            "sbirAwardsTracked": len(sbir),
            "dealsTracked": len(deals),
            "newsItemsTracked": len(news),
            "dataPointsUpdated": f"{len(companies) * 40:,}+",
        },
        "topFunds": top_funds,
        "sectorConcentration": dict(
            sorted([(s, n) for s, n in by_sector.items()], key=lambda x: -x[1])[:15]
        ),
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote fund intelligence: {OUT_PATH}")
    print(f"    {payload['platform']['companiesTracked']} companies tracked")
    print(f"    {len(top_funds)} top funds ranked by portfolio mentions")


if __name__ == "__main__":
    main()
