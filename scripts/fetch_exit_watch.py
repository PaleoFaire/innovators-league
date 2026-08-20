#!/usr/bin/env python3
"""
Exit Watch — pre-company formation detector
─────────────────────────────────────────────────────────────────────────
Every other pipeline in this repo points INWARD: what is happening at the
companies we already track. Exit Watch points outward and asks the opposite
question — which company is about to exist that is not in COMPANIES yet?

The insight is that you cannot reliably detect the departure. LinkedIn has
no lawful API and scraping it is both brittle and against their terms. So we
do not try. We detect the FORMATION, which announces itself in public
records, and then backfill the pedigree from documented sources.

Backbone: SEC Form D. Every US private raise over $5,000 files one within
15 days of first sale, and it is filed BEFORE any press release. The XML
gives us, for free and officially:

    entityName          the new company
    industryGroupType   lets us drop pooled funds, real estate, banking
    yearOfInc           a 2026 incorporation filing its first Form D is
                        precisely the signal we want
    totalAmountSold     capital actually raised
    dateOfFirstSale     when the money moved
    relatedPersonInfo   the officers, BY NAME

A newly incorporated technology or manufacturing entity, raising real money,
whose officers have a documented frontier-tech pedigree, is a company worth
knowing about roughly 6-18 months before anyone writes it up.

This script does ingestion and filtering only. Pedigree matching and scoring
live in build_exit_watch.py, so that the expensive network sweep and the
cheap re-scoring can run on different cadences.

Output: data/exit_watch_raw.json

Usage:
    python scripts/fetch_exit_watch.py --days 30
    python scripts/fetch_exit_watch.py --days 7 --dry
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
OUT = DATA / "exit_watch_raw.json"
CACHE = DATA / ".exit_watch_cache.json"

# SEC requires a descriptive UA with a contact address; unidentified traffic
# gets blocked at the edge. Published limit is 10 req/sec — we stay well under.
HEADERS = {
    "User-Agent": "Rational Optimist Society stephen@rationaloptimistsociety.com",
    "Accept-Encoding": "gzip, deflate",
}
THROTTLE = 0.15

# Form D's own industry taxonomy. We keep the groups where a frontier-tech
# company would classify itself and drop the rest. This is the single highest
# yield filter available — roughly two thirds of all Form D volume is funds
# and real estate, and dropping it costs us nothing.
KEEP_INDUSTRY = {
    "Computers", "Technology", "Telecommunications", "Other Technology",
    "Biotechnology", "Pharmaceuticals", "Health Care", "Other Health Care",
    "Manufacturing", "Industrial", "Construction",
    "Energy", "Coal Mining", "Electric Utilities", "Other Energy",
    "Oil and Gas", "Environmental Services", "Utilities",
    "Aerospace", "Airlines and Airports", "Transportation",
    "Chemicals", "Materials", "Mining", "Metals",
    "Agriculture", "Food and Beverage",
    "Business Services", "Other",
}
DROP_INDUSTRY = {
    "Pooled Investment Fund", "Real Estate", "REITS and Finance",
    "Commercial Banking", "Investment Banking", "Insurance",
    "Residential", "Commercial", "Other Real Estate",
    "Restaurants", "Retailing", "Travel", "Hotels and Motels",
}

# Filer names that are structurally investment vehicles rather than operating
# companies. Form D's industry field usually catches these, but not always —
# a fund occasionally self-classifies as "Other".
SPV_MARKER = re.compile(
    r"\b(fund|fund\s+[ivx\d]+|partners|capital|ventures?|syndicate|spv|"
    r"series\s+[a-z0-9]+|investors?|opportunit(?:y|ies)|acquisition\s+corp|"
    r"realty|properties|estates?|reit)\b", re.I)

LEGAL_SUFFIX = re.compile(
    r"\b(inc|incorporated|llc|l\.?l\.?c|corp|corporation|co|company|ltd|limited|"
    r"lp|l\.?p|llp|plc|holdings?|group|technologies|technology|labs?|"
    r"industries|systems|international|worldwide|usa|us|the)\b", re.I)


# ─────────────────────────────── helpers ────────────────────────────────

def stem(s: str) -> str:
    """Normalised company token with legal suffixes stripped, applied
    repeatedly because filers stack them."""
    v = re.sub(r"[^a-z0-9\s.]", " ", (s or "").lower())
    for _ in range(4):
        w = LEGAL_SUFFIX.sub(" ", v)
        w = re.sub(r"\s+", " ", w).strip()
        if w and w != v:
            v = w
        else:
            break
    return re.sub(r"[^a-z0-9]", "", v)


def person_key(name: str) -> str:
    """First+last only, so 'Palmer Luckey' == 'Palmer F. Luckey'."""
    parts = [p for p in re.split(r"[^A-Za-z]+", name or "") if len(p) > 1]
    if len(parts) < 2:
        return ""
    return (parts[0] + parts[-1]).lower()


def get(url: str, tries: int = 3) -> str | None:
    """Fetch with retry. A miss here is invisible; a ban is not."""
    for attempt in range(tries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace")
        except HTTPError as e:
            if e.code in (403, 429):
                time.sleep(2 ** attempt)
                continue
            if e.code == 404:
                return None
        except (URLError, TimeoutError, OSError):
            time.sleep(1 + attempt)
    return None


def tag(xml: str, name: str) -> str:
    m = re.search(rf"<{name}>(.*?)</{name}>", xml, re.S)
    if not m:
        return ""
    return re.sub(r"<[^>]+>", " ", m.group(1)).strip()


def load_tracked_stems() -> set[str]:
    """Company name stems already in COMPANIES — Exit Watch is only
    interested in what we do NOT already track."""
    try:
        text = DATA_JS.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    start = text.find("const COMPANIES = [")
    if start < 0:
        return set()
    chunk = text[start:start + 4_000_000]
    return {stem(n) for n in re.findall(r'\bname:\s*"([^"]{2,80})"', chunk)}


def load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ─────────────────────────────── ingest ─────────────────────────────────

def daily_form_d(day: datetime) -> list[dict]:
    """Every Form D filed on one calendar day, from EDGAR's daily index."""
    q = (day.month - 1) // 3 + 1
    url = (f"https://www.sec.gov/Archives/edgar/daily-index/"
           f"{day:%Y}/QTR{q}/form.{day:%Y%m%d}.idx")
    body = get(url)
    if not body:
        return []
    rows = []
    for line in body.splitlines():
        if not line.startswith("D "):
            continue
        # Fixed-width-ish: FORM  COMPANY  CIK  DATE  PATH
        parts = line.split()
        if len(parts) < 4 or not parts[-1].endswith(".txt"):
            continue
        path = parts[-1]
        filed = parts[-2]
        cik = parts[-3]
        name = " ".join(parts[1:-3]).strip()
        if not cik.isdigit():
            continue
        rows.append({"issuer_name": name, "cik": cik,
                     "filed": filed, "path": path})
    return rows


