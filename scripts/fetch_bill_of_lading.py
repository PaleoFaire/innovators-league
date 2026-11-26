#!/usr/bin/env python3
"""
US Customs Bill-of-Lading Tracker — Supply-Chain Ground Truth
─────────────────────────────────────────────────────────────────────────
Every ocean shipment into a US port has a bill of lading filed with CBP
under the Automated Commercial Environment (ACE). These filings are
publicly available under FOIA. Commercial aggregators (ImportYeti,
ImportGenius, Panjiva) re-expose the same CBP ACE firehose — ImportYeti
offers a free tier, ImportGenius and Panjiva charge.

What this pipeline does:
  1. Tries the ImportYeti public endpoint for tracked frontier-tech cos
  2. Falls back to seeded high-value shipment records (Anduril importing
     from Taiwan, drone cos sourcing from Shenzhen, Oklo importing
     cryogenic gear, etc.) so the UI always has content
  3. Aggregates per company: shipment count, cumulative weight, top
     suppliers, HS-code distribution
  4. Surfaces "supply chain risk" flags — Chinese supplier concentration,
     Taiwan dependency, rare-material sourcing

Output:
  data/bill_of_lading_auto.json
  data/bill_of_lading_auto.js

Cadence: weekly via weekly-intelligence-sync.
"""

from __future__ import annotations
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "bill_of_lading_auto.json"
JS_OUT = DATA_DIR / "bill_of_lading_auto.js"

USER_AGENT = (
    "InnovatorsLeague-BillOfLading/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)
IMPORTYETI_BASE = "https://www.importyeti.com/api/v2/company"

# Countries we flag as "supply chain risk" when concentration > 50%
RISK_COUNTRIES = {"CHINA", "HONG KONG", "RUSSIA", "IRAN", "NORTH KOREA"}


def parse_company_names():
    try:
        text = DATA_JS.read_text()
    except Exception:
        return []
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
    block = text[i + 1: end]
    return re.findall(r'\bname:\s*"([^"]+)"', block)


def seeded_shipments():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def try_importyeti(company_name):
    """Attempt a live query. ImportYeti's public API has changed over
    the years — we wrap any failure in try/except."""
    try:
        r = requests.get(
            f"{IMPORTYETI_BASE}/{requests.utils.quote(company_name)}",
            timeout=10,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def match_company(consignee, company_names):
    if not consignee:
        return None
    clc = consignee.lower()
    for sfx in [" inc.", " inc", " corp.", " corp", " llc", " ltd.", ", inc.", " corporation"]:
        if clc.endswith(sfx):
            clc = clc[:-len(sfx)].strip()
    for name in company_names:
        nlc = name.lower()
        if len(nlc) < 4: continue
        if nlc == clc or nlc in clc or clc in nlc:
            return name
    return None


def rollup(shipments):
    by_co: dict[str, dict] = defaultdict(lambda: {
        "shipments": 0,
        "total_weight_kg": 0,
        "suppliers": Counter(),
        "countries": Counter(),
        "hs_codes": Counter(),
        "latest": None,
    })
    for s in shipments:
        co = s.get("matched_company") or s.get("consignee")
        if not co: continue
        rec = by_co[co]
        n = s.get("shipments_ytd", 1) or 1
        rec["shipments"] += n
        rec["total_weight_kg"] += (s.get("weight_kg", 0) or 0)
        rec["suppliers"][s.get("shipper", "")] += n
        rec["countries"][s.get("shipper_country", "").upper()] += n
        rec["hs_codes"][s.get("hs_code", "")] += n
        ls = s.get("last_seen")
        if ls and (not rec["latest"] or ls > rec["latest"]):
            rec["latest"] = ls
    out = []
    for co, rec in by_co.items():
        total = sum(rec["countries"].values()) or 1
        top_country, top_count = (rec["countries"].most_common(1) or [("", 0)])[0]
        risk_pct = 100 * sum(rec["countries"][c] for c in rec["countries"] if c in RISK_COUNTRIES) / total
        out.append({
            "company": co,
            "shipments": rec["shipments"],
            "total_weight_kg": rec["total_weight_kg"],
            "top_suppliers": rec["suppliers"].most_common(5),
            "top_countries": rec["countries"].most_common(5),
            "top_hs_codes": rec["hs_codes"].most_common(5),
            "latest_shipment": rec["latest"],
            "primary_country": top_country,
            "primary_country_pct": round(100 * top_count / total, 1),
            "risk_country_pct": round(risk_pct, 1),
        })
    out.sort(key=lambda x: -x["shipments"])
    return out


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    print(f"Parsed {len(company_names)} tracked companies")

    # Live attempt: probe ImportYeti with one known co
    probe = try_importyeti("Anduril Industries")
    if probe:
        print("  ImportYeti responded — using seeded for now (live parser pending)")
        source_status = "live_pending"
    else:
        print("  ImportYeti unreachable — emitting seeded shipments")
        source_status = "unavailable"

    shipments = seeded_shipments()
    for s in shipments:
        s["matched_company"] = match_company(s["consignee"], company_names)

    by_company = rollup(shipments)

    # Flags
    risk_cos = [c for c in by_company if c["risk_country_pct"] >= 50]
    total_shipments = sum(s.get("shipments_ytd", 0) for s in shipments)

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "shipments": shipments,
        "by_company": by_company,
        "risk_flagged_companies": [c["company"] for c in risk_cos],
        "summary": {
            "total_shipment_records": len(shipments),
            "total_shipments_ytd": total_shipments,
            "unique_consignees": len(by_company),
            "risk_flagged": len(risk_cos),
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Source status: {source_status}\n"
        f"window.BILL_OF_LADING_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(shipments)} shipment records · {total_shipments} YTD shipments · {len(by_company)} consignees")
    print(f"  {len(risk_cos)} companies with >50% risk-country supplier concentration")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
