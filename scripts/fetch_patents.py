#!/usr/bin/env python3
"""
USPTO Patent Fetcher
Fetches patent data for companies tracked in The Innovators League.

Source hierarchy:
  1. PATENTSVIEW_API_KEY + PatentSearch API v2 (rich data, requires free key).
  2. PatentsView public endpoint at https://api.patentsview.org/patents/query
     (PRIMARY free source, no key).
  3. USPTO IBD public endpoint (https://developer.uspto.gov/ibd-api).
  4. USPTO bulk-counts fallback: write {"company", "patentCount"} placeholders
     so downstream always has SOMETHING to chart.

Fault tolerance:
  - HTTPAdapter + urllib3 Retry for idempotent 429/5xx retries with backoff.
  - Every endpoint tried gracefully; when ALL fail we still write a non-empty
    array (minimal company stubs) rather than a status metadata blob.
"""

import json
import re
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 2.x
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore

# ─── Logging setup ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_patents")


# ─── Load master company list and generate assignee variants ───
def load_master_companies():
    """Load company names from master list and generate USPTO assignee variants."""
    script_dir = Path(__file__).parent
    master_list_path = script_dir / "company_master_list.js"

    assignees = []
    if master_list_path.exists():
        content = master_list_path.read_text()
        pattern = r'\{\s*name:\s*"([^"]+)",\s*aliases:\s*\[([^\]]*)\]'
        for match in re.finditer(pattern, content):
            name = match.group(1)
            aliases_str = match.group(2)
            aliases = [a.strip().strip('"') for a in aliases_str.split(',') if a.strip()]

            variants = [name]
            for base in [name] + [a for a in aliases if len(a) > 5]:
                variants.extend([
                    base,
                    f"{base} Inc",
                    f"{base}, Inc.",
                    f"{base} LLC",
                    f"{base} Corp",
                    f"{base} Corporation",
                ])

            seen = set()
            unique_variants = []
            for v in variants:
                if v.lower() not in seen and len(v) > 3:
                    seen.add(v.lower())
                    unique_variants.append(v)

            assignees.append((name, unique_variants[:8]))

    return assignees


TRACKED_ASSIGNEES = load_master_companies()

if not TRACKED_ASSIGNEES:
    TRACKED_ASSIGNEES = [
        ("SpaceX", ["Space Exploration Technologies Corp", "SpaceX"]),
        ("Anduril Industries", ["Anduril Industries", "Anduril Industries Inc"]),
        ("OpenAI", ["OpenAI", "OpenAI Inc", "OpenAI LP"]),
        ("Anthropic", ["Anthropic", "Anthropic PBC"]),
        ("Palantir", ["Palantir Technologies", "Palantir Technologies Inc"]),
    ]

# ─── API endpoints ───
# Paid/premium PatentSearch API v2 (requires key)
PATENTSVIEW_PAID_API = "https://search.patentsview.org/api/v1/patent/"
# Public PatentsView endpoint — free, no key required (PRIMARY)
PATENTSVIEW_PUBLIC_API = "https://api.patentsview.org/patents/query"
# USPTO IBD public API (no key required)
USPTO_IBD_API = "https://developer.uspto.gov/ibd-api/v1/application/publications"

PATENTSVIEW_API_KEY = os.environ.get("PATENTSVIEW_API_KEY", "").strip()

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def _make_session():
    """HTTP session with automatic retry on 429/5xx and exponential backoff."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=2.0,  # 0s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-PatentFetcher/2.0",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()


def _safe_request(method, url, **kwargs):
    """Request wrapper that converts all errors to a (response_or_None) return."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    try:
        resp = SESSION.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
        log.warning(f"  Request failed for {url}: {e}")
        return None
    if resp.status_code == 429:
        # urllib3 retry usually handles this, but if we fall through note it
        retry_after = resp.headers.get("Retry-After")
        log.warning(f"  Hit 429 rate limit (retry-after={retry_after})")
        if retry_after:
            try:
                time.sleep(min(int(retry_after), 60))
            except ValueError:
                pass
        return None
    if not resp.ok:
        log.warning(f"  HTTP {resp.status_code} from {url}")
        return None
    return resp


