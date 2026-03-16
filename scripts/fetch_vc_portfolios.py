#!/usr/bin/env python3
"""
VC Portfolio Page Scraper for ROS Startup Database
Scrapes portfolio/companies pages from tracked VC firm websites to detect
new portfolio additions. Compares against existing portfolioCompanies in
data.js and outputs newly discovered companies.

Runs weekly via GitHub Actions. Free — no paid APIs needed.
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS_PATH = Path(__file__).parent.parent / "data.js"

# Known portfolio page URLs for each VC firm
# Most VCs have standardized portfolio/companies pages
VC_PORTFOLIO_URLS = {
    "a16z": [
        "https://a16z.com/portfolio/",
    ],
    "8VC": [
        "https://8vc.com/portfolio/",
    ],
    "Founders Fund": [
        "https://foundersfund.com/portfolio/",
    ],
    "Khosla": [
        "https://khoslaventures.com/portfolio/",
    ],
    "Sequoia": [
        "https://sequoiacap.com/companies/",
    ],
    "DCVC": [
        "https://dcvc.com/portfolio/",
    ],
    "Eclipse": [
        "https://eclipse.vc/portfolio/",
    ],
    "GC": [
        "https://generalcatalyst.com/portfolio/",
    ],
    "AV": [
        "https://av.vc/portfolio/",
    ],
    "Lux": [
        "https://luxcapital.com/portfolio/",
    ],
    "Harpoon": [
        "https://harpoon.vc/portfolio/",
    ],
    "Lower Carbon": [
        "https://lowercarbon.com/portfolio/",
    ],
    "Cantos": [
        "https://cantos.vc/portfolio/",
    ],
    "Shield Capital": [
        "https://shieldcap.com/portfolio/",
    ],
    "Bedrock": [
        "https://bedrockcap.com/portfolio/",
    ],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def load_existing_portfolios():
    """Load existing portfolioCompanies from data.js for each VC."""
    if not DATA_JS_PATH.exists():
        return {}

    content = DATA_JS_PATH.read_text()
    portfolios = {}

    # Find each VC entry and extract its portfolioCompanies
    for short_name in VC_PORTFOLIO_URLS.keys():
        pattern = rf'shortName:\s*"{re.escape(short_name)}"'
        match = re.search(pattern, content)
        if not match:
            continue

        # Look for portfolioCompanies array after this match
        after = content[match.start():match.start() + 3000]
        portfolio_match = re.search(r'portfolioCompanies:\s*\[([^\]]*)\]', after)
        if portfolio_match:
            companies = re.findall(r'"([^"]+)"', portfolio_match.group(1))
            portfolios[short_name] = set(companies)

    return portfolios


def load_tracked_companies():
    """Load all company names tracked in the database."""
    if not DATA_JS_PATH.exists():
        return set()

    content = DATA_JS_PATH.read_text()
    # Match company names from the COMPANIES array
    names = set(re.findall(r'name:\s*"([^"]+)"', content[:500000]))
    return names


def scrape_portfolio_page(url):
    """
    Scrape a VC portfolio page and extract company names.
    Uses simple HTML parsing to find company names in common patterns.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as e:
        print(f"  Failed to fetch {url}: {e}")
        return []

    company_names = set()

    # Strategy 1: Look for company names in common HTML patterns
    # Many VC sites use structured markup for portfolio companies

    # Pattern: <h2>, <h3>, <h4> tags with company names
    for tag in ['h2', 'h3', 'h4', 'h5']:
        for match in re.finditer(
            rf'<{tag}[^>]*>\s*([^<]+?)\s*</{tag}>',
            html, re.IGNORECASE
        ):
            name = match.group(1).strip()
            # Filter: reasonable company name length
            if 2 < len(name) < 60 and not name.startswith('<'):
                company_names.add(name)

    # Pattern: alt text on images (logos)
    for match in re.finditer(r'alt="([^"]+)"', html, re.IGNORECASE):
        name = match.group(1).strip()
        # Filter for likely company names (not generic alt text)
        if (2 < len(name) < 50
            and 'logo' not in name.lower()
            and 'icon' not in name.lower()
            and 'image' not in name.lower()
            and 'photo' not in name.lower()
            and 'banner' not in name.lower()):
            company_names.add(name)

    # Pattern: data attributes commonly used for company names
    for match in re.finditer(
        r'data-(?:company|name|title)="([^"]+)"',
        html, re.IGNORECASE
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 60:
            company_names.add(name)

    # Pattern: aria-label on links/cards
    for match in re.finditer(
        r'aria-label="([^"]+)"',
        html, re.IGNORECASE
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 50:
            company_names.add(name)

    # Pattern: JSON-LD structured data
    for match in re.finditer(
        r'"name"\s*:\s*"([^"]+)"',
        html
    ):
        name = match.group(1).strip()
        if 2 < len(name) < 60:
            company_names.add(name)

    return list(company_names)


def match_to_tracked(scraped_names, tracked_companies):
    """
    Match scraped company names to tracked companies in the database.
    Uses fuzzy matching to handle slight name variations.
    """
    matches = set()
    tracked_lower = {name.lower(): name for name in tracked_companies}

    for scraped in scraped_names:
        scraped_lower = scraped.lower().strip()

        # Exact match
        if scraped_lower in tracked_lower:
            matches.add(tracked_lower[scraped_lower])
            continue

        # Match without common suffixes
        for suffix in [' inc', ' inc.', ' corp', ' corp.', ' llc', ' ltd',
                       ' co', ' co.', ' technologies', ' technology']:
            cleaned = scraped_lower.rstrip('.').removesuffix(suffix)
            if cleaned in tracked_lower:
                matches.add(tracked_lower[cleaned])
                break

        # Check if any tracked company name is contained in the scraped name
        for tracked_lower_name, tracked_original in tracked_lower.items():
            if len(tracked_lower_name) >= 5:
                if tracked_lower_name in scraped_lower or scraped_lower in tracked_lower_name:
                    matches.add(tracked_original)

    return matches


def main():
    print("=" * 60)
    print("VC Portfolio Page Scraper")
    print(f"Run time: {datetime.now().isoformat()}")
    print("=" * 60)

    # Load existing data
    existing_portfolios = load_existing_portfolios()
    tracked_companies = load_tracked_companies()

    print(f"\nLoaded {len(existing_portfolios)} VC portfolios from data.js")
    print(f"Tracking {len(tracked_companies)} companies in database")

    all_changes = []
    total_new = 0

    for vc_short, urls in VC_PORTFOLIO_URLS.items():
        existing = existing_portfolios.get(vc_short, set())
        print(f"\n--- {vc_short} (currently {len(existing)} companies) ---")

        all_scraped = set()
        for url in urls:
            print(f"  Scraping: {url}")
            scraped = scrape_portfolio_page(url)
            print(f"    Found {len(scraped)} raw names")
            all_scraped.update(scraped)

        # Match scraped names to tracked companies
        matched = match_to_tracked(all_scraped, tracked_companies)
        print(f"  Matched to {len(matched)} tracked companies")

        # Find new additions (in scraped but not in existing portfolio)
        new_companies = matched - existing
        if new_companies:
            print(f"  NEW: {', '.join(sorted(new_companies))}")
            total_new += len(new_companies)

            for company in sorted(new_companies):
                all_changes.append({
                    "vc": vc_short,
                    "company": company,
                    "source": "portfolio_page",
                    "detected_date": datetime.now().strftime("%Y-%m-%d"),
                })
        else:
            print("  No new companies detected")

    # Save results
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / "vc_portfolio_changes.json"

    # Load existing changes and append (keep history)
    existing_changes = []
    if output_path.exists():
        try:
            existing_changes = json.loads(output_path.read_text())
        except json.JSONDecodeError:
            existing_changes = []

    # Deduplicate: don't add if same vc+company already recorded this week
    existing_keys = {(c["vc"], c["company"]) for c in existing_changes
                     if c.get("detected_date", "") >= (datetime.now().strftime("%Y-%m"))}

    new_changes = [c for c in all_changes
                   if (c["vc"], c["company"]) not in existing_keys]

    if new_changes:
        combined = existing_changes + new_changes
        # Keep last 90 days of history
        cutoff = datetime.now().strftime("%Y-%m-%d")
        combined = [c for c in combined
                    if c.get("detected_date", "2020-01-01") >= "2025-12-01"]
        output_path.write_text(json.dumps(combined, indent=2))

    print(f"\n{'=' * 60}")
    print(f"Total new portfolio additions detected: {total_new}")
    print(f"Changes saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
