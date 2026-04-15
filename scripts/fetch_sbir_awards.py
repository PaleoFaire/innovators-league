#!/usr/bin/env python3
"""
SBIR/STTR Government Grant Awards Fetcher

Identifies frontier tech companies receiving early-stage government funding.
SBIR awards are the strongest early signal — companies appear here 2-5 years
before they show up on Crunchbase or PitchBook.

Endpoint strategy (tried in order):
  1. https://www.sbir.gov/api/awards.json      (primary JSON endpoint)
  2. https://api.www.sbir.gov/public/api/awards (secondary — DATA.gov proxy)
  3. https://api.data.gov/sbir/v1/awards       (tertiary — requires DATA_GOV_API_KEY)
  4. Scrape https://www.sbir.gov/sbirsearch/award/all  (final fallback)

Error handling:
  - HTTPAdapter + urllib3 Retry for 429/5xx with exponential backoff.
  - Each endpoint is logged ONCE per run — no log spam.
  - If ALL endpoints & scrape fail, writes a minimal one-record placeholder
    with status metadata embedded in the first record so downstream scripts
    (which expect a list) keep working.

No API key required (DATA_GOV_API_KEY is optional and improves tier 3).
"""

import json
import os
import re
import time
import logging
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from urllib3.util import Retry  # type: ignore

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("fetch_sbir_awards")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"

SBIR_ENDPOINTS = [
    ("primary_sbir_json", "https://www.sbir.gov/api/awards.json"),
    ("secondary_api_proxy", "https://api.www.sbir.gov/public/api/awards"),
    ("tertiary_data_gov", "https://api.data.gov/sbir/v1/awards"),
]
SBIR_SCRAPE_URL = "https://www.sbir.gov/sbirsearch/award/all"

DATA_GOV_API_KEY = os.environ.get("DATA_GOV_API_KEY", "").strip()

AGENCIES = ["DOD", "DOE", "NASA", "NSF", "HHS"]

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
REQUEST_TIMEOUT = 30


def _make_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "InnovatorsLeague-Bot/2.0 (+https://innovatorsleague.com)",
        "Accept": "application/json",
    })
    return session


SESSION = _make_session()

# Remember which endpoints we've already logged as dead to avoid spam
_DEAD_ENDPOINTS = set()


def extract_companies_from_datajs():
    if not DATA_JS.exists():
        return set()
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")
    names = set()
    for match in re.finditer(r'name:\s*["\']([^"\']+)["\']', content):
        names.add(match.group(1).lower().strip())
    return names


