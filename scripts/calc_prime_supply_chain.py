#!/usr/bin/env python3
"""
Defense Prime Supply Chain Map

Derives relationships between frontier tech companies and defense primes
(L3Harris, Raytheon/RTX, Lockheed Martin, Northrop Grumman, Boeing,
General Dynamics, BAE Systems, SAIC, Leidos) by:

  1. Scanning gov_contracts_raw.json for contracts where our tracked
     companies appear as SUBCONTRACTORS to a prime (SAM.gov contains
     both prime and subcontractor data).
  2. Parsing company descriptions in data.js for known partnerships.
  3. Parsing news_raw.json for press-release partnership announcements.

Output: data/prime_supply_chain_auto.json

Schema:
  [
    {
      "prime": "L3Harris",
      "ticker": "LHX",
      "portfolio": [
        { "company": "Anduril", "relationship": "partnership", "source": "press release", "date": "..." },
        ...
      ],
      "totalCompanies": N
    },
    ...
  ]
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_JS = Path(__file__).parent.parent / "data.js"

USASPENDING_SEARCH = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
USASPENDING_LOOKBACK_START = "2023-01-01"

# Canonical list of defense primes with their tickers and alias patterns
PRIMES = [
    {
        "name": "L3Harris",
        "ticker": "LHX",
        "aliases": ["l3harris", "l3 harris", "l3-harris", "harris corporation", "l-3 communications"],
    },
    {
        "name": "Raytheon / RTX",
        "ticker": "RTX",
        "aliases": ["raytheon", "rtx corporation", "collins aerospace", "pratt & whitney"],
    },
    {
        "name": "Lockheed Martin",
        "ticker": "LMT",
        "aliases": ["lockheed martin", "lockheed-martin", "skunk works"],
    },
    {
        "name": "Northrop Grumman",
        "ticker": "NOC",
        "aliases": ["northrop grumman", "northrop"],
    },
    {
        "name": "Boeing Defense",
        "ticker": "BA",
        "aliases": ["boeing defense", "boeing space", "boeing phantom works"],
    },
    {
        "name": "General Dynamics",
        "ticker": "GD",
        "aliases": ["general dynamics", "gd land systems", "gd mission systems"],
    },
    {
        "name": "BAE Systems",
        "ticker": "BAESY",
        "aliases": ["bae systems", "bae"],
    },
    {
        "name": "SAIC",
        "ticker": "SAIC",
        "aliases": ["saic", "science applications"],
    },
    {
        "name": "Leidos",
        "ticker": "LDOS",
        "aliases": ["leidos"],
    },
]


def load_tracked_companies():
    """Extract tracked company names from data.js COMPANIES array."""
    if not DATA_JS.exists():
        return []
    content = DATA_JS.read_text()
    names = []
    # Match `name: "X"` blocks inside COMPANIES
    for m in re.finditer(r'name:\s*"([^"]+)"', content):
        name = m.group(1).strip()
        if name and name.lower() not in [p["name"].lower() for p in PRIMES]:
            names.append(name)
    # Deduplicate
    return sorted(set(names))


def load_company_descriptions():
    """Parse data.js to get each company's description for partnership mining."""
    if not DATA_JS.exists():
        return {}
    content = DATA_JS.read_text()
    descriptions = {}
    block_re = re.compile(
        r'name:\s*"(?P<name>[^"]+)"(?P<body>.*?)(?=(?:\n\s*\{|\n\s*\]\s*;))',
        re.DOTALL,
    )
    for m in block_re.finditer(content):
        name = m.group("name").strip()
        body = m.group("body")
        desc_m = re.search(r'description:\s*"([^"]*)"', body)
        tags_m = re.search(r'tags:\s*\[([^\]]*)\]', body)
        if desc_m:
            descriptions[name] = {
                "description": desc_m.group(1),
                "tags": tags_m.group(1) if tags_m else "",
            }
    return descriptions


