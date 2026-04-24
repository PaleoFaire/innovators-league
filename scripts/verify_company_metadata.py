#!/usr/bin/env python3
"""
Company Metadata Verifier — the pipeline that catches rebrands, acquisitions,
IPO-status mismatches, and dead websites across the COMPANIES array.

Why this exists:
  All the other fetch_*.py scripts pull SIGNALS about companies (patents, gov
  contracts, news, funding filings). None of them VERIFY that the canonical
  record in data.js — name, fundingStage, website, founder, description —
  is still correct. When Amidon Heavy Industries rebranded to Standard Subsea
  in 2026, nothing caught it. This script does.

What it does:
  1. Website 301 check — for every company with a `website` field, HEAD the
     URL and note if it permanently redirects to a different host. That's a
     strong rebrand signal.
  2. Website liveness — if site returns 404/5xx, flag as potentially defunct.
  3. Acquisition-language scan — regex over description/insight for phrases
     like "acquired by X", "merger with X", "bought by X" — flag if
     fundingStage != "Acquired".
  4. IPO-status cross-check — for a maintained list of known-public tickers,
     verify fundingStage == "Public". Flag any mismatches.
  5. SPAC staleness — flag fundingStage == "SPAC" entries, since most SPAC
     deals have resolved (closed or collapsed) by 2026.
  6. Missing-website enrichment queue — list companies without a website so
     the next enrichment pass knows what to fill.

Output:
  data/metadata_verification.json — structured report with categories:
    rebrands[], acquisitions_missed[], ipo_mismatches[],
    spac_staleness[], dead_websites[], missing_websites[]

  Stephen gets a TL;DR at the top so he can act on P0 issues in < 60 seconds.

Run locally:
  python3 scripts/verify_company_metadata.py [--probe] [--limit N]
  --probe  actually hit the web (slow; ~5 req/sec). Without, only does
           desk-check scans (acquisition language, IPO list, SPAC).
  --limit  cap number of web probes (useful for CI cost control).

Re-run: weekly, wired into weekly-intelligence-sync.yml.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
OUT_PATH = ROOT / "data" / "metadata_verification.json"

USER_AGENT = (
    "InnovatorsLeague-MetadataVerifier/1.0 "
    "(+https://paleofaire.github.io/innovators-league)"
)

# ──────────────────────────────────────────────────────────────────────
# Known-public companies that MUST have fundingStage = "Public".
# Extend this list as companies IPO. Kept as a flat dict for quick lookup:
# {company_name: "exchange:TICKER"}.
# ──────────────────────────────────────────────────────────────────────
KNOWN_PUBLIC = {
    "Palantir":                    "NYSE: PLTR",
    "Intuitive Machines":          "NASDAQ: LUNR",
    "Rocket Lab":                  "NASDAQ: RKLB",
    "Joby Aviation":               "NYSE: JOBY",
    "Archer Aviation":             "NYSE: ACHR",
    "AST SpaceMobile":             "NASDAQ: ASTS",
    "BlackSky":                    "NYSE: BKSY",
    "Planet Labs":                 "NYSE: PL",
    "Spire Global":                "NYSE: SPIR",
    "Redwire":                     "NYSE: RDW",
    "Satellogic":                  "NASDAQ: SATL",
    "Sidus Space":                 "NASDAQ: SIDU",
    "Terran Orbital":              "NYSE: LLAP",  # acquired by Lockheed 2024; review
    "Virgin Galactic":             "NYSE: SPCE",
    "Lunar Outpost":               None,  # still private as of writing; sanity-check
    "Nuscale Power":               "NYSE: SMR",
    "Oklo":                        "NYSE: OKLO",
    "Centrus Energy":              "NYSE: LEU",
    "Lightning eMotors":           None,  # went private/defunct
    "Nano Nuclear Energy":         "NASDAQ: NNE",
    "Lilium":                      "NASDAQ: LILM",  # bankruptcy 2024; review
    "Eve Air Mobility":            "NYSE: EVEX",
    "QuantumScape":                "NYSE: QS",
    "Solid Power":                 "NASDAQ: SLDP",
    "IonQ":                        "NYSE: IONQ",
    "D-Wave":                      "NYSE: QBTS",
    "Rigetti Computing":           "NASDAQ: RGTI",
    "Quantum Computing Inc":       "NASDAQ: QUBT",
    "SentinelOne":                 "NYSE: S",
    "CrowdStrike":                 "NASDAQ: CRWD",
    "Hims & Hers":                 "NYSE: HIMS",
    "Recursion Pharmaceuticals":   "NASDAQ: RXRX",
    "Schrödinger":                 "NASDAQ: SDGR",
    "Symbotic":                    "NASDAQ: SYM",
    "Serve Robotics":              "NASDAQ: SERV",
    "Richtech Robotics":           "NASDAQ: RR",
    "Terra Drone":                 "TYO: 278A",
    "Horizon Quantum Computing":   "NASDAQ: HQ",  # dMY Squared SPAC closed 2026-03-19
}

# Phrases that suggest a company was acquired; we flag if fundingStage
# does NOT already contain one of the acquisition markers.
ACQ_PATTERNS = [
    r"\bacquired by\b",
    r"\bacquisition by\b",
    r"\bbought by\b",
    r"\bmerged with\b",
    r"\bpurchased by\b",
]
ACQ_STAGE_MARKERS = ["Acquired", "Subsidiary", "Defunct"]

# Phrases suggesting a company shut down — separate from acquisition.
DEFUNCT_PATTERNS = [
    r"\bshut down\b",
    r"\bceased operations\b",
    r"\bfiled for (chapter 7|bankruptcy)\b",
    r"\bwound down\b",
    r"\bdissolved\b",
]

# Don't bother probing these well-known CDNs / redirects where a 301 isn't
# a rebrand signal (eg. http→https upgrade, non-www→www).
REDIRECT_NOISE = {
    "www.example.com", "example.com",  # placeholder
}

# Domain-parking / broker services. If a company's website 301-redirects to
# one of these, they LOST the domain (didn't rebrand). Flag separately as
# "domain_lost" instead of "rebrand_suspect" — very different action.
PARKING_HOSTS = {
    "domaineasy.com", "www.domaineasy.com",
    "hugedomains.com", "www.hugedomains.com",
    "sedoparking.com", "www.sedoparking.com",
    "dan.com", "www.dan.com",
    "godaddy.com", "www.godaddy.com",
    "afternic.com", "www.afternic.com",
    "buydomains.com", "www.buydomains.com",
    "squadhelp.com", "www.squadhelp.com",
}


# ──────────────────────────────────────────────────────────────────────
# data.js parsing
# ──────────────────────────────────────────────────────────────────────

def parse_companies(src: str) -> list[dict[str, Any]]:
    """Extract the COMPANIES array from data.js. Brace-aware tokenizer so
    nested objects in insight/thesis notes don't break us."""
    s = src.find("const COMPANIES = [")
    if s < 0:
        raise RuntimeError("COMPANIES array not found in data.js")
    i = src.find("[", s)
    depth = 0
    in_str = False
    sc = None
    esc = False
    end = None
    for k in range(i, len(src)):
        c = src[k]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if in_str:
            if c == sc:
                in_str = False
            continue
        if c in "\"'":
            in_str = True
            sc = c
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = k
                break
    block = src[i + 1:end]

    # Walk top-level {…} objects inside the block.
    entries = []
    idx = 0
    n = len(block)
    d = 0
    in_str = False
    sc = None
    esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,":
            idx += 1
        if idx >= n:
            break
        if block[idx] != "{":
            idx += 1
            continue
        start = idx
        while idx < n:
            c = block[idx]
            if esc:
                esc = False
                idx += 1
                continue
            if c == "\\" and in_str:
                esc = True
                idx += 1
                continue
            if in_str:
                if c == sc:
                    in_str = False
                idx += 1
                continue
            if c in "\"'":
                in_str = True
                sc = c
                idx += 1
                continue
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    idx += 1
                    entries.append(block[start:idx])
                    break
            idx += 1
    return [_entry_to_dict(e) for e in entries]


