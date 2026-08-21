#!/usr/bin/env python3
"""
The Wire + Pre-Announcement Radar — member-facing data builder
─────────────────────────────────────────────────────────────────────────
Generates data/wire_auto.js: the two payloads behind the site's pulse layer.

Why this exists
───────────────
The 2026-08-20 member-site audit landed on one sentence: the database is a
snapshot, and people pay for a pulse. A member who logs in twice sees the
identical company grid twice; meanwhile the pipeline catches rounds, federal
awards and regulatory milestones every night that no member-facing surface
shows. This script closes that gap with two products:

  WIRE   a chronological "what changed" feed across every company we track —
         rounds, Form Ds, contract wins, regulatory milestones, exec moves —
         each joined against what the database already knows ("$120M Form D,
         against the $105M round on record").

  RADAR  the flagship: every SEC Form D matched to a tracked company, with
         subscription progress and a last-round comparison. A Form D hits
         EDGAR when a round closes, weeks before the press release — this
         week it caught Antares, Dexterity, Pixxel and Windborne pre-press.

Relationship to build_action_brief.py
─────────────────────────────────────
Same collectors, same joins, imported directly — one engine, two renderings.
The difference is deliberate and must stay: the Action Brief is Stephen's
private morning briefing and weights events by HIS relationships (portfolio,
visited, covered) from data/relationships.json. The Wire is member-facing, so
none of that may leak here: no tiers, no "you visited them", no beats. Events
rank on public merits only — kind, size, recency.

Output
──────
  data/wire_auto.js    const WIRE = {...}; const RADAR = {...};

Usage
─────
  python3 scripts/build_wire.py            # 30-day window
  python3 scripts/build_wire.py --days 45
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_action_brief import (  # noqa: E402  (one engine, two renderings)
    collect, companies_from_data_js, fmt_money, load, load_tracker, money,
    months_between, norm, rows,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wire_auto.js"

# Member-facing kinds only. Podcast chatter and GitHub stars stay out — the
# Wire's promise is "something happened", not "something was mentioned".
KIND_META = {
    "form_d":     {"label": "FORM D",     "weight": 45},
    "funding":    {"label": "ROUND",      "weight": 40},
    "contract":   {"label": "CONTRACT",   "weight": 36},
    "regulatory": {"label": "REGULATORY", "weight": 30},
    "grant":      {"label": "GRANT",      "weight": 24},
    "exec":       {"label": "PEOPLE",     "weight": 20},
    "launch":     {"label": "LAUNCH",     "weight": 20},
    "announcement": {"label": "COMPANY NEWS", "weight": 14},
    "patent":     {"label": "PATENTS",    "weight": 12},
}


def wire_score(e: dict) -> float:
    s = float(KIND_META[e["kind"]]["weight"])
    if e["value"] > 0:
        s += min(30.0, 5.0 * math.log10(max(e["value"], 1e5) / 1e5))
    try:
        age = (datetime.now(timezone.utc).date()
               - datetime.strptime(e["date"], "%Y-%m-%d").date()).days
        s -= min(25, max(0, age) * 0.9)
    except ValueError:
        pass
    return round(s, 1)


def context_for(e: dict, db_rec: dict, tracker: dict) -> str:
    """The join that turns a fact into an insight — same rule as the brief:
    every slot is a database field, nothing is generated.

    Funding context ONLY on funding events. "Series C · $140M raised to date"
    under an NRC milestone made readers unable to tell whether the news was
    the milestone or a raise. On anything that is not a round, the line is
    company + what happened, nothing else.
    """
    if e["kind"] not in ("form_d", "funding"):
        return ""
    tr = tracker.get(norm(e["company"])) or {}
    if e["value"] > 0 and tr.get("amount"):
        gap = months_between(tr.get("date", ""), e["date"])
        ratio = e["value"] / tr["amount"] if tr["amount"] else 0
        line = f"{fmt_money(tr['amount'])} {tr.get('round') or 'round'} on record"
        if gap is not None and 0 < gap < 60:
            line += f" {gap} mo ago"
        if ratio > 0 and abs(ratio - 1) > 0.15:
            line += f" — this is {ratio:.1f}× that"
        return line
    stage = db_rec.get("stage") or ""
    raised = db_rec.get("raised") or ""
    if stage or raised:
        return " · ".join(x for x in (stage, f"{raised} raised to date" if raised else "") if x)
    return ""


def build_wire(days: int, db: dict, tracker: dict) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = collect(cutoff)

    seen, events = set(), []
    for e in raw:
        if e["kind"] not in KIND_META:
            continue
        # The Wire reports what HAPPENED. The launch manifest carries scheduled
        # future launches (some with Dec-31 placeholder dates), which sorted to
        # the top of a reverse-chronological feed and made day one read
        # "Thursday, December 31". Future events belong on the calendar page.
        if not e["date"] or e["date"] > today:
            continue
        n = norm(e["company"])
        if n not in db["by_norm"]:
            continue
        # in-batch dedupe: the two Form D files overlap by design
        key = (e["kind"], n, e["date"], e["headline"][:50])
        if key in seen:
            continue
        seen.add(key)
        rec = db["by_norm"][n]
        events.append({
            "kind": e["kind"],
            "label": KIND_META[e["kind"]]["label"],
            "company": rec["name"],          # canonical casing from data.js
            "sector": rec.get("sector") or "",
            "headline": e["headline"],
            "detail": e["detail"],
            "context": context_for(e, rec, tracker),
            "date": e["date"],
            "url": e["url"],
            "value": e["value"],
            "source": e["source"],
            "score": wire_score(e),
        })

    events.sort(key=lambda x: (x["date"], x["score"]), reverse=True)

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week = [e for e in events if e["date"] >= week_ago]
    capital_week = sum(e["value"] for e in this_week
                       if e["kind"] in ("form_d", "funding", "contract", "grant"))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "stats": {
            "events": len(events),
            "events_this_week": len(this_week),
            "capital_this_week": capital_week,
            "capital_this_week_fmt": fmt_money(capital_week) if capital_week else "$0",
            "companies_moved": len({e["company"] for e in events}),
        },
        # Top of the feed by score, for the landing-page strip.
        "top": sorted(events, key=lambda x: -x["score"])[:6],
        "events": events[:200],
    }


def build_radar(db: dict, tracker: dict) -> dict:
    payload = load("form_d_filings") or {}
    filings = rows(payload, "filings")

    out = []
    seen_acc = set()
    for f in filings:
        acc = f.get("accession") or ""
        if acc and acc in seen_acc:
            continue
        seen_acc.add(acc)
        n = norm(f.get("company", ""))
        rec = db["by_norm"].get(n)
        if not rec:
            continue

        offering = money(f.get("offering_amount"))
        sold = money(f.get("amount_sold"))
        pct = round(100 * sold / offering) if offering and sold else None
        fully = bool(offering and sold and sold >= offering * 0.99)

        tr = tracker.get(n) or {}
        vs_last = ""
        if tr.get("amount") and offering:
            gap = months_between(tr.get("date", ""), f.get("filed_date", ""))
            ratio = offering / tr["amount"]
            vs_last = f"{fmt_money(tr['amount'])} {tr.get('round') or 'round'} on record"
            if gap is not None and 0 < gap < 60:
                vs_last += f" {gap} mo ago"
            if ratio > 0 and abs(ratio - 1) > 0.15:
                vs_last += f" — this filing is {ratio:.1f}× that"

        out.append({
            "company": rec["name"],
            "sector": rec.get("sector") or "",
            "filed_date": f.get("filed_date", ""),
            "form": f.get("form", "D"),
            "offering": offering,
            "offering_fmt": fmt_money(offering) if offering else "",
            "sold": sold,
            "sold_fmt": fmt_money(sold) if sold else "",
            "pct_subscribed": pct,
            "fully_subscribed": fully,
            "vs_last_round": vs_last,
            "securities_type": f.get("securities_type", ""),
            "is_safe": bool(f.get("is_safe")),
            "exemption": f.get("exemption", ""),
            "filing_url": f.get("filing_url", ""),
            "match_method": f.get("match_method", ""),
        })

    out.sort(key=lambda r: r["filed_date"], reverse=True)
    d30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    last30 = [r for r in out if r["filed_date"] >= d30]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "filings_30d": len(last30),
            "offered_30d": sum(r["offering"] for r in last30),
            "offered_30d_fmt": fmt_money(sum(r["offering"] for r in last30)) or "$0",
            "fully_subscribed_30d": sum(1 for r in last30 if r["fully_subscribed"]),
            "total_tracked": len(out),
        },
        "filings": out[:120],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    db = companies_from_data_js()
    tracker = load_tracker()
    print(f"companies: {len(db['by_norm'])}   tracker rows: {len(tracker)}")

    wire = build_wire(args.days, db, tracker)
    radar = build_radar(db, tracker)
    print(f"WIRE: {wire['stats']['events']} events "
          f"({wire['stats']['events_this_week']} this week, "
          f"{wire['stats']['capital_this_week_fmt']} moved)")
    print(f"RADAR: {radar['stats']['total_tracked']} filings tracked, "
          f"{radar['stats']['filings_30d']} in 30d, "
          f"{radar['stats']['fully_subscribed_30d']} fully subscribed")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    OUT.write_text(
        "// Auto-generated by scripts/build_wire.py — member-facing pulse data\n"
        "// The Wire: chronological change feed. The Radar: Form D pre-announcement tracker.\n"
        "// Deliberately relationship-free: see the header of build_wire.py.\n"
        f"// Last updated: {stamp} UTC\n"
        f"const WIRE = {json.dumps(wire, indent=1, ensure_ascii=False)};\n\n"
        f"const RADAR = {json.dumps(radar, indent=1, ensure_ascii=False)};\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
