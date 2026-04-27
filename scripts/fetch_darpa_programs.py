#!/usr/bin/env python3
"""
DARPA Performer Map fetcher.

Pulls every contract awarded by the Defense Advanced Research Projects Agency
(USAspending sub-agency: "Defense Advanced Research Projects Agency") for the
last 5 fiscal years.

Strategy:
  1. Pull all DARPA contracts from USAspending API
  2. Match recipient names to our COMPANIES list (frontier-tech sub-set)
  3. Cluster by program area (parsed from description: e.g. "HAWC", "OPS-5G",
     "AIE", "GARDEN") and by recipient
  4. Emit data/darpa_programs_auto.json + .js with:
       - performers list (recipient + total $ + program count + sample programs)
       - program clusters
       - timeline of awards

Sources:
  - USAspending API: api.usaspending.gov/api/v2/search/spending_by_award/
  - DARPA.mil/program-list (linked for verification, not scraped here)

Trust contract: every dollar amount, recipient, and award ID is sourced
directly from USAspending. No estimation, no inference.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
COMPANIES_JS = ROOT / "data.js"
OUT_JSON = ROOT / "data" / "darpa_programs_auto.json"
OUT_JS = ROOT / "data" / "darpa_programs_auto.js"

API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
HEADERS = {"User-Agent": "Mozilla/5.0 (ROS Innovators League)"}

# Lookback window — DARPA programs typically have 3-5 year cycles
LOOKBACK_START = "2020-01-01"
LOOKBACK_END = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def extract_companies():
    """Parse the COMPANIES array from data.js to get the frontier-tech roster."""
    if not COMPANIES_JS.exists():
        return []
    src = COMPANIES_JS.read_text(encoding="utf-8", errors="replace")
    # Find the COMPANIES array start
    m = re.search(r"const COMPANIES\s*=\s*\[", src)
    if not m:
        return []
    # Brace-aware scan
    start = m.end() - 1
    depth = 0
    end = start
    in_str = False
    str_q = None
    in_comment = False
    i = start
    while i < len(src):
        ch = src[i]
        nx = src[i + 1] if i + 1 < len(src) else ""
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == str_q:
                in_str = False
        elif in_comment:
            if ch == "*" and nx == "/":
                in_comment = False
                i += 2
                continue
        else:
            if ch == "/" and nx == "/":
                # line comment
                while i < len(src) and src[i] != "\n":
                    i += 1
                continue
            if ch == "/" and nx == "*":
                in_comment = True
                i += 2
                continue
            if ch in ('"', "'", "`"):
                in_str = True
                str_q = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1

    block = src[start:end]
    # Just extract names + sectors via regex (avoid full JS parse)
    out = []
    for nm in re.finditer(r'name:\s*"([^"]+)"[^}]*?sector:\s*"([^"]*)"', block, re.S):
        out.append({"name": nm.group(1).strip(), "sector": nm.group(2).strip()})
    return out


def fuzzy_match_company(recipient, companies):
    """Match a USAspending recipient name to one of our COMPANIES entries.
    Returns the matched company name or None."""
    if not recipient:
        return None
    rec_norm = re.sub(r"[^a-z0-9 ]", "", recipient.lower()).strip()
    rec_words = set(rec_norm.split())
    for c in companies:
        cname = c["name"].lower()
        cname_norm = re.sub(r"[^a-z0-9 ]", "", cname).strip()
        # Direct word-boundary match
        if re.search(r"\b" + re.escape(cname_norm) + r"\b", rec_norm):
            return c["name"]
        # Multi-word company → all tokens must appear
        c_words = set(cname_norm.split())
        if len(c_words) >= 2 and c_words.issubset(rec_words):
            return c["name"]
    return None


PROGRAM_KEYWORDS = [
    "AIE", "ALIAS", "ASIST", "ASTRA", "ATLAS", "BLACKJACK", "CASE", "CHIPS", "COFFEE",
    "GAMBIT", "GARDEN", "GLIDE", "GREMLINS", "HAWC", "HORSEPLAY", "HYPERSPECTRAL",
    "LATITUDE", "LIBERTY", "LONGSHOT", "MASS", "MOABB", "MORPHEUS", "OPS-5G",
    "OFFSET", "OFFENSIVE SWARM", "RACE", "RACER", "RANGE", "REMA", "REMODEL",
    "RGU", "RECONSURV", "ROBOSUB", "SAILS", "SCISRS", "SCOUT", "SEACOR", "SIDARM",
    "SIGNETIC", "SIGNAL", "SIGMA+", "STRIDE", "SUBT", "SuperBEACON", "SyNAPSE",
    "TIDES", "TRACE", "TRADES", "TROJAN", "USE", "VAMP", "VANTAGE", "VECTORS",
    "WARP", "ZAGREB",
    # Tech areas (used as fallback grouping)
    "HYPERSONIC", "QUANTUM", "AUTONOMOUS", "BIOSURVEILLANCE", "BIOLOGICAL",
    "ROBOTICS", "AI/ML", "CYBER", "SPACE", "SATELLITE", "DIRECTED ENERGY",
]


def extract_program(description):
    if not description:
        return None
    desc_upper = description.upper()
    for kw in PROGRAM_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", desc_upper):
            return kw
    return None


def fetch_darpa_awards(max_pages=20):
    """Pull DARPA awards from USAspending in pages of 100."""
    all_results = []
    payload_template = {
        "filters": {
            "agencies": [
                {"type": "awarding", "tier": "subtier",
                 "name": "Defense Advanced Research Projects Agency"}
            ],
            "award_type_codes": ["A", "B", "C", "D"],  # Contract types
            "time_period": [{"start_date": LOOKBACK_START, "end_date": LOOKBACK_END}]
        },
        "fields": [
            "Award ID", "Recipient Name", "Award Amount", "Description",
            "Start Date", "End Date", "awarding_sub_agency_name", "Award Type"
        ],
        "limit": 100,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc"
    }
    for page in range(1, max_pages + 1):
        payload = dict(payload_template)
        payload["page"] = page
        try:
            r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  Page {page}: HTTP {r.status_code}")
                break
            data = r.json()
            results = data.get("results", [])
            if not results:
                break
            all_results.extend(results)
            if len(results) < 100:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  Page {page}: ERROR {e}")
            break
    print(f"  Fetched {len(all_results)} DARPA awards from USAspending")
    return all_results


def main():
    print("=" * 60)
    print("DARPA Performer Map · USAspending pull")
    print("=" * 60)

    companies = extract_companies()
    print(f"  Loaded {len(companies)} companies from data.js")

    awards = fetch_darpa_awards()
    if not awards:
        print("  ❌ No awards returned. Aborting.")
        return 1

    # Annotate each award with: matched ROS company, program tag, ID + URL
    annotated = []
    for a in awards:
        recipient = a.get("Recipient Name") or ""
        award_id = a.get("Award ID") or ""
        amt = a.get("Award Amount") or 0
        desc = a.get("Description") or ""
        matched = fuzzy_match_company(recipient, companies)
        prog = extract_program(desc)
        annotated.append({
            "awardId": award_id,
            "recipient": recipient,
            "rosCompany": matched,
            "amount": amt,
            "amountFormatted": fmt_dollar(amt),
            "description": desc[:200],
            "program": prog,
            "startDate": a.get("Start Date"),
            "endDate": a.get("End Date"),
            "awardType": a.get("Award Type"),
            "verifyUrl": (
                f"https://www.usaspending.gov/award/CONT_AWD_{award_id}"
                if award_id else None
            ),
        })

    # Performer aggregation: per recipient (matched OR raw)
    by_performer = {}
    for a in annotated:
        key = a["rosCompany"] or a["recipient"]
        if not key:
            continue
        bp = by_performer.setdefault(key, {
            "performer": key,
            "isRosCompany": bool(a["rosCompany"]),
            "totalAwarded": 0,
            "awardCount": 0,
            "programs": set(),
            "topAwards": [],
            "lastDate": "",
        })
        bp["totalAwarded"] += a["amount"]
        bp["awardCount"] += 1
        if a["program"]:
            bp["programs"].add(a["program"])
        bp["topAwards"].append(a)
        if a["startDate"] and a["startDate"] > bp["lastDate"]:
            bp["lastDate"] = a["startDate"]

    performers = []
    for k, v in by_performer.items():
        v["programs"] = sorted(v["programs"])
        v["topAwards"] = sorted(v["topAwards"], key=lambda x: x["amount"], reverse=True)[:5]
        v["totalAwardedFormatted"] = fmt_dollar(v["totalAwarded"])
        performers.append(v)
    performers.sort(key=lambda x: x["totalAwarded"], reverse=True)

    # Program clusters: per program tag
    by_program = {}
    for a in annotated:
        if not a["program"]:
            continue
        bp = by_program.setdefault(a["program"], {
            "program": a["program"],
            "totalAwarded": 0,
            "performerCount": set(),
            "rosPerformers": set(),
            "awards": []
        })
        bp["totalAwarded"] += a["amount"]
        bp["performerCount"].add(a["recipient"])
        if a["rosCompany"]:
            bp["rosPerformers"].add(a["rosCompany"])
        bp["awards"].append(a)

    programs = []
    for k, v in by_program.items():
        v["performerCount"] = len(v["performerCount"])
        v["rosPerformers"] = sorted(v["rosPerformers"])
        v["topAwards"] = sorted(v["awards"], key=lambda x: x["amount"], reverse=True)[:3]
        del v["awards"]
        v["totalAwardedFormatted"] = fmt_dollar(v["totalAwarded"])
        programs.append(v)
    programs.sort(key=lambda x: x["totalAwarded"], reverse=True)

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "USAspending API · spending_by_award (subtier: Defense Advanced Research Projects Agency)",
        "lookbackStart": LOOKBACK_START,
        "lookbackEnd": LOOKBACK_END,
        "totalAwards": len(annotated),
        "totalDollars": sum(a["amount"] for a in annotated),
        "totalDollarsFormatted": fmt_dollar(sum(a["amount"] for a in annotated)),
        "performerCount": len(performers),
        "rosMatchCount": sum(1 for a in annotated if a["rosCompany"]),
        "performers": performers,
        "programs": programs,
    }

    OUT_JSON.write_text(json.dumps(out, indent=2))
    js = (
        f"// Auto-generated from {OUT_JSON.name}\n"
        f"// Last updated: {out['generatedAt']}\n"
        f"const DARPA_PROGRAMS_AUTO = {json.dumps(out, indent=2)};\n"
        f"if (typeof window !== 'undefined') window.DARPA_PROGRAMS_AUTO = DARPA_PROGRAMS_AUTO;\n"
    )
    OUT_JS.write_text(js)

    print(f"✅ {OUT_JSON.relative_to(ROOT)}: {len(annotated)} awards, "
          f"{len(performers)} performers, {len(programs)} programs")
    print(f"✅ {OUT_JS.relative_to(ROOT)}: script-tag loadable")
    print(f"   ROS-matched performers: {sum(1 for p in performers if p['isRosCompany'])}")
    print(f"   Total $: {out['totalDollarsFormatted']}")
    return 0


def fmt_dollar(n):
    if not isinstance(n, (int, float)) or n == 0:
        return None
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    if n >= 1e3:
        return f"${n/1e3:.0f}K"
    return f"${n:,.0f}"


if __name__ == "__main__":
    raise SystemExit(main())