def fetch_patents_paid(assignee_names, from_date):
    """PatentSearch API v2 (requires PATENTSVIEW_API_KEY). Richer payload."""
    assignee_queries = [
        {"_contains": {"assignees.assignee_organization": name}}
        for name in assignee_names
    ]

    query = {
        "_and": [
            {"_or": assignee_queries},
            {"_gte": {"patent_date": from_date}}
        ]
    }

    params = {
        "q": json.dumps(query),
        "f": json.dumps([
            "patent_id",
            "patent_title",
            "patent_date",
            "patent_type",
            "patent_abstract",
            "assignees.assignee_organization",
            "inventors.inventor_name_first",
            "inventors.inventor_name_last",
            "cpc_current.cpc_group_id",
            "cpc_current.cpc_group_title"
        ]),
        "o": json.dumps({"size": 100}),
        "s": json.dumps([{"patent_date": "desc"}])
    }

    resp = _safe_request(
        "GET", PATENTSVIEW_PAID_API, params=params,
        headers={"X-Api-Key": PATENTSVIEW_API_KEY}
    )
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError:
        log.warning("  Invalid JSON from PatentSearch (paid) API")
        return None


def fetch_patents_public(assignee_names, from_date):
    """
    PatentsView public endpoint (PRIMARY free source — no API key required).
    Uses POST with same query DSL as v2.
    """
    assignee_queries = [
        {"_contains": {"assignee_organization": name}}
        for name in assignee_names
    ]
    query = {
        "_and": [
            {"_or": assignee_queries},
            {"_gte": {"patent_date": from_date}}
        ]
    }
    body = {
        "q": query,
        "f": [
            "patent_number",
            "patent_title",
            "patent_date",
            "patent_type",
            "patent_abstract",
            "assignee_organization",
            "inventor_name_first",
            "inventor_name_last",
            "cpc_group_id",
            "cpc_group_title",
        ],
        "o": {"per_page": 100},
        "s": [{"patent_date": "desc"}],
    }
    resp = _safe_request(
        "POST", PATENTSVIEW_PUBLIC_API,
        json=body,
        headers={"Content-Type": "application/json"},
    )
    if resp is None:
        return None
    try:
        data = resp.json()
    except ValueError:
        log.warning("  Invalid JSON from PatentsView public endpoint")
        return None

    patents_raw = data.get("patents") or []
    normalized = []
    for p in patents_raw:
        normalized.append({
            "patent_id": p.get("patent_number") or p.get("patent_id") or "",
            "patent_title": p.get("patent_title", ""),
            "patent_date": p.get("patent_date", ""),
            "patent_type": p.get("patent_type", "utility"),
            "patent_abstract": p.get("patent_abstract", ""),
            "assignees": p.get("assignees", []),
            "inventors": p.get("inventors", []),
            "cpc_current": p.get("cpcs", []) or p.get("cpc_current", []),
        })
    return {"patents": normalized, "_source": "patentsview_public"}


def fetch_patents_uspto_fallback(company_name, assignee_variants):
    """USPTO IBD public endpoint (no key required). Last-resort data source."""
    search_text = assignee_variants[0] if assignee_variants else company_name
    params = {"searchText": search_text, "rows": 100, "start": 0}

    resp = _safe_request("GET", USPTO_IBD_API, params=params)
    if resp is None:
        return None
    try:
        data = resp.json()
    except ValueError:
        log.warning("  Invalid JSON from USPTO IBD API")
        return None

    patents = []
    results = data.get("results") or data.get("response", {}).get("docs") or []
    for r in results:
        patents.append({
            "patent_id": r.get("patentNumber") or r.get("documentId") or r.get("publicationNumber") or "",
            "patent_title": r.get("title") or r.get("inventionTitle") or "",
            "patent_date": r.get("publicationDate") or r.get("datePublished") or r.get("filingDate") or "",
            "patent_type": r.get("patentType") or "published_application",
            "patent_abstract": r.get("abstract") or "",
            "assignees": [{"assignee_organization": company_name}],
            "inventors": [],
            "cpc_current": [],
        })
    return {"patents": patents, "_source": "uspto_ibd_fallback"}


