#!/usr/bin/env python3
"""
Trade-press funding watcher
─────────────────────────────────────────────────────────────────────────
High-signal defence and frontier-tech funding announcements, from outlets that
cover nothing else.

Why a separate fetcher
──────────────────────
fetch_deals.py already reads seven RSS feeds — Crunchbase, TechCrunch,
Business Wire, PR Newswire, VentureBeat. They are broad-spectrum: a fintech
Series B and a defence-autonomy Series A arrive through the same pipe, and the
generic parser has to guess which is which. Stephen's note on Axios is exactly
this — good coverage, too much noise, because it is not only frontier tech.

Trade press is the opposite trade-off. Tectonic Defense publishes an
investment-only category feed where essentially every item is a round in a
company we would want. Volume is low; hit rate is near total. That justifies a
parser built for the way these outlets actually write headlines, which is far
more regular than a general wire:

  "Smack Raises $61M for AI at the Edge"
  "Heaviside Raises $60M at a $600M Valuation"
  "Exclusive: Nigeria's Terra Industries Closes $52M Seed Round, Expands to London"
  "Neros Plans Production Scale and New Products After $250M Raise"
  "Aevex Expands Into Maritime Autonomy with $650M Acquisition of BlackSea"

Company, amount, round and valuation all sit in fixed positions relative to the
verb. Parsing the title is therefore high precision — and precision is the
whole point, because on 2026-08-19 the generic body-text parser was found to
have produced 139 fabricated rounds by lifting market sizes out of article
copy. Nothing here is read from body text. If the headline does not say it, we
do not record it.

Two outputs, because these items split two ways
───────────────────────────────────────────────
  MATCHED    the company is already in data.js -> a funding event, which flows
             into the deal feed and the Action Brief
  DISCOVERY  the company is not -> a candidate for the database. This is half
             the value: "Riven Emerges from Stealth" and "Heaviside Raises
             $60M" are exactly the companies a frontier-tech database should
             hear about the week they surface, not a year later.

Output
──────
  data/trade_press_auto.json     every parsed item, matched and unmatched
  data/trade_press_status.json   run status
  appends matched rounds to data/deals_auto.json (deduped)

Usage
─────
  python3 scripts/fetch_trade_press.py --dry
  python3 scripts/fetch_trade_press.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "trade_press_auto.json"
STATUS = DATA / "trade_press_status.json"
DEALS = DATA / "deals_auto.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# Outlets that cover frontier/defence tech and nothing else. Add siblings here;
# the parser is generic across them because trade-press headline grammar is.
SOURCES = [
    ("Tectonic Defense", "https://www.tectonicdefense.com/category/investment/feed/",
     "defense"),
]

# Editorial prefixes that sit in front of the company name.
PREFIX = re.compile(r"^\s*(exclusive|icymi|scoop|breaking|just in|report|update|deal)\s*[:\-–]\s*",
                    re.I)
# "Nigeria's Terra Industries" -> "Terra Industries". A leading proper noun in
# the possessive is a place or a parent, never the company being funded.
POSSESSIVE = re.compile(r"^[A-Z][\w.&-]*(?:\s+[A-Z][\w.&-]*)?['’]s\s+")

RAISE_VERB = (r"raises?|raised|closes?|closed|lands?|landed|secures?|secured|"
              r"nabs?|nabbed|banks?|banked|scores?|pulls? in|picks? up|announces?")

MONEY = r"\$\s?(\d+(?:\.\d+)?)\s*([BMK])\b"


def to_usd(num: str, unit: str) -> float:
    return float(num) * {"B": 1e9, "M": 1e6, "K": 1e3}[unit.upper()]


def fmt(v: float) -> str:
    if v >= 1e9:
        s = f"${v/1e9:.2f}B"
        return s.replace(".00B", "B").replace("0B", "B") if s.endswith("0B") else s
    if v >= 1e6:
        return f"${v/1e6:g}M"
    return f"${v/1e3:g}K"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# An acquisition headline often names what was bought rather than who: "Archer
# Acquires Three Boeing Autonomous Flight Subsidiaries" describes assets, not a
# company we could ever add to the database. Recording it as a discovery
# candidate would put a phrase in the queue for a human to puzzle over.
NOT_A_COMPANY = re.compile(
    r"^(?:the\s+)?(?:two|three|four|five|several|certain|its|their)\b"
    r"|\b(?:subsidiaries|subsidiary|assets|business unit|division|portfolio|"
    r"stake|majority|remaining)\b", re.I)


def clean_company(s: str) -> str:
    s = PREFIX.sub("", s or "").strip()
    s = POSSESSIVE.sub("", s).strip()
    # trailing connective words the headline used to reach the verb
    s = re.sub(r"\s+(?:has|have|just|now|finally|officially|reportedly)$", "", s, flags=re.I)
    return s.strip(" ,–—-")


def parse_title(title: str) -> dict | None:
    """Structured fields out of a trade-press headline. None if it is not a deal.

    Deliberately conservative: only the headline is read, never the body. A
    headline that does not state an amount still yields a company and a kind,
    which is enough for discovery, but never a fabricated figure.
    """
    t = re.sub(r"\s+", " ", (title or "")).strip()
    if not t:
        return None
    body = PREFIX.sub("", t)

    # ── acquisition ──────────────────────────────────────────────────────
    # Named groups throughout: MONEY carries two capture groups of its own, so
    # positional indices shift the moment it is embedded in a larger pattern —
    # which is what silently dropped "…with $650M Acquisition of BlackSea".
    m2 = re.search(r"^(?P<acq>.*?)\s+.*?\$\s?(?P<n>\d+(?:\.\d+)?)\s*(?P<u>[BMK])\b"
                   r"\s+acquisition of\s+(?P<tgt>.+?)$", body, re.I)
    m = re.search(r"^(?P<acq>.*?)\s+(?:acquires|acquired|buys|bought|to acquire)\s+"
                  r"(?P<tgt>.+?)$", body, re.I)
    if m2 or m:
        if m2:
            acquirer, target = m2.group("acq"), m2.group("tgt")
            val = to_usd(m2.group("n"), m2.group("u"))
        else:
            acquirer, target, val = m.group("acq"), m.group("tgt"), 0.0
            mm = re.search(MONEY, body, re.I)
            if mm:
                val = to_usd(mm.group(1), mm.group(2))
        tgt = clean_company(target)
        if NOT_A_COMPANY.search(tgt):
            return None
        return {"kind": "acquisition", "company": tgt,
                "counterparty": clean_company(acquirer), "amount_usd": val,
                "round": "Acquisition", "valuation_usd": 0.0}

    # ── stealth emergence (no amount required) ───────────────────────────
    m = re.search(r"^(?P<co>.*?)\s+(?:emerges?|emerged|launches?|launched|comes?|came)\s+"
                  r"(?:out\s+)?(?:from|of)\s+stealth(?P<tail>.*)$", body, re.I)
    if m:
        # "Atlas Motion Emerges from Stealth with $11.5M in Funding" — the
        # figure is the point of the story, so take it when the headline gives
        # one rather than recording a bare emergence.
        amt = 0.0
        am = re.search(MONEY, m.group("tail"), re.I)
        if am:
            amt = to_usd(am.group(1), am.group(2))
        return {"kind": "stealth", "company": clean_company(m.group("co")),
                "amount_usd": amt, "round": "Seed" if amt else "",
                "valuation_usd": 0.0}

    # ── funding round ────────────────────────────────────────────────────
    # Company sits before the verb; the amount is the first figure after it.
    # The trailing "After $250M Raise" shape is tried FIRST. Otherwise the
    # general verb pattern matches the word "Raise" at the very end of
    # "Neros Plans Production Scale and New Products After $250M Raise", the
    # lazy prefix swallows the entire headline, and the tail left to search for
    # an amount is empty — so a real $250M round parsed as nothing.
    m = re.search(r"^(?P<co>.*?)\s+.*?\bafter\s+(?:a\s+|an\s+|its\s+)?"
                  r"(?P<amt>\$\s?\d+(?:\.\d+)?\s*[BMK]\b.*)$", body, re.I)
    if m:
        company, tail = m.group("co"), m.group("amt")
    else:
        m = re.search(r"^(.*?)\s+(?:" + RAISE_VERB + r")\b(.*)$", body, re.I)
        if not m:
            return None
        company, tail = m.group(1), m.group(2)

    amounts = [(to_usd(a, b), mm.start())
               for mm in re.finditer(MONEY, tail, re.I)
               for a, b in [(mm.group(1), mm.group(2))]]
    if not amounts:
        return None

    # Valuation is whichever figure the headline attaches to the word.
    val = 0.0
    vm = re.search(r"(?:at|to)\s+(?:a|an)?\s*" + MONEY + r"[^.]{0,24}valuation", tail, re.I)
    if not vm:
        vm = re.search(r"valuation[^.]{0,18}?" + MONEY, tail, re.I)
    if vm:
        val = to_usd(vm.group(1), vm.group(2))

    raise_amt = next((a for a, _ in amounts if a != val), amounts[0][0])

    rnd = ""
    rm = re.search(r"\b(pre-seed|seed|series\s+[a-j])\b", tail, re.I)
    if rm:
        rnd = rm.group(1).title().replace("Series ", "Series ")
        rnd = re.sub(r"series\s+([a-j])", lambda x: "Series " + x.group(1).upper(), rnd, flags=re.I)

    return {"kind": "funding", "company": clean_company(company),
            "amount_usd": raise_amt, "round": rnd or "Funding Round",
            "valuation_usd": val}


def known_companies() -> dict:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.map(c=>c.name);",s);'
          'console.log(JSON.stringify(s.__n));')
    try:
        out = subprocess.run(["node", "-e", js, str(ROOT / "data.js")],
                             capture_output=True, text=True, check=True).stdout
        return {norm(n): n for n in json.loads(out)}
    except Exception as e:
        print(f"  could not read data.js: {e}")
        return {}


def fetch(url: str) -> list:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return []
        x = r.text
    except requests.RequestException as e:
        print(f"  fetch failed: {type(e).__name__}")
        return []

    def tag(block, t):
        m = re.search(rf"<{t}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{t}>", block, re.S)
        if not m:
            return ""
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()

    items = []
    for b in re.findall(r"<item>(.*?)</item>", x, re.S):
        pub = tag(b, "pubDate")
        try:
            d = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
        except Exception:
            d = ""
        items.append({"title": tag(b, "title"), "url": tag(b, "link"), "date": d,
                      "summary": tag(b, "description")[:280]})
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    print("=" * 68)
    print("Trade-press funding watcher")
    print("=" * 68)

    known = known_companies()
    print(f"tracking {len(known)} companies\n")

    parsed, matched, discovery = [], [], []
    for name, url, beat in SOURCES:
        items = fetch(url)
        print(f"  {name}: {len(items)} items")
        for it in items:
            p = parse_title(it["title"])
            if not p:
                continue
            rec = {**p, **{"title": it["title"], "url": it["url"], "date": it["date"],
                           "source": name, "beat": beat}}
            rec["amount"] = fmt(rec["amount_usd"]) if rec["amount_usd"] else ""
            rec["valuation"] = fmt(rec["valuation_usd"]) if rec["valuation_usd"] else ""
            key = norm(rec["company"])
            if key in known:
                rec["matched_to"] = known[key]
                matched.append(rec)
            else:
                rec["matched_to"] = None
                discovery.append(rec)
            parsed.append(rec)

    print(f"\n  parsed {len(parsed)}   matched {len(matched)}   new to us {len(discovery)}\n")
    for r in matched:
        print(f"    [KNOWN]     {r['matched_to'][:26]:<28}{r['amount'] or '—':<9}"
              f"{r['round'][:14]:<16}{r['date']}")
    for r in discovery:
        print(f"    [DISCOVERY] {r['company'][:26]:<28}{r['amount'] or '—':<9}"
              f"{r['round'][:14]:<16}{r['date']}")

    if args.dry:
        print("\nDRY RUN — nothing written")
        return 0

    stamp = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps({"generated_at": stamp, "sources": [s[0] for s in SOURCES],
                               "matched": len(matched), "discovery": len(discovery),
                               "items": parsed}, indent=2))
    STATUS.write_text(json.dumps({"script": "fetch_trade_press.py", "finished_at": stamp,
                                  "ok": True, "parsed": len(parsed),
                                  "matched": len(matched), "discovery": len(discovery)}, indent=2))
    print(f"\nwrote {OUT.name}")

    # Append matched rounds to the deal feed, deduped. Only funding — an
    # acquisition is not a round, and a stealth emergence has no figure.
    try:
        deals = json.loads(DEALS.read_text())
    except Exception:
        deals = []
    have = {(norm(d.get("company", "")), d.get("amount", ""), str(d.get("date", ""))[:7])
            for d in deals}
    added = 0
    for r in matched:
        if r["kind"] != "funding" or not r["amount"]:
            continue
        k = (norm(r["matched_to"]), r["amount"], r["date"][:7])
        if k in have:
            continue
        deals.append({"company": r["matched_to"], "investor": "Undisclosed",
                      "amount": r["amount"], "round": r["round"],
                      "date": r["date"][:7], "valuation": r["valuation"],
                      "leadOrParticipant": "lead", "source": r["source"],
                      "sourceUrl": r["url"]})
        have.add(k)
        added += 1
    if added:
        deals.sort(key=lambda d: str(d.get("date", "")), reverse=True)
        DEALS.write_text(json.dumps(deals, indent=2))
        print(f"appended {added} rounds to {DEALS.name} ({len(deals)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
