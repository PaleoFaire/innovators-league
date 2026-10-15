#!/usr/bin/env python3
"""
Job-board discovery — keeps data/pulse/job_boards.json (the registry that
scripts/fetch_jobs.py pulls from) in step with the 1,200 companies in data.js.

For every company that has no working board it:

  1. Walks the company's own site: the homepage, the careers link in its nav,
     the conventional paths (/careers, /jobs, /join …) and one level below a
     careers page. It reads board LINKS, SCRIPT/IFRAME EMBEDS (Greenhouse
     job_board?for=, jobs.ashbyhq.com/{org}/embed, Lever, Workday, iCIMS,
     SmartRecruiters …) and JSON-LD JobPosting markup. A board on the
     company's own page is accepted as soon as the board responds — unless the
     page lists several boards, in which case each must name the company.
  2. Probes the ATS APIs with slugs derived from the DOMAIN, then from the NAME.
     A hit is accepted only when the board itself names the company: its
     organisation field, its posting text, or the company's domain. Anything
     else is logged with the reason it was rejected.

Public companies are included. Known companies whose registered boards
returned nothing in the last pull (data/jobs_stats.json → boards) are
re-checked, so a company that changes ATS is re-found on the next run.

Outputs
  data/pulse/job_boards.json             the registry (verified boards)
  data/pulse/job_boards_discovered.json  one record per company checked:
        {company, checked, site: {reachable, careers_pages, jsonld, unsupported},
         candidates: [{platform, slug, confidence: high|rejected, how, evidence, jobs_seen, reason}]}

Usage
  python3 scripts/discover_job_boards.py                 # every company without a working board
  python3 scripts/discover_job_boards.py --limit 60      # a sample
  python3 scripts/discover_job_boards.py --only "Valar Atomics,Antares"
  python3 scripts/discover_job_boards.py --workers 8 --no-slug-probes
  python3 scripts/discover_job_boards.py --skip-checked-today   # resume an interrupted run
"""
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_boards as jb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = jb.DISCOVERED_PATH
PAUSE = 0.1

# platforms worth probing blind, cheapest and most common first
DOMAIN_PROBE_PLATFORMS = ("greenhouse", "ashby", "lever", "workable", "smartrecruiters", "rippling")
# Recruitee, Breezy, Teamtailor, Personio, Pinpoint, JazzHR, iCIMS and Workday are found through the company's
# own careers page only (a blind probe of a subdomain that does not exist costs more than it finds).
NAME_PROBE_PLATFORMS = ("greenhouse", "ashby", "lever", "workable", "smartrecruiters")


def load_companies():
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync("data.js","utf8")+";globalThis.__n=COMPANIES.map(c=>({name:c.name,'
          'website:c.website||\'\',status:c.status||\'\',ticker:c.ticker||\'\',location:c.location||\'\',country:c.country||\'\'}));",s);console.log(JSON.stringify(s.__n));')
    raw = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    return json.loads(raw)


def companies_needing_boards(companies, registry, health, only=None):
    """Active/public companies with no registry board that returned jobs in the last pull."""
    by_company = jb.registry_by_company(registry)
    todo = []
    for c in companies:
        if only is not None:
            if c["name"] in only:
                todo.append(c)
            continue
        if c["status"] not in ("active", "ipo", ""):
            continue
        recs = by_company.get(c["name"], [])
        live = False
        for r in recs:
            h = health.get((r["platform"], r["slug"]))
            if h is None:
                live = live or bool(r.get("jobs_seen"))   # never pulled yet: trust the registry
            elif h.get("status") == "ok":
                live = True
        if not live:
            todo.append(c)
    return todo


def _probe_and_verify(company, website, platform, slug, own_site, crowded, how, evidence, hq="", country=""):
    pr = jb.probe_board(platform, slug)
    ok, why = jb.verify_candidate(company, website, platform, slug, pr, own_site=own_site, crowded=crowded, hq=hq, country=country)
    return {"platform": platform, "slug": slug, "confidence": "high" if ok else "rejected", "how": how,
            "evidence": evidence, "jobs_seen": pr["n"], "org": pr.get("org", ""), "reason": why}, pr