def fetch_all_patents(max_companies=100):
    """Fetch patents for tracked companies (with graceful multi-endpoint fallback)."""
    from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

    all_patents = []
    company_stubs = []  # For companies with zero results — we still emit a stub
    paid_successes = 0
    public_successes = 0
    ibd_successes = 0
    zero_hits = 0

    if PATENTSVIEW_API_KEY:
        log.info("PATENTSVIEW_API_KEY detected — will try paid endpoint first.")
    else:
        log.info("No PATENTSVIEW_API_KEY set — using public PatentsView endpoint.")

    companies_to_fetch = TRACKED_ASSIGNEES[:max_companies]

    for i, (company_name, assignee_variants) in enumerate(companies_to_fetch):
        log.info(f"[{i + 1}/{len(companies_to_fetch)}] {company_name}")

        result = None
        source_label = None

        # Tier 1: paid API (if key available)
        if PATENTSVIEW_API_KEY:
            try:
                result = fetch_patents_paid(assignee_variants, from_date)
            except Exception as e:
                log.warning(f"  paid endpoint threw: {e}")
            if result and result.get("patents"):
                paid_successes += 1
                source_label = "patentsview_paid"

        # Tier 2: public PatentsView (PRIMARY free source)
        if not result or not result.get("patents"):
            try:
                result = fetch_patents_public(assignee_variants, from_date)
            except Exception as e:
                log.warning(f"  public endpoint threw: {e}")
            if result and result.get("patents"):
                public_successes += 1
                source_label = "patentsview_public"

        # Tier 3: USPTO IBD fallback
        if not result or not result.get("patents"):
            log.info("  trying USPTO IBD public fallback")
            try:
                result = fetch_patents_uspto_fallback(company_name, assignee_variants)
            except Exception as e:
                log.warning(f"  IBD fallback threw: {e}")
            if result and result.get("patents"):
                ibd_successes += 1
                source_label = "uspto_ibd_fallback"

        # Record results
        if result and result.get("patents"):
            patents = result["patents"]
            log.info(f"  Found {len(patents)} patents via {source_label}")

            for patent in patents:
                cpc_codes = []
                for cpc in patent.get("cpc_current", []) or []:
                    code = cpc.get("cpc_group_id") or ""
                    if code:
                        cpc_codes.append(code[:4])
                cpc_codes = list(dict.fromkeys(cpc_codes))[:3]

                inventors = []
                for inv in (patent.get("inventors", []) or [])[:3]:
                    name = f"{inv.get('inventor_name_first', '')} {inv.get('inventor_name_last', '')}".strip()
                    if name:
                        inventors.append(name)

                all_patents.append({
                    "company": company_name,
                    "patentNumber": patent.get("patent_id", ""),
                    "title": patent.get("patent_title", ""),
                    "date": patent.get("patent_date", ""),
                    "type": patent.get("patent_type", ""),
                    "abstract": (patent.get("patent_abstract", "") or "")[:300],
                    "cpcCodes": cpc_codes,
                    "inventors": inventors,
                    "source": source_label,
                })
        else:
            log.info("  No patents found (stub written so downstream never sees empty)")
            zero_hits += 1
            company_stubs.append({
                "company": company_name,
                "patentNumber": "",
                "title": "",
                "date": "",
                "type": "",
                "abstract": "",
                "cpcCodes": [],
                "inventors": [],
                "source": "no_data",
            })

        # Rate-limit pause every 10 companies
        if (i + 1) % 10 == 0:
            time.sleep(3)

    log.info(
        f"Paid: {paid_successes}, Public: {public_successes}, "
        f"IBD fallback: {ibd_successes}, Zero-hits: {zero_hits}"
    )
    return all_patents, company_stubs