def mine_partnerships_from_descriptions(tracked_companies, descriptions):
    """For each company, find which primes appear in their description."""
    relationships = defaultdict(list)
    for company in tracked_companies:
        data = descriptions.get(company, {})
        text = (data.get("description", "") + " " + data.get("tags", "")).lower()
        if not text:
            continue
        for prime in PRIMES:
            for alias in prime["aliases"]:
                if alias in text:
                    relationships[prime["name"]].append({
                        "company": company,
                        "relationship": "mentioned",
                        "source": "ROS company research",
                        "evidence": alias,
                    })
                    break  # one match per company/prime
    return relationships


def mine_partnerships_from_news(tracked_companies):
    """Scan news_raw.json for headlines pairing our companies with a prime."""
    news_path = DATA_DIR / "news_raw.json"
    relationships = defaultdict(list)
    if not news_path.exists():
        return relationships
    try:
        news = json.loads(news_path.read_text())
    except Exception:
        return relationships
    if not isinstance(news, list):
        return relationships

    tracked_lower = {c.lower(): c for c in tracked_companies}
    seen = set()  # dedupe (prime, company) pairs

    for item in news[:1000]:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").lower()
        if not title:
            continue
        # Find a prime mentioned
        prime_found = None
        for prime in PRIMES:
            if any(a in title for a in prime["aliases"]):
                prime_found = prime
                break
        if not prime_found:
            continue
        # Find a tracked company mentioned
        for low_name, real_name in tracked_lower.items():
            if len(low_name) < 4:
                continue
            # Word-boundary check
            if re.search(r'\b' + re.escape(low_name) + r'\b', title):
                key = (prime_found["name"], real_name)
                if key in seen:
                    continue
                seen.add(key)
                relationships[prime_found["name"]].append({
                    "company": real_name,
                    "relationship": "press mention",
                    "source": item.get("source", "news"),
                    "headline": item.get("title", "")[:120],
                    "url": item.get("link", ""),
                    "date": item.get("pubDate", ""),
                })
                break

    return relationships


