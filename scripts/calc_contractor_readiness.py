#!/usr/bin/env python3
"""
Derive CONTRACTOR_READINESS scores for each company in COMPANIES based on:
  * gov contracts tracked (SAM / SBIR / NASA / DOE)
  * estimated headcount (from headcount_estimates_auto.json)
  * description keywords (clearance, ITAR, production heritage)
  * Frontier Index govTraction axis

Output: data/contractor_readiness_auto.json
Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_JS = Path(__file__).resolve().parent.parent / "data.js"
OUT_PATH = DATA_DIR / "contractor_readiness_auto.json"


def safe_json(name):
    p = DATA_DIR / name
    if not p.exists(): return []
    try: return json.load(open(p))
    except Exception: return []


def parse_companies_and_scores():
    text = DATA_JS.read_text()

    def extract(label):
        start = text.find(f"const {label} = [")
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
        return text[i+1:end]

    comp_block = extract("COMPANIES")
    innov_block = extract("INNOVATOR_SCORES")

    # Parse companies
    entries = []
    idx = 0; n = len(comp_block); d = 0; in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and comp_block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if comp_block[idx] != "{": idx += 1; continue
        s = idx
        while idx < n:
            c = comp_block[idx]
            if esc: esc = False; idx += 1; continue
            if c == "\\" and in_str: esc = True; idx += 1; continue
            if in_str:
                if c == sc: in_str = False
                idx += 1; continue
            if c in "\"'": in_str = True; sc = c; idx += 1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: idx += 1; entries.append(comp_block[s:idx]); break
            idx += 1
    companies = []
    for e in entries:
        def gs(f):
            m = re.search(rf"\b{f}:\s*\"((?:[^\"\\]|\\.)*)\"", e)
            return m.group(1) if m else ""
        companies.append({
            "name": gs("name"), "sector": gs("sector"),
            "description": gs("description"), "insight": gs("insight"),
            "fundingStage": gs("fundingStage"), "totalRaised": gs("totalRaised"),
        })

    # Parse INNOVATOR_SCORES for govTraction
    innov_rows = re.findall(
        r'company:\s*"((?:[^"\\]|\\.)*)",[^}]*govTraction:\s*(\d+),\s*composite:\s*([\d.]+)',
        innov_block
    )
    gov_by = {r[0]: (int(r[1]), float(r[2])) for r in innov_rows}

    return companies, gov_by


def main():
    companies, gov_by = parse_companies_and_scores()
    print(f"  Scoring contractor readiness for {len(companies)} companies")

    gc = safe_json("sam_contracts_aggregated.json") or safe_json("gov_contracts_aggregated.json") or []
    sbir = safe_json("sbir_awards_auto.json") or []
    hc = safe_json("headcount_estimates_auto.json") or []
    hc_by = {h.get("company"): h for h in hc}

    # Count contracts per company
    contract_counts = defaultdict(int)
    contract_agencies = defaultdict(set)
    for item in gc:
        companies_tagged = item.get("matchedCompanies") or [item.get("awardee", "")]
        for co in companies_tagged:
            if co:
                contract_counts[co] += 1
                if item.get("agency"):
                    contract_agencies[co].add(item["agency"])
    for r in sbir:
        co = r.get("company", "")
        if co:
            contract_counts[co] += 1
            if r.get("agency"):
                contract_agencies[co].add(r["agency"])

    # Score each company
    rows = []
    for c in companies:
        name = c["name"]
        gov_score, composite = gov_by.get(name, (0, 0.0))

        # Start with govTraction × 10 as base readiness (0-100)
        readiness = gov_score * 10

        # Boost for number of tracked contracts
        cn = contract_counts.get(name, 0)
        if cn >= 10: readiness = min(100, readiness + 15)
        elif cn >= 5: readiness = min(100, readiness + 10)
        elif cn >= 1: readiness = min(100, readiness + 5)

        # Description keywords
        text = (c["description"] + " " + c["insight"]).lower()
        itar = any(k in text for k in ["itar", "export control"])
        clearance = any(k in text for k in ["clearance", "classified", "ts/sci", "sbi"])
        cmmc = any(k in text for k in ["cmmc", "nist 800", "fedramp"])

        if clearance: readiness = min(100, readiness + 5)
        if itar: readiness = min(100, readiness + 3)

        # Skip very-low-readiness companies (not contractor-relevant)
        if readiness < 20:
            continue

        # Get headcount
        headcount = hc_by.get(name, {}).get("estimatedHeadcount", 0)
        headcount_formatted = hc_by.get(name, {}).get("headcountFormatted", "")

        rows.append({
            "company": name,
            "sector": c["sector"],
            "readinessScore": readiness,
            "govTractionScore": gov_score,
            "compositeScore": composite,
            "contractsTracked": cn,
            "agencies": sorted(contract_agencies.get(name, []))[:8],
            "keyIndicators": {
                "clearance": clearance,
                "itar_compliant": itar,
                "cmmc_level_3": cmmc,
            },
            "estimatedHeadcount": headcount,
            "headcountFormatted": headcount_formatted,
        })

    rows.sort(key=lambda x: -x["readinessScore"])
    OUT_PATH.write_text(json.dumps(rows[:200], indent=2))  # top 200
    print(f"  Wrote {min(len(rows), 200)} contractor readiness records to {OUT_PATH}")
    print(f"    Top 5: {[r['company'] for r in rows[:5]]}")


if __name__ == "__main__":
    main()
