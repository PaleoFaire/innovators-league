#!/usr/bin/env python3
"""
Diffbot Company Enrichment Pipeline for The Innovators League

Primary source:  Diffbot Knowledge Graph Enhance API - DIFFBOT_API_TOKEN required
Fallback sources (no keys needed):
  - Wikipedia REST API (summary + extracts)
  - Wikidata SPARQL (structured company facts)
  - Open Corporates-style company homepage meta scraping (very light)

Free tier (Diffbot): 10,000 credits/month (each enhance = 1 credit)

Fields we try to extract (primary or fallback):
  - employee count
  - founding date / founded year
  - founder names
  - headquarters location
  - short description / summary
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
log = logging.getLogger("fetch_diffbot_enrichment")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"
DIFFBOT_TOKEN = os.environ.get("DIFFBOT_API_TOKEN", "")

ENHANCE_API = "https://kg.diffbot.com/kg/v3/enhance"
WIKIPEDIA_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def extract_companies_from_datajs():
    """Extract company names and websites from data.js for enrichment."""
    if not DATA_JS.exists():
        return []
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")

    companies = []
    for match in re.finditer(
        r'name:\s*"([^"]+)"[^}]*?'
        r'(?:website:\s*"([^"]*)")?[^}]*?'
        r'(?:sector:\s*"([^"]*)")?',
        content,
        re.DOTALL,
    ):
        name = match.group(1).strip()
        website = (match.group(2) or "").strip()
        sector = (match.group(3) or "").strip()
        if name and len(name) > 2:
            companies.append({
                "name": name,
                "website": website,
                "sector": sector,
            })

    # Deduplicate by name
    seen = set()
    unique = []
    for c in companies:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique.append(c)
    return unique


def _request_with_retry(method, url, **kwargs):
    """HTTP request wrapper with exponential backoff retries."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code in (429, 503):
                wait = 2 ** attempt * 3
                log.warning(f"    HTTP {resp.status_code} from {url}, waiting {wait}s")
                time.sleep(wait)
                continue
            if 500 <= resp.status_code < 600:
                wait = 2 ** attempt * 2
                time.sleep(wait)
                continue
            return resp
        except requests.exceptions.RequestException as e:
            log.warning(f"    Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    return None


def enrich_company_diffbot(name, website=None):
    """Enrich a single company using Diffbot Enhance API."""
    params = {
        "type": "Organization",
        "name": name,
        "token": DIFFBOT_TOKEN,
        "size": 1,
    }
    if website:
        clean_url = website.replace("https://", "").replace("http://", "").rstrip("/")
        params["url"] = clean_url

    resp = _request_with_retry(
        "GET",
        ENHANCE_API,
        params=params,
        headers={"Accept": "application/json"},
    )
    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None

    entities = data.get("data", [])
    return entities[0] if entities else None


def enrich_company_wikipedia(name):
    """
    Fallback enrichment using Wikipedia REST API.
    No key required. Returns a dict normalized to the same shape as Diffbot output.
    """
    # Wikipedia page titles use underscores
    title = name.replace(" ", "_")
    url = f"{WIKIPEDIA_SUMMARY_API}{title}"

    resp = _request_with_retry(
        "GET",
        url,
        headers={
            "User-Agent": "InnovatorsLeague-Bot/1.0 (https://example.com)",
            "Accept": "application/json",
        },
    )
    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None

    if data.get("type") == "disambiguation":
        return None

    description = (data.get("extract") or "")[:500]
    if not description:
        return None

    return {
        "name": data.get("title", name),
        "description": description,
        "summary": description,
        "homepageUri": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "_source": "wikipedia",
    }


def enrich_company_wikidata(name):
    """
    Fallback enrichment using Wikidata SPARQL.
    Extracts founding date, founders, HQ, and employee count where available.
    """
    query = f'''
    SELECT ?company ?companyLabel ?inception ?hqLabel ?founderLabel ?employees
    WHERE {{
      ?company rdfs:label "{name}"@en.
      ?company wdt:P31/wdt:P279* wd:Q4830453.
      OPTIONAL {{ ?company wdt:P571 ?inception. }}
      OPTIONAL {{ ?company wdt:P159 ?hq. }}
      OPTIONAL {{ ?company wdt:P112 ?founder. }}
      OPTIONAL {{ ?company wdt:P1128 ?employees. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    '''
    resp = _request_with_retry(
        "GET",
        WIKIDATA_SPARQL,
        params={"query": query, "format": "json"},
        headers={
            "User-Agent": "InnovatorsLeague-Bot/1.0",
            "Accept": "application/sparql-results+json",
        },
    )
    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None

    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return None

    row = bindings[0]
    result = {"_source": "wikidata"}
    if "inception" in row:
        result["foundingDate"] = {"str": row["inception"]["value"][:4]}
    if "hqLabel" in row:
        result["location"] = row["hqLabel"]["value"]
    if "founderLabel" in row:
        result["founders"] = [row["founderLabel"]["value"]]
    if "employees" in row:
        try:
            result["nbEmployees"] = int(float(row["employees"]["value"]))
        except (TypeError, ValueError):
            pass
    return result


def merge_fallback_data(name, website):
    """Combine Wikipedia + Wikidata fallback data into a single entity dict."""
    merged = {}
    wiki = enrich_company_wikipedia(name)
    if wiki:
        merged.update(wiki)
    wd = enrich_company_wikidata(name)
    if wd:
        # Don't overwrite populated fields from Wikipedia
        for k, v in wd.items():
            merged.setdefault(k, v)
    return merged if merged else None


def extract_enrichment(entity):
    """Extract useful fields from a Diffbot entity (or a fallback entity)."""
    if not entity:
        return {}

    result = {}

    # Basic info
    result["diffbotName"] = entity.get("name", "")
    result["description"] = (entity.get("description", "") or "")[:300]
    result["summary"] = (
        entity.get("summary", "") or entity.get("description", "") or ""
    )[:200]
    if entity.get("_source"):
        result["source"] = entity["_source"]

    # Employee count
    nb_employees = entity.get("nbEmployees")
    if nb_employees:
        result["employeeCount"] = nb_employees
        if nb_employees >= 10000:
            result["employeeRange"] = "10,000+"
        elif nb_employees >= 1000:
            result["employeeRange"] = "1,000-10,000"
        elif nb_employees >= 500:
            result["employeeRange"] = "500-1,000"
        elif nb_employees >= 100:
            result["employeeRange"] = "100-500"
        elif nb_employees >= 50:
            result["employeeRange"] = "50-100"
        elif nb_employees >= 10:
            result["employeeRange"] = "10-50"
        else:
            result["employeeRange"] = "1-10"

    nb_employees_range = entity.get("nbEmployeesRange")
    if nb_employees_range and not nb_employees:
        result["employeeRange"] = nb_employees_range

    # Founding date
    founding_date = entity.get("foundingDate")
    if founding_date:
        if isinstance(founding_date, dict):
            result["foundedYear"] = (founding_date.get("str", "") or "")[:4]
        else:
            result["foundedYear"] = str(founding_date)[:4]

    # Founders
    founders = entity.get("founders") or entity.get("founder")
    if founders:
        if isinstance(founders, list):
            result["founders"] = [
                (f.get("name") if isinstance(f, dict) else str(f))
                for f in founders[:5]
            ]
        elif isinstance(founders, str):
            result["founders"] = [founders]

    # Location
    location = entity.get("location")
    if location:
        if isinstance(location, dict):
            city = location.get("city", {})
            region = location.get("region", {})
            parts = []
            if isinstance(city, dict) and city.get("name"):
                parts.append(city["name"])
            elif isinstance(city, str):
                parts.append(city)
            if isinstance(region, dict) and region.get("name"):
                parts.append(region["name"])
            elif isinstance(region, str):
                parts.append(region)
            if parts:
                result["headquarters"] = ", ".join(parts)
        elif isinstance(location, str):
            result["headquarters"] = location

    locations = entity.get("locations", [])
    if locations and isinstance(locations, list):
        loc = locations[0]
        if isinstance(loc, dict):
            city_name = ""
            region_name = ""
            if loc.get("city"):
                city_obj = loc["city"]
                city_name = (
                    city_obj.get("name", "") if isinstance(city_obj, dict) else str(city_obj)
                )
            if loc.get("region"):
                reg_obj = loc["region"]
                region_name = (
                    reg_obj.get("name", "") if isinstance(reg_obj, dict) else str(reg_obj)
                )
            if city_name or region_name:
                result["headquarters"] = ", ".join(filter(None, [city_name, region_name]))

    # Revenue
    revenue = entity.get("revenue")
    if revenue:
        if isinstance(revenue, dict):
            val = revenue.get("value", 0)
            if val:
                result["estimatedRevenue"] = val
                if val >= 1_000_000_000:
                    result["revenueFormatted"] = f"${val / 1_000_000_000:.1f}B"
                elif val >= 1_000_000:
                    result["revenueFormatted"] = f"${val / 1_000_000:.0f}M"
                elif val >= 1_000:
                    result["revenueFormatted"] = f"${val / 1_000:.0f}K"
        elif isinstance(revenue, (int, float)) and revenue > 0:
            result["estimatedRevenue"] = revenue

    # Social links
    social_links = {}
    for link_obj in entity.get("linkedInUri", []) or []:
        if isinstance(link_obj, str):
            social_links["linkedin"] = link_obj
        elif isinstance(link_obj, dict):
            social_links["linkedin"] = link_obj.get("uri", link_obj.get("value", ""))
    if entity.get("linkedInUri") and isinstance(entity["linkedInUri"], str):
        social_links["linkedin"] = entity["linkedInUri"]

    for link_obj in entity.get("twitterUri", []) or []:
        if isinstance(link_obj, str):
            social_links["twitter"] = link_obj
        elif isinstance(link_obj, dict):
            social_links["twitter"] = link_obj.get("uri", link_obj.get("value", ""))
    if entity.get("twitterUri") and isinstance(entity["twitterUri"], str):
        social_links["twitter"] = entity["twitterUri"]

    # Homepage
    homepage = entity.get("homepageUri")
    if homepage:
        if isinstance(homepage, str):
            result["website"] = homepage
        elif isinstance(homepage, dict):
            result["website"] = homepage.get("uri", homepage.get("value", ""))

    if social_links:
        result["socialLinks"] = social_links

    # Industry / categories
    categories = entity.get("categories", [])
    if categories:
        result["industries"] = [
            c.get("name", "") if isinstance(c, dict) else str(c)
            for c in categories[:5]
            if (c.get("name", "") if isinstance(c, dict) else str(c))
        ]

    # Stock / public status
    result["isPublic"] = bool(entity.get("isPublic") or entity.get("stock"))
    if entity.get("stock"):
        stock = entity["stock"]
        if isinstance(stock, dict):
            result["ticker"] = stock.get("symbol", "")
            result["exchange"] = stock.get("exchange", "")

    result["confidence"] = entity.get("score", 0)

    return result


def save_status_metadata(filename, status, message):
    """Write a status metadata file instead of leaving empty arrays."""
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / filename
    metadata = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "source": "fetch_diffbot_enrichment.py",
        "data": []
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    log.warning(f"Wrote status metadata to {output_path}: {status}")


def main():
    log.info("=" * 60)
    log.info("Diffbot Company Enrichment Pipeline")
    log.info("=" * 60)
    log.info(f"Diffbot token present: {bool(DIFFBOT_TOKEN)}")

    if not DIFFBOT_TOKEN:
        log.warning("DIFFBOT_API_TOKEN not set. Will fall back to Wikipedia + Wikidata.")
        log.warning("Get a Diffbot token at: https://www.diffbot.com/ (10K credits/month free)")

    DATA_DIR.mkdir(exist_ok=True)

    companies = extract_companies_from_datajs()
    log.info(f"Found {len(companies)} companies in data.js")

    # Load existing enrichment data to avoid re-fetching recently enriched companies
    existing_path = DATA_DIR / "diffbot_enrichment_raw.json"
    existing_data = {}
    if existing_path.exists():
        try:
            raw = json.load(open(existing_path))
            # Handle both list and status-metadata formats
            if isinstance(raw, dict) and "data" in raw:
                raw = raw["data"]
            if isinstance(raw, list):
                for entry in raw:
                    if entry.get("name") and entry.get("lastEnriched"):
                        if entry["lastEnriched"] >= datetime.now().strftime("%Y-%m-") + "01":
                            existing_data[entry["name"]] = entry
        except (json.JSONDecodeError, IOError):
            pass

    log.info(f"Cached enrichment data: {len(existing_data)} companies (skip if recent)")

    MAX_PER_RUN = 200

    all_enrichments = []
    enriched_count = 0
    cached_count = 0
    failed_count = 0
    fallback_used_count = 0

    for i, company in enumerate(companies):
        name = company["name"]

        if name in existing_data:
            all_enrichments.append(existing_data[name])
            cached_count += 1
            continue

        if enriched_count >= MAX_PER_RUN:
            log.info(f"Reached max enrichments per run ({MAX_PER_RUN}), stopping.")
            all_enrichments.append({
                "name": name,
                "sector": company.get("sector", ""),
                "enriched": False,
                "lastEnriched": "",
            })
            continue

        log.info(f"[{i + 1}/{len(companies)}] Enriching: {name}")

        entity = None
        source_used = None

        # Try Diffbot first if token is available
        if DIFFBOT_TOKEN:
            entity = enrich_company_diffbot(name, website=company.get("website"))
            if entity:
                source_used = "diffbot"

        # Fallback to Wikipedia + Wikidata
        if not entity:
            entity = merge_fallback_data(name, website=company.get("website"))
            if entity:
                source_used = entity.get("_source", "wikipedia")
                fallback_used_count += 1

        if entity:
            enrichment = extract_enrichment(entity)
            enrichment["name"] = name
            enrichment["sector"] = company.get("sector", "")
            enrichment["enriched"] = True
            enrichment["source"] = source_used
            enrichment["lastEnriched"] = datetime.now().strftime("%Y-%m-%d")
            all_enrichments.append(enrichment)
            enriched_count += 1

            emp_str = enrichment.get("employeeRange", "?")
            hq_str = enrichment.get("headquarters", "?")
            log.info(f"  OK ({emp_str} employees, {hq_str}) via {source_used}")
        else:
            all_enrichments.append({
                "name": name,
                "sector": company.get("sector", ""),
                "enriched": False,
                "lastEnriched": datetime.now().strftime("%Y-%m-%d"),
            })
            failed_count += 1
            log.info("  no data from any source")

        # Rate limiting
        time.sleep(1.0)

    log.info("Enrichment complete:")
    log.info(f"  Total companies: {len(all_enrichments)}")
    log.info(f"  Newly enriched (primary): {enriched_count - fallback_used_count}")
    log.info(f"  Enriched via fallback: {fallback_used_count}")
    log.info(f"  Used cache: {cached_count}")
    log.info(f"  Failed/no data: {failed_count}")

    # If nothing was enriched AND nothing was cached, write status metadata
    if enriched_count == 0 and cached_count == 0:
        save_status_metadata(
            "diffbot_enrichment_raw.json",
            "api_unavailable",
            "Diffbot token not set and Wikipedia/Wikidata fallbacks returned no data",
        )
        js_path = DATA_DIR / "diffbot_enrichment_auto.js"
        with open(js_path, "w") as f:
            f.write("// Diffbot enrichment — no data retrieved from any source\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const DIFFBOT_ENRICHMENT_AUTO = [];\n")
        return

    # Save raw JSON
    raw_path = DATA_DIR / "diffbot_enrichment_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_enrichments, f, indent=2)
    log.info(f"Saved raw data to {raw_path}")

    # Filter to only enriched companies for JS output
    enriched = [e for e in all_enrichments if e.get("enriched")]

    js_lines = [
        "// Auto-generated company enrichment data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Enriched companies: {len(enriched)} / {len(all_enrichments)}",
        f"// Sources used: Diffbot + Wikipedia/Wikidata fallback",
        "const DIFFBOT_ENRICHMENT_AUTO = [",
    ]

    for entry in enriched:
        name_esc = entry.get("name", "").replace('"', '\\"')
        desc_esc = (entry.get("summary", "") or "").replace('"', '\\"').replace("\n", " ")[:150]
        hq_esc = entry.get("headquarters", "").replace('"', '\\"')
        industries = json.dumps(entry.get("industries", [])[:3])
        social = json.dumps(entry.get("socialLinks", {}))

        js_lines.append("  {")
        js_lines.append(f'    name: "{name_esc}",')
        js_lines.append(f'    summary: "{desc_esc}",')

        if entry.get("employeeCount"):
            js_lines.append(f'    employeeCount: {entry["employeeCount"]},')
        if entry.get("employeeRange"):
            js_lines.append(f'    employeeRange: "{entry["employeeRange"]}",')
        if entry.get("foundedYear"):
            js_lines.append(f'    foundedYear: "{entry["foundedYear"]}",')
        if hq_esc:
            js_lines.append(f'    headquarters: "{hq_esc}",')
        if entry.get("founders"):
            founders_json = json.dumps(entry["founders"])
            js_lines.append(f'    founders: {founders_json},')
        if entry.get("industries"):
            js_lines.append(f'    industries: {industries},')
        if entry.get("socialLinks"):
            js_lines.append(f'    socialLinks: {social},')
        if entry.get("isPublic"):
            js_lines.append(f'    isPublic: true,')
            if entry.get("ticker"):
                js_lines.append(f'    ticker: "{entry["ticker"]}",')
        if entry.get("revenueFormatted"):
            js_lines.append(f'    estimatedRevenue: "{entry["revenueFormatted"]}",')
        if entry.get("source"):
            js_lines.append(f'    source: "{entry["source"]}",')

        js_lines.append(f'    lastEnriched: "{entry.get("lastEnriched", "")}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "diffbot_enrichment_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    log.info(f"Saved JS to {js_path}")

    log.info("=" * 60)


if __name__ == "__main__":
    main()