def parse_form_d(cik: str, path: str, cache: dict) -> dict | None:
    """Pull and parse one Form D primary document."""
    acc = Path(path).stem.replace("-", "")
    key = f"{cik}/{acc}"
    if key in cache:
        return cache[key] or None

    url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml")
    xml = get(url)
    time.sleep(THROTTLE)
    if not xml:
        cache[key] = None
        return None

    persons = []
    for blk in re.findall(r"<relatedPersonInfo>(.*?)</relatedPersonInfo>", xml, re.S):
        first = tag(blk, "firstName")
        last = tag(blk, "lastName")
        full = " ".join(x for x in (first, tag(blk, "middleName"), last) if x).strip()
        if not full:
            continue
        rels = re.findall(r"<relationship>(.*?)</relationship>", blk)
        persons.append({
            "name": full,
            "key": person_key(f"{first} {last}"),
            "roles": [r.strip() for r in rels if r.strip()],
            "state": tag(blk, "stateOrCountryDescription") or tag(blk, "stateOrCountry"),
        })

    sold_raw = tag(xml, "totalAmountSold")
    try:
        sold = float(sold_raw)
    except (TypeError, ValueError):
        sold = None

    rec = {
        "cik": cik,
        "accession": acc,
        "entity": tag(xml, "entityName"),
        "industry": tag(xml, "industryGroupType"),
        "year_inc": (re.search(r"\b(19|20)\d{2}\b", tag(xml, "yearOfInc")) or [None])[0]
                    if tag(xml, "yearOfInc") else None,
        "state": tag(xml, "stateOrCountry"),
        "amount_sold": sold,
        "first_sale": tag(xml, "dateOfFirstSale"),
        "persons": persons,
        "url": (f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml"),
        "filing_url": (f"https://www.sec.gov/cgi-bin/browse-edgar"
                       f"?action=getcompany&CIK={cik}&type=D&dateb=&owner=include&count=10"),
    }
    # year_inc via regex on the raw tag (the XML nests a boolean before it)
    m = re.search(r"<yearOfInc>.*?<value>(\d{4})</value>", xml, re.S) or \
        re.search(r"<yearOfInc>.*?(\b(?:19|20)\d{2}\b)", xml, re.S)
    rec["year_inc"] = int(m.group(1)) if m else None

    cache[key] = rec
    return rec


def is_candidate(rec: dict, tracked: set[str], max_age: int) -> tuple[bool, str]:
    """Should this filing enter the Exit Watch queue?"""
    name = rec.get("entity") or ""
    if not name:
        return False, "no entity name"

    if stem(name) in tracked:
        return False, "already tracked in COMPANIES"

    ind = (rec.get("industry") or "").strip()
    if ind in DROP_INDUSTRY:
        return False, f"industry: {ind}"
    if ind and ind not in KEEP_INDUSTRY:
        return False, f"industry not frontier-adjacent: {ind}"

    if SPV_MARKER.search(name):
        return False, "name looks like an investment vehicle"

    yr = rec.get("year_inc")
    this_year = datetime.now(timezone.utc).year
    if yr and (this_year - yr) > max_age:
        return False, f"incorporated {yr}, older than {max_age}y"

    if not rec.get("persons"):
        return False, "no named officers"

    return True, ""


# ──────────────────────────────── main ──────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30,
                    help="calendar days of EDGAR daily index to sweep")
    ap.add_argument("--max-age", type=int, default=3,
                    help="max years since incorporation to count as a formation")
    ap.add_argument("--dry", action="store_true", help="write nothing")
    args = ap.parse_args()

    print("=" * 72)
    print("Exit Watch — Form D formation sweep")
    print("=" * 72)

    tracked = load_tracked_stems()
    cache = load_cache()
    print(f"companies already tracked: {len(tracked)}")
    print(f"cached filings: {len(cache)}")

    today = datetime.now(timezone.utc)
    filings = []
    for i in range(args.days):
        day = today - timedelta(days=i + 1)
        if day.weekday() >= 5:          # EDGAR does not publish at weekends
            continue
        rows = daily_form_d(day)
        if rows:
            print(f"  {day:%Y-%m-%d}  {len(rows):4d} Form D")
        filings.extend(rows)
        time.sleep(THROTTLE)

    print(f"\ntotal Form D filings scanned: {len(filings)}")
    if not filings:
        print("no filings retrieved — EDGAR may be unreachable; leaving output untouched")
        return 1

    kept, dropped = [], {}
    for i, f in enumerate(filings, 1):
        if i % 100 == 0:
            print(f"  parsed {i}/{len(filings)}…")
        rec = parse_form_d(f["cik"], f["path"], cache)
        if not rec:
            continue
        rec["filed"] = f["filed"]
        ok, why = is_candidate(rec, tracked, args.max_age)
        if ok:
            kept.append(rec)
        else:
            dropped[why.split(":")[0]] = dropped.get(why.split(":")[0], 0) + 1

    kept.sort(key=lambda r: (r.get("first_sale") or "", r.get("amount_sold") or 0),
              reverse=True)

    print(f"\ncandidates surviving filters: {len(kept)}")
    print("dropped:")
    for k, v in sorted(dropped.items(), key=lambda x: -x[1])[:8]:
        print(f"  {v:5d}  {k}")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": args.days,
        "filings_scanned": len(filings),
        "candidates": kept,
        "note": ("New US entities filing their first Form D in a frontier-adjacent "
                 "industry group. Pedigree matching and scoring happen in "
                 "build_exit_watch.py — nothing here is yet a claim about anyone."),
    }

    if args.dry:
        print("\n--dry: nothing written")
        return 0

    DATA.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}  ({len(kept)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
