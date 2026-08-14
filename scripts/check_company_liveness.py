#!/usr/bin/env python3
"""
Liveness Check
─────────────────────────────────────────────────────────────────────────
Finds companies that have quietly died, been acquired, or been absorbed.

Why
───
On 2026-08-14 only 7 of 1,143 companies carried a status other than active or
ipo — 4 acquired, 2 zombie, 1 dead. No portfolio of 1,100 venture-backed
frontier startups has a 0.6% mortality rate. The status field was simply never
verified for most records, and the 169 imported in the buildlist sweep all
defaulted to "active".

A dead company leaves fingerprints on its own domain, which is the cheapest
reliable signal available:

  gone        DNS no longer resolves, or the host refuses connections
  parked      a registrar / for-sale holding page
  acquired    redirects to a DIFFERENT company's domain, or the page says
              "has been acquired by" / "is now part of"
  winding_down the page says "shutting down", "ceased operations", "wind-down"

None of these are conclusive on their own — a startup can rebrand, move domain,
or sit behind Cloudflare. So this script CLASSIFIES and reports; it never edits
data.js. Each finding needs a human to confirm before a status changes, and the
report records exactly what was seen.

Output
──────
  data/liveness_report.json   every company, verdict, evidence

Usage
─────
  python3 scripts/check_company_liveness.py
  python3 scripts/check_company_liveness.py --limit 100 --workers 16
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
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
REPORT = ROOT / "data" / "liveness_report.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 10

PARKED = re.compile(
    r"(domain (?:is |may be )?for sale|buy this domain|hugedomains|sedo\.com|"
    r"dan\.com|afternic|this domain is parked|parked (?:free )?(?:by|at)|"
    r"expired domain|renew (?:this|your) domain)", re.I)

ACQUIRED = re.compile(
    r"(has been acquired by|was acquired by|is now part of|joins? forces with|"
    r"acquired by [A-Z][\w&.\- ]{2,40}|we(?:'| a)re now [A-Z][\w&.\- ]{2,40}|"
    r"is now known as|has joined [A-Z][\w&.\- ]{2,40})", re.I)

DEAD = re.compile(
    r"(ceased operations|shutting down|shut down our|wind(?:ing)?[- ]down|"
    r"we are closing|has closed its doors|no longer in (?:business|operation)|"
    r"discontinued operations|assignment for the benefit of creditors|"
    r"chapter (?:7|11) bankruptcy)", re.I)


def host(u: str) -> str:
    try:
        return (urlparse(u).netloc or "").lower().replace("www.", "")
    except ValueError:
        return ""


def check(c: dict) -> dict:
    url = c["w"]
    out = {"company": c["n"], "url": url, "status_in_db": c["s"], "verdict": None,
           "evidence": ""}
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                         headers={"User-Agent": UA})
    except requests.exceptions.SSLError as e:
        out["verdict"] = "tls_error"; out["evidence"] = str(e)[:120]; return out
    except requests.exceptions.ConnectionError:
        out["verdict"] = "gone"; out["evidence"] = "DNS/connection failed"; return out
    except requests.RequestException as e:
        out["verdict"] = "unreachable"; out["evidence"] = type(e).__name__; return out

    if r.status_code >= 500:
        out["verdict"] = "server_error"; out["evidence"] = f"http {r.status_code}"; return out
    if r.status_code == 404:
        out["verdict"] = "not_found"; out["evidence"] = "http 404"; return out
    if r.status_code != 200:
        out["verdict"] = "http_" + str(r.status_code); out["evidence"] = f"http {r.status_code}"
        return out

    html = r.text or ""
    text = re.sub(r"<[^>]+>", " ", html[:80000])
    text = re.sub(r"\s+", " ", text)

    if PARKED.search(html[:6000]):
        out["verdict"] = "parked"
        m = PARKED.search(html[:6000]); out["evidence"] = m.group(0)[:100]
        return out

    # Redirected off its own domain -> often an acquisition
    if host(r.url) and host(url) and host(r.url) != host(url):
        out["verdict"] = "redirected"
        out["evidence"] = f"{host(url)} -> {host(r.url)}"
        return out

    m = DEAD.search(text)
    if m:
        i = m.start()
        out["verdict"] = "winding_down"; out["evidence"] = text[max(0, i-90):i+110]; return out
    m = ACQUIRED.search(text)
    if m:
        i = m.start()
        out["verdict"] = "acquired_language"; out["evidence"] = text[max(0, i-90):i+110]; return out

    if len(text.strip()) < 250:
        out["verdict"] = "empty_page"; out["evidence"] = text.strip()[:100]; return out

    out["verdict"] = "live"
    return out


def load() -> list[dict]:
    js = ('const fs=require("fs"),vm=require("vm");const s={};vm.createContext(s);'
          'vm.runInContext(fs.readFileSync(process.argv[1],"utf8")'
          '+";globalThis.__n=COMPANIES.filter(c=>c.website).map(c=>({n:c.name,'
          'w:c.website,s:c.status||\'\'}));",s);console.log(JSON.stringify(s.__n));')
    return json.loads(subprocess.run(["node", "-e", js, str(DATA_JS)],
                                     capture_output=True, text=True, check=True).stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()

    cos = load()
    if args.limit:
        cos = cos[:args.limit]
    print(f"checking {len(cos)} companies with a website")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(check, cos), 1):
            results.append(res)
            if res["verdict"] != "live":
                print(f"  [{i:>4}] {res['verdict']:<18}{res['company'][:30]:<31}"
                      f"{res['evidence'][:60]}", flush=True)

    by = {}
    for r in results:
        by.setdefault(r["verdict"], []).append(r)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(),
         "checked": len(results),
         "summary": {k: len(v) for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))},
         "results": results}, indent=2))

    print("\nsummary:")
    for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(v):>5}  {k}")
    print(f"\nwrote {REPORT}")
    print("Nothing was edited — each non-live verdict needs a human to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
