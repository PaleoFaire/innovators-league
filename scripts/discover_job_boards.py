#!/usr/bin/env python3
"""
Job-board discovery — the coverage fix for the Build-Out Pulse.
─────────────────────────────────────────────────────────────────────────
The jobs feed covers ~80 companies because fetch_jobs.py carries hard-coded
board lists. This script finds boards for the other ~1,100 by:

  1. Reading each company's own careers page (/careers, /jobs, /join, /careers/,
     /company/careers, /about/careers) and looking for an embedded board link —
     Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Rippling, BambooHR.
     A link on the company's own site is definitive → confidence "high".
  2. Probing the board APIs directly with slugs derived from the DOMAIN
     (valaratomics.com → valaratomics, valar-atomics, valar) → "high" when the
     board returns jobs and at least one job URL or company field echoes the slug.
  3. Probing with slugs derived from the NAME → "medium" (review before use;
     a common word can hit somebody else's board).

Output: data/pulse/job_boards_discovered.json
  [{company, platform, slug, confidence, evidence, jobs_seen, checked}]
fetch_jobs.py loads the "high" entries automatically; "medium" wait in the queue.

Usage:
  python3 scripts/discover_job_boards.py                # all private companies without a board
  python3 scripts/discover_job_boards.py --limit 60     # a sample
  python3 scripts/discover_job_boards.py --only "Valar Atomics,Antares"
"""
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "pulse" / "job_boards_discovered.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; InnovatorsLeagueBot/1.0; +https://innovatorsleague.com)"}
TIMEOUT = 8
PAUSE = 0.15

BOARD_LINK = re.compile(
    r"(?:boards\.greenhouse\.io|job-boards\.greenhouse\.io|boards-api\.greenhouse\.io/v1/boards)/([A-Za-z0-9_-]+)"
    r"|jobs\.lever\.co/([A-Za-z0-9_-]+)"
    r"|jobs\.ashbyhq\.com/([A-Za-z0-9_.-]+)"
    r"|apply\.workable\.com/([A-Za-z0-9_-]+)"
    r"|jobs\.smartrecruiters\.com/([A-Za-z0-9_-]+)"
    r"|ats\.rippling\.com/([A-Za-z0-9_-]+)"
    r"|([A-Za-z0-9_-]+)\.bamboohr\.com/(?:careers|jobs)",
    re.I,
)
PLATFORMS = ["greenhouse", "lever", "ashby", "workable", "smartrecruiters", "rippling", "bamboohr"]
CAREERS_PATHS = ["/careers", "/jobs", "/join", "/careers/", "/company/careers", "/about/careers", "/join-us", "/work-with-us"]


def load_companies():
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync("data.js","utf8")+";globalThis.__n=COMPANIES.map(c=>({name:c.name,'
          'website:c.website||\'\',status:c.status||\'\',ticker:c.ticker||\'\'}));",s);console.log(JSON.stringify(s.__n));')
    raw = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    return json.loads(raw)


def known_boards():
    """Companies already in fetch_jobs.py's hard-coded lists or the jobs feed."""
    known = set()
    src = (ROOT / "scripts" / "fetch_jobs.py").read_text(encoding="utf-8")
    for m in re.finditer(r'\(\s*"([^"]+)"\s*,\s*"[^"]+"\s*\)', src):
        known.add(m.group(1))
    try:
        txt = (DATA / "jobs_auto.js").read_text(encoding="utf-8")
        i = txt.find("const JOBS_DATA = ")
        for j in json.JSONDecoder().raw_decode(txt[i + len("const JOBS_DATA = "):])[0]:
            known.add(j.get("company"))
    except Exception:
        pass
    return known


def get(url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True, **kw)
        return r
    except requests.RequestException:
        return None


def slugs_from_domain(website):
    host = urlparse(website if website.startswith("http") else "https://" + website).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    base = host.split(".")[0]
    out = [base]
    for suf in ("inc", "co", "hq", "labs", "ai", "tech", "technologies", "energy", "space", "aero", "systems", "robotics", "industries"):
        if base.endswith(suf) and len(base) > len(suf) + 2:
            out.append(base[: -len(suf)])
    # camel/compound split: valaratomics → valar-atomics is unknowable; try the first 5+ letters as a guess only via name slugs
    return list(dict.fromkeys(s for s in out if s))


def slugs_from_name(name):
    n = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    words = n.split()
    out = ["".join(words), "-".join(words)]
    if len(words) > 1:
        out.append(words[0])
    for suf in ("inc", "corp", "co", "labs", "ai", "technologies", "tech", "industries", "systems", "energy", "space"):
        if words and words[-1] == suf and len(words) > 1:
            out.append("".join(words[:-1])); out.append("-".join(words[:-1]))
    return [s for s in dict.fromkeys(out) if len(s) >= 3]


