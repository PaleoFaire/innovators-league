#!/usr/bin/env python3
"""
USPTO PatentsView Patent Fetcher
Fetches patent data for companies tracked in The Innovators League.

Primary source:  PatentSearch API v2 (search.patentsview.org) - API key required
Fallback source: USPTO IBD public endpoint (developer.uspto.gov) - no key required

Get a PatentsView API key at:
https://patentsview-support.atlassian.net/servicedesk/customer/portal/1
"""

import json
import requests
import re
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

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
PATENTSVIEW_API = "https://search.patentsview.org/api/v1/patent/"
PATENTSVIEW_API_KEY = os.environ.get("PATENTSVIEW_API_KEY", "")

# USPTO IBD public API (no key required)
USPTO_IBD_API = "https://developer.uspto.gov/ibd-api/v1/application/publications"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def _request_with_retry(method, url, **kwargs):
    """HTTP request wrapper with exponential backoff retries."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code in (429, 503):
                backoff = 2 ** attempt * 5
                log.warning(f"  HTTP {resp.status_code} — backing off {backoff}s")
                time.sleep(backoff)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            log.warning(f"  Timeout on attempt {attempt + 1}/{MAX_RETRIES}")
        except requests.exceptions.RequestException as e:
            log.warning(f"  Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    return None


def fetch_patents_for_assignee(assignee_names, from_date=None):
    """Fetch patents for a specific assignee using PatentSearch API v2."""
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

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

    headers = {}
    if PATENTSVIEW_API_KEY:
        headers["X-Api-Key"] = PATENTSVIEW_API_KEY

    resp = _request_with_retry("GET", PATENTSVIEW_API, params=params, headers=headers)
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError:
        log.warning("  Invalid JSON from PatentsView API")
        return None


def fetch_patents_uspto_fallback(company_name, assignee_variants):
    """
    Fallback: Query USPTO IBD public endpoint (no API key required).
    This endpoint returns published patent applications containing a search term.
    """
    search_text = assignee_variants[0] if assignee_variants else company_name

    params = {
        "searchText": search_text,
        "rows": 100,
        "start": 0,
    }

    resp = _request_with_retry("GET", USPTO_IBD_API, params=params)
    if resp is None:
        return None
    try:
        data = resp.json()
    except ValueError:
        log.warning("  Invalid JSON from USPTO IBD API")
        return None

    # Normalize USPTO IBD response shape into what our aggregator expects
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
    """Fetch patents for tracked companies (with rate limiting)."""
    all_patents = []
    fallback_attempts = 0
    fallback_successes = 0
    primary_successes = 0

    if not PATENTSVIEW_API_KEY:
        log.warning("No PATENTSVIEW_API_KEY set. PatentSearch API v2 requires a key.")
        log.warning("Get a free key at: https://patentsview-support.atlassian.net/servicedesk/customer/portal/1")
        log.warning("Set it as: export PATENTSVIEW_API_KEY=your_key_here")
        log.warning("Or add it as a GitHub Actions secret.")
        log.warning("Falling back to USPTO IBD public endpoint (no key required).")

    companies_to_fetch = TRACKED_ASSIGNEES[:max_companies]

    for i, (company_name, assignee_variants) in enumerate(companies_to_fetch):
        log.info(f"[{i + 1}/{len(companies_to_fetch)}] Fetching patents for: {company_name}")

        result = None
        if PATENTSVIEW_API_KEY:
            result = fetch_patents_for_assignee(assignee_variants)
            if result and result.get("patents"):
                primary_successes += 1

        if not result or not result.get("patents"):
            fallback_attempts += 1
            log.info("  trying USPTO IBD public fallback")
            result = fetch_patents_uspto_fallback(company_name, assignee_variants)
            if result and result.get("patents"):
                fallback_successes += 1

        if (i + 1) % 10 == 0:
            log.info("  (pausing 15s for rate limiting)")
            time.sleep(15)

        if result and "patents" in result and result["patents"]:
            patents = result["patents"]
            log.info(f"  Found {len(patents)} patents")

            for patent in patents:
                cpc_codes = []
                if patent.get("cpc_current"):
                    cpc_codes = list(set([
                        cpc.get("cpc_group_id", "")[:4]
                        for cpc in patent["cpc_current"]
                        if cpc.get("cpc_group_id")
                    ]))[:3]

                inventors = []
                if patent.get("inventors"):
                    inventors = [
                        f"{inv.get('inventor_name_first', '')} {inv.get('inventor_name_last', '')}".strip()
                        for inv in patent["inventors"][:3]
                    ]

                patent_data = {
                    "company": company_name,
                    "patentNumber": patent.get("patent_id", ""),
                    "title": patent.get("patent_title", ""),
                    "date": patent.get("patent_date", ""),
                    "type": patent.get("patent_type", ""),
                    "abstract": (patent.get("patent_abstract", "") or "")[:300],
                    "cpcCodes": cpc_codes,
                    "inventors": inventors
                }
                all_patents.append(patent_data)
        else:
            log.info("  No patents found")

    log.info(
        f"Primary API successes: {primary_successes}, "
        f"fallback attempts: {fallback_attempts}, "
        f"fallback successes: {fallback_successes}"
    )
    return all_patents


def aggregate_by_company(patents):
    """Aggregate patents by company for the PATENT_INTEL format."""
    company_data = {}

    for patent in patents:
        company = patent["company"]
        if company not in company_data:
            company_data[company] = {
                "company": company,
                "patentCount": 0,
                "recentPatents": [],
                "technologyAreas": set(),
                "latestPatentDate": ""
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
                "type": patent["type"]
            })

    result = []
    for company, data in company_data.items():
        if data["patentCount"] > 0:
            result.append({
                "company": company,
                "patentCount": data["patentCount"],
                "recentPatents": data["recentPatents"],
                "technologyAreas": list(data["technologyAreas"])[:5],
                "latestPatentDate": data["latestPatentDate"],
                "lastUpdated": datetime.now().strftime("%Y-%m-%d")
            })

    result.sort(key=lambda x: x["patentCount"], reverse=True)
    return result


def save_to_json(data, filename):
    """Save data to JSON file (wraps empty results with status metadata)."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    log.info(f"Saved {len(data) if isinstance(data, list) else 1} record(s) to {output_path}")


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    output_path = Path(__file__).parent.parent / "data" / filename
    output_path.parent.mkdir(exist_ok=True)

    metadata = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "source": "fetch_patents.py",
        "data": []
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def generate_js_snippet(aggregated_data):
    """Generate JavaScript code snippet to update data.js."""
    js_output = "// Auto-generated patent intelligence data\n"
    js_output += f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    js_output += "const PATENT_INTEL_AUTO = [\n"

    for item in aggregated_data:
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


