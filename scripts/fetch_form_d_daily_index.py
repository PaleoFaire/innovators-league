#!/usr/bin/env python3
"""
Form D — EDGAR Daily Index Sweep
─────────────────────────────────────────────────────────────────────────
Catches private fundraises the CIK map cannot see.

Why this exists
───────────────
A Form D is the earliest public evidence that a private round has closed —
weeks to months before the press release. It is the single best leading
indicator we have, and on 2026-08-19 we were showing FOUR of them.

The reason is structural, not a bug in the old fetcher. `fetch_form_d_filings.py`
joins EDGAR results to our companies through `data/cik_map.json`, and only a
`match_method == "cik"` row is allowed to go live. That map holds a real CIK for
377 of 1,181 companies — 32%. A further 193 companies (the buildlist and
Black Flag imports) have no entry in the map at all, because they were added
after it was built. So two-thirds of the database is invisible to our best
signal, and every new company we add starts out invisible too.

This script inverts the join. Instead of asking EDGAR about companies we know,
it reads EDGAR's daily index — the authoritative list of every filing accepted
that day, ~180-290 of them Form D — and asks which of those we recognise. New
companies are covered the day they are added, with no map maintenance.

Why not just loosen the name matching
─────────────────────────────────────
Because most Form D filers are shell entities. A real day's index contains
"8VC Entrepreneurs Fund VII, L.P.", "1789 CAPITAL DAWN LP", "ACP I Fund LLC".
Loose matching against a 1,181-name list would attach a Dallas real-estate
syndicate to a defence company because both stem to the same token, and a
fabricated $40M round on a company profile is far more damaging than a missed
one. We already made the cheap version of this mistake twice — pilgrim.com (a
Massachusetts telephone company) and remora.com (car-dealership software).

So a match must clear one of three bars, in descending order of strength:

  cik          the filer's CIK equals a High/Medium-confidence CIK we hold.
               Conclusive.
  founder      the filer's name stems to ours AND the Form D's own
               "related persons" list contains a founder or executive we
               already have on record. Form D requires real names of
               directors and officers, so this is close to conclusive — and
               it is the reason this script is worth writing rather than
               simply relaxing a threshold.
  name-strict  the filer's name stems to ours exactly after stripping legal
               suffixes, the stem is >= 6 characters, and we hold no
               conflicting CIK for that company. Plausible, not proven.

Only `cik` and `founder` matches go live. `name-strict` goes to the review
queue, same as the existing script's behaviour — visible to us, not to members.

A company whose recorded CIK differs from the filer's CIK is rejected outright
rather than downgraded: that is positive evidence of a different legal entity,
not weak evidence of the same one.

Self-healing
────────────
Every `founder`-confirmed match writes its CIK back into `data/cik_map.json`
with confidence "High". The map therefore fills in from real filings over time
instead of by hand, and each company only has to be caught once.

Output
──────
  data/form_d_daily_auto.json    matched filings, with evidence for each
  data/form_d_daily_review.json  name-only candidates awaiting a human
  data/cik_map.json              updated in place with newly proven CIKs

Merging into the live payload is done by --merge, which folds these rows into
data/form_d_filings_auto.json + .js, deduped by accession number, so signals.js
and terminal.js render them with no front-end change.

Usage
─────
  python3 scripts/fetch_form_d_daily_index.py --days 3 --dry
  python3 scripts/fetch_form_d_daily_index.py --days 8 --merge
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_JS = ROOT / "data.js"
CIK_MAP = DATA / "cik_map.json"
AUTO_OUT = DATA / "form_d_daily_auto.json"
REVIEW_OUT = DATA / "form_d_daily_review.json"
LIVE_JSON = DATA / "form_d_filings_auto.json"
LIVE_JS = DATA / "form_d_filings_auto.js"

# SEC requires a descriptive UA with a contact address; unidentified traffic
# gets blocked at the edge. Their published limit is 10 req/sec — we stay well
# under it because a miss here is invisible and a ban is not.
HEADERS = {
    "User-Agent": "Rational Optimist Society stephen@rationaloptimistsociety.com",
    "Accept-Encoding": "gzip, deflate",
}
THROTTLE = 0.15

LEGAL_SUFFIX = re.compile(
    r"\b(inc|incorporated|llc|l\.?l\.?c|corp|corporation|co|company|ltd|limited|"
    r"lp|l\.?p|llp|plc|holdings?|group|technologies|technology|labs?|"
    r"industries|systems|international|worldwide|usa|us|the)\b", re.I)

# Filer names that are structurally SPVs / funds rather than operating
# companies. A Form D from one of these is a real signal — it is often how a
# round in one of our companies actually reaches EDGAR — but the filer name
# does not identify the portfolio company, so it must never be name-matched.
SPV_MARKER = re.compile(
    r"\b(fund|partners|capital|ventures?|syndicate|spv|series|investors?|"
    r"holdings? (?:i{1,3}|\d+)|opportunit(?:y|ies)|管理)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def stem(s: str) -> str:
    """Normalised company token with legal suffixes stripped.

    Applied repeatedly because filers stack them: "Dexterity, Inc." and
    "Hadrian Automation Technologies Inc" both need more than one pass.
    """
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


def load_companies() -> list[dict]:
    """name, founders, existing CIK — read through node so we parse data.js
    exactly the way the browser does rather than by regex."""
    js = (
        'const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
        'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
        '+";globalThis.__n=COMPANIES.map(c=>({name:c.name,'
        'founders:c.founders||c.founder||\'\','
        'former:c.formerNames||[]}));",s);'
        "console.log(JSON.stringify(s.__n));"
    )
    out = subprocess.run(["node", "-e", js, str(DATA_JS)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def build_indexes(companies: list[dict]):
    """stem -> company name, and company name -> set of founder keys."""
    by_stem: dict[str, str] = {}
    collisions: set[str] = set()
    founders: dict[str, set[str]] = {}

    for c in companies:
        nm = c["name"]
        f = c.get("founders")
        if isinstance(f, list):
            flat = " , ".join(str(x) for x in f)
        else:
            flat = str(f or "")
        keys = {person_key(p) for p in re.split(r"[,&;]| and ", flat)}
        founders[nm] = {k for k in keys if k}

        for label in [nm] + list(c.get("former") or []):
            s = stem(label)
            if len(s) < 6:
                continue          # too short to be safe on a name-only match
            if s in by_stem and by_stem[s] != nm:
                collisions.add(s)  # two of OUR companies share a stem
            else:
                by_stem[s] = nm

    for s in collisions:
        by_stem.pop(s, None)
    return by_stem, founders, collisions


def load_cik_map() -> dict:
    try:
        return json.loads(CIK_MAP.read_text())
    except Exception:
        return {}


def daily_index(day: datetime) -> list[dict]:
    """Every Form D / D/A accepted on `day`. Empty on weekends and holidays."""
    qtr = (day.month - 1) // 3 + 1
    url = (f"https://www.sec.gov/Archives/edgar/daily-index/{day.year}/"
           f"QTR{qtr}/form.{day.strftime('%Y%m%d')}.idx")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"  {day:%Y-%m-%d}  fetch failed: {type(e).__name__}")
        return []
    # SEC serves 403 (not 404) for a daily index that does not exist — weekends,
    # market holidays, and the current day before the feed is published. All
    # three are normal, so they are silent rather than logged as failures.
    if r.status_code in (403, 404):
        return []
    if r.status_code != 200:
        print(f"  {day:%Y-%m-%d}  HTTP {r.status_code}")
        return []

    rows = []
    for line in r.text.splitlines():
        # Fixed-width: form type, company name, CIK, date filed, file name.
        # Form type is left-justified in the first column.
        if not (line.startswith("D ") or line.startswith("D/A ")):
            continue
        m = re.match(r"^(D(?:/A)?)\s+(.+?)\s{2,}(\d+)\s+(\d{8})\s+(\S+)\s*$", line)
        if not m:
            continue
        form, company, cik, filed, path = m.groups()
        rows.append({
            "form": form,
            "issuer_name": company.strip(),
            "cik": cik.lstrip("0"),
            "filed_date": f"{filed[:4]}-{filed[4:6]}-{filed[6:]}",
            "path": path,
        })
    return rows


def accession_from_path(path: str) -> str:
    """edgar/data/2137857/0002137857-26-000002.txt -> 0002137857-26-000002"""
    base = path.rsplit("/", 1)[-1]
    return base[:-4] if base.endswith(".txt") else base


def fetch_form_d_xml(cik: str, accession: str) -> dict:
    """Offering amounts and the related-persons list from the filing itself."""
    adsh = accession.replace("-", "")
    url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh}/"
           "primary_doc.xml")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return {}
        x = r.text
    except requests.RequestException:
        return {}

    def tag(t):
        m = re.search(rf"<{t}>(.*?)</{t}>", x, re.S)
        return (m.group(1).strip() if m else "")

    persons = []
    for blk in re.findall(r"<relatedPersonInfo>(.*?)</relatedPersonInfo>", x, re.S):
        first = re.search(r"<firstName>(.*?)</firstName>", blk, re.S)
        last = re.search(r"<lastName>(.*?)</lastName>", blk, re.S)
        if first and last:
            persons.append(f"{first.group(1).strip()} {last.group(1).strip()}")

    return {
        "offering_amount": tag("totalOfferingAmount"),
        "amount_sold": tag("totalAmountSold"),
        "amount_remaining": tag("totalRemaining"),
        "securities_type": "Equity" if "<isEquityType>true" in x.replace(" ", "")
                           else ("Debt" if "<isDebtType>true" in x.replace(" ", "") else ""),
        "related_persons": persons,
        "is_safe": bool(re.search(r"SAFE|simple agreement", x, re.I)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=8,
                    help="calendar days of daily index to sweep")
    ap.add_argument("--dry", action="store_true", help="write nothing")
    ap.add_argument("--merge", action="store_true",
                    help="fold live matches into form_d_filings_auto.json/.js")
    args = ap.parse_args()

    print("=" * 70)
    print("Form D — EDGAR daily index sweep")
    print("=" * 70)

    companies = load_companies()
    by_stem, founders, collisions = build_indexes(companies)
    cik_map = load_cik_map()
    cik_to_company = {
        str(v.get("cik", "")).lstrip("0"): k
        for k, v in cik_map.items()
        if isinstance(v, dict) and str(v.get("cik", "")).strip()
        and v.get("confidence") in ("High", "Medium")
    }
    print(f"companies: {len(companies)}   "
          f"safe name stems: {len(by_stem)}   "
          f"known CIKs: {len(cik_to_company)}")
    if collisions:
        print(f"  ({len(collisions)} stems dropped — two of our own companies share them)")

    # ── sweep ────────────────────────────────────────────────────────────
    today = datetime.now(timezone.utc)
    filings = []
    for i in range(args.days):
        day = today - timedelta(days=i)
        rows = daily_index(day)
        if rows:
            print(f"  {day:%Y-%m-%d}  {len(rows)} Form D")
        filings.extend(rows)
        time.sleep(THROTTLE)
    print(f"total Form D filings scanned: {len(filings)}")

    # ── match ────────────────────────────────────────────────────────────
    live, review = [], []
    for f in filings:
        issuer = f["issuer_name"]
        s = stem(issuer)
        company = None
        method = None
        evidence = ""

        # 1. CIK — conclusive
        if f["cik"] in cik_to_company:
            company = cik_to_company[f["cik"]]
            method = "cik"
            evidence = f"filer CIK {f['cik']} == our recorded CIK"

        # 2. name stem, then corroborate
        elif s in by_stem and not SPV_MARKER.search(issuer):
            cand = by_stem[s]
            known = cik_map.get(cand, {})
            known_cik = str(known.get("cik", "")).lstrip("0") if isinstance(known, dict) else ""
            if known_cik and known_cik != f["cik"]:
                # We hold a CIK for this company and it is not this filer.
                # Positive evidence of a different entity — drop it.
                continue
            company, method = cand, "name-strict"
            evidence = f"'{issuer}' stems to '{cand}'"

        if not company:
            continue

        acc = accession_from_path(f["path"])
        detail = fetch_form_d_xml(f["cik"], acc)
        time.sleep(THROTTLE)

        # Promote a name match to `founder` when the filing names one of ours
        if method == "name-strict" and detail.get("related_persons"):
            ours = founders.get(company, set())
            hit = [p for p in detail["related_persons"] if person_key(p) in ours]
            if hit:
                method = "founder"
                evidence += f"; Form D names {hit[0]}, a recorded founder"

        rec = {
            "match_method": method,
            "match_evidence": evidence,
            "company": company,
            "issuer_name": issuer,
            "form": f["form"],
            "filed_date": f["filed_date"],
            "cik": f["cik"],
            "accession": acc,
            "filing_url": (f"https://www.sec.gov/Archives/edgar/data/"
                           f"{f['cik']}/{acc.replace('-', '')}/primary_doc.xml"),
            "offering_amount": detail.get("offering_amount", ""),
            "amount_sold": detail.get("amount_sold", ""),
            "amount_remaining": detail.get("amount_remaining", ""),
            "securities_type": detail.get("securities_type", ""),
            "related_persons": detail.get("related_persons", [])[:8],
            "is_safe": detail.get("is_safe", False),
            "source": "edgar-daily-index",
        }
        (live if method in ("cik", "founder") else review).append(rec)
        mark = {"cik": "CIK", "founder": "FOUNDER", "name-strict": "review"}[method]
        amt = rec["offering_amount"] or "—"
        print(f"    [{mark:<7}] {company[:26]:<28}{f['filed_date']}  ${amt}")

    live.sort(key=lambda r: r["filed_date"], reverse=True)
    print(f"\nlive matches: {len(live)}   review queue: {len(review)}")

    if args.dry:
        print("DRY RUN — nothing written")
        return 0

    stamp = datetime.now(timezone.utc).isoformat()
    AUTO_OUT.write_text(json.dumps(
        {"generated_at": stamp, "lookback_days": args.days,
         "scanned": len(filings), "total": len(live), "filings": live}, indent=2))
    REVIEW_OUT.write_text(json.dumps(
        {"generated_at": stamp,
         "note": "name-only matches. NOT shown to members. Confirm, then add the "
                 "CIK to data/cik_map.json to promote.",
         "candidates": review}, indent=2))
    print(f"wrote {AUTO_OUT.name} and {REVIEW_OUT.name}")

    # ── self-heal the CIK map from founder-confirmed filings ────────────
    learned = 0
    for r in live:
        if r["match_method"] != "founder":
            continue
        cur = cik_map.get(r["company"])
        if isinstance(cur, dict) and str(cur.get("cik", "")).strip():
            continue
        cik_map[r["company"]] = {
            "cik": r["cik"], "confidence": "High",
            "edgarName": r["issuer_name"], "hasFormD": True,
            "note": (f"Learned {r['filed_date']} from EDGAR daily index; "
                     f"Form D related persons include a recorded founder."),
        }
        learned += 1
    if learned:
        CIK_MAP.write_text(json.dumps(cik_map, indent=2, sort_keys=True))
        print(f"learned {learned} new CIKs into {CIK_MAP.name}")

    # ── merge into the payload the site already renders ──────────────────
    if args.merge and live:
        try:
            payload = json.loads(LIVE_JSON.read_text())
        except Exception:
            payload = {"filings": []}
        existing = payload.get("filings", [])
        seen = {r.get("accession") for r in existing}
        added = [r for r in live if r["accession"] not in seen]
        merged = existing + added
        merged.sort(key=lambda r: r.get("filed_date", ""), reverse=True)
        payload.update({
            "generated_at": stamp,
            "source": "SEC EDGAR Form D (full-text search + daily index)",
            "total_filings": len(merged),
            "filings": merged,
        })
        LIVE_JSON.write_text(json.dumps(payload, indent=2))
        header = (
            "// Auto-generated Form D + SAFE exempt-offering filings\n"
            "// Source: SEC EDGAR (public) — full-text search + daily index\n"
            f"// Last updated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC\n"
            f"// Total: {len(merged)} filings across "
            f"{len({m['company'] for m in merged})} companies\n"
        )
        LIVE_JS.write_text(header + "const FORM_D_FILINGS = "
                           + json.dumps(payload, indent=2, ensure_ascii=False) + ";\n")
        print(f"merged {len(added)} new filings into {LIVE_JSON.name} "
              f"(now {len(merged)} total)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
