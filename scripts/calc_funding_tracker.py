#!/usr/bin/env python3
"""
Funding Tracker Calculator for The Innovators League
Aggregates funding data from DEAL_TRACKER into a summary view:
  - Total raised per company
  - Latest round info
  - Lead investors
  - Funding velocity

Uses deals_auto.json (from fetch_deals.py) as primary source.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"


def parse_amount(amount_str):
    """Parse $600M or $2.5B to millions.

    Includes sanity cap: individual deal amounts above $15B are almost certainly
    misparses from news articles (market sizes, government budgets, etc.)
    and are rejected. The only exceptions are mega-rounds from OpenAI/Anthropic scale.
    """
    if not amount_str:
        return 0
    amount_str = amount_str.replace('+', '').replace('~', '').strip()
    match = re.match(r'\$(\d+(?:\.\d+)?)\s*([TBMKtbmk])', amount_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2).upper()
        multiplier = {"T": 1e6, "B": 1e3, "M": 1, "K": 0.001}.get(unit, 1)
        amount_m = num * multiplier
        # Sanity cap: reject deals > $15B ($15000M) — likely misparses
        # Even the largest real startup rounds (OpenAI $6.6B, Anthropic $8B) are below this
        if amount_m > 15000:
            return 0
        return amount_m
    return 0


def format_amount(millions):
    """Format millions to human-readable."""
    if millions >= 1000:
        return f"${millions/1000:.1f}B+"
    elif millions >= 1:
        return f"${millions:.0f}M+"
    return "$0"


def load_deals():
    """Load deals from auto JSON or data.js."""
    deals_path = DATA_DIR / "deals_auto.json"
    if deals_path.exists():
        with open(deals_path) as f:
            return json.load(f)

    # Fallback: parse from data.js
    if DATA_JS_PATH.exists():
        with open(DATA_JS_PATH) as f:
            content = f.read()
        match = re.search(r'const DEAL_TRACKER = \[([\s\S]*?)\];', content)
        if match:
            deals = []
            for obj in re.finditer(r'\{([^}]+)\}', match.group(1)):
                deal = {}
                for field in ['company', 'investor', 'amount', 'round', 'date', 'valuation']:
                    fm = re.search(rf'{field}:\s*"([^"]*)"', obj.group(1))
                    if fm:
                        deal[field] = fm.group(1)
                if deal.get('company'):
                    deals.append(deal)
            return deals
    return []


def load_curated_funding():
    """name -> (totalRaised, valuation) from the hand-maintained COMPANIES records.

    The deal feed only sees rounds that made the news since early 2025, so its
    sum is not a company's total: it showed Anduril at "$2.5B+" raised when the
    real figure was $11B+. The curated record is the authority for the total,
    and for which companies belong in the tracker at all.
    """
    if not DATA_JS_PATH.exists():
        return {}
    content = DATA_JS_PATH.read_text()
    start = content.find("const COMPANIES")
    end = content.find("\n];", start)
    if start < 0 or end < 0:
        return {}
    block = content[start:end]
    names = list(re.finditer(r'\n    name:\s*"((?:[^"\\]|\\.)*)"', block))
    curated = {}
    for i, m in enumerate(names):
        rec = block[m.end(): names[i + 1].start() if i + 1 < len(names) else len(block)]
        tr = re.search(r'\n    totalRaised:\s*"((?:[^"\\]|\\.)*)"', rec)
        va = re.search(r'\n    valuation:\s*"((?:[^"\\]|\\.)*)"', rec)
        curated[m.group(1)] = (tr.group(1) if tr else "", va.group(1) if va else "")
    return curated


def main():
    print("=" * 60)
    print("Funding Tracker Calculator")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    deals = load_deals()
    print(f"Deals loaded: {len(deals)}")

    # Aggregate by company
    company_data = defaultdict(lambda: {
        "total_raised_m": 0,
        "rounds": [],
        "lead_investors": [],
        "latest_date": "",
        "latest_round": "",
        "latest_amount": "",
        "latest_valuation": "",
    })

    for deal in deals:
        company = deal.get("company", "")
        if not company:
            continue

        cd = company_data[company]
        amount_m = parse_amount(deal.get("amount", ""))

        # Only count each round once (by amount + date combo)
        round_key = f"{deal.get('amount', '')}|{deal.get('date', '')}"
        if round_key not in cd["rounds"]:
            cd["total_raised_m"] += amount_m
            cd["rounds"].append(round_key)

        # Track lead investors
        if deal.get("leadOrParticipant") == "lead" and deal.get("investor"):
            if deal["investor"] not in cd["lead_investors"]:
                cd["lead_investors"].append(deal["investor"])

        # Track latest round.
        # Only accept the round if parse_amount() also accepts it. The raw
        # string was previously written straight through, so the $15B sanity
        # cap guarded total_raised_m but NOT the displayed lastRoundAmount —
        # which is how "$510B" (Amca), "$392B" (ARC Clean Technology, total
        # raised $14M) and "$188B" (Databricks' valuation, not a round) reached
        # FUNDING_TRACKER. A blank amount is better than a fabricated one.
        date = deal.get("date", "")
        raw_amount = deal.get("amount", "")
        if date > cd["latest_date"] and (amount_m > 0 or not raw_amount):
            cd["latest_date"] = date
            cd["latest_round"] = deal.get("round", "")
            cd["latest_amount"] = raw_amount if amount_m > 0 else ""
            cd["latest_valuation"] = deal.get("valuation", "")

    print(f"Companies with funding data: {len(company_data)}")

    # Build FUNDING_TRACKER entries. Only companies in the database belong
    # here; their total (and, failing a disclosed round valuation, their
    # valuation) comes from the curated record, not from the news-feed sum.
    curated = load_curated_funding()
    tracker = []
    for company, data in company_data.items():
        if curated and company not in curated:
            continue
        cur_total, cur_val = curated.get(company, ("", ""))
        total_raw = max(data["total_raised_m"], parse_amount(cur_total))
        valuation = data["latest_valuation"]
        if not valuation and cur_val and parse_amount(cur_val) > 0:
            valuation = cur_val
        tracker.append({
            "company": company,
            "totalRaised": cur_total if parse_amount(cur_total) > 0 else format_amount(data["total_raised_m"]),
            "totalRaisedRaw": total_raw,
            "lastRound": data["latest_round"],
            "lastRoundAmount": data["latest_amount"],
            "lastRoundDate": data["latest_date"],
            "valuation": valuation,
            "leadInvestors": data["lead_investors"][:5],
            "roundCount": len(data["rounds"]),
        })

    # Sort by total raised descending
    tracker.sort(key=lambda x: x["totalRaisedRaw"], reverse=True)

    # Save
    output_path = DATA_DIR / "funding_tracker_auto.json"
    with open(output_path, "w") as f:
        json.dump(tracker, f, indent=2)

    print(f"Saved {len(tracker)} entries to {output_path}")

    if tracker:
        print("\nTop 10 by Total Raised:")
        for t in tracker[:10]:
            investors = ", ".join(t["leadInvestors"][:3]) or "N/A"
            print(f"  {t['company']:30s} | {t['totalRaised']:>10s} | {t['lastRound']} | {investors}")

    print("=" * 60)


if __name__ == "__main__":
    main()
