#!/usr/bin/env python3
"""
SBIR/STTR Government Grant Awards Fetcher

Identifies frontier tech companies receiving early-stage government funding.
SBIR awards are the strongest early signal — companies appear here 2-5 years
before they show up on Crunchbase or PitchBook.

Primary endpoint:  https://api.www.sbir.gov/public/api/awards
Fallback endpoint: https://www.sbir.gov/api/awards.json
                   https://www.sbir.gov/awards-api
                   (The SBIR.gov API has been rotating endpoints — we try several.)

No API key required.
"""

import json
import os
import re
import requests
import time
import logging
from datetime import datetime
from pathlib import Path

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_sbir_awards")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"

# Ordered list of SBIR endpoints we will try. The first one that responds wins.
SBIR_ENDPOINTS = [
    "https://api.www.sbir.gov/public/api/awards",
    "https://www.sbir.gov/api/awards.json",
    "https://www.sbir.gov/awards-api",
]

# Agencies most relevant to frontier tech
AGENCIES = ["DOD", "DOE", "NASA", "NSF", "HHS"]

# Keywords for frontier tech searches
SEARCH_KEYWORDS = [
    "artificial intelligence machine learning",
    "autonomous systems robotics",
    "hypersonic missile defense",
    "quantum computing",
    "nuclear fusion fission reactor",
    "satellite space launch",
    "gene therapy CRISPR",
    "advanced manufacturing 3D printing",
    "battery energy storage",
    "cybersecurity zero trust",
    "drone unmanned aerial",
    "semiconductor chip fabrication",
    "directed energy laser",
    "synthetic biology",
    "carbon capture climate",
]

MAX_RETRIES = 4
BASE_BACKOFF = 3  # seconds; doubles each retry
REQUEST_TIMEOUT = 30


def extract_companies_from_datajs():
    """Extract company names from data.js for matching."""
    if not DATA_JS.exists():
        return set()
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for match in re.finditer(r'name:\s*["\']([^"\']+)["\']', content):
        names.add(match.group(1).lower().strip())
    return names