def _entry_to_dict(entry: str) -> dict[str, Any]:
    """Pull out the fields we care about via regex. Good enough for a
    verification pass — we don't need a full JS parser."""
    out = {"_raw": entry}
    for field in ("name", "sector", "description", "insight", "founder",
                  "location", "fundingStage", "totalRaised", "valuation",
                  "website", "ticker", "acquiredBy"):
        m = re.search(rf'\b{field}:\s*"((?:[^"\\]|\\.)*)"', entry)
        if m:
            out[field] = m.group(1)
    m = re.search(r"\bfounded:\s*(\d+)", entry)
    if m:
        out["founded"] = int(m.group(1))
    # formerNames: array of strings, rare.
    m = re.search(r"formerNames:\s*\[([^\]]*)\]", entry)
    if m:
        out["formerNames"] = re.findall(r'"([^"]+)"', m.group(1))
    return out


# ──────────────────────────────────────────────────────────────────────
# Desk-check scans (fast; no network)
# ──────────────────────────────────────────────────────────────────────

def scan_acquisition_language(companies: list[dict]) -> list[dict]:
    flagged = []
    for c in companies:
        text = " ".join(
            c.get(f, "") for f in ("description", "insight")
        ).lower()
        stage = c.get("fundingStage", "").lower()
        # Skip if stage already correctly reflects acquisition/merger, or
        # if the company is already Public (merger language is expected
        # there, e.g. Ouster-Velodyne).
        if any(m.lower() in stage for m in ACQ_STAGE_MARKERS):
            continue
        if "public" in stage:
            continue
        hit = next(
            (p for p in ACQ_PATTERNS if re.search(p, text, re.I)), None
        )
        if hit:
            flagged.append({
                "name": c.get("name"),
                "current_stage": stage,
                "pattern_hit": hit,
                "excerpt": _excerpt(text, hit, 120),
                "action": f'Change fundingStage to "Acquired" and add acquiredBy field',
            })
    return flagged