def main():
    log.info("=" * 60)
    log.info("USPTO PatentsView Patent Fetcher")
    log.info("=" * 60)
    log.info(f"Master company list: {len(TRACKED_ASSIGNEES)} companies loaded")
    log.info(f"Primary API key present: {bool(PATENTSVIEW_API_KEY)}")
    log.info("=" * 60)

    try:
        patents = fetch_all_patents()
    except Exception as e:
        log.error(f"Fatal error during fetch: {e}")
        save_status_metadata(
            "patents_raw.json",
            "error",
            f"Fatal error during fetch: {e}",
        )
        save_status_metadata(
            "patents_aggregated.json",
            "error",
            f"Fatal error during fetch: {e}",
        )
        return

    log.info(f"Total patents found: {len(patents)}")

    if not patents:
        status = "api_unavailable"
        if not PATENTSVIEW_API_KEY:
            message = "PATENTSVIEW_API_KEY not set and USPTO fallback returned no data"
        else:
            message = "PatentsView API and USPTO fallback both returned no data"
        save_status_metadata("patents_raw.json", status, message)
        save_status_metadata("patents_aggregated.json", status, message)
        return

    aggregated = aggregate_by_company(patents)
    log.info(f"Companies with patents: {len(aggregated)}")

    save_to_json(patents, "patents_raw.json")
    save_to_json(aggregated, "patents_aggregated.json")

    generate_js_snippet(aggregated)

    log.info("=" * 60)
    log.info("Done!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