BUDGET_SECONDS = 150   # per company; slow sites get the site scan and whatever probes fit


def discover(company, previous=None, slug_probes=True):
    name, website = company["name"], company["website"]
    rec = {"company": name, "checked": jb.today_iso(), "site": {}, "candidates": []}
    tried = set()
    t0 = time.time()

    def over_budget():
        if time.time() - t0 > BUDGET_SECONDS:
            rec["site"]["budget_exceeded"] = True
            return True
        return False

    def consider(platform, slug, own_site, crowded, how, evidence):
        key = (platform, slug.lower())
        if key in tried or platform not in jb.PLATFORMS:
            return False
        tried.add(key)
        cand, pr = _probe_and_verify(name, website, platform, slug, own_site, crowded, how, evidence,
                                     company.get("location", ""), company.get("country", ""))
        rec["candidates"].append(cand)
        return cand["confidence"] == "high" and pr["exists"]

    accepted = False
    # 1. the company's own site
    info = jb.scan_company_site(website) if website else {"reachable": False, "boards": [], "careers_pages": [], "jsonld": False, "unsupported": [], "pages": []}
    rec["site"] = {"reachable": info["reachable"], "careers_pages": info["careers_pages"][:4], "jsonld": info["jsonld"],
                   "unsupported": [list(u) for u in info["unsupported"][:6]], "pages_scanned": len(info["pages"])}
    boards = info["boards"]
    if boards:
        per_page = {}
        for platform, slug, how, page in boards:
            per_page.setdefault(page, []).append((platform, slug, how))
        for platform, slug, how, page in boards:
            crowded = len(boards) > 1
            if consider(platform, slug, True, crowded, how, page):
                accepted = True
        if not accepted and len(boards) > 1:
            # several boards on the company's pages and none names the company: take the one whose slug is the company
            n = jb.norm(name)
            d = jb.domain_base(website)
            for cand in rec["candidates"]:
                s = jb.norm(cand["slug"])
                if cand["jobs_seen"] is not None and s and (s == n or s == jb.norm(d) or (len(s) >= 5 and (s in n or n in s))):
                    cand["confidence"], cand["reason"] = "high", cand["reason"] + " → slug is the company"
                    accepted = True
                    break
    # 2. re-check what an earlier run found (so the queue of unverified candidates gets a decision)
    if not accepted and previous:
        for c in previous.get("candidates", []):
            if c.get("platform") in jb.PLATFORMS and c.get("slug"):
                ev = c.get("evidence") or ""
                evh = urlparse(ev).netloc.lower().replace("www.", "") if ev.startswith("http") else ""
                host = jb.domain_host(website)
                own = bool(host) and (evh == host or evh.endswith("." + host))
                if consider(c["platform"], c["slug"], own, len(previous.get("candidates", [])) > 1, c.get("how", "previous"), ev):
                    accepted = True
                    break
    # 3. domain-derived slugs
    if not accepted and slug_probes and website:
        for slug in jb.slugs_from_domain(website):
            for platform in DOMAIN_PROBE_PLATFORMS:
                if over_budget():
                    break
                if consider(platform, slug, False, False, "domain-slug", f"{platform}:{slug}"):
                    accepted = True
                    break
                time.sleep(PAUSE)
            if accepted or over_budget():
                break
    # 4. name-derived slugs
    if not accepted and slug_probes:
        for slug in jb.slugs_from_name(name):
            for platform in NAME_PROBE_PLATFORMS:
                if over_budget():
                    break
                if consider(platform, slug, False, False, "name-slug", f"{platform}:{slug}"):
                    accepted = True
                    break
                time.sleep(PAUSE)
            if accepted or over_budget():
                break
    # keep rejected "board not found" noise short
    rec["candidates"] = [c for c in rec["candidates"] if not (c["confidence"] == "rejected" and c["reason"] == "board not found" and c["how"] in ("domain-slug", "name-slug"))]
    return rec