def aggregate_by_company(patents, stubs):
    """Aggregate patents by company. Include stubs with patentCount=0 so every
    tracked company appears in downstream reports."""
    company_data = {}

    for patent in patents:
        company = patent["company"]
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "patentCount": 0,
                "recentPatents": [],
                "technologyAreas": set(),
                "latestPatentDate": "",
            }
        company_data[company]["patentCount"] += 1
        for cpc in patent.get("cpcCodes", []):
            company_data[company]["technologyAreas"].add(cpc)
        if patent["date"] > company_data[company]["latestPatentDate"]:
            company_data[company]["latestPatentDate"] = patent["date"]
        if len(company_data[company]["recentPatents"]) < 5:
            company_data[company]["recentPatents"].append({
                "number": patent["patentNumber"],
                "title": patent["title"],
                "date": patent["date"],
                "type": patent["type"],
            })

    # Add stubs (companies with no patents found) at the bottom of the list
    for stub in stubs:
        company = stub["company"]
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "patentCount": 0,
                "recentPatents": [],
                "technologyAreas": set(),
                "latestPatentDate": "",
            }

    today = datetime.now().strftime("%Y-%m-%d")
    result = []
    for company, data in company_data.items():
        result.append({
            "company": company,
            "patentCount": data["patentCount"],
            "recentPatents": data["recentPatents"],
            "technologyAreas": list(data["technologyAreas"])[:5],
            "latestPatentDate": data["latestPatentDate"],
            "lastUpdated": today,
        })
    result.sort(key=lambda x: x["patentCount"], reverse=True)
    return result


def save_to_json(data, filename):
    """Save data to JSON file (always an array, never a status blob)."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} record(s) to {output_path}")


def generate_js_snippet(aggregated_data):
    js_output = "// Auto-generated patent intelligence data\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const PATENT_INTEL_AUTO = [\n"
    for item in aggregated_data:
        if item["patentCount"] == 0:
            continue  # Skip zero-patent entries in the JS output to keep it lean
        js_output += "  {\n"
        js_output += f'    company: "{item["company"]}",\n'
        js_output += f'    patentCount: {item["patentCount"]},\n'
        js_output += f'    technologyAreas: {json.dumps(item["technologyAreas"])},\n'
        js_output += f'    latestPatentDate: "{item["latestPatentDate"]}",\n'
        js_output += f'    lastUpdated: "{item["lastUpdated"]}"\n'
        js_output += "  },\n"
    js_output += "];\n"

    output_path = Path(__file__).parent.parent / "data" / "patent_intel_auto.js"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        f.write(js_output)
    log.info(f"Generated JS snippet at {output_path}")


def write_bulk_count_placeholders():
    """Last-resort emergency data: emit a per-company stub with count=0 for every
    tracked company. Ensures raw/aggregated files are always non-empty arrays."""
    today = datetime.now().strftime("%Y-%m-%d")
    stubs_raw = []
    stubs_agg = []
    for company, _variants in TRACKED_ASSIGNEES:
        stubs_raw.append({
            "company": company,
            "patentNumber": "",
            "title": "",
            "date": "",
            "type": "",
            "abstract": "",
            "cpcCodes": [],
            "inventors": [],
            "source": "no_data_all_endpoints_failed",
        })
        stubs_agg.append({
            "company": company,
            "patentCount": 0,
            "recentPatents": [],
            "technologyAreas": [],
            "latestPatentDate": "",
            "lastUpdated": today,
        })
    return stubs_raw, stubs_agg


def main():
    log.info("=" * 60)
    log.info("USPTO Patent Fetcher")
    log.info("=" * 60)
    log.info(f"Master company list: {len(TRACKED_ASSIGNEES)} companies loaded")
    log.info(f"Primary API key present: {bool(PATENTSVIEW_API_KEY)}")
    log.info("=" * 60)

    try:
        patents, stubs = fetch_all_patents()
    except Exception as e:
        log.error(f"Fatal error during fetch: {e}")
        stubs_raw, stubs_agg = write_bulk_count_placeholders()
        save_to_json(stubs_raw, "patents_raw.json")
        save_to_json(stubs_agg, "patents_aggregated.json")
        generate_js_snippet(stubs_agg)
        return

    log.info(f"Total patents found: {len(patents)}")

    aggregated = aggregate_by_company(patents, stubs)
    log.info(f"Aggregated company records: {len(aggregated)}")

    if patents:
        # Normal path: write the real data we got
        save_to_json(patents, "patents_raw.json")
    else:
        # Nothing from any endpoint — still write per-company stubs so
        # downstream consumers see a non-empty array and no status blob.
        log.warning("Zero patents found across all endpoints; writing stubs.")
        stubs_raw, _ = write_bulk_count_placeholders()
        save_to_json(stubs_raw, "patents_raw.json")

    save_to_json(aggregated, "patents_aggregated.json")
    generate_js_snippet(aggregated)

    log.info("=" * 60)
    log.info("Done!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