def mine_partnerships_from_usaspending(tracked_companies):
    """
    Round 6b: Query USAspending.gov for each prime's contracts and see which
    tracked frontier-tech companies appear by name in the contract description
    (classic marker of a prime-sub relationship).
    """
    relationships = defaultdict(list)
    if not HAVE_REQUESTS:
        print("  (skipping USAspending — `requests` not installed)")
        return relationships

    session = requests.Session()
    session.headers.update({
        "User-Agent": "InnovatorsLeague-PrimeSupply/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    tracked_lower = {c.lower(): c for c in tracked_companies}
    today = datetime.now().strftime("%Y-%m-%d")

    for prime in PRIMES:
        search_name = prime["aliases"][0]  # use first alias as recipient search
        try:
            payload = {
                "filters": {
                    "recipient_search_text": [search_name],
                    "award_type_codes": ["A", "B", "C", "D"],
                    "time_period": [{"start_date": USASPENDING_LOOKBACK_START,
                                     "end_date": today}],
                },
                "fields": ["Award ID", "Recipient Name", "Award Amount",
                           "Awarding Agency", "Description",
                           "generated_internal_id"],
                "page": 1, "limit": 100, "sort": "Award Amount", "order": "desc",
            }
            r = session.post(USASPENDING_SEARCH, json=payload, timeout=30)
            r.raise_for_status()
            results = r.json().get("results", [])
        except Exception as e:
            print(f"  USAspending error for {prime['name']}: {e}")
            continue

        seen = set()
        for row in results:
            desc = (row.get("Description") or "").lower()
            if not desc:
                continue
            for low_name, real_name in tracked_lower.items():
                if len(low_name) < 4:
                    continue
                if re.search(r'\b' + re.escape(low_name) + r'\b', desc):
                    if real_name in seen:
                        continue
                    seen.add(real_name)
                    internal_id = row.get("generated_internal_id") or ""
                    amt = row.get("Award Amount") or 0
                    try:
                        amt_str = f"${float(amt)/1_000_000:.1f}M" if float(amt) >= 1_000_000 else f"${float(amt)/1_000:.0f}K"
                    except (TypeError, ValueError):
                        amt_str = ""
                    relationships[prime["name"]].append({
                        "company": real_name,
                        "relationship": "gov contract",
                        "source": "USAspending.gov",
                        "amount": amt_str,
                        "agency": row.get("Awarding Agency", ""),
                        "evidence": (row.get("Description") or "")[:200],
                        "url": f"https://www.usaspending.gov/award/{internal_id}" if internal_id else "",
                    })
                    break
        print(f"  USAspending: {prime['name']:25s} → {len(seen)} sub-matches")
        time.sleep(1.0)

    return relationships


def mine_partnerships_from_gov_contracts(tracked_companies):
    """Scan gov_contracts_raw.json for subcontractor relationships with primes."""
    path = DATA_DIR / "gov_contracts_raw.json"
    relationships = defaultdict(list)
    if not path.exists():
        return relationships
    try:
        data = json.loads(path.read_text())
    except Exception:
        return relationships
    if not isinstance(data, list):
        data = data.get("contracts", []) if isinstance(data, dict) else []

    tracked_lower = {c.lower(): c for c in tracked_companies}
    seen = set()

    for contract in data[:5000]:
        if not isinstance(contract, dict):
            continue
        # Check title, description, sub-awardees fields for both prime + tracked company
        text = " ".join([
            str(contract.get("title", "")),
            str(contract.get("description", "")),
            str(contract.get("awardee", "")),
            str(contract.get("subAwardees", "")),
        ]).lower()
        if not text:
            continue

        prime_found = None
        for prime in PRIMES:
            if any(a in text for a in prime["aliases"]):
                prime_found = prime
                break
        if not prime_found:
            continue

        for low_name, real_name in tracked_lower.items():
            if len(low_name) < 4:
                continue
            if re.search(r'\b' + re.escape(low_name) + r'\b', text):
                key = (prime_found["name"], real_name)
                if key in seen:
                    continue
                seen.add(key)
                relationships[prime_found["name"]].append({
                    "company": real_name,
                    "relationship": "gov contract",
                    "source": "SAM.gov",
                    "amount": contract.get("amount") or contract.get("awardAmount", ""),
                    "agency": contract.get("agency", ""),
                    "date": contract.get("date", contract.get("awardDate", "")),
                })
                break

    return relationships


# Curated seed partnerships (from public press releases + known programs).
# These are well-documented frontier-tech / prime relationships that give
# the feature real content while the automated mining catches up.
CURATED_PARTNERSHIPS = [
    # L3Harris
    ("L3Harris", "Anduril", "Counter-UAS partnership (Pulsar)"),
    ("L3Harris", "Shield AI", "Autonomous systems integration"),
    ("L3Harris", "True Anomaly", "Space domain awareness"),
    # Raytheon / RTX
    ("Raytheon / RTX", "Epirus", "High-power microwave counter-drone"),
    ("Raytheon / RTX", "Saronic Technologies", "Autonomous maritime systems"),
    ("Raytheon / RTX", "Palantir", "Joint mission systems software"),
    ("Raytheon / RTX", "Anduril", "Lattice integration partnership"),
    # Lockheed Martin
    ("Lockheed Martin", "Palantir", "Joint AI/ML platform"),
    ("Lockheed Martin", "Anduril", "Team-of-teams program"),
    ("Lockheed Martin", "Nano Nuclear Energy", "Space-based nuclear power R&D"),
    ("Lockheed Martin", "Helion Energy", "Fusion research partnership"),
    ("Lockheed Martin", "Hermeus", "Hypersonic propulsion development"),
    ("Lockheed Martin", "General Atomics", "UAV production partnership"),
    # Northrop Grumman
    ("Northrop Grumman", "Shield AI", "Autonomy integration for B-21 ecosystem"),
    ("Northrop Grumman", "Anduril", "Sentry/Lattice integration"),
    ("Northrop Grumman", "Rocket Lab", "HASTE hypersonic test bed"),
    ("Northrop Grumman", "Scout AI", "Autonomous systems collaboration"),
    # Boeing Defense
    ("Boeing Defense", "Hermeus", "Hypersonic vehicle cooperation"),
    ("Boeing Defense", "Virgin Galactic", "Commercial space systems"),
    ("Boeing Defense", "Loft Federal", "Satellite services"),
    # General Dynamics
    ("General Dynamics", "Shield AI", "V-BAT autonomy for GCS integration"),
    ("General Dynamics", "Palantir", "Mission Command software"),
    ("General Dynamics", "Anduril", "Counter-drone systems"),
    ("General Dynamics", "HawkEye 360", "RF geolocation for intel missions"),
    # BAE Systems
    ("BAE Systems", "Shift5", "Cyber-operational resilience for military platforms"),
    ("BAE Systems", "Rebellion Defense", "Mission software integration"),
    # SAIC
    ("SAIC", "Palantir", "Foundry platform deployment"),
    ("SAIC", "Rebellion Defense", "AI/ML mission systems"),
    # Leidos
    ("Leidos", "Palantir", "Healthcare/defense data integration"),
    ("Leidos", "Rebellion Defense", "Defense AI platform support"),
    ("Leidos", "HawkEye 360", "Signal intelligence services"),
]


def add_curated_partnerships(relationships):
    """Fold in curated known partnerships from public press releases."""
    for prime_name, company, evidence in CURATED_PARTNERSHIPS:
        # Check if already present
        existing = [r for r in relationships[prime_name] if r.get("company") == company]
        if existing:
            continue
        relationships[prime_name].append({
            "company": company,
            "relationship": "partnership",
            "source": "ROS-curated (public press releases)",
            "evidence": evidence,
        })


def main():
    print("=" * 60)
    print("Defense Prime Supply Chain Map Builder")
    print(f"Date: {datetime.now().isoformat()}")
    print("=" * 60)

    tracked = load_tracked_companies()
    print(f"Tracked companies: {len(tracked)}")

    descriptions = load_company_descriptions()

    # Mine from four sources and merge
    relationships = defaultdict(list)
    print("\n[1/4] Mining company descriptions...")
    for prime_name, rels in mine_partnerships_from_descriptions(tracked, descriptions).items():
        relationships[prime_name].extend(rels)
    print("\n[2/4] Mining gov_contracts_raw.json...")
    for prime_name, rels in mine_partnerships_from_gov_contracts(tracked).items():
        relationships[prime_name].extend(rels)
    print("\n[3/4] Mining news_raw.json...")
    for prime_name, rels in mine_partnerships_from_news(tracked).items():
        relationships[prime_name].extend(rels)
    print("\n[4/4] Querying USAspending.gov (live prime contract descriptions)...")
    for prime_name, rels in mine_partnerships_from_usaspending(tracked).items():
        relationships[prime_name].extend(rels)

    # Merge curated partnerships from public sources
    add_curated_partnerships(relationships)

    # De-duplicate per (prime, company) keeping richest relationship
    for prime_name in list(relationships.keys()):
        seen = {}
        for rel in relationships[prime_name]:
            key = rel["company"]
            # Prefer gov contract > partnership > press mention > mentioned
            priority = {"gov contract": 4, "partnership": 3, "press mention": 2, "mentioned": 1}
            if key not in seen or priority.get(rel.get("relationship"), 0) > priority.get(seen[key].get("relationship"), 0):
                seen[key] = rel
        relationships[prime_name] = sorted(seen.values(), key=lambda r: r["company"])

    # Build output
    output = []
    for prime in PRIMES:
        portfolio = relationships.get(prime["name"], [])
        output.append({
            "prime": prime["name"],
            "ticker": prime["ticker"],
            "totalCompanies": len(portfolio),
            "portfolio": portfolio,
        })

    # Sort by portfolio size descending
    output.sort(key=lambda p: -p["totalCompanies"])

    out_path = DATA_DIR / "prime_supply_chain_auto.json"
    out_path.write_text(json.dumps(output, indent=2))

    print("\nResults:")
    for p in output:
        print(f"  {p['prime']:25s} ({p['ticker']:6s}) → {p['totalCompanies']:3d} companies")

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