def _parse_sbir_payload(data):
    """Normalize a SBIR.gov response into a plain list of award records."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "data", "awards", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def fetch_sbir_awards(keyword, agency=None, year=None, max_results=100,
                     page_size=100):
    """
    Fetch SBIR awards matching a keyword, trying each known endpoint in turn.
    Supports pagination and exponential backoff.
    """
    headers = {
        "User-Agent": "InnovatorsLeague-Bot/1.0",
        "Accept": "application/json",
    }

    for endpoint in SBIR_ENDPOINTS:
        all_records = []
        start = 0
        endpoint_worked = False

        while len(all_records) < max_results:
            params = {
                "keyword": keyword,
                "rows": min(page_size, max_results - len(all_records)),
                "start": start,
            }
            if agency:
                params["agency"] = agency
            if year:
                params["year"] = year

            # Retry loop with exponential backoff
            resp = None
            for attempt in range(MAX_RETRIES):
                try:
                    resp = requests.get(
                        endpoint,
                        params=params,
                        timeout=REQUEST_TIMEOUT,
                        headers=headers,
                    )
                except requests.exceptions.Timeout:
                    log.warning(
                        f"  Timeout on {endpoint} (attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(BASE_BACKOFF * (2 ** attempt))
                    continue
                except requests.exceptions.RequestException as e:
                    log.warning(
                        f"  Request error on {endpoint} (attempt {attempt + 1}): {e}"
                    )
                    time.sleep(BASE_BACKOFF * (2 ** attempt))
                    continue

                if resp.status_code == 403:
                    log.warning(f"  {endpoint} returned 403 (maintenance). Trying next endpoint.")
                    resp = None
                    break
                if resp.status_code == 404:
                    log.warning(f"  {endpoint} returned 404. Trying next endpoint.")
                    resp = None
                    break
                if resp.status_code == 429:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    log.warning(f"  Rate limited (429), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    log.warning(
                        f"  Server error {resp.status_code}, waiting {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                break  # 2xx or unhandled client error - break retry loop

            if resp is None:
                break  # Try next endpoint
            if resp.status_code != 200:
                log.warning(
                    f"  {endpoint} returned HTTP {resp.status_code}. Trying next endpoint."
                )
                break

            try:
                data = resp.json()
            except ValueError:
                log.warning(f"  Invalid JSON from {endpoint}. Trying next endpoint.")
                break

            page = _parse_sbir_payload(data)
            if not page:
                endpoint_worked = True  # empty but valid response
                break

            all_records.extend(page)
            endpoint_worked = True

            # Stop paginating when we've filled the quota or the page is short
            if len(page) < page_size:
                break
            start += page_size
            time.sleep(0.5)  # Be gentle between pages

        if endpoint_worked:
            return all_records

    # All endpoints failed
    return None


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    metadata = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "source": "fetch_sbir_awards.py",
        "data": []
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def main():
    log.info("=" * 60)
    log.info("SBIR/STTR Government Grant Awards Fetcher")
    log.info("=" * 60)
    log.info(
        f"Searching {len(SEARCH_KEYWORDS)} keyword sets across "
        f"{len(AGENCIES)} agencies"
    )
    log.info(f"Endpoints to try (in order): {SBIR_ENDPOINTS}")
    log.info("=" * 60)

    known_companies = extract_companies_from_datajs()
    log.info(f"Loaded {len(known_companies)} company names from data.js for matching")

    all_awards = []
    seen_ids = set()
    api_calls_attempted = 0
    api_calls_successful = 0
    all_endpoints_failed = False

    for keyword in SEARCH_KEYWORDS:
        api_calls_attempted += 1
        awards = fetch_sbir_awards(keyword)

        if awards is None:
            log.warning(
                "All SBIR endpoints failed for this keyword. "
                "Will fall back to cached data at end."
            )
            all_endpoints_failed = True
            continue

        api_calls_successful += 1

        new_count = 0
        for award in awards:
            award_id = (
                award.get("agency_tracking_number", "")
                or award.get("contract", "")
                or award.get("award_number", "")
                or f"{award.get('firm', '')}:{award.get('award_title', '')}"
            )
            if not award_id or award_id in seen_ids:
                continue
            seen_ids.add(award_id)

            firm = (award.get("firm") or "").strip()
            if not firm:
                continue

            firm_lower = firm.lower()
            is_known = any(
                known in firm_lower or firm_lower in known
                for known in known_companies
            )

            entry = {
                "firm": firm,
                "title": award.get("award_title", ""),
                "agency": award.get("agency", ""),
                "branch": award.get("branch", ""),
                "phase": award.get("phase", ""),
                "program": award.get("program", "SBIR"),
                "awardYear": award.get("award_year", 0),
                "awardAmount": award.get("award_amount", 0),
                "awardDate": award.get("proposal_award_date", ""),
                "abstract": (award.get("abstract", "") or "")[:500],
                "city": award.get("city", ""),
                "state": award.get("state", ""),
                "employees": award.get("number_employees", ""),
                "companyUrl": award.get("company_url", ""),
                "keywords": award.get("research_area_keywords", ""),
                "piName": award.get("pi_name", ""),
                "isKnownCompany": is_known,
            }
            all_awards.append(entry)
            new_count += 1

        log.info(
            f"  [{keyword[:40]}...] -> +{new_count} new ({len(all_awards)} total)"
        )
        time.sleep(1.5)  # SBIR API is strict

    # Fall back to cached data if all live calls failed
    if not all_awards:
        raw_path = DATA_DIR / "sbir_awards_raw.json"
        if raw_path.exists():
            try:
                cached = json.load(open(raw_path))
                if isinstance(cached, list) and cached:
                    log.info(f"Loaded {len(cached)} cached awards from existing file")
                    all_awards = cached
                elif isinstance(cached, dict) and cached.get("data"):
                    all_awards = cached["data"]
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Could not load cached data: {e}")

    # Still empty? Write status metadata and bail
    if not all_awards:
        if all_endpoints_failed or api_calls_successful == 0:
            status = "api_unavailable"
            message = (
                f"All {len(SBIR_ENDPOINTS)} SBIR endpoints failed. "
                f"Attempted {api_calls_attempted} keyword searches, "
                f"0 returned usable data. No cached data available."
            )
        else:
            status = "no_results"
            message = (
                f"SBIR endpoints responded ({api_calls_successful}/"
                f"{api_calls_attempted} successful) but returned no awards."
            )
        save_status_metadata("sbir_awards_raw.json", status, message)
        save_status_metadata("sbir_awards_aggregated.json", status, message)

        # Still write a minimal JS snippet so front-end doesn't crash
        js_path = DATA_DIR / "sbir_awards_auto.js"
        DATA_DIR.mkdir(exist_ok=True)
        with open(js_path, "w") as f:
            f.write(f"// SBIR/STTR awards — {message}\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const SBIR_AWARDS_AUTO = [];\n")
        log.warning(f"Wrote empty JS snippet to {js_path}")
        return

    # Sort by award year (newest first), then amount
    all_awards.sort(
        key=lambda a: (
            -int(a.get("awardYear", 0) or 0),
            -float(a.get("awardAmount", 0) or 0),
        )
    )

    # Separate known vs discovered companies
    known_awards = [a for a in all_awards if a.get("isKnownCompany")]
    new_companies = [a for a in all_awards if not a.get("isKnownCompany")]

    log.info(f"Total unique awards: {len(all_awards)}")
    log.info(f"  Awards to known companies: {len(known_awards)}")
    log.info(f"  Awards to new/unknown companies: {len(new_companies)}")

    # Save raw JSON
    DATA_DIR.mkdir(exist_ok=True)
    raw_path = DATA_DIR / "sbir_awards_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_awards, f, indent=2)
    log.info(f"Saved raw data to {raw_path}")

    # Generate JS snippet
    js_lines = [
        "// Auto-generated SBIR/STTR award data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total awards: {len(all_awards)} | Known companies: {len(known_awards)}",
        "const SBIR_AWARDS_AUTO = [",
    ]

    for award in all_awards[:500]:  # Cap at 500 for JS file size
        firm_esc = (award.get("firm") or "").replace('"', '\\"')
        title_esc = (award.get("title") or "")[:100].replace('"', '\\"')
        abstract_esc = (
            (award.get("abstract") or "")[:200]
            .replace('"', '\\"')
            .replace("\n", " ")
        )
        js_lines.append("  {")
        js_lines.append(f'    firm: "{firm_esc}",')
        js_lines.append(f'    title: "{title_esc}",')
        js_lines.append(f'    agency: "{award.get("agency", "")}",')
        js_lines.append(f'    phase: "{award.get("phase", "")}",')
        js_lines.append(f'    program: "{award.get("program", "")}",')
        js_lines.append(f'    awardYear: {award.get("awardYear", 0) or 0},')
        js_lines.append(f'    awardAmount: {award.get("awardAmount", 0) or 0},')
        js_lines.append(f'    state: "{award.get("state", "")}",')
        js_lines.append(f'    abstract: "{abstract_esc}",')
        js_lines.append(
            f'    isKnownCompany: {"true" if award.get("isKnownCompany") else "false"},'
        )
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "sbir_awards_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    log.info(f"Saved JS to {js_path}")

    # Top agencies summary
    agency_counts = {}
    for a in all_awards:
        ag = a.get("agency", "Unknown")
        agency_counts[ag] = agency_counts.get(ag, 0) + 1
    log.info("Top agencies:")
    for ag, count in sorted(agency_counts.items(), key=lambda x: -x[1])[:10]:
        log.info(f"  {ag}: {count} awards")

    log.info("=" * 60)


if __name__ == "__main__":
    main()
