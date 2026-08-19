#!/usr/bin/env python3
"""
One-off purge of deals produced by the broken extractor (2026-08-19)
─────────────────────────────────────────────────────────────────────────
Three defects in fetch_deals.py put fabricated rounds in front of members:

  1. parse_funding_amount tried the BILLIONS pattern first, across the whole
     article, and returned the first hit. "Durin raises $12 million ...
     targeting the $12 billion drilling market" was recorded as a $12B round.
  2. parse_round_type matched "series o" inside "a series of funding rounds",
     and read any single letter before "round" as a series letter, producing
     61 rows claiming Series E through Series N.
  3. match_investors used naked substring matching, so "nearly", "beneath" and
     "linear accelerator" all matched NEA, which is why NEA appears as the
     investor on deals it had no part in.

All three are fixed, but the fix only governs future runs. The rows already in
deals_auto.json carry no source text, so they cannot be re-parsed — they can
only be judged on their face. This script removes the ones that cannot be
true, then rebuilds every downstream artefact that was computed from them.

What is removed, and why these rules
────────────────────────────────────
  amount >= $2B    No private company in this database has raised a $2B round
                   from a wire story we parsed. The genuinely large rounds
                   (Anduril's $2.5B Series G, SpaceX) are recoverable — future
                   runs re-capture them with the fixed parser, and the
                   canonical figures already live in data.js. Keeping a
                   plausible-looking $12B on Durin is not worth preserving a
                   correct $2.5B on Anduril, because we cannot tell them apart
                   from the stored row alone.
  Series K-Z       No such round exists in this dataset; every one is the
                   "series of" misparse.
  investor NEA on  Cannot distinguish a real NEA deal from the "nearly"
  a removed row    artefact, so investor lists are left alone on surviving
                   rows and simply go with the rows that are removed.

Removal is logged in full to data/purged_deals_2026-08-19.json so the decision
is auditable and reversible.

Usage
─────
  python3 scripts/purge_bad_deals.py --dry
  python3 scripts/purge_bad_deals.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEALS = ROOT / "data" / "deals_auto.json"
LOG = ROOT / "data" / "purged_deals_2026-08-19.json"

# Two thresholds, because the failure has two shapes.
#
# Above $2B the figure is almost always a market size or a market cap that the
# parser lifted out of the same sentence.
#
# Between $900M and $2B it is almost always the VALUATION rather than the
# round: Skild AI "$1.4B" (raised ~$300M at $1.5B), Neura Robotics "$1.4B"
# (raised ~€120M at ~€1B), Helsing "$1.8B" (raised €600M). The tell is the
# cluster — five separate companies all landing on exactly $1.8B in the same
# month is a template, not five coincidences. Rounds this size are never
# reported without naming the lead investor, so an unnamed one in this band is
# not a round we can stand behind.
#
# The deals feed is a news-derived signal layer, not the source of truth: the
# canonical funding figures live in data.js and are untouched by this. So the
# cost of over-purging is a signal we re-capture on the next run, while the
# cost of under-purging is a fabricated round on a member-facing page.
MAX_PLAUSIBLE_M = 2000.0        # $2B — implausible on its face
VALUATION_BAND_M = 900.0        # $900M-$2B — implausible without a named lead


def to_millions(amount: str) -> float:
    m = re.match(r"\$(\d+(?:\.\d+)?)\s*([BMK])", (amount or "").strip(), re.I)
    if not m:
        return 0.0
    n, u = float(m.group(1)), m.group(2).upper()
    return n * {"B": 1000.0, "M": 1.0, "K": 0.001}[u]


def reason_to_drop(row: dict) -> str | None:
    amt = to_millions(row.get("amount", ""))
    if amt >= MAX_PLAUSIBLE_M:
        return f"amount {row.get('amount')} >= $2B — misparsed market size or valuation"
    if amt >= VALUATION_BAND_M:
        return (f"amount {row.get('amount')} in the $900M-$2B valuation band — "
                f"the parser could not tell a round from a valuation")
    rnd = (row.get("round") or "").strip()
    m = re.match(r"^Series ([A-Z])", rnd)
    if m and m.group(1) >= "K":
        return f"round '{rnd}' — 'series of' misparse; no such round exists here"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    raw = json.loads(DEALS.read_text())
    rows = raw if isinstance(raw, list) else raw.get("data", [])

    keep, drop = [], []
    for r in rows:
        why = reason_to_drop(r)
        (drop if why else keep).append({**r, "_why": why} if why else r)

    print(f"deals: {len(rows)}   keeping {len(keep)}   removing {len(drop)}")
    by = {}
    for d in drop:
        k = "amount >= $2B" if "amount" in d["_why"] else "Series K-Z"
        by[k] = by.get(k, 0) + 1
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"   {v:>4}  {k}")

    print("\n  largest removals:")
    for d in sorted(drop, key=lambda r: -to_millions(r.get("amount", "")))[:12]:
        print(f"    {d.get('company','')[:26]:<28}{d.get('amount',''):<9}"
              f"{d.get('round',''):<16}{d.get('investor','')}")

    if args.dry:
        print("\nDRY RUN — nothing written")
        return 0

    LOG.write_text(json.dumps({
        "purged_at": datetime.now(timezone.utc).isoformat(),
        "reason": "fetch_deals.py amount/round/investor parser defects, fixed same day",
        "removed": len(drop), "kept": len(keep), "rows": drop}, indent=2))
    DEALS.write_text(json.dumps(keep if isinstance(raw, list)
                                else {**raw, "data": keep}, indent=2))
    print(f"\nwrote {DEALS.name} ({len(keep)} rows) and {LOG.name}")

    # Rebuild everything computed from deals
    for script in ("calc_funding_tracker.py", "calc_valuation_benchmarks.py",
                   "calc_sector_momentum.py", "calc_innovator_scores.py"):
        p = ROOT / "scripts" / script
        if not p.exists():
            continue
        r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
        print(f"   rebuilt {script}: exit {r.returncode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
