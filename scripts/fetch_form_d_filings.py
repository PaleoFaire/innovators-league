#!/usr/bin/env python3
"""
Form D + SAFE / Exempt-Securities Filings Fetcher
─────────────────────────────────────────────────────────────────────────
Every private funding round > $5K in the US triggers an SEC Form D
filing within 15 days of first sale. Form D discloses:

  • Issuer name + address
  • Offering amount (total + sold to date)
  • Exemption claimed (Rule 506(b), 506(c), Reg CF, Reg A+, …)
  • Date of first sale
  • Executive officers

For frontier-tech specifically, Form D is the *leading indicator* for
funding rounds — it hits EDGAR weeks before any press release. Scraping
these for companies in our COMPANIES array gives us "raising now but not
announced yet" signal that nobody else systematically tracks.

SAFE (Simple Agreement for Future Equity) and convertible-note rounds
are filed under the same Form D regime. The "type of securities"
disclosure fields tell us whether it's equity, debt, or option/warrant.

Source: SEC EDGAR full-text search (no auth needed; rate-limited to
10 req/sec; we use 0.2s throttle to stay polite).

Output:
  data/form_d_filings_raw.json    — every Form D from last 30 days
  data/form_d_filings_auto.json   — filings matched to COMPANIES
  data/form_d_filings_auto.js     — browser-ready global FORM_D_FILINGS

Cadence: daily via comprehensive-data-sync workflow.
"""

import json
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_JS = ROOT / "data.js"

RAW_OUT  = DATA_DIR / "form_d_filings_raw.json"
AUTO_OUT = DATA_DIR / "form_d_filings_auto.json"
JS_OUT   = DATA_DIR / "form_d_filings_auto.js"

SEC_SEARCH = "https://efts.sec.gov/LATEST/search-index"
SEC_ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"
HEADERS = {
    "User-Agent": "InnovatorsLeague/1.0 contact@innovatorsleague.com",
    "Accept": "application/json",
}

# Days of history to scan. 60d is enough to cover the 15-day filing
# window plus two weeks of late filings / amendments.
LOOKBACK_DAYS = 60


def parse_companies_from_data_js():
    """Read COMPANIES names from data.js — we only surface Form D filings
    for issuers we actually track."""
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    if start < 0:
        return set()
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i + 1:end] if end else ""
    names = set()
    for m in re.finditer(r'\bname:\s*"((?:[^"\\]|\\.)+)"', block):
        names.add(m.group(1))
    return names