def _parse_sbir_payload(data):
    """Normalize various SBIR.gov response shapes into a list of awards."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("results", "data", "awards", "items", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def _fetch_one_endpoint(endpoint_name, url, keyword, agency=None, year=None,
                       max_results=100, page_size=100):
    """Pull paginated awards from a single endpoint. Returns list or None."""
    if endpoint_name in _DEAD_ENDPOINTS:
        return None

    all_records = []
    start = 0

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
        if endpoint_name == "tertiary_data_gov" and DATA_GOV_API_KEY:
            params["api_key"] = DATA_GOV_API_KEY

        try:
            resp = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} connection error: {e}")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        if resp.status_code in (403, 404):
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(
                    f"  {endpoint_name} returned HTTP {resp.status_code} — marking dead."
                )
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None
        if resp.status_code >= 500:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} HTTP {resp.status_code} — marking dead.")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None
        if resp.status_code != 200:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} HTTP {resp.status_code}")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        try:
            data = resp.json()
        except ValueError:
            if endpoint_name not in _DEAD_ENDPOINTS:
                log.warning(f"  {endpoint_name} returned non-JSON — marking dead.")
                _DEAD_ENDPOINTS.add(endpoint_name)
            return None

        page = _parse_sbir_payload(data)
        if not page:
            return all_records  # valid but empty
        all_records.extend(page)
        if len(page) < page_size:
            break
        start += page_size
        time.sleep(0.5)

    return all_records


def fetch_sbir_awards(keyword, agency=None, year=None, max_results=100):
    """Try each endpoint in order; return first successful list."""
    for endpoint_name, url in SBIR_ENDPOINTS:
        records = _fetch_one_endpoint(
            endpoint_name, url, keyword,
            agency=agency, year=year, max_results=max_results
        )
        if records is not None:
            return records, endpoint_name
    return None, None


# ─────────────────────────────────────────────────────────────────
# Scrape fallback
# ─────────────────────────────────────────────────────────────────
def scrape_sbir_results(keyword, max_results=50):
    """
    Minimal fallback: scrape the public search results page.
    Returns a list of dict records matching the shape of the JSON API so
    the rest of the pipeline doesn't need a special branch.
    """
    params = {"keywords": keyword, "per_page": max_results}
    try:
        resp = SESSION.get(SBIR_SCRAPE_URL, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        log.warning(f"  scrape fallback connection error: {e}")
        return None
    if not resp.ok:
        log.warning(f"  scrape fallback HTTP {resp.status_code}")
        return None

    html = resp.text
    # Very forgiving parser: look for award cards / table rows
    rows = []
    # pattern: <h4>Award Title</h4> ... <a>Company</a>
    pattern = re.compile(
        r'<h4[^>]*>(?P<title>[^<]+)</h4>.*?'
        r'(?:Company|Firm)[^<]*<[^>]*>(?P<firm>[^<]+)<'
        r'.*?(?:Agency)[^<]*<[^>]*>(?P<agency>[^<]+)<'
        r'.*?(?:Award Amount|Amount)[^<]*<[^>]*>\s*\$?(?P<amount>[\d,\.]+)',
        re.DOTALL | re.IGNORECASE,
    )
    for m in pattern.finditer(html):
        try:
            amount = float(m.group("amount").replace(",", ""))
        except ValueError:
            amount = 0
        rows.append({
            "firm": m.group("firm").strip(),
            "award_title": m.group("title").strip(),
            "agency": m.group("agency").strip(),
            "award_amount": amount,
            "award_year": datetime.now().year,
            "phase": "",
            "program": "SBIR",
            "abstract": "",
            "_source": "sbir_scrape_fallback",
        })
        if len(rows) >= max_results:
            break
    return rows


def save_to_json(data, filename):
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved {len(data) if isinstance(data, list) else 1} record(s) to {output_path}")


def write_placeholder_array(status, message):
    """
    All endpoints failed. Write a list with a single placeholder record
    carrying the status metadata inside it. Downstream scripts iterating
    the list see ONE record, can check `isPlaceholder`, and move on without
    crashing.
    """
    placeholder = [{
        "firm": "",
        "title": "",
        "agency": "",
        "branch": "",
        "phase": "",
        "program": "SBIR",
        "awardYear": 0,
        "awardAmount": 0,
        "awardDate": "",
        "abstract": "",
        "city": "",
        "state": "",
        "employees": "",
        "companyUrl": "",
        "keywords": "",
        "piName": "",
        "isKnownCompany": False,
        "isPlaceholder": True,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }]
    save_to_json(placeholder, "sbir_awards_raw.json")
    save_to_json(placeholder, "sbir_awards_aggregated.json")

    js_path = DATA_DIR / "sbir_awards_auto.js"
    DATA_DIR.mkdir(exist_ok=True)
    with open(js_path, "w") as f:
        f.write(f"// SBIR/STTR awards — {message}\n")
        f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("const SBIR_AWARDS_AUTO = [];\n")
    log.warning(f"Wrote placeholder to {js_path}")


def main():
    log.info("=" * 60)
    log.info("SBIR/STTR Government Grant Awards Fetcher")
    log.info("=" * 60)
    log.info(f"Searching {len(SEARCH_KEYWORDS)} keyword sets")
    log.info(f"Endpoints: {[n for n, _ in SBIR_ENDPOINTS]}")
    log.info(f"DATA_GOV_API_KEY: {'set' if DATA_GOV_API_KEY else 'not set'}")
    log.info("=" * 60)

    known_companies = extract_companies_from_datajs()
    log.info(f"Loaded {len(known_companies)} company names from data.js for matching")

    all_awards = []
    seen_ids = set()
    api_calls_attempted = 0
    api_calls_successful = 0
    endpoint_wins = {}

    for keyword in SEARCH_KEYWORDS:
        api_calls_attempted += 1
        awards, endpoint_used = fetch_sbir_awards(keyword)

        if awards is None:
            continue
        api_calls_successful += 1
        endpoint_wins[endpoint_used] = endpoint_wins.get(endpoint_used, 0) + 1

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

            all_awards.append({
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
                "_endpoint": endpoint_used,
            })
            new_count += 1

        log.info(
            f"  [{keyword[:40]}...] via {endpoint_used} -> "
            f"+{new_count} new ({len(all_awards)} total)"
        )
        time.sleep(1.5)

    # All APIs failed — try scrape fallback
    if not all_awards and api_calls_successful == 0:
        log.warning("All JSON endpoints failed — trying scrape fallback.")
        scraped_total = []
        for keyword in SEARCH_KEYWORDS[:5]:  # Limit scrapes to avoid ban
            scraped = scrape_sbir_results(keyword)
            if scraped:
                scraped_total.extend(scraped)
                time.sleep(2.0)
        if scraped_total:
            log.info(f"Scrape fallback: {len(scraped_total)} records")
            for s in scraped_total:
                all_awards.append({
                    "firm": s.get("firm", ""),
                    "title": s.get("award_title", ""),
                    "agency": s.get("agency", ""),
                    "branch": "",
                    "phase": "",
                    "program": "SBIR",
                    "awardYear": s.get("award_year", 0),
                    "awardAmount": s.get("award_amount", 0),
                    "awardDate": "",
                    "abstract": "",
                    "city": "",
                    "state": "",
                    "employees": "",
                    "companyUrl": "",
                    "keywords": "",
                    "piName": "",
                    "isKnownCompany": False,
                    "_endpoint": "sbir_scrape_fallback",
                })

    # Fall back to cached data if live calls + scrape both failed
    if not all_awards:
        raw_path = DATA_DIR / "sbir_awards_raw.json"
        if raw_path.exists():
            try:
                cached = json.load(open(raw_path))
                if isinstance(cached, list) and cached:
                    # Skip placeholder-only cache
                    if not (len(cached) == 1 and cached[0].get("isPlaceholder")):
                        log.info(f"Loaded {len(cached)} cached awards from existing file")
                        all_awards = cached
                elif isinstance(cached, dict) and cached.get("data"):
                    all_awards = cached["data"]
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Could not load cached data: {e}")

    # Still empty? Write a placeholder array so downstream keeps working
    if not all_awards:
        status = "api_unavailable"
        message = (
            f"All {len(SBIR_ENDPOINTS)} SBIR endpoints and scrape fallback failed. "
            f"Attempted {api_calls_attempted} keyword searches, "
            f"{api_calls_successful} succeeded. No cached data available."
        )
        write_placeholder_array(status, message)
        log.warning(message)
        return

    # Sort by award year (newest first), then amount
    all_awards.sort(
        key=lambda a: (
            -int(a.get("awardYear", 0) or 0),
            -float(a.get("awardAmount", 0) or 0),
        )
    )

    known_awards = [a for a in all_awards if a.get("isKnownCompany")]
    new_companies = [a for a in all_awards if not a.get("isKnownCompany")]

    log.info(f"Total unique awards: {len(all_awards)}")
    log.info(f"  Awards to known companies: {len(known_awards)}")
    log.info(f"  Awards to new/unknown companies: {len(new_companies)}")
    log.info(f"  Endpoint wins: {endpoint_wins}")

    save_to_json(all_awards, "sbir_awards_raw.json")

    js_lines = [
        "// Auto-generated SBIR/STTR award data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Total awards: {len(all_awards)} | Known companies: {len(known_awards)}",
        "const SBIR_AWARDS_AUTO = [",
    ]
    for award in all_awards[:500]:
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
