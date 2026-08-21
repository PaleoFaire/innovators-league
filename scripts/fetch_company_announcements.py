#!/usr/bin/env python3
"""
First-Party Funding Watcher
─────────────────────────────────────────────────────────────────────────
Polls each tracked company's OWN newsroom for funding announcements, and
compares what it finds against what data.js already records.

Why this exists
───────────────
On 2026-08-11 Neros announced a $250M Series C at $2.5B on its own X account.
Every existing channel missed it:

  • fetch_deals.py watches Crunchbase / TechCrunch / Business Wire / PR
    Newswire / GlobeNewswire. Neros issued no wire release, so there was
    nothing to catch.
  • Form D detection is blind — Neros has no EDGAR CIK, and only ~38% of
    tracked companies do.
  • The X/Twitter watcher does not include Neros.
  • fetch_website_changes.py uses Wayback snapshots, which lag by days and
    report only that "something changed", not what.

The structural gap: every source watched the PRESS, not the COMPANIES.
Frontier-tech companies increasingly announce on their own site first and
get picked up later, if at all. This script closes that gap.

How it works
────────────
For each company in scope:
  1. Try RSS/Atom at the usual paths (/feed, /rss.xml, /blog/feed, ...).
     A feed is cheap, dated and unambiguous, so it is always preferred.
  2. Fall back to scraping the newsroom pages (/news, /blog, /press, ...)
     for headline-ish text.
  3. Scan for funding language and extract round, amount and valuation.
  4. Compare against the company's current record in data.js. Only a round
     that looks NEW (later stage, or bigger than what is recorded) is
     promoted to the review queue.

Output
──────
  data/company_announcements_auto.json   every hit, with evidence
  data/company_announcements_auto.js     window global for the frontend
  data/funding_review_queue.json         NEW rounds awaiting human confirm

IMPORTANT: this script never writes to data.js. Auto-extracted funding data
is not reliable enough to publish unreviewed — the same run of fetch_deals.py
that correctly found Valar's $1B round also produced "Synthesis: $63M Series O"
and three contradictory rows for one company. Detections land in a review
queue; a human promotes them.

Usage
─────
  python3 scripts/fetch_company_announcements.py                # IL30 (default)
  python3 scripts/fetch_company_announcements.py --scope all
  python3 scripts/fetch_company_announcements.py --company Neros
  python3 scripts/fetch_company_announcements.py --limit 50

Cadence: daily.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"
JSON_OUT = DATA_DIR / "company_announcements_auto.json"
JS_OUT = DATA_DIR / "company_announcements_auto.js"
QUEUE_OUT = DATA_DIR / "funding_review_queue.json"

USER_AGENT = "InnovatorsLeague-Bot/1.0 (+https://innovatorsleague.com; research)"
TIMEOUT = 12
POLITE_DELAY = 0.4

FEED_PATHS = [
    "/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/index.xml",
    "/blog/feed", "/blog/rss.xml", "/news/feed", "/news/rss.xml",
]
PAGE_PATHS = [
    "/news", "/blog", "/press", "/newsroom", "/updates", "/company/news",
    "/about/news", "/media", "/posts", "/announcements",
]

# Round labels, longest-first so "pre-seed" wins over "seed".
ROUND_RE = re.compile(
    r"\b(pre-?seed|seed(?:\s+extension)?|series\s+[a-k](?:-\d)?|"
    r"bridge|growth|pre-?ipo|ipo|spac)\b",
    re.I,
)
# $250M / $2.5 billion / $250 million
AMOUNT_RE = re.compile(
    r"\$\s?(\d{1,4}(?:[.,]\d{1,3})?)\s*(billion|million|bn|mm|[bm])\b", re.I
)
VALUATION_CUE = re.compile(
    r"(post[- ]money|pre[- ]money|valuation|valued at|valuing)", re.I
)
FUNDING_CUE = re.compile(
    r"\b(rais(?:e|ed|ing)|funding|financing|clos(?:e|ed|ing)|secur(?:e|ed)|"
    r"led\s+by|co-?led\s+by|oversubscribed|round|investment|backed\s+by)\b",
    re.I,
)

STAGE_ORDER = [
    "pre-seed", "seed", "series a", "series b", "series c", "series d",
    "series e", "series f", "series g", "series h", "series i", "series j",
]


def log(msg: str) -> None:
    print(msg, flush=True)


# ── data.js ──────────────────────────────────────────────────────────────

def load_companies() -> tuple[list[dict], list[str]]:
    """Read COMPANIES and INNOVATORS_LEAGUE_30 out of data.js via node."""
    js = (
        'const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
        'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
        '+";globalThis.__o={c:COMPANIES.map(c=>({name:c.name,website:c.website,'
        'fundingStage:c.fundingStage,totalRaised:c.totalRaised,valuation:c.valuation,'
        'signal:c.signal})),'
        'i:INNOVATORS_LEAGUE_30};",s);'
        "console.log(JSON.stringify(s.__o));"
    )
    out = subprocess.run(
        ["node", "-e", js, str(DATA_JS)], capture_output=True, text=True, check=True
    ).stdout
    payload = json.loads(out)
    return payload["c"], payload["i"]


# ── amount / stage helpers ───────────────────────────────────────────────

def to_millions(num: str, unit: str) -> float:
    """'250','million' -> 250.0 ; '2.5','billion' -> 2500.0"""
    value = float(num.replace(",", ""))
    u = unit.lower()
    if u in ("billion", "bn", "b"):
        return value * 1000.0
    return value


def parse_raised_millions(raised: str | None) -> float:
    """'$121M' / '~$23.7M' / '$1.2B+' -> millions. 0 when unparseable."""
    if not raised:
        return 0.0
    m = AMOUNT_RE.search(raised.replace("~", ""))
    return to_millions(m.group(1), m.group(2)) if m else 0.0


def stage_rank(stage: str | None) -> int:
    if not stage:
        return -1
    s = stage.strip().lower()
    for i, known in enumerate(STAGE_ORDER):
        if s.startswith(known):
            return i
    return -1


def normalise_round(raw: str) -> str:
    r = " ".join(raw.split()).lower().replace("pre seed", "pre-seed")
    if r.startswith("series"):
        return "Series " + r.split()[-1].upper()
    return r.title()


# ── extraction ───────────────────────────────────────────────────────────

def extract_funding(text: str) -> dict | None:
    """Pull a funding claim out of a blob of announcement text.

    Requires a funding cue AND an amount, so a bare 'Series A' mention in an
    unrelated post does not fire. The valuation is only recorded when a
    valuation cue sits near the figure — otherwise a '$2.5B' anywhere in the
    text would be mistaken for the round size, which is exactly the bug that
    put '$188B' (Databricks' valuation) into FUNDING_TRACKER as a round.
    """
    if not FUNDING_CUE.search(text):
        return None

    amounts = list(AMOUNT_RE.finditer(text))
    if not amounts:
        return None

    round_m = ROUND_RE.search(text)
    round_label = normalise_round(round_m.group(1)) if round_m else ""

    # Decide, per figure, whether it is the round size or the valuation.
    #
    # A valuation cue only belongs to a figure when NO OTHER FIGURE sits
    # between them. Without that rule, "$250M at $2.5B post money valuation"
    # tags the $250M as the valuation, because "valuation" falls inside a
    # naive +60 char window — and the round size is then lost entirely.
    def is_valuation(idx: int, m: re.Match) -> bool:
        prev_end = amounts[idx - 1].end() if idx > 0 else max(0, m.start() - 40)
        before = text[max(prev_end, m.start() - 40): m.start()]
        next_start = amounts[idx + 1].start() if idx + 1 < len(amounts) else min(len(text), m.end() + 80)
        after = text[m.end(): min(next_start, m.end() + 80)]
        return bool(VALUATION_CUE.search(before) or VALUATION_CUE.search(after))

    amount_m = valuation_m = None
    for idx, m in enumerate(amounts):
        if is_valuation(idx, m):
            if valuation_m is None:
                valuation_m = m
        elif amount_m is None:
            amount_m = m
    # Everything looked like a valuation and nothing like a round: fall back to
    # the first figure so a single-number announcement is not dropped.
    if amount_m is None and valuation_m is None:
        amount_m = amounts[0]

    result = {"round": round_label}
    if amount_m:
        result["amount_m"] = to_millions(amount_m.group(1), amount_m.group(2))
        result["amount_text"] = amount_m.group(0).strip()
    if valuation_m:
        result["valuation_m"] = to_millions(valuation_m.group(1), valuation_m.group(2))
        result["valuation_text"] = valuation_m.group(0).strip()
    return result if "amount_m" in result or "valuation_m" in result else None


def fmt_millions(m: float) -> str:
    if m >= 1000:
        return "$" + f"{m / 1000:.2f}".rstrip("0").rstrip(".") + "B"
    return "$" + f"{m:.1f}".rstrip("0").rstrip(".") + "M"


# ── fetching ─────────────────────────────────────────────────────────────

def get(url: str) -> requests.Response | None:
    try:
        r = requests.get(
            url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        return r if r.status_code == 200 and r.content else None
    except requests.RequestException:
        return None


def strip_tags(html: str) -> str:
    html = re.sub(r"<(script|style|nav|footer)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = (html.replace("&amp;", "&").replace("&#8217;", "'").replace("&nbsp;", " ")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&8212;", "-"))
    return " ".join(html.split())


def try_feeds(base: str) -> list[dict]:
    """Return [{title, summary, date, link}] from the first feed that parses."""
    for path in FEED_PATHS:
        r = get(urljoin(base, path))
        if not r:
            continue
        body = r.text
        if "<rss" not in body[:2000].lower() and "<feed" not in body[:2000].lower():
            continue
        items = []
        chunks = re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", body, re.S | re.I)
        for chunk in chunks[:25]:
            def tag(name):
                m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", chunk, re.S | re.I)
                if not m:
                    return ""
                v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", m.group(1), flags=re.S)
                return strip_tags(v)
            link = tag("link")
            if not link:
                lm = re.search(r'<link[^>]*href="([^"]+)"', chunk, re.I)
                link = lm.group(1) if lm else ""
            items.append({
                "title": tag("title"),
                "summary": (tag("description") or tag("summary") or tag("content"))[:600],
                "date": (tag("pubDate") or tag("published") or tag("updated"))[:40],
                "link": link,
                "via": urljoin(base, path),
            })
        if items:
            return items
        time.sleep(POLITE_DELAY)
    return []


def try_pages(base: str) -> list[dict]:
    """Scrape newsroom pages when no feed exists."""
    out = []
    for path in PAGE_PATHS:
        url = urljoin(base, path)
        r = get(url)
        if not r:
            continue
        text = strip_tags(r.text)
        if len(text) < 200:
            continue
        out.append({"title": "", "summary": text[:4000], "date": "", "link": url, "via": url})
        if len(out) >= 2:
            break
        time.sleep(POLITE_DELAY)
    return out


# ── per-company check ────────────────────────────────────────────────────

def check_company(company: dict) -> dict:
    name, site = company["name"], (company.get("website") or "").strip()
    record = {
        "company": name, "website": site, "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_type": None, "hits": [], "error": None,
    }
    if not site:
        record["error"] = "no website"
        return record

    items = try_feeds(site)
    record["source_type"] = "feed" if items else None
    if not items:
        items = try_pages(site)
        record["source_type"] = "page" if items else "none"

    known_stage = stage_rank(company.get("fundingStage"))
    known_raised = parse_raised_millions(company.get("totalRaised"))

    for it in items:
        blob = f"{it['title']} {it['summary']}"
        found = extract_funding(blob)
        if not found:
            continue
        amt = found.get("amount_m", 0.0)
        new_rank = stage_rank(found.get("round"))

        # Is this actually news to us? Either a later stage than recorded, or
        # a single round bigger than everything we have on file.
        is_new = (new_rank > known_stage >= -1 and new_rank != -1) or (
            amt and known_raised and amt > known_raised
        )
        record["hits"].append({
            "title": it["title"][:200],
            "date": it["date"],
            "link": it["link"],
            "round": found.get("round", ""),
            "amount": fmt_millions(amt) if amt else "",
            "valuation": fmt_millions(found["valuation_m"]) if "valuation_m" in found else "",
            "known_stage": company.get("fundingStage", ""),
            "known_raised": company.get("totalRaised", ""),
            "looks_new": bool(is_new),
            "evidence": blob[:300],
        })
    return record


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["il30", "hot", "all"], default="hot")
    ap.add_argument("--company", help="check a single company by exact name")
    ap.add_argument("--limit", type=int, default=0, help="cap companies checked")
    args = ap.parse_args()

    companies, il30 = load_companies()
    by_name = {c["name"]: c for c in companies}

    if args.company:
        if args.company not in by_name:
            log(f"No company named {args.company!r} in data.js")
            return 1
        targets = [by_name[args.company]]
    elif args.scope == "il30":
        targets = [by_name[n] for n in il30 if n in by_name]
    elif args.scope == "hot":
        # IL30 plus every company the database itself marks as running hot —
        # signal:"hot" or a $1B+ valuation. Found the hard way: Generalist AI
        # ($2B, signal hot) shipped GEN-1.5 on 2026-08-19 and the watcher never
        # saw it, because a default that only reads the IL30 is blind to
        # exactly the companies most likely to make news. This tier stays
        # small enough for a daily sweep without watching all 1,181.
        def is_hot(c):
            if (c.get("signal") or "").lower() == "hot":
                return True
            v = str(c.get("valuation") or "")
            return "B" in v.upper() and v.strip().startswith("$")
        names = set(il30)
        targets = [by_name[n] for n in il30 if n in by_name]
        for c in companies:
            if c["name"] not in names and c.get("website") and is_hot(c):
                names.add(c["name"])
                targets.append(c)
    else:
        targets = [c for c in companies if c.get("website")]
    if args.limit:
        targets = targets[: args.limit]

    log(f"First-party funding watcher — {len(targets)} companies ({args.scope})")
    log("=" * 62)

    results, new_rounds = [], []
    for i, c in enumerate(targets, 1):
        rec = check_company(c)
        results.append(rec)
        flagged = [h for h in rec["hits"] if h["looks_new"]]
        new_rounds.extend({**h, "company": rec["company"], "website": rec["website"]} for h in flagged)
        mark = "!" if flagged else ("." if rec["hits"] else " ")
        log(f"  [{i:>3}/{len(targets)}] {mark} {rec['company']:<32} "
            f"{rec['source_type'] or '-':<5} hits={len(rec['hits'])}")
        time.sleep(POLITE_DELAY)

    generated = datetime.now(timezone.utc)
    payload = {
        "generated_at": generated.isoformat(),
        "scope": args.company or args.scope,
        "companies_checked": len(results),
        "with_feed": sum(1 for r in results if r["source_type"] == "feed"),
        "total_hits": sum(len(r["hits"]) for r in results),
        "new_rounds": len(new_rounds),
        "results": results,
    }
    DATA_DIR.mkdir(exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2))
    JS_OUT.write_text(
        f"// Last updated: {generated.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"window.COMPANY_ANNOUNCEMENTS_AUTO = {json.dumps(payload)};\n"
    )

    # Merge into the review queue, keyed so a repeat run does not re-add.
    queue = []
    if QUEUE_OUT.exists():
        try:
            queue = json.loads(QUEUE_OUT.read_text())
        except json.JSONDecodeError:
            queue = []
    seen = {f"{q.get('company')}|{q.get('round')}|{q.get('amount')}" for q in queue}
    added = 0
    for nr in new_rounds:
        key = f"{nr['company']}|{nr['round']}|{nr['amount']}"
        if key in seen:
            continue
        queue.append({**nr, "detected_at": generated.isoformat(), "status": "pending"})
        seen.add(key)
        added += 1
    QUEUE_OUT.write_text(json.dumps(queue, indent=2))

    log("=" * 62)
    log(f"  checked {len(results)} · feeds {payload['with_feed']} · "
        f"hits {payload['total_hits']} · new rounds {len(new_rounds)} · queued {added}")
    if new_rounds:
        log("\n  NEW ROUNDS FOR REVIEW (not written to data.js):")
        for nr in new_rounds:
            log(f"    {nr['company']}: {nr['round'] or '?'} {nr['amount']}"
                f"{' @ ' + nr['valuation'] if nr['valuation'] else ''}"
                f"   (recorded: {nr['known_stage']} / {nr['known_raised']})")
            log(f"      {nr['link'][:110]}")
    log(f"\n  wrote {JSON_OUT.name}, {JS_OUT.name}, {QUEUE_OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