def search_form_d(days=LOOKBACK_DAYS):
    """SEC EDGAR full-text search for every Form D within `days`.
    Returns list of dicts with the raw search-result shape."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "forms": "D",
        "dateRange": "custom",
        "startdt": start.strftime("%Y-%m-%d"),
        "enddt":   end.strftime("%Y-%m-%d"),
    }
    out = []
    # EDGAR returns paginated results; walk up to 20 pages (2000 rows)
    for page in range(20):
        params["from"] = page * 100
        try:
            r = requests.get(SEC_SEARCH, params=params, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                print(f"  Form D search HTTP {r.status_code} — stopping pagination")
                break
            data = r.json()
        except Exception as e:
            print(f"  Form D search failed: {e}")
            break
        hits = (((data.get("hits") or {}).get("hits")) or [])
        if not hits:
            break
        out.extend(hits)
        if len(hits) < 100:
            break
        time.sleep(0.2)
    print(f"  EDGAR returned {len(out)} Form D filings in last {days} days")
    return out


def _first(value, default=""):
    """Normalize EDGAR search result fields which may be str or list."""
    if isinstance(value, list):
        return value[0] if value else default
    return value or default


def build_record(hit, tracked_names):
    """Turn an EDGAR search hit into a richer, UI-friendly row.
    Returns None for filings we can't match to a tracked company.

    EDGAR returns results at the top level (not under `_source`) in the
    newer JSON API, e.g.
      {"display_names": ["Anduril Industries, Inc. (CIK 0001813756)"],
       "ciks": ["0001813756"], "adsh": "0001193125-26-...", …}
    """
    # Support both the old `_source`-wrapped and new flat shape
    src = hit.get("_source", hit)
    display_names = src.get("display_names") or []

    # Tracked names normalized once for faster matching
    tracked_lc = {n.lower(): n for n in tracked_names}
    tracked_alnum = {re.sub(r"[^a-z0-9]", "", n.lower()): n for n in tracked_names}

    matched = None
    raw_issuer = None
    for display in display_names:
        # Accept either "Foo, Inc. (0001234567) (Issuer)" or
        # "Foo, Inc. (CIK 0001234567)" or "Foo, Inc.  (CIK 0001234567)"
        m = re.match(r"^(.+?)\s*\((?:CIK\s*)?\d+\)", display)
        if not m:
            continue
        name = m.group(1).strip().rstrip(",.;")
        if not raw_issuer:
            raw_issuer = name

        # Drop common legal suffixes for matching
        name_root = re.sub(r"\s+(Inc\.?|LLC|Corp\.?|Corporation|Ltd\.?|Co\.?|"
                           r"Holdings|Technologies|Technology|Industries|"
                           r"Group|Company|Systems|Labs?|LP|L\.P\.?|Partners?)$",
                           "", name, flags=re.I).strip()
        name_alnum = re.sub(r"[^a-z0-9]", "", name_root.lower())

        # Try exact → prefix → alnum match (handles "Anduril Industries, Inc."
        # → "Anduril Industries", and "Anduril-Industries" variations).
        tracked = tracked_lc.get(name_root.lower()) \
               or next((v for k, v in tracked_lc.items()
                        if name_root.lower().startswith(k + " ")
                        or name_root.lower() == k), None) \
               or tracked_alnum.get(name_alnum)
        if tracked:
            matched = tracked
            break

    if not matched:
        return None

    # Accession number → build document URL
    adsh = src.get("adsh") or hit.get("_id", "").replace(":", "")
    adsh_clean = adsh  # already has dashes in the right places
    cik_raw = _first(src.get("ciks"), "")
    cik = cik_raw.lstrip("0")

    # Canonical filing index URL
    filing_url = (f"https://www.sec.gov/cgi-bin/browse-edgar?"
                  f"action=getcompany&CIK={cik_raw}&type=D&dateb=&owner=include&count=10"
                  if cik_raw else "https://www.sec.gov/edgar/search/")

    file_date = _first(src.get("file_date"), "")

    return {
        "company":         matched,
        "issuer_name":     raw_issuer or matched,
        "form":            _first(src.get("forms"), "D"),
        "filed_date":      file_date,
        "cik":             cik,
        "accession":       adsh_clean,
        "filing_url":      filing_url,
        "adsh_raw":        adsh,
    }


def enrich_with_offering_details(rows):
    """Download the Form D XML for each match and extract the dollar
    amount + securities type. One HTTP request per filing; we throttle."""
    for row in rows:
        adsh = row["accession"].replace("-", "")
        cik = row["cik"]
        if not cik or not adsh:
            continue
        # Form D XML is at /Archives/edgar/data/<cik>/<adsh>/primary_doc.xml
        xml_url = f"{SEC_ARCHIVE_BASE}/{cik}/{adsh}/primary_doc.xml"
        try:
            r = requests.get(xml_url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                continue
            body = r.text
        except Exception:
            continue

        # Parse key fields via regex (full XML parse is overkill here)
        def grab(tag):
            m = re.search(rf"<{tag}>([^<]*)</{tag}>", body)
            return m.group(1).strip() if m else ""

        total = grab("totalOfferingAmount")
        sold  = grab("totalAmountSold")
        remaining = grab("totalRemaining")
        first_sale = grab("dateOfFirstSale")
        sec_type = []
        for m in re.finditer(r"<isEquityType>(true|false)</isEquityType>", body):
            sec_type.append("Equity" if m.group(1) == "true" else None)
        for m in re.finditer(r"<isDebtType>(true|false)</isDebtType>", body):
            if m.group(1) == "true":
                sec_type.append("Debt")
        # Fallback: look for <securityType> tag
        for m in re.finditer(r"<securityType>([^<]+)</securityType>", body):
            sec_type.append(m.group(1))
        sec_type = list({s for s in sec_type if s})  # dedupe, drop None

        # Exemption claimed
        exemption = grab("federalExemptionsExclusions") or grab("federalExemption")
        if not exemption:
            # Try Item 6 styled tag
            m = re.search(r"<federalExemptionsExclusions>.*?<item>([^<]+)</item>",
                          body, re.DOTALL)
            exemption = m.group(1).strip() if m else ""

        row["offering_amount"] = total
        row["amount_sold"]     = sold
        row["amount_remaining"] = remaining
        row["securities_type"] = ", ".join(sec_type) if sec_type else ""
        row["exemption"]       = exemption
        row["first_sale_date"] = first_sale

        # Heuristic: flag SAFEs (usually filed as Equity + small notation in
        # "description of business"). Our regex here is a best-effort guess.
        description = grab("descriptionOfBusiness") or ""
        row["is_safe"] = bool(re.search(r"\b(safe|simple agreement)\b",
                                        description, re.I))
        time.sleep(0.12)  # stay ≤ 10 req/sec per SEC guideline


def main():
    print("=" * 68)
    print("Form D / SAFE Filings Fetcher")
    print(f"Lookback: {LOOKBACK_DAYS} days")
    print("=" * 68)

    tracked = parse_companies_from_data_js()
    print(f"Loaded {len(tracked)} tracked companies")

    hits = search_form_d(days=LOOKBACK_DAYS)
    # New EDGAR API returns the source fields flat; old one wrapped them in `_source`.
    RAW_OUT.write_text(json.dumps([h.get("_source", h) for h in hits], indent=2))
    print(f"Wrote {RAW_OUT.name} ({len(hits)} raw filings)")

    # Match to tracked companies
    matched = [build_record(h, tracked) for h in hits]
    matched = [m for m in matched if m]
    # Dedupe by accession number
    seen = set(); dedup = []
    for m in matched:
        if m["accession"] in seen: continue
        seen.add(m["accession"])
        dedup.append(m)
    matched = dedup
    print(f"Matched to tracked companies: {len(matched)}")

    # Enrich with offering details
    print("Fetching filing XMLs for dollar-amount enrichment...")
    enrich_with_offering_details(matched)

    # Sort by filing date desc
    matched.sort(key=lambda r: r.get("filed_date", ""), reverse=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "SEC EDGAR Form D / Rule 506 exempt offerings",
        "lookback_days": LOOKBACK_DAYS,
        "total_filings": len(matched),
        "filings": matched,
    }
    AUTO_OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {AUTO_OUT.name} ({len(matched)} enriched filings)")

    # Emit browser-ready auto.js
    header = (
        f"// Auto-generated Form D + SAFE exempt-offering filings\n"
        f"// Source: SEC EDGAR (public)\n"
        f"// Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"// Total: {len(matched)} filings across {len({m['company'] for m in matched})} companies\n"
    )
    body = f"const FORM_D_FILINGS = {json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    JS_OUT.write_text(header + body)
    print(f"Wrote {JS_OUT.name}")

    if matched[:5]:
        print("\nMost recent Form D filings:")
        for m in matched[:5]:
            amt = m.get("offering_amount") or "—"
            print(f"  {m['filed_date'][:10]}  {m['company']:30s}  ${amt:<15s}  {m.get('securities_type') or '—'}")


if __name__ == "__main__":
    main()
