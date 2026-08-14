#!/usr/bin/env python3
"""
Website Resolver
─────────────────────────────────────────────────────────────────────────
Fills the `website` field for companies that have none.

Why it matters
──────────────
Stephen's bar for the database is "if I go to this city, would it be worth
meeting this company". A record with no website fails that test on contact:
you cannot look them up before the meeting. As of 2026-08-14, 171 of 1,143
companies had no website — mostly thin imports from the buildlist sweep, which
supplies founders and funding but no URL.

How it works — and why it does not guess
────────────────────────────────────────
For each company it tries a small set of domain candidates derived from the
name (acme.com, acme.ai, acme.io, getacme.com, acmerobotics.com ...), fetches
each, and only accepts one when the page CONFIRMS the company:

  * the page must return 200 and contain real text
  * the company name (normalised) must appear in the title, an og:site_name,
    or the body copy
  * a parked/for-sale/registrar holding page is rejected outright

A wrong website is worse than a missing one — it sends a member to a stranger's
site and looks like sloppy data. So an unconfirmed candidate is discarded and
the field is left empty for a human, not filled with a plausible guess. This is
the same failure we already hit once: PILGRIM's record pointed at pilgrim.com,
which is a Massachusetts telephone company.

Output
──────
  data/website_resolution.json   every attempt, accepted and rejected, with why
  writes accepted URLs into data.js (guarded by the data-quality gate)

Usage
─────
  python3 scripts/enrich_websites.py --dry        # report only, no writes
  python3 scripts/enrich_websites.py --limit 40
  python3 scripts/enrich_websites.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
REPORT = ROOT / "data" / "website_resolution.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 8
TLDS = [".com", ".ai", ".io", ".co", ".tech", ".space", ".energy", ".xyz", ".us"]

PARKED = re.compile(
    r"(domain (?:is )?(?:for sale|parking)|buy this domain|godaddy|namecheap|"
    r"sedo\.com|hugedomains|this domain may be for sale|under construction|"
    r"coming soon</title>|website is parked)", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def candidates(name: str) -> list[str]:
    """Domain guesses, most likely first."""
    base = norm(name)
    if not base:
        return []
    words = re.findall(r"[A-Za-z0-9]+", name)
    short = norm("".join(words[:-1])) if len(words) > 1 else ""
    out = []
    for stem in filter(None, [base, short]):
        for tld in TLDS:
            out.append(stem + tld)
    if len(base) > 3:
        out += [f"get{base}.com", f"{base}hq.com", f"{base}app.com"]
    seen, uniq = set(), []
    for d in out:
        if d not in seen:
            seen.add(d)
            uniq.append(d)
    return uniq[:14]


STOPWORDS = {
    "the","and","for","that","with","from","into","this","their","using","uses","used",
    "builds","build","building","company","technology","technologies","platform","system",
    "systems","solution","solutions","products","product","first","world","new","more",
    "than","over","across","which","while","into","under","also","its","are","was",
}


def keywords(text: str) -> set[str]:
    """Distinctive words from our own description, for corroboration."""
    ws = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", (text or "").lower())
    return {w for w in ws if w not in STOPWORDS}


def confirms(html: str, name: str, desc: str = "") -> bool:
    """Does this page actually belong to THIS company?

    The name alone is not enough. remora.com is a car-dealership software firm,
    not our truck-exhaust carbon-capture company, and it passed a name-only
    check because "Remora" is in its title. So we also require the page to
    corroborate what we already believe the company does: at least two
    distinctive words from our own description must appear on the page.

    This is the pilgrim.com failure mode — a plausible domain belonging to a
    different company entirely — and a wrong URL is worse than a blank one.
    """
    if PARKED.search(html[:4000]):
        return False
    target = norm(name)
    if len(target) < 3:
        return False
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        title = m.group(1)
    og = ""
    m = re.search(r'property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if m:
        og = m.group(1)
    body = re.sub(r"<[^>]+>", " ", html[:60000])
    name_ok = (target in norm(title) or target in norm(og)
               or (target in norm(body) and len(body.strip()) > 400))
    if not name_ok:
        return False
    kws = keywords(desc)
    if not kws:
        return True                     # nothing to corroborate against
    page = set(re.findall(r"[a-z][a-z\-]{4,}", body.lower()))
    overlap = kws & page
    # Scale the demand to how much description we actually have. Groq's whole
    # record is "Delivers LPU-based AI compute" — three usable words — so a
    # flat two-word rule rejected its real site. Rich descriptions still have
    # to clear two.
    need = 2 if len(kws) >= 6 else 1
    return len(overlap) >= need


def resolve(company: dict) -> dict:
    name = company["n"]
    tried = []
    for dom in candidates(name):
        for scheme in ("https://",):
            url = scheme + dom
            try:
                r = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                                 headers={"User-Agent": UA})
            except requests.RequestException as e:
                tried.append({"url": url, "result": type(e).__name__})
                continue
            if r.status_code != 200 or not r.text:
                tried.append({"url": url, "result": f"http {r.status_code}"})
                continue
            if confirms(r.text, name, company.get("d", "")):
                final = r.url.rstrip("/")
                return {"company": name, "website": final, "confirmed_via": url,
                        "attempts": tried}
            tried.append({"url": url, "result": "no name match / parked"})
    return {"company": name, "website": None, "attempts": tried}


def load_missing() -> list[dict]:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.filter(c=>!c.website).map(c=>({n:c.name,'
          'd:(c.description||\'\')+\' \'+(c.techApproach||\'\')+\' \'+(c.sector||\'\')}));",s);'
          "console.log(JSON.stringify(s.__n));")
    return json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)


def write_back(found: list[dict]) -> int:
    d = DATA_JS.read_text()
    n = 0
    for f in found:
        name, url = f["company"], f["website"]
        i = d.find(f'name: "{name}",')
        if i < 0:
            continue
        s = d.rfind("{", 0, i)
        depth = 0
        j = s
        while j < len(d):
            if d[j] == "{":
                depth += 1
            elif d[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        rec = d[s:j + 1]
        if "website:" in rec:
            continue
        # insert after the name line so field order stays predictable
        new = rec.replace(f'name: "{name}",',
                          f'name: "{name}",\n    website: "{url}",', 1)
        d = d[:s] + new + d[j + 1:]
        n += 1
    DATA_JS.write_text(d)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    missing = load_missing()
    if args.limit:
        missing = missing[:args.limit]
    print(f"companies with no website: {len(missing)}")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(resolve, missing), 1):
            results.append(res)
            mark = "OK " if res["website"] else "   "
            print(f"  [{i:>3}/{len(missing)}] {mark}{res['company'][:30]:<31}"
                  f"{res['website'] or '-'}", flush=True)

    found = [r for r in results if r["website"]]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(),
         "checked": len(results), "resolved": len(found), "results": results}, indent=2))

    print(f"\nresolved {len(found)} / {len(results)}")
    if args.dry:
        print("DRY RUN — data.js untouched")
        return 0
    n = write_back(found)
    print(f"wrote {n} websites into data.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