def probe(platform, slug):
    """Returns (jobs_count, evidence) if the board exists with ≥1 job, else None."""
    try:
        if platform == "greenhouse":
            r = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
            if r is not None and r.status_code == 200:
                jobs = r.json().get("jobs", [])
                if jobs:
                    return len(jobs), jobs[0].get("absolute_url", "")
        elif platform == "lever":
            r = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            if r is not None and r.status_code == 200:
                jobs = r.json()
                if isinstance(jobs, list) and jobs:
                    return len(jobs), jobs[0].get("hostedUrl", "")
        elif platform == "ashby":
            r = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
            if r is not None and r.status_code == 200:
                jobs = r.json().get("jobs", [])
                if jobs:
                    return len(jobs), jobs[0].get("jobUrl", "")
        elif platform == "workable":
            r = get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}")
            if r is not None and r.status_code == 200:
                jobs = r.json().get("jobs", [])
                if jobs:
                    return len(jobs), jobs[0].get("url", "")
        elif platform == "smartrecruiters":
            r = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings")
            if r is not None and r.status_code == 200:
                c = r.json().get("content", [])
                if c:
                    return len(c), c[0].get("ref", "")
    except (ValueError, AttributeError):
        return None
    return None


def careers_page_links(website):
    """Look for an ATS link on the company's own careers pages."""
    base = website if website.startswith("http") else "https://" + website
    base = base.rstrip("/")
    found = []
    for path in [""] + CAREERS_PATHS:
        r = get(base + path)
        if r is None or r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            continue
        for m in BOARD_LINK.finditer(r.text):
            groups = m.groups()
            for i, g in enumerate(groups):
                if g:
                    found.append((PLATFORMS[i], g.lower(), base + path))
        if found:
            break
        time.sleep(PAUSE)
    return found


def discover(company):
    name, website = company["name"], company["website"]
    rec = {"company": name, "checked": date.today().isoformat(), "candidates": []}
    # 1. the company's own careers page — definitive
    if website:
        for platform, slug, page in careers_page_links(website):
            if platform in ("rippling", "bamboohr"):
                rec["candidates"].append({"platform": platform, "slug": slug, "confidence": "high", "evidence": page, "jobs_seen": None})
                continue
            p = probe(platform, slug)
            if p:
                rec["candidates"].append({"platform": platform, "slug": slug, "confidence": "high", "evidence": page, "jobs_seen": p[0]})
        if rec["candidates"]:
            return rec
    # 2. domain-derived slugs
    if website:
        for slug in slugs_from_domain(website):
            for platform in ("greenhouse", "ashby", "lever", "workable"):
                p = probe(platform, slug)
                time.sleep(PAUSE)
                if p:
                    conf = "high" if slug in (p[1] or "").lower() else "medium"
                    rec["candidates"].append({"platform": platform, "slug": slug, "confidence": conf, "evidence": p[1], "jobs_seen": p[0]})
            if rec["candidates"]:
                return rec
    # 3. name-derived slugs — review before use
    for slug in slugs_from_name(name):
        for platform in ("greenhouse", "ashby", "lever"):
            p = probe(platform, slug)
            time.sleep(PAUSE)
            if p:
                rec["candidates"].append({"platform": platform, "slug": slug, "confidence": "medium", "evidence": p[1], "jobs_seen": p[0]})
        if rec["candidates"]:
            break
    return rec


def main():
    limit = None
    only = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--only" in sys.argv:
        only = set(x.strip() for x in sys.argv[sys.argv.index("--only") + 1].split(","))
    companies = load_companies()
    known = known_boards()
    existing = {}
    if OUT.exists():
        for r in json.load(open(OUT)):
            existing[r["company"]] = r
    todo = [c for c in companies
            if not c["ticker"] and c["status"] in ("active", "") and c["name"] not in known
            and (only is None or c["name"] in only)
            and (only is not None or c["name"] not in existing)]
    if limit:
        todo = todo[:limit]
    print(f"probing {len(todo)} companies ({len(known)} already have boards, {len(existing)} previously checked)")
    results = list(existing.values()) if only is None else [r for r in existing.values() if r["company"] not in (only or set())]
    hits = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(discover, c): c for c in todo}
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            results.append(rec)
            if rec["candidates"]:
                hits += 1
                best = rec["candidates"][0]
                print(f"  ✓ {rec['company']}: {best['platform']}/{best['slug']} [{best['confidence']}] jobs={best['jobs_seen']}")
            if i % 50 == 0:
                print(f"  … {i}/{len(todo)} checked, {hits} boards found")
                json.dump(sorted(results, key=lambda r: r["company"]), open(OUT, "w"), indent=1)
    json.dump(sorted(results, key=lambda r: r["company"]), open(OUT, "w"), indent=1)
    high = sum(1 for r in results if any(c["confidence"] == "high" for c in r["candidates"]))
    med = sum(1 for r in results if r["candidates"] and not any(c["confidence"] == "high" for c in r["candidates"]))
    print(f"done: {len(results)} checked, {high} high-confidence boards, {med} medium (review) → {OUT}")


if __name__ == "__main__":
    main()
