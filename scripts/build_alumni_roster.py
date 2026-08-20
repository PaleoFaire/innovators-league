#!/usr/bin/env python3
"""
Alumni roster from patent inventor records — the Exit Watch force multiplier
─────────────────────────────────────────────────────────────────────────
Exit Watch can only recognise a mafia founder it already knows about. Today
that roster is ~190 people, built from the curated FOUNDER_MAFIAS block and
the mafia clusters in our own database. That is enough to prove the mechanism
and far too small to fire often: 190 specific individuals against a 30-day
window of Form D filings is a very thin lottery.

This script fixes the bottleneck using the one source that is both large and
legally unambiguous: **granted patents**.

A patent record states, as a matter of public law, that a named person was an
inventor on an invention assigned to a named company. That is documented
employment evidence with a citation attached — patent number, grant date,
assignee. It is not an inference from a job-title string, and it is not
scraped from a site whose terms forbid it.

Why this beats every alternative we tested:
  • LinkedIn        — no lawful API, terms forbid scraping
  • OpenAlex        — free and large, but affiliation matching is loose. Its
                      top "SpaceX" author is a Johns Hopkins planetary
                      scientist who never worked there. Using it would
                      manufacture false claims about real people.
  • Podcast corpus  — genuinely proprietary and accurate, but pedigree is
                      stated conversationally and needs LLM extraction across
                      266 documents. Worth doing; it is a separate build.

One honest caveat, stated up front: **SpaceX deliberately files very few
patents.** Musk has said publicly that patents mainly help competitors copy
you. So this source is weak for the SpaceX mafia specifically and strong for
Palantir, Anduril, Tesla, NVIDIA, Google, Apple and Microsoft.

Requires PATENTSVIEW_API_KEY (free, registration only). Without it the script
writes status metadata rather than failing, matching the convention in
scripts/API_STATUS.md.

Output: data/alumni_roster.json

Usage:
    PATENTSVIEW_API_KEY=... python scripts/build_alumni_roster.py
    python scripts/build_alumni_roster.py --limit 200
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "alumni_roster.json"

PATENTSVIEW_V2 = "https://search.patentsview.org/api/v1/patent/"
API_KEY = os.environ.get("PATENTSVIEW_API_KEY", "").strip()
TIMEOUT = 40
THROTTLE = 0.8          # PatentsView is rate limited; be a good citizen

# Assignee strings to query, mapped to the mafia label Exit Watch uses.
# Multiple spellings per parent because assignee_organization is free text.
PARENTS = {
    "SpaceX":       ["Space Exploration Technologies"],
    "Palantir":     ["Palantir Technologies"],
    "Anduril":      ["Anduril Industries"],
    "Tesla":        ["Tesla, Inc.", "Tesla Motors"],
    "NVIDIA":       ["Nvidia Corporation"],
    "Neuralink":    ["Neuralink"],
    "Waymo":        ["Waymo LLC"],
    "Blue Origin":  ["Blue Origin"],
    "Rocket Lab":   ["Rocket Lab"],
    "OpenAI":       ["OpenAI"],
    "DeepMind":     ["DeepMind Technologies"],
    "Google":       ["Google LLC"],
    "Apple":        ["Apple Inc."],
    "Microsoft":    ["Microsoft Technology Licensing"],
    "Amazon/AWS":   ["Amazon Technologies"],
    "Meta":         ["Meta Platforms"],
}


def person_key(first: str, last: str) -> str:
    a = "".join(ch for ch in (first or "") if ch.isalpha())
    b = "".join(ch for ch in (last or "") if ch.isalpha())
    return (a + b).lower() if a and b else ""


def query_assignee(session, assignee: str, limit: int) -> list[dict]:
    """Every inventor on patents assigned to this organisation."""
    rows, page, size = [], 1, 100
    while len(rows) < limit:
        params = {
            "q": json.dumps({"_contains": {"assignees.assignee_organization": assignee}}),
            "f": json.dumps(["patent_id", "patent_date", "patent_title",
                             "inventors.inventor_name_first",
                             "inventors.inventor_name_last"]),
            "o": json.dumps({"size": min(size, limit - len(rows)), "page": page}),
        }
        try:
            r = session.get(PATENTSVIEW_V2, params=params,
                            headers={"X-Api-Key": API_KEY}, timeout=TIMEOUT)
        except Exception as e:
            print(f"    request failed for {assignee}: {e}")
            break
        if r.status_code == 429:
            time.sleep(5)
            continue
        if not r.ok:
            print(f"    HTTP {r.status_code} for {assignee}")
            break
        js = r.json()
        batch = js.get("patents") or js.get("data", {}).get("patents") or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < size:
            break
        page += 1
        time.sleep(THROTTLE)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400,
                    help="max patents to pull per parent company")
    args = ap.parse_args()

    print("=" * 72)
    print("Alumni roster — patent inventor records")
    print("=" * 72)

    DATA.mkdir(exist_ok=True)

    if not API_KEY or requests is None:
        why = ("PATENTSVIEW_API_KEY is not set" if not API_KEY
               else "the requests library is unavailable")
        print(f"\n{why}.")
        print("\nThis is the single highest-yield upgrade available to Exit Watch.")
        print("The key is free and takes about two minutes:")
        print("  https://patentsview-support.atlassian.net/servicedesk/customer/portal/1")
        print("Then add it to repo secrets as PATENTSVIEW_API_KEY.")
        print("\nscripts/API_STATUS.md already lists it as a high-priority missing")
        print("secret for the patent pipeline, so it unblocks two things at once.")
        payload = {
            "status": "api_unavailable",
            "message": why,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "people": {},
        }
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nwrote status metadata to {OUT.relative_to(ROOT)} — Exit Watch will")
        print("carry on with the curated roster and ignore this file.")
        return 0

    session = requests.Session()
    people: dict[str, dict] = {}

    for mafia, assignees in PARENTS.items():
        got = 0
        for assignee in assignees:
            patents = query_assignee(session, assignee, args.limit)
            got += len(patents)
            for p in patents:
                pid = p.get("patent_id")
                for inv in (p.get("inventors") or []):
                    first = inv.get("inventor_name_first") or ""
                    last = inv.get("inventor_name_last") or ""
                    k = person_key(first, last)
                    if not k:
                        continue
                    rec = people.setdefault(k, {
                        "name": f"{first} {last}".strip(),
                        "employers": [],
                        "evidence": [],
                        "patent_count": 0,
                    })
                    rec["patent_count"] += 1
                    if mafia not in rec["employers"]:
                        rec["employers"].append(mafia)
                    if pid and len(rec["evidence"]) < 3:
                        rec["evidence"].append(
                            f"named inventor on US patent {pid}, assigned to {assignee}")
            time.sleep(THROTTLE)
        print(f"  {mafia:14} {got:5} patents")

    # An inventor with a single patent at a giant company is weak evidence of
    # anything; someone with several is clearly a real employee.
    strong = {k: v for k, v in people.items() if v["patent_count"] >= 2}

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "PatentsView PatentSearch API v1 (search.patentsview.org)",
        "note": ("Each person is named as an inventor on at least two granted "
                 "patents assigned to the parent. That is a public legal record "
                 "of employment, with the patent number as its citation. It is "
                 "not an inference from a job title."),
        "caveat": ("SpaceX files very few patents by policy, so this source "
                   "under-represents the SpaceX mafia specifically."),
        "total_people": len(people),
        "people": strong,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\ninventors found:            {len(people)}")
    print(f"with 2+ patents (kept):     {len(strong)}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