def merge_into_registry(rec, registry):
    """Add accepted candidates to the registry (one board per platform per company, replacing dead ones)."""
    accepted = [c for c in rec["candidates"] if c["confidence"] == "high"]
    if not accepted:
        return 0
    today = jb.today_iso()
    added = 0
    for c in accepted:
        existing = [r for r in registry if r["company"] == rec["company"] and r["platform"] == c["platform"]]
        if any(r["slug"] == c["slug"] for r in existing):
            for r in existing:
                if r["slug"] == c["slug"]:
                    r["verified"] = today if c["jobs_seen"] else r.get("verified", "")
                    r["jobs_seen"] = c["jobs_seen"]
            continue
        # the old board on this platform returned nothing (that's why we are here) → replace it
        for r in existing:
            registry.remove(r)
        registry.append({"company": rec["company"], "platform": c["platform"], "slug": c["slug"],
                         "verified": today if c["jobs_seen"] else "", "jobs_seen": c["jobs_seen"],
                         "evidence": f"{c['how']} {c['evidence']}".strip(), "added": today})
        added += 1
    # a newly verified board makes the company's dead boards on other platforms redundant only if they are dead
    return added


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    limit = only = None
    workers = 6
    slug_probes = "--no-slug-probes" not in argv
    skip_today = "--skip-checked-today" in argv
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    if "--only" in argv:
        only = {x.strip() for x in argv[argv.index("--only") + 1].split(",")}
    if "--workers" in argv:
        workers = int(argv[argv.index("--workers") + 1])

    companies = load_companies()
    jb.set_universe([c["name"] for c in companies])
    jb.FAST_PROBES = True
    registry = jb.load_registry()
    health = jb.load_board_health()
    existing = {}
    if OUT.exists():
        try:
            for r in json.load(open(OUT, encoding="utf-8")):
                existing[r["company"]] = r
        except ValueError:
            pass
    todo = companies_needing_boards(companies, registry, health, only)
    if skip_today:
        today = jb.today_iso()
        todo = [c for c in todo if (existing.get(c["name"]) or {}).get("checked") != today]
    if limit:
        todo = todo[:limit]
    live_companies = {r["company"] for r in registry if r.get("jobs_seen")}
    print(f"probing {len(todo)} companies ({len(live_companies)} have a live board, {len(existing)} checked before)", flush=True)

    found = 0
    done = 0
    results = dict(existing)

    def flush():
        json.dump(sorted(results.values(), key=lambda r: r["company"]), open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        jb.save_registry(registry)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(discover, c, existing.get(c["name"]), slug_probes): c for c in todo}
        for f in as_completed(futs):
            c = futs[f]
            try:
                rec = f.result()
            except Exception as e:  # noqa: BLE001
                print(f"  ! {c['name']}: {e}", flush=True)
                continue
            done += 1
            results[rec["company"]] = rec
            n_added = merge_into_registry(rec, registry)
            best = next((x for x in rec["candidates"] if x["confidence"] == "high"), None)
            if best:
                found += 1
                print(f"  ✓ {rec['company']}: {best['platform']}/{best['slug']} jobs={best['jobs_seen']} ({best['how']}; {best['reason']})", flush=True)
            elif rec["candidates"]:
                r0 = rec["candidates"][0]
                print(f"  ✗ {rec['company']}: {len(rec['candidates'])} rejected, e.g. {r0['platform']}/{r0['slug']} — {r0['reason']}", flush=True)
            if done % 25 == 0:
                print(f"  … {done}/{len(todo)} checked, {found} boards found", flush=True)
                flush()
    flush()
    with_board = len({r["company"] for r in registry if r.get("jobs_seen")})
    print(f"done: {done} checked, {found} boards found → registry {len(registry)} boards / {with_board} companies with jobs ({OUT.name} updated)")


if __name__ == "__main__":
    main()
