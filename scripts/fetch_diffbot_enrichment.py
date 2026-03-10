#!/usr/bin/env python3
"""
Diffbot Company Enrichment Pipeline for The Innovators League
Uses Diffbot's Knowledge Graph to enrich company profiles with real-time data:
  - Employee count, founding year, description
  - Social profiles (LinkedIn, Twitter/X)
  - Industry classification, location
  - Revenue estimates, tech stack signals

API: Diffbot Knowledge Graph (Enhance API)
  https://docs.diffbot.com/reference/kg-enhance-api
Free tier: 10,000 credits/month (each enhance = 1 credit)

Requires DIFFBOT_API_TOKEN environment variable.
"""

import json
import os
import re
import requests
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"
DIFFBOT_TOKEN = os.environ.get("DIFFBOT_API_TOKEN", "")
ENHANCE_API = "https://kg.diffbot.com/kg/v3/enhance"


def extract_companies_from_datajs():
    """Extract company names and websites from data.js for enrichment."""
    if not DATA_JS.exists():
        return []
    content = DATA_JS.read_text(encoding="utf-8", errors="replace")

    companies = []
    # Extract company entries with name, website, sector
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


def enrich_company(name, website=None):
    """Enrich a single company using Diffbot Enhance API."""
    params = {
        "type": "Organization",
        "name": name,
        "token": DIFFBOT_TOKEN,
        "size": 1,
    }
    if website:
        # Strip protocol for cleaner matching
        clean_url = website.replace("https://", "").replace("http://", "").rstrip("/")
        params["url"] = clean_url

    try:
        resp = requests.get(ENHANCE_API, params=params, timeout=30,
                           headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()

        entities = data.get("data", [])
        if not entities:
            return None

        entity = entities[0]
        return entity
    except requests.exceptions.RequestException as e:
        print(f"    Error enriching {name}: {e}")
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def extract_enrichment(entity):
    """Extract useful fields from a Diffbot entity."""
    if not entity:
        return {}

    result = {}

    # Basic info
    result["diffbotName"] = entity.get("name", "")
    result["description"] = (entity.get("description", "") or "")[:300]
    result["summary"] = (entity.get("summary", "") or entity.get("description", "") or "")[:200]

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

    # Employee count ranges (Diffbot sometimes returns this instead)
    nb_employees_range = entity.get("nbEmployeesRange")
    if nb_employees_range and not nb_employees:
        result["employeeRange"] = nb_employees_range

    # Founding date
    founding_date = entity.get("foundingDate")
    if founding_date:
        result["foundedYear"] = founding_date.get("str", "")[:4] if isinstance(founding_date, dict) else str(founding_date)[:4]

    # Location
    location = entity.get("location")
    if location:
        if isinstance(location, dict):
            city = location.get("city", {})
            region = location.get("region", {})
            country = location.get("country", {})
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

    # Locations list
    locations = entity.get("locations", [])
    if locations and isinstance(locations, list):
        loc = locations[0]
        if isinstance(loc, dict):
            city_name = ""
            region_name = ""
            if loc.get("city"):
                city_obj = loc["city"]
                city_name = city_obj.get("name", "") if isinstance(city_obj, dict) else str(city_obj)
            if loc.get("region"):
                reg_obj = loc["region"]
                region_name = reg_obj.get("name", "") if isinstance(reg_obj, dict) else str(reg_obj)
            if city_name or region_name:
                result["headquarters"] = ", ".join(filter(None, [city_name, region_name]))

    # Revenue
    revenue = entity.get("revenue")
    if revenue:
        if isinstance(revenue, dict):
            val = revenue.get("value", 0)
            currency = revenue.get("currency", "USD")
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

    # Confidence score from Diffbot
    result["confidence"] = entity.get("score", 0)

    return result


def main():
    print("=" * 60)
    print("Diffbot Company Enrichment Pipeline")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not DIFFBOT_TOKEN:
        print("WARNING: DIFFBOT_API_TOKEN not set. Generating empty output files.")
        with open(DATA_DIR / "diffbot_enrichment_raw.json", "w") as f:
            json.dump([], f)
        js_path = DATA_DIR / "diffbot_enrichment_auto.js"
        with open(js_path, "w") as f:
            f.write(f"// Diffbot enrichment — API token not configured\n")
            f.write(f"// Last updated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("const DIFFBOT_ENRICHMENT_AUTO = [];\n")
        print("Empty output files created.")
        return

    print(f"API Token: {'*' * 8}...{DIFFBOT_TOKEN[-4:]}")
    print("=" * 60)

    companies = extract_companies_from_datajs()
    print(f"Found {len(companies)} companies in data.js")

    # Load existing enrichment data to avoid re-fetching recently enriched companies
    existing_path = DATA_DIR / "diffbot_enrichment_raw.json"
    existing_data = {}
    if existing_path.exists():
        try:
            raw = json.load(open(existing_path))
            for entry in raw:
                if entry.get("name") and entry.get("lastEnriched"):
                    # Skip if enriched within last 7 days
                    enriched_date = entry["lastEnriched"]
                    today = datetime.now().strftime("%Y-%m-%d")
                    if enriched_date >= (datetime.now().strftime("%Y-%m-") + "01"):
                        existing_data[entry["name"]] = entry
        except (json.JSONDecodeError, IOError):
            pass

    print(f"Cached enrichment data: {len(existing_data)} companies (skip if recent)")

    # Budget: 10K credits/month. Enriching ~625 companies = 625 credits.
    # With weekly runs, that's ~2,500/month — well within budget.
    # Limit to 200 per run to be safe (leaves room for debugging)
    MAX_PER_RUN = 200

    all_enrichments = []
    enriched_count = 0
    cached_count = 0
    failed_count = 0

    for i, company in enumerate(companies):
        name = company["name"]

        # Use cached data if recent
        if name in existing_data:
            all_enrichments.append(existing_data[name])
            cached_count += 1
            continue

        if enriched_count >= MAX_PER_RUN:
            print(f"\n  Reached max enrichments per run ({MAX_PER_RUN}), stopping.")
            # Still include remaining companies with empty data
            all_enrichments.append({
                "name": name,
                "sector": company.get("sector", ""),
                "enriched": False,
                "lastEnriched": "",
            })
            continue

        print(f"  [{i + 1}/{len(companies)}] Enriching: {name}...", end=" ")

        entity = enrich_company(name, website=company.get("website"))

        if entity:
            enrichment = extract_enrichment(entity)
            enrichment["name"] = name
            enrichment["sector"] = company.get("sector", "")
            enrichment["enriched"] = True
            enrichment["lastEnriched"] = datetime.now().strftime("%Y-%m-%d")
            all_enrichments.append(enrichment)
            enriched_count += 1

            emp_str = enrichment.get("employeeRange", "?")
            hq_str = enrichment.get("headquarters", "?")
            print(f"✓ ({emp_str} employees, {hq_str})")
        else:
            all_enrichments.append({
                "name": name,
                "sector": company.get("sector", ""),
                "enriched": False,
                "lastEnriched": datetime.now().strftime("%Y-%m-%d"),
            })
            failed_count += 1
            print("✗ (no data)")

        # Rate limiting: Diffbot free tier allows ~1 req/sec
        time.sleep(1.0)

    print(f"\nEnrichment complete:")
    print(f"  Total companies: {len(all_enrichments)}")
    print(f"  Newly enriched: {enriched_count}")
    print(f"  Used cache: {cached_count}")
    print(f"  Failed/no data: {failed_count}")
    print(f"  API credits used: ~{enriched_count}")

    # Save raw JSON
    raw_path = DATA_DIR / "diffbot_enrichment_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_enrichments, f, indent=2)
    print(f"\nSaved raw data to {raw_path}")

    # Filter to only enriched companies for JS output
    enriched = [e for e in all_enrichments if e.get("enriched")]

    # Generate JS snippet
    js_lines = [
        "// Auto-generated Diffbot company enrichment data",
        f"// Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"// Enriched companies: {len(enriched)} / {len(all_enrichments)}",
        "const DIFFBOT_ENRICHMENT_AUTO = [",
    ]

    for entry in enriched:
        name_esc = entry.get("name", "").replace('"', '\\"')
        desc_esc = entry.get("summary", "").replace('"', '\\"').replace("\n", " ")[:150]
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

        js_lines.append(f'    lastEnriched: "{entry.get("lastEnriched", "")}",')
        js_lines.append("  },")

    js_lines.append("];")

    js_path = DATA_DIR / "diffbot_enrichment_auto.js"
    with open(js_path, "w") as f:
        f.write("\n".join(js_lines))
    print(f"Saved JS to {js_path}")

    # Top stats
    with_employees = [e for e in enriched if e.get("employeeCount")]
    with_revenue = [e for e in enriched if e.get("estimatedRevenue")]
    with_social = [e for e in enriched if e.get("socialLinks")]
    public = [e for e in enriched if e.get("isPublic")]

    print(f"\nEnrichment coverage:")
    print(f"  Employee count: {len(with_employees)} companies")
    print(f"  Revenue estimate: {len(with_revenue)} companies")
    print(f"  Social links: {len(with_social)} companies")
    print(f"  Publicly traded: {len(public)} companies")

    # Employee distribution
    if with_employees:
        ranges = {}
        for e in with_employees:
            r = e.get("employeeRange", "Unknown")
            ranges[r] = ranges.get(r, 0) + 1
        print(f"\n  Employee distribution:")
        for r, count in sorted(ranges.items()):
            print(f"    {r}: {count}")

    print("=" * 60)


if __name__ == "__main__":
    main()
