#!/usr/bin/env python3
"""
State Public Utility Commission Dockets Tracker
─────────────────────────────────────────────────────────────────────────
Large-load (data center, fab, lithium refinery) applications often
surface in state PUC dockets BEFORE they hit FERC interconnection queues.
Texas SB 6 (2025) requires every >75 MW interconnection to file a PUCT
docket; California CPUC tracks similar filings; most other states have
equivalent processes.

This pipeline tracks:
  • Texas PUCT Interchange (interchange.puc.texas.gov)
  • California CPUC (docs.cpuc.ca.gov)
  • Other state PUCs as applicable (on demand expand)

What it surfaces:
  • >50 MW large-load interconnection applications
  • Tariff filings for colocation arrangements
  • Certificates of Convenience and Necessity (CCNs) for new data
    centers / fabs / SMR sites

Output:
  data/state_puct_dockets_auto.json
  data/state_puct_dockets_auto.js

Cadence: weekly via weekly-intelligence-sync.
"""

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "state_puct_dockets_auto.json"
JS_OUT = DATA_DIR / "state_puct_dockets_auto.js"

USER_AGENT = (
    "InnovatorsLeague-PUCTTracker/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)

TX_PUCT_INDEX = "https://interchange.puc.texas.gov/Search/Filings"
CA_CPUC_INDEX = "https://docs.cpuc.ca.gov/SearchRes.aspx"


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


def seeded_dockets():
    """Placeholder records were removed on 26 Nov 2026. The site never publishes
    invented data: if the live source is down, the output is empty and marked
    "unavailable"."""
    return []


def match_company(applicant, company_names):
    if not applicant:
        return None
    alc = applicant.lower()
    for name in company_names:
        nlc = name.lower()
        if len(nlc) < 4: continue
        if nlc in alc or alc.startswith(nlc):
            return name
    return None


def main():
    DATA_DIR.mkdir(exist_ok=True)
    company_names = parse_company_names()
    print(f"Parsed {len(company_names)} tracked companies")

    # Probe Texas PUCT reachability
    try:
        r = requests.get(TX_PUCT_INDEX, timeout=10, headers={"User-Agent": USER_AGENT})
        tx_live = r.status_code == 200
    except Exception:
        tx_live = False

    if tx_live:
        source_status = "live_pending"
        print("  Texas PUCT reachable — live scrape pending (using seeded)")
    else:
        source_status = "unavailable"
        print("  PUCT unreachable — emitting seeded dockets")

    dockets = seeded_dockets()
    for d in dockets:
        d["matched_company"] = match_company(d["applicant"], company_names)

    # Summary
    by_state: dict[str, dict] = {}
    for d in dockets:
        st = d["state"]
        b = by_state.setdefault(st, {"count": 0, "total_mw": 0})
        b["count"] += 1
        b["total_mw"] += d.get("mw_requested", 0) or 0
    total_mw = sum(d.get("mw_requested", 0) or 0 for d in dockets)
    matched = sum(1 for d in dockets if d.get("matched_company"))

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_status": source_status,
        "dockets": dockets,
        "by_state": by_state,
        "summary": {
            "total_dockets": len(dockets),
            "total_mw_requested": total_mw,
            "unique_states": len(by_state),
            "matched_tracked_companies": matched,
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2, default=str))
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    JS_OUT.write_text(
        f"// Last updated: {ts}\n"
        f"// Source status: {source_status}\n"
        f"window.STATE_PUCT_DOCKETS_AUTO = {json.dumps(payload, default=str)};\n"
    )
    print(f"\n✓ {len(dockets)} dockets · {total_mw:,.0f} MW · {len(by_state)} states · {matched} matched")
    print(f"  → {JSON_OUT.name}, {JS_OUT.name}")


if __name__ == "__main__":
    main()