def scan_defunct_language(companies: list[dict]) -> list[dict]:
    flagged = []
    for c in companies:
        text = " ".join(
            c.get(f, "") for f in ("description", "insight")
        ).lower()
        stage = c.get("fundingStage", "")
        if "defunct" in stage.lower():
            continue
        hit = next(
            (p for p in DEFUNCT_PATTERNS if re.search(p, text, re.I)), None
        )
        if hit:
            flagged.append({
                "name": c.get("name"),
                "current_stage": stage,
                "pattern_hit": hit,
                "excerpt": _excerpt(text, hit, 120),
                "action": 'Change fundingStage to "Defunct" and preserve historical record',
            })
    return flagged


def scan_ipo_mismatches(companies: list[dict]) -> list[dict]:
    flagged = []
    by_name = {c.get("name"): c for c in companies}
    for pub_name, ticker in KNOWN_PUBLIC.items():
        # ticker=None = still private / defunct; don't flag, just a note.
        if ticker is None:
            continue
        if pub_name not in by_name:
            continue
        c = by_name[pub_name]
        stage = c.get("fundingStage", "")
        if "public" not in stage.lower():
            flagged.append({
                "name": pub_name,
                "current_stage": stage,
                "expected_stage": "Public",
                "ticker": ticker,
                "action": f'Update fundingStage to "Public" and set ticker to "{ticker}"',
            })
    return flagged


def scan_spac_staleness(companies: list[dict]) -> list[dict]:
    """Most SPAC deals from the 2021-23 wave have either closed (→ Public)
    or collapsed (→ Defunct / still-private) by 2026. Flag all SPAC-stage
    entries for manual review."""
    flagged = []
    for c in companies:
        stage = c.get("fundingStage", "")
        if stage == "SPAC":
            flagged.append({
                "name": c.get("name"),
                "current_stage": stage,
                "action": "SPAC is transitional. Verify current status — did the merger close (→ Public) or collapse (→ Late Stage / Defunct)?",
            })
    return flagged


def scan_missing_websites(companies: list[dict]) -> list[dict]:
    missing = []
    for c in companies:
        w = c.get("website", "")
        if not w:
            missing.append({
                "name": c.get("name"),
                "sector": c.get("sector"),
                "founder": c.get("founder"),
            })
    return missing


