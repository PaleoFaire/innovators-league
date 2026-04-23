#!/usr/bin/env python3
"""
USPTO Trademark Filings Watch
─────────────────────────────────────────────────────────────────────────
Trademarks leak product launches 6-12 months before public reveals.
For frontier tech: when a company files a trademark for a new product
or brand name, the USPTO publishes it within days.

Why it matters:
  • New product names before the reveal event
    ("Anduril files LATTICE AEGIS" → new product line coming)
  • Subsidiary / joint-venture formation
    ("SpaceX Starshield" → defense-specific subsidiary)
  • Strategic pivots (marks in new Nice classes reveal category
    expansion — defense company filing in class 10 medical devices)

Source: USPTO Trademark APIs via the developer.uspto.gov gateway.
As of Oct 2024 USPTO requires a free API key — get one at
https://developer.uspto.gov/api-catalog and set USPTO_API_KEY in
GitHub Actions secrets.

When no key is set, this script writes placeholder-status output so
downstream consumers (company-profile.js, daily digest) don't blow up
— they show "awaiting USPTO API key" rather than empty sections.

Output:
  data/trademarks_raw.json       — raw API responses per company
  data/trademarks_auto.json      — enriched, flat row list
  data/trademarks_auto.js        — browser-ready global TRADEMARK_FILINGS

Cadence: weekly via weekly-extended-sync.
"""

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS  = ROOT / "data.js"

RAW_OUT  = DATA_DIR / "trademarks_raw.json"
AUTO_OUT = DATA_DIR / "trademarks_auto.json"
JS_OUT   = DATA_DIR / "trademarks_auto.js"

USPTO_API_KEY = os.environ.get("USPTO_API_KEY", "").strip()

# Official USPTO Trademark Search endpoint (post-Oct-2024 gateway).
# Per their docs: GET /api/v1/search/trademark with query param, api-key header.
# Field reference: https://developer.uspto.gov/api-catalog/trademark-apis
USPTO_ENDPOINT = "https://api.uspto.gov/api/v1/search/trademark"

HEADERS_BASE = {
    "User-Agent": "InnovatorsLeague/1.0 contact@innovatorsleague.com",
    "Accept": "application/json",
}

# Days of history per run. Trademark processing is slow (180d captures
# typical first-publication-to-public window) but we still run weekly.
LOOKBACK_DAYS = 365  # 12 months covers most product roadmaps

# Nice classes most meaningful for frontier tech
FRONTIER_CLASSES = {
    "9":  "Electronics / Software / Scientific Instruments",
    "12": "Vehicles / Aerospace",
    "13": "Firearms / Munitions",
    "5":  "Pharmaceuticals / Biotech",
    "10": "Medical Devices",
    "40": "Manufacturing / Treatment Services",
    "42": "Scientific & Technology Services",
    "45": "Security Services",
    "7":  "Machinery / Industrial",
    "38": "Telecommunications",
    "39": "Transportation / Satellite Services",
    "41": "Education / Training",
    "35": "Business / Consulting",
    "37": "Construction / Repair",
}

# IL30 gets priority scanning per run to keep within rate limits.
PRIORITY_CAP = 100

# Courtesy rate limit (USPTO allows 500 req/day free; 0.3s between calls
# stays well under)
REQUEST_DELAY_S = 0.3


def parse_tracked_companies():
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
    block = text[i + 1:end] if end else ""
    companies = []
    for m in re.finditer(r'\{[^{}]*?\bname:\s*"((?:[^"\\]|\\.)+)"[^{}]*?'
                         r'\bsector:\s*"((?:[^"\\]|\\.)*)"', block):
        companies.append({"name": m.group(1), "sector": m.group(2)})
    return companies


def parse_priority_names():
    text = DATA_JS.read_text()
    m = re.search(r"const INNOVATORS_LEAGUE_30\s*=\s*\[([^\]]+)\]", text, re.DOTALL)
    if not m: return []
    return [n.group(1) for n in re.finditer(r'"((?:[^"\\]|\\.)+)"', m.group(1))]


def search_uspto(owner_name):
    """Query USPTO for marks owned by a company. Returns list of hits.

    Query shape per USPTO docs:
      GET /api/v1/search/trademark
        ?query=<owner>&searchFields=ownerName&rows=100&from=0
      Headers: X-API-Key: <USPTO_API_KEY>
    """
    if not USPTO_API_KEY:
        return []
    params = {
        "query": owner_name,
        "searchFields": "ownerName",
        "rows": 50,
        "from": 0,
    }
    headers = dict(HEADERS_BASE, **{"X-API-Key": USPTO_API_KEY})
    try:
        r = requests.get(USPTO_ENDPOINT, params=params, headers=headers, timeout=20)
        if r.status_code == 401:
            print("  USPTO 401 — API key rejected. Check USPTO_API_KEY in secrets.")
            return []
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("results") or data.get("trademarks") or []
    except Exception as e:
        print(f"  USPTO fetch error for {owner_name}: {e}")
        return []


