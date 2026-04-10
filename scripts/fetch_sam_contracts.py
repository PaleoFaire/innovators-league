#!/usr/bin/env python3
"""
SAM.gov Contract Awards Fetcher for The Innovators League

Primary source:  SAM.gov Opportunities API  (api.sam.gov)       - SAM_API_KEY required
Fallback source: USAspending.gov Awards API (api.usaspending.gov)- no key required

SAM.gov free key: https://sam.gov/content/api (register, 1000 req/day)
USAspending.gov: public API, no key needed
"""

import json
import os
import re
import requests
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_sam_contracts")

DATA_DIR = Path(__file__).parent.parent / "data"
SAM_API_KEY = os.environ.get("SAM_API_KEY", "")

# SAM.gov Opportunities API
SAM_OPPORTUNITIES_URL = "https://api.sam.gov/opportunities/v2/search"
# USAspending.gov fallback (no key required)
USASPENDING_AWARDS_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# Keywords to search for that relate to our tracked companies/sectors
SEARCH_KEYWORDS = [
    # Defense tech keywords
    "autonomous systems", "counter-UAS", "unmanned aerial", "drone",
    "electronic warfare", "directed energy", "hypersonic",
    "artificial intelligence defense", "machine learning defense",
    "cybersecurity defense", "command and control",
    # Space keywords
    "satellite launch", "space launch", "orbital", "small satellite",
    "earth observation", "space situational awareness",
    # Nuclear & Energy
    "advanced nuclear", "nuclear reactor", "microreactor",
    "small modular reactor", "fusion energy", "geothermal",
    # Robotics & Manufacturing
    "robotics manufacturing", "autonomous vehicle", "additive manufacturing",
    "advanced manufacturing", "3D printing metal",
    # Semiconductors
    "semiconductor", "chip manufacturing", "CHIPS Act",
]

# Company names to search for directly
TRACKED_COMPANY_NAMES = [
    "Anduril", "Shield AI", "Palantir", "SpaceX", "Epirus", "Saronic",
    "Skydio", "Castelion", "Forterra", "Vannevar Labs", "Hadrian",
    "Rocket Lab", "Relativity Space", "Axiom Space", "Sierra Space",
    "Varda Space", "Planet Labs", "Capella Space", "BlackSky",
    "Oklo", "Kairos Power", "TerraPower", "X-energy", "NuScale",
    "Radiant", "Fervo Energy", "Scale AI", "Figure AI",
    "Boom Supersonic", "Joby Aviation", "Archer Aviation",
    "Cerebras", "Groq", "Tenstorrent",
]