def scan_founding_stage_vocabulary(companies: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for c in companies:
        counts[c.get("fundingStage", "")] += 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


# ──────────────────────────────────────────────────────────────────────
# Network probes (slow; only when --probe)
# ──────────────────────────────────────────────────────────────────────

def probe_website(url: str, timeout: int = 8) -> dict[str, Any]:
    """HEAD the URL and return status + final URL. Returns a dict with
    whichever signals we can collect — this script never raises."""
    result = {
        "url": url, "status": None, "final_url": None,
        "redirected": False, "rebrand_suspect": False,
        "domain_lost": False, "error": None,
    }
    try:
        r = requests.head(
            url, timeout=timeout, allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        result["status"] = r.status_code
        result["final_url"] = r.url
        if r.url.rstrip("/") != url.rstrip("/"):
            result["redirected"] = True
            # If the host changed, this is a strong rebrand signal —
            # UNLESS the new host is a domain-parking / broker service,
            # in which case the company just lost the domain (still exists).
            a = urlparse(url).netloc.replace("www.", "").lower()
            b_full = urlparse(r.url).netloc.lower()
            b = b_full.replace("www.", "")
            if a and b and a != b and b not in REDIRECT_NOISE:
                if b_full in PARKING_HOSTS or b in PARKING_HOSTS:
                    result["domain_lost"] = True
                else:
                    result["rebrand_suspect"] = True
    except requests.RequestException as e:
        result["error"] = type(e).__name__
    return result


def probe_websites(companies: list[dict], limit: int | None) -> list[dict]:
    findings = []
    count = 0
    for c in companies:
        url = c.get("website", "")
        if not url:
            continue
        if limit is not None and count >= limit:
            break
        count += 1
        r = probe_website(url)
        if r["rebrand_suspect"]:
            findings.append({
                "kind": "rebrand_suspect",
                "name": c.get("name"),
                "old_url": url,
                "new_url": r["final_url"],
                "action": f"Website 301-redirects to new domain. Likely rebrand. Investigate and update data.js.",
            })
        elif r["domain_lost"]:
            findings.append({
                "kind": "domain_lost",
                "name": c.get("name"),
                "old_url": url,
                "parked_at": r["final_url"],
                "action": "Old domain went to a parking/broker service. Company may have lost the domain. Search for their current website and update.",
            })
        elif r["status"] and r["status"] >= 400:
            findings.append({
                "kind": "dead_website",
                "name": c.get("name"),
                "url": url,
                "status": r["status"],
                "action": "Website returns error code. Verify company is still operating.",
            })
        elif r["error"]:
            findings.append({
                "kind": "unreachable_website",
                "name": c.get("name"),
                "url": url,
                "error": r["error"],
                "action": "Website unreachable (network or SSL error). Re-probe next week.",
            })
        time.sleep(0.2)  # be gentle
    return findings


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _excerpt(text: str, pattern: str, span: int) -> str:
    m = re.search(pattern, text, re.I)
    if not m:
        return text[:span]
    s = max(0, m.start() - span // 2)
    e = min(len(text), m.end() + span // 2)
    return ("…" if s else "") + text[s:e] + ("…" if e < len(text) else "")


# ──────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true",
                    help="Also HEAD every website (slow).")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap number of web probes (for CI cost control).")
    args = ap.parse_args()

    src = DATA_JS.read_text(encoding="utf-8")
    companies = parse_companies(src)
    print(f"Parsed {len(companies)} companies from data.js")

    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "company_count": len(companies),
        "checks": {},
    }

    # Desk-checks (always on).
    report["checks"]["acquisition_language"] = scan_acquisition_language(companies)
    report["checks"]["defunct_language"] = scan_defunct_language(companies)
    report["checks"]["ipo_mismatches"] = scan_ipo_mismatches(companies)
    report["checks"]["spac_staleness"] = scan_spac_staleness(companies)
    report["checks"]["missing_websites"] = scan_missing_websites(companies)
    report["checks"]["stage_vocabulary"] = scan_founding_stage_vocabulary(companies)

    # Network probes (optional).
    if args.probe:
        n_with_site = sum(1 for c in companies if c.get("website"))
        print(f"Probing {n_with_site} websites"
              + (f" (capped at {args.limit})" if args.limit else "")
              + "...")
        probe_findings = probe_websites(companies, args.limit)
        report["checks"]["web_probes"] = probe_findings
    else:
        report["checks"]["web_probes"] = []
        print("Skipping web probes (pass --probe to enable).")

    # TL;DR summary block.
    p0_count = (
        len(report["checks"]["ipo_mismatches"])
        + len(report["checks"]["acquisition_language"])
        + sum(1 for f in report["checks"]["web_probes"]
              if f.get("kind") == "rebrand_suspect")
    )
    p1_count = (
        len(report["checks"]["spac_staleness"])
        + len(report["checks"]["defunct_language"])
        + sum(1 for f in report["checks"]["web_probes"]
              if f.get("kind") == "dead_website")
    )
    report["summary"] = {
        "p0_issues": p0_count,
        "p1_issues": p1_count,
        "missing_websites": len(report["checks"]["missing_websites"]),
        "distinct_stages": len(report["checks"]["stage_vocabulary"]),
    }

    # Emit.
    OUT_PATH.parent.mkdir(exist_ok=True, parents=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print()
    print("="*72)
    print(f"TL;DR  →  P0: {p0_count}   P1: {p1_count}   "
          f"Missing websites: {report['summary']['missing_websites']}")
    print("="*72)

    # Human-readable console output for the top findings.
    if report["checks"]["ipo_mismatches"]:
        print("\nIPO mismatches (P0):")
        for f in report["checks"]["ipo_mismatches"]:
            print(f"  {f['name']:30s}  stage={f['current_stage']:15s}  "
                  f"expected=Public ({f['ticker']})")
    if report["checks"]["acquisition_language"]:
        print("\nAcquisition language (P0):")
        for f in report["checks"]["acquisition_language"][:15]:
            print(f"  {f['name']:30s}  stage={f['current_stage']:15s}  "
                  f"hit={f['pattern_hit']}")
    rebrand = [f for f in report["checks"]["web_probes"]
               if f.get("kind") == "rebrand_suspect"]
    if rebrand:
        print("\nRebrand suspects (P0):")
        for f in rebrand:
            print(f"  {f['name']:30s}  {f['old_url']} → {f['new_url']}")
    spac = report["checks"]["spac_staleness"]
    if spac:
        print(f"\nSPAC entries to re-verify (P1 — {len(spac)}):")
        for f in spac[:10]:
            print(f"  {f['name']}")

    print(f"\n→ wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
