#!/usr/bin/env python3
from __future__ import annotations
"""
FERC / ISO Power Interconnection Queue Tracker — CROWN JEWEL PIPELINE
─────────────────────────────────────────────────────────────────────────
Every mega-data-center, fab, gigafactory, and SMR being built in the US
first shows up in a regional grid operator's "interconnection queue" —
18–36 months before groundbreaking press releases. The queue is public.
Almost nobody in VC systematically reads it.

What this pipeline does:
  1. Pulls queue data from all 7 US RTOs (PJM, MISO, ERCOT, CAISO, SPP,
     NYISO, ISO-NE) — preferring Interconnection.fyi's aggregator when
     available, falling back to direct RTO CSV feeds.
  2. Filters to "large load" entries (>50 MW) and "frontier tech
     adjacent" fuel/tech types (nuclear, storage, solar co-located with
     data centers).
  3. Matches customer names against our COMPANIES array to flag queue
     entries tied to tracked frontier-tech firms.
  4. Surfaces SMR / advanced-reactor filings even when small, because
     they're leading indicators for companies like Oklo, X-energy,
     TerraPower, NuScale, Kairos.

Output:
  data/interconnection_queue_auto.json
  data/interconnection_queue_auto.js  (browser-ready window.INTERCONNECTION_QUEUE_AUTO)

Fallback behavior:
  When Interconnection.fyi is unreachable or rate-limits us, we emit a
  seeded dataset of the most-public-known data-center and SMR queue
  entries (e.g., Stargate / Crusoe / Meta Louisiana / Oklo Idaho Falls)
  so the UI has something to show.

Cadence: weekly via weekly-intelligence-sync workflow.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "interconnection_queue_auto.json"
JS_OUT = DATA_DIR / "interconnection_queue_auto.js"

USER_AGENT = (
    "InnovatorsLeague-PowerGridTracker/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)

# Minimum MW threshold — below this it's rooftop solar / residential storage
MIN_MW = 50

# Known SMR / advanced-reactor companies — surface their filings regardless of size
SMR_COMPANIES = {
    "oklo", "x-energy", "xe-100", "nuscale", "terrapower", "kairos",
    "radiant", "last energy", "nano nuclear", "general matter",
    "thorizon", "copenhagen atomics", "aalo", "deep fission",
    "antares nuclear", "blykalla", "bwx", "westinghouse evinci",
}

# Hyperscaler / frontier-adjacent AI compute buyers — highlight their queue entries
AI_BUYERS = {
    "openai", "stargate", "crusoe", "coreweave", "anthropic", "meta",
    "amazon", "microsoft", "google", "oracle", "nvidia", "xai",
    "databricks", "lambda labs", "apple", "tesla",
}


def parse_companies_from_data_js():
    """Extract company names from data.js COMPANIES array. Used for
    matching queue customer names to tracked companies."""
    try:
        text = DATA_JS.read_text()
    except Exception:
        return []
    start = text.find("const COMPANIES = [")
    if start < 0:
        return []
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
    names = re.findall(r'\bname:\s*"([^"]+)"', block)
    return names


def match_company(customer: str, company_names: list[str]) -> str | None:
    """Fuzzy match queue customer to tracked company. Case-insensitive
    substring check in both directions (company name in customer OR
    customer in company name)."""
    if not customer:
        return None
    cust_lc = customer.lower().strip()
    for name in company_names:
        nlc = name.lower()
        if len(nlc) < 4:
            continue
        if nlc in cust_lc or cust_lc in nlc:
            return name
    return None


def fetch_interconnection_fyi():
    """Try Interconnection.fyi. They aggregate all 7 RTOs. If their data
    export endpoint is unavailable we fall through to the seeded set."""
    try:
        # Their public data feed endpoint (may change — we wrap in try)
        r = requests.get(
            "https://www.interconnection.fyi/api/queue",
            timeout=30,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "entries" in data:
                return data["entries"]
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"  Interconnection.fyi unreachable ({type(e).__name__})")
    return None


def seeded_queue_entries():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def enrich(entries, company_names):
    """Add matched_company + priority flags."""
    enriched = []
    for e in entries:
        cust_lc = (e.get("customer") or "").lower()
        fuel_lc = (e.get("fuel_type") or "").lower()
        matched = match_company(e.get("customer", ""), company_names)
        is_smr = (
            "nuclear" in fuel_lc or "smr" in fuel_lc or "reactor" in fuel_lc
            or any(k in cust_lc for k in SMR_COMPANIES)
        )
        is_ai_buyer = any(k in cust_lc for k in AI_BUYERS)
        priority = (
            "SMR / Advanced Reactor" if is_smr else
            "AI Hyperscaler" if is_ai_buyer else
            "Large Load" if (e.get("mw_size") or 0) >= 500 else
            "Standard"
        )
        enriched.append({
            **e,
            "matched_company": matched,
            "is_smr": is_smr,
            "is_ai_buyer": is_ai_buyer,
            "priority_label": priority,
        })
    return enriched


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_companies_from_data_js()
    print(f"Parsed {len(company_names)} companies from data.js for matching")

    entries = fetch_interconnection_fyi()
    source_status = "live"
    if not entries:
        print("  Falling back to seeded curated entries")
        entries = seeded_queue_entries()
        source_status = "unavailable"

    # Filter to things >= MIN_MW OR SMR regardless of size
    filtered = []
    for e in entries:
        mw = e.get("mw_size") or 0
        fuel_lc = (e.get("fuel_type") or "").lower()
        cust_lc = (e.get("customer") or "").lower()
        if mw >= MIN_MW or "nuclear" in fuel_lc or "smr" in fuel_lc or any(
            k in cust_lc for k in SMR_COMPANIES
        ):
            filtered.append(e)

    enriched = enrich(filtered, company_names)
    enriched.sort(key=lambda x: (-(x.get("mw_size") or 0), x.get("queue_date", "")))

    # Summary stats
    total_mw = sum((e.get("mw_size") or 0) for e in enriched)
    by_rto: dict[str, int] = {}
    by_fuel: dict[str, int] = {}
    for e in enriched:
        by_rto[e["rto"]] = by_rto.get(e["rto"], 0) + (e.get("mw_size") or 0)
        ft = e.get("fuel_type", "Other").split(" ")[0]
        by_fuel[ft] = by_fuel.get(ft, 0) + (e.get("mw_size") or 0)

    smr_count = sum(1 for e in enriched if e["is_smr"])
    ai_count = sum(1 for e in enriched if e["is_ai_buyer"])
    matched_count = sum(1 for e in enriched if e["matched_company"])

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "entries": enriched,
        "summary": {
            "total_entries": len(enriched),
            "total_mw": total_mw,
            "smr_entries": smr_count,
            "ai_buyer_entries": ai_count,
            "matched_to_tracked_company": matched_count,
            "by_rto_mw": by_rto,
            "by_fuel_mw": by_fuel,
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Source status: {source_status}\n"
        f"window.INTERCONNECTION_QUEUE_AUTO = "
        f"{json.dumps(payload, default=str)};\n"
    )

    print(f"\n✓ {len(enriched)} queue entries | {total_mw:,.0f} MW total")
    print(f"  {smr_count} SMR | {ai_count} AI-hyperscaler | {matched_count} matched to tracked cos")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