def fetch_with_retry(url, params=None, json_body=None, method="GET",
                     max_retries=3, timeout=20):
    """Fetch URL with retry and exponential backoff."""
    headers = {
        "User-Agent": "InnovatorsLeague-Bot/1.0",
        "Accept": "application/json",
    }
    if json_body is not None:
        headers["Content-Type"] = "application/json"

    for attempt in range(max_retries):
        try:
            if method == "POST":
                resp = requests.post(url, params=params, json=json_body,
                                     headers=headers, timeout=timeout)
            else:
                resp = requests.get(url, params=params, headers=headers,
                                    timeout=timeout)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 5
                log.warning(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code in (500, 502, 503, 504):
                wait = (2 ** attempt) * 3
                log.warning(f"  HTTP {resp.status_code}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            log.warning(f"  Timeout on attempt {attempt + 1}/{max_retries}")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) * 2
                log.warning(f"  Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                log.error(f"  Failed after {max_retries} retries: {e}")
                return None
    return None


def search_opportunities(keyword, api_key, days_back=90):
    """Search SAM.gov for contract opportunities matching a keyword."""
    if not api_key:
        return []

    posted_from = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "q": keyword,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": 25,
        "offset": 0,
    }

    data = fetch_with_retry(SAM_OPPORTUNITIES_URL, params=params)
    if not data:
        return []

    return data.get("opportunitiesData", [])


def search_usaspending_by_recipient(company_name, days_back=180):
    """
    Fallback: Query USAspending.gov for awards to a specific recipient.
    No API key required.
    """
    time_period_start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    time_period_end = datetime.now().strftime("%Y-%m-%d")

    # USAspending "spending_by_award" POST body
    body = {
        "filters": {
            "time_period": [
                {"start_date": time_period_start, "end_date": time_period_end}
            ],
            "award_type_codes": ["A", "B", "C", "D"],  # Contract types
            "recipient_search_text": [company_name],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Award Type",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Description",
            "Start Date",
            "End Date",
        ],
        "page": 1,
        "limit": 25,
        "sort": "Award Amount",
        "order": "desc",
    }

    data = fetch_with_retry(USASPENDING_AWARDS_URL, json_body=body, method="POST")
    if not data:
        return []

    results = data.get("results", []) or []

    # Normalize to the same shape we use for SAM.gov opportunities
    normalized = []
    for r in results:
        normalized.append({
            "noticeId": r.get("Award ID", ""),
            "title": (r.get("Description") or "")[:240],
            "description": r.get("Description", ""),
            "departmentName": r.get("Awarding Agency", ""),
            "subtierAgency": r.get("Awarding Sub Agency", ""),
            "type": r.get("Award Type", ""),
            "postedDate": r.get("Start Date", ""),
            "_awardAmount": r.get("Award Amount"),
            "_recipientName": r.get("Recipient Name", ""),
            "_source": "usaspending_fallback",
        })
    return normalized


def match_company(text, company_names):
    """Check if any tracked company name appears in the text."""
    text_lower = text.lower()
    for company in company_names:
        if company.lower() in text_lower:
            return company
    return None


def format_amount(amount):
    """Format dollar amount for display."""
    if amount is None:
        return "Undisclosed"
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "Undisclosed"
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.0f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,.0f}"


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    metadata = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "source": "fetch_sam_contracts.py",
        "data": []
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def write_empty_js_snippet(message):
    """Write a JS snippet placeholder with a diagnostic message."""
    DATA_DIR.mkdir(exist_ok=True)
    js_path = DATA_DIR / "sam_contracts_auto.js"
    with open(js_path, "w") as f:
        f.write(f"// SAM.gov contract data — {message}\n")
        f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("const SAM_CONTRACTS_AUTO = [];\n")


def main():
    log.info("=" * 60)
    log.info("SAM.gov Contract Opportunities Fetcher")
    log.info("=" * 60)
    log.info(f"Primary API (SAM.gov) key present: {bool(SAM_API_KEY)}")

    all_opportunities = []
    seen_ids = set()
    primary_used = False

    # ─── Primary: SAM.gov ───
    if SAM_API_KEY:
        primary_used = True
        log.info(f"SAM API Key: {'*' * 8}...{SAM_API_KEY[-4:]}")
        log.info("=" * 60)

        # Search by company names
        log.info("Searching SAM.gov by company names...")
        for company in TRACKED_COMPANY_NAMES:
            opps = search_opportunities(company, SAM_API_KEY, days_back=90)
            new_count = 0
            for opp in opps:
                opp_id = opp.get("noticeId", "")
                if opp_id and opp_id not in seen_ids:
                    seen_ids.add(opp_id)
                    opp["_matchedCompany"] = company
                    all_opportunities.append(opp)
                    new_count += 1
            if new_count > 0:
                log.info(f"  {company}: {new_count} opportunities")
            time.sleep(0.5)

        # Search by sector keywords
        log.info("Searching SAM.gov by sector keywords...")
        for keyword in SEARCH_KEYWORDS:
            opps = search_opportunities(keyword, SAM_API_KEY, days_back=60)
            new_count = 0
            for opp in opps:
                opp_id = opp.get("noticeId", "")
                if opp_id and opp_id not in seen_ids:
                    seen_ids.add(opp_id)
                    title = opp.get("title", "")
                    desc = opp.get("description", "")
                    matched = match_company(f"{title} {desc}", TRACKED_COMPANY_NAMES)
                    opp["_matchedCompany"] = matched or ""
                    opp["_matchedKeyword"] = keyword
                    all_opportunities.append(opp)
                    new_count += 1
            if new_count > 0:
                log.info(f"  '{keyword}': {new_count} opportunities")
            time.sleep(0.5)
    else:
        log.warning("SAM_API_KEY not set — skipping SAM.gov opportunities query.")
        log.warning("Get a free key at https://sam.gov/content/api (1000 req/day).")

    # ─── Fallback: USAspending.gov ───
    if not all_opportunities:
        log.info("")
        log.info("Falling back to USAspending.gov (no key required)...")
        for company in TRACKED_COMPANY_NAMES:
            awards = search_usaspending_by_recipient(company, days_back=180)
            new_count = 0
            for opp in awards:
                opp_id = opp.get("noticeId", "")
                if opp_id and opp_id not in seen_ids:
                    seen_ids.add(opp_id)
                    opp["_matchedCompany"] = company
                    all_opportunities.append(opp)
                    new_count += 1
            if new_count > 0:
                log.info(f"  {company}: {new_count} USAspending awards")
            time.sleep(0.25)  # USAspending rate limit is generous

    log.info(f"Total unique records found: {len(all_opportunities)}")

    # ─── Handle empty ───
    if not all_opportunities:
        if not SAM_API_KEY:
            message = "SAM_API_KEY not set and USAspending fallback returned no data"
        else:
            message = "SAM.gov and USAspending fallback both returned no data"
        save_status_metadata("sam_contracts_raw.json", "api_unavailable", message)
        save_status_metadata("sam_contracts_aggregated.json", "api_unavailable", message)
        write_empty_js_snippet(message)
        return

    # Save raw data
    raw_path = DATA_DIR / "sam_contracts_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_opportunities, f, indent=2, default=str)
    log.info(f"Saved raw data to {raw_path}")

    # Aggregate by company
    company_opps = {}
    for opp in all_opportunities:
        company = opp.get("_matchedCompany", "")
        if not company:
            continue

        if company not in company_opps:
            company_opps[company] = {
                "company": company,
                "opportunityCount": 0,
                "agencies": set(),
                "types": set(),
                "recentOpportunities": [],
            }

        entry = company_opps[company]
        entry["opportunityCount"] += 1

        agency = opp.get("departmentName", "") or opp.get("subtierAgency", "")
        if agency:
            entry["agencies"].add(agency)

        notice_type = opp.get("type", "")
        if notice_type:
            entry["types"].add(notice_type)

        if len(entry["recentOpportunities"]) < 5:
            entry["recentOpportunities"].append({
                "title": (opp.get("title") or "")[:120],
                "agency": agency,
                "postedDate": opp.get("postedDate", ""),
                "type": notice_type,
                "noticeId": opp.get("noticeId", ""),
                "awardAmount": format_amount(opp.get("_awardAmount")) if opp.get("_awardAmount") else "",
            })

    # Convert sets to lists for JSON
    aggregated = []
    for company, data in sorted(company_opps.items(), key=lambda x: -x[1]["opportunityCount"]):
        data["agencies"] = sorted(list(data["agencies"]))
        data["types"] = sorted(list(data["types"]))
        data["lastUpdated"] = datetime.now().strftime("%Y-%m-%d")
        aggregated.append(data)

    agg_path = DATA_DIR / "sam_contracts_aggregated.json"
    with open(agg_path, "w") as f:
        json.dump(aggregated, f, indent=2)
    log.info(f"Saved aggregated data to {agg_path} ({len(aggregated)} companies)")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated SAM.gov/USAspending contract data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total records: {len(all_opportunities)}, Companies matched: {len(aggregated)}",
        f"// Primary source used: {'SAM.gov' if primary_used else 'USAspending.gov (fallback)'}",
        "const SAM_CONTRACTS_AUTO = [",
    ]

    for item in aggregated:
        agencies_str = json.dumps(item["agencies"][:5])
        recent_str = json.dumps(item["recentOpportunities"][:3])
        js_lines.append("  {")
        js_lines.append(f'    company: "{item["company"]}",')
        js_lines.append(f'    opportunityCount: {item["opportunityCount"]},')
        js_lines.append(f"    agencies: {agencies_str},")
        js_lines.append(f'    types: {json.dumps(item["types"])},')
        js_lines.append(f"    recentOpportunities: {recent_str},")
        js_lines.append(f'    lastUpdated: "{item["lastUpdated"]}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "sam_contracts_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    log.info(f"Saved JS to {js_path}")

    unmatched = [opp for opp in all_opportunities if not opp.get("_matchedCompany")]
    log.info(f"Unmatched sector-level opportunities: {len(unmatched)}")

    if aggregated:
        log.info("Top companies by opportunity count:")
        for item in aggregated[:10]:
            agencies_preview = ', '.join(item['agencies'][:3])
            log.info(
                f"  {item['company']:30s} | {item['opportunityCount']:3d} opportunities "
                f"| Agencies: {agencies_preview}"
            )

    log.info("=" * 60)


if __name__ == "__main__":
    main()
