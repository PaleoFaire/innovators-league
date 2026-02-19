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
    """Parse $600M or $2.5B to millions."""
    if not amount_str:
        return 0
    amount_str = amount_str.replace('+', '').replace('~', '').strip()
    match = re.match(r'\$(\d+(?:\.\d+)?)\s*([TBMKtbmk])', amount_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2).upper()
        multiplier = {"T": 1e6, "B": 1e3, "M": 1, "K": 0.001}.get(unit, 1)
        return num * multiplier
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

        # Track latest round
        date = deal.get("date", "")
        if date > cd["latest_date"]:
            cd["latest_date"] = date
            cd["latest_round"] = deal.get("round", "")
            cd["latest_amount"] = deal.get("amount", "")
            cd["latest_valuation"] = deal.get("valuation", "")

    print(f"Companies with funding data: {len(company_data)}")

    # Build FUNDING_TRACKER entries
    tracker = []
    for company, data in company_data.items():
        tracker.append({
            "company": company,
            "totalRaised": format_amount(data["total_raised_m"]),
            "totalRaisedRaw": data["total_raised_m"],
            "lastRound": data["latest_round"],
            "lastRoundAmount": data["latest_amount"],
            "lastRoundDate": data["latest_date"],
            "valuation": data["latest_valuation"],
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