def _format_hit(raw, company, sector):
    """Normalize one USPTO search result into our row shape. USPTO's
    response varies a bit between endpoints; we probe multiple field
    names so we don't depend on a specific version."""
    serial = str(raw.get("serialNumber") or raw.get("serial_number") or "")
    mark   = (raw.get("markLiteralElement") or raw.get("mark") or "").strip()
    filing = (raw.get("filingDate") or raw.get("filing_date") or "")[:10]
    status = (raw.get("currentStatusDescription") or
              raw.get("status") or "").strip()
    # Nice classes can appear in several shapes — collect all numbers
    classes = []
    classes_raw = raw.get("niceClass") or raw.get("classCodes") or []
    if isinstance(classes_raw, list):
        for c in classes_raw:
            if isinstance(c, dict):
                val = str(c.get("code") or c.get("class") or "")
            else:
                val = str(c)
            for num in re.findall(r"\d+", val):
                if num not in classes: classes.append(num)
    elif isinstance(classes_raw, str):
        for num in re.findall(r"\d+", classes_raw):
            if num not in classes: classes.append(num)
    return {
        "company":      company,
        "sector":       sector,
        "mark":         mark,
        "serial_number": serial,
        "filing_date":  filing,
        "status":       status[:80],
        "nice_classes": classes,
        "nice_class_labels": [FRONTIER_CLASSES.get(c, f"Class {c}") for c in classes],
        "source_url":   f"https://tsdr.uspto.gov/#caseNumber={serial}&caseType=SERIAL_NO&searchType=statusSearch",
    }


def main():
    print("=" * 68)
    print("USPTO Trademark Filings Watch")
    print(f"Lookback: {LOOKBACK_DAYS} days")
    print(f"USPTO_API_KEY set: {'yes' if USPTO_API_KEY else 'NO'}")
    print("=" * 68)

    companies = parse_tracked_companies()
    by_name = {c["name"]: c for c in companies}
    priority = parse_priority_names()
    priority_set = set(priority)
    targets = (
        [c for c in companies if c["name"] in priority_set] +
        sorted([c for c in companies if c["name"] not in priority_set],
               key=lambda x: x["name"])
    )[:PRIORITY_CAP]
    print(f"Tracked: {len(companies)}  |  Priority scan: {len(targets)}")

    cutoff = (datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    all_rows = []
    raw_by_company = {}

    if not USPTO_API_KEY:
        # Emit placeholder-status output so downstream consumers don't
        # treat this as a dead pipeline. This matches the pattern used
        # by LinkedIn headcount / Twitter signals when their keys aren't
        # yet configured.
        placeholders = [{
            "company":      c["name"],
            "sector":       c["sector"],
            "status":       "awaiting_uspto_api_key",
            "mark":         None,
            "serial_number": None,
            "filing_date":  None,
            "nice_classes": [],
        } for c in targets[:30]]
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source":       "USPTO Trademark API (pending configuration)",
            "status":       "awaiting_uspto_api_key",
            "message":      "Set USPTO_API_KEY in GitHub Actions secrets. Free at "
                            "https://developer.uspto.gov/api-catalog",
            "lookback_days": LOOKBACK_DAYS,
            "total_hits":    0,
            "trademarks":    placeholders,
        }
        RAW_OUT.write_text(json.dumps({"status": "awaiting_api_key"}, indent=2))
        AUTO_OUT.write_text(json.dumps(payload, indent=2))
        header = (
            f"// Auto-generated USPTO trademark filings — awaiting API key\n"
            f"// Set USPTO_API_KEY in GitHub Actions secrets. Free at\n"
            f"// https://developer.uspto.gov/api-catalog\n"
            f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        )
        body = f"const TRADEMARK_FILINGS = {json.dumps(payload, indent=2, ensure_ascii=False)};\n"
        JS_OUT.write_text(header + body)
        print("USPTO_API_KEY not set — wrote placeholder output and exiting cleanly.")
        return

    # Real run
    for i, c in enumerate(targets):
        hits = search_uspto(c["name"])
        raw_by_company[c["name"]] = hits
        for h in hits:
            row = _format_hit(h, c["name"], c["sector"])
            # Filter to lookback window when filing date is known
            if row["filing_date"] and row["filing_date"] < cutoff:
                continue
            all_rows.append(row)
        if (i + 1) % 20 == 0:
            print(f"  [{i + 1}/{len(targets)}] scanned  (cumulative: {len(all_rows)})")
        time.sleep(REQUEST_DELAY_S)

    # Sort by filing date desc
    all_rows.sort(key=lambda r: r.get("filing_date") or "", reverse=True)

    RAW_OUT.write_text(json.dumps(raw_by_company, indent=2))

    from collections import Counter
    by_co = Counter(r["company"] for r in all_rows)
    by_cls = Counter(c for r in all_rows for c in r.get("nice_classes", []))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source":       "USPTO Trademark Search API",
        "lookback_days": LOOKBACK_DAYS,
        "targets_scanned": len(targets),
        "total_hits":      len(all_rows),
        "by_company":      dict(by_co.most_common(20)),
        "by_nice_class":   dict(by_cls.most_common(10)),
        "trademarks":      all_rows,
    }
    AUTO_OUT.write_text(json.dumps(payload, indent=2))

    header = (
        f"// Auto-generated USPTO trademark filings (last {LOOKBACK_DAYS} days)\n"
        f"// Source: USPTO Trademark Search API\n"
        f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"// {len(all_rows)} filings across {len(by_co)} tracked companies\n"
    )
    body = f"const TRADEMARK_FILINGS = {json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    JS_OUT.write_text(header + body)

    print(f"\nWrote {AUTO_OUT.name}  ({len(all_rows)} filings)")
    if all_rows[:8]:
        print("\nMost recent trademark filings:")
        for r in all_rows[:8]:
            cls = "/".join(r.get("nice_classes") or ["?"])
            print(f"  {r['filing_date']}  {r['company']:25s}  \"{r['mark'][:40]:40s}\"  classes={cls}")


if __name__ == "__main__":
    main()
